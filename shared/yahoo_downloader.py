# shared/yahoo_downloader.py
# Direkter Yahoo Finance Downloader — ersetzt yfinance komplett.

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
    close_data = adjclose if adjclose is not None else quotes.get("close")

    df = pd.DataFrame({
        "Open":   quotes.get("open",   [np.nan] * len(timestamps)),
        "High":   quotes.get("high",   [np.nan] * len(timestamps)),
        "Low":    quotes.get("low",    [np.nan] * len(timestamps)),
        "Close":  close_data,
        "Volume": quotes.get("volume", [np.nan] * len(timestamps)),
    }, index=index)

    df.index.name = "Date"
    df = df.dropna(subset=["Close"])

    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Volume"] = pd.to_numeric(df["Volume"], errors="coerce").fillna(0).astype(int)

    return df


@st.cache_data(ttl=3600, show_spinner=False)
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
    Fügt hinzu: return, log_return, day_of_year, year, month
    """
    if df is None or len(df) == 0:
        return df
    df = df.copy()
    df["return"]      = df["Close"].pct_change()
    df["log_return"]  = np.log(df["Close"] / df["Close"].shift(1))
    df["day_of_year"] = df.index.dayofyear
    df["year"]        = df.index.year
    df["month"]       = df.index.month
    df = df.dropna(subset=["return"])
    return df


def clear_cache():
    """Leert den Streamlit-Cache für download_data."""
    download_data.clear()
