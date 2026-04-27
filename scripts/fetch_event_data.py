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

YAHOO_CHART_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    "?range=25y&interval=1d&events={events}&includeAdjustedClose=false"
)
YAHOO_SUMMARY_URL = (
    "https://query1.finance.yahoo.com/v11/finance/quoteSummary/{ticker}"
    "?modules=earningsHistory"
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # service-role key

# ── Yahoo Finance Session ────────────────────────────────────────────────────

def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.4.1 Safari/605.1.15"
        ),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    })
    # Establish session cookie
    try:
        s.get("https://finance.yahoo.com/", timeout=15)
    except Exception:
        pass
    return s


_SESSION: requests.Session | None = None


def _get_session() -> requests.Session:
    global _SESSION
    if _SESSION is None:
        _SESSION = _make_session()
    return _SESSION


def _get_json(url: str, retries: int = 3) -> dict:
    s = _get_session()
    for attempt in range(retries):
        r = s.get(url, timeout=25)
        if r.status_code == 429:
            wait = 30 * (attempt + 1)
            print(f"    [rate-limit] warte {wait}s …", flush=True)
            time.sleep(wait)
            continue
        if r.status_code == 404:
            return {}
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Nach {retries} Versuchen noch immer 429 für {url}")


# ── Dividenden ───────────────────────────────────────────────────────────────

def fetch_dividends(ticker: str) -> list[dict]:
    url = YAHOO_CHART_URL.format(ticker=ticker, events="dividends")
    data = _get_json(url)
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
    url = YAHOO_SUMMARY_URL.format(ticker=ticker)
    data = _get_json(url)
    if not data:
        return []
    results = ((data.get("quoteSummary") or {}).get("result")) or []
    if not results:
        return []
    history = (results[0].get("earningsHistory") or {}).get("history") or []
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

    print(f"\nErgebnis: {ok} OK / {err} Fehler")
    print(f"  Dividenden:  {div_total} Einträge")
    print(f"  Earnings:    {earn_total} Einträge")


if __name__ == "__main__":
    main()
