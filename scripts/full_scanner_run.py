"""
scripts/full_scanner_run.py — Dedicated Full-Scanner Run
=========================================================
Berechnet den Saison-Score (shared/saison_score.py) fuer ALLE Ticker aus shared/symbols.py
und schreibt pro Ticker SOFORT nach Supabase (statt Batch am Ende).

Unterschied zu nightly_refresh.py:
- Scanner-ONLY (kein TDoM/TDoY/Monthly, kein Calendar, kein CPI)
- Pro-Ticker-Upsert (Resume-safe: bei Abbruch bleibt der Progress erhalten)
- Progress-Report alle N Ticker (default 10)
- Quick-Mode default OFF (volle Qualitaet fuer den wichtigen Weekly Run)
- --limit Option fuer manuellen Test-Run
- --resume Option fuer Weiterlaufen nach Abbruch (ueberspringt Ticker die
  heute bereits einen Eintrag in scanner_results haben)
- --quick / --full Modus
- Exit-Code spiegelt Success-Rate wider

Usage:
  py scripts/full_scanner_run.py                  # Full run, alle Ticker
  py scripts/full_scanner_run.py --limit 10       # Nur erste 10 (Test)
  py scripts/full_scanner_run.py --resume         # Ueberspringe schon gescannte
  py scripts/full_scanner_run.py --quick          # Quick-Mode (schneller)
  py scripts/full_scanner_run.py --only AAPL,MSFT # Nur spezifische Ticker

Erwartete Laufzeit (Full Mode, 270 Ticker):
  - Quick-Mode:  ~10-20 Min
  - Full-Mode:   ~45-90 Min (je nach Netzwerk, Supabase-Latency)
"""
from __future__ import annotations

import argparse
import gc
import os
import pathlib
import sys
import time
from datetime import date, datetime

# Projekt-Root in sys.path
_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)


def load_already_scanned_today() -> set:
    """Ticker, die HEUTE schon eine Saison-Score-Zeile haben (für --resume). Nur methode = saison_v1 — eine alte
    KI-Score-Zeile von heute darf einen Ticker nicht überspringen lassen. Ein Fehler beim Lesen ist ein Abbruch,
    kein leeres Ergebnis (sonst liefe --resume still über alles)."""
    from shared.supabase_client import get_client
    today = date.today().strftime("%Y-%m-%d")
    zeilen, offset = set(), 0
    while True:
        teil = (get_client().table("scanner_results").select("ticker").eq("scan_date", today)
                .eq("methode", "saison_v1").range(offset, offset + 999).execute().data) or []
        zeilen.update(r["ticker"] for r in teil)
        if len(teil) < 1000:
            return zeilen
        offset += 1000


def scan_ticker(ticker: str, today: str) -> dict:
    """Saison-Score aus den Supabase-Kursen rechnen und sofort schreiben (resume-safe). Wirft bei Lade-/Schreibfehler."""
    from shared import saison_score_betrieb as sb
    from shared.supabase_client import get_client
    e = sb.fuer_ticker(ticker, get_client())
    for ab in sb.schreibe(get_client(), [sb.scanner_zeile(e, ticker, today)], [sb.protokoll_zeile(e, ticker)]):
        print(f"  Protokoll weicht ab (erster Eintrag bleibt): {ab}", flush=True)
    return e


