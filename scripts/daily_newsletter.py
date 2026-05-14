#!/usr/bin/env python3
"""
scripts/daily_newsletter.py — SeasonAlpha Daily Morning Briefing Sender

Rendert das tägliche Morning-Briefing (Top-5 ETFs + Top-5 Aktien, Events,
saisonale Strategien, Sektor-Rotation, Risikolage) und sendet an alle
aktiven Subscriber der `daily_subscribers`-Tabelle via Brevo.

Schedule: Mo-Fr 06:00 UTC via .github/workflows/daily_newsletter.yml.

Usage:
    py scripts/daily_newsletter.py              # Live-Send an alle Daily-Subscriber
    py scripts/daily_newsletter.py --dry-run    # HTML auf Disk, kein Versand
    py scripts/daily_newsletter.py --test       # Nur an ADMIN_EMAIL
    py scripts/daily_newsletter.py --to x@y.de  # Einzelner Test-Empfänger

Environment:
    BREVO_API_KEY        — zwingend für Versand
    ADMIN_EMAIL          — Test-Empfänger für --test
    UNSUBSCRIBE_SECRET   — HMAC-Secret (gemeinsam mit Weekly)
    SUPABASE_URL/KEY     — DB-Zugriff
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
import time
from datetime import datetime, timezone

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)


TEMPLATE_DIR = pathlib.Path(_project_dir) / "scripts" / "templates"
TEMPLATE_NAME = "daily_report.html.j2"
SEND_RATE_LIMIT_SEC = 0.35
DRY_RUN_OUTPUT_FILE = pathlib.Path(_project_dir) / "daily_report_preview.html"


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


def render_email(context: dict, recipient_email: str) -> tuple[str, str]:
    """Rendert HTML + Subject. Unsubscribe-URL pro Empfänger mit type=daily."""
    from shared.unsubscribe_token import generate_unsubscribe_url

    base = generate_unsubscribe_url(recipient_email)
    # Pfad-spezifischer Suffix damit /unsubscribe weiß welche Tabelle
    sep = "&" if "?" in base else "?"
    unsubscribe_url = f"{base}{sep}type=daily"

    tpl = _load_template()
    ctx = {**context, "unsubscribe_url": unsubscribe_url}
    html = tpl.render(**ctx)
    subject = f"🌅 SeasonAlpha — Morning Briefing {context['target_display']}"
    return subject, html


def _get_active_daily_subscribers() -> list[str]:
    """Liest aus daily_subscribers (status=active + no_emails=false)."""
    from shared.supabase_client import get_client
    rows = (
        get_client()
        .table("daily_subscribers")
        .select("email")
        .eq("status", "active")
        .eq("no_emails", False)
        .order("subscribed_at")
        .execute()
        .data
    ) or []
    return [r["email"] for r in rows if r.get("email")]


def _write_refresh_log(elapsed_sec: float, sent: int, failed: int,
                       failed_emails: list[str]) -> None:
    """Schreibt refresh_log-Eintrag für daily_health_check.py."""
    try:
        import json as _json
        from shared.supabase_client import get_client
        get_client().table("refresh_log").insert({
            "run_date":         datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "run_type":         "daily_newsletter",
            "tickers_total":    sent + failed,
            "tickers_success":  sent,
            "tickers_missing":  failed,
            "missing_details":  _json.dumps({"failed_emails": failed_emails[:20]}),
            "auto_fixed":       0,
            "duration_seconds": round(elapsed_sec, 1),
            "errors":           "[]",
        }).execute()
    except Exception as exc:
        print(f"[daily] refresh_log insert failed: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="SeasonAlpha Daily Morning Briefing")
    parser.add_argument("--dry-run", action="store_true",
                        help="HTML auf Disk schreiben, kein Versand")
    parser.add_argument("--test", action="store_true",
                        help="Nur an ADMIN_EMAIL senden")
    parser.add_argument("--to", type=str, help="Einzelner Test-Empfänger")
    parser.add_argument("--n-etfs", type=int, default=5)
    parser.add_argument("--n-stocks", type=int, default=5)
    args = parser.parse_args()

    from shared.logger import app_logger, error_logger
    from shared.daily_report import build_daily_context

    app_logger.info("[daily] Starting daily newsletter job")
    t_start = time.time()

    # 1. Context bauen
    try:
        context = build_daily_context(n_etfs=args.n_etfs, n_stocks=args.n_stocks)
    except Exception as e:
        error_logger.error(f"[daily] build_daily_context failed: {e}")
        print(f"[ERROR] Context-Aufbau fehlgeschlagen: {e}")
        return 2

    # Sanity-Check: leerer Newsletter macht keinen Sinn
    has_content = bool(context.get("etfs") or context.get("stocks") or context.get("events"))
    if not has_content:
        app_logger.warning("[daily] Kein Inhalt — abort send")
        print("[WARN] Newsletter würde leer sein (keine Tipps, keine Events).")
        if not args.dry_run and not args.to and not args.test:
            print("[ABORT] Live-Send abgebrochen.")
            return 3

    # 2. Empfänger bestimmen
    if args.to:
        recipients = [args.to.strip().lower()]
        mode = "single"
    elif args.test:
        admin = os.environ.get("ADMIN_EMAIL", "heiko.seibel@gmail.com")
        recipients = [admin]
        mode = "test (admin)"
    else:
        try:
            recipients = _get_active_daily_subscribers()
            mode = "live (daily_subscribers)"
        except Exception as e:
            error_logger.error(f"[daily] get subscribers failed: {e}")
            print(f"[ERROR] Subscriber-Liste konnte nicht geladen werden: {e}")
            return 4

    print(f"[daily] Mode: {mode}")
    print(f"[daily] Empfänger: {len(recipients)}")
    print(f"[daily] Target: {context['target_display']} (TDOM {context.get('target_tdom')})")
    print(f"[daily] Top-ETFs: {len(context.get('etfs', []))}  Top-Aktien: {len(context.get('stocks', []))}")
    print(f"[daily] Events: {len(context.get('events', []))}  Strategien aktiv: {len(context.get('strategies', []))}")

    # 3. Dry-Run
    if args.dry_run:
        subject, html = render_email(context, "preview@seasonalpha.ai")
        with open(DRY_RUN_OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[DRY-RUN] Subject: {subject}")
        print(f"[DRY-RUN] HTML: {DRY_RUN_OUTPUT_FILE}")
        return 0

    # 4. Live-Send
    from shared.email_brevo import send_html, send_admin_alert

    sent = 0
    failed = 0
    failed_emails: list[str] = []

    for i, email in enumerate(recipients, 1):
        try:
            subject, html = render_email(context, email)
            ok = send_html(email, subject, html)
            if ok:
                sent += 1
            else:
                failed += 1
                failed_emails.append(email)
        except Exception as e:
            error_logger.error(f"[daily] Send failed for {email}: {e}")
            failed += 1
            failed_emails.append(email)

        if i % 50 == 0:
            print(f"[daily] Progress: {i}/{len(recipients)} (sent={sent}, failed={failed})")
        time.sleep(SEND_RATE_LIMIT_SEC)

    elapsed = time.time() - t_start
    print(f"[daily] Done in {elapsed:.1f}s: {sent} sent, {failed} failed")
    app_logger.info(f"[daily] Done in {elapsed:.1f}s: sent={sent} failed={failed}")

    # 5. refresh_log für Health-Check (auch im Live-Mode)
    _write_refresh_log(elapsed, sent, failed, failed_emails)

    # 6. Admin-Alert bei >10% Failrate
    if recipients and failed > len(recipients) * 0.1:
        try:
            preview = ", ".join(failed_emails[:10])
            send_admin_alert(
                f"Daily Newsletter: {failed}/{len(recipients)} sends failed.\n"
                f"First failures: {preview}"
            )
        except Exception:
            pass
        return 5

    return 0


if __name__ == "__main__":
    sys.exit(main())
