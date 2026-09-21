#!/usr/bin/env python3
"""
bond_kontrollen.py — die Auflagen, ohne die der TLT-Befund nicht taugt.

    py -3.14 scripts/research/bond_kontrollen.py

Der Rohbefund lautet: nach einem TLT-Kursanstieg ab 4,1 % ueber 10 Handelstage
steigt SPY in den folgenden Wochen deutlich staerker als im Durchschnitt. Bevor
das veroeffentlicht wird, muss ausgeschlossen werden, dass es etwas anderes ist.
Ein externer Reviewer hat dafuer vier Auflagen gestellt; hier sind sie.

KONTROLLE 1 — SPY-VORTREND.
Die wichtigste. Wenn SPY vor dem Ereignis ohnehin schon lief, koennte der
"Vorlauf" schlicht Momentum sein. Gemessen wird deshalb, ob der Effekt auch
dann bleibt, wenn man die Ereignisse nach dem vorangegangenen SPY-Verlauf
aufteilt.

KONTROLLE 2 — VOLATILITAETSREGIME.
Starke Anleihebewegungen haeufen sich in unruhigen Phasen, und in unruhigen
Phasen sind Aktienrenditen anders verteilt. Getrennt nach ruhig/unruhig
(gemessen an der eigenen realisierten Vola von SPY) zeigt sich, ob der Effekt
ein Stress-Artefakt ist.

KONTROLLE 3 — TEILPERIODEN, vorab festgelegt.
2003-2019 gegen 2020-2025. Nicht die Perioden mit dem schoensten Ergebnis,
sondern der offensichtliche Schnitt: vor und nach dem Regimewechsel von 2020.
Haelt der Befund in BEIDEN Haelften, ist er kein Produkt einer Episode.

KONTROLLE 4 — MAX-T UEBER DIE GANZE FAMILIE.
Es wurden 4 Schwellen x 2 Richtungen x 2 Signalgeber x 4 Horizonte getestet.
Der kleinste Einzel-p-Wert daraus sagt wenig. Der Max-T-Test fragt stattdessen:
wie oft erreicht der BESTE Zufallstreffer aus einer ebenso grossen Familie das
beobachtete Niveau? Das ist die ehrliche Zahl fuer "wir haben viel probiert".
"""
from __future__ import annotations

import importlib.util
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
from shared.realized_vol import log_returns, rv_aus_returns          # noqa: E402

# Die Schwelle kommt aus bond_lead_lag.schwellen(), NICHT als gerundete Zahl.
# Angezeigt wird sie dort als "4,1 %", exakt ist sie 0,040632 — wer die
# gerundete Zahl nachbildet, prueft eine andere Ereignismenge als der
# Hauptbefund und erzeugt Abweichungen, die wie ein Rechenfehler aussehen
# (aufgefallen beim Schreiben des Artikels: +2,09 % gegen +2,07 % fuer
# dieselbe Groesse).
_bl = importlib.util.module_from_spec(importlib.util.spec_from_file_location(
    "bond_lead_lag", str(pathlib.Path(__file__).with_name("bond_lead_lag.py"))))
_bl.__loader__.exec_module(_bl)


def _schwelle_90() -> float:
    from shared.data import lade_closes as _lc
    _, c = _lc("TLT")
    return _bl.schwellen([float(x) for x in c])[1][1]


SCHWELLE = None         # wird in main() aus der Quelle gesetzt
HORIZONT = 10           # zwei Wochen


def lade():
    reihen = {}
    for t in ("TLT", "SPY"):
        d, c = lade_closes(t)
        reihen[t] = dict(zip(d, [float(x) for x in c]))
    tage = sorted(set(reihen["TLT"]) & set(reihen["SPY"]))
    return tage, reihen


def ereignisse(tage, kum, richtung="auf"):
    tr, letztes = [], -10 ** 9
    for i in range(B.BASIS + B.L, len(tage)):
        k = kum[i]
        if k is None:
            continue
        bew = math.exp(k) - 1.0
        passt = (bew >= SCHWELLE) if richtung == "auf" else (bew <= -SCHWELLE)
        if passt and i - letztes >= B.ABSTAND:
            tr.append(i)
            letztes = i
    return tr


def auswerten(spy, treffer, tage_n, k=HORIZONT, null=None):
    pf = [p for p in (B.pfad(spy, i) for i in treffer) if p]
    if len(pf) < 5:
        return None
    m = B.mittelpfad(pf)
    ist = m[B.VOR + k]
    if null is None:
        null = B.nullband(spy, treffer, tage_n)
    vert = sorted(x[B.VOR + k] for x in null)
    einzel = [p[B.VOR + k] for p in pf]
    return {"n": len(pf), "mittel": ist, "p": B._p_wert(ist, vert),
            "treffer": sum(1 for x in einzel if x > 0) / len(einzel) * 100}


def zeile(label, r, basis=None):
    if not r:
        print("  %-34s zu wenige Ereignisse" % label)
        return
    zus = ""
    if basis is not None:
        zus = "   (Basis %+.2f %%)" % basis
    print("  %-34s n=%-3d  %+6.2f %%  p=%.3f  Treffer %.0f %%%s"
          % (label, r["n"], r["mittel"], r["p"], r["treffer"], zus))