def run_full_scan(
    *,
    limit: int | None,
    resume: bool,
    quick: bool,
    only: list[str] | None,
    progress_every: int,
) -> int:
    """
    Fuehrt den Full-Scan aus.

    Returns:
        Exit-Code (0 = erfolgreich, 1 = >20% Errors, 2 = nichts berechnet)
    """
    from shared.symbols import SYMBOLS
    from shared.logger import app_logger

    t_start = time.time()
    mode_label = "QUICK" if quick else "FULL"
    print("=" * 64)
    print(f"  SeasonAlpha Full Scanner Run ({mode_label})")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 64)

    # 1. Ticker-Liste
    all_tickers = list(SYMBOLS.keys())
    if only:
        tickers = [t for t in all_tickers if t in set(only)]
        print(f"  Mode: --only filter -> {len(tickers)} Ticker")
    else:
        tickers = all_tickers
        print(f"  Mode: full run -> {len(tickers)} Ticker")

    # 2. Resume: bereits gescannte ueberspringen
    skipped_existing = 0
    if resume:
        already = load_already_scanned_today()
        if already:
            pre = len(tickers)
            tickers = [t for t in tickers if t not in already]
            skipped_existing = pre - len(tickers)
            print(f"  Resume: {skipped_existing} Ticker bereits heute gescannt, skip")

    # 3. Limit anwenden
    if limit is not None and limit < len(tickers):
        tickers = tickers[:limit]
        print(f"  Limit: {limit} Ticker")

    print(f"  Zu scannen: {len(tickers)}")
    print("-" * 64)

    if not tickers:
        print("  Keine Ticker zu scannen, Exit.")
        return 0

    # 4. Scanner-Loop
    success = 0
    skipped_nodata = 0
    errors = 0
    error_details: list[tuple[str, str]] = []

    today = date.today().strftime("%Y-%m-%d")

    for i, ticker in enumerate(tickers, 1):
        t_ticker = time.time()
        try:
            e = scan_ticker(ticker, today)
            elapsed = time.time() - t_ticker
            if e["status"] != "ok":
                skipped_nodata += 1     # als Zeile mit Grund gespeichert — kein Fehler
                print(f"  [{i:3d}/{len(tickers)}] {ticker:<14} nicht berechenbar ({e.get('grund_code')})  {elapsed:4.1f}s")
                continue
            success += 1
            print(
                f"  [{i:3d}/{len(tickers)}] {ticker:<14} Saison-Score {e['score']:4.1f}  "
                f"30T-Trefferquote {e['b1']['k']}/{e['b1']['n']}  Ø {e['b2']['mittel']:+6.2f}%  {elapsed:4.1f}s"
            )
        except KeyboardInterrupt:
            print("\n  [STOP] KeyboardInterrupt — partial results bleiben in DB")
            break
        except Exception as e:
            errors += 1
            error_details.append((ticker, str(e)[:100]))
            elapsed = time.time() - t_ticker
            print(f"  [{i:3d}/{len(tickers)}] {ticker:<14} ERROR             {elapsed:4.1f}s — {str(e)[:80]}")
            app_logger.error(f"full_scanner_run: {ticker}: {e}")
        finally:
            gc.collect()

        # Progress Summary alle N Ticker
        if progress_every > 0 and i % progress_every == 0:
            elapsed_total = time.time() - t_start
            eta = elapsed_total / i * (len(tickers) - i)
            print(
                f"  --- Progress: {i}/{len(tickers)}  "
                f"success={success} skip={skipped_nodata} err={errors}  "
                f"elapsed={elapsed_total/60:.1f}min eta={eta/60:.1f}min ---"
            )

    # 5. Summary
    total_elapsed = time.time() - t_start
    print("-" * 64)
    print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total Time: {total_elapsed/60:.1f} min")
    print(f"  Success:    {success:3d}")
    print(f"  Nicht berechenbar: {skipped_nodata:3d} (als Zeile mit Grund gespeichert)")
    print(f"  Errors:     {errors:3d}")
    if resume:
        print(f"  Resumed:    {skipped_existing:3d} (bereits heute gescannt, skipped)")
    print("=" * 64)

    if errors > 0:
        print("\nError Details (erste 10):")
        for t, msg in error_details[:10]:
            print(f"  {t}: {msg}")

    # 6. Exit-Code: jeder Lade- oder Schreibfehler macht den Lauf rot (vorher erst ab 20 %) — sonst stünde im
    #    Scanner still ein Teilstand. Ein nicht berechenbarer Ticker ist kein Fehler (Zeile mit Grund).
    if success == 0 and skipped_nodata == 0:
        return 2      # nichts verarbeitet; nur nicht berechenbare, aber geschriebene Zeilen sind kein Fehler
    if errors > 0:
        return 1
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Full Scanner Run (all tickers)")
    ap.add_argument("--limit", type=int, default=None, help="Nur erste N Ticker (Test)")
    ap.add_argument("--resume", action="store_true", help="Skip Ticker die heute schon gescannt sind")
    ap.add_argument("--quick", action="store_true", help="Quick-Mode (schneller, weniger akkurat)")
    ap.add_argument("--full", action="store_true", help="Full-Mode (default)")
    ap.add_argument("--only", type=str, default=None, help="Nur spezifische Ticker (komma-separiert)")
    ap.add_argument("--progress-every", type=int, default=10, help="Progress-Report alle N Ticker")
    args = ap.parse_args()

    quick = args.quick and not args.full
    only_list = [t.strip() for t in args.only.split(",")] if args.only else None

    exit_code = run_full_scan(
        limit=args.limit,
        resume=args.resume,
        quick=quick,
        only=only_list,
        progress_every=args.progress_every,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
