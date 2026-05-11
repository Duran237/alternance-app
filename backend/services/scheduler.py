import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import AsyncSessionLocal
from services.night_job import run_night_job_all_users

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def _scheduled_night_job():
    async with AsyncSessionLocal() as db:
        await run_night_job_all_users(db)


def start_scheduler():
    # Toutes les heures pleines de 2h à 7h (2:00, 3:00, 4:00, 5:00, 6:00, 7:00)
    scheduler.add_job(
        _scheduled_night_job,
        trigger=CronTrigger(hour="2-7", minute=0, timezone="Europe/Paris"),
        id="night_job_hour",
        name="Recherche nocturne (heure pleine)",
        replace_existing=True,
    )
    # Toutes les demi-heures de 2h30 à 6h30 (2:30, 3:30, 4:30, 5:30, 6:30)
    scheduler.add_job(
        _scheduled_night_job,
        trigger=CronTrigger(hour="2-6", minute=30, timezone="Europe/Paris"),
        id="night_job_half",
        name="Recherche nocturne (demi-heure)",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[Scheduler] Tâche nocturne planifiée toutes les 30 min de 2h à 7h (Europe/Paris)")


def stop_scheduler():
    scheduler.shutdown()
