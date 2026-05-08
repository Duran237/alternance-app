from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.application import Application
from models.night_report import NightReport
from models.user import User
from services.night_job import run_night_job_for_user
from utils.security import get_current_user

router = APIRouter(prefix="/automation", tags=["automation"])


class NightReportOut(BaseModel):
    id: int
    run_at: datetime
    new_jobs_found: int
    compatible_jobs: int
    drafts_prepared: int
    keywords_used: Optional[str] = None
    top_jobs: List[dict] = []

    model_config = {"from_attributes": True}


class DraftApplicationOut(BaseModel):
    id: int
    job_id: int
    match_score: Optional[int] = None
    cover_letter: Optional[str] = None
    sent_at: datetime
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_url: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get("/report/latest", response_model=Optional[NightReportOut])
async def get_latest_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NightReport)
        .where(NightReport.user_id == current_user.id)
        .order_by(NightReport.run_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/report/history", response_model=List[NightReportOut])
async def get_report_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NightReport)
        .where(NightReport.user_id == current_user.id)
        .order_by(NightReport.run_at.desc())
        .limit(30)
    )
    return result.scalars().all()


@router.post("/run", response_model=NightReportOut)
async def trigger_night_job(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Déclenche manuellement le job nocturne pour l'utilisateur courant."""
    summary = await run_night_job_for_user(current_user, db)

    result = await db.execute(
        select(NightReport)
        .where(NightReport.user_id == current_user.id)
        .order_by(NightReport.run_at.desc())
        .limit(1)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=500, detail="Erreur lors de la création du rapport")
    return report


@router.get("/drafts", response_model=List[DraftApplicationOut])
async def get_draft_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.user_id == current_user.id, Application.status == "draft")
        .order_by(Application.match_score.desc())
    )
    apps = result.scalars().all()

    return [
        DraftApplicationOut(
            id=a.id,
            job_id=a.job_id,
            match_score=a.match_score,
            cover_letter=a.cover_letter,
            sent_at=a.sent_at,
            job_title=a.job.title if a.job else None,
            company=a.job.company if a.job else None,
            location=a.job.location if a.job else None,
            job_url=a.job.url if a.job else None,
        )
        for a in apps
    ]


@router.post("/drafts/{app_id}/validate")
async def validate_draft(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Valider un draft → le passe en statut 'sent'."""
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == current_user.id,
            Application.status == "draft",
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Draft introuvable")

    app.status = "sent"
    app.sent_at = datetime.utcnow()
    db.add(app)
    await db.commit()
    return {"ok": True, "message": "Candidature validée et marquée comme envoyée"}


@router.delete("/drafts/{app_id}")
async def discard_draft(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ignorer un draft (le supprimer)."""
    result = await db.execute(
        select(Application).where(
            Application.id == app_id,
            Application.user_id == current_user.id,
            Application.status == "draft",
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Draft introuvable")

    await db.delete(app)
    await db.commit()
    return {"ok": True}
