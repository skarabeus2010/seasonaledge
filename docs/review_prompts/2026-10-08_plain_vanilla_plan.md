# Entwurf v2: Umsetzungsplan /plain-vanilla — zur Prüfung VOR dem Code

Repo `C:\dev\Seasonaledge`. Befunde: `docs/review_prompts/2026-10-08_plain_vanilla_runde1_antwort.md` (17). Deine
Einwände zu v1: `docs/review_prompts/2026-10-08_plain_vanilla_plan_antwort1.md` (10). Prüfe diesen **Plan** (noch kein
Produktivcode). Antwort auf Deutsch: je Einwand Schwere + Plan-Punkt + Änderung; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`. Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## 0. Messrahmen (umgesetzt, prüfbar)
- `scripts/research/plain_vanilla_kurse.py` lädt Kurse wie die Seite (öffentliche Abfrage). Ein **eingefrorener
  Kurs-Snapshot** (5 Ticker: ^DJI, ^GSPC, SPY, QQQ, ^GDAXI; Stichtag 2026-10-07; Hash in `snapshot.json`) wird für
  alle Phasen verwendet; neue Daten nur mit neuem Snapshot und eigener Basislinie.
- `scripts/js/probe_plain_vanilla_messlauf.js` lädt die Module **aus der Script-Liste der Seite** (in deren Reihenfolge),
  rechnet alle 22 Strategien × Zeitraum (10 J ab Stichtag, max) × Stop (aus, fixed 8, trailing 8) und schreibt Trades +
  Kennzahlen mit Kurs-Hash, Modul-Hash und Stichtag. Basislinie: `scripts/research/out/plain_vanilla_phase0.json`.
  **Eigener Fehler beim ersten Lauf:** ohne `indicators.js` fiel LBR still auf Sell in May zurück → identische Zahlen.
  Daraus neuer Befund **N1** (unten).
- **Ablauf je Phase** (verbindlich): Basislinie → je fachlicher Korrektur ein Zwischenlauf `phaseX_schrittY.json` +
  Differenz (geänderte Einzeltrades, Befundnummer) → Wächter + Mutationen → Codex-Code-Runden bis Freigabe →
  Differenzbericht an den Nutzer → Commit/Push. Archiv in `scripts/research/out/plain_vanilla_*/`.

## Phase 1 — Rechenkern der Seite (JS + Python-Zwilling `shared/strategies/plain_vanilla.py`)

**1a Terminauflösung (Befund 1, Einwand 2/3).** Neue Funktion `_regeltermin(rows, regel, boerse)` mit vier Zuständen:
`gefunden` (Index), `noch_nicht_faellig` (regelgemäßer Termin liegt nach dem Stichtag), `daten_fehlen` (Termin liegt
in belegter Kalenderzeit, Kurszeile fehlt), `kalender_unbekannt`. Ablauf: erst den regelgemäßen **Handelstermin** aus
dem Börsenkalender bestimmen (`SA.holidays`, Börse aus `SA.holidays.detect(ticker)`), dann die Kursabdeckung prüfen.
- **Belegte Kalenderzeit:** NYSE ab 1971 (gemessen in der Wahlen-Studie, `election_calendar_exceptions.json`), XETRA
  ab dem Jahr, für das `holidays.js` Regeln hat und Kurslücken = Feiertage nachgewiesen sind (Messung vor Einsatz,
  Ergebnis im Plan v3). **Davor** bleibt die heutige Zeilenzählung (Samstagssitzungen bleiben drin), Zustand
  `kalender_unbekannt` wird je Trade mitgeführt und im Messlauf gezählt — kein Trade wird deshalb verworfen.
- `noch_nicht_faellig` am Ausstieg → `open:true`, bewertet zum letzten Kurs, **nicht** in der realisierten Statistik.
  Ein Einstieg auf der letzten Kurszeile ergibt eine offene Position (Rendite 0).
- `daten_fehlen` am Ein- oder Ausstieg → kein Trade, gezählt als `ausgelassen_datenluecke` mit Datum.
- Erfasst werden **alle** Zielsuchen: `_nthTradingDay`, `_lastTradingDay`, `_nthLastTradingDay`, `_nearestBackward/
  Forward`-Aufrufe je Strategie (Liste im Plan v3 vollständig aus `grep`), LBR-Suchschleifen (Einstieg erfolgt, kein
  Ausstieg beobachtet → offen statt verworfen).
**1b LBR (3):** Entscheidung `hist[i-1]`, Ausführung Close `i`; **N1:** fehlt `SA.indicators.calcMACD`, wirft
`calc_lbr_november_mai` einen sichtbaren Fehler statt still Sell in May zu rechnen.
**1c Santa Claus (6):** Einstieg = dritte Handelssitzung **streng vor** Thanksgiving (Registry: „3 HT vor Thanksgiving
→ 5. HT Jan"), JS und Python gleich; Thanksgiving außerhalb der Historie → kein Trade.
**1d Präzision und ungültige Werte (10, Teil 9):** intern ungerundete Preise und Renditen in **allen**
Erzeugungswegen (`_makeTrade`, `applyStopLoss`, `applyTrailingStop`, Sonderstrategien), Rundung nur in der Anzeige;
endliche positive Preise verlangt; Vergleiche mit fehlendem Indikatorwert = `false`; PF ohne Verlusttrades = `null`
(„—"); Gewinn/Verlust-Einstufung auf ungerundeten Werten.
**1e Zwei getrennte Kennzahlenfamilien (7, Einwand 5):** *Realisiert* (nur geschlossene Trades: Anzahl, Trefferquote,
Ø, PF, Sharpe über Trades, Drawdown der abgeschlossenen Trades) und *täglich bewertet* (Equity: 1.000 Startkapital,
voll investiert in genau eine Position, Cash dazwischen 0 % Verzinsung, Hebelfaktor der Strategie auf die
Tagesrendite, Bewertung zum Close, nach Stop Cash; **inklusive** der am Stichtag offenen Position). Chart und täglicher
Max-DD nutzen dieselbe Equity. Vor der Umsetzung misst ein Lauf, ob eine Strategie sich überschneidende Trades erzeugt
(dann: zweite Position verworfen, gezählt). Abnahmefälle: `100→80→110`, offene Verlustposition, vorzeitiger Stop.
**1f Streak (13):** aus denselben konfigurierten geschlossenen Trades wie die Kennzahlen.
**1g Median (12):** gemeinsame Quantilfunktion (numpy „linear") in `seasonal-compute.js`, Fundstellen 229 und 625.

## Phase 2 — Signale und Texte (5, 8, 14, 15, 16, 17)
- Dashboard `3*5` → `3`; Signalansicht und Dashboard nutzen **dieselbe** Terminfunktion aus 1a.
- Alle künftigen Termine heißen „Regeltermin" bzw. „Suchfenster" (LBR, Barometer-Bedingungen), mit Zustand
  `Bedingung offen / erfüllt / nicht erfüllt`; nur historische Trades heißen Ein-/Ausstieg. Farben neutral (Gold-
  Intensität), Beträge neutral. DE+EN gemeinsam abgenommen.
- Signifikanz: „unkorrigierter Einzeltest; Auswahl aus 22 Strategien und frei wählbaren Parametern nicht
  berücksichtigt"; Overfitting-Satz gestrichen.
- Newsletter (`daily_report.py`): Santa/Sell-in-May auf die Seitendefinition oder als eigene Variante benannt; „~75 %"
  nur mit Zeitraum und Quelle.
- TDOM-Header (17): kein DB-Fallback an handelsfreien Tagen.
- Dashboard Constant-Fill (8): Konsument filtert je Tag **und** je Intervall mit `last_actual_day`; unbekannte
  Abdeckung gilt nicht als vollständig.

## Phase 3 — Zwillinge und gemeinsame Bausteine (2, 4, 9, 11)
- EMA/MACD (9): verbindlich Seed, Warm-up, Signal-Start, ungültige Werte; Zwillingstest JS↔Python über alle 22
  Strategien **nur** ohne Stop bzw. im gemeinsamen Close-Modus.
- Stops (2): Seite Close-basiert; beide Python-OHLC-Pfade (`backtest_engine.py`, `plain_vanilla.apply_stop_loss`):
  Gap zuerst, Trailing-Niveau erst ab Folgetag; eigene Gap-/Trailing-Fälle.
- Maskenvertrag (11, 4): `mask[t]` = Zustand nach Schluss von `t`, Ausführung an `i` liest `mask[i-1]`. **Alle**
  Konsumenten von `applyFilter` (Backtest-Engine, Monatswechsel, Mondphasen, Opex, Overnight, TDOM, Vixpiration,
  Zentralbanken, Wochentage — Liste per `grep`) gemeinsam umgestellt. Regime: expandierende Referenzverteilung bis
  `t`, Mindesthistorie, Gleichstand. Test: angehängte Zukunftsdaten ändern frühere Zustände nicht; genau ein Tag
  Verzögerung im Konsumenten.

## Wächter (Einwand 9)
Je Befund mindestens eine fachliche Prüfung + zugehörige Mutation, ausgeführt gegen die **echten** betroffenen
Module/Konsumenten (Seite per node mit DOM-Stub nur, wo nötig; Dashboard-Konsument; `daily_report.py`; Python-OHLC).
Mechanik wie Polymarket: `[Aufbau]`, Endmarker, Mutation benennt ihre Prüfung, Ausnahme ≠ Nachweis, `UNGUELTIG_ERWARTET`.

## Blogartikel (Einwand 10)
Eigene Reproduktion je Artikel mit dessen Regeln/Zeitraum/Datenbasis: `monthly-10-strategie` (SPY 1994–2025, tägliche
Risikokennzahlen), `sell-in-may-2026` (Nov–Apr gegen Mai–Okt). Abweichungen samt Ursache an den Nutzer, keine
eigenmächtige Änderung.

## Prüfe besonders
- Trägt die Kalender-Abdeckungsregel (NYSE ab 1971, davor Zeilenzählung mit Kennzeichnung)?
- Ist 1e (Equity-Definition) widerspruchsfrei, auch für Hebel-Strategien (UHTS 1,5)?
- Fehlt etwas, damit Phase 1 begonnen werden kann?
