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
    scheduler.add_job(
        _scheduled_night_job,
        trigger=CronTrigger(hour=2, minute=0, timezone="Europe/Paris"),
        id="night_job",
        name="Recherche nocturne d'alternances",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[Scheduler] Tâche nocturne planifiée à 02h00 heure de Paris")


def stop_scheduler():
    scheduler.shutdown()
