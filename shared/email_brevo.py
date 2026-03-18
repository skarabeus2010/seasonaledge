"""
shared/email_brevo.py — Brevo (ex-Sendinblue) E-Mail-Integration

Template-IDs:
  1: Willkommen / E-Mail-Bestätigung
  2: Passwort zurücksetzen
  3: Premium-Buchungsbestätigung
  4: Wöchentlicher Newsletter
  5: Admin-Alert (Systemfehler)
"""
import os
import requests
from shared.logger import app_logger, error_logger

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
SENDER = {"name": "SeasonalEdge", "email": "noreply@seasonaledge.app"}
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _get_api_key() -> str:
    """API-Key aus Environment oder Streamlit Secrets."""
    key = BREVO_API_KEY
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("BREVO_API_KEY", "")
        except Exception:
            pass
    return key


def send_transactional(
    to_email: str,
    template_id: int,
    params: dict = None,
) -> bool:
    """
    Transaktions-E-Mail über Brevo senden.

    Args:
        to_email: Empfänger-Adresse
        template_id: Brevo Template-ID (1-5)
        params: Template-Parameter als dict

    Returns:
        True bei Erfolg, False bei Fehler
    """
    api_key = _get_api_key()
    if not api_key:
        error_logger.error("BREVO_API_KEY nicht gesetzt!")
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
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        app_logger.info(f"E-Mail gesendet: template={template_id} to={to_email}")
        return True
    except requests.RequestException as e:
        error_logger.error(f"E-Mail fehlgeschlagen: template={template_id} to={to_email} error={e}")
        return False


def send_welcome(to_email: str, username: str = "") -> bool:
    """Willkommens-E-Mail senden."""
    return send_transactional(to_email, 1, {"username": username})


def send_password_reset(to_email: str, reset_link: str) -> bool:
    """Passwort-Reset-E-Mail senden."""
    return send_transactional(to_email, 2, {"reset_link": reset_link})


def send_premium_confirmation(to_email: str, plan: str = "Premium") -> bool:
    """Premium-Buchungsbestätigung senden."""
    return send_transactional(to_email, 3, {"plan": plan})


def send_admin_alert(message: str) -> bool:
    """Admin-Alert bei Systemfehler (an Admin-Adresse)."""
    admin_email = os.environ.get("ADMIN_EMAIL", "heiko@seasonaledge.app")
    return send_transactional(admin_email, 5, {"error_message": message})
