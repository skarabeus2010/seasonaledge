# Neue Ticker schneller laden — Plan (kanonisch)

Stand 2026-10-11 · **Status: S1-Lader + Migration Schritte 1–3 umgesetzt (alle Kurslader der Seiten über `SA.kurse`); S2/S3 offen** · Plan mit Codex in vier Runden erarbeitet
([Auftrag](review_prompts/2026-10-10_ticker_laden_plan.md) · [v2](review_prompts/2026-10-10_ticker_laden_plan_v2.md) ·
[v3](review_prompts/2026-10-10_ticker_laden_plan_v3.md) · [v4](review_prompts/2026-10-10_ticker_laden_plan_v4.md);
Antworten [1](review_prompts/2026-10-10_ticker_laden_plan_antwort1.md) · [2](review_prompts/2026-10-10_ticker_laden_plan_antwort2.md) ·
[3](review_prompts/2026-10-10_ticker_laden_plan_antwort3.md) · [4](review_prompts/2026-10-10_ticker_laden_plan_antwort4.md)).
Codex Runde 4: **Freigabe als Bauplan mit Auflagen** — die Auflagen sind unten eingearbeitet.

## Warum es langsam ist (gemessen, lokal → Supabase, nur lesend)

| Ticker | Zeilen | Anfragen | sequenziell mit `count=exact` | ohne count |
|---|---|---|---|---|
| SPY | 8 482 | 9 | 1,6 s | 2,6 s |
| ^GDAXI | 16 871 | 17 | 4,8 s | 3,1 s |
| ^DJI | 33 739 | 34 | 6,6 s | 4,1 s |

Die Werte schwanken stark; das Muster nicht:
1. **`SA.fetchAllPrices` zählt bei jedem Block** (`Prefer: count=exact`) und blättert per Offset **nacheinander**.
2. **Zwei Lader für dieselbe Historie**: `SA.fetchAllPrices` und `SA.decadeCompute.ladeVollHistorie`;
   Saison-Score und Anomalie-Radar laden die Historie auf manchen Seiten ein zweites Mal.
3. **Zehn Seiten haben eigene Lader ohne Fehlerprüfung** — ein Fehlerkörper kann als leere Reihe durchgehen.
4. **Dashboard-Overnight paginiert nicht** und `embed.html` hat einen eigenen Lader (1000 statt 1500 Zeilen).
5. **localStorage-Cache leert bei einem Quota-Fehler alles** — ^DJI allein wären ~2,8 MB.

## Schritte

### S0 Messbasis (vor jedem Code)
- **Transport** `scripts/perf/kurse_messen.py`: SPY, ^GDAXI, ^DJI, SAP.DE, BTC-USD, CRWV; je Variante 10 gültige
  Läufe abwechselnd, Median/p95, Anfragen, Bytes, Zeilen; ein Fehlerkörper ist kein gültiger Lauf.
- **Browser** (Playwright, feste Version unter `scripts/perf/`): vorher und nachher **identisch** — je Variante
  ein lokaler nginx mit `deploy/nginx.conf`, `landing/` aus dem jeweiligen Git-Stand (vollständiges HTML inkl.
  Inline-Code), beide gegen dieselbe Supabase, **kein** Netzabfang. Zustände kalt / Rückwechsel A→B→A / zweite
  Seite, Profile Desktop und „Slow 4G“. Messpunkte: Auswahl → erstes Chart → vollständige Ansicht.
- **Inhaltsgleichheit je Messzelle** wird **pro fachlich benötigter Sicht** kanonisch verglichen, nicht über alle
  übertragenen Zeilen (der neue Lader lädt absichtlich weniger doppelt); Zeilen, Bytes und Anfragen sind eigene
  Messgrößen.
- Ziel vorab: p95 „erstes Chart, kalt“ für ^DJI auf Dashboard/Dekadenzyklus −50 %; keine Seite langsamer (Median).
  Messbericht, kein Deploy-Gate.

