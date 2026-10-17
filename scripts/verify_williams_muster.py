#!/usr/bin/env python3
"""verify_williams_muster.py — prüft scripts/research/williams_muster.py gegen handgebaute Kerzenreihen.

Unabhängige Sollwerte (von Hand gerechnet), keine Kopie der Rechnung. Ohne DB, ohne Netz.
Exit: 0 grün, 1 rot, 3 Absturz (für den Mutationstest: Absturz ist kein Nachweis).
"""
from __future__ import annotations

import math
import sys
import traceback
from datetime import date, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

FEHLER: list[str] = []


def pruef(name, ok, detail=""):
    print(("  ok   " if ok else "  FEHL ") + name + ("" if ok else f"  ->  {detail}"))
    if not ok:
        FEHLER.append(name)


def werktage(start: str, n: int) -> list[str]:
    d, aus = date.fromisoformat(start), []
    while len(aus) < n:
        if d.weekday() < 5:
            aus.append(d.isoformat())
        d += timedelta(days=1)
    return aus


def reihe(tage, kerzen, vol=1000):
    """kerzen: [(o, h, l, c), …] → rows mit log_return aus den Schlusskursen (erste Zeile 0)."""
    rows, vor = [], None
    for d, (o, h, l, c) in zip(tage, kerzen):
        lr = 0.0 if vor is None else math.log(c / vor)
        rows.append([d, o, h, l, c, vol, lr])
        vor = c
    return rows


def flach(n, kurs=100.0):
    """n unauffällige Kerzen: steigend um 0,1 %, Spanne ±0,5 %, Schluss in der Mitte (kein Muster)."""
    out, c = [], kurs
    for _ in range(n):
        c2 = c * 1.001
        out.append((c, c2 * 1.005, c * 0.995, c2))
        c = c2
    return out


