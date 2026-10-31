#!/usr/bin/env python3
"""
drawdown_analyse.py — Drawdown-Episoden eines Tickers und historische Einordnung des laufenden Drawdowns.

    py -3.14 scripts/research/drawdown_analyse.py blog/daten/qqq_2026-10-30.json > ausgabe.json

Plan: docs/review_prompts/2026-10-31_drawdown_analyse_plan.md, Codex-Antwort *_antwort.md (FREIGABE MIT AUFLAGEN,
Auflagen 1–6 hier umgesetzt). Rein beschreibend — keine Prognose der Restdauer.

Datenvertrag (Auflage 6): Zeilen aufsteigend, keine doppelten Daten; die erste Zeile ist die Indexbasis (ihr
log_return wird nicht verwendet), jede spätere Zeile braucht einen endlichen log_return — sonst Abbruch statt still 0.
Index I_t = exp(Σ lr) aus den gespeicherten Renditen (adjustierte Schlusskurse des Datenlieferanten → Näherung an die
Gesamtrendite; Kurs- und Gesamtrendite werden nicht gemischt).

Episode: Hoch P (letzter Schluss mit Drawdown 0) bis zur ersten Sitzung R mit I ≥ Hoch. Tief T = erste Sitzung mit
dem minimalen Drawdown (bei Gleichstand die frühere). Laufende Episode: R unbekannt (rechtszensiert).
Zeitmaße in Sitzungsabständen: „bis zum Wiedererreichen des Hochs“ = R − P, „bis zum Tief“ = T − P,
„Erholungszeit“ = R − T; dazu Kalendertage.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import date

MINDESTTIEFEN = (0.05, 0.10, 0.20)
FENSTER = (10, 15, 20, None)                     # Jahre; None = gesamte Historie


def quantil(v, q):
    """Lineare Interpolation wie numpy (Methode 'linear')."""
    s = sorted(v)
    if not s:
        return None
    pos = (len(s) - 1) * q
    lo = math.floor(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def pruefe_daten(z):
    datum = [r["date"] for r in z]
    if datum != sorted(datum) or len(set(datum)) != len(datum):
        raise SystemExit("Daten nicht aufsteigend oder mit doppelten Daten")
    for r in z[1:]:
        x = r["log_return"]
        if x is None or not math.isfinite(x):
            raise SystemExit(f"log_return fehlt/ungültig am {r['date']} — Pfad unbekannt, keine Auswertung")
    return datum


def reihe(daten):
    z = daten["zeilen"]
    datum = pruefe_daten(z)
    idx, k = [1.0], 0.0
    for r in z[1:]:
        k += r["log_return"]
        idx.append(math.exp(k))
    return datum, idx


def episoden(idx):
    aus, hoch_i, ep = [], 0, None
    for i in range(1, len(idx)):
        if idx[i] >= idx[hoch_i]:
            if ep is not None:
                ep["r"] = i
                aus.append(ep)
                ep = None
            hoch_i = i
        else:
            d = idx[i] / idx[hoch_i] - 1
            if ep is None:
                ep = {"p": hoch_i, "t": i, "r": None, "tiefe": d}
            elif d < ep["tiefe"]:                    # strikt kleiner: bei Gleichstand bleibt das frühere Tief
                ep["t"], ep["tiefe"] = i, d
    if ep is not None:
        aus.append(ep)
    return aus


def auswertung(daten):
    datum, idx = reihe(daten)
    letzt = len(idx) - 1
    kt = lambda a, b: (date.fromisoformat(datum[b]) - date.fromisoformat(datum[a])).days   # noqa: E731
    eps = episoden(idx)
    lauf = eps[-1] if eps and eps[-1]["r"] is None else None
    fertig = [e for e in eps if e["r"] is not None]
    d_heute = idx[letzt] / idx[lauf["p"]] - 1 if lauf else 0.0      # UNGERUNDET (Auflage 2)

    def erstes(e, schwelle):
        h, ende = idx[e["p"]], (e["r"] if e["r"] is not None else letzt + 1)
        for i in range(e["p"] + 1, ende):
            if idx[i] / h - 1 <= schwelle:
                return i
        return None

    def zeile(e):
        r = e["r"]
        z = {"hoch": datum[e["p"]], "tief": datum[e["t"]], "erholt": datum[r] if r is not None else None,
             "tiefe": 100 * e["tiefe"], "bis_tief": e["t"] - e["p"], "bis_tief_kt": kt(e["p"], e["t"])}
        if r is not None:
            z.update({"bis_hoch": r - e["p"], "bis_hoch_kt": kt(e["p"], r),
                      "erholung": r - e["t"], "erholung_kt": kt(e["t"], r)})
        s = erstes(e, d_heute) if lauf else None
        if s is not None:
            z["schwelle_am"] = datum[s]
            z["bis_schwelle"] = s - e["p"]
            if r is not None:
                z["schwelle_bis_hoch"] = r - s
                z["schwelle_bis_hoch_kt"] = kt(s, r)
        return z

    out = {"ticker": daten.get("ticker", "QQQ"), "erste_sitzung": datum[0], "letzte_sitzung": datum[-1],
           "d_heute": 100 * d_heute,
           "kurve": [[datum[i], round(100 * (idx[i] / h - 1), 3)]
                     for i, h in enumerate(_laufendes_hoch(idx))],
           "episoden": [zeile(e) for e in eps if e["tiefe"] <= -MINDESTTIEFEN[0]],
           "n_unter_schwelle": sum(1 for e in fertig if e["tiefe"] > -MINDESTTIEFEN[0]),
           "fenster": {}}
    if lauf:
        out["laufend"] = zeile(lauf)
        out["laufend"].update({"seit_hoch": letzt - lauf["p"], "seit_hoch_kt": kt(lauf["p"], letzt),
                               "aktuell": 100 * d_heute})

    hoch_kurve = _laufendes_hoch(idx)
    for jahre in FENSTER:
        start = datum[0] if jahre is None else _minus_jahre(datum[-1], jahre)
        fen = {"start": start, "mindesttiefe": {}}
        # Sitzungen im Fenster mit mindestens dem heutigen Verlust (zeitgewichtet, Auflage 7)
        tage_fen = [i for i in range(len(idx)) if datum[i] >= start]
        fen["sitzungen"] = len(tage_fen)
        fen["sitzungen_mind_heute"] = sum(1 for i in tage_fen if idx[i] / hoch_kurve[i] - 1 <= d_heute)
        # Episoden, die vor dem Fenster begannen und in das Fenster hineinreichen (Auflage 4)
        fen["grenzueberschreitend"] = [zeile(e) for e in eps if datum[e["p"]] < start
                                       and (e["r"] is None or datum[e["r"]] >= start) and e["tiefe"] <= -0.05]
        for m in MINDESTTIEFEN:
            grp = [e for e in fertig if datum[e["p"]] >= start and e["tiefe"] <= -m]
            dauer = [e["r"] - e["p"] for e in grp]
            g = {"n": len(grp), "dauer_median": quantil(dauer, .5), "dauer_q25": quantil(dauer, .25),
                 "dauer_q75": quantil(dauer, .75), "dauer_max": max(dauer) if dauer else None,
                 "erholung_median": quantil([e["r"] - e["t"] for e in grp], .5),
                 "tiefe_median": quantil([100 * e["tiefe"] for e in grp], .5)}
            if lauf and d_heute <= -m:
                alter = letzt - lauf["p"]
                g["laufend_erfuellt"] = True
                g["kuerzer_als_laufend"] = sum(1 for x in dauer if x < alter)      # Auflage 3
                g["tiefer_als_heute"] = sum(1 for e in grp if e["tiefe"] < d_heute)
            else:
                g["laufend_erfuellt"] = False
            # Überlebenskurve abgeschlossener Episoden: Anteil noch unter Wasser nach k Sitzungen (Auflage 5)
            g["ueberleben"] = _ueberleben(dauer)
            fen["mindesttiefe"][str(int(m * 100))] = g
        # Vergleichsgruppe „mindestens so tief wie heute“ (Episodentiefe ≤ D_heute, Auflage 2)
        tief = [e for e in fertig if datum[e["p"]] >= start and e["tiefe"] <= d_heute]
        ab = [e for e in tief]
        sb = [e["r"] - erstes(e, d_heute) for e in ab]
        tempo = [erstes(e, d_heute) - e["p"] for e in ab]
        fen["so_tief"] = {"n": len(tief),
                          "schwelle_bis_hoch": sorted(sb), "schwelle_median": quantil(sb, .5),
                          "schwelle_q25": quantil(sb, .25), "schwelle_q75": quantil(sb, .75),
                          "tempo": sorted(tempo),
                          # Tempo = erster Übertritt der aktuellen Tiefe − Peak, für historische UND laufende Episode identisch
                          # (Codex Seitenplan R1, Befund 4: vorher gegen das ganze Alter der laufenden Episode)
                          "langsamer_als_laufend": (sum(1 for x in tempo if x > out["laufend"]["bis_schwelle"])
                                                    if lauf and out["laufend"].get("bis_schwelle") is not None else None),
                          "ueberleben_ab_schwelle": _ueberleben(sb)}
        out["fenster"]["alle" if jahre is None else str(jahre)] = fen
    return out


def _laufendes_hoch(idx):
    h, aus = idx[0], []
    for x in idx:
        h = max(h, x)
        aus.append(h)
    return aus


def _minus_jahre(iso, n):
    d = date.fromisoformat(iso)
    try:
        return d.replace(year=d.year - n).isoformat()
    except ValueError:                               # 29.02.
        return d.replace(year=d.year - n, day=28).isoformat()


def _ueberleben(dauern):
    """Stützpunkte (k, Anteil der Episoden mit Dauer > k) an jedem Sprung; abgeschlossene Episoden."""
    if not dauern:
        return []
    n, aus = len(dauern), [[0, 1.0]]
    for k in sorted(set(dauern)):
        aus.append([k, sum(1 for x in dauern if x > k) / n])
    return aus


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    print(json.dumps(auswertung(d), ensure_ascii=False))