### S1 Ein gemeinsamer Lader `SA.kurse` (`landing/js/kurse.js`)
**Aufruf** `SA.kurse.laden(ticker, {felder, ab})` → `{zeilen, generation, abdeckungAb, geladenUm}`.
- `zeilen`: kopierte Zeilen mit `date >= ab`, aufsteigend, genau die angeforderten Felder, Werte unverändert
  (`null` bleibt `null`, `0` bleibt `0`); fehlt ein Feld → Ablehnung, nie stilles `undefined`.
- **Vollständig oder Ablehnung**: Keyset (`order=date.asc&limit=1000&date=gt.<letztes>`), kein `count=exact`,
  Ende = Block < 1000; je Block HTTP-/Array-Prüfung, gültige ISO-Daten, **streng aufsteigend und erstes Datum >
  Cursor**; Retry bei 429/5xx/Netz mit `Retry-After`; Timeout 20 s je Block; höchstens 61 Blöcke je Ladung.
  Ein gescheiterter Block lehnt die ganze Ladung ab — nichts wird veröffentlicht oder gecacht.
- **Koordinator je Ticker**: ein Bestand (Felder, `abdeckungAb` = angeforderte Grenze), 15 min frisch.
  Deckt Bestand oder laufende Ladung die Anfrage → daraus bedienen. Sonst eine Ladung des **vereinigten** Bedarfs
  (Felder ∪, früheste Grenze), höchstens eine wartende; ersetzt den Bestand erst nach Erfolg. Fehler → wartende
  Anfragen lehnen ab, alter Bestand bleibt, ohne seine Frische zu verlängern.
- **Generation**: global monoton, nie wiederverwendet. Verbraucher-Ergebniscaches nutzen
  `ticker|generation|Parameter` als Schlüssel.
- **Speicher** 12 Ticker LRU (nur ruhende Koordinatoren werden verdrängt); **Pool** 4 Netzanfragen gleichzeitig.
- **Migration** aller 27 Ladestellen + `embed.html` mit denselben Feldern und Grenzen; jeder Abschluss prüft
  `SA.ladeKennung.aktuell` vor dem Zeichnen; Score und Radar behalten ihre Historienregeln;
  `fetchAllPrices`/`ladeVollHistorie` werden Hüllen und dann entfernt; alte `sa-cache-prices*` einmal löschen.
- **Dabei korrigiert** (die einzigen beabsichtigten Zahlenänderungen): Overnight-Pagination, Fehlerprüfung der
  zehn lokalen Lader, O1-Kürzung.

### S2 localStorage-Cache entschärfen
Übergroße Einträge (> 512 KB) vorab ablehnen; bei Quota-Fehler nur eigene `sa-cache-*`-Einträge in LRU-Reihenfolge
verdrängen; andere Fehler → `false` ohne Verdrängung. Kurse nutzen ihn nach S1 nicht mehr.

### S3 Statische Kursdateien — nur Schattenmodus
Größter Gewinn bei kalten Aufrufen, aber erst nach (a) Koordination aller Schreiber (Sperre oder DB-Snapshot),
(b) Frischenachweis aus dem erfolgreichen Aktualisierungsstand mit Börsenkalender — also nach der Umschaltung
`SA.boersenkalender` (Vorhaben „Tage nach Börsenkalender“, P4). Bis dahin nur erzeugen und gegen die DB messen.

## Abnahme
- `scripts/js/probe_kurse.js` (node, echter `kurse.js`, PostgREST-Stub): Sollmengen 0/999/1000/1001/2000/33 739,
  Teilfehler, Retry-After, Timeout, Grenze inklusive, Projektion, Kopie, geteilte Ladung = ein Netzaufruf,
  vereinigte Nachladung, Fehler mit wartender Anfrage, TTL während laufender Ladung, CRWV „ab 1990“ vollständig,
  LRU, Pool ≤ 4, Cursor ohne Fortschritt → Ablehnung.
