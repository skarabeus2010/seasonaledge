"""Auswertung des Skew-Trockenlaufs (Block A, Ausreißer im Radar) — rein lesend, nur lokale Dateien.

Eingaben (Verzeichnis als Argument):
  skew_trockenlauf.jsonl, skew_trockenlauf_2.jsonl   — Fälle der Probe (scripts/research/skew_trockenlauf_probe.py)
  skew_trockenlauf_rest.txt                           — echte Menge der Fälle aus Lauf 2 (SYM:DATUM:MENGE)
  options_skew_history.json                           — Referenzverteilung je Ticker

Vorab festgelegt (Plan v2): Fenster date >= 2025-10-13, nur cm/cm_extrap; MAD roh (ohne 1,4826), MAD = 0 -> 0,1;
auffällig = |Wert - Median| / MAD > 6 (zusätzlich > 4 berichtet). Hauptgröße skew_pts, Zetas nebenher.

Regelvarianten werden auf die Kandidatengruppen angewandt: Live nimmt die erste Gruppe (Rangfolge) mit zwei gültigen
Legs — geprüft: 261/261 rankbare Fälle. Eine Regel verwirft eine Gruppe, dann gilt die nächste; bleibt keine, ist der
Tag nicht rankbar. Schwellen werden NUR an "entwicklung" abgeleitet und an "pruefung" geprüft.
"""
import itertools
import json
import math
import os
import statistics
import sys

VON, BIS = "2025-10-13", "2026-10-12"


def lade(verz):
    faelle = []
    for fn in ("skew_trockenlauf.jsonl", "skew_trockenlauf_2.jsonl"):
        with open(os.path.join(verz, fn), encoding="utf-8") as fh:
            for zeile in fh:
                if zeile.startswith("@@FALL@@"):
                    faelle.append(json.loads(zeile[8:]))
    menge = {}
    with open(os.path.join(verz, "skew_trockenlauf_rest.txt"), encoding="utf-8") as fh:
        for tok in fh.read().split():
            s, d, m = tok.split(":")
            menge[(s, d)] = m
    for f in faelle:
        if f["menge"] == "einzeln":
            f["menge"] = menge.get((f["sym"], f["datum"]), "einzeln?")
    # Doppelte Datensätze (gleiche Menge, gleicher Ticker/Tag) nur einmal zählen
    gesehen, eindeutig = set(), []
    for f in faelle:
        k = (f["menge"], f["sym"], f["datum"])
        if k not in gesehen:
            gesehen.add(k)
            eindeutig.append(f)
    faelle = eindeutig
    with open(os.path.join(verz, "options_skew_history.json"), encoding="utf-8") as fh:
        hist = json.load(fh)
    return faelle, hist


def referenz(hist, sym):
    zeilen = [z for z in hist.get(sym, []) if VON <= z.get("date", "") <= BIS and z.get("cm_mode") in ("cm", "cm_extrap")]
    out = {}
    for k in ("skew_pts", "put_zeta_pts", "call_zeta_pts"):
        w = [z[k] for z in zeilen if isinstance(z.get(k), (int, float))]
        if len(w) < 20:
            out[k] = None
            continue
        med = statistics.median(w)
        mad = statistics.median([abs(x - med) for x in w]) or 0.1
        out[k] = (med, mad)
    out["n"] = len(zeilen)
    return out


def werte(g):
    return {"skew_pts": (g["put_iv"] - g["call_iv"]) * 100,
            "put_zeta_pts": (g["put_iv"] - g["iv_atm"]) * 100,
            "call_zeta_pts": (g["call_iv"] - g["iv_atm"]) * 100}


def merkmale(f, g):
    """Leg-Kennzahlen der Gruppe, nur Legs mit Gewicht != 0 (w: Anteil des zweiten Legs)."""
    w = g["w"]
    gewichte = [1 - w, w] if len(g["exps"]) == 2 else [1]
    vol, dab, ziel, klam = [], [], [], []
    for exp, gw in zip(g["exps"], gewichte):
        if abs(gw) < 1e-12:
            continue
        leg = f["legs"].get(exp) or {}
        for s in ("call25", "put25"):
            k = leg.get(s)
            if k:
                vol.append(k.get("vol") or 0)
                dab.append(k.get("delta_abstand") or 0)
        ziel.append(min(leg.get("n_call_zielregion", 0), leg.get("n_put_zielregion", 0)))
        kl = leg.get("klammer") or {}
        klam.append(kl.get("max_abstand", 9) if kl.get("beidseitig") else 9)
    return {"vol_min": min(vol) if vol else 0, "delta_max": max(dab) if dab else 9,
            "ziel_min": min(ziel) if ziel else 0, "klammer_max": max(klam) if klam else 9, "h": g["h"]}


def waehle(f, regel):
    gs = sorted((g for g in f.get("gruppen", []) if "legs_ok" in g and all(g["legs_ok"])), key=lambda g: g["rang"])
    for g in gs:
        # Produktionsprüfungen (compute_options_skew.py ~570): Abstandsschutz 15 Tage, Interpolation erfolgreich
        lo, hi = min(g["dte"]), max(g["dte"])
        if not (lo <= 30 <= hi) and min(abs(lo - 30), abs(hi - 30)) > 15:
            continue
        if g.get("call_iv") is None or g.get("put_iv") is None:
            continue
        m = merkmale(f, g)
        if (m["h"] <= regel["H"] and m["vol_min"] >= regel["V"] and m["delta_max"] <= regel["D"]
                and m["ziel_min"] >= regel["N"] and m["klammer_max"] <= regel["K"]):
            return g, m
    return None, None


def z(ref, wv, k):
    if ref.get(k) is None:
        return None
    med, mad = ref[k]
    return abs(wv[k] - med) / mad


