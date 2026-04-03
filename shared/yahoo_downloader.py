# shared/yahoo_downloader.py
# Direkter Yahoo Finance Downloader — ersetzt yfinance komplett.
from __future__ import annotations

import requests
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, date

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

_BASE_URL  = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
_BASE_URL2 = "https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"

_VALID_PERIODS   = ["1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"]
_VALID_INTERVALS = ["1d","1wk","1mo"]

# Ticker die lange Historie von Stooq beziehen koennen
_STOOQ_TICKERS = {
    "^DJI":      "^dji",
    "^GSPC":     "^spx",
    "^GDAXI":    "^dax",
    "^FTSE":     "^ukx",
    "^N225":     "^nkx",
    "^FCHI":     "^cac",
    "^STOXX50E": "^sx5e",
    "^SSMI":     "^smi",
    "^HSI":      "^hsi",
    "^KS11":     "^kospi",
}


def _fetch_stooq(stooq_ticker: str, timeout: int = 15) -> pd.DataFrame:
    """Laedt historische Daten von Stooq.com (Langzeit-Fallback)."""
    url = f"https://stooq.com/q/d/l/?s={stooq_ticker}&i=d"
    try:
        # Stooq erfordert ein Session-Cookie (cookie_uu) — ohne liefert es leeren Body
        session = requests.Session()
        session.get("https://stooq.com/", headers=_HEADERS, timeout=timeout)
        resp = session.get(url, headers=_HEADERS, timeout=timeout)
        if resp.status_code != 200 or len(resp.text) < 50:
            return pd.DataFrame()

        from io import StringIO
        df = pd.read_csv(StringIO(resp.text))

        if "Date" not in df.columns or "Close" not in df.columns:
            return pd.DataFrame()

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
        df.index.name = "Date"

        # Spalten normalisieren
        for col in ["Open", "High", "Low", "Close"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "Volume" in df.columns:
            df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(int)
        else:
            df["Volume"] = 0

        df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
        return df

    except Exception:
        return pd.DataFrame()


def _fetch_yahoo(ticker: str, params: dict, timeout: int) -> dict | None:
    """HTTP-Request gegen Yahoo Finance API. Versucht query1, dann query2."""
    for base_url in [_BASE_URL, _BASE_URL2]:
        url = base_url.format(ticker=ticker.upper())
        try:
            resp = requests.get(
                url, headers=_HEADERS, params=params,
                timeout=timeout, allow_redirects=True
            )
            if resp.status_code == 200:
                data  = resp.json()
                chart = data.get("chart", {})
                if chart.get("error") is None and chart.get("result"):
                    return data
        except (requests.exceptions.RequestException, ValueError):
            continue
    return None


def _parse_yahoo_response(data: dict) -> pd.DataFrame:
    """Parst Yahoo Finance JSON zu sauberem DataFrame."""
    result     = data["chart"]["result"][0]
    timestamps = result.get("timestamp", [])
    if not timestamps:
        return pd.DataFrame()

    quotes   = result["indicators"]["quote"][0]
    adj_list = result["indicators"].get("adjclose", [{}])
    adjclose = adj_list[0].get("adjclose") if adj_list else None

    index      = pd.to_datetime(timestamps, unit="s", utc=True).tz_localize(None)
    raw_close  = quotes.get("close", [np.nan] * len(timestamps))
    close_data = adjclose if adjclose is not None else raw_close

    raw_open = quotes.get("open",   [np.nan] * len(timestamps))
    raw_high = quotes.get("high",   [np.nan] * len(timestamps))
    raw_low  = quotes.get("low",    [np.nan] * len(timestamps))

    # Open/High/Low mit Adjustierungsfaktor skalieren (Splits + Dividenden)
    if adjclose is not None:
        adj_factor = [
            (a / c) if c and a and c != 0 else 1.0
            for a, c in zip(adjclose, raw_close)
        ]
        raw_open = [o * f if o is not None else np.nan for o, f in zip(raw_open, adj_factor)]
        raw_high = [h * f if h is not None else np.nan for h, f in zip(raw_high, adj_factor)]
        raw_low  = [l * f if l is not None else np.nan for l, f in zip(raw_low,  adj_factor)]

    df = pd.DataFrame({
        "Open":   raw_open,
        "High":   raw_high,
        "Low":    raw_low,
        "Close":  close_data,
        "Volume": quotes.get("volume", [np.nan] * len(timestamps)),
    }, index=index)

    df.index.name = "Date"
    df = df.dropna(subset=["Close"])

    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(int)

    return df


@st.cache_data(ttl=900, show_spinner=False)
def download_data(
    ticker:   str,
    period:   str = "max",
    interval: str = "1d",
    timeout:  int = 15,
) -> pd.DataFrame:
    """
    Lädt historische Kursdaten direkt von Yahoo Finance.

    WICHTIG: period="max" mit interval="1d" liefert bei Yahoo nur
    monatliche Daten. Wir umgehen das mit einem expliziten Datumsrange
    (period1/period2 statt range=max).

    Args:
        ticker   : z.B. "SPY", "^GSPC", "BTC-USD", "EURUSD=X"
        period   : "1d","5d","1mo","3mo","6mo","1y","2y","5y","10y","ytd","max"
        interval : "1d","1wk","1mo"
        timeout  : HTTP-Timeout in Sekunden

    Returns:
        pd.DataFrame mit DatetimeIndex und Spalten: Open, High, Low, Close, Volume
        Leerer DataFrame bei Fehler.
    """
    if interval not in _VALID_INTERVALS:
        interval = "1d"

    # ── Spezialfall: max mit 1d → expliziter Datumsrange ──────────────────────
    # Yahoo liefert bei range=max&interval=1d nur monatliche Daten (Bug/Limit).
    # Fix: period1=0 (Unix-Epoch) + period2=heute → volle tägliche Historie.
    if period == "max" and interval == "1d":
        params = {
            "interval": "1d",
            "period1":  0,                          # 1970-01-01
            "period2":  int(datetime.now().timestamp()),
        }
    else:
        if period not in _VALID_PERIODS:
            period = "max"
        params = {"interval": interval, "range": period}

    data = _fetch_yahoo(ticker, params, timeout)

    if data is None:
        print(f"[yahoo_downloader] Keine Daten für '{ticker}' erhalten.")
        return pd.DataFrame()

    try:
        df = _parse_yahoo_response(data)
        if len(df) == 0:
            print(f"[yahoo_downloader] Leerer DataFrame für '{ticker}'.")
            return pd.DataFrame()

        # Stooq-Fallback: Wenn Yahoo < 40 Jahre liefert und Ticker lange Historie hat
        if ticker.upper() in _STOOQ_TICKERS and period == "max":
            yahoo_years = df.index[-1].year - df.index[0].year
            if yahoo_years < 40:
                stooq_ticker = _STOOQ_TICKERS[ticker.upper()]
                stooq_df = _fetch_stooq(stooq_ticker, timeout)
                if len(stooq_df) > len(df):
                    # Stooq-Daten vor Yahoo-Start anhaengen
                    yahoo_start = df.index[0]
                    stooq_pre = stooq_df[stooq_df.index < yahoo_start]
                    if len(stooq_pre) > 0:
                        df = pd.concat([stooq_pre, df]).sort_index()
                        # Duplikate entfernen (gleicher Tag)
                        df = df[~df.index.duplicated(keep="last")]
                        print(f"[yahoo_downloader] Stooq-Backfill: {len(stooq_pre)} Tage vor {yahoo_start.strftime('%Y-%m-%d')}")

        return df
    except Exception as e:
        print(f"[yahoo_downloader] Parse-Fehler für '{ticker}': {e}")
        return pd.DataFrame()


def get_current_price(ticker: str, timeout: int = 10) -> dict | None:
    """Aktueller Preis (nicht gecacht)."""
    params = {"interval": "1d", "range": "1d"}
    data   = _fetch_yahoo(ticker, params, timeout)
    if data is None:
        return None
    try:
        meta = data["chart"]["result"][0]["meta"]
        return {
            "symbol":      meta.get("symbol", ticker),
            "price":       meta.get("regularMarketPrice"),
            "currency":    meta.get("currency", ""),
            "market_time": datetime.fromtimestamp(meta.get("regularMarketTime", 0)),
            "exchange":    meta.get("fullExchangeName", ""),
        }
    except Exception:
        return None


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ergänzt rohen OHLCV-DataFrame um berechnete Spalten.
    Fügt hinzu: return, log_return, day_of_year, year, month, tdoy.

    Wenn log_return bereits aus Supabase vorhanden ist, wird die
    Berechnung uebersprungen (Performance-Optimierung).
    """
    if df is None or len(df) == 0:
        return df
    df = df.copy()

    # Renditen: nur berechnen wenn nicht bereits aus DB vorhanden
    if "return" not in df.columns or df["return"].isna().all():
        df["return"] = df["Close"].pct_change()
    elif df["return"].isna().any():
        df["return"] = df["return"].fillna(df["Close"].pct_change())
    if "log_return" not in df.columns or df["log_return"].isna().all():
        df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))
    elif df["log_return"].isna().any():
        df["log_return"] = df["log_return"].fillna(
            np.log(df["Close"] / df["Close"].shift(1)))

    # Metadata-Spalten (immer setzen — sehr guenstig)
    df["day_of_year"] = df.index.dayofyear          # CDOY (Kalendertag)
    df["year"]        = df.index.year
    df["month"]       = df.index.month

    # TDOY/TDOM: DB-Spalten nutzen wenn vorhanden, sonst Fallback cumcount
    if "tdoy" in df.columns and df["tdoy"].notna().sum() > 0:
        pass  # Bereits aus Supabase geladen
    else:
        df["tdoy"] = df.groupby("year").cumcount() + 1  # Fallback
    if "tdom" not in df.columns or df["tdom"].isna().all():
        df["tdom"] = df.groupby(["year", "month"]).cumcount() + 1  # Fallback
    df = df.dropna(subset=["return"])
    return df


def clear_cache():
    """Leert den Streamlit-Cache für download_data."""
    download_data.clear()
