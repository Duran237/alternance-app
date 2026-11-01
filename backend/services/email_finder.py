import re
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)

# Patterns RH les plus courants en France
HR_PATTERNS = ["rh", "recrutement", "contact", "jobs", "carriere", "candidature", "emploi", "talent"]


def _normalize_domain(company_name: str) -> str:
    name = company_name.lower()
    # Supprimer formes juridiques courantes
    for suffix in [
        " sas", " sarl", " sa ", " sasu", " sci", " snc", " eurl",
        " groupe", " group", " france", " paris", " lyon", " informatique",
        " solutions", " consulting", " technologies", " services", " systems",
    ]:
        name = name.replace(suffix, " ")
    # Garder lettres, chiffres, espaces
    name = re.sub(r"[^a-z0-9\s]", "", name).strip()
    name = re.sub(r"\s+", "-", name).strip("-")
    return name


async def find_company_domain(company_name: str, siret: str | None = None) -> str | None:
    """Tente de trouver le domaine web d'une entreprise via recherche Google."""
    slug = _normalize_domain(company_name)
    if not slug:
        return None

    candidates = [f"{slug}.fr", f"{slug}.com"]

    async with httpx.AsyncClient(timeout=5) as client:
        for domain in candidates:
            try:
                r = await client.head(f"https://{domain}", follow_redirects=True)
                if r.status_code < 400:
                    return domain
            except Exception:
                pass
    return None


def guess_hr_emails(domain: str, limit: int = 3) -> list[dict]:
    """Génère des adresses email RH probables pour un domaine donné."""
    return [
        {
            "email": f"{pattern}@{domain}",
            "pattern": pattern,
            "confidence": "probable",
            "source": "pattern",
        }
        for pattern in HR_PATTERNS[:limit]
    ]


async def find_hr_emails(company_name: str, siret: str | None = None) -> list[dict]:
    """Point d'entrée principal : trouve des emails RH probables pour une entreprise."""
    domain = await find_company_domain(company_name, siret)
    if not domain:
        # Fallback : construire un domaine probable sans vérification
        slug = _normalize_domain(company_name)
        if slug:
            domain = f"{slug}.fr"
        else:
            return []

    emails = guess_hr_emails(domain, limit=3)
    logger.info(f"[EmailFinder] {company_name} → {domain} → {[e['email'] for e in emails]}")
    return emails
