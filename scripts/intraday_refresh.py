#!/usr/bin/env python3
"""
SeasonAlpha — Intraday Price Refresh

Lightweight-Script fuer unterta¨gige Kurs-Updates.
Laedt nur Preise herunter (keine KI-Scores, TDOM, Monthly Stats).
Wird alle 30 Min via GitHub Actions getriggert und entscheidet
anhand der aktuellen UTC-Zeit, welche Ticker-Gruppen aktualisiert werden.

Nutzung:
    python scripts/intraday_refresh.py              # Normaler Lauf
    python scripts/intraday_refresh.py --dry-run    # Nur anzeigen, nichts laden
    python scripts/intraday_refresh.py --group eu   # Nur eine Gruppe
"""

import sys
import os
import pathlib
import time
from datetime import datetime, timezone

# ── Projekt-Setup ────────────────────────────────────────────────────────────

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import numpy as np
from shared.yahoo_downloader import download_data
from shared.symbols import SYMBOLS

# ── Ticker-Gruppen ───────────────────────────────────────────────────────────

EU_CATEGORIES = {"EU-Index", "EU-Aktie"}
US_CATEGORIES = {"US-Index", "US-ETF", "US-Aktie", "Rohstoff", "Futures",
                 "Anleihen", "Emerging Markets"}
ASIA_CATEGORIES = {"Asien-Index"}
FX_CATEGORIES = {"FX"}
CRYPTO_CATEGORIES = {"Krypto"}

TICKERS_EU = [t for t, v in SYMBOLS.items() if v["kategorie"] in EU_CATEGORIES]
TICKERS_US = [t for t, v in SYMBOLS.items() if v["kategorie"] in US_CATEGORIES]
TICKERS_ASIA = [t for t, v in SYMBOLS.items() if v["kategorie"] in ASIA_CATEGORIES]
TICKERS_FX = [t for t, v in SYMBOLS.items() if v["kategorie"] in FX_CATEGORIES]
TICKERS_CRYPTO = [t for t, v in SYMBOLS.items() if v["kategorie"] in CRYPTO_CATEGORIES]

# ── Update-Zeiten (UTC-Minuten seit Mitternacht) ────────────────────────────
# MESZ = UTC + 2 (Sommerzeit), MEZ = UTC + 1 (Winterzeit)
# Alle Zeiten hier in UTC (MESZ - 2h)

def _hm(h, m=0):
    """Stunde:Minute → Minuten seit Mitternacht."""
    return h * 60 + m

# EU:  9:15-17:35 MESZ → 7:15-15:35 UTC
EU_TIMES = [_hm(7, 15), _hm(7, 35), _hm(9), _hm(11), _hm(13), _hm(15), _hm(15, 35)]

# US: 15:35-22:05 MESZ → 13:35-20:05 UTC
US_TIMES = [_hm(13, 35), _hm(14, 15), _hm(15), _hm(16), _hm(17), _hm(18),
            _hm(19, 30), _hm(20, 5)]

# Asien: 3:00-8:00 MESZ → 1:00-6:00 UTC
ASIA_TIMES = [_hm(1), _hm(3), _hm(6)]

# FX: 8:00-22:00 MESZ → 6:00-20:00 UTC
FX_TIMES = [_hm(6), _hm(10), _hm(13, 30), _hm(16), _hm(20)]

# Crypto: stuendlich
CRYPTO_TIMES = [_hm(h) for h in range(24)]

GROUPS = {
    "eu":     {"tickers": TICKERS_EU,     "times": EU_TIMES,     "weekdays_only": True},
    "us":     {"tickers": TICKERS_US,     "times": US_TIMES,     "weekdays_only": True},
    "asia":   {"tickers": TICKERS_ASIA,   "times": ASIA_TIMES,   "weekdays_only": True},
    "fx":     {"tickers": TICKERS_FX,     "times": FX_TIMES,     "weekdays_only": True},
    "crypto": {"tickers": TICKERS_CRYPTO, "times": CRYPTO_TIMES, "weekdays_only": False},
}

# ── Logik ────────────────────────────────────────────────────────────────────

TOLERANCE_MINUTES = 16  # ±16 Min Toleranz (Cron laeuft alle 30 Min)


