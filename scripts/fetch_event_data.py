"""
fetch_event_data.py — Dividenden- und Earnings-Daten von Yahoo Finance laden
und in Supabase (dividend_events, earnings_events) upserten.

Aufruf:
  py scripts/fetch_event_data.py                      # alle Ticker aus symbols.py
  py scripts/fetch_event_data.py --tickers SPY AAPL   # bestimmte Ticker
  py scripts/fetch_event_data.py --dry-run            # ohne DB-Schreiben
  py scripts/fetch_event_data.py --mode dividends     # nur Dividenden
  py scripts/fetch_event_data.py --mode earnings      # nur Earnings
"""

import sys, os, pathlib, argparse, time, requests
from datetime import datetime, timezone

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.env_loader import load_env
load_env()

from shared.symbols import SYMBOLS

YAHOO_CHART_HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]
YAHOO_CHART_PATH = (
    "/v8/finance/chart/{ticker}"
    "?range=25y&interval=1d&events={events}&includeAdjustedClose=false"
)
YAHOO_SUMMARY_PATH = (
    "/v10/finance/quoteSummary/{ticker}"
    "?modules=earningsHistory,earnings"
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # service-role key

# ── Yahoo Finance HTTP ───────────────────────────────────────────────────────
# Pattern aus shared/yahoo_downloader.py: simple Browser-UA, KEIN
# Pre-GET auf finance.yahoo.com (das triggert sonst sofort 429-Rate-Limit auf
# GitHub-Actions-IPs). Pro Aufruf frischer Request, query1→query2-Fallback.

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Crumb-Authentication für quoteSummary ──
# v11/quoteSummary erfordert seit ~2023 einen crumb-Token. Algorithmus:
#   1. GET https://fc.yahoo.com  → empfängt A3-Cookie
#   2. GET https://query2.finance.yahoo.com/v1/test/getcrumb mit Cookie → crumb-String
#   3. Alle nachfolgenden quoteSummary-Calls mit &crumb=… und der Cookie-Session
# Cache: einmal pro Process.

_CRUMB_SESSION: requests.Session | None = None
_CRUMB: str | None = None


def _get_crumb() -> tuple[requests.Session, str] | tuple[None, None]:
    global _CRUMB_SESSION, _CRUMB
    if _CRUMB_SESSION is not None and _CRUMB is not None:
        return _CRUMB_SESSION, _CRUMB
    s = requests.Session()
    s.headers.update(_HEADERS)
    try:
        # Schritt 1: Cookie-Set über fc.yahoo.com (kann redirecten oder 404 — Cookie wird trotzdem gesetzt)
        s.get("https://fc.yahoo.com/", timeout=15, allow_redirects=True)
        # Schritt 2: crumb anfragen
        r = s.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=15)
        if r.status_code == 200 and r.text and len(r.text) < 50:
            _CRUMB_SESSION = s
            _CRUMB = r.text.strip()
            print(f"    [crumb] OK crumb={_CRUMB[:8]}… cookies={len(s.cookies)}", flush=True)
            return s, _CRUMB
        print(f"    [crumb] FAIL status={r.status_code} body='{r.text[:80]}'", flush=True)
    except requests.RequestException as exc:
        print(f"    [crumb] EXC {exc}", flush=True)
    return None, None


