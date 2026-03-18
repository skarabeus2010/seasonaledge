"""
shared/supabase_client.py — Supabase DB-Connector für SeasonalEdge
"""
import os
from supabase import create_client

# Keys aus Streamlit Secrets oder Environment
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

_client = None


def get_client():
    """Lazy-Init des Supabase-Clients."""
    global _client
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
