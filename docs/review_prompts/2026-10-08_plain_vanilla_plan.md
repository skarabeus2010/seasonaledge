# Entwurf v5: Umsetzungsplan /plain-vanilla — zur Prüfung VOR dem Code

Repo `C:\dev\Seasonaledge`. Befunde: `docs/review_prompts/2026-10-08_plain_vanilla_runde1_antwort.md` (17). Einwände:
`..._plan_antwort1.md` (10 zu v1), `..._plan_antwort2.md` (7 zu v2), `..._plan_antwort3.md` (6 zu v3), `..._plan_antwort4.md` (3 zu v4). Prüfe diesen **Plan**. Antwort auf Deutsch: je
Einwand Schwere + Plan-Punkt + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein` — Freigabe
bezieht sich hier **nur auf Phase 1A** (Code darf beginnen); 1B und später werden eigens vorgelegt.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## v5 — Festlegungen zu den Einwänden aus Runde 4

**E7 Reihenfolge Datenende/Stops (Einwand 1).** Verbindlicher Ablauf je Strategie: (1) Trade-Kandidaten bis zum
letzten vorhandenen Kurs erzeugen (offene Kandidaten zum letzten Kurs bewertet), (2) Stops anwenden — ein dabei
geschlossener Trade bleibt realisiert, (3) erst danach verbleibende offene Kandidaten bei `datenbestand_veraltet` aus
der aktiven Darstellung (Signal, offene Position) herausnehmen und als unvollständig protokollieren; keine fingierte
Schließung. Wächterfälle: Einstieg 100 → Close 80, regulärer Exit offen, mit Fixed-Stop 8 % (→ geschlossen −20 %) und
ohne Stop (→ offen bzw. ausgeschlossen); Abstand letzte Kurszeile zum Stichtag genau 10 und 11 Sitzungen.
**E8 Zustände im Messformat (Einwand 2).** Schon in 1A trägt jeder Kandidat `zustand_einstieg`/`zustand_ausstieg` ∈
{`gefunden`, `noch_nicht_faellig`, `kurs_ausstehend`, `datenbestand_veraltet`} plus Regeltermin, Bewertungsstichtag und
letztes Kursdatum; der Messlauf gibt sie aus. **Einstieg ohne vorhandenen Ausführungskurs** (noch nicht fällig oder Kurs
ausstehend) → **kein Trade**, protokollierter Grund. Nur ein erfolgter Einstieg erzeugt eine offene Position.
Das umfassende historische Lückenmodell bleibt 1B.
**E9 Streak über den echten Konsumentenpfad (Einwand 3).** Die Aufbereitung „Strategie rechnen → Zeitraum filtern →
Stop anwenden → Kennzahlen + Streak" wird eine Funktion `SA.strategy.auswerten(rows, key, {zeitraum, stop})` →
`{trades, stats, streak}`; Kennzahlenansicht **und** Signalansicht der Seite rufen nur noch sie auf (der eigene Cache
der Signalansicht entfällt). Wächter: Zeitraum- und Stopwechsel verändern Kennzahlen **und** Streak erwartbar
(Fall +10 % geschlossen / −20 % offen aus Runde 1); Mutation „Signalansicht übergibt ungefilterte Trades" scheitert dort.
**Zu E1 ergänzt:** `holidays.js` kennt **keine** NYSE-Sonderschließung (Python `shared/nyse_holidays._NYSE_SPECIAL_CLOSURES`:
9/11 2001 ×4, 2004-06-11, 2007-01-02, 2012-10-29/30, 2018-12-05, 2025-01-09). Teil von N2: Liste nach JS übernehmen;
der Kalendervergleich 2000–2035 prüft sie mit. **XETRA (Codex R5):** JS führt 24.12./31.12. in allen Jahren als handelsfrei, Python erst ab 2011 — Jahresgrenze in die N2-Korrekturen und gezielte Wächterfälle (2010/2011).

**Stand: Plan v5 von Codex für Phase 1A FREIGEGEBEN (Runde 5).**

## v4 — Festlegungen zu den Einwänden aus Runde 3 (gehen den Punkten unten vor)

**E1 Kalender (Einwand 1).** Nachgeprüft: `holidays.js` setzt den 31.12. als NYSE-Feiertag, wenn der 1.1. des
Folgejahres ein Samstag ist (falsch — NYSE schließt dann nicht; `shared/exchange_holidays` hat recht: 2021-12-31 war
Handelstag), und setzt Juneteenth für alle Jahre (gilt erst ab 2022). Das ist ein eigener, seitenweiter Befund **N2**
(betrifft TDOM/TDOY im Frontend, z. B. Dezember 2021). 1A korrigiert `holidays.js` (NYSE: 31.12.-Regel, Juneteenth ab
2022, MLK ab 1998 nach Prüfung) und legt einen **Kalendervertrag für 2000–2035** fest: NYSE- und XETRA-Sitzungsmenge
JS = Python, als Wächterprüfung über jeden Tag des Bereichs. Neue Kalenderentscheidungen (Punkt 5) nur innerhalb
dieses Bereichs; außerhalb bleibt das bisherige Verhalten.
**Bewertungsstichtag ≠ letzte Kurszeile.** Seite: heutiges Datum in der Zeitzone der Börse; Messlauf: Stichtag des
Snapshots. Regeltermin > Stichtag → `noch_nicht_faellig`. Regeltermin ≤ Stichtag, aber nach der letzten Kurszeile →
`kurs_ausstehend` (wie offen behandelt, eigens gekennzeichnet, nicht in der Statistik). Liegt die letzte Kurszeile mehr
als 10 Handelssitzungen vor dem Stichtag, gilt der Datenbestand als **beendet**: keine offenen Trades, kein Signal.

**E2 Ein- und Ausstiegszustände + Inventar (Einwand 2).** Einstieg `noch_nicht_faellig` → kein Trade. Einstieg
erfolgt (≤ Stichtag, Kurszeile vorhanden), Ausstieg ausstehend → offener Trade; Einstieg auf der letzten Kurszeile →
offener Trade mit 0 % (`_makeTrade` und Python `_make_trade` erlauben `entry == exit` nur für `open:true`).
Inventar (aus `grep`, fachlich zugeordnet):
- *Über die Hilfsfunktionen, am Datenrand durch E1/E2 korrigiert:* sell_in_may, nasdaq_trend, month_end, santa (Exit),
  first/last_five_days, january_barometer, post_christmas, second_trading_day, election_7months (Exit), uecs (t2–t6),
  downmonth_tom (Einstieg).
- *Feste Kalenderdaten über `_nearestForward/_nearestBackward`, am Datenrand korrigiert* (stateful Variante: Ziel nach
  der letzten Zeile → Zustand statt letzter Zeile): september_avoid, mid_decade, cycle_20_year, cycle_212/40_week,
  midterm_election, uecs (Wahl-Anker), one_day_holiday, uhts, lbr (Fensterstarts), election_7months (Einstieg).
- *Direkte Sitzungs-Offsets:* downmonth_tom `entryIdx + HOLD` (am Rand: Ziel hinter letzter Zeile → offen, wie
  heute; über historische Lücken → 1B), santa `thxIdx − k` (durch E-Punkt 3 ersetzt), monthly_10 `days.length` (im
  **laufenden** Monat aus dem Kalender E1 bestimmt; historisch unverändert → 1B).
**E3 Hebel (Einwand 3).** Bestehende Unterschiede bleiben bis 1B: JS-UHTS = Gesamtrendite × 1,5, Python-UHTS mit
aufgeteilter Rendite. Die Zwillingsgleichheit in 1A **schließt uhts aus** (ausdrücklich). In JS gilt für gestoppte
Trades dieselbe Renditeregel wie für regulär geschlossene (Hebel bleibt erhalten).
**E4 Close-Modus und Zwillingsgrenze (Einwand 4).** Gemeinsamer Close-Modus der Seite: Auslösung am Close, Trailing-
Peak aus Closes, Ausführung am Close. Python `apply_stop_loss` (OHLC) bleibt in 1A unverändert und wird nicht verglichen;
Zwillingsgleichheit in 1A nur **ohne Stop**. LBR-Vortagsregel wird mit identisch vorgegebenen Histogrammvektoren in
beiden Sprachen geprüft; die EMA-/MACD-Unterschiede bleiben ausgewiesen (Phase 3), volle LBR-Tradegleichheit wird erst
danach verlangt.
**E5 Stop am regulären Ausstiegstag (Einwand 5).** Stopprüfung einschließlich Exit-Close; löst er aus → `stopped:true`,
genau ein geschlossener Trade, Preis und Rendite identisch zum regulären Close-Exit. Abnahme für Fixed und Trailing
sowie für einen ursprünglich offenen, tatsächlich gestoppten Trade.
**E6 Seitenlogik im Wächter (Einwand 6).** Die betroffene Inline-Logik wandert in `strategy-compute.js`, beide Seiten
rufen sie auf: `SA.strategy.regeltermine(Y)` (Dashboard-Terminliste, ersetzt die `3*5`-Stelle),
`SA.strategy.streak(trades)`, `SA.strategy.formatPF(pf)`. Der Wächter testet diese Funktionen und prüft statisch, dass
`dashboard.html` und `plain-vanilla.html` sie verwenden (keine Kopie mehr); Mutationen: `3*5` zurück, Streak aus
ungefilterten Trades, `.toFixed()` auf `null`-PF. DE/EN-Texte (Drawdown-Bezeichnung, „—") über `de.json`/`en.json`
und `verify_en`. Python: offene Trades fehlen in `compute_strategy_stats` und der Abschluss-Equity (eigene Prüfung).

## Neuer Zuschnitt (Antwort auf v2-Einwände 1–3)
v2 versuchte Kalender, Lücken, Hebel und Equity gleichzeitig mit den klaren Fehlern zu lösen. Die vier Grundsatzfragen
(Kalendervertrag, Lücken innerhalb einer Haltedauer, Hebelmodell, tägliche Equity) brauchen Messungen und teils eine
**Nutzerentscheidung** (Hebelmodell). Deshalb:
- **Phase 1A:** Fehler, deren richtige Lösung ohne neues Modell feststeht. Kein Verhalten für historische Daten außer
  den benannten Korrekturen; insbesondere bleibt die heutige Zeilenzählung für die Vergangenheit unverändert.
- **Phase 1B:** Kalendervertrag JS=Python (NYSE inkl. `election_calendar_exceptions.json`, XETRA nach Messung),
  Lückenbehandlung über die ganze Haltedauer inkl. direkter Index-Offsets (`entryIdx + HOLD`), tägliche Equity,
  Hebelmodell, Überschneidungen, Zuordnung `final_equity`/`total_return`/CAGR. Wird nach 1A eigens vorgelegt.

## 0. Messrahmen (umgesetzt — v2-Einwand 6)
- `scripts/research/plain_vanilla_kurse.py` schreibt `snapshot.json` (Stichtag, Hash, Quelle, Verfahren: sha256 über
  Dateiname+NUL+Inhalt, Sortierung nach Dateiname in Zeichencode-Reihenfolge), verweigert das Überschreiben eines
  vorhandenen Snapshots, `--pruefen` rechnet den Hash nach. Der Messlauf rechnet denselben Hash in JS und **bricht bei
  Abweichung ab** (geprüft mit einer untergeschobenen Datei). Eigener Fehler dabei: `WindowsPath` sortiert ohne
  Groß/klein, JS nach Zeichencode → verschiedene Hashes auf gleichen Daten; beide jetzt nach Dateiname-Codepunkt.
- Trade-Tupel enthalten jetzt Ein-/Ausstiegspreis, Rendite, offen, gestoppt, Hebel; Strategiefehler machen den Lauf
  `gueltig:false` mit Exit 1. Kalender-/Lückenstatus kommt mit 1B (gibt es in 1A nicht).
- Snapshot: 5 Ticker, Stichtag 2026-10-07, Hash `a563a159fc2da067`; Basislinie `plain_vanilla_phase0.json` (22
  Strategien × {10 J, max} × {aus, fixed 8, trailing 8}). Kursdaten außerhalb des Repos (Datenbestand); Messskripte im Repo.
- Ablauf je Korrektur: Zwischenlauf `phase1a_<schritt>.json`, Differenz geänderter Einzeltrades je Strategie mit
  Befundnummer, archiviert unter `scripts/research/out/plain_vanilla_1a/` (gitignoriert, reproduzierbar).

## Phase 1A — klare Korrekturen (JS `strategy-compute.js` + Python `shared/strategies/plain_vanilla.py` gleich)
1. **N1 stiller Rückfall:** fehlt `SA.indicators.calcMACD`, wirft `calc_lbr_november_mai` einen Fehler (sichtbar als
   Strategiefehler), statt Sell in May zu rechnen.
2. **LBR (3):** Einstieg am ersten Tag `i` im Fenster mit `hist[i-1] > 0` (bzw. `< 0` für den Ausstieg), Ausführung zum
   Close von `i`; `hist[i-1]` muss gültig (endlich) sein. Ist der Einstieg erfolgt und das Ausstiegsfenster noch nicht
   abgeschlossen → offener Trade statt verworfen; ist das Fenster abgeschlossen ohne Signal → wie heute (kein Trade),
   im Messlauf gezählt.
3. **Santa Claus (6):** dritte Handelssitzung **streng vor** dem Thanksgiving-Datum (Registry „3 HT vor Thanksgiving →
   5. HT Jan"); liegt Thanksgiving vor der ersten Zeile → kein Trade.
4. **Dashboard (5, Teil):** `_nthTradingDay(Y,5,3*5)` → `3`.
5. **Noch nicht fällige Termine (1, nur Gegenwart):** ein Regeltermin, der **nach der letzten Kurszeile** liegt, ist
   `noch_nicht_faellig` → offener Trade (Mark-to-Market zum letzten Kurs, nicht in der realisierten Statistik).
   Entscheidung „liegt nach der letzten Zeile" mit dem **heutigen** Kalender aus `SA.holidays` (bzw.
   `shared/exchange_holidays` in Python) — nur für Termine ab der letzten Zeile, also dort, wo der moderne Kalender
   gilt: der letzte Handelstag eines Monats gilt als erreicht, wenn die nächste Handelssitzung nach der letzten Zeile
   im Folgemonat liegt (Monat endet Sonntag → Freitag ist abgeschlossen). Die Funktionen `_nthTradingDay`,
   `_lastTradingDay`, `_nthLastTradingDay`, `_nearestBackward/Forward` liefern dafür einen Zustand statt still die
   letzte Zeile; Inventar aller Aufrufer und direkten Offsets per `grep` im Code-Review-Prompt beigelegt. Historische
   Lücken: unverändert (1B).
6. **Stops zum beobachteten Close (v2-Einwand 4):** Fixed- und Trailing-Stop steigen zum Close des auslösenden Tages
   aus, nicht zum Stopniveau (die Seite rechnet Close-basiert; Hinweis auf der Seite). Das neue Tradeobjekt behält alle
   Metadaten (Hebel, Strategie-Felder) und ist nach dem Stop **geschlossen**, auch wenn der Ursprungstrade offen war.
   **Hebel in 1A unverändert:** Rendite = Kursrendite × Hebel wie heute (UHTS 1,5), ausdrücklich als vorläufig
   gekennzeichnet; das Modell entscheidet 1B.
7. **Präzision und ungültige Werte (10):** ungerundete Preise/Renditen in **allen** Erzeugungswegen (`_makeTrade`,
   beide Stops, Sonderstrategien), Rundung nur in Anzeige; endliche positive Preise verlangt, sonst kein Trade
   (gezählt); Indikatorbedingungen prüfen **zuerst** die Gültigkeit beider Operanden — ungültig ergibt `false` für
   **jeden** Operator inkl. `!=` und Negation; PF ohne Verlusttrades = `null` (Anzeige „—"), `0/0` ebenso.
8. **Streak (13):** aus denselben konfigurierten, geschlossenen Trades wie die Kennzahlen (inkl. Zeitraum und Stop).
9. **Median (12):** eine Quantilfunktion (numpy „linear") in `seasonal-compute.js`, Zeilen 229 und 625.
10. **Drawdown-Bezeichnung (7, vorläufig):** Feld heißt „Drawdown der abgeschlossenen Trades" (DE/EN), Erklärtext
    entsprechend; der täglich bewertete Max-DD kommt mit 1B.

## Wächter Phase 1A
`scripts/js/probe_plain_vanilla_1a.js` führt die echten Module aus (wie der Messlauf aus der Script-Liste der Seite) +
`seasonal-compute.js`; Python-Gegenprobe `scripts/verify_plain_vanilla_1a.py` ruft `plain_vanilla.py` mit denselben
Eingabefällen. Je Punkt mindestens ein fachlicher Fall (Codex' Eingaben aus Runde 1 wörtlich: Sep-Vermeidung
100…160, LBR-Treppe 100/120/80, Santa 2024, Streak +10/−20, Median [10,30], NaN-Exit, SMA-Warm-up, `!=` mit null,
Stop mit Gap 100→80) und je Fall eine Mutation, die genau diese Prüfung reißen muss; `[Aufbau]`-Prüfungen, Endmarker,
Ausnahme ≠ Nachweis, `UNGUELTIG_ERWARTET`.

## Danach
Differenzbericht 1A (Trades/Kennzahlen je Strategie und Ticker gegenüber Phase 0, je Änderung mit Befundnummer) an den
Nutzer, eigene Reproduktion der Blogzahlen (`monthly-10-strategie`, `sell-in-may-2026`) — keine eigenmächtige
Änderung veröffentlichter Zahlen. Dann Codex-Code-Runden bis Freigabe, Commit/Push. Phase 1B, 2, 3 wie in v2
(Texte/Signale; Zwillinge/OHLC/Maskenvertrag) mit konkreten Regelvektoren vor der Umsetzung (v2-Einwand 7).

## Prüfe besonders
- Ist 1A in sich widerspruchsfrei, obwohl Hebel und historische Lücken bewusst erst in 1B kommen?
- Trägt Punkt 5 (moderner Kalender nur für Termine nach der letzten Zeile)?
- Stops zum Close: Folgen für Trades, deren Stop am Tag des regulären Ausstiegs auslöst?
