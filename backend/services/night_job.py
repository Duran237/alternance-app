"""
Tâche nocturne : scraping, matching, génération de drafts, rapport.
Peut être déclenchée manuellement ou automatiquement via le scheduler.
"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.application import Application
from models.job import Job
from models.night_report import NightReport
from models.notification import Notification
from models.user import User
from services.ai_service import generate_cover_letter
from services.matching import compute_match_score
from services.scraper import scrape_all

logger = logging.getLogger(__name__)

MIN_MATCH_SCORE = 40
DRAFT_THRESHOLD = 60


async def run_night_job_for_user(user: User, db: AsyncSession) -> dict:
    """Lance le job nocturne pour un utilisateur et retourne un résumé."""

    # Construire les mots-clés : domaine souhaité > compétences > niveau d'études
    keywords_parts = []
    if user.target_roles:
        keywords_parts += list(user.target_roles)[:3]
    if user.skills:
        keywords_parts += list(user.skills)[:3]

    edu_keyword_map = {
        "Bac+1": "Bac+1",
        "Bac+2 (BTS / BUT)": "BTS",
        "Bac+3 (Licence / Bachelor)": "Licence",
        "Bac+4 (Master 1 / Ingénieur 3ème année)": "Master 1",
        "Bac+5 (Master 2 / Ingénieur)": "Master ingénieur",
    }
    if user.education_level:
        edu_kw = edu_keyword_map.get(user.education_level, "")
        if edu_kw:
            keywords_parts.append(edu_kw)

    if not keywords_parts:
        keywords_parts = ["alternance informatique"]
    keywords = " ".join(keywords_parts)
    location = user.target_city or "France"

    # Scraping
    scraped = await scrape_all(keywords, location)
    new_jobs_added = 0
    for job_data in scraped:
        existing = await db.execute(select(Job).where(Job.url == job_data["url"]))
        if not existing.scalar_one_or_none():
            db.add(Job(**job_data))
            new_jobs_added += 1
    await db.commit()

    # Récupérer toutes les offres récentes
    result = await db.execute(select(Job).order_by(Job.scraped_at.desc()).limit(300))
    all_jobs = result.scalars().all()

    # Offres déjà postulées par l'utilisateur (y compris drafts)
    applied_result = await db.execute(
        select(Application.job_id).where(Application.user_id == user.id)
    )
    already_applied_ids = {row[0] for row in applied_result.fetchall()}

    # Calculer les scores et filtrer
    compatible = []
    for job in all_jobs:
        if job.id in already_applied_ids:
            continue
        score = compute_match_score(user, job)
        if score >= MIN_MATCH_SCORE:
            compatible.append((score, job))

    compatible.sort(key=lambda x: x[0], reverse=True)
    top_matches = compatible[:10]

    # Créer des drafts pour les meilleures offres
    drafts_created = 0
    for score, job in top_matches:
        if score < DRAFT_THRESHOLD:
            continue

        # Vérifier encore une fois qu'il n'existe pas déjà
        existing_app = await db.execute(
            select(Application).where(
                Application.user_id == user.id,
                Application.job_id == job.id,
            )
        )
        if existing_app.scalar_one_or_none():
            continue

        cover_letter = await generate_cover_letter(
            user_name=user.name,
            user_skills=user.skills or [],
            job_title=job.title,
            company=job.company,
            job_description=job.description or "",
            cv_text=user.cv_text or "",
            target_roles=user.target_roles or [],
            target_city=user.target_city or "",
            github_url=user.github_url or "",
            linkedin_url=user.linkedin_url or "",
            school=user.school or "",
            education_level=user.education_level or "",
            gender=user.gender or "",
        )

        draft = Application(
            user_id=user.id,
            job_id=job.id,
            status="draft",
            cover_letter=cover_letter,
            match_score=score,
        )
        db.add(draft)
        drafts_created += 1

    # Rapport de nuit
    top_jobs_data = [
        {"title": job.title, "company": job.company, "score": score, "location": job.location}
        for score, job in top_matches[:5]
    ]

    report = NightReport(
        user_id=user.id,
        run_at=datetime.utcnow(),
        new_jobs_found=new_jobs_added,
        compatible_jobs=len(compatible),
        drafts_prepared=drafts_created,
        keywords_used=keywords,
        top_jobs=top_jobs_data,
    )
    db.add(report)

    # Notification de synthèse
    if new_jobs_added > 0 or drafts_created > 0:
        notif = Notification(
            user_id=user.id,
            type="night_report",
            message=(
                f"Rapport nocturne : {new_jobs_added} nouvelles offres trouvées, "
                f"{len(compatible)} compatibles, {drafts_created} candidatures prêtes à valider."
            ),
        )
        db.add(notif)

    await db.commit()

    return {
        "new_jobs_found": new_jobs_added,
        "compatible_jobs": len(compatible),
        "drafts_prepared": drafts_created,
        "keywords_used": keywords,
        "top_jobs": top_jobs_data,
    }


async def run_night_job_all_users(db: AsyncSession):
    """Lance le job pour tous les utilisateurs. Appelé par le scheduler."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    logger.info(f"[NightJob] Démarrage pour {len(users)} utilisateur(s)")

    for user in users:
        try:
            summary = await run_night_job_for_user(user, db)
            logger.info(f"[NightJob] {user.email}: {summary}")
        except Exception as e:
            logger.error(f"[NightJob] Erreur pour {user.email}: {e}")
