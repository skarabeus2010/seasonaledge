# Kalender-Umstellung V1d — Entwurf v1 (Sitzungshelfer Python + JS, vor dem Code)

Plan: [P3/P4-Plan v9](2026-10-11_kalender_p3p4_plan_v9.md), Verträge B1/B2/B5 in
[Matrix-Antwort](2026-10-11_kalender_p3p4_matrix_antwort1.md). Vorgänger live: V1c-1 Ereigniskatalog, V1c-2
Produkttermine; V1c-3 Halbtage im Deploy. Read-only.

<task>Ist der Entwurf als Bauvorlage für V1d tragfähig und vertragsgerecht (B1.5–B1.6, B2.1–B2.4, B5.1–B5.8)?
Welche Funktionen fehlen, welche Fallen sehe ich nicht?</task>

## Bestand
- Python (`shared/exchange_holidays.py`): `is_trading_day`, `handelstag_nummern` (B1.1–B1.4), `kalender_status`,
  `boerse_normalisieren`, Betriebsfunktionen `letzte_session`/`markt_offen`/`pruefe_eod_fenster` (mit
  `_SCHLUSSZEIT`-Zeitzonen je Börse, `_uhr` injizierbar). **Kein** Nachfolger/Vorgänger, kein n-ter Handelstag, keine
  Sitzungsfolge, kein Zieltermin.
- JS (`SA.boersenkalender`): `istHandelstag`, `nummern`, `nterHandelstag`, `letzterHandelstag`,
  `nterHandelstagImJahr`, `naechsterHandelstag` (ab einschließlich, Fehler am Datenende) — ohne Python-Zwilling.
- Verbraucher rechnen heute mit eigenen Schleifen (`nextTradingDay` mit 10-Tage-Grenze, `current_tdom + offset`,
  Mo–Fr-Zählung) — Umstellung in V2–V5, nicht hier.

## Vorschlag: ein Modul, zwei Zwillinge, keine Verbraucheränderung
Neues `shared/sitzungen.py` (Python) und Erweiterung von `SA.boersenkalender` (JS), beide auf derselben
Offenheitsdefinition (`is_trading_day` = `istHandelstag`, Halbtage offen):
1. `sitzungen(boerse, von, bis)` → geordnete offene Sitzungen (B2.1); Fehler außerhalb des Rechenbereichs.
2. `naechste(datum, boerse, *, einschliesslich: bool)` / `vorherige(datum, boerse, *, einschliesslich: bool)` —
   **Pflichtargument**, damit „ab einschließlich" und „streng nach" nie verwechselt werden (B5.2); Suche bis zum
   Kalenderende, dann Fehler (B5.8), keine feste Tagesgrenze.
3. `verschiebe(sitzung, n, boerse)` → n-te Sitzung danach/davor (n ≠ 0); Ausgangsdatum muss offen sein, sonst
   Fehler — für Fenster/Offsets statt `tdom + offset` (B5.5).
4. `nte_im_monat(j, m, n, boerse)`, `nte_von_hinten_im_monat`, `nte_im_jahr` — Python-Zwillinge der JS-Funktionen
   (`None`/`null` wenn nicht vorhanden).
5. `heute(boerse, jetzt)` → Börsendatum zum injizierten Zeitpunkt in der Börsenzeitzone (`_SCHLUSSZEIT`-Zonen),
   CRYPTO/FOREX in UTC (B1.5) — **ohne** Standard „jetzt" in JS (Pflichtargument), Python mit `_uhr`.
6. `zieltermin(boerse, referenz, *, art)` → `{boerse, referenzzeitpunkt, datum, kalenderstatus, art}` mit
   `art ∈ {heutige_sitzung_oder_naechste, naechste_nach_heute}` (B5.1, B5.3, B5.6): ist heute offen, adressiert
   „heutige_…" heute, „naechste_nach_heute" den echten Nachfolger; ist heute geschlossen, beide den nächsten offenen
   Tag. `kalenderstatus` = `kalender_status(boerse, jahr)` des Zieldatums.
7. `sitzung_info(datum, boerse)` → `{offen, halbtag, schlusszeit, zeitzone}` (Halbtag aus V1c-3, offen).
Bewusst **nicht**: `letzte_session`/`markt_offen` ändern (Betriebskonvention Halbtag = voller Tag bleibt, P3m);
Renditeberechnung (B2.2–B2.14) — die Helfer liefern Sitzungsfolge/Nachfolger, die Renditen bauen V4.

## Wächter `verify_sitzungen.py` + Mutationstest
Handgeschriebene Sollfälle mit Quelle: NYSE 2026-07-02 → nächste 2026-07-06 (3.7. geschlossen), strikt vs.
einschließlich an offenem Tag, Jahreswechsel 2025-12-31 → 2026-01-02, XETRA 2026-12-23 → 2026-12-28 (24.–26.12.
geschlossen), TSE Golden Week, CRYPTO jeden Tag, FOREX Fr → Mo; `verschiebe` über Monats- und Jahresgrenzen;
`heute` in sechs Zonen um Mitternacht/Börsenschluss (inkl. Berlin vor/nach 00:00 für NYSE); `zieltermin`
Morning-Mail-Fälle (B5.3) an offenem und geschlossenem Tag; Kalenderende → Fehler (Python-Ausnahme, JS
`KalenderFehler`). **Python = JS** vollständig: alle Funktionen über ein festes Raster je Börse 2000–2030 (jeder
Tag × beide Richtungen × einschließlich/strikt, `verschiebe` mit n ∈ {±1, ±5, ±21, ±252}) unter zwei Zeitzonen.
Mutationen: einschließlich/strikt vertauscht, feste 10-Tage-Grenze, Halbtag als geschlossen, `heute` in UTC statt
Börsenzone, `verschiebe` zählt Kalendertage, Jahresgrenze verliert eine Sitzung.

## Fragen
1. Reicht das Funktionsset für V2–V5, oder fehlt ein Helfer (z. B. „Sitzungsfolge eines Monats mit Position")?
2. Gehört `zieltermin` mit seinen zwei Arten so in den Kern, oder ist das schon Verbraucherlogik?
3. Soll `heute` für die Börsen mit `_SCHLUSSZEIT` die Zone daraus nehmen — und für Börsen ohne Eintrag ein Fehler?

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2) · **Antworten 1–3** · **Auflagen**. ≤ 30 Zeilen.
