"""
SeasonAlpha — Newsletter-Indikatoren / Score-Engine
===================================================
Reine Compute-Funktion (kein DB-Zugriff, kein Streamlit, keine Seiteneffekte)
für die Newsletter-Score-Berechnung pro Ticker.

Liefert LBR-Oszillator-Fastline & RSI(14) auf Tages- UND Wochenbasis sowie
einen additiven Score. Bausteine kommen aus ``shared.indicators`` (calc_lbr,
calc_rsi) — hier NICHT neu erfunden.
"""

import numpy as np
import pandas as pd

# Beim Direktaufruf (`py shared/newsletter_indicators.py`) liegt nur das
# shared/-Verzeichnis auf sys.path, nicht der Projekt-Root → 'shared' wäre
# nicht importierbar. Beim normalen `import shared.newsletter_indicators`
# ist das Paket bereits aufgelöst und dieser Block ein No-op.
if __package__ in (None, ""):
    import os
    import sys
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _root not in sys.path:
        sys.path.insert(0, _root)

from shared.indicators import calc_lbr, calc_rsi

# Mindestanzahl Bars, damit LBR/RSI sinnvoll konvergieren
# (slow=10 + smoothing=16 für LBR, +14 für RSI → grosszügiger Puffer).
_MIN_DAILY_BARS = 40
_MIN_WEEKLY_BARS = 30


def _last_valid(series: pd.Series) -> float | None:
    """Letzter nicht-NaN-Wert einer Serie als float, sonst None."""
    if series is None or len(series) == 0:
        return None
    s = series.dropna()
    if s.empty:
        return None
    val = s.iloc[-1]
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return float(val)


def compute_ticker_signals(daily_closes: pd.Series) -> dict:
    """Berechnet Newsletter-Signale & Score aus Tages-Schlusskursen.

    Parameters
    ----------
    daily_closes : pd.Series
        Index = Datum (aufsteigend sortiert), Werte = Tages-Schlusskurse (EOD).

    Returns
    -------
    dict mit EXAKT diesen Keys:
        lbr_daily   : LBR-Fastline (Tagesbasis), letzter Wert (float | None)
        lbr_weekly  : LBR-Fastline (Wochenbasis), letzter Wert (float | None)
        rsi_daily   : RSI(14) Tagesbasis, letzter Wert (float | None)
        rsi_weekly  : RSI(14) Wochenbasis, letzter Wert (float | None)
        score       : int (additive Formel, siehe unten)
    """
    lbr_daily = lbr_weekly = rsi_daily = rsi_weekly = None

    # ── Tagesbasis ───────────────────────────────────────────
    if daily_closes is not None and len(daily_closes) >= _MIN_DAILY_BARS:
        d = pd.Series(daily_closes).dropna()
        if len(d) >= _MIN_DAILY_BARS:
            lbr_daily = _last_valid(calc_lbr(d)["fastline"])
            rsi_daily = _last_valid(calc_rsi(d, period=14))

    # ── Wochenbasis ──────────────────────────────────────────
    # Woche endet Freitag; letzter Close je Woche, NaN-Wochen entfernen.
    if daily_closes is not None and len(daily_closes) > 0:
        d = pd.Series(daily_closes).dropna()
        if not d.empty:
            idx = pd.to_datetime(d.index)
            weekly = pd.Series(d.values, index=idx).resample("W-FRI").last().dropna()
            if len(weekly) >= _MIN_WEEKLY_BARS:
                lbr_weekly = _last_valid(calc_lbr(weekly)["fastline"])
                rsi_weekly = _last_valid(calc_rsi(weekly, period=14))

    # ── Score (additiv, EXAKT nach Spec) ─────────────────────
    score = 0
    if lbr_weekly is not None and lbr_weekly > 0:
        score += 1
    if lbr_daily is not None and lbr_daily > 0:
        score += 1
    if rsi_weekly is not None and rsi_weekly > 50:
        score += 1  # sonst +0
    if (rsi_daily is not None and rsi_weekly is not None
            and rsi_daily > 90 and rsi_weekly > 90):
        score -= 1  # beide extrem überkauft → Strafpunkt
    if (rsi_daily is not None and rsi_weekly is not None
            and rsi_daily < 10 and rsi_weekly < 10):
        score += 1  # beide extrem überverkauft → Bonus

    return {
        "lbr_daily": round(lbr_daily, 4) if lbr_daily is not None else None,
        "lbr_weekly": round(lbr_weekly, 4) if lbr_weekly is not None else None,
        "rsi_daily": round(rsi_daily, 1) if rsi_daily is not None else None,
        "rsi_weekly": round(rsi_weekly, 1) if rsi_weekly is not None else None,
        "score": int(score),
    }


