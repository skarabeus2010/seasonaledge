"""
scripts/build_etf_flows.py — Panel C der /flows-Seite: ETF-Flow-Heatmap (Sektor-Rotation)
========================================================================================
ETF-Creations/Redemptions = tägliche Änderung der ausstehenden Anteile (Shares Outstanding).
Netto-Kapitalfluss ≈ ΔShsOut × Preis (die Marktbewegung wird so herausgerechnet, anders als bei
ΔAUM). Über die 11 Select-Sector-SPDRs gelegt zeigt es Rotation (Geld rein XLK, raus XLE) und
Risk-on/off (SPY/QQQ vs. TLT/GLD).

DATENLAGE (ehrlich): Yahoo liefert Shares-Outstanding nur als PUNKT-IN-ZEIT-Snapshot (kein
Verlauf) und aktualisiert ihn TRÄGE → Flows sind lumpig, echte Historie muss VORWÄRTS aufgebaut
werden. Cache `_etf_flows_history.json` (gitignored) akkumuliert je Handelstag einen Snapshot;
belastbare Wochen-Flows entstehen erst nach ~2 Wochen. Klar als Proxy gelabelt.

Schreibt `landing/data/etf_flows.json`.
  PYTHONUTF8=1 py -3.14 scripts/build_etf_flows.py
"""
from __future__ import annotations
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

_DATA = _ROOT / "landing" / "data"
_HISTORY = _DATA / "_etf_flows_history.json"

SECTORS = [("XLK", "Technologie"), ("XLF", "Finanzen"), ("XLE", "Energie"), ("XLV", "Gesundheit"),
           ("XLI", "Industrie"), ("XLY", "Zykl. Konsum"), ("XLP", "Basiskonsum"), ("XLU", "Versorger"),
           ("XLB", "Rohstoffe"), ("XLRE", "Immobilien"), ("XLC", "Kommunikation")]
BROAD = [("SPY", "S&P 500"), ("QQQ", "Nasdaq 100"), ("IWM", "Russell 2000"),
         ("TLT", "Langläufer-Anleihen"), ("GLD", "Gold")]
UNIVERSE = SECTORS + BROAD
_NAMES = dict(UNIVERSE)
_SECTOR_TK = [t for t, _ in SECTORS]

_YHEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}
_HIST_DAYS = 120
_OUT_WEEKS = 12


def _get_crumb():
    for _ in range(3):
        s = requests.Session(); s.headers.update(_YHEADERS)
        try:
            s.get("https://fc.yahoo.com/", timeout=15, allow_redirects=True)
            cr = s.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=15)
            c = cr.text.strip()
            if cr.status_code == 200 and c and len(c) < 50 and "{" not in c:
                return s, c
        except requests.RequestException:
            pass
        time.sleep(4)
    return None, None


def _snapshot() -> dict[str, list]:
    """{ticker: [shares_out, price]} für das Universum (leer bei Crumb-/Quote-Fehler)."""
    s, crumb = _get_crumb()
    if not crumb:
        print("    [etf] kein crumb — Snapshot übersprungen", flush=True)
        return {}
    syms = ",".join(t for t, _ in UNIVERSE)
    out = {}
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            r = s.get(f"https://{host}/v7/finance/quote?symbols={syms}&crumb={crumb}", timeout=25)
            if r.status_code != 200:
                continue
            for q in (r.json().get("quoteResponse", {}).get("result", []) or []):
                so, px = q.get("sharesOutstanding"), q.get("regularMarketPrice")
                # Fallback: implizite Anteile = netAssets / Preis (für ETFs ohne sharesOutstanding, z.B. XLRE/XLC)
                if not so and q.get("netAssets") and px:
                    so = float(q["netAssets"]) / float(px)
                if q.get("symbol") and so and px:
                    out[q["symbol"]] = [float(so), float(px)]
            break
        except (requests.RequestException, ValueError):
            continue
    print(f"    [etf] Snapshot: {len(out)}/{len(UNIVERSE)} Ticker", flush=True)
    return out


