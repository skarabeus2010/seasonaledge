# Kalender-Umstellung V1c-2 — Entwurf v1 (US-Produkttermine OPEX und VIX, vor dem Code)

Vorgänger: V1c-1 Ereigniskatalog freigegeben und deployt (`shared/boersenereignisse.py`,
[Code-Freigabe](2026-10-12_kalender_v1c_code_r2_antwort.md)); Matrix B4 8–9 aus
[Entwurf v2 §5](2026-10-11_kalender_v1c_entwurf_v2.md). Read-only.

<task>Ist dieser Entwurf als Bauvorlage für V1c-2 tragfähig? Prüfe insbesondere die Regeltexte gegen die
Primärquellen (Cboe/OCC), die Zuordnung der Befunde zu Phasen und den Bestandsschutz.</task>

## Bestand (Inventur 2026-10-12, Datei:Zeile)
- **Python OPEX:** `shared/nyse_holidays.py:164 get_opex_date` (3. Freitag; NYSE-Feiertag → **genau 1 Kalendertag**
  zurück), `:187 get_all_opex_dates` (Triple {3,6,9,12}, `holiday_note` fest „Good Friday"). Verbraucher:
  `market_calendar.populate_opex` → DB `market_events` (Nightly cur..cur+2), `build_calendar_data.py` → JSON/ICS,
  `build_flows_rebalancing.py`, Daily/Weekly-Mail (lesen `market_events`).
- **Python ohne Feiertag:** `daily_report.py:1101 _third_friday` (OPEX-Woche, „Bis Fr 19.06." am 2026-06-18-Monat);
  `black_scholes.py:589 ist_monatsverfall` + Kopie `backfill_skew_massive.py:212` (`weekday()==4 and 15<=day<=21`) —
  ein auf Donnerstag verlegter Monatsverfall gilt nicht als Monatsverfall.
- **Python VIX:** im Betrieb **keine** Rechnung; nur `verify_calendar_rules.py:215 vix_settlement` (Mi-Feiertag und
  Fr-Feiertag verschieben **additiv**), und Regel 8 prüft diese eigene Kopie, nicht den Seitencode.
- **JS:** `opex.html:425/443` + Kopie `vixpiration.html:392…` (OPEX: vorheriger NYSE-Handelstag, rekursiv; VIX:
  Kalender-3.-Freitag des Referenzmonats − 30 Tage, Fr ODER Mi Feiertag → einmal vorheriger Handelstag),
  `dashboard.html:1232 _adjOpex`, `backtest-engine.html:586 makeOpexEvents` (**ohne** Feiertag, Einrasten
  **vorwärts** → Karfreitag 2025 ergibt Mo 21.04. statt Do 17.04.).
- Weitere Befunde: VIX-Ereignisse tragen den Referenzmonat statt des Kontraktmonats und das Triple-Kennzeichen;
  „(Mi)"/„(Di)" fest beschriftet; VIX-Termine ab 1990 (Futures erst 2004); „heute" per `toISOString` (UTC);
  `market_events` löscht nie (eine verschobene Zeile bliebe doppelt).

## Regeln (Vorschlag — bitte gegen Quellen prüfen)
**R1 Monatsverfall US-Aktien-/Indexoptionen (Standard, AM/PM nicht unterschieden):** Regeltermin = 3. Freitag des
Monats. Ist er an der Börse kein Handelstag, gilt der **vorangehende Handelstag** (rekursiv). Wirksam = letzter
Handelstag des Verfalls. Vor 2015-02 lag das formale Verfallsdatum auf dem Samstag danach; maßgeblich für uns ist
der letzte Handelstag → Regel bleibt gleich, Quelle nennt den Wechsel. Gültig ab Cboe-Start 1973-04 (davor
`ungeprueft`, Termine werden trotzdem gerechnet — Bestandsschutz).
**R2 Triple Witching:** Monate 3/6/9/12 von R1, eigene Kennung, nicht für VIX.
**R3 VIX-Endabrechnung (Futures + Optionen):** Mittwoch 30 Kalendertage vor dem 3. Freitag des **Folgemonats** des
Kontraktmonats. Ist dieser Freitag ein Cboe-Feiertag: 30 Tage vor dem Handelstag unmittelbar vor diesem Freitag.
Ist der so bestimmte Tag kein Handelstag: der vorangehende Handelstag. Kontraktmonat = Monat **vor** dem
Referenzmonat (Cboe-Benennung). Gültig ab 2004-03 (Futures; Optionen 2006-02), davor keine Ereignisse.
**R4 Börsenkalender:** Cboe-Feiertage = NYSE-Schließungen aus dem V1c-1-Katalog (inkl. Sonderschließungen) —
als `annahme` ausgewiesen, Abweichungen (z. B. Cboe offen bei NYSE-Sonderschließung) als Sollfälle mit Quelle.

## Modell
Neues Modul `shared/produkttermine.py` (nutzt `boersenereignisse.schliessungen`/`is_trading_day`), Ereignis wie
V1c-1 mit `art ∈ {opex, triple_witching, vix_settlement}`, `nominal` (3. Freitag bzw. rechnerischer Mittwoch),
`wirksam`, `ersatzgrund ∈ {keiner, feiertag}`, `kontraktmonat` (VIX), `quelle`; Kennung
`<B>:<regel_id>:<kontraktmonat YYYY-MM>`. Eine Versionsangabe `produktversion` (Hash über Inhalte) + Bundle-Teil in
`boersenkalender.js` (`SA.boersenkalender.produkttermine(j, art)`).

## Bestandsschutz und Umstellung
- `get_opex_date`/`get_all_opex_dates` werden Hüllen über R1/R2; eingefrorene Momentaufnahme **vor** dem Umbau
  (alle Monate 1885–2100) → 0 Abweichungen verlangt (heute fällt kein NYSE-Feiertag auf Do 14.–20., die Regel
  „1 Kalendertag" und „vorangehender Handelstag" geben dieselben Daten — der Wächter beweist das).
  `holiday_note` nennt künftig den echten Grund (Datenänderung in `meta.note` → **V3**, nicht hier).
- **V1c-2 baut nur Katalog + Bundle + Wächter.** Alle Verbraucher (Seiten J1–J7, Daily-Woche, `ist_monatsverfall`,
  VIX-Monatsbeschriftung, `market_events`-Altzeilen) stellen in **V3** um; jeder Befund oben ist dort als Posten
  mit Sollfall eingetragen.
- Wächter `verify_produkttermine.py`: Momentaufnahme, Sollfälle mit Quelle (OPEX 2025-04 → 17.04., 2026-06 → 18.06.,
  2026-03 → 20.03.; VIX: Kontrakt 2025-03 → 2025-03-18 (Karfreitag-Referenz), 2024-06 Juneteenth-Mittwoch
  2024-06-19 → 2024-06-18, Kontrakt 2026-05 → 2026-05-19, ein Normalmonat, erster VIX-Kontrakt 2004),
  Python = JS Objektgleichheit, Mutationstest. `verify_calendar_rules` Regel 8 prüft künftig den Katalog statt seiner
  Kopie.

## Fragen
1. Stimmen R1/R3 wörtlich mit den Cboe-Spezifikationen (VIX Futures Contract Specs, Cboe Rule zu Expiration Date)?
   Insbesondere R3 bei Freitag-Feiertag und bei Mittwoch-Feiertag.
2. Ist „Cboe-Feiertag = NYSE-Schließung" für 1973–2026 haltbar, oder kennt ihr Abweichungen?
3. Gehört der letzte Handelstag (VIX-Futures enden am Abrechnungsmorgen, Optionen am Vortag) als eigenes Feld hinein?

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2) · **Antworten 1–3** · **Auflagen**. ≤ 30 Zeilen.
