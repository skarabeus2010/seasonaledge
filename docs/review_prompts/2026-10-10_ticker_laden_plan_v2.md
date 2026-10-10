# Neue Ticker schneller laden — Plan v2 (Runde 2)

Runde 1: [Auftrag](2026-10-10_ticker_laden_plan.md) · [deine Antwort](2026-10-10_ticker_laden_plan_antwort1.md)
(Bestandsaufnahme 41 Seiten, Bewertung O1–O9, Reihenfolge, zehn Befunde). v2 übernimmt deine Reihenfolge und
macht sie umsetzbar. Read-only.

<task>Prüfe Plan v2 auf Lücken, bevor Code entsteht. Besonders: S1 und S2 (zuerst umzusetzen) und die
Schnittstelle des gemeinsamen Laders.</task>

## Leitlinie
Eine Kursreihe wird **einmal** geladen, **einmal** gecacht, von **allen** Verbrauchern geteilt — und ein Teil-
oder Fehlerergebnis wird nie als vollständig ausgegeben. Erst danach kommt die statische Datei (größter Gewinn
bei kalten Aufrufen). Kein Schritt darf eine angezeigte Zahl verändern, außer die drei heute live falschen
Stellen (Befunde 2, 3 und der O1-Fehler), die dabei korrekt werden.

## S0 Messbasis (vor jedem Code)
- `scripts/perf/kurse_messen.py` (Transport, lesend, Anon-Key aus der Seite): Ticker SPY, ^GDAXI, ^DJI, SAP.DE,
  BTC-USD, CRWV (kurz); je Lader-Variante 10 gültige Wiederholungen, abwechselnd; Median/p95, Anfragen, Bytes
  (übertragen/dekodiert), Zeilen, Fehler; ein Fehlerkörper ist kein gültiger Lauf.
- `scripts/perf/seiten_messen.js` (Browser-Probe mit der echten Seite und dem echten Auswahlhandler, Chrome über
  Puppeteer oder Playwright aus `npx` — lokal gegen `python -m http.server` mit Live-Supabase): Auswahl → erstes
  gerendertes Chart, → vollständige Ansicht (Score/Radar), Anfragen, Bytes; Zustände kalt / Rückwechsel A→B→A /
  zweite Seite. Seiten: Dashboard, Dekadenzyklus, Jahreszyklus, Saison-Score, Overnight, Watchlist.
- Ergebnis als Tabelle in `docs/TICKER_LADEN.md` (neu, kanonisch), Vorherwerte festgeschrieben.

## S1 Gemeinsamer Lader `SA.kurse` (ersetzt F, V und die zehn lokalen Lader; O1 + O2 + O8)
- Datei `landing/js/kurse.js`, geladen vor den Seiten-Skripten (alle Seiten, die heute F/V/L nutzen; EN-Build
  übernimmt). Schnittstelle:
  `SA.kurse.laden(ticker, {felder: ['date','close','log_return',…], ab: 'YYYY-MM-DD'|null}) → Promise<Zeilen>`
  mit Vertrag: aufsteigend nach Datum, vollständig für den Bereich oder Ablehnung; Ergebnis ist eine **Sicht**
  auf den geteilten Bestand (eingefroren oder Kopie, damit kein Verbraucher den Cache verändert).
- **Keyset statt Offset**: `order=date.asc&limit=1000&date=gt.<letztes>` (wie `ladeVollHistorie`), kein
  `count=exact`, Ende = Block < 1000 (auch genau 1000/2000 → eine leere Schlussanfrage). HTTP-/Array-Prüfung und
  Wiederholungen bei 429/5xx/Netz wie heute in F. Fehler → Ablehnung, nichts cachen.
- **Ein Bestand je Ticker**: geladen wird immer die Vereinigung der angeforderten Felder und der frühesten
  angeforderten Grenze; spätere Anfragen mit engerem Bereich/weniger Feldern bedienen sich daraus; breitere
  Anfragen laden nur den fehlenden **älteren** Teil nach (`date=lt.<frühestes>`) bzw. die fehlenden Felder neu.
- **Laufende Abrufe teilen**: eine Promise je (Ticker, Feldsatz, Grenze); A→B→A nutzt die laufende A-Ladung.
- **Globaler Pool**: höchstens 4 gleichzeitige Netzanfragen über alle Verbraucher (Watchlist, Sektor-Rotation,
  Intermarket, Radar).
- **Cache**: im Speicher, 15 min, je Ticker (nicht je Filter); `SA.cache`/localStorage wird für Kurse **nicht
  mehr** benutzt (Befund 7). Abrufkennung `SA.ladeKennung` bleibt die Regel gegen verspätete Antworten.
- **Migration**: jede Zeile der Bestandsaufnahme (16 F-Seiten, 10 L-Seiten, Watchlist V, Radar R, Saison-Score
  `mitHistorie`) wird auf `SA.kurse.laden` umgestellt, mit denselben Feldern und Grenzen wie heute. Danach gibt
  es keinen `fetch('/rest/v1/prices` mehr außerhalb von `kurse.js` (Wächter prüft das).
