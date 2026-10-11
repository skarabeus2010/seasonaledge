# Kalender-Umstellung V1c-2 — Entwurf v3 (US-Produkttermine OPEX und VIX)

Runde 2: [Entwurf v2](2026-10-12_kalender_v1c2_entwurf_v2.md) · [Antwort](2026-10-12_kalender_v1c2_entwurf_v2_antwort.md)
(2 × P1, 1 × P2; Konstanten teilweise belegt). Alles aus v2 gilt, außer den folgenden Punkten. Read-only.

<task>Sind die Befunde aus Runde 2 aufgelöst? Ist V1c-2 als Bauvorlage freigegeben? Die mit „(belegen)"
markierten Grenzen bitte bestätigen oder korrigieren — oder sagen, dass sie nicht belegbar sind; dann gilt die
jeweils beschriebene `null`-Regel.</task>

## 1 Grundsatz: Regelstände mit belegten Intervallen, sonst `null`
Jede Feldgruppe (OPEX-Verfall, VX-Settlement, VX-Handelsende, VIX-Optionen-Handelsende) hat eine Tabelle
`REGELSTAENDE[(gruppe)] = [(ab_kontrakt, bis_kontrakt, regel, quelle)]`. Ein Feld wird **nur** gefüllt, wenn der
Kontraktmonat in einem belegten Intervall liegt; sonst `null` mit `status = "ungeprueft"` und Grund. Ein bereits
widerlegter Wert wird nie ausgegeben. Die Feiertags-Teilregel einer historischen Fassung, deren Wortlaut zur
Feiertagsbehandlung nicht vorliegt, gilt als eigener Regelstand — ohne Beleg `null`, nicht „aktuelle Regel".

## 2 VIX-Futures (P1 historisches Settlement, P2 Handelsende)
- **Stand A** (SR-CFE-2004-010): Settlement = Mittwoch unmittelbar vor dem 3. Freitag **des Kontraktmonats**
  (Juni 2004 → 16.06.); Handelsende = Geschäftstag vor Settlement. Intervall: `2004-05` bis zum letzten Kontrakt
  vor Stand B (belegen, aus SR-CFE-2005-028: erster Kontrakt nach neuer Regel).
- **Stand B** (SR-CFE-2005-028 ff.): Settlement = Referenzfreitag (3. Freitag des Folgemonats) − 30 Tage;
  Feiertagsregel nach Wortlaut dieser Fassung (belegen; sonst `null` bei Feiertagsberührung, Normalfall gefüllt).
  Handelsende = Geschäftstag vor Settlement bis zum Wechsel auf „Ende am Abrechnungsmorgen" (belegen: erster
  Kontrakt mit Handelsende am Settlementtag).
- **Stand C** (aktuelles Regelbuch, S. 170): ODER-Regel aus v2 §1; Handelsende Futures = Settlementtag.
  Intervall ab belegter Einführung der ODER-Fassung bis heute (belegen); dazwischen gilt Stand B.
- Gelistete Kontraktmonate: anfangs nicht jeder Monat (2004: Mai/Juni/August/November) → **Liste der gelisteten
  Monate je Zeitraum** (belegen: ab wann monatlich); nicht gelistete Monate erzeugen kein Ereignis.

## 3 VIX-Optionen
Erster Kontrakt `2006-03` (Settlement 22.03.2006, Handelsende 21.03.); Settlement = VX-Settlement desselben
Kontraktmonats (gleiche Abrechnung), Handelsende = Geschäftstag vor Settlement. Gelistete Monate anfangs
März/April/Mai → wie oben je Zeitraum (belegen: ab wann monatlich).

## 4 OPEX (P1 Startkonstante, P2 AM/PM)
- **AM/PM-Handelsende entfällt** aus V1c-2 (war meine Ergänzung, nicht Vertrag B4): kein Feld, also keine
  unbegrenzte Produktgeltung. Bleiben: `regeltermin`, `verfallstermin`, `formaler_verfall`, `triple_witching`,
  `verfallsmonat`.
- **Begriff:** „Standard-Monatsverfall US-Aktien- und Indexoptionen" als Kalenderanker, nicht ein bestimmtes
  gelistetes Produkt. Ereignisse erst ab dem Monat, von dem an **jeder** Kalendermonat einen Standardverfall hatte
  (belegen: frühester belegbarer Zeitpunkt, Kandidat OEX/SPX-Monatsserien 1983); davor keine Ereignisse. Die
  1973er Quartalszyklen (erster Verfall Juli 1973) liegen davor und werden nicht nachgebildet.
- `formaler_verfall`: Samstag nach dem 3. Freitag bis vor dem Grenztermin 2015-02-01 (Codex R2 belegt), danach =
  `verfallstermin`; erster Freitagsstandard 2015-02-20. Wortlaut der Samstagsregel für die Zeit ab OPEX-Beginn
  (belegen); grandfathered Serien nicht modelliert (Status `annahme`).
- `verfallstermin` nach OCC (vorangehender Geschäftstag bei Feiertag) — gilt dieser Wortlaut ab OPEX-Beginn
  (belegen)? Sonst Intervallgrenze und davor `null`.

## 5 Sollfälle (ergänzt)
Juni 2004 → 16.06. (Stand A); erster Kontrakt Stand B; erster Kontrakt Stand C; 2004 nicht gelisteter Monat
(Juli 2004) → kein Ereignis; Handelsende-Wechsel; erster VIX-Optionskontrakt; OPEX-Beginn und Monat davor (kein
Ereignis); 2015-01/2015-02 formaler Verfall. Bestandsschutz unverändert (Hüllen geben die alten Werte auch vor
OPEX-Beginn zurück).

## Ausgabevertrag
**Urteil** · **Befunde** · **belegte Grenzen** (je mit Quelle) bzw. „nicht belegbar" · **Auflagen**. ≤ 30 Zeilen.
