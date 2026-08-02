"""
scripts/build_buyback_blackout.py — Panel B der /flows-Seite: Buyback-Blackout-Saisonkurve
==========================================================================================
~4-6 Wochen vor Earnings dürfen Firmen keine eigenen Aktien zurückkaufen (Blackout). Buybacks
sind ein struktureller Dauer-Bid; im Blackout fehlt er → der Markt ist dünner. Aggregiert über
das US-Kern-Universum entsteht eine Saison-Kurve des "fehlenden Bids" (Peaks am Anfang jeder
Earnings-Saison: Mitte Jan/Apr/Jul/Okt).

Aufwertung (Research-Spec 2026-08-02):
  * MARKTKAP-GEWICHTUNG (die von Bank-Desks geführte Kennzahl) via Yahoo v7-Quote + Crumb-Auth,
    plus gleichgewichtete Vergleichslinie (Konzentrations-Transparenz).
  * VOLL-KALENDERJAHR-Serie (Jan–Dez) statt ±90-Tage-Ausschnitt → Saison-Overlay.
  * Timing-Anker präziser: Blackout-START = Quartalsende−14T (exakt bekannt), ENDE = +ANNOUNCE_LAG+2T.
  * blackout_heavyweights (Top-Schwergewichte heute) + est. fehlender Tages-Bid ($).

DATENLAGE (ehrlich): `earnings_events` (Supabase) enthält nur VERGANGENE Quartals-Reports
(report_date = Fiskal-Quartalsende). Nächste Fenster aus Quartals-Kadenz (~91T) projiziert.
$-Zahlen sind extern zitierte/geschätzte Referenzen, NICHT aus unserer Pipeline. → Proxy, gelabelt.

Schreibt `landing/data/buyback_blackout.json` (Cache: landing/data/_mktcap_cache.json).
  PYTHONUTF8=1 py -3.14 scripts/build_buyback_blackout.py
"""
from __future__ import annotations
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

_DATA = _ROOT / "landing" / "data"
_MKTCAP_CACHE = _DATA / "_mktcap_cache.json"

QUARTER_DAYS = 91          # Quartals-Kadenz
ANNOUNCE_LAG = 30          # Tage von Fiskal-Quartalsende bis Ankündigung (typisch)
BLACKOUT_PRE = 14          # Blackout-START = Quartalsende − 14T (Standard-Definition, exakt bekannt)
BLACKOUT_POST = 2          # ENDE = Ankündigung(+ANNOUNCE_LAG) + 2T
ANNUAL_BUYBACK_USD = 1.0e12   # S&P-500-Rückkäufe ~1 Bio $/Jahr (S&P DJI, jährlich manuell pflegen)

_YHEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
}


def _load_env():
    envf = _ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


