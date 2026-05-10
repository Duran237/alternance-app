import logging
import os

from config import settings

logger = logging.getLogger(__name__)

FROM_EMAIL = "Alternance App <onboarding@resend.dev>"


def _can_send() -> bool:
    return bool(settings.RESEND_API_KEY and settings.RESEND_API_KEY.startswith("re_"))


def _send_email(to: str, subject: str, html: str) -> bool:
    if not _can_send():
        logger.warning(f"[Email] RESEND_API_KEY non configuré — email non envoyé à {to}")
        return False
    try:
        import resend
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": FROM_EMAIL,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        logger.info(f"[Email] Envoyé à {to} : {subject}")
        return True
    except Exception as e:
        logger.error(f"[Email] Erreur : {e}")
        return False


def send_otp_email(to_email: str, user_name: str, otp_code: str) -> bool:
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
    return _send_email(to_email, f"{otp_code} — Code de vérification Alternance App", html)


def send_welcome_email(to_email: str, user_name: str) -> bool:
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
    return _send_email(to_email, "Bienvenue sur Alternance App !", html)


def send_application_confirmation(
    to_email: str, user_name: str, job_title: str,
    company: str, job_url: str, cover_letter: str = "",
) -> bool:
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
    return _send_email(to_email, f"Candidature — {job_title} chez {company}", html)


def send_real_application(
    recruiter_email: str, user_name: str, user_email: str,
    job_title: str, company: str, cover_letter: str, cv_path: str = "",
) -> bool:
    html = f"""
    <div style="font-family: Arial, sans-serif;">
      <p>{cover_letter.replace(chr(10), '<br>')}</p>
      <hr>
      <p>{user_name}<br>{user_email}</p>
    </div>
    """
    return _send_email(
        recruiter_email,
        f"Candidature alternance – {job_title} – {user_name}",
        html,
    )
