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
from datetime import date, timedelta
from pathlib import Path

_THROTTLE = 0.05  # s zwischen Massive-Seiten (flatrate/unlimited; kleiner Puffer)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.env_loader import load_env          # noqa: E402
load_env()
from shared.yahoo_downloader import download_data, clear_cache  # noqa: E402

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
# Massive.com (Polygon.io) Option-Chain-Snapshot — Flatrate, 1 Ticker = ganze Chain
# (Greeks/IV/OI je Kontrakt), paginiert. Ersetzt die per-Kontrakt-bepreiste marketdata-API.
_SNAP = "https://api.polygon.io/v3/snapshot/options/{sym}?expiration_date.lte={hi}&limit=250"
_MAXDTE = 190                       # nur Laufzeiten ≤190d (deckt Term-Structure + 25Δ ab)
_TERM_TARGETS = (7, 30, 60, 90, 120, 180)
_DEFAULT_TICKERS = ["SPY","QQQ","IWM","AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","LLY","JPM","V","WMT","XOM","UNH","MA","HD","COST","ORCL","NFLX","AMD","CRM","BAC","KO","PEP","ADBE"]


def _get(url: str, key: str, tries: int = 5):
    """GET (Massive: apiKey als Query-Param) mit 429-Backoff."""
    full = url + ("&" if "?" in url else "?") + "apiKey=" + key
    for i in range(tries):
        time.sleep(_THROTTLE)
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(full, headers={"User-Agent": "SeasonAlpha/1.0"}),
                timeout=30, context=_CTX).read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(2.0 * (i + 1))
                continue
            raise


def _chain(sym: str, key: str) -> list:
    """Volle Option-Chain (≤190d) als Kontraktliste (paginiert)."""
    hi = (date.today() + timedelta(days=_MAXDTE)).isoformat()
    url = _SNAP.format(sym=sym, hi=hi)
    out, pages = [], 0
    while url and pages < 45:
        d = _get(url, key)
        if d.get("status") not in ("OK", "DELAYED") and not d.get("results"):
            break
        out += d.get("results", [])
        url = d.get("next_url")
        pages += 1
    return out


def _pick(lst, target):
    """Kontrakt mit |delta| am nächsten an target (lst = [(delta, iv, strike, oi), …])."""
    return min(lst, key=lambda x: abs(abs(x[0]) - target)) if lst else None


def _byexp(contracts: list) -> dict:
    """Kontrakte je Verfallstag: {exp: {dte, call:[(δ,iv,K,oi)], put:[…], spot}}."""
    today = date.today(); by = {}
    for c in contracts:
        g = c.get("greeks") or {}; iv = c.get("implied_volatility"); dl = g.get("delta")
        if iv is None or dl is None:
            continue
        det = c.get("details") or {}; ex = det.get("expiration_date"); typ = det.get("contract_type")
        if not ex or typ not in ("call", "put"):
            continue
        dte = (date.fromisoformat(ex) - today).days
        e = by.setdefault(ex, {"dte": dte, "call": [], "put": []})
        e[typ].append((float(dl), round(float(iv), 4), det.get("strike_price"), c.get("open_interest")))
    return by


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


def _nearest_exp(by: dict, target_dte: int):
    return min(by, key=lambda e: abs(by[e]["dte"] - target_dte)) if by else None


def _skew_at(by: dict, target_dte: int) -> dict | None:
    """25Δ-Skew (Put-IV − Call-IV) bei der Expiry nahe target_dte."""
    ex = _nearest_exp(by, target_dte)
    if ex is None:
        return None
    e = by[ex]; cc = _pick(e["call"], 0.25); pp = _pick(e["put"], 0.25)
    if not cc or not pp:
        return None
    return {"exp": ex, "dte": e["dte"], "call_iv": cc[1], "call_strike": cc[2], "call_delta": round(cc[0], 3),
            "put_iv": pp[1], "put_strike": pp[2], "put_delta": round(pp[0], 3),
            "skew_pts": round((pp[1] - cc[1]) * 100, 2)}


def _atm_iv(e: dict):
    """ATM-IV = Mittel der 50Δ-Call/Put-IV einer Expiry."""
    cc = _pick(e["call"], 0.5); pp = _pick(e["put"], 0.5)
    return round((cc[1] + pp[1]) / 2, 4) if (cc and pp) else None


def _enrich(sym: str, key: str) -> dict | None:
    """Voll-Metrik-Objekt aus EINEM Massive-Chain-Snapshot."""
    try:
        contracts = _chain(sym, key)
    except Exception as e:
        print(f"  [massive] {sym}: {str(e)[:80]}")
        return None
    by = _byexp(contracts)
    s30 = _skew_at(by, 30)
    if not s30:
        print(f"  [massive] {sym}: kein 25Δ@30 (n={len(contracts)})")
        return None
    s90 = _skew_at(by, 90)
    # Term-Structure: ATM-IV je Ziel-Laufzeit (nächstliegende Expiry, dedupliziert)
    term, seen = [], set()
    for tgt in _TERM_TARGETS:
        ex = _nearest_exp(by, tgt)
        if ex is None or ex in seen:
            continue
        atm = _atm_iv(by[ex])
        if atm:
            term.append({"dte": by[ex]["dte"], "iv": atm}); seen.add(ex)
    term.sort(key=lambda t: t["dte"])
    iv_atm = min(term, key=lambda t: abs(t["dte"] - 30))["iv"] if term else None
    put_iv, call_iv = s30["put_iv"], s30["call_iv"]
    rv20, rv30 = _realized_vol(sym)
    spot = None
    for c in contracts:
        p = (c.get("underlying_asset") or {}).get("price")
        if p:
            spot = round(float(p), 2); break
    r = {
        "ticker": sym, "underlying": spot, "dte": s30["dte"],
        "call_25d": {"strike": s30["call_strike"], "iv": call_iv, "delta": s30["call_delta"]},
        "put_25d": {"strike": s30["put_strike"], "iv": put_iv, "delta": s30["put_delta"]},
        "skew_25d": round(put_iv - call_iv, 4), "skew_pts": s30["skew_pts"],
        "iv_atm": iv_atm, "rv20": rv20, "rv30": rv30,
        "vrp_pts": round((iv_atm - rv30) * 100, 2) if (iv_atm and rv30) else None,
        "bfly_pts": round(((put_iv + call_iv) / 2 - iv_atm) * 100, 2) if iv_atm else None,
        "pc_ratio": round(put_iv / call_iv, 3) if call_iv else None,
        "skew_back_pts": s90["skew_pts"] if s90 else None,
        "skew_term_pts": round(s90["skew_pts"] - s30["skew_pts"], 2) if s90 else None,
        "term": term,
    }
    if term and iv_atm:
        r["contango"] = bool(term[0]["iv"] < iv_atm)
        r["term_slope_pts"] = round((term[-1]["iv"] - term[0]["iv"]) * 100, 2)
    else:
        r["contango"] = None; r["term_slope_pts"] = None
    return r


def build(tickers: list[str], write: bool = True) -> dict:
    tok = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
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
        print("  [massive] MASSIVE_API_KEY fehlt — überspringe Per-Ticker-Metriken.")
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
        "source": "CBOE ^SKEW/^VIX/^VVIX/^COR (Yahoo) + Massive/Polygon Option-Chain-Snapshot (25Δ-Skew, ATM-Term-Structure, VRP)",
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
