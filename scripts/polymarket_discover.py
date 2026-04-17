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
    fetch_events_by_tag,
    fetch_event_detail,
    fetch_market_by_condition_id,
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


# Module-Cache: pro Tag einmal Events+Markets holen, fuer alle Slugs wiederverwenden.
# Key = tag_slug, Value = list[market_raw_dict]
_TAG_MARKETS_CACHE: dict[str, list[dict]] = {}

# Max Events pro Tag die wir per event_detail aufloesen (Liquiditaets-Top sortiert)
_MAX_EVENTS_PER_TAG = 80


def _markets_for_tag(tag_slug: str) -> list[dict]:
    """
    Alle aktiven Markets unter einem Tag.

    Geht events?tag_slug -> events/{id} um an markets[] zu kommen.
    Cached module-global, damit 30 YAML-Slugs nicht 30x denselben Tag fetchen.
    """
    if tag_slug in _TAG_MARKETS_CACHE:
        return _TAG_MARKETS_CACHE[tag_slug]

    events = fetch_events_by_tag(tag_slug=tag_slug, active=True, closed=False, limit=200)

    # Nach Liquiditaet auf Event-Ebene vorsortieren (Top-Events zuerst),
    # dann pro Event Detail holen. Limit auf _MAX_EVENTS_PER_TAG kappt API-Flood.
    def _ev_liq(ev: dict) -> float:
        try:
            return float(ev.get("liquidity") or ev.get("liquidityNum") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    events_sorted = sorted(events, key=_ev_liq, reverse=True)[:_MAX_EVENTS_PER_TAG]

    markets: list[dict] = []
    for ev in events_sorted:
        # Viele Events liefern markets[] schon im Listing — wenn ja, sparen wir
        # uns den Detail-Roundtrip.
        embedded = ev.get("markets")
        if isinstance(embedded, list) and embedded:
            markets.extend(embedded)
            continue
        eid = ev.get("id")
        if not eid:
            continue
        detail = fetch_event_detail(eid)
        if not detail:
            continue
        mk = detail.get("markets") or []
        if isinstance(mk, list):
            markets.extend(mk)

    _TAG_MARKETS_CACHE[tag_slug] = markets
    app_logger.debug(f"polymarket tag={tag_slug} -> {len(events_sorted)} events, {len(markets)} markets")
    return markets


def _score_match(market: dict, search_terms: list[str]) -> float:
    """Wie gut passt ein Gamma-Market zu den Suchbegriffen?"""
    text = " ".join([
        str(market.get("question", "")),
        str(market.get("title", "")),
        str(market.get("slug", "")),
        str(market.get("description", "")),
        str(market.get("groupItemTitle", "")),  # Bei Multi-Outcome-Events ("1 cut", "2 cuts")
    ]).lower()
    if not text.strip():
        return 0.0
    hits = sum(1 for term in search_terms if term.lower() in text)
    # Bonus: Liquiditaet (logarithmisch bis 1.0)
    liquidity = 0.0
    try:
        liquidity = float(
            market.get("liquidityNum")
            or market.get("liquidity")
            or market.get("liquidity_num")
            or 0.0
        )
    except (TypeError, ValueError):
        liquidity = 0.0
    import math
    liq_score = min(1.0, math.log10(max(1.0, liquidity)) / 6.0) if liquidity > 0 else 0.0
    return hits + liq_score


def find_candidate(entry: dict) -> dict | None:
    """
    Sucht den besten Gamma-Market fuer einen YAML-Eintrag.
    Geht alle Tags der Kategorie durch (via Events-API), sammelt Markets
    aller Events und scored nach Keyword-Match + Liquiditaet.
    """
    cat = entry.get("category", "")
    tags = CATEGORY_TAGS.get(cat, ["economy"])
    terms = entry.get("search_terms", []) or []
    seen: dict[str, dict] = {}

    for tag in tags:
        for m in _markets_for_tag(tag):
            cid = m.get("conditionId") or m.get("condition_id") or ""
            if not cid or cid in seen:
                continue
            # Geschlossene/inaktive Markets fuer Discovery ausschliessen
            if m.get("closed") is True or m.get("active") is False:
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


def find_top_candidates(entry: dict, n: int = 5) -> list[tuple[dict, float]]:
    """Top-N Kandidaten fuer --interactive-Modus."""
    cat = entry.get("category", "")
    tags = CATEGORY_TAGS.get(cat, ["economy"])
    terms = entry.get("search_terms", []) or []
    seen: dict[str, dict] = {}
    for tag in tags:
        for m in _markets_for_tag(tag):
            cid = m.get("conditionId") or m.get("condition_id") or ""
            if not cid or cid in seen:
                continue
            if m.get("closed") is True or m.get("active") is False:
                continue
            seen[cid] = m
    scored = [(m, _score_match(m, terms)) for m in seen.values()]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:n]


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
        # Volle Metadata von Gamma holen (end_date, token_ids, liquiditaet)
        raw = fetch_market_by_condition_id(cid)
        if not raw:
            app_logger.debug(f"skip {entry['slug']}: kein Gamma-Detail fuer {cid}")
            continue
        norm = normalize_market(raw)
        # YAML-seitige Metadata in meta mergen (event_id fuer Gruppierung im Frontend)
        meta = dict(norm["meta"] or {})
        if entry.get("event_id"):
            meta["event_id"] = entry["event_id"]
        if entry.get("refresh"):
            meta["refresh"] = entry["refresh"]
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
            "meta": meta,
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
