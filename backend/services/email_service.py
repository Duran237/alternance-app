import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from config import settings

logger = logging.getLogger(__name__)


def _can_send() -> bool:
    return bool(settings.SMTP_USER and settings.SMTP_PASSWORD)


def _smtp_connect():
    """Connexion SMTP compatible Gmail (SSL 465) et Outlook/autre (STARTTLS 587)."""
    host = settings.SMTP_HOST
    port = settings.SMTP_PORT
    if port == 465:
        server = smtplib.SMTP_SSL(host, port)
    else:
        server = smtplib.SMTP(host, port)
        server.ehlo()
        server.starttls()
        server.ehlo()
    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    return server


def _send(msg) -> bool:
    with _smtp_connect() as server:
        server.sendmail(settings.SMTP_USER, msg["To"], msg.as_string())
    return True


def send_otp_email(to_email: str, user_name: str, otp_code: str) -> bool:
    if not _can_send():
        return False
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
      <div style="background: #2563eb; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 20px;">Vérifie ton email</h1>
      </div>
      <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p>Bonjour <strong>{user_name}</strong>,</p>
        <p>Voici ton code de vérification :</p>
        <div style="text-align: center; margin: 24px 0;">
          <span style="font-size: 40px; font-weight: bold; letter-spacing: 12px; color: #2563eb; background: #eff6ff; padding: 16px 24px; border-radius: 12px; display: inline-block;">{otp_code}</span>
        </div>
        <p style="color: #6b7280; font-size: 13px;">Ce code expire dans <strong>10 minutes</strong>.</p>
      </div>
    </div>
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{otp_code} — Code de vérification Alternance App"
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))
        _send(msg)
        logger.info(f"[Email] OTP envoyé à {to_email}")
        return True
    except Exception as e:
        logger.error(f"[Email] Erreur OTP : {e}")
        return False


def send_welcome_email(to_email: str, user_name: str) -> bool:
    if not _can_send():
        return False
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #2563eb; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 22px;">Bienvenue sur Alternance App</h1>
      </div>
      <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p>Bonjour <strong>{user_name}</strong>,</p>
        <p>Ton compte a bien été créé. L'app va t'aider à :</p>
        <ul style="color: #374151; line-height: 2;">
          <li>Trouver des offres d'alternance en temps réel</li>
          <li>Générer des lettres de motivation personnalisées</li>
          <li>Envoyer des candidatures directement aux recruteurs</li>
          <li>Suivre toutes tes candidatures au même endroit</li>
        </ul>
        <p style="margin-top: 16px;"><strong>Prochaine étape :</strong> upload ton CV dans ton profil.</p>
        <p style="color: #6b7280; font-size: 13px; margin-top: 24px;">— Alternance App</p>
      </div>
    </div>
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Bienvenue sur Alternance App !"
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))
        _send(msg)
        logger.info(f"[Email] Bienvenue envoyé à {to_email}")
        return True
    except Exception as e:
        logger.error(f"[Email] Erreur bienvenue : {e}")
        return False


def send_application_confirmation(
    to_email: str, user_name: str, job_title: str,
    company: str, job_url: str, cover_letter: str = "",
) -> bool:
    if not _can_send():
        return False
    letter_block = (
        f'<div style="margin-top:24px;"><h3 style="color:#374151;">Ta lettre de motivation :</h3>'
        f'<div style="background:white;border:1px solid #e5e7eb;border-radius:8px;padding:16px;'
        f'white-space:pre-line;font-size:14px;line-height:1.6;">{cover_letter}</div></div>'
        if cover_letter else ""
    )
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <div style="background: #2563eb; padding: 24px; border-radius: 8px 8px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 20px;">Candidature enregistrée</h1>
      </div>
      <div style="background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 8px 8px;">
        <p>Bonjour <strong>{user_name}</strong>,</p>
        <div style="background:white;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin:16px 0;">
          <p style="margin:0;"><strong>Poste :</strong> {job_title}</p>
          <p style="margin:8px 0 0;"><strong>Entreprise :</strong> {company}</p>
        </div>
        <a href="{job_url}" style="display:inline-block;background:#2563eb;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">
          Postuler sur le site de l'offre
        </a>
        {letter_block}
        <p style="color:#6b7280;font-size:13px;margin-top:24px;">— Alternance App</p>
      </div>
    </div>
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Candidature — {job_title} chez {company}"
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))
        _send(msg)
        return True
    except Exception as e:
        logger.error(f"[Email] Erreur confirmation : {e}")
        return False


def send_real_application(
    recruiter_email: str, user_name: str, user_email: str,
    job_title: str, company: str, cover_letter: str, cv_path: str = "",
) -> bool:
    if not _can_send():
        return False
    body = f"{cover_letter}\n\n---\n{user_name}\n{user_email}"
    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"Candidature alternance – {job_title} – {user_name}"
        msg["From"] = f"{user_name} <{settings.SMTP_USER}>"
        msg["To"] = recruiter_email
        msg["Reply-To"] = user_email
        msg.attach(MIMEText(body, "plain", "utf-8"))
        if cv_path and os.path.exists(cv_path):
            with open(cv_path, "rb") as f:
                part = MIMEBase("application", "pdf")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="CV_{user_name.replace(" ", "_")}.pdf"')
                msg.attach(part)
        with _smtp_connect() as server:
            server.sendmail(settings.SMTP_USER, recruiter_email, msg.as_string())
        logger.info(f"[Email] Candidature envoyée à {recruiter_email}")
        return True
    except Exception as e:
        logger.error(f"[Email] Erreur candidature : {e}")
        return False
