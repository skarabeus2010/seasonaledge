"""
scripts/nightly_refresh.py — Nightly DB Refresh
=================================================
Berechnet Market Calendar + KI Scores + Scanner Results + TDoM Stats
und speichert alles in Supabase.

Aufruf: py -m scripts.nightly_refresh
Oder:   py scripts/nightly_refresh.py
"""

import sys
import os
import pathlib
import time
from datetime import date

# Projekt-Root in sys.path
_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.logger import app_logger


def refresh_calendar():
    """Phase A: Market Calendar sync."""
    from shared.market_calendar import sync_calendar

    current_year = date.today().year
    count = sync_calendar(current_year, current_year + 2)
    app_logger.info(f"nightly_refresh: Calendar synced — {count} events")
    return count


def refresh_ticker_data(tickers: list[str], years_back: int = 20, quick_mode: bool = True):
    """Phase B: Ticker-Daten berechnen und cachen."""
    from shared.yahoo_downloader import download_data, preprocess
    from shared.calculations import build_year_data, calculate_seasonal_average
    from shared.cache_manager import (
        get_or_compute_monthly_stats,
        get_or_compute_ki_score,
        get_or_compute_tdom_stats,
        store_scanner_results,
    )

    current_year = date.today().year
    start_year = current_year - years_back
    scanner_results = []

    for i, ticker in enumerate(tickers):
        try:
            t0 = time.time()

            # Download + Preprocess
            raw_df = download_data(ticker, period="max")
            if raw_df is None or raw_df.empty:
                app_logger.debug(f"nightly_refresh: {ticker} — keine Daten")
                continue

            df = preprocess(raw_df)
            if df is None or df.empty:
                continue

            # Monthly Stats
            get_or_compute_monthly_stats(ticker, df, years_back)

            # KI Score
            available_years = sorted([
                y for y in df["year"].unique()
                if start_year <= y <= current_year
            ])
            if len(available_years) >= 3:
                year_data = build_year_data(df, available_years)
                if len(year_data) >= 3:
                    avg, std = calculate_seasonal_average(year_data)
                    result = get_or_compute_ki_score(
                        ticker, df, year_data, avg, std,
                        quick_mode=quick_mode,
                    )
                    if result:
                        from shared.symbols import SYMBOLS, get_display_name
                        sym_info = SYMBOLS.get(ticker, {})
                        result["name"] = sym_info.get("name", get_display_name(ticker))
                        result["kategorie"] = sym_info.get("kategorie", "Sonstige")

                        wr_details = result["sub_scores"]["win_rate"]["details"]
                        result["win_rate"] = wr_details.get("win_rate", 0)
                        result["avg_return"] = wr_details.get("avg_return", 0)

                        tracking_details = result["sub_scores"]["tracking"]["details"]
                        result["deviation"] = round(
                            1 - tracking_details.get("correlation", 0), 3
                        )
                        scanner_results.append(result)

            # TDoM Stats (alle 3 Strategien, forward)
            for strategy in ["open_to_close", "open_to_next_open", "close_to_next_close"]:
                get_or_compute_tdom_stats(ticker, df, strategy=strategy, direction="forward")

            elapsed = time.time() - t0
            app_logger.info(
                f"nightly_refresh: [{i+1}/{len(tickers)}] {ticker} — {elapsed:.1f}s"
            )

        except Exception as e:
            app_logger.error(f"nightly_refresh: {ticker} — Fehler: {e}")
            continue

    # Scanner Results speichern
    if scanner_results:
        scanner_results.sort(key=lambda x: x["score"], reverse=True)
        store_scanner_results(scanner_results)
        app_logger.info(f"nightly_refresh: Scanner — {len(scanner_results)} Ticker gespeichert")

    return len(scanner_results)


def main():
    """Hauptfunktion: Calendar + Ticker Refresh."""
    from shared.symbols import SYMBOLS

    app_logger.info("nightly_refresh: Start")
    t_start = time.time()

    # Phase A: Calendar
    try:
        n_events = refresh_calendar()
        print(f"Calendar: {n_events} events synced")
    except Exception as e:
        app_logger.error(f"nightly_refresh: Calendar-Sync fehlgeschlagen: {e}")
        print(f"Calendar sync failed: {e}")

    # Phase A2: CPI Update
    try:
        from shared.cpi_data import update_cpi_in_db
        update_cpi_in_db()
        print("CPI: updated")
    except Exception as e:
        app_logger.error(f"nightly_refresh: CPI-Update fehlgeschlagen: {e}")
        print(f"CPI update failed: {e}")

    # Phase B: Ticker Data
    tickers = list(SYMBOLS.keys())
    print(f"Ticker refresh: {len(tickers)} Ticker")

    n_results = refresh_ticker_data(tickers, years_back=20, quick_mode=True)

    elapsed = time.time() - t_start
    app_logger.info(f"nightly_refresh: Fertig — {n_results} Scanner-Ergebnisse in {elapsed:.0f}s")
    print(f"Done: {n_results} scanner results in {elapsed:.0f}s")


if __name__ == "__main__":
    main()
