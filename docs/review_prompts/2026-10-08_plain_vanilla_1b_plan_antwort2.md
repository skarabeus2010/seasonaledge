codex
Geprüft gegen `6170252`; keine Dateien geändert. v2 löst die meisten Einwände aus v1. Folgende Punkte bleiben vor dem Code offen:

1. **Hoch — T3/L2: Eine Lücke über den Hebelwechsel wird fälschlich als exakt behandelt.**  
   Fehlt S⁻1, kann ein beobachtetes Intervall `a < S⁻1 < b` liegen. T3 verwendet dafür 1x; L2 setzt deshalb kein `naeherung`. Die vorgesehene Aufstockung innerhalb des Intervalls lässt sich jedoch ohne Zwischenkurs nicht rekonstruieren. Beispiel: 26.11.2024 Close 100, fehlender 27.11. mit tatsächlichem Close 110, 29.11. Close 121. Der Regelpfad ergibt `1,1 × 1,2 − 1 = 32 %`, die Ersatzbewertung 21 %.  
   **Änderung:** Die Ersatzbewertung mit dem Hebel nach Close a beibehalten, aber zusätzlich jedes Intervall mit übersprungenem Hebelwechsel als Näherung markieren. „Bei h = 1 exakt“ gilt nur bei durchgehendem 1x-Regelpfad. Diesen Fall ausdrücklich in Wächter und Mutationen aufnehmen.

2. **Hoch — T1: Die Python-Näherungsliste hat weitere aktive Konsumenten.**  
   `_US_HOLIDAYS_MONTH_DAY` wird auch von `_is_near_holiday` für Ultimate Monthly und von `_compute_kti_daily` verwendet: [plain_vanilla.py:697](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:697), [plain_vanilla.py:893](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:893). Einfaches Entfernen bricht diese Strategien; ihre Umstellung verändert zusätzliche Ergebnisse.  
   **Änderung:** Den Umfang ausdrücklich festlegen. Für eine begrenzte Phase 1B die bisherige Liste als benannte Legacy-Regel dieser Konsumenten erhalten und nur One-Day-Holiday/UHTS umstellen. Alternativ alle Konsumenten migrieren und deren Änderungen gesondert prüfen und messen. „Betraf One-Day-Holiday und UHTS“ entsprechend korrigieren.

3. **Hoch — E1/S2: Der Rückfall auf 1x passt nicht zu allen Python-Strategien.**  
   `calc_kti_leveraged` erzeugt bereits gehebelte Trades mit `leverage`, aber ohne täglichen `hebel`-Pfad: [plain_vanilla.py:938](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:938). E1 würde diese im Konto mit 1x bewerten, während die Trade-Rendite gehebelte Werte enthält. Der beschreibende Durchschnittshebel rekonstruiert keinen täglichen Pfad.  
   **Änderung:** Den Geltungsbereich der Tagesauswertung ausdrücklich auf unterstützte Strategien begrenzen und für KTI-Hebel keinen scheinbar gültigen 1x-Kontowert liefern; oder dessen tatsächlichen Hebelpfad mit aufnehmen. Dieselbe Grenze für die neue Stop-Renditeberechnung festlegen und prüfen.

4. **Mittel — K3: Mehrere feste Sollwerte sind falsch formuliert.**  
   Der 03.10.2020 war Samstag, der 03.10.2021 Sonntag: Beide sind keine Sitzungen. Auch „die Nachbartage = offen“ funktioniert beispielsweise um Heiligabend und um einen Pfingstmontag nicht.  
   **Änderung:** Feiertagsstatus und Handelstagsstatus getrennt prüfen. Für den 3. Oktober 2020/2021 gilt „keine zusätzliche Feiertagsschließung, aber Wochenende“. Für Nachbartage konkrete Datums-/Sollwertpaare verwenden; keine pauschale Offen-Annahme.

5. **Mittel — K1/K4/K5: Die globale historische Reichweite ist größer als der geprüfte Bereich.**  
   Das Entfernen von `year >= 2011` verändert den gemeinsamen Kalender auch vor 2000. `backfill_tdoy` liest und berechnet die gesamte Tickerhistorie, ohne Jahresgrenze: [backfill_tdoy.py:88](C:/dev/Seasonaledge/scripts/backfill_tdoy.py:88). Der zeilenbasierte Kalender von `/plain-vanilla` verhindert diese Änderung gespeicherter Zähler nicht.  
   **Änderung:** Für diese Phase die globale Korrektur und den Backfill auf den belegten beziehungsweise ausdrücklich angenommenen Zeitraum begrenzen, oder die frühere Historie zusätzlich belegen. Die tatsächlichen Änderungen getrennt für TDOM/TDOY zählen: Der vorhandene Backfill meldet geschriebene, nicht inhaltlich geänderte Zeilen. Außerdem verschiebt jede Schließung TDOY bis Jahresende, TDOM nur bis Monatsende; mehrere Schließungen wirken kumulativ.

Zu deinen besonders hervorgehobenen Fragen:

- **K2:** „24.12.2001 geschlossen, nicht primär belegt“ ist als ausdrücklich dokumentierte Kalenderannahme vertretbar. Spätere offizielle Kalender, etwa [2004](https://www.cashmarket.deutsche-boerse.com/resource/blob/286010/e0ff72fcb9036a40eca9030e82d83549/data/trading-calendar-2004.pdf), stützen die Plausibilität, beweisen aber 2001 nicht. „^GDAXI: 0 fehlende Sitzungen“ muss daher als Ergebnis **unter dieser Annahme** bezeichnet werden.
- **T3:** Bei vorhandenen Kursen stimmt die Zuordnung: Das erste Intervall nach Einstieg ist 1x, das erste nach Aufstockung 2x. Wochenenden ändern daran nichts.
- **E1:** Das Maximum ist konsistent. Stoppt ein Fenster am Close b, trägt es noch zum Intervall a→b bei. Ab b→c fällt es weg; ein weiterhin laufendes 2x-Fenster hält das Konto trotzdem bei 2x.
- **K4:** Für die gespeicherten `prices.tdom/tdoy` reicht der begrenzte Recompute. Eine zusätzliche zwingende Neuberechnung von `tdom_stats`/`tdoy_stats` ergibt sich aus dem aktuellen Code nicht: Deren Builder zählen Kurszeilen selbst. Das sollte im Plan ausdrücklich stehen.
- **Messung:** Einen eigenen Schritt **S — Python OHLC→Close-Stops** ergänzen. Dessen Abweichungen werden durch K/T/H/E nicht erklärt.

FREIGABE: nein
