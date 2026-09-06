#!/usr/bin/env python3
"""
compute_key_levels.py — Key Levels & Max Pain je Ticker (SpotGamma-Style-Panel).

Kombiniert zwei Quellen zu einem kompakten, teilbaren Level-Set je Ticker:
  1) landing/data/gex_summary.json (bereits aus der Massive-Voll-Chain gebaut):
     Spot, Zero-Gamma-Flip (= Vol-Trigger), Regime, Call-/Put-Wall.
     Diese Felder werden DIREKT übernommen (nicht neu gerechnet).
  2) Massive/Polygon-Option-Chain-Snapshot: Max Pain + OI-by-Strike + P/C-OI-Ratio
     (das steckt NICHT in gex_summary).

Max Pain (je nächstem großen Verfall mit substantieller OI, 0DTE gemieden):
  Der Strike, der die Summe der Auszahlungen über alle offenen Kontrakte minimiert:
    Σ_calls OI·max(0, S−K) + Σ_puts OI·max(0, K−S)  über Kandidat-S = alle Strikes.

Schreibt landing/data/key_levels.json (gitignored).

Nutzung:  py -3.14 scripts/compute_key_levels.py [--tickers SPY QQQ IWM DIA NVDA ...]
"""
from __future__ import annotations
import argparse, gc, json, os, ssl, sys, time, urllib.error, urllib.request
from datetime import date, timedelta
from pathlib import Path

_THROTTLE = 0.05  # s zwischen Massive-Seiten (flatrate/unlimited; kleiner Puffer)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.env_loader import load_env          # noqa: E402
load_env()
from shared.options_universe import CORE_OPTIONS, categories_for  # noqa: E402

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
# Massive.com (Polygon.io) Option-Chain-Snapshot — Flatrate, 1 Ticker = ganze Chain, paginiert.
_SNAP = "https://api.polygon.io/v3/snapshot/options/{sym}?expiration_date.lte={hi}&limit=250"
_MAXDTE = 70                       # Max Pain am nächsten Monatsverfall reicht (≤70d)
_MIN_EXP_OI = 5000                 # min. Gesamt-OI eines Verfalls, damit er als "groß" zählt
_DEFAULT_TICKERS = CORE_OPTIONS    # SPY, QQQ, IWM, DIA + Mag7


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
    """Volle Option-Chain (≤_MAXDTE) als Kontraktliste (paginiert)."""
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


def _by_exp(contracts: list) -> dict:
    """Kontrakte je Verfallstag: {exp: {dte, oi_total, calls:{K:oi}, puts:{K:oi}}}."""
    today = date.today(); by = {}
    for c in contracts:
        det = c.get("details") or {}
        ex = det.get("expiration_date"); typ = det.get("contract_type"); K = det.get("strike_price")
        oi = c.get("open_interest")
        if not ex or typ not in ("call", "put") or K is None:
            continue
        oi = float(oi or 0)
        e = by.setdefault(ex, {"dte": (date.fromisoformat(ex) - today).days,
                               "oi_total": 0.0, "calls": {}, "puts": {}})
        side = e["calls"] if typ == "call" else e["puts"]
        side[float(K)] = side.get(float(K), 0.0) + oi
        e["oi_total"] += oi
    return by


def _pick_expiry(by: dict) -> str | None:
    """Nächster Verfall mit substantieller OI (0DTE/heute meiden)."""
    cand = [(ex, e) for ex, e in by.items()
            if e["dte"] >= 1 and e["oi_total"] >= _MIN_EXP_OI]
    if not cand:  # Fallback: irgendein Verfall ≥1 DTE mit der meisten OI
        cand = [(ex, e) for ex, e in by.items() if e["dte"] >= 1]
    if not cand:
        return None
    # der früheste großer Verfall (nächster Monats-/Wochenverfall mit Substanz)
    cand.sort(key=lambda t: t[1]["dte"])
    return cand[0][0]


