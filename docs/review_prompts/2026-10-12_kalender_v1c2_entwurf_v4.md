# Kalender-Umstellung V1c-2 — Entwurf v4 (US-Produkttermine OPEX und VIX)

Runde 3: [Entwurf v3](2026-10-12_kalender_v1c2_entwurf_v3.md) · [Antwort](2026-10-12_kalender_v1c2_entwurf_v3_antwort.md)
(2 × P1, 1 × P2; Grenzen teilweise belegt, frühe nicht belegbar). Alles aus v3 gilt, außer den folgenden Punkten.
Read-only.

<task>Sind die Befunde aus Runde 3 aufgelöst? Ist V1c-2 als Bauvorlage freigegeben?</task>

## 1 Katalog nur im belegten Bereich (P1 OPEX_AB, P1 Listung)
Die frühen Grenzen sind nicht belegbar — also beginnt der Katalog dort, wo **Regel und Listung** belegt sind, und
weist alles davor als **Abdeckungslücke** aus (eigene Funktion `abdeckung()` + Wächterausgabe, nie still grün):
- **OPEX ab `2015-02`** (Grenztermin 01.02.2015, SEC/OCC 34-69772; danach OCC-Wortlaut: 3. Freitag, sonst
  vorangehender Geschäftstag). Listung: Standard-Monatsserien von SPX-Optionen sind seitdem in jedem Monat gelistet
  (belegen über Cboe-Historiendaten je Verfall, z. B. die monatlichen SPX-Settlement-Werte; sonst Intervall kürzen).
- **VIX ab Kontrakt `2015-09`** (ODER-Regel SR-CFE-2015-023, Settlement 16.09.2015). Listung je Kontrakt belegt durch
  die Cboe-Historiendatei des VX-Kontrakts (eine Datei je Kontraktmonat, z. B. `VX+U15`); fehlt sie, kein Ereignis.
  `handelsende_futures` = Settlementtag (SR-CFE-2014-025 gilt für alle Kontrakte ≥ 2015-09, die Grenze 18.11.2014 liegt
  davor). VIX-Optionen: Settlement = VX-Settlement desselben Kontraktmonats nach SR-CBOE-2015-050 (belegen: gilt für
  ≥ 2015-09), `handelsende_optionen` = Geschäftstag vor Settlement.
- **Zukunft** (Monate nach dem letzten belegt gelisteten Kontrakt): Ereignisse nach geltender Regel mit
  `listung = "projektion"`, Status `regel`; sie werden nie als „gelistet" ausgegeben.
- **Davor** (OPEX < 2015-02, VIX < 2015-09): **keine** Katalogereignisse. Die Hüllen `get_opex_date` usw. liefern dort
  weiter die alten Werte (Bestandsschutz, Status für Verbraucher `konvention`). Wie Seiten mit Historie vor 2015
  (/opex und /vixpiration rechnen ab 1990) damit umgehen — Konventionsdaten kennzeichnen oder weglassen — ist eine
  **Nutzerentscheidung in V3**, hier nur festgehalten.

## 2 Unsicherheit wird weitergegeben (P2)
Ist ein Feld `null`/`ungeprueft`, sind alle davon abgeleiteten Felder ebenfalls `null` mit demselben Grund
(Handelsende aus Settlement, Optionssettlement aus VX-Settlement). Ein `status` je Feldgruppe; der Wächter prüft die
Weitergabe mit einem synthetisch ungeprüften Settlement.

## 3 Sollfälle (ersetzt v3 §5)
Belegt: OPEX 2015-01 kein Katalogereignis (Lücke ausgewiesen), 2015-02 → 20.02.2015, 2025-04 → 17.04., 2026-06 →
18.06., 2026-03 → 20.03.; VIX 2015-08 kein Ereignis, 2015-09 → 16.09.2015 (Handelsende Futures 16.09., Optionen
15.09.), 2025-03 → 18.03.2025, 2024-06 → 18.06.2024, 2026-04 → 15.04.2026; Zukunftsmonat → `projektion`.
Synthetisch: Donnerstag zusätzlich geschlossen (OPEX → Mittwoch), Mittwoch und Freitag Feiertag (VIX einmal vor
dem Mittwoch), Codex-Fall 17.04.2025 → 18.03.2025, ungeprüftes Settlement → abhängige Felder `null`.
Keine Negativfälle vor den belegten Grenzen (nur „korrekt ausgelassen + Lücke gemeldet").
Bestandsschutz (2 592 Monate, alle Rückgabefelder, `populate_opex`) unverändert; Python = JS Objektgleichheit.

## 4 Listungsnachweis als Daten
`shared/produkttermine_listung.py`: belegte Kontraktmonate je Produkt (aus den Cboe-Historiendateien einmalig
erhoben, mit Quelle und Abrufdatum), Pflege halbjährlich; ein Monat ohne Eintrag zwischen Beginn und letztem
Eintrag ist eine gemeldete Lücke, keine stille Auslassung.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 20 Zeilen.
