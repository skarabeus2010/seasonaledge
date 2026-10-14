"""Trockenlauf (Plan docs/review_prompts/2026-10-13_skew_ausreisser_phase0.md, Codex-Freigabe Runde 3): Skew-Tage aus
Tagesbars nachrechnen und je Stützstelle die Messqualität protokollieren — NUR LESEN, Ergebnis als JSON-Zeilen auf stdout.

Läuft im Container (/app, `PYTHONDONTWRITEBYTECODE=1`). Netz: Supabase EINMAL je Ticker für Spot/Handelstage
(`_closes`, Werte je Stichtag in der Ausgabe festgehalten), sonst nur Massive (Kontraktliste + Tagesbars).

Je Ticker-Tag:
  * alle Expiries der Rangliste `cm_leg_kandidaten` werden mit Bars versorgt (eine Abfrage je Kontrakt, im Speicher
    wiederverwendet — auch für den Backfill-Vergleich);
  * je Expiry: Kontrakte je Seite vor/nach den Filtern, in der Zielregion (|Δ_ref − 0,25| ≤ 0,10) und im ATM-Band,
    die gewählten 25Δ-Kontrakte und ATM-Anker mit Strike, Rohpreis, Volumen, IV (ungerundet), Delta-Abstand,
    Ankerklammer (beidseitig, Abstand am Forward), Verwerfungsgründe; dazu das echte `leg_from_prices` zum Abgleich;
  * je Kandidatengruppe: w, h ungerundet, interpolierte IVs ungerundet (aus den ungerundeten Leg-Werten);
  * Entscheidungen: Live (`compute_options_skew._skew_cm`) und Backfill (`_plan` + `_reconstruct`) mit denselben Bars;
  * Abruffehler je Kontrakt gezählt, getrennt von „keine verwertbare Tagesbar“.

Aufruf: python3 skew_trockenlauf_probe.py --stichprobe   (feste Stichprobe, Startwert 20261013)
        python3 skew_trockenlauf_probe.py SYM:DATUM …     (einzelne Tage)"""
import sys, os, json, math, random
sys.path.insert(0, "/app"); sys.path.insert(0, "/app/scripts")
sys.dont_write_bytecode = True
from datetime import date, timedelta
from shared.env_loader import load_env
load_env()
import backfill_skew_massive as bf
import compute_options_skew as cs
import shared.black_scholes as bs

KEY = os.environ["MASSIVE_API_KEY"]
TICKER = ["XLF", "JPM", "BAC", "GS", "MS", "C", "SPY", "AAPL"]
VON, BIS = "2025-10-13", "2026-10-12"
SEED, JE_TICKER = 20261013, 40
# Bekannte Problemfälle und gezielte Kontrollen — getrennt ausgewiesen, nicht Teil der Zufallsstichprobe
BEKANNT = ["MS:2026-09-16", "XLF:2026-09-16", "C:2026-06-18", "C:2025-10-29", "GS:2025-10-20"]
KONTROLLEN = {  # Earnings (Tag davor / Tag danach) und Verfallswochen
    "earnings": ["JPM:2026-07-13", "JPM:2026-07-15", "JPM:2026-04-13", "AAPL:2026-07-29", "AAPL:2026-07-31",
                 "GS:2026-07-15", "GS:2026-07-17"],
    "verfall": ["SPY:2026-03-18", "SPY:2026-03-20", "XLF:2026-06-17", "XLF:2026-06-19", "JPM:2026-09-17"],
}


def stichprobe(closes_je_ticker):
    rnd = random.Random(SEED)
    out = []
    for t in TICKER:
        tage = sorted(d for d in closes_je_ticker[t] if VON <= d <= BIS)
        je_monat = {}
        for d in tage:
            je_monat.setdefault(d[:7], []).append(d)
        monate = sorted(je_monat)
        gezogen = []
        while len(gezogen) < JE_TICKER:           # reihum je Monat, damit die Tage über das Jahr verteilt sind
            for m in monate:
                rest = [d for d in je_monat[m] if d not in gezogen]
                if rest and len(gezogen) < JE_TICKER:
                    gezogen.append(rnd.choice(rest))
        for i, d in enumerate(sorted(gezogen)):
            out.append({"sym": t, "datum": d, "menge": "entwicklung" if rnd.random() < 0.5 else "pruefung"})
    return out


