# Kalender-Umstellung V2 — Entwurf v2 (Browserkern)

Runde 1: [Entwurf v1](2026-10-18_kalender_v2_entwurf.md) · [Antwort](2026-10-18_kalender_v2_entwurf_antwort.md)
(keine Freigabe, 7 × P2, Architektur trägt; Antworten: Werfen bis V9 ja, String-Rückgabe behalten, Bundle schon in
V2, DB-Zeile im Header entbehrlich). v2 ändert v1 nur in den unten genannten Punkten. Read-only.

<task>Sind die sieben Befunde und die Auflagen aus Runde 1 erledigt? Ist v1 + v2 als Bauvorlage freigabefähig?</task>

## Zu den Befunden
**B1 — `catch → 'NONE'` und Kurzschlüsse.** In V2 werden die Stellen, die einen Zuordnungsfehler in „jeder Tag
offen“ oder NYSE verwandeln, **methodenabhängig** gemacht — `alt` bleibt Zeichen für Zeichen gleich im Verhalten:
`dashboard.html:565,626,643,2154,2193`, `monatszyklus.html:442`, `watchlist.html:315`. Muster:
`catch(e){ if (SA.kalenderMethode !== 'alt') throw e; ex = 'NONE'; }` und der Kurzschluss
`ex === 'NONE' || …` bleibt, weil unter `kalender_v1` `detect` nie `'NONE'` liefert (Inventar-Eintrag, Entfernen in
Phase der Seite). Ein Wächterteil sucht strukturell (Tokenizer, nicht Textsuche) nach `catch`-Blöcken, die einer
Variablen aus `detect` einen Börsennamen zuweisen, und nach `=== 'NONE'`/`'NYSE'`-Vergleichen auf `detect`-Ergebnissen;
jede Fundstelle muss entweder methodenabhängig sein oder im Inventar mit Phase stehen. Unbekannte Fundstelle → rot.

**B2 — Isolationsassertionen.** Beide werden ersetzt: `verify_boersenkalender_js.py:268` (`isolation_scan`) und die
entsprechende Prüfung in `verify_einbindung.py` weichen einem **Einbindungsvertrag** aus einem Manifest
(`scripts/fixtures/einbindung_manifest.json`): Liste der Seiten, die `holidays.js` laden (heute 26) + Converter; je
Seite Pflichtreihenfolge `methode.js` → `boersenkalender.js` → `holidays.js` → erste Verbraucherdatei; Seiten
außerhalb des Manifests dürfen das Bundle **nicht** laden. Prüfung auf `landing/`, generiertem `landing/en/` und der
gebauten Converter-Ausgabe. Lese-/Traversierungsfehler bleiben rot (die Gegenprobe `kaputter_walk` wird übernommen).

**B3 — Converter-Vertrag.** Ausdrücklich:
- Eingabe ISO-Datum + Börse; Ausgabe CDOY, TDOM, TDOY, Rückwärtsnummern, Monats-/Jahressumme (= Länge von
  `sitzungen`), `offen`, Kalenderstatus `status(b, jahr)`.
- Geschlossener Tag: „geschlossen“ + kumulierte Vorwärtsnummern (B1.3), keine Rückwärtsnummern.
- CRYPTO „täglich (Konvention)“, FOREX „Mo–Fr ohne Feiertage (Konvention)“ sichtbar; `annahme` sichtbar;
  `ungeprueft` → Ergebnis als „exploratorisch, Kalender dieses Jahres nicht belegt“ markiert.
- Erklärkarten/FAQ ohne feste Grenzen: „1–23“, „1–252“, „365“ werden durch **gemessene** Spannen ersetzt
  (TDOM-Monatssummen und TDOY-Jahressummen je Börse über 2000–2030, im Build aus dem Bundle erzeugt; CDOY 1–365/366).
  Die Texte sind methodenneutral formuliert und gelten auch unter `alt` — sie werden in V2 geändert.
- Release-/Methodenvertrag: der Converter bekommt `__SA_RELEASE`/`__SA_METHODE` und `methode.js` wie die Seiten
  (`deploy/release_setzen.py:31` erfasst `seo/tools` schon); beide Zweige werden auf der **ausgelieferten** Seite
  (`seo/output/…` nach dem Build) in jsdom geprüft.

**B4 — Unabhängigkeit der Prüfung.** Die Fassade ist reine Delegation; ihre Prüfung unter `kalender_v1` hat drei
Ebenen:
1. **Delegation:** Fassade = `SA.boersenkalender` für jede Funktion auf einem Raster je Börse 1990–2035 (beweist nur
   Weiterleitung, nicht Richtigkeit — so benannt).
2. **Richtigkeit gegen Sollfälle mit Quelle, durch die Fassade:** alle 86 Fälle aus `verify_kalender_sollfaelle.py`
   und die Sollfälle aus `verify_boersenereignisse.py` werden zusätzlich über `SA.holidays.isTradingDay/get` geprüft;
   dazu **handgeschriebene Sitzungslisten** je Börse für je einen Monat mit Feiertag (NYSE 11/2026, XETRA 12/2026,
   LSE 05/2026, EURONEXT 04/2026, MILAN 12/2026, SIX 08/2026, STOCKHOLM 06/2026, OSLO 05/2026, TSE 05/2026,
   HKEX 10/2026, KRX 09/2026, CRYPTO 02/2028, FOREX 12/2026) aus dem jeweils veröffentlichten Börsenkalender,
   Quelle je Liste notiert, **nicht** aus dem Bundle erzeugt.