def _get_json(path: str, retries: int = 3, use_crumb: bool = False) -> dict:
    """Holt JSON von Yahoo. Mit use_crumb=True für quoteSummary-Endpoints."""
    session: requests.Session | None = None
    full_path = path
    if use_crumb:
        session, crumb = _get_crumb()
        if not crumb:
            print(f"    [crumb] kein crumb verfügbar — überspringe {path}", flush=True)
            return {}
        sep = "&" if "?" in path else "?"
        full_path = f"{path}{sep}crumb={crumb}"

    last_status = None
    for attempt in range(retries):
        for host in YAHOO_CHART_HOSTS:
            url = f"https://{host}{full_path}"
            try:
                if session is not None:
                    r = session.get(url, timeout=25, allow_redirects=True)
                else:
                    r = requests.get(url, headers=_HEADERS, timeout=25, allow_redirects=True)
            except requests.RequestException as exc:
                last_status = f"net-error: {exc}"
                continue
            last_status = r.status_code
            if r.status_code == 200:
                try:
                    return r.json()
                except ValueError:
                    last_status = "invalid-json"
                    continue
            if r.status_code == 404:
                return {}
            if r.status_code == 429:
                continue
        if attempt < retries - 1:
            wait = 20 * (attempt + 1)
            print(f"    [rate-limit] warte {wait}s …", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Nach {retries} Versuchen Status={last_status} für {full_path}")


# ── Dividenden ───────────────────────────────────────────────────────────────

def fetch_dividends(ticker: str) -> list[dict]:
    path = YAHOO_CHART_PATH.format(ticker=ticker, events="dividends")
    data = _get_json(path)
    result = (data.get("chart") or {}).get("result") or []
    if not result:
        return []
    raw = ((result[0].get("events") or {}).get("dividends")) or {}
    rows = []
    for v in raw.values():
        dt = datetime.fromtimestamp(v["date"], tz=timezone.utc).date().isoformat()
        rows.append({"ticker": ticker, "ex_date": dt, "amount": v.get("amount")})
    return sorted(rows, key=lambda r: r["ex_date"])


# ── Earnings ─────────────────────────────────────────────────────────────────

def fetch_earnings(ticker: str) -> list[dict]:
    # earningsHistory liefert max 4 Quartale. Indizes/Futures/Crypto haben
    # keine Earnings — silent return [] ist erwartet, kein Logging dafür.
    path = YAHOO_SUMMARY_PATH.format(ticker=ticker)
    data = _get_json(path, use_crumb=True)
    if not data:
        return []
    qs = data.get("quoteSummary") or {}
    err = qs.get("error")
    if err:
        print(f"    [earn-err] {ticker}: {err}", flush=True)
    results = qs.get("result") or []
    if not results:
        return []
    res0 = results[0] or {}
    history = (res0.get("earningsHistory") or {}).get("history") or []
    rows = []
    for item in history:
        quarter_raw = (item.get("quarter") or {}).get("raw")
        if not quarter_raw:
            continue
        dt = datetime.fromtimestamp(quarter_raw, tz=timezone.utc).date().isoformat()
        eps_a = (item.get("epsActual") or {}).get("raw")
        eps_e = (item.get("epsEstimate") or {}).get("raw")
        surprise_raw = (item.get("surprisePercent") or {}).get("raw")
        # surprisePercent.raw ist z.B. 0.191 = 19.1 %
        surprise = round(surprise_raw * 100, 4) if surprise_raw is not None else None
        rows.append({
            "ticker":       ticker,
            "report_date":  dt,
            "eps_actual":   eps_a,
            "eps_estimate": eps_e,
            "surprise_pct": surprise,
        })
    return sorted(rows, key=lambda r: r["report_date"])


# ── Supabase Upsert ──────────────────────────────────────────────────────────

def upsert(table: str, rows: list[dict]) -> None:
    if not rows or not SUPABASE_URL or not SUPABASE_KEY:
        return
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates,return=minimal",
    }
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        r = requests.post(url, headers=headers, json=batch, timeout=30)
        if not r.ok:
            raise RuntimeError(f"Supabase {table} upsert error {r.status_code}: {r.text[:200]}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Event-Daten (Dividenden/Earnings) nach Supabase")
    parser.add_argument("--tickers", nargs="*", help="Bestimmte Ticker (Standard: alle aus symbols.py)")
    parser.add_argument("--dry-run", action="store_true", help="Kein DB-Schreiben")
    parser.add_argument("--mode", choices=["both", "dividends", "earnings"], default="both")
    args = parser.parse_args()

    tickers = args.tickers if args.tickers else list(SYMBOLS.keys())
    print(f"fetch_event_data.py — {len(tickers)} Ticker, mode={args.mode}, dry-run={args.dry_run}")

    t_start = time.time()
    ok = err = div_total = earn_total = 0

    for ticker in tickers:
        try:
            div_rows  = []
            earn_rows = []

            if args.mode in ("both", "dividends"):
                div_rows = fetch_dividends(ticker)
                if not args.dry_run:
                    upsert("dividend_events", div_rows)
                div_total += len(div_rows)

            if args.mode in ("both", "earnings"):
                earn_rows = fetch_earnings(ticker)
                if not args.dry_run:
                    upsert("earnings_events", earn_rows)
                earn_total += len(earn_rows)

            label = []
            if div_rows:  label.append(f"{len(div_rows)} div")
            if earn_rows: label.append(f"{len(earn_rows)} earn")
            if not label: label = ["keine Events"]
            print(f"  OK  {ticker}: {', '.join(label)}")
            ok += 1

        except Exception as exc:
            print(f"  ERR {ticker}: {exc}", file=sys.stderr)
            err += 1

        time.sleep(0.5)  # Rate-Limiting Yahoo Finance

    elapsed = time.time() - t_start
    print(f"\nErgebnis: {ok} OK / {err} Fehler")
    print(f"  Dividenden:  {div_total} Einträge")
    print(f"  Earnings:    {earn_total} Einträge")

    # ── refresh_log: Health-Monitoring ────────────────────────────────────
    # daily_health_check.py liest run_type='event_data' für Frische-Check.
    if not args.dry_run:
        try:
            import json as _json
            from datetime import datetime as _dt, timezone as _tz
            from shared.supabase_client import get_client
            get_client().table("refresh_log").insert({
                "run_date":         _dt.now(_tz.utc).strftime("%Y-%m-%d"),
                "run_type":         "event_data",
                "tickers_total":    len(tickers),
                "tickers_success":  ok,
                "tickers_missing":  err,
                "missing_details":  _json.dumps({"div_rows": div_total, "earn_rows": earn_total}),
                "auto_fixed":       0,
                "duration_seconds": round(elapsed, 1),
                "errors":           "[]",
            }).execute()
        except Exception as exc:
            print(f"[event-data] refresh_log insert failed: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
