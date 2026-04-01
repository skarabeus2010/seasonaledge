"""
SeasonAlpha - Data Layer (Supabase-First)
==========================================
Lädt Kursdaten primär aus Supabase (schnell, ~0.5s).
Fallback auf Yahoo Finance + Stooq (langsam, ~3-7s).

Alle Pages importieren: from shared.data import download_data, preprocess
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from shared.yahoo_downloader import (
    download_data as _yahoo_download,
    preprocess,
)

# Maximales Alter der Supabase-Daten bevor Yahoo-Fallback greift
_MAX_STALE_DAYS = 5  # Wochenende + Feiertage abdecken


def _load_from_supabase(ticker: str) -> pd.DataFrame | None:
    """
    Versucht Kursdaten aus Supabase zu laden.

    Returns:
        DataFrame im Yahoo-Format (DatetimeIndex, OHLCV) oder None bei Fehler.
    """
    try:
        from shared.supabase_client import fetch_prices
        records = fetch_prices(ticker)

        if not records or len(records) < 50:
            return None

        df = pd.DataFrame(records)

        # Spalten normalisieren (Supabase: lowercase, Yahoo: Title)
        col_map = {"date": "Date", "open": "Open", "high": "High",
                   "low": "Low", "close": "Close", "volume": "Volume"}
        df = df.rename(columns=col_map)

        if "Close" not in df.columns or "Date" not in df.columns:
            return None

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
        df.index.name = "Date"

        # Numerische Spalten sicherstellen
        for col in ["Open", "High", "Low", "Close"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "Volume" in df.columns:
            df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(int)
        else:
            df["Volume"] = 0

        # Nur OHLCV behalten (wie Yahoo-Format)
        keep_cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
        df = df[keep_cols].dropna(subset=["Close"])

        # Frische prüfen: Letzter Eintrag < _MAX_STALE_DAYS alt?
        last_date = df.index[-1]
        cutoff = datetime.now() - timedelta(days=_MAX_STALE_DAYS)
        if last_date < pd.Timestamp(cutoff):
            return None  # Zu alt → Yahoo-Fallback

        # OHLC-Qualität prüfen: Open/High/Low müssen für >50% der Zeilen vorhanden sein.
        # Nightly-Refresh schreibt nur die letzten 60 Tage → ältere Zeilen haben Open=NULL.
        # Wenn zu viel fehlt, liefert Yahoo-Fallback vollständige OHLCV-Daten.
        if "Open" in df.columns:
            open_fill_rate = df["Open"].notna().mean()
            if open_fill_rate < 0.5:
                return None  # Zu viele fehlende Open-Werte → Yahoo-Fallback

        return df

    except Exception:
        return None


def download_data(ticker: str, period: str = "max", interval: str = "1d",
                  timeout: int = 15) -> pd.DataFrame:
    """
    Lädt Kursdaten: Supabase-First, Yahoo-Fallback.

    Signatur identisch zu yahoo_downloader.download_data().
    """
    # 1. Supabase versuchen (nur für period="max" oder "5y"+ sinnvoll)
    if period in ("max", "5y", "10y", "20y"):
        db_df = _load_from_supabase(ticker)
        if db_df is not None and len(db_df) > 100:
            return db_df

    # 2. Fallback: Yahoo Finance + Stooq
    return _yahoo_download(ticker, period=period, interval=interval, timeout=timeout)
