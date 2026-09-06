#!/usr/bin/env python3
"""
compute_options_skew.py — Options-Skew, IV-Term-Structure & Vol-Metriken, daily.

Ebenen:
  1) Markt-Gauges (gratis, kein Key): ^SKEW, ^VIX, ^VVIX via yahoo_downloader.
  2) Per-Ticker via marketdata.app (ein Token):
     - 25Δ-Skew (Put-IV − Call-IV) bei 30d UND 90d  → Skew + Skew-Term-Structure
     - ATM-IV-Term-Structure (delta=.5) über mehrere Laufzeiten (Contango/Backwardation)
     - VRP = ATM-IV(30d) − realisierte Vola (aus unseren Kursen)
     - 25Δ-Butterfly = (Put25+Call25)/2 − ATM  (Smile-Krümmung)
     - Put/Call-IV-Ratio

Schreibt landing/data/options_skew.json (+ akkumuliert options_skew_history.json).

Nutzung:  py -3.14 scripts/compute_options_skew.py [--tickers AAPL SPY QQQ]
"""
from __future__ import annotations
import argparse, gc, json, math, os, ssl, sys, time, urllib.error, urllib.request
from datetime import date
from pathlib import Path

_THROTTLE = 0.4   # s zwischen marketdata-Requests (Rate-Limit-Schutz)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.env_loader import load_env          # noqa: E402
load_env()
from shared.yahoo_downloader import download_data, clear_cache  # noqa: E402

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_MD25 = "https://api.marketdata.app/v1/options/chain/{sym}/?dte={dte}&delta=.25&token={tok}"
_MDATM = "https://api.marketdata.app/v1/options/chain/{sym}/?dte={dte}&delta=.5&token={tok}"
_TERM_DTES = (7, 30, 60, 90, 120, 180)
_DEFAULT_TICKERS = ["SPY","QQQ","IWM","AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","LLY","JPM","V","WMT","XOM","UNH","MA","HD","COST","ORCL","NFLX","AMD","CRM","BAC","KO","PEP","ADBE"]


def _get(url: str, tries: int = 5):
    """GET mit Throttle + 429-Backoff (marketdata rate-limitet Bursts)."""
    for i in range(tries):
        time.sleep(_THROTTLE)
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "SeasonAlpha/1.0"}),
                timeout=25, context=_CTX).read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(2.0 * (i + 1))       # exponentiell zurückstufen
                continue
            raise


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


def _realized_vol(sym: str):
    """Annualisierte realisierte Vola (20d, 30d) aus unseren Kursen. Decimals."""
    try:
        df = download_data(sym, period="6mo")
    except Exception:
        clear_cache(); gc.collect(); return None, None
    if df is None or len(df) < 25:
        clear_cache(); gc.collect(); return None, None
    c = df["Close"].to_numpy(dtype=float)
    r = [math.log(c[i] / c[i - 1]) for i in range(1, len(c)) if c[i - 1] > 0 and c[i] > 0]
    clear_cache(); gc.collect()

    def rv(n):
        if len(r) < n:
            return None
        seg = r[-n:]
        m = sum(seg) / n
        var = sum((x - m) ** 2 for x in seg) / (n - 1)
        return round(math.sqrt(var) * math.sqrt(252), 4)
    return rv(20), rv(30)


def _ticker_skew(sym: str, tok: str, dte: int = 30) -> dict | None:
    """25Δ-Put-IV − 25Δ-Call-IV via marketdata.app bei gegebener Laufzeit."""
    try:
        d = _get(_MD25.format(sym=sym, dte=dte, tok=tok))
    except Exception as e:
        print(f"  [md] {sym} 25Δ@{dte}: HTTP {e}")
        return None
    if d.get("s") != "ok":
        print(f"  [md] {sym} 25Δ@{dte}: {d.get('errmsg', d.get('s'))}")
        return None
    n = len(d.get("optionSymbol", []))
    best = {"call": None, "put": None}
    for i in range(n):
        side = d["side"][i]; dl = d["delta"][i]; iv = d["iv"][i]
        if dl is None or iv is None:
            continue
        cand = {"strike": d["strike"][i], "iv": round(float(iv), 4),
                "delta": round(float(dl), 3), "dist": abs(abs(float(dl)) - 0.25)}
        if best[side] is None or cand["dist"] < best[side]["dist"]:
            best[side] = cand
    if not best["call"] or not best["put"]:
        return None
    skew = round(best["put"]["iv"] - best["call"]["iv"], 4)
    return {
        "ticker": sym,
        "underlying": round(float(d["underlyingPrice"][0]), 2) if d.get("underlyingPrice") else None,
        "dte": d["dte"][0] if d.get("dte") else None,
        "call_25d": {k: best["call"][k] for k in ("strike", "iv", "delta")},
        "put_25d": {k: best["put"][k] for k in ("strike", "iv", "delta")},
        "skew_25d": skew,
        "skew_pts": round(skew * 100, 2),
    }


def _term_iv(sym: str, tok: str, dtes=_TERM_DTES) -> dict:
    """ATM-IV (delta=.5) je Laufzeit → {real_dte: iv-decimal}."""
    term = {}
    for dte in dtes:
        try:
            d = _get(_MDATM.format(sym=sym, dte=dte, tok=tok))
        except Exception:
            continue
        if d.get("s") != "ok":
            continue
        ivs = [d["iv"][i] for i in range(len(d.get("iv", []))) if d["iv"][i]]
        rd = int(d["dte"][0]) if d.get("dte") else dte
        if ivs:
            term[rd] = round(sum(ivs) / len(ivs), 4)
    return term


