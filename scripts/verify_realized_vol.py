#!/usr/bin/env python3
"""
verify_realized_vol.py — Wächter für shared/realized_vol.py.

    py -3.14 scripts/verify_realized_vol.py        Exit 1 bei Abweichung

Geprüft wird gegen DREI Referenzen, nicht gegen die eigene Formel:

1. `statistics.stdev` aus der Standardbibliothek — eine fremde Implementierung
   der Stichproben-Standardabweichung (÷ N−1). Damit hängt der Nachweis nicht
   an derselben Zeile Code, die er prüfen soll.
2. Analytisch bekannte Fälle: konstante Returns haben Varianz 0; bei
   alternierenden ±r um den Mittelwert 0 lässt sich die RV in einer Zeile
   hinschreiben.
3. Die Identität zwischen rollender und einmaliger Rechnung: `rv_reihe` muss
   am letzten Tag genau das liefern, was `rv_aus_closes` über die ganze Reihe
   liefert. Zwei Wege, ein Ergebnis — sonst driftet die Nachrüstung gegen den
   Live-Lauf, und das VRP der Historie wäre nicht mit dem des Live-Punkts
   vergleichbar.

Grund für diesen Wächter: das VRP steht in der Historie nur in 793 von 6271
Zeilen, weil der Backfill es nicht schreibt. Die Nachrüstung rechnet dieselbe
Größe für vergangene Tage — und eine zweite Implementierung derselben
Mathematik ist in diesem Projekt die teuerste wiederkehrende Fehlerklasse.
"""
from __future__ import annotations

import math
import os
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from shared.realized_vol import (                                    # noqa: E402
    HANDELSTAGE_JAHR, RV_FENSTER, iso_tag, kappe_auf, log_returns,
    rv_aus_closes, rv_aus_returns, rv_reihe,
)

_fehler = 0
_faelle = 0


def pruef(name: str, ist, soll, tol: float = 1e-9) -> None:
    global _fehler, _faelle
    _faelle += 1
    abw = ""
    if ist is None or soll is None:
        ok = (ist is None and soll is None)
    elif isinstance(ist, (bool, str)) or isinstance(soll, (bool, str)):
        ok = (ist == soll)                      # Wahrheitswerte/Text exakt
    else:
        ok = abs(float(ist) - float(soll)) <= tol
        abw = "   (Abweichung %.3e)" % abs(float(ist) - float(soll))
    if not ok:
        _fehler += 1
    print(("  ok    " if ok else "  FEHL  ") + name + "  ->  " + str(ist)
          + ("" if ok else "   erwartet " + str(soll) + abw))


def kurse_aus_returns(returns, start: float = 100.0) -> list[float]:
    """Kursreihe, die genau diese Log-Returns erzeugt."""
    c = [start]
    for r in returns:
        c.append(c[-1] * math.exp(r))
    return c


print("-- Referenz 1: gegen statistics.stdev (fremde Implementierung) --")
# Eine unregelmaessige, aber deterministische Reihe. Kein Zufall: ein Waechter
# muss bei jedem Lauf dasselbe pruefen.
roh = [math.sin(i * 0.7) * 0.013 + math.cos(i * 0.31) * 0.004 for i in range(60)]
for n in (5, 21, 40):
    seg = roh[-n:]
    soll = statistics.stdev(seg) * math.sqrt(HANDELSTAGE_JAHR)
    pruef("rv_aus_returns n=%-2d == stdev x sqrt(252)" % n,
          rv_aus_returns(roh, n), round(soll, 4), tol=5e-5)

closes = kurse_aus_returns(roh)
seg = roh[-RV_FENSTER:]
pruef("rv_aus_closes rechnet die Kurse korrekt zurueck",
      rv_aus_closes(closes), round(statistics.stdev(seg) * math.sqrt(HANDELSTAGE_JAHR), 4),
      tol=5e-5)

print("-- Referenz 2: analytisch bekannte Faelle --")
# Konstante Returns -> Varianz 0 -> RV 0. Eine Reihe mit konstanter
# prozentualer Aenderung hat keine Streuung, egal wie steil sie steigt.
pruef("konstante Returns (+1 % taeglich) -> RV 0",
      rv_aus_closes([100.0 * 1.01 ** i for i in range(40)]), 0.0, tol=1e-9)
