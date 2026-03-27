"""
SeasonAlpha — Technische Indikatoren & Filter-Engine
=====================================================
Reine Berechnungen (kein Streamlit). Wird von indicator_filter_ui.py
und den Pages importiert.

Indikatoren: SMA, EMA, RSI, Bollinger Bands, MACD
Filter-Engine: apply_indicator_filter() gibt Boolean-Maske zurueck.
"""

import numpy as np
import pandas as pd


# ── SMA / EMA ────────────────────────────────────────────────

def calc_sma(series: pd.Series, period: int = 200) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(period, min_periods=period).mean()


def calc_ema(series: pd.Series, period: int = 200) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


# ── RSI ──────────────────────────────────────────────────────

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (0-100)."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


# ── Bollinger Bands ──────────────────────────────────────────

def calc_bollinger(series: pd.Series, period: int = 20,
                   num_std: float = 2.0) -> dict:
    """Bollinger Bands mit %B und Bandbreite."""
    middle = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    band_range = upper - lower
    pct_b = (series - lower) / band_range.replace(0, np.nan)
    bandwidth = band_range / middle.replace(0, np.nan) * 100
    return {
        "middle": middle, "upper": upper, "lower": lower,
        "pct_b": pct_b, "bandwidth": bandwidth,
    }


# ── MACD ─────────────────────────────────────────────────────

def calc_macd(series: pd.Series, fast: int = 12, slow: int = 26,
              signal: int = 9) -> dict:
    """MACD Line, Signal Line, Histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


# ── LBR Oscillator ───────────────────────────────────────

def calc_lbr(series: pd.Series, fast: int = 3, slow: int = 10,
             smoothing: int = 16) -> dict:
    """LBR Oscillator (Linda Bradford Raschke).
    Ist ein MACD mit kurzen Parametern: Fast=3, Slow=10, Signal=16.
    Fastline = MACD Line, Slowline = Signal Line, Histogram = Differenz."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    fastline = ema_fast - ema_slow
    slowline = fastline.ewm(span=smoothing, adjust=False).mean()
    histogram = fastline - slowline
    return {"fastline": fastline, "slowline": slowline, "histogram": histogram}


# ── Filter-Engine ────────────────────────────────────────────

# Verfuegbare Indikatoren + Bedingungen
INDICATOR_REGISTRY = {
    "SMA": {
        "label": "SMA (Simple Moving Average)",
        "params": [{"name": "period", "label": "Periode", "min": 10, "max": 400, "default": 200}],
        "conditions": ["Close > SMA", "Close < SMA"],
    },
    "EMA": {
        "label": "EMA (Exponential Moving Average)",
        "params": [{"name": "period", "label": "Periode", "min": 10, "max": 400, "default": 200}],
        "conditions": ["Close > EMA", "Close < EMA"],
    },
    "RSI": {
        "label": "RSI (Relative Strength Index)",
        "params": [
            {"name": "period", "label": "Periode", "min": 5, "max": 30, "default": 14},
            {"name": "threshold", "label": "Schwelle", "min": 0, "max": 100, "default": 50},
        ],
        "conditions": ["RSI > Schwelle", "RSI < Schwelle"],
    },
    "Bollinger": {
        "label": "Bollinger Bands",
        "params": [
            {"name": "period", "label": "Periode", "min": 10, "max": 50, "default": 20},
            {"name": "num_std", "label": "Std-Abweichung", "min": 1.0, "max": 3.0,
             "default": 2.0, "step": 0.5},
        ],
        "conditions": ["Close > Upper Band", "Close < Lower Band", "Close innerhalb Bands"],
    },
    "MACD": {
        "label": "MACD",
        "params": [
            {"name": "fast", "label": "Fast", "min": 5, "max": 26, "default": 12},
            {"name": "slow", "label": "Slow", "min": 12, "max": 50, "default": 26},
            {"name": "signal", "label": "Signal", "min": 5, "max": 20, "default": 9},
        ],
        "conditions": ["MACD > Signal (bullish)", "MACD < Signal (bearish)"],
    },
    "LBR": {
        "label": "LBR Oscillator (Raschke)",
        "params": [
            {"name": "fast", "label": "Fast", "min": 2, "max": 10, "default": 3},
            {"name": "slow", "label": "Slow", "min": 5, "max": 20, "default": 10},
            {"name": "smoothing", "label": "Smoothing", "min": 5, "max": 30, "default": 16},
        ],
        "conditions": ["LBR > 0 (bullish)", "LBR < 0 (bearish)"],
    },
}


