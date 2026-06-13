#!/usr/bin/env python3
"""
scripts/onboard_ticker.py — Neuen Ticker sicher & vollständig aufnehmen
======================================================================
Macht den KORREKTEN Onboarding-Weg zum Ein-Befehl-Prozess, damit keine
halb-angelegten Ticker (Orphans / vergessene Backfills) mehr entstehen:

  1. Prüft, dass der Ticker in shared/symbols.py steht (Registry = Quelle der Wahrheit).
  2. Validiert gegen Yahoo (liefert er überhaupt Daten?).
  3. Voll-Backfill der Historie via backfill_new_ticker.py (OHLC + log_return +
     TDOM/TDOY, upsert prices + tickers-Tabelle).
  4. Regeneriert landing/data/tickers.json (Autocomplete-Quelle).
  5. Verifiziert, dass der Ticker bis zum letzten Handelstag reicht.

ki_scores/scanner/monthly_stats/tdom_stats ziehen danach automatisch der nächste
Nightly-Refresh nach (der Ticker ist jetzt in get_all_tickers()).

Voraussetzung: Ticker(s) sind bereits in shared/symbols.py eingetragen
(Code-Edit — bewusst manuell, damit Name/Kategorie/Exchange stimmen).

Usage:
    py scripts/onboard_ticker.py SMH
    py scripts/onboard_ticker.py NKE TRV BAYN.DE
    py scripts/onboard_ticker.py --skip-validate SMH   # Yahoo-Check überspringen
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from shared.symbols import SYMBOLS


def _run(script: str, args: list[str]) -> bool:
    cmd = [sys.executable, os.path.join(_project_dir, "scripts", script)] + args
    print(f"  → {script} {' '.join(args)}")
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    r = subprocess.run(cmd, cwd=_project_dir, env=env)
    return r.returncode == 0


def _yahoo_has_data(ticker: str) -> bool:
    from shared.yahoo_downloader import download_data
    try:
        df = download_data(ticker, period="1mo")
        return df is not None and not df.empty
    except Exception as e:
        print(f"    ⚠ Yahoo-Fehler {ticker}: {str(e)[:80]}")
        return False


def main() -> int:
    args = [a for a in sys.argv[1:]]
    skip_validate = "--skip-validate" in args
    tickers = [a for a in args if not a.startswith("--")]

    if not tickers:
        print("Usage: py scripts/onboard_ticker.py <TICKER> [<TICKER> ...]")
        return 2

    print("=" * 64)
    print(f"  Onboarding: {', '.join(tickers)}")
    print("=" * 64)

    # 1+2: Registry-Check + Yahoo-Validierung
    valid = []
    for t in tickers:
        if t not in SYMBOLS:
            print(f"  ✗ {t}: NICHT in shared/symbols.py — erst dort eintragen "
                  f"(Name/Kategorie/Exchange), dann erneut ausführen.")
            continue
        if not skip_validate and not _yahoo_has_data(t):
            print(f"  ✗ {t}: Yahoo liefert keine Daten — Ticker-Symbol prüfen.")
            continue
        print(f"  ✓ {t}: in symbols.py" + ("" if skip_validate else " + Yahoo-Daten ok"))
        valid.append(t)

    if not valid:
        print("\nKeine validen Ticker — abgebrochen.")
        return 1

    # 3: Voll-Backfill
    print(f"\n[backfill] Max-Historie für {len(valid)} Ticker …")
    if not _run("backfill_new_ticker.py", valid):
        print("  ⚠ backfill_new_ticker meldete einen Fehler — Log prüfen.")

    # 4: tickers.json regenerieren
    print("\n[tickers.json] regeneriere Autocomplete-Quelle …")
    _run("generate_tickers_json.py", [])

    # 5: Verifikation
    print("\n[verify] jüngstes Datum je Ticker:")
    try:
        from shared.supabase_client import get_client
        c = get_client()
        for t in valid:
            d = (c.table("prices").select("date").eq("ticker", t)
                 .order("date", desc=True).limit(1).execute().data)
            n = (c.table("prices").select("id", count="exact")
                 .eq("ticker", t).limit(1).execute().count)
            print(f"  {t:10s} {d[0]['date'] if d else 'KEINE':12s}  ({n} Zeilen)")
    except Exception as e:
        print(f"  ⚠ Verifikation fehlgeschlagen: {str(e)[:80]}")

    print("\n" + "=" * 64)
    print(f"  Fertig: {len(valid)}/{len(tickers)} onboarded. "
          f"ki_scores/scanner/stats füllt der nächste Nightly nach.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
