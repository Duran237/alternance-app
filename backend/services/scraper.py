"""
Scrapers multi-sources avec Playwright (rendu JS) + APIs officielles.
Sources : HelloWork, Indeed, Welcome to the Jungle, APEC, France Travail API.
"""
import asyncio
import logging
from typing import Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TECH_KEYWORDS = [
    # Langages & dev
    "python", "bash", "powershell", "javascript", "typescript", "java", "c++", "rust", "go", "php",
    "react", "fastapi", "django", "flask", "sql", "nosql", "html", "css",

    # Réseau & infrastructure
    "réseau", "network", "tcp/ip", "dns", "dhcp", "vlan", "vpn", "mpls", "bgp", "ospf", "eigrp",
    "spanning tree", "routage", "commutation", "switching", "routing",
    "cisco", "juniper", "fortinet", "palo alto", "checkpoint", "mikrotik", "hp aruba",
    "wifi", "lan", "wan", "sd-wan", "fibre optique", "ipv6",
    "administrateur réseau", "admin réseau", "ingénieur réseau",

    # Systèmes
    "linux", "windows server", "ubuntu", "debian", "centos", "redhat", "rhel",
    "vmware", "vsphere", "esxi", "hyper-v", "proxmox", "virtualisation",
    "active directory", "ldap", "gpo", "ad", "exchange", "office 365", "m365",
    "administrateur système", "admin système", "admin sys", "sysadmin",
    "administrateur systèmes et réseaux", "infrastructure",

    # Cybersécurité
    "cybersécurité", "cybersecurity", "sécurité informatique", "sécurité réseau",
    "soc", "siem", "splunk", "ibm qradar", "microsoft sentinel",
    "firewall", "ids", "ips", "waf", "edr", "xdr", "antivirus", "endpoint",
    "pentest", "test d'intrusion", "ethical hacking", "red team", "blue team",
    "wireshark", "nmap", "metasploit", "burp suite", "kali linux", "nessus", "openvas",
    "iso 27001", "rgpd", "pci-dss", "anssi", "ssi", "risque", "audit sécurité",
    "zero trust", "iam", "pam", "gestion des identités",
    "threat intelligence", "vulnerability management", "ctf", "oscp", "ceh",
    "ccna", "ccnp", "comptia security+",

    # Cloud & DevOps
    "aws", "azure", "gcp", "cloud", "docker", "kubernetes", "ansible", "terraform",
    "ci/cd", "devops", "devsecops", "git", "jenkins", "gitlab",

    # Monitoring & supervision
    "zabbix", "nagios", "prometheus", "grafana", "supervision", "monitoring", "snmp",
    "prtg", "centreon",

    # Stockage & backup
    "san", "nas", "sauvegarde", "backup", "veeam",

    # IA & data
    "machine learning", "ia", "intelligence artificielle", "data",
    "microservices", "api",
]

# Codes ROME informatique/réseau/cybersécurité pour La Bonne Alternance
_ROME_IT = "M1805,M1806,M1801,M1802,M1810"

CITY_COORDS: dict[str, tuple[float, float]] = {
    "paris": (48.8566, 2.3522),
    "lyon": (45.7640, 4.8357),
    "marseille": (43.2965, 5.3698),
    "toulouse": (43.6047, 1.4442),
    "bordeaux": (44.8378, -0.5792),
    "nantes": (47.2184, -1.5536),
    "lille": (50.6292, 3.0573),
    "strasbourg": (48.5734, 7.7521),
    "montpellier": (43.6108, 3.8767),
    "rennes": (48.1173, -1.6778),
    "grenoble": (45.1885, 5.7245),
    "nice": (43.7102, 7.2620),
    "france": (48.8566, 2.3522),
}

