#!/usr/bin/env python3
"""
black_scholes.py — EINE Black-Scholes-Implementierung für alle Options-Pipelines.

WARUM GEMEINSAM: Skew-Historie und Live-Tageswert landen in DERSELBEN Reihe, über
die das Frontend Rank/Percentile rechnet. Sobald beide Seiten die IV auch nur
leicht unterschiedlich bestimmen, entsteht ein systematischer Versatz zwischen
Backfill- und Live-Punkten — und der Percentile misst dann den Methodenwechsel
statt den Skew.

Gemessener Schaden vor der Vereinheitlichung (2026-09-09): Provider-IV vs. eigene
BS-Inversion wichen im Zeta um 0,84–1,30 Punkte ab, bei NVDA so viel wie der
gesamte Interquartilsabstand der Reihe (1,28) — der Live-Punkt landete dadurch
im 99. Percentil, rein methodisch. Deshalb: eine Quelle, keine Kopien.
"""
from __future__ import annotations
import math

# Risk-free-Näherung; q=0. Für Differenzen INNERHALB einer Expiry unkritisch,
# muss aber auf beiden Seiten identisch sein.
R = 0.045


def cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bs_price(S, K, T, sig, typ):
    if T <= 0 or sig <= 0 or S <= 0 or K <= 0:
        return max(0.0, (S - K) if typ == "call" else (K - S))
    srt = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (R + 0.5 * sig * sig) * T) / srt
    d2 = d1 - srt
    if typ == "call":
        return S * cdf(d1) - K * math.exp(-R * T) * cdf(d2)
    return K * math.exp(-R * T) * cdf(-d2) - S * cdf(-d1)


def bs_delta(S, K, T, sig, typ):
    srt = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (R + 0.5 * sig * sig) * T) / srt
    return cdf(d1) if typ == "call" else cdf(d1) - 1.0


def implied_vol(price, S, K, T, typ):
    """IV per Bisektion; None wenn kein Root (z.B. Preis = reiner innerer Wert)."""
    if price is None or price <= 0 or T <= 0:
        return None
    lo, hi = 1e-4, 5.0
    plo = bs_price(S, K, T, lo, typ) - price
    phi = bs_price(S, K, T, hi, typ) - price
    if plo * phi > 0:
        return None
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        pm = bs_price(S, K, T, mid, typ) - price
        if abs(pm) < 1e-6:
            return mid
        if plo * pm < 0:
            hi = mid
        else:
            lo, plo = mid, pm
    return 0.5 * (lo + hi)

# ── Konstante Laufzeit (Constant Maturity) ───────────────────────────────────
# Diese Parameter MUESSEN auf beiden Seiten identisch sein (Backfill + Live),
# sonst driften die Reihen wieder auseinander — dieselbe Klasse Fehler, die die
# BS-Vereinheitlichung oben beseitigt hat. Deshalb hier zentral, nicht als
# Kopie je Skript.
CM_DAYS = 30              # Ziel-Laufzeit der Reihe
CM_DTE_MIN, CM_DTE_MAX = 7, 75   # zulaessige Spanne fuer Stuetzstellen
CM_SINGLE_TOL = 10        # nur EINE Stuetzstelle: max. Abstand zu CM_DAYS
DELTA_TOL = 0.08          # max. Abweichung vom Ziel-Delta, sonst unbrauchbar
VOL_PCTL = 0.5            # Volumen-Perzentilfilter gegen den Stale-Print-Bias


def cm_interp(v1, t1, v2, t2, t_target=CM_DAYS):
    """IV auf konstante Laufzeit interpolieren — linear in der TOTALEN VARIANZ.

    Linear in sigma^2*T (nicht in sigma), weil sich Varianz ueber die Zeit
    addiert; das ist dieselbe Interpolation, die der VIX fuer seine 30-Tage-
    Konstante nutzt. Linear in sigma laege bis zu 3 Vol-Punkte daneben.

    Ohne diesen Schritt misst die Reihe die Position im Verfallszyklus statt den
    Skew: die Laufzeit laeuft von ~46 Tagen auf ~10 herunter und springt beim
    Roll zurueck, die IV folgt der Term-Struktur mit."""
    if v1 is None or v2 is None or t1 is None or t2 is None or t1 == t2:
        return None
    if t1 > t2:
        v1, t1, v2, t2 = v2, t2, v1, t1
    w1, w2 = v1 * v1 * t1, v2 * v2 * t2
    var = w1 + (w2 - w1) * (t_target - t1) / (t2 - t1)
    if var <= 0 or t_target <= 0:
        return None
    return round(math.sqrt(var / t_target), 4)