def _load_cache() -> dict:
    try:
        if _HISTORY.exists():
            return json.loads(_HISTORY.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _iso_week(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def build() -> dict:
    today = datetime.now(timezone.utc).date()
    cache = _load_cache()
    snap = _snapshot()
    if snap:
        cache[today.isoformat()] = snap
    # Cache auf Fenster beschneiden
    cutoff = (today - timedelta(days=_HIST_DAYS)).isoformat()
    cache = {k: v for k, v in cache.items() if k >= cutoff}
    try:
        _HISTORY.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    dates = sorted(cache.keys())
    # Tages-Flows: (SO[t]-SO[t-1]) * px[t]  je Ticker
    weekly: dict[str, dict[str, float]] = {}   # week -> ticker -> flow_usd
    for i in range(1, len(dates)):
        dprev, dcur = dates[i - 1], dates[i]
        wk = _iso_week(date.fromisoformat(dcur))
        for tk in _NAMES:
            a, b = cache[dprev].get(tk), cache[dcur].get(tk)
            if a and b:
                flow = (b[0] - a[0]) * b[1]
                if abs(flow) > 0:
                    weekly.setdefault(wk, {}).setdefault(tk, 0.0)
                    weekly[wk][tk] += flow

    weeks = sorted(weekly.keys())[-_OUT_WEEKS:]
    # Sektor-Heatmap-Matrix (in Mio $)
    flows_mn = {tk: [round(weekly.get(w, {}).get(tk, 0.0) / 1e6, 1) for w in weeks] for tk in _SECTOR_TK}

    # Top-Bewegungen der jüngsten Woche (über gesamtes Universum)
    top = {"week": weeks[-1] if weeks else None, "inflows": [], "outflows": []}
    if weeks:
        last = [(tk, weekly.get(weeks[-1], {}).get(tk, 0.0)) for tk in _NAMES]
        last = [(tk, f) for tk, f in last if abs(f) > 0]
        last.sort(key=lambda x: x[1], reverse=True)
        top["inflows"] = [{"ticker": tk, "name": _NAMES[tk], "flow_mn": round(f / 1e6, 1)} for tk, f in last[:5] if f > 0]
        top["outflows"] = [{"ticker": tk, "name": _NAMES[tk], "flow_mn": round(f / 1e6, 1)} for tk, f in last[-5:] if f < 0][::-1]

    # Aktueller Snapshot (für den Aufbau-Zustand / Beleg, dass getrackt wird)
    last_date = dates[-1] if dates else None
    latest_snapshot = []
    if last_date:
        for tk, _ in UNIVERSE:
            v = cache[last_date].get(tk)
            if v:
                latest_snapshot.append({"ticker": tk, "name": _NAMES[tk],
                                        "shares_out": int(v[0]), "price": round(v[1], 2),
                                        "aum_bn": round(v[0] * v[1] / 1e9, 1)})

    n_weeks_nonzero = sum(1 for w in weeks if any(abs(weekly.get(w, {}).get(tk, 0.0)) > 0 for tk in _SECTOR_TK))
    ready = n_weeks_nonzero >= 2

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "today": today.isoformat(),
        "n_snapshots": len(dates),
        "ready": ready,
        "sectors": [{"ticker": t, "name": n} for t, n in SECTORS],
        "weeks": weeks,
        "flows_mn": flows_mn,
        "top_week": top,
        "latest_snapshot": latest_snapshot,
        "note": ("Proxy: Netto-Flow ≈ ΔShares-Outstanding × Preis (rechnet die Marktbewegung heraus). "
                 "Yahoo aktualisiert Shares-Outstanding träge und liefert keinen Verlauf → Flows sind "
                 "lumpig, die Historie wird ab Aktivierung täglich vorwärts aufgebaut. Positiv = "
                 "Creations (Zufluss), negativ = Redemptions (Abfluss). Kein Handelssignal."),
    }


def main() -> int:
    out = build()
    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "etf_flows.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[etf] {out['n_snapshots']} Snapshots · {len(out['weeks'])} Wochen · "
          f"ready={out['ready']} · Universum {len(out['latest_snapshot'])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
