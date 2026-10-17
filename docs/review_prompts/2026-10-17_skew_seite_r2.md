# Codex-Review: /skew überarbeitet (2026-10-17, Runde 2)

Runde 1: [2026-10-17_skew_seite_r1.md](2026-10-17_skew_seite_r1.md) — ein Befund (P2: gescheiterte Ticker zählten nur
unter „Alle“, „Energie & Grid“ 20 von 26 statt 28). Nur lesen, nichts ändern. Diff: `git diff HEAD -- landing scripts`.

## Seit Runde 1 geändert
1. **P2 behoben:** `scripts/compute_options_skew.py` schreibt `cats` (`categories_for`) in beide `coverage.failed`-
   Einträge; die Seite übernimmt sie in `SKEW_CATMAP` (ohne vorhandene Ticker-Kategorien zu überschreiben) und
   `renderQuadStand` zählt gescheiterte Ticker per `_inCat`. Ältere Dateien ohne `cats`: Ticker zählt nur unter „Alle“.
   Wächterfall „Kategorie X: C (X) zählt mit, D (Y) nicht“, zwei neue Mutationen.
2. **Vol-Kennzahlen-Tabelle** (Nutzerwunsch): Klasse `sk-kz`, `width:auto`, Container `max-height:700px; overflow:auto`,
   Kopfzeile `position:sticky; top:0`, Ticker-Spalte `position:sticky; left:0` mit Kartenhintergrund. Zusammenlegen mit
   dem Vol-Trigger bewusst NICHT (20 gegen 161 Ticker, 6 Spalten wären bei ~140 Zeilen leer).

## Prüffragen
1. Ist P2 vollständig: Fehlliste, Zähler, Kategorie-Tags der Kacheln — und kann ein gescheiterter Ticker durch die
   CATMAP-Ergänzung in VRP/Tabelle/Extremlisten/Vol-Trigger auftauchen, wo er nichts zu suchen hat?
2. Liest irgendein anderer Verbraucher `coverage.failed` mit fester Feldmenge (Mail, Health-Check, Bericht)?
3. Sticky-Tabelle: überdeckt die fixierte Ticker-Spalte die Heatmap-Farbe oder die Auswahl-Hervorhebung (`tr.sel td`,
   Hover) — oder bleibt beim Seitwärtsscrollen Text der Nachbarspalte durchscheinend sichtbar?
4. Alles aus Runde 1, sofern durch die Änderungen berührt.

Antwort: Befunde mit Datei:Zeile und Schwere, am Ende **FREIGABE** oder **KEINE FREIGABE**.
