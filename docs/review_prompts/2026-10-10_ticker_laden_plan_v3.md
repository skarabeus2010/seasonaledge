# Neue Ticker schneller laden — Plan v3 (Runde 3)

Vorgänger: [v2](2026-10-10_ticker_laden_plan_v2.md) · [Antwort 2](2026-10-10_ticker_laden_plan_antwort2.md) (11 Befunde,
Auflagen vor S1) · [Antwort 1](2026-10-10_ticker_laden_plan_antwort1.md) (Bestandsaufnahme). Read-only.

<task>Prüfe, ob v3 die Auflagen vor S1 erfüllt und als Bauplan reicht. S3 bleibt ausdrücklich Schattenmodus.</task>

## S0 Messbasis (reproduzierbar)
- **Transport** `scripts/perf/kurse_messen.py` (wie v2): sechs Ticker, Varianten „heute F“, „heute V“, „neuer
  Lader“, 10 gültige Läufe abwechselnd, Median/p95, Anfragen, Bytes, Zeilen; Fehlerkörper = ungültiger Lauf.
- **Browser** `scripts/perf/seiten_messen.mjs` mit Playwright in fester Version (`package.json` unter
  `scripts/perf/`, `npx playwright install chromium`), gegen die **Live-Seite** `https://seasonalpha.ai` (echte
  nginx-Routen und Header) für den Vorher-Wert und gegen einen lokalen Stand für den Nachher-Wert — dafür ein
  Abfang der eigenen `/landing/js/*.js` per `page.route` auf die Arbeitsdateien (gleiche Seite, gleiche Header,
  nur die JS-Dateien ausgetauscht; Supabase bleibt live). Messpunkte: Ticker auswählen (echter Handler) →
  erstes fertiges Chart (`apexcharts`-Ereignis `mounted`/`updated` am Hauptchart, je Seite benannt) → vollständige
  Ansicht (Score/Radar-Element gefüllt). Zustände: kalt (neuer Kontext), Rückwechsel A→B→A, zweite Seite im
  selben Tab. Profile: Desktop und „Slow 4G“-Drosselung. Watchlist ohne Anmeldung nicht messbar → ausgenommen,
  nur Funktionsprobe. **Kein Deploy-Gate** (Live-Leistung schwankt); Ergebnis als Messbericht in
  `docs/TICKER_LADEN.md`. Leistungsziel vorab: p95 „erstes Chart, kalt“ für ^DJI auf Dashboard/Dekadenzyklus
  −50 % gegenüber vorher; keine Seite langsamer als vorher (Median).

## S1 Gemeinsamer Lader `SA.kurse` — Vertrag
**Aufruf** `SA.kurse.laden(ticker, {felder, ab})` → `Promise<Zeile[]>`.
- `felder` ⊆ {date, open, high, low, close, log_return, tdom, tdoy}; `date` immer enthalten. `ab` = `'YYYY-MM-DD'`
  oder `null` (ganze Historie).
- **Rückgabe** = neues Array mit **kopierten** Zeilenobjekten, genau die Zeilen mit `date >= ab` (Grenztag
  eingeschlossen), aufsteigend, genau die angeforderten Felder; Werte unverändert aus der Datenbank (Zahlen als
  Zahlen, `null` bleibt `null`, `0` bleibt `0`); fehlt einer Zeile ein angefordertes Feld (Spalte nicht geladen),
  ist das ein Vertragsbruch → Ablehnung, nie ein stilles `undefined`.
- **Vollständig oder Ablehnung**: Keyset (`order=date.asc&limit=1000&date=gt.<letztes>`), Ende = Block < 1000;
  HTTP-/Array-Prüfung je Block; Retry bei 429/5xx/Netz (wie F, `Retry-After` beachten); ein gescheiterter Block
  lehnt die ganze Ladung ab, nichts wird veröffentlicht oder gecacht. Timeout je Block 20 s → Fehler.

**Koordinator je Ticker** (ein Objekt pro Ticker):
- Zustand: `bestand` (Zeilen), `felder` (geladener Feldsatz), `abdeckungAb` (die **angeforderte** Grenze, ab der
  der Bestand vollständig ist; `null` = ganze Historie — unabhängig vom frühesten vorhandenen Datum, auch bei
  leerem Ergebnis), `geladenUm`, `laufend` (Promise + deren Feldsatz/Grenze).
- **Deckt** der Bestand eine Anfrage (Felder ⊆ `felder`, `ab` ≥ `abdeckungAb` bzw. `abdeckungAb = null`) und ist
  er jünger als 15 min → Sicht daraus. **Deckt** eine laufende Ladung die Anfrage → auf sie warten.
- Sonst **eine neue Ladung des vereinigten Bedarfs** (Felder ∪, früheste Grenze, `null` gewinnt) — vollständig
  neu, keine Teil-Nachladung; laufen schon Ladungen, wird die neue danach eingereiht (höchstens eine wartende,
  deren Bedarf wächst mit). Erst **nach Erfolg** ersetzt sie den Bestand (atomar: neuer Bestand, neue Felder,
  neue Abdeckung, neues `geladenUm`); eine später fertige kleinere Ladung überschreibt keinen größeren neueren
  Bestand (Generationszähler). Fehler → alle wartenden Anfragen dieser Ladung lehnen ab; ein älterer gültiger
  Bestand bleibt, verlängert aber seine Frische nicht.
