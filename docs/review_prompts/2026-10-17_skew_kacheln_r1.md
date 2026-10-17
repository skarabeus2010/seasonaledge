# Codex-Review: /skew Kacheln, Wall-Veränderung, Tabelle zweispaltig, Sortier-Fehler (2026-10-17, Runde 1)

Nur lesen. Diff: `git diff HEAD -- landing scripts .github`. Alle Wünsche vom Nutzer (Entscheidungen, nicht zur
Diskussion): VRP-Kachel so hoch wie der Vol-Trigger und lesbare Beschriftung (positive Werte links der Nulllinie,
negative rechts), Call-/Put-Wall mit Veränderung zur Vorsession in Klammern (höher = grün, tiefer = rot, für beide
Walls), Vol-Kennzahlen zweispaltig ohne Ticker ohne Werte, Sortierung darf die Überschriften nicht verlieren.

## Änderungen
1. **`landing/js/app.js` `SA.makeSortable`:** im `<tbody>`-Fall wird die Kopfzeile aus den sortierten Zeilen
   ausgeschlossen. Ursache des Fehlers: eine per innerHTML gebaute `<table><tr><th>…` bekommt ein implizites `<tbody>`,
   in dem auch die Kopfzeile steht; sie wanderte beim Sortieren ans Ende (betrifft jede so gebaute Tabelle der Seite).
2. **VRP (`renderVRP`):** HTML-Balken statt ApexCharts; `.sk-vrp-box` absolut positionierte Liste in einer
   Flex-Kachel (Grid `align-items:stretch`) → Höhe folgt dem Vol-Trigger; unter 820 px Mindesthöhe 380 px.
3. **Walls (`ladeVorher`, `_wallZelle`):** lädt die jüngste Archivdatei `gex_history_session/<datum>.json` mit
   `session < aktuelle Session` (bis 10 Kalendertage zurück), Differenz gerundet, Farbe nach Vorzeichen, Tooltip mit
   Session. Ohne Vorsession nur der Wert.
4. **Vol-Kennzahlen (`renderSkewTable`):** Zeilen ohne `skew_pts` und `iv_atm` raus (Zahl in der Kachel), Sortierung
   `SKEW_KZ_SORT` über alle Zeilen (leer immer hinten, Gleichstand nach Ticker), dann in zwei Hälften auf zwei Tabellen
   mit `<thead>` und `data-no-sort="1"`; Klick auf eine Überschrift sortiert neu und zeichnet beide.
5. **Wächter:** `scripts/js/probe_sortierer.js` (jsdom): makeSortable mit implizitem tbody (Gegenprobe: alte app.js
   wird rot), /skew-Tabelle mit echtem Seiten-JS (Hälften, Sortierung, Köpfe, ausgeblendete Zeilen); ins Deploy-Gate.
   `probe_skew_tabelle.js` zählt Tooltips der ersten Tabelle. `_JSON_VER` v21.

## Prüffragen
1. Kann der Sortier-Fix andere Seiten brechen (Tabellen mit `<thead>`, Tabellen ohne `<th>`, mehrere `<tbody>`)?
2. Wall-Differenz: Ist „jüngste Archivdatei vor der Session“ die richtige Vorsession — auch nach Feiertagen, bei
   fehlender Archivdatei (Ausfall), bei einem Ticker, der vorher fehlte? Ist die Rundung irreführend (Walls auf 0,5er
   Strikes)? Kann ein Vergleich über eine Verfallsgrenze (OPEX) eine große, mechanische Verschiebung als „bullish“
   ausweisen — sollte das gekennzeichnet werden?
3. Tabelle: Geht durch das Ausblenden etwas verloren, das vorher sichtbar war (NE-Skew ohne 30-Tage-Wert)?
   Sortierung stabil und richtig für Text-/Zahl-/bool-Spalten? Tickerauswahl (`sel`) nach Neuzeichnen erhalten?
4. VRP: Bleibt der Klick auf eine Zeile → Tickerauswahl? EN-Texte vollständig?

Befunde mit Datei:Zeile und Schwere, am Ende **FREIGABE** oder **KEINE FREIGABE**.
