# Code-Review Phase 1A /plain-vanilla, Runde 1

Repo `C:\dev\Seasonaledge`, Arbeitsstand (`git diff` + neue Dateien). Freigegebener Plan:
`docs/review_prompts/2026-10-08_plain_vanilla_plan.md` (v5, Festlegungen E1–E9 gehen vor). Prüfe den **Code** gegen den
Plan und auf neue Fehler. Antwort auf Deutsch: je Befund Schwere + Datei:Zeile + konkreter Eingabefall + Änderung; am
Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Umgesetzt
- **N2 Kalender** `landing/js/holidays.js`: kein NYSE-Ersatztag 31.12. bei Neujahr am Samstag, MLK ab 1998, Juneteenth ab
  2022, NYSE-Sonderschließungen (Liste wie `shared/nyse_holidays.py`), XETRA 24./31.12. erst ab 2011. Wächter
  `scripts/verify_kalender_zwilling.py`: jeder Tag 2000–2035 NYSE+XETRA JS = Python + gezielte Fälle, 5/5 Mutationen;
  alter Stand: 53 abweichende Tage.
- **Rechenkern** `landing/js/strategy-compute.js`: Kontext (Stichtag, Börse), Zustandscodes −1/−2/−3, Kalender nur am
  Datenrand (2000–2035), `_sitzung`/`_offset`, `_makeTrade` mit Zuständen und ungerundeten Werten, LBR mit `hist[i-1]` und
  ohne stillen Rückfall, Santa streng vor Thanksgiving, Stops im Close-Modus mit Metadaten, `auswerten` (Reihenfolge E7),
  `streak`, `regeltermine`, `formatPF`, `formatZahl`, Profit-Faktor `null`. **Neu, nicht im Plan:** Sharpe erst ab
  `MIN_TRADES_SHARPE = 5` geschlossenen Trades (sonst `null`) — die ungerundeten Renditen machten aus zwei Trades mit
  11,847/11,845 % eine Sharpe von 6855 (vorher durch Rundung 0).
- `landing/js/indicators.js`: Gültigkeit beider Operanden zuerst, für jeden Operator.
- `landing/js/seasonal-compute.js`: `_quantil` (numpy linear), **drei** Fundstellen (Zeile 156 zusätzlich zu 229/625).
  Gleiche Floor-Median-Stelle in `decade-compute.js:136` bewusst NICHT angefasst (andere Seite, notiert).
- Seiten: `plain-vanilla.html` (calcStrategy → `auswerten`, Streak der Signalansicht aus derselben Auswertung, PF/Sharpe
  über Formatfunktionen, Drawdown-Bezeichnung „der abgeschlossenen Trades" DE/EN), `dashboard.html` (Termine aus
  `regeltermine`, Streak aus `auswerten`). **Zusätzlich gefunden:** `opex.html`, `tdom-analyse.html`, `vixpiration.html`
  nutzen `computeStats`/Stops → PF/Sharpe-Anzeige auf die Formatfunktionen umgestellt (sonst Absturz bei `null`); ihre
  Stops rechnen damit ebenfalls zum Close. i18n `_JSON_VER` v6, `verify_en` FAIL 0.
- **Python-Zwilling** `shared/strategies/plain_vanilla.py`: dieselben Bausteine (Kontext, Zustände, Datenrand-Helfer,
  `_make_trade`, LBR-Vortag, Statistik ohne offene Trades, PF/Sharpe `None`). Bewusst nicht: UHTS, OHLC-Stops (E3/E4),
  sowie strategie-eigene Abweichungen (z. B. Python-One-Day-Holiday mit festen Daten) — Phase 3.

## Belege
- `scripts/verify_plain_vanilla_1a.py`: 34/34 Prüfungen (node-Probe mit echten Modulen `scripts/js/probe_plain_vanilla_1a.js`,
  statische Seitenprüfungen, Python-Gegenprobe), `--mutationen` 30/30 gefangen, 3/3 untaugliche als ungültig erkannt.
  Gegen den alten Stand (git archive HEAD): 23/25 rot.
- Messlauf (eingefrorener Snapshot `a563a159fc2da067`, `scripts/js/probe_plain_vanilla_messlauf.js`, Zeitraum wie
  `getFilteredRows`), Zwischenläufe je Schritt; historische Trades bis Ende 2025 für Monthly 10, Sell in May, Nasdaq-Trend,
  Sep-Vermeidung, Januar-Strategien, Down-Month ToM auf SPY/^GSPC/^DJI auf 2 Stellen identisch → Blogzahlen unberührt.

## Prüfe besonders
1. Randlogik: Gibt es Strategien/Pfade, in denen ein Termin hinter der letzten Zeile still die letzte Zeile wird oder ein
   historischer Termin fälschlich über den Kalender läuft (`_amRand` für den Monat der letzten Zeile)?
2. `_sitzung` mit 'vor'/'nach' gegenüber den alten Index-Rechnungen (Midterm, UECS, One-Day-Holiday, UHTS): gleiche
   historische Ergebnisse?
3. `auswerten`-Reihenfolge, `_datenVeraltet`-Zählung (10/11), `heute()` Zeitzone.
4. Python-Zwilling: Abweichungen zur JS-Semantik in den geteilten Bausteinen.
5. Seitenänderungen: Absturzpfade bei `null`, EN-Texte.
