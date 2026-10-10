# Antwort Codex — Paket 3 Code Runde 2 (2026-10-10)

Prompt: [2026-10-10_kalender_paket3_code_runde2.md](2026-10-10_kalender_paket3_code_runde2.md). model: gpt-6.1-sol

**Urteil: Keine Freigabe.** Die ursprünglichen Befunde sind im getesteten Normalpfad behoben; zwei Fehlerpfade und eine Wächterlücke bleiben.

**Befunde**

- **[P1] Intraday veröffentlicht teilweise berechnete Nummern.** [intraday_refresh.py:172](C:/dev/SeasonalEdge/scripts/intraday_refresh.py:172): Der Fehlerpfad entfernt bereits gesetzte TDOM/TDOY-Spalten nicht. Gezielt ausgelöster Kalenderfehler am zweiten Datum → Exit 1, aber der erste Upsert-Datensatz enthält weiterhin `tdoy=1, tdom=1`. Nummern erst nach vollständig erfolgreicher Berechnung übernehmen oder beim Fehler vollständig entfernen.

- **[P2] Globaler Health-Abbruch meldet ungeprüfte Ticker als erfolgreich.** [nightly_refresh.py:291](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:291): Scheitert `get_client()` vor der Schleife, bleiben `ungeprueft` und `errors` leer. Echter Hauptlauf mit offline simuliertem Initialisierungsfehler → Exit 1, jedoch `refresh_log`: **2/2 erfolgreich**, `errors=[]`. Nicht geprüfte Ticker und den Phasenfehler auch im Ergebnisvertrag erfassen.

- **[P2] Der Wächter schützt den Nightly-Exit nicht.** [verify_kalender_fehlerweitergabe.py:104](C:/dev/SeasonalEdge/scripts/verify_kalender_fehlerweitergabe.py:104) prüft nur `health_check()`. Ausschließlich im Arbeitsspeicher `_FEHLGESCHLAGEN.extend(_hc["gescheitert"])` entfernt → weiterhin **8/8**, Exit 0. Den echten Nightly-Hauptlauf einschließlich Log und Exit prüfen und diese Mutation ergänzen.

**Antworten**

1. **Befunde behoben?** Intraday-Toleranz, Nightly-Einzelfehler und `.BR`/`.LS`: ja. Nightly-Hauptlauf mit ungültiger Börsenzuordnung bestätigt Exit 1 und **1/2 erfolgreich**. Die verbleibenden Fälle stehen oben.

2. **Herausziehen verhaltensgleich?** Der bisherige Prüf-/Nachladeablauf und seine Variablen bleiben erhalten; die beabsichtigten Fehleränderungen greifen. Beim globalen Abbruch ist die Erfolgs-/Fehlermetadaten-Behandlung noch unvollständig.

3. **Vor dem Commit?** Die drei Punkte beheben und gezielt absichern. Bestätigt: Ticker **56/56**, Fehlerweitergabe **8/8**, Sollfälle **86/86**, Nummern **86/86**, Stress ohne Snapshot **32/32**; **370** Bestandszuordnungen unverändert. Im Speicher: **7/7 + 15/15** Mutationen erkannt, **4/4** Gegenproben verworfen. Python 3.12 steht vor den Deploy-Wächtern.

Keine Dateien oder Datenbankdaten geschrieben.
