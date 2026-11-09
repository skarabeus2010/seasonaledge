# Codex-Antwort Runde 2 (gpt-6-astra, 2026-11-09)

**FREIGABE (Code): ja**

**Befunde:** keine neuen P1/P2/P3. Die beiden Befunde aus Runde 1 sind behoben.
- **P2 Watchlist:** Filter greift vor Limit, Historie und OHLC-Abruf. Gegenprobe mit Originalfunktion und Attrappen, Limit 1: nur SPY; ohne Ausschluss erscheint ATKR. RPC-Eingabe bleibt unverändert.
- **P3 Query-Formen:** Fremde Queries bleiben stehen und erzeugen einen Befund. Release-Verarbeitung im Arbeitsspeicher: **215 HTML-Dateien, 0 Fehler**.
- **Holidays-Fixture:** Die 373 Ticker entsprechen exakt dem V2-Commit `30b8abf`. Prüfung: **840 Gruppen, 0 Abweichungen**. Die eingefrorene Ausgabe bleibt unverändert.
- **Generierte Daten:** `tickers.json` verliert ausschließlich ATKR; das Kalender-Bundle zusätzlich nur den daraus folgenden Versionshash.
Zur Frage nach weiteren Momentaufnahmen:
| Prüfung | Abhängigkeit von Live-Tickerliste |
|---|---|
| `kalender_momentaufnahme` | Keine; 3.024 Börsen-Jahre ohne Abweichung |
| `opex_momentaufnahme` | Keine; 2.592 Monate und 12 Stichproben bestanden |
| `converter_alt` | Eingabetage aus Fixture |
| Ticker-Börse-Fixture | Bestandsprüfung nutzt Fixture-Schlüssel; neue SYMBOLS separat. 56/56 bestanden |
| `header_alt_seiten` | Seitenprobe kann Live-Tickerdaten laden; eingefroren werden Header festgelegter Seiten, kein Hash des gesamten Universums. Kein entsprechender ATKR-Folgefehler gefunden |
`Disallow: /landing/data/*/$` passt für die genannten Ordneradressen; darunterliegende JSON-Dateien werden dadurch nicht gesperrt. [Google-Spezifikation](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec)
Read-only eingehalten. Vollständiges Gate, Builder und schreibende Mutationstests wurden hier nicht erneut ausgeführt; deren gemeldete Ergebnisse sind nicht als eigene Testläufe gezählt.
tokens used
70.044
**FREIGABE (Code): ja**
