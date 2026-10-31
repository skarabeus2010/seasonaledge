**NICHT FREIGABEFÄHIG**
tokens used
91.938
Die vier R2-Befunde sind im Code behoben. Es bleibt ein neuer Befund:

**[P2] Rundungsreste zählen unveränderte Forward-Kurse als Gewinn.**  
Belege: [shared/drawdown.py:398](C:/dev/SeasonalEdge/shared/drawdown.py:398), [drawdown-compute.js:305](C:/dev/SeasonalEdge/landing/js/drawdown-compute.js:305).

Gegenbeispiel: 22 tägliche Krypto-Schlüsse `100 → 90 → 110 → anschließend 19-mal 90`, Renditen jeweils `log(close/vorheriger_close)`. Beim ersten −10-%-Übertritt startet das 20-Tage-Fenster bei 90 und endet bei 90: Rendite mathematisch null. Beide Kerne liefern jedoch `2,22 × 10⁻¹⁴ %` und zählen den Fall durch `> 0` als positiv.

Der Produktionsrenderer zeigt deshalb **„100 % positiv“ bei n = 1** neben „+0,00 %“ ([drawdown.html:497](C:/dev/SeasonalEdge/landing/pages/drawdown.html:497)). Auch die Basisquote ist betroffen. Hier eine konsistente Nulltoleranz verwenden.

**Prüflücke:** Die unabhängige Forward-Prüfung kontrolliert die Positivquoten nicht ([verify_drawdown.py:397](C:/dev/SeasonalEdge/scripts/verify_drawdown.py:397)). Einen Nullrendite-Handfall für Ereignisse und Basis ergänzen.

Python, JavaScript und den Tabellenrenderer habe ich mit diesem Gegenbeispiel ausgeführt. Der vollständige Kernwächter lieferte vor Abbruch kein Gesamtergebnis. Dateischreibende Seiten- und Mutationstests wurden nicht ausgeführt. Keine Dateien geändert.

**NICHT FREIGABEFÄHIG**
