#!/usr/bin/env python3
"""
compute_options_skew.py — Options-Skew & IV (Put vs. Call), daily.

Zwei Ebenen:
  1) Markt-Gauges (gratis, kein Key): ^SKEW (CBOE Skew-Index), ^VIX, ^VVIX
     via yahoo_downloader — letzter Wert + kurze Historie.
  2) Per-Ticker 25-Delta-Skew via marketdata.app: ein Request je Ticker
     (chain?dte=30&delta=.25) liefert 25Δ-Call- + 25Δ-Put-IV → Skew =
     Put-IV − Call-IV (positiv = Put-Skew / Tail-Risk teurer).

Schreibt landing/data/options_skew.json.

Hinweis: Sandbox-Token (test_…) kann NUR AAPL. Für SPY/QQQ/mehr Ticker
einen Live-marketdata.app-Token in MARKETDATA_API_KEY hinterlegen.

Nutzung:  py -3.14 scripts/compute_options_skew.py [--tickers AAPL SPY QQQ]
"""
from __future__ import annotations
import argparse, json, os, ssl, sys, urllib.request
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.env_loader import load_env          # noqa: E402
load_env()
from shared.yahoo_downloader import download_data, clear_cache  # noqa: E402

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_MD = "https://api.marketdata.app/v1/options/chain/{sym}/?dte=30&delta=.25&token={tok}"
_DEFAULT_TICKERS = ["SPY","QQQ","IWM","AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","LLY","JPM","V","WMT","XOM","UNH","MA","HD","COST","ORCL","NFLX","AMD","CRM","BAC","KO","PEP","ADBE"]   # SPY/QQQ/IWM + Top-Aktien (Live-Token)


def _index_series(sym: str, days: int = 504) -> dict:
    """Letzte ~days Handelstage: {dates:[...], vals:[...]} + letzter Wert."""
    try:
        df = download_data(sym, period="max")
        clear_cache()
        if df is None or len(df) == 0:
            return {}
        dts = [str(d)[:10] for d in (df["Date"] if "Date" in df.columns else df.index).tolist()][-days:]
        vals = [None if v != v else round(float(v), 2) for v in df["Close"].to_numpy()[-days:]]
        return {"dates": dts, "vals": vals, "last": vals[-1], "date": dts[-1]}
    except Exception as e:
        print(f"  [idx] {sym}: {e}")
        return {}


def _ticker_skew(sym: str, tok: str) -> dict | None:
    """25Δ-Put-IV − 25Δ-Call-IV via marketdata.app."""
    try:
        raw = urllib.request.urlopen(
            urllib.request.Request(_MD.format(sym=sym, tok=tok), headers={"User-Agent": "SeasonAlpha/1.0"}),
            timeout=25, context=_CTX).read()
        d = json.loads(raw)
    except Exception as e:
        print(f"  [md] {sym}: HTTP {e}")
        return None
    if d.get("s") != "ok":
        print(f"  [md] {sym}: {d.get('errmsg', d.get('s'))}")
        return None

    n = len(d.get("optionSymbol", []))
    best = {"call": None, "put": None}   # je Seite: Kontrakt mit |delta| am nächsten an 0.25
    for i in range(n):
        side = d["side"][i]
        dl = d["delta"][i]
        iv = d["iv"][i]
        if dl is None or iv is None:
            continue
        cand = {"strike": d["strike"][i], "iv": round(float(iv), 4),
                "delta": round(float(dl), 3), "dist": abs(abs(float(dl)) - 0.25)}
        if best[side] is None or cand["dist"] < best[side]["dist"]:
            best[side] = cand
    if not best["call"] or not best["put"]:
        print(f"  [md] {sym}: kein 25Δ-Call/Put gefunden")
        return None
    skew = round(best["put"]["iv"] - best["call"]["iv"], 4)
    return {
        "ticker": sym,
        "underlying": round(float(d["underlyingPrice"][0]), 2) if d.get("underlyingPrice") else None,
        "dte": d["dte"][0] if d.get("dte") else None,
        "call_25d": {k: best["call"][k] for k in ("strike", "iv", "delta")},
        "put_25d": {k: best["put"][k] for k in ("strike", "iv", "delta")},
        "skew_25d": skew,
        "skew_pts": round(skew * 100, 2),   # Vol-Punkte
    }


def build(tickers: list[str], write: bool = True) -> dict:
    tok = os.environ.get("MARKETDATA_API_KEY", "")
    # Zeitreihen (für den Chart) + letzte Werte
    skew_s = _index_series("^SKEW")
    vix_s = _index_series("^VIX")
    vvix_s = _index_series("^VVIX")
    indices = {}
    for name, s in [("SKEW", skew_s), ("VIX", vix_s), ("VVIX", vvix_s)]:
        if s:
            indices[name] = {"last": s["last"], "date": s["date"]}
            print(f"  idx {name:5} {s['last']} ({s['date']})")
    # Chart-Serie: ^SKEW + ^VIX auf gemeinsame Daten ausgerichtet
    series = []
    if skew_s:
        vixmap = dict(zip(vix_s.get("dates", []), vix_s.get("vals", [])))
        for dt_, sk in zip(skew_s["dates"], skew_s["vals"]):
            series.append({"date": dt_, "skew": sk, "vix": vixmap.get(dt_)})

    per = []
    if not tok:
        print("  [md] MARKETDATA_API_KEY fehlt — überspringe Per-Ticker-Skew.")
    else:
        for t in tickers:
            r = _ticker_skew(t, tok)
            if r:
                per.append(r)
                print(f"  skew {t:6} Put {r['put_25d']['iv']} − Call {r['call_25d']['iv']} = {r['skew_pts']:+.2f} pts")

    out = {
        "generated": date.today().isoformat(),
        "source": "CBOE ^SKEW/^VIX/^VVIX (Yahoo) + marketdata.app 25Δ IV",
        "indices": indices,
        "series": series,
        "tickers": per,
    }
    if write:
        p = _ROOT / "landing/data/options_skew.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] {len(per)} Ticker + {len(indices)} Indizes → {p}")
        # Per-Ticker-Skew vorwärts akkumulieren (historisches IV gibt's auf dem Plan nicht)
        hp = _ROOT / "landing/data/options_skew_history.json"
        hist = {}
        if hp.exists():
            try: hist = json.loads(hp.read_text(encoding="utf-8"))
            except Exception: hist = {}
        today = out["generated"]
        for t in per:
            arr = hist.setdefault(t["ticker"], [])
            if not any(e.get("date") == today for e in arr):
                arr.append({"date": today, "skew_pts": t["skew_pts"],
                            "put_iv": t["put_25d"]["iv"], "call_iv": t["call_25d"]["iv"]})
            hist[t["ticker"]] = arr[-750:]      # ~3 Jahre Cap
        hp.write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[history] {sum(len(v) for v in hist.values())} Punkte über {len(hist)} Ticker → {hp.name}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=_DEFAULT_TICKERS)
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    build(a.tickers, not a.no_write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
