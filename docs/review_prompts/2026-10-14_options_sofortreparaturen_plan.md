# Entwurf v1: Options-Sofortreparaturen + Radar-Standard Percentile — Runde 1 (Plan)

Read-only, Repo `C:\dev\Seasonaledge`, Stand `origin/master` `d944a26`. Deutsch, echte Umlaute, Datei:Zeile, am Ende
**FREIGABE (Plan): ja/nein**. Hintergrund: `docs/OPENING_SETUP_PLAN.md` Abschnitt 1 + 4 (Stufe 1),
`docs/OPTIONS_OFFEN_2026-10-13.md` B. Nutzerentscheidungen 2026-10-14: diese Stufe umsetzen; Radar /skew standardmäßig
**Percentile** statt Rank (Umschalter bleibt).

## R1 — ETHA: realisierte Vola 380 %, VRP −333 (live seit 07.10.)
Befund (Agent, read-only): in `prices` springt ETHA am 30.09. von 20,28 auf 60,36 (Reverse-Split 1:3), `log_return`
dort korrekt (−0,79 %). `compute_options_skew._realized_vol` (`scripts/compute_options_skew.py:277`) rechnet über
`shared.data.lade_closes` → `shared/realized_vol.log_returns(closes)` aus **Schlusskursen**; der Sprung ln 3 im
21-T.-Fenster ergibt σ ≈ 3,8. Vermutung: der Nightly schreibt nur 7 Tage → ältere Zeilen behalten die alte Basis.
Plan:
- **a) Diagnose über das Universum (Server, nur lesen):** je Ticker die letzten 2 Jahre, Tage mit
  |ln(close_t/close_{t−1}) − log_return_t| > 0,05 → Liste (Ticker, Datum, Faktor). Ergebnis bestimmt, ob ETHA ein
  Einzelfall ist.
- **b) Ursache beim Erzeuger:** RV aus der Spalte `log_return` statt aus Schlusskursen? Dagegen spricht: `lade_closes`
  ist bewusst die eine Kursquelle für RV und Spot; `log_return` ist die Spalte, die der Nightly beim Split korrekt
  setzt. Alternative: Kursreihe beim Laden auf die jüngste Basis zurückrechnen, wenn ein Sprung ≠ log_return
  erkannt wird (Faktor = exp(log_return)·close_{t−1}/close_t). Beide Varianten bitte bewerten; die Spot-Rolle von
  `last_close` (Optionsbewertung braucht den unadjustierten Schluss) darf sich nicht ändern.
- **c) Datenreparatur:** betroffene Ticker-Historien in `prices` per Backfill neu laden (`onboard_ticker`/Backfill,
  server-seitig, nur mit Nutzerfreigabe), danach RV/VRP der History-Zeilen seit dem Split neu rechnen oder als
  ungültig markieren (sie stehen bereits in `options_skew_history.json`).
- Wächter: Fall „Split im Fenster“ (Kursreihe mit Faktor-3-Sprung, log_return korrekt) → RV plausibel; Mutation
  „zurück auf closes“.

## R2 — Datumsstempel = Session, nicht Lauftag
`scripts/snapshot_gex_massive.py:231` `stamp = date.today()` (Lauf 03:03 UTC am 13.10. → „2026-10-13“ für den
EOD-Stand 12.10.); `/dealer-positioning` zeigt „Stand: … (EOD)“ (`landing/pages/dealer-positioning.html:316`).
`compute_options_skew.py:1204` `pc_ratio.date = date.today()`. Plan: beide aus `shared.exchange_holidays.letzte_session()`
(wie der Skew-Cron seit v65.0). **Frage:** `gex_history/<stamp>.json` wird nach demselben Stempel benannt — bisherige
Dateien tragen den Lauftag. Umbenennen (Migration), oder ab jetzt Session, mit Hinweis im Archiv? Wer liest das Archiv?

