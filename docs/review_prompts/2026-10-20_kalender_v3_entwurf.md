# Entwurf: Kalender-Umstellung V3 — Ereignisse

Dieser Entwurf geht **vor** der ersten Codezeile zur Prüfung. In V1a–V2 hat sich das
jedes Mal bezahlt: der Entwurf brauchte zwischen 2 und 6 Runden, und mehrfach war eine
meiner Annahmen falsch, die sonst in den Produktivcode gewandert wäre.

Gegenstand sind die **25 Stellen**, die das Inventar
`scripts/fixtures/kalender_v2_inventar.json` für V3 markiert. Sie sind nicht gleichartig
und zerfallen in zwei Pakete.

---

## 0. Was heute dort steht (nachgelesen, nicht erinnert)

**Paket A — OPEX/VIX wird in JS nachgerechnet, fest auf NYSE (12 Stellen).**

| Datei | Stellen | was dort steht |
|---|---|---|
| `landing/pages/opex.html` | 14–17 | dritter Freitag, dann `SA.holidays.isTradingDay(..., 'NYSE')` rückwärts; VIX über „Freitag geschlossen?" / „Mittwoch geschlossen?" |
| `landing/pages/vixpiration.html` | 22–25 | dieselbe Rechnung ein zweites Mal |
| `landing/pages/dashboard.html` | 9, 10 | OPEX-Termin mit `'NYSE'` fest verdrahtet |

**Paket B — Feiertage NYSE-only, über Listenposition oder mit stillem Ersatz (13 Stellen).**

| Datei | Stellen | was dort steht |
|---|---|---|
| `landing/js/strategy-compute.js` | 1, 2 | `SA.holidays._NYSE_SONDER` (unter `kalender_v1` gesperrt!) und `get(y,'NYSE')` minus Sonderschließungen |
| | 3 | Zeitzone über ein Ternär für genau drei Börsen, sonst New York |
| | 4 | `(!boerse \|\| boerse === 'NONE') ? 'NYSE' : boerse` — stiller Ersatz |
| | 5, 6 | `if (boerse !== 'NONE')` — Feiertagsstrategien fallen sonst weg |
| | 7 | `_geprueft` = `boerse === 'NYSE' \|\| boerse === 'XETRA'` |
| `landing/pages/dashboard.html` | 8 | `SA.holidays.detect(currentTicker \|\| 'NYSE')` — ein Börsenname als Ticker-Ersatz |
| | 11 | `if (ex !== 'NONE')` |
| | 12 | `NYSE_NAMES[holIdx]` — Feiertagsname über die **Listenposition** |
| `landing/pages/feiertage.html` | 13 | Vorgabebörse `'NYSE'` |
| `landing/pages/plain-vanilla.html` | 18–21 | vier Stellen, alle an `_exchange === 'NYSE'` bzw. `get(Y,'NYSE')` |

Verfügbare Bausteine nach V1c/V1d/V2: `SA.holidays` (Fassade, V2), `SA.boersenkalender`
mit `ereignisse`, `schliessungen`, `sitzungen`, `naechste`/`vorherige`, `verschiebe`,
`heute(boerse)`, `sitzungInfo`, `produkttermine`, `abdeckung`, `status`.

---

## 1. Zwei Pakete, getrennt gebaut und getrennt freigegeben

**Grund für die Trennung:** Paket A ändert **sichtbare Termine** auf zwei Seiten und im
Dashboard und hat eine Nutzerentscheidung an sich (Historie vor 2015 weglassen). Paket B
ändert Feiertagsanzeige und Strategiesignale. Ein gemeinsamer Bau hätte eine
Momentaufnahme, in der sich beides gleichzeitig bewegt — dann ist nicht mehr zu sagen,
welche Änderung welchen Unterschied verursacht hat.

Reihenfolge: **A zuerst**, weil die Vorbedingung (Momentaufnahme) nur A betrifft und weil
die Nutzerentscheidung dort schon vorliegt.

---

## 2. Vorbedingung von Paket A: die OPEX-Momentaufnahme

`docs/KALENDER_UMSTELLUNG.md` verlangt sie ausdrücklich: *„Vor dem V3-Umbau die
OPEX-Momentaufnahme einfrieren (2 592 Monate, alle Rückgabefelder von
`get_opex_date`/`get_all_opex_dates`, `populate_opex`)."*

Gebaut wie `scripts/kalender_momentaufnahme.py` (V1c-1): **eine Prüfsummenliste, keine
zweite Kalenderquelle.** Neu `scripts/opex_momentaufnahme.py` mit `--schreiben` und
`--pruefen`, Ziel `scripts/fixtures/opex_vor_v3.json`.

Erfasst wird je Monat im Bereich der bisherigen Funktionen:

* alle Rückgabefelder von `get_opex_date(j, m)` — nicht nur das Datum, denn der Umbau
  darf auch kein Nebenfeld verschieben,
