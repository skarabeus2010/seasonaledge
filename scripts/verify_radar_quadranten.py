#!/usr/bin/env python3
"""
verify_radar_quadranten.py — Strategie-Beschriftungen der Vol-Regime-Radare (/skew, /flows) folgen EINER Lesart
(Nutzerentscheidung 2026-10-15): oben (teure Vola) wird die teure Seite des Skews verkauft, unten (billige Vola) die
günstige gekauft. X-Achse auf beiden Seiten = Rang von call_iv − put_iv: rechts sind Calls relativ teuer.

  oben links  Sell Put Spread     oben rechts  Sell Call Spread
  unten links Buy Call Spread     unten rechts Buy Put Spread

Bis 2026-10-15 waren auf /skew die beiden rechten Felder vertauscht und auf /flows die untere Zeile (Nutzerhinweis).
Geprüft werden die Beschriftungen samt Position direkt in den Seiten sowie die X-Achsen-Definition (call − put) und die
Tabelle im Blogartikel DE/EN. Exit 0 grün, 1 rot.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOLL = {("links", "oben"): "Sell Put Spread", ("rechts", "oben"): "Sell Call Spread",
        ("links", "unten"): "Buy Call Spread", ("rechts", "unten"): "Buy Put Spread"}
FEHLER = []


def pruef(name, ok, info=""):
    print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  ->  {info}" if info else ""))
    if not ok:
        FEHLER.append(name)


def _feld(x, y):
    return ("links" if x < 50 else "rechts", "oben" if y > 50 else "unten")


print("== /skew")
s = (ROOT / "landing/pages/skew.html").read_text(encoding="utf-8")
ist = {_feld(float(x), float(y)): t for x, y, t in re.findall(r"\[(\d+),(\d+),'((?:Sell|Buy) (?:Put|Call) Spread)'", s)}
pruef("vier Strategie-Felder gefunden", len(ist) == 4, ist)
for feld, soll in SOLL.items():
    pruef(f"{feld[1]} {feld[0]} = {soll}", ist.get(feld) == soll, ist.get(feld))
pruef("X-Achse = call_iv − put_iv", "rr=arr.map(function(e){return e.call_iv-e.put_iv;})" in s)

print("== /flows")
f = (ROOT / "landing/pages/flows.html").read_text(encoding="utf-8")
ist = {_feld(float(x), float(y)): t for x, y, t in
       re.findall(r"\{x:(\d+),y:(\d+),marker:\{size:0\},label:\{text:'((?:Sell|Buy) (?:Put|Call) Spread)'", f)}
pruef("vier Strategie-Felder gefunden", len(ist) == 4, ist)
for feld, soll in SOLL.items():
    pruef(f"{feld[1]} {feld[0]} = {soll}", ist.get(feld) == soll, ist.get(feld))
pruef("X-Achse = call_iv − put_iv", "var rr=arr.map(function(e){return e.call_iv-e.put_iv;});" in f)

print("== Blogartikel Vol-Regime-Radar")
for datei, zeilen in [
    ("blog/posts/2026-09-06_vol-regime-radar-risk-reversal-iv-rank.md",
     {"Oben rechts": "Call Credit Spread", "Oben links": "Put Credit Spread",
      "Unten rechts": "Put Debit Spread", "Unten links": "Call Debit Spread"}),
    ("blog/posts/en/2026-09-06_vol-regime-radar-risk-reversal-iv-rank.md",
     {"Top right": "call credit spread", "Top left": "put credit spread",
      "Bottom right": "put debit spread", "Bottom left": "call debit spread"})]:
    t = (ROOT / datei).read_text(encoding="utf-8")
    for quad, struktur in zeilen.items():
        z = next((l for l in t.splitlines() if l.startswith(f"| {quad} |")), "")
        pruef(f"{Path(datei).parent.name}: {quad} -> {struktur}", struktur in z, z.strip())
    # Der Rang ist relativ zur EIGENEN Historie: „rechts sind die Calls teuer“ wäre falsch (Codex 2026-10-15 — eine
    # RR-Historie −10…−2 Pp ergibt Rank 100, obwohl die Puts weiter die höhere IV haben).
    rel = "im Vergleich zur eigenen Historie" if "/en/" not in datei else "relative to its own history"
    falsch = "rechts sind die Calls teuer" if "/en/" not in datei else "on the right calls are rich"
    pruef(f"{Path(datei).parent.name}: Erklärung relativ zur eigenen Historie", rel in t and falsch not in t)

print()
if FEHLER:
    print(f"[FAIL] {len(FEHLER)} Prüfung(en)")
    sys.exit(1)
print("[OK] alle Prüfungen grün")
