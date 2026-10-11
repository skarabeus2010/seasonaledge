# Kalender-Umstellung V1c-2 — Entwurf v2 (US-Produkttermine OPEX und VIX)

Runde 1: [Entwurf v1](2026-10-12_kalender_v1c2_entwurf.md) · [Antwort](2026-10-12_kalender_v1c2_entwurf_antwort1.md)
(4 × P1, 3 × P2). Alles aus v1 gilt, außer den folgenden Punkten. Read-only.

<task>Sind die Befunde aus Runde 1 aufgelöst? Ist V1c-2 als Bauvorlage freigegeben? Bitte die mit „(belegen)"
markierten Konstanten gegen Primärquellen bestätigen oder korrigieren.</task>

## 1 Terminanker und Felder (P1 R1 + P1 B4.9)
Je Monatsverfall ein Ereignis mit **getrennten Feldern**, keine gemeinsame „wirksam"-Deutung:
- `regeltermin` = 3. Freitag (Kalender).
- `verfallstermin` = OCC-„Expiration Date"-Anker für Serien mit Freitagsverfall: `regeltermin`, ist er kein
  Geschäftstag der Optionsbörse (Regelsitzung, §3), der **vorangehende** Geschäftstag (rekursiv). Das ist der Tag,
  den alle bisherigen Verbraucher als „OPEX" meinen.
- `formaler_verfall` = vor dem Stichtag (belegen: erster Freitagsverfall Standardserien **2015-02-20**) der Samstag
  nach `regeltermin`, danach = `verfallstermin`. Grandfathered-Samstagsserien nach 2015 werden **nicht** modelliert;
  Status des Feldes dafür `annahme`.
- `handelsende_pm` = `verfallstermin` (PM-abgerechnete Serien, z. B. SPXW, Aktienoptionen);
  `handelsende_am` = Geschäftstag vor `verfallstermin` (AM-abgerechnete Standard-Indexserien, z. B. SPX).
- `ersatzgrund ∈ {keiner, feiertag}` (verfallstermin ≠ regeltermin), `triple_witching` (Monat 3/6/9/12) als Feld,
  `verfallsmonat` = `YYYY-MM` des Regeltermins; Kennung `US_OPT:opex.monat:<verfallsmonat>`.

Je VIX-Kontraktmonat ein Ereignis:
- `nominal` = 3. Freitag des **Folgemonats** − 30 Kalendertage (ein Mittwoch); `referenzfreitag` = jener Freitag.
- `settlement` (Final Settlement Date) = `nominal`; ist **`nominal` ODER `referenzfreitag`** kein Geschäftstag:
  **einmal** der Geschäftstag unmittelbar vor `nominal` (rekursiv nur, falls auch dieser geschlossen ist).
  (Codex-Gegenbeispiel aus R1: zusätzlich geschlossener 17.04.2025 → 18.03.2025.)
- `handelsende_optionen` = Geschäftstag vor `settlement` (ab Optionsstart, sonst `null`);
  `handelsende_futures` = `settlement` (aktuelle Spezifikation: Ende am Abrechnungsmorgen). Historische Fassungen der
  Futures-Regel (belegen: galt anfangs der Vortag?) → je Zeitraum eigener Regelstand mit Quelle; bis belegt
  `ungeprueft`.
- `kontraktmonat` = `YYYY-MM` des Monats **vor** dem Referenzmonat (Cboe-Benennung). Kennung
  `US_VIX:vix.settlement:<kontraktmonat>`. Kein Triple-Kennzeichen.

## 2 Startgrenzen (P1)
Ereignisse nur für **tatsächlich gelistete** Kontraktmonate, je Produkt eine belegte Konstante:
`OPEX_AB` (belegen: erster Monatsverfall gelisteter Cboe-Aktienoptionen nach Handelsstart 26.04.1973),
`VX_ERSTER_KONTRAKT` (belegen: Handelsstart 26.03.2004 — erster gelisteter Kontraktmonat und dessen Settlement),
`VIX_OPT_ERSTER_KONTRAKT` (belegen: Handelsstart 24.02.2006). Davor **keine** Ereignisse. Die Regelgültigkeit
(welche Fassung von R3 galt wann) ist ein eigenes Feld `regelstand` mit Quelle, getrennt vom Handelsstart.

