from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.job import Job
from models.user import User
from services.matching import compute_match_score
from services.scraper import scrape_all
from utils.security import get_current_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    skills_required: List[str] = []
    url: str
    source: Optional[str] = None
    contract_type: Optional[str] = None
    match_score: Optional[int] = None

    model_config = {"from_attributes": True}


@router.get("/", response_model=List[JobOut])
async def list_jobs(
    q: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=7)
    stmt = select(Job).where(Job.scraped_at >= cutoff)

    filters = []
    if q:
        words = [w.strip() for w in q.split() if len(w.strip()) > 2]
        for word in words:
            term = f"%{word}%"
            filters.append(or_(Job.title.ilike(term), Job.description.ilike(term), Job.company.ilike(term)))
    if location:
        filters.append(Job.location.ilike(f"%{location}%"))

    if filters:
        from sqlalchemy import and_
        stmt = stmt.where(and_(*filters))

    stmt = stmt.order_by(Job.scraped_at.desc()).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    out = []
    for job in jobs:
        score = compute_match_score(current_user, job)
        job_dict = {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary": job.salary,
            "description": job.description,
            "skills_required": job.skills_required or [],
            "url": job.url,
            "source": job.source,
            "contract_type": job.contract_type,
            "match_score": score,
        }
        out.append(job_dict)

    out.sort(key=lambda j: j["match_score"], reverse=True)
    return out


@router.get("/recommended", response_model=List[JobOut])
async def recommended_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cutoff = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(select(Job).where(Job.scraped_at >= cutoff).order_by(Job.scraped_at.desc()).limit(200))
    jobs = result.scalars().all()

    scored = []
    for job in jobs:
        score = compute_match_score(current_user, job)
        if score >= 30:
            scored.append((score, job))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary": job.salary,
            "description": job.description,
            "skills_required": job.skills_required or [],
            "url": job.url,
            "source": job.source,
            "contract_type": job.contract_type,
            "match_score": score,
        }
        for score, job in scored[:20]
    ]


@router.post("/scrape", response_model=List[JobOut])
async def trigger_scrape(
    keywords: str = Query("alternance cybersécurité"),
    location: str = Query("France"),
    company: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    scraped = await scrape_all(
        keywords, location,
        ft_client_id=settings.FT_CLIENT_ID,
        ft_client_secret=settings.FT_CLIENT_SECRET,
        target_company=company,
    )
    result_jobs: list[Job] = []

    for job_data in scraped:
        existing = await db.execute(select(Job).where(Job.url == job_data["url"]))
        existing_job = existing.scalar_one_or_none()
        if existing_job:
            result_jobs.append(existing_job)
            continue
        job = Job(**job_data)
        db.add(job)
        result_jobs.append(job)

    await db.commit()
    for job in result_jobs:
        await db.refresh(job)

    out = []
    for job in result_jobs:
        score = compute_match_score(current_user, job)
        out.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary": job.salary,
            "description": job.description,
            "skills_required": job.skills_required or [],
            "url": job.url,
            "source": job.source,
            "contract_type": job.contract_type,
            "match_score": score,
        })

    out.sort(key=lambda j: j["match_score"] or 0, reverse=True)
    return out


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Offre introuvable")
    score = compute_match_score(current_user, job)
    return {**job.__dict__, "match_score": score}
