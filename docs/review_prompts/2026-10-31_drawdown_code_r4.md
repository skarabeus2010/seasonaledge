# Code-Prüfung R4 — Drawdown-Analyse Phase 1 (`/drawdown`)

Grundlage: R3 [2026-10-31_drawdown_code_r3.md](2026-10-31_drawdown_code_r3.md), Antwort
[..._r3_antwort.md](2026-10-31_drawdown_code_r3_antwort.md) (NICHT FREIGABEFÄHIG, ein P2-Befund: Positivquote zählte
einen Rundungsrest als positiv; dazu die Lücke, dass die Referenz die Quote nicht nachrechnete).

Umgesetzt, bitte abnehmen:

1. **Positivquote mit Toleranz:** `shared/drawdown.py::forward_returns` → `sum(1 for w in v if w[0] > EPS) / len(v)`,
   `landing/js/drawdown-compute.js` → `v.filter(function (w) { return w[0] > EPS; })`. Gilt für Ereignisse und Basis
   (dieselbe Kennzahlfunktion).
2. **Referenz rechnet die Quote nach:** `scripts/verify_drawdown.py::referenz_forward` liefert je Fenster
   `exp(kum) − 1 > 1e-9` und zählt `pos`/`basis_pos`; der Forward-Vergleich verlangt
   `round(anteil_positiv · n) == pos` für Ereignisse und Basis.
3. **Handfall A15 „Nullrendite nicht positiv"** (Ihr Gegenbeispiel): CRYPTO, `100 → 90 → 110`, dann 19 × 90; fr10,
   h20: Ereignisse n = 1, Quote 0, Mittel ≈ 0; Basis n = 2, Quote 0 — Python und JS (drei Zeitzonen).

Stand: `verify_drawdown.py` BESTANDEN (239 Prüfungen, mit Seite). Mutationstest **32/32 an der benannten Prüfung**,
neu: „Positivquote ohne Toleranz" (→ `[A] A15 Nullrendite nicht positiv (Python)`) und „JS: Positivquote ohne
Toleranz" (→ `[A] A15 Nullrendite nicht positiv (JS)`).

Fragen: Ist der R3-Befund behoben? Gibt es noch eine Anzeige, die Kern und Seite bei Rundungsresten auseinanderlaufen
lässt (Vorzeichen/Farbe von ±0,00 %, Rangaussagen, Kohorten, Kalender)? Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder
NICHT FREIGABEFÄHIG.
