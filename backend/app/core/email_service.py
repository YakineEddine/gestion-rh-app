"""
Service centralise d'envoi d'emails pour l'application Gestion RH.

Fournisseurs supportes :
  - "resend"  : API Resend (https://resend.com) — recommande
  - "brevo"   : API Brevo / Sendinblue (https://brevo.com)
  - "smtp"    : SMTP classique (Gmail, etc.) — fallback

Configuration (.env) :
  EMAIL_PROVIDER=resend          # resend | brevo | smtp
  EMAIL_API_KEY=re_xxx...        # cle API du fournisseur
  EMAIL_FROM=noreply@mondomaine.com
  EMAIL_FROM_NAME=Enterprise RH

  # Uniquement pour le provider "smtp" :
  SMTP_EMAIL=...
  SMTP_PASSWORD=...

Regles de securite :
  - Ne jamais logguer la cle API ni le mot de passe SMTP.
  - Une erreur d'envoi ne doit JAMAIS faire echouer une operation metier.
  - Les envois sont traces dans l'audit (action EMAIL_SENT) sans donnees sensibles.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("email_service")

# ─── Configuration ──────────────────────────────────────────────────────
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "").lower().strip()
EMAIL_API_KEY = os.getenv("EMAIL_API_KEY", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Enterprise RH")

# SMTP fallback (conserve la compatibilite avec l'ancien systeme)
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# URL de l'application frontend (pour les boutons dans les emails)
APP_URL = os.getenv("APP_URL", "http://localhost:5174")

# Timeout HTTP pour les appels API (secondes)
_HTTP_TIMEOUT = 15


def is_configured() -> bool:
    """Retourne True si un fournisseur email est correctement configure."""
    if EMAIL_PROVIDER == "resend":
        return bool(EMAIL_API_KEY and EMAIL_FROM)
    if EMAIL_PROVIDER == "brevo":
        return bool(EMAIL_API_KEY and EMAIL_FROM)
    if EMAIL_PROVIDER == "smtp":
        return bool(SMTP_EMAIL and SMTP_PASSWORD)
    # Fallback : tenter SMTP si les anciennes variables sont presentes
    return bool(SMTP_EMAIL and SMTP_PASSWORD)


# ─── Fonction d'envoi generique ─────────────────────────────────────────

def send_email(
    to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> bool:
    """
    Envoie un email via le fournisseur configure.

    Retourne True si l'envoi a reussi, False sinon.
    Ne leve JAMAIS d'exception : les erreurs sont logguees et avalees.
    """
    if not is_configured():
        logger.warning("[EMAIL] Service non configure. Aucun email envoye.")
        return False

    provider = EMAIL_PROVIDER or "smtp"

    try:
        if provider == "resend":
            return _send_via_resend(to, subject, html_content, text_content)
        elif provider == "brevo":
            return _send_via_brevo(to, subject, html_content, text_content)
        else:
            return _send_via_smtp(to, subject, html_content, text_content)
    except Exception as e:
        logger.error(f"[EMAIL] Erreur inattendue ({provider}) : {e}")
        return False


# ─── Providers ──────────────────────────────────────────────────────────

def _send_via_resend(to: str, subject: str, html: str, text: Optional[str]) -> bool:
    payload = {
        "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>",
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    resp = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {EMAIL_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=_HTTP_TIMEOUT,
    )

    if resp.status_code in (200, 201):
        logger.info(f"[EMAIL/resend] Email envoye a {to}")
        return True
    else:
        logger.error(f"[EMAIL/resend] Echec {resp.status_code} : {resp.text[:200]}")
        return False


def _send_via_brevo(to: str, subject: str, html: str, text: Optional[str]) -> bool:
    payload = {
        "sender": {"name": EMAIL_FROM_NAME, "email": EMAIL_FROM},
        "to": [{"email": to}],
        "subject": subject,
        "htmlContent": html,
    }
    if text:
        payload["textContent"] = text

    resp = httpx.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "api-key": EMAIL_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=_HTTP_TIMEOUT,
    )

    if resp.status_code in (200, 201):
        logger.info(f"[EMAIL/brevo] Email envoye a {to}")
        return True
    else:
        logger.error(f"[EMAIL/brevo] Echec {resp.status_code} : {resp.text[:200]}")
        return False


def _send_via_smtp(to: str, subject: str, html: str, text: Optional[str]) -> bool:
    sender = SMTP_EMAIL
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{EMAIL_FROM_NAME} <{sender}>"
    msg["To"] = to

    if text:
        msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=_HTTP_TIMEOUT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender, SMTP_PASSWORD)
    server.send_message(msg)
    server.quit()
    logger.info(f"[EMAIL/smtp] Email envoye a {to}")
    return True


# ─── Fonction de reinitialisation (conservee pour compatibilite) ────────

def envoyer_email_reinitialisation(destinataire: str, prenom: str, reset_url: str) -> bool:
    """Envoyer un email de reinitialisation de mot de passe (legacy wrapper)."""
    subject = "Reinitialisation de votre mot de passe - Enterprise RH"
    html = _template_reset_password(prenom, reset_url)
    text = (
        f"Bonjour {prenom},\n\n"
        f"Cliquez sur le lien suivant pour reinitialiser votre mot de passe :\n{reset_url}\n\n"
        f"Ce lien est valable 15 minutes.\n\n-- Enterprise RH"
    )
    return send_email(destinataire, subject, html, text)


def envoyer_email_notification(
    destinataire: str,
    prenom: str,
    sujet: str,
    titre: str,
    corps: str,
    bouton_text: str = "",
    bouton_url: str = "",
) -> bool:
    """Envoyer une notification de sécurité générique (non bloquante)."""
    html = _template_notification(prenom, titre, corps, bouton_text, bouton_url)
    text = (
        f"Bonjour {prenom},\n\n"
        f"{titre}\n\n"
        f"{corps}\n\n"
        f"-- Enterprise RH"
    )
    return send_email(destinataire, sujet, html, text)


# ─── Templates HTML professionnels ─────────────────────────────────────

def _base_template(title: str, body_html: str, button_text: str = "", button_url: str = "") -> str:
    """Template de base responsive reutilise par tous les emails."""
    button_block = ""
    if button_text and button_url:
        button_block = f"""
        <p style="text-align:center;margin:24px 0;">
          <a href="{button_url}" style="display:inline-block;background-color:#4f46e5;
            color:#ffffff!important;text-decoration:none;padding:14px 32px;
            border-radius:8px;font-weight:600;font-size:15px;">{button_text}</a>
        </p>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background-color:#f1f5f9;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;padding:40px 0;">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:16px;border:1px solid #e2e8f0;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
  <tr><td style="background:linear-gradient(135deg,#4f46e5 0%,#6366f1 100%);padding:28px 32px;text-align:center;">
    <h1 style="color:#ffffff;font-size:20px;margin:0;letter-spacing:0.02em;">Enterprise RH</h1>
    <p style="color:rgba(255,255,255,0.8);font-size:13px;margin:6px 0 0;">{title}</p>
  </td></tr>
  <tr><td style="padding:32px;">
    {body_html}
    {button_block}
  </td></tr>
  <tr><td style="padding:20px 32px;background-color:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;font-size:12px;color:#94a3b8;">
    Cet email a ete envoye automatiquement par Enterprise RH.<br>
    Veuillez ne pas repondre a cet email.
  </td></tr>
