from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.application import Application
from models.job import Job
from models.notification import Notification
from models.user import User
from services.ai_service import generate_cover_letter, generate_application_email
from services.email_service import send_application_confirmation, send_real_application
from services.contact_finder import find_email_in_description, find_email_on_job_page
from services.matching import compute_match_score
from utils.security import get_current_user

router = APIRouter(prefix="/applications", tags=["applications"])

VALID_STATUSES = {"draft", "sent", "interview", "rejected", "accepted", "follow_up"}


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    status: str
    cover_letter: Optional[str] = None
    notes: Optional[str] = None
    match_score: Optional[int] = None
    email_sent_to: Optional[str] = None
    sent_at: datetime
    updated_at: datetime
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_url: Optional[str] = None

    model_config = {"from_attributes": True}


class CreateApplicationRequest(BaseModel):
    job_id: int
    notes: Optional[str] = None
    generate_letter: bool = True


class UpdateApplicationRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    cover_letter: Optional[str] = None


@router.get("/", response_model=List[ApplicationOut])
async def list_applications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.user_id == current_user.id)
        .order_by(Application.sent_at.desc())
    )
    apps = result.scalars().all()

    return [
        ApplicationOut(
            id=a.id,
            job_id=a.job_id,
            status=a.status,
            cover_letter=a.cover_letter,
            notes=a.notes,
            match_score=a.match_score,
            sent_at=a.sent_at,
            updated_at=a.updated_at,
            email_sent_to=a.email_sent_to,
            job_title=a.job.title if a.job else None,
            company=a.job.company if a.job else None,
            location=a.job.location if a.job else None,
            job_url=a.job.url if a.job else None,
        )
        for a in apps
    ]


@router.post("/", response_model=ApplicationOut, status_code=201)
async def create_application(
    data: CreateApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job_result = await db.execute(select(Job).where(Job.id == data.job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Offre introuvable")

    existing = await db.execute(
        select(Application).where(Application.user_id == current_user.id, Application.job_id == data.job_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Candidature déjà envoyée pour cette offre")

    cover_letter = None
    if data.generate_letter:
        cover_letter = await generate_cover_letter(
            user_name=current_user.name,
            user_skills=current_user.skills or [],
            job_title=job.title,
            company=job.company,
            job_description=job.description or "",
        )

    # Chercher l'email du recruteur
    recruiter_email = (
        job.contact_email
        or find_email_in_description(job.description or "")
    )
    # Si pas trouvé dans la description, on tente la page de l'offre
    if not recruiter_email:
        try:
            recruiter_email = await find_email_on_job_page(job.url)
        except Exception:
            pass

    # Envoyer la vraie candidature si email trouvé
    email_sent_to = None
    if recruiter_email and cover_letter:
        sent = send_real_application(
            recruiter_email=recruiter_email,
            user_name=current_user.name,
            user_email=current_user.email,
            job_title=job.title,
            company=job.company,
            cover_letter=cover_letter,
            cv_path=current_user.cv_path or "",
        )
        if sent:
            email_sent_to = recruiter_email

    score = compute_match_score(current_user, job)
    app = Application(
        user_id=current_user.id,
        job_id=data.job_id,
        status="sent",
        cover_letter=cover_letter,
        notes=data.notes,
        match_score=score,
        email_sent_to=email_sent_to,
    )
    db.add(app)

    notif_msg = (
        f"Candidature envoyée par email à {recruiter_email} — {job.title} chez {job.company}"
        if email_sent_to
        else f"Candidature préparée pour {job.title} chez {job.company} — postule sur le site"
    )
    notif = Notification(
        user_id=current_user.id,
        type="new_application",
        message=notif_msg,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(app)

    # Email de confirmation à l'utilisateur
    try:
        send_application_confirmation(
            to_email=current_user.email,
            user_name=current_user.name,
            job_title=job.title,
            company=job.company,
            job_url=job.url,
            cover_letter=cover_letter or "",
        )
    except Exception:
        pass

    return ApplicationOut(
        id=app.id,
        job_id=app.job_id,
        status=app.status,
        cover_letter=app.cover_letter,
        notes=app.notes,
        match_score=app.match_score,
        email_sent_to=app.email_sent_to,
        sent_at=app.sent_at,
        updated_at=app.updated_at,
        job_title=job.title,
        company=job.company,
        location=job.location,
        job_url=job.url,
    )


@router.put("/{app_id}", response_model=ApplicationOut)
async def update_application(
    app_id: int,
    data: UpdateApplicationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.id == app_id, Application.user_id == current_user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Candidature introuvable")

    if data.status and data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Valeurs acceptées : {VALID_STATUSES}")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(app, field, value)
    app.updated_at = datetime.utcnow()

    if data.status == "interview":
        notif = Notification(
            user_id=current_user.id,
            type="interview",
            message=f"Entretien obtenu chez {app.job.company if app.job else ''} !",
        )
        db.add(notif)

    db.add(app)
    await db.commit()
    await db.refresh(app)

    return ApplicationOut(
        id=app.id,
        job_id=app.job_id,
        status=app.status,
        cover_letter=app.cover_letter,
        notes=app.notes,
        match_score=app.match_score,
        sent_at=app.sent_at,
        updated_at=app.updated_at,
        job_title=app.job.title if app.job else None,
        company=app.job.company if app.job else None,
        location=app.job.location if app.job else None,
        job_url=app.job.url if app.job else None,
    )


@router.delete("/{app_id}", status_code=204)
async def delete_application(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(Application.id == app_id, Application.user_id == current_user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    await db.delete(app)
    await db.commit()


@router.post("/{app_id}/cover-letter")
async def regenerate_cover_letter(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.id == app_id, Application.user_id == current_user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Candidature introuvable")

    letter = await generate_cover_letter(
        user_name=current_user.name,
        user_skills=current_user.skills or [],
        job_title=app.job.title,
        company=app.job.company,
        job_description=app.job.description or "",
    )
    app.cover_letter = letter
    db.add(app)
    await db.commit()
    return {"cover_letter": letter}


@router.post("/{app_id}/email")
async def get_application_email(
    app_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.id == app_id, Application.user_id == current_user.id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Candidature introuvable")

    email = await generate_application_email(
        user_name=current_user.name,
        job_title=app.job.title,
        company=app.job.company,
    )
    return {"email": email}
