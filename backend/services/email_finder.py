import re
import logging
import httpx

from config import settings

logger = logging.getLogger(__name__)

HR_PATTERNS = ["rh", "recrutement", "contact", "jobs", "carriere", "candidature", "emploi", "talent"]


def _normalize_domain(company_name: str) -> str:
    name = company_name.lower()
    for suffix in [
        " sas", " sarl", " sa ", " sasu", " sci", " snc", " eurl",
        " groupe", " group", " france", " paris", " lyon", " informatique",
        " solutions", " consulting", " technologies", " services", " systems",
    ]:
        name = name.replace(suffix, " ")
    name = re.sub(r"[^a-z0-9\s]", "", name).strip()
    name = re.sub(r"\s+", "-", name).strip("-")
    return name


async def find_company_domain(company_name: str) -> str | None:
    slug = _normalize_domain(company_name)
    if not slug:
        return None
    async with httpx.AsyncClient(timeout=5) as client:
        for domain in [f"{slug}.fr", f"{slug}.com"]:
            try:
                r = await client.head(f"https://{domain}", follow_redirects=True)
                if r.status_code < 400:
                    return domain
            except Exception:
                pass
    return None


async def _hunter_search(domain: str) -> list[dict]:
    """Interroge Hunter.io pour obtenir des emails vérifiés sur un domaine."""
    if not settings.HUNTER_API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": settings.HUNTER_API_KEY, "limit": 5},
            )
            if r.status_code != 200:
                return []
            data = r.json().get("data", {})
            emails = data.get("emails", [])
            results = []
            for e in emails:
                value = e.get("value", "")
                if not value:
                    continue
                confidence = e.get("confidence", 0)
                position = e.get("position") or e.get("department") or "contact"
                results.append({
                    "email": value,
                    "pattern": position,
                    "confidence": f"{confidence}%",
                    "source": "hunter",
                })
            logger.info(f"[Hunter] {domain} → {[e['email'] for e in results]}")
            return results
    except Exception as ex:
        logger.warning(f"[Hunter] Erreur pour {domain}: {ex}")
        return []


def _guess_hr_emails(domain: str, limit: int = 3) -> list[dict]:
    return [
        {"email": f"{p}@{domain}", "pattern": p, "confidence": "estimé", "source": "pattern"}
        for p in HR_PATTERNS[:limit]
    ]


async def find_hr_emails(company_name: str, siret: str | None = None) -> list[dict]:
    domain = await find_company_domain(company_name)
    if not domain:
        slug = _normalize_domain(company_name)
        domain = f"{slug}.fr" if slug else None
    if not domain:
        return []

    # Hunter.io en priorité (emails vérifiés), sinon patterns devinés
    emails = await _hunter_search(domain)
    if not emails:
        emails = _guess_hr_emails(domain, limit=3)

    logger.info(f"[EmailFinder] {company_name} → {domain} → {[e['email'] for e in emails]}")
    return emails
