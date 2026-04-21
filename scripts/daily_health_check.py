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
            .select("run_date")
            .order("run_date", desc=True)
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
            last_date_str = rows[0]["run_date"]
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