pruef("flache Reihe -> RV 0", rv_aus_closes([50.0] * 40), 0.0, tol=1e-12)

# Alternierende +-r bei GERADEM n: Mittelwert 0, Varianz = n*r^2/(n-1).
r = math.log(1.02)
alt = [r if i % 2 == 0 else -r for i in range(40)]
n = 20
soll = math.sqrt(n * r * r / (n - 1)) * math.sqrt(HANDELSTAGE_JAHR)
pruef("alternierende +-r, n=20 -> r*sqrt(n/(n-1))*sqrt(252)",
      rv_aus_returns(alt, n), round(soll, 4), tol=5e-5)

# Stichproben- gegen Populationsvarianz: bei n=2 unterscheiden sie sich um
# Faktor sqrt(2). Faengt ein versehentliches "/ n".
zwei = [0.01, -0.01]
pruef("n=2 nutzt ÷(N-1), nicht ÷N",
      rv_aus_returns(zwei, 2), round(0.02 / math.sqrt(2) * math.sqrt(252), 4), tol=5e-5)

print("-- Referenz 3: rollend == einmalig (Zwillings-Identitaet) --")
daten = ["2026-01-%02d" % (i + 1) for i in range(len(closes))]
reihe = rv_reihe(daten, closes)
pruef("rv_reihe am letzten Tag == rv_aus_closes",
      reihe.get(daten[-1]), rv_aus_closes(closes), tol=1e-12)
# Und an einem MITTLEREN Tag gegen die auf diesen Tag gekappte Reihe — das ist
# der Fall, den die Nachruestung braucht (RV zu einem vergangenen Datum).
mitte = 45
pruef("rv_reihe an Tag 45 == rv_aus_closes(closes[:46])",
      reihe.get(daten[mitte]), rv_aus_closes(closes[:mitte + 1]), tol=1e-12)
pruef("erster Tag mit vollem Fenster ist Index %d" % RV_FENSTER,
      daten[RV_FENSTER] in reihe, True)
pruef("ein Tag davor hat noch kein volles Fenster",
      daten[RV_FENSTER - 1] in reihe, False)

print("-- Luecken: kein Wert ist besser als ein falscher --")
mit_luecke = list(closes)
mit_luecke[30] = 0.0                      # unbrauchbarer Kurs mitten im Fenster
lr = log_returns(mit_luecke)
pruef("unbrauchbarer Kurs erzeugt zwei None-Returns",
      sum(1 for x in lr if x is None), 2)
pruef("Fenster mit Luecke -> None", rv_aus_returns(lr[:32], RV_FENSTER), None)
r2 = rv_reihe(daten, mit_luecke)
pruef("Tag 30 faellt aus der Reihe", daten[30] in r2, False)
pruef("Tag 52 (Luecke ausserhalb des Fensters) ist wieder da", daten[52] in r2, True)
pruef("Tag 52 stimmt mit der gekappten Rechnung ueberein",
      r2.get(daten[52]), rv_aus_closes(mit_luecke[:53]), tol=1e-12)
# Die Luecke muss IM Fenster liegen: rv_aus_closes schaut auf die letzten 21
# Returns. Liegt sie davor, ist ein Ergebnis voellig richtig — genau das hat
# dieser Fall beim ersten Lauf gezeigt (0.0 statt None, und 0.0 war korrekt).
pruef("None im Fenster -> None",
      rv_aus_closes([100.0] * 30 + [None] + [100.0] * 5), None)
pruef("NaN im Fenster -> None",
      rv_aus_closes([100.0] * 30 + [float("nan")] + [100.0] * 5), None)
pruef("None VOR dem Fenster stoert nicht",
      rv_aus_closes([100.0] * 5 + [None] + [100.0] * 30), 0.0, tol=1e-12)

print("-- Randfaelle --")
pruef("leere Reihe", rv_aus_closes([]), None)
pruef("zu kurze Reihe (n Kurse fuer n Returns reicht nicht)",
      rv_aus_closes([100.0] * RV_FENSTER), None)