def leg_instrumentiert(cands, spot, dte):
    """Wörtlich die Schritte von leg_from_prices, aber mit allen Zwischenwerten."""
    info = {"n_call_roh": sum(c["typ"] == "call" for c in cands), "n_put_roh": sum(c["typ"] == "put" for c in cands)}
    bs.diagnose_start()
    g = bs._gefilterte_punkte([{k: c[k] for k in ("typ", "K", "px")} for c in cands], spot, dte)
    if g is None:
        info["gruende"] = bs.diagnose_stop(); info["ergebnis"] = None
        return info
    gueltig, iv_atm, T, klammer = g
    F = bs.forward(spot, T)
    info.update({"n_call_gefiltert": sum(p[0] == "call" for p in gueltig), "n_put_gefiltert": sum(p[0] == "put" for p in gueltig),
                 "iv_atm_roh": iv_atm, "klammer": klammer, "forward": F})
    for seite in ("call", "put"):
        info[f"n_{seite}_zielregion"] = sum(1 for typ, K, iv in gueltig if typ == seite
                                             and abs(abs(bs.bs_delta(spot, K, T, iv_atm, typ)) - 0.25) <= 0.10)
    info["n_atm_band"] = sum(1 for typ, K, iv in gueltig if abs(math.log(K / F)) <= bs.PARITAET_BAND)
    best = bs._waehle_delta(gueltig, spot, T, iv_atm, 0.25)
    preis = {(c["typ"], c["K"]): (c["px"], c["vol"]) for c in cands}
    for seite in ("call", "put"):
        b = best[seite]
        if b:
            px, vol = preis.get((seite, b[2]), (None, None))
            info[f"{seite}25"] = {"K": b[2], "iv": b[1], "delta_abstand": b[0], "px": px, "vol": vol}
    strikes = sorted({K for typ, K, iv in gueltig if abs(math.log(K / F)) <= bs.PARITAET_BAND})
    unten = [k for k in strikes if k <= F]; oben = [k for k in strikes if k > F]
    info["atm_anker"] = [{"K": k, "call": preis.get(("call", k)), "put": preis.get(("put", k))}
                         for k in ([unten[-1]] if unten else []) + ([oben[0]] if oben else [])]
    leg = bs.leg_from_prices([{k: c[k] for k in ("typ", "K", "px")} for c in cands], spot, dte)
    info["gruende"] = bs.diagnose_stop()
    info["ergebnis"] = None if not leg else {"call_iv": best["call"][1], "put_iv": best["put"][1], "iv_atm": iv_atm,
                                             "dte": dte, "gerundet": leg}
    return info


def interp_roh(v1, t1, v2, t2, t=30):
    if None in (v1, v2, t1, t2) or t1 == t2:
        return None
    if t1 > t2:
        v1, t1, v2, t2 = v2, t2, v1, t1
    var = v1 * v1 * t1 + (v2 * v2 * t2 - v1 * v1 * t1) * (t - t1) / (t2 - t1)
    return math.sqrt(var / t) if var > 0 else None


