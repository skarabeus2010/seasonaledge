**Noch keine Codefreigabe.** Zwei Vertragslücken und eine relevante Prüflücke bleiben:

1. **P2 – mittel: Duplikate sperren nur einzelne Fenster; die Meldung fehlt.**  
   [shared/skew_rang.py:99](C:/dev/Seasonaledge/shared/skew_rang.py:99) behandelt `None` wie ein leeres Ergebnis und übernimmt andere Fenster desselben Tickers weiterhin. Gegenprobe: 20 aktuelle Punkte plus ein doppeltes Datum bei S−100 ergeben weiterhin `rang.TEST["92"]`; 183/365 fehlen, ohne Diagnose. Der Plan verlangt „Ticker ohne Rang + Meldung“. Bei einem Duplikat den Ticker vollständig verwerfen und Ticker/Datum melden. Die vorgelagerte Cron-Deduplizierung reduziert das Risiko, ersetzt aber diesen vereinbarten Defektschutz nicht.

2. **P2 – mittel: Datumsstrings werden abgeschnitten statt validiert.**  
   [shared/skew_rang.py:72](C:/dev/Seasonaledge/shared/skew_rang.py:72) vergleicht ausschließlich die ersten zehn Zeichen. Reproduziert: Bei Session `2026-09-18` zählt `2026-08-99` als gültige Beobachtung und hebt eine Reihe von 19 auf 20 Punkte. Auch Zeitstempel werden ohne definierte Zeitzonenregel zum Sessiondatum gekürzt. `_fix_session_dates` lässt unparsbare Datumswerte ausdrücklich stehen; dieser Fall erreicht daher den Rangcode. Kanonische, tatsächlich gültige Sessiondaten `YYYY-MM-DD` verlangen; unzulässige Werte ausschließen und diagnostizieren. Die JS-Referenz übernimmt derzeit dieselbe Lücke.

3. **P2 – mittel: Tabellenanbindung bleibt trotz echter Seitenprobe ungeprüft.**  
   [scripts/verify_skew_rang.py:214](C:/dev/Seasonaledge/scripts/verify_skew_rang.py:214) prüft nur Radar-Koordinaten. Die Probe liefert Tabellen-HTML, aber keine Assertion wertet es aus; außerdem enthält die Seitenfixture keinen `skew`-Rang. Ein defektes `_skewMetric()` oder dauerhaft leere Rangspalten blieben damit unbemerkt. Beide Spalten mit unterschiedlichen Rank-/Percentile-Werten und Fenstern prüfen, einschließlich fehlendem `rang` und Sessionabweichung.

Die übrigen Prüfaufträge ergeben:

- **Berechnung/Cron:** Formeln, metrikweises Filtern, Mindestzahl, Rundung und Zeta-Paar passen. Rangbildung erfolgt nach dem Zusammenführen unter derselben Sperre vor History-/Snapshot-Schreiben.
- **History-only-Ticker:** Werden berechnet und im Radar unter „Alle“ berücksichtigt. Ohne Snapshot-Eintrag fehlt die Kategoriezuordnung; in Kategorieansichten erscheinen sie deshalb nicht.
- **Seite:** Keine eigene Rangrechnung und kein Uhranker mehr gefunden. Altdateien ohne `rang` liefern leere Rangspalten und keine Radarpunkte; angezeigt wird allerdings weiterhin der allgemeine Lade-/Backfill-Text.
- **Mail:** Sessionlogik passt. Direkt geprüft: Montag, 19.10., morgens → Freitag, 16.10.; Dienstag nach Labor Day → Freitag, 04.09.; Sonntagslauf → Freitag. Ein Wochenendsnapshot mit dieser Session wird akzeptiert.
- **Wächter:** Rechenkern, Cron und Mail rufen echte Funktionen auf; die Seitenprobe führt echtes Seiten-JS aus. Ergänzen: historisch unterschiedliche gültige Stichprobenumfänge samt Mutation „gemeinsames n“, Duplikat nur im längeren Fenster, ungültiges Datum sowie den vereinbarten Abbruch zwischen History- und Snapshot-Schreiben.

Read-only geblieben. Rechenkern-Fixtures einschließlich Python/JS-Vergleich schreibfrei erfolgreich ausgeführt; Gesamtgate und mutierende Tests nicht erneut ausgeführt. Die gemeldeten 17/17 sind daher hier nicht unabhängig bestätigt.

**FREIGABE (Code): nein**
