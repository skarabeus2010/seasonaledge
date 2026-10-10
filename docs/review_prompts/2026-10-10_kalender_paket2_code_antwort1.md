# Antwort Codex — Paket 2 Code Runde 1 (2026-10-10)

Prompt: [2026-10-10_kalender_paket2_code.md](2026-10-10_kalender_paket2_code.md). model: gpt-6.1-sol

**Urteil: keine Freigabe für Paket 2.** Die Nummernrechnung ist korrekt geprüft; die Statusauskunft braucht Korrekturen und zusätzliche Belege.

Ausgeführt: Wächter **74/74**, unabhängige direkte Zählung für **126 Börse/Jahr-Kombinationen**, vorgegebene Mutationen **12/12 im Speicher erkannt**. Der schreibende Mutationstest wurde nicht ausgeführt. Keine Dateien geändert.

**Befunde**

1. **P2 — Ungeprüfte Vergangenheit wird als „Annahme“ aufgewertet:** [exchange_holidays.py:765](C:/dev/SeasonalEdge/shared/exchange_holidays.py:765).
   Die historischen Intervalle beginnen erst 1950. Reproduziert: `kalender_status("NYSE", 1948)` und entsprechend TSE liefern `annahme`.
   Dagegen dokumentieren [nyse_holidays.py:154](C:/dev/SeasonalEdge/shared/nyse_holidays.py:154) und der TSE-Code ausdrücklich ungeprüfte ältere Historie.
   Die Intervalle müssen bis zum Rechenbeginn 1885 reichen; ebenso bei den übrigen ausdrücklich ungeprüften Altbereichen.

2. **P2 — Bedingte Belegintervalle ohne nachgewiesenen Vollabgleich aktiviert:** [exchange_holidays.py:769](C:/dev/SeasonalEdge/shared/exchange_holidays.py:769).
   EURONEXT 2018–2026, MILAN 2022–2026 und OSLO 2021–2026 heißen bereits `belegt`.
   Die verlinkte [Antwort 4:149](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_xetra_tdoy_plan_antwort4.md:149) dokumentiert jedoch Jahresstichproben; A2 verlangt vor dieser Einstufung vollständige Sollabgleiche.
   Diese sind im Paket nicht nachgewiesen. Abgleiche samt Quelle, Fassung und Marktumfang liefern oder vorerst `annahme` verwenden.

3. **P2 — Statusgrenzen sind nicht wirksam abgesichert:** [verify_handelstag_nummern.py:171](C:/dev/SeasonalEdge/scripts/verify_handelstag_nummern.py:171).
   Zusätzliche Mutation ausschließlich im Speicher: XETRA-Intervall `(2002, 2026, "belegt")` → `(2002, 2100, "belegt")`.
   Ergebnis: **74/74, Exit 0**. Der Wächter bestätigt damit auch unbelegte Zukunftsjahre.
   Je Intervall beide Grenzen und unmittelbar benachbarte Jahre prüfen; diese Mutation ergänzen.

**Antworten**

1. **Vertrag:** umgesetzt. Monats-/Jahreswechsel, vollständige Periodensummen, geschlossene Tage, Reihenfolge, Duplikate und Validierung stimmen.
   Zusätzliche Proben einschließlich 1885/2100, HKEX-/KRX-Tabellenrändern und Jahrhundertschaltregeln stimmen gegen direkte Zählung.
   CRYPTO am 31.12.2000 ergibt `(31, 366, -1, -1, True)`.

2. **Sollkalender:** alle fünf Listen enthalten die vollständigen Werktags-Schließtage der geprüften Jahre.
   XETRA: [2012](https://www.cashmarket.deutsche-boerse.com/resource/blob/281590/2420eeaa55be56d9f11a165184e34597/data/trading-calendar-2012.pdf), [2018](https://www.cashmarket.deutsche-boerse.com/resource/blob/154422/d8296c92db56d4ae96997246ab54d4ae/data/handelskalender-2018.pdf).
   NYSE 2025: [Jahreskalender](https://www.nyse.com/publicdocs/ICE_NYSE_2025_Yearly_Trading_Calendar.pdf) plus [Carter-Sonderschließung](https://beta.nyse.com/publicdocs/nyse/markets/american-options/rule-interpretations/2025/National_Day_of_Mourning_20250102.pdf).
   LSE 2022: [amtlicher Kalender](https://www.gov.uk/bank-holidays) und [Börsenmitteilung](https://docs.londonstockexchange.com/sites/default/files/documents/n1622.pdf).
   TSE 2021: [revidierter NAOJ-Kalender](https://eco.mtk.nao.ac.jp/koyomi/yoko/pdf/yoko2021.pdf) plus [JPX-Schließungsregel](https://www.jpx.co.jp/english/corporate/about-jpx/calendar/index.html).

3. **NumPy-Unabhängigkeit:** für Arithmetik ausreichend; inklusive Endpunkte sind richtig.
   Produktionsfeiertage und Mo–Fr-Wochenmaske bleiben gemeinsame Annahmen. Historische Samstags- oder Sondersitzungen werden dadurch nicht unabhängig geprüft.

4. **Statusintervalle:** Einwände gemäß Befunden 1–2. XETRA 2001 als Annahme und KRX als Annahme sind angemessen.
   HKEX 2026 stimmt als veröffentlichter Plan mit dem [offiziellen Wertpapierkalender](https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2025/ce_SEHK_CT_075_2025.pdf) überein; halbe Sitzungen zählen korrekt als offen.

5. **Mutationen:** die vorhandenen zwölf greifen fachlich. Es fehlt insbesondere die wirksame Absicherung der Statusgrenzen.
   Die nachgewiesen entwichene XETRA-Zukunftsmutation sollte nach Ergänzung der Grenzprüfungen rot werden.