## 3 Sitzungsdefinition (P2 R4)
„Geschäftstag" heißt hier: **Regelsitzung (RTH) der Cboe-Optionsbörse**. Annahme: = NYSE-Handelstag aus dem
V1c-1-Katalog, Status `annahme` je Jahr, außer wo belegt. Sollfall 2025-01-09: NYSE geschlossen, Cboe RTH für
SPX/VIX-Optionen geschlossen, GTH und VX-Futures offen → für unsere Felder (RTH-Geschäftstag) geschlossen; die
Futures-Sitzung ist für keinen Termin hier maßgeblich (Settlement fällt nie darauf). Abweichungen werden als Tabelle
`CBOE_RTH_ABWEICHUNG` mit Quelle gepflegt (heute leer).

## 4 Bestandsschutz (P2)
- Momentaufnahme **vor** dem Umbau über alle 2 592 Monate 1885–2100: **sämtliche Rückgabefelder** von
  `get_opex_date`/`get_all_opex_dates` (inkl. `holiday_note` „⚠️ Verschoben (Good Friday)"), die Zeilen von
  `market_calendar.populate_opex` und der OPEX-Teil von `build_calendar_data`/`build_flows_rebalancing`.
- Die Python-Hüllen liefern bis V3 **wörtlich** die alten Felder (auch den falschen Text) — V1c-2 ändert keine
  Live-Metadaten. Hinweis Codex R1: 0 nicht offene Alt-OPEX-Termine in 2 592 Monaten → Datumsgleichheit belegt.
- Der Katalog selbst gilt **auch vor `OPEX_AB`** nicht; die Hülle rechnet dort wie bisher (Bestandsschutz), der
  Katalog liefert keine Ereignisse.

## 5 Modellvertrag (P2)
Jedes Ereignis trägt `kalenderversion` (des V1c-1-Katalogs, von dem die Geschäftstage stammen), `regelstand`,
`status` (`belegt`/`annahme`/`ungeprueft` je Feldgruppe), `quelle`. `produktversion` = Hash über die Inhalte ohne
Versionsfelder. Bundle: `SA.boersenkalender.produkttermine(von, bis, art)` mit denselben Objekten.

## 6 Sollfälle (unabhängig, mit Quelle) und Prüfung
- OPEX: 2025-04 → verfallstermin 17.04., handelsende_am 16.04.; 2026-06 → 18.06.; 2026-03 → 20.03.;
  2015-01 formaler_verfall Sa 17.01.; 2015-02 formaler_verfall = 20.02.
- **Synthetisch** (eingeschleuster Kalender, Funktionen nehmen ein optionales `offen(datum)`): zusätzliche
  Donnerstagsschließung bei Freitagsfeiertag → Mittwoch (rekursiv); VIX mit Mittwoch- UND Freitagsfeiertag →
  einmal vor dem Mittwoch; Codex-Fall 17.04.2025 geschlossen → 18.03.2025.
- VIX real: Kontrakt 2025-03 → 2025-03-18; 2024-06 (Juneteenth-Mittwoch 19.06.) → 18.06.; 2026-04 (Referenz
  15.05.2026) → 2026-04-15 Normalfall; erster VX-Kontrakt und erster Optionskontrakt.
- Python = JS vollständige Objektgleichheit über alle Ereignisse, zwei Zeitzonen; Mutationstest isoliert;
  `verify_calendar_rules` Regel 8 prüft den Katalog.

## Ausgabevertrag
**Urteil** · **Befunde** · **belegte/korrigierte Konstanten** · **Auflagen**. ≤ 30 Zeilen.
