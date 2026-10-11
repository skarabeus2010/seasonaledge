# Antwort Codex — V1c-2 Entwurf v3 (2026-10-12)

Zu: [Entwurf v3](2026-10-12_kalender_v1c2_entwurf_v3.md). Erster Lauf scheiterte am Werkzeug (setup refresh), dies ist die Wiederholung.

**Urteil**

Noch **keine uneingeschränkte Freigabe als Bauvorlage**. Die R2-Befunde zur historischen Berechnung und zur AM/PM-Produktgeltung sind durch belegte Intervalle, `null` und Feldentfernung konzeptionell aufgelöst; die Ereignisexistenz bleibt unvollständig geregelt.

**Befunde**

- **P1 – Fehlender Listing-Beleg braucht einen eigenen Rückfall.** „Nicht gelistet“ und „Listung ungeprüft“ sind verschieden. Die anfängliche VX-Monatsliste beweist nicht, dass Juli 2004 später niemals gelistet wurde; diesen Negativ-Sollfall noch nicht festschreiben.
- **P1 – `OPEX_AB` bleibt offen.** Der Start von OEX/SPX 1983 beweist keinen durchgehenden Monatsanker ab einem bestimmten Monat. Ohne belegte Startgrenze ist ausdrücklich **kein Katalogereignis** zu erzeugen.
- **P2 – Abhängigkeiten müssen Unsicherheit weitergeben.** Ungeprüftes Settlement → auch davon abgeleitetes Handelsende `null`; eine belegte Vortagsregel allein macht dessen Datum nicht belegt. VIX-Optionssettlement benötigt zudem einen eigenen Gültigkeitsnachweis. [SEC, SR-CBOE-2015-050](https://www.govinfo.gov/content/pkg/FR-2015-07-27/pdf/2015-18274.pdf)

**Belegte Grenzen / nicht belegbar**

- **VX-Stand C:** heutige ODER-Feiertagsformel ab **04.09.2015** durch SR-CFE-2015-023; daraus abgeleitet erster folgender Standardkontrakt **2015-09**, Settlement **16.09.2015**. Das Filing korrigiert ausdrücklich den vorherigen Wortlaut. [CFE, S. 1–2/8](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2015/SR-CFE-2015-023.pdf)
- **VX-Handelsende ist eine separate Grenze:** SR-CFE-2014-025 verschiebt es auf den Settlementtag, während weiterhin die ältere Feiertagsformel gilt. Angekündigt ist „ab 18.11.2014“, mit operativem Datum per Circular; **erster betroffener Kontrakt in dieser Prüfung nicht belegbar**. [CFE, S. 1/5](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2014/SR-CFE-2014-025.pdf)
- **VX A→B:** erster betroffener Kontrakt und vollständiges Übergangsintervall **nicht belegbar in dieser Prüfung**; kein pauschales Fortschreiben von A oder B über die ungeklärte Grenze. [SR-CFE-2005-028](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2005/SR-CFE-2005-028.pdf)
- **Listing:** vollständige historische VX-/VIX-Monatslisten und Beginn lückenlos monatlicher Listung **nicht belegbar**. „May list … up to“ belegt eine Erlaubnis, keine tatsächliche Listung. [CFE 2014](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2014/SR-CFE-2014-025.pdf), [SEC 2015](https://www.govinfo.gov/content/pkg/FR-2015-07-27/pdf/2015-18274.pdf)
- **VIX-Optionsstart:** `2006-03`, Settlement **22.03.2006**, bleibt durch die archivierte Cboe-Startmitteilung und den OCC/OIC-Nachweis gestützt; vollständige Folgeintervalle sind damit nicht belegt. [Cboe-Mitteilung, archiviert](https://mondovisione.com/media-and-resources/news/cboe-to-begin-trading-options-on-the-cboe-volatility-index-vix-on-friday-februar-2011124/), [OCC/OIC, Fußnote 7](https://www.optionseducation.org/getmedia/75ff0baf-3943-437d-87d8-19694e19c64d/vixfuturesoptionsumassfull.pdf)
- **OPEX:** Grenztermin **01.02.2015**, daraus Standardfälle **17.01.2015 Samstag / 20.02.2015 Freitag**, bestätigt; Grandfathering bleibt auszunehmen. [SEC/OCC-Genehmigung](https://www.sec.gov/files/rules/sro/occ/2013/34-69772.pdf)
- **Historische OPEX-Regeln:** OCC bestätigt Samstag vor der Grenze und vorherigen Börsengeschäftstag für Freitagsverfälle danach; Rückgeltung der Feiertagsregel bis zum ungeklärten OPEX-Beginn **nicht belegbar**. [OCC By-Laws, Art. I und XVII](https://www.theocc.com/getContentAsset/3309eceb-56cf-48fc-b3b3-498669a24572/dfc3d011-8f63-43f6-9ed8-4b444333a1d0/occ_bylaws.pdf)

**Auflagen**

- Ungeprüfte Listung → keine behauptete Kontraktexistenz; unbekanntes `OPEX_AB` → keine OPEX-Ereignisse. Abdeckungslücken ausdrücklich ausweisen.
- Regelgrenzen je Feldgruppe unabhängig führen; `null` und Status durch sämtliche abhängigen Felder weitergeben.
- Unbelegte Grenz- und Negativfälle ersetzen durch Prüfungen auf korrekte Auslassung beziehungsweise `null`; Bestandsschutz unverändert beibehalten.
- Read-only geprüft; keine Dateien oder DB-Daten geändert. Die gescannten frühen Filings waren hier nicht zuverlässig auslesbar; ihre offenen Grenzen wurden deshalb nicht freigegeben.
