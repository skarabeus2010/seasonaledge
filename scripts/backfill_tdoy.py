#!/usr/bin/env python3
"""
SeasonAlpha — Backfill TDOM/TDOY
=================================
Berechnet TDOM (Trading Day of Month) und TDOY (Trading Day of Year)
fuer alle Zeilen in der prices-Tabelle und schreibt sie zurueck.

Nutzt den boersenspezifischen Feiertagskalender pro Ticker.

Aufruf:  py scripts/backfill_tdoy.py
"""
from __future__ import annotations

import sys, os, pathlib

# -- Projekt-Root finden --
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

try:  # Windows: UTF-8 erzwingen (✓-Prints crashen sonst unter cp1252 bei Datei-Umleitung)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from datetime import date, datetime, timedelta
from shared.supabase_client import get_client
from shared.exchange_holidays import is_trading_day
from shared.symbols import SYMBOLS, get_exchange_for_holidays

print("=" * 60)
print("SeasonAlpha — Backfill TDOM/TDOY")
print("=" * 60)
print(datetime.now())


def compute_tdoy_tdom(dates: list[date], exchange: str) -> list[dict]:
    """TDOM + TDOY je Datum — gezaehlt auf dem BOERSENKALENDER, nicht auf den Zeilen.

    Frueher lief der Zaehler ueber die uebergebene Datumsliste. Beginnt die
    gespeicherte Historie eines Tickers am 1. Juli, bekam dieser Tag `tdoy=1`,
    obwohl auf dem Kalender schon rund 125 Handelstage vorbei waren; eine
    Datenluecke schob analog alle folgenden Indizes nach vorn. TDOY/TDOM sind
    aber Eigenschaften des KALENDERS, nicht unserer Datenlage — genau so steht
    es auch in CLAUDE.md ("Ground-Truth = reiner Boersenkalender ab Jan 1").

    Deshalb wird je betroffenem Jahr einmal der komplette Handelstags-Kalender
    aufgebaut und jedes Datum darauf nachgeschlagen.
    """
    if not dates:
        return []

    # Kalender je Jahr genau einmal aufbauen (365/366 is_trading_day-Aufrufe).
    kalender: dict[int, dict[date, tuple[int, int]]] = {}
    for jahr in sorted({d.year for d in dates}):
        tage: dict[date, tuple[int, int]] = {}
        tdoy = 0
        tdom = 0
        letzter_monat = None
        tag = date(jahr, 1, 1)
        while tag.year == jahr:
            if tag.month != letzter_monat:
                letzter_monat = tag.month
                tdom = 0
            if is_trading_day(tag, exchange):
                tdoy += 1
                tdom += 1
            tage[tag] = (tdom, tdoy)
            tag += timedelta(days=1)
        kalender[jahr] = tage

    results = []
    for d in dates:
        tdom, tdoy = kalender[d.year].get(d, (0, 0))
        results.append({"date": d, "tdom": tdom, "tdoy": tdoy})
    return results



# Fehlgeschlagene Upsert-Batches — entscheidet am Ende ueber den Exit-Code.
_FAILED_BATCHES: list[str] = []


def backfill_ticker(client, ticker: str, exchange: str) -> int:
    """Backfill TDOM/TDOY fuer einen Ticker. Returns: Anzahl aktualisierter Zeilen."""

    # Alle Rows fuer diesen Ticker laden (date + close fuer Upsert)
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        result = (client.table("prices")
                  .select("date,close")
                  .eq("ticker", ticker)
                  .order("date")
                  .range(offset, offset + page_size - 1)
                  .execute())
        if not result.data:
            break
        all_rows.extend(result.data)
        if len(result.data) < page_size:
            break
        offset += page_size

    if not all_rows:
        return 0

    # Zeilen ohne Close filtern (NOT NULL constraint)
    all_rows = [r for r in all_rows if r.get("close") is not None]
    if not all_rows:
        return 0

    all_dates = [date.fromisoformat(r["date"]) for r in all_rows]

    # TDOM/TDOY berechnen
    td_values = compute_tdoy_tdom(all_dates, exchange)

    # In Batches zurueckschreiben (Upsert MIT close → NOT NULL constraint OK)
    batch_size = 500
    total_updated = 0

    for i in range(0, len(td_values), batch_size):
        batch = td_values[i:i + batch_size]
        records = []
        for j, v in enumerate(batch):
            row_idx = i + j
            records.append({
                "ticker": ticker,
                "date": v["date"].isoformat(),
                "close": all_rows[row_idx]["close"],  # Bestehenden Close mitgeben
                "tdom": v["tdom"],
                "tdoy": v["tdoy"],
            })
        try:
            client.table("prices").upsert(
                records,
                on_conflict="ticker,date"
            ).execute()
            total_updated += len(records)
        except Exception as e:
            print(f"    ⚠ Batch-Fehler bei {ticker}: {e}")
            # Nicht nur melden: mitzaehlen. Frueher lief das Skript nach einem
            # fehlgeschlagenen Batch weiter, endete mit Exit 0 und meldete
            # "Fertig" — Monitoring stand auf gruen, waehrend Zeilen veraltet
            # blieben. Ein Fehlschlag muss sich als Fehlschlag zeigen.
            _FAILED_BATCHES.append(f"{ticker}: {str(e)[:120]}")
        del records  # Speicher freigeben

    # Explizit aufraeumen
    del all_rows, all_dates, td_values
    return total_updated


def main():
    import gc
    args = sys.argv[1:]
    single_ticker = None
    for i, arg in enumerate(args):
        if arg == "--ticker" and i + 1 < len(args):
            single_ticker = args[i + 1]

    client = get_client()

    # Alle Ticker aus SYMBOLS (oder einzelner)
    if single_ticker:
        tickers = [single_ticker]
    else:
        tickers = sorted(SYMBOLS.keys())
    print(f"\nGefunden: {len(tickers)} Ticker\n")

    total_rows = 0
    total_fixed = 0

    for idx, ticker in enumerate(tickers, 1):
        exchange = get_exchange_for_holidays(ticker)
        updated = backfill_ticker(client, ticker, exchange)

        if updated > 0:
            total_fixed += 1
            total_rows += updated
            print(f"  [{idx:3d}/{len(tickers)}] {ticker:<12s} — ✓ {updated:6d} Zeilen ({exchange})")
        else:
            print(f"  [{idx:3d}/{len(tickers)}] — ⚠ Übersprungen (keine Daten)")

        # Speicher freigeben nach jedem Ticker (verhindert OOM bei Docker)
        gc.collect()

    print(f"\n{'=' * 60}")
    print(f"Fertig: {total_fixed} Ticker, {total_rows} Zeilen aktualisiert")
    if _FAILED_BATCHES:
        print("")
        print(f"[FAIL] {len(_FAILED_BATCHES)} Batch(es) nicht geschrieben — "
              f"TDOM/TDOY sind nur TEILWEISE aktualisiert:")
        for _f in _FAILED_BATCHES[:20]:
            print(f"  - {_f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