</table>
</td></tr></table>
</body></html>"""


def _template_notification(prenom: str, titre: str, corps: str, bouton_text: str = "", bouton_url: str = "") -> str:
    """Template générique pour les notifications de sécurité."""
    body = f"""
    <p style="color:#334155;font-size:15px;line-height:1.6;">Bonjour <strong>{prenom}</strong>,</p>
    <div style="background-color:#f8fafc;border:1px solid #e2e8f0;color:#334155;padding:16px;border-radius:8px;font-size:14px;line-height:1.6;margin-top:16px;">
      <p style="margin:0 0 8px;font-weight:700;color:#4f46e5;font-size:14px;">{titre}</p>
      <p style="margin:0;">{corps}</p>
    </div>"""
    return _base_template(titre, body, bouton_text, bouton_url)


def _template_reset_password(prenom: str, reset_url: str) -> str:
    body = f"""
    <p style="color:#334155;font-size:15px;line-height:1.6;">Bonjour <strong>{prenom}</strong>,</p>
    <p style="color:#334155;font-size:15px;line-height:1.6;">
      Vous avez demande la reinitialisation de votre mot de passe.
    </p>
    <div style="background-color:#fef3c7;border:1px solid #fde68a;color:#92400e;padding:12px 16px;border-radius:8px;font-size:13px;margin-top:16px;">
      Ce lien est valable pendant <strong>15 minutes</strong>.
      Si vous n'avez pas fait cette demande, ignorez simplement cet email.
    </div>"""
    return _base_template("Reinitialisation du mot de passe", body, "Reinitialiser mon mot de passe", reset_url)


def template_contract_expiring(
    prenom: str, reference: str, date_fin: str, jours_restants: int, priorite: str
) -> str:
    """Template pour l'alerte d'expiration prochaine d'un contrat."""
    color = "#dc2626" if priorite == "CRITICAL" else "#d97706"
    label = "CRITIQUE" if priorite == "CRITICAL" else "ATTENTION"
    body = f"""
    <p style="color:#334155;font-size:15px;line-height:1.6;">Bonjour <strong>{prenom}</strong>,</p>
    <div style="background-color:{'#fef2f2' if priorite == 'CRITICAL' else '#fffbeb'};border-left:4px solid {color};padding:16px;border-radius:0 8px 8px 0;margin:16px 0;">
      <p style="margin:0 0 4px;font-weight:700;color:{color};font-size:13px;">{label}</p>
      <p style="margin:0;color:#334155;font-size:15px;">
        Le contrat <strong>{reference}</strong> expire dans <strong>{jours_restants} jour(s)</strong>
        (le {date_fin}).
      </p>
    </div>
    <p style="color:#64748b;font-size:14px;">Veuillez prendre les mesures necessaires (renouvellement, cloture, etc.).</p>"""
    return _base_template("Alerte expiration de contrat", body, "Voir le contrat", f"{APP_URL}/contrats")


