"""
SeasonalEdge — Supabase DB-Connector

Tabellen:
  prices       — Kursdaten (ticker, date, OHLCV)
  seasonality  — Vorberechnete Saisonalität (ticker, day_of_year, avg_return, ...)
  app_logs     — Logging auf Streamlit Cloud (kein persistentes Filesystem)

Verwendung:
  from shared.supabase_client import fetch_seasonality, upsert_prices, log_to_db
"""

import os
from shared.logger import app_logger, error_logger

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None
    app_logger.warning("supabase-py nicht installiert — DB-Funktionen deaktiviert")

# ── Credentials aus Environment ──────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_client: "Client | None" = None


def get_client() -> "Client":
    """Lazy-Init des Supabase-Clients."""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL und SUPABASE_KEY müssen als Environment-Variablen gesetzt sein. "
                "Lokal: .streamlit/secrets.toml | Cloud: Streamlit Secrets"
            )
        if create_client is None:
            raise RuntimeError("supabase-py nicht installiert: pip install supabase")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        app_logger.info("Supabase-Client initialisiert")
    return _client


# ── Prices ───────────────────────────────────────────────────

def upsert_prices(records: list[dict]) -> None:
    """Kursdaten upserten (ON CONFLICT ticker+date)."""
    if not records:
        return
    try:
        get_client().table("prices").upsert(
            records, on_conflict="ticker,date"
        ).execute()
        app_logger.info(f"Prices upserted: {len(records)} Zeilen")
    except Exception as e:
        error_logger.error(f"Prices upsert fehlgeschlagen: {e}", exc_info=True)
        raise


def fetch_prices(ticker: str, start: str = None, end: str = None) -> list[dict]:
    """Kursdaten für einen Ticker laden. Optional mit Datumsfilter."""
    try:
        query = get_client().table("prices").select("*").eq("ticker", ticker)
        if start:
            query = query.gte("date", start)
        if end:
            query = query.lte("date", end)
        result = query.order("date").execute()
        return result.data
    except Exception as e:
        error_logger.error(f"Prices fetch fehlgeschlagen: {ticker} — {e}", exc_info=True)
        return []


# ── Seasonality ──────────────────────────────────────────────

def fetch_seasonality(ticker: str) -> list[dict]:
    """Vorberechnete Saisonalität für einen Ticker."""
    try:
        result = (
            get_client()
            .table("seasonality")
            .select("*")
            .eq("ticker", ticker)
            .order("day_of_year")
            .execute()
        )
        return result.data
    except Exception as e:
        error_logger.error(f"Seasonality fetch fehlgeschlagen: {ticker} — {e}", exc_info=True)
        return []


def upsert_seasonality(records: list[dict]) -> None:
    """Saisonalitätsdaten upserten."""
    if not records:
        return
    try:
        get_client().table("seasonality").upsert(
            records, on_conflict="ticker,day_of_year"
        ).execute()
        app_logger.info(f"Seasonality upserted: {len(records)} Zeilen")
    except Exception as e:
        error_logger.error(f"Seasonality upsert fehlgeschlagen: {e}", exc_info=True)
        raise


# ── App Logs (für Streamlit Cloud) ───────────────────────────

def log_to_db(level: str, channel: str, message: str, user_email: str = "") -> None:
    """Log-Eintrag in Supabase app_logs Tabelle schreiben."""
    try:
        get_client().table("app_logs").insert({
            "level": level,
            "channel": channel,
            "message": message,
            "user_email": user_email,
        }).execute()
    except Exception:
        # Stilles Fallback — DB-Logging darf App nicht crashen
        pass
