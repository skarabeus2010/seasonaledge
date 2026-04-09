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
SENDER = {"name": "SeasonAlpha", "email": "noreply@seasonaledge.app"}
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _get_api_key() -> str:
    """
    API-Key laden in folgender Reihenfolge:
        1. Environment-Variable BREVO_API_KEY
        2. .streamlit/secrets.toml (direkt geparsed, ohne Streamlit-Runtime)
        3. streamlit.secrets (Fallback für Streamlit-Kontext)
    """
    # 1. Env-Var
    key = BREVO_API_KEY
    if key:
        return key

    # 2. Direkter TOML-Read (funktioniert im Cron-Kontext ohne Streamlit)
    try:
        import pathlib
        # Suche secrets.toml im Projekt-Root oder ~/.streamlit/
        candidates = [
            pathlib.Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml",
            pathlib.Path.home() / ".streamlit" / "secrets.toml",
        ]
        for path in candidates:
            if path.exists():
                try:
                    import tomllib  # Python 3.11+
                except ImportError:
                    try:
                        import tomli as tomllib  # Fallback
                    except ImportError:
                        tomllib = None
                if tomllib:
                    with open(path, "rb") as f:
                        data = tomllib.load(f)
                    # Key kann als top-level oder case-variiert drin sein
                    for k in ("BREVO_API_KEY", "brevo_api_key"):
                        if k in data and data[k]:
                            return data[k]
                    break
    except Exception:
        pass

    # 3. Streamlit-Secrets (nur im Streamlit-Kontext sinnvoll)
    try:
        import streamlit as st
        k = st.secrets.get("BREVO_API_KEY", "") or st.secrets.get("brevo_api_key", "")
        if k:
            return k
    except Exception:
        pass

    return ""


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


def send_html(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = None,
    reply_to: str = None,
) -> bool:
    """
    Beliebigen HTML-Body via Brevo API senden (kein Template).

    Verwendung: Weekly Newsletter, ad-hoc Broadcasts, manuell gerenderte Mails
    die nicht zu einem Brevo-Template passen.

    Args:
        to_email: Empfänger-Adresse
        subject: Betreff
        html_content: HTML-Body (inline CSS empfohlen)
        text_content: Optional Plaintext-Fallback (für Clients ohne HTML)
        reply_to: Optional Reply-To Header

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
        "subject": subject,
        "htmlContent": html_content,
    }
    if text_content:
        payload["textContent"] = text_content
    if reply_to:
        payload["replyTo"] = {"email": reply_to}

    try:
        resp = requests.post(
            BREVO_API_URL,
            headers={
                "api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        # Brevo liefert messageId zurück — wichtig für Tracking in Brevo Logs
        msg_id = ""
        try:
            msg_id = resp.json().get("messageId", "")
        except Exception:
            pass
        app_logger.info(
            f"HTML-E-Mail gesendet: to={to_email} subject={subject[:60]} "
            f"sender={SENDER.get('email')} status={resp.status_code} messageId={msg_id}"
        )
        print(
            f"[brevo] to={to_email} status={resp.status_code} "
            f"messageId={msg_id} sender={SENDER.get('email')}"
        )
        return True
    except requests.HTTPError as e:
        # Bei 4xx/5xx versuchen wir die Brevo-Fehler-Response zu loggen
        body = ""
        try:
            body = resp.text[:500]
        except Exception:
            pass
        error_logger.error(
            f"HTML-E-Mail HTTP-Fehler: to={to_email} "
            f"status={resp.status_code if 'resp' in dir() else '?'} body={body} error={e}"
        )
        print(f"[brevo] HTTP ERROR: status={getattr(resp, 'status_code', '?')} body={body[:200]}")
        return False
    except requests.RequestException as e:
        error_logger.error(f"HTML-E-Mail fehlgeschlagen: to={to_email} error={e}")
        print(f"[brevo] REQUEST ERROR: {e}")
        return False
