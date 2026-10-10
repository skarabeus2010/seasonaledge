# Handelstag-Nummern — Plan v6: P1b isoliert (Weg A) (Runde 6)

Vorgänger: [v5](2026-10-10_xetra_tdoy_plan_v5.md) · [Antwort 5](2026-10-10_xetra_tdoy_plan_antwort5.md) („mit Auflagen“).
P1a ist **deployt** (Server auf `8f976a0`, Gates grün, im Container nachgeprüft).

<task>
**Nutzerentscheidung 2026-10-10: Weg A.** Datendatei und JS-Kalender werden **isoliert** gebaut — keine Seite
nutzt sie, bis P2–P4 fertig sind; dann wird alles in einem Schritt umgeschaltet, nach einer Liste der
veröffentlichten Zahlen, die sich ändern. Prüfe, ob der isolierte Aufbau die Auflagen aus Runde 5 erfüllt,
soweit sie ihn betreffen. Read-only.
</task>

## Entwurf
**I1 Neue, eigenständige Datei** `landing/js/boersenkalender.js` (erzeugt, getrackt) = Daten **und** API in
einem Bundle (deine Antwort 4: eine Anfrage, eine Generation). Namensraum `SA.boersenkalender` — **nicht**
`SA.holidays`. `holidays.js` und alle Seiten bleiben unverändert; keine Seite bindet die neue Datei ein
(Wächter prüft das, bis zur Aktivierung).

**I2 Datenvertrag** (Erzeuger `scripts/build_boersenkalender_js.py`, Quelle ausschließlich Python):
- `schema: 1`, `version: sha256` über die kanonische JSON-Serialisierung **aller** Nutzdaten
  (sortierte Schlüssel, `separators=(",", ":")`, `ensure_ascii=False`).
- `von: 1885, bis: 2100`; `woche` je Börse (`MoFr`/`taeglich`).
- `schliessungen[börse][jahr]` = Liste `{d: "MMDD", art: "feiertag"|"sonder"|"boerse"}` — `sonder` =
  Einmalschließung (NYSE `_NYSE_SPECIAL_CLOSURES`, XETRA `XETRA_SONDER`, TSE-Einmaltage), `boerse` =
  Schließung ohne Feiertag (TSE 2020-10-01). Dafür bekommt Python je Kalender eine Quelle der Art
  (`_SONDER`-Listen existieren; Codex-Auflage 6 „unmarkierte Liste reicht nicht“).
- **Keine Ereigniskennungen in P1b**: stabile Kennungen (Ostern, Thanksgiving …) brauchen erst
  `/feiertage` und das Dashboard (P4). Notiert, nicht vergessen.
- `status[börse]` = `[standard, [[von, bis, status], …]]` aus `KALENDER_GUELTIG`, Prüfdatum.
- `ticker` (370, aus `get_exchange_for_holidays`) und `suffix` (aus `SUFFIX_ZU_BOERSE`).

**I3 API** (`SA.boersenkalender`), zeitzonenfrei (nur ganzzahlige Jahr/Monat/Tag-Arithmetik, kein `Date`
mit lokaler Zeit — deine Apia-Gegenprobe): `boerse(ticker)`, `istHandelstag(iso, börse)`,
`nummern(isoListe, börse)` (= Python `handelstag_nummern`, gleiche fünf Felder, gleiche Fehler),
`nterHandelstag(j, m, n, börse)`, `letzterHandelstag(j, m, nVonHinten, börse)`, `nterHandelstagImJahr`,
`naechsterHandelstag(iso, börse)` (sucht bis zum ersten offenen Tag, über Jahresgrenzen; Datenende →
`throw`), `schliessungen(jahr, börse)` (mit `art`), `status(börse, jahr)`. Validierung zuerst (Typ, strenges
ISO, Börse inkl. Alias NASDAQ → NYSE, Bereich), auch vor Wochenend/CRYPTO-Abkürzungen. Kein `'NONE'`.

**I4 Git**: `.gitattributes` mit `landing/js/boersenkalender.js text eol=lf` (und für den Erzeuger-Output
generell); Prüfung byteweise gegen Arbeitsdatei **und** `git show HEAD:` ohne zu schreiben (`--pruefen`).

**I5 Prüfung** `scripts/verify_boersenkalender_js.py` (node führt die ECHTE Bundle-Datei aus):
(a) aktuell (`--pruefen`); (b) `istHandelstag` == Python für 13 Börsen × jeden Tag 1885–2100; (c) `nummern`
== `handelstag_nummern` für dieselbe Menge (alle fünf Felder); (d) die vier Monats-/Jahres-/Nächster-Tag-
APIs gegen Python-Referenzen inkl. TSE 2019-04-27 → 2019-05-07; (e) `boerse()` == Python für 370 Ticker +
Regelfälle + Fehlerfälle; (f) Validierung/Bereich/Alias/fehlende Daten; (g) Sollfälle aus
`verify_kalender_sollfaelle.py` in JS; (h) **zeitzonenfrei**: (b)–(d) unter mindestens `UTC`,
`Europe/Berlin`, `America/New_York`, `Pacific/Apia`, `Pacific/Kiritimati`, `America/Adak` (Zone im Prozess
gesetzt + Offset-Nachweis wie `verify_seasonal_twins` 4b); (i) **Isolation**: keine Datei unter `landing/`
außer der Bundle-Datei selbst referenziert `boersenkalender.js` oder `SA.boersenkalender`. Mutationstest
deterministisch (`python_probe`, Anker, benannte Prüfung). Im Deploy-Gate (node + numpy vorhanden).

**I6 Nicht in P1b** (bewusst, mit Ort): Aktivierung, `detect()`, `'NONE'`-Zweige, `/feiertage`- und
Dashboard-Ereignisvergleich, `app.js:877`, Forex auf Seiten, sichtbare Gültigkeitsanzeige → P4.
`holidays.js` `nextTradingDay` (10-Tage-Fehler) und Zeitzonenfehler bleiben bis zur Aktivierung im alten
Code — **Frage 2**.

## Fokusfragen
1. Erfüllt I1–I5 die Runde-5-Auflagen, die den isolierten Aufbau betreffen? Was fehlt im Datenvertrag
   für P4 schon jetzt (sonst Schema-Bruch später)?
2. Zwei heute live falsche Stellen in `holidays.js` (`nextTradingDay` gibt nach 10 Tagen einen geschlossenen
   Tag zurück; Datumsparsing über lokale Zeit) — jetzt im alten Code beheben (kleiner, sichtbarer Fix ohne
   Kalenderwechsel) oder bis zur Aktivierung lassen? Wo wirken sie heute konkret falsch (NYSE/XETRA/LSE)?
3. (h): Ist die Zeitzonenliste ausreichend, und wie setzt man die Zone in node verlässlich (Windows, Git Bash)?
4. Größe 1885–2100 mit `art` je Schließung: Bedenken?

## Ausgabevertrag
**Urteil** · **Antworten** (je ≤ 8 Zeilen, Datei:Zeile) · **Befunde** · **Auflagen vor dem Code**. ≤ 80 Zeilen.
