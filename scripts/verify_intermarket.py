#!/usr/bin/env python3
"""
verify_intermarket.py — Wächter für die Signale im Daily Briefing.

    py -3.14 scripts/verify_intermarket.py        Exit 1 bei Abweichung

WARUM ES DAS GIBT: shared/intermarket.py entscheidet, was täglich an echte
Empfänger geht. Der gefährlichste Fehler wäre nicht ein Absturz, sondern ein
Signal, das OHNE seine Bedingung gemeldet wird — der Anleihen-Befund gilt nur
bei erhöhter Marktvolatilität. In ruhigen Phasen lag der Effekt bei +0,50 %
gegen einen Marktdurchschnitt von +0,48 %, also bei null (p = 0,975). Wer die
Bedingung fallen lässt, verschickt Rauschen als Aussage.

Geprüft wird deshalb verhaltensbasiert gegen eingesetzte Kursbewegungen, nicht
gegen den Quelltext: die Marktdaten werden ersetzt, das Modul bleibt echt.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from shared import intermarket as IM                                 # noqa: E402

_fehler = 0
_faelle = 0


def pruef(name: str, ist, soll) -> None:
    global _fehler, _faelle
    _faelle += 1
    ok = (ist == soll)
    if not ok:
        _fehler += 1
    print(("  ok    " if ok else "  FEHL  ") + name + "  ->  " + repr(ist)
          + ("" if ok else "   erwartet " + repr(soll)))


def lage(tlt=0.0, btc=0.0, eth=0.0, vola=0.10):
    """Marktlage einsetzen und die Signale holen."""
    def _bew(ticker, tage=IM.FENSTER):
        return ({"TLT": tlt, "BTC-USD": btc, "ETH-USD": eth}.get(ticker, 0.0),
                "2026-09-22")
    IM._bewegung = _bew
    IM._spy_vola = lambda: vola
    return IM.intermarket_signale()


def arten(sig):
    return sorted(s["art"] for s in sig)


print("-- Anleihen: das Signal braucht BEIDE Bedingungen --")
pruef("Auslöser + hohe Vola -> Signal",
      arten(lage(tlt=0.05, vola=0.20)), ["anleihen"])
pruef("Auslöser, aber RUHIGER Markt -> KEIN Signal",
      arten(lage(tlt=0.05, vola=0.10)), [])
pruef("hohe Vola, aber kein Auslöser -> kein Signal",
      arten(lage(tlt=0.01, vola=0.20)), [])
pruef("knapp unter der Schwelle (4,0 %) -> kein Signal",
      arten(lage(tlt=0.040, vola=0.20)), [])
pruef("genau auf der Schwelle (4,1 %) -> Signal",
      arten(lage(tlt=IM.TLT_SCHWELLE, vola=0.20)), ["anleihen"])
pruef("Vola exakt auf dem Median -> kein Signal (strikt größer)",
      arten(lage(tlt=0.05, vola=IM.VOLA_SCHWELLE)), [])
pruef("TLT FÄLLT stark -> kein Signal (Gegenrichtung zeigte nichts)",
      arten(lage(tlt=-0.08, vola=0.25)), [])

print("-- Krypto: erst ab 20 %, darunter nichts --")
pruef("Bitcoin +12 % -> kein Signal", arten(lage(btc=0.12)), [])
pruef("Bitcoin +5 % (der Median!) -> kein Signal", arten(lage(btc=0.05)), [])
pruef("Bitcoin +25 % -> Signal", arten(lage(btc=0.25)), ["krypto"])
pruef("Ether +22 % -> Signal", arten(lage(eth=0.22)), ["krypto"])
pruef("beide über der Schwelle -> zwei Signale",
      arten(lage(btc=0.25, eth=0.30)), ["krypto", "krypto"])
pruef("Bitcoin -25 % -> Signal (als Information gekennzeichnet)",
      arten(lage(btc=-0.25)), ["krypto"])

print("-- der Normalfall ist STILL --")
pruef("ruhiger Markt, nichts Auffälliges -> keine Sektion",
      lage(tlt=0.01, btc=0.03, eth=0.02, vola=0.11), [])

print("-- Texte sagen, was sie sollen --")
s = lage(tlt=0.05, vola=0.20)[0]
pruef("Anleihen-Text nennt die Erholung, nicht die Prognose",
      "Erholungsmuster" in s["text"] and "keine Prognose" in s["text"], True)
pruef("Anleihen-Text nennt den vorherigen Rückgang",
      "zuvor" in s["text"] and "gefallen" in s["text"], True)
pruef("Anleihen-Text nennt den Marktdurchschnitt zum Vergleich",
      "0,48" in s["text"], True)
pruef("Anleihen-Text verlinkt den richtigen Artikel",
      s["artikel"], "/blog/anleihen-fruehindikator-aktienmarkt")
k = lage(btc=0.25)[0]
pruef("Krypto-Aufwärts-Text nennt die schwache Evidenz",
      "knapp" in k["text"], True)
pruef("Krypto-Text sagt, dass kleinere Anstiege nichts zeigten",
      "Kleinere" in k["text"], True)
kab = lage(btc=-0.25)[0]
pruef("Krypto-Abwärts-Text nennt es ausdrücklich kein Signal",
      "nicht als Signal" in kab["text"], True)

print("-- Ausfall der Datenquelle --")
IM._bewegung = lambda t, tage=IM.FENSTER: (None, None)
IM._spy_vola = lambda: None
pruef("keine Kursdaten -> keine Signale, kein Absturz", IM.intermarket_signale(), [])

print()
if _fehler:
    print("FEHLER: %d von %d Fällen" % (_fehler, _faelle))
else:
    print("[OK] alle %d Fälle grün" % _faelle)
sys.exit(1 if _fehler else 0)
