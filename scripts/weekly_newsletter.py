#!/usr/bin/env python3
"""
scripts/weekly_newsletter.py — SeasonAlpha Weekly Report Sender

Rendert den wöchentlichen Saisonalitäts-Report und sendet ihn an alle
aktiven Subscriber via Brevo. Läuft Sonntags 18:00 Europe/Berlin via
Phase F in nightly_refresh.py (oder separatem Cron).

Usage:
    py scripts/weekly_newsletter.py              # Live-Send an alle Subscriber
    py scripts/weekly_newsletter.py --dry-run    # HTML auf Disk, kein Versand
    py scripts/weekly_newsletter.py --test       # Nur an ADMIN_EMAIL
    py scripts/weekly_newsletter.py --to x@y.de  # Einzelner Test-Empfänger

Environment Variables:
    BREVO_API_KEY        — Brevo API-Key (zwingend für Versand)
    ADMIN_EMAIL          — Test-Empfänger für --test (Default: heiko@...)
    UNSUBSCRIBE_SECRET   — HMAC-Secret für Unsubscribe-Tokens
    SUPABASE_URL         — Supabase REST Endpoint
    SUPABASE_KEY         — Supabase Service-Role-Key
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
import time
from datetime import datetime

# Projekt-Root in sys.path
_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)


# ── Konfiguration ────────────────────────────────────────────────────────
TEMPLATE_DIR = pathlib.Path(_project_dir) / "scripts" / "templates"
TEMPLATE_NAME = "weekly_report.html.j2"
SEND_RATE_LIMIT_SEC = 0.35  # ≈ 2.8 Mails/Sekunde, unter Brevo-Free-Limit
DRY_RUN_OUTPUT_FILE = pathlib.Path(_project_dir) / "weekly_report_preview.html"


def _load_template():
    """Lädt das Jinja2-Template — import lazy damit das Modul auch ohne
    Jinja2 importierbar bleibt (für Phase F health-check)."""
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        raise RuntimeError(
            "Jinja2 fehlt — bitte installieren: py -m pip install jinja2"
        )
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env.get_template(TEMPLATE_NAME)


def render_email(context: dict, recipient_email: str) -> tuple[str, str]:
    """
    Rendert HTML + Subject für einen konkreten Empfänger.
    Der Unsubscribe-Link ist recipient-spezifisch (HMAC-Token).
    """
    from shared.unsubscribe_token import generate_unsubscribe_url

    tpl = _load_template()
    context_with_unsub = {
        **context,
        "unsubscribe_url": generate_unsubscribe_url(recipient_email),
    }
    html = tpl.render(**context_with_unsub)
    subject = f"SeasonAlpha Weekly — KW {context['week_number']} · {context['report_date_display']}"
    return subject, html


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SeasonAlpha Weekly Newsletter Sender",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="HTML lokal rendern und auf Disk schreiben, kein Email-Versand",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Nur an ADMIN_EMAIL senden (für Live-Test im Postfach)",
    )
    parser.add_argument(
        "--to",
        type=str,
        help="Einzelner Test-Empfänger (überschreibt --test)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Anzahl Top-KI-Tickers im Report (Default 10)",
    )
    args = parser.parse_args()

    from shared.logger import app_logger, error_logger
    from shared.weekly_report import build_report_context

    app_logger.info("[weekly] Starting weekly newsletter job")
    t_start = time.time()

    # 1. Report-Context bauen
    try:
        context = build_report_context(top_n=args.top_n)
    except Exception as e:
        error_logger.error(f"[weekly] build_report_context failed: {e}")
        print(f"[ERROR] Report-Context-Aufbau fehlgeschlagen: {e}")
        return 2

    if not context.get("top_ki"):
        app_logger.warning("[weekly] Kein top_ki in Context — scanner_results leer?")
        print("[WARN] Keine KI-Scores verfügbar, Report würde leer sein.")
        if not args.dry_run and not args.to and not args.test:
            print("[ABORT] Versand abgebrochen — kein Inhalt.")
            return 3

    # 2. Empfänger bestimmen
    if args.to:
        recipients = [args.to.strip().lower()]
        mode = "single"
    elif args.test:
        admin = os.environ.get("ADMIN_EMAIL", "heiko@seasonalpha.ai")
        recipients = [admin]
        mode = "test (admin)"
    else:
        try:
            from shared.supabase_client import get_active_subscribers
            subs = get_active_subscribers() or []
            recipients = [s["email"] for s in subs if s.get("email")]
            mode = "live (all subscribers)"
        except Exception as e:
            error_logger.error(f"[weekly] get_active_subscribers failed: {e}")
            print(f"[ERROR] Subscriber-Liste konnte nicht geladen werden: {e}")
            return 4

    print(f"[weekly] Mode: {mode}")
    print(f"[weekly] Empfänger: {len(recipients)}")
    print(f"[weekly] Report-Datum: {context['report_date_display']} (KW {context['week_number']})")
    print(f"[weekly] Top-KI Ticker: {len(context['top_ki'])}")
    print(f"[weekly] Events: {len(context['events'])}")
    print(f"[weekly] TDoM-Bias: {len(context['tdom_bias'])}")
    print(f"[weekly] Regime-Records: {len(context['regimes'])}")

    # 3. Dry-Run: HTML auf Disk schreiben und fertig
    if args.dry_run:
        subject, html = render_email(context, "preview@seasonalpha.ai")
        with open(DRY_RUN_OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[DRY-RUN] Subject: {subject}")
        print(f"[DRY-RUN] HTML geschrieben nach: {DRY_RUN_OUTPUT_FILE}")
        print(f"[DRY-RUN] Würde an {len(recipients)} Empfänger gehen")
        return 0

    # 4. Live-Send mit Rate-Limiting
    from shared.email_brevo import send_html, send_admin_alert

    sent = 0
    failed = 0
    failed_emails = []

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
            error_logger.error(f"[weekly] Send failed for {email}: {e}")
            failed += 1
            failed_emails.append(email)

        # Progress-Log alle 50 Mails
        if i % 50 == 0:
            print(f"[weekly] Progress: {i}/{len(recipients)} (sent={sent}, failed={failed})")

        time.sleep(SEND_RATE_LIMIT_SEC)

    elapsed = time.time() - t_start
    summary = (
        f"[weekly] Done in {elapsed:.1f}s: {sent} sent, {failed} failed "
        f"(total {len(recipients)})"
    )
    print(summary)
    app_logger.info(summary)

    # 5. Admin-Alert bei hoher Fehlerrate
    if recipients and failed > len(recipients) * 0.1:
        try:
            preview = ", ".join(failed_emails[:10])
            send_admin_alert(
                f"Weekly Newsletter: {failed}/{len(recipients)} sends failed.\n"
                f"First failures: {preview}"
            )
        except Exception:
            pass
        return 5

    return 0


if __name__ == "__main__":
    sys.exit(main())
