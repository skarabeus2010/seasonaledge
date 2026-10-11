# Kalender-Umstellung V1c — Entwurf: Ereigniskatalog (Vertrag B4), vor dem Code

Bauplan: docs/KALENDER_UMSTELLUNG.md (V1: „Ereigniskatalog (B4)"), Vertrag B4 in
[Matrix-Antwort](2026-10-11_kalender_p3p4_matrix_antwort1.md) Z. 123–134. V1a/V1b live (`64ab4b8`). Read-only.

<task>Ist der Entwurf tragfähig und vertragsgerecht (B4 1–10)? Welche Aufteilung, welche Fallen?</task>

## Ist-Stand (gemessen)
- `shared/exchange_holidays.py`: je Börse `_compute_<börse>_holidays(jahr) -> list[date]` (XETRA, LSE, EURONEXT, MILAN,
  TSE, SIX, STOCKHOLM, OSLO, HKEX, KRX); NYSE/NASDAQ aus `shared/holidays.get_nyse_holidays` (inkl.
  `_NYSE_SPECIAL_CLOSURES`). Ergebnis ist eine **Datumsmenge** — keine Regel-Identität, kein Bezug Ersatztag ↔
  nominaler Feiertag, keine Halbtage. `kalender_status()` je Börse/Jahr (belegt/annahme/ungeprueft/konvention).
- Wächter: `verify_kalender_sollfaelle.py` (86 wörtliche Fälle mit Quelle), `verify_handelstag_nummern.py`,
  `verify_boersenkalender_js.py` (Bundle = Python), `verify_kalender_zwilling.py`.
- Bundle `landing/js/boersenkalender.js` hat ein leeres Feld `ereignisse`. Seiten nutzen es noch nicht (V2/V3).
- OPEX/VIX rechnen heute Seiten/Python je selbst (Matrix P3f/P3c); Notenbank-/Mond-/Earnings-Termine sind
  Kalendertagsdaten (d) und NICHT Teil dieses Katalogs.

## Aufteilung
**V1c-1 Schließungsereignisse** (dieser Entwurf) · **V1c-2 US-Produkttermine** (OPEX, VIX nach Cboe, B4 8–9) ·
**V1c-3 Halbtage** (nur mit Quelle je Börse/Jahr; bis dahin keine). Begründung: V1c-1 ändert keine Schließung,
V1c-2/3 brauchen Quellenarbeit.

## V1c-1
1. **Modell** `shared/boersenereignisse.py`: `Ereignis(boerse, regel_id, ereignis_id, art, nominal, wirksam,
   name_de, name_en, quelle, kalenderversion)`; `art ∈ {feiertag, ersatztag, sonderschliessung, halbtag}`.
   - `regel_id`: stabil je Regel, z. B. `LSE.christmas`, `LSE.boxing_day`, `XETRA.karfreitag`,
     `NYSE.independence_day`; Sonderschließungen `NYSE.sonder.2025-01-09_carter`.
   - `ereignis_id = f"{boerse}:{regel_id}:{nominal.isoformat()}"` — eindeutig, unabhängig von der Listenposition.
   - **Ersatztag**: eigenes Ereignis mit `art=ersatztag`, `nominal` = Datum des nominalen Feiertags (z. B. Sa
     25.12.), `wirksam` = Ersatztermin, `regel_id` der nominalen Regel (B4.4). Fällt der nominale Feiertag auf ein
     Wochenende ohne Ersatz (XETRA), gibt es nur das `feiertag`-Ereignis mit `wirksam = nominal` am geschlossenen
     Wochentag; es zählt NICHT als Schließung „auf sonst offenem Tag".
   - `kalenderversion` = Pythonkalender-Version (Hash der Schließungsdaten wie im Bundle) + `kalender_status`.
2. **Eine Quelle:** die `_compute_*`-Funktionen werden zu Regeltabellen umgebaut, die Ereignisse liefern;
   `get_holidays` = `{e.wirksam | art ≠ halbtag, wirksam ist Mo–Fr}` daraus abgeleitet (keine zweite Liste).
3. **Bestandsschutz:** vor dem Umbau eine eingefrorene Momentaufnahme aller Schließungsmengen je Börse und Jahr
   1885–2100 (`scripts/fixtures/kalender_schliessungen_vor_v1c.json`, aus HEAD erzeugt, mit Prüfsumme). Wächter:
   nach dem Umbau identisch (jede Abweichung rot, auch eine zusätzliche Schließung); 86 Sollfälle unverändert grün.
4. **Bundle:** `ereignisse[boerse][jahr] = [[regel_id, art, nominal(MMDD|YYYYMMDD), wirksam(MMDD), name_idx]]`
   + Namenstabelle DE/EN; JS-API `SA.boersenkalender.ereignisse(boerse, jahr)` liefert dieselben Objekte;
   Zwillingsprüfung Python = JS je Börse/Jahr (Kennung, Art, Daten, Namen). Version im Bundle-Hash.
5. **Verbraucher bleiben unverändert** (Umschaltung in V3); nur der Katalog und seine Prüfungen entstehen.
6. Prüfplan C P3f (Sollfälle): NYSE-Sonderschließung 09.01.2025 (eigene Kennung, nicht MLK), LSE-Ersatztage
   (Weihnachten/Boxing Day auf Sa/So → Ersatz mit Bezug), LSE Krönung 2023 und Jubiläen (Sonderschließung bzw.
   verschobene Regel?), identisches Datum mehrerer Ereignisse (z. B. Karfreitag an mehreren Börsen; LSE 27.12. als
   Weihnachts- ODER Boxing-Ersatz), UID-Kollision ausgeschlossen (Eindeutigkeit aller `ereignis_id`).

## Fragen
1. Verschobene Regeltermine (LSE Early May 2020 → 8. Mai, Spring Bank 2002/2012/2022): `ersatztag` der
   nominalen Regel oder `sonderschliessung`? Mein Vorschlag: verschobener Regeltermin = `ersatztag` mit Bezug;
   ZUSÄTZLICHE Tage (Jubiläums-Extratag, Krönung, Royal Wedding, Staatsbegräbnis) = `sonderschliessung`.
2. Reicht „wirksam an einem Wochenende ohne Ersatz zählt nicht" für B4.4, oder soll ein solches Ereignis gar nicht
   erscheinen (der Feiertag existiert, die Börse wäre ohnehin zu)?
3. Ist die Momentaufnahme 1885–2100 als Bestandsschutz ausreichend, oder braucht es zusätzlich den Vergleich der
   Handelstagnummern (`handelstag_nummern`) über denselben Bereich?
4. Halbtage erst in V1c-3: Bis dahin trägt jede Börse `halbtage: ungeprüft` im Status — genügt das B4.2?

## Ausgabevertrag
**Urteil** · **Befunde** · **Antworten 1–4** · **Auflagen**. ≤ 35 Zeilen.
