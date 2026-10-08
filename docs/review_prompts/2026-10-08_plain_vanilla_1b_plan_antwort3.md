codex
Geprüft gegen `6170252` und die beiden vorherigen Reviews; keine Dateien geändert. **v3 ist als Implementierungsplan freigabefähig.** Die ausdrücklich vorrangigen Festlegungen V1–V6 schließen die bisherigen Einwände.

1. **Hoch, erledigt — V1 / T3 / L2: Näherung bei übersprungenem Hebelwechsel.**  
   Die Prüfung auf Trade-Ebene erfasst jetzt auch ein Lückenintervall, dessen Ersatzbewertung 1x verwendet, obwohl darin die Aufstockung liegen sollte. Der konkrete November-2024-Wächter mit 21 % und `naeherung = true` trifft den Fehler. **Änderung:** V1 wie vorgesehen anstelle der alten h=2-Bedingung implementieren; keine zusätzliche Modelländerung nötig.

2. **Hoch, erledigt — V2 / T1: Weitere Python-Konsumenten der Feiertagsliste.**  
   Die Legacy-Liste für Ultimate Monthly und KTI bleibt erhalten; nur One-Day-Holiday und UHTS erhalten exakte Anker. **Änderung:** Umbenennung und Vorher-/Nachher-Wächter wie festgelegt übernehmen. „One-Day-Holiday unverändert“ bezeichnet dabei die Sitzungsregel beziehungsweise den bisherigen JS-Pfad; die Python-Termine können sich durch die neuen Anker ändern.

3. **Hoch, erledigt — V3 / S2 / E1: Hebel ohne Tagespfad.**  
   Die drei Fälle sind ausreichend getrennt. `taeglich = null` verhindert für KTI-Hebel einen scheinbar gültigen Kontowert. Die Stop-Rendite mit dem vorhandenen `leverage` ist eine ausdrücklich festgelegte Ersatzrechnung, kein rekonstruierter täglicher KTI-Pfad. **Änderung:** Null-Behandlung einschließlich Chart und beider Streamlit-Ansichten durchziehen; kein Rückfall auf Trade-Equity oder 1x.

4. **Mittel, erledigt — V4 / K3: Kalender-Sollwerte.**  
   Feiertagsstatus und Handelstagsstatus werden korrekt getrennt; Wochenenden sind damit keine falschen Offen-Sollwerte mehr. **Änderung:** Die konkreten Datumspaare wie angekündigt wörtlich in den Wächter aufnehmen.

5. **Mittel, erledigt — V5 / K1 / K4: Historische Reichweite und Backfill.**  
   Die Grenze ab 2001 mit der einzelnen Ausnahme 03.10.2000 vermeidet unbelegte Änderungen der früheren Historie. [backfill_tdoy.py](C:/dev/Seasonaledge/scripts/backfill_tdoy.py:40) berechnet bereits **TDOM und TDOY**. Der geplante Trockenlauf muss zusätzlich gespeicherte Werte laden und tatsächliche Differenzen prüfen; die vorhandene Anzahl geschriebener Zeilen genügt nicht. **Änderung:** V5 umsetzen. Für `tdom_stats` und `tdoy_stats` ist wegen ihrer eigenen Kurszeilenzählung kein zusätzlicher Recompute erforderlich.

6. **Mittel, erledigt — V6 / Messung: Python-Stopwechsel.**  
   Der eigene Schritt S macht die OHLC→Close-Abweichungen zurechenbar. **Änderung:** S als separaten Zwischenlauf aufnehmen, wie festgelegt.

Zu den besonders genannten Modellfragen:

- **K2:** 24.12.2001 geschlossen ist als dokumentierte, nicht primär belegte Annahme vertretbar. Der offizielle [Kalender 2004](https://www.cashmarket.deutsche-boerse.com/resource/blob/286010/e0ff72fcb9036a40eca9030e82d83549/data/trading-calendar-2004.pdf) bestätigt die spätere Regel, beweist aber 2001 nicht. Die Einschränkung „unter dieser Annahme“ bleibt erforderlich.
- **T3:** Der Hebel nach Close a ist konsistent: erstes Intervall nach Einstieg 1x, erstes nach Aufstockung 2x; Wochenenden ändern diese Zuordnung nicht.
- **E1:** Ein am Close b gestopptes Fenster zählt noch für a→b, anschließend nicht mehr. Ein weiter laufendes 2x-Fenster hält das Konto auch für b→c bei 2x.

FREIGABE: ja