- Dabei behoben (sichtbar): Dashboard-Overnight ohne Pagination (Befund 3) und die zehn lokalen Lader ohne
  Fehlerprüfung (Befund 2).

## S2 localStorage-Cache entschärfen (O5-Vorstufe)
- `SA.cache.set` löscht nicht mehr **alle** Einträge bei einem Quota-Fehler, sondern verdrängt die ältesten bis
  zu einem Budget (z. B. 2 MB) und gibt bei Misserfolg `false` zurück, ohne andere Einträge zu löschen.
  (Mit S1 ist er für Kurse ohnehin nicht mehr im Spiel; andere Nutzer behalten ihn.)

## S3 Statische Kursdateien (O4) — Pilot
- **Erzeuger** `scripts/build_kursdateien.py`, liest die **gespeicherten DB-Zeilen** (Keyset), schreibt je
  Ticker `landing/data/kurse/<sicherer Name>.json` spaltenweise
  `{schema, ticker, revision, erste, letzte, zeilen, stand_utc, felder: {date:[…], open:[…], close:[…],
  log_return:[…], tdom:[…], tdoy:[…]}}` per `write_json_atomic`; `revision` = sha256 über den Inhalt; Pfad
  gitignored; HTTP-Abnahme 200/304 + gzip.
- **Wann**: am Ende des Nightly (nach Phase D, also nach Rendite-Reparaturen) und am Ende jedes Intraday-Laufs
  nur für die aktualisierten Ticker; außerdem nach Onboarding/Backfills (Aufrufer). Konsistenz: der Exporter
  läuft im selben Prozess **nach** den Schreibern dieses Laufs; Nightly und Intraday überlappen nicht
  (systemd-Timer zu verschiedenen Zeiten — prüfen).
- **nginx**: eigene `location ^~ /landing/data/kurse/` mit `Cache-Control: no-cache`, ETag, gzip — vor der
  Regex-Regel mit `max-age=86400` wirksam (Befund 9; `^~` gewinnt gegen Regex).
- **Leser**: `SA.kurse.laden` versucht zuerst die Datei; Frische-Regel je Börse (letzte erwartete Sitzung nach
  Börsenkalender aus `SA.boersenkalender`? — nein, der ist noch isoliert → vorerst: `stand_utc` jünger als
  26 h an Börsentagen, sonst DB-Lader); fehlt/kaputt/zu alt → einmal DB-Lader; dessen Fehler → Ladefehler.
- **Pilot**: nur die sechs Messticker, „Schatten“-Modus (Datei laden + mit DB vergleichen, Abweichungen in die
  Konsole/Probe), danach erst produktiv. Rollout 370 nach Messung (Größe, Erzeugungszeit, gzip).

## S4 Wahrnehmung (O6/O9), S5 O3/O7 nur bei Bedarf
- Erstes Chart vor teuren Folgeauswertungen; Watchlist-Karten einzeln veröffentlichen; kein `concat` in
  Schleifen. Vorläufige Teilanzeigen nur ausdrücklich gekennzeichnet; Saison-Score nie auf Teilhistorie.

## Prüfung je Schritt
- S1: `scripts/js/probe_kurse.js` + `scripts/verify_kurse.py` mit gestubbtem `fetch` (PostgREST-Verhalten:
  `Content-Range …/*`, 1000er-Grenze, Fehler im n-ten Block, 429 mit Retry-After) — Sollmengen 0/999/1000/1001/
  2000/33 739, Teilfehler lehnt ab und cacht nicht, geteilte laufende Promise (ein Netzaufruf), Pool-Grenze,
  Sicht unveränderlich, Bereichserweiterung lädt nur das Fehlende; Bestandswächter „kein `/rest/v1/prices`
  außerhalb `kurse.js`“. Mutationstest.
- S3: Datei == DB für jede Zeile/jedes Feld der Pilotticker; Revision ändert sich bei gleicher letzter Zeile und
  geändertem Close; fehlende/alte/kaputte Datei → DB.

## Fokusfragen
1. Reicht S1 so als Vertrag, oder fehlt etwas, damit die Migration der 27 Ladestellen keine Zahl verändert?
2. „Breitere Anfrage lädt nur den älteren Teil nach“ — korrekt, oder lieber immer ganz neu laden (einfacher)?
3. Ist die Browser-Probe mit Puppeteer/Playwright aus `npx` lokal + im Deploy realistisch, oder nur lokal?
4. S3-Frische ohne den (noch isolierten) Börsenkalender — genügt die 26-h-Regel als Übergang?
5. Was fehlt sonst?

## Ausgabevertrag
**Urteil** · **Antworten** (je ≤ 8 Zeilen) · **Befunde** · **Auflagen vor S1**. ≤ 90 Zeilen.
