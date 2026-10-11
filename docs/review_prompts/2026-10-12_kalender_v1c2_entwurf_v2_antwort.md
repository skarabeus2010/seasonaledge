# Antwort Codex — V1c-2 Entwurf v2 (2026-10-12)

Zu: [Entwurf v2](2026-10-12_kalender_v1c2_entwurf_v2.md)

**Urteil**
Noch **keine Freigabe als Bauvorlage**. Die aktuelle ODER-Regel, getrennte Terminfelder und Bestandsschutz lösen die entsprechenden R1-Befunde auf; historische Regeln und Startgrenzen bleiben unvollständig.

**Befunde**

- **P1 – Historisches VX-Settlement fehlt weiterhin.** 2004 galt „Mittwoch vor dem dritten Freitag des Kontraktmonats“, nicht durchgehend „Referenzfreitag − 30 Tage“. Beispiel Juni 2004: alte Regel **16.06.**, Entwurf **21.06.** Die Änderung ist in SR-CFE-2005-028 dokumentiert; ihre operative Gültigkeitsgrenze muss feststehen. [Originalregel 2004](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2004/SR-CFE-2004-010.pdf), [Änderung 2005](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2005/SR-CFE-2005-028.pdf)
- **P1 – `OPEX_AB` allein beweist keine monatliche Drittfreitag-Historie.** Eine zeitgenössische SEC-Originalrede nennt zunächst vier Verfallsmonate Januar/April/Juli/Oktober und den ersten Verfall Ende Juli 1973. Damit ist „jeder Monat ab einer Startkonstante“ als tatsächlich gelisteter Verfall nicht belegt; auch die damalige Tagesregel braucht einen eigenen Nachweis. [SEC-Originalrede, S. 6/9](https://www.sechistorical.org/collection/papers/1970/1973_1114_SommerOptions.pdf)
- **P2 – Historische Handelsenden benötigen konkrete Gültigkeitsbereiche.** VX endete ursprünglich am Geschäftstag **vor** Settlement um 15:15 CT. `ungeprueft` darf keinen bereits widerlegten Settlementtag als historischen Wert legitimieren. Auch OPEX-AM/PM-Felder brauchen eine ausdrücklich begrenzte Produktgeltung. [VX-Originalregel](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2004/SR-CFE-2004-010.pdf)
- **Bestandsschutz bestätigt:** Python 3.14 direkt ausgeführt: **0 geschlossene Termine in 2.592 Alt-OPEX-Monaten**; Juni 2026 liefert weiterhin den geschützten „Good Friday“-Text. Die echte JS-Funktion bestätigt alle drei aktuellen VIX-Sollfälle sowie beide synthetischen Fälle.

**Belegte/korrigierte Konstanten**

- **Freitagsumstellung:** rechtlicher Grenztermin **2015-02-01**; daraus folgt **2015-02-20** als erster Standard-Monatsfreitag für nicht grandfathered Serien. Kein universeller erster Freitagsverfall sämtlicher Optionen. [SEC/OCC-Genehmigung, S. 2–3](https://www.sec.gov/files/rules/sro/occ/2013/34-69772.pdf)
- **`OPEX_AB`:** erster historischer Verfallsmonat **1973-07**, Ende Juli; exakten Termin und Beginn der Drittfreitag-Regel noch nicht freigeben. [SEC-Originalrede](https://www.sechistorical.org/collection/papers/1970/1973_1114_SommerOptions.pdf)
- **`VX_ERSTER_KONTRAKT = 2004-05`**, Settlement **2004-05-19**, ursprüngliches Handelsende **2004-05-18**. Start 26.03.2004; anfänglich Mai/Juni/August/November. [Cboe-Startmitteilung, archiviert](https://mondovisione.com/news/cboe-futures-exchange-cfe-to-open-for-trading-vix-futures-to-debut-2011124/), [Originalregel](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2004/SR-CFE-2004-010.pdf)
- **`VIX_OPT_ERSTER_KONTRAKT = 2006-03`**; Settlement nach der 30-Tage-Regel **2006-03-22**, Handelsende **21.03.** Start 24.02.2006; anfänglich März/April/Mai. [Cboe-Startmitteilung, archiviert](https://mondovisione.com/media-and-resources/news/cboe-to-begin-trading-options-on-the-cboe-volatility-index-vix-on-friday-februar-2011124/)
- **Aktuelle VIX-ODER-Regel bestätigt**, ausdrücklich VIX-spezifisch; RTH-Schließung am **09.01.2025** ebenfalls bestätigt. [Cboe-Regelbuch, S. 170](https://cdn.cboe.com/resources/regulation/rule_book/C1_Exchange_Rule_Book.pdf), [Sonderkalender](https://cdn.cboe.com/resources/schedule_update/2025/Update-Cboe-to-Observe-National-Day-of-Mourning-on-Thursday-January-9-2025.pdf)

**Auflagen**

- Historische Settlement-, Handelsende- und OPEX-Regeln mit belegten Gültigkeitsintervallen ergänzen; unbelegte Felder klar begrenzen oder `null` liefern.
- Historische Listing-Zyklen nachweisen; eine Startkonstante darf keine nicht gelisteten Monatsverfälle erzeugen.
- Unabhängige Sollfälle für Juni 2004, Regelwechsel, erste Kontrakte und fehlende historische Verfallsmonate ergänzen; vollständigen Bestandsschutz beibehalten.
- Read-only geprüft; keine Dateien oder DB-Daten geändert. Mutationstests und Implementierungsabnahme bleiben dem Code-Review vorbehalten.
