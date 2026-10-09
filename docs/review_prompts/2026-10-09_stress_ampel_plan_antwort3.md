# Codex-Antwort: Plan Stress-Ampel, Runde 3

codex
**v3 ist deutlich verbessert, aber noch nicht freigabefähig.** Geprüft am Stand `95209ec`, einschließlich der bisherigen Einwände und der betroffenen Leser und Schreiber. Keine Codeänderungen, kein Live-DB-Zugriff.

Die Formel, Gewichtung und Mindesthistorie sind jetzt ausreichend festgelegt: erster Score am 777., volle Referenz am 2541. bereinigten Schluss. Die neue Tabelle beseitigt das Risiko einer Mischung aus IF- und Stress-Werten. Drei Lücken bleiben:

1. **HOCH — W2/V8: Datumsabdeckung erkennt einen unvollständigen Neuberechnungslauf nicht.**

   **Konkreter Fall:** `stress_scores` ist bereits vollständig gefüllt. Nach einer historischen Kurskorrektur startet `--full`; einige Batches werden aktualisiert, danach scheitert der Lauf. Sämtliche Datumszeilen existieren weiterhin, also akzeptiert das Frontend die Tabelle. Die Werte stammen aber aus unterschiedlichen Kursdatenständen. Der nachträgliche Rücklesevergleich kann den Fehler melden, verhindert jedoch nicht die Anzeige. W3 prüft nur die letzte Zeile und sichert damit den historischen Verlauf ebenfalls nicht ab.

   **Änderung:** Die Freigabe der DB-Werte zusätzlich an einen erfolgreich abgeschlossenen Berechnungslauf binden. Beispielsweise einen persistenten Status je Ticker **vor dem ersten Write** auf „in Bearbeitung“ setzen und erst nach bestandenem Rücklesevergleich freigeben; währenddessen und nach Fehlern Browserberechnung verwenden. Gleichzeitige Schreiber müssen diesen Zustand gemeinsam respektieren. Alternativ abgeschlossene Berechnungsversionen veröffentlichen. Wächter: bereits vollständige Tabelle, geänderte Kurse, Batchfehler — das Frontend muss auf Browserberechnung wechseln.

2. **HOCH — W2: Reiner Upsert kann die vorgeschriebene exakte Sollmenge nach Kursbereinigungen nicht wiederherstellen.**

   **Konkreter Fall:** Bei 3000 bereinigten Schlüssen stehen 2224 Scorezeilen in der Tabelle. Ein Schluss nach dem 777. wird später gelöscht oder ungültig. Jetzt sind genau 2223 Scorezeilen zulässig. `--full` aktualisiert diese, entfernt aber die überzählige Altzeile nicht. Der Rücklesevergleich scheitert dauerhaft; derselbe Wiederanlauf kann das nicht beheben. Damit widersprechen sich „kein Delete“, exakter Bestandsvergleich und idempotente Reparatur.

   **Änderung:** Die Behandlung nicht mehr gültiger Scoretermine ausdrücklich festlegen. Wenn das Löschverbot bestehen bleibt, etwa Berechnungsversionen mit eigener Kennung verwenden und ausschließlich eine vollständig geprüfte Version lesen; alte Versionen bleiben erhalten. Alternativ das Löschverbot auf `regime_scores` begrenzen und eine geregelte Bereinigung ausschließlich von `stress_scores` vorsehen. Wächter: gültige Kurszeile nach erfolgreichem Erstlauf entfernen, erneut rechnen und die tatsächlich gelesene Datumsmenge prüfen.

3. **MITTEL — W1/W4/V2: Der vorgesehene Python-Lader verwechselt sehr kurze Historien mit Ladefehlern.**

   **Konkreter Fall:** [lade_closes](/C:/dev/Seasonaledge/shared/data.py:237) verlangt standardmäßig mindestens **30** bereinigte Schlüsse und wirft darunter `KursreiheFehlt`. Der ausdrücklich vorgesehene Aufruf `stress_aktuell(lade_closes(t))` erreicht bei 21 gültigen Schlüssen deshalb die Stressberechnung gar nicht. Der Wochenreport würde „fehlt“ statt „zu_kurz“ ausweisen; bereits berechenbare Komponenten gingen verloren. Im Browser wäre dieselbe Reihe hingegen auswertbar.

   **Änderung:** Für sämtliche Stress-Aufrufer `lade_closes(..., mindestens=0)` beziehungsweise einen entsprechend definierten Adapter festlegen. Erfolgreich geladene Reihen mit 0–776 gültigen Schlüssen von tatsächlichen Abruffehlern unterscheiden; Komponenten gemäß W1 ausgeben. Den allgemeinen Standard des Laders für andere Konsumenten beibehalten. Adaptertests für 0, 6, 20, 21, 29 und 777 Schlüsse sowie einen echten Ladefehler ergänzen.

Die bereits entschiedene Gewichtung muss dafür nicht erneut geöffnet werden. Auch Wochenreport, Watchlist-Summen, Health-Check, Completeness und EN-Erzeugung sind grundsätzlich im Umfang enthalten. Die verbleibenden Änderungen betreffen den Wiederanlauf und den konkreten Eingabevertrag.

FREIGABE: nein
