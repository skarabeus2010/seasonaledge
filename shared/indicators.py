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


def _ema_werte(werte: np.ndarray, period: int) -> np.ndarray:
    """EMA mit SMA-Startwert über die ersten `period` gültigen Werte (wie SA.indicators.calcEMA und TA-Lib);
    davor NaN. NaN-Stellen in der Eingabe bleiben NaN und werden übersprungen."""
    out = np.full(len(werte), np.nan)
    gueltig = np.flatnonzero(~np.isnan(werte))
    if period < 1 or len(gueltig) < period:
        return out
    k = 2.0 / (period + 1)
    ema = float(np.mean(werte[gueltig[:period]]))
    out[gueltig[period - 1]] = ema
    for i in gueltig[period:]:
        ema = werte[i] * k + ema * (1 - k)
        out[i] = ema
    return out


def calc_ema(series: pd.Series, period: int = 200) -> pd.Series:
    """Exponential Moving Average, SMA-Startwert (Zwilling: landing/js/indicators.js calcEMA).

    Bis 2026-11-15 startete Python beim ersten Kurs (pandas ewm), JS mit dem SMA — dieselben Kurse ergaben
    verschiedene EMA/MACD/LBR (Audit mit Codex). Jetzt eine Definition: Wächter scripts/verify_indikator_zwillinge.py."""
    return pd.Series(_ema_werte(series.to_numpy(dtype=float), period), index=series.index)


# ── RSI ──────────────────────────────────────────────────────

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (0-100) nach Wilder (Zwilling: SA.indicators.calcRSI).

    Startwert = einfacher Mittelwert der ersten `period` Gewinne/Verluste, danach Wilder-Glättung
    avg = (avg·(n−1) + x)/n. Kein Verlust bei Gewinn → 100, keine Bewegung im Fenster → NaN (unbestimmt).
    Bis 2026-11-15 rechnete Python ein gleitendes einfaches Mittel und gab bei Verlust 0 NaN, JS 99,0099."""
    werte = series.to_numpy(dtype=float)
    out = np.full(len(werte), np.nan)
    if len(werte) < period + 1 or np.isnan(werte).any():
        if np.isnan(werte).any():   # Lücken: auf den gültigen Werten rechnen, an ihre Stellen zurücklegen
            maske = ~np.isnan(werte)
            teil = calc_rsi(pd.Series(werte[maske]), period).to_numpy()
            out[maske] = teil
        return pd.Series(out, index=series.index)
    d = np.diff(werte)
    gew, ver = np.where(d > 0, d, 0.0), np.where(d < 0, -d, 0.0)

    def rsi(g, v):
        if v > 0:
            return 100.0 - 100.0 / (1.0 + g / v)
        return 100.0 if g > 0 else np.nan
    ag, av = float(np.mean(gew[:period])), float(np.mean(ver[:period]))
    out[period] = rsi(ag, av)
    for i in range(period, len(d)):
        ag = (ag * (period - 1) + gew[i]) / period
        av = (av * (period - 1) + ver[i]) / period
        out[i + 1] = rsi(ag, av)
    return pd.Series(out, index=series.index)


# ── Bollinger Bands ──────────────────────────────────────────

def calc_bollinger(series: pd.Series, period: int = 20,
                   num_std: float = 2.0) -> dict:
    """Bollinger Bands mit %B und Bandbreite. Populations-Standardabweichung (ddof=0) wie Bollinger und
    SA.indicators.calcBollinger — bis 2026-11-15 Stichprobe (ddof=1), Bänder dadurch breiter als im Browser."""
    middle = series.rolling(period).mean()
    std = series.rolling(period).std(ddof=0)
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
    """MACD Line, Signal Line, Histogram — EMAs mit SMA-Startwert, Signal = EMA über die gültige MACD-Linie
    (wie SA.indicators.calcMACD)."""
    macd_line = calc_ema(series, fast) - calc_ema(series, slow)
    signal_line = calc_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


# ── LBR Oscillator ───────────────────────────────────────

def calc_lbr(series: pd.Series, fast: int = 3, slow: int = 10,
             smoothing: int = 16) -> dict:
    """LBR Oscillator (Linda Bradford Raschke).
    Ist ein MACD mit kurzen Parametern: Fast=3, Slow=10, Signal=16.
    Fastline = MACD Line, Slowline = Signal Line, Histogram = Differenz."""
    m = calc_macd(series, fast, slow, smoothing)   # eine Rechnung wie SA.indicators.calcLBR → calcMACD
    fastline, slowline, histogram = m["macd"], m["signal"], m["histogram"]
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
