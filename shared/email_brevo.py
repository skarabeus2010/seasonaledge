"""
SeasonalEdge — Brevo E-Mail-Integration

Template-IDs:
  1: Willkommen / E-Mail-Bestätigung
  2: Passwort zurücksetzen
  3: Premium-Buchungsbestätigung
  4: Wöchentlicher Newsletter
  5: Admin-Alert (Systemfehler)

Verwendung:
  from shared.email_brevo import send_transactional, send_admin_alert
  send_transactional("user@example.com", template_id=1, params={"name": "Max"})
  send_admin_alert("Download-Manager crashed")
"""

import os

import requests

from shared.logger import app_logger, error_logger

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
SENDER = {"name": "SeasonalEdge", "email": "noreply@seasonaledge.app"}

# Admin-E-Mail für System-Alerts
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")


def send_transactional(
    to_email: str,
    template_id: int,
    params: dict | None = None,
) -> bool:
    """
    Transaktions-E-Mail über Brevo senden.

    Args:
        to_email: Empfänger-Adresse
        template_id: Brevo Template-ID (1-5)
        params: Template-Parameter (z.B. {"name": "Max", "ticker": "SPY"})

    Returns:
        True bei Erfolg, False bei Fehler
    """
    if not BREVO_API_KEY:
        app_logger.warning("BREVO_API_KEY nicht gesetzt — E-Mail übersprungen")
        return False

    payload = {
        "sender": SENDER,
        "to": [{"email": to_email}],
        "templateId": template_id,
    }
    if params:
        payload["params"] = params

    try:
        resp = requests.post(
            BREVO_API_URL,
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        app_logger.info(f"E-Mail gesendet: template={template_id} to={to_email}")
        return True
    except requests.RequestException as e:
        error_logger.error(
            f"E-Mail fehlgeschlagen: template={template_id} to={to_email} — {e}",
            exc_info=True,
        )
        return False


def send_welcome(to_email: str, name: str = "") -> bool:
    """Willkommens-E-Mail senden."""
    return send_transactional(to_email, template_id=1, params={"name": name})


def send_password_reset(to_email: str, reset_link: str) -> bool:
    """Passwort-Reset-E-Mail senden."""
    return send_transactional(
        to_email, template_id=2, params={"reset_link": reset_link}
    )


def send_premium_confirmation(to_email: str, plan: str = "Premium") -> bool:
    """Premium-Buchungsbestätigung senden."""
    return send_transactional(
        to_email, template_id=3, params={"plan": plan}
    )


def send_admin_alert(message: str) -> bool:
    """System-Alert an Admin senden."""
    if not ADMIN_EMAIL:
        error_logger.error("ADMIN_EMAIL nicht gesetzt — Alert verworfen")
        return False
    return send_transactional(
        ADMIN_EMAIL, template_id=5, params={"message": message}
    )