- `scripts/js/probe_seiten_kurse.js`: je migrierter Seite die **echte HTML-Seite** mit ihren Skripten, deterministisch
  bedient (Komponenten, Wörterbücher, Metadaten, Nebenabfragen, Auth, Credential-Werte), **feste Uhr, Zeitzone,
  leerer Ausgangsspeicher, benannter Baseline-Commit**; jeder Fall braucht einen nachgewiesenen Auswahl-/Ladepfad
  und einen Abschluss mit Frist — zwei leere Ergebnisse beweisen nichts. Gleich bleiben müssen die
  **Anforderungen und Rückgabesichten je Verbraucher** sowie Chart-Serien und sichtbare Kennzahlen; die
  gebündelten Netzabfragen werden gesondert gegen den Keyset-/Vereinigungsvertrag geprüft. Seiten, die jsdom
  nicht trägt, laufen mit denselben Prüfungen in Playwright. EN-Einbindung für tatsächlich erzeugte EN-Seiten.
- `scripts/verify_kurse.py`: kein `rest/v1/prices` außerhalb `kurse.js` in ganz `landing/`; jede Seite mit
  Kurszugriff bindet `kurse.js` ein. Mutationstest deterministisch (`_atomar_schreiben`, Ausnahme ≠ Nachweis).

## Offene Nutzerentscheidung
Freigabe zur Umsetzung von S0–S2 (S3 bleibt Schatten). Reihenfolge: S0 → S1 → S2, je Schritt Codex-Code-Runden.

## Umsetzung

### Messbasis S0 — Transport (2026-10-10, `scripts/perf/kurse_messen.py`, 10 gültige Läufe je Variante)

| Ticker | Zeilen | heute F (Offset + count) Median / p95 | Keyset Median / p95 |
|---|---|---|---|
| SPY | 8 482 | 0,80 / 1,98 s | 0,73 / 0,81 s |
| ^GDAXI | 16 871 | 1,62 / 1,82 s | 1,39 / 1,44 s |
| ^DJI | 33 739 | 3,65 / 5,91 s | 2,77 / 2,86 s |
| BTC-USD | 4 407 | 0,44 / 0,46 s | 0,43 / 0,45 s |

Der Transport allein bringt wenig — der Gewinn kommt aus dem Wegfall der Doppelladungen (und später S3).

### S1 Lader (`05e6310`) und Migration Schritt 1 (`a19f3f0`)
- `landing/js/kurse.js` wie oben; Codex S1-Code in 4 Runden bis Freigabe. Zusätzlich zur Planung: **eine Anfrage
  scheitert nur an ihrem eigenen Bedarf** (Codex M1 R1) — hängt sie an einer breiteren gemeinsamen Ladung und
  scheitert diese, wird genau ihr Bedarf einmal allein geladen (nicht gecacht). Ohne das rechnete das Radar still
  auf 29 statt 30 Vergleichsjahren, wenn die Vollhistorie des Saison-Scores scheiterte.
- Schritt 1: `SA.fetchAllPrices` und `ladeVollHistorie` sind Hüllen; `kurse.js` in allen 44 DE-Seiten.
- Wächter im Deploy-Gate: `verify_kurse.py` (Lader + Hüllen alt/neu wörtlich), `verify_seiten_kurse.py` (echte
  `dashboard.html` in jsdom 25.0.1, vorher = Fixtures `scripts/fixtures/kurse_vorher/`, Fälle normal / gescheiterte
  Vollhistorie / TTL). Mutationstest `verify_kurse_mutation.py` 37/37.
- **Live (2026-10-11, ^DJI, ausgelieferte Seite gegen die echte Datenbank):** Ansicht nach 4,0 s, Saison-Score und
  Radar nach 9 s; 43 Kursanfragen (8 für 30 Jahre, 34 Vollhistorie gemeinsam für Score und Radar, 1 Overnight),
  keine mit `count=exact`. Nach altem Code wären es 51 gewesen (Radar lud seine 31 Jahre zusätzlich).