* `get_all_opex_dates` als Ganzes,
* `populate_opex` je Jahr,
* und — das ist mein Zusatz — die **JS-Seite**: die heute auf den Seiten gerechneten
  Termine. Sonst friere ich nur Python ein und baue JS um.

Für die JS-Seite heißt das: die Rechnung aus `opex.html` und `vixpiration.html` wird
**einmal** in einer node-Probe ausgeführt und ihr Ergebnis mit eingefroren. Das ist
Arbeit, aber ohne sie gibt es für die 12 Stellen keinen Bestandsschutz — und genau
diese Stellen ändere ich.

**Offene Frage 1:** Reicht der Bereich der bisherigen Funktionen, oder soll die
Momentaufnahme auch die Monate umfassen, die nach der Umstellung **wegfallen** (vor
OPEX 2015-02 / VIX 2015-09)? Mein Vorschlag: ja, ausdrücklich mit aufnehmen und als
`entfaellt_mit_v3` kennzeichnen — dann steht schwarz auf weiß, was die
Nutzerentscheidung kostet, und der Wächter kann es prüfen statt es zu behaupten.

---

## 3. Paket A — die Termine kommen aus dem Katalog

Alle 12 Stellen rufen künftig `SA.boersenkalender.produkttermine(von, bis, art,
{pruefdatum})`. Die eigene Rechnung („dritter Freitag, dann rückwärts") verschwindet;
sie ist der Grund, warum derselbe Termin auf drei Seiten dreimal unterschiedlich
entstehen konnte.

**Was sich für den Leser ändert (Nutzerentscheidung vom 2026-10-12):**
Termine vor OPEX `2015-02` und VIX `2015-09` werden **weggelassen**, nicht
gekennzeichnet gezeigt. Für `/opex` und `/vixpiration` heißt das: die Historie beginnt
später als heute. Die Seiten sagen das in einem Satz, statt es stillschweigend zu tun.

**Die Feiertagsregel kommt mit.** Der Katalog kennt sie (Mittwoch ODER Freitag
geschlossen → einmal vor den Mittwoch). Belegbar gemessen: Kontraktmonat `2026-05`,
nominal `2026-05-20`, Settlement `2026-05-19`. Genau dieser Fall trennt eine korrekte
Umstellung von einer, die `nominal` nimmt — und er ist mir heute beim Einbau von
VIXpiration in die Morgen-Mail schon einmal nützlich gewesen.

**`pruefdatum` ist Pflicht.** Im Browser ist das „heute" der gewählten Börse, also
`SA.boersenkalender.heute('NYSE')` — **nicht** `new Date()`. Begründung: die
Einstufung belegt/projektion darf nicht von der Uhr des Besuchers abhängen, und das
Projekt hat für `new Date()` ohne Zeitzone schon einmal bezahlt (v66.8: 16 801 von
16 801 Tagen falsch unter `America/New_York`).

**Offene Frage 2:** Die Produkttermine sind **US-Produkte**. Dashboard-Stelle 9/10 zeigt
den OPEX-Termin heute für jeden Ticker, auch für `.DE`. Richtig wäre: der Termin gilt für
US-Produkte, und bei einem XETRA-Ticker ist er entweder weglassen oder als
US-Termin zu benennen. Was davon? Ich neige zu „benennen statt weglassen", weil der
Termin für den Gesamtmarkt relevant bleibt — aber das ist eine Anzeigeentscheidung und
keine Rechenfrage.

---

## 4. Paket B — Ereignisse statt Listenposition, und kein stiller Ersatz

**B1 Feiertagsnamen über `ereignisse()`.** Stelle 12 liest den Namen über
`NYSE_NAMES[holIdx]`, also über die **Position** in einer Liste. Das ist dieselbe
Fehlerklasse, die der Ereigniskatalog beseitigen sollte (V1c-1: „Identität je
Regeltermin, nie Listenposition") — und sie hat im Projekt schon einmal zugeschlagen:
`market_events` nannte „Good Friday" als Grund für Juneteenth.

**B2 Sonderschließungen.** Stellen 1 und 2 lesen `SA.holidays._NYSE_SONDER`, und das
ist unter `kalender_v1` **gesperrt**. Künftig `ereignisse(boerse, jahr)` und daraus die
Art filtern, statt eine Menge abzuziehen.

**B3 Kein stiller Ersatz mehr.** Stellen 4, 8, 11, 13 ersetzen eine fehlende oder
unbekannte Börse still durch NYSE. P1a hat dieselbe Klasse in Python geschlossen
(`get_exchange_for_holidays` wirft `ValueError` statt NYSE zu unterstellen). Im Browser
darf eine Seite nicht abstürzen, deshalb: **kennzeichnen und die Funktion abschalten**,
nicht ersetzen. Konkret bedeutet das eine sichtbare Zeile („für diesen Basiswert liegt
kein Börsenkalender vor") statt stillschweigend US-Feiertage.

**B4 `NONE` ist keine Börse.** Stellen 5, 6, 11 behandeln `'NONE'` als Sonderfall mit
Weglassen. Nach V1d gibt es `CRYPTO` (24/7) und `FOREX` (Mo–Fr, UTC) als echte
Kalender. Mein Vorschlag: `NONE` verschwindet als Begriff; wer heute `NONE` bekäme,
bekommt künftig den Kalender seines Handelsplatzes oder die Kennzeichnung aus B3.

**B5 Zeitzone.** Stelle 3 kennt drei Börsen. `heute(boerse)` kennt alle und wirft ohne
Zeitzone. Ersetzen.

**B6 Prüfumfang.** Stelle 7 hält `NYSE`/`XETRA` für geprüft. `status(boerse, jahr)`
sagt es genauer (belegt/annahme/ungeprueft/konvention). Der sichtbare Unterschied: eine
Strategie, die heute auf einem `annahme`-Kalender rechnet und das nicht sagt, sagt es
danach.

**Offene Frage 3:** B3 ändert, was der Nutzer sieht — eine Kennzeichnung statt
stillschweigender US-Feiertage. Ich halte das für eine Korrektur und nicht für ein
abgeschaltetes Feature, aber die Entscheidung gehört dem Nutzer, und ich baue sie nicht
ohne Antwort.

---

## 5. Wächter

Je Paket einer, im Gate, mit Mutationstest.

**Paket A** `scripts/verify_opex_v3.py`:
1. Momentaufnahme: jeder Monat **im belegten Bereich** ergibt vor und nach dem Umbau
   denselben Termin — Python und JS.
2. Die wegfallenden Monate fallen **nachweislich** weg und werden nicht still auf
   irgendetwas abgebildet.
3. Der Feiertagsfall `2026-05` (nominal ≠ Settlement) kommt auf beiden Seiten richtig
   heraus. Mutation „`nominal` statt `settlement`" muss reißen.
4. `pruefdatum` stammt aus `heute(boerse)`; eine Mutation auf `new Date()` muss reißen —
   geprüft **in drei Zeitzonen**, wie `verify_spot_vol_beta` es tut.
5. Die drei Seiten (`/opex`, `/vixpiration`, Dashboard) liefern für denselben Monat
   **denselben** Termin. Heute ist das nicht garantiert, weil jede ihre eigene Rechnung
   hat.

**Paket B** `scripts/verify_kalender_ereignisse_seiten.py`:
6. Feiertagsnamen über die Identität, nicht die Position: eine Mutation, die zwei
   Namen in der Liste **vertauscht**, muss reißen. Das ist der Fall, der in V1c-1
   unentdeckt geblieben wäre.
7. Kein stiller NYSE-Ersatz: ein unbekannter Handelsplatz ergibt die Kennzeichnung,
   **nicht** US-Feiertage.
8. Sonderschließungen kommen aus `ereignisse()`; `_NYSE_SONDER` wird nicht mehr gelesen
   (und ist unter `kalender_v1` gesperrt, also prüfbar).
9. `heute(boerse)` in drei Zeitzonen.
10. `status()` wird angezeigt, wenn er nicht `belegt` ist.

Beweisregeln wie gehabt. Und eine Lehre von heute früh ausdrücklich: **keine Prüfung,
die ein Wort sucht**, wenn das Wort im eigenen erklärenden Kommentar stehen kann — das
ist mir heute zweimal passiert (`HISTORIC_BEST`, `market_events`). Geprüft wird die
Wirkung.

---

## 6. Was dieser Entwurf NICHT macht

* **Keine Umstellung der Python-Leser** (`tdom_analysis`, `daily_report`, Mails) — das
  ist P3 und hat eine eigene Nutzerentscheidung, weil sich veröffentlichte Zahlen
  ändern können.
* **Kein Umschalter Kalendertag ↔ Handelstag** — V4.
* **Keine Bereinigung der 2 438 Phantomzeilen** — eigener Posten mit DB-Schreibzugriff.
* **Keine Änderung an `prices.tdom/tdoy`** — P5, Nutzerfreigabe.

## 7. Konkrete Bitte

1. Ist die Trennung in A und B richtig geschnitten, oder gehört eine Stelle ins andere
   Paket?
2. Reicht die Momentaufnahme aus Abschnitt 2 als Bestandsschutz — insbesondere, deckt
   sie die JS-Seite wirklich ab, oder täusche ich mich über den Umfang?
3. Die drei offenen Fragen (wegfallende Monate mit aufnehmen; US-Termin bei
   EU-Tickern; Kennzeichnung statt stillem Ersatz) — welche davon ist eine
   Nutzerentscheidung und welche kann ich selbst entscheiden?
4. Fehlt in der Wächterliste ein Fall, dessen Ausfall niemandem auffiele?