def _max_pain(e: dict) -> dict | None:
    """Max Pain + OI-Walls + P/C-Ratio für EINEN Verfall e."""
    calls, puts = e["calls"], e["puts"]
    strikes = sorted(set(calls) | set(puts))
    if len(strikes) < 3:
        return None
    # Auszahlungs-Summe über alle offenen Kontrakte je Kandidat-Strike S; Argmin = Max Pain
    best_S, best_pay = None, None
    for S in strikes:
        pay = 0.0
        for K, oi in calls.items():
            if S > K:
                pay += oi * (S - K)
        for K, oi in puts.items():
            if S < K:
                pay += oi * (K - S)
        if best_pay is None or pay < best_pay:
            best_pay, best_S = pay, S
    call_oi_sum = sum(calls.values()); put_oi_sum = sum(puts.values())
    top_call = sorted(calls.items(), key=lambda kv: kv[1], reverse=True)[:5]
    top_put = sorted(puts.items(), key=lambda kv: kv[1], reverse=True)[:5]
    return {
        "max_pain": best_S,
        "exp": None,  # vom Aufrufer gesetzt
        "top_call_oi": [{"strike": k, "oi": int(v)} for k, v in top_call],
        "top_put_oi": [{"strike": k, "oi": int(v)} for k, v in top_put],
        "pc_oi_ratio": round(put_oi_sum / call_oi_sum, 3) if call_oi_sum else None,
        "call_oi_sum": int(call_oi_sum), "put_oi_sum": int(put_oi_sum),
    }


def _load_gex() -> dict:
    """gex_summary.json → {ticker: {...}}. Fehlt sie, {} (graceful)."""
    p = _ROOT / "landing/data/gex_summary.json"
    if not p.exists():
        print("  [gex] gex_summary.json fehlt — Flip/Walls bleiben leer.")
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [gex] {e}")
        return {}
    return {t["ticker"]: t for t in d.get("tickers", [])}


def _one(sym: str, key: str, gex: dict) -> dict | None:
    """Ein Ticker: gex-Felder + Max-Pain/OI aus der Chain."""
    try:
        contracts = _chain(sym, key)
    except Exception as e:
        print(f"  [massive] {sym}: {str(e)[:80]}")
        contracts = []
    row = {"ticker": sym, "cats": categories_for(sym)}
    g = gex.get(sym, {})
    # gex_summary direkt übernehmen (nicht neu rechnen)
    row["spot"] = g.get("spot")
    row["vol_trigger"] = g.get("zero_gamma")
    row["regime"] = g.get("regime")
    row["call_wall"] = g.get("call_wall")
    row["put_wall"] = g.get("put_wall")
    row["net_gex_usd_bn"] = g.get("net_gex_usd_bn")
    # Max Pain + OI aus der Chain
    if contracts:
        by = _by_exp(contracts)
        ex = _pick_expiry(by)
        if ex:
            mp = _max_pain(by[ex])
            if mp:
                mp["exp"] = ex
                mp["exp_dte"] = by[ex]["dte"]
                row.update(mp)
    gc.collect()
    # Abstand Spot→Vol-Trigger und Spot→Max-Pain (%), fürs Frontend
    sp = row.get("spot")
    if sp:
        vt = row.get("vol_trigger")
        row["vt_dist_pct"] = round((sp - vt) / vt * 100, 2) if vt else None
        mpv = row.get("max_pain")
        row["mp_dist_pct"] = round((mpv - sp) / sp * 100, 2) if mpv else None
    # nur zurückgeben, wenn wenigstens irgendein Level da ist
    if row.get("spot") is None and row.get("max_pain") is None:
        print(f"  [skip] {sym}: keine Daten")
        return None
    return row


def build(tickers: list[str], write: bool = True) -> dict:
    tok = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
    gex = _load_gex()
    per = []
    if not tok:
        print("  [massive] MASSIVE_API_KEY fehlt — Max-Pain/OI übersprungen (nur gex-Felder).")
    for t in tickers:
        r = _one(t, tok, gex) if tok else (
            {"ticker": t, "cats": categories_for(t), **{k: gex.get(t, {}).get(v) for k, v in
             [("spot", "spot"), ("vol_trigger", "zero_gamma"), ("regime", "regime"),
              ("call_wall", "call_wall"), ("put_wall", "put_wall")]}} if t in gex else None)
        if r:
            per.append(r)
            print(f"  {t:6} spot {r.get('spot')} · flip {r.get('vol_trigger')} · "
                  f"MaxPain {r.get('max_pain')} ({r.get('exp')}) · CW {r.get('call_wall')} · "
                  f"PW {r.get('put_wall')} · P/C-OI {r.get('pc_oi_ratio')}")
    out = {
        "generated": date.today().isoformat(),
        "source": "gex_summary.json (Spot/Flip/Walls/Regime) + Massive/Polygon Option-Chain "
                  "(Max Pain, OI-by-Strike, P/C-OI). EOD, naive Dealer-Heuristik, kein Signal.",
        "tickers": per,
    }
    if write:
        p = _ROOT / "landing/data/key_levels.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[OK] {len(per)} Ticker → {p}")
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
