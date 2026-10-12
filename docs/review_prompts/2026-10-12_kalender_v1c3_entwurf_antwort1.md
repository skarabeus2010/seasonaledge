# Antwort Codex — V1c-3 Entwurf v1 (2026-10-12)

Zu: [Entwurf v1](2026-10-12_kalender_v1c3_entwurf.md)

**Urteil:** Grundsätzlich tragfähig, aber noch keine uneingeschränkte Bau-Freigabe. Die NYSE-Sollfälle stimmen; Zeitsemantik, Abdeckung und Vollständigkeitsprüfung müssen präzisiert werden.

**Befunde (P1/P2)**

- **P2 – Schlusszeit ist nicht eindeutig:** `13:00` muss ausdrücklich den NYSE-Aktien-Kernhandel bezeichnen; Optionen und Spätsitzungen haben andere Zeiten. Bei LSE bezeichnet `12:30` den **Beginn des Schließungsprozesses**, keinen garantierten endgültigen Sitzungsschluss. [NYSE](https://www.nyse.com/trade/hours-calendars), [LSE](https://www.londonstockexchange.com/equities-trading/business-days)
- **P2 – Jahresabdeckung braucht eigene Belege:** Einzeltermine beweisen kein vollständig geprüftes Jahr. Die aktuelle LSE-Tabelle beginnt im August 2026; daraus darf `halbtag_status("LSE", 2026)="belegt"` nicht entstehen. Einzelne belegte Ereignisse dürfen trotzdem erscheinen. [LSE](https://www.londonstockexchange.com/equities-trading/business-days)
- **P2 – Wächter prüft bisher keine Halbtagsvollständigkeit:** Offenheit und Python/JS-Gleichheit erkennen einen gemeinsam ausgelassenen Halbtag nicht. Der Entwurf braucht vollständige unabhängige Jahres-Sollmengen sowie Mutationen für Löschung, falsche Uhrzeit/Zone und fälschlich belegte Abdeckung.
- **Kein P1 gefunden.** Bestand bestätigt: Python `kompat()`/`schliessungen()` und die JS-Schließungsprojektion überspringen `halbtag`; die konservative Betriebskonvention steht ausdrücklich in `markt_offen()`.

**Antworten 1–3 (mit Quellen)**

1. **Ja:** Nur veröffentlichte Termine übernehmen, einschließlich angekündigter Zukunftstermine. Diese sind belegte **Ankündigungen**, keine eigenen Regelprojektionen und kein Nachweis später tatsächlich erfolgten Handels. Die NYSE veröffentlicht derzeit 2026–2028. [NYSE-Kalender](https://www.nyse.com/trade/hours-calendars)
2. **Mindestens 2014–2028 sind durch offizielle Kalenderveröffentlichungen belegbar:** [2014/15](https://ir.theice.com/press/news-details/2013/NYSE-Euronext-Announces-2015-Holiday-Calendar-and-Early-Closings/default.aspx), [2016/17](https://ir.theice.com/press/news-details/2016/NYSE-Group-Announces-2017-Holiday-and-Early-Closings-Calendar/default.aspx), [2018–2020](https://ir.theice.com/press/news-details/2017/NYSE-Group-Announces-2018-2019-and-2020-Holiday-and-Early-Closings-Calendar/default.aspx), [2019–2021](https://ir.theice.com/press/news-details/2018/NYSE-Group-Announces-2019-2020-and-2021-Holiday-and-Early-Closings-Calendar/default.aspx), [2022–2024](https://ir.theice.com/press/news-details/2021/NYSE-Group-Announces-2022-2023-and-2024-Holiday-and-Early-Closings-Calendar/default.aspx), [2023–2025](https://ir.theice.com/press/news-details/2022/NYSE-Group-Announces-2023-2024-and-2025-Holiday-and-Early-Closings-Calendar/default.aspx), [2026–2028](https://www.nyse.com/trade/hours-calendars). Eine vollständige ältere amtliche Halbtagschronik wurde nicht nachgewiesen; Regel 7.2 allein ersetzt keine datierten Halbtagsbelege.
   **Sollfälle 2025:** 03.07., 28.11., 24.12., jeweils `13:00`, `America/New_York`. Alle drei vorgeschlagenen Termine stimmen. [NYSE-Veröffentlichung](https://ir.theice.com/press/news-details/2022/NYSE-Group-Announces-2023-2024-and-2025-Holiday-and-Early-Closings-Calendar/default.aspx)
   **Sollfälle 2026–2028:** 2026: 27.11., 24.12.; 2027: nur 26.11.; 2028: 03.07., 24.11.; jeweils `13:00`. **Kein Juli-Halbtag 2026**, insbesondere keiner am 02.07.; 03.07. ist Vollschließung. [NYSE-Kalender](https://www.nyse.com/trade/hours-calendars)
3. **NYSE reicht für V1c-3:** B4/P3f verlangt die Artunterscheidung und einen Halbtag-Identitätsfall, keine vollständige Halbtagsabdeckung sämtlicher Börsen. LSE darf ausdrücklich ungeprüft bleiben.
   **LSE-Belege sind allerdings vorhanden:** 24./31.12.2026, 24./31.12.2027 sowie **22./29.12.2028**; jeweils Schließungsprozess ab `12:30`, `Europe/London`. „LSE zunächst keine Belege“ entsprechend korrigieren. [LSE Business days](https://www.londonstockexchange.com/equities-trading/business-days)

**Auflagen**

- Markt/Sitzungsphase und Bedeutung von `schlusszeit` verbindlich festlegen; LSE-Schließungsbeginn nicht als endgültigen Schluss speichern.
- Belegreihe mit Abdeckungsintervall, Abrufdatum und reproduzierbarem Quellenstand speichern; vollständige Jahresabdeckung separat prüfen und im JS-Bundle mitführen.
- Schema/Generator/JS-Decoder gemeinsam erweitern; beide neuen Felder bei Nicht-Halbtagen ausdrücklich `null`.
- Unabhängige vollständige Sollmengen, negative Juli-Fälle und wirksame Mutationen verlangen; Uhrzeit-/Zonenänderung muss `ereignisversion` ändern, `kalenderversion` unverändert lassen.
- Momentaufnahme und Betriebskonvention erhalten. Prüfung war read-only gegen Code und Primärquellen; keine Tests ausgeführt.