def get_active_groups(now_utc=None, force_group=None):
    """Ermittelt welche Gruppen jetzt aktualisiert werden sollen."""
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    if force_group:
        if force_group in GROUPS:
            return {force_group: GROUPS[force_group]}
        print(f"  [FEHLER] Unbekannte Gruppe: {force_group}")
        print(f"  Verfuegbar: {', '.join(GROUPS.keys())}")
        return {}

    now_minutes = now_utc.hour * 60 + now_utc.minute
    is_weekday = now_utc.weekday() < 5  # Mo=0, Fr=4

    active = {}
    for name, cfg in GROUPS.items():
        if cfg["weekdays_only"] and not is_weekday:
            continue
        for t in cfg["times"]:
            diff = abs(now_minutes - t)
            # Mitternachts-Wrap (z.B. 23:50 vs 0:05)
            diff = min(diff, 1440 - diff)
            if diff <= TOLERANCE_MINUTES:
                active[name] = cfg
                break

    return active


def refresh_tickers(tickers, group_name, dry_run=False):
    """Laedt Kursdaten fuer eine Liste von Tickern und schreibt sie in Supabase."""
    import pandas as pd
    success = 0
    errors = []

    for i, ticker in enumerate(tickers, 1):
        if dry_run:
            print(f"    [{i:2d}/{len(tickers)}] {ticker} (dry-run)")
            success += 1
            continue

        try:
            t0 = time.time()
            df = download_data(ticker, period="5d")
            if df is not None and not df.empty:
                # log_return berechnen (ln(close_t / close_{t-1}))
                df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))

                # Preise in Supabase schreiben
                try:
                    from shared.supabase_client import upsert_prices
                    records = []
                    for idx, row in df.iterrows():
                        rec = {
                            "ticker": ticker,
                            "date": idx.strftime("%Y-%m-%d") if hasattr(idx, 'strftime') else str(idx),
                            "close": round(float(row["Close"]), 4),
                            "source": "yahoo",
                        }
                        for col in ["Open", "High", "Low"]:
                            if col in row and pd.notna(row[col]):
                                rec[col.lower()] = round(float(row[col]), 4)
                        if "Volume" in row and pd.notna(row["Volume"]):
                            rec["volume"] = int(row["Volume"])
                        if "log_return" in row and pd.notna(row["log_return"]):
                            rec["log_return"] = round(float(row["log_return"]), 8)
                        records.append(rec)
                    if records:
                        upsert_prices(records)
                except Exception as db_err:
                    print(f"    [{i:2d}/{len(tickers)}] {ticker} — DB-Fehler: {db_err}")

            elapsed = time.time() - t0
            print(f"    [{i:2d}/{len(tickers)}] {ticker} — {elapsed:.1f}s ({len(df) if df is not None else 0} rows)")
            success += 1
        except Exception as e:
            errors.append(ticker)
            print(f"    [{i:2d}/{len(tickers)}] {ticker} — FEHLER: {e}")

    return success, errors


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    force_group = None

    for i, arg in enumerate(args):
        if arg == "--group" and i + 1 < len(args):
            force_group = args[i + 1]

    now_utc = datetime.now(timezone.utc)
    now_mesz = now_utc.hour + 2  # Vereinfacht (MESZ = UTC+2)

    print("=" * 60)
    print(f"  SeasonAlpha — Intraday Price Refresh")
    print(f"  {now_utc.strftime('%Y-%m-%d %H:%M UTC')} (ca. {now_mesz}:xx MESZ)")
    if dry_run:
        print("  ** DRY RUN — keine Downloads **")
    print("=" * 60)

    active = get_active_groups(now_utc, force_group)

    if not active:
        print("\n  Keine Gruppe aktiv zu dieser Zeit.")
        print(f"  Wochentag: {'ja' if now_utc.weekday() < 5 else 'nein (Wochenende)'}")
        print(f"  UTC-Minute: {now_utc.hour * 60 + now_utc.minute}")
        return

    total_success = 0
    total_errors = []
    t_start = time.time()

    for name, cfg in active.items():
        tickers = cfg["tickers"]
        print(f"\n  [{name.upper()}] {len(tickers)} Ticker")
        s, e = refresh_tickers(tickers, name, dry_run)
        total_success += s
        total_errors.extend(e)

    elapsed = time.time() - t_start
    print(f"\n{'=' * 60}")
    print(f"  Fertig! {total_success} Ticker in {elapsed:.1f}s")
    if total_errors:
        print(f"  Fehler bei: {', '.join(total_errors)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
