"""
AI service using Claude (Anthropic).
When ANTHROPIC_API_KEY is not set, fallback templates are used.
"""
from config import settings


import re


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting from AI-generated text."""
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text.strip()


def _has_api_key() -> bool:
    return bool(settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.startswith("sk-ant"))


async def analyze_cv(cv_text: str) -> dict:
    """Extract structured info from CV text using Claude."""
    if not _has_api_key():
        return {"message": "Configurez ANTHROPIC_API_KEY pour activer l'analyse IA du CV."}

    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = f"""Analyse ce CV et extrais en JSON :
- name (string, prénom et nom)
- skills (liste de strings, toutes les compétences techniques trouvées)
- experience_years (int, 0 si étudiant)
- education (string, formation principale)
- languages (liste de strings, langues parlées)
- target_roles (liste de 3 strings max, les postes recherchés ou adaptés au profil, ex: "Administrateur réseau", "Analyste SOC")
- phone (string ou null, numéro de téléphone si présent)
- summary (2 phrases max résumant le profil)

CV :
{cv_text[:3000]}

Réponds uniquement avec le JSON valide, sans markdown."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    import json
    try:
        return json.loads(message.content[0].text)
    except Exception:
        return {"raw": message.content[0].text}


async def generate_cover_letter(
    user_name: str,
    user_skills: list,
    job_title: str,
    company: str,
    job_description: str,
    cv_text: str = "",
    target_roles: list = None,
    target_city: str = "",
    github_url: str = "",
    linkedin_url: str = "",
    school: str = "",
    education_level: str = "",
) -> str:
    """Generate a personalized cover letter."""
    if not _has_api_key():
        skills_str = ", ".join(user_skills[:5]) if user_skills else "Python, Linux, cybersécurité"
        school_line = f" à {school}" if school else ""
        edu_line = f"En {education_level}" if education_level else "Étudiant(e)"
        return f"""Madame, Monsieur,

{edu_line}{school_line}, je me permets de vous soumettre ma candidature pour le poste de {job_title} au sein de {company} dans le cadre d'une alternance.

Passionné(e) par l'informatique et les nouvelles technologies, je dispose de compétences en {skills_str}. Mon parcours académique et mes projets personnels m'ont permis de développer une expertise technique solide et un sens de la rigueur indispensable dans ce domaine.

Je suis convaincu(e) que {company} représente un environnement stimulant pour développer mes compétences et contribuer à vos projets. Motivé(e) et curieux(se), je m'engage à apporter mon implication totale à votre équipe.

Dans l'attente d'un entretien, je reste disponible pour tout renseignement complémentaire.

Cordialement,
{user_name}"""

    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    profile_parts = [
        f"- Nom : {user_name}",
        f"- Compétences : {', '.join(user_skills[:10]) if user_skills else 'non renseignées'}",
    ]
    if school:
        profile_parts.append(f"- École / Établissement : {school}")
    if education_level:
        profile_parts.append(f"- Niveau d'études : {education_level}")
    if target_roles:
        profile_parts.append(f"- Postes visés : {', '.join(target_roles[:3])}")
    if target_city:
        profile_parts.append(f"- Ville cible : {target_city}")
    if github_url:
        profile_parts.append(f"- GitHub : {github_url}")
    if linkedin_url:
        profile_parts.append(f"- LinkedIn : {linkedin_url}")
    if cv_text:
        profile_parts.append(f"\nExtrait du CV :\n{cv_text[:1500]}")

    profile_section = "\n".join(profile_parts)

    school_instruction = f"- Mentionne obligatoirement l'établissement ({school}) et le niveau d'études ({education_level}) dès le premier paragraphe" if school or education_level else ""

    prompt = f"""Génère une lettre de motivation professionnelle en français pour une candidature en alternance.

Profil du candidat :
{profile_section}

Offre :
- Poste : {job_title}
- Entreprise : {company}
- Description : {job_description[:600]}

Instructions :
- 3 paragraphes percutants et personnalisés
- Utilise les éléments concrets du CV et du profil
- Montre pourquoi ce candidat est fait pour ce poste précis
{school_instruction}
- Ne mets pas de date, adresse ou objet
- IMPORTANT : texte brut uniquement, aucun markdown"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return _strip_markdown(message.content[0].text)


async def generate_application_email(user_name: str, job_title: str, company: str) -> str:
    """Generate a short application email."""
    if not _has_api_key():
        return f"""Objet : Candidature alternance – {job_title} – {user_name}

Madame, Monsieur,

Veuillez trouver ci-joint mon CV et ma lettre de motivation pour le poste de {job_title} au sein de {company}.

Disponible pour un entretien à votre convenance.

Cordialement,
{user_name}"""

    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = f"""Génère un email court de candidature en français (5 lignes max) pour :
- Candidat : {user_name}
- Poste : {job_title}
- Entreprise : {company}

Inclure objet et corps. Ton professionnel.
IMPORTANT : Réponds en texte brut uniquement. N'utilise aucun markdown (pas de #, **, *, _, etc.)."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return _strip_markdown(message.content[0].text)