def main() -> int:
    import numpy as np
    from scripts.research import williams_muster as W

    tage = werktage("2015-01-05", 40)
    sitz = tage[:]                                     # alle Werktage sind Sitzungen

    # ── 1. Fenster, Gültigkeit, Lücke, Kopie, Basisbruch ───────────────────────────────────────────────────────
    print("== Fenster und Gültigkeit")
    r = W.aufbereiten(reihe(tage, flach(40)), sitz)
    f = r["fenster"]
    pruef("saubere Reihe: Fenster genau für t = 1 … n−11", list(np.nonzero(f)[0]) == list(range(1, 40 - W.H_MAX)),
          list(np.nonzero(f)[0]))
    rows = reihe(tage, flach(40))
    rows[20][4] = rows[19][4]                          # Kopie: Schluss = Vortag, Volumen 0
    rows[20][5] = 0
    rows[20][2], rows[20][3], rows[20][1] = rows[20][4] * 1.001, rows[20][4] * 0.999, rows[20][4]
    rows[20][6] = 0.0
    r = W.aufbereiten(rows, sitz)
    betroffen = [t for t in range(1, 30) if t - 1 <= 20 <= t + W.H_MAX]
    pruef("Kopie (C = Vortag, Volumen 0) sperrt alle Fenster, die sie berühren",
          not any(r["fenster"][t] for t in betroffen) and int((r["grund"] == "kopie").sum()) == 1, list(r["grund"][18:23]))
    r = W.aufbereiten(rows, sitz, volumen_pflicht=False)
    pruef("Kopie wird auch ohne Volumenregel erkannt (Sensitivitätslauf)",
          not any(r["fenster"][t] for t in betroffen) and int((r["grund"] == "kopie").sum()) == 1, list(r["grund"][18:23]))
    sitz_luecke = tage[:15] + ["2015-01-24"] + tage[15:]   # fehlende Sitzung zwischen tage[14] und tage[15] (Samstag als Sitzung)
    r = W.aufbereiten(reihe(tage, flach(40)), sitz_luecke)
    pruef("Lücke im Börsenkalender: kein Glied 14→15, Fenster darüber gesperrt",
          not r["glied"][15] and not r["fenster"][10] and r["fenster"][16], (r["glied"][15], r["fenster"][10]))
    rows = reihe(tage, flach(40))
    rows[25][6] = rows[25][6] + 0.003                  # log_return passt nicht zum Kursverhältnis → Basisbruch
    r = W.aufbereiten(rows, sitz)
    pruef("Basisbruch (|ln(C/Cv) − lr| > Toleranz) sperrt das Glied",
          not r["glied"][25] and int(r["basisbruch"].sum()) == 1, int(r["basisbruch"].sum()))
    rows = reihe(tage, flach(40))
    rows[25][6] = rows[25][6] + 0.00005                # innerhalb der Rundungstoleranz
    r = W.aufbereiten(rows, sitz)
    pruef("Abweichung unter der Toleranz bleibt gültig", bool(r["glied"][25]))

    # ── 2. Muster ──────────────────────────────────────────────────────────────────────────────────────────────
    print("== Muster")
    k = flach(40)
    o, h, l, c = k[19]
    k[20] = (c, c * 1.002, l * 0.99, l * 0.995)        # SMASH_K: C_t < L_{t−1}, auch Outside? H_t < H_{t−1}? prüfen
    r = W.aufbereiten(reihe(tage, k), sitz)
    m = W.muster(r)
    pruef("SMASH_K erkannt (C_t < L_{t−1})", bool(m["SMASH_K"][20]) and not m["SMASH_V"][20])
    pruef("kein OUT_K ohne neues Hoch", not m["OUT_K"][20])
    kg = flach(40)
    o, h, l, c = kg[19]
    kg[20] = (c, c * 1.002, l * 0.99, l)               # Schluss genau auf dem Vortagestief → kein Smash
    pruef("Grenzfall C_t = L_{t−1}: kein SMASH_K", not W.muster(W.aufbereiten(reihe(tage, kg), sitz))["SMASH_K"][20])
    k2 = flach(40)
    o, h, l, c = k2[19]
    k2[20] = (c, h * 1.002, l * 0.99, l * 0.995)       # Outside + Schluss unter Vortagestief
    m = W.muster(W.aufbereiten(reihe(tage, k2), sitz))
    pruef("OUT_K erkannt und ist zugleich SMASH_K", bool(m["OUT_K"][20]) and bool(m["SMASH_K"][20]))
    k3 = flach(40)
    o, h, l, c = k3[19]
    k3[20] = (c * 1.0001, h * 0.999, l * 1.001, c * 1.0002)   # Inside
    m = W.muster(W.aufbereiten(reihe(tage, k3), sitz))
    pruef("INSIDE erkannt", bool(m["INSIDE"][20]) and not m["SMASH_K"][20])
    k4 = flach(40)
    k4[20] = (100.0, 101.0, 99.0, 99.6)                # Körper 0,4/2,0 = 20,0 % → nicht < 20
    k4[21] = (100.0, 101.0, 99.0, 99.61)               # 19,5 % → < 20
    rows = reihe(tage, k4)
    m = W.muster(W.aufbereiten(rows, sitz))
    pruef("BODY: genau 20,0 % ist kein Treffer, 19,5 % ist einer", not m["BODY"][20] and bool(m["BODY"][21]),
          (m["BODY"][20], m["BODY"][21]))
    pruef("Muster nur an Fenster-Tagen (letzte 10 Tage nie)", not any(m[x][-W.H_MAX:].any() for x in m))
    rows = reihe(tage, k)
    rows[20][5] = 0                                    # Mustertag ohne Volumen → ungültig → kein Muster
    pruef("Mustertag mit Volumen 0 → kein Muster", not W.muster(W.aufbereiten(rows, sitz))["SMASH_K"][20])

    # ── 3. Renditen ────────────────────────────────────────────────────────────────────────────────────────────
    print("== Renditen")
    k = flach(40)
    k[20] = (100.0, 102.0, 98.0, 99.0)
    k[21] = (103.0, 104.0, 101.0, 103.5)               # Lücke über H_t=102 → Kauf zum Open 103
    k[22] = (103.5, 105.0, 103.0, 104.0)
    r = W.aufbereiten(reihe(tage, k), sitz)
    lr = r["lr"]
    soll_bek = sum(lr[21:26])
    pruef("R_bek(5) = Σ lr[t+1..t+5]", abs(W.rendite(r, "bek", 1, 5)[20] - soll_bek) < 1e-12)
    pruef("R_bek Short-Sicht = −R_bek", abs(W.rendite(r, "bek", -1, 5)[20] + soll_bek) < 1e-12)
    soll_open = math.log(103.5 / 103.0) + sum(lr[22:26])
    pruef("R_open(5) = ln(C_{t+1}/O_{t+1}) + Σ lr[t+2..t+5]", abs(W.rendite(r, "open", 1, 5)[20] - soll_open) < 1e-12)
    pruef("Stopp Kauf bei Lücke über die Schwelle: Kurs = Open (103), nicht Schwelle (102)",
          abs(W.rendite(r, "stopp", 1, 5)[20] - soll_open) < 1e-12)
    k[21] = (101.0, 104.0, 100.5, 103.5)               # Open unter der Schwelle → Kurs = Schwelle 102
    r = W.aufbereiten(reihe(tage, k), sitz)
    soll = math.log(103.5 / 102.0) + sum(r["lr"][22:26])
    pruef("Stopp Kauf ohne Lücke: Kurs = H_t", abs(W.rendite(r, "stopp", 1, 5)[20] - soll) < 1e-12)
    k[21] = (101.0, 102.0, 100.5, 101.5)               # H_{t+1} = H_t genau → nicht ausgelöst (strikt >)
    r = W.aufbereiten(reihe(tage, k), sitz)
    pruef("Stopp Kauf: H_{t+1} = H_t löst nicht aus", math.isnan(W.rendite(r, "stopp", 1, 5)[20]))
    k[21] = (101.0, 101.9, 100.5, 101.5)               # H_{t+1} ≤ H_t → nicht ausgelöst
    r = W.aufbereiten(reihe(tage, k), sitz)
    pruef("Stopp Kauf nicht ausgelöst → NaN", math.isnan(W.rendite(r, "stopp", 1, 5)[20]))
    pruef("Setup inkl. nicht ausgelöster → 0", W.rendite(r, "setup", 1, 5)[20] == 0.0)
    k[21] = (97.0, 99.0, 96.0, 98.0)                   # Verkauf: Lücke unter L_t=98 → Kurs = Open 97
    r = W.aufbereiten(reihe(tage, k), sitz)
    soll = -(math.log(98.0 / 97.0) + sum(r["lr"][22:26]))
    pruef("Stopp Verkauf bei Lücke: Kurs = Open, Short-Vorzeichen", abs(W.rendite(r, "stopp", -1, 5)[20] - soll) < 1e-12)
    pruef("|R| für INSIDE/BODY", abs(W.rendite(r, "abs", 1, 5)[20] - abs(sum(r["lr"][21:26]))) < 1e-12)

    # ── 3b. Vola-Quintil ───────────────────────────────────────────────────────────────────────────────────────
    print("== Vola-Quintil")
    tq = werktage("2010-01-04", 320)
    kq, c = [], 100.0
    for i in range(320):
        f_ = 1.03 if (i >= 300 and i % 2) else (0.97 if i >= 300 else (1.001 if i % 2 else 0.999))
        c2 = c * f_
        kq.append((c, max(c, c2) * 1.001, min(c, c2) * 0.999, c2))
        c = c2
    rq = W.aufbereiten(reihe(tq, kq), tq)
    erstes = int(np.nonzero(rq["quintil"] >= 0)[0][0])
    # 20 Renditen brauchen 21 Schlusskurse → erster Vola-Wert an Tag 20, erstes Quintil nach 250 Vorwerten an Tag 270
    pruef("Quintil erst ab 250 Vorwerten (erster Tag = 20 + 250)", erstes == 20 + 250, erstes)
    pruef("ruhige Phase: mittleres Quintil, Sprung der Vola: oberstes Quintil (4)",
          rq["quintil"][299] in (0, 1, 2, 3, 4) and rq["quintil"][305] == 4, (rq["quintil"][299], rq["quintil"][305]))

    # ── 4. Abschnittsgrenzen ───────────────────────────────────────────────────────────────────────────────────
    print("== Abschnitte")
    t2 = werktage("2023-11-20", 60)
    r = W.aufbereiten(reihe(t2, flach(60)), t2)
    ent, pr = W.im_abschnitt(r, "entdeckung"), W.im_abschnitt(r, "pruef")
    letzt_ent = max(i for i in range(60) if ent[i])
    pruef("Entdeckung: t+10 liegt nicht nach 2023-12-29", r["d"][letzt_ent + W.H_MAX] <= "2023-12-29",
          r["d"][letzt_ent + W.H_MAX])
    pruef("Prüfzeitraum: erstes t ab 2024-01-02", min(r["d"][i] for i in range(60) if pr[i]) >= "2024-01-02")
    pruef("Fenster über die Grenze gehören zu keinem Abschnitt",
          any(r["fenster"][i] and not ent[i] and not pr[i] for i in range(60)))

    # ── 5. Punktschätzer, Zellen, Bootstrap-Formel ─────────────────────────────────────────────────────────────
    print("== Statistik")
    # Kontrolle A: y = 0…19 an d0…d19 (Mittel 9,5); B: 19 Kontrolltage (unter der Mindestzahl 20).
    # Ereignisse ⊂ Kontrolle: A an d3 und d4 (Kontrollwerte dort hier überschrieben: 15 bzw. 5,5), B an d5.
    ko = [(("A", "x"), f"d{i}", {3: 15.0, 4: 5.5}.get(i, float(i))) for i in range(20)] + \
         [(("B", "x"), f"d{i}", 9.0 if i == 5 else 1.0) for i in range(19)]
    ev = [(("A", "x"), "d3", 15.0), (("A", "x"), "d4", 5.5), (("B", "x"), "d5", 9.0)]
    # Achse: alphabetisch d0, d1, d10 … d19, d2 … d9, dazu zwei Sitzungen ohne Einträge (e0, e1) als Nullspalten
    achse = {d: i for i, d in enumerate(sorted({f"d{i}" for i in range(20)} | {"e0", "e1"}))}
    zellen = W.Zellen()
    daten = W.daten_aus_tupeln(ko, ev, zellen, achse)
    p = W.punkt(daten, zellen)
    mA = (sum(range(20)) - 3 - 4 + 15.0 + 5.5) / 20
    pruef("T = Mittel(y − m_Zelle), Zelle mit 19 Kontrollen samt Ereignis ausgeschlossen",
          abs(p["T"] - ((15.0 - mA) + (5.5 - mA)) / 2) < 1e-12 and p["n"] == 2 and p["ausgeschlossen_zellen"] == 1, p)
    Z, D = len(zellen.ticker), len(achse)
    original = W.ziehung
    try:
        W.ziehung = lambda D, L, rng: np.ones(D, dtype=np.int64)
        bs = W.bootstrap({"x": daten}, Z, D, 3, 20, 1)
    finally:
        W.ziehung = original
    pruef("Bootstrap mit Gewicht 1 je Tag (inkl. leerer Sitzungen) reproduziert T exakt",
          np.allclose(bs["x"]["T_stern"], p["T"]), bs["x"]["T_stern"])
    try:
        W.ziehung = lambda D, L, rng: np.where(np.arange(D) < 6, 0, 1)   # d0, d1, d10 … d13 gezogen 0×
        bs = W.bootstrap({"x": daten}, Z, D, 1, 20, 1)
    finally:
        W.ziehung = original
    # Achse alphabetisch: d0, d1, d10 … d19, d2 … d9 → Gewicht 0 für d0, d1, d10, d11, d12, d13.
    # Zelle A ohne diese Tage: Werte d2…d9 (mit 15 und 5,5 statt 3 und 4) + d14…d19 → (44 − 7 + 20,5 + 99)/14
    mA2 = (44 - 7 + 20.5 + 99) / 14
    soll_bs = ((15.0 - mA2) + (5.5 - mA2)) / 2
    pruef("Bootstrap: Kontrollmittel je Zelle wird aus den gezogenen Tagen neu geschätzt",
          abs(float(bs["x"]["T_stern"][0]) - soll_bs) < 1e-12, (bs["x"]["T_stern"], soll_bs))
    # |T*−T| = [1, 1.5, 0.2, 0.1] ≥ 1 → 2 Treffer → (1+2)/(1+4)
    pruef("p zweiseitig mit +1", abs(W.p_zweiseitig(1.0, np.array([0.0, 2.5, 1.2, 0.9])) - 3 / 5) < 1e-12)
    # d=+1: T*−1 ≥ 1 → nur 2,5 → (1+1)/5;  d=−1, T=−1: −(T*+1) ≥ 1 → nur −2,5 → (1+1)/3
    pruef("p einseitig in Richtung d", abs(W.p_einseitig(1.0, np.array([0.0, 2.5, 1.2, 0.9]), 1) - 2 / 5) < 1e-12
          and abs(W.p_einseitig(-1.0, np.array([-2.5, 0.1]), -1) - 2 / 3) < 1e-12
          # d=−1, T=−1: Treffer T* ≤ −2 → −2,5 und −3,0 → (1+2)/4 (ohne Richtung wären es (1+1)/4)
          and abs(W.p_einseitig(-1.0, np.array([-2.5, -3.0, 0.5]), -1) - 3 / 4) < 1e-12)
    hl = W.holm({"a": 0.001, "b": 0.02, "c": 0.04})
    pruef("Holm: 0,001 < 0,0167 verworfen, 0,02 < 0,025 verworfen, 0,04 < 0,05 verworfen",
          hl["a"][0] and hl["b"][0] and hl["c"][0])
    hl = W.holm({"a": 0.001, "b": 0.03, "c": 0.04})
    pruef("Holm stoppt: 0,03 ≥ 0,025 → b und c nicht verworfen", hl["a"][0] and not hl["b"][0] and not hl["c"][0])
    hl = W.holm({"a": 0.001, "b": None})
    pruef("Holm: None bleibt in der Familie (m = 2)", hl["a"][0] and abs(hl["a"][1] - 0.025) < 1e-12 and not hl["b"][0])
    # N-Familie: N4 ohne (b) mit winzigem p darf N2 nicht auf die günstigere zweite Schwelle schieben
    nf = W.netto_familie({"N2": 0.014, "N4": 0.0001, "N6": 0.2, "N8": 0.3},
                         {"N2": True, "N4": False, "N6": True, "N8": True})
    pruef("N-Familie: ohne (b) nicht verwerfbar und ohne Einfluss auf die Schwellen (N2 0,014 ≥ 0,0125)",
          not nf["N4"][0] and not nf["N2"][0] and abs(nf["N2"][1] - 0.0125) < 1e-12, nf)
    # Codex R2: N2 p = 0,007 (b erfüllt), N4 p = 0,00001 ohne (b) → maßgebliche N2-Schwelle 0,0125 → Feinziehung
    pruef("Feinziehung prüft die N-Familie mit denselben bereinigten Schwellen wie die Entscheidung",
          W.fein_noetig({}, {}, {"N2": 0.007, "N4": 0.00001, "N6": 0.3, "N8": 0.4},
                        {"N2": True, "N4": False, "N6": True, "N8": True}))
    hl = W.holm({"a": 0.03})
    pruef("Feinziehung nahe der Schwelle (0,03 bei 0,05) ja, 0,2 nein",
          W.nahe_schwelle({"a": 0.03}, hl) and not W.nahe_schwelle({"a": 0.2}, W.holm({"a": 0.2})))

    # ── 5b. Quintil gegen unabhängige Referenz (Vorgeschichte inklusive t) ───────────────────────────────────────
    print("== Quintil-Referenz")
    rng = np.random.default_rng(7)
    tq = werktage("2005-01-03", 420)
    kq, c = [], 100.0
    for i in range(420):
        s = 0.004 if (i // 60) % 2 == 0 else 0.02
        c2 = c * math.exp(rng.normal(0, s))
        kq.append((c, max(c, c2) * 1.001, min(c, c2) * 0.999, c2))
        c = c2
    rq = W.aufbereiten(reihe(tq, kq), tq)
    lrq = rq["lr"]
    ref, vor = {}, []
    for t in range(20, 420):
        rv = float(np.std(lrq[t - 19:t + 1], ddof=1))
        if len(vor) >= 250:
            alle = vor + [rv]
            unter = sum(1 for x in alle if x < rv)
            gleich = sum(1 for x in alle if x == rv)
            ref[t] = min(4, int((unter + gleich / 2) / len(alle) * 5))
        vor.append(rv)
    abw = [t for t, q in ref.items() if rq["quintil"][t] != q]
    pruef("Quintil = Referenz (Rang inklusive t) an allen Tagen", not abw and len(ref) > 100, abw[:5])

    # ── 5c. Phasentrennung und Achse ───────────────────────────────────────────────────────────────────────────
    print("== Phasentrennung")
    import gzip, json, tempfile, os
    td = werktage("2023-11-01", 80)
    rows = reihe(td, flach(80))
    i24 = next(i for i, d in enumerate(td) if d >= "2024-02-01")
    rows[i24][6] = None                                # ungültige Zeile im Prüfzeitraum
    with tempfile.TemporaryDirectory() as tmp:
        ex = Path(tmp) / "export.json.gz"
        with gzip.open(ex, "wt", encoding="utf-8") as fh:
            json.dump({"erzeugt": "x", "universum": ["T"], "sitzungen": {"NYSE": td},
                       "ticker": {"T": {"boerse": "NYSE", "rows": rows}}}, fh)
        reihen, _, _, sitz = W.export_lesen(ex, bis=W.ENTDECKUNG_BIS)
        r = reihen["T"]
        dg = W.diagnostik(reihen, "entdeckung")
        pruef("Entdeckung liest keine Zeile nach 2023-12-29 (vor der Aufbereitung gekürzt)",
              max(r["d"]) <= "2023-12-29" and "nicht_endlich" not in dg["zeilen"], (max(r["d"]), dg["zeilen"]))
        ac = W.achse_fuer(sitz, {"NYSE"}, "entdeckung")
        pruef("Achse = alle Sitzungen des Abschnitts (auch ohne Einträge)",
              list(ac) == [d for d in td if "2000-01-03" <= d <= "2023-12-29"], len(ac))
        # Einfrieren exklusiv: zweiter Aufruf darf nicht überschreiben
        alt = W.AUSGABE
        try:
            W.AUSGABE = Path(tmp)
            (Path(tmp) / "entdeckung.json").write_text(json.dumps(
                {"export_sha256": "a", "skript_sha256": "b", "universum_sha256": "c",
                 "hypothesen": {"H1": {"punkt": {"T": 0.1}, "weiter_in_pruefzeitraum": True}}}), encoding="utf-8")
            argv = sys.argv
            sys.argv = ["x", "--einfrieren", "abc"]
            W.main()
            erst = (Path(tmp) / "einfrieren.json").read_text(encoding="utf-8")
            try:
                W.main()
                zweit_ok = False
            except FileExistsError:
                zweit_ok = True
            sys.argv = argv
        finally:
            W.AUSGABE = alt
        pruef("Einfrier-Datei exklusiv: zweiter Aufruf scheitert, Inhalt unverändert",
              zweit_ok and (Path(tmp) / "einfrieren.json").read_text(encoding="utf-8") == erst)

    # ── 6. Universum ───────────────────────────────────────────────────────────────────────────────────────────
    print("== Universum")
    pruef("ohne Krypto/Devisen/Futures/Indizes",
          [t for t in ("SPY", "BTC-USD", "EURUSD=X", "GC=F", "^GSPC", "SAP.DE") if W.im_universum(t)] == ["SPY", "SAP.DE"])
    return 0


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        print("[Absturz]")
        sys.exit(3)
    print()
    if FEHLER:
        print(f"[FAIL] {len(FEHLER)} Prüfung(en): " + "; ".join(FEHLER))
        sys.exit(1)
    print("[OK] alle Prüfungen grün")
    sys.exit(0)