def _eval_single_filter(df: pd.DataFrame, f: dict) -> pd.Series:
    """Berechnet Boolean-Maske fuer einen einzelnen Filter.
    Nutzt shift(1) um Look-Ahead-Bias zu vermeiden."""
    ind_type = f["type"]
    cond = f["condition"]
    close = df["Close"]

    if ind_type == "SMA":
        sma = calc_sma(close, f.get("period", 200))
        if cond == "Close > SMA":
            return (close.shift(1) > sma.shift(1)).fillna(False)
        return (close.shift(1) < sma.shift(1)).fillna(False)

    if ind_type == "EMA":
        ema = calc_ema(close, f.get("period", 200))
        if cond == "Close > EMA":
            return (close.shift(1) > ema.shift(1)).fillna(False)
        return (close.shift(1) < ema.shift(1)).fillna(False)

    if ind_type == "RSI":
        rsi = calc_rsi(close, f.get("period", 14))
        threshold = f.get("threshold", 50)
        if cond == "RSI > Schwelle":
            return (rsi.shift(1) > threshold).fillna(False)
        return (rsi.shift(1) < threshold).fillna(False)

    if ind_type == "Bollinger":
        bb = calc_bollinger(close, f.get("period", 20), f.get("num_std", 2.0))
        if cond == "Close > Upper Band":
            return (close.shift(1) > bb["upper"].shift(1)).fillna(False)
        if cond == "Close < Lower Band":
            return (close.shift(1) < bb["lower"].shift(1)).fillna(False)
        # Innerhalb Bands
        above_lower = close.shift(1) >= bb["lower"].shift(1)
        below_upper = close.shift(1) <= bb["upper"].shift(1)
        return (above_lower & below_upper).fillna(False)

    if ind_type == "MACD":
        macd = calc_macd(close, f.get("fast", 12), f.get("slow", 26),
                         f.get("signal", 9))
        if cond == "MACD > Signal (bullish)":
            return (macd["macd"].shift(1) > macd["signal"].shift(1)).fillna(False)
        return (macd["macd"].shift(1) < macd["signal"].shift(1)).fillna(False)

    if ind_type == "LBR":
        lbr = calc_lbr(close, f.get("fast", 3), f.get("slow", 10),
                        f.get("smoothing", 16))
        if cond == "LBR > 0 (bullish)":
            return (lbr["fastline"].shift(1) > 0).fillna(False)
        return (lbr["fastline"].shift(1) < 0).fillna(False)

    # Fallback: alles True
    return pd.Series(True, index=df.index)


def apply_indicator_filter(df: pd.DataFrame,
                           filters: list[dict]) -> pd.Series:
    """Wendet alle Filter mit UND-Verknuepfung an.

    Parameters
    ----------
    df : DataFrame mit mindestens 'Close'-Spalte
    filters : Liste von Filter-Dicts, z.B.:
        [{"type": "RSI", "period": 14, "threshold": 30, "condition": "RSI < Schwelle"},
         {"type": "SMA", "period": 200, "condition": "Close > SMA"}]

    Returns
    -------
    pd.Series[bool] — True = Tag erfuellt ALLE Bedingungen
    """
    if not filters:
        return pd.Series(True, index=df.index)

    mask = pd.Series(True, index=df.index)
    for f in filters:
        mask = mask & _eval_single_filter(df, f)
    return mask
