#!/usr/bin/env python3
"""
SeasonAlpha — Polymarket Discovery

Fuellt condition_id's in shared/polymarket_markets.yaml fuer Eintraege die
noch keine ID haben. Sucht via Gamma API nach den in search_terms angegebenen
Keywords und nimmt den liquidesten Treffer.

Nutzung:
    py scripts/polymarket_discover.py                  # Report: was fehlt?
    py scripts/polymarket_discover.py --update-yaml    # IDs eintragen + Katalog in DB schreiben
    py scripts/polymarket_discover.py --slug fed-decision-next-cut --interactive
"""
from __future__ import annotations

import argparse
import sys
import os
import pathlib
import json

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.polymarket_data import (
    fetch_markets_by_tag,
    fetch_market_detail,
    normalize_market,
    load_markets_yaml,
    save_markets_yaml,
)
from shared.logger import app_logger


# ── Gamma-Tag-Mapping pro YAML-Kategorie ──────────────────────────────────────

CATEGORY_TAGS = {
    "fed":    ["fed", "us-economic-policy", "economy"],
    "macro":  ["economy", "us-economic-policy", "recession"],
    "index":  ["sp500", "stocks", "us-economic-policy"],
    "events": ["cpi", "jobs-report", "economy"],
    "crypto": ["crypto-prices", "bitcoin", "ethereum"],
}


def _score_match(market: dict, search_terms: list[str]) -> float:
    """Wie gut passt ein Gamma-Market zu den Suchbegriffen?"""
    text = " ".join([
        str(market.get("question", "")),
        str(market.get("title", "")),
        str(market.get("slug", "")),
        str(market.get("description", "")),
    ]).lower()
    if not text.strip():
        return 0.0
    hits = sum(1 for term in search_terms if term.lower() in text)
    # Bonus: Liquiditaet (logarithmisch bis 1.0)
    liquidity = 0.0
    try:
        liquidity = float(market.get("liquidity") or market.get("liquidity_num") or 0.0)
    except (TypeError, ValueError):
        liquidity = 0.0
    import math
    liq_score = min(1.0, math.log10(max(1.0, liquidity)) / 6.0) if liquidity > 0 else 0.0
    return hits + liq_score


def find_candidate(entry: dict) -> dict | None:
    """
    Sucht den besten Gamma-Market fuer einen YAML-Eintrag.
    Geht alle Tags der Kategorie durch, sammelt Kandidaten, scored nach
    Keyword-Match + Liquiditaet.
    """
    cat = entry.get("category", "")
    tags = CATEGORY_TAGS.get(cat, ["economy"])
    terms = entry.get("search_terms", []) or []
    seen: dict[str, dict] = {}

    for tag in tags:
        sample = fetch_markets_by_tag(tag=tag, active=True, closed=False, limit=200)
        for m in sample:
            cid = m.get("condition_id") or m.get("conditionId") or m.get("id") or ""
            if not cid:
                continue
            if cid in seen:
                continue
            seen[cid] = m

    if not seen:
        return None

    scored = [
        (mid, m, _score_match(m, terms))
        for mid, m in seen.items()
    ]
    scored.sort(key=lambda x: x[2], reverse=True)
    top = scored[0]
    if top[2] < 0.5:
        return None
    return top[1]


def sync_catalog_to_db(data: dict) -> int:
    """
    Schreibt alle Eintraege aus YAML (mit condition_id) in Supabase
    polymarket_markets.
    """
    from shared.supabase_client import upsert_polymarket_markets

    records = []
    for entry in data.get("markets", []):
        cid = (entry.get("condition_id") or "").strip()
        if not cid:
            continue
        # Volle Metadata von CLOB holen (end_date, token_ids, liquiditaet)
        raw = fetch_market_detail(cid)
        if not raw:
            app_logger.debug(f"skip {entry['slug']}: kein CLOB-Detail fuer {cid}")
            continue
        norm = normalize_market(raw)
        records.append({
            "condition_id": norm["condition_id"],
            "slug": entry["slug"],
            "question": norm["question"] or entry.get("question", ""),
            "category": entry["category"],
            "end_date": norm["end_date"],
            "yes_token_id": norm["yes_token_id"],
            "no_token_id": norm["no_token_id"],
            "liquidity_usd": norm["liquidity_usd"],
            "volume_total_usd": norm["volume_total_usd"],
            "meta": norm["meta"],
            "active": True,
        })

    if records:
        upsert_polymarket_markets(records)
    return len(records)


def main():
    ap = argparse.ArgumentParser(description="Polymarket Discovery & YAML-Updater")
    ap.add_argument("--update-yaml", action="store_true",
                    help="Leere condition_id's in YAML automatisch fuellen")
    ap.add_argument("--sync-db", action="store_true",
                    help="YAML-Eintraege in Supabase polymarket_markets schreiben")
    ap.add_argument("--slug", default=None,
                    help="Nur diesen einen Slug bearbeiten")
    ap.add_argument("--interactive", action="store_true",
                    help="Top-5-Kandidaten zeigen, manuell auswaehlen")
    ap.add_argument("--dry-run", action="store_true",
                    help="Nichts schreiben, nur Report")
    args = ap.parse_args()

    data = load_markets_yaml()
    entries = data.get("markets", [])

    target = [e for e in entries if not args.slug or e.get("slug") == args.slug]
    if not target:
        print(f"Kein Eintrag mit slug={args.slug} gefunden")
        sys.exit(1)

    missing = [e for e in target if not (e.get("condition_id") or "").strip()]
    filled = [e for e in target if (e.get("condition_id") or "").strip()]

    print("=" * 60)
    print("  Polymarket Discovery")
    print("=" * 60)
    print(f"  Eintraege:     {len(target)}")
    print(f"  Mit ID:        {len(filled)}")
    print(f"  Ohne ID:       {len(missing)}")
    print()

    if args.update_yaml and missing:
        print(f"  Suche IDs fuer {len(missing)} Eintraege...")
        changed = 0
        for entry in missing:
            slug = entry["slug"]
            print(f"  -> {slug}  (category={entry['category']}, terms={entry['search_terms']})")
            cand = find_candidate(entry)
            if not cand:
                print(f"     kein passender Kandidat gefunden")
                continue
            cid = cand.get("condition_id") or cand.get("conditionId") or cand.get("id") or ""
            q = (cand.get("question") or cand.get("title") or "")[:100]
            print(f"     Match: {q}")
            print(f"     cid:   {cid}")
            if not args.dry_run:
                entry["condition_id"] = cid
                entry["question"] = q
                changed += 1

        if changed and not args.dry_run:
            save_markets_yaml(data)
            print(f"\n  YAML aktualisiert: {changed} Eintraege")

    if args.sync_db:
        print("\n  Syncing Katalog zu Supabase polymarket_markets...")
        if args.dry_run:
            print("  (dry-run) -- skip")
        else:
            n = sync_catalog_to_db(data)
            print(f"  {n} Eintraege in DB upserted")

    if not args.update_yaml and not args.sync_db:
        print("  (Report-only: nutze --update-yaml und/oder --sync-db fuer Aktionen)")
        if missing:
            print("\n  Fehlende condition_id's:")
            for e in missing:
                print(f"    - {e['slug']:40s}  [{e['category']}]")


if __name__ == "__main__":
    main()
