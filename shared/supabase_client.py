"""
shared/supabase_client.py — Supabase DB-Connector für SeasonalEdge
"""
import os

try:
    from supabase import create_client
except ImportError:
    create_client = None

# Keys aus Streamlit Secrets oder Environment
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_client = None


def get_client():
    """Lazy-Init des Supabase-Clients."""
    global _client
    if create_client is None:
        raise ImportError(
            "supabase-Paket nicht installiert. "
            "Installiere es mit: pip install supabase"
        )
    if _client is None:
        url = SUPABASE_URL
        key = SUPABASE_KEY
        # Streamlit Secrets Fallback
        if not url or not key:
            try:
                import streamlit as st
                url = url or st.secrets.get("SUPABASE_URL", "")
                key = key or st.secrets.get("SUPABASE_KEY", "")
            except Exception:
                pass
        if not url or not key:
            raise ValueError("SUPABASE_URL und SUPABASE_KEY müssen gesetzt sein!")
        _client = create_client(url, key)
    return _client


# ── Prices ──────────────────────────────────────────

def fetch_prices(ticker: str, start_date: str = None) -> list[dict]:
    """Kursdaten aus Supabase laden."""
    q = get_client().table("prices").select("*").eq("ticker", ticker)
    if start_date:
        q = q.gte("date", start_date)
    return q.order("date").execute().data


def upsert_prices(records: list[dict]):
    """Kursdaten in Supabase upserten (insert or update)."""
    if not records:
        return
    get_client().table("prices").upsert(
        records, on_conflict="ticker,date"
    ).execute()


def delete_prices(ticker: str):
    """Alle Kursdaten für einen Ticker löschen."""
    get_client().table("prices").delete().eq("ticker", ticker).execute()


# ── Seasonality ─────────────────────────────────────

def fetch_seasonality(ticker: str) -> list[dict]:
    """Vorberechnete Saisonalität laden."""
    return (
        get_client()
        .table("seasonality")
        .select("*")
        .eq("ticker", ticker)
        .order("day_of_year")
        .execute()
        .data
    )


def upsert_seasonality(records: list[dict]):
    """Saisonalitätsdaten upserten."""
    if not records:
        return
    get_client().table("seasonality").upsert(
        records, on_conflict="ticker,day_of_year"
    ).execute()


# ── App Logs ────────────────────────────────────────

def insert_log(level: str, channel: str, message: str, user_email: str = None):
    """Log-Eintrag in Supabase schreiben (für Streamlit Cloud)."""
    get_client().table("app_logs").insert({
        "level": level,
        "channel": channel,
        "message": message,
        "user_email": user_email,
    }).execute()


# ── Subscribers ────────────────────────────────────

def subscribe_email(
    email: str,
    source: str = "website",
    ip_address: str = None,
    brevo_synced: bool = False,
) -> dict | None:
    """
    Neuen Subscriber anlegen oder reaktivieren.

    Falls E-Mail bereits existiert und unsubscribed war,
    wird der Status auf 'active' zurückgesetzt.

    Returns:
        dict mit Subscriber-Daten oder None bei Fehler
    """
    email = email.strip().lower()
    client = get_client()

    # Prüfen ob schon vorhanden
    existing = (
        client.table("subscribers")
        .select("*")
        .eq("email", email)
        .execute()
        .data
    )

    if existing:
        # Reaktivieren falls unsubscribed
        record = existing[0]
        if record["status"] != "active" or record["no_emails"]:
            client.table("subscribers").update({
                "status": "active",
                "no_emails": False,
                "unsubscribed_at": None,
                "brevo_synced": brevo_synced,
                "source": source,
            }).eq("email", email).execute()
        elif brevo_synced and not record["brevo_synced"]:
            client.table("subscribers").update({
                "brevo_synced": True,
            }).eq("email", email).execute()
        return record

    # Neu anlegen
    result = client.table("subscribers").insert({
        "email": email,
        "status": "active",
        "source": source,
        "no_emails": False,
        "brevo_synced": brevo_synced,
        "ip_address": ip_address,
    }).execute()

    return result.data[0] if result.data else None


def unsubscribe_email(email: str) -> bool:
    """
    Subscriber austragen — setzt status='unsubscribed' und no_emails=True.

    Returns:
        True wenn erfolgreich, False wenn E-Mail nicht gefunden
    """
    email = email.strip().lower()
    client = get_client()

    existing = (
        client.table("subscribers")
        .select("id")
        .eq("email", email)
        .execute()
        .data
    )

    if not existing:
        return False

    client.table("subscribers").update({
        "status": "unsubscribed",
        "no_emails": True,
        "unsubscribed_at": "now()",
    }).eq("email", email).execute()

    return True


def get_subscriber(email: str) -> dict | None:
    """Subscriber-Daten abrufen."""
    email = email.strip().lower()
    result = (
        get_client()
        .table("subscribers")
        .select("*")
        .eq("email", email)
        .execute()
        .data
    )
    return result[0] if result else None


def get_active_subscribers() -> list[dict]:
    """Alle aktiven Subscriber laden (für Newsletter-Versand)."""
    return (
        get_client()
        .table("subscribers")
        .select("email, subscribed_at")
        .eq("status", "active")
        .eq("no_emails", False)
        .order("subscribed_at")
        .execute()
        .data
    )


def count_subscribers() -> dict:
    """Subscriber-Statistiken."""
    client = get_client()
    active = len(
        client.table("subscribers")
        .select("id", count="exact")
        .eq("status", "active")
        .eq("no_emails", False)
        .execute()
        .data
    )
    total = len(
        client.table("subscribers")
        .select("id", count="exact")
        .execute()
        .data
    )
    return {"active": active, "total": total, "unsubscribed": total - active}
