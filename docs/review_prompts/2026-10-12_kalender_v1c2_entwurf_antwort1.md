# Antwort Codex — V1c-2 Entwurf v1 (2026-10-12)

Zu: [Entwurf v1](2026-10-12_kalender_v1c2_entwurf.md)

**Urteil**
Der Entwurf ist noch nicht als Bauvorlage freigabefähig. Verbraucher auf V3 zu verschieben ist grundsätzlich richtig; Regelkorrekturen und vollständige Ereignisfelder gehören bereits in V1c-2.

**Befunde (P1/P2)**

- **P1 – R1 vermischt Verfall, Abrechnung und Handelsende.** Standard-SPX (AM) endet gewöhnlich am vorherigen Handelstag, SPXW (PM) am Verfallstag. „Wirksam = letzter Handelstag“ ist deshalb für den gemeinsamen Produkttyp falsch. [Cboe-SPX-Spezifikation](https://www.cboe.com/tradable-products/sp-500/spx-options/spx-specifications)
- **P1 – R3 entspricht nicht der aktuellen VIX-Regel.** Ausgangspunkt bleibt der nominale Mittwoch; Mittwoch **oder** Referenzfreitag als Feiertag führen einmal zum Geschäftstag unmittelbar vor diesem Mittwoch. Synthetisch zusätzlich geschlossener 17.04.2025: Entwurf → 17.03., Cboe-Regel → 18.03. [Cboe-VIX-Regeln](https://www.cboe.com/tradable_products/vix/faqs)
- **P1 – B4.9 fehlt im Modell.** Der freigegebene Vertrag verlangt drei getrennte Felder: Settlement, Options-Handelsende, Futures-Handelsende. Ihre Erstellung gehört in V1c-2; lediglich die Verbraucherumstellung darf auf V3 warten.
- **P1 – Startgrenzen erzeugen Scheinverfälle.** „Ab 2004-03“ würde den 17.03.2004 einschließen, obwohl VX erst am 26.03.2004 startete. Handelsstart, tatsächlich gelistete Kontraktmonate und historische Regelgültigkeit müssen getrennt belegt werden. [Cboe-Originalregel 2004](https://cdn.cboe.com/resources/regulation/rule_filings/approved/2004/SR-CFE-2004-010.pdf)
- **P2 – R4 braucht eine Sitzungsdefinition.** Am NYSE-Schließtag 09.01.2025 gab es SPX/VIX-GTH und VX-Handel samt täglicher Abrechnung. „Cboe geschlossen“ ist ohne Produkt/Sitzung falsch; die Gleichheit für 1973–2026 ist nicht nachgewiesen. [Cboe-Sonderkalender](https://cdn.cboe.com/resources/schedule_update/2025/Update-Cboe-to-Observe-National-Day-of-Mourning-on-Thursday-January-9-2025.pdf)
- **P2 – Bestandsschutz muss vollständige Rückgaben schützen.** `get_all_opex_dates()` liefert am 18.06.2026 weiterhin „Good Friday“; `populate_opex()` übernimmt das unmittelbar in `meta.note`. Die Hülle muss diesen Text bis V3 bewahren.
- **P2 – Modellvertrag vervollständigen.** `kalenderversion`, maschinenlesbarer Belegstatus/Gültigkeitsbereich und Monatskennung für OPEX/Triple fehlen beziehungsweise bleiben unklar; ein Inhaltshash ersetzt sie nicht.

**Antworten 1–3**

1. **R1 teilweise:** Die OCC bestätigt dritten Freitag/vorherigen geöffneten Börsentag sowie den Samstag vor Februar 2015, nennt aber auch spätere grandfathered-Samstagsverfälle. Das bestätigt keinen gemeinsamen letzten Handelstag. **R3 nein:** aktuelle VIX-spezifische ODER-Regel verwenden; historische Fassungen gesondert prüfen. [OCC, Art. I „Expiration Date“](https://www.theocc.com/getmedia/3309eceb-56cf-48fc-b3b3-498669a24572/occ_bylaws.pdf), [Cboe-Regelbuch](https://cdn.cboe.com/resources/regulation/rule_book/C1_Exchange_Rule_Book.pdf)
2. **Keine pauschale Gleichheit:** NYSE höchstens als ausdrücklich begrenzte Annahme für die relevante Cboe-Optionssitzung verwenden; belegte Abweichungen produktbezogen hinterlegen.
3. **Ja, zwingend:** Optionen enden am Geschäftstag vor Settlement, Futures am Settlementtag um 09:00 ET gemäß aktueller Spezifikation; vor Einführung des jeweiligen Produkts kein gültiges Handelsende ausgeben. [Cboe-VIX-Regeln](https://www.cboe.com/tradable_products/vix/faqs)

**Auflagen**

- R1 als genau benannten Terminanker definieren; AM/PM-Handelsende und historischen formalen Verfall getrennt modellieren.
- Unabhängige Sollfälle ergänzen: beide Feiertagsbedingungen gleichzeitig, zusätzliche Donnerstagsschließung, Produktstart und historische Regelwechsel; anschließend Python/JS vollständig vergleichen.
- Momentaufnahme vor Umbau über **2.592 Monate** einschließlich sämtlicher Rückgabefelder und nachgelagerter OPEX-Ausgaben einfrieren; V1c-2 darf keine Live-Metadaten ändern.
- Bestand nachgerechnet: **0 nicht offene Alt-OPEX-Termine in 2.592 Monaten**; damit ist die Datumsäquivalenz im bestehenden NYSE-Kalender bestätigt. Ausführung unter Python 3.9, da lokal 3.14 fehlt; keine Dateien oder DB-Daten geändert.
