from models.user import User
from models.job import Job

# Mapping niveau utilisateur → valeur numérique
_USER_LEVEL_MAP: dict[str, int] = {
    "bac+1": 1,
    "bac+2": 2,
    "bac+3": 3,
    "bac+4": 4,
    "bac+5": 5,
}

# Termes détectés dans les offres → niveau numérique
_JOB_LEVEL_TERMS: list[tuple[int, list[str]]] = [
    (5, ["bac+5", "master 2", "master 2", "m2", "bac +5", "bac + 5"]),
    (4, ["bac+4", "master 1", "m1", "bac +4", "bac + 4", "ingénieur 4", "3ème année"]),
    (3, ["bac+3", "licence", "bachelor", "bac +3", "bac + 3", "l3"]),
    (2, ["bac+2", "bts", "but", "dut", "bac +2", "bac + 2"]),
    (1, ["bac+1", "bac +1"]),
]

_EDU_TERMS: dict[str, list[str]] = {
    "bac+2": ["bac+2", "bts", "but", "dut"],
    "bac+3": ["bac+3", "licence", "bachelor"],
    "bac+4": ["bac+4", "master 1", "m1"],
    "bac+5": ["bac+5", "master 2", "master", "m2", "ingénieur", "ingenieur"],
}


def _detect_job_level(job: Job) -> int | None:
    """Détecte le niveau d'études requis par l'offre. Retourne None si non détecté."""
    text = ((job.title or "") + " " + (job.description or "")).lower()
    for level, terms in _JOB_LEVEL_TERMS:
        if any(t in text for t in terms):
            return level
    return None


def _user_level_value(education_level: str) -> int | None:
    """Convertit le niveau utilisateur en valeur numérique."""
    if not education_level:
        return None
    edu_lower = education_level.lower()
    for key, val in _USER_LEVEL_MAP.items():
        if key in edu_lower:
            return val
    return None


def compute_match_score(user: User, job: Job) -> int:
    """Return a compatibility score 0-100 between a user profile and a job offer."""
    score = 0
    user_skills = {s.lower() for s in (user.skills or [])}
    job_skills = {s.lower() for s in (job.skills_required or [])}

    # Compétences : 40 pts max
    if job_skills:
        matched = user_skills & job_skills
        skill_ratio = len(matched) / len(job_skills)
        score += int(skill_ratio * 40)

    # Domaine souhaité : 15 pts
    if user.target_roles:
        desc_text = ((job.title or "") + " " + (job.description or "")).lower()
        for role in (user.target_roles or []):
            if role.lower() in desc_text:
                score += 15
                break

    # Compatibilité niveau d'études : jusqu'à +20 pts ou pénalité
    user_lvl = _user_level_value(user.education_level or "")
    job_lvl = _detect_job_level(job)

    if user_lvl and job_lvl:
        diff = job_lvl - user_lvl
        if diff == 0:
            score += 20   # Niveau exact → bonus fort
        elif diff == 1:
            score += 5    # Un niveau au-dessus → acceptable
        elif diff == -1:
            score += 10   # L'offre accepte un niveau légèrement inférieur
        elif diff >= 2:
            score -= 25   # Offre trop élevée → pénalité forte
        # diff <= -2 : surqualifié, on ne pénalise pas
    elif user_lvl and not job_lvl:
        score += 5        # Offre sans niveau précisé → léger bonus (ouvert à tous)

    # Localisation : 15 pts max
    if user.target_city and job.location:
        if user.target_city.lower() in job.location.lower():
            score += 15
        elif "remote" in job.location.lower() or "télétravail" in job.location.lower():
            score += 8

    # Contrat alternance : 10 pts
    if job.contract_type and "alternance" in job.contract_type.lower():
        score += 10

    return max(0, min(score, 100))