3. **Statusgrenzen:** je Börse das erste/letzte `belegt`-Jahr und das Nachbarjahr (aus `kalender_status` abgelesen und
   als Literal festgeschrieben), Anzeige im Header/Converter entsprechend.
Dazu aus C: DST-Wechsel (NYSE März/November, Europa März/Oktober) und Mitternacht in sechs Zonen für Header-`heute`;
**A→B→A-Tickerwechsel** (SPY → SAP.DE → SPY, BTC-USD → EURUSD=X → BTC-USD) auf Dashboard, TDOM-Analyse, Watchlist
mit Nachweis, dass Header und Zähler je Schritt der neuen Börse folgen.

**B5 — Rückgabe-/Fehlervertrag** (nur `kalender_v1`; `alt` unverändert):

| Fall | Ergebnis |
|---|---|
| Börse fehlt (`undefined`/`''`) | Fehler (alt: NYSE) |
| Börse unbekannt oder `'NONE'` | Fehler |
| Datum keine Zeichenkette `YYYY-MM-DD` oder ungültig (30.02.) | Fehler |
| Jahr/Monat/`n` keine ganze Zahl | Fehler |
| `n < 1` | Fehler |
| `n` > Periodensumme | `null` (wie alt) |
| außerhalb 1885–2100 | Fehler |
| `detect('')`/`detect(null)` | Fehler |
| `detect` unbekannter Index/Future/Suffix | Fehler |
| `detect` unbekannter einfacher Name | `'NYSE'` (Listingregel, wie Python) |

Fehlerklasse ist die vorhandene `KalenderFehler` des Bundles; die Fassade fängt nichts ab. Header und Converter
ergänzen `nummern` um `status(b, jahr)` selbst.

**B6 — Sonderliste.** Unter `kalender_v1` ist `SA.holidays._NYSE_SONDER` (und `_XETRA_SONDER`) eine Eigenschaft mit
**werfendem Getter** (`Object.defineProperty`, Meldung „ersetzt durch ereignisse(), Verbraucher in V3 umstellen“),
damit `strategy-compute.js:335` nicht still `[]` nimmt. Inventar: `strategy-compute.js:335` → V3.

**B7 — Zuordnung.** Vertrag präzisiert: `detect` folgt der gemeinsamen Listingregel (`boerse` = Python
`get_exchange_for_holidays`), d. h. unbekannte einfache Namen → NYSE. Der Header bekommt deshalb einen optionalen
4. Parameter `kalenderTicker`; `sektor-rotation.html:671` übergibt `'SPY'` und behält „n Sektoren“ als Anzeigetext.
Unter `alt` wird der Parameter ignoriert (Ausgabe unverändert); unter `kalender_v1` nennt der Header „Kalender:
SPY · NYSE“.

## Zu den Auflagen
- Header: **alle** Felder (Wochentag, Datum, TDOM, TWOY, TDOY, Quartal, Zyklus) aus demselben Börsendatum
  `heute(b, jetzt).datum`; TWOY als ISO-Woche dieses Datums (rein arithmetisch auf Y/M/T, kein `Date` mit lokaler Zone).
  `ungeprueft` → Zusatz „exploratorisch“.
- Momentaufnahme `alt` vor dem ersten Codeschritt eingefroren, mit Defaults (`exchange` fehlt → NYSE, `nFromEnd`
  fehlt → 1), Rückgabeformen (`null`, Ausgangsdatum nach 10 Tagen), Fehlerverhalten und Randfällen; plus
  Header-Ausgabe unter festen Uhren für alle 23 Header-Seiten und der Converter-Ausgabe für ein Datumsraster.
- Mutationen nennen je die Vertragszeile, die sie verletzen (B5-Tabelle, B1.x, Einbindungsvertrag).

## Reihenfolge der Umsetzung
0. gzip im Block `location ~* ^/landing/.+\.(css|js)$` (eigener Commit, HTTP-Nachweis `Content-Encoding: gzip` auf
   `app.js` und `boersenkalender.js`, nginx per `restart`).
1. Momentaufnahme `alt` einfrieren.
2. Fassade + Sonderliste + Fehlervertrag; Wächter Delegation/Sollfälle/Momentaufnahme.
3. Einbindung (Manifest, beide Isolationsassertionen ersetzt) auf 26 Seiten.
4. Catch-/Kurzschlussstellen + Inventar-Wächter.
5. Header (+ i18n, `_JSON_VER`), Seitenproben in jsdom.
6. Converter.
7. Mutationstest, Gate-Schritte, Codex-Coderunden.

## Fragen
1. Ist die Prüfung in drei Ebenen (Delegation / Sollfälle mit Quelle / Statusgrenzen) unabhängig genug, oder fehlt
   eine Ebene?
2. Reicht ein Monat je Börse als handgeschriebene Sitzungsliste?
3. Converter-Texte methodenneutral schon in V2 ändern — einverstanden?

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2) · **Antworten 1–3** · **Auflagen**. ≤ 30 Zeilen.
