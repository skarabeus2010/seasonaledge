#!/usr/bin/env python3
"""
scripts/daily_health_check.py — SeasonAlpha System-Health Morning Report

Pruft taeglich 07:00 UTC ob die wichtigsten Cron-Jobs + DB-Schreibzugriffe
der letzten 24h gesund waren. Sendet eine farbkodierte Status-Mail an
ADMIN_EMAIL (Grun/Gelb/Rot mit Detail-Tabelle).

Usage:
    py scripts/daily_health_check.py            # Live an ADMIN_EMAIL
    py scripts/daily_health_check.py --dry-run  # HTML auf Disk, kein Versand
    py scripts/daily_health_check.py --to x@y   # Einzelner Empfanger

Environment:
    BREVO_API_KEY   — zwingend fuer Versand
    ADMIN_EMAIL     — Default-Empfanger (Fallback: heiko.seibel@gmail.com)
    SUPABASE_URL    — Supabase REST Endpoint
    SUPABASE_KEY    — Service-Role-Key
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
from datetime import datetime, date, timedelta, timezone

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)


TEMPLATE_DIR = pathlib.Path(_project_dir) / "scripts" / "templates"
TEMPLATE_NAME = "health_report.html.j2"
DRY_RUN_OUTPUT_FILE = pathlib.Path(_project_dir) / "health_report_preview.html"

# Schwellen in Werktagen (Mo-Fr). Crypto ist 24/7 aber wir pruefen gegen UTC-Datum.
PRICES_MAX_AGE_WORKDAYS = 1       # SPY darf hoechstens 1 Werktag alt sein
CRYPTO_MAX_AGE_DAYS = 1           # BTC darf hoechstens 1 Tag alt sein
WEEKLY_SCANNER_MAX_AGE_DAYS = 8   # Scanner laeuft Sonntags, 8 Tage Puffer
POLYMARKET_MAX_AGE_DAYS = 2       # Phase G taeglich
EVENT_DATA_MAX_AGE_DAYS = 2       # event_data_daily.yml taeglich 22:15 UTC
DAILY_NL_MAX_AGE_WORKDAYS = 2     # daily_newsletter.yml Mo-Fr 06:00 UTC


def _last_workday(ref: date) -> date:
    """Letzter Werktag (Mo-Fr) bis einschl. ref."""
    d = ref
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def _status(ok: bool, warn: bool = False) -> str:
    if ok:
        return "green"
    if warn:
        return "yellow"
    return "red"


def collect_health_data() -> dict:
    """Sammelt alle Health-Checks in ein Dict fuer Template-Rendering."""
    from shared.supabase_client import get_client

    now_utc = datetime.now(timezone.utc)
    today_utc = now_utc.date()
    yesterday_utc = today_utc - timedelta(days=1)
    last_workday = _last_workday(today_utc - timedelta(days=1))

    client = get_client()
    checks = []
    overall_status = "green"

    def downgrade(new_status: str):
        nonlocal overall_status
        priority = {"green": 0, "yellow": 1, "red": 2}
        if priority[new_status] > priority[overall_status]:
            overall_status = new_status

    # ── Check 1: Letzter Nightly-Run ──────────────────────────────────
    try:
        resp = (
            client.table("refresh_log")
            .select("run_date,run_type,duration_seconds,errors,tickers_success,tickers_total,created_at")
            .eq("run_type", "nightly")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            checks.append({
                "name": "Nightly Refresh",
                "status": "red",
                "detail": "Kein Eintrag in refresh_log",
                "value": "—",
            })
            downgrade("red")
        else:
            last = rows[0]
            run_date = last.get("run_date")
            errors_raw = last.get("errors") or "[]"
            try:
                errors = json.loads(errors_raw) if isinstance(errors_raw, str) else errors_raw
            except Exception:
                errors = []
            duration = last.get("duration_seconds")
            success = last.get("tickers_success", 0)
            total = last.get("tickers_total", 0)

            run_d = datetime.strptime(run_date, "%Y-%m-%d").date() if run_date else None
            age_days = (today_utc - run_d).days if run_d else 999

            if age_days > 1:
                status = "red"
                detail = f"Letzter Run {age_days} Tage alt ({run_date})"
            elif errors and len(errors) > 0:
                status = "yellow"
                detail = f"{run_date} · {len(errors)} Fehler: {str(errors[0])[:80]}"
            elif total and success < total * 0.95:
                status = "yellow"
                detail = f"{run_date} · {success}/{total} erfolgreich ({(success/total*100):.0f}%)"
            else:
                status = "green"
                detail = f"{run_date} · {duration}s · {success}/{total} Ticker"
            checks.append({
                "name": "Nightly Refresh",
                "status": status,
                "detail": detail,
                "value": run_date or "—",
            })
            downgrade(status)
    except Exception as e:
        checks.append({
            "name": "Nightly Refresh",
            "status": "red",
            "detail": f"Query-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    # ── Check 2: prices Frische SPY (als US-Proxy) ────────────────────
    try:
        resp = (
            client.table("prices")
            .select("date")
            .eq("ticker", "SPY")
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            checks.append({
                "name": "prices: SPY",
                "status": "red",
                "detail": "Keine Datenzeilen",
                "value": "—",
            })
            downgrade("red")
        else:
            last_date_str = rows[0]["date"]
            last_d = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            age_workdays = 0
            probe = last_workday
            while probe > last_d:
                probe -= timedelta(days=1)
                while probe.weekday() >= 5:
                    probe -= timedelta(days=1)
                age_workdays += 1

            if age_workdays == 0:
                status, detail = "green", f"Aktuell bis {last_date_str}"
            elif age_workdays <= PRICES_MAX_AGE_WORKDAYS:
                status = "yellow"
                detail = f"{last_date_str} ({age_workdays} Werktag hinterher)"
            else:
                status = "red"
                detail = f"{last_date_str} ({age_workdays} Werktage hinterher)"
            checks.append({
                "name": "prices: SPY",
                "status": status,
                "detail": detail,
                "value": last_date_str,
            })
            downgrade(status)
    except Exception as e:
        checks.append({
            "name": "prices: SPY",
            "status": "red",
            "detail": f"Query-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    # ── Check 3: prices Frische BTC-USD (Crypto 24/7) ─────────────────
    try:
        resp = (
            client.table("prices")
            .select("date")
            .eq("ticker", "BTC-USD")
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            checks.append({
                "name": "prices: BTC-USD",
                "status": "red",
                "detail": "Keine Datenzeilen",
                "value": "—",
            })
            downgrade("red")
        else:
            last_date_str = rows[0]["date"]
            last_d = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            age = (today_utc - last_d).days
            if age <= CRYPTO_MAX_AGE_DAYS:
                status, detail = "green", f"Aktuell bis {last_date_str}"
            elif age <= CRYPTO_MAX_AGE_DAYS + 1:
                status = "yellow"
                detail = f"{last_date_str} ({age} Tage alt)"
            else:
                status = "red"
                detail = f"{last_date_str} ({age} Tage alt)"
            checks.append({
                "name": "prices: BTC-USD",
                "status": status,
                "detail": detail,
                "value": last_date_str,
            })
            downgrade(status)
    except Exception as e:
        checks.append({
            "name": "prices: BTC-USD",
            "status": "red",
            "detail": f"Query-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    # ── Check 4: Weekly Scanner-Run ───────────────────────────────────
    try:
        resp = (
            client.table("scanner_results")
            .select("scan_date")
            .order("scan_date", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            checks.append({
                "name": "Weekly Scanner",
                "status": "red",
                "detail": "scanner_results leer",
                "value": "—",
            })
            downgrade("red")
        else:
            last_date_str = rows[0]["scan_date"]
            last_d = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            age = (today_utc - last_d).days
            if age <= WEEKLY_SCANNER_MAX_AGE_DAYS:
                status, detail = "green", f"Letzter Run: {last_date_str} ({age}d)"
            else:
                status = "red"
                detail = f"{last_date_str} ({age} Tage alt, erwartet ≤{WEEKLY_SCANNER_MAX_AGE_DAYS}d)"
            checks.append({
                "name": "Weekly Scanner",
                "status": status,
                "detail": detail,
                "value": last_date_str,
            })
            downgrade(status)
    except Exception as e:
        checks.append({
            "name": "Weekly Scanner",
            "status": "red",
            "detail": f"Query-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    # ── Check 4b: Options-Daten (Skew/IV + GEX-Ketten) ────────────────
    try:
        import json as _json
        _dd = pathlib.Path(__file__).resolve().parent.parent / "landing" / "data"
        sp = _dd / "options_skew.json"
        if not sp.exists():
            checks.append({"name": "Options: Skew/IV", "status": "red",
                           "detail": "options_skew.json fehlt (Cron nie gelaufen?)", "value": "—"})
            downgrade("red")
        else:
            od = _json.loads(sp.read_text(encoding="utf-8"))
            gen = od.get("generated"); tk = od.get("tickers", [])
            wterm = sum(1 for t in tk if t.get("term") and t.get("iv_atm"))
            age = (today_utc - datetime.strptime(gen, "%Y-%m-%d").date()).days if gen else 999
            if age > 5 or len(tk) < 50:
                status = "red"; detail = f"{gen} · {len(tk)} Ticker, {wterm} mit Metrik ({age}d alt)"
            elif age > 3 or len(tk) < 100 or wterm < 100:
                status = "yellow"; detail = f"{gen} · {len(tk)} Ticker, {wterm} mit voller Metrik"
            else:
                status = "green"; detail = f"{gen} · {len(tk)} Ticker, {wterm} mit voller Metrik"
            checks.append({"name": "Options: Skew/IV", "status": status, "detail": detail, "value": gen or "—"})
            downgrade(status)
        gp = _dd / "gex_summary.json"
        if not gp.exists():
            checks.append({"name": "Options: GEX-Ketten", "status": "red",
                           "detail": "gex_summary.json fehlt", "value": "—"})
            downgrade("red")
        else:
            gd = _json.loads(gp.read_text(encoding="utf-8"))
            gdate = gd.get("date"); gtk = gd.get("tickers", [])
            wflip = sum(1 for t in gtk if t.get("zero_gamma"))
            age = (today_utc - datetime.strptime(gdate, "%Y-%m-%d").date()).days if gdate else 999
            if age > 8 or len(gtk) < 5:
                status = "red"; detail = f"{gdate} · {len(gtk)} Ticker ({age}d alt)"
            elif age > 4 or wflip < len(gtk) * 0.6:
                status = "yellow"; detail = f"{gdate} · {len(gtk)} Ticker, {wflip} mit Zero-Gamma-Flip"
            else:
                status = "green"; detail = f"{gdate} · {len(gtk)} Ticker (Flip/Walls)"
            checks.append({"name": "Options: GEX-Ketten", "status": status, "detail": detail, "value": gdate or "—"})
            downgrade(status)
    except Exception as e:
        checks.append({"name": "Options-Daten", "status": "red",
                       "detail": f"Fehler: {str(e)[:100]}", "value": "ERR"})
        downgrade("red")

    # ── Check 5: Polymarket Snapshot ──────────────────────────────────
    try:
        resp = (
            client.table("polymarket_prices")
            .select("ts")
            .order("ts", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            checks.append({
                "name": "Polymarket Phase G",
                "status": "red",
                "detail": "polymarket_prices leer",
                "value": "—",
            })
            downgrade("red")
        else:
            ts_str = rows[0]["ts"]
            # ts kommt als ISO; date-Anteil reicht
            last_d = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).date()
            age = (today_utc - last_d).days
            if age <= POLYMARKET_MAX_AGE_DAYS:
                status, detail = "green", f"Letzter Snapshot: {last_d}"
            else:
                status = "red"
                detail = f"{last_d} ({age} Tage alt)"
            checks.append({
                "name": "Polymarket Phase G",
                "status": status,
                "detail": detail,
                "value": last_d.isoformat(),
            })
            downgrade(status)
    except Exception as e:
        checks.append({
            "name": "Polymarket Phase G",
            "status": "red",
            "detail": f"Query-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    # ── Check 5b: Event Data (Dividenden + Earnings) ──────────────────
    try:
        resp = (
            client.table("refresh_log")
            .select("run_date,duration_seconds,tickers_success,tickers_total,missing_details,created_at")
            .eq("run_type", "event_data")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            checks.append({
                "name": "Event Data (Div+Earn)",
                "status": "red",
                "detail": "Kein Eintrag in refresh_log (Cron nie gelaufen?)",
                "value": "—",
            })
            downgrade("red")
        else:
            last = rows[0]
            run_date = last.get("run_date")
            run_d = datetime.strptime(run_date, "%Y-%m-%d").date() if run_date else None
            age_days = (today_utc - run_d).days if run_d else 999
            success = last.get("tickers_success", 0)
            total = last.get("tickers_total", 0)
            details_raw = last.get("missing_details") or "{}"
            try:
                details = json.loads(details_raw) if isinstance(details_raw, str) else details_raw
            except Exception:
                details = {}
            div_n = details.get("div_rows", 0)
            earn_n = details.get("earn_rows", 0)

            if age_days > EVENT_DATA_MAX_AGE_DAYS:
                status = "red"
                detail = f"Letzter Run {age_days}d alt ({run_date})"
            elif total and success < total * 0.80:
                status = "yellow"
                detail = f"{run_date} · {success}/{total} OK · {div_n}d/{earn_n}e"
            else:
                status = "green"
                detail = f"{run_date} · {success}/{total} Ticker · {div_n} div + {earn_n} earn"
            checks.append({
                "name": "Event Data (Div+Earn)",
                "status": status,
                "detail": detail,
                "value": run_date or "—",
            })
            downgrade(status)
    except Exception as e:
        checks.append({
            "name": "Event Data (Div+Earn)",
            "status": "red",
            "detail": f"Query-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    # ── Check 6b: Intraday-Coverage (letzte 24h) ──────────────────────
    try:
        since_iso = (now_utc - timedelta(hours=24)).isoformat()
        resp = (
            client.table("refresh_log")
            .select("created_at,duration_seconds,errors")
            .eq("run_type", "intraday")
            .gte("created_at", since_iso)
            .order("created_at", desc=True)
            .execute()
        )
        rows = resp.data or []
        count = len(rows)
        is_weekend = now_utc.weekday() >= 5

        if is_weekend:
            # Wochenende: nur Crypto aktiv, ~4 Runs im Durchschnitt
            if count >= 3:
                status, detail = "green", f"{count} Runs (Wochenende, erwartet 3+)"
            elif count >= 1:
                status, detail = "yellow", f"{count} Runs (Wochenende, erwartet 3+)"
            else:
                status, detail = "red", "Keine Intraday-Runs in 24h"
        else:
            if count >= 10:
                status, detail = "green", f"{count} Runs in 24h"
            elif count >= 5:
                status, detail = "yellow", f"{count} Runs (erwartet ≥10)"
            else:
                status, detail = "red", f"Nur {count} Runs in 24h (erwartet ≥10)"

        checks.append({
            "name": "Intraday-Coverage (24h)",
            "status": status,
            "detail": detail,
            "value": str(count),
        })
        downgrade(status)
    except Exception as e:
        checks.append({
            "name": "Intraday-Coverage (24h)",
            "status": "red",
            "detail": f"Query-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    # ── Check 6c: Brier-Stats (Polymarket-Kalibrierung, wöchentlich) ──
    try:
        import os as _os
        _brier_path = "/app/landing/data/brier_stats.json"
        if not _os.path.exists(_brier_path):
            checks.append({
                "name": "Brier-Stats",
                "status": "red",
                "detail": "brier_stats.json fehlt (compute nie gelaufen)",
                "value": "—",
            })
            downgrade("red")
        else:
            _mtime = datetime.fromtimestamp(_os.path.getmtime(_brier_path), tz=timezone.utc)
            _age_days = (now_utc - _mtime).days
            if _age_days <= 10:
                status, detail = "green", f"Zuletzt berechnet: {_mtime.date()} ({_age_days}d)"
            elif _age_days <= 14:
                status = "yellow"
                detail = f"{_mtime.date()} ({_age_days}d, erwartet ≤10d)"
            else:
                status = "red"
                detail = f"{_mtime.date()} ({_age_days}d alt, Cron greift nicht)"
            checks.append({
                "name": "Brier-Stats",
                "status": status,
                "detail": detail,
                "value": _mtime.date().isoformat(),
            })
            downgrade(status)
    except Exception as e:
        checks.append({
            "name": "Brier-Stats",
            "status": "red",
            "detail": f"Check-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    # ── Check 5c: Daily Newsletter ─────────────────────────────────
    # Mo-Fr 06:00 UTC. Am Wochenende gibt es keinen Run, daher Schwelle in
    # Werktagen (ähnlich SPY-Frische): erlaubt 2 Werktage Verzug.
    try:
        resp = (
            client.table("refresh_log")
            .select("run_date,duration_seconds,tickers_success,tickers_total,missing_details,created_at")
            .eq("run_type", "daily_newsletter")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        is_weekend_today = now_utc.weekday() >= 5
        if not rows:
            # Vor erstem Live-Run noch keine Daten — yellow statt red.
            checks.append({
                "name": "Daily Newsletter",
                "status": "yellow",
                "detail": "Kein Eintrag in refresh_log (noch nie gelaufen?)",
                "value": "—",
            })
            downgrade("yellow")
        else:
            last = rows[0]
            run_date = last.get("run_date")
            run_d = datetime.strptime(run_date, "%Y-%m-%d").date() if run_date else None
            # Werktage zwischen run_d und last_workday zählen
            age_workdays = 0
            if run_d is not None:
                probe = last_workday
                while probe > run_d:
                    probe -= timedelta(days=1)
                    while probe.weekday() >= 5:
                        probe -= timedelta(days=1)
                    age_workdays += 1
            success = last.get("tickers_success", 0)
            total = last.get("tickers_total", 0)

            if is_weekend_today and age_workdays <= 1:
                # Wochenende: kein Send erwartet, gestern's Run ist OK
                status = "green"
                detail = f"{run_date} · {success}/{total} (kein Send am WE)"
            elif age_workdays == 0:
                status = "green"
                detail = f"{run_date} · {success}/{total} Empfänger"
            elif age_workdays <= DAILY_NL_MAX_AGE_WORKDAYS:
                status = "yellow"
                detail = f"{run_date} ({age_workdays} Werktag(e) hinterher)"
            else:
                status = "red"
                detail = f"{run_date} ({age_workdays} Werktage hinterher)"

            # Hohe Fehlerrate → mindestens yellow
            if total and success < total * 0.9 and status == "green":
                status = "yellow"
                detail = f"{run_date} · nur {success}/{total} (<90%) zugestellt"

            checks.append({
                "name": "Daily Newsletter",
                "status": status,
                "detail": detail,
                "value": run_date or "—",
            })
            downgrade(status)
    except Exception as e:
        checks.append({
            "name": "Daily Newsletter",
            "status": "red",
            "detail": f"Query-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    # ── Check 6: Regime-Scores (Crash-Ampel) ──────────────────────────
    try:
        resp = (
            client.table("regime_scores")
            .select("date")
            .eq("ticker", "SPY")
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        rows = resp.data or []
        if not rows:
            checks.append({
                "name": "Regime-Scores (SPY)",
                "status": "red",
                "detail": "regime_scores leer",
                "value": "—",
            })
            downgrade("red")
        else:
            last_date_str = rows[0]["date"]
            last_d = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            age_workdays = 0
            probe = last_workday
            while probe > last_d:
                probe -= timedelta(days=1)
                while probe.weekday() >= 5:
                    probe -= timedelta(days=1)
                age_workdays += 1
            if age_workdays == 0:
                status, detail = "green", f"Aktuell bis {last_date_str}"
            elif age_workdays <= 1:
                status = "yellow"
                detail = f"{last_date_str} ({age_workdays} Werktag hinterher)"
            else:
                status = "red"
                detail = f"{last_date_str} ({age_workdays} Werktage hinterher)"
            checks.append({
                "name": "Regime-Scores (SPY)",
                "status": status,
                "detail": detail,
                "value": last_date_str,
            })
            downgrade(status)
    except Exception as e:
        checks.append({
            "name": "Regime-Scores (SPY)",
            "status": "red",
            "detail": f"Query-Fehler: {str(e)[:100]}",
            "value": "ERR",
        })
        downgrade("red")

    return {
        "overall_status": overall_status,
        "checks": checks,
        "report_time": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "report_date": today_utc.strftime("%Y-%m-%d"),
    }


def _load_template():
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        raise RuntimeError("Jinja2 fehlt — py -m pip install jinja2")
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env.get_template(TEMPLATE_NAME)


def render_email(context: dict) -> tuple[str, str]:
    tpl = _load_template()
    html = tpl.render(**context)
    icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(context["overall_status"], "⚪")
    subject = f"{icon} SeasonAlpha Health — {context['report_date']}"
    return subject, html


def main() -> int:
    parser = argparse.ArgumentParser(description="SeasonAlpha Daily Health Check")
    parser.add_argument("--dry-run", action="store_true",
                        help="HTML auf Disk schreiben, kein Versand")
    parser.add_argument("--to", type=str, help="Einzelner Empfanger")
    args = parser.parse_args()

    from shared.logger import app_logger

    app_logger.info("[health] Starting daily health check")
    t_start = time.time()

    context = collect_health_data()
    subject, html = render_email(context)

    print(f"[health] Overall status: {context['overall_status']}")
    for c in context["checks"]:
        print(f"  [{c['status'].upper():6s}] {c['name']:25s} {c['detail']}")

    if args.dry_run:
        with open(DRY_RUN_OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[DRY-RUN] {subject}")
        print(f"[DRY-RUN] HTML: {DRY_RUN_OUTPUT_FILE}")
        return 0

    recipient = args.to or os.environ.get("ADMIN_EMAIL", "heiko.seibel@gmail.com")
    print(f"[health] Sending to: {recipient}")

    from shared.email_brevo import send_html
    ok = send_html(recipient, subject, html)

    elapsed = time.time() - t_start
    print(f"[health] Done in {elapsed:.1f}s: {'OK' if ok else 'FAILED'}")
    app_logger.info(f"[health] Done in {elapsed:.1f}s: sent={ok}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