# ── Selbsttest ───────────────────────────────────────────────
if __name__ == "__main__":
    def _make_series(values, start="2022-01-03"):
        idx = pd.bdate_range(start=start, periods=len(values))
        return pd.Series(values, index=idx)

    rng = np.random.default_rng(42)
    n = 400

    # 1) Aufwärtstrend (Drift + Rauschen) → LBR > 0, RSI > 50, Score hoch
    up = _make_series(100 + np.cumsum(0.4 + rng.normal(0, 0.5, n)))
    r_up = compute_ticker_signals(up)

    # 2) Abwärtstrend (Drift + Rauschen) → LBR < 0, RSI < 50, Score niedrig
    down = _make_series(300 + np.cumsum(-0.4 + rng.normal(0, 0.5, n)))
    r_down = compute_ticker_signals(down)

    # 3) Überkauft-Endspurt: leichtes Rauschen, dann steiler Schub → RSI extrem hoch
    base = 100 + np.cumsum(rng.normal(0, 0.3, n - 30))
    spike = base[-1] + np.cumsum(np.full(30, 3.0))
    overbought = _make_series(np.concatenate([base, spike]))
    r_ob = compute_ticker_signals(overbought)

    # 4) Überverkauft-Endspurt: leichtes Rauschen, dann steiler Absturz → RSI extrem tief
    crash = base[-1] - np.cumsum(np.full(30, 3.0))
    oversold = _make_series(np.concatenate([base, crash]))
    r_os = compute_ticker_signals(oversold)

    # 5) Zu kurze Serie (10 Tage) → keine Exception, alles None / score 0
    short = _make_series(100 + np.arange(10, dtype=float))
    r_short = compute_ticker_signals(short)

    # 6) Mittlere Serie (45 Tage, mit Rauschen): daily ok, weekly None (zu wenig Wochen).
    # Rauschen ist nötig, sonst hat eine streng monotone Linie keine "Verluste"
    # und RSI bleibt NaN (loss-mean = 0 → RS undefiniert).
    mid = _make_series(100 + np.cumsum(0.3 + rng.normal(0, 0.5, 45)))
    r_mid = compute_ticker_signals(mid)

    # 7) Leere Serie → keine Exception
    r_empty = compute_ticker_signals(pd.Series([], dtype=float))

    print("1) Aufwärts   :", r_up)
    print("2) Abwärts    :", r_down)
    print("3) Überkauft  :", r_ob)
    print("4) Überverkauft:", r_os)
    print("5) Kurz (10)  :", r_short)
    print("6) Mittel (45):", r_mid)
    print("7) Leer       :", r_empty)

    # ── Assertions ───────────────────────────────────────────
    assert r_up["lbr_daily"] is not None and r_up["lbr_daily"] > 0, "Aufwärts: lbr_daily > 0"
    assert r_up["lbr_weekly"] is not None and r_up["lbr_weekly"] > 0, "Aufwärts: lbr_weekly > 0"
    assert r_up["rsi_daily"] is not None and r_up["rsi_weekly"] is not None, "Aufwärts: RSI berechnet"
    assert r_up["score"] >= 3, "Aufwärts: Score hoch erwartet"

    assert r_down["lbr_daily"] is not None and r_down["lbr_daily"] < 0, "Abwärts: lbr_daily < 0"
    assert r_down["lbr_weekly"] is not None and r_down["lbr_weekly"] < 0, "Abwärts: lbr_weekly < 0"
    assert r_down["score"] <= 1, "Abwärts: Score niedrig erwartet"

    # Kurze/leere Serien dürfen niemals crashen und liefern int-Score
    for r in (r_short, r_mid, r_empty):
        assert isinstance(r["score"], int), "Score muss int sein"
    assert r_mid["rsi_daily"] is not None, "Mittel: daily sollte berechnet sein"
    assert r_mid["lbr_weekly"] is None, "Mittel: weekly None (zu wenig Wochen)"
    assert all(r_short[k] is None for k in ("lbr_daily", "lbr_weekly", "rsi_daily", "rsi_weekly")), \
        "Kurz: alle Indikatoren None"

    print("\nAlle Selbsttests bestanden.")