# Codes INSEE pour La Bonne Alternance (insee = code commune)
CITY_INSEE: dict[str, str] = {
    "paris": "75056",
    "lyon": "69123",
    "marseille": "13055",
    "toulouse": "31555",
    "bordeaux": "33063",
    "nantes": "44109",
    "lille": "59350",
    "strasbourg": "67482",
    "montpellier": "34172",
    "rennes": "35238",
    "grenoble": "38185",
    "nice": "06088",
    "france": "75056",
}

PLAYWRIGHT_TIMEOUT = 25000


def _extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    return [kw for kw in TECH_KEYWORDS if kw in text_lower]


def _full_url(href: str, base: str) -> str:
    if not href:
        return ""
    return href if href.startswith("http") else base.rstrip("/") + "/" + href.lstrip("/")


# ── Playwright helper ─────────────────────────────────────────────────────────
async def _pw_get_html(url: str, wait_selector: Optional[str] = None, wait_seconds: float = 3.0) -> str:
    """Charge une page avec Playwright et retourne le HTML rendu."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                locale="fr-FR",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = await ctx.new_page()
            await page.goto(url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT)
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=10000)
                except Exception:
                    await asyncio.sleep(wait_seconds)
            else:
                await asyncio.sleep(wait_seconds)
            html = await page.content()
            await browser.close()
            return html
    except Exception as e:
        logger.error(f"[Playwright] Erreur sur {url[:60]}: {e}")
        return ""


# ── 1. HelloWork ─────────────────────────────────────────────────────────────
async def scrape_hellowork(keywords: str, location: str = "France", company: str = "") -> list[dict]:
    jobs = []
    kw_full = f"{keywords} {company}".strip() if company else keywords
    query = kw_full.replace(" ", "+")
    url = f"https://www.hellowork.com/fr-fr/emploi/recherche.html?k={query}&l={location}&c=Alternance"

    try:
        html = await _pw_get_html(url, wait_selector='[data-cy="serpCard"]')
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        cards = soup.select('[data-cy="serpCard"]')

        for card in cards[:25]:
            title_el = card.select_one('[data-cy="offerTitle"]')
            location_el = card.select_one('[data-cy="localisationCard"]')
            salary_el = card.select_one('[data-cy="salaryCard"]')

            if not title_el:
                continue

            # Titre et entreprise séparés par | dans le même lien
            raw = title_el.get_text("|", strip=True)
            parts = [p.strip() for p in raw.split("|") if p.strip()]
            title = parts[0] if parts else "Poste non précisé"
            company = parts[1] if len(parts) > 1 else "Entreprise"

            href = title_el.get("href", "")
            full_url = _full_url(href, "https://www.hellowork.com")
            if not full_url:
                continue

            desc = card.get_text(" ", strip=True)
            jobs.append({
                "title": title,
                "company": company,
                "location": location_el.get_text(strip=True) if location_el else location,
                "salary": salary_el.get_text(strip=True) if salary_el else None,
                "description": desc[:1200],
                "skills_required": _extract_skills(desc),
                "url": full_url,
                "source": "hellowork",
                "contract_type": "Alternance",
                "level": None,
            })

    except Exception as e:
        logger.error(f"[HelloWork] {e}")

    logger.info(f"[HelloWork] {len(jobs)} offres")
    return jobs


# ── 2. Indeed ────────────────────────────────────────────────────────────────
async def scrape_indeed(keywords: str, location: str = "France", company: str = "") -> list[dict]:
    jobs = []
    query = keywords.replace(" ", "+")
    if company:
        url = f"https://fr.indeed.com/jobs?q={query}+alternance&l={location}&rbc={company.replace(' ', '+')}&rbt=EMPLOYER&sort=date"
    else:
        url = f"https://fr.indeed.com/jobs?q={query}+alternance&l={location}&sort=date"

    try:
        html = await _pw_get_html(url, wait_selector=".job_seen_beacon, .jobsearch-ResultsList")
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        cards = soup.select(".job_seen_beacon") or soup.select(".result")

        for card in cards[:20]:
            title_el = card.select_one("h2.jobTitle span[title], h2.jobTitle span, [data-testid='jobTitle']")
            company_el = card.select_one("[data-testid='company-name'], .companyName")
            location_el = card.select_one("[data-testid='text-location'], .companyLocation")
            salary_el = card.select_one(".salary-snippet-container, .salaryText")
            link_el = card.select_one("a[data-jk]") or card.select_one("a[href*='/viewjob']")

            if not title_el:
                continue

            job_id = link_el.get("data-jk", "") if link_el else ""
            href = link_el.get("href", "") if link_el else ""
            if job_id:
                full_url = f"https://fr.indeed.com/viewjob?jk={job_id}"
            elif href:
                full_url = _full_url(href, "https://fr.indeed.com")
            else:
                continue

            desc = card.get_text(" ", strip=True)
            jobs.append({
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Entreprise",
                "location": location_el.get_text(strip=True) if location_el else location,
                "salary": salary_el.get_text(strip=True) if salary_el else None,
                "description": desc[:1200],
                "skills_required": _extract_skills(desc),
                "url": full_url,
                "source": "indeed",
                "contract_type": "Alternance",
                "level": None,
            })

    except Exception as e:
        logger.error(f"[Indeed] {e}")

    logger.info(f"[Indeed] {len(jobs)} offres")
    return jobs


# ── 3. Welcome to the Jungle ─────────────────────────────────────────────────
async def scrape_wttj(keywords: str, location: str = "France") -> list[dict]:
    jobs = []
    query = keywords.replace(" ", "%20")
    loc = location if location.lower() != "france" else "France"
    url = (
        f"https://www.welcometothejungle.com/fr/jobs"
        f"?query={query}&aroundQuery={loc}"
        f"&refinementList[contract_type_names][0]=Alternance"
    )

    try:
        html = await _pw_get_html(url, wait_selector="[data-testid='job-card'], .ais-Hits-item")
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        cards = (
            soup.select("[data-testid='search-results-list-item-wrapper']")
            or soup.select("[data-testid='job-card']")
            or soup.select(".ais-Hits-item")
            or soup.select("li[class*='sc-']")
        )

        for card in cards[:20]:
            title_el = card.select_one("h2, h3, [data-testid='job-title'], [class*='Title']")
            company_el = card.select_one("[data-testid='company-name'], [class*='company']")
            location_el = card.select_one("[data-testid='job-location'], [class*='location']")
            link_el = card.select_one("a[href*='/jobs/']") or card.select_one("a[href]")

            if not (title_el and link_el):
                continue

            href = link_el["href"]
            full_url = _full_url(href, "https://www.welcometothejungle.com")
            desc = card.get_text(" ", strip=True)

            jobs.append({
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Entreprise",
                "location": location_el.get_text(strip=True) if location_el else location,
                "salary": None,
                "description": desc[:1200],
                "skills_required": _extract_skills(desc),
                "url": full_url,
                "source": "welcome_to_the_jungle",
                "contract_type": "Alternance",
                "level": None,
            })

    except Exception as e:
        logger.error(f"[WTTJ] {e}")

    logger.info(f"[WTTJ] {len(jobs)} offres")
    return jobs


# ── 4. APEC ─────────────────────────────────────────────────────────────────
async def scrape_apec(keywords: str, location: str = "France") -> list[dict]:
    jobs = []
    query = keywords.replace(" ", "+")
    url = f"https://www.apec.fr/candidat/recherche-emploi.html/emploi?motsCles={query}&typeContrat=85"

    try:
        html = await _pw_get_html(url, wait_selector=".job-item, .result-item, [class*='offer']")
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        cards = (
            soup.select(".job-item")
            or soup.select("article[class*='offer']")
            or soup.select("[class*='job-card']")
        )

        for card in cards[:20]:
            title_el = card.select_one("h2, h3, [class*='title']")
            company_el = card.select_one("[class*='company'], [class*='entreprise']")
            location_el = card.select_one("[class*='location'], [class*='lieu']")
            link_el = card.select_one("a[href*='/emploi/']") or card.select_one("a[href]")

            if not title_el:
                continue

            href = link_el["href"] if link_el else ""
            full_url = _full_url(href, "https://www.apec.fr")
            if not full_url:
                continue

            desc = card.get_text(" ", strip=True)
            jobs.append({
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Entreprise",
                "location": location_el.get_text(strip=True) if location_el else location,
                "salary": None,
                "description": desc[:1200],
                "skills_required": _extract_skills(desc),
                "url": full_url,
                "source": "apec",
                "contract_type": "Alternance",
                "level": None,
            })

    except Exception as e:
        logger.error(f"[APEC] {e}")

    logger.info(f"[APEC] {len(jobs)} offres")
    return jobs


# ── 5. France Travail API (clés gratuites sur francetravail.io) ───────────────
async def scrape_france_travail(
    keywords: str,
    location: str = "France",
    client_id: str = "",
    client_secret: str = "",
    target_company: str = "",
) -> list[dict]:
    if not (client_id and client_secret):
        return []

    jobs = []
    DEPT_MAP = {
        "paris": "75", "lyon": "69", "marseille": "13", "toulouse": "31",
        "bordeaux": "33", "nantes": "44", "lille": "59", "strasbourg": "67",
        "montpellier": "34", "rennes": "35", "grenoble": "38", "nice": "06",
    }

    # Inclure "alternance" dans la recherche — l'API v2 n'a plus de code typeContrat dédié
    search_kw = f"alternance {keywords}"
    if target_company:
        search_kw = f"alternance {keywords} {target_company}"

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            token_resp = await client.post(
                "https://entreprise.francetravail.fr/connexion/oauth2/access_token",
                params={"realm": "/partenaire"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": "api_offresdemploiv2 o2dsoffre",
                },
            )
            token = token_resp.json().get("access_token")
            if not token:
                logger.warning("[FranceTravail] Impossible d'obtenir un token")
                return []

            params: dict = {"motsCles": search_kw, "range": "0-49"}
            dept = DEPT_MAP.get(location.lower())
            if dept:
                params["departement"] = dept

            resp = await client.get(
                "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
                params=params,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            )
            if resp.status_code not in (200, 206):
                logger.warning(f"[FranceTravail] {resp.status_code}: {resp.text[:200]}")
                return []
            data = resp.json()

        for offer in data.get("resultats", [])[:30]:
            desc = offer.get("description", "") or ""
            company = (offer.get("entreprise") or {}).get("nom") or "Entreprise"
            offer_id = offer.get("id", "")
            jobs.append({
                "title": offer.get("intitule", ""),
                "company": company,
                "location": (offer.get("lieuTravail") or {}).get("libelle") or location,
                "salary": (offer.get("salaire") or {}).get("libelle"),
                "description": desc[:1200],
                "skills_required": _extract_skills(desc),
                "url": f"https://www.francetravail.fr/offres/recherche/detail/{offer_id}",
                "source": "france_travail",
                "contract_type": "Alternance",
                "level": None,
            })

    except Exception as e:
        logger.error(f"[FranceTravail] {e}")

    logger.info(f"[FranceTravail] {len(jobs)} offres")
    return jobs


# ── 6. La Bonne Alternance (API officielle gouvernementale) ──────────────────
async def scrape_lba(keywords: str, location: str = "France") -> list[dict]:
    jobs = []
    loc_key = location.lower()
    coords = CITY_COORDS.get(loc_key, CITY_COORDS["france"])
    insee = CITY_INSEE.get(loc_key, CITY_INSEE["france"])
    lat, lon = coords

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://labonnealternance.apprentissage.beta.gouv.fr/api/v1/jobsEtFormations",
                params={
                    "caller": "alternance_app",
                    "insee": insee,
                    "latitude": lat,
                    "longitude": lon,
                    "radius": 60,
                    "romes": _ROME_IT,
                },
            )
            if resp.status_code != 200:
                logger.warning(f"[LBA] Status {resp.status_code}: {resp.text[:200]}")
                return []
            data = resp.json()

        jobs_data = data.get("jobs") or {}
        raw_jobs = []
        for key in ("peJobs", "partnerJobs", "matchas"):
            section = jobs_data.get(key) or {}
            results = section.get("results") or []
            raw_jobs.extend(results)

        for offer in raw_jobs[:30]:
            title = (offer.get("title") or "").strip()
            if not title:
                continue
            company_obj = offer.get("company") or {}
            company = company_obj.get("name") or "Entreprise"
            if not company or company == "":
                company = "Entreprise"
            place_obj = offer.get("place") or {}
            offer_loc = place_obj.get("city") or place_obj.get("address") or location
            desc_raw = offer.get("job", {}).get("description") or offer.get("description") or ""
            # Strip HTML tags if present
            import re as _re
            desc = _re.sub(r"<[^>]+>", " ", str(desc_raw)).strip()

            # URL: direct url field, or contact.url, or build from id
            url = (
                offer.get("url")
                or (offer.get("contact") or {}).get("url")
                or ""
            )
            if not url and offer.get("id"):
                url = f"https://labonnealternance.apprentissage.beta.gouv.fr/recherche-emploi?display=list&page=1&job={offer['id']}"
            if not url:
                continue

            jobs.append({
                "title": title,
                "company": company,
                "location": offer_loc,
                "salary": None,
                "description": desc[:1200],
                "skills_required": _extract_skills(desc),
                "url": url,
                "source": "la_bonne_alternance",
                "contract_type": "Alternance",
                "level": None,
            })

    except Exception as e:
        logger.error(f"[LBA] {e}")

    logger.info(f"[LBA] {len(jobs)} offres")
    return jobs


# ── 7. L'Etudiant Emploi (API interne tRPC) ───────────────────────────────────
async def scrape_letudiant(keywords: str, location: str = "France") -> list[dict]:
    jobs = []
    ALTERNANCE_CONTRACT_ID = "627d164572f9aba0dccf93e7"
    MEDIA_ID = "66229d6f878dc9f2bf192806"

    import json as _json

    input_data = _json.dumps({
        "0": {
            "json": {
                "limit": 30,
                "media_id": MEDIA_ID,
                "language": "fr",
                "pertinence": True,
                "contracts": [ALTERNANCE_CONTRACT_ID],
                "direction": "forward",
                "search": keywords,
            }
        }
    })

    try:
        async with httpx.AsyncClient(timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://jobs-stages.letudiant.fr/",
        }) as client:
            resp = await client.get(
                "https://jobs-stages.letudiant.fr/api/trpc/jobInfinite.getMediaJobsInfinite",
                params={"batch": "1", "input": input_data},
            )
            if resp.status_code != 200:
                logger.warning(f"[Etudiant] Status {resp.status_code}: {resp.text[:200]}")
                return []
            data = resp.json()

        results = []
        if isinstance(data, list) and data:
            results = data[0].get("result", {}).get("data", {}).get("json", {}).get("items", [])

        for offer in results[:25]:
            title = offer.get("name", "").strip()
            if not title:
                continue
            company = offer.get("companyName") or "Entreprise"
            loc_obj = offer.get("location") or {}
            if isinstance(loc_obj, dict):
                offer_loc = loc_obj.get("city") or loc_obj.get("administrative_area_department") or location
            else:
                offer_loc = str(loc_obj) if loc_obj else location
            desc = str(offer.get("aiContent") or offer.get("description") or "")
            public_id = offer.get("public_id") or offer.get("id") or ""
            url = f"https://jobs-stages.letudiant.fr/offres/emploi-{public_id}" if public_id else ""
            if not url:
                continue
            salary_obj = offer.get("salary")
            salary = str(salary_obj) if salary_obj else None

            jobs.append({
                "title": title,
                "company": company,
                "location": offer_loc,
                "salary": salary,
                "description": desc[:1200],
                "skills_required": _extract_skills(desc),
                "url": url,
                "source": "letudiant",
                "contract_type": "Alternance",
                "level": None,
            })

    except Exception as e:
        logger.error(f"[Etudiant] {e}")

    logger.info(f"[Etudiant] {len(jobs)} offres")
    return jobs


# ── 8. JobTeaser (offres directes des entreprises partenaires) ────────────────
async def scrape_jobteaser(keywords: str, location: str = "France") -> list[dict]:
    jobs = []
    query = keywords.replace(" ", "+")
    url = (
        f"https://www.jobteaser.com/fr/job-offers"
        f"?contract_type[]=apprenticeship&search={query}"
    )

    try:
        html = await _pw_get_html(url, wait_selector="[data-testid='job-card'], article[class*='JobCard'], [class*='job-card']")
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        # JobTeaser uses different possible selectors
        cards = (
            soup.select("[data-testid='job-card']")
            or soup.select("article[class*='JobCard']")
            or soup.select("li[class*='job']")
            or soup.select("[class*='JobOfferCard']")
        )

        for card in cards[:20]:
            title_el = card.select_one("h2, h3, [class*='title'], [class*='Title']")
            company_el = card.select_one("[class*='company'], [class*='Company'], [class*='organization']")
            location_el = card.select_one("[class*='location'], [class*='Location'], [class*='city']")
            link_el = card.select_one("a[href*='/job-offers/'], a[href*='/offres/'], a[href]")

            if not title_el:
                continue

            href = link_el["href"] if link_el else ""
            full_url = _full_url(href, "https://www.jobteaser.com")
            if not full_url:
                continue

            desc = card.get_text(" ", strip=True)
            jobs.append({
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "Entreprise",
                "location": location_el.get_text(strip=True) if location_el else location,
                "salary": None,
                "description": desc[:1200],
                "skills_required": _extract_skills(desc),
                "url": full_url,
                "source": "jobteaser",
                "contract_type": "Alternance",
                "level": None,
            })

    except Exception as e:
        logger.error(f"[JobTeaser] {e}")

    logger.info(f"[JobTeaser] {len(jobs)} offres")
    return jobs


# ── 9. SmartRecruiters — offres directes d'entreprises ───────────────────────
# Entreprises françaises connues utilisant SmartRecruiters (API publique)
_SR_COMPANIES: dict[str, str] = {
    "Decathlon": "Decathlon",
    "Saint-Gobain": "SaintGobain",
    "Sopra Steria": "SopraSteria",
    "Worldline": "Worldline",
    "Michelin": "Michelin",
    "Renault": "Renault",
    "Stellantis": "Stellantis",
    "Schneider Electric": "SchneiderElectric",
    "Air France": "AirFrance",
    "Dassault Systèmes": "DassaultSystemes",
    "Amadeus": "Amadeus",
    "CGI": "CGI",
    "Atos": "Atos",
    "Ericsson": "Ericsson",
    "Nokia": "Nokia",
}

# Contrats SmartRecruiters correspondant à l'alternance
_SR_APPRENTICESHIP_TYPES = {"intern", "internship", "apprenticeship", "alternance"}


async def scrape_smartrecruiters(
    keywords: str,
    target_company: str = "",
) -> list[dict]:
    """Scrape les offres d'alternance via l'API publique SmartRecruiters."""
    jobs = []
    kw_lower = keywords.lower()

    # Si une entreprise cible est spécifiée, ne chercher que chez elle (si connue)
    if target_company:
        slug = _SR_COMPANIES.get(target_company) or target_company.replace(" ", "")
        slugs_to_search = {target_company: slug}
    else:
        slugs_to_search = _SR_COMPANIES

    async def fetch_company(display_name: str, slug: str) -> list[dict]:
        results = []
        try:
            async with httpx.AsyncClient(timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "application/json",
            }) as client:
                resp = await client.get(
                    f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
                    params={"limit": 100, "q": keywords},
                )
                if resp.status_code != 200:
                    return []
                data = resp.json()

            for offer in data.get("content", []):
                # Filtre alternance/stage
                type_id = (offer.get("typeOfEmployment") or {}).get("id", "").lower()
                name_low = offer.get("name", "").lower()
                if type_id not in _SR_APPRENTICESHIP_TYPES and "alternance" not in name_low and "apprenti" not in name_low:
                    continue

                loc_obj = offer.get("location") or {}
                city = loc_obj.get("city") or loc_obj.get("country") or "France"
                offer_id = offer.get("id") or ""
                url = f"https://jobs.smartrecruiters.com/{slug}/{offer_id}" if offer_id else ""
                if not url:
                    url = offer.get("applyUrl") or ""
                if not url:
                    continue

                desc = offer.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text") or ""
                results.append({
                    "title": offer.get("name", ""),
                    "company": display_name,
                    "location": city,
                    "salary": None,
                    "description": desc[:1200],
                    "skills_required": _extract_skills(desc),
                    "url": url,
                    "source": "entreprise_directe",
                    "contract_type": "Alternance",
                    "level": None,
                })
        except Exception as e:
            logger.debug(f"[SR] {display_name}: {e}")
        return results

    tasks = [fetch_company(name, slug) for name, slug in slugs_to_search.items()]
    batches = await asyncio.gather(*tasks, return_exceptions=True)
    for b in batches:
        if isinstance(b, list):
            jobs.extend(b)

    logger.info(f"[SmartRecruiters] {len(jobs)} offres directes")
    return jobs


# ── Orchestrateur ─────────────────────────────────────────────────────────────
async def scrape_all(
    keywords: str,
    location: str = "France",
    ft_client_id: str = "",
    ft_client_secret: str = "",
    target_company: str = "",
) -> list[dict]:
    """Lance tous les scrapers en parallèle et déduplique par URL."""

    # Si une entreprise cible est spécifiée, on l'ajoute aux mots-clés pour tous les scrapers
    search_kw = f"{keywords} {target_company}".strip() if target_company else keywords

    # Scrapers Playwright (séquentiel — un seul navigateur à la fois)
    pw_results = []
    for scraper in [scrape_hellowork, scrape_wttj, scrape_apec, scrape_jobteaser]:
        try:
            result = await scraper(search_kw, location)
            pw_results.append(result)
        except Exception as e:
            logger.error(f"[scrape_all] {scraper.__name__}: {e}")
            pw_results.append([])

    # Indeed séparé : supporte le filtre entreprise natif
    try:
        indeed_result = await scrape_indeed(search_kw, location, target_company)
        pw_results.append(indeed_result)
    except Exception as e:
        logger.error(f"[scrape_all] scrape_indeed: {e}")
        pw_results.append([])

    # APIs légères (parallèle — pas de navigateur)
    api_results = await asyncio.gather(
        scrape_lba(search_kw, location),
        scrape_letudiant(search_kw, location),
        scrape_france_travail(keywords, location, ft_client_id, ft_client_secret, target_company),
        scrape_smartrecruiters(keywords, target_company),
        return_exceptions=True,
    )
    api_batches = [r if isinstance(r, list) else [] for r in api_results]

    seen_urls: set[str] = set()
    merged: list[dict] = []

    for batch in pw_results + api_batches:
        for job in batch:
            url = job.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(job)

    sources = set(j["source"] for j in merged)
    logger.info(f"[scrape_all] {len(merged)} offres uniques | sources : {sources}")
    return merged
