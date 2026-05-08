from collections import Counter
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.application import Application
from models.notification import Notification
from models.user import User
from utils.security import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])


class StatsOut(BaseModel):
    total_applications: int
    sent: int
    interviews: int
    rejected: int
    accepted: int
    follow_up: int
    response_rate: float
    interview_rate: float
    top_skills_demanded: List[dict]
    applications_by_month: List[dict]
    notifications_unread: int


class NotificationOut(BaseModel):
    id: int
    type: str
    message: str
    read: bool

    model_config = {"from_attributes": True}


@router.get("/", response_model=StatsOut)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.user_id == current_user.id)
    )
    apps = result.scalars().all()

    status_counts = Counter(a.status for a in apps)
    total = len(apps)
    interviews = status_counts.get("interview", 0)
    accepted = status_counts.get("accepted", 0)
    rejected = status_counts.get("rejected", 0)

    responses = interviews + accepted + rejected
    response_rate = round(responses / total * 100, 1) if total else 0
    interview_rate = round(interviews / total * 100, 1) if total else 0

    skills_counter: Counter = Counter()
    for a in apps:
        if a.job and a.job.skills_required:
            skills_counter.update(a.job.skills_required)

    top_skills = [{"skill": s, "count": c} for s, c in skills_counter.most_common(10)]

    month_counter: Counter = Counter()
    for a in apps:
        key = a.sent_at.strftime("%Y-%m") if a.sent_at else "?"
        month_counter[key] += 1
    by_month = [{"month": m, "count": c} for m, c in sorted(month_counter.items())]

    notif_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id, Notification.read == False
        )
    )
    unread = notif_result.scalar() or 0

    return StatsOut(
        total_applications=total,
        sent=status_counts.get("sent", 0),
        interviews=interviews,
        rejected=rejected,
        accepted=accepted,
        follow_up=status_counts.get("follow_up", 0),
        response_rate=response_rate,
        interview_rate=interview_rate,
        top_skills_demanded=top_skills,
        applications_by_month=by_month,
        notifications_unread=unread,
    )


@router.get("/notifications", response_model=List[NotificationOut])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.post("/notifications/{notif_id}/read")
async def mark_notification_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    result = await db.execute(
        select(Notification).where(Notification.id == notif_id, Notification.user_id == current_user.id)
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    notif.read = True
    db.add(notif)
    await db.commit()
    return {"ok": True}
