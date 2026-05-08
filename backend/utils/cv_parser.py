import re
from pathlib import Path

import pdfplumber


TECH_SKILLS = [
    # Dev
    "python", "javascript", "typescript", "react", "node.js", "sql", "postgresql",
    "mysql", "mongodb", "docker", "kubernetes", "linux", "bash", "powershell", "git",
    "aws", "azure", "gcp", "fastapi", "django", "flask", "java", "c++", "rust", "php",
    "ansible", "terraform", "ci/cd", "jenkins", "github actions", "gitlab",
    # Réseau
    "cisco", "juniper", "fortinet", "palo alto", "checkpoint", "mikrotik",
    "vlan", "vpn", "bgp", "ospf", "tcp/ip", "dns", "dhcp", "wifi", "sd-wan",
    "firewall", "routage", "switching", "réseau", "network", "lan", "wan",
    # Système
    "active directory", "windows server", "vmware", "vsphere", "hyper-v", "proxmox",
    "ubuntu", "debian", "centos", "redhat", "ldap", "office 365",
    "virtualisation", "sysadmin",
    # Cybersécurité
    "cybersecurity", "cybersécurité", "soc", "siem", "splunk", "sentinel",
    "wireshark", "nmap", "metasploit", "burp suite", "kali", "nessus",
    "pentest", "iso 27001", "rgpd", "ids", "ips", "waf", "edr", "xdr",
    "threat intelligence", "zero trust", "iam", "oscp", "ccna", "ccnp",
    # Monitoring
    "zabbix", "nagios", "prometheus", "grafana", "prtg", "centreon", "snmp",
]


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text.strip()


def extract_skills_from_text(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill in TECH_SKILLS:
        if skill in text_lower:
            found.append(skill)
    return list(set(found))


def parse_cv(pdf_path: str) -> dict:
    text = extract_text_from_pdf(pdf_path)
    skills = extract_skills_from_text(text)

    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text)
    phone_match = re.search(r"(\+33|0)[1-9][\s.-]?(\d{2}[\s.-]?){4}", text)
    github_match = re.search(r"github\.com/[\w-]+", text)
    linkedin_match = re.search(r"linkedin\.com/in/[\w-]+", text)

    return {
        "text": text,
        "skills": skills,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "github": f"https://{github_match.group(0)}" if github_match else None,
        "linkedin": f"https://{linkedin_match.group(0)}" if linkedin_match else None,
    }
