"""Phase 0 (Plan docs/review_prompts/2026-10-13_skew_ausreisser_plan_v2.md, Codex-Freigabe): einzelne Tage der
Skew-Historie aus Tagesbars nachrechnen — NUR LESEN, Ausgabe auf stdout. Läuft im Container (/app), Code-Stand 88c02ff.

Je Fall: Spot, alle Expiries 1..80 Tage mit DTE, je Expiry die Leg (25Δ-Call/Put + ATM, ungerundet soweit möglich)
oder der Verwerfungsgrund (Diagnosezähler aus shared.black_scholes), dann jede Kandidatengruppe aus
cm_leg_kandidaten mit w, h und interpolierten IVs (ungerundet), dazu die Entscheidung
  (a) Live-Logik  = scripts.compute_options_skew._skew_cm mit diesen Legs (vollständige Versorgung),
  (b) Backfill-Original = _plan (erste 3 Gruppen) + _reconstruct,
und die gespeicherte History-Zeile zum Vergleich.
Aufruf: PYTHONDONTWRITEBYTECODE=1 python3 skew_phase0.py SYM:DATUM [SYM:DATUM …]"""
import sys, os, json, math
sys.path.insert(0, "/app"); sys.path.insert(0, "/app/scripts")
sys.dont_write_bytecode = True
from datetime import date, timedelta
from shared.env_loader import load_env
load_env()
import backfill_skew_massive as bf
import compute_options_skew as cs
import shared.black_scholes as bs

KEY = os.environ["MASSIVE_API_KEY"]
HIST = json.load(open("/app/landing/data/options_skew_history.json")) if os.path.exists("/app/landing/data/options_skew_history.json") else {}


def interp_roh(v1, t1, v2, t2, t=30):
    if None in (v1, v2, t1, t2) or t1 == t2:
        return None
    if t1 > t2:
        v1, t1, v2, t2 = v2, t2, v1, t1
    w1, w2 = v1 * v1 * t1, v2 * v2 * t2
    var = w1 + (w2 - w1) * (t - t1) / (t2 - t1)
    return math.sqrt(var / t) if var > 0 else None


def fall(sym, d):
    out = {"sym": sym, "datum": d}
    closes = bf._closes(sym)
    if d not in closes:
        return {**out, "fehler": "kein Spot"}
    spot = closes[d]; out["spot"] = spot
    dd = date.fromisoformat(d)
    contracts = bf._list_contracts(sym, KEY, (dd + timedelta(days=1)).isoformat(), (dd + timedelta(days=80)).isoformat(),
                                   spot * (1 - bf._BAND), spot * (1 + bf._BAND))
    contracts, weg = bs.standardserie_filter(contracts, sym, ticker_feld=lambda c: c.get("ticker", ""))
    out["kontrakte"] = len(contracts); out["angepasst_verworfen"] = weg
    by_exp = {}
    for c in contracts:
        e = c.get("expiration_date")
        if e and c.get("strike_price") and c.get("contract_type") in ("call", "put"):
            by_exp.setdefault(e, []).append(c)
    dte = {e: (date.fromisoformat(e) - dd).days for e in by_exp}
    gruppen = bs.cm_leg_kandidaten(dte)
    out["gruppen"] = [{"exps": g["exps"], "dte": [dte[e] for e in g["exps"]], "pool": g["pool"], "art": g["art"]} for g in gruppen]
    noetig = sorted({e for g in gruppen for e in g["exps"]})
    lo, hi = spot * (1 - bf._BAND), spot * (1 + bf._BAND)
    legs, rohdaten = {}, {}
    for e in noetig:
        picked = []
        for typ in ("call", "put"):
            ss = sorted((c for c in by_exp[e] if c["contract_type"] == typ and lo <= c["strike_price"] <= hi),
                        key=lambda c: c["strike_price"])
            if len(ss) > bf._MAX_STRIKES:
                step = len(ss) / bf._MAX_STRIKES
                ss = [ss[int(i * step)] for i in range(bf._MAX_STRIKES)]
            picked += ss
        cands, fehler = [], 0
        for c in picked:
            try:
                b = bf._bars(c["ticker"], KEY, d, d, strict=True).get(d)
            except Exception as ex:
                fehler += 1; continue
            if b:
                cands.append({"typ": c["contract_type"], "K": float(c["strike_price"]), "px": b[0], "vol": b[1]})
        bs.diagnose_start()
        leg = bs.leg_from_prices([{k: x[k] for k in ("typ", "K", "px")} for x in cands], spot, dte[e])
        gruende = bs.diagnose_stop()
        legs[e] = leg
        rohdaten[e] = {"dte": dte[e], "kontrakte": len(picked), "mit_preis": len(cands), "abruffehler": fehler,
                       "vol_summe": sum(x["vol"] for x in cands), "leg": leg, "gruende": gruende}
    out["legs"] = rohdaten
    bew = []
    for g in gruppen:
        if len(g["exps"]) != 2:
            continue
        a, b = legs.get(g["exps"][0]), legs.get(g["exps"][1])
        t1, t2 = sorted([dte[g["exps"][0]], dte[g["exps"][1]]])
        w = (30 - t1) / (t2 - t1); h = max(0, -w, w - 1)
        r = {"exps": g["exps"], "dte": [t1, t2], "art": g["art"], "pool": g["pool"], "w": round(w, 3), "h": round(h, 3),
             "legs_ok": [bool(a), bool(b)]}
        if a and b:
            r.update({k: interp_roh(a[k], a["dte"], b[k], b["dte"]) for k in ("call_iv", "put_iv", "iv_atm")})
            r["putZeta"] = (r["put_iv"] - r["iv_atm"]) * 100 if r["put_iv"] and r["iv_atm"] else None
            r["callZeta"] = (r["call_iv"] - r["iv_atm"]) * 100 if r["call_iv"] and r["iv_atm"] else None
        bew.append(r)
    out["gruppen_bewertet"] = bew
    # (a) Live-Entscheidung mit vollständiger Versorgung
    by = {e: {"dte": dte[e]} for e in by_exp if e in legs}
    try:
        out["live_entscheidung"] = cs._skew_cm(by, leg_fn=lambda e: legs.get(e))
    except Exception as ex:
        out["live_entscheidung"] = {"fehler": repr(ex)}
    # (b) Backfill-Original: _plan (erste 3 Gruppen) + _reconstruct
    try:
        plan, need = bf._plan({d: spot}, contracts, [d], underlying=None)
        bars = {}
        for occ in need:
            try:
                bars[occ] = bf._bars(occ, KEY, d, d, strict=True)
            except Exception:
                bars[occ] = {}
        out["backfill_entscheidung"] = bf._reconstruct(d, spot, plan.get(d, []), need, bars) if d in plan else None
        out["backfill_legs_geplant"] = [(x[0], x[1]) for x in plan.get(d, [])]
    except Exception as ex:
        out["backfill_entscheidung"] = {"fehler": repr(ex)}
    out["gespeichert"] = next((x for x in HIST.get(sym, []) if x["date"] == d), None)
    return out


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        s, d = arg.split(":")
        try:
            r = fall(s, d)
        except Exception as ex:
            r = {"sym": s, "datum": d, "fehler": repr(ex)}
        print("@@FALL@@" + json.dumps(r, default=str), flush=True)
