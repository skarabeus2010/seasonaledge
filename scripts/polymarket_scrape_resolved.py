#!/usr/bin/env python3
"""
SeasonAlpha — Polymarket Resolved Markets Scraper
==================================================

Zieht bereits aufgeloeste Polymarket-Markets aus der Gamma-API + deren
Preis-Historie aus der CLOB-API und schreibt sie in:
  polymarket_resolved_markets (Katalog)
  polymarket_resolved_prices  (Zeitreihe)

Verwendung: Datengrundlage fuer Brier-Score / Kalibrierungs-Analyse.

Filter:
  - closed=true + active=false (d.h. Markt ist geschlossen)
  - outcomePrices liefert eindeutige Resolution (["1","0"] oder ["0","1"])
  - Binary (genau 2 Outcomes)
  - Volume >= MIN_VOLUME (Ghost-Markets ausschliessen)
  - Resolution innerhalb REG_START_DATE..REG_END_DATE

Scope (Plan A — breites Sample ueber alle Kategorien):
  Tags: fed, economy, crypto, crypto-prices, us-politics, politics, sports
  Zeitraum: 2024-01-01 .. heute

Nutzung:
    py scripts/polymarket_scrape_resolved.py                # alle Tags
    py scripts/polymarket_scrape_resolved.py --tag crypto   # nur ein Tag
    py scripts/polymarket_scrape_resolved.py --dry-run
    py scripts/polymarket_scrape_resolved.py --skip-prices  # nur Metadaten, keine Historie

Windows: PYTHONIOENCODING=utf-8 setzen (Pfeile/Sonderzeichen in Titles).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from datetime import datetime, timezone

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.polymarket_data import (
    fetch_events_by_tag,
    fetch_event_detail,
    fetch_price_history,
    _extract_token_ids,
    _safe_float,
)
from shared.logger import app_logger, error_logger


# ── Konfiguration ─────────────────────────────────────────────────────────────

SCOPE_TAGS = [
    "fed",
    "economy",
    "crypto",
    "crypto-prices",
    "us-politics",
    "politics",
]

RES_START = datetime(2024, 1, 1, tzinfo=timezone.utc)
RES_END = datetime.now(timezone.utc)
MIN_VOLUME = 10_000.0   # USD — darunter sind Ghost-Markets
PER_TAG_LIMIT = 500     # Max Events pro Tag-Abruf
GAMMA_PAGE = 100        # Events-API Page-Groesse


# ── Helper ────────────────────────────────────────────────────────────────────

def _parse_outcome(outcome_prices) -> bool | None:
    """
    outcomePrices ist typisch ein JSON-String wie '["1", "0"]'.
    Index 0 = YES, Index 1 = NO (Polymarket-Konvention).
    Returns True wenn YES resolved, False wenn NO, None bei unklarem Format.
    """
    if outcome_prices is None:
        return None
    try:
        if isinstance(outcome_prices, str):
            outcome_prices = json.loads(outcome_prices)
        if not isinstance(outcome_prices, (list, tuple)) or len(outcome_prices) != 2:
            return None
        yes_p = float(outcome_prices[0])
        no_p = float(outcome_prices[1])
    except (ValueError, TypeError):
        return None
    # Eindeutig: genau einer ist 1, der andere 0
    if yes_p >= 0.99 and no_p <= 0.01:
        return True
    if no_p >= 0.99 and yes_p <= 0.01:
        return False
    return None  # nicht sauber aufgeloest (z.B. partial)


def _is_binary_market(m: dict) -> bool:
    """Genau 2 Outcomes, typisch YES/NO."""
    outcomes = m.get("outcomes")
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except (ValueError, TypeError):
            return False
    return isinstance(outcomes, list) and len(outcomes) == 2


def _parse_date(s: str | None):
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    # Falls TZ fehlt, UTC annehmen (Gamma-API liefert inkonsistent)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _guess_category(tag_slug: str, question: str) -> str:
    """
    Mappe Tag-Slug auf unsere Kategorien. Fallback via Keyword im Titel.
    """
    t = tag_slug.lower()
    q = (question or "").lower()
    if t == "fed" or "fed" in q or "fomc" in q or "rate cut" in q:
        return "fed"
    if t == "economy" or "recession" in q or "gdp" in q or "inflation" in q or "unemployment" in q:
        return "macro"
    if t in ("crypto", "crypto-prices") or "bitcoin" in q or "ethereum" in q or "btc" in q or "eth" in q or "solana" in q:
        return "crypto"
    if t in ("us-politics", "politics") or "election" in q or "president" in q or "senate" in q or "congress" in q:
        return "politics"
    return "other"


# ── Ein-Event-Processing ──────────────────────────────────────────────────────

def process_event(event: dict, tag_slug: str) -> list[dict]:
    """
    Holt markets[] fuer ein Event, filtert auf binary + resolved + im Zeitfenster.

    Returns Liste von dicts mit allen Feldern fuer polymarket_resolved_markets
    plus 'yes_token_id' (nicht persistiert, wird fuer Historie gebraucht).
    """
    eid = event.get("id")
    if eid is None:
        return []
    detail = fetch_event_detail(eid)
    if not detail or not detail.get("markets"):
        return []

    out: list[dict] = []
    for m in detail.get("markets") or []:
        if not m.get("closed"):
            continue
        if not _is_binary_market(m):
            continue
        outcome_yes = _parse_outcome(m.get("outcomePrices"))
        if outcome_yes is None:
            continue

        end_date = _parse_date(m.get("endDateIso") or m.get("endDate"))
        if not end_date:
            continue
        if end_date < RES_START or end_date > RES_END:
            continue

        vol = _safe_float(m.get("volumeNum") or m.get("volume"))
        if vol is None or vol < MIN_VOLUME:
            continue

        cid = m.get("conditionId")
        if not cid:
            continue

        yes_token, no_token = _extract_token_ids(m.get("clobTokenIds"))
        if not yes_token:
            continue

        question = m.get("question") or ""
        category = _guess_category(tag_slug, question)

        out.append({
            "condition_id": cid,
            "slug": m.get("slug"),
            "question": question,
            "category": category,
            "event_id": int(eid) if str(eid).isdigit() else None,
            "end_date": end_date.isoformat(),
            "resolution_date": end_date.isoformat(),
            "outcome_yes": outcome_yes,
            "volume_total_usd": vol,
            "meta": {
                "tag_slug": tag_slug,
                "gamma_id": m.get("id"),
                "neg_risk": m.get("negRisk"),
            },
            "yes_token_id": yes_token,  # wird fuer Preis-Historie genutzt
        })

    return out


# ── Hauptablauf ───────────────────────────────────────────────────────────────

def scrape_tag(tag_slug: str) -> list[dict]:
    """Zieht alle closed Events fuer einen Tag + extrahiert qualifizierte Markets."""
    print(f"\n== Tag: {tag_slug} ==")
    all_markets: list[dict] = []
    offset = 0
    events_seen = 0
    while True:
        events = fetch_events_by_tag(
            tag_slug=tag_slug,
            active=False,
            closed=True,
            limit=GAMMA_PAGE,
            offset=offset,
        )
        if not events:
            break
        events_seen += len(events)
        for ev in events:
            markets = process_event(ev, tag_slug)
            if markets:
                all_markets.extend(markets)
        if len(events) < GAMMA_PAGE or events_seen >= PER_TAG_LIMIT:
            break
        offset += GAMMA_PAGE

    print(f"  {events_seen} Events gesehen -> {len(all_markets)} qualifizierte Markets")
    return all_markets


def fetch_history_for_market(m: dict) -> list[dict]:
    """
    Holt CLOB prices-history fuer ein resolved market und baut Zeilen fuer
    polymarket_resolved_prices.
    """
    yes_token = m.get("yes_token_id")
    if not yes_token:
        return []
    history = fetch_price_history(yes_token, interval="max", fidelity=1440)
    rows: list[dict] = []
    for pt in history:
        ts_s = pt.get("t")
        price = pt.get("p")
        if ts_s is None or price is None:
            continue
        try:
            ts = datetime.fromtimestamp(int(ts_s), tz=timezone.utc)
        except (ValueError, OSError, TypeError):
            continue
        # Sicherstellen dass ts <= resolution_date (manche Markets liefern
        # auch Post-Resolution-Snapshots, die klemmen wir ab).
        res = _parse_date(m.get("resolution_date"))
        if res and ts > res:
            continue
        rows.append({
            "condition_id": m["condition_id"],
            "ts": ts.isoformat(),
            "yes_price": round(float(price), 4),
        })
    return rows


def strip_token(m: dict) -> dict:
    """Entfernt yes_token_id vor dem DB-Upsert (nicht Teil des Schemas)."""
    m2 = dict(m)
    m2.pop("yes_token_id", None)
    return m2


def main() -> None:
    ap = argparse.ArgumentParser(description="Scrape resolved Polymarket markets for Brier-Score.")
    ap.add_argument("--tag", default=None, help=f"Einzelner Tag (default: alle {len(SCOPE_TAGS)})")
    ap.add_argument("--dry-run", action="store_true", help="Nur lesen, nicht in DB schreiben")
    ap.add_argument("--skip-prices", action="store_true", help="Nur Metadaten scrapen, keine CLOB prices-history")
    args = ap.parse_args()

    tags = [args.tag] if args.tag else SCOPE_TAGS

    print("=" * 60)
    print("  SeasonAlpha — Polymarket Resolved Markets Scraper")
    print(f"  Fenster: {RES_START.date()}..{RES_END.date()} | min_vol=${MIN_VOLUME:.0f}")
    print(f"  Tags:    {', '.join(tags)}")
    if args.dry_run:
        print("  ** DRY RUN **")
    if args.skip_prices:
        print("  ** SKIP PRICES (nur Metadaten) **")
    print("=" * 60)

    t0 = time.time()
    if not args.dry_run:
        from shared.supabase_client import (
            upsert_polymarket_resolved_markets,
            upsert_polymarket_resolved_prices,
        )

    # Pro Tag: Discovery + Markets sofort in DB schreiben. Das haelt die
    # Supabase-Connection warm (sonst httpx-Keep-Alive-Socket nach 15+ min
    # stale -> ConnectError "Name or service not known").
    seen_cids: set[str] = set()
    all_unique: list[dict] = []
    for tag in tags:
        markets = scrape_tag(tag)
        # Dedup gegen vorherige Tags
        fresh = [m for m in markets if m["condition_id"] not in seen_cids]
        for m in fresh:
            seen_cids.add(m["condition_id"])
        all_unique.extend(fresh)
        if fresh and not args.dry_run:
            upsert_polymarket_resolved_markets([strip_token(m) for m in fresh])
            print(f"  -> {len(fresh)} frische Markets sofort in polymarket_resolved_markets geschrieben")

    print(f"\n-- Gefunden: {len(all_unique)} unique resolved markets ueber alle Tags")
    by_cat: dict[str, int] = {}
    for m in all_unique:
        by_cat[m["category"]] = by_cat.get(m["category"], 0) + 1
    for cat, n in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"    {cat:10s}: {n}")

    if not all_unique:
        print("\nNichts zu speichern.")
        return

    if args.dry_run:
        print("\n(dry-run) Nichts in DB geschrieben.")
        return

    if args.skip_prices:
        print("\n(skip-prices) Keine Preis-Historie gezogen.")
        return

    # Preis-Historie pro Markt ziehen + upserten (haeppchenweise)
    print(f"\n-- Preis-Historie ziehen (CLOB prices-history) fuer {len(all_unique)} Markets ...")
    total_rows = 0
    for i, m in enumerate(all_unique, 1):
        rows = fetch_history_for_market(m)
        if rows:
            upsert_polymarket_resolved_prices(rows)
            total_rows += len(rows)
        if i % 25 == 0 or i == len(all_unique):
            print(f"  [{i:4d}/{len(all_unique)}] bisher {total_rows} Zeilen in _resolved_prices")

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"  Fertig! {len(all_unique)} Markets, {total_rows} Preis-Snapshots in {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
