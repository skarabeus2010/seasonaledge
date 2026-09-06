"""
scripts/snapshot_gex_massive.py — täglicher GEX-Snapshot aus der MASSIVE-Voll-Chain
====================================================================================
Wie `snapshot_gex.py`, aber die Options-Chain kommt aus **Massive/Polygon** (Flatrate,
EOD-Open-Interest + Greeks/IV je Kontrakt) statt aus Yahoo. Damit fällt Yahoos
`openInterest=0`-Vormittagsloch weg — die Chain ist jederzeit vollständig.

Schreibt **exakt dasselbe Schema** wie snapshot_gex.py:
  landing/data/gex_summary.json          (Live-Summary für /dealer-positioning + /skew-Vol-Trigger)
  landing/data/gex_history/<YYYY-MM-DD>.json   (dagestempeltes, schlankes Archiv — proprietäre Historie)
  landing/data/gex_profile_<T>.json      (Per-Strike/Per-Term-Profile für die Charts)

Datenquelle (alles Flatrate/unlimited über MASSIVE_API_KEY):
  • Spot     GET /v2/aggs/ticker/<SYM>/prev            (EOD-Close = passt zum EOD-OI-Snapshot)
  • Chain    GET /v3/snapshot/options/<SYM>?expiration_date.lte=<hi>&limit=250   (paginiert via next_url)
Greeks werden NICHT von Polygon übernommen, sondern intern per Black-Scholes neu gerechnet
(dieselbe Engine + `--self-test`-Beweis wie die Yahoo-Variante) — nur K/OI/IV/T/typ fließen ein.

  PYTHONUTF8=1 py -3.14 scripts/snapshot_gex_massive.py
  PYTHONUTF8=1 py -3.14 scripts/snapshot_gex_massive.py --tickers SPY,QQQ,IWM   # Teilmenge (verify)
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from shared.env_loader import load_env  # noqa: E402
load_env()
# GEX-Engine (Black-Scholes-Greeks + Aggregation) — unverändert wiederverwendet.
from compute_gamma_exposure import (  # noqa: E402
    _exposures, _zero_gamma, _walls, _skew, _profile, _profile_by_term, _INDEX_TICKERS,
)
# Universum/Horizonte aus der Yahoo-Variante importieren → EIN Ort der Wahrheit, damit
# gex_summary.json (Frontend) und die dagestempelte Historie deckungsgleich bleiben.
from snapshot_gex import UNIVERSE, CHART_TICKERS, MAX_DAYS, PROFILE_MAX_DAYS  # noqa: E402

_DATA = _ROOT / "landing" / "data"

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_UA = {"User-Agent": "SeasonAlpha/1.0"}
_THROTTLE = 0.05          # s zwischen Massive-Seiten (Flatrate, kleiner Puffer)
_MAX_PAGES = 120          # Seiten-Cap (250 Kontrakte/Seite) — deckt auch die 1200d-Profil-Chains
_MIN_CONTRACTS = 20       # darunter ist der Snapshot kaputt (Fetch-Fehler), nicht bloß illiquide
_IV_LO, _IV_HI = 0.01, 5.0  # Polygon liefert für Deep-ITM/OTM Müll-IV (~0.0004) → verwerfen
_Q = 0.0                  # Dividendenrendite: bei ≤45d-Horizont für Gamma/GEX/Walls vernachlässigbar

_AGG = "https://api.polygon.io/v2/aggs/ticker/{sym}/prev?adjusted=true"
_SNAP = "https://api.polygon.io/v3/snapshot/options/{sym}?expiration_date.lte={hi}&limit=250"


def _get(url: str, key: str, tries: int = 5):
    """GET (Massive: apiKey als Query-Param, NICHT Header) mit 429-Backoff."""
    full = url + ("&" if "?" in url else "?") + "apiKey=" + key
    for i in range(tries):
        time.sleep(_THROTTLE)
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(full, headers=_UA), timeout=30, context=_CTX).read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(2.0 * (i + 1))
                continue
            raise
    return None


def _spot(sym: str, key: str) -> float | None:
    """EOD-Close des Underlyings (passt zeitlich zum EOD-Open-Interest der Chain)."""
    try:
        d = _get(_AGG.format(sym=sym), key)
    except Exception as e:
        print(f"  [massive] {sym} Spot: {str(e)[:80]}", flush=True)
        return None
    res = (d or {}).get("results") or []
    c = res[0].get("c") if res else None
    return float(c) if c else None


def _fetch_chain(sym: str, hi_days: int, key: str) -> list:
    """Volle Option-Chain (≤hi_days) als Polygon-Kontraktliste (paginiert via next_url)."""
    hi = (date.today() + timedelta(days=hi_days)).isoformat()
    url = _SNAP.format(sym=sym, hi=hi)
    out, pages = [], 0
    while url and pages < _MAX_PAGES:
        d = _get(url, key)
        if not d or (d.get("status") not in ("OK", "DELAYED") and not d.get("results")):
            break
        out += d.get("results", [])
        url = d.get("next_url")
        pages += 1
    return out


def _map(raw: list) -> list:
    """Polygon-Kontrakte → internes Engine-Format {type,K,oi,iv,T,exp,dte}.
    Verwirft Kontrakte ohne OI/IV und die Deep-ITM/OTM-Müll-IVs (~0)."""
    today = date.today()
    out = []
    for c in raw:
        det = c.get("details") or {}
        typ = det.get("contract_type"); K = det.get("strike_price"); ex = det.get("expiration_date")
        oi = c.get("open_interest") or 0
        iv = c.get("implied_volatility") or 0.0
        if typ not in ("call", "put") or not K or not ex or not oi:
            continue
        if not (_IV_LO <= iv <= _IV_HI):
            continue
        dte = (date.fromisoformat(ex) - today).days
        if dte < 0:
            continue
        out.append({"type": typ, "K": float(K), "oi": int(oi), "iv": float(iv),
                    "T": max(dte / 365.0, 1e-6), "exp": ex, "dte": dte})
    return out


def analyze_massive(sym: str, key: str, max_days: int,
                    profile_days: int | None = None) -> dict | None:
    """GEX-Objekt im EXAKTEN analyze()-Schema (compute_gamma_exposure), aber aus Massive-Daten.
    profile_days>None → fetch bis dorthin + hänge Per-Strike/Per-Term-Profil an."""
    horizon = profile_days or max_days
    spot = _spot(sym, key)
    if not spot:
        return None
    try:
        raw = _fetch_chain(sym, horizon, key)
    except Exception as e:
        print(f"  [massive] {sym} Chain: {str(e)[:80]}", flush=True)
        return None
    all_c = _map(raw)
    summary_c = [c for c in all_c if c["dte"] <= max_days]
    if len(summary_c) < _MIN_CONTRACTS:
        print(f"  [SKIP] {sym}: nur {len(summary_c)} brauchbare Kontrakte ≤{max_days}d "
              f"(von {len(raw)} roh) — Snapshot unbrauchbar.", flush=True)
        return None
    gex, vex, cex = _exposures(spot, summary_c, _Q)
    cw, pw, ag = _walls(spot, summary_c, _Q)
    n_exp = len({c["exp"] for c in summary_c})
    obj = {
        "ticker": sym, "spot": round(spot, 2), "div_yield": round(_Q, 4),
        "net_gex_usd_bn": round(gex / 1e9, 3),
        "net_vanna_usd_mn": round(vex / 1e6, 2),
        "net_charm_usd_mn_per_day": round(cex / 1e6, 2),
        "regime": "long_gamma" if gex > 0 else "short_gamma",
        "vol_regime": "vola-reduzierend" if gex > 0 else "vola-forcierend",
        "zero_gamma": _zero_gamma(spot, summary_c, _Q),
        "call_wall": cw, "put_wall": pw, "abs_gamma": ag,
        "skew": _skew(spot, summary_c),
        "n_contracts": len(summary_c), "n_expiries": n_exp,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "Massive/Polygon EOD-Chain (OI+IV je Kontrakt) · naive Dealer-Vorzeichen "
                "(long Calls/short Puts) = Heuristik, keine echten Dealer-Bücher · "
                "Greeks Black-Scholes (q=0 bei ≤45d vernachlässigbar)",
    }
    if profile_days:
        obj["profile"] = {"by_strike": _profile(spot, all_c, _Q),
                          "by_term": _profile_by_term(spot, all_c, _Q)}
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", help="Komma-Liste statt Voll-Universum (Verify/Teilmenge)")
    ap.add_argument("--no-write", action="store_true", help="nur rechnen + drucken, nichts schreiben")
    a = ap.parse_args()

    key = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
    if not key:
        print("[snapshot] ABBRUCH: MASSIVE_API_KEY fehlt (.env).", flush=True)
        return 1

    universe = ([t.strip().upper() for t in a.tickers.split(",") if t.strip()]
                if a.tickers else list(UNIVERSE))
    chart_set = set(CHART_TICKERS)

    results, charts, failed = [], {}, []
    for tk in universe:
        try:
            profile_days = PROFILE_MAX_DAYS if tk in chart_set else None
            o = analyze_massive(tk, key, MAX_DAYS, profile_days=profile_days)
        except Exception as e:
            o = None
            print(f"  [WARN] {tk}: {type(e).__name__}: {e}", flush=True)
        if not o:
            failed.append(tk)
            gc.collect()
            continue
        prof = o.pop("profile", None)
        results.append(o)
        flip = o["zero_gamma"]
        pos = f"Spot {o['spot']} {'ÜBER' if (flip and o['spot'] >= flip) else 'UNTER'} Flip {flip}"
        print(f"  [{tk:5}] GEX {o['net_gex_usd_bn']:+.3f}  {o['regime']:<12} {pos}  "
              f"CallW {o['call_wall']} PutW {o['put_wall']}  n={o['n_contracts']}", flush=True)
        if tk in chart_set:
            charts[tk] = prof
            if prof:
                print(f"          Profil {PROFILE_MAX_DAYS}d: {len(prof.get('by_term', []))} Verfälle, "
                      f"{len(prof.get('by_strike', []))} Strikes", flush=True)
        gc.collect()

    # Reissleine (identisch zur Yahoo-Variante): lieber gar nichts schreiben als die guten
    # bestehenden JSONs mit einem halben Lauf überbügeln.
    if len(results) < 0.6 * len(universe):
        print(f"[snapshot] ABBRUCH: nur {len(results)}/{len(universe)} Ticker brauchbar "
              f"(Fehlschläge: {failed}). Bestehende JSONs bleiben unverändert.", flush=True)
        return 1

    idx = [o for o in results if o["ticker"] in _INDEX_TICKERS]
    gamma_index = None
    if idx:
        val = round(sum(o["net_gex_usd_bn"] for o in idx), 3)
        gamma_index = {"value_usd_bn_per_pct": val,
                       "vol_regime": "vola-reduzierend" if val > 0 else "vola-forcierend",
                       "components": [o["ticker"] for o in idx]}

    stamp = date.today().isoformat()
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "date": stamp, "gamma_index": gamma_index, "tickers": results, "failed": failed,
        "note": "Naive Dealer-Heuristik (long Calls/short Puts), EOD-Massive/Polygon-Chain, "
                "kein Handelssignal — Referenzen, keine Barrieren.",
    }
    print(f"\n[gamma-index] {gamma_index['value_usd_bn_per_pct'] if gamma_index else '—'} Mrd $/1 % "
          f"({gamma_index['vol_regime'] if gamma_index else '—'})", flush=True)

    if a.no_write:
        print("[snapshot] --no-write: nichts geschrieben.", flush=True)
        return 0

    _DATA.mkdir(parents=True, exist_ok=True)
    (_DATA / "gex_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    for tk, prof in charts.items():
        (_DATA / f"gex_profile_{tk.replace('^', '')}.json").write_text(
            json.dumps({"ticker": tk, "date": stamp, "max_days": PROFILE_MAX_DAYS,
                        "profile": prof}, ensure_ascii=False), encoding="utf-8")

    hist = _DATA / "gex_history"
    hist.mkdir(exist_ok=True)
    slim = {"date": stamp, "gamma_index": gamma_index,
            "tickers": [{k: o[k] for k in ("ticker", "spot", "net_gex_usd_bn", "net_vanna_usd_mn",
                                           "net_charm_usd_mn_per_day", "regime", "zero_gamma",
                                           "call_wall", "put_wall", "skew")} for o in results]}
    (hist / f"{stamp}.json").write_text(json.dumps(slim, ensure_ascii=False), encoding="utf-8")

    print(f"[snapshot] {len(results)} ok / {len(failed)} fail · Gamma-Index "
          f"{gamma_index['value_usd_bn_per_pct'] if gamma_index else '—'} · Archiv {stamp}.json", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