def _enrich(sym: str, tok: str) -> dict | None:
    """Voll-Metrik-Objekt für einen Ticker."""
    r = _ticker_skew(sym, tok, 30)
    if not r:
        return None
    r90 = _ticker_skew(sym, tok, 90)
    term = _term_iv(sym, tok)
    rv20, rv30 = _realized_vol(sym)
    put_iv = r["put_25d"]["iv"]; call_iv = r["call_25d"]["iv"]
    iv_atm = None
    if term:
        k = min(term, key=lambda kk: abs(kk - 30)); iv_atm = term[k]
    r["iv_atm"] = iv_atm
    r["rv20"] = rv20
    r["rv30"] = rv30
    r["vrp_pts"] = round((iv_atm - rv30) * 100, 2) if (iv_atm and rv30) else None
    r["bfly_pts"] = round(((put_iv + call_iv) / 2 - iv_atm) * 100, 2) if iv_atm else None
    r["pc_ratio"] = round(put_iv / call_iv, 3) if call_iv else None
    r["skew_back_pts"] = r90["skew_pts"] if r90 else None
    r["skew_term_pts"] = round(r90["skew_pts"] - r["skew_pts"], 2) if r90 else None
    r["term"] = [{"dte": k, "iv": term[k]} for k in sorted(term)]
    if r["term"] and iv_atm:
        r["contango"] = bool(r["term"][0]["iv"] < iv_atm)
        r["term_slope_pts"] = round((r["term"][-1]["iv"] - r["term"][0]["iv"]) * 100, 2)
    else:
        r["contango"] = None; r["term_slope_pts"] = None
    return r


def build(tickers: list[str], write: bool = True) -> dict:
    tok = os.environ.get("MARKETDATA_API_KEY", "")
    skew_s = _index_series("^SKEW"); vix_s = _index_series("^VIX"); vvix_s = _index_series("^VVIX")
    indices = {}
    for name, s in [("SKEW", skew_s), ("VIX", vix_s), ("VVIX", vvix_s)]:
        if s:
            indices[name] = {"last": s["last"], "date": s["date"]}
            print(f"  idx {name:5} {s['last']} ({s['date']})")
    # CBOE Implied-Correlation-Indizes (gratis via Yahoo; oft nur letzter Wert) → KPI + Forward-History
    corr = {}
    for name, sym in [("COR1M", "^COR1M"), ("COR3M", "^COR3M"), ("COR30D", "^COR30D")]:
        s = _index_series(sym, days=504)
        if s and s.get("last") is not None:
            corr[name] = {"last": s["last"], "date": s["date"]}
            print(f"  cor {name:6} {s['last']} ({s['date']})")
    series = []
    if skew_s:
        vixmap = dict(zip(vix_s.get("dates", []), vix_s.get("vals", [])))
        for dt_, sk in zip(skew_s["dates"], skew_s["vals"]):
            series.append({"date": dt_, "skew": sk, "vix": vixmap.get(dt_)})

    per = []
    if not tok:
        print("  [md] MARKETDATA_API_KEY fehlt — überspringe Per-Ticker-Metriken.")
    else:
        for t in tickers:
            r = _enrich(t, tok)
            if r:
                per.append(r)
                ct = "contango" if r.get("contango") else ("backwardation" if r.get("contango") is False else "?")
                print(f"  {t:6} skew {r['skew_pts']:+.2f} · ATM {(r['iv_atm'] or 0)*100:.1f}% · "
                      f"VRP {r.get('vrp_pts')} · bfly {r.get('bfly_pts')} · P/C {r.get('pc_ratio')} · term {ct}")

    out = {
        "generated": date.today().isoformat(),
        "source": "CBOE ^SKEW/^VIX/^VVIX/^COR (Yahoo) + marketdata.app IV (25Δ-Skew, ATM-Term-Structure)",
        "indices": indices, "correlation": corr, "series": series, "tickers": per,
    }
    if write:
        p = _ROOT / "landing/data/options_skew.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] {len(per)} Ticker + {len(indices)} Indizes → {p}")
        # Skalare Metriken vorwärts in History akkumulieren
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
                            "put_iv": t["put_25d"]["iv"], "call_iv": t["call_25d"]["iv"],
                            "iv_atm": t.get("iv_atm"), "vrp_pts": t.get("vrp_pts"),
                            "pc_ratio": t.get("pc_ratio"), "bfly_pts": t.get("bfly_pts")})
            hist[t["ticker"]] = arr[-750:]
        # CBOE-Correlation vorwärts akkumulieren (Yahoo liefert oft nur letzten Wert)
        if corr:
            carr = hist.setdefault("__CORR", [])
            if not any(e.get("date") == today for e in carr):
                carr.append({"date": today, "COR1M": (corr.get("COR1M") or {}).get("last"),
                             "COR3M": (corr.get("COR3M") or {}).get("last"),
                             "COR30D": (corr.get("COR30D") or {}).get("last")})
            hist["__CORR"] = carr[-750:]
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