BASIS = {"H": math.inf, "V": 0, "D": math.inf, "N": 0, "K": math.inf}


def bewerte(faelle, refs, regel, schwelle=6.0):
    r = {"n": 0, "rankbar": 0, "auff": 0, "auff_basis": 0, "auff_weg": 0, "unauff_verloren": 0, "auff_neu": 0,
         "geaendert": 0}
    for f in faelle:
        if "gruppen" not in f:
            continue
        ref = refs[f["sym"]]
        r["n"] += 1
        gb, _ = waehle(f, BASIS)
        g, _ = waehle(f, regel)
        zb = z(ref, werte(gb), "skew_pts") if gb else None
        zn = z(ref, werte(g), "skew_pts") if g else None
        ab = zb is not None and zb > schwelle
        an = zn is not None and zn > schwelle
        r["rankbar"] += g is not None
        r["auff"] += an
        r["auff_basis"] += ab
        if ab and not an:
            r["auff_weg"] += 1
        if gb is not None and not ab and g is None:
            r["unauff_verloren"] += 1
        if an and not ab:
            r["auff_neu"] += 1
        if gb is not None and g is not None and gb["rang"] != g["rang"]:
            r["geaendert"] += 1
    return r


def raster():
    for H, V, D, N, K in itertools.product((math.inf, 1.0, 0.75, 0.5, 0.25),
                                           (0, 2, 5, 10, 25, 50),
                                           (math.inf, 0.06, 0.04),
                                           (0, 1, 2),
                                           (math.inf, 0.03, 0.02)):
        yield {"H": H, "V": V, "D": D, "N": N, "K": K}


def fmt(regel):
    return " ".join(f"{k}={'∞' if v == math.inf else v}" for k, v in regel.items())


def main():
    verz = sys.argv[1]
    faelle, hist = lade(verz)
    refs = {s: referenz(hist, s) for s in {f["sym"] for f in faelle}}
    mengen = {}
    for f in faelle:
        mengen.setdefault(f["menge"], []).append(f)
    print("Fälle je Menge:", {k: len(v) for k, v in mengen.items()})
    print("Referenz je Ticker (n, Median/MAD skew):",
          {s: (r["n"], tuple(round(x, 2) for x in r["skew_pts"]) if r["skew_pts"] else None) for s, r in refs.items()})

    print("\n== Basis (heutige Live-Auswahl) je Menge, Schwelle 6 / 4 MAD ==")
    for m, ff in sorted(mengen.items()):
        b6, b4 = bewerte(ff, refs, BASIS, 6), bewerte(ff, refs, BASIS, 4)
        print(f"{m:20s} n={b6['n']:3d} rankbar={b6['rankbar']:3d} auff>6={b6['auff']:2d} auff>4={b4['auff']:2d}")

    # Einzelmerkmale der auffälligen Basisfälle (alle Mengen), damit die Regel erklärbar bleibt
    print("\n== Auffällige Basisfälle (> 4 MAD), Merkmale der gewählten Gruppe ==")
    for f in faelle:
        if "gruppen" not in f:
            continue
        g, m = waehle(f, BASIS)
        if not g:
            continue
        wv = werte(g)
        zz = z(refs[f["sym"]], wv, "skew_pts")
        if zz is not None and zz > 4:
            print(f"{f['sym']:5s} {f['datum']} {f['menge']:18s} z={zz:5.1f} skew={wv['skew_pts']:6.2f} art={g['art']:10s} "
                  f"dte={g['dte']} h={m['h']:.2f} vol_min={m['vol_min']:.0f} delta_max={m['delta_max']:.3f} "
                  f"ziel_min={m['ziel_min']} klammer={m['klammer_max']:.3f}")

    dev = mengen.get("entwicklung", [])
    print("\n== Entwicklung: Regelraster (sortiert: auffällige weg, dann wenig verlorene unauffällige) ==")
    erg = []
    for regel in raster():
        r = bewerte(dev, refs, regel, 6)
        r4 = bewerte(dev, refs, regel, 4)
        erg.append((regel, r, r4))
    erg.sort(key=lambda t: (-(t[1]["auff_weg"] - t[1]["auff_neu"]), t[1]["unauff_verloren"]))
    for regel, r, r4 in erg[:25]:
        print(f"{fmt(regel):45s} rankbar={r['rankbar']:3d}/{r['n']} weg6={r['auff_weg']} neu6={r['auff_neu']} "
              f"weg4={r4['auff_weg']} neu4={r4['auff_neu']} unauff_verloren={r['unauff_verloren']} geändert={r['geaendert']}")

    print("\n== Einzelregeln (nur ein Merkmal), Entwicklung und Prüfung ==")
    einzel = [{"H": h} for h in (1.0, 0.75, 0.5, 0.25)] + [{"V": v} for v in (2, 5, 10, 25)] + \
             [{"D": d} for d in (0.06, 0.04)] + [{"N": n} for n in (1, 2)] + [{"K": k} for k in (0.03, 0.02)]
    for e in einzel:
        regel = dict(BASIS, **e)
        zeile = []
        for m in ("entwicklung", "pruefung"):
            r, r4 = bewerte(mengen.get(m, []), refs, regel, 6), bewerte(mengen.get(m, []), refs, regel, 4)
            zeile.append(f"{m[:4]}: rankbar {r['rankbar']}/{r['n']} weg6 {r['auff_weg']} neu6 {r['auff_neu']} "
                         f"weg4 {r4['auff_weg']} neu4 {r4['auff_neu']} verloren {r['unauff_verloren']}")
        print(f"{fmt(e):10s} | " + " | ".join(zeile))
    return erg, mengen, refs


if __name__ == "__main__":
    main()
