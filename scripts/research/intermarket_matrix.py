#!/usr/bin/env python3
"""
intermarket_matrix.py — Wer laeuft wem voraus? Eine Matrix ueber 19 Maerkte.

    py -3.14 scripts/research/intermarket_matrix.py --json <datei>

FRAGE: Wenn Gold stark steigt — was macht danach Oel? Wenn Anleihen einbrechen
— was macht danach der Russell? Fuer jedes Paar aus 19 Handelsinstrumenten
wird gemessen, wie sich das Ziel entwickelt, NACHDEM der Signalgeber sich stark
bewegt hat.

METHODIK: identisch zu scripts/research/btc_lead_lag.py und bond_lead_lag.py,
deren Funktionen importiert statt nachgebaut werden. Kurz:
  - Signal = kumulierte Bewegung ueber 10 Handelstage
  - Schwelle = 90. Perzentil der EIGENEN Bewegungsverteilung des Signalgebers.
    Feste Prozentschwellen waeren unbrauchbar: eine 10-Tage-Bewegung liegt im
    Median bei Bitcoin bei 5,6 %, bei HYG bei 0,8 %. Ueber Perzentile ist
    "gleich selten" vergleichbar.
  - gemessen wird NUR, was nach dem Signal liegt (t+1 aufwaerts) — eine
    gleichzeitige Korrelation ist keine Prognose
  - Mindestabstand 41 Handelstage, damit die Pfade disjunkt sind
  - jede Zahl gegen die BASISRATE des Ziels, nicht gegen null

DAS EIGENTLICHE PROBLEM EINER MATRIX: sie ist ein Data-Mining-Generator. Bei
19 x 18 Paaren x 2 Richtungen sind es 684 Tests; bei p < 0,05 waeren rund 34
Zufallstreffer zu erwarten. Ein einzelner kleiner p-Wert bedeutet hier also
NICHTS. Deshalb:

  MAX-T UEBER DIE GESAMTE MATRIX. In jeder der 2000 Bootstrap-Runden wird EIN
  gemeinsamer zirkulaerer Zeitversatz gezogen und damit die GANZE Matrix neu
  gerechnet; gespeichert wird nur der groesste Effekt daraus. Die Frage lautet
  dann nicht "ist diese Zelle auffaellig?", sondern "wie oft erreicht die beste
  Zelle einer komplett zufaelligen Matrix diesen Wert?". Nur was diese Schranke
  reisst, gilt als Befund. Alles andere ist eine bunte Zelle.

  Der gemeinsame Versatz je Runde ist wichtig: er erhaelt die Abhaengigkeit
  zwischen den Paaren (XLK, SMH und IGV messen fast dasselbe). Unabhaengig
  gezogene Versaetze wuerden die Schranke zu niedrig ansetzen.

ZUSAETZLICH muss ein Befund in BEIDEN Haelften der Historie halten (vorab am
Median der gemeinsamen Handelstage geteilt). Ein Effekt, der nur in einer
Haelfte existiert, ist ein Hinweis, kein Ergebnis.

Paare mit weniger als MIN_EREIGNISSE Ereignissen werden gar nicht ausgewertet.
MAGS laeuft erst ab 04-2023 und ist deshalb nur Ziel, nie Signalgeber.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import pathlib
import random
import statistics
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

_spec = importlib.util.spec_from_file_location(
    "btc_lead_lag", str(pathlib.Path(__file__).with_name("btc_lead_lag.py")))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

from shared.data import lade_closes                                  # noqa: E402
from shared.realized_vol import log_returns                          # noqa: E402

# Name, Gruppe, und ob als Signalgeber zugelassen
MAERKTE = [
    ("GLD", "Gold", "Rohstoffe", True),
    ("SLV", "Silber", "Rohstoffe", True),
    ("USO", "Öl", "Rohstoffe", True),
    ("URA", "Uran", "Rohstoffe", True),
    ("XLE", "Energie", "Rohstoffe", True),
    ("BTC-USD", "Bitcoin", "Krypto", True),
    ("ETH-USD", "Ether", "Krypto", True),
    ("IGV", "Software", "Technologie", True),
    ("XLK", "Technologie", "Technologie", True),
    ("SMH", "Halbleiter", "Technologie", True),
    ("MAGS", "Mag 7", "Technologie", False),      # erst ab 04-2023
    ("SPY", "S&P 500", "Breiter Markt", True),
    ("QQQ", "Nasdaq 100", "Breiter Markt", True),
    ("DIA", "Dow Jones", "Breiter Markt", True),
    ("IWM", "Russell 2000", "Breiter Markt", True),
    ("TLT", "Anleihen 20J+", "Zinsen", True),
    ("HYG", "High Yield", "Zinsen", True),
    ("XLF", "Finanzen", "Sektoren", True),
    ("XLU", "Versorger", "Sektoren", True),
]

L = 10                    # Signalfenster in Handelstagen
HORIZONT = 10             # Hauptspezifikation: zwei Wochen, vorab festgelegt
PERZENTIL = 0.90
MIN_EREIGNISSE = 20       # damit eine Zelle ueberhaupt ausgewertet wird
MIN_JE_HAELFTE = 20      # damit sie als BESTAETIGT gelten darf
ABSTAND = 41
RUNDEN = 2000


def lade_alle() -> dict:
    reihen = {}
    for t, name, _, _ in MAERKTE:
        try:
            d, c = lade_closes(t, mindestens=300)
            reihen[t] = dict(zip(d, [float(x) for x in c]))
        except Exception as e:
            print("  %-8s nicht ladbar (%s)" % (t, str(e)[:40]))
    return reihen


def kum_reihe(closes: list[float]) -> list[float | None]:
    lr = log_returns(closes)
    out: list[float | None] = [None] * len(closes)
    for i in range(L, len(closes)):
        f = lr[i - L:i]
        out[i] = None if any(x is None for x in f) else sum(f)
    return out


def schwelle(closes: list[float]) -> float:
    lr = log_returns(closes)
    bew = []
    for i in range(L, len(lr)):
        f = lr[i - L:i]
        if not any(x is None for x in f):
            bew.append(abs(math.exp(sum(f)) - 1))
    bew.sort()
    return bew[int(PERZENTIL * (len(bew) - 1))] if bew else 9.99


def ereignis_indizes(kum, sw: float, richtung: str, ab: int, bis: int) -> list[int]:
    tr, letztes = [], -10 ** 9
    for i in range(ab, bis):
        k = kum[i]
        if k is None:
            continue
        bew = math.exp(k) - 1.0
        passt = (bew >= sw) if richtung == "auf" else (bew <= -sw)
        if passt and i - letztes >= ABSTAND:
            tr.append(i)
            letztes = i
    return tr


def effekt(ziel: list[float], treffer: list[int], k: int = HORIZONT,
           versatz: int = 0) -> float | None:
    """Mittlere Rendite des Ziels k Tage nach den Ereignissen, in Prozent."""
    n = len(ziel)
    w = []
    for i in treffer:
        j = (i + versatz) % n
        if j + k >= n or ziel[j] <= 0:
            continue
        w.append((ziel[j + k] / ziel[j] - 1) * 100)
    return statistics.fmean(w) if len(w) >= 5 else None


def t_wert(ziel: list[float], treffer: list[int], basis: float, streuung: float,
           k: int = HORIZONT, versatz: int = 0) -> float | None:
    """Der Effekt in Einheiten seines eigenen Standardfehlers.

    DER ENTSCHEIDENDE PUNKT DER GANZEN MATRIX. Ein erster Versuch verglich die
    Zellen ueber rohe Prozentpunkte — dabei setzten Bitcoin und Uran als Ziele
    eine Max-T-Schranke von 11 Prozentpunkten, an der kein einziger der
    ruhigeren Maerkte je vorbeikommt. Zwei Prozentpunkte bei SPY und zwei bei
    Bitcoin sind nicht dieselbe Aussage: der eine Markt schwankt in zwei Wochen
    um zwei Prozent, der andere um zwanzig.

    Verglichen wird deshalb der standardisierte Effekt: Ueberschuss geteilt
    durch den Standardfehler des Mittelwerts. Damit sind die Zellen
    untereinander vergleichbar, und eine Max-T-Schranke gilt fuer alle gleich.
    """
    e = effekt(ziel, treffer, k, versatz)
    if e is None or streuung <= 0:
        return None
    m = max(5, len(treffer))
    return (e - basis) / (streuung / math.sqrt(m))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()

    print("INTERMARKET-MATRIX — wer läuft wem voraus?")
    print("Signal: 10-Tage-Bewegung über dem 90. Perzentil des jeweiligen Marktes.")
    print("Gemessen: das Ziel %d Handelstage SPÄTER (zwei Wochen), gegen seine Basisrate."
          % HORIZONT)
    print()
    reihen = lade_alle()
    vorhanden = [(t, n, g, s) for t, n, g, s in MAERKTE if t in reihen]
    print("%d Märkte geladen." % len(vorhanden))

    # Paare vorbereiten: je Paar die eigene Schnittmenge der Handelstage.
    # Ein gemeinsames Fenster für alle würde die Historie auf MAGS (2023)
    # zusammenstauchen und 20 Jahre wegwerfen.
    zellen = []
    for st, sn, sg, darf in vorhanden:
        if not darf:
            continue
        for zt, zn, zg, _ in vorhanden:
            if zt == st:
                continue
            tage = sorted(set(reihen[st]) & set(reihen[zt]))
            if len(tage) < 500:
                continue
            sig = [reihen[st][d] for d in tage]
            ziel = [reihen[zt][d] for d in tage]
            kum = kum_reihe(sig)
            sw = schwelle(sig)
            haelfte = len(tage) // 2
            for richtung in ("auf", "ab"):
                tr = ereignis_indizes(kum, sw, richtung, L + 5, len(tage))
                tr = [i for i in tr if i + HORIZONT < len(tage)]
                if len(tr) < MIN_EREIGNISSE:
                    continue
                bas = [(ziel[i + HORIZONT] / ziel[i] - 1) * 100
                       for i in range(len(ziel) - HORIZONT) if ziel[i] > 0]
                streuung = statistics.pstdev(bas) if len(bas) > 2 else 0.0
                zellen.append({
                    "streuung_pct": round(streuung, 3),
                    # PRIMAERFAMILIE = nur Paare ueber Kategoriegrenzen hinweg.
                    # SPY->DIA, XLK->SMH oder Bitcoin->Ether sind keine
                    # eigenstaendigen Intermarket-Hypothesen: sie messen
                    # weitgehend denselben Faktor und blaehen die Testfamilie
                    # auf, ohne eine neue Frage zu stellen. Sie werden weiter
                    # gerechnet und angezeigt, gelten aber als Replikations-
                    # zellen und koennen keinen Befund stiften.
                    # Die Regel trennt nach KATEGORIE, nicht nach gemessener
                    # Korrelation — sonst waere die Verkleinerung der Familie
                    # selbst wieder Data Mining.
                    "primaer": sg != zg,
                    "signal": st, "signal_name": sn, "signal_gruppe": sg,
                    "ziel": zt, "ziel_name": zn, "ziel_gruppe": zg,
                    "richtung": richtung, "n": len(tr),
                    # Zeitraum und Umfang je Zelle. Codex hat darauf bestanden,
                    # und zu Recht: die Zellen haben VERSCHIEDENE Historien
                    # (Uran ab 2010, Ether ab 2017), also ist eine Zelle mit
                    # 6000 Beobachtungen nicht so belastbar wie eine mit 1200 —
                    # und ohne die Angabe sieht man das in der Tabelle nicht.
                    "von": tage[0], "bis": tage[-1], "beob": len(tage),
                    "schwelle_pct": round(sw * 100, 2),
                    "basis_pct": round(statistics.fmean(bas), 3),
                    "_ziel": ziel, "_tr": tr, "_haelfte": haelfte,
                })
    print("%d auswertbare Zellen (mindestens %d Ereignisse)." % (len(zellen), MIN_EREIGNISSE))
    if not zellen:
        return 1

    # Beobachtete Effekte
    for z in zellen:
        e = effekt(z["_ziel"], z["_tr"])
        z["effekt_pct"] = round(e, 3) if e is not None else None
        z["ueberschuss_pp"] = (round(e - z["basis_pct"], 3)
                               if e is not None else None)
        tw = t_wert(z["_ziel"], z["_tr"], z["basis_pct"], z["streuung_pct"])
        z["t_wert"] = round(tw, 3) if tw is not None else None
        # beide Haelften, vorab am Median der Handelstage geteilt
        for label, aus in (("h1", [i for i in z["_tr"] if i < z["_haelfte"]]),
                           ("h2", [i for i in z["_tr"] if i >= z["_haelfte"]])):
            eh = effekt(z["_ziel"], aus) if len(aus) >= 5 else None
            z[label + "_pp"] = (round(eh - z["basis_pct"], 3)
                                if eh is not None else None)
            z[label + "_n"] = len(aus)

    # ── Max-T über die GESAMTE Matrix ───────────────────────────────────────
    # Je Runde EIN gemeinsamer Versatz für alle Zellen: das erhält die
    # Abhängigkeit zwischen den Paaren. Gespeichert wird nur das Maximum.
    primaer = [z for z in zellen if z["primaer"]]
    print("Max-T über die Primärfamilie (%d von %d Zellen), %d Runden ..."
          % (len(primaer), len(zellen), RUNDEN), flush=True)
    rnd = random.Random(20260922)
    maxima = []
    for r in range(RUNDEN):
        versatz = rnd.randrange(1000, 100000)
        groesstes = 0.0
        for z in primaer:
            tw = t_wert(z["_ziel"], z["_tr"], z["basis_pct"], z["streuung_pct"],
                        versatz=versatz)
            if tw is not None:
                groesstes = max(groesstes, abs(tw))
        maxima.append(groesstes)
        if (r + 1) % 400 == 0:
            print("   %d/%d" % (r + 1, RUNDEN), flush=True)
    maxima.sort()

    def p_max(wert: float) -> float:
        """Anteil der Zufallsmatrizen, deren BESTE Zelle mindestens so gross war."""
        return (sum(1 for x in maxima if x >= abs(wert)) + 1) / (len(maxima) + 1)

    schranke = maxima[int(0.95 * (len(maxima) - 1))]
    print()
    print("Max-T-Schranke (95 %%): der standardisierte Effekt muss |t| > %.2f" % schranke)
    print("erreichen — so gross wird die beste Zelle einer rein zufaelligen Matrix")
    print("in 5 %% der Faelle. Ohne Korrektur fuer die %d Tests laege die Schwelle"
          % len(primaer))
    print("bei |t| = 1,96.")

    for z in zellen:
        u, tw = z["ueberschuss_pp"], z["t_wert"]
        z["p_max_t"] = round(p_max(tw), 4) if tw is not None else None
        z["haelt_beide"] = bool(
            u is not None and z.get("h1_pp") is not None and z.get("h2_pp") is not None
            and (z["h1_pp"] > 0) == (u > 0) and (z["h2_pp"] > 0) == (u > 0))
        # Ein Befund muss VIER Huerden nehmen, nicht eine:
        #   1. in der Primaerfamilie liegen (Frage ueber Kategoriegrenzen)
        #   2. die Max-T-Schranke reissen (Korrektur fuer die ganze Familie)
        #   3. in beiden Zeithaelften dasselbe Vorzeichen zeigen
        #   4. in JEDER Haelfte genug Ereignisse haben — 20 insgesamt heisst
        #      schlimmstenfalls 3 in der einen Haelfte, und "haelt beide
        #      Haelften" waere dann eine Aussage ueber 3 Faelle.
        genug = (z.get("h1_n", 0) >= MIN_JE_HAELFTE
                 and z.get("h2_n", 0) >= MIN_JE_HAELFTE)
        z["genug_je_haelfte"] = bool(genug)
        z["befund"] = bool(z["primaer"] and tw is not None
                           and abs(tw) > schranke and z["haelt_beide"] and genug)
        for k in ("_ziel", "_tr", "_haelfte"):
            z.pop(k, None)

    befunde = sorted([z for z in zellen if z["befund"]],
                     key=lambda z: -abs(z["ueberschuss_pp"]))
    knapp = sorted([z for z in zellen if not z["befund"] and z["t_wert"]
                    and abs(z["t_wert"]) > max(1.96, schranke * 0.7)],
                   key=lambda z: -abs(z["t_wert"]))
    for z in zellen:
        z["status"] = ("bestaetigt" if z["befund"]
                       else "hinweis" if (z["t_wert"] is not None
                                          and abs(z["t_wert"]) > 1.96)
                       else "unauffaellig")

    print()
    print("=" * 78)
    print("BEFUNDE: %d von %d Zellen der Primärfamilie halten alle vier Hürden"
          % (len(befunde), len(primaer)))
    print("=" * 78)
    if befunde:
        print("  %-20s %-20s %-6s %4s %9s %9s %6s %8s"
              % ("wenn ...", "dann ...", "Rtg", "n", "Ziel", "Basis", "t", "p(MaxT)"))
        for z in befunde[:25]:
            print("  %-20s %-20s %-6s %4d %+8.2f %% %+8.2f %% %6.2f %8.3f"
                  % (z["signal_name"], z["ziel_name"],
                     "hoch" if z["richtung"] == "auf" else "runter",
                     z["n"], z["effekt_pct"], z["basis_pct"], z["t_wert"],
                     z["p_max_t"]))
    else:
        print("  Keine. Das ist ein Ergebnis: über 19 Märkte und zwei Richtungen")
        print("  bleibt nach ehrlicher Korrektur für die Zahl der Tests nichts übrig.")

    if knapp:
        print()
        print("KNAPP DARUNTER (Hinweise, keine Befunde) — %d Zellen:" % len(knapp))
        for z in knapp[:10]:
            print("  %-19s %-19s %-6s n=%-3d(%2d/%2d) %+6.2f pp t=%5.2f %s%s"
                  % (z["signal_name"], z["ziel_name"],
                     "hoch" if z["richtung"] == "auf" else "runter",
                     z["n"], z.get("h1_n", 0), z.get("h2_n", 0),
                     z["ueberschuss_pp"], z["t_wert"],
                     "beide" if z["haelt_beide"] else "EINE",
                     "" if z["primaer"] else " REPLIKATION"))

    if a.json:
        pathlib.Path(a.json).write_text(json.dumps({
            "stand": "2026-09-22", "horizont_tage": HORIZONT,
            "signalfenster_tage": L, "perzentil": PERZENTIL,
            "min_ereignisse": MIN_EREIGNISSE,
            "min_je_haelfte": MIN_JE_HAELFTE,
            "primaerfamilie": len(primaer), "runden": RUNDEN,
            "max_t_schranke_t": round(schranke, 3),
            "n_zellen": len(zellen), "n_befunde": len(befunde),
            "zellen": zellen}, ensure_ascii=False, indent=2), encoding="utf-8")
        print()
        print("JSON: %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
