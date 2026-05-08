"""
Cherche l'email de contact du recruteur dans la description ou la page complète de l'offre.
"""
import re
import logging
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Domaines génériques à exclure (pas des emails de recruteurs)
_EXCLUDED_DOMAINS = {
    "example.com", "gmail.com", "yahoo.fr", "yahoo.com", "hotmail.com",
    "hellowork.com", "indeed.com", "welcometothejungle.com", "apec.fr",
    "francetravail.fr", "pole-emploi.fr", "linkedin.com", "sentry.io",
    "wixpress.com", "w3.org", "schema.org",
}

_EMAIL_RE = re.compile(r"[\w.+-]+@([\w-]+\.)+[a-z]{2,}", re.IGNORECASE)


def _extract_email(text: str) -> str | None:
    matches = _EMAIL_RE.findall(text)
    # findall avec groupe capturant retourne les groupes — on reparse
    for m in _EMAIL_RE.finditer(text):
        email = m.group(0).lower()
        domain = email.split("@")[1]
        if domain not in _EXCLUDED_DOMAINS and not domain.startswith("no-reply"):
            return email
    return None


def find_email_in_description(description: str) -> str | None:
    """Cherche un email de contact dans la description de l'offre."""
    if not description:
        return None
    return _extract_email(description)


async def find_email_on_job_page(url: str) -> str | None:
    """Charge la page de l'offre et cherche un email de contact."""
    if not url:
        return None
    try:
        async with httpx.AsyncClient(
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.text, "lxml")
            # Chercher dans les balises mailto
            for a in soup.select("a[href^='mailto:']"):
                href = a.get("href", "").replace("mailto:", "").strip()
                email = _extract_email(href) or _extract_email(a.get_text())
                if email:
                    return email
            # Chercher dans le texte brut
            return _extract_email(soup.get_text())
    except Exception as e:
        logger.warning(f"[ContactFinder] Erreur sur {url[:60]}: {e}")
        return None
