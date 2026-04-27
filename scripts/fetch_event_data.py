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

import sys, os, pathlib, argparse, time, json, requests
from datetime import datetime, timezone

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.env_loader import load_env
load_env()

from shared.symbols import SYMBOLS

YAHOO_URL = (
    "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    "?range=25y&interval=1d&events={events}&includeAdjustedClose=false"
)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")  # service-role key


# ── Yahoo Finance Fetch ──────────────────────────────────────────────────────

def _yahoo_events(ticker: str, events: str) -> dict:
    url = YAHOO_URL.format(ticker=ticker, events=events)
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    data = r.json()
    result = (data.get("chart") or {}).get("result") or []
    if not result:
        return {}
    return ((result[0].get("events") or {}).get(events)) or {}


def fetch_dividends(ticker: str) -> list[dict]:
    raw = _yahoo_events(ticker, "dividends")
    rows = []
    for v in raw.values():
        dt = datetime.fromtimestamp(v["date"], tz=timezone.utc).date().isoformat()
        rows.append({
            "ticker":  ticker,
            "ex_date": dt,
            "amount":  v.get("amount"),
        })
    return sorted(rows, key=lambda r: r["ex_date"])


def fetch_earnings(ticker: str) -> list[dict]:
    raw = _yahoo_events(ticker, "earnings")
    rows = []
    for v in raw.values():
        dt = datetime.fromtimestamp(v["date"], tz=timezone.utc).date().isoformat()
        eps_a = v.get("epsActual")
        eps_e = v.get("epsEstimate")
        surprise = None
        if eps_a is not None and eps_e is not None and eps_e != 0:
            surprise = round((eps_a - eps_e) / abs(eps_e) * 100, 4)
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
    # In Batches von 500 senden
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

        time.sleep(0.35)  # Rate-Limiting Yahoo Finance

    print(f"\nErgebnis: {ok} OK / {err} Fehler")
    print(f"  Dividenden:  {div_total} Einträge")
    print(f"  Earnings:    {earn_total} Einträge")


if __name__ == "__main__":
    main()
