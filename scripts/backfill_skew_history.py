#!/usr/bin/env python3
"""
backfill_skew_history.py — historisches 25Δ-Skew rekonstruieren (Black-Scholes).

marketdata liefert historisch nur Preise (kein IV/Greeks), aber eine breite
historische Chain kostet nur 1 Credit. Wir invertieren die IV je Kontrakt selbst
aus dem Mid-Preis (BS-Bisektion), berechnen Delta und picken 25Δ-Call + 25Δ-Put
→ Skew = Put-IV − Call-IV. Ergebnis wird in landing/data/options_skew_history.json
gemergt (dedup je Datum), dieselbe Struktur wie die Vorwärts-Akkumulation.

Nutzung:
  py -3.14 scripts/backfill_skew_history.py [--years 2] [--step-days 7]
      [--symbols SPY QQQ ...] [--max-credits 8000]
"""
from __future__ import annotations
import argparse, json, math, os, socket, ssl, sys, time, urllib.request
from datetime import date, timedelta
from pathlib import Path

socket.setdefaulttimeout(20)   # harte Obergrenze — kein hängender urlopen

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from shared.env_loader import load_env          # noqa: E402
load_env()
from shared.yahoo_downloader import download_data, clear_cache  # noqa: E402

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_MD = "https://api.marketdata.app/v1/options/chain/{sym}/?date={d}&dte=30&strikeLimit=120&token={tok}"
_R = 0.045   # Risk-free-Näherung; q=0. Für Skew (Put-IV−Call-IV) unkritisch.

# ── Black-Scholes (self-contained) ──────────────────────────────────────────
def _cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def _bs_price(S, K, T, sig, typ):
    if T <= 0 or sig <= 0 or S <= 0 or K <= 0:
        return max(0.0, (S - K) if typ == "call" else (K - S))
    srt = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (_R + 0.5 * sig * sig) * T) / srt
    d2 = d1 - srt
    if typ == "call":
        return S * _cdf(d1) - K * math.exp(-_R * T) * _cdf(d2)
    return K * math.exp(-_R * T) * _cdf(-d2) - S * _cdf(-d1)

def _bs_delta(S, K, T, sig, typ):
    srt = sig * math.sqrt(T)
    d1 = (math.log(S / K) + (_R + 0.5 * sig * sig) * T) / srt
    return _cdf(d1) if typ == "call" else _cdf(d1) - 1.0

def _implied_vol(price, S, K, T, typ):
    """IV per Bisektion; None wenn kein Root (z.B. reiner Innerer Wert)."""
    if price is None or price <= 0 or T <= 0:
        return None
    lo, hi = 1e-4, 5.0
    plo = _bs_price(S, K, T, lo, typ) - price
    phi = _bs_price(S, K, T, hi, typ) - price
    if plo * phi > 0:
        return None
    for _ in range(64):
        mid = 0.5 * (lo + hi)
        pm = _bs_price(S, K, T, mid, typ) - price
        if abs(pm) < 1e-6:
            return mid
        if plo * pm < 0:
            hi = mid
        else:
            lo, plo = mid, pm
    return 0.5 * (lo + hi)


def _get(url):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "SeasonAlpha/1.0"}),
        timeout=25, context=_CTX).read())


def _skew_for(sym, d, tok, s_close):
    """25Δ-Skew für einen Ticker+Datum aus historischer Chain (BS-IV). None bei Lücke."""
    try:
        r = _get(_MD.format(sym=sym, d=d, tok=tok))
    except Exception:
        return None, 0
    if r.get("s") != "ok":
        return None, 0
    n = len(r.get("strike", []))
    S = None
    if r.get("underlyingPrice") and r["underlyingPrice"][0]:
        S = float(r["underlyingPrice"][0])
    if not S:
        S = s_close
    if not S:
        return None, 1
    best = {"call": None, "put": None}
    for i in range(n):
        K = r["strike"][i]; mid = r["mid"][i]; typ = r["side"][i]
        T = (r["dte"][i] or 30) / 365.0
        iv = _implied_vol(mid, S, K, T, typ)
        if iv is None or iv <= 0.01 or iv > 4.0:
            continue
        dl = _bs_delta(S, K, T, iv, typ)
        dist = abs(abs(dl) - 0.25)
        if best[typ] is None or dist < best[typ]["dist"]:
            best[typ] = {"iv": round(iv, 4), "dist": dist}
    if not best["call"] or not best["put"]:
        return None, 1
    return {"put_iv": best["put"]["iv"], "call_iv": best["call"]["iv"],
            "skew_pts": round((best["put"]["iv"] - best["call"]["iv"]) * 100, 2)}, 1


def _closes(sym):
    """Yahoo: date(ISO)->Close-Map."""
    df = download_data(sym, period="max"); clear_cache()
    if df is None or len(df) == 0:
        return {}
    dts = [str(x)[:10] for x in (df["Date"] if "Date" in df.columns else df.index).tolist()]
    return dict(zip(dts, (float(v) for v in df["Close"].to_numpy())))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=float, default=2.0)
    ap.add_argument("--every-n-td", type=int, default=5, help="jeder N-te Handelstag (5=wöchentlich)")
    ap.add_argument("--symbols", nargs="+", default=None)
    ap.add_argument("--max-credits", type=int, default=8000)
    a = ap.parse_args()
    tok = os.environ.get("MARKETDATA_API_KEY", "")
    if not tok:
        print("MARKETDATA_API_KEY fehlt."); return 1

    syms = a.symbols or ["SPY","QQQ","IWM","AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","LLY",
                         "JPM","V","WMT","XOM","UNH","MA","HD","COST","ORCL","NFLX","AMD","CRM","BAC","KO","PEP","ADBE"]

    today = date.today()
    cutoff = (today - timedelta(days=int(a.years * 365))).isoformat()

    hp = _ROOT / "landing/data/options_skew_history.json"
    hist = {}
    if hp.exists():
        try: hist = json.loads(hp.read_text(encoding="utf-8"))
        except Exception: hist = {}

    credits = 0
    for si, sym in enumerate(syms, 1):
        print(f"[{si}/{len(syms)}] {sym} …", flush=True)
        closes = _closes(sym)
        # echte Handelstage im Fenster, jeder N-te = wöchentlich (garantiert Daten + Close)
        traded = sorted(d for d in closes if d >= cutoff)
        targets = traded[::max(1, a.every_n_td)]
        arr = hist.setdefault(sym, [])
        have = {e["date"] for e in arr}
        added = 0
        for d in targets:
            if d in have:
                continue
            if credits >= a.max_credits:
                print(f"[stop] Credit-Limit {a.max_credits} erreicht."); break
            res, used = _skew_for(sym, d, tok, closes.get(d))
            credits += used
            if res:
                arr.append({"date": d, **res, "reconstructed": True})
                added += 1
            time.sleep(0.05)
        arr.sort(key=lambda e: e["date"])
        hist[sym] = arr[-900:]
        # inkrementell nach JEDEM Ticker persistieren → Fortschritt überlebt Abbruch
        hp.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {sym:6} +{added} Punkte (gesamt {len(arr)}) · Credits bisher {credits}", flush=True)
        if credits >= a.max_credits:
            break

    hp.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[OK] History: {sum(len(v) for v in hist.values())} Punkte / {len(hist)} Ticker · {credits} Credits verbraucht → {hp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
