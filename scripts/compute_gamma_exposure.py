"""
scripts/compute_gamma_exposure.py — GEX (Gamma Exposure) Proof-of-Concept
=========================================================================
Holt die Options-Chain eines Underlyings von Yahoo (EOD, Crumb-Session wie fetch_event_data),
rechnet je Kontrakt das Black-Scholes-Gamma und aggregiert die **Dealer-Gamma-Exposure**:

  net-GEX  = Σ [call: +γ·OI·100·S²·0,01]  −  Σ [put: γ·OI·100·S²·0,01]   ($ pro 1 % Spot-Move)
  Zero-Gamma-Flip = Spot-Level, an dem net-GEX das Vorzeichen wechselt
  Call/Put-Wall   = Strike mit max. Dealer-$-Gamma (Call bzw. Put)

⚠️ ANNAHME: „naive" Dealer-Vorzeichen (Dealer long Calls / short Puts). Die echten Dealer-Bücher
   sind unbekannt — reine Heuristik (wie bei SpotGamma & Co.). Ergebnis IMMER so kennzeichnen.

Aufruf:  PYTHONUTF8=1 py -3.14 scripts/compute_gamma_exposure.py --ticker SPY --max-days 90
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from scipy.stats import norm

_ROOT = Path(__file__).resolve().parent.parent
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
_OPT_HOSTS = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]

_SESSION: requests.Session | None = None
_CRUMB: str | None = None


def _crumb_session():
    global _SESSION, _CRUMB
    if _SESSION is not None:
        return _SESSION, _CRUMB
    s = requests.Session(); s.headers.update(_HEADERS)
    try:
        s.get("https://fc.yahoo.com/", timeout=15, allow_redirects=True)
        r = s.get("https://query2.finance.yahoo.com/v1/test/getcrumb", timeout=15)
        _CRUMB = r.text.strip() if (r.status_code == 200 and len(r.text) < 50) else None
    except requests.RequestException:
        _CRUMB = None
    _SESSION = s
    print(f"[gex] crumb={'OK' if _CRUMB else 'none'} cookies={len(s.cookies)}", flush=True)
    return s, _CRUMB


def _fetch_options(ticker: str, date_epoch: int | None = None) -> dict:
    s, crumb = _crumb_session()
    q = f"?crumb={crumb}" if crumb else ""
    if date_epoch:
        q = (q + "&" if q else "?") + f"date={date_epoch}"
    for host in _OPT_HOSTS:
        url = f"{host}/v7/finance/options/{ticker}{q}"
        try:
            r = s.get(url, timeout=20)
            if r.status_code == 200:
                res = r.json().get("optionChain", {}).get("result", [])
                if res:
                    return res[0]
        except (requests.RequestException, ValueError):
            continue
    return {}


def _bs_gamma(S: float, K: float, T: float, sigma: float, r: float = 0.04) -> float:
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    return norm.pdf(d1) / (S * sigma * math.sqrt(T))


def _collect(ticker: str, max_days: int):
    root = _fetch_options(ticker)
    if not root:
        return None
    spot = (root.get("quote", {}) or {}).get("regularMarketPrice")
    exps = root.get("expirationDates", []) or []
    now = time.time()
    keep = [e for e in exps if 0 <= (e - now) / 86400 <= max_days]
    contracts = []
    for i, e in enumerate(keep):
        node = root if (i == 0 and root.get("options")) else _fetch_options(ticker, e)
        opts = (node.get("options") or [{}])[0]
        T = max((e - now) / (365 * 86400), 1e-6)
        for typ, arr in (("call", opts.get("calls", [])), ("put", opts.get("puts", []))):
            for o in arr:
                K = o.get("strike"); oi = o.get("openInterest") or 0
                iv = o.get("impliedVolatility") or 0.0
                if K and oi and iv > 0:
                    contracts.append({"type": typ, "K": float(K), "oi": int(oi),
                                      "iv": float(iv), "T": T})
        time.sleep(0.25)
    return spot, contracts, len(keep)


def _net_gex_at(S: float, contracts: list) -> float:
    g = 0.0
    for c in contracts:
        dollar = _bs_gamma(S, c["K"], c["T"], c["iv"]) * c["oi"] * 100 * S * S * 0.01
        g += dollar if c["type"] == "call" else -dollar
    return g


def _zero_gamma(spot: float, contracts: list) -> float | None:
    lo, hi = spot * 0.85, spot * 1.15
    xs = [lo + (hi - lo) * i / 200 for i in range(201)]
    vals = [(x, _net_gex_at(x, contracts)) for x in xs]
    for (x0, v0), (x1, v1) in zip(vals, vals[1:]):
        if v0 == 0:
            return round(x0, 2)
        if v0 * v1 < 0:                       # Vorzeichenwechsel → lineare Interpolation
            return round(x0 + (x1 - x0) * (-v0) / (v1 - v0), 2)
    return None


def _walls(spot: float, contracts: list):
    agg = {}
    for c in contracts:
        dollar = _bs_gamma(spot, c["K"], c["T"], c["iv"]) * c["oi"] * 100 * spot * spot * 0.01
        agg.setdefault((c["type"], c["K"]), 0.0)
        agg[(c["type"], c["K"])] += dollar
    calls = {k[1]: v for k, v in agg.items() if k[0] == "call"}
    puts = {k[1]: v for k, v in agg.items() if k[0] == "put"}
    call_wall = max(calls, key=calls.get) if calls else None
    put_wall = max(puts, key=puts.get) if puts else None
    return call_wall, put_wall


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="SPY")
    ap.add_argument("--max-days", type=int, default=90)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    print(f"[gex] Hole Options-Chain {a.ticker} (≤{a.max_days} Tage)…", flush=True)
    got = _collect(a.ticker, a.max_days)
    if not got or not got[0] or not got[1]:
        print("[gex] FEHLER: keine Options-Daten (Auth/Rate-Limit/leere Chain).")
        return 1
    spot, contracts, n_exp = got
    net = _net_gex_at(spot, contracts)
    zg = _zero_gamma(spot, contracts)
    cw, pw = _walls(spot, contracts)
    out = {
        "ticker": a.ticker, "spot": round(spot, 2),
        "net_gex_usd_bn": round(net / 1e9, 3),
        "regime": "long_gamma" if net > 0 else "short_gamma",
        "zero_gamma": zg, "call_wall": cw, "put_wall": pw,
        "n_contracts": len(contracts), "n_expiries": n_exp,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "PoC · naive Dealer-Vorzeichen (long Calls/short Puts) = Heuristik, "
                "nicht echte Dealer-Bücher · EOD-OI von Yahoo",
    }
    print("\n" + "=" * 54)
    print(f"  {a.ticker}  Spot {out['spot']}   ({n_exp} Expiries, {len(contracts)} Kontrakte)")
    print("=" * 54)
    print(f"  net-GEX        {out['net_gex_usd_bn']:+.2f} Mrd $ / 1 %   → {out['regime']}")
    print(f"  Zero-Gamma     {zg}   (Flip long↔short)")
    print(f"  Call-Wall      {cw}   (Widerstand / Pinning oben)")
    print(f"  Put-Wall       {pw}   (Support / Pinning unten)")
    print(f"  Interpretation: {'>Flip = Dealer dämpfen (Mean-Reversion/Pinning)' if net>0 else '<Flip = Dealer verstärken (Trend/Vola)'}")
    outp = Path(a.out) if a.out else _ROOT / "landing" / "data" / f"gex_{a.ticker}.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[gex] JSON -> {outp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
