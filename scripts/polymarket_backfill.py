#!/usr/bin/env python3
"""
SeasonAlpha — Polymarket Historischer Backfill

Zieht die gesamte verfuegbare Preis-Historie pro Markt aus der CLOB
prices-history API und schreibt sie in Supabase polymarket_prices.

Idempotent: UPSERT auf (condition_id, ts) — mehrfaches Laufen ueberschreibt
gleiche Timestamps, fuegt neue hinzu. Kein Loeschen.

Nutzung:
    py scripts/polymarket_backfill.py                     # alle aktiven Maerkte
    py scripts/polymarket_backfill.py --slug fed-...      # einzelner Markt
    py scripts/polymarket_backfill.py --interval 1h       # statt 1d (mehr Granularitaet)
    py scripts/polymarket_backfill.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
import os
import pathlib
import time
from datetime import datetime, timezone

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.polymarket_data import (
    fetch_price_history,
    load_markets_yaml,
)
from shared.logger import app_logger


def history_to_records(
    condition_id: str,
    points: list[dict],
    source: str = "prices-history",
) -> list[dict]:
    """{t:unix, p:float} -> Supabase-Records."""
    out = []
    for pt in points:
        try:
            ts = datetime.fromtimestamp(int(pt["t"]), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            continue
        p = pt.get("p")
        if p is None:
            continue
        out.append({
            "condition_id": condition_id,
            "ts": ts.isoformat(),
            "yes_price": round(float(p), 4),
            "source": source,
        })
    return out


def backfill_markets(
    entries: list[dict],
    interval: str = "1d",
    fidelity: int = 1440,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Laedt fuer jeden Eintrag die gesamte Historie und schreibt sie in DB.

    Returns (total_records_written, markets_processed).
    """
    from shared.supabase_client import (
        fetch_polymarket_markets as _fetch_catalog,
        upsert_polymarket_prices,
    )

    catalog = _fetch_catalog(active_only=False)
    by_cid = {c["condition_id"]: c for c in catalog}

    total = 0
    processed = 0
    for i, entry in enumerate(entries, 1):
        slug = entry["slug"]
        cid = (entry.get("condition_id") or "").strip()
        if not cid:
            print(f"  [{i:2d}/{len(entries)}] {slug:40s}  -- skip (keine condition_id)")
            continue

        cat_entry = by_cid.get(cid)
        if not cat_entry:
            print(f"  [{i:2d}/{len(entries)}] {slug:40s}  -- skip (nicht im DB-Katalog)")
            continue

        yes_token = cat_entry.get("yes_token_id") or ""
        if not yes_token:
            print(f"  [{i:2d}/{len(entries)}] {slug:40s}  -- skip (kein yes_token_id)")
            continue

        points = fetch_price_history(yes_token, interval=interval, fidelity=fidelity)
        if not points:
            print(f"  [{i:2d}/{len(entries)}] {slug:40s}  -- keine Historie zurueck")
            continue

        records = history_to_records(cid, points, source="prices-history")
        if not records:
            print(f"  [{i:2d}/{len(entries)}] {slug:40s}  -- parse lieferte 0 Records")
            continue

        if not dry_run:
            upsert_polymarket_prices(records)

        total += len(records)
        processed += 1
        first_ts = records[0]["ts"][:10]
        last_ts = records[-1]["ts"][:10]
        print(
            f"  [{i:2d}/{len(entries)}] {slug:40s}  "
            f"{len(records):5d} pts  {first_ts} -> {last_ts}"
        )

    return total, processed


def main():
    ap = argparse.ArgumentParser(description="Polymarket Historischer Backfill")
    ap.add_argument("--slug", default=None, help="Nur diesen Slug backfillen")
    ap.add_argument("--category", default=None,
                    help="Komma-getrennte Liste: fed,macro,index,events,crypto")
    ap.add_argument("--interval", default="max", choices=["1h", "6h", "1d", "1w", "max"])
    ap.add_argument("--fidelity", type=int, default=1440,
                    help="Minuten-Aufloesung (60=stuendlich, 1440=taeglich)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load_markets_yaml()
    entries = data.get("markets", [])
    if args.slug:
        entries = [e for e in entries if e.get("slug") == args.slug]
    if args.category:
        wanted = set(c.strip().lower() for c in args.category.split(","))
        entries = [e for e in entries if e.get("category", "").lower() in wanted]

    print("=" * 60)
    print(f"  SeasonAlpha — Polymarket Backfill")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    if args.dry_run:
        print("  ** DRY RUN **")
    print(f"  Maerkte: {len(entries)}")
    print(f"  Interval/Fidelity: {args.interval} / {args.fidelity} min")
    print("=" * 60)

    if not entries:
        print("\n  Keine Maerkte in Scope.")
        return

    t0 = time.time()
    total, processed = backfill_markets(
        entries,
        interval=args.interval,
        fidelity=args.fidelity,
        dry_run=args.dry_run,
    )
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"  Fertig! {total} Datenpunkte aus {processed}/{len(entries)} Maerkten in {elapsed:.1f}s")
    print("=" * 60)
    app_logger.info(
        f"polymarket_backfill: {processed}/{len(entries)} Maerkte, {total} Punkte, {elapsed:.1f}s"
    )


if __name__ == "__main__":
    main()
