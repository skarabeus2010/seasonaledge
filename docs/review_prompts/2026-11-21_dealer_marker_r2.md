# /dealer-positioning + /polymarket Marker — Runde 2 (Codex, read-only)

Du bist Reviewer. Ändere NICHTS, schreibe keine Dateien. Antworte auf Deutsch. Runde 1:
docs/review_prompts/2026-11-21_dealer_marker_antwort.md (NICHT FREIGEGEBEN, vier Befunde).

## Umsetzung (git diff im Arbeitsbaum)

1. **20-%-Grenze vor Rand/Rundung**: `m.linie = spot==null || |x−spot| ≤ 0,2·spot` wird gesetzt, bevor der Ausschnitt
   berechnet wird; der Ausschnitt erweitert sich nur auf zugelassene Marker; Linie oder Text entscheidet `m.linie`.
2. **/polymarket** (`landing/js/polymarket.js`, `renderFedDistChart`): numerische Achse (min −1, max 13, tickAmount 14,
   Formatter 0..11 / „12+“ / Ränder leer), Balken als `{x:i, y, fillColor}`, `distributed` entfernt, Annotation am
   exakten Erwartungswert. `scripts/js/probe_polymarket_fedverteilung.js` liest die Balken jetzt über `.y`.
3. **Wächter** (`scripts/js/probe_options_session.js`, Blöcke 4 und 5): jeder Strike im Ausschnitt mit seinem Wert und
   vollständig, ungleiche Abstände, Flip bei genau 20 % als Linie, Call-Wall bei 20,5 % als Text trotz gerundetem
   Ausschnitt bis 121, Spot 0 ohne Linie, Polymarket-Achse/Annotation/Balken/Beschriftung. Mutationstest (Scratchpad,
   Datei-Kopie + Wiederherstellung): 6/6 gefangen (20-%-Regel nach Rundung, Spot 0 gültig, Balkenwerte genullt,
   Strike-Achse Kategorie, Polymarket Kategorie, Polymarket Balken um 1 verschoben). Fed-Mutationstest 17/17.
4. **Spot > 0**: `spot` nur endlich und > 0, sonst null.
5. `columnWidth:'80%'` in `plotOptions.bar` verschoben.

## Fragen

- Sind die vier Befunde behoben? Neue Fehler?
- /polymarket mit echter ApexCharts 4.7.0: Balken korrekt gefärbt (fillColor ohne distributed), Breite, Tooltip-x
  (`opts.dataPointIndex` → `cats[n]`), Beschriftung, keine Achsen-Tooltip-Artefakte? `colors` steht zweimal im
  Konfigurationsobjekt (vorbestehend) — Wirkung?
- Wenn möglich: SVG-x der Polymarket-Annotation gegen die lineare Abbildung prüfen wie in Runde 1.

Antworte mit Befunden (nummeriert, Datei:Zeile, Schwere) und FREIGABE oder NICHT FREIGEGEBEN.