def fall(sym, d, closes, kontrakte_cache):
    out = {"sym": sym, "datum": d}
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
    noetig = sorted({e for g in gruppen for e in g["exps"]})
    lo, hi = spot * (1 - bf._BAND), spot * (1 + bf._BAND)
    bars, abruffehler, legs, legs_info = {}, 0, {}, {}

    def hole(occ):
        nonlocal abruffehler
        if occ not in bars:
            try:
                bars[occ] = bf._bars(occ, KEY, d, d, strict=True)
            except Exception:
                abruffehler += 1; bars[occ] = None
        return bars[occ]

    for e in noetig:
        picked = []
        for typ in ("call", "put"):
            ss = sorted((c for c in by_exp[e] if c["contract_type"] == typ and lo <= c["strike_price"] <= hi),
                        key=lambda c: c["strike_price"])
            if len(ss) > bf._MAX_STRIKES:
                step = len(ss) / bf._MAX_STRIKES
                ss = [ss[int(i * step)] for i in range(bf._MAX_STRIKES)]
            picked += ss
        cands, ohne_bar = [], 0
        for c in picked:
            b = hole(c["ticker"])
            rec = (b or {}).get(d)
            if rec:
                cands.append({"typ": c["contract_type"], "K": float(c["strike_price"]), "px": rec[0], "vol": rec[1]})
            elif b is not None:
                ohne_bar += 1
        info = leg_instrumentiert(cands, spot, dte[e])
        info.update({"dte": dte[e], "kontrakte": len(picked), "ohne_verwertbare_bar": ohne_bar, "mit_preis": len(cands),
                     "vol_summe": sum(c["vol"] for c in cands)})
        legs_info[e] = info
        legs[e] = info["ergebnis"]
    out["legs"] = legs_info
    out["gruppen"] = []
    for g in gruppen:
        r = {"exps": g["exps"], "dte": [dte[x] for x in g["exps"]], "pool": g["pool"], "art": g["art"], "rang": g["rang"]}
        if len(g["exps"]) == 2:
            t1, t2 = sorted(r["dte"]); w = (30 - t1) / (t2 - t1)
            r.update({"w": w, "h": max(0.0, -w, w - 1)})
            a, b = legs.get(g["exps"][0]), legs.get(g["exps"][1])
            r["legs_ok"] = [bool(a), bool(b)]
            if a and b:
                for k in ("call_iv", "put_iv", "iv_atm"):
                    r[k] = interp_roh(a[k], a["dte"], b[k], b["dte"])
        out["gruppen"].append(r)
    by = {e: {"dte": dte[e]} for e in by_exp if e in legs}
    out["live"] = cs._skew_cm(by, leg_fn=lambda e: (legs.get(e) or {}).get("gerundet"))
    plan, need = bf._plan({d: spot}, contracts, [d], underlying=None)
    for occ in need:
        hole(occ)
    bars_bf = {occ: (bars.get(occ) or {}) for occ in need}
    out["backfill"] = bf._reconstruct(d, spot, plan.get(d, []), need, bars_bf) if d in plan else None
    out["abruffehler"] = abruffehler
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    faelle = []
    if args and args[0] == "--stichprobe":
        closes = {t: bf._closes(t) for t in TICKER}
        faelle = stichprobe(closes)
        faelle += [{"sym": x.split(":")[0], "datum": x.split(":")[1], "menge": "bekannt"} for x in BEKANNT]
        for art, lst in KONTROLLEN.items():
            faelle += [{"sym": x.split(":")[0], "datum": x.split(":")[1], "menge": "kontrolle_" + art} for x in lst]
    else:
        faelle = [{"sym": a.split(":")[0], "datum": a.split(":")[1], "menge": "einzeln"} for a in args]
        closes = {}
    for t in {f["sym"] for f in faelle}:
        if t not in closes:
            closes[t] = bf._closes(t)
    print("@@META@@" + json.dumps({"seed": SEED, "von": VON, "bis": BIS, "faelle": faelle,
                                   "spot": {f"{f['sym']}:{f['datum']}": closes[f["sym"]].get(f["datum"]) for f in faelle}}), flush=True)
    for f in faelle:
        try:
            if f["datum"] not in closes[f["sym"]]:
                r = {"fehler": "kein Spot / kein Handelstag"}
            else:
                r = fall(f["sym"], f["datum"], closes[f["sym"]], None)
        except Exception as ex:
            r = {"fehler": repr(ex)}
        print("@@FALL@@" + json.dumps({**f, **r}, default=str), flush=True)
