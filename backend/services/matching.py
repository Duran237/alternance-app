from models.user import User
from models.job import Job


def compute_match_score(user: User, job: Job) -> int:
    """Return a compatibility score 0-100 between a user profile and a job offer."""
    score = 0
    user_skills = {s.lower() for s in (user.skills or [])}
    job_skills = {s.lower() for s in (job.skills_required or [])}

    if job_skills:
        matched = user_skills & job_skills
        skill_ratio = len(matched) / len(job_skills)
        score += int(skill_ratio * 60)

    if user.target_city and job.location:
        if user.target_city.lower() in job.location.lower():
            score += 20
        elif "remote" in job.location.lower() or "télétravail" in job.location.lower():
            score += 10

    if job.contract_type and "alternance" in job.contract_type.lower():
        score += 20

    return min(score, 100)
