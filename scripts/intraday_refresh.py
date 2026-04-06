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
                 "Anleihen", "Emerging Markets", "Volatility"}
ASIA_CATEGORIES = {"Asien-Index"}
FX_CATEGORIES = {"FX"}
CRYPTO_CATEGORIES = {"Krypto"}

TICKERS_EU = [t for t, v in SYMBOLS.items() if v["kategorie"] in EU_CATEGORIES]
TICKERS_US = [t for t, v in SYMBOLS.items() if v["kategorie"] in US_CATEGORIES]
TICKERS_ASIA = [t for t, v in SYMBOLS.items() if v["kategorie"] in ASIA_CATEGORIES]
TICKERS_FX = [t for t, v in SYMBOLS.items() if v["kategorie"] in FX_CATEGORIES]
TICKERS_CRYPTO = [t for t, v in SYMBOLS.items() if v["kategorie"] in CRYPTO_CATEGORIES]

# ── Handelszeiten als Zeitfenster (UTC) ──────────────────────────────────────
# Statt fester Slots: Wenn die Boerse OFFEN ist, wird geladen.
# Jeder Cron-Run der ins Fenster faellt, aktualisiert die Gruppe.
# MESZ = UTC + 2 (Sommerzeit), MEZ = UTC + 1 (Winterzeit)

def _hm(h, m=0):
    """Stunde:Minute → Minuten seit Mitternacht."""
    return h * 60 + m

# Zeitfenster: (start_utc, end_utc) — waehrend dieser Zeit wird geladen
GROUPS = {
    "eu":     {"tickers": TICKERS_EU,     "open": _hm(7, 0),  "close": _hm(16, 0),  "weekdays_only": True},
    "us":     {"tickers": TICKERS_US,     "open": _hm(13, 30), "close": _hm(21, 0),  "weekdays_only": True},
    "asia":   {"tickers": TICKERS_ASIA,   "open": _hm(0, 0),  "close": _hm(8, 0),   "weekdays_only": True},
    "fx":     {"tickers": TICKERS_FX,     "open": _hm(6, 0),  "close": _hm(20, 0),  "weekdays_only": True},
    "crypto": {"tickers": TICKERS_CRYPTO, "open": _hm(0, 0),  "close": _hm(23, 59), "weekdays_only": False},
}

# ── Logik ────────────────────────────────────────────────────────────────────


def get_active_groups(now_utc=None, force_group=None):
    """Ermittelt welche Gruppen jetzt aktualisiert werden sollen.

    Einfache Logik: Liegt die aktuelle UTC-Zeit im Handelsfenster
    der Gruppe? Wenn ja → laden. Kein Slot-Matching, keine Toleranz.
    """
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
        if cfg["open"] <= now_minutes <= cfg["close"]:
            active[name] = cfg

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

                # TDOM/TDOY berechnen: Letzten bekannten Wert aus DB lesen + weiterzaehlen
                try:
                    from shared.exchange_holidays import is_trading_day as _is_td
                    from shared.symbols import get_exchange_for_holidays
                    from shared.supabase_client import get_client as _get_client
                    _exchange = get_exchange_for_holidays(ticker)

                    # Letzten TDOY/TDOM aus Supabase holen (vor dem aeltesten Tag im Download)
                    _sorted_df = df.sort_index()
                    _first_date = _sorted_df.index[0]
                    _first_str = _first_date.strftime("%Y-%m-%d") if hasattr(_first_date, 'strftime') else str(_first_date)
                    _db_client = _get_client()
                    _prev = (_db_client.table("prices")
                             .select("date,tdom,tdoy")
                             .eq("ticker", ticker)
                             .lt("date", _first_str)
                             .order("date", desc=True)
                             .limit(1)
                             .execute())

                    _tdoy = 0
                    _tdom = 0
                    _prev_month = None
                    if _prev.data and _prev.data[0].get("tdoy") is not None:
                        _tdoy = int(_prev.data[0]["tdoy"])
                        _tdom = int(_prev.data[0]["tdom"])
                        _prev_month = int(_prev.data[0]["date"].split("-")[1])

                    for _d_idx in _sorted_df.index:
                        _d = _d_idx.date() if hasattr(_d_idx, 'date') else _d_idx
                        # Jahreswechsel: TDOY reset
                        if _prev_month is not None and _d.month == 1 and _prev_month == 12:
                            _tdoy = 0
                            _tdom = 0
                        # Monatswechsel: TDOM reset
                        if _prev_month is not None and _d.month != _prev_month:
                            _tdom = 0
                        _prev_month = _d.month

                        if _is_td(_d, _exchange):
                            _tdoy += 1
                            _tdom += 1
                        df.loc[_d_idx, "tdoy"] = _tdoy
                        df.loc[_d_idx, "tdom"] = _tdom
                except Exception:
                    pass  # Fallback: kein TDOM/TDOY

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
                        if "tdoy" in row and pd.notna(row["tdoy"]):
                            rec["tdoy"] = int(row["tdoy"])
                        if "tdom" in row and pd.notna(row["tdom"]):
                            rec["tdom"] = int(row["tdom"])
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
