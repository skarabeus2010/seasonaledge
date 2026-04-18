"""
shared/brier_score.py — Brier-Score + Kalibrierungs-Metriken
=============================================================

Misst wie gut Polymarket-YES-Preise als Wahrscheinlichkeitsschaetzer
kalibriert sind. Input: resolved markets mit Preis-Historie + finalem
Outcome (YES/NO).

Kern-Formel: Brier = mean((p - o)^2)
  p = YES-Wahrscheinlichkeit (0..1), o = actual outcome (0 oder 1).
  Perfekter Forecaster: Brier = 0.
  Naive 50-50-Guess: Brier = 0.25.
  Schlechtest moeglich (100% falsch): Brier = 1.0.

Zusaetzlich: Reliability-Diagramm (Kalibrierungs-Buckets) und Brier
aufgeschluesselt nach Zeit-zu-Resolution.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable


# ── Einzel-Score ──────────────────────────────────────────────────────────────

def brier_score_single(probability: float, outcome: bool) -> float:
    """(p - o)^2 fuer eine einzelne Prognose."""
    o = 1.0 if outcome else 0.0
    return (float(probability) - o) ** 2


def brier_score_mean(items: Iterable[tuple[float, bool]]) -> float | None:
    """
    Mittlerer Brier-Score ueber (p, outcome)-Paare.
    Returns None wenn leer.
    """
    total = 0.0
    n = 0
    for p, o in items:
        total += brier_score_single(p, o)
        n += 1
    return total / n if n else None


# ── Kalibrierungs-Kurve (Reliability-Diagramm) ────────────────────────────────

def calibration_curve(
    items: Iterable[tuple[float, bool]],
    n_bins: int = 10,
) -> list[dict]:
    """
    Buckets ueber [0,1] in n_bins gleich-breite Faecher. Pro Bucket:
        avg_prob       = mittlere prognostizierte Wahrscheinlichkeit
        observed_freq  = Anteil positiver Outcomes
        count          = Anzahl Forecasts im Bucket

    Ein perfekt kalibrierter Forecaster hat avg_prob == observed_freq
    in jedem Bucket → Punkte liegen auf der Diagonale (0,0)-(1,1).
    """
    buckets: list[dict] = [
        {"bin_lo": i / n_bins, "bin_hi": (i + 1) / n_bins,
         "sum_prob": 0.0, "sum_obs": 0, "count": 0}
        for i in range(n_bins)
    ]
    for p, o in items:
        p = max(0.0, min(1.0, float(p)))
        idx = min(n_bins - 1, int(p * n_bins))
        b = buckets[idx]
        b["sum_prob"] += p
        b["sum_obs"] += 1 if o else 0
        b["count"] += 1

    out: list[dict] = []
    for b in buckets:
        n = b["count"]
        out.append({
            "bin_lo": round(b["bin_lo"], 4),
            "bin_hi": round(b["bin_hi"], 4),
            "avg_prob": round(b["sum_prob"] / n, 4) if n else None,
            "observed_freq": round(b["sum_obs"] / n, 4) if n else None,
            "count": n,
        })
    return out


# ── Brier als Funktion der Zeit-zu-Resolution ─────────────────────────────────

def brier_by_days_to_resolution(
    forecasts: Iterable[tuple[datetime, float, datetime, bool]],
    bucket_days: list[int] | None = None,
) -> list[dict]:
    """
    Aggregiert Brier-Scores nach Abstand zur Resolution.

    Input pro forecast: (ts, probability, resolution_date, outcome)

    bucket_days definiert die Bucket-Obergrenzen in Tagen. Default:
      [7, 30, 90, 180, 365, float('inf')]
      → Labels: "<=7d", "<=30d", ... ">365d"

    Returns list mit {bucket_label, avg_days, brier, count}.
    """
    if bucket_days is None:
        bucket_days = [7, 30, 90, 180, 365]

    # Buckets: (limit_days, label)
    limits: list[tuple[float, str]] = []
    prev = 0
    for d in bucket_days:
        limits.append((float(d), f"{prev}-{d}d"))
        prev = d
    limits.append((float("inf"), f">{bucket_days[-1]}d"))

    agg: dict[str, dict] = {lbl: {"sum_brier": 0.0, "sum_days": 0.0, "count": 0}
                             for _, lbl in limits}

    for ts, p, res, o in forecasts:
        if not isinstance(ts, datetime) or not isinstance(res, datetime):
            continue
        delta_days = (res - ts).total_seconds() / 86400.0
        if delta_days < 0:
            continue
        label = next(lbl for lim, lbl in limits if delta_days <= lim)
        agg[label]["sum_brier"] += brier_score_single(p, o)
        agg[label]["sum_days"] += delta_days
        agg[label]["count"] += 1

    out: list[dict] = []
    for _, label in limits:
        a = agg[label]
        out.append({
            "bucket": label,
            "avg_days": round(a["sum_days"] / a["count"], 2) if a["count"] else None,
            "brier": round(a["sum_brier"] / a["count"], 4) if a["count"] else None,
            "count": a["count"],
        })
    return out


# ── Benchmarks (fuer UI-Vergleich) ────────────────────────────────────────────

def naive_baseline_brier(outcomes: Iterable[bool]) -> float | None:
    """
    Brier fuer einen Baseline-Forecaster, der immer die **Basisrate** prognostiziert.
    Das ist die theoretisch beste konstante Prognose.
    Brier = p*(1-p) wo p = Anteil positiver Outcomes.
    """
    outcomes = list(outcomes)
    if not outcomes:
        return None
    base = sum(1 for o in outcomes if o) / len(outcomes)
    return round(base * (1 - base), 4)


def random_50_50_brier() -> float:
    """Brier fuer 'immer 50-50' — klassischer Referenzwert."""
    return 0.25


__all__ = [
    "brier_score_single",
    "brier_score_mean",
    "calibration_curve",
    "brier_by_days_to_resolution",
    "naive_baseline_brier",
    "random_50_50_brier",
]