# ── marketCap-Snapshot (Yahoo v7-Quote + Crumb), täglich gecacht ────────────────
def _fetch_marketcaps(tickers: list[str], today: date) -> dict[str, float]:
    # Cache: einmal/Tag (mktcap driftet langsam)
    try:
        if _MKTCAP_CACHE.exists():
            c = json.loads(_MKTCAP_CACHE.read_text(encoding="utf-8"))
            if c.get("date") == today.isoformat() and c.get("caps"):
                return {k: float(v) for k, v in c["caps"].items()}
    except Exception:
        pass
    caps: dict[str, float] = {}
    try:
        s = requests.Session(); s.headers.update(_YHEADERS)
        s.get("https://fc.yahoo.com/", timeout=15, allow_redirects=True)
        cr = s.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=15)
        crumb = cr.text.strip() if cr.status_code == 200 and len(cr.text) < 50 else None
        if not crumb:
            print("    [crumb] kein crumb — marketCap-Fallback gleichgewichtet", flush=True)
            return {}
        for i in range(0, len(tickers), 50):
            batch = tickers[i:i + 50]
            for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
                try:
                    url = (f"https://{host}/v7/finance/quote"
                           f"?symbols={','.join(batch)}&crumb={crumb}")
                    r = s.get(url, timeout=25)
                    if r.status_code != 200:
                        continue
                    for q in (r.json().get("quoteResponse", {}).get("result", []) or []):
                        mc = q.get("marketCap")
                        if q.get("symbol") and mc:
                            caps[q["symbol"]] = float(mc)
                    break
                except (requests.RequestException, ValueError):
                    continue
    except requests.RequestException as exc:
        print(f"    [mktcap] EXC {exc}", flush=True)
    if caps:
        try:
            _MKTCAP_CACHE.write_text(json.dumps({"date": today.isoformat(), "caps": caps},
                                                ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
    print(f"    [mktcap] {len(caps)}/{len(tickers)} marketCaps geladen", flush=True)
    return caps


def _latest_report_per_us_ticker(sb) -> dict[str, date]:
    cutoff = (date.today() - timedelta(days=150)).isoformat()
    rows = (sb.table("earnings_events").select("ticker,report_date")
            .gte("report_date", cutoff).limit(5000).execute().data)
    latest: dict[str, date] = {}
    for r in rows:
        tk = r["ticker"]
        if "." in tk or tk.startswith("^") or "-" in tk or "=" in tk:
            continue
        try:
            d = date.fromisoformat(r["report_date"][:10])
        except (TypeError, ValueError):
            continue
        if tk not in latest or d > latest[tk]:
            latest[tk] = d
    return latest


def _windows_for_year(last_qend: date, y0: date, y1: date) -> list[tuple[date, date]]:
    """Blackout-Fenster [Quartalsende−14, Ankündigung+2] über [y0-40 .. y1+40]."""
    wins = []
    for k in range(-6, 7):
        qend = last_qend + timedelta(days=QUARTER_DAYS * k)
        if y0 - timedelta(days=40) <= qend <= y1 + timedelta(days=40):
            wins.append((qend - timedelta(days=BLACKOUT_PRE),
                         qend + timedelta(days=ANNOUNCE_LAG + BLACKOUT_POST)))
    return wins


def build() -> dict:
    _load_env()
    from shared.supabase_client import get_client
    sb = get_client()
    today = datetime.now(timezone.utc).date()
    latest = _latest_report_per_us_ticker(sb)
    universe = sorted(latest.keys())
    n_universe = len(universe)
    if n_universe == 0:
        raise SystemExit("[buyback] kein US-Universum in earnings_events")

    caps = _fetch_marketcaps(universe, today)
    total_cap = sum(caps.get(tk, 0.0) for tk in universe)
    use_cap = total_cap > 0

    y0, y1 = date(today.year, 1, 1), date(today.year, 12, 31)
    ticker_wins = {tk: _windows_for_year(latest[tk], y0, y1) for tk in universe}

    # Voll-Kalenderjahr-Serie (Jan–Dez)
    series, entering = [], []
    d = y0
    day_before = today - timedelta(days=1)
    prev_in = {tk for tk in universe if any(a <= day_before <= b for a, b in ticker_wins[tk])}
    while d <= y1:
        in_bo = [tk for tk in universe if any(a <= d <= b for a, b in ticker_wins[tk])]
        pct_eq = len(in_bo) / n_universe
        if use_cap:
            pct_cap = sum(caps.get(tk, 0.0) for tk in in_bo) / total_cap
        else:
            pct_cap = pct_eq
        series.append({
            "date": d.isoformat(),
            "n_in_blackout": len(in_bo),
            "pct_in_blackout": round(pct_eq, 4),
            "pct_mktcap_in_blackout": round(pct_cap, 4),
        })
        if today <= d <= today + timedelta(days=7):
            for tk in sorted(set(in_bo) - prev_in):
                entering.append({"ticker": tk, "blackout_since": d.isoformat()})
        prev_in = set(in_bo)
        d += timedelta(days=1)

    latest_pt = next((p for p in series if p["date"] == today.isoformat()), series[-1])

    # Schwergewichte heute im Blackout (nach marketCap-Gewicht)
    heavyweights = []
    if use_cap:
        in_today = [tk for tk in universe if any(a <= today <= b for a, b in ticker_wins[tk])]
        def _since(tk):
            for a, b in ticker_wins[tk]:
                if a <= today <= b:
                    return a.isoformat()
            return None
        for tk in sorted(in_today, key=lambda t: caps.get(t, 0.0), reverse=True)[:10]:
            if caps.get(tk):
                heavyweights.append({"ticker": tk, "weight": round(caps[tk] / total_cap, 4),
                                     "blackout_since": _since(tk)})

    est_missing = (ANNUAL_BUYBACK_USD / 252.0) * latest_pt["pct_mktcap_in_blackout"]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "year": today.year,
        "n_universe": n_universe,
        "mktcap_weighted": use_cap,
        "annual_buyback_usd": ANNUAL_BUYBACK_USD,
        "series": series,
        "latest": latest_pt,
        "est_missing_daily_bid_usd": round(est_missing, 0),
        "blackout_heavyweights": heavyweights,
        "entering_this_week": entering[:20],
        "note": ("Doppel-Proxy: nächste Earnings aus Quartals-Kadenz (~91T) projiziert; Blackout = "
                 "Quartalsende −14T (Standard-START) bis Ankündigung +2T (ENDE geschätzt). "
                 "Marktkap-gewichtet (Bank-Desk-Standard) + gleichgewichtete Vergleichslinie. "
                 "Rückkauf-Autorisierung ≠ Ausführung; $-Zahlen sind extern zitierte/geschätzte "
                 "Referenzen (~1 Bio $/Jahr, S&P DJI), NICHT aus unseren Daten. Markt-Wirkung des "
                 "Blackouts ist empirisch umstritten (SSGA: kein signif. Effekt). Kein Handelssignal."),
    }


def main() -> int:
    out = build()
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "buyback_blackout.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    lt = out["latest"]
    print(f"[buyback] {out['n_universe']} US-Firmen · heute "
          f"{lt['pct_mktcap_in_blackout']:.0%} Marktwert / {lt['pct_in_blackout']:.0%} Firmen im Blackout "
          f"· fehlender Bid ~{out['est_missing_daily_bid_usd']/1e9:.1f} Mrd $/Tag · "
          f"{len(out['blackout_heavyweights'])} Schwergewichte", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
