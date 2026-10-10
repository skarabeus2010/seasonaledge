# Neue Ticker schneller laden — Plan (kanonisch)

Stand 2026-10-10 · **Status: Plan, nicht umgesetzt** · mit Codex in vier Runden erarbeitet
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