def main() -> int:
    global SCHWELLE
    SCHWELLE = _schwelle_90()
    tage, reihen = lade()
    spy = [reihen["SPY"][d] for d in tage]
    kum = B.kumulierte([reihen["TLT"][d] for d in tage], B.L)
    tr = ereignisse(tage, kum)
    null = B.nullband(spy, tr, len(tage))

    # Basisrate fuer denselben Horizont
    bw = [(spy[i + HORIZONT] / spy[i] - 1) * 100
          for i in range(len(spy) - HORIZONT) if spy[i] > 0]
    basis = statistics.fmean(bw)

    print("TLT-Kursanstieg ab %.1f %% ueber %d Handelstage, SPY nach %d Tagen"
          % (SCHWELLE * 100, B.L, HORIZONT))
    print("Marktdurchschnitt ohne Signal: %+.2f %% (Treffer %.1f %%)"
          % (basis, sum(1 for x in bw if x > 0) / len(bw) * 100))
    print()
    zeile("ALLE EREIGNISSE", auswerten(spy, tr, len(tage), null=null), basis)

    # ── Kontrolle 1: SPY-Vortrend ───────────────────────────────────────────
    print()
    print("KONTROLLE 1 — lief SPY vorher schon? (Momentum statt Vorlauf?)")
    vor = []
    for i in tr:
        p = B.pfad(spy, i)
        if p:
            vor.append((i, p[B.VOR] - p[0]))      # SPY-Verlauf t-10 bis t0
    med = statistics.median([v for _, v in vor])
    print("  Median des SPY-Verlaufs in den 10 Tagen VOR dem Ereignis: %+.2f %%" % med)
    for label, auswahl in (("Ereignisse mit schwachem Vorlauf", [i for i, v in vor if v <= med]),
                           ("Ereignisse mit starkem Vorlauf", [i for i, v in vor if v > med])):
        zeile(label, auswerten(spy, auswahl, len(tage)), basis)
    print("  -> Haelt der Effekt in BEIDEN Haelften, ist er nicht blosses Momentum.")

    # ── Kontrolle 2: Volatilitaetsregime ────────────────────────────────────
    print()
    print("KONTROLLE 2 — Stress-Artefakt? (getrennt nach SPY-Vola vor dem Ereignis)")
    lr = log_returns(spy)
    vola = []
    for i in tr:
        v = rv_aus_returns(lr[:i], 21)
        if v is not None:
            vola.append((i, v))
    if vola:
        medv = statistics.median([v for _, v in vola])
        print("  Median der realisierten SPY-Vola am Ereignistag: %.1f %%" % (medv * 100))
        for label, auswahl in (("ruhige Phasen (Vola unter Median)",
                                [i for i, v in vola if v <= medv]),
                               ("unruhige Phasen (Vola ueber Median)",
                                [i for i, v in vola if v > medv])):
            zeile(label, auswerten(spy, auswahl, len(tage)), basis)
        print("  -> Nur in unruhigen Phasen waere ein Erholungs-Artefakt.")

    # ── Kontrolle 3: Teilperioden ───────────────────────────────────────────
    print()
    print("KONTROLLE 3 — vorab festgelegte Teilung am Regimewechsel 2020")
    for label, ab, bis in (("2003-2019", "2000-01-01", "2019-12-31"),
                           ("2020-2025", "2020-01-01", "2030-12-31")):
        zeile(label, auswerten(spy, [i for i in tr if ab <= tage[i] <= bis],
                               len(tage)), basis)
    print("  -> Haelt er in beiden Haelften, ist er kein Produkt einer Episode.")

    # ── Kontrolle 4: Max-T ueber die Familie ────────────────────────────────
    print()
    print("KONTROLLE 4 — Max-T ueber alle 64 getesteten Kombinationen")
    print("  Frage: wie oft erreicht der BESTE Zufallstreffer aus einer ebenso")
    print("  grossen Familie den beobachteten Wert? Das ist die ehrliche Zahl,")
    print("  wenn man viel probiert hat.")
    echt = auswerten(spy, tr, len(tage), null=null)
    rnd = random.Random(20260921)
    besser = 0
    RUNDEN = 2000
    FAMILIE = 64
    for _ in range(RUNDEN):
        bestes = 0.0
        for _ in range(FAMILIE):
            versatz = rnd.randrange(len(tage))
            ps = [B.pfad(spy, (i + versatz) % len(tage)) for i in tr]
            ps = [p for p in ps if p]
            if not ps:
                continue
            w = abs(B.mittelpfad(ps)[B.VOR + HORIZONT] - basis)
            bestes = max(bestes, w)
        if bestes >= abs(echt["mittel"] - basis):
            besser += 1
    p_max = (besser + 1) / (RUNDEN + 1)
    print("  beobachtet: %+.2f %% (Abstand zur Basis %.2f pp)"
          % (echt["mittel"], abs(echt["mittel"] - basis)))
    print("  Max-T-p-Wert ueber %d Familien a %d Tests: %.3f" % (RUNDEN, FAMILIE, p_max))
    print("  -> Unter 0,05 hiesse: auch nach Beruecksichtigung der vielen Tests")
    print("     bleibt der Befund auffaellig.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
