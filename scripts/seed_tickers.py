#!/usr/bin/env python
"""
scripts/seed_tickers.py — SYMBOLS dict nach Supabase tickers-Tabelle upserten.

Einmalig ausfuehren:  py -m scripts.seed_tickers
Oder in nightly_refresh.py integrieren.
"""
import sys
import os
import pathlib
from datetime import datetime, timezone

# Projektpfad sicherstellen
_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.symbols import SYMBOLS
from shared.supabase_client import upsert_tickers


def build_records() -> list[dict]:
    """Konvertiert SYMBOLS dict in Supabase-kompatible Records."""
    now = datetime.now(timezone.utc).isoformat()
    records = []
    for ticker, info in SYMBOLS.items():
        records.append({
            "ticker": ticker,
            "name": info["name"],
            "kategorie": info["kategorie"],
            "waehrung": info.get("währung", "USD"),
            "exchange": info.get("exchange", ""),
            "beschreibung": info.get("beschreibung", ""),
            "aktiv": True,
            "updated_at": now,
        })
    return records


def main():
    records = build_records()
    print(f"Upserte {len(records)} Ticker nach Supabase ...")
    upsert_tickers(records)
    print("Fertig.")


if __name__ == "__main__":
    main()
