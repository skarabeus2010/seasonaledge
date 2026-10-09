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

import pandas as pd
from shared.logger import app_logger

# Umgebung der Kind-Skripte (Phasen F-I), festgehalten VOR der ersten Phase.
# Grund (2026-09-29): ein Zugriff auf `st.secrets` (shared/cpi_data.py, Phase A2)
# kopierte die Eintraege einer veralteten .streamlit/secrets.toml in os.environ,
# darunter eine alte SUPABASE_URL. Der Hauptprozess arbeitete mit seinem schon
# gebauten Client weiter, jedes Kind erbte die alte Adresse und scheiterte an DNS —
# Weekly Newsletter und Polymarket-Snapshot liefen deshalb nie (20/20 Sonntage).
_KIND_UMGEBUNG = dict(os.environ)

# Phasen, deren Kind-Skript gescheitert ist. Nicht leer -> Exit 1, damit der
# Ausfall im systemd-Journal/`systemctl --failed` sichtbar wird statt als
# gruener Lauf durchzugehen.
_FEHLGESCHLAGEN: list[str] = []


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
        get_or_compute_tdom_stats,
        get_or_compute_tdoy_stats,
    )
    from shared import saison_score_betrieb as _saison
    from shared.supabase_client import get_client as _get_client

    current_year = date.today().year
    start_year = current_year - years_back
    scanner_results = []
    saison_fehler: list[str] = []
    ticker_fehler: list[str] = []     # alles im Tickerpfad, was den Lauf rot machen muss (Codex D3/D4 R1 Befund 4)
    today_str = date.today().strftime("%Y-%m-%d")

    for i, ticker in enumerate(tickers):
        try:
            t0 = time.time()

            # Download + Preprocess
            raw_df = download_data(ticker, period="max")
            if raw_df is None or raw_df.empty:
                ticker_fehler.append(f"{ticker}: keine Kursdaten geladen")
                app_logger.error(f"nightly_refresh: {ticker} — keine Daten")
                continue

            df = preprocess(raw_df)
            if df is None or df.empty:
                ticker_fehler.append(f"{ticker}: Vorverarbeitung leer")
                continue

            # Preise in Supabase schreiben (letzte 7 Tage — historische Daten bleiben unverändert)
            # 7 statt 5 Tage: Feiertags-Konstellationen (z.B. 1. Mai + Wochenende) abfangen
            try:
                from shared.supabase_client import upsert_prices
                _cutoff = (date.today() - __import__('datetime').timedelta(days=7)).strftime("%Y-%m-%d")
                _recent = df[df.index >= _cutoff] if hasattr(df.index, 'year') else df
                _price_records = []
                for _idx, _row in _recent.iterrows():
                    _rec = {
                        "ticker": ticker,
                        "date": _idx.strftime("%Y-%m-%d") if hasattr(_idx, 'strftime') else str(_idx),
                        "close": round(float(_row["Close"]), 4),
                        "source": "yahoo",
                    }
                    for _col in ["Open", "High", "Low"]:
                        if _col in _row and pd.notna(_row[_col]):
                            _rec[_col.lower()] = round(float(_row[_col]), 4)
                    if "Volume" in _row and pd.notna(_row["Volume"]):
                        _rec["volume"] = int(_row["Volume"])
                    if "log_return" in _row and pd.notna(_row["log_return"]):
                        _rec["log_return"] = round(float(_row["log_return"]), 8)
                    # TDOM/TDOY aus preprocess() (nutzt DB-Werte oder Fallback)
                    if "tdoy" in _row and pd.notna(_row["tdoy"]):
                        _rec["tdoy"] = int(_row["tdoy"])
                    if "tdom" in _row and pd.notna(_row["tdom"]):
                        _rec["tdom"] = int(_row["tdom"])
                    _price_records.append(_rec)
                if _price_records:
                    upsert_prices(_price_records)
            except Exception as _pe:
                # Ohne frische Kurse würde der Saison-Score aus alten Supabase-Kursen einen heutigen Eintrag schreiben
                # → Ticker als Fehler zählen und überspringen (Codex D3/D4 R1 Befund 4)
                ticker_fehler.append(f"{ticker}: Kurs-Upsert {str(_pe)[:100]}")
                app_logger.error(f"nightly_refresh: {ticker} price upsert failed: {_pe}")
                continue

            # Monthly Stats
            get_or_compute_monthly_stats(ticker, df, years_back)

            # Saison-Score (shared/saison_score.py, Nachfolger des KI-Score): aus den Supabase-Kursen — dieselbe Quelle
            # wie die Seiten, nachdem oben die letzten 7 Tage geschrieben wurden. Lade-/Schreibfehler werden gezählt
            # und machen den Nightly rot; ein nicht berechenbarer Ticker ist KEIN Fehler, sondern eine Zeile mit Grund.
            try:
                _e = _saison.fuer_ticker(ticker, _get_client())
                for _ab in _saison.schreibe(_get_client(), [_saison.scanner_zeile(_e, ticker, today_str)],
                                            [_saison.protokoll_zeile(_e, ticker)]):
                    app_logger.warning(f"nightly_refresh: Saison-Protokoll weicht ab (erster Eintrag bleibt): {_ab}")
                if _e["status"] == "ok":
                    scanner_results.append(ticker)
            except Exception as _se:  # noqa: BLE001
                saison_fehler.append(f"{ticker}: {str(_se)[:120]}")
                app_logger.error(f"nightly_refresh: Saison-Score {ticker}: {_se}")

            # TDoM Stats (alle 4 Strategien, forward) — Daily-Newsletter Multi-Window-Score
            for strategy in ["open_to_close", "open_to_next_open", "open_to_next_close", "close_to_next_close"]:
                get_or_compute_tdom_stats(ticker, df, strategy=strategy, direction="forward")

            # TDoY Stats (alle 4 Strategien, forward)
            for strategy in ["open_to_close", "open_to_next_open", "open_to_next_close", "close_to_next_close"]:
                get_or_compute_tdoy_stats(ticker, df, strategy=strategy, direction="forward")

            elapsed = time.time() - t0
            app_logger.info(
                f"nightly_refresh: [{i+1}/{len(tickers)}] {ticker} — {elapsed:.1f}s"
            )

        except Exception as e:
            ticker_fehler.append(f"{ticker}: {str(e)[:120]}")
            app_logger.error(f"nightly_refresh: {ticker} — Fehler: {e}")
            continue

    app_logger.info(f"nightly_refresh: Saison-Score — {len(scanner_results)} berechnet, {len(saison_fehler)} Fehler")
    if saison_fehler:
        _FEHLGESCHLAGEN.append(f"Saison-Score ({len(saison_fehler)} Lade-/Schreibfehler, z. B. {saison_fehler[0]})")
    if ticker_fehler:
        _FEHLGESCHLAGEN.append(f"Ticker-Refresh ({len(ticker_fehler)} Fehler, z. B. {ticker_fehler[0]})")
    return len(scanner_results)


