# Antwort Codex Runde 4 — P1a (2026-10-10)

Prompt: [2026-10-10_xetra_tdoy_plan_v4.md](2026-10-10_xetra_tdoy_plan_v4.md). model: gpt-6.1-sol

**Urteil**

**Keine Freigabe für P1a in der vorliegenden Fassung.** Die Richtung stimmt, aber K4 widerspricht K6, K2 überschätzt die vorhandenen Belege, und K3 würde mehrere bestehende Fehlerpfade aktivieren, die anschließend Erfolg melden oder Ersatzwerte verwenden.

Mit Python **3.14.3** bestätigt: **11 LSE- und 27 TSE-Abweichungen** im Tagesvergleich 2000–2030 sowie zusätzliche HKEX-, KRX- und NYSE-Fälle. A2 und A3 sind unten bearbeitet. **A1 ist hinsichtlich der verlangten jährlichen Archivstichproben noch nicht vollständig belegt:** Die verbleibenden Lücken stehen ausdrücklich in der Abdeckungstabelle. Zukünftige Regelprojektionen sind außerdem keine Bestätigung tatsächlich stattfindender Sitzungen.

Es wurden keine Dateien geschrieben und keine Datenbankläufe ausgeführt. Der versionierte Arbeitsbaum ist unverändert.

**A1 Abweichungstabelle**

„Offiziell“ bezeichnet hier den veröffentlichten Handelskalender beziehungsweise eine nachvollziehbare Ableitung aus amtlichem Feiertagskalender und Börsenregel. Ein verkürzter Handelstag zählt als **offen**. Die Python-Spalte stammt aus dem ausgeführten Produktionspfad `shared.exchange_holidays.is_trading_day`.

Für LSE und TSE wurden jeweils **11.323 Kalendertage** verglichen. Die folgenden Tabellen enthalten sämtliche Differenzen gegenüber der separat hergeleiteten Referenz. Für zukünftige Jahre gilt dabei der derzeit veröffentlichte Kalender beziehungsweise die kenntlich gemachte Regelprojektion; zukünftige Sonderschließungen sind damit nicht ausgeschlossen.

LSE-Quellen:

- **L1:** [LSE Business Days](https://www.londonstockexchange.com/equities-trading/business-days) und [England-and-Wales-Kalender samt Ersatzregel](https://www.gov.uk/bank-holidays).
- **L2:** [Amtliche Proklamation für den 3. Januar 2000](https://www.thegazette.co.uk/notice/L-55541-3).
- **L3:** [Amtliche Proklamation für das Jubiläum 2002](https://www.thegazette.co.uk/notice/L-56043-1001).
- **L4:** [Amtliche Proklamation zur Hochzeit 2011](https://www.thegazette.co.uk/notice/L-59637-1268656).

| Börse | Datum | Offiziell | Python | Ursache / Quelle |
|---|---|---|---|---|
| LSE | 2000-01-03 | geschlossen | offen | Neujahrsersatz, L2 |
| LSE | 2002-06-03 | geschlossen | offen | Zusätzlicher Jubiläumstag, L3 |
| LSE | 2004-12-28 | geschlossen | offen | Weihnachtsersatz, L1; Regelableitung |
| LSE | 2005-01-03 | geschlossen | offen | Neujahrsersatz, L1; Regelableitung |
| LSE | 2010-12-28 | geschlossen | offen | Weihnachtsersatz, L1; Regelableitung |
| LSE | 2011-01-03 | geschlossen | offen | Neujahrsersatz, L1 |
| LSE | 2011-04-29 | geschlossen | offen | Royal Wedding, L4 |
| LSE | 2021-12-28 | geschlossen | offen | Weihnachtsersatz, L1 |
| LSE | 2022-01-03 | geschlossen | offen | Neujahrsersatz, L1 |
| LSE | 2027-12-28 | geschlossen laut veröffentlichtem Kalender | offen | Weihnachtsersatz, L1 |
| LSE | 2028-01-03 | geschlossen laut veröffentlichtem Kalender | offen | Neujahrsersatz, L1 |

Keine weiteren Differenzen ergaben sich für 2001, 2003, 2006–2009, 2012–2020, 2023–2026 und in der Regelprojektion 2029–2030.

**Wichtige Gegenproben:** Der Ersatzmontag bei **Freitag 25.12. / Samstag 26.12.** ist bereits richtig umgesetzt: 2009, 2015, 2020 und 2026 jeweils der 28. Dezember. Auch 2016-12-27, 2022-09-19 und 2023-05-08 sind bereits geschlossen. K1 darf diese Fälle nicht verschieben. Die England-and-Wales-Regel und die veröffentlichten Kalender stützen diese Unterscheidung. [Bank Holidays](https://www.gov.uk/bank-holidays)

Der LSE-Ausfall am **2000-04-05** ist keine zusätzliche Ganztagsschließung: Der Markt öffnete am Nachmittag. Der aktuelle Rückgabewert `True` ist für die Tagesnummerierung richtig. [LSEG-Geschäftsbericht 2000](https://www.lseg.com/content/dam/lseg/en_us/documents/investor-relations/annual-reports/lseg-annual-report-2000.pdf)

**1999-12-31** liegt außerhalb des verlangten Vergleichszeitraums. Die Proklamation belegt einen Bank Holiday; sie allein ersetzt keinen historischen Nachweis der LSE-Ganztagsschließung. Diesen Fall daher erst nach einem passenden LSE-Beleg ändern. [Proklamation](https://www.thegazette.co.uk/notice/L-55541-3)

TSE-Quellen und Ableitung:

Die JPX-Regel schließt den Aktienmarkt an nationalen Feiertagen sowie am 2./3. Januar und 31. Dezember. Offene Tage werden aus dieser Regel und dem vollständigen nationalen Feiertagskalender abgeleitet. [JPX-Handelskalender](https://www.jpx.co.jp/english/corporate/about-jpx/calendar/index.html)

- **J1:** [NAOJ-Historie der Gesetzesänderungen](https://eco.mtk.nao.ac.jp/koyomi/yoko/appendix.html): Meerestag und Tag der älteren Menschen erst ab 2003 auf Montag; Ersatzregel geändert ab 2007.
- **J2:** [NAOJ-Kalender 2003](https://eco.mtk.nao.ac.jp/koyomi/yoko/pdf/yoko2003.pdf).
- **J3:** [JPX-Schließung zur Thronbesteigung 2019](https://www.jpx.co.jp/news/1030/20190115-01.html) und [revidierter NAOJ-Kalender 2019](https://eco.mtk.nao.ac.jp/koyomi/yoko/pdf/yoko2019.pdf).
- **J4:** [NAOJ-Kalender 2020](https://eco.mtk.nao.ac.jp/koyomi/yoko/pdf/yoko2020.pdf).
- **J5:** [revidierter NAOJ-Kalender 2021](https://eco.mtk.nao.ac.jp/koyomi/yoko/pdf/yoko2021.pdf).
- **J6:** [JPX-Mitteilung zur vollständigen Schließung am 1. Oktober 2020](https://www.jpx.co.jp/news/1030/20201001-06.html).

| Börse | Datum | Offiziell | Python | Ursache / Quelle |
|---|---|---|---|---|
| TSE | 2000-07-17 | offen | geschlossen | Meerestag damals am 20. Juli, J1 |
| TSE | 2000-07-20 | geschlossen | offen | Meerestag, J1 |
| TSE | 2000-09-15 | geschlossen | offen | Tag der älteren Menschen, J1 |
| TSE | 2000-09-18 | offen | geschlossen | Montagregel noch nicht gültig, J1 |
| TSE | 2001-07-16 | offen | geschlossen | Meerestag damals am 20. Juli, J1 |
| TSE | 2001-07-20 | geschlossen | offen | Meerestag, J1 |
| TSE | 2001-09-17 | offen | geschlossen | 15. September war Samstag; kein Montagsersatz, J1 |
| TSE | 2002-07-15 | offen | geschlossen | Montagregel noch nicht gültig, J1 |
| TSE | 2003-05-06 | offen | geschlossen | Historische Ersatzregel, J2 |
| TSE | 2019-04-30 | geschlossen | offen | Thronbesteigung, J3 |
| TSE | 2019-05-01 | geschlossen | offen | Thronbesteigung, J3 |
| TSE | 2019-05-02 | geschlossen | offen | Thronbesteigung, J3 |
| TSE | 2019-10-22 | geschlossen | offen | Inthronisierung, J3 |
| TSE | 2019-12-23 | offen | geschlossen | Alter Kaisergeburtstag entfällt, J3 |
| TSE | 2020-07-20 | offen | geschlossen | Meerestag verschoben, J4 |
| TSE | 2020-07-23 | geschlossen | offen | Verschobener Meerestag, J4 |
| TSE | 2020-07-24 | geschlossen | offen | Verschobener Sporttag, J4 |
| TSE | 2020-08-10 | geschlossen | offen | Verschobener Bergtag, J4 |
| TSE | 2020-08-11 | offen | geschlossen | Bergtag verschoben, J4 |
| TSE | 2020-10-01 | geschlossen | offen | Ganztägiger Systemausfall, J6 |
| TSE | 2020-10-12 | offen | geschlossen | Sporttag verschoben, J4 |
| TSE | 2021-07-19 | offen | geschlossen | Meerestag verschoben, J5 |
| TSE | 2021-07-22 | geschlossen | offen | Verschobener Meerestag, J5 |
| TSE | 2021-07-23 | geschlossen | offen | Verschobener Sporttag, J5 |
| TSE | 2021-08-09 | geschlossen | offen | Ersatz für verschobenen Bergtag am Sonntag, J5 |
| TSE | 2021-08-11 | offen | geschlossen | Bergtag verschoben, J5 |
| TSE | 2021-10-11 | offen | geschlossen | Sporttag verschoben, J5 |

Keine weiteren Differenzen ergaben sich für 2004–2018 und 2022–2027 sowie in der Regelprojektion 2028–2030.

Die jährlichen NAOJ-Veröffentlichungen 2001–2027 wurden herangezogen; das Archiv enthält auch 2000, dessen Scan nicht vollständig als Text auslesbar war. Für 2028–2030 sind die Tagundnachtgleichen eine amtliche astronomische Vorausberechnung, keine bereits endgültig veröffentlichte Feiertagsfestsetzung. NAOJ erläutert ausdrücklich die Veröffentlichung im Februar des Vorjahres. [NAOJ-Archiv](https://eco.mtk.nao.ac.jp/koyomi/yoko/archives.html), [Vorausberechnung](https://www.nao.ac.jp/faq/a0301.html), [Veröffentlichungsverfahren](https://eco.mtk.nao.ac.jp/koyomi/yoko/)

Weitere Börsen:

Für HKEX gelten die veröffentlichten Feiertage des Wertpapiermarkts. Für KRX belegt die offizielle KOSPI-Regel die Übernahme der staatlichen Feiertage; die koreanischen Fälle mit „Regelableitung“ verbinden diese Regel mit amtlichen Datumsangaben. [HKEX-Kalender 2016](https://www.hkex.com.hk/-/media/hkex-market/services/circulars-and-notices/participant-and-members-circulars/sehk/2015/ct03915e), [KRX-KOSPI Holiday Rules](https://global.krx.co.kr/contents/GLB/06/0602/0602010201/GLB0602010201T1.jsp)

| Börse | Datum | Offiziell | Python | Quelle |
|---|---|---|---|---|
| HKEX | 2015-02-19 | geschlossen | offen | [Amtlicher Kalender 2015](https://www.gov.hk/en/about/abouthk/holiday/2015.htm), Börsenregel |
| HKEX | 2015-02-20 | geschlossen | offen | [Amtlicher Kalender 2015](https://www.gov.hk/en/about/abouthk/holiday/2015.htm), Börsenregel |
| HKEX | 2015-04-07 | geschlossen | offen | [Amtlicher Kalender 2015](https://www.gov.hk/en/about/abouthk/holiday/2015.htm), Börsenregel |
| HKEX | 2015-05-25 | geschlossen | offen | [Amtlicher Kalender 2015](https://www.gov.hk/en/about/abouthk/holiday/2015.htm), Börsenregel |
| HKEX | 2015-09-03 | geschlossen | offen | [Zusätzlicher amtlicher Feiertag](https://www.gov.hk/en/about/abouthk/holiday/2015.htm); [HKEX-Mitteilungsarchiv 2015](https://www.hkex.com.hk/eng/prod/dataprod/2015notices.htm) |
| HKEX | 2015-09-28 | geschlossen | offen | [Amtlicher Kalender 2015](https://www.gov.hk/en/about/abouthk/holiday/2015.htm), Börsenregel |
| HKEX | 2015-10-21 | geschlossen | offen | [Amtlicher Kalender 2015](https://www.gov.hk/en/about/abouthk/holiday/2015.htm), Börsenregel |
| HKEX | 2016-01-01 | geschlossen | offen | [HKEX-Wertpapierkalender 2016](https://www.hkex.com.hk/-/media/hkex-market/services/circulars-and-notices/participant-and-members-circulars/sehk/2015/ct03915e) |
| KRX | 2015-02-18 | geschlossen | offen | Regelableitung: Seollal-Vortag; [KASI-Jahresdaten](https://astro.kasi.re.kr/life/pageView/1), KOSPI-Regel |
| KRX | 2015-02-19 | geschlossen | offen | Regelableitung: Seollal; [KASI-Jahresdaten](https://astro.kasi.re.kr/life/pageView/1), KOSPI-Regel |
| KRX | 2015-02-20 | geschlossen | offen | Regelableitung: Seollal-Folgetag; [KASI-Jahresdaten](https://astro.kasi.re.kr/life/pageView/1), KOSPI-Regel |
| KRX | 2015-05-25 | geschlossen | offen | Regelableitung: Buddha-Geburtstag; [KASI-Mondkalenderdaten](https://astro.kasi.re.kr/life/pageView/1), KOSPI-Regel |
| KRX | 2015-08-14 | geschlossen | offen | [Finanzaufsicht: Finanzmärkte geschlossen](https://www.korea.kr/briefing/policyBriefingView.do?newsId=156069060) |
| KRX | 2015-09-28 | geschlossen | offen | Regelableitung: Chuseok-Folgetag; [KASI-Jahresdaten](https://astro.kasi.re.kr/life/pageView/1), KOSPI-Regel |
| KRX | 2015-09-29 | geschlossen | offen | [Amtlich bestimmter Ersatzfeiertag](https://www.korea.kr/briefing/policyBriefingView.do?newsId=148769079), KOSPI-Regel |
| KRX | 2016-01-01 | geschlossen | offen | [Amtlicher Kalender 2016](https://astro.kasi.re.kr/resources/file/compressed.tracemonkey-pldi-09.pdf), KOSPI-Regel |
| KRX | 2017-09-22 | offen | geschlossen | [KRX-veröffentlichte Meldung mit tatsächlichem Handelstag](https://kind.krx.co.kr/external/2017/09/27/000145/20170927000361/00650.htm) |
| KRX | 2017-12-20 | offen | geschlossen | [KRX-veröffentlichte Preisberechnung mit Handelstag](https://kind.krx.co.kr/external/2017/12/21/000062/20171221000114/10601.htm) |
| KRX | 2022-01-03 | offen | geschlossen | [KRX-veröffentlichte Preisberechnung: ausdrücklich dritter Handelstag](https://kind.krx.co.kr/external/2022/01/04/000085/20220104000228/10001.htm) |
| KRX | 2022-05-09 | offen | geschlossen | [KRX-veröffentlichte Meldung mit Handelsvolumen](https://kind.krx.co.kr/external/2022/06/16/000056/20220616000076/10002.htm) |

Die vier KRX-Nachweise offener Tage sind Primärmeldungen im offiziellen Veröffentlichungssystem, keine aus fehlenden Yahoo-Zeilen erschlossenen Feiertage.

**KRX 2026-07-17 bleibt geschlossen.** Die Wiedereinführung wurde 2026 beschlossen. Ein früher veröffentlichter Kalender ohne diesen Feiertag wäre inzwischen überholt. [Amtliche Mitteilung vom 3. Februar 2026](https://www.korea.kr/news/policyNewsView.do?newsId=148959009&pWise=sub&pWiseSub=C1)

Bei HKEX zählen halbe Sitzungen weiter als Handelstage, beispielsweise **2026-02-16, 2026-12-24 und 2026-12-31**. [HKEX-Wertpapierkalender 2026](https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2025/ce_SEHK_CT_075_2025.pdf)

NYSE-Zufallsbefunde:

Die Quelle ist ein **von der NYSE verfasstes, extern gespiegeltes Originaldokument**. Sie dokumentiert die historischen Schließungen; der Hosting-Domain kommt dabei keine Beweisfunktion zu. [NYSE Special Closings](https://www.ltadvisors.net/Info/research/closings.pdf)

| Börse | Datum | Offiziell | Python | Anlass / Quelle |
|---|---|---|---|---|
| NYSE | 1951-02-12 | geschlossen | offen | Lincoln’s Birthday; NYSE-Historie |
| NYSE | 1968-06-12 | geschlossen | offen | Mittwochsschließung während der Paperwork Crisis; NYSE-Historie |
| NYSE | 1972-11-07 | geschlossen | offen | Präsidentschaftswahl; NYSE-Historie |
| NYSE | 1972-12-28 | geschlossen | offen | Begräbnis Truman; NYSE-Historie |
| NYSE | 1973-01-25 | geschlossen | offen | Begräbnis Johnson; NYSE-Historie |
| NYSE | 1976-11-02 | geschlossen | offen | Präsidentschaftswahl; NYSE-Historie |
| NYSE | 1977-07-14 | geschlossen | offen | Stromausfall; NYSE-Historie |
| NYSE | 1980-11-04 | geschlossen | offen | Präsidentschaftswahl; NYSE-Historie |
| NYSE | 1985-09-27 | geschlossen | offen | Hurrikan Gloria; NYSE-Historie |
| NYSE | 1994-04-27 | geschlossen | offen | Begräbnis Nixon; NYSE-Historie |

Die acht Fälle ab 1971 sind bereits in [election_calendar_exceptions.json](C:/dev/SeasonalEdge/landing/data/election_calendar_exceptions.json) vorhanden. Der gemeinsame Python-Kalender übernimmt sie jedoch nicht. Deshalb darf die WAHLEN-Validierung nicht auf den jetzigen gemeinsamen Kalender übertragen werden.

**Abdeckung der geforderten jährlichen Stichproben:**

| Börse | Tatsächlich geprüfte Jahre / Beispiele | Noch fehlender Jahresbeleg |
|---|---|---|
| EURONEXT | 2018–2026: unter anderem 2018-05-01 geschlossen, 2019-12-24 offen, 2020-12-25 geschlossen, 2021-12-24 offen; Karfreitage 2022–2026 geschlossen. Keine Differenz in diesen Stichproben. | 2015–2017 |
| SIX | 2016-03-25, 2020-12-24, 2021-05-13, 2022-08-01, 2026-01-02 jeweils geschlossen und richtig. | 2015, 2017–2019, 2023–2025 |
| MILAN | 2022–2025 jeweils 15. August; 2026-12-24: geschlossen und richtig. | 2015–2021; ein gefundener Kalender 2015 war hinsichtlich seiner farblichen Tagesmarkierung nicht ausreichend auslesbar. |
| STOCKHOLM | 2026-01-05 offen, 2026-01-06 und 2026-06-19 geschlossen; richtig. | 2015–2025 |
| OSLO | 2020-12-24 sowie Gründonnerstage 2021–2026 geschlossen und richtig. | 2015–2019 |
| HKEX | Stichproben 2015–2026 anhand amtlicher beziehungsweise HKEX-Veröffentlichungen; Unterschiede oben. Beispiele ab 2017: 2017-01-02, 2018-01-01, 2019-01-01, 2020-04-30, 2021-02-12, 2022-05-09, 2023-01-02, 2024-01-01, 2025-01-01, 2026-04-07 jeweils richtig geschlossen. | Keine Lücke bei diesen Jahresstichproben; vollständige zusätzliche Prüfung historischer Wetterschließungen steht aus. |
| KRX | Amtliche Regelableitungen und Einzelfallnachweise für 2015, 2016, 2017, 2022 und 2026; Unterschiede oben. | Direkte Jahreskalenderstichproben 2018–2021 und 2023–2025; dynamischer Kalender nicht auslesbar. |

Die europäischen Stichproben beruhen auf [Euronext 2018](https://www.euronext.com/en/about/media/euronext-press-releases/euronext-announces-2018-holiday-calendar-its-cash-and), [2019](https://www.euronext.com/zh/media/2523/download), [2020](https://www.euronext.com/en/about/media/euronext-press-releases/euronext-announces-2020-holiday-calendar-its-cash-and), [2021](https://www.euronext.com/en/about/media/euronext-press-releases/euronext-announces-2021-holiday-calendar-for-its-cash-and) und den [Markttabellen 2022–2026](https://www.euronext.com/en/trading/trading-hours-holidays). SIX-Belege: [2016](https://www.six-group.com/dam/download/market-data/news/exfeed-messages/2016/exfeed-message-2016-02.pdf), [2020](https://www.six-group.com/dam/download/market-data/news/exfeed-messages/2020/exfeed-message-2020-39.pdf), [2021](https://www.six-group.com/dam/download/market-data/news/exfeed-messages/2021/exfeed-message-2021-08.pdf), [2022](https://www.six-group.com/dam/download/market-data/news/exfeed-messages/2022/exfeed-message-2022-19.pdf), [aktueller Kalender](https://www.six-group.com/en/market-data/news-tools/trading-currency-holiday-calendar.html). Stockholm: [Nasdaq-Handelskalender](https://www.nasdaq.com/is/european-market-activity/trading-hours).

Für HKEX wurden insbesondere die Wertpapierkalender [2017](https://www.hkex.com.hk/-/media/hkex-market/services/circulars-and-notices/participant-and-members-circulars/sehk/2016/ct01716e), [2019](https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2018/CT05318E.pdf), [2020](https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2019/ce_SEHK_CT_044_2019.pdf), [2021](https://www.hkex.com.hk/-/media/hkex-market/services/circulars-and-notices/participant-and-members-circulars/sehk/2020/ce_sehk_ct_038_2020.pdf), [2022](https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2021/ce_SEHK_CT_082_2021.pdf), [2023](https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2022/ce_SEHK_CT_058_2022.pdf), [2024](https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2023/ce_SEHK_CT_079_2023.pdf) und [2025](https://www.hkex.com.hk/-/media/HKEX-Market/Services/Circulars-and-Notices/Participant-and-Members-Circulars/SEHK/2024/ce_SEHK_CT_063_2024.pdf) herangezogen. Die einzelne Stichprobe 2018 stützt sich auf den [offiziell indexierten HKEX-Januarkalender](https://www.hkex.com.hk/News/HKEX-Calendar?currenttab=all-agenda&defaultDate=2018-01-15&sc_lang=en).

Für XETRA ergab sich kein zusätzlicher belegter Unterschied. Das ist keine neue Vollvalidierung.

**A2**

Ein einziges Tupel je Börse reicht nicht: Vergangenheit, geprüfte Teilintervalle und Zukunft benötigen unterschiedliche Status. Ich empfehle **Intervalle plus Standardstatus**, ergänzt um Quelle, Prüfdatum, Kalenderfassung und Geltungsgegenstand.

`belegt` bedeutet: **Die implementierte Fassung stimmt mit dem genannten Beleg überein.** Ein veröffentlichter zukünftiger Kalender ist dabei als *geplanter Kalender zum Prüfdatum* belegt, nicht als Garantie späterer tatsächlicher Sitzungen.

Konservativer Vorschlag **nach Korrektur und bestandenem Sollvergleich**:

| Kalender | Vorschlag für `belegt` | Andere Bereiche / Begründung |
|---|---|---|
| NYSE | 1971–2025 erst nach Übernahme und Abgleich der WAHLEN-Ausnahmen; veröffentlichter Plan 2026–2028 nach Sollvergleich | Vor 1971 `ungeprueft`; 2029–2035 `annahme`. Die offizielle aktuelle Veröffentlichung reicht bis 2028. |
| NASDAQ | Alias auf NYSE | Als Kalenderalias behandeln; die historische Gleichheit jedes tatsächlichen Handelsplatzes damit nicht zusätzlich behaupten. |
| XETRA | Zunächst nur unabhängig geprüfte Jahresfassungen, hier keine pauschale Erweiterung über 2026 hinaus | 2001 nicht automatisch `belegt`: Der historische Weihnachtsfall enthält bereits eine Beleglücke. Frühere beziehungsweise ungeprüfte historische Regeln und zukünftige Fortschreibungen getrennt kennzeichnen. |
| LSE | Veröffentlichten Plan 2026–2028 nach Korrektur der Ersatzregeln | 2000–2025 vorerst `annahme`, bis historische Börsenabdeckung abgeschlossen ist; belegte Einzelkorrekturen trotzdem übernehmen. Ab 2029 `annahme`. |
| TSE | 2001–2027 nach den oben genannten Korrekturen und Abgleich der Jahresveröffentlichungen | 2000 wegen der verbleibenden Scanprüfung zunächst `annahme`; vor 2000 `ungeprueft`; ab 2028 `annahme`. |
| EURONEXT | Regeln/Jahresfassungen 2018–2026 für den geprüften Marktumfang nach vollständigem Sollabgleich | 2015–2017 und frühere Historie zunächst `annahme`; spätere Jahre nur gemäß tatsächlich geprüftem veröffentlichtem Kalender. |
| SIX | Zunächst geprüfte Fassung 2026 | Historische Stichproben begründen keine lückenlose Gültigkeit 2015–2026; übrige dokumentierte Fortschreibung `annahme`. |
| MILAN | 2022–2026 nach vollständigem Abgleich der veröffentlichten Markttabellen | Frühere Jahre `annahme`, bis die jährlichen Quellen geprüft sind. |
| STOCKHOLM | Geprüfte Fassung 2026 | Historische und zukünftige Fortschreibung `annahme`. |
| OSLO | 2021–2026 nach vollständigem Abgleich der Markttabellen | Ältere Bereiche zunächst `annahme`; Einzelbeleg 2020 erweitert noch kein vollständiges Intervall. |
| HKEX | Geprüfter Plan 2026 nach Sollvergleich | 2015–2025 vorerst `annahme`, bis Feiertage **und tatsächliche Sonderschließungen** vollständig abgeglichen sind; außerhalb ergänzter Tabellen `ungeprueft`. |
| KRX | Derzeit kein vollständiges Intervall freigeben | Nach Korrektur der bekannten Fehler 2016–2026 zunächst `annahme`; außerhalb ergänzter Tabellen `ungeprueft`. |
| FOREX | Projektkonvention „Montag–Freitag, keine Feiertage“ im unterstützten Rechenbereich | Als Modellkonvention kennzeichnen; keine universelle Aussage über sämtliche FX-Handelsplätze und deren Sitzungsgrenzen. |
| CRYPTO | Projektkonvention „jeden Tag offen“ im unterstützten Rechenbereich | Ebenfalls Modellkonvention; Handelsplatzstörungen sind davon nicht erfasst. |

Die aktuelle NYSE-Veröffentlichung nennt ausdrücklich 2026–2028, nicht 2035. [NYSE Holidays & Trading Hours](https://www.nyse.com/trade/hours-calendars)

Zusätzlich muss der **Marktumfang** feststehen: `EURONEXT` bezeichnet hier den gemeinsamen Kalender der geprüften kontinentaleuropäischen Cash-Märkte. Mailand und Oslo haben eigene Regeln. Die Zuordnung spanischer `.MC`-Ticker zum gemeinsamen Kalender bleibt eine gesondert zu belegende Zuordnung. Ein belegter Kalender macht einen Ticker-Proxy nicht automatisch belegt. [Euronext-Markttabellen](https://www.euronext.com/en/trading/trading-hours-holidays)

Bekannt falsche Bereiche dürfen vor ihrer Korrektur nicht allein durch `annahme` aufgewertet werden. Insbesondere die HKEX-/KRX-Tabellen sind im aktuellen Zustand **nicht** pauschal `belegt`.

**A3**

Inventar aus Quelltextsuche, AST-Auswertung einschließlich Importaliasen und Prüfung der umgebenden Fehlerbehandlung. Zeilen beziehen sich auf den geprüften Arbeitsstand. Zusammengefasste Zeilen nennen sämtliche betreffenden Aufrufstellen.

| Datei:Zeile | Aufruf / Herkunft | Verhalten bei `ValueError` heute |
|---|---|---|
| [exchange_holidays.py:385](C:/dev/SeasonalEdge/exchange_holidays.py:385), 407 | `is_holiday(d, exchange)`; `get_holidays(exchange, …)` | Kein Catch; würde propagieren. Betrifft die Root-Kopie. |
| [exchange_holidays.py:433](C:/dev/SeasonalEdge/exchange_holidays.py:433) | `get_exchange_for_ticker(t)` im Selbsttest | Kein äußerer Catch; alter Resolver liefert üblicherweise NYSE statt Fehler. |
| [backfill_new_ticker.py:57](C:/dev/SeasonalEdge/scripts/backfill_new_ticker.py:57), 76 | Handelstagsprüfung mit aufgelöstem Tickerkalender | Äußerer Catch in `main` meldet `FATAL` und merkt Fehlschlag; **kein entsprechender Nichtnull-Exit**. |
| [backfill_tdoy.py:68](C:/dev/SeasonalEdge/scripts/backfill_tdoy.py:68), 178 | Handelstagsprüfung; Resolver für SYMBOLS oder CLI-Ticker | Kein Catch um diese Kalenderaufrufe; Abbruch mit Nichtnull-Exit. |
| [build_calendar_data.py:106](C:/dev/SeasonalEdge/scripts/build_calendar_data.py:106) | Variable `exchange` aus fester Liste NYSE/XETRA/LSE | Kein Catch; Abbruch. Eingabewerte sind gültige Literale aus der Liste. |
| [check_db_completeness.py:97](C:/dev/SeasonalEdge/scripts/check_db_completeness.py:97) | Resolver in `_is_us_listed` | Catch `Exception`; ersetzt Ergebnis durch Tickerheuristik. |
| [check_db_completeness.py:218](C:/dev/SeasonalEdge/scripts/check_db_completeness.py:218), 232 | `is_trading_day` in Hilfsfunktionen mit übergebenem Kalender | Kein lokaler Catch; Verhalten hängt vom Aufrufer ab. |
| [check_db_completeness.py:246](C:/dev/SeasonalEdge/scripts/check_db_completeness.py:246) | Resolver für `"SPY"` | Kein Catch; fester bekannter Ticker. |
| [check_db_completeness.py:449](C:/dev/SeasonalEdge/scripts/check_db_completeness.py:449) | Resolver im Ticker-Audit; nutzt auch obige Hilfsfunktionen | Catch `Exception` mit `pass`: betroffener Ticker wird aus diesen Prüfungen ausgelassen. |
| [fix_missing_days.py:46](C:/dev/SeasonalEdge/scripts/fix_missing_days.py:46), 189 | Handelstagsprüfung; Resolver für SYMBOLS/CLI | Kein Catch um Kalenderpfad; Abbruch mit Nichtnull-Exit. |
| [intraday_refresh.py:133](C:/dev/SeasonalEdge/scripts/intraday_refresh.py:133), 167 | Resolver; **Alias `_is_td`** | Innerer Catch `Exception` mit `pass`; Refresh kann ohne erfolgreich berechnete Nummerierung weiter schreiben und Erfolg zählen. |
| [nightly_refresh.py:241](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:241), 256 | Resolver und Handelstagsprüfung im Health-Check | Ticker-Catch legt Fehler in `health_errors`; Prüfung läuft weiter. Vollständigkeitsmeldung und Erfolgszählung berücksichtigen diese Fehler nicht ausreichend; Fehler erzwingt keinen Nichtnull-Exit. |
| [central_banks.py:325](C:/dev/SeasonalEdge/shared/central_banks.py:325) | Resolver für Ticker | Catch `Exception`; Rückgabe `[]`. Zuordnungsfehler erscheint als fehlende Ereignisse. |
| [daily_report.py:509](C:/dev/SeasonalEdge/shared/daily_report.py:509) | Resolver für TDOM-Pfad | Catch `Exception`; Ersatzkalender NYSE. |
| [daily_report.py:516](C:/dev/SeasonalEdge/shared/daily_report.py:516) | Handelstagsprüfung mit aufgelöstem Kalender | Catch `Exception`; Ersatz durch reine Wochentagsprüfung. |
| [daily_report.py:789](C:/dev/SeasonalEdge/shared/daily_report.py:789), 817 | Jahres-/Monatszählung mit Parameter `exchange` | `ValueError` aus dem eigentlichen Aufruf propagiert. Catch schützt lediglich den Import. |
| [daily_report.py:836](C:/dev/SeasonalEdge/shared/daily_report.py:836) | Resolver für Statuszeile | Catch `Exception`; Ersatzkalender NYSE. |
| [daily_report.py:947](C:/dev/SeasonalEdge/shared/daily_report.py:947) | `get_holidays(exch, …)` aus fester Börsentabelle | Catch `Exception`; protokolliert und lässt Börsenereignisse weg. Feste Eingabewerte sind gültig. |
| [data.py:158](C:/dev/SeasonalEdge/shared/data.py:158), 159 | Resolver und Prüfung vor Download | Catch `Exception` mit `pass`; Download wird trotzdem versucht. |
| [data.py:193](C:/dev/SeasonalEdge/shared/data.py:193) | Erneuter Resolver vor Nummerierung | Catch `Exception` mit `pass`; Nummern bleiben gegebenenfalls `None`, werden beim Upsert dann ausgelassen. |
| [exchange_holidays.py:526](C:/dev/SeasonalEdge/shared/exchange_holidays.py:526) | `is_holiday` innerhalb `is_trading_day` | Kein Catch. Der bisherige Wochenend-Ausgang liegt davor. |
| [exchange_holidays.py:590](C:/dev/SeasonalEdge/shared/exchange_holidays.py:590) | Handelstagsprüfung in `letzte_session` | Kein Catch. Zuvor werden leere Werte auf NYSE und unbekannte Sitzungszeiten auf NYSE-Zeiten ersetzt. |
| [exchange_holidays.py:631](C:/dev/SeasonalEdge/shared/exchange_holidays.py:631) | Handelstagsprüfung in `markt_offen` | Kein Catch; ebenfalls vorgeschaltete NYSE-Ersatzwerte. |
| [exchange_holidays.py:670](C:/dev/SeasonalEdge/shared/exchange_holidays.py:670) | `get_holidays` in **`get_holidays_for_ticker`** | Kein Catch, aber eigener `_TICKER_MAP`-Resolver mit NYSE-Fallback. Bleibt in K4 bislang erhalten. |
| [exchange_holidays.py:713](C:/dev/SeasonalEdge/shared/exchange_holidays.py:713) | `get_exchange_for_ticker(t)` im Selbsttest | Kein äußerer Catch; alter Resolver verschluckt Fehler seiner internen Import-/Lookup-Strecke. |
| [plain_vanilla.py:136](C:/dev/SeasonalEdge/shared/strategies/plain_vanilla.py:136) | Handelstagsprüfung mit Börse aus Auswertungskontext | Kein Catch für `ValueError`; propagiert. Kontext wird beim Verlassen zurückgesetzt. |
| [stress_score.py:229](C:/dev/SeasonalEdge/shared/stress_score.py:229) | Handelstagsprüfung mit Parameter `boerse` | Kein passender Catch; propagiert. Der äußere Pfad behandelt `LadeFehler`, nicht allgemein `ValueError`. |
| [verify_calendar_rules.py:86](C:/dev/SeasonalEdge/scripts/verify_calendar_rules.py:86), 91 | Resolver; Prüfung eines Testkalenders | Resolver außerhalb des Catch: Abbruch. Prüfaufruf innerhalb des Catch: Fehlerbefund. |
| [verify_calendar_rules.py:116](C:/dev/SeasonalEdge/scripts/verify_calendar_rules.py:116) | Resolver **und** Handelstagsprüfung im Crypto-Test | Kein Catch; Abbruch. |
| [verify_calendar_rules.py:131](C:/dev/SeasonalEdge/scripts/verify_calendar_rules.py:131), 136, 137, 138, 139 | Resolver und vier FOREX-Prüfungen | Kein Catch; Abbruch. |
| [verify_calendar_rules.py:174](C:/dev/SeasonalEdge/scripts/verify_calendar_rules.py:174) | Variable Börse aus festen Sollfällen | Kein Catch; Abbruch. |
| [verify_calendar_rules.py:338](C:/dev/SeasonalEdge/scripts/verify_calendar_rules.py:338) | Resolver im DB-Abgleich | Catch `Exception` mit `pass`: Ticker kann ungeprüft bleiben. |
| [verify_kalender_zwilling.py:127](C:/dev/SeasonalEdge/scripts/verify_kalender_zwilling.py:127), 134 | Variable Börse aus festen Vergleichsfällen | Kein Catch um Kalenderaufruf; Abbruch. |
| [verify_plain_vanilla_1a.py:95](C:/dev/SeasonalEdge/scripts/verify_plain_vanilla_1a.py:95) | Handelstagsprüfung beim Aufbau der Testdaten | In registrierten Testfällen vom Test-Catch erfasst und als fehlgeschlagene Prüfung gespeichert. |
| [verify_plain_vanilla_1b.py:80](C:/dev/SeasonalEdge/scripts/verify_plain_vanilla_1b.py:80) | Entsprechender Testdatenaufbau | Entsprechender Fehlerbefund durch Test-Catch. |

Zusätzlich geprüft:

- Reine Literal-Börsenaufrufe und die an NYSE gebundene Einargument-Funktion in `build_flows_rebalancing.py` benötigen keine neue Tickerzuordnung.
- Es wurden keine ausführbaren Imports der Root-Kopie gefunden. Ihre Entfernung ist damit vertretbar.
- `shared.market_calendar` und `shared.daily_report` importieren außerdem private Kalenderfunktionen direkt. Diese Stellen stehen außerhalb des angeforderten Namensfilters, sind aber für Kalenderfassung, Status und Wirkungsbericht relevant.

**Antworten Fokusfragen**

1. **K1–K6 tragfähig?**  
   Nach Überarbeitung ja. Es fehlen die älteren TSE-Regeln, HKEX-/KRX-Korrekturen, die NYSE-Ausnahmen, Änderungen an verschluckenden Aufrufern und die Bereinigung von `get_holidays_for_ticker`. K4 muss den tatsächlichen Listingkalender erhalten. K6 braucht getrennte Beweise für Kalenderwahrheit und Nummerierungsarithmetik.

2. **Außerhalb `belegt` rechnen?**  
   Ja, sofern der Kalenderstatus zusammen mit der verwendeten Fassung verfügbar bleibt. `annahme` muss `handelstag_nummern` nicht zum Scheitern bringen. Unbekannte Börsen und ungültige Eingaben müssen dagegen scheitern. `ungeprueft` darf nicht still als belastbare historische Nummerierung erscheinen.

3. **Unbekanntes `^XYZ`: `ValueError` oder NYSE?**  
   `ValueError` ist richtig. Das Präfix liefert keinen Handelsplatz. Einen gewollten Proxy ausdrücklich in Metadaten aufnehmen. Aufrufer müssen den Fehler anschließend als Zuordnungsfehler behandeln und dürfen ihn nicht wieder durch NYSE ersetzen.

**Befunde**

**[P1] K4 und K6 sind unvereinbar.**  
`SYMBOLS.exchange` ist ein informatives Heimatbörsenfeld. Der bestehende Resolver folgt bei ADRs ausdrücklich dem tatsächlichen US-Listing. Eine Umstellung auf das Heimatbörsenfeld ändert diese **23 bekannten Ticker**:

| Neuer Heimatbörsenkalender statt bisher NYSE | Ticker |
|---|---|
| EURONEXT | ASML, TTE, SAN, BUD, BBVA, SNY, ING |
| LSE | AZN, HSBC, SHEL, RIO, BTI, UL, BP, GSK, NGG, LYG, BCS |
| SIX | NVS, UBS |
| XETRA | LIN |
| STOCKHOLM-Proxy | NVO |
| OSLO | EQNR |

Der Widerspruch steht bereits in [symbols.py:70](C:/dev/SeasonalEdge/shared/symbols.py:70). **K4(1) muss einen ausdrücklich festgelegten Holiday-/Listingkalender liefern**, nicht unmittelbar `exchange`.

Bei blindem Wiederverwenden der bisherigen Übersetzungstabellen vor der Formaterkennung entstehen zusätzlich **17 Crypto-/FOREX-Abweichungen** über `NONE → NYSE`; die ausgeführte Variante ergab insgesamt **40 Differenzen bei 370 Tickern**. Das ist eine weitere Implementierungsfalle, keine unvermeidbare Folge jeder möglichen Neufassung von K4.

**[P1] K1 muss mehr korrigieren als Olympia und die bereits genannten LSE-Tage.**  
Der Vollvergleich findet zusätzlich die alten TSE-Regeln, 2019 und den Ausfall 2020-10-01. HKEX/KRX sind bereits innerhalb 2016–2026 fehlerhaft. Eine bloße Ergänzung der im Entwurf genannten Daten würde diese Kalender weiterhin falsch lassen.

**[P1] Die WAHLEN-Belege gelten nicht automatisch für den gemeinsamen NYSE-Kalender.**  
[nyse_holidays.py:140](C:/dev/SeasonalEdge/shared/nyse_holidays.py:140) enthält nur die jüngeren Sonderschließungen. Die acht belegten älteren Fälle sind auf einem getrennten Datenpfad. K2 darf dessen Validierung erst nach Zusammenführung beziehungsweise identischem belegtem Datenbestand verwenden.

**[P1] K3 kann heute einen grünen Lauf mit ausgelassenen Prüfungen erzeugen.**  
Besonders relevant sind Completeness-Audit, Nightly-Health-Check, Intraday-Refresh, `shared.data`, Daily-Mail und `backfill_new_ticker`. A3 zeigt die konkreten Pfade. „Alle Aufrufer liefern gültige Werte“ genügt als Anforderung nicht: **Ein unerwarteter Zuordnungsfehler muss auch nach dem Catch als Fehler erkennbar bleiben.**

**[P2] K4 beseitigt nicht alle parallelen Resolver.**  
`get_holidays_for_ticker` verwendet weiterhin `_TICKER_MAP` und NYSE-Fallback. Auch `get_holiday_calendar` braucht einen eindeutigen Weg über die neue zentrale Zuordnung. Unbenutzte Funktionen entfernen oder als dünne Delegation erhalten; keinen zweiten Regelbestand behalten.

**[P2] K2 vermischt Beleg, Fortschreibung und tatsächliche Sitzung.**  
Eine amtliche Quelle kann durch eine spätere Entscheidung überholt sein. KRX 2017-12-20 und die Wiedereinführung von 2026-07-17 zeigen, warum Veröffentlichungsstand und spätere Änderungen dazugehören. Eine einzelne Stichprobe je Jahr genügt zudem nicht, um die komplette Feiertagstabelle desselben Jahres als geprüft zu erklären.

**[P2] K5 braucht einen vollständigen Nummerierungsvertrag.**

- Vorwärtszahlen zählen alle offenen Tage vom Periodenbeginn **bis einschließlich Datum**, auch wenn der angefragte Tag geschlossen ist.
- Vor der ersten Sitzung ist die Vorwärtszahl **0**; bei geschlossenen Tagen bleiben beide Rückwärtszahlen `None`.
- Periodensummen beziehen sich auf den vollständigen Monat beziehungsweise das vollständige Jahr, unabhängig vom übergebenen Ausschnitt.
- Unsorte Eingaben, Duplikate, mehrere Jahre und Monatswechsel dürfen das Ergebnis nicht beeinflussen.
- NASDAQ vor Bildung des Cache-Schlüssels auf NYSE normalisieren; Cache-Inhalte gegen nachträgliche Mutation schützen.
- Den unterstützten Datumsbereich ausdrücklich festlegen. „Alle Jahre“ ist insbesondere bei historischen Regelgrenzen und der Endgrenze von `date` kein ausreichender Vertrag.

**[P2] K6(a) beweist Zählung, nicht Kalenderwahrheit.**  
`busday_count` mit den aus dem Produktionskalender gewonnenen Feiertagen kann dessen falsche Feiertage nicht entdecken. Es braucht zwei getrennte Referenzen:

1. Amtlich belegte Sitzungserwartungen, einschließlich **offener Gegenfälle**.
2. Unabhängige Nummerierungsarithmetik über diesen Sitzungsmengen.

Für CRYPTO gilt die Siebentagewoche; FOREX hat im Projekt fünf Tage ohne Feiertage. Historische NYSE-Regeln vor 1971 sind im aktuellen Kalender nachweislich unvollständig. Ein grüner NumPy-Vergleich 1950–2035 darf deshalb nicht als historische Kalenderbestätigung bezeichnet werden.

**[P2] K7 unterschätzt den Wirkungsbereich.**  
Neben den erwarteten vier Tickern sind **`^HSI` und `^KS11`** betroffen. Dem NYSE-Kalender sind aktuell **267 von 370 Tickern** zugeordnet; tatsächliche historische Betroffenheit hängt von deren vorhandenen Kurszeilen ab und wurde hier nicht per DB geprüft.

Ein neu geschlossener Tag senkt nachfolgende Vorwärtsnummern der jeweiligen Periode. Rückwärtsnummern können sich auch **vor** diesem Tag ändern, weil sich die Periodensumme ändert. Bei einem wieder geöffneten Tag gilt das entsprechend umgekehrt.

Ohne Neuberechnung bleiben gespeicherte `prices`-/`tdom_stats`-Zuordnungen auf der alten Fassung, während Daily-Pfade bereits neue Kalendernummern berechnen könnten. Der Bericht muss diese Mischung ausdrücklich behandeln; reine Backendänderungen haben bereits sichtbare Mail- und Datenfolgen.

**Auflagen vor dem P1a-Code**

1. **K4 neu formulieren:** Exakte bekannte Ticker erhalten einen expliziten Listing-/Holidaykalender. Alle **370 bisherigen Zuordnungen** müssen unverändert bleiben. Crypto, FOREX, Futures, Indizes und nichtkanonische Börsenbezeichnungen ausdrücklich abdecken.
2. **A1-Beleglücken schließen:** Die fehlenden Börse/Jahr-Stichproben aus der Abdeckungstabelle beschaffen und prüfen. Bis dahin keine lückenlose Validierung behaupten. Zukünftige Kalender als veröffentlichte Planung beziehungsweise Regelprojektion kennzeichnen.
3. **K1-Sollfälle vollständig aufnehmen:** Beide Änderungsrichtungen testen: fehlende Schließungen **und fälschlich geschlossene offene Tage**. Historische Regeländerungen gezielt zeitlich begrenzen.
4. **Eine Kalenderbasis herstellen:** Die belegten NYSE-Ausnahmen übernehmen; verbleibende Resolver entfernen oder zentral delegieren. Private direkte Kalenderaufrufe hinsichtlich Status und Fassung berücksichtigen.
5. **K3-Aufrufer zuerst korrigieren:** Kein NYSE-/Wochentagsersatz bei Zuordnungsfehlern. Keine ausgelassene Prüfung als Erfolg zählen. Betroffene Jobs müssen den Fehler bis zum Nichtnull-Exit beziehungsweise eindeutigen Fehlerstatus weiterreichen.
6. **K2 als Intervalle mit Herkunft spezifizieren:** Quellen, Prüfdatum, Fassung, Marktumfang und Planung/tatsächliche Sitzung festhalten. Bekannte Fehler erst nach Korrektur aufwerten.
7. **K5 präzisieren:** Inklusive Endpunkte, vollständige Periodensummen, geschlossene Tage, leere Eingabe, strikte Datumsvalidierung, Aliasnormalisierung und Rechengrenzen festlegen.
8. **K6 fachlich trennen:** Kalenderbelege unabhängig von Produktionsfunktionen; NumPy für Arithmetik. Mutation nur mit vorhandenem Anker, deterministisch über `_atomar_schreiben`; bloße Ausnahme zählt nicht als fachlich gefangene Mutation.
9. **K7 vor Integration konkretisieren:** Fassung und Folgen für gespeicherte Nummern, `tdom_stats`, Daily-Mail und weitere Kalenderverbraucher berichten. In P1a keine automatische Datenneuberechnung auslösen.

Mutationstests wurden wegen ihrer Dateischreibzugriffe hier nicht ausgeführt. Die belegten Produktionsbefunde und die unveränderte Ticker-Baseline wurden ausschließlich lesend geprüft.
