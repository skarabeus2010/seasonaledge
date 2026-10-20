# Entwurf V3 v2 — Ereignisse

Runde 1 war **NICHT TRAGFÄHIG**, elf Befunde. Ich habe alle am Code nachgeprüft und
alle als zutreffend bestätigt; drei trafen die Grundlage, nicht Details. v2 ist eine
Neufassung, kein Flicken.

Dazu zwei Nutzerentscheidungen vom 2026-10-20, die den Umfang ändern:

* **Dashboard-OPEX-Karte bei Nicht-US-Tickern weglassen** (nicht umbenennen — gegen
  Codex' Empfehlung, Entscheidung des Nutzers).
* **Ereignismarkt der Feiertagsstrategien: noch nicht umstellen.** Die Messung liegt
  vor (`scripts/research/feiertag_ereignismarkt.js`: XETRA-Titel besser mit lokalem
  Kalender, US-Titel ohne Unterschied), aber sie ist beschreibend. Der Nutzer verlangt
  zuerst eine **richtige Studie mit vorab festgelegtem Plan und Prüfzeitraum**, wie bei
  den Williams-Mustern. **Folge für V3: NYSE bleibt der Ereignismarkt.** Befund B8
  verschwindet damit aus V3 und wird ein eigenes Vorhaben.

---

## 1. Was ich in Runde 1 falsch hatte (und was daraus folgt)

**B1 — die Aufrufformen.** Am Code nachgeprüft:
`heute(boerse, jetzt)` nimmt **zwei** Argumente und liefert ein **Objekt** mit `.datum`;
`produkttermine(von, bis, art, pruefdatum)` nimmt das Prüfdatum **positional**;
JS-`ereignisse(j, boerse)` erwartet das **Jahr zuerst** — in Python ist es
`ereignisse(boerse, jahr)`. Alle drei Formen aus v1 hätten geworfen.

**Vertrag für v2, wörtlich:**

```
const tag   = K.heute('NYSE', jetztMs).datum;          // ein Zeitpunkt JE AUSWERTUNG
const liste = K.produkttermine(von, bis, 'vix', tag);
const ev    = K.ereignisse(jahr, boerse);              // Jahr zuerst (JS!)
```

Der Zeitpunkt wird **einmal je Auswertung** erfasst und durchgereicht, nicht an jeder
Stelle neu geholt — sonst kann eine Auswertung zwei verschiedene „heute" sehen.

**B2 — die Methodenisolation gilt bis V9.** Das ist der schwerste meiner Fehler: v1
schrieb „die eigene Rechnung verschwindet". Die Fassade delegiert nur unter
`kalender_v1`; unter `alt` läuft der alte Code gegen die eingefrorene
`holidays_alt.json`. Eine Umsetzung nach v1 hätte **schon unter `alt`** Historie und
Signale geändert.

**Beide Pakete werden methodenabhängig gebaut.** Jede umgestellte Stelle bekommt zwei
Zweige: unter `alt` bleibt der bisherige Code **unverändert**, unter `kalender_v1` läuft
die neue Ableitung. Die alten Regeln werden im neuen Zweig **nicht** aufgerufen. Der
Wächter prüft beide Zweige: unter `alt` Bestandsschutz gegen die Momentaufnahme, unter
`kalender_v1` die neue Wirkung.

**B3 — die Monatsidentität ist verschoben.** `getVixpirationDateStr(y, m)` nimmt den
**OPEX-Monat** und rechnet 30 Tage zurück; der Katalog ist nach **Kontraktmonat**
geordnet. Nachgeprüft: alter Aufruf `(2026, 6)` → `2026-05-19`; Katalog `2026-05` →
derselbe Tag; Katalog `2026-06` → ein anderer. `buildOpexDates` speichert
`{date, year, month, isTriple, vixDate, vixLtd}`, wobei `year`/`month`/`isTriple` den
**Referenzmonat** tragen und in Gruppierung und Monatsdarstellung eingehen.

**Ein Vergleich der Datumsmenge sieht das nicht** — die Daten bleiben dieselben, nur die
Beschriftung wandert. Deshalb braucht v2 eine **ausdrückliche Zuordnungstabelle**
Referenzmonat ↔ Kontraktmonat, inklusive Januar/Dezember-Übergang und Startgrenze, und
die Momentaufnahme friert **alle Felder** ein, nicht nur `date`. Zusätzlich: `vixLtd` ist
der **Options**handelsschluss, nicht das Futures-Handelsende — im Katalog
`handelsende_optionen`, nicht `handelsende_futures`.

---

## 2. Vorbedingung: die Momentaufnahme, in vollem Umfang

**Python** (`scripts/opex_momentaufnahme.py`, Muster `kalender_momentaufnahme.py`):
alle **2 592 Monate 1885-01 bis 2100-12** — ausdrücklich auch die, die im Browser nach
der Umstellung wegfallen (Codex' Antwort O1: „`entfaellt_mit_v3` ist eine Erwartung für
den neuen Verbraucher, kein Grund, alte Ergebnisse auszulassen"). Erfasst werden
**sämtliche** Rückgabefelder von `get_opex_date`, `get_all_opex_dates` und
`populate_opex` — also auch `adjusted`, `holiday_note`, `type`, `subtype`, `meta`. Eine
Datumsprüfung schützt diese Felder nicht; die heutige Verschiebungsnotiz lautet
pauschal „Good Friday", und genau so etwas soll sichtbar werden, wenn es sich ändert.

Drei Zustände werden unterschieden, nicht zwei: **außerhalb des Regelbereichs**,
**unbelegte historische Feldgruppe**, **Zukunftsprojektion**.

**JS** (`scripts/js/opex_momentaufnahme_probe.js`): die heute auf den Seiten gerechneten
Ergebnisse, **je Seite getrennt** und mit allen Feldern:

* `opex.html` → `buildOpexDates` vollständig: `{date, year, month, isTriple, vixDate, vixLtd}`
* `vixpiration.html` → dieselben Funktionen, eigener Lauf (sie sind Kopien, aber das ist
  eine Behauptung, die die Momentaufnahme **prüfen** soll, nicht voraussetzen)
* `dashboard.html` → `getNextEvents` samt der eigenen **15-Jahres-OPEX-Historie**
  (`historicDates`). Die fehlte in v1 vollständig.

Ohne diesen Teil friere ich Python ein und baue JS um — genau der Fehler, den das
Projekt als „eine Momentaufnahme, die nur eine Seite einfriert" kennt.

---

## 3. Paket A — Produkttermine (10 Inventarstellen)

Codex' Zählung übernommen: A umfasst die Stellen 9–10, 14–17, 22–25 (**10**), nicht 12.

Unter `kalender_v1` kommen die Termine aus `produkttermine`. Zu klären war, dass „ab
2015 verfügbar" und „nur belegte Termine" **nicht dasselbe** sind — B4, am Katalog
nachgeprüft:

| Fall | Katalog zum Prüfdatum 2026-10-20 |
|---|---|
| OPEX `2015-02` | **kein Eintrag** (historische Beleglücke) |
| VIX `2015-09` | Futures-Settlement belegt, `handelsende_optionen: null` |
| OPEX `2027-01` | **Projektion** |

Daraus die Regel: **Zulässigkeit je Produkt UND Feldgruppe.** Die Seite zeigt einen
Termin nur, wenn die benötigte Feldgruppe `belegt` ist; eine Projektion wird entweder
gekennzeichnet oder weggelassen (Nutzerentscheidung steht: weglassen). Ein fehlender
Optionswert wird **nicht** aus dem Futures-Termin abgeleitet und **nicht** durch die
alte Rechnung ersetzt. Die VIX-Historie entsteht **unabhängig** von der
OPEX-Verfügbarkeit — ein gemeinsamer Join würde gültige VIX-Termine verlieren, weil
OPEX 2015–2019 Lücken hat.

**Dashboard:** Die OPEX-Karte entfällt bei Nicht-US-Tickern (Nutzerentscheidung). Das
ist die einzige sichtbare Produktänderung in Paket A außer der verkürzten Historie.

---

## 4. Paket B — Feiertagsereignisse (15 Inventarstellen, ohne Ereignismarkt)

**B7 — der Ereignisvertrag.** `ereignisse()` enthält fünf Arten, gemessen:
NYSE 2026 = 9 `feiertag` + 1 `ersatztag` + 2 `halbtag`; NYSE 2001 = 9 `feiertag` +
4 `sonderschliessung`; XETRA 2026 = 8 `feiertag`. „Art filtern" ist kein Vertrag.
Je Verbraucher wird festgelegt:

| Verbraucher | zulässige Arten | Datum | Mehrfach |
|---|---|---|---|
| Feiertagsanzeige | `feiertag`, `ersatztag` | `wirksam` | je Tag einmal |
| Handelsanlass der Strategien | `feiertag`, `ersatztag` — **weiter NYSE** | `wirksam` | je Tag einmal |
| Geschlossen-Prüfung | `feiertag`, `ersatztag`, `sonderschliessung`, `unbestimmt` | `wirksam` | — |
| Halbtage | **nie** als Feiertagsanlass — offene Sitzung | — | — |

**N1 — die Reihenfolge gehört in den Vertrag.** `ereignisse()` liefert
**Katalogreihenfolge**, nicht chronologische. Am Code nachgeprüft, NYSE 2026: Weihnachten
(`2026-12-25`) kommt **vor** Labor Day (`2026-09-07`) und Thanksgiving (`2026-11-26`).
`calc_one_day_holiday` und `calc_uhts` übernehmen diese Reihenfolge, und `auswerten`
reicht sie unsortiert an `computeStats`, das daraus Anfang, Ende und Drawdown bildet.
Eine reine Filter- und Abbildungs-Umstellung hätte die **Kennzahlen allein über die
Reihenfolge** verändert — Codex hat es an 21 synthetischen Trades gemessen: unsortiert
CAGR −0,72 % und Drawdown −2,4 %, chronologisch −0,69 % und −1,8 %.

Also: im neuen Zweig wird nach der Entdoppelung **aufsteigend sortiert**, und das steht
im Vertrag, nicht im Zufall. (Meine eigene Messung zum Ereignismarkt war davon nicht
betroffen, weil sie `.sort()` aufruft — Glück, nicht Absicht.)

`unbestimmt` (Tabellenereignisse) wird als „geschlossen (Tabelle)" behandelt und bekommt
**keine** erfundene jährliche Feiertagsfamilie; sie haben keine belegte
Feiertagsidentität (benannte Abnahmelücke HKEX/KRX 2016–2026).

**B6 — die Listenposition steckt an mehr Stellen als inventarisiert.** Nachzuziehen
sind: `dashboard.html:1303` (`hyHols[holIdx]`, auch für die **historische Stichprobe** —
nur den sichtbaren Namen zu ersetzen ließe falsche Vergleichsrenditen stehen),
`feiertage.html::getHolidayDates` (Zuordnung nach Position, Rückfall auf
`HOL_NAMES.NYSE`, Begrenzung auf die Namenanzahl), `renderNext` und `buildCheckboxes`.
Verbunden wird über **Börse + `regel_id`**, nicht über `ereignis_id` — die enthält das
Jahr und ist kein jahresübergreifender Schlüssel.

Die inventarisierte Zeile `_currentExchange = 'NYSE'` ist **nicht** der entscheidende
Pfad: `loadTicker` setzt die erkannte Börse. Sie wird mitgeändert, aber der Wächter
prüft `loadTicker`.

**B3 der Fehlerverträge — kein stiller Ersatz, und drei Fälle unterscheiden:**
„Kalender unbekannt", „bekannter Kalender ohne Feiertage" (CRYPTO, FOREX) und „Termin
nicht belegt". CRYPTO und FOREX dürfen **nicht** als unbekannte Handelsplätze
erscheinen — sie haben einen Kalender, er ist nur leer.

**B9 — `_geprueft` geht nach V4.** Es ist keine Anzeige: der Rückgabewert entscheidet
zwischen exakter Zählung fehlender Sitzungen und der Heuristik „mehr als vier
Kalendertage" und verändert `fehlende_sitzungen`, `auffaellige_abstaende` und bei
Hebeltrades `naeherung`. Außerdem wären alle vier Statuszeichenketten wahrheitswertig —
ein direkter Austausch gegen `status()` hätte die Heuristik stillschweigend
abgeschaltet. Das ist eine Rechenänderung und gehört nicht in V3.

**B10 — die übrigen Zeitpfade.** Ein korrektes Prüfdatum behebt sie nicht:
Zeitraumgrenzen, Auswahl kommender Ereignisse, Countdown und Beschriftung nutzen
weiter UTC-Tagesdatum oder lokale Browserzeit (`opex.html:943,958,1149`;
`vixpiration.html:864,879,1055`; `plain-vanilla.html:523,549`), und `/opex` hängt
unabhängig vom Datum fest „(Mi)" an die VIXpiration (`:963`). Ein Börsentag **je
Auswertung**, Datumsausgabe ohne lokale Umdeutung — und der Fall `2026-05-19` muss als
**Dienstag** erscheinen, nicht als Mittwoch.

**B11 — Fehler am Seiteneinstieg.** Das Dashboard fängt Kalenderfehler mit `catch(e){}`;
Ereignisse können still verschwinden. Künftig wird am Seiteneinstieg behandelt und die
kalenderabhängige Ausgabe **zurückgesetzt**, damit nach einem Tickerwechsel kein altes
Ergebnis stehenbleibt. Erwartete Kalenderfehler werden von Programmfehlern
unterschieden.

---

## 5. Wächter

**Paket A** `scripts/verify_opex_v3.py`:
1. Unter `alt`: jede Seite und Python ergeben **Feld für Feld** die Momentaufnahme.
2. Unter `kalender_v1`: belegte Monate ergeben denselben Termin; die wegfallenden
   fallen **nachweislich** weg und werden nicht still abgebildet.
3. Die Zuordnungstabelle Referenz- ↔ Kontraktmonat, inklusive Januar/Dezember und
   Startgrenze. Mutation „Zeilenmonat als Kontraktmonat" muss reißen.
4. `isTriple` und die Gruppierung bleiben am Referenzmonat (oder die Änderung wird
   ausdrücklich ausgewiesen).
5. `handelsende_optionen` ≠ `handelsende_futures`; eine Mutation, die das eine für das
   andere nimmt, muss reißen.
6. Abdeckung je Feldgruppe: OPEX `2015-02` ohne Eintrag, VIX `2015-09` mit `null`
   Optionswert, OPEX `2027-01` als Projektion — jeder Fall einzeln.
7. Die drei Seiten liefern für denselben Monat **denselben** Termin (heute nicht
   garantiert, weil jede ihre eigene Rechnung hat). Dazu: **drei Seiten mit demselben
   falschen Adapter bestehen jede Gleichheitsprüfung** — also zusätzlich gegen die
   Momentaufnahme, nicht nur gegeneinander.
8. Prüfdatum aus `heute(boerse, jetztMs).datum`, **ein** Zeitpunkt je Auswertung,
   geprüft in drei Zeitzonen mit **demselben festen** Zeitpunkt an Tages- und
   Jahresgrenzen — sichtbare Auswahl, Beschriftung und Countdown.
9. Dashboard ohne OPEX-Karte bei `.DE`, mit Karte bei US-Tickern.

**Paket B** `scripts/verify_kalender_ereignisse_seiten.py`:
10. Namen und historische Stichprobe über **Börse + `regel_id`**. Mutationen: zwei
    Namen vertauschen; die Ereignisreihenfolge ändern, ohne die Objekte zu verfälschen.
    Prüffälle Juneteenth vor/nach Einführung und die Carter-Sonderschließung 2025.
11. Je Verbraucher die zulässigen Arten, mit unabhängigen Sollwerten. Halbtage sind
    **keine** Feiertage; `unbestimmt` erzeugt keine Feiertagsfamilie.
12. Drei Fehlerzustände getrennt; CRYPTO/FOREX als **erfolgreicher Leerfall**.
13. Tickerwechsel gültig → unbekannt → gültig: die alte Ausgabe verschwindet.
14. `catch(e){}` ist weg; ein erwarteter Kalenderfehler ist von einem Programmfehler
    unterscheidbar.
15. Die echten Seiten mit festen Kursfixtures — eine herausgelöste Terminrechnung
    beweist keine Einbindung.
16. Unter `alt` ändert sich **nichts** (Bestandsschutz), unter `kalender_v1` die neue
    Wirkung. Eine Mutation, die den alten Zweig im neuen Pfad aufruft, muss reißen.
17. **Reihenfolgeinvarianz bis zu den Kennzahlen** (N1): bei permutierter Ereignisliste
    liefern `one_day_holiday` und `uhts` **identische** Trades UND identische
    Kennzahlen. Eine Mutation, die die Sortierung im neuen Zweig entfernt, muss reißen
    — und zwar an den Kennzahlen, nicht nur an der Trade-Reihenfolge.

Keine Prüfung, die ein **Wort** sucht, das im eigenen erklärenden Kommentar stehen kann
— das ist mir am 2026-10-20 zweimal passiert.

---

## 6. Was V3 ausdrücklich NICHT macht

* **Kein Wechsel des Ereignismarktes** (Nutzerentscheidung: erst eine Studie mit
  vorab festgelegtem Plan und Prüfzeitraum). NYSE bleibt der Handelsanlass; die
  Strategieseite benennt ihn sichtbar als US-Feiertag.
* **`_geprueft` nach V4** (ändert die Rechnung, nicht die Anzeige).
* Keine Python-Leser, kein Kalendertag-/Handelstag-Umschalter, keine
  Phantomzeilen-Bereinigung, keine `prices`-Schreibzugriffe.

## 7. Bitte für Runde 2

1. Ist der methodenabhängige Bau aus Abschnitt 1 (B2) so beschrieben, dass unter `alt`
   nachweislich nichts passiert?
2. Deckt die Momentaufnahme aus Abschnitt 2 jetzt den Bestand — oder bleibt ein
   Rückgabewert, der nach dem Umbau unbemerkt anders wird?
3. Ist die Zuordnungstabelle Referenz- ↔ Kontraktmonat der richtige Weg, oder gibt es
   einen Fall, in dem sie nicht eindeutig ist?
4. Fehlt in der Wächterliste 1–16 ein Fall, dessen Ausfall niemandem auffiele?