def heartbeat():
    """Phase Z: Supabase Heartbeat — verhindert Free-Tier Pausing."""
    from shared.supabase_client import get_client
    from datetime import datetime, timezone

    client = get_client()

    # 1) Einfacher DB-Ping via RPC oder direkten SELECT
    try:
        client.table("market_events").select("id").limit(1).execute()
    except Exception:
        pass  # Tabelle existiert evtl. nicht — egal, der Request zählt

    # 2) Heartbeat-Eintrag in app_logs schreiben (echte Write-Aktivität)
    try:
        _now_utc = datetime.now(timezone.utc).isoformat()
        client.table("app_logs").insert({
            "level": "info",
            "message": f"nightly_heartbeat: alive — {_now_utc}",
            "created_at": _now_utc,
        }).execute()
        app_logger.info("nightly_refresh: Supabase heartbeat OK")
        print("Heartbeat: Supabase pinged")
    except Exception as e:
        # Fallback: Mindestens der SELECT oben war ein API-Call
        app_logger.info(f"nightly_refresh: Heartbeat write failed ({e}), SELECT sent")
        print(f"Heartbeat: SELECT sent (write failed: {e})")


def main():
    """Hauptfunktion: Calendar + Ticker Refresh + Heartbeat."""
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

    # Phase C: Health-Check — fehlende Handelstage der letzten 7 Tage finden + nachladen
    missing_total = 0
    auto_fixed = 0
    missing_details = {}
    health_errors = []
    try:
        from shared.supabase_client import get_client, upsert_prices
        from shared.exchange_holidays import is_trading_day
        from shared.symbols import get_exchange_for_holidays
        from shared.yahoo_downloader import download_data as yahoo_download

        client = get_client()
        check_start = date.today() - __import__('datetime').timedelta(days=7)
        # check_end = gestern, nicht heute — "heute" hat vor Börsenschluss
        # noch keine Daten und würde fälschlich als "missing" gezählt
        check_end = date.today() - __import__('datetime').timedelta(days=1)

        for ticker in tickers:
            try:
                exchange = get_exchange_for_holidays(ticker)

                # DB-Dates der letzten 7 Tage
                result = (client.table("prices")
                          .select("date")
                          .eq("ticker", ticker)
                          .gte("date", check_start.strftime("%Y-%m-%d"))
                          .lte("date", check_end.strftime("%Y-%m-%d"))
                          .execute())
                db_dates = set(r["date"] for r in result.data)

                # Erwartete Handelstage
                d = check_start
                missing_days = []
                while d <= check_end:
                    if is_trading_day(d, exchange) and d.strftime("%Y-%m-%d") not in db_dates:
                        missing_days.append(d)
                    d += __import__('datetime').timedelta(days=1)

                if missing_days:
                    # Auto-Fix: Yahoo nachladen + Kalender-Edgecase-Erkennung
                    # Wenn Yahoo für ALLE fehlenden Tage keine Daten hat → Börse war zu
                    # (Feiertag der nicht in shared/exchange_holidays steht). Nur dann
                    # zählt der Ticker nicht als echte Lücke in missing_details/tickers_success.
                    _yahoo_confirmed_any = False
                    _yahoo_fixed_ticker = 0
                    try:
                        fresh = yahoo_download(ticker, period="1mo")
                        if fresh is not None and not fresh.empty:
                            fresh.index = fresh.index.normalize()
                            records = []
                            for md in missing_days:
                                ts = pd.Timestamp(md)
                                if ts in fresh.index and pd.notna(fresh.loc[ts, "Close"]):
                                    _yahoo_confirmed_any = True
                                    rec = {
                                        "ticker": ticker,
                                        "date": md.strftime("%Y-%m-%d"),
                                        "close": round(float(fresh.loc[ts, "Close"]), 4),
                                        "source": "yahoo",
                                    }
                                    for col in ["Open", "High", "Low"]:
                                        if col in fresh.columns and pd.notna(fresh.loc[ts, col]):
                                            rec[col.lower()] = round(float(fresh.loc[ts, col]), 4)
                                    records.append(rec)
                            if records:
                                upsert_prices(records)
                                auto_fixed += len(records)
                                _yahoo_fixed_ticker = len(records)
                    except Exception:
                        _yahoo_confirmed_any = True  # Bei Fehler: konservativ als echte Lücke werten

                    # Echte Lücke: Yahoo hat Daten (oder Fehler), aber nicht alle fehlen konnten gefixxt werden
                    if _yahoo_confirmed_any and (len(missing_days) - _yahoo_fixed_ticker) > 0:
                        missing_total += len(missing_days) - _yahoo_fixed_ticker
                        missing_details[ticker] = [d.strftime("%Y-%m-%d") for d in missing_days]
                    # Sonst: Kalender-Edgecase — Börse war zu, kein Eintrag in missing_details

            except Exception as te:
                health_errors.append(f"{ticker}: {te}")

        if missing_total > 0:
            print(f"Health-Check: {len(missing_details)} Ticker mit {missing_total} fehlenden Tagen, {auto_fixed} auto-gefixt")
        else:
            print("Health-Check: Alle Ticker vollständig ✓")

    except Exception as e:
        app_logger.error(f"nightly_refresh: Health-Check fehlgeschlagen: {e}")
        print(f"Health-Check failed: {e}")

    # Phase D: Backfill NULL log_return (letzte 14 Tage)
    # Fängt Fälle ab, in denen Kurse vorhanden sind aber log_return fehlt
    # (z.B. nach Feiertags-Lücken oder Import ohne Vortags-Close)
    # Per-Ticker-Iteration statt Full-Table-Scan → vermeidet Supabase Statement-Timeout
    backfill_fixed = 0
    backfill_null_total = 0
    try:
        import math
        from shared.supabase_client import get_client as _get_client_bf

        _bf_client = _get_client_bf()
        _bf_cutoff = (date.today() - __import__('datetime').timedelta(days=14)).strftime("%Y-%m-%d")

        for _bf_ticker in tickers:
            try:
                _null_rows = (_bf_client.table("prices")
                              .select("date,close")
                              .eq("ticker", _bf_ticker)
                              .gte("date", _bf_cutoff)
                              .is_("log_return", "null")
                              .order("date")
                              .execute().data)

                backfill_null_total += len(_null_rows)
                for _bf_row in _null_rows:
                    try:
                        _prev = (_bf_client.table("prices")
                                 .select("close")
                                 .eq("ticker", _bf_ticker)
                                 .lt("date", _bf_row["date"])
                                 .order("date", desc=True)
                                 .limit(1)
                                 .execute().data)
                        if _prev and _prev[0]["close"] and _prev[0]["close"] > 0:
                            _lr = math.log(_bf_row["close"] / _prev[0]["close"])
                            (_bf_client.table("prices")
                             .update({"log_return": round(_lr, 8)})
                             .eq("ticker", _bf_ticker)
                             .eq("date", _bf_row["date"])
                             .execute())
                            backfill_fixed += 1
                    except Exception:
                        pass
            except Exception:
                pass  # Einzelner Ticker-Fehler → weiter

        if backfill_fixed:
            print(f"Backfill log_return: {backfill_fixed}/{backfill_null_total} gefixt")
        else:
            print("Backfill log_return: keine NULL-Rows ✓")

    except Exception as e:
        app_logger.error(f"nightly_refresh: Backfill fehlgeschlagen: {e}")
        print(f"Backfill log_return failed: {e}")

    # Phase E: Stress-Ampel (shared/stress_score.py) — jeder Lauf ist ein geprüfter Vollauf mit eigener Version;
    # sichtbar erst nach Rücklesevergleich und atomarer Veröffentlichung (Plan 2026-10-09 v5, Y1/Y2).
    regime_status = {"ok": False, "tickers": [], "scores": 0, "error": None}
    try:
        from shared import stress_score as _stress
        for _rt in ["SPY"]:
            _r = _stress.vollauf(_rt, protokoll=lambda m: print(m, flush=True))
            regime_status["tickers"].append(_rt)
            regime_status["scores"] += _r["n_scores"]
        regime_status["ok"] = regime_status["scores"] > 0
    except Exception as e:
        # Volltext (kann Score/Farbe enthalten, z. B. aus dem Rücklesevergleich) NUR ins App-Log; refresh_log und damit
        # die Health-Mail bekommen einen neutralen Befund — keine Ampel in Mails (Nutzerentscheidung 2026-10-09).
        regime_status["error"] = f"Stress-Lauf gescheitert ({type(e).__name__}), Details im App-Log"
        app_logger.error(f"nightly_refresh: Stress-Ampel fehlgeschlagen: {e}")
        print(f"Stress-Ampel failed: {e}")

    # Phase E1b: Spot-Vol-Beta (SPX vs VIX) — hatte bisher KEINEN Cron und stand still.
    try:
        from shared.spot_vol_beta import (
            load_spot_vol_data, compute_spot_vol_beta, sync_spot_vol_to_db,
        )
        _svb_df = load_spot_vol_data()
        if _svb_df is not None and not _svb_df.empty:
            _svb_calc, _ = compute_spot_vol_beta(_svb_df)
            _svb_n = sync_spot_vol_to_db(_svb_calc)
            print(f"Spot-Vol-Beta: {_svb_n} Zeilen aktualisiert", flush=True)
        else:
            print("Spot-Vol-Beta: keine Daten geladen", flush=True)
    except Exception as e:
        app_logger.error(f"nightly_refresh: Spot-Vol-Beta fehlgeschlagen: {e}")
        print(f"Spot-Vol-Beta failed: {e}", flush=True)

    # Phase E2: refresh_log schreiben
    try:
        from shared.supabase_client import get_client
        _log_client = get_client()
        import json
        _log_entry = {
            "run_date": date.today().strftime("%Y-%m-%d"),
            "run_type": "nightly",
            "tickers_total": len(tickers),
            "tickers_success": len(tickers) - len(missing_details),
            "tickers_missing": len(missing_details),
            "missing_details": json.dumps(missing_details),
            "auto_fixed": auto_fixed + backfill_fixed,
            "duration_seconds": round(time.time() - t_start, 1),
            "errors": json.dumps(health_errors[:20]),
        }
        # Regime-Status ergaenzen (in errors-Feld, da kein eigenes Feld)
        if not regime_status["ok"]:
            _errs = json.loads(_log_entry["errors"])
            _errs.append(f"STRESS: {regime_status.get('error') or 'kein Lauf veröffentlicht'}")
            _log_entry["errors"] = json.dumps(_errs)
        _log_client.table("refresh_log").insert(_log_entry).execute()
        print("Refresh-Log: geschrieben ✓")
    except Exception as e:
        print(f"Refresh-Log failed: {e}")

    # Phase F: Weekly Newsletter (nur Sonntags ab 17:00 UTC = 18:00 Berlin-Winter / 19:00 Berlin-Sommer)
    # WICHTIG: capture_output=False damit Newsletter-Output direkt in docker logs
    # erscheint (analog Phase G). Vorher war capture_output=True, dadurch war der
    # Output unsichtbar und Fehler nicht diagnostizierbar.
    try:
        from datetime import datetime as _dt, timezone as _tz
        _now = _dt.now(_tz.utc)
        from shared.constants import WEEKLY_NEWSLETTER_AN
        if not WEEKLY_NEWSLETTER_AN:
            print("Weekly Newsletter: abgeschaltet (shared/constants.py WEEKLY_NEWSLETTER_AN)", flush=True)
        elif _now.weekday() == 6 and _now.hour >= 17:  # 6 = Sonntag
            app_logger.info("[phase-f] Sonntag ≥17 UTC → starte Weekly Newsletter")
            print("=" * 60, flush=True)
            print("Weekly Newsletter: Sonntag erkannt, starte Versand...", flush=True)
            import subprocess as _sp
            _res = _sp.run(
                [sys.executable, "scripts/weekly_newsletter.py"],
                cwd=_project_dir, env=_KIND_UMGEBUNG,
                timeout=1800,  # 30 Min max
            )
            if _res.returncode == 0:
                print("Weekly Newsletter: versendet ✓", flush=True)
            else:
                app_logger.error(f"[phase-f] weekly_newsletter exit {_res.returncode}")
                print(f"Weekly Newsletter FAILED (exit {_res.returncode})", flush=True)
                _FEHLGESCHLAGEN.append("Weekly Newsletter")
            print("=" * 60, flush=True)
        else:
            print(f"Weekly Newsletter: skip (weekday={_now.weekday()}, hour={_now.hour} UTC, Sonntag ≥17 UTC gefordert)")
    except Exception as e:
        app_logger.error(f"nightly_refresh: Weekly Newsletter fehlgeschlagen: {e}")
        print(f"Weekly Newsletter: exception {e}")
        _FEHLGESCHLAGEN.append("Weekly Newsletter")

    # Phase G (Polymarket-Snapshot/-Backfill) und Phase H (Brier) sind entfernt
    # (2026-09-29). Sie scheiterten hier jeden Tag an der vererbten alten
    # SUPABASE_URL (siehe _KIND_UMGEBUNG) und waren laengst durch eigene Workflows
    # ersetzt: polymarket_daily.yml (taeglich, montags Backfill) und
    # brier_compute.yml (sonntags, mit vorherigem Scrape). Nach dem Umgebungs-Fix
    # liefen sie sonst doppelt. Genau EIN Ausloeser pro Aufgabe.

    # Phase I: Landing-Hero-Chart regenerieren (chart-data.json) — taeglich, sonst friert die
    # "aktuelles Jahr"-Kurve ein (stand bis 2026-06 still, weil kein Cron). Schreibt landing/data (rw-Mount).
    try:
        import subprocess as _sp3
        app_logger.info("[phase-i] starte generate_landing_chart")
        _resI = _sp3.run(
            [sys.executable, "scripts/generate_landing_chart.py"],
            cwd=_project_dir, env=_KIND_UMGEBUNG, timeout=300,
        )
        if _resI.returncode == 0:
            print("Landing-Chart: OK", flush=True)
            app_logger.info("[phase-i] generate_landing_chart OK")
        else:
            print(f"Landing-Chart FAILED (exit {_resI.returncode})", flush=True)
            _FEHLGESCHLAGEN.append("Landing-Chart")
            app_logger.error(f"[phase-i] generate_landing_chart exit {_resI.returncode}")
    except Exception as e:
        app_logger.error(f"nightly_refresh: Landing-Chart Phase I fehlgeschlagen: {e}")
        print(f"Landing-Chart Phase I: exception {e}", flush=True)
        _FEHLGESCHLAGEN.append("Landing-Chart Phase I")

    # Phase J: Wahl-Ereignisstudie (/wahlen) — Kurse um US-Wahltermine + Live-Linie der
    # nächsten Wahl. Läuft nach dem Kurs-Refresh, damit die letzte Session drin ist.
    # Exit != 0 (z. B. Wahl ab 1971 ohne Pfad, fehlende Live-Linie) → Nightly rot.
    try:
        import subprocess as _spJ
        app_logger.info("[phase-j] starte build_wahlen")
        _resJ = _spJ.run(
            [sys.executable, "scripts/build_wahlen.py"],
            cwd=_project_dir, env=_KIND_UMGEBUNG, timeout=600,
        )
        if _resJ.returncode == 0:
            print("Wahl-Studie: OK", flush=True)
        else:
            print(f"Wahl-Studie FAILED (exit {_resJ.returncode})", flush=True)
            _FEHLGESCHLAGEN.append("Wahl-Studie")
            app_logger.error(f"[phase-j] build_wahlen exit {_resJ.returncode}")
    except Exception as e:
        app_logger.error(f"nightly_refresh: Wahl-Studie Phase J fehlgeschlagen: {e}")
        print(f"Wahl-Studie Phase J: exception {e}", flush=True)
        _FEHLGESCHLAGEN.append("Wahl-Studie Phase J")

    # Phase Z: Supabase Heartbeat (verhindert Free-Tier Pausing)
    try:
        heartbeat()
    except Exception as e:
        app_logger.error(f"nightly_refresh: Heartbeat fehlgeschlagen: {e}")
        print(f"Heartbeat failed: {e}")

    elapsed = time.time() - t_start
    app_logger.info(f"nightly_refresh: Fertig — {n_results} Scanner-Ergebnisse in {elapsed:.0f}s")
    print(f"Done: {n_results} scanner results in {elapsed:.0f}s")

    if _FEHLGESCHLAGEN:
        print(f"Gescheiterte Phasen: {', '.join(_FEHLGESCHLAGEN)}", flush=True)
        app_logger.error(f"nightly_refresh: gescheiterte Phasen {_FEHLGESCHLAGEN}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
