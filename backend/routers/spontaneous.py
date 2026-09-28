import asyncio
import logging
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from config import settings
from models.user import User
from utils.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/spontaneous", tags=["spontaneous"])

IT_NAF_CODES = [
    "62.01Z",  # Programmation informatique
    "62.02A",  # Conseil en systèmes et logiciels
    "62.02B",  # Tierce maintenance informatique
    "62.03Z",  # Gestion d'installations informatiques
    "63.11Z",  # Traitement de données / hébergement
    "62.09Z",  # Autres activités informatiques
]

PME_TRANCHES = {"11", "12", "21", "22", "31"}

CITY_DEPT: dict[str, str] = {
    "paris": "75", "lyon": "69", "marseille": "13", "toulouse": "31",
    "bordeaux": "33", "nantes": "44", "lille": "59", "strasbourg": "67",
    "montpellier": "34", "rennes": "35", "grenoble": "38", "nice": "06",
    "thiais": "94", "créteil": "94", "vincennes": "94", "vitry-sur-seine": "94",
    "ivry-sur-seine": "94", "boulogne-billancourt": "92", "nanterre": "92",
    "issy-les-moulineaux": "92", "versailles": "78", "saint-denis": "93",
    "montreuil": "93", "metz": "57", "nancy": "54", "reims": "51",
    "dijon": "21", "caen": "14", "rouen": "76", "amiens": "80",
    "tours": "37", "angers": "49", "brest": "29", "le havre": "76",
    "clermont-ferrand": "63", "aix-en-provence": "13", "toulon": "83",
}

NAF_LABELS: dict[str, str] = {
    "62.01Z": "Développement logiciel",
    "62.02A": "Conseil IT / SSII",
    "62.02B": "Maintenance informatique",
    "62.03Z": "Infra & réseaux",
    "63.11Z": "Data / Hébergement",
    "62.09Z": "Services informatiques",
}

TRANCHE_LABELS: dict[str, str] = {
    "11": "10–19 salariés",
    "12": "20–49 salariés",
    "21": "50–99 salariés",
    "22": "100–199 salariés",
    "31": "200–249 salariés",
}


class CompanyOut(BaseModel):
    name: str
    siret: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    sector: Optional[str] = None
    sector_label: Optional[str] = None
    size_label: Optional[str] = None


class CoverLetterRequest(BaseModel):
    company_name: str
    company_address: Optional[str] = None
    sector_label: Optional[str] = None


async def _fetch_naf(client: httpx.AsyncClient, naf: str, dept: Optional[str]) -> list:
    all_results = []
    for page in [1, 2]:
        params: dict = {"activite_principale": naf, "per_page": 25, "page": page}
        if dept:
            params["departement"] = dept
        try:
            resp = await client.get(
                "https://recherche-entreprises.api.gouv.fr/search",
                params=params,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                all_results.extend(data.get("results", []))
                if len(data.get("results", [])) < 25:
                    break
            else:
                break
        except Exception as e:
            logger.warning(f"[Spontaneous] NAF {naf} p{page}: {e}")
            break
    return all_results


@router.get("/companies", response_model=List[CompanyOut])
async def find_pme_companies(
    city: str = Query(default="Paris"),
    limit: int = Query(default=30, le=50),
    current_user: User = Depends(get_current_user),
):
    dept = CITY_DEPT.get(city.lower().strip())

    async with httpx.AsyncClient(timeout=15) as client:
        batches = await asyncio.gather(
            *[_fetch_naf(client, naf, dept) for naf in IT_NAF_CODES],
            return_exceptions=True,
        )

    companies: list[CompanyOut] = []
    seen: set[str] = set()

    for naf, batch in zip(IT_NAF_CODES, batches):
        if isinstance(batch, Exception) or not isinstance(batch, list):
            continue
        for r in batch:
            siege = r.get("siege") or {}
            siret = siege.get("siret") or r.get("siren", "")
            if not siret or siret in seen:
                continue
            if r.get("categorie_entreprise") != "PME":
                continue
            tranche = siege.get("tranche_effectif_salarie") or r.get("tranche_effectif_salarie") or ""
            seen.add(siret)
            companies.append(CompanyOut(
                name=r.get("nom_complet") or r.get("nom_raison_sociale") or "Entreprise",
                siret=siret,
                address=siege.get("adresse"),
                city=siege.get("libelle_commune"),
                postal_code=siege.get("code_postal"),
                sector=naf,
                sector_label=NAF_LABELS.get(naf),
                size_label=TRANCHE_LABELS.get(tranche),
            ))

    return companies[:limit]


def _template_letter(name: str, company: str, sector: str, roles: str, skills: str, education: str, school: str) -> str:
    role_short = roles.split(",")[0].strip() if roles else "un poste en informatique"
    skill_list = [s.strip() for s in skills.split(",") if s.strip()][:3]
    skills_highlight = ", ".join(skill_list) if skill_list else "mes compétences techniques"
    return f"""Madame, Monsieur,

Actuellement en formation {education} à {school}, je me permets de vous adresser ma candidature spontanée pour {role_short} au sein de votre entreprise.

Votre activité dans le domaine {sector} correspond parfaitement à mon projet professionnel. Mes compétences en {skills_highlight} me permettraient de contribuer rapidement et efficacement à vos projets. Je suis rigoureux, motivé et désireux de mettre en pratique mes apprentissages dans un contexte professionnel stimulant.

L'alternance me semble être le cadre idéal pour allier formation théorique et expérience terrain. Je suis convaincu que rejoindre {company} me permettrait de développer mon expertise tout en apportant une réelle valeur ajoutée à votre équipe.

Dans l'attente de votre réponse, je reste disponible pour un entretien.
Cordialement,
{name}"""


@router.post("/cover-letter")
async def generate_cover_letter(
    data: CoverLetterRequest,
    current_user: User = Depends(get_current_user),
):
    skills_str = ", ".join(current_user.skills or []) or "compétences informatiques"
    roles_str = ", ".join(current_user.target_roles or []) or "poste en informatique"
    education = current_user.education_level or "Bac+2/Bac+3"
    school = current_user.school or "mon école"

    if settings.ANTHROPIC_API_KEY:
        prompt = f"""Rédige une lettre de motivation concise et professionnelle pour une candidature spontanée en alternance.

Entreprise : {data.company_name}
Adresse : {data.company_address or 'France'}
Secteur : {data.sector_label or 'informatique'}

Profil du candidat :
- Nom : {current_user.name}
- Formation : {education}
- École : {school}
- Compétences : {skills_str}
- Postes visés : {roles_str}

Règles strictes :
- Commence directement par "Madame, Monsieur,"
- 3 paragraphes maximum, ton professionnel mais naturel
- Personnalise en mentionnant le secteur de l'entreprise ({data.sector_label or 'IT'})
- Met en avant les compétences les plus pertinentes
- Termine par : "Dans l'attente de votre réponse, je reste disponible pour un entretien.\\nCordialement,\\n{current_user.name}"
- Pas d'objet, pas de coordonnées, juste le corps de la lettre"""

        try:
            import anthropic as _anthropic
            client = _anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            msg = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return {"cover_letter": msg.content[0].text.strip(), "company": data.company_name, "source": "ai"}
        except Exception as e:
            logger.warning(f"[Spontaneous] IA indisponible, fallback template: {e}")

    letter = _template_letter(
        name=current_user.name,
        company=data.company_name,
        sector=data.sector_label or "informatique",
        roles=roles_str,
        skills=skills_str,
        education=education,
        school=school,
    )
    return {"cover_letter": letter, "company": data.company_name, "source": "template"}
