# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

1. **P2 – Konstanter Pfad wird als perfekt korreliert gewertet.**  
   [shared/saison_score.py:100](C:/dev/Seasonaledge/shared/saison_score.py:100), [landing/js/saison-score.js:44](C:/dev/Seasonaledge/landing/js/saison-score.js:44).  
   **Eingabe:** Montag–Freitag vom 01.01.2000 bis 11.02.2025, durchgehend `close=0.17`, Ticker `SPY`. Beide Kerne liefern `status=ok`, Score **2,5**, Musterkorrelationen und Konformität **1**. Erwartet ist `zu_wenige_musterjahre`. Die Normierung ergibt `99.99999999999999`; die Mittelwertsummation erzeugt trotz konstantem Pfad eine positive Restvarianz. **Auch die NumPy-Referenz bestätigt das falsche Ergebnis.**  
   **Änderung:** Konstanz im tatsächlich verglichenen Präfix ausdrücklich vor der Mittelwertrechnung erkennen, beispielsweise über identische Minimal-/Maximalwerte. In beiden Kernen und unabhängig in der Referenz absichern; diesen Dezimalkurs als Regression aufnehmen.

2. **P2 – Referenz beherrscht den vorgeschriebenen Nullgewichtsfall nicht.**  
   [scripts/verify_saison_score.py:132](C:/dev/Seasonaledge/scripts/verify_saison_score.py:132).  
   **Eingabe:** Tägliche Kurse 2000–2024 mit `close=100−(Tagesnummer−1)/8`; 2025 bis 20.01. mit `close=100+(Tagesnummer−1)/8`. Alle Musterkorrelationen sind exakt `−1`. Beide Kerne liefern korrekt `gewichte_null`; die Referenz wirft **ZeroDivisionError**. Der entsprechende Pflichtfall fehlt im Wächter.  
   **Änderung:** Gewichtssumme vor der Division prüfen und `nicht_berechenbar/gewichte_null` zurückgeben; diesen analytischen Fall mit festem Sollstatus ergänzen.

3. **P2 – Mutationsnachweis für Gleichstände ist wirkungslos; Tag-366-Mutation ist ungeeignet.**  
   [scripts/verify_saison_score.py:310](C:/dev/Seasonaledge/scripts/verify_saison_score.py:310), [scripts/verify_saison_score.py:317](C:/dev/Seasonaledge/scripts/verify_saison_score.py:317).  
   **Eingabe:** Die vorhandenen synthetischen Fälle, jeweils mit umgekehrter Gleichstandsreihenfolge beziehungsweise entfernter Begrenzung von `d`. Beide Mutationen bestehen weiterhin **15/15** Prüfungen. `fall_konstant` erreicht die Sortierung mit keinen gültigen Kandidaten und kann deren Reihenfolge niemals prüfen. Die Tag-366-Mutation bleibt im Ergebnis wirkungslos: Der Pfad hat ohnehin 365 Elemente, und Pearson verwendet die kürzere Länge.  
   **Änderung:** Nichtkonstante, exakt identische Musterpräfixe mit fest erwarteter Jahresreihenfolge ergänzen. Für Tag 366 eine tatsächlich ergebnisverändernde Mutation verwenden. Halbaufwärtsrundung zusätzlich deterministisch prüfen, etwa `1.25 → 1.3`, statt auf zufällige Snapshot-Treffer zu vertrauen.

4. **P3 – D2-Prüfumfang unterschreitet den freigegebenen Plan.**  
   [scripts/verify_saison_score.py:152](C:/dev/Seasonaledge/scripts/verify_saison_score.py:152), [scripts/verify_saison_score.py:282](C:/dev/Seasonaledge/scripts/verify_saison_score.py:282).  
   **Eingabefälle:** Der ausdrücklich verlangte 30.12. eines Schaltjahres und ein einzelner Sprung mit analytisch festgelegter Fensterrendite fehlen. Der Snapshot wird jeden **21.** statt jeden **5.** Handelstag geprüft.  
   **Änderung:** Diese Fälle ergänzen und das vereinbarte Raster 2005–2025 herstellen oder die Abweichung ausdrücklich freigeben lassen.

Die Kursquotienten als kanonischen Jahrespfad halte ich grundsätzlich für vertretbar; Befund 1 muss dabei behoben werden. Die Fensterbildung ausschließlich für abgeschlossene Jahre ist korrekt. Bei Summenreihenfolge und Rundungsformel sehe ich keinen konkreten sprachabhängigen Fehler; `>> 1` ist bei üblichen täglichen Kursreihen unkritisch.

Prüfung ausschließlich lesend, Testanpassungen nur im Speicher: vorhandene synthetische Prüfungen **15/15**; die beiden Fehlerfälle zusätzlich in Python und echtem JS reproduziert. Den Snapshot-Lauf habe ich nicht wiederholt.

FREIGABE: nein