pruef("genau n+1 Kurse reichen", rv_aus_closes([100.0] * (RV_FENSTER + 1)), 0.0, tol=1e-12)
pruef("n=1 ist keine Varianz", rv_aus_returns([0.01, 0.02], 1), None)
pruef("None als Reihe", rv_aus_closes(None), None)
pruef("rv_reihe mit leeren Eingaben", len(rv_reihe([], [])), 0)

try:
    rv_reihe(["2026-01-01"], [1.0, 2.0])
    pruef("ungleiche Laengen werfen", "kein Fehler", "ValueError")
except ValueError:
    pruef("ungleiche Laengen werfen ValueError", "ValueError", "ValueError")

print("-- Gegen den bisherigen Live-Rechenweg --")
# Die Formel, wie sie bis zur Zusammenlegung in compute_options_skew stand.
# Beweist, dass die Zusammenlegung KEINE Zahl verschoben hat.
def _alt(closes_, n):
    c = list(closes_)
    if len(c) < n + 5:
        return None
    rr = [math.log(c[i] / c[i - 1]) for i in range(1, len(c)) if c[i - 1] > 0 and c[i] > 0]
    if len(rr) < n:
        return None
    s = rr[-n:]
    m = sum(s) / n
    var = sum((x - m) ** 2 for x in s) / (n - 1)
    return round(math.sqrt(var) * math.sqrt(252), 4)

for n in (5, 21, 40):
    pruef("alte Live-Formel == rv_aus_closes, n=%-2d" % n,
          rv_aus_closes(closes, n), _alt(closes, n), tol=1e-12)

print("-- Kappung: der Zeitstempel-Fallstrick vom 2026-09-18 --")
# Der Fehler, der im Live-Lauf sass: `df[df.index <= "2026-09-18"]` auf einem
# DatetimeIndex mit Uhrzeit schnitt die Session weg. Hier nachgestellt.
import datetime as _dt
stempel = [_dt.datetime(2026, 9, d, 13, 30) for d in (14, 15, 16, 17, 18)]
kurse = [100.0, 101.0, 102.0, 103.0, 104.0]
d2, c2 = kappe_auf(stempel, kurse, "2026-09-18")
pruef("Zeitstempel mit Uhrzeit: die Session bleibt drin", d2[-1] if d2 else None, "2026-09-18")
pruef("und kein Kurs geht verloren", len(c2), 5)
pruef("der Kurs der Session ist der letzte", c2[-1] if c2 else None, 104.0, tol=1e-12)
# Gegenprobe: der naive Vergleich, der den Fehler verursachte
naiv = [i for i, x in enumerate(stempel) if x <= _dt.datetime(2026, 9, 18)]
pruef("Beweis: der naive Zeitstempel-Vergleich verliert die Session", len(naiv), 4)
# Kappen auf einen frueheren Tag schneidet wirklich
d3, c3 = kappe_auf(stempel, kurse, "2026-09-16")
pruef("Kappung auf den 16. laesst 3 Tage", len(d3), 3)
pruef("und endet am 16.", d3[-1] if d3 else None, "2026-09-16")
# Reine Datums-Strings muessen genauso funktionieren
d4, c4 = kappe_auf(["2026-09-17", "2026-09-18"], [1.0, 2.0], "2026-09-18")
pruef("ISO-Strings als Datum", len(d4), 2)
pruef("bis=None laesst alles stehen", len(kappe_auf(stempel, kurse, None)[0]), 5)
pruef("Kappung vor dem Reihenbeginn ergibt leer",
      len(kappe_auf(stempel, kurse, "2026-01-01")[0]), 0)
pruef("iso_tag schneidet die Uhrzeit ab", iso_tag(stempel[-1]), "2026-09-18")
try:
    kappe_auf(["2026-01-01"], [1.0, 2.0], None)
    pruef("ungleiche Laengen werfen (kappe_auf)", "kein Fehler", "ValueError")
except ValueError:
    pruef("ungleiche Laengen werfen ValueError (kappe_auf)", "ValueError", "ValueError")