def template_contract_expired(prenom: str, reference: str, date_fin: str) -> str:
    """Template pour un contrat deja expire."""
    body = f"""
    <p style="color:#334155;font-size:15px;line-height:1.6;">Bonjour <strong>{prenom}</strong>,</p>
    <div style="background-color:#fef2f2;border-left:4px solid #dc2626;padding:16px;border-radius:0 8px 8px 0;margin:16px 0;">
      <p style="margin:0 0 4px;font-weight:700;color:#dc2626;font-size:13px;">CONTRAT EXPIRE</p>
      <p style="margin:0;color:#334155;font-size:15px;">
        Le contrat <strong>{reference}</strong> est arrive a expiration le <strong>{date_fin}</strong>.
      </p>
    </div>
    <p style="color:#64748b;font-size:14px;">Veuillez mettre a jour le statut de ce contrat dans l'application.</p>"""
    return _base_template("Contrat expire", body, "Gerer les contrats", f"{APP_URL}/contrats")


def template_contract_activated(prenom: str, reference: str, date_debut: str) -> str:
    """Template pour informer un employe que son contrat est actif et disponible."""
    body = f"""
    <p style="color:#334155;font-size:15px;line-height:1.6;">Bonjour <strong>{prenom}</strong>,</p>
    <div style="background-color:#f0fdf4;border-left:4px solid #16a34a;padding:16px;border-radius:0 8px 8px 0;margin:16px 0;">
      <p style="margin:0 0 4px;font-weight:700;color:#16a34a;font-size:13px;">CONTRAT DISPONIBLE</p>
      <p style="margin:0;color:#334155;font-size:15px;">
        Votre contrat <strong>{reference}</strong> (debut le {date_debut}) est desormais actif et
        disponible dans votre espace personnel.
      </p>
    </div>
    <p style="color:#64748b;font-size:14px;">Vous pouvez le consulter et le telecharger a tout moment depuis votre tableau de bord.</p>"""
    return _base_template("Votre contrat est disponible", body, "Acceder a mon espace", f"{APP_URL}/mon-espace/contrats")


def template_contract_status_change(prenom: str, reference: str, ancien_statut: str, nouveau_statut: str) -> str:
    """Template pour un changement de statut important sur un contrat (RH)."""
    body = f"""
    <p style="color:#334155;font-size:15px;line-height:1.6;">Bonjour <strong>{prenom}</strong>,</p>
    <div style="background-color:#eff6ff;border-left:4px solid #2563eb;padding:16px;border-radius:0 8px 8px 0;margin:16px 0;">
      <p style="margin:0 0 4px;font-weight:700;color:#2563eb;font-size:13px;">CHANGEMENT DE STATUT</p>
      <p style="margin:0;color:#334155;font-size:15px;">
        Le contrat <strong>{reference}</strong> est passe de
        <strong>{ancien_statut}</strong> a <strong>{nouveau_statut}</strong>.
      </p>
    </div>"""
    return _base_template("Changement de statut de contrat", body, "Voir le contrat", f"{APP_URL}/contrats")
