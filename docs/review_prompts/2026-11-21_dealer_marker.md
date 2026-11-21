# /dealer-positioning: Marker-Linien lagen falsch — Code-Review (Codex, read-only)

Du bist Reviewer. Ändere NICHTS, schreibe keine Dateien. Antworte auf Deutsch.

## Nutzerbefund (Screenshot 21.11.2026, SPY, Gamma by Strike)

Spot 689.81 war bei Strike ~671 eingezeichnet, Put-Wall 675 rechts vom Spot, Flip 737.02 bei ~674, Call-Wall 775 bei
~677. Die Werte selbst stimmen (Put-Wall < Spot < Call-Wall), nur die Positionen nicht.

## Meine Diagnose

Die Strike-Ansicht war eine Kategorie-Achse (`xaxis.categories = strikes`, Bar-Chart → ApexCharts 4.7.0 setzt
`convertedCatToNumeric`). Annotationen bekamen `x: Number(wert)`. In `landing/vendor/apexcharts.min.js`,
`getX1X2` → `getStringX(a)`: `t = categoryLabels.indexOf(a) + 1`; nicht gefunden → 0 → `labels.indexOf(0)` = −1 →
kein Achsentext gefunden → Rückgabe `i = a`, also der ROHE WERT als Pixelposition. Spot 689.81 → 689,81 px usw.
Bitte im minifizierten Code nachprüfen.

## Änderung (git diff im Arbeitsbaum)

- `landing/pages/dealer-positioning.html`, `renderChart()`: Strike-Ansicht mit `xaxis.type = 'numeric'`, Daten als
  `[strike, wert]`, Annotationen am exakten Wert. Ausschnitt ±8 % um den Spot, erweitert auf Marker bis ±20 %,
  2 % Rand. Marker außerhalb → keine Linie, Nennung im Text unter dem Chart (`chart-horizon`). Term-Ansicht unverändert
  (Kategorien, ohne Marker).
- `scripts/js/probe_options_session.js` (läuft im Gate über `verify_gex_session.py`): neuer Block (3) prüft Achsentyp,
  Linienpositionen, Ausschnitt, Text für Marker > 20 %, Datenform. Gegen die alte Seite: 4 Prüfungen rot.

## Fragen

1. Stimmt die Diagnose? (Datei/Stelle im Vendor-Code)
2. Ist der Fix korrekt und vollständig? Insbesondere:
   - Bar-Chart mit numerischer x-Achse in ApexCharts 4.7.0: Balkenbreite bei ungleichen Strike-Abständen (1er nahe
     Spot, 5er weiter weg), Balken am Rand (min/max), `tickAmount` + `formatter` (Math.round) → doppelte/irreführende
     Ticklabels?
   - Tooltip-Formatter für x in beiden Ansichten.
   - `hz.innerHTML +=` — kann der Text bei wiederholtem `renderChart()` (Umschalten Gamma/Vanna/Charm) doppelt
     erscheinen? (hz wird am Funktionsanfang neu gesetzt — prüfen.)
   - Spot fehlt (`spot` null/0) → Verhalten?
   - Wechsel strike→term→strike: bleiben alte Optionen (xaxis min/max) hängen? (`chart.destroy()` + neu)
3. Gibt es dieselbe Fehlerklasse (numerische Annotation auf Kategorie-Achse) auf anderen Seiten? Suche in
   `landing/pages/*.html` und `landing/js/*.js` nach `annotations` mit `xaxis` auf Charts mit `categories`.
4. Prüft der Wächter genug? Welche Mutation käme durch?

Antworte mit: Befunde (nummeriert, Datei:Zeile, Schwere), dann FREIGABE oder NICHT FREIGEGEBEN.
