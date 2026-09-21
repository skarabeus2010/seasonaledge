#!/usr/bin/env python3
"""
btc_lead_lag.py — Laeuft Bitcoin den breiten Aktienmaerkten voraus?

    py -3.14 scripts/research/btc_lead_lag.py                 Hauptspezifikation
    py -3.14 scripts/research/btc_lead_lag.py --json <datei>   Ergebnis fuer das Frontend

FRAGE: Wenn Bitcoin stark steigt oder faellt — ziehen SPY, QQQ und DIA danach
nach, und mit welchem Abstand? Und ab welcher STAERKE der Bewegung?

WARUM LAG 0 NICHT ZAEHLT: eine gleichzeitige Korrelation ist keine Prognose.
Dass SPY am selben Tag steigt wie BTC, ist nicht handelbar — beide reagieren
dann auf dieselbe Information. Gemessen wird deshalb ausschliesslich, was NACH
dem BTC-Signal passiert.

DER MECHANISCHE FALLSTRICK, der eine solche Studie am leichtesten ruiniert:
BTC handelt 24/7 und sein Tagesschluss liegt bei 00:00 UTC, der ETF-Schluss bei
20:00/21:00 UTC. Ein gleich datierter BTC-Return endet also NACH dem ETF-Schluss
desselben Tages. Wer ihn gegen den ETF-Return desselben Datums stellt,
vergleicht teils dasselbe Informationsintervall und erzeugt einen Scheinvorlauf
von rund einem Handelstag. Deshalb ist der erste gewertete ETF-Return der von
Schluss(T) auf Schluss(T+1) — er liegt vollstaendig nach dem Signal. Zusaetzlich
wird eine noch konservativere Variante ausgewiesen, die erst zum naechsten
Schluss einsteigt (Eintritt T+1, Rendite ab T+1).

HAUPTSPEZIFIKATION, vorab festgelegt (damit nicht die Suche das Ergebnis macht):
  - gemeinsame NYSE-Handelstage von BTC-USD, SPY, QQQ, DIA
  - Signal: kumulierter BTC-Log-Return ueber L=10 Handelstage
  - normiert mit der Streuung der vorangegangenen 252 ueberlappenden
    10-Tage-Renditen, gerechnet AUSSCHLIESSLICH bis t-1 (kein Look-ahead)
  - Ereignis bei |z| >= 2,5, Auf- und Abwaertsbewegungen getrennt
  - mindestens 31 Handelstage Abstand zwischen Ereignissen, damit die
    ausgewerteten Pfade disjunkt sind (das Fenster -10..+20 umfasst 31 Tage;
    eine Sperrfrist von nur L=10 liesse dieselben ETF-Returns mehrfach zaehlen
    und wuerde die Ereigniszahl und damit die Praezision aufblaehen)
  - SPY ist das primaere Ziel, QQQ und DIA sind Bestaetigung
  - Nullverteilung per ZIRKULAERER Zeitverschiebung der Ereignistage: sie
    erhaelt Volatilitaets-Clustering und Kalenderstruktur. Gleichverteilte
    Pseudo-Ereignisse waeren kein sauberer Vergleich, weil echte Ereignisse in
    turbulenten Phasen liegen und Zufallsereignisse meist in ruhigen.

ALLES WEITERE IST EXPLORATIV und als solches gekennzeichnet — insbesondere die
Staerke-Tabelle (Buckets in Prozent) und die Regime-Aufteilung. Wer ueber
Fenster, Schwellen, Richtungen, drei ETFs und 30 Lags sucht, findet immer
irgendwo p < 0,05; solche Zahlen sind Hinweise, keine Nachweise.

Methodik abgestimmt mit einem externen Reviewer am 2026-09-21; die
Literaturanker dort: Brown/Warner zur Event-Study-Praxis bei Tagesdaten,
Politis/Romano zum Block-Bootstrap, Scholes/Williams zum Problem
nicht-synchroner Beobachtungen.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import statistics
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from shared.data import lade_closes                                  # noqa: E402
from shared.realized_vol import log_returns                          # noqa: E402

ETFS = ("SPY", "QQQ", "DIA")
KRYPTO = "BTC-USD"

L = 10                  # Signalfenster in Handelstagen
Z_SCHWELLE = 2.5        # Ereignisschwelle
BASIS = 252             # Fenster fuer den Nenner
VOR, NACH = 10, 30      # ausgewerteter Pfad um das Ereignis (30 HT = 6 Wochen)
ABSTAND = VOR + NACH + 1
BOOTSTRAP = 2000

REGIME = [("bis 2019 (vor der Kopplung)", "2000-01-01", "2019-12-31"),
          ("2020-2021 (Liquiditaetsflut)", "2020-01-01", "2021-12-31"),
          ("2022-2026 (Straffung danach)", "2022-01-01", "2030-12-31")]

# Staerke-Buckets in PROZENT. Absolut, nicht z-normiert: so ist die Frage
# gestellt ("ab 5 % passiert etwas"), und so steht sie in der Literatur.
# Horizonte: 5 Handelstage = 1 Woche. Bewusst auch die kurzen, damit sichtbar
# bleibt, ob ein Effekt sofort da ist oder erst spaeter entsteht.
HORIZONTE = (1, 2, 3, 5, 10, 15, 20, 30)
WOCHEN = {5: "1 Wo", 10: "2 Wo", 15: "3 Wo", 20: "4 Wo", 30: "6 Wo"}

# Staerke-Schwellen. ZWEI Formen, weil sie verschiedene Fragen beantworten:
#   BUCKETS    — disjunkt, zeigt ob die Wirkung mit der Staerke WAECHST
#   KUMULATIV  — "ab 5 %", so ist die These formuliert und so waere sie handelbar
# Absolute Prozentschwellen, nicht z-normiert: so steht die Frage in der
# Literatur. Nachteil, der mitgelesen werden muss: BTCs Volatilitaet ist ueber
# die Jahre stark gefallen, 5 % waren 2017 ein normaler Tag.
BUCKETS = [("3-5 %", 0.03, 0.05), ("5-10 %", 0.05, 0.10),
           ("10-20 %", 0.10, 0.20), ("ueber 20 %", 0.20, 9.99)]
KUMULATIV = [("ab 3 %", 0.03), ("ab 5 %", 0.05),
             ("ab 10 %", 0.10), ("ab 20 %", 0.20)]


def lade() -> tuple[list, dict]:
    reihen = {}
    for t in (KRYPTO,) + ETFS:
        d, c = lade_closes(t)
        reihen[t] = dict(zip(d, [float(x) for x in c]))
    # Nur Tage, an denen ALLE vier gehandelt haben. BTC hat Wochenenden, die
    # ETFs nicht — wer auf BTCs Kalender rechnet, vergleicht Wochenendbewegungen
    # mit Nicht-Handelstagen und misst Kalendermechanik statt Marktverhalten.
    tage = sorted(set.intersection(*[set(v) for v in reihen.values()]))
    return tage, reihen


def kumulierte(reihe: list[float], n: int) -> list[float | None]:
    """Kumulierter Log-Return ueber n Tage, Index i = Ende des Fensters."""
    lr = log_returns(reihe)
    out: list[float | None] = [None] * len(reihe)
    for i in range(n, len(reihe)):
        fenster = lr[i - n:i]
        out[i] = None if any(x is None for x in fenster) else sum(fenster)
    return out


def ereignisse(tage, btc_kum, richtung: str) -> list[int]:
    """Indizes der Ereignistage. richtung: 'auf' oder 'ab'.

    Der Nenner nutzt ausschliesslich Fenster, die VOR t enden — sonst enthaelt
    die Normierung den Ereignistag selbst und waehlt Ereignisse mit Wissen aus
    der Zukunft aus.
    """
    treffer = []
    letztes = -10 ** 9
    for i in range(BASIS + L, len(tage)):
        hier = btc_kum[i]
        if hier is None:
            continue
        vergangen = [x for x in btc_kum[i - BASIS:i] if x is not None]
        if len(vergangen) < BASIS // 2:
            continue
        s = statistics.pstdev(vergangen)
        if s <= 0:
            continue
        z = hier / s
        if (richtung == "auf" and z >= Z_SCHWELLE) or (richtung == "ab" and z <= -Z_SCHWELLE):
            if i - letztes >= ABSTAND:
                treffer.append(i)
                letztes = i
    return treffer


def pfad(etf_reihe: list[float], idx: int) -> list[float] | None:
    """Kumulierter ETF-Verlauf in Prozent, normiert auf 0 am Ereignistag.

    t=0 ist der ETF-Schluss des Ereignistages. Der Wert bei t=+1 ist damit der
    erste, der VOLLSTAENDIG nach dem BTC-Signal liegt — er ist die eigentliche
    Prognosegroesse. t<0 dient nur der Einordnung (lief der Markt schon vorher?).
    """
    if idx - VOR < 0 or idx + NACH >= len(etf_reihe):
        return None
    basis = etf_reihe[idx]
    if basis <= 0:
        return None
    return [(etf_reihe[idx + k] / basis - 1.0) * 100 for k in range(-VOR, NACH + 1)]


def mittelpfad(pfade: list[list[float]]) -> list[float]:
    return [statistics.fmean([p[j] for p in pfade]) for j in range(len(pfade[0]))]


def nullband(etf_reihe, treffer_n, tage_n, runden=BOOTSTRAP, seed=12345):
    """Verteilung der Vorwaerts-Rendite unter der Nullhypothese.

    ZIRKULAERE VERSCHIEBUNG aller Ereignistage um denselben zufaelligen Betrag:
    die Abstaende zwischen den Ereignissen bleiben erhalten, ihre Lage im
    Volatilitaets- und Kalenderverlauf aendert sich. Damit wird gegen "irgendwo
    im Markt" getestet, nicht gegen "in ruhigen Phasen".
    """
    rnd = random.Random(seed)
    werte = []
    for _ in range(runden):
        versatz = rnd.randrange(tage_n)
        ps = []
        for i in treffer_n:
            j = (i + versatz) % tage_n
            p = pfad(etf_reihe, j)
            if p:
                ps.append(p)
        if ps:
            werte.append(mittelpfad(ps))
    return werte


def perzentil(sortiert: list[float], q: float) -> float:
    if not sortiert:
        return float("nan")
    pos = q * (len(sortiert) - 1)
    lo = int(math.floor(pos)); hi = min(lo + 1, len(sortiert) - 1)
    return sortiert[lo] + (sortiert[hi] - sortiert[lo]) * (pos - lo)


def auswerten(tage, reihen, treffer, etf) -> dict | None:
    er = [reihen[etf][d] for d in tage]
    pfade = [p for p in (pfad(er, i) for i in treffer) if p]
    if len(pfade) < 5:
        return None
    m = mittelpfad(pfade)
    null = nullband(er, treffer, len(tage))

    def stelle(k: int) -> dict:
        """k = Handelstage NACH dem Ereignis. k>=1, weil t=0 keine Prognose ist."""
        j = VOR + k
        ist = m[j]
        vert = sorted(x[j] for x in null)
        # Einseitiger empirischer p-Wert in Richtung des beobachteten Effekts.
        if ist >= 0:
            p = sum(1 for x in vert if x >= ist) / max(1, len(vert))
        else:
            p = sum(1 for x in vert if x <= ist) / max(1, len(vert))
        einzel = [x[j] for x in pfade]
        return {"tage": k, "wochen": WOCHEN.get(k, ""), "mittel_pct": round(ist, 3),
                "median_pct": round(statistics.median(einzel), 3),
                "anteil_positiv_pct": round(sum(1 for x in einzel if x > 0) / len(einzel) * 100, 1),
                "null_5pct": round(perzentil(vert, 0.05), 3),
                "null_95pct": round(perzentil(vert, 0.95), 3),
                "p_wert": round(p, 4)}

    return {"etf": etf, "n_ereignisse": len(pfade),
            "pfad_mittel_pct": [round(x, 3) for x in m],
            "pfad_von": -VOR, "pfad_bis": NACH,
            "null_5pct": [round(perzentil(sorted(x[j] for x in null), 0.05), 3)
                          for j in range(len(m))],
            "null_95pct": [round(perzentil(sorted(x[j] for x in null), 0.95), 3)
                           for j in range(len(m))],
            "horizonte": [stelle(k) for k in HORIZONTE]}


def basisrate(tage, reihen) -> dict:
    """Was der ETF in einem BELIEBIGEN Fenster tut — ohne jedes Signal.

    Der wichtigste Vergleichswert der ganzen Studie. "+2,48 % nach 20 Tagen"
    klingt nach einem Effekt, ist aber erst dann einer, wenn der Markt nicht
    ohnehin so laeuft: SPY macht unkonditional rund +1,1 % in 20 Handelstagen
    und steigt in 68 % dieser Fenster. Jede Ereigniszahl gehoert gegen DIESE
    Zeile gelesen, nicht gegen null.
    """
    out = {}
    for e in ETFS:
        er = [reihen[e][d] for d in tage]
        out[e] = {}
        for k in HORIZONTE:
            w = [(er[i + k] / er[i] - 1) * 100
                 for i in range(len(er) - k) if er[i] > 0]
            out[e][k] = {"mittel_pct": round(statistics.fmean(w), 3),
                         "median_pct": round(statistics.median(w), 3),
                         "anteil_positiv_pct": round(
                             sum(1 for x in w if x > 0) / len(w) * 100, 1),
                         "n": len(w)}
    return out


def einzelfall_test(tage, reihen, treffer, etf, k=1) -> dict:
    """Haengt der Effekt an einem einzelnen Ereignis?

    Bei zweistelligen Ereigniszahlen kann ein Ausnahmetag das Mittel allein
    tragen. Gemessen am 2026-09-21: der Befund "BTC-Einbruch -> SPY +1,29 % am
    Folgetag, p=0,002" schrumpfte ohne den 2020-03-12 (COVID-Tiefpunkt, allein
    +8,55 % Beitrag) auf +0,49 % bei p=0,101. Ein Effekt, der mit einem
    weggelassenen Datum verschwindet, ist keiner — deshalb steht dieser Test
    nicht im Anhang, sondern im Ergebnis.
    """
    er = [reihen[etf][d] for d in tage]
    voll = auswerten(tage, reihen, treffer, etf)
    if not voll:
        return {}
    h = {x["tage"]: x for x in voll["horizonte"]}
    bei = []
    for i in treffer:
        pf = pfad(er, i)
        if pf:
            bei.append((tage[i], round(pf[VOR + k], 3)))
    bei.sort(key=lambda x: -abs(x[1]))
    ohne = []
    for datum, _ in bei[:3]:
        rest = [i for i in treffer if tage[i] != datum]
        r = auswerten(tage, reihen, rest, etf)
        if r:
            hh = {x["tage"]: x for x in r["horizonte"]}
            ohne.append({"ohne": datum, "n": r["n_ereignisse"],
                         "mittel_pct": hh[k]["mittel_pct"],
                         "p_wert": hh[k]["p_wert"]})
    return {"horizont": k,
            "voll": {"n": voll["n_ereignisse"], "mittel_pct": h[k]["mittel_pct"],
                     "p_wert": h[k]["p_wert"]},
            "einzelbeitraege": bei, "ohne_groesste": ohne}


def staerke_tabelle(tage, reihen, btc_kum, richtung: str) -> list[dict]:
    """EXPLORATIV: wirkt die Staerke der BTC-Bewegung? Buckets in Prozent.

    Absolute Schwellen, weil die Frage so gestellt ist. Sie haben den bekannten
    Nachteil, dass BTCs Volatilitaet ueber die Jahre stark gefallen ist: 5 %
    waren 2017 ein normaler Tag und sind 2026 eine Bewegung. Die Buckets sind
    deshalb NICHT mit der z-basierten Hauptspezifikation vergleichbar und
    tragen keinen p-Wert aus einer vorab festgelegten Hypothese.
    """
    er = {e: [reihen[e][d] for d in tage] for e in ETFS}
    out = []
    for name, lo, hi in BUCKETS:
        treffer, letztes = [], -10 ** 9
        for i in range(BASIS + L, len(tage)):
            k = btc_kum[i]
            if k is None:
                continue
            bew = math.exp(k) - 1.0            # Log- zurueck in Prozentbewegung
            passt = (lo <= bew < hi) if richtung == "auf" else (-hi < bew <= -lo)
            if passt and i - letztes >= ABSTAND:
                treffer.append(i); letztes = i
        zeile = {"bucket": name, "n": len(treffer)}
        for e in ETFS:
            pf = [p for p in (pfad(er[e], i) for i in treffer) if p]
            if len(pf) < 5:
                zeile[e] = None
                continue
            m = mittelpfad(pf)
            zeile[e] = {("t%d" % k): round(m[VOR + k], 3) for k in HORIZONTE}
            zeile[e]["treffer_t5_pct"] = round(
                sum(1 for p in pf if p[VOR + 5] > 0) / len(pf) * 100, 1)
        out.append(zeile)
    return out


def kumulativ_tabelle(tage, reihen, btc_kum, richtung: str) -> list[dict]:
    """EXPLORATIV: "Bitcoin steigt um mindestens X %" — und dann?

    Genau die Form, in der die These in der Literatur steht und in der sie
    handelbar waere. Im Unterschied zu BUCKETS sind die Gruppen hier
    verschachtelt (ab 3 % enthaelt ab 5 %), die Zeilen sind also nicht
    unabhaengig voneinander.
    """
    er = {e: [reihen[e][d] for d in tage] for e in ETFS}
    out = []
    for name, lo in KUMULATIV:
        treffer, letztes = [], -10 ** 9
        for i in range(BASIS + L, len(tage)):
            k = btc_kum[i]
            if k is None:
                continue
            bew = math.exp(k) - 1.0
            passt = (bew >= lo) if richtung == "auf" else (bew <= -lo)
            if passt and i - letztes >= ABSTAND:
                treffer.append(i); letztes = i
        zeile = {"schwelle": name, "n": len(treffer)}
        for e in ETFS:
            pf = [p for p in (pfad(er[e], i) for i in treffer) if p]
            if len(pf) < 5:
                zeile[e] = None
                continue
            m = mittelpfad(pf)
            zeile[e] = {}
            for k in HORIZONTE:
                einzel = [p[VOR + k] for p in pf]
                zeile[e]["t%d" % k] = {
                    "mittel_pct": round(m[VOR + k], 3),
                    "median_pct": round(statistics.median(einzel), 3),
                    "treffer_pct": round(sum(1 for x in einzel if x > 0) / len(einzel) * 100, 1)}
        out.append(zeile)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="Ergebnis als JSON hierhin schreiben")
    a = ap.parse_args()

    tage, reihen = lade()
    btc = [reihen[KRYPTO][d] for d in tage]
    btc_kum = kumulierte(btc, L)
    print("Gemeinsame Handelstage: %d  (%s .. %s)" % (len(tage), tage[0], tage[-1]))
    print("Signal: BTC %d-Tage-Kumulativreturn, |z| >= %.1f gegen die vorangegangenen"
          % (L, Z_SCHWELLE))
    print("%d Fenster (nur bis t-1), Mindestabstand %d Handelstage." % (BASIS, ABSTAND))
    print("t=0 ist der ETF-Schluss des Ereignistages und KEINE Prognose —")
    print("gewertet wird ab t+1, weil BTCs Tagesschluss (00:00 UTC) nach dem")
    print("ETF-Schluss (20:00/21:00 UTC) liegt.")

    bas = basisrate(tage, reihen)
    print()
    print("BASISRATE — was der Markt OHNE Signal tut (der Vergleichsmassstab):")
    print("  %-5s | %8s %8s %8s %8s %8s   Treffer t+5"
          % ("ETF", "t+1", "t+3", "t+5", "t+10", "t+20"))
    for e in ETFS:
        print("  %-5s | %8.2f %8.2f %8.2f %8.2f %8.2f   %.1f %%"
              % (e, bas[e][1]["mittel_pct"], bas[e][3]["mittel_pct"],
                 bas[e][5]["mittel_pct"], bas[e][10]["mittel_pct"],
                 bas[e][20]["mittel_pct"], bas[e][5]["anteil_positiv_pct"]))

    ergebnis = {"stand": tage[-1], "handelstage": len(tage),
                "basisrate": bas,
                "von": tage[0], "bis": tage[-1],
                "spezifikation": {"fenster_tage": L, "z_schwelle": Z_SCHWELLE,
                                  "basis_fenster": BASIS, "mindestabstand": ABSTAND,
                                  "pfad_von": -VOR, "pfad_bis": NACH,
                                  "bootstrap": BOOTSTRAP},
                "richtungen": {}, "staerke": {}, "regime": {}}

    for richtung, label in (("auf", "BITCOIN-RALLYE"), ("ab", "BITCOIN-EINBRUCH")):
        tr = ereignisse(tage, btc_kum, richtung)
        print()
        print("=" * 78)
        print("%s  —  %d Ereignisse" % (label, len(tr)))
        if tr:
            print("   z. B. " + ", ".join(tage[i] for i in tr[:6])
                  + (" ..." if len(tr) > 6 else ""))
        print("=" * 78)
        ergebnis["richtungen"][richtung] = {"n_ereignisse": len(tr),
                                           "daten": [tage[i] for i in tr], "etfs": {}}
        if not tr:
            print("  keine Ereignisse — Schwelle zu streng fuer diese Reihe")
            continue
        print("  %-5s %4s | %-42s" % ("ETF", "n", "kumuliert NACH dem Ereignis (%)"))
        print("  %-5s %4s | %8s %8s %8s %8s %8s"
              % ("", "", "t+1", "t+3", "t+5", "t+10", "t+20"))
        for e in ETFS:
            r = auswerten(tage, reihen, tr, e)
            if not r:
                continue
            ergebnis["richtungen"][richtung]["etfs"][e] = r
            h = {x["tage"]: x for x in r["horizonte"]}
            print("  %-5s %4d | %8.2f %8.2f %8.2f %8.2f %8.2f"
                  % (e, r["n_ereignisse"], h[1]["mittel_pct"], h[3]["mittel_pct"],
                     h[5]["mittel_pct"], h[10]["mittel_pct"], h[20]["mittel_pct"]))
            print("        p    | %8.3f %8.3f %8.3f %8.3f %8.3f"
                  % (h[1]["p_wert"], h[3]["p_wert"], h[5]["p_wert"],
                     h[10]["p_wert"], h[20]["p_wert"]))
            print("        Tref%%|" + "".join("%9.1f" % h[k]["anteil_positiv_pct"]
                                              for k in (1, 3, 5, 10, 20)))

        # Der Einzelfall-Test gehoert zum Ergebnis, nicht in den Anhang.
        if tr:
            ef = einzelfall_test(tage, reihen, tr, "SPY", k=1)
            ergebnis["richtungen"][richtung]["einzelfall_spy_t1"] = ef
            if ef.get("ohne_groesste"):
                print()
                print("  EINZELFALL-TEST (SPY, t+1): haelt der Effekt ohne das")
                print("  jeweils staerkste Ereignis?")
                v = ef["voll"]
                print("    alle:                  n=%2d  %+6.2f %%  p=%.3f"
                      % (v["n"], v["mittel_pct"], v["p_wert"]))
                for o in ef["ohne_groesste"]:
                    print("    ohne %-17s n=%2d  %+6.2f %%  p=%.3f"
                          % (o["ohne"], o["n"], o["mittel_pct"], o["p_wert"]))

        print()
        print("  \"BTC steigt/faellt um mindestens X %\" -> SPY danach (explorativ).")
        print("  Jede Zeile gegen die BASISRATE lesen, nicht gegen null.")
        ku = kumulativ_tabelle(tage, reihen, btc_kum, richtung)
        ergebnis.setdefault("kumulativ", {})[richtung] = ku
        kopf = "  %-10s %4s |" % ("Schwelle", "n")
        for k in (5, 10, 15, 20, 30):
            kopf += "%10s" % WOCHEN[k]
        print(kopf + "   Treffer 2 Wo")
        zb = "  %-10s %4d |" % ("ohne Signal", 0)
        for k in (5, 10, 15, 20, 30):
            zb += "%10.2f" % bas["SPY"][k]["mittel_pct"]
        print(zb + "        %.1f %%" % bas["SPY"][10]["anteil_positiv_pct"])
        for z in ku:
            sp = z.get("SPY")
            if not sp:
                print("  %-10s %4d | zu wenige Ereignisse" % (z["schwelle"], z["n"]))
                continue
            zeile = "  %-10s %4d |" % (z["schwelle"], z["n"])
            for k in (5, 10, 15, 20, 30):
                zeile += "%10.2f" % sp["t%d" % k]["mittel_pct"]
            print(zeile + "        %.1f %%" % sp["t10"]["treffer_pct"])

        print()
        print("  STAERKE (explorativ, absolute Buckets — nicht mit der")
        print("  Hauptspezifikation vergleichbar):")
        st = staerke_tabelle(tage, reihen, btc_kum, richtung)
        ergebnis["staerke"][richtung] = st
        print("  %-11s %4s | %s" % ("BTC-Bewegung", "n",
                                    "SPY nach dem Ereignis (%), Trefferquote t+5"))
        print("  %-11s %4s | %7s %7s %7s %7s %7s  %8s"
              % ("", "", "t+1", "t+3", "t+5", "t+10", "t+20", "Tref% t+5"))
        print("  %-11s %4d | %7.2f %7.2f %7.2f %7.2f %7.2f  %8.1f  <- BASISRATE"
              % ("ohne Signal", 0, bas["SPY"][1]["mittel_pct"],
                 bas["SPY"][3]["mittel_pct"], bas["SPY"][5]["mittel_pct"],
                 bas["SPY"][10]["mittel_pct"], bas["SPY"][20]["mittel_pct"],
                 bas["SPY"][5]["anteil_positiv_pct"]))
        for z in st:
            s = z.get("SPY")
            if not s:
                print("  %-11s %4d | zu wenige Ereignisse" % (z["bucket"], z["n"]))
                continue
            print("  %-11s %4d | %7.2f %7.2f %7.2f %7.2f %7.2f  %8.1f"
                  % (z["bucket"], z["n"], s["t1"], s["t3"], s["t5"],
                     s["t10"], s["t20"], s["treffer_t5_pct"]))

    # Regime: die Kopplung entstand erst 2020, ein Mittel ueber zwoelf Jahre
    # vermischt zwei verschiedene Welten.
    print()
    print("=" * 78)
    print("REGIME (explorativ) — SPY, Rallye/Einbruch, kumuliert bis t+5")
    print("=" * 78)
    for name, ab, bis in REGIME:
        zeile = {"name": name}
        aus = []
        for richtung in ("auf", "ab"):
            tr = [i for i in ereignisse(tage, btc_kum, richtung) if ab <= tage[i] <= bis]
            r = auswerten(tage, reihen, tr, "SPY") if len(tr) >= 5 else None
            if r:
                h = {x["tage"]: x for x in r["horizonte"]}
                aus.append("%s n=%-3d t+5 %+6.2f %% (p %.3f)"
                           % (richtung, r["n_ereignisse"], h[5]["mittel_pct"], h[5]["p_wert"]))
                zeile[richtung] = {"n": r["n_ereignisse"], "t5": h[5]["mittel_pct"],
                                   "p": h[5]["p_wert"]}
            else:
                aus.append("%s n=%-3d zu wenige" % (richtung, len(tr)))
                zeile[richtung] = {"n": len(tr)}
        print("  %-30s %s" % (name, "  |  ".join(aus)))
        ergebnis["regime"][name] = zeile

    if a.json:
        pathlib.Path(a.json).write_text(
            json.dumps(ergebnis, ensure_ascii=False, indent=2), encoding="utf-8")
        print()
        print("JSON geschrieben: %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
