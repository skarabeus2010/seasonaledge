#!/usr/bin/env python3
"""
scripts/check_db_completeness.py — SeasonAlpha DB-Vollstaendigkeits-Audit
========================================================================
Tiefer Vollstaendigkeits-Check der Supabase-DB ueber 4 Dimensionen. Geht
ueber den taeglichen Freshness-Spotcheck (daily_health_check.py) hinaus:
prueft, ob ALLE Ticker in JEDER abgeleiteten Tabelle vorhanden sind, ob es
historische Datumsluecken gibt und ob die Event-Tabellen befuellt sind.

Dimensionen:
  freshness  — max(date) je Tabelle vs. letztem Handelstag
  coverage   — sind alle Ticker in jeder abgeleiteten Tabelle (+ vollstaendig)?
  gaps       — fehlende Handelstage in prices (boersenspezifisch) + NULL-Felder
  events     — earnings_events/dividend_events fuer Aktien befuellt?

Report: Konsole + JSON (landing/data/db_completeness.json) + refresh_log
(run_type='completeness') + optional Brevo-Mail an ADMIN_EMAIL.

Auto-Backfill (delegiert an bestehende Skripte, KEINE neue Write-Logik):
  --fix          schliesst Daten-Layer-Luecken (prices/ohlc/log_return/tdom/tdoy)
  --fix-derived  zusaetzlich teure Recomputes (ki/scanner/regime/events)
  --max-fixes N  Sicherheits-Cap (Default 50)

Usage:
    py scripts/check_db_completeness.py                          # read-only, alle Dimensionen
    py scripts/check_db_completeness.py --dim freshness,coverage # nur bestimmte
    py scripts/check_db_completeness.py --ticker AAPL            # nur ein Ticker
    py scripts/check_db_completeness.py --gap-years 5            # Gap-Scan-Tiefe
    py scripts/check_db_completeness.py --fix --mail             # fixen + Mail
    py scripts/check_db_completeness.py --fix --fix-derived --mail

Environment: SUPABASE_URL, SUPABASE_KEY, BREVO_API_KEY, ADMIN_EMAIL
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import pathlib
import statistics
import subprocess
import sys
import time
from datetime import datetime, date, timedelta, timezone

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from shared.symbols import (
    get_all_tickers,
    get_symbols_by_category,
    get_exchange_for_holidays,
)
from shared.exchange_holidays import is_trading_day
# Gap-Detection wiederverwenden (single source of truth)
from scripts.fix_missing_days import get_expected_trading_days, get_db_dates

TEMPLATE_DIR = pathlib.Path(_project_dir) / "scripts" / "templates"
TEMPLATE_NAME = "completeness_report.html.j2"
JSON_OUT = pathlib.Path(_project_dir) / "landing" / "data" / "db_completeness.json"

ALL_DIMS = ["freshness", "coverage", "gaps", "events"]

# Statische abgeleitete Tabellen: per-Ticker Zeilenzahl gegen den MEDIAN aller
# Ticker (selbst-kalibrierend — kein fragiler hardcoded Soll). Ticker mit
# count < Median*RATIO gelten als unvollstaendig (gelb), count==0 als fehlend (rot).
COVERAGE_STATIC = ["seasonality", "tdom_stats", "tdoy_stats", "monthly_stats"]
INCOMPLETE_RATIO = 0.5
# "Latest-Snapshot"-Tabellen: 1 Zeile/Ticker am letzten Lauf-Datum.
COVERAGE_DAILY = {
    "ki_scores": "computed_date",
    "scanner_results": "scan_date",
    "regime_scores": "date",
}

EQUITY_CATEGORIES = ["US-Aktie", "EU-Aktie"]

_PRIO = {"green": 0, "yellow": 1, "red": 2}


# ───────────────────────── DB-Helfer (read-only) ─────────────────────────

_client = None


def _c():
    global _client
    if _client is None:
        from shared.supabase_client import get_client
        _client = get_client()
    return _client


def _count(table: str, ticker: str | None = None, null_col: str | None = None) -> int:
    """Exakte Zeilenzahl (count=exact, kein Body) — optional je Ticker / NULL-Feld."""
    q = _c().table(table).select("ticker", count="exact")
    if ticker is not None:
        q = q.eq("ticker", ticker)
    if null_col is not None:
        q = q.is_(null_col, "null")
    r = q.limit(1).execute()
    return r.count or 0


def _max_value(table: str, col: str, ticker: str | None = None) -> str | None:
    q = _c().table(table).select(col)
    if ticker is not None:
        q = q.eq("ticker", ticker)  # nutzt (ticker,col)-Index → kein Full-Scan
    r = q.order(col, desc=True).limit(1).execute()
    return r.data[0][col] if r.data else None


def _tickers_since(table: str, col: str, since: str) -> set[str]:
    """Alle Ticker mit einer Zeile ab `since` (paginiert)."""
    out: set[str] = set()
    offset = 0
    while True:
        r = (_c().table(table).select("ticker").gte(col, since)
             .range(offset, offset + 999).execute())
        if not r.data:
            break
        out.update(row["ticker"] for row in r.data)
        if len(r.data) < 1000:
            break
        offset += 1000
    return out


def _tickers_with_any_row(table: str) -> set[str]:
    """Distinct-Ticker einer (kleinen) Tabelle via Paginierung."""
    out: set[str] = set()
    offset = 0
    while True:
        r = _c().table(table).select("ticker").range(offset, offset + 999).execute()
        if not r.data:
            break
        out.update(row["ticker"] for row in r.data)
        if len(r.data) < 1000:
            break
        offset += 1000
    return out


# ───────────────────────── Datums-Logik ─────────────────────────

def _last_trading_day(exchange: str, ref: date) -> date:
    d = ref
    for _ in range(15):
        if is_trading_day(d, exchange):
            return d
        d -= timedelta(days=1)
    return ref


def _trading_days_behind(have: date, exchange: str, ref: date) -> int:
    """Anzahl Handelstage, die `have` hinter dem letzten HT bis `ref` liegt."""
    probe = _last_trading_day(exchange, ref)
    behind = 0
    guard = 0
    while probe > have and guard < 4000:
        behind += 1
        probe -= timedelta(days=1)
        while not is_trading_day(probe, exchange):
            probe -= timedelta(days=1)
        guard += 1
    return behind


def _parse_d(s: str) -> date:
    return datetime.strptime(s[:10], "%Y-%m-%d").date()


# ───────────────────────── Dimensionen ─────────────────────────

def dim_freshness(ctx: dict) -> dict:
    """max(date) je Tabelle vs. letztem Handelstag."""
    us_ex = get_exchange_for_holidays("SPY")
    today = ctx["today"]
    checks = []
    status = "green"

    def add(name, st, detail, value):
        nonlocal status
        checks.append({"name": name, "status": st, "detail": detail, "value": value})
        if _PRIO[st] > _PRIO[status]:
            status = st

    # (table, col, kind, threshold)
    specs = [
        ("prices", "date", "workday", 1),
        ("ki_scores", "computed_date", "workday", 1),
        ("regime_scores", "date", "workday", 1),
        ("spot_vol_beta", "event_date", "workday", 1),
        ("scanner_results", "scan_date", "calday", 8),
        ("polymarket_prices", "ts", "calday", 2),
        ("earnings_events", "report_date", "info", None),
        ("dividend_events", "ex_date", "info", None),
    ]
    for table, col, kind, thr in specs:
        try:
            # prices ist riesig → über liquiden Proxy SPY (Index-Lookup) statt Full-Scan
            mx = _max_value(table, col, ticker="SPY" if table == "prices" else None)
            if not mx:
                add(table, "red", "Tabelle leer", "—")
                continue
            mxd = _parse_d(mx)
            if kind == "workday":
                behind = _trading_days_behind(mxd, us_ex, today)
                if behind <= 0:
                    add(table, "green", f"Aktuell bis {mxd}", str(mxd))
                elif behind <= thr:
                    add(table, "yellow", f"{mxd} ({behind} HT hinterher)", str(mxd))
                else:
                    add(table, "red", f"{mxd} ({behind} HT hinterher)", str(mxd))
            elif kind == "calday":
                age = (today - mxd).days
                if age <= thr:
                    add(table, "green", f"Letzter Eintrag: {mxd} ({age}d)", str(mxd))
                else:
                    add(table, "red", f"{mxd} ({age}d alt, erwartet ≤{thr}d)", str(mxd))
            else:  # info — Forward-Kalender, nur melden
                add(table, "green", f"Jüngstes Datum: {mxd}", str(mxd))
        except Exception as e:
            add(table, "red", f"Query-Fehler: {str(e)[:80]}", "ERR")

    return {"title": "Freshness", "status": status, "checks": checks}


def dim_coverage(ctx: dict) -> dict:
    """Ticker-Abdeckung je abgeleiteter Tabelle + Zeilenzahl vs. Soll."""
    universe = set(ctx["tickers"])
    checks = []
    status = "green"
    findings = ctx["findings"]

    def add(name, st, detail):
        nonlocal status
        checks.append({"name": name, "status": st, "detail": detail, "value": ""})
        if _PRIO[st] > _PRIO[status]:
            status = st

    # prices: Ticker, die gar nicht vorhanden sind
    try:
        missing_prices = []
        for t in sorted(universe):
            if _count("prices", ticker=t) == 0:
                missing_prices.append(t)
        findings["missing_prices"] = missing_prices
        if missing_prices:
            add("prices", "red",
                f"{len(missing_prices)} Ticker fehlen komplett: {', '.join(missing_prices[:8])}"
                + ("…" if len(missing_prices) > 8 else ""))
        else:
            add("prices", "green", f"alle {len(universe)} Ticker vorhanden")
    except Exception as e:
        add("prices", "red", f"Fehler: {str(e)[:80]}")

    # Latest-Snapshot-Tabellen: hat jeder Ticker eine Zeile im jüngsten Fenster?
    # (NICHT nur am Max-Datum — das kann partiell/in-progress sein.) Adaptiv:
    # sehr niedrige Abdeckung = Subset/Legacy-Tabelle (nur informativ, KEIN Auto-Fix).
    n = len(universe)
    for table, col in COVERAGE_DAILY.items():
        try:
            mx = _max_value(table, col)
            if not mx:
                add(table, "yellow", "Tabelle leer / nicht befüllt — übersprungen")
                continue
            since = (_parse_d(mx) - timedelta(days=5)).strftime("%Y-%m-%d")
            present = _tickers_since(table, col, since)
            covered = present & set(universe)
            missing = sorted(set(universe) - present)
            ratio = len(covered) / n if n else 0
            if ratio < 0.2:
                # Klar kein Full-Universe-Daily (Subset/Legacy) → nicht auto-fixen.
                add(table, "yellow",
                    f"nur {len(covered)}/{n} Ticker aktuell (seit {since}) — "
                    f"Subset/Legacy, kein Auto-Fix")
            elif not missing:
                add(table, "green", f"alle {n} Ticker aktuell (seit {since})")
                findings.setdefault("missing_derived", {})[table] = []
            else:
                findings.setdefault("missing_derived", {})[table] = missing
                st = "red" if len(missing) > n * 0.1 else "yellow"
                add(table, st,
                    f"{len(missing)} ohne Eintrag seit {since}: {', '.join(missing[:8])}"
                    + ("…" if len(missing) > 8 else ""))
        except Exception as e:
            add(table, "red", f"Fehler: {str(e)[:80]}")

    # Statische Tabellen: per-Ticker count vs. relativem Median (selbst-kalibrierend).
    for table in COVERAGE_STATIC:
        try:
            counts = {t: _count(table, ticker=t) for t in sorted(universe)}
            present = [n for n in counts.values() if n > 0]
            if not present:
                add(table, "yellow", "Tabelle leer / nicht befüllt — übersprungen")
                continue
            med = statistics.median(present)
            thr = med * INCOMPLETE_RATIO
            missing = [t for t, n in counts.items() if n == 0]
            incomplete = [(t, n) for t, n in counts.items() if 0 < n < thr]
            findings.setdefault("missing_derived", {})[table] = missing
            if table in ("tdom_stats", "tdoy_stats"):
                findings.setdefault("incomplete_tdomy", {})[table] = [t for t, _ in incomplete]
            if missing:
                add(table, "red",
                    f"{len(missing)} fehlen komplett, {len(incomplete)} unvollständig "
                    f"(Median {med:.0f})")
            elif incomplete:
                add(table, "yellow",
                    f"{len(incomplete)} unvollständig (<{thr:.0f}, Median {med:.0f}): "
                    + ", ".join(f"{t}:{n}" for t, n in incomplete[:6])
                    + ("…" if len(incomplete) > 6 else ""))
            else:
                add(table, "green", f"alle {len(universe)} Ticker ~vollständig (Median {med:.0f})")
        except Exception as e:
            add(table, "red", f"Fehler: {str(e)[:80]}")

    return {"title": "Coverage", "status": status, "checks": checks}


def dim_gaps(ctx: dict) -> dict:
    """Fehlende Handelstage in prices (boersenspezifisch) + NULL-Felder."""
    tickers = ctx["tickers"]
    gap_years = ctx["gap_years"]
    today = ctx["today"]
    findings = ctx["findings"]
    checks = []
    status = "green"

    def add(name, st, detail):
        nonlocal status
        checks.append({"name": name, "status": st, "detail": detail, "value": ""})
        if _PRIO[st] > _PRIO[status]:
            status = st

    if gap_years and gap_years > 0:
        win_start = date(today.year - (gap_years - 1), 1, 1)
    else:
        win_start = date(1900, 1, 1)  # volle Historie ab db_min
    client = _c()

    price_gaps: dict[str, int] = {}
    total_missing = 0
    for i, t in enumerate(tickers):
        try:
            exchange = get_exchange_for_holidays(t)
            db_dates = get_db_dates(client, t, win_start, today)
            if len(db_dates) < 5:
                continue  # zu wenig/keine Daten — von coverage erfasst
            db_min = _parse_d(min(db_dates))
            db_max = _parse_d(max(db_dates))
            rstart = max(win_start, db_min)
            rend = min(today, db_max)
            expected = get_expected_trading_days(exchange, rstart, rend)
            missing = [d for d in expected if d.strftime("%Y-%m-%d") not in db_dates]
            if missing:
                price_gaps[t] = len(missing)
                total_missing += len(missing)
        except Exception:
            pass
        if (i + 1) % 40 == 0:
            gc.collect()

    findings["price_gaps"] = price_gaps
    if not price_gaps:
        add("prices: Datumslücken", "green",
            f"keine Lücken (Fenster {win_start.year}–{today.year})")
    else:
        worst = sorted(price_gaps.items(), key=lambda x: -x[1])[:6]
        st = "red" if total_missing > 50 else "yellow"
        add("prices: Datumslücken", st,
            f"{len(price_gaps)} Ticker, {total_missing} fehlende HT gesamt — "
            + ", ".join(f"{t}:{n}" for t, n in worst))

    # NULL-Felder (fixbar via backfill_ohlc/backfill_log_return → max. gelb).
    # Im Single-Modus auf den Ticker scopen; Offender-Liste ist eine Stichprobe.
    single = ctx.get("single")
    for null_col, key in (("open", "null_ohlc"), ("log_return", "null_logret")):
        try:
            gtotal = _count("prices", ticker=single, null_col=null_col)
            if gtotal == 0:
                add(f"prices: NULL {null_col}", "green", "keine NULL-Werte")
                findings[key] = []
                continue
            q = client.table("prices").select("ticker").is_(null_col, "null")
            if single:
                q = q.eq("ticker", single)
            r = q.limit(3000).execute()
            offenders = sorted({row["ticker"] for row in (r.data or [])})
            findings[key] = offenders
            add(f"prices: NULL {null_col}", "yellow",
                f"{gtotal} Zeilen · Ticker (Stichprobe): "
                + ", ".join(offenders[:10]) + ("…" if len(offenders) >= 10 else ""))
        except Exception as e:
            add(f"prices: NULL {null_col}", "red", f"Fehler: {str(e)[:80]}")

    return {"title": "Gaps", "status": status, "checks": checks}


def dim_events(ctx: dict) -> dict:
    """earnings_events/dividend_events fuer Aktien-Ticker befuellt?"""
    findings = ctx["findings"]
    checks = []
    status = "green"

    def add(name, st, detail):
        nonlocal status
        checks.append({"name": name, "status": st, "detail": detail, "value": ""})
        if _PRIO[st] > _PRIO[status]:
            status = st

    equities = set()
    for cat in EQUITY_CATEGORIES:
        equities.update(get_symbols_by_category(cat).keys())
    # Auf Wunsch-Einzelticker einschraenken
    if ctx.get("single"):
        equities &= {ctx["single"]}

    for table, key in (("earnings_events", "earnings"), ("dividend_events", "dividends")):
        try:
            have = _tickers_with_any_row(table)
            missing = sorted(equities - have)
            findings.setdefault("missing_events", {})[key] = missing
            if not equities:
                add(table, "green", "keine Aktien-Ticker im Scope")
            elif not missing:
                add(table, "green", f"alle {len(equities)} Aktien-Ticker haben Einträge")
            else:
                st = "red" if len(missing) > len(equities) * 0.5 else "yellow"
                add(table, st,
                    f"{len(missing)}/{len(equities)} Aktien ohne Einträge: "
                    + ", ".join(missing[:8]) + ("…" if len(missing) > 8 else ""))
        except Exception as e:
            add(table, "red", f"Fehler: {str(e)[:80]}")

    return {"title": "Events", "status": status, "checks": checks}


# ───────────────────────── Auto-Backfill (Dispatch) ─────────────────────────

def _run_script(script: str, args: list[str], timeout: int = 1800) -> bool:
    cmd = [sys.executable, os.path.join(_project_dir, "scripts", script)] + args
    print(f"    → {script} {' '.join(args)}")
    try:
        r = subprocess.run(cmd, cwd=_project_dir, timeout=timeout,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"      ⚠ rc={r.returncode}: {(r.stderr or r.stdout)[-200:]}")
        return r.returncode == 0
    except Exception as e:
        print(f"      ⚠ {e}")
        return False


def run_fixes(ctx: dict) -> tuple[int, list[str], list[str]]:
    """Schliesst gefundene Luecken via bestehende Skripte. Gibt
    (fixed_count, ausgefuehrte_befehle, empfohlene_befehle) zurueck."""
    f = ctx["findings"]
    do_fix = ctx["fix"]
    do_derived = ctx["fix_derived"]
    cap = ctx["max_fixes"]
    fixed = 0
    done: list[str] = []
    recommend: list[str] = []

    def cmd_str(script, args):
        return f"python scripts/{script} {' '.join(args)}"

    def exec_or_recommend(script, args, derived=False, run=True):
        nonlocal fixed
        c = cmd_str(script, args)
        gate = (do_derived if derived else do_fix)
        if run and gate and fixed < cap:
            if _run_script(script, args):
                fixed += 1
            done.append(c)
        else:
            recommend.append(c)

    # 1) Ticker fehlt komplett in prices → Voll-Backfill (+ tdoy danach)
    for t in f.get("missing_prices", []):
        exec_or_recommend("backfill_new_ticker.py", [t])
        exec_or_recommend("backfill_tdoy.py", ["--ticker", t])

    # 2) Datumsluecken → fix_missing_days (+ tdoy)
    for t in sorted(f.get("price_gaps", {}), key=lambda x: -f["price_gaps"][x]):
        exec_or_recommend("fix_missing_days.py", ["--ticker", t])
        exec_or_recommend("backfill_tdoy.py", ["--ticker", t])

    # 3) NULL OHLC / log_return → globale Backfills (idempotent, einmal)
    if f.get("null_ohlc"):
        exec_or_recommend("backfill_ohlc.py", [])
    if f.get("null_logret"):
        exec_or_recommend("backfill_log_return.py", [])

    # 4) Unvollstaendige tdom/tdoy → backfill_tdoy je Ticker
    for table, tlist in f.get("incomplete_tdomy", {}).items():
        for t in tlist:
            exec_or_recommend("backfill_tdoy.py", ["--ticker", t])

    # 5) Fehlende abgeleitete (teuer) → --fix-derived
    md = f.get("missing_derived", {})
    for t in md.get("regime_scores", []):
        exec_or_recommend("compute_regime_scores.py", ["--ticker", t], derived=True)
    ki_or_scan = sorted(set(md.get("ki_scores", [])) | set(md.get("scanner_results", [])))
    for t in ki_or_scan:
        exec_or_recommend("full_scanner_run.py", ["--only", t], derived=True)

    # 6) Event-Luecken (teuer) → fetch_event_data
    me = f.get("missing_events", {})
    if me.get("earnings"):
        exec_or_recommend("fetch_event_data.py",
                          ["--mode", "earnings", "--tickers", *me["earnings"]], derived=True)
    if me.get("dividends"):
        exec_or_recommend("fetch_event_data.py",
                          ["--mode", "dividends", "--tickers", *me["dividends"]], derived=True)

    # seasonality / monthly_stats haben kein Per-Ticker-Fix-Skript → nur Hinweis
    for table in ("seasonality", "monthly_stats"):
        miss = md.get(table, [])
        if miss:
            recommend.append(
                f"# {table}: {len(miss)} Ticker fehlen → naechster Nightly-Refresh (Phase B) fuellt nach")

    return fixed, done, recommend


# ───────────────────────── Report / Mail / Persistenz ─────────────────────────

def render_email(ctx: dict) -> tuple[str, str]:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True, lstrip_blocks=True,
    )
    tpl = env.get_template(TEMPLATE_NAME)
    html = tpl.render(**ctx["report"])
    icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(ctx["report"]["overall_status"], "⚪")
    subject = f"{icon} SeasonAlpha DB-Vollständigkeit — {ctx['report']['report_date']}"
    return subject, html


def write_json(report: dict):
    try:
        JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(JSON_OUT, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, separators=(",", ":"))
        print(f"[json] {JSON_OUT}")
    except Exception as e:
        print(f"[json] Schreibfehler: {e}")


def write_refresh_log(ctx: dict, report: dict, elapsed: float):
    try:
        f = ctx["findings"]
        problem = (len(f.get("missing_prices", []))
                   + len(f.get("price_gaps", {}))
                   + sum(len(v) for v in f.get("missing_derived", {}).values())
                   + sum(len(v) for v in f.get("missing_events", {}).values()))
        _c().table("refresh_log").insert({
            "run_date": ctx["today"].isoformat(),
            "run_type": "completeness",
            "tickers_total": len(ctx["tickers"]),
            "tickers_success": max(0, len(ctx["tickers"]) - len(f.get("missing_prices", []))),
            "tickers_missing": problem,
            "missing_details": {
                "missing_prices": f.get("missing_prices", []),
                "price_gaps": f.get("price_gaps", {}),
                "missing_derived": f.get("missing_derived", {}),
                "missing_events": f.get("missing_events", {}),
            },
            "auto_fixed": ctx.get("fixed_count", 0),
            "duration_seconds": round(elapsed, 1),
            "errors": [c["detail"] for s in report["sections"]
                       for c in s["checks"] if c["status"] == "red"][:20],
        }).execute()
        print("[refresh_log] Eintrag run_type='completeness' geschrieben")
    except Exception as e:
        print(f"[refresh_log] Schreibfehler: {e}")


# ───────────────────────── Main ─────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="SeasonAlpha DB-Vollständigkeits-Audit")
    ap.add_argument("--dim", default=",".join(ALL_DIMS),
                    help="Komma-Liste: freshness,coverage,gaps,events (Default alle)")
    ap.add_argument("--ticker", help="Nur ein Ticker prüfen")
    ap.add_argument("--gap-years", type=int, default=2,
                    help="Tiefe des Datumslücken-Scans in Jahren (0=volle Historie)")
    ap.add_argument("--fix", action="store_true", help="Daten-Layer-Lücken auto-backfillen")
    ap.add_argument("--fix-derived", action="store_true",
                    help="Zusätzlich teure Recomputes (ki/scanner/regime/events)")
    ap.add_argument("--max-fixes", type=int, default=50, help="Cap für Auto-Fixes")
    ap.add_argument("--mail", action="store_true", help="Brevo-Report an ADMIN_EMAIL")
    ap.add_argument("--to", help="Mail-Empfänger überschreiben")
    ap.add_argument("--no-json", action="store_true", help="Kein JSON schreiben")
    args = ap.parse_args()

    dims = [d.strip() for d in args.dim.split(",") if d.strip() in ALL_DIMS]
    now_utc = datetime.now(timezone.utc)
    universe = [args.ticker] if args.ticker else get_all_tickers()

    ctx = {
        "today": now_utc.date(),
        "tickers": universe,
        "single": args.ticker,
        "gap_years": args.gap_years,
        "fix": args.fix,
        "fix_derived": args.fix_derived,
        "max_fixes": args.max_fixes,
        "findings": {},
    }

    print("=" * 72)
    print(f"  SeasonAlpha DB-Vollständigkeits-Audit — {len(universe)} Ticker")
    print(f"  Dimensionen: {', '.join(dims)} · Gap-Fenster: {args.gap_years}J"
          + (" · FIX" if args.fix else "") + (" · FIX-DERIVED" if args.fix_derived else ""))
    print("=" * 72)
    t0 = time.time()

    runners = {"freshness": dim_freshness, "coverage": dim_coverage,
               "gaps": dim_gaps, "events": dim_events}
    sections = []
    overall = "green"
    for d in dims:
        print(f"\n── {d} ──")
        sec = runners[d](ctx)
        sections.append(sec)
        if _PRIO[sec["status"]] > _PRIO[overall]:
            overall = sec["status"]
        for c in sec["checks"]:
            print(f"  [{c['status'].upper():6s}] {c['name']:28s} {c['detail']}")

    # Auto-Fix / Empfehlungen
    fixed, done, recommend = run_fixes(ctx)
    ctx["fixed_count"] = fixed
    if done:
        print(f"\n[fix] {fixed} Auto-Fixes ausgeführt")
    if recommend:
        print(f"\n[fix] {len(recommend)} empfohlene Befehle (ohne --fix/--fix-derived):")
        for c in recommend[:30]:
            print(f"    {c}")

    elapsed = time.time() - t0
    report = {
        "overall_status": overall,
        "report_time": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "report_date": ctx["today"].strftime("%Y-%m-%d"),
        "sections": sections,
        "fix_done": done,
        "fix_recommend": recommend,
        "fixed_count": fixed,
        "duration_seconds": round(elapsed, 1),
    }
    ctx["report"] = report

    print(f"\n{'=' * 72}")
    print(f"  Gesamt: {overall.upper()} · {elapsed:.0f}s · {fixed} gefixt · "
          f"{len(recommend)} empfohlen")
    print("=" * 72)

    if not args.no_json:
        write_json(report)
    write_refresh_log(ctx, report, elapsed)

    if args.mail:
        try:
            subject, html = render_email(ctx)
            recipient = args.to or os.environ.get("ADMIN_EMAIL", "heiko.seibel@gmail.com")
            from shared.email_brevo import send_html
            ok = send_html(recipient, subject, html)
            print(f"[mail] an {recipient}: {'OK' if ok else 'FEHLER'}")
        except Exception as e:
            print(f"[mail] Fehler: {e}")

    return 0 if overall != "red" else 1


if __name__ == "__main__":
    sys.exit(main())
