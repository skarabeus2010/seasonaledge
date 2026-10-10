# Antwort Codex — Paket 2 Code Runde 2 (2026-10-10)

Prompt: [2026-10-10_kalender_paket2_code_runde2.md](2026-10-10_kalender_paket2_code_runde2.md). model: gpt-6.1-sol

**Urteil**

**Freigabe für Paket 2.** Die drei Befunde aus Runde 1 sind behoben. Keine neuen blockierenden Befunde gefunden.

**Befunde**

Keine offenen Codebefunde im geprüften Diff und den beiden neuen Wächterdateien.

**Antworten**

1. **Befunde behoben:** Ungeprüfte Altbereiche beginnen jetzt 1885; die fünf nur stichprobenhaft geprüften Kalender bleiben `annahme`. Die unabhängige Bruchpunkt-Tabelle prüft sämtliche 216 Jahre und 13 Börsen. Die zuvor entwichene XETRA-Zukunftsmutation wird erkannt.

2. **NYSE 1971–2025 ist im dokumentierten Prüfstand haltbar.** [WAHLEN.md:42](/C:/dev/SeasonalEdge/docs/WAHLEN.md:42) dokumentiert bereits den vollständigen Abgleich mit `^GSPC`/`^DJI`; Paket 1 übernimmt die Ausnahmen. Zusätzlich geprüft: **13.880 Tage 1971–2008, keine Abweichung** gegenüber einer separat aus der [historischen NYSE-Veröffentlichung](https://www.ltadvisors.net/Info/research/closings.pdf) hergeleiteten Referenz. Für **2026–2028** ebenfalls vollständiger Tagesvergleich ohne Abweichungen gegen den [veröffentlichten NYSE-Plan](https://www.nyse.com/trade/hours-calendars). Den historischen Kursabgleich habe ich nicht erneut live ausgeführt.

3. **Vor dem Commit keine weitere Korrektur erforderlich.** Die Aufnahme ins Deploy-Gate bleibt wie vorgesehen Paket 3 vorbehalten.

Ausgeführt: Wächter **86/86**, Mutationen **15/15 ausschließlich im Speicher**, Gegenproben **2/2 korrekt verworfen**. Den schreibenden Mutationstest nicht gestartet; dessen atomaren Dateischreibweg und behauptete Laufdeterministik damit nicht erneut bestätigt. Keine Dateien geschrieben.
