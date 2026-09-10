#!/usr/bin/env python3
"""
compute_options_flow.py — ΔOI-Flow (neue Positionierung) + 0DTE/Short-Dated, daily.

Zwei Analysen aus der Massive/Polygon-Voll-Chain (flatrate, EIN Fetch/Ticker):

  (4) ΔOI-Flow — Tag-über-Tag-Veränderung des Open Interest je Strike.
      OI ändert sich täglich (OCC-Settlement). Wir haben KEINE OI-Historie von
      Polygon → wir akkumulieren forward: je Kern-Ticker wird ein täglicher
      OI-by-Strike-Snapshot in landing/data/oi_history/<TICKER>.json persistiert
      (letzte ~30 Tage). ΔOI = heute − letzter Snapshot: net Call-ΔOI, net
      Put-ΔOI, die größten ΔOI-Strikes (Aufbau/Abbau), Put/Call-ΔOI.
      Am ersten Tag (kein Vortag) ist ΔOI leer → Seite zeigt "baut sich auf".

  (6) 0DTE / Short-Dated — Front-Verfall (0-2 DTE, sonst nächster Verfall):
      Gamma-Konzentration je Strike, die Strikes mit höchster Gamma/OI nahe
      Spot ("0DTE-Pins"), Front-Skew (25Δ), Call/Put-Volumen/OI-Verhältnis.
      Ehrlich: EOD-Chain, kein Intraday-Tape → "Short-Dated-Positionierung (EOD)".

Schreibt landing/data/options_flow.json (+ oi_history/<TICKER>.json). Beide
gitignored (Cron-Output → würde vom Deploy sonst zurückgeworfen).

Nutzung:  py -3.14 scripts/compute_options_flow.py [--tickers SPY QQQ NVDA]
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
from shared.options_universe import CORE_OPTIONS, categories_for  # noqa: E402

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
# Massive.com (Polygon.io) Option-Chain-Snapshot — Flatrate, 1 Ticker = ganze Chain
_SNAP = "https://api.polygon.io/v3/snapshot/options/{sym}?expiration_date.lte={hi}&limit=250"
_MAXDTE = 120                       # ΔOI: Laufzeiten ≤120d (OI ballt sich near-term)
_HIST_KEEP = 30                     # oi_history: letzte ~30 Snapshots je Ticker
_MONEY = 0.30                       # ±30 % Moneyness-Fenster für die Chain
_FRONT_MONEY = 0.08                 # ±8 % um Spot fürs 0DTE-Gamma-Profil
_TOP_STRIKES = 12                   # Top-ΔOI-Strikes je Ticker


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


def _spot(sym: str, key: str):
    """EOD-Vortagsschluss als Spot-Proxy (Underlying im Snapshot ist oft leer)."""
    try:
        d = _get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/prev", key)
        r = d.get("results") or []
        return round(float(r[0]["c"]), 2) if r else None
    except Exception:
        return None


def _chain(sym: str, key: str, spot=None) -> list:
    """Option-Chain (≤_MAXDTE) als Kontraktliste (paginiert). Bei bekanntem Spot
    auf ±_MONEY Moneyness gefiltert — spart Seiten (ΔOI/0DTE liegen near-money)."""
    hi = (date.today() + timedelta(days=_MAXDTE)).isoformat()
    url = _SNAP.format(sym=sym, hi=hi)
    if spot:
        url += f"&strike_price.gte={round(spot * (1 - _MONEY), 2)}&strike_price.lte={round(spot * (1 + _MONEY), 2)}"
    out, pages = [], 0
    while url and pages < 50:
        d = _get(url, key)
        if d.get("status") not in ("OK", "DELAYED") and not d.get("results"):
            break
        out += d.get("results", [])
        url = d.get("next_url")
        pages += 1
    return out


def _records(contracts: list) -> list:
    """Normalisiert Kontrakte → [{exp,dte,typ,strike,oi,gamma,delta,iv,vol}]."""
    today = date.today(); out = []
    for c in contracts:
        det = c.get("details") or {}
        ex = det.get("expiration_date"); typ = det.get("contract_type")
        strike = det.get("strike_price")
        if not ex or typ not in ("call", "put") or strike is None:
            continue
        g = c.get("greeks") or {}
        out.append({
            "exp": ex, "dte": (date.fromisoformat(ex) - today).days, "typ": typ,
            "strike": float(strike), "oi": int(c.get("open_interest") or 0),
            "gamma": (float(g["gamma"]) if g.get("gamma") is not None else None),
            "delta": (float(g["delta"]) if g.get("delta") is not None else None),
            "iv": (round(float(c["implied_volatility"]), 4) if c.get("implied_volatility") is not None else None),
            "vol": int((c.get("day") or {}).get("volume") or 0),
        })
    return out


# ── (4) ΔOI-Flow ─────────────────────────────────────────────────────────────
_OI_SCHEMA = 2      # 1 = je Strike (alle Laufzeiten summiert), 2 = je (Expiry, Strike)


def _oi_by_contract(recs: list) -> dict:
    """OI je (Expiry, Strike): {"<exp>|<strike>": {"c":oi,"p":oi}}.

    Warum nicht nur je Strike (Schema 1): Ein Roll von Verfall A nach B taucht dann
    als grosses positives Delta-OI an einem Strike auf und sieht aus wie neue
    Positionierung. Und verfallene Kontrakte verschwinden aus der Kette, statt als
    Abfluss zu zaehlen — nach jedem OPEX war die Netto-Summe dadurch systematisch
    zu positiv."""
    by: dict = {}
    for r in recs:
        k = f"{r.get('exp')}|{r['strike']:g}"
        e = by.setdefault(k, {"c": 0, "p": 0})
        e["c" if r["typ"] == "call" else "p"] += r["oi"]
    return by


def _load_hist(sym: str) -> list:
    p = _ROOT / "landing/data/oi_history" / f"{sym}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_hist(sym: str, hist: list):
    d = _ROOT / "landing/data/oi_history"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sym}.json").write_text(json.dumps(hist, ensure_ascii=False), encoding="utf-8")


def _doi(sym: str, recs: list, spot, today: str) -> dict:
    """ΔOI heute − letzter Snapshot, je (Expiry, Strike). Persistiert forward.

    Zwei Korrekturen gegenüber der Aggregation je Strike:
      * Ein Roll von Verfall A nach B ist kein Netto-Zufluss mehr. Vorher sah er
        wie neue Positionierung aus.
      * Kontrakte, die aus der Kette VERSCHWUNDEN sind (verfallen), zählen als
        Abfluss. Vorher wurde nur über die heutigen Schlüssel iteriert, ihr
        negatives ΔOI fehlte — nach jedem OPEX war die Netto-Summe zu positiv.

    Der Vergleich braucht ein Vorgänger-Snapshot IM SELBEN Schema. Nach der
    Umstellung ist der letzte Snapshot noch Schema 1 (nur Strike); dann wird kein
    ΔOI ausgewiesen statt eines Scheinwerts, bei dem jeder Kontrakt neu aussieht."""
    cur = _oi_by_contract(recs)
    hist = _load_hist(sym)
    prev = next((h for h in reversed(hist) if h.get("date") != today), None)
    out = {"available": False, "prev_date": None, "strikes": [],
           "net_call_doi": None, "net_put_doi": None, "pc_doi": None,
           "unavailable_reason": None, "gap_sessions": None}
    if not prev:
        out["unavailable_reason"] = "kein Vorgaenger-Snapshot"
    elif int(prev.get("schema") or 1) != _OI_SCHEMA:
        out["unavailable_reason"] = (f"Vorgaenger in Schema {prev.get('schema') or 1}, "
                                     f"aktuell {_OI_SCHEMA} — erster Lauf nach der Umstellung")
    else:
        pmap = prev.get("strikes") or {}
        net_c = net_p = 0
        per_strike: dict = {}                      # Anzeige bleibt je Strike aggregiert
        for k in set(cur) | set(pmap):             # UNION: verfallene Kontrakte zaehlen mit
            c_now = cur.get(k) or {"c": 0, "p": 0}
            c_old = pmap.get(k) or {}
            dc = int(c_now["c"]) - int(c_old.get("c") or 0)
            dp = int(c_now["p"]) - int(c_old.get("p") or 0)
            net_c += dc; net_p += dp
            try:
                strike = float(k.split("|", 1)[1])
            except Exception:
                continue
            e = per_strike.setdefault(strike, {"dc": 0, "dp": 0, "oi_c": 0, "oi_p": 0})
            e["dc"] += dc; e["dp"] += dp
            e["oi_c"] += int(c_now["c"]); e["oi_p"] += int(c_now["p"])
        diffs = []
        for strike, e in per_strike.items():
            if e["dc"]:
                diffs.append({"strike": strike, "type": "call", "doi": e["dc"], "oi": e["oi_c"]})
            if e["dp"]:
                diffs.append({"strike": strike, "type": "put", "doi": e["dp"], "oi": e["oi_p"]})
        diffs.sort(key=lambda x: abs(x["doi"]), reverse=True)
        gap = None
        try:
            gap = (date.fromisoformat(today) - date.fromisoformat(prev["date"])).days
        except Exception:
            pass
        out.update({
            "available": True, "prev_date": prev.get("date"), "gap_sessions": gap,
            "strikes": diffs[:_TOP_STRIKES],
            "net_call_doi": net_c, "net_put_doi": net_p,
            "pc_doi": round(abs(net_p) / abs(net_c), 3) if net_c else None,
        })
    # heutigen Snapshot upserten (Schema-Marke mitschreiben)
    hist = [h for h in hist if h.get("date") != today]
    hist.append({"date": today, "spot": spot, "schema": _OI_SCHEMA, "strikes": cur})
    _save_hist(sym, hist[-_HIST_KEEP:])
    return out


# ── (6) 0DTE / Short-Dated ───────────────────────────────────────────────────
def _pick_delta(lst, target):
    lst = [r for r in lst if r["delta"] is not None]
    return min(lst, key=lambda r: abs(abs(r["delta"]) - target)) if lst else None


def _front(recs: list, spot) -> dict | None:
    """Front-Verfall (kleinstes dte≥0). Gamma-by-Strike near Spot, Pins, 25Δ-Skew,
    Call/Put-Volumen & -OI der Front."""
    fut = [r for r in recs if r["dte"] >= 0]
    if not fut:
        return None
    front_dte = min(r["dte"] for r in fut)
    fr = [r for r in fut if r["dte"] == front_dte]
    exp = fr[0]["exp"]
    calls = [r for r in fr if r["typ"] == "call"]
    puts = [r for r in fr if r["typ"] == "put"]
    # Gamma-by-Strike (near Spot): Score = Σ gamma·OI je Strike (Call/Put getrennt)
    lo = spot * (1 - _FRONT_MONEY) if spot else None
    hi = spot * (1 + _FRONT_MONEY) if spot else None
    bys: dict = {}
    for r in fr:
        if r["gamma"] is None or r["oi"] <= 0:
            continue
        if spot and not (lo <= r["strike"] <= hi):
            continue
        e = bys.setdefault(r["strike"], {"strike": r["strike"], "call_oi": 0, "put_oi": 0,
                                         "call_g": 0.0, "put_g": 0.0})
        if r["typ"] == "call":
            e["call_oi"] += r["oi"]; e["call_g"] += r["gamma"] * r["oi"]
        else:
            e["put_oi"] += r["oi"]; e["put_g"] += r["gamma"] * r["oi"]
    strikes = sorted(bys.values(), key=lambda x: x["strike"])
    for s in strikes:
        s["gamma_oi"] = round(s["call_g"] + s["put_g"], 2)
        s["call_g"] = round(s["call_g"], 2); s["put_g"] = round(s["put_g"], 2)
    pins = sorted(strikes, key=lambda x: x["gamma_oi"], reverse=True)[:3]
    # 25Δ-Front-Skew (Put-IV − Call-IV)
    cc = _pick_delta(calls, 0.25); pp = _pick_delta(puts, 0.25)
    skew_pts = round((pp["iv"] - cc["iv"]) * 100, 2) if (cc and pp and cc["iv"] and pp["iv"]) else None
    call_vol = sum(r["vol"] for r in calls); put_vol = sum(r["vol"] for r in puts)
    call_oi = sum(r["oi"] for r in calls); put_oi = sum(r["oi"] for r in puts)
    return {
        "exp": exp, "dte": front_dte, "is_0dte": front_dte <= 2,
        "strikes": strikes, "pins": [{"strike": p["strike"], "score": p["gamma_oi"]} for p in pins],
        "skew_pts": skew_pts,
        "call_vol": call_vol, "put_vol": put_vol, "call_oi": call_oi, "put_oi": put_oi,
        "pc_vol": round(put_vol / call_vol, 3) if call_vol else None,
        "pc_oi": round(put_oi / call_oi, 3) if call_oi else None,
    }


def _enrich(sym: str, key: str, today: str) -> dict | None:
    spot = _spot(sym, key)
    try:
        contracts = _chain(sym, key, spot)
    except Exception as e:
        print(f"  [massive] {sym}: {str(e)[:80]}")
        return None
    recs = _records(contracts)
    if not recs:
        print(f"  [massive] {sym}: leere Chain (n={len(contracts)})")
        return None
    if not spot:                                    # Fallback: Underlying aus Snapshot
        for c in contracts:
            p = (c.get("underlying_asset") or {}).get("price")
            if p:
                spot = round(float(p), 2); break
    doi = _doi(sym, recs, spot, today)
    front = _front(recs, spot)
    return {"ticker": sym, "cats": categories_for(sym), "spot": spot,
            "doi": doi, "front": front}


def build(tickers: list[str], write: bool = True) -> dict:
    tok = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
    today = date.today().isoformat()
    per = []
    if not tok:
        print("  [massive] MASSIVE_API_KEY fehlt — nichts zu tun.")
    else:
        for t in tickers:
            r = _enrich(t, tok, today)
            if r:
                per.append(r)
                d, f = r["doi"], r["front"]
                doi_s = (f"ΔCall {d['net_call_doi']:+d} · ΔPut {d['net_put_doi']:+d}"
                         if d.get("available") else "ΔOI baut sich auf")
                fr_s = (f"Front {f['dte']}d ({'0DTE' if f['is_0dte'] else 'short'}) · "
                        f"skew {f['skew_pts']}" if f else "keine Front")
                print(f"  {t:6} {doi_s} · {fr_s}", flush=True)
            gc.collect()

    out = {
        "generated": today,
        "source": "US-Voll-Optionskette (EOD) · ΔOI = heute − Vortags-Snapshot (forward-akkumuliert) · Front-Verfall-Gamma/Skew. Kein Intraday-Tape.",
        "core": list(tickers), "tickers": per,
    }
    if write:
        p = _ROOT / "landing/data/options_flow.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        avail = sum(1 for r in per if r["doi"].get("available"))
        print(f"\n[OK] {len(per)} Ticker ({avail} mit ΔOI) → {p}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=list(CORE_OPTIONS))
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    build(a.tickers, not a.no_write)
    return 0


if __name__ == "__main__":
    sys.exit(main())
