"""
scripts/full_scanner_run.py — Dedicated Full-Scanner Run
=========================================================
Berechnet den KI-Saisonalitaets-Score fuer ALLE Ticker aus shared/symbols.py
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
    """Liest alle Ticker die heute schon in scanner_results sind (fuer --resume)."""
    try:
        from shared.supabase_client import get_client
        today = date.today().strftime("%Y-%m-%d")
        client = get_client()
        result = (
            client.table("scanner_results")
            .select("ticker")
            .eq("scan_date", today)
            .execute()
        )
        return set(r["ticker"] for r in result.data)
    except Exception as e:
        print(f"[WARN] resume-check failed: {e}", file=sys.stderr)
        return set()


def _clean_num(v, fallback=None):
    """NaN/inf -> fallback (Postgres lehnt NaN-Token im JSON-Body ab, 22P02)."""
    import math
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return fallback
    return v


def upsert_single_scanner_result(result: dict) -> None:
    """Ein einzelnes Scanner-Result nach Supabase schreiben (resume-safe)."""
    from shared.supabase_client import upsert_scanner_results
    today = date.today().strftime("%Y-%m-%d")
    record = {
        "ticker": result["ticker"],
        "score": _clean_num(result["score"], 0.0),        # NOT NULL
        "signal": result["signal"],
        "win_rate": _clean_num(result.get("win_rate", 0)),
        "avg_return": _clean_num(result.get("avg_return", 0)),
        "deviation": _clean_num(result.get("deviation", 0)),
        "scan_date": today,
    }
    upsert_scanner_results([record])


def compute_scanner_for_ticker(ticker: str, *, years_back: int, quick_mode: bool) -> dict | None:
    """
    Berechnet KI-Score + Scanner-Result fuer einen Ticker.

    Returns:
        dict mit keys: ticker, score, signal, win_rate, avg_return, deviation
        oder None wenn nicht berechnet werden konnte.
    """
    from shared.yahoo_downloader import download_data, preprocess
    from shared.calculations import build_year_data, calculate_seasonal_average
    from shared.cache_manager import get_or_compute_ki_score

    current_year = date.today().year
    start_year = current_year - years_back

    # 1. Download
    raw_df = download_data(ticker, period="max")
    if raw_df is None or raw_df.empty:
        return None

    # 2. Preprocess
    df = preprocess(raw_df)
    if df is None or df.empty:
        return None

    # 3. Verfuegbare Jahre
    available_years = sorted([
        y for y in df["year"].unique()
        if start_year <= y <= current_year
    ])
    if len(available_years) < 3:
        return None

    # 4. Year-Data + Seasonal Average
    year_data = build_year_data(df, available_years)
    if len(year_data) < 3:
        return None

    avg, std = calculate_seasonal_average(year_data)

    # 5. KI-Score
    result = get_or_compute_ki_score(
        ticker, df, year_data, avg, std,
        quick_mode=quick_mode,
    )
    if not result:
        return None

    # 6. Scanner-Fields extrahieren
    wr_details = result["sub_scores"]["win_rate"]["details"]
    tracking_details = result["sub_scores"]["tracking"]["details"]

    return {
        "ticker": result["ticker"],
        "score": result["score"],
        "signal": result["signal"],
        "win_rate": wr_details.get("win_rate", 0),
        "avg_return": wr_details.get("avg_return", 0),
        "deviation": round(1 - tracking_details.get("correlation", 0), 3),
    }


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

    # OOM-Schutz: download_data ist @st.cache_data → cached jede Voll-Historie im
    # Memory. Bei 324 Tickern (tiefe Historien) sprengt das den Container (exit 137).
    from shared.yahoo_downloader import clear_cache

    for i, ticker in enumerate(tickers, 1):
        t_ticker = time.time()
        try:
            result = compute_scanner_for_ticker(
                ticker, years_back=20, quick_mode=quick,
            )
            if result is None:
                skipped_nodata += 1
                elapsed = time.time() - t_ticker
                print(f"  [{i:3d}/{len(tickers)}] {ticker:<14} SKIP (kein Score)  {elapsed:4.1f}s")
                continue

            # Pro-Ticker Upsert (resume-safe)
            upsert_single_scanner_result(result)
            success += 1

            elapsed = time.time() - t_ticker
            print(
                f"  [{i:3d}/{len(tickers)}] {ticker:<14} "
                f"{result['signal']:<8} score={result['score']:4.1f} "
                f"wr={result['win_rate']:5.1f}% avg={result['avg_return']:+6.2f}%  "
                f"{elapsed:4.1f}s"
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
            # Pro-Ticker Speicher freigeben (sonst OOM/exit 137 ab ~Ticker 69).
            try:
                clear_cache()
            except Exception:
                pass
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
    print(f"  No Data:    {skipped_nodata:3d} (Ticker ohne ausreichende Historie)")
    print(f"  Errors:     {errors:3d}")
    if resume:
        print(f"  Resumed:    {skipped_existing:3d} (bereits heute gescannt, skipped)")
    print("=" * 64)

    if errors > 0:
        print("\nError Details (erste 10):")
        for t, msg in error_details[:10]:
            print(f"  {t}: {msg}")

    # 6. Exit-Code
    if success == 0:
        return 2  # Nichts berechnet = harter Fehler
    if errors > len(tickers) * 0.2:
        return 1  # >20% Errors = weicher Warn-Fehler
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