- **Speicher**: höchstens 12 Ticker-Bestände, LRU; je Dokument (keine Seitenübergreifung — Navigation lädt neu,
  das wird in S0 gemessen; HTTP-Cache greift für Supabase nicht).
- **Pool**: höchstens 4 gleichzeitige Netzanfragen über alle Ticker; Blöcke einer Ladung bleiben sequenziell
  (Keyset), Parallelität entsteht über verschiedene Ticker.

**Migration** (jede Zeile der Bestandsaufnahme aus Runde 1, 27 Ladestellen): gleiche Felder, gleiche Grenze wie
heute → Sollwert „unveränderte Zahl“ je Seite. Zusätzlich:
- lokale Ergebnis-Caches ohne TTL (Dekadenzyklus `tickerCache`, Earnings, Dividenden) rufen künftig immer
  `SA.kurse.laden` (dessen TTL gilt) und cachen nur noch abgeleitete Ergebnisse **mit** der Bestandsgeneration
  als Schlüssel;
- **jeder** Abschluss, auch Nebenabrufe (Dashboard-Overnight, Radar, Score), prüft `SA.ladeKennung.aktuell` vor
  dem Zeichnen;
- Score (`mitHistorie`) und Radar (`anomalieMitHistorie`) behalten ihre Regeln (volle Historie bzw. 31 Jahre) —
  nur der Ladeweg ändert sich; `fetchAllPrices`/`ladeVollHistorie` werden zu dünnen Hüllen auf `SA.kurse` und
  danach entfernt, sobald kein Aufrufer bleibt;
- `kurse.js` wird in **jeder** Seite eingebunden, die einen Lader nutzt (Liste aus Runde 1), vor den
  Seiten-Skripten; EN-Seiten über `build_en.py` (prüfen);
- alte localStorage-Einträge `sa-cache-prices*` werden beim Start einmal entfernt.

**Behoben dabei**: Dashboard-Overnight ohne Pagination, zehn lokale Lader ohne Fehlerprüfung, O1-Kürzung.

## S2 entfällt weitgehend
Nach S1 hat `SA.cache` keinen Kursnutzer mehr (Antwort 2, Befund 7). S2 = nur noch: übergroße Einträge vorab
ablehnen (`> 512 KB` → `false`), bei Quota-Fehler **nur** eigene `sa-cache-*`-Einträge in LRU-Reihenfolge
verdrängen, Nicht-Quota-Fehler ohne Verdrängung → `false`.

## S1-Prüfung
- `scripts/js/probe_kurse.js` (node, echter `kurse.js`, gestubbtes `fetch` mit PostgREST-Verhalten: `…/*`,
  1000er-Grenze, Fehler im n-ten Block, 429 + Retry-After, Timeout): Sollmengen 0/999/1000/1001/2000/33 739;
  Teilfehler lehnt ab, cacht nicht, älterer Bestand bleibt ohne Frischeverlängerung; Grenze inklusive; Projektion
  exakt, `null`/`0` erhalten; kopierte Zeilen (Mutation des Ergebnisses ändert den Bestand nicht); geteilte
  laufende Ladung = ein Netzaufruf; Erweiterung während laufender Ladung → eingereihte Vereinigung, Abschluss-
  reihenfolge vertauscht → größerer Bestand bleibt; Abdeckung bei CRWV „ab 1990“ = vollständig, nicht 2025;
  TTL-Ablauf → Neuladen; LRU-Grenze; Pool ≤ 4.
- `scripts/verify_kurse.py`: Bestand „kein `'/rest/v1/prices` außerhalb `kurse.js`“ (Suche nach dem Literal
  `rest/v1/prices` in `landing/`, auch `fetchAllPrices`/`ladeVollHistorie`-Aufrufe zählen nach der Migration als
  Befund); jede Seite mit Kurszugriff bindet `kurse.js` ein.
- **Verbraucherprobe**: je migrierter Seite die zentrale Rechenfunktion mit denselben Fixture-Kursen vor/nach
  (vorhandene Proben `probe_plain_vanilla_*`, Radar-Proben auf `SA.kurse` umgestellt) — gleiche Kennzahlen.
- Mutationstest deterministisch (`_atomar_schreiben`, Anker, benannte Prüfung, Ausnahmen kein Nachweis).

## S3 Statische Kursdateien — nur Schattenmodus, getrennt zu klären
Vor jedem produktiven Einsatz: Koordination aller Schreiber/Exporter (gemeinsame Sperre über Nightly, Intraday,
Onboarding, Backfills) oder ein DB-Snapshot-Vertrag; Frischenachweis je Ticker aus dem **erfolgreichen**
Aktualisierungsstand (nicht aus der Exportzeit) mit Börsenkalender — erst nach der Umschaltung von
`SA.boersenkalender` (Plan „Tage nach Börsenkalender“, P4). Bis dahin nur Schatten: Datei erzeugen, im Browser
nicht verwenden, Abweichungen zur DB messen.

## Fokusfragen
1. Erfüllt v3 die Auflagen vor S1? 2. Ist der Koordinator (ein Bestand, vereinigter Bedarf, eingereiht,
Generationszähler) widerspruchsfrei? 3. Reicht die Verbraucherprobe als Nachweis „keine Zahl ändert sich“?
4. S0: Ist der JS-Austausch per `page.route` gegen die Live-Seite ein fairer Vorher/Nachher-Vergleich?

## Ausgabevertrag
**Urteil** (Freigabe als Bauplan / mit Auflagen / nicht) · **Antworten** · **Befunde** · **Auflagen**. ≤ 60 Zeilen.