print("-- Codex-Befunde 5-7: inf, Sortierung, Wrapper, n+5-Grenze --")
# Befund 6: inf kam durch (inf > 0 ist wahr, inf == inf ist wahr) und erzeugte
# eine NaN-RV statt eines fehlenden Wertes.
pruef("+inf im Fenster -> None",
      rv_aus_closes([100.0] * 30 + [float("inf")] + [100.0] * 5), None)
pruef("-inf im Fenster -> None",
      rv_aus_closes([100.0] * 30 + [float("-inf")] + [100.0] * 5), None)
_lr = log_returns([100.0, float("inf"), 100.0])
pruef("log_returns macht aus inf zwei None", sum(1 for x in _lr if x is None), 2)
pruef("kein NaN-Ergebnis mehr moeglich",
      all(x is None or math.isfinite(x) for x in _lr), True)

# Befund 7: doppelte oder unsortierte Tage ordneten Werte still falsch zu.
_d = ["2026-01-%02d" % (i + 1) for i in range(30)]
_c = [100.0 + i for i in range(30)]
try:
    rv_reihe(_d[:15] + [_d[14]] + _d[16:], _c)
    pruef("doppelter Tag wirft", "kein Fehler", "ValueError")
except ValueError:
    pruef("doppelter Tag wirft ValueError", "ValueError", "ValueError")
try:
    rv_reihe(list(reversed(_d)), _c)
    pruef("absteigende Reihe wirft", "kein Fehler", "ValueError")
except ValueError:
    pruef("absteigende Reihe wirft ValueError", "ValueError", "ValueError")
pruef("aufsteigend und eindeutig geht durch", len(rv_reihe(_d, _c)) > 0, True)

# Befund 5: der LIVE-WRAPPER mit Luecke und die n+5-Grenze waren ungeprueft.
# _realized_vol nimmt n+5 Kurse, nicht n+1 — bewusst ein Puffer, aber niemand
# hat nachgesehen, ob die Grenze auch sitzt.
import pandas as _pd

def _wrapper(closes_, n=RV_FENSTER, bis=None):
    """Bildet den Pfad in _realized_vol nach: DataFrame mit Uhrzeiten im Index,
    Kappung, n+5-Grenze, dann der gemeinsame Kern."""
    idx = [_pd.Timestamp("2026-01-01 13:30") + _pd.Timedelta(days=i)
           for i in range(len(closes_))]
    df = _pd.DataFrame({"Close": closes_}, index=idx)
    daten, cc = kappe_auf(df.index, df["Close"].to_numpy(dtype=float), bis)
    if not cc or len(cc) < n + 5:
        return None, (daten[-1] if daten else None)
    return rv_aus_closes(cc, n), daten[-1]

pruef("Wrapper: genau n+5 Kurse reichen",
      _wrapper([100.0 + i for i in range(RV_FENSTER + 5)])[0] is not None, True)
pruef("Wrapper: n+4 Kurse reichen nicht (n+5-Grenze sitzt)",
      _wrapper([100.0 + i for i in range(RV_FENSTER + 4)])[0], None)
_mit = [100.0] * 26 + [0.0] + [100.0] * 4
pruef("Wrapper: Luecke im letzten Fenster -> None", _wrapper(_mit)[0], None)
pruef("Wrapper: Luecke weit vorne stoert nicht",
      _wrapper([100.0] * 2 + [0.0] + [100.0] * 40)[0], 0.0, tol=1e-12)
# Und der Kappungsfehler im Wrapper-Kontext: das war der Live-Fehler.
_c30 = [100.0 + i for i in range(30)]
_rv, _ld = _wrapper(_c30, bis="2026-01-30")
pruef("Wrapper: die Session bleibt beim Kappen erhalten", _ld, "2026-01-30")
pruef("Wrapper ohne Kappung endet am selben Tag", _wrapper(_c30)[1], "2026-01-30")

print()
if _fehler:
    print("FEHLER: %d von %d Faellen" % (_fehler, _faelle))
else:
    print("[OK] alle %d Faelle gruen — drei unabhaengige Referenzen" % _faelle)
sys.exit(1 if _fehler else 0)
