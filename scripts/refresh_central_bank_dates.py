"""
scripts/refresh_central_bank_dates.py — Zentralbank-Termine in Supabase laden
==============================================================================
Laedt alle Notenbank-Sitzungstermine aus den shared-Modulen in Supabase.
Kann als einmaliger Load oder als periodischer Refresh verwendet werden.

Aufruf:
    docker exec seasonalpha-app python3 scripts/refresh_central_bank_dates.py

Empfehlung: Alle 2 Monate ausfuehren (Termine aendern sich selten).
"""

import sys
import os
import pathlib

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.fed_dates import get_fomc_dates
from shared.central_banks import (
    get_ecb_dates, get_boe_dates, get_boj_dates,
)
from shared.supabase_client import get_client


def load_dates():
    """Laedt alle Zentralbank-Termine in Supabase (upsert)."""
    sb = get_client()

    sources = {
        "fomc": (get_fomc_dates, "FOMC"),
        "ecb": (get_ecb_dates, "ECB"),
        "boe": (get_boe_dates, "BOE"),
        "boj": (get_boj_dates, "BOJ"),
    }

    total = 0
    for bank, (func, label) in sources.items():
        dates = func()
        rows = []
        for d in dates:
            rows.append({
                "bank": bank,
                "date": d.strftime("%Y-%m-%d"),
                "label": label,
            })

        # Upsert in 500er-Chunks
        for i in range(0, len(rows), 500):
            chunk = rows[i:i + 500]
            sb.table("central_bank_dates").upsert(
                chunk, on_conflict="bank,date"
            ).execute()

        print(f"  {bank.upper()}: {len(rows)} Termine geladen")
        total += len(rows)

    print(f"\nGesamt: {total} Termine in Supabase geschrieben.")
    return total


if __name__ == "__main__":
    print("Lade Zentralbank-Termine in Supabase...")
    load_dates()
    print("Fertig!")