## R3 — Morgen-Mail: Skew-Perzentil wie /skew, einfarbig
`shared/daily_report.py:53-83` `skew_pctl_map`: alle Zeilen (auch ohne `cm_mode`), ≥ 5 Punkte, Fenster ab
`date.today()`, Anteil `< heute` über **alle** Werte inkl. heute; /skew (`landing/pages/skew.html:240-268`): nur
`cm`/`cm_extrap`, ≥ 20 (`MIN_NORM`), letzter Punkt muss die Session sein (sonst kein Ranking), Percentile = Anteil
der **vorigen** Werte kleiner als der letzte, ÷ (n−1). Plan: **eine Rechnung im Cron** (`compute_options_skew.py`
schreibt je Ticker `skew_rank`/`skew_pctl` und `iv_rank`/`iv_pctl` in `options_skew.json`, Regel wörtlich wie
`_normHist`/`_rank`/`_pctl`), Mail und Seite **lesen** sie. Fehlt der Wert (nicht rankbar, Session alt), zeigt die
Mail „—“. Template `scripts/templates/daily_report.html.j2:115`: Grün/Rot nach Vorzeichen → einfarbig wie /skew;
Tooltip-Text „hoch = ungewöhnlich put-lastig“ prüfen (Skew = put − call). Wächter: Zwilling Python = JS auf
denselben History-Fixtures (Rank und Percentile, Session-Regel, MIN_NORM), Mutationen.
**Frage:** Soll /skew danach ebenfalls nur noch lesen (eine Quelle), oder bleibt die JS-Rechnung für die
Fensterwahl 3M/6M/1J nötig? (Seite rechnet je Fenster, der Cron nur 1J.)

## R4 — Morgen-Mail: Earnings-Zeilen
`shared/daily_report.py:943-966` liest `earnings_events.report_date` — `scripts/fetch_event_data.py:161-180` speichert
dort das Ende des **Geschäftsquartals** (bestätigt in `scripts/build_buyback_blackout.py:16`), nur vergangene
Quartale. Folge: „Earnings“-Einträge an Quartalsenden, echte Termine fehlen. Plan: Block entfernen (nicht nur
ausblenden), bis eine echte Terminquelle existiert (eigenes Vorhaben, Stufe 4); `build_buyback_blackout` bleibt
(nutzt die Spalte wissentlich). Wächter: Mail ohne „Quartalszahlen“-Ereignis aus `earnings_events`.

## R5 — Radar /skew: Standard Percentile
`landing/pages/skew.html:222` `SKEW_MODE='rank'` → `'pctl'`. Prüfen: Texte/Untertitel/Achsen, die „Rank“ fest nennen
(`_metricLbl`, Quadrant-Untertitel `skew.quad_sub`, EN), Tabellen-Spalte „Skew-Rk“, `SA.prefs`-Gedächtnis (falls der
Modus gemerkt wird), Blogartikel „Vol-Regime-Radar“ (beschreibt Rank als Standard?).

## Reihenfolge / Deploy
R5, R4, R2 klein und unabhängig; R3 mittel (Cron + Mail + Zwilling); R1 erst Diagnose (a), dann Entscheidung b/c mit
dem Nutzer. Wirkungsbericht vor dem Push: Mail-Spalte alt/neu für die Ticker der letzten Morgen-Mail, Radar-Positionen
Rank vs. Percentile.

## Prüffragen
1. Ursachen und Anker korrekt? Fehlt eine Fundstelle (weitere Leser von `earnings_events`, `pc_ratio.date`, `gex`-Stempel)?
2. R1: Variante b (log_return) oder Rückrechnung beim Laden — oder beides falsch?
3. R2: Archiv-Benennung?
4. R3: eine Rechnung im Cron vs. JS-Rechnung je Fenster — wie ohne Zwillingsbruch?
5. Freigabe für R1a (Diagnose) sofort und für R2–R5 als Plan?
