#!/usr/bin/env python3
"""
SeasonAlpha — Brier-Score Precompute
=====================================

Liest resolved markets + deren Preis-Historie aus Supabase, berechnet
Brier-Score-Aggregate und schreibt die Ergebnisse als JSON-File nach
landing/data/brier_stats.json. Das Frontend liest diese Datei direkt
(statisch via nginx), keine Supabase-Query im Browser.

Berechnungen:
  - Overall Brier + Benchmarks (Basisrate, 50-50)
  - Pro Kategorie (fed, macro, crypto, politics, other)
  - Kalibrierungs-Kurve (10 Buckets, Reliability-Diagramm)
  - Brier aufgeschluesselt nach Zeit-zu-Resolution

Sampling der Forecasts pro Market:
  - Variante "snapshot": letzter Preis pro Tag (Daily-Aggregation aus Historie)
  - Dadurch bekommen wir ~30-365 Forecasts pro Market, nicht Millionen.

Nutzung:
    py scripts/compute_brier_stats.py            # alle Kategorien
    py scripts/compute_brier_stats.py --dry-run  # nur berechnen, nichts schreiben
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.brier_score import (
    brier_score_mean,
    calibration_curve,
    brier_by_days_to_resolution,
    naive_baseline_brier,
    random_50_50_brier,
)
from shared.logger import app_logger, error_logger


OUTPUT_PATH = pathlib.Path(_project_dir) / "landing" / "data" / "brier_stats.json"


def _parse_ts(s: str | datetime | None) -> datetime | None:
    if not s:
        return None
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def load_data():
    """Markets + Preis-Historie aus Supabase ziehen (paginiert)."""
    from shared.supabase_client import get_client
    client = get_client()

    # Markets paginiert (PostgREST-Default cappt sonst bei 1000)
    markets: list[dict] = []
    PAGE = 1000
    offset = 0
    while True:
        batch = (
            client.table("polymarket_resolved_markets")
            .select("*")
            .range(offset, offset + PAGE - 1)
            .execute()
            .data or []
        )
        if not batch:
            break
        markets.extend(batch)
        if len(batch) < PAGE:
            break
        offset += PAGE
    print(f"Markets geladen: {len(markets)}")

    # Preise paginiert (ueber viele tausend Zeilen)
    all_prices: list[dict] = []
    PAGE = 1000
    offset = 0
    while True:
        batch = (
            client.table("polymarket_resolved_prices")
            .select("*")
            .order("ts")
            .range(offset, offset + PAGE - 1)
            .execute()
            .data or []
        )
        if not batch:
            break
        all_prices.extend(batch)
        if len(batch) < PAGE:
            break
        offset += PAGE
    print(f"Preise geladen: {len(all_prices)}")

    return markets, all_prices


def build_daily_snapshots(prices_by_cid: dict[str, list[dict]]) -> dict[str, list[tuple[datetime, float]]]:
    """
    Reduziert Preis-Zeitreihe auf 1 Snapshot pro Tag (letzter Preis des Tages).
    Das verhindert dass Markets mit stuendlicher Historie unverhaeltnismaessig
    im Aggregat gewichtet werden.
    """
    out: dict[str, list[tuple[datetime, float]]] = {}
    for cid, rows in prices_by_cid.items():
        by_day: dict[str, tuple[datetime, float]] = {}
        for r in rows:
            ts = _parse_ts(r.get("ts"))
            if ts is None:
                continue
            day = ts.date().isoformat()
            price = float(r.get("yes_price", 0))
            # "letzter Preis des Tages" — spaeterer ts gewinnt
            prev = by_day.get(day)
            if prev is None or ts > prev[0]:
                by_day[day] = (ts, price)
        out[cid] = sorted(by_day.values(), key=lambda x: x[0])
    return out


def flatten_forecasts(markets: list[dict], snapshots: dict) -> list[tuple[datetime, float, datetime, bool, str]]:
    """
    Flacht alle Market-Snapshots zu einer Liste (ts, prob, resolution_date, outcome, category).
    """
    flat: list[tuple[datetime, float, datetime, bool, str]] = []
    for m in markets:
        cid = m.get("condition_id")
        if not cid or cid not in snapshots:
            continue
        res = _parse_ts(m.get("resolution_date") or m.get("end_date"))
        if res is None:
            continue
        outcome = bool(m.get("outcome_yes"))
        cat = m.get("category") or "other"
        for ts, price in snapshots[cid]:
            flat.append((ts, price, res, outcome, cat))
    return flat


def compute_stats(markets: list[dict], prices: list[dict]) -> dict:
    """Berechnet das komplette Stats-Objekt fuer den Frontend-Konsum."""
    # 1. Snapshots indexieren
    prices_by_cid: dict[str, list[dict]] = {}
    for r in prices:
        cid = r.get("condition_id")
        if cid:
            prices_by_cid.setdefault(cid, []).append(r)
    snapshots = build_daily_snapshots(prices_by_cid)

    # 2. Forecasts flatten
    flat = flatten_forecasts(markets, snapshots)
    print(f"Forecasts (daily snapshots): {len(flat)}")

    if not flat:
        return {"error": "no_data"}

    items = [(p, o) for _ts, p, _res, o, _cat in flat]
    outcomes = [o for _, o in items]

    # 3. Overall
    overall_brier = brier_score_mean(items)
    baseline = naive_baseline_brier(outcomes)
    base_rate = sum(1 for o in outcomes if o) / len(outcomes)

    # 4. Pro Kategorie
    by_cat: dict[str, list[tuple[float, bool]]] = {}
    for _ts, p, _res, o, cat in flat:
        by_cat.setdefault(cat, []).append((p, o))
    cat_stats = []
    for cat, pairs in sorted(by_cat.items(), key=lambda x: -len(x[1])):
        cat_outcomes = [o for _, o in pairs]
        cat_stats.append({
            "category": cat,
            "forecasts": len(pairs),
            "markets": sum(1 for m in markets if m.get("category") == cat),
            "brier": round(brier_score_mean(pairs) or 0, 4),
            "baseline": naive_baseline_brier(cat_outcomes),
            "base_rate": round(sum(1 for o in cat_outcomes if o) / len(cat_outcomes), 4),
        })

    # 5. Kalibrierungs-Kurve (10 Buckets)
    curve = calibration_curve(items, n_bins=10)

    # 6. Brier nach Zeit-zu-Resolution
    time_buckets = brier_by_days_to_resolution(
        [(ts, p, res, o) for ts, p, res, o, _c in flat],
        bucket_days=[7, 30, 90, 180, 365],
    )

    # 7. Meta
    dates = sorted([m.get("resolution_date") for m in markets if m.get("resolution_date")])
    meta = {
        "markets_count": len(markets),
        "forecasts_count": len(flat),
        "date_range": {
            "earliest": dates[0] if dates else None,
            "latest": dates[-1] if dates else None,
        },
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "meta": meta,
        "overall": {
            "brier": round(overall_brier or 0, 4),
            "baseline_brier": baseline,
            "random_50_50_brier": random_50_50_brier(),
            "base_rate": round(base_rate, 4),
        },
        "by_category": cat_stats,
        "calibration": curve,
        "time_to_resolution": time_buckets,
    }


def main():
    ap = argparse.ArgumentParser(description="Precompute Brier-Score-Aggregate")
    ap.add_argument("--dry-run", action="store_true", help="Nur berechnen, nichts in JSON schreiben")
    args = ap.parse_args()

    print("=" * 60)
    print("  SeasonAlpha — Brier-Score Precompute")
    print(f"  Output: {OUTPUT_PATH}")
    if args.dry_run:
        print("  ** DRY RUN **")
    print("=" * 60)

    markets, prices = load_data()
    if not markets:
        print("\nKeine resolved markets in DB — Scraper muss zuerst laufen.")
        return

    stats = compute_stats(markets, prices)

    # Guard: wenn keine Forecasts (z.B. nach --skip-prices Scrape) → sauber exitieren
    if stats.get("error") == "no_data" or stats.get("meta", {}).get("forecasts_count", 0) == 0:
        print("\n-- Ergebnisse --")
        print(f"  {len(markets)} Markets in DB, aber 0 Forecasts (Preis-Historie fehlt).")
        print("  Scraper ohne --skip-prices starten, dann erneut compute_brier_stats.")
        return

    print("\n-- Ergebnisse --")
    print(f"  Overall Brier: {stats['overall']['brier']}")
    print(f"  vs Baseline:   {stats['overall']['baseline_brier']}")
    print(f"  vs 50-50:      {stats['overall']['random_50_50_brier']}")
    print(f"  Basisrate:     {stats['overall']['base_rate']*100:.1f}% YES")
    print(f"\n  Pro Kategorie:")
    for c in stats["by_category"]:
        print(f"    {c['category']:10s}  brier={c['brier']:.4f}  baseline={c['baseline']}  n={c['forecasts']}")
    print(f"\n  Kalibrierungs-Buckets (10):")
    for b in stats["calibration"]:
        if b["count"]:
            print(f"    [{b['bin_lo']:.1f}-{b['bin_hi']:.1f}]  avg_p={b['avg_prob']}  obs={b['observed_freq']}  n={b['count']}")

    if args.dry_run:
        print("\n(dry-run) Nicht in JSON geschrieben.")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, default=str)
    print(f"\n-> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
