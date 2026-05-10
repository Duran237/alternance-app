from models.user import User
from models.job import Job

_EDU_TERMS: dict[str, list[str]] = {
    "bac+2": ["bac+2", "bts", "but", "dut"],
    "bac+3": ["bac+3", "licence", "bachelor"],
    "bac+4": ["bac+4", "master 1", "m1"],
    "bac+5": ["bac+5", "master 2", "master", "m2", "ingénieur", "ingenieur"],
}


def compute_match_score(user: User, job: Job) -> int:
    """Return a compatibility score 0-100 between a user profile and a job offer."""
    score = 0
    user_skills = {s.lower() for s in (user.skills or [])}
    job_skills = {s.lower() for s in (job.skills_required or [])}

    # Compétences : 50 pts max
    if job_skills:
        matched = user_skills & job_skills
        skill_ratio = len(matched) / len(job_skills)
        score += int(skill_ratio * 50)

    # Domaine souhaité vs titre/description : 15 pts max
    if user.target_roles:
        desc_text = ((job.title or "") + " " + (job.description or "")).lower()
        for role in (user.target_roles or []):
            if role.lower() in desc_text:
                score += 15
                break

    # Niveau d'études mentionné dans l'offre : 10 pts
    if user.education_level and job.description:
        edu_lower = user.education_level.lower()
        desc_lower = job.description.lower()
        for key, terms in _EDU_TERMS.items():
            if key in edu_lower:
                if any(t in desc_lower for t in terms):
                    score += 10
                break

    # Localisation : 15 pts max
    if user.target_city and job.location:
        if user.target_city.lower() in job.location.lower():
            score += 15
        elif "remote" in job.location.lower() or "télétravail" in job.location.lower():
            score += 8

    # Contrat alternance : 10 pts
    if job.contract_type and "alternance" in job.contract_type.lower():
        score += 10

    return min(score, 100)
