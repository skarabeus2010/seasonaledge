# Codex-Antwort: Plan Stress-Ampel, Runde 5

codex
**v5 ist als Umsetzungsplan freigabefähig.** Geprüft am Repository-Stand `95209ec` und gegen die bisherigen Prüfrunden. Keine Codeänderungen und keine Live-DB-Prüfung.

Die drei Einwände aus Runde 4 sind behoben: Jeder Schreiblauf erzeugt eine vollständige Version; historische Korrekturen und entfernte Kurszeilen gehen damit in den nächsten erfolgreichen Lauf ein. Der Unique-Index verhindert parallele aktive Läufe je Ticker. Die Veröffentlichung prüft Status und Lease atomar, sodass ein verdrängter Lauf nicht sichtbar wird. Ungeprüftes Anhängen an fertige Versionen entfällt.

Zwei kleinere Präzisierungen bleiben für die Umsetzung:

1. **NIEDRIG — Y2, SQL-Abnahme: Die vorgesehenen RPC-Prüfungen sind nicht lesend.**  
   **Konkreter Fall:** Bereits `stress_lauf_starten('__TEST__')` legt einen Datensatz an. Der Ablauf-Test benötigt außerdem eine tatsächlich abgelaufene Lease; zwei unmittelbar aufeinanderfolgende Starts prüfen diesen Fall nicht.  
   **Änderung:** Als isolierten, schreibenden Integrationstest kennzeichnen. Ablauf gezielt über eine ausschließlich dem Test dienende Vorbereitung herstellen; Testdaten anschließend auch bei fehlgeschlagenen Assertions entfernen. Den aus Runde 4 übernommenen Paralleltest mit erzwungener Überlappung zusätzlich zum sequenziellen zweiten Start beibehalten.

2. **NIEDRIG — Y2/X1, Abbruchfunktion: Die zugesicherte Unveränderlichkeit fertiger Läufe ausdrücklich im Statusübergang festhalten.**  
   **Konkreter Fall:** Die Veröffentlichung wird serverseitig erfolgreich abgeschlossen, ihre HTTP-Antwort geht verloren. Der Client behandelt das als Fehler und ruft `stress_lauf_abbrechen` auf.  
   **Änderung:** Abbrechen darf ausschließlich `laeuft → abgebrochen` ausführen; bei `fertig` bleibt der Lauf unverändert. Diesen Fall im Wächter ergänzen. Das konkretisiert die bereits verbindliche Y1-Regel, dass fertige Läufe unveränderlich sind.

Gewichtung, Mindesthistorie und Verbraucherumfang müssen nicht erneut geöffnet werden: 0,3/0,3/0,4 ist als beschriebenes heuristisches Maß vertretbar; erster Score am 777. und volle Referenz am 2541. bereinigten Schluss sind konsistent. Ein Ticker mit zwei Jahren Historie bleibt grau, mit verfügbaren Komponenten. Wochenreport, Health-Check, Completeness, Watchlist-Summen und EN-Erzeugung sind im Plan berücksichtigt.

Die Freigabe gilt dem Plan. Ob SQL-Rechte, Statusübergänge, tatsächliche Leser und Fehlerpfade diese Regeln einhalten, ist anschließend am Code und mit den vorgesehenen Integrationstests nachzuweisen.

FREIGABE: ja
