#!/usr/bin/env python3
"""
SeasonAlpha — Polymarket Refresh

Zieht fuer alle aktiven Maerkte im Katalog einen aktuellen Preis-Snapshot
aus der CLOB API und schreibt ihn nach Supabase polymarket_prices.

Nutzung:
    py scripts/polymarket_refresh.py                    # alle aktiven Maerkte
    py scripts/polymarket_refresh.py --category fed     # nur Fed-Maerkte
    py scripts/polymarket_refresh.py --refresh hourly   # nur hourly-Tier
    py scripts/polymarket_refresh.py --near-fomc-only   # nur wenn FOMC ±2d
    py scripts/polymarket_refresh.py --dry-run
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
    fetch_current_price,
    load_markets_yaml,
)
from shared.logger import app_logger, error_logger


def build_price_record(condition_id: str, snap: dict, ts: datetime) -> dict:
    return {
        "condition_id": condition_id,
        "ts": ts.isoformat(),
        "yes_price": snap["yes_price"],
        "volume_24h": snap.get("volume_24h"),
        "spread": snap.get("spread"),
        "source": "clob",
    }


def refresh_markets(
    entries: list[dict],
    dry_run: bool = False,
) -> tuple[int, list[str]]:
    """
    Schreibt Preis-Snapshots fuer die gegebenen YAML-Eintraege.
    Returns (success_count, errors).
    """
    from shared.supabase_client import (
        fetch_polymarket_markets as _fetch_catalog,
        upsert_polymarket_prices,
    )

    # Katalog aus DB laden (token_id-Mapping liegt dort)
    catalog = _fetch_catalog(active_only=False)
    by_cid = {c["condition_id"]: c for c in catalog}

    records = []
    errors: list[str] = []
    now = datetime.now(timezone.utc)

    for i, entry in enumerate(entries, 1):
        slug = entry["slug"]
        cid = (entry.get("condition_id") or "").strip()
        if not cid:
            app_logger.debug(f"skip {slug}: keine condition_id in YAML")
            continue

        cat_entry = by_cid.get(cid)
        if not cat_entry:
            errors.append(f"{slug}: nicht im DB-Katalog (erst 'polymarket_discover --sync-db' laufen lassen)")
            continue

        # fetch_current_price nimmt die conditionId (Gamma-Markets-Endpoint).
        # yes_token_id wird nur fuer CLOB prices-history gebraucht (Backfill).
        snap = fetch_current_price(cid)
        if not snap:
            errors.append(f"{slug}: fetch_current_price liefert None")
            print(f"  [{i:2d}/{len(entries)}] {slug:40s} -- FEHLER: kein Preis")
            continue

        rec = build_price_record(cid, snap, now)
        records.append(rec)
        print(
            f"  [{i:2d}/{len(entries)}] {slug:40s} "
            f"YES={snap['yes_price']:.3f}  "
            f"spread={snap.get('spread', 0) or 0:.3f}"
        )

    if records and not dry_run:
        upsert_polymarket_prices(records)

    return len(records), errors


def filter_entries(
    entries: list[dict],
    category: str | None = None,
    refresh_tier: str | None = None,
) -> list[dict]:
    out = entries
    if category:
        wanted = set(c.strip().lower() for c in category.split(","))
        out = [e for e in out if e.get("category", "").lower() in wanted]
    if refresh_tier:
        out = [e for e in out if e.get("refresh", "").lower() == refresh_tier.lower()]
    return out


def main():
    ap = argparse.ArgumentParser(description="Polymarket Refresh (Snapshot)")
    ap.add_argument("--category", default=None,
                    help="Komma-getrennte Liste: fed,macro,index,events,crypto")
    ap.add_argument("--refresh", default=None, choices=["hourly", "daily"],
                    help="Nur Maerkte dieses Refresh-Tiers")
    ap.add_argument("--near-fomc-only", action="store_true",
                    help="Nur ausfuehren wenn heute innerhalb des FOMC-Fensters liegt "
                         "(FOMC-Tag -2 bis +1). Sonst Early-Exit ohne Fehler.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Nichts in DB schreiben, nur logging")
    args = ap.parse_args()

    t0 = time.time()

    if args.near_fomc_only:
        from shared.fed_dates import is_near_fomc
        if not is_near_fomc():
            print(f"  [fomc-gate] Heute {datetime.now(timezone.utc).strftime('%Y-%m-%d')} "
                  f"nicht im FOMC-Fenster (+/-2d). Early-Exit.")
            # Auch der Skip hinterlaesst eine Zeile: der Health-Check erkennt am
            # Alter der letzten Zeile, ob der stuendliche Timer ueberhaupt laeuft.
            return 0 if _log_intraday(0, 0, [], t0, skip=True, dry_run=args.dry_run) else 1

    data = load_markets_yaml()
    entries = filter_entries(data.get("markets", []), args.category, args.refresh)

    print("=" * 60)
    print(f"  SeasonAlpha — Polymarket Refresh")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    if args.dry_run:
        print("  ** DRY RUN **")
    print(f"  Maerkte in Scope: {len(entries)}")
    if args.category:
        print(f"  Kategorie-Filter: {args.category}")
    if args.refresh:
        print(f"  Refresh-Tier:     {args.refresh}")
    print("=" * 60)

    if not entries:
        print("\n  Keine Maerkte im Scope.")
        if args.near_fomc_only:
            # Im FOMC-Fenster ohne Maerkte ist die YAML kaputt oder leer — ein Ausfall,
            # der sonst als stiller Erfolg ohne Log-Zeile durchginge.
            _log_intraday(0, 0, ["keine Maerkte im Scope (markets.yaml leer?)"], t0,
                          skip=False, dry_run=args.dry_run)
            return 1
        return 0

    try:
        success, errors = refresh_markets(entries, dry_run=args.dry_run)
    except Exception as e:
        # Schreibfehler der Snapshots: frueher ungefangen ohne Log-Zeile.
        success, errors = 0, [f"upsert/abruf abgebrochen: {e}"]
    elapsed = time.time() - t0

    print(f"\n{'=' * 60}")
    print(f"  Fertig! {success}/{len(entries)} Snapshots in {elapsed:.1f}s")
    if errors:
        print(f"  Fehler ({len(errors)}):")
        for err in errors:
            print(f"    - {err}")
    print("=" * 60)

    if errors:
        app_logger.info(f"polymarket_refresh: {success} ok, {len(errors)} Fehler")

    log_ok = True
    if args.near_fomc_only:
        log_ok = _log_intraday(len(entries), success, errors, t0, skip=False, dry_run=args.dry_run)

    # Gescheitert = gar kein Snapshot geschrieben. Einzelne Maerkte ohne Preis
    # (z. B. noch nicht im DB-Katalog) sind Dauerzustand und kein Ausfall.
    if success == 0 or not log_ok:
        return 1
    return 0


def _log_intraday(total: int, success: int, errors: list[str], t0: float,
                  skip: bool, dry_run: bool) -> bool:
    """refresh_log-Zeile run_type='polymarket_intraday' (nur im stuendlichen Modus)."""
    if dry_run:
        return True
    try:
        import json as _json
        from shared.supabase_client import get_client
        now = datetime.now(timezone.utc)
        get_client().table("refresh_log").insert({
            "run_date": now.strftime("%Y-%m-%d"),
            "run_type": "polymarket_intraday",
            "tickers_total": total,
            "tickers_success": success,
            "tickers_missing": len(errors),
            "missing_details": _json.dumps({"skip": "ausserhalb FOMC-Fenster"} if skip else {}),
            "auto_fixed": 0,
            "duration_seconds": round(time.time() - t0, 1),
            "errors": _json.dumps(errors[:20]),
        }).execute()
        return True
    except Exception as e:
        print(f"[polymarket] refresh_log insert failed: {e}")
        return False


if __name__ == "__main__":
    sys.exit(main())
