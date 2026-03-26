"""
shared/supabase_client.py — Supabase DB-Connector für SeasonAlpha
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


# ── Market Events ──────────────────────────────────

def upsert_market_events(records: list[dict]):
    """Market Events in Supabase upserten (Feiertage, OPEX, Zentralbank)."""
    if not records:
        return
    # Supabase hat ein Limit von ~1000 Rows pro Request
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("market_events").upsert(
            batch,
            on_conflict="event_date,event_type,event_name,exchange",
        ).execute()


def fetch_market_events(
    start_date: str,
    end_date: str,
    event_types: list[str] = None,
    exchanges: list[str] = None,
) -> list[dict]:
    """Market Events aus Supabase laden."""
    q = (
        get_client()
        .table("market_events")
        .select("*")
        .gte("event_date", start_date)
        .lte("event_date", end_date)
    )
    if event_types:
        q = q.in_("event_type", event_types)
    if exchanges:
        q = q.in_("exchange", exchanges)
    return q.order("event_date").execute().data


# ── Monthly Stats ──────────────────────────────────

def upsert_monthly_stats(records: list[dict]):
    """Monatliche Statistiken upserten."""
    if not records:
        return
    get_client().table("monthly_stats").upsert(
        records, on_conflict="ticker,month,years_back"
    ).execute()


def fetch_monthly_stats(ticker: str, years_back: int = 20) -> list[dict]:
    """Monatliche Statistiken aus DB laden."""
    return (
        get_client()
        .table("monthly_stats")
        .select("*")
        .eq("ticker", ticker)
        .eq("years_back", years_back)
        .order("month")
        .execute()
        .data
    )


# ── KI Scores ─────────────────────────────────────

def upsert_ki_score(record: dict):
    """KI Score upserten."""
    if not record:
        return
    get_client().table("ki_scores").upsert(
        [record], on_conflict="ticker,computed_date"
    ).execute()


def fetch_ki_score(ticker: str, computed_date: str) -> dict | None:
    """KI Score aus DB laden."""
    result = (
        get_client()
        .table("ki_scores")
        .select("*")
        .eq("ticker", ticker)
        .eq("computed_date", computed_date)
        .execute()
        .data
    )
    return result[0] if result else None


# ── Scanner Results ────────────────────────────────

def upsert_scanner_results(records: list[dict]):
    """Scanner-Ergebnisse upserten."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("scanner_results").upsert(
            batch, on_conflict="ticker,scan_date"
        ).execute()


def fetch_scanner_results(scan_date: str = None) -> list[dict]:
    """Scanner-Ergebnisse aus DB laden (neuestes Datum wenn kein Datum angegeben)."""
    client = get_client()
    if scan_date:
        return (
            client.table("scanner_results")
            .select("*")
            .eq("scan_date", scan_date)
            .order("score", desc=True)
            .execute()
            .data
        )
    # Neuestes Datum
    latest = (
        client.table("scanner_results")
        .select("scan_date")
        .order("scan_date", desc=True)
        .limit(1)
        .execute()
        .data
    )
    if not latest:
        return []
    return (
        client.table("scanner_results")
        .select("*")
        .eq("scan_date", latest[0]["scan_date"])
        .order("score", desc=True)
        .execute()
        .data
    )


# ── TDoM Stats ────────────────────────────────────

def upsert_tdom_stats(records: list[dict]):
    """TDoM-Statistiken upserten."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("tdom_stats").upsert(
            batch, on_conflict="ticker,tdom,direction,strategy"
        ).execute()


def fetch_tdom_stats(
    ticker: str,
    direction: str = "forward",
    strategy: str = "open_to_close",
) -> list[dict]:
    """TDoM-Statistiken aus DB laden."""
    return (
        get_client()
        .table("tdom_stats")
        .select("*")
        .eq("ticker", ticker)
        .eq("direction", direction)
        .eq("strategy", strategy)
        .order("tdom")
        .execute()
        .data
    )


# ── Spot-Vol Beta ─────────────────────────────────

def upsert_spot_vol_beta(records: list[dict]):
    """Spot-Vol Beta Daten upserten."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("spot_vol_beta").upsert(
            batch, on_conflict="event_date"
        ).execute()


# ── Historical CPI ───────────────────────────────

def upsert_historical_cpi(records: list[dict]):
    """CPI-Jahresdaten upserten (year, cpi, source)."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("historical_cpi").upsert(
            batch, on_conflict="year"
        ).execute()


def fetch_historical_cpi() -> list[dict]:
    """CPI-Jahresdaten aus DB laden."""
    return (
        get_client()
        .table("historical_cpi")
        .select("*")
        .order("year")
        .execute()
        .data
    )


# ── Tickers (Stammdaten) ─────────────────────────

def upsert_tickers(records: list[dict]):
    """Ticker-Stammdaten upserten (aus shared/symbols.py)."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("tickers").upsert(
            batch, on_conflict="ticker"
        ).execute()


def search_tickers_db(query: str, limit: int = 10) -> list[dict]:
    """Ticker-Suche via Supabase RPC (fuer zukuenftige API-Nutzung)."""
    return (
        get_client()
        .rpc("search_tickers", {"q": query, "lim": limit})
        .execute()
        .data
    )


def fetch_spot_vol_beta(
    start_date: str = None,
    end_date: str = None,
) -> list[dict]:
    """Spot-Vol Beta aus DB laden."""
    q = get_client().table("spot_vol_beta").select("*")
    if start_date:
        q = q.gte("event_date", start_date)
    if end_date:
        q = q.lte("event_date", end_date)
    return q.order("event_date").execute().data
