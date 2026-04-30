"""
backfill_earnings_finnhub.py — Initial-Backfill der Earnings-Historie via Finnhub.

Hintergrund: Yahoo's quoteSummary?modules=earningsHistory liefert nur die
letzten 4 Quartale und ist auf US-Aktien fokussiert. Internationale Werte
(NESN.SW, MC.PA, AZN, RO.SW etc.) bekommen leere history zurück. Finnhub
hat ~10 Jahre Historie für US + EU + Asia in einem Endpoint.

Cron-Pipeline (fetch_event_data.py via event_data_daily.yml) bleibt parallel
aktiv für tägliche Frische — dieses Script läuft nur 1× zur Initial-Befüllung
oder gelegentlich als Backfill nach längerer Pause.

Aufruf:
  py scripts/backfill_earnings_finnhub.py                      # alle Ticker
  py scripts/backfill_earnings_finnhub.py --tickers AAPL MSFT  # einzelne
  py scripts/backfill_earnings_finnhub.py --dry-run            # ohne DB-Schreiben

Environment:
  FINNHUB_API_KEY  — Free-Tier reicht (60 calls/min)
  SUPABASE_URL     — Standard
  SUPABASE_KEY     — service-role
"""

import sys, os, pathlib, argparse, time, requests
from datetime import datetime

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from shared.env_loader import load_env
load_env()

from shared.symbols import SYMBOLS

FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

FINNHUB_URL = "https://finnhub.io/api/v1/stock/earnings"

# Tickers ohne Earnings rausfiltern (Indizes, Futures, Crypto, FX)
SKIP_PATTERNS = ("^", "=F", "-USD", "=X")


def _skip(ticker: str) -> bool:
    return any(p in ticker for p in SKIP_PATTERNS)


def fetch_finnhub_earnings(ticker: str, retries: int = 3) -> list[dict]:
    """Holt komplette Earnings-Historie. Free-Tier liefert ~10y."""
    params = {"symbol": ticker, "token": FINNHUB_KEY}
    for attempt in range(retries):
        try:
            r = requests.get(FINNHUB_URL, params=params, timeout=20)
        except requests.RequestException as exc:
            print(f"    [net] {ticker}: {exc}", flush=True)
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429:
            wait = 30 * (attempt + 1)
            print(f"    [rate-limit] warte {wait}s …", flush=True)
            time.sleep(wait)
            continue
        if r.status_code == 200:
            try:
                return r.json() or []
            except ValueError:
                return []
        if r.status_code in (401, 403):
            raise RuntimeError(f"Finnhub Auth-Fehler {r.status_code}: {r.text[:100]}")
        if r.status_code == 404:
            return []
        # andere 4xx/5xx: kurzer Backoff
        time.sleep(2)
    return []


def to_supabase_rows(ticker: str, raw: list[dict]) -> list[dict]:
    """Finnhub-Format → earnings_events-Schema."""
    rows = []
    for item in raw:
        period = item.get("period")  # ISO date string, z.B. "2025-09-30"
        if not period:
            continue
        try:
            datetime.strptime(period, "%Y-%m-%d")
        except ValueError:
            continue
        actual = item.get("actual")
        estimate = item.get("estimate")
        surprise_pct = item.get("surprisePercent")
        rows.append({
            "ticker":       ticker,
            "report_date":  period,
            "eps_actual":   actual,
            "eps_estimate": estimate,
            "surprise_pct": surprise_pct,
        })
    return sorted(rows, key=lambda r: r["report_date"])


def upsert(rows: list[dict]) -> None:
    if not rows or not SUPABASE_URL or not SUPABASE_KEY:
        return
    url = f"{SUPABASE_URL}/rest/v1/earnings_events"
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
            raise RuntimeError(f"Supabase upsert error {r.status_code}: {r.text[:200]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Earnings-Backfill via Finnhub")
    parser.add_argument("--tickers", nargs="*", help="Bestimmte Ticker (Standard: alle aus symbols.py)")
    parser.add_argument("--dry-run", action="store_true", help="Kein DB-Schreiben")
    args = parser.parse_args()

    if not FINNHUB_KEY:
        print("ERROR: FINNHUB_API_KEY nicht gesetzt (.env oder Env-Var)", file=sys.stderr)
        sys.exit(1)

    candidates = args.tickers if args.tickers else list(SYMBOLS.keys())
    tickers = [t for t in candidates if not _skip(t)]
    skipped = len(candidates) - len(tickers)
    print(f"backfill_earnings_finnhub.py — {len(tickers)} Ticker (skipped: {skipped} non-equity), dry-run={args.dry_run}")

    t_start = time.time()
    ok = err = total_rows = 0

    for i, ticker in enumerate(tickers, 1):
        try:
            raw = fetch_finnhub_earnings(ticker)
            rows = to_supabase_rows(ticker, raw)
            if not args.dry_run:
                upsert(rows)
            total_rows += len(rows)
            n = len(rows)
            label = f"{n} earn" if n else "leer"
            print(f"  [{i:3d}/{len(tickers)}] OK  {ticker}: {label}")
            ok += 1
        except Exception as exc:
            print(f"  [{i:3d}/{len(tickers)}] ERR {ticker}: {exc}", file=sys.stderr)
            err += 1

        time.sleep(1.1)  # 60 calls/min = 1 call/s; etwas Puffer

    elapsed = time.time() - t_start
    print(f"\nErgebnis: {ok} OK / {err} Fehler in {elapsed:.0f}s")
    print(f"  Earnings gesamt:  {total_rows} Einträge")


if __name__ == "__main__":
    main()
