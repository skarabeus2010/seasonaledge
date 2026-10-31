**Die acht R1-Befunde sind noch nicht vollständig behoben. Vier Befunde bleiben:**

1. **Wichtig – Die Kurzantwort zeigt weiterhin „0 von 0“.**  
   Beleg: [drawdown.html:346](C:/dev/SeasonalEdge/landing/pages/drawdown.html:346), Prüflücke: [verify_drawdown.py:555](C:/dev/SeasonalEdge/scripts/verify_drawdown.py:555).  
   **Gegenprobe:** Die echte Seite mit `100 → 90 → 85 → 80` zeigt korrekt „nicht bestimmbar“ in den Kacheln, schreibt aber darüber: „Tiefer als die aktuellen −20,00 % fielen 0 von 0.“ Der neue Wächter kontrolliert ausschließlich den Kacheltext. Auch die Kurzantwort braucht den Fall „keine Vergleichsepisode“.

2. **Wichtig – Periodenübergreifende Episoden verlieren die Schwelltoleranz.**  
   Belege: [drawdown.py:280](C:/dev/SeasonalEdge/shared/drawdown.py:280), [drawdown-compute.js:222](C:/dev/SeasonalEdge/landing/js/drawdown-compute.js:222).  
   **Gegenprobe:** `100 → 102 → 96,9 → 102 → 103`, Zeitraumstart am dritten Schluss. Beide Kerne zählen die abgeschlossene Episode unter „mindestens 5 %“, liefern für die periodenübergreifende Liste aber `[]`: Die rekonstruierte Tiefe ist `−0,04999999999999993`, der dortige Vergleich verwendet strikt `≤ −0,05`. Damit fehlt die versprochene gesonderte Nennung unter der Tabelle. Hier dieselbe EPS-Regel verwenden.

3. **Wichtig – Die neuen Übersetzungen erreichen bestehende Sitzungen nicht zuverlässig.**  
   Belege: [i18n.js:112](C:/dev/SeasonalEdge/landing/js/i18n.js:112), [en.json:2374](C:/dev/SeasonalEdge/landing/i18n/en.json:2374).  
   `_JSON_VER` steht trotz inhaltlicher R2-Änderungen weiterhin auf `v28`.  
   **Gegenprobe:** Frisch gebaute EN-Seite mit einem bestehenden `sa-i18n-v28-en`-Cache ohne die vier neuen R2-Schlüssel geöffnet. Die Rang-Kachel erscheint gemischtsprachig: „not determinableKeine abgeschlossene Episode … Peak in the last 10 years — kein Vergleich möglich.“ Kennung erhöhen und einen Cache-Fall prüfen.

4. **Wichtig – Ein gescheiterter EN-Neubau kann weiterhin grün bleiben.**  
   Beleg: [verify_drawdown.py:495](C:/dev/SeasonalEdge/scripts/verify_drawdown.py:495).  
   Der Rückgabecode von `build_en.py --write` wird ignoriert; danach genügt eine bereits vorhandene Datei.  
   **Gegenprobe ausschließlich im Speicher:** Builder gezielt mit Exit `1` beantwortet und vorhandene Seitenresultate bereitgestellt. **Alle 44 Seitenprüfungen bleiben grün.** Der Wächter muss den erfolgreichen Neubau verlangen, bevor er die EN-Seite prüft.

Die **185 Kernprüfungen bestehen**. Die Seitengegenproben bestätigen insbesondere Recovery, Reset nach Erfolg, Schalttage, Kurzantwort-Schwelle, Methodik und Forward-Basisfallzahlen. Die frisch mit dem Produktionsbuilder im Speicher erzeugte EN-Seite liefert ebenfalls die erwarteten Werte.

Zur EPS-Frage: Ein neues Hoch um `0,5 × EPS` setzt in beiden Kernen den Peak korrekt auf die neuere Sitzung. Auch eine Recovery knapp unter dem alten Hoch wird übereinstimmend toleriert. Der verbliebene konkrete Widerspruch liegt im Schwellvergleich aus Befund 2.

Keine Dateien geändert. Den dateischreibenden Mutationstest habe ich geprüft, nicht ausgeführt.

**NICHT FREIGABEFÄHIG**
