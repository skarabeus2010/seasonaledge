# Antwort Codex — V1c-2 Entwurf v4 (2026-10-12)

Zu: [Entwurf v4](2026-10-12_kalender_v1c2_entwurf_v4.md)

**Urteil**

Noch **keine uneingeschränkte Freigabe als Bauvorlage**. Frühhistorien-Lücken und Unsicherheitsweitergabe sind konzeptionell aufgelöst; zwei Vertragslücken bleiben.

**Befunde**

- **Bestätigt:** OPEX-Grenze 01.02.2015 und vorheriger Börsengeschäftstag bei Freitagsfeiertag; Grandfathering bleibt ausdrücklich ausgenommen. [SEC/OCC](https://www.sec.gov/files/rules/sro/occ/2013/34-69772.pdf), [OCC, Art. I](https://www.theocc.com/getContentAsset/3309eceb-56cf-48fc-b3b3-498669a24572/dfc3d011-8f63-43f6-9ed8-4b444333a1d0/occ_bylaws.pdf)
- **Bestätigt:** VX-ODER-Regel ab 04.09.2015; dasselbe Filing bestätigt unmittelbar das Handelsende am Settlementtag. Die offene operative Grenze von 2014 ist für diesen Katalogbereich entbehrlich. [CFE-2015-023, S. 1/6/8](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2015/SR-CFE-2015-023.pdf)
- **P1 – Optionslistung:** §1 belegt Kontraktmonate durch VX-Dateien; diese belegen Futures. §4 „je Produkt“ legt den Rückfall bei **VX belegt, VIX-Optionen ungeprüft** nicht fest. Die SEC-Regel belegt Berechnung und Listungserlaubnis, keine vollständige tatsächliche Optionslistung. [Cboe-Futuresarchiv](https://www.cboe.com/markets/us/futures/market-statistics/historical-data/futures/), [SEC, SR-CBOE-2015-050](https://www.govinfo.gov/content/pkg/FR-2015-07-27/pdf/2015-18274.pdf)
- **P2 – Projektionsgrenze:** „Nach dem letzten belegten Kontrakt“ bedeutet bei veraltetem Datenstand auch bereits vergangene Monate. Diese würden als Projektionen statt Abdeckungslücken erscheinen.
- **Codeabgleich:** Die echten JS-Funktionen liefern die vier VIX-Solltermine und bei gleichzeitig geschlossenem Mittwoch/Freitag genau eine Rückverlegung. Die additive Python-Kopie in `verify_calendar_rules.py:215` muss wie geplant ersetzt werden.

**Auflagen**

- Listung und Abdeckung für SPX-Standardserien, VX und VIX-Optionen getrennt führen; bei ungeprüfter Optionslistung Optionsfelder `null` samt Grund, belegte Futuresfelder erhalten.
- Projektionen nur für tatsächlich zukünftige, unbelegt gelistete Monate; historischen Nachlauf ohne Beleg als Lücke melden. Prüfdatum und Datenstand ausdrücklich festlegen.
- Wächterfälle ergänzen: unterschiedliche VX-/Optionslistung sowie veraltetes Listungsende mit historischen Folgemonaten; Monatsbelege vor Code-Abnahme vollständig erheben oder Abdeckung verkürzen.
- Read-only geprüft; keine Dateien oder DB-Daten geändert.
