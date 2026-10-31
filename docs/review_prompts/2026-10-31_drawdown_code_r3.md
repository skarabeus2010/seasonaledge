# Code-Prüfung R3 — Drawdown-Analyse Phase 1 (`/drawdown`)

Grundlage: R2 [2026-10-31_drawdown_code_r2.md](2026-10-31_drawdown_code_r2.md), Antwort
[..._r2_antwort.md](2026-10-31_drawdown_code_r2_antwort.md) (NICHT FREIGABEFÄHIG, vier Befunde).

Umgesetzt, bitte je Befund abnehmen:

1. **Kurzantwort bei n = 0:** neuer Zweig `else if (!g5.n)` in `landing/pages/drawdown.html` vor der Rangaussage —
   „Keine abgeschlossene Episode … ein Vergleich von Drawdown-Dauer und Tiefe ist nicht möglich.“ (`dd.a_keine`,
   DE-Fallback + `en.json`). Seitenprüfung `[F] n0: Kurzantwort ohne „0 von 0“, mit „kein Vergleich“`.
2. **EPS an der Schwelle der periodenübergreifenden Episoden:** `e["tiefe"] <= -0.05 + EPS` in
   `shared/drawdown.py::grenzueberschreitend` und `e.tiefe <= -0.05 + EPS` in `landing/js/drawdown-compute.js`.
   Handfall A14 (Ihr Gegenbeispiel `100 → 102 → 96,9 → 102 → 103`, Start am dritten Schluss) in Python und JS
   (drei Zeitzonen) — genau eine Episode, Peak = zweiter Schluss.
3. **Cache-Kennung:** `_JSON_VER = 'v29'` in `landing/js/i18n.js` (HEAD v27).
4. **EN-Neubau:** der Wächter verlangt Exit 0 von `build_en.py --write` UND die Datei; sonst rot, und der EN-Seitenfall
   wird nicht gegen eine alte Datei geprüft.

Stand: `verify_drawdown.py` BESTANDEN (234 Prüfungen, mit Seite). Mutationstest **30/30 an der benannten Prüfung**,
neu: „Periodenübergreifend ohne Toleranz“ (Python, A14), „JS: periodenübergreifend ohne Toleranz“ (A14 JS UTC),
„Seite: Kurzantwort zeigt „0 von 0““ (`[F] n0: Kurzantwort`).

Fragen: Sind die vier Befunde behoben? Gibt es weitere Schwellenvergleiche ohne EPS (Seite, Kalender, Forward,
Kohorten), die bei Rundungsresten zwischen Kern und Anzeige auseinanderlaufen? Welche falsche Anzeige käme noch durch?
Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT FREIGABEFÄHIG.