- Lesson: eine Live-Probe in jsdom mit node-`fetch` darf jsdoms `AbortSignal` nicht durchreichen — node lehnt es
  ab, der Lader wiederholt, und es sieht aus wie ein Hänger der Seite.

### Schritt 2 (`4b8b6c6`) — lokale Lader, Dashboard-Overnight, Embed
- Zehn Seiten mit eigenem Lader (Offset + `count=exact`, ohne HTTP-/Array-Prüfung — ein Fehlerkörper wurde als
  „Zeile" angehängt und mitgerechnet) und `embed.html` laufen über `SA.kurse`; ein Ladefehler erscheint als Fehler.
- Dashboard-Overnight lud ohne Pagination nur die ersten 1000 Zeilen des Zeitraums — jetzt vollständig. Soll in
  der Seitenprobe: der **alte Code auf vollständigen Daten** (Nachbau ohne die 1000er-Grenze).
- **VORLADEN**: jede gemeinsame Ladung holt mindestens `date, open, close, log_return, tdom, tdoy` — sonst löste ein
  weiteres Feld (Overnight: `open`) eine zweite Vollladung aus (gemessen 44 statt 27 Anfragen). Dashboard: 36 → 26.
- Rückfall auf den eigenen Bedarf, sobald die gescheiterte gemeinsame Ladung **mehr** verlangte — längerer
  Zeitraum ODER zusätzliche Spalten (Codex M2 R1: ein Fehler kann an einer Spalte hängen). Bei genau dem eigenen
  Bedarf kein zweiter Versuch.

### Schritt 3 (`35e1df4`) — Abrufkennung
- Wochentage, Backtest-Engine, OPEX, VIXpiration, Spot-Vol-Beta ohne Abrufkennung: ein schneller zweiter Ticker
  wurde von der verspäteten Antwort des ersten überschrieben (Seitenprobe: im alten Stand auf allen fünf).
- Wochentage/Backtest-Engine kehrten beim angezeigten Ticker VOR der Kennung zurück → A → B → A blieb ungeschützt;
  jetzt `SA.ladeKennung.start(ticker, angezeigt)`.
- Dashboard-Overnight: Abrufkennung UND Darstellungszähler — nach TTL-Ablauf überschrieb ein später 30-J-Fehler die
  5-J-Ansicht (Codex M3 R1).
- Seitenprobe 313/313 mit `wechsel`, `rueckwechsel`, `zeitraum`; jeder verglichene Lauf muss Ruhe, keine
  Seitenfehler, vollständige Anzeige und gefüllte Charts haben.

### Lessons
- **Ein Test, der ein Feld wechselt, prüft nach VORLADEN etwas anderes** — fünf Probefälle verloren ihre Aussage,
  sichtbar erst im Mutationstest (Felder `open`/`tdom` jetzt immer geladen → auf `high` umgestellt).
- **„Fertig" heißt: nichts offen UND kein Lader aktiv** — zwischen Wiederholungen ist keine Anfrage offen; die
  Seitenprobe meldete dort zweimal zu früh Ruhe (Wiederholungspause, dann Rückfall-Ladung).
- **Ein Wettlauf kann durch eine andere Änderung verschwinden** — nach VORLADEN wird Overnight aus der
  30-J-Ladung bedient, der von Codex nachgestellte Overnight-Wettlauf war auf diesem Weg nicht mehr erreichbar;
  erreichbar blieb er über den Zeitraum-Regler nach TTL-Ablauf.

### Offen
- **S2** localStorage-Cache entschärfen (`SA.cache` hat nach S1 keinen Kursnutzer mehr) · **S3** statische
  Kursdateien (Schatten, erst nach der Umschaltung auf `SA.boersenkalender`).
- Alte Hüllen `SA.fetchAllPrices`/`ladeVollHistorie` entfernen, sobald kein Aufrufer bleibt; dann
  `verify_kurse.py --streng` ins Gate.
