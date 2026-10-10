# Antwort Codex Runde 2 — Handelstag-Nummern (2026-10-10)

Prompt: [2026-10-10_xetra_tdoy_plan_v2.md](2026-10-10_xetra_tdoy_plan_v2.md). Modell laut Log: gpt-6.1-sol

## Urteil

**Plan v2 ist noch nicht tragfähig, weil Renditezuordnung, Kalenderumfang, vollständige Statistik-Erneuerung und die gemeinsame Umstellung von Schreibern und Lesern noch wesentliche Lücken haben.**

## Bestandsliste

Geprüft wurde der aktuelle Hauptarbeitsbaum auf Stand `9b0e3ef`, einschließlich der obersten drei Versionseinträge von `CLAUDE.md`. Es wurden keine Dateien oder Datenbankinhalte geschrieben. Die Gegenproben liefen ausschließlich im Speicher; der getrackte Arbeitsbaum ist unverändert.

Alle Pfade sind relativ zu `C:\dev\SeasonalEdge`. Gleichartige Verbraucher sind teilweise zusammengefasst, jeweils mit ihren einzelnen Zeilenankern. **P** kennzeichnet produktive Quellen öffentlich sichtbarer Zahlen; **B** kennzeichnet belegte Verbindungen zu Blogzahlen oder Blogcharts. „Nein“ bei Füllzeilen/Lücken bedeutet: keine durchgängige Prüfung nach V3/V4. Eine Kalenderzählung kann eine Nummer trotz Kurslücke richtig bestimmen, ohne deshalb eine Rendite über diese Lücke richtig zu behandeln.

**Kalender, Schreiber und Speicherung**

| Datei:Zeile | Funktion | schreibt/rechnet/liest | Zählweise heute | Börse berücksichtigt? | Füllzeilen/Lücken berücksichtigt? | sichtbar wo |
|---|---|---|---|---|---|---|
| `shared/exchange_holidays.py:480,515,673` | `get_holidays`, `is_trading_day`, `get_exchange_for_ticker` | rechnet Kalendergrundlage | Kalender; CRYPTO täglich, FOREX Mo–Fr | Mehrere Börsen; unbekannte Kalender können auf NYSE fallen | Unabhängig von Kurszeilen; Kalendergültigkeit nicht gleich Datenvollständigkeit | Grundlage für Schreiber, Mails, Strategien |
| `shared/symbols.py:98` | `get_exchange_for_holidays` | liest Börsenzuordnung | Metadaten | Ja | Keine Kursprüfung | Grundlage für Python-Verbraucher |
| `exchange_holidays.py:1` | Kompatibilitätsimport | liest/reexportiert | Kalender | Wie gemeinsames Modul | Wie gemeinsames Modul | Intern |
| `landing/js/holidays.js:206,226,259` | `detect`, `get`, `isTradingDay` | rechnet Kalendergrundlage | Kalender; `NONE` täglich | NYSE/XETRA/LSE; Forex wird `NONE`; weitere Börsen fallen auf NYSE | Unabhängig von Kurszeilen; Zuordnung unvollständig | **P** zahlreiche Seiten |
| `landing/js/holidays.js:273,291,308` | `nthTradingDay`, `lastTradingDay`, `nthTradingDayOfYear` | rechnet inverse Monats-/Jahresnummern | Kalender | Über vorstehende Zuordnung | Nummern unabhängig von Kurslücken; keine Prüfung verfügbarer Kurse | **P** Signale, TDOY-Datumsbeschriftungen |
| `shared/yahoo_downloader.py:239,267` | `preprocess` | liest/rechnet Spalten | DB-Spalte, falls vorhanden; sonst `groupby(...).cumcount()` | Kein Börsenparameter | Keine durchgängige Behandlung; auch teilweise vorhandene Spalten problematisch | **P/B** Nightly, Bulk-Import, Analysen |
| `scripts/nightly_refresh.py:49,79,105` | `refresh_ticker_data` → `preprocess`, Preisserialisierung | schreibt `prices.tdom/tdoy` | Ergebnis von `preprocess`; jüngste Kurszeilen | Nicht beim Nummerieren | Nein | **P** Preise und davon abhängige Seiten |
| `scripts/nightly_refresh.py:137,141` | Statistikteil in `refresh_ticker_data` | liest/rechnet/schreibt Stats | Über Cache und Analyse-Builder | Nicht durchgängig | Nein; nur `forward`, alle vier Renditearten | **P** Mails und Statistikleser |
| `scripts/nightly_refresh.py:252,276,297` | Lückenfüller in `main`, Phase C | schreibt neue Preiszeilen; keine Tagesnummern | Keine Nummerierung | Erwartete Tage kalenderbasiert | Fehlender Yahoo-Kurs wird weiterhin als Schließung behandelt; Nummern fehlen | **P**, ausdrücklich in P2 |
| `scripts/intraday_refresh.py:128,141,167,193` | Aktualisierung je Ticker | liest alte, rechnet neue, schreibt Nummern | Letzter DB-Wert plus gelieferte offene Kurszeilen | Kalender als Zulässigkeitsprüfung | Übersprungene Sitzungen erhöhen Zähler nicht; Teil-NULLs nicht sauber behandelt | **P** aktuelle Kurszeilen |
| `scripts/backfill_new_ticker.py:39` | `compute_tdoy_tdom` | rechnet | Zählt vorhandene, kalendergültige Daten | Ja | Geschlossene Zeilen zählen nicht; fehlende offene Sitzungen verschieben Nummern | **P** Onboarding/Vollhistorie |
| `scripts/backfill_new_ticker.py:66,139` | `backfill_ticker`, Serialisierung | schreibt Nummern | Vorstehendes Ergebnis | Ja | Schreibt Nummern nur bei `> 0` | **P** neue/erneuerte Historien |
| `scripts/onboard_ticker.py:45,95` | `_run`, `main` | veranlasst Schreiben | Delegiert an `backfill_new_ticker` | Über Delegat | Über Delegat; Fehler wird gewarnt, anschließend trotzdem Rückgabe 0 | **P** Onboarding |
| `scripts/backfill_tdoy.py:40,60` | `compute_tdoy_tdom` | rechnet | Vollständiger Monats-/Jahreskalender | Ja | Kurslücken ändern Nummern nicht; geschlossene Tage tragen Vorwärtswert/0 | Historische Korrektur |
| `scripts/backfill_tdoy.py:87,95,119,133` | `backfill_ticker` | liest/schreibt Nummern | Kalender | Ja | Pagination vorhanden; schreibt per Upsert auch `close`; keine alte-Sollwert-Transaktion oder Grenze ab 2001 | **P**, vorhandener historischer Schreibpfad |
| `bulk_load_supabase.py:108,134,254` | `upload_ticker`, Hauptlauf → `preprocess` | schreibt Nummern | `preprocess`/Zeilen | Nicht beim Nummerieren | Nein | **P** Vollhistorien; in P2 nicht aufgeführt |
| `scripts/fix_missing_days.py:41,76,124` | `get_expected_trading_days`, `download_and_fill` | prüft Kalender, schreibt Preise ohne Nummern | Keine Nummerierung der eingefügten Datensätze | Ja bei Lückensuche | Fehlende Sitzungen gesucht; `log_return=NULL`; Nummern bleiben aus; Batchfehler werden abgefangen | **P** Reparaturpfad |
| `shared/data.py:25,72` | `_load_from_supabase` | transportiert, verwirft Nummern | DB-Abfrage; `keep_cols` entfernt `tdom/tdoy` | Nein | Kein V5-Durchreichen | Python-Datenpfad |
| `shared/data.py:132,196,217` | `append_today_if_missing` | rechnet/schreibt Nummern | Letzter Wert plus 1 | Nicht beim Nummerieren | Nein | Kein aktueller Code-Aufrufer gefunden; Löschkandidat |
| `shared/supabase_client.py:69,93` | `fetch_prices`, `upsert_prices` | liest/schreibt transportierte Spalten | DB-Spalte | Nein | Keine semantische Prüfung | Gemeinsamer Produktionspfad |
| `shared/cache_manager.py:127,142,161` | `get_or_compute_tdom_stats` | liest/rechnet/schreibt | DB-Stats oder Analyse-Builder | Nicht durchgängig | Tagesaktuelle alte Stats werden akzeptiert; keine Methodenversion | **P** Nightly/Mails |
| `shared/cache_manager.py:183,198,217` | `get_or_compute_tdoy_stats` | liest/rechnet/schreibt | DB-Stats oder Analyse-Builder | Nicht durchgängig | Wie TDOM; kein `n_luecke` in Serialisierung | **P** Statistikleser |
| `shared/supabase_client.py:379,392` | `upsert_tdom_stats`, `fetch_tdom_stats` | schreibt/liest | DB-Spalte | Nein | Upsert entfernt keine verschwundenen Gruppen | **P** Statistik-Cache |
| `shared/supabase_client.py:133,142` | `upsert_tdoy_stats`, `fetch_tdoy_stats` | schreibt/liest | DB-Spalte | Nein | Wie TDOM; getrennte Requests sind getrennte Transaktionen | **P** Statistik-Cache |
| `scripts/create_market_tables.sql:83,102` | DDL für `tdom_stats`, `tdoy_stats` | definiert Speicherung | DB-Spalte, Schlüssel aus Ticker/Nummer/Richtung/Strategie | Kein Kalender-/Methodenmerkmal | Kein `n_luecke`, keine vollständige Generation | Intern/produktives Schema |
| `scripts/fix_tdom_trigger_and_log_returns.sql:10,15,22` | Trigger-/Zeitstempelkorrektur | beeinflusst gespeicherte Stats | DB-Spalten; keine Nummernberechnung | Nein | Zeitstempel bestätigen keine neue Rechenmethode | Intern |
| `scripts/sql/fix_tdoy_2026_08_glitch.sql:3` | Historischer `UPDATE` | schreibt TDOY | Feste SQL-Sollwerte | Implizit über Auswahl | Keine allgemeine Kalenderreferenz | Historischer Reparaturpfad |
| `scripts/check_db_completeness.py:391,639,657,665` | Vollständigkeitsprüfung, Reparatursteuerung | liest Anzahl Stats; veranlasst Rückschreiben | DB-Gruppenanzahl relativ zu Vergleichstickern | Nicht für Soll-Gruppenmenge | Repariert unvollständige Stats durch Preisnummern-Backfill; kann Vollhistorie ändern | Intern, automatisierbarer Schreibpfad |

**Python-Analysen und Mails**

| Datei:Zeile | Funktion | schreibt/rechnet/liest | Zählweise heute | Börse berücksichtigt? | Füllzeilen/Lücken berücksichtigt? | sichtbar wo |
|---|---|---|---|---|---|---|
| `shared/tdom_analysis.py:17,41,44` | `add_tdom_columns` | rechnet vorwärts/rückwärts | Kurszeilen je Ticker/Jahr/Monat | Nein | Nein; reverse bezieht sich auf beobachtetes Monatsende | **P/B** Stats und Strategien |
| `shared/tdom_analysis.py:51,68` | `calc_strategy_returns` | rechnet Renditen für nummerierte Zeilen | Nächste Kurszeile; Intraday gleiche Zeile | Nein | Keine Prüfung auf nächste Sitzung; drei Modi am **früheren** Tag verankert | **P** vier Statistikarten |
| `shared/tdom_analysis.py:86,110,115` | `build_tdom_stats` | liest/rechnet | Zeilenbasierte Vorwärts-/Rückwärtszahl | Nein | Nein; harte Grenze ±23 | **P** Durchschnitt, Win-Rate, Fallzahl |
| `shared/tdom_analysis.py:136,156,170,199` | `calc_tdom_range_return` | liest/rechnet | Zeilennummern; Haltedauer aus Zeilen | Nein | Keine Sitzungsvollständigkeit | Range-Backtests; Prüfpfad |
| `shared/tdom_analysis.py:232,242` | `build_tdom_month_matrix` | liest/rechnet | Zeilennummern | Nein | Nein | Heatmaps/Legacy-Leser |
| `shared/tdom_analysis.py:269,279` | `build_tdom_year_breakdown` | liest/rechnet | Zeilennummern | Nein | Nein | Jahres-Breakdown/Legacy-Leser |
| `shared/tdoy_analysis.py:20,38,41` | `add_tdoy_columns` | rechnet vorwärts/rückwärts | Kurszeilen je Jahr | Nein; auch keine Tickergruppierung | Nein | **P** Jahresstatistik |
| `shared/tdoy_analysis.py:50,70` | `build_tdoy_stats` | liest/rechnet | Zeilennummern | Nein | Nein | **P** TDOY-Stats |
| `shared/tdoy_analysis.py:119,139,146` | `calc_tdoy_range_return` | liest/rechnet | Zeilennummern/nummerierte Endpunkte | Nein | Keine Sitzungsvollständigkeit | Range-Analyse |
| `shared/tdoy_analysis.py:185,233` | `build_tdoy_month_matrix`, `build_tdoy_year_breakdown` | liest/rechnet | Zeilennummern | Nein | Nein | Heatmap/Jahres-Breakdown |
| `shared/tdoy_analysis.py:265,275,283` | `get_current_tdoy` | liest/rechnet | Nummer der letzten vorhandenen Jahreszeile | Nein | Alter Kurs ersetzt heutigen Stand | Intern/Legacy |
| `shared/tdoy_analysis.py:288,306,318` | `get_tdoy_month_boundaries` | liest/rechnet | Minimum vorhandener TDOY je Monat, dann Median | Nein | Fehlender Monatsanfang verschiebt Grenze | Achsenbeschriftung/Legacy |
| `shared/daily_report.py:156,176,182` | `compute_multi_window_tdom_score` | liest/rechnet | Lookup nach DB-TDOM | Vom übergebenen Ziel abhängig | Vertraut Stats; fehlende Fenster gesondert | **P** Daily-Mail |
| `shared/daily_report.py:393,434` | `_signal_row_from_series` | liest/rechnet | Kalender-TDOM je Ticker → Stats | Ja über `_tdom_for_ticker` | Kalenderzahl und alter Stats-Cache können auseinanderfallen | **P** Barometer/Watchlist-Mail |
| `shared/daily_report.py:502,509,518` | `_tdom_for_ticker` | rechnet | Kalender; Fehlerfallback Mo–Fr | Ja, Fehlerfallback NYSE/Mo–Fr | Nummer kursunabhängig; Fehler wird durch Ersatzkalender verdeckt | **P** Mail-Scores |
| `shared/daily_report.py:525,533` | `_tdom_for_date` | rechnet | Kalender | NYSE/XETRA, sonst NYSE | Nummer kursunabhängig | **P** Ziel-TDOM |
| `shared/daily_report.py:635,644,661,712` | `_try_build`, `top_daily_tips` | liest/rechnet | Gemeinsamer NYSE-Ziel-TDOM für Kandidaten | **Nicht je Kandidat**, obwohl EU-Aktien enthalten | Nein | **P** Top-Auswahl und Rangfolge |
| `shared/daily_report.py:777,800,844` | Jahres-/Monatszähler, Statuszeile | rechnet/liest | Kalender, bei Importfehler Mo–Fr | Über gewählten Kalender | Fallback kann Fehler verdecken | **P** Mail-Kopf |
| `shared/daily_report.py:1453` | Kontextaufbau | liest/reicht weiter | Berechneter `target_tdom` | Wie Top-Auswahl | Keine zusätzliche Prüfung | **P** Daily-Template |
| `shared/weekly_report.py:164,194,203,207` | `tdom_bias_for_week` | liest/rechnet | Mo–Fr-Nummer; folgende Gruppen per `current_tdom+offset` | Nein | Monatswechsel nicht abgebildet; weniger als fünf Gruppen möglich | **P** Weekly-Mail |
| `shared/weekly_report.py:683,694` | `_estimate_tdom` | rechnet | Mo–Fr | Nein | Kursunabhängig, Feiertage fehlen | **P** Weekly-Mail |
| `scripts/templates/daily_report.html.j2:151,195,322` | Ausgabe `target_tdom`, Score-Erklärung | liest | Kontext-/DB-Ergebnis | Behauptet börsenspezifische TDOM | Keine eigene Prüfung | **P** versendeter Lesertext |
| `scripts/templates/weekly_report.html.j2:133,145,154` | TDOM-Bias-Ausgabe | liest | Kontext-/DB-Ergebnis | Nein | Beschriftet Auswahl als nächste fünf Handelstage | **P** versendeter Lesertext |
| `scripts/daily_newsletter.py:211` | Newsletter-Ausführung/Statusausgabe | liest/reicht weiter | Kontext-TDOM | Wie Report | Wie Report | Mail und Laufprotokoll |
| `scripts/weekly_newsletter.py:181` | Newsletter-Ausführung/Statusausgabe | liest/reicht weiter | Kontext-TDOM-Bias | Wie Report | Wie Report | Mail und Laufprotokoll |
| `scripts/backtest_newsletter_scoring.py:152,167,178` | `compute_sc_series` | liest/rechnet | Historische Zeilen-TDOM → neu gebaute Stats | Nein | Keine kalendergenaue Zuordnung | Intern; Validierung der Mail-Scores |
| `scripts/backtest_newsletter_scoring.py:273,278,312,318` | `analyze_ticker`, `analyze_ticker_oos` | rechnet/liest | `add_tdom_columns` | Nein | Nein | Intern; Ergebniszahlen |
| `shared/charts.py:180,214,216,226,261,281,548` | `build_seasonal_chart` | rechnet/liest | TDOY-Spalte/Zeilenfallback; TDOM-Zeilen; Zukunft NYSE | Historie nein, Projektion NYSE | Carry kann Monatsgrenze überqueren; Lücken bleiben Zeilenpositionen | Legacy-Chart; kein aktueller Code-Aufrufer gefunden |
| `shared/drawdown_analysis.py:251,294,302` | `compute_current_vola_stats` | rechnet implizite Jahresposition | Anzahl aktueller Jahreszeilen; historisch derselbe Arrayindex | Nein | Kürzere Historie wird auf letzten Wert begrenzt | Intern/Legacy; kein aktueller Code-Aufrufer gefunden |
| `shared/calculations.py:502,518,528` | `analyze_turn_of_month` | rechnet implizite Rückwärts-/Vorwärtspositionen | Letzte/erste Monatszeilen | Nein | Monatsnachbarschaft geprüft; einzelne fehlende Sitzungen nicht | **B** TOM-Blogchart |
| `shared/saison_score.py:165,174` | Jahrespfad-/Mindestdatenprüfung | rechnet eine als 20. Handelstag beschriftete Schwelle | Anzahl Jahreskurszeilen | Nicht für diese Schwelle | Datenanfang geprüft, keine Kalendernummer | **P** Saison-Score-Status; Bedeutung der Schwelle klären |

**Python-Strategien mit Monatspositionen**

Die folgenden Verbraucher hängen entweder unmittelbar an `add_tdom_columns` oder an den historischen Monatszeilenhelfern. Damit reicht eine Prüfung der drei Importstellen allein nicht.

| Datei:Zeile | Funktion | schreibt/rechnet/liest | Zählweise heute | Börse berücksichtigt? | Füllzeilen/Lücken berücksichtigt? | sichtbar wo |
|---|---|---|---|---|---|---|
| `shared/strategies/plain_vanilla.py:213,222` | `_kalender_monat`, `_get_trading_days` | rechnet/liest | Kalender beziehungsweise vorhandene Monatszeilen | Kalenderhelfer ja; Zeilenhelfer nein | Kalender kennt Sitzungen, Zeilenliste kennt nur Kurse | Strategiegrundlage |
| `shared/strategies/plain_vanilla.py:228,239,250` | `_nth_trading_day`, `_last_trading_day`, `_nth_last_trading_day` | rechnet inverse Monatsnummern | Historie: Zeilen; Datenrand: Kalender | Am Datenrand ja | Historische fehlende Sitzung verschiebt Termin | **P/B** zahlreiche Strategien |
| `shared/strategies/plain_vanilla.py:334,335` | `calc_sell_in_may` | liest/rechnet | Letzte Oktoberzeile, dritte Maizeile | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:409,410` | `calc_nasdaq_trend` | liest/rechnet | Letzte Monatszeilen | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:430,434` | `calc_month_end` | liest/rechnet | Vorletzte Monatszeile, vierte Folge-Monatszeile | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:445,453,465,487` | `calc_monthly_10` | rechnet/liest | Zeilen-TDOM; `max(tdom)`; am Rand Zeilen plus künftige Sitzungen | Am Rand ja | Fehlende vergangene Sitzung bleibt fehlende Position; fehlendes Monatsende verändert „letzte zwei“ | **P/B** Monthly 10 |
| `shared/strategies/plain_vanilla.py:546` | `calc_santa_claus` | liest/rechnet | Fünfte Januarzeile über Helfer | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:726,736,753,760` | `calc_ultimate_monthly` | rechnet/liest | Zeilen-TDOM und Maximum beobachteter TDOM | Teilweise über andere Helfer | Nein | Interne/Legacy-Strategie |
| `shared/strategies/plain_vanilla.py:814,822,835,838,844` | `_compute_kti_daily` | rechnet/liest | Zeilen-TDOM, `max(tdom)` als Monatsende | Nicht für Monatsnummern | Nein | KTI-Grundlage |
| `shared/strategies/plain_vanilla.py:923,951` | `calc_kti_long_only`, `calc_kti_leveraged` | liest/rechnet | Vorstehender KTI | Teilweise | Nein | Interne/Legacy-Strategien |
| `shared/strategies/plain_vanilla.py:1002,1006,1012` | `calc_first_five_days` | liest/rechnet | Erste/fünfte Januarzeile; erste Februar-/letzte Dezemberzeile | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:1024,1028,1034` | `calc_last_five_days` | liest/rechnet | Letzte fünf Januarzeilen, weitere Monatsendpunkte | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:1046,1050,1056` | `calc_january_barometer` | liest/rechnet | Erste/letzte Januarzeile; Monatsendpunkte | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:1141` | `calc_post_christmas` | liest/rechnet | Letzte Dezemberzeile über Helfer | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:1157,1158` | `calc_second_trading_day` | liest/rechnet | Erste/zweite Monatszeile | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:1213` | `calc_election_year_7months` | liest/rechnet | Letzte Dezemberzeile | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/plain_vanilla.py:1257,1265,1273,1281,1289` | `calc_uecs` | liest/rechnet | Erste/letzte Monatszeilen in fünf Komponenten | Wie Helfer | Nein in Historie | **P** Strategie-Kennzahlen |
| `shared/strategies/januar_trifecta.py:38,46,86,129` | `_get_trading_days`, `check_santa_claus_rally`, `check_first_five_days`, `check_january_barometer` | rechnet/liest | Monatszeilen, letzte fünf/erste zwei/fünfte/letzte | Nein | Nein | Python-Trifecta, Legacy/Prüfgrundlage |
| `shared/strategies/januar_trifecta.py:198,255` | `calculate_trifecta`, `calculate_trifecta_history` | liest/rechnet | Vorstehende Resultate und Monatsendpunkte | Nein | Nein | Trifecta-Ergebnisse |
| `shared/strategies/kaeppel.py:262,304,325,327` | KTI-Komponente, `_is_turn_of_month` | rechnet/liest | Letzte vier Vormonatszeilen, erste drei Monatszeilen | Nein | Nein | Intern/Legacy-KTI |

**Gemeinsame JS-Berechnungen und Strategien**

| Datei:Zeile | Funktion | schreibt/rechnet/liest | Zählweise heute | Börse berücksichtigt? | Füllzeilen/Lücken berücksichtigt? | sichtbar wo |
|---|---|---|---|---|---|---|
| `landing/js/app.js:756` | Preisabruf | liest/transportiert | DB-Spalte `tdom/tdoy` | Nein | Keine Nummernprüfung | Gemeinsamer Seiten-Datenpfad |
| `landing/js/app.js:826,854,866,877` | `renderTradingDayHeader` | rechnet/liest | Kalender; an geschlossenen Tagen letzte DB-Zeile | Über `detect`, begrenzt | Fallback prüft weder Monat/Jahr noch Aktualität | **P** 23 Seiten, unten vollständig aufgeführt |
| `landing/js/decade-compute.js:542` | Preisabruf | transportiert Nummern | DB-Spalte | Nein | Keine Prüfung | Dekaden-/Anomalie-Datenpfad |
| `landing/js/decade-compute.js:21,69,318,330` | `fromPrices`, `computeRollingVola` | rechnet implizite Jahrespositionen | Kursreihenfolge → **252 interpolierte Punkte** | Nein | Fehlende/geschlossene Zeilen verändern Interpolation | **P** Dekadenkurven; kein semantischer TDOY-Spaltenleser |
| `scripts/generate_decade_data.py:28` | `_approx_date` | rechnet Datumsbeschriftung | Virtueller 252er Index → Kalenderdatum | Nein | Kein tatsächlicher Sitzungsindex | **P** Dekaden-Datenartefakte |
| `landing/pages/dekadenzyklus.html:882` | Approximative Datumszuordnung | rechnet/liest | Virtueller 252er Index | Nein | Nein | **P** Hoch-/Tief-Datumsbeschriftung |
| `landing/js/seasonal-compute.js:47,86,90` | `analyzeTurnOfMonth` | rechnet implizite Monatspositionen | Letzte/erste Monatszeilen | Nein | Monatsnachbarschaft geprüft; Sitzungslücken nicht | **P** Monatswechsel |
| `landing/js/saison-score.js:75,77,83` | `pfad`, Jahres-Mindestdatenprüfung | rechnet/liest Schwelle | Jahreskurszeilen, beschriftet als 20. Handelstag | Nicht für diese Schwelle | Nein für Kalendernummer | **P** Saison-Score-Status |
| `landing/js/strategy-compute.js:27,161` | `_getTradingDays`, `_kalenderMonat` | liest/rechnet | Monatszeilen beziehungsweise Kalender | Kalender ja | Historische Zeilen unbereinigt | **P/B** Strategiebasis |
| `landing/js/strategy-compute.js:179,191,201` | `_nthTradingDay`, `_lastTradingDay`, `_nthLastTradingDay` | rechnet inverse Nummern | Historie: Zeilen; Datenrand: Kalender | Am Rand ja | Historische Lücken verschieben Termine | **P/B** Strategie-Kennzahlen |
| `landing/js/strategy-compute.js:357,358` | `calc_sell_in_may` | liest/rechnet | Letzte Oktober-/dritte Maiposition | Wie Helfer | Nein in Historie | **P** Plain Vanilla |
| `landing/js/strategy-compute.js:369,370` | `calc_nasdaq_trend` | liest/rechnet | Letzte Monatspositionen | Wie Helfer | Nein in Historie | **P** Plain Vanilla |
| `landing/js/strategy-compute.js:382,385` | `calc_month_end` | liest/rechnet | Vorletzte/fierte Monatsposition | Wie Helfer | Nein in Historie | **P** Plain Vanilla |
| `landing/js/strategy-compute.js:403` | `calc_santa_claus` | liest/rechnet | Fünfte Januarposition | Wie Helfer | Nein in Historie | **P** Plain Vanilla |
| `landing/js/strategy-compute.js:491,494,495` | `calc_first_five_days` | liest/rechnet | Erste/fünfte Januarzeile und Monatshelfer | Wie Helfer | Nein in Historie | **P** Plain Vanilla |
| `landing/js/strategy-compute.js:507,510,511` | `calc_last_five_days` | liest/rechnet | Letzte fünf Januarzeilen und Monatshelfer | Wie Helfer | Nein in Historie | **P** Plain Vanilla |
| `landing/js/strategy-compute.js:523,526,527` | `calc_january_barometer` | liest/rechnet | Erste/letzte Januarzeile und Monatshelfer | Wie Helfer | Nein in Historie | **P** Plain Vanilla |
| `landing/js/strategy-compute.js:596,608,609` | `calc_post_christmas`, `calc_second_trading_day` | liest/rechnet | Letzte Jahres-/erste und zweite Monatsposition | Wie Helfer | Nein in Historie | **P** Plain Vanilla |
| `landing/js/strategy-compute.js:650,670,675,680,685,690` | `calc_election_year_7months`, `calc_uecs` | liest/rechnet | Erste/letzte Monatspositionen | Wie Helfer | Nein in Historie | **P** Plain Vanilla |
| `landing/js/strategy-compute.js:712,718,721,730` | `calc_monthly_10` | rechnet/liest | Zeilenanzahl; am Rand Zeilen plus zukünftige Sitzungen | Am Rand ja | Fehlende vergangene Sitzung und fehlendes Monatsende bleiben falsch | **P/B** Monthly 10 |
| `landing/js/strategy-compute.js:898,899,939` | `regeltermine` | rechnet/liest | Kalendertermine; `NONE` wird NYSE | Begrenzt, Krypto/Forex problematisch | Kein vollständiger Kalendervertrag | **P** Dashboard-Strategietermine |
| `landing/js/strategy-compute.js:1141,1146` | `calc_downmonth_tom` | liest/rechnet | TDOM-14-Einstieg über Monatszeilenhelfer | Wie Helfer | Nein in Historie | **P** Strategie-/Research-Pfad |

**HTML-Inline-Berechnungen und deren Leser**

| Datei:Zeile | Funktion | schreibt/rechnet/liest | Zählweise heute | Börse berücksichtigt? | Füllzeilen/Lücken berücksichtigt? | sichtbar wo |
|---|---|---|---|---|---|---|
| `landing/pages/dashboard.html:472` | `assignTdom` | rechnet | Zähler über Monatskurszeilen | Nein | Nein | **P** Dashboard |
| `landing/pages/dashboard.html:483,517` | `calcIntramonthCurve`, `calcCurrentMonthCurve` | liest/rechnet | Zugewiesene Zeilen-TDOM | Nein | Keine kalendergenaue Ausrichtung | **P** Monatskurve |
| `landing/pages/dashboard.html:529` | `calcTdomPositionStreak` | liest/rechnet | TDOM-Positionen der Kurven | Nein | Wie Kurven | **P** Streaks |
| `landing/pages/dashboard.html:558,566,578` | `getTdomMiniStats` | rechnet/liest | Kalender-TDOM trifft zeilenbasierte Statistik | Begrenzt über `detect` | Historie und Zielnummer können verschiedene Sitzungen meinen | **P** TDOM-Karten |
| `landing/pages/dashboard.html:633,644` | `getCurrentTdom` | rechnet | Kalender | Begrenzt über `detect` | Nummer kursunabhängig | **P** aktueller Marker |
| `landing/pages/dashboard.html:947,953,960,967,974` | `_getTradingDays`, `_checkSCR`, `_checkFFD`, `_checkJanB`, `calcTrifecta` | rechnet/liest | Monatszeilen, fünfte/letzte/erste Positionen | Nein | Nein | **P** Trifecta-Karte |
| `landing/pages/dashboard.html:1579,1763,1792,2095` | `renderMonthChart`, `renderTdomMiniCard`, `renderTrifectaCard`, Aufruf in `renderAll` | liest | Vorstehende Ergebnisse | Wie Berechnung | Keine zusätzliche Prüfung | **P** Charts, Karten, Zahlen |
| `landing/pages/monatszyklus.html:405` | `assignTdom` | rechnet | Monatszeilenzähler | Nein | Nein | **P** Monatszyklus |
| `landing/pages/monatszyklus.html:430,457,511` | `getCurrentTdom`, `calcIntramonthCurve`, `calcCurrentMonthCurve` | rechnet/liest | Aktuell Kalender; Historie Zeilen | Begrenzt nur beim aktuellen Tag | Nein in Historie | **P** Haupt-/Jahreskurven |
| `landing/pages/monatszyklus.html:526,544` | `calcWeeklyPerformance` | liest/rechnet | TDOM-Blöcke aus Zeilennummern | Nein | Keine kalendergenaue Blockvollständigkeit | **P** Wochenzahlen |
| `landing/pages/monatszyklus.html:620,668` | `calcTwoWeekPerformance`, `calcTwoWeekCurrentYear` | liest/rechnet | Split an Zeilen-TDOM | Nein | Nein | **P** Zwei-Hälften-Analyse |
| `landing/pages/monatszyklus.html:704,726,770` | `computeDetrend`, `calcSeasonalMatch`, `calcCycleMatch` | liest/rechnet | TDOM-Statistik-/Kurvenpositionen | Nein | Erben falsche Ausrichtung | **P** Detrend/Match-Zahlen |
| `landing/pages/monatszyklus.html:848,881,969` | `calcMomentumCheck`, `calcTwoWeekSignificance`, `applyOutlierFilter` | liest/rechnet | TDOM-Split beziehungsweise TDOM-Gruppen | Nein | Erben Zeilenpositionen | **P** Momentum, Signifikanz, bereinigte Kurven |
| `landing/pages/monatszyklus.html:1082,1208,1281,1432` | `MZ.renderMain`, `renderIndividualYears`, `renderDetrend`, `renderWeekly` | liest | TDOM-Statistik, Kurven, Marker | Wie Berechnung | Keine zusätzliche Prüfung | **P** Charts |
| `landing/pages/monatszyklus.html:1540,1610,1657,1712,1747,1776` | `renderTwoWeek`, `renderTwHeatmap`, `renderTwOverlay`, `renderTwRanking`, `renderMomentum`, `renderTwSignificance` | liest | TDOM-Splits und abgeleitete Ergebnisse | Wie Berechnung | Keine zusätzliche Prüfung | **P** Tabellen, Rankings, Kennzahlen |
| `landing/pages/monatszyklus.html:1918,1930,1961` | `renderAll` | veranlasst/reicht weiter | `assignTdom` und Kalender-Marker | Gemischt | Keine gemeinsame Gültigkeitsregel | **P** gesamte Seite |
| `landing/pages/tdom-analyse.html:340` | `fetchOHLC` | liest/transportiert | DB-TDOM/TDOY | Nein | Keine Prüfung | Statistik-Eingang |
| `landing/pages/tdom-analyse.html:357,379,380` | `addTdomColumns` | rechnet | Vorwärts-/Rückwärtszahl über Monatszeilen; TDOY wird verworfen | Nein | Nein | **P** alle Tagespositionen der Seite |
| `landing/pages/tdom-analyse.html:390` | `calcStrategyReturn` | rechnet | Gleiche/nächste **Arrayzeile** | Nein | Keine Sitzungsnachbarschaft | **P** Tagesrenditen |
| `landing/pages/tdom-analyse.html:416,478` | `buildTdomStats`, `buildTdomMonthMatrix` | liest/rechnet | Zeilen-TDOM/-reverse | Nein | Nein; Tagesbereich auf 23 begrenzt | **P** Statistik, Heatmap |
| `landing/pages/tdom-analyse.html:526,557,568` | `calcRangeReturns` | liest/rechnet | Zugewiesene TDOM-Endpunkte | Nein | Arbeitet auch auf bereits gefilterter Kursliste | **P** Strategie-Tester |
| `landing/pages/tdom-analyse.html:593,603,621` | `getCurrentTdom` | rechnet | Kalender, auch rückwärts | Begrenzt über `detect` | Geschlossener Tag erhält derzeit dennoch Rückwärtsmarker | **P** aktueller Marker |
| `landing/pages/tdom-analyse.html:809,827,828,837` | `buildTdoyStats` | liest/rechnet | DB-TDOY, sonst Jahreszeilenzähler | Nein | Vorgänger verwirft DB-Spalte; gefilterte Liste wird neu gezählt; Grenze 260 | **P** TDOY Top 25 |
| `landing/pages/tdom-analyse.html:880,894` | `renderTdoyTop25` | liest/rechnet Datumszuordnung | Stats-TDOY → Kalenderdatum | Begrenzt | Zeilennummer wird als Kalendernummer interpretiert | **P** beste Jahrestage |
| `landing/pages/tdom-analyse.html:990,1005` | `renderStreakPerTdom` | liest/rechnet | TDOM-Gruppen und Array-Nachfolger | Nein | Nein | **P** Streak-Analyse |
| `landing/pages/tdom-analyse.html:629,649,697,745,1025,1048` | `renderKPIs`, `renderBars`, `renderWinRate`, `renderHeatmap`, `renderStats`, `renderRange` | liest | Vorstehende Nummern/Statistiken | Wie Berechnung | Keine zusätzliche Prüfung | **P** Kennzahlen, Diagramme, Trades |
| `landing/pages/tdom-analyse.html:126,127,1181,1235,1241` | Eingabegrenzen, `rerender`, `loadTicker` | liest/filtert/rechnet | ±23; Kursliste vor Renditebildung verkürzt | Nein | Indikatorfilter und fehlendes Open erzeugen neue Arraynachbarn | **P** Statistik-/Range-Ergebnisse |
| `landing/pages/monatswechsel.html:304,358,399,644` | `renderAll`, `buildCurrentYearTOMCurves`, `renderCycleTOM` | rechnet/liest | Letzte/erste Monatszeilen | Nein | Monatsnachbarschaft geprüft; Sitzungspositionen nicht | **P** TOM-/Zykluskurven |
| `landing/pages/monatswechsel.html:445,505,518,535,564,590,601` | Chart, KPI, Signifikanz, Best/Worst, Heatmap, Streaks, Fensteroptimierung | liest/rechnet | Vorstehende relative Monatspositionen | Nein | Keine zusätzliche Kalenderausrichtung | **P** veröffentlichte Seitenzahlen |
| `landing/pages/overnight.html:278,282` | `fetchOHLC` | transportiert | DB-TDOM/TDOY | Nein | Keine Prüfung | Overnight-Datenpfad |
| `landing/pages/overnight.html:299,301,311,317` | `compute` | rechnet Renditen; **keine** TDOM/TDOY-Nummer | Vorherige Arrayzeile; Mo–Fr-Filter | Kein Börsenfeiertagsfilter | V3/V4-Abhängigkeit; Wochenende wird erst nach Wahl des Vorgängers ausgeschlossen | **P** Overnight-Statistik |
| `landing/pages/backtest-engine.html:994,1010,1016` | `makeTdomEvents` | rechnet | Mo–Fr-Zähler | Nein | Feiertage zählen als Sitzungen; Kurslücken verschieben Ereignisabbildung | **P/B** TDOM-Backtests |
| `landing/pages/backtest-engine.html:1373,1485,1722,1733,1744,1755,1766,1777,1788` | Parameter-/Ereignispfad und sieben Presets | liest/rechnet | TDOM-Ereignisse aus vorstehender Zählung | Nein | Wie Ereignisgenerator | **P/B** Preset-Kennzahlen |
| `landing/pages/plain-vanilla.html:274,529,530` | `calcStrategy`, `_nthTD`, `_lastTD` | liest/rechnet | Shared-Strategien und Kalendertermine | Über Shared-JS, begrenzt | Historie und künftiger Kalendertermin können auseinanderfallen | **P/B** Strategie-Kennzahlen/Signale |
| `landing/pages/watchlist.html:310,316,320,334` | `exchangeFor`, `_lastTradingDay`, `_nthTradingDay`, `computeNextStrategySignal` | rechnet/liest | Kalender; `NONE` wird NYSE | Begrenzt; Krypto/Forex falsch zusammengeführt | Kalender kennt Sitzungen, Kursstatus separat | **P** Watchlist-Strategietermine |
| `landing/pages/watchlist.html:362,372,380,389,407,410,419,422,424` | Strategie-spezifische Terminaufrufe | liest/rechnet | Erste/n-te/letzte Monatsposition | Wie Helfer | Wie Helfer | **P** Watchlist-Signale |
| `landing/pages/trifecta.html:211,218,225,232` | `getTradingDays`, `checkSCR`, `checkFFD`, `checkJanB` | rechnet/liest | Monatszeilen; fünfte/letzte/erste Positionen | Nein | Nein | **P** Trifecta-Renditen |
| `landing/pages/trifecta.html:240,248,256` | `calcTrifecta`, `calcHistory` | liest/rechnet | Vorstehende Resultate und Monatsendpunkte | Nein | Nein | **P** historische Erfolgszahlen |
| `seo/tools/trading-day-converter.html:238,256,268,279,290,321` | `isTradingDay`, `getTDOY`, `getTDOM`, `getTDOMMax`, `update` | rechnet/liest | Eigener statischer NYSE-Kalender | Nur NYSE, begrenzte Jahresliste | Kalender nicht zentral; lokale Datumsteile mit UTC-Feiertagsdatum vermischt | **P** Handelstagskonverter |

**Sämtliche produktiven Aufrufer des gemeinsamen Headers**

Diese Aufrufer lesen beziehungsweise zeigen über `SA.renderTradingDayHeader` TDOM/TDOY. Die übrige Fachrechnung einer Seite ist dadurch nicht automatisch betroffen.

| Datei:Zeile | Funktion | schreibt/rechnet/liest | Zählweise heute | Börse berücksichtigt? | Füllzeilen/Lücken berücksichtigt? | sichtbar wo |
|---|---|---|---|---|---|---|
| `landing/pages/backtest-engine.html:1678`; `crash-fruehwarnung.html:242`; `dashboard.html:2028` | Header-Aufruf | liest/zeigt | Kalender plus DB-Fallback | Über Header | Monats-/Jahresprüfung fehlt | **P** jeweiliger Seitenkopf |
| `landing/pages/dekadenzyklus.html:341`; `feiertage.html:641`; `intermarket-shocks.html:818` | Header-Aufruf | liest/zeigt | Kalender plus DB-Fallback | Über Header | Wie Header | **P** jeweiliger Seitenkopf |
| `landing/pages/jahreszyklus.html:1705`; `ki-saisonalitaet.html:756`; `monatswechsel.html:338` | Header-Aufruf | liest/zeigt | Kalender plus DB-Fallback | Über Header | Wie Header | **P** jeweiliger Seitenkopf |
| `landing/pages/kriegszeiten.html:390`; `monatszyklus.html:1964`; `mondphasen.html:271` | Header-Aufruf | liest/zeigt | Kalender plus DB-Fallback | Über Header | Wie Header | **P** jeweiliger Seitenkopf |
| `landing/pages/overnight.html:670`; `opex.html:1265`; `plain-vanilla.html:326` | Header-Aufruf | liest/zeigt | Kalender plus DB-Fallback | Über Header | Wie Header | **P** jeweiliger Seitenkopf |
| `landing/pages/risikozyklus.html:898`; `spot-vol-beta.html:1191`; `tdom-analyse.html:1242` | Header-Aufruf | liest/zeigt | Kalender plus DB-Fallback | Über Header | Wie Header | **P** jeweiliger Seitenkopf |
| `landing/pages/trifecta.html:291`; `vixpiration.html:1158`; `wochentage.html:1744`; `zentralbanken.html:584` | Header-Aufruf | liest/zeigt | Kalender plus DB-Fallback | Über Header | Wie Header | **P** jeweiliger Seitenkopf |
| `landing/pages/sektor-rotation.html:670` | Header-Aufruf mit Text statt Ticker | liest/zeigt | Kalender plus DB-Fallback | Übergibt `loadedCount + ' Sektoren'`; damit Standardzuordnung | Wie Header | **P** Sektor-Seitenkopf |

**Research, Blogproduktion und Prüfpfade**

| Datei:Zeile | Funktion | schreibt/rechnet/liest | Zählweise heute | Börse berücksichtigt? | Füllzeilen/Lücken berücksichtigt? | sichtbar wo |
|---|---|---|---|---|---|---|
| `scripts/ml/tom_ml_filter.py:49,59,60,95,108` | `_compute_tdom_features`, Feature-/TOM-Fensteraufbau | rechnet/liest | Vorwärts-/Rückwärtszahl über Monatszeilen | Nein | Nein | Interne ML-Features/Backtests |
| `scripts/ml/regime_clustering.py:225,233,257,271` | `_ensure_tdom`, TDOM-Auswertungen | liest/rechnet | DB-TDOM, sonst Zeilen | Nein | Nein | Research-Ausgabe; direkte Veröffentlichung dieser TDOM-Zahlen nicht belegt |
| `scripts/ml/backtest_new_filters.py:30` | `get_tdom_dates`, Filter-Backtests | rechnet/liest | Mo–Fr | Nein | Feiertage fehlen | **B** SPY-Down-Month-Reversal-Studie |
| `scripts/research/etf_seasonal_scan.py:203,210,214,219,224` | `_by_month`, `_td`, `_nth`, `_last`, `_nth_last` | rechnet/liest | Monatszeilen | Nein | Nein | Research-Strategiegrundlage |
| `scripts/research/etf_seasonal_scan.py:271,275,279,288` | `S_sell_in_may`, `S_nasdaq_trend`, `S_month_end`, `S_santa_claus` | liest/rechnet | Erste/n-te/letzte Monatszeile | Nicht für Nummern | Nein | Research-Kennzahlen |
| `scripts/research/etf_seasonal_scan.py:335,344,353,380,384,398` | `S_first_five`, `S_last_five`, `S_jan_barometer`, `S_post_christmas`, `S_second_td`, `S_election_7m` | liest/rechnet | Monatszeilen-Endpunkte | Nicht für Nummern | Nein | Research-Kennzahlen |
| `scripts/research/etf_seasonal_scan.py:402,423,428,452` | `S_monthly_10`, `S_downmonth_tom`, Monatsend-Fallback in `S_lbr_nov_mai` | liest/rechnet | Monatszeilen/Zeilenanzahl | Nicht für Nummern | Nein | Research; Referenz für Strategieentwicklung |
| `scripts/research/monthly10_blogzahlen.py:46,55,56,87` | `bloecke`, Hauptauswertung | rechnet/liest | Monatszeilen, erste vier/9–12/letzte zwei | Nein | Nein | **B** veröffentlichte Monthly-10-Zahlen |
| `scripts/research/monthly10_charts.py:31,45,85,87` | Import `bloecke`, `daten`, Chartbeschriftung | liest/rechnet | Dieselbe zeilenbasierte Blocklogik | Nein | Nein | **B** DE-/EN-Blogbilder |
| `scripts/research/plain_vanilla_kurse.py:39` | Kurssnapshot-Abfrage | transportiert | DB-TDOM/TDOY | Nein | Keine semantische Prüfung | Interne Vergleichseingabe |
| `scripts/research/plain_vanilla_zwilling.py:87,115` | Hauptvergleich → `auswerten` | liest/rechnet indirekt | Produktionsstrategien | Übergibt Börse | Erbt jeweilige Strategiefehler | Intern; keine unabhängige Kalenderreferenz |
| `blog/blog_builder.py:779,796` | `_build_tom_effect_chart` | rechnet/liest indirekte Monatspositionen | `analyze_turn_of_month` | Nein | Keine Sitzungsprüfung | **B** bei Blog-Neubau neu erzeugter TOM-Chart |
| `scripts/video/render_vertical_chart.py:298,327,328,335` | `_load_intramonth`, `draw_intramonth` | rechnet/zeigt | Monatskurven nach Arrayposition gemittelt | Nein | Sitzungslücken verschieben Kurvenpositionen | Video-Artefakte; konkrete Veröffentlichung nicht nachgewiesen |
| `scripts/sql/verify_tdoy_2026_08.sql:4,12` | `LAG`-Prüfung | liest/prüft | Erwartet +1 zwischen benachbarten Kurszeilen | Nein | Mit Kalendernummern bei Lücke falscher Wächter | Intern |
| `scripts/verify_calendar_rules.py:288,306,310,313,316` | Regeln 4–6 | liest/prüft | Erwartet +1 beziehungsweise Periodenstart 1 | Teilweise über ausgewählte Ticker | Widerspricht fehlenden Sitzungen und geschlossenen Tagen mit 0 | Intern; Completeness-Workflow |
| `scripts/verify_kalender_zwilling.py:105,119,147,178` | JS-Kalenderprobe, `pruefe`, Einzeltest, Mutationen | prüft Kalendergrundlage | Kalender | **NYSE/XETRA 2000–2035**, nicht alle Python-Kalender | Prüft heute noch keine V2-Nummern oder V4-Endpunkte | Intern; P1 erweitern |
| `scripts/verify_seasonal_twins.py:423,433`; `scripts/js/twin_probe.js:61,112,149` | TDOM-Range-/TOM-Proben | rechnet/liest | Produktionsfunktionen | Nicht umfassend | Einzelne bestehende Fälle; keine komplette neue Kalenderabnahme | Intern |
| `scripts/verify_twins_mutation.py:82` | TDOM-Mutationsanker | prüft | Produktionsfunktion | Wie Produktionspfad | Neuer Vertrag braucht zusätzliche gültige Anker | Intern |
| `scripts/verify_plain_vanilla_1a.py:196,227`; `scripts/js/probe_plain_vanilla_1a.js:231,271` | Strategie-/Monatsrandprüfungen | rechnet/liest indirekt | Produktionsstrategien | Teilweise | Bestehende Fälle, keine vollständige Kalenderlückenreferenz | Intern |
| `scripts/verify_plain_vanilla_1b.py:301,361,376`; `scripts/js/probe_plain_vanilla_1b.js:224` | Legacy-/Monthly-10-Snapshotvergleich | rechnet/liest indirekt | Produktionslogik gegen alte zeilenbasierte Referenz | Teilweise | Gleiche Zeilenlogik ist keine dritte Kalenderreferenz | Intern; Schutz veröffentlichter Zahlen |

**Belegte veröffentlichte Zahlen und lokale Altartefakte**

Die Markdown-Einträge ergänzen die verlangte Codebestandsliste um die tatsächlich betroffenen Veröffentlichungen.

| Datei:Zeile | Funktion | schreibt/rechnet/liest | Zählweise heute | Börse berücksichtigt? | Füllzeilen/Lücken berücksichtigt? | sichtbar wo |
|---|---|---|---|---|---|---|
| `blog/posts/2026-09-17_monthly-10-strategie.md:26,44,46`; `blog/posts/en/2026-09-17_monthly-10-strategy.md:27,45,47` | Feste Resultate und Bilder der Monthly-10-Studie | zeigt veröffentlichte Rechnung | Aus zeilenbasierter Referenz | Studie SPY | Keine neue Kalenderabnahme | **B** 32 Jahre, 1994–2025; Endwert, Rendite, Blockbeiträge |
| `blog/posts/2026-09-22_boersenregeln-nachgerechnet.md:43,126,200,209`; `blog/posts/en/market-rules-tested.md:44,127,201,210` | Wiederholte Monthly-10-Zahlen | zeigt | Dieselbe Studie | SPY | Wie Ursprungsstudie | **B** doppelte Veröffentlichung der Kennzahlen |
| `blog/posts/2026-07-31_spy-turn-of-month-down-monat-reversal-backtest.md:57,73,117`; EN-Datei `2026-07-31_spy-turn-of-month-down-month-reversal-backtest.md:58,118` | Feste Backtestresultate/Methodik | zeigt | Research-/Engine-Pfad zählt Mo–Fr | SPY; Text behauptet Börsenkalender | Feiertage fehlen im Ereignisgenerator | **B** Trades, Win-Rate, PF, Rendite, Drawdown |
| `blog/posts/2026-06-14_turn-of-month-effekt-lebt-noch.md:42`; `blog/posts/en/2026-06-14_turn-of-month-effect-still-alive.md:43` | `{{chart:tom_effect:^GSPC:20}}` | veranlasst Neuberechnung | Letzte/erste Monatskurszeilen | Nein | Nein | **B** dynamisch erzeugter Blogchart |
| `blog/posts/2026-04-09_turn-of-month-effekt-erklaert.md:29,33`; `blog/posts/en/turn-of-month-effect-explained.md:30,34` | Feste TDOM-/Reverse-TDOM-Ergebnisse | zeigt | Reproduzierbarer Ursprung im aktuellen Code nicht belegt | S&P 500 laut Text | Nicht nachgewiesen | **B** Tagesrenditen, Win-Rates, Bilder; eigene Herkunftsprüfung nötig |
| `pages/90_TDOM_Analyse.py:55,98,121,162,281,291,396,443,492` | Alte Streamlit-Charts, Stats-/Range-/Breakdown-Aufrufe | liest/rechnet | Gemeinsame Python-Zeilenlogik | Nein | Nein | **Ungetrackte lokale Altdatei**, abgeschaltete Anwendung |
| `daily_report_preview.html:66,75,261` | Gerenderte feste Mailvorschau | zeigt | Festes früheres Report-Ergebnis | Wie damaliger Report | Keine Neuberechnung | **Ungetracktes lokales Artefakt**, keine aktuelle Quelle |

Reine Navigation, SEO-Stichwörter, Metadaten und Styling-Treffer rechnen oder lesen keine Tagesnummern und sind deshalb keine zusätzlichen Rechenstellen. Ebenso sind CDOY, ISO-Wochennummern und gewöhnliche rollierende Fenster keine Monats-/Jahresordinalzahlen. Die separaten Arbeitsbäume unter `.claude/worktrees/` sind andere Checkout-Stände und wurden nicht als zusätzliche Produktionsstellen dieses Hauptarbeitsbaums gezählt.

## Antworten Fokusfragen

**1. V1–V5 tragfähig?**  
V1 ist mathematisch brauchbar; V2 braucht einheitliche Börsennamen, Gültigkeitsbereiche und Fehler-/Datentypverträge.  
V3 muss ausschließlich am Kalender entscheiden; `volume=0` oder gleicher Schlusskurs allein beweisen keine Füllzeile.  
V4: ausschließen und zählen ist richtig für eine unvollständig beobachtete Tagesrendite; nicht auf Sitzungen verteilen.  
Die Prüfung muss je Renditeart an den tatsächlichen Endpunkten ansetzen: drei Modi gehören zum früheren Tag (`shared/tdom_analysis.py:68,73`), Intraday braucht keinen Vorgängerkurs.  
Kurven dürfen beobachtete Endpunktbewegungen behalten; fehlende Positionen bleiben erkennbar, ohne erfundene Zwischenrenditen. V5 stimmt erst nach Entfernung des periodenfremden Header-Fallbacks (`landing/js/app.js:877`).

**2. Reihenfolge P2 vor P3/P4?**  
Als Implementierungsfolge möglich, als getrennte produktive Freigabe ungeeignet.  
P2 erzeugt kalenderbasierte aktuelle Zeilen, während historische Preise, Stats und Seiten noch alte Nummern verwenden (`scripts/nightly_refresh.py:105`, `landing/pages/dashboard.html:472`).  
P3/P4 können wiederum neue Nummern mit alten Tages-Stats kombinieren (`shared/cache_manager.py:142`).  
P1–P4 zunächst ohne Aktivierung vorbereiten; anschließend Schreibruhe, begrenzte P5-Korrektur, vollständige P6-Erneuerung und gemeinsamer Wechsel der Leser.  
Eine versionierte parallele Berechnung ist ebenfalls möglich, wenn alle Leser eindeutig dieselbe Generation auswählen.

**3. Welche Plain-Vanilla-Strategien und wie messen?**  
Direkt: Monthly 10 (`:453`), Ultimate Monthly (`:736`), KTI Long Only und KTI Leveraged über `_compute_kti_daily` (`:822`, `:923`, `:951`) in `shared/strategies/plain_vanilla.py`.  
Daneben alle in der Tabelle genannten n-ten/letzten Monatspositionen; nicht nur diese vier Strategien.  
Identische eingefrorene Kurse, Börse, Stichtag 31.12.2025 und Stop-/Hebeleinstellungen verwenden; alte und neue Trades nach Datum, Kurs, Rendite und Zustand vergleichen.  
Vollpräzise Abweichungen und Darstellung auf zwei Stellen berichten; hinzugekommene/entfallene Trades sowie Kennzahlen mit Fallzahlen ausweisen.  
Python und JS zusätzlich gegen unabhängige Kalenderendpunkte prüfen; `monthly10_blogzahlen.py:46` ist heute selbst zeilenbasiert.  
Blogtexte, DE-/EN-Bilder und Wiederholungen separat abgleichen; Ultimate/KTI sind derzeit Legacy-Verbraucher, nicht angebotene JS-Strategien.

**4. SQL-Editor oder SECURITY-DEFINER-RPC; Schreibruhe?**  
Der SQL-Editor genügt für den einmaligen, ausdrücklich freigegebenen Lauf, wenn sämtliche Prüfungen und das Update in derselben Transaktion liegen.  
Eine RPC ist dafür nicht erforderlich; mehrere REST-/RPC-Aufrufe ergeben keine gemeinsame Transaktion.  
Manifest mit eindeutigen Schlüsseln, alten NULL-sicher verglichenen Werten, erwarteten Änderungen und Referenzversion verwenden (`scripts/backfill_tdoy.py:133` erfüllt das noch nicht).  
Timer und manuelle Startmöglichkeiten sperren; laufende Services sowie Prozesse im Container müssen beendet sein (`deploy/systemd/sa-intraday.service:15`).  
Auch Completeness-Reparatur, Vollimporte, Onboarding und Deployment-Timeraktivierung berücksichtigen (`scripts/check_db_completeness.py:657`, `deploy/install_timers.sh:46`).  
Unmittelbar vor Commit Schlüssel, Treffer, neue Werte und Nichtzielspalten prüfen; jede Abweichung muss die Transaktion abbrechen.

**5. Was fehlt?**  
Ein Kalendervertrag für alle tatsächlich angebotenen Börsen/Jahre, einschließlich Forex/Krypto (`landing/js/holidays.js:206`).  
Rendite-Endpunkte vor analytischen Filtern sowie feldweise OHLC-Gültigkeit (`landing/pages/tdom-analyse.html:1181,1235`).  
Vollständiger Stats-Ersatz einschließlich backward, Methodenversion, `n_luecke` und Fehlerstatus (`scripts/nightly_refresh.py:137`, `shared/cache_manager.py:176`).  
Kalenderbasierte Monatsenden statt `max(beobachtet)` und korrekte Mailziele je Ticker (`plain_vanilla.py:487`, `daily_report.py:644`).  
Watchlist, Trifecta, Konverter, Research-/Blogpfade, neue Wächter und Krypto-Bereiche bis 31/366.  
Klare Trennung zwischen echten TDOY und interpolierter 252er Achse (`landing/js/decade-compute.js:69`).

## Befunde

1. **Hoch — Die beiden vorgeschlagenen Kalenderquellen erfüllen V1 derzeit nicht für denselben Börsenumfang.**  
   Python behandelt FOREX als Mo–Fr und CRYPTO als täglich; JS ordnet Forex und ausgewählte Kryptowährungen gemeinsam `NONE` zu. `NONE` bedeutet täglich. Explizite JS-Werte `FOREX`/`CRYPTO` werden dagegen nicht entsprechend unterstützt und fallen in die normale Feiertags-/Werktagslogik. Auch `AIR.PA` wird als NYSE erkannt. Belege: [Python-Kalender](/C:/dev/SeasonalEdge/shared/exchange_holidays.py:515), [JS-Zuordnung](/C:/dev/SeasonalEdge/landing/js/holidays.js:206), `holidays.js:226,259`.  
   Ausgeführt: Forex am Samstag 10.10.2026 ist in Python geschlossen, nach JS-Tickererkennung offen. Der vorhandene Zwillingstest deckt nur NYSE/XETRA 2000–2035 ab (`verify_kalender_zwilling.py:119`). P1 muss den tatsächlich aktivierten Umfang abdecken; P7 „Rest nur Bericht“ passt nicht zu einer vorherigen allgemeinen Umstellung dieser Leser.

2. **Hoch — V4 beschreibt für drei Produktionsstrategien den falschen Renditeanker.**  
   `open_to_next_open`, `open_to_next_close` und `close_to_next_close` speichern die Rendite auf der Ausgangszeile; der Zielkurs kommt aus `shift(-1)`. Bei fehlendem 3. Januar hängt die Rendite 2.→4. Januar daher am **2. Januar**. Ein Ausschluss nur auf der späteren Zeile trifft sie nicht. Intraday 4. Januar bleibt bei gültigem Open/Close auswertbar, auch wenn der 3. Januar fehlt. Beleg: [Renditeberechnung](/C:/dev/SeasonalEdge/shared/tdom_analysis.py:51).  
   Ausgeführt mit zwei Kurszeilen: Open 100 am 2. Januar und 110 am 4. Januar erzeugen 10 % auf dem 2. Januar. Vor P1 erforderlich: Endpunkt-, Sitzungsnachbarschafts- und Zählvertrag je Modus, einschließlich periodenübergreifender nächster Sitzung und noch nicht fälliger Endpunkte.

3. **Hoch — Analytische Filter und fehlendes Open verändern derzeit die wirtschaftliche Haltedauer.**  
   `/tdom-analyse` entfernt Indikatorzeilen vor `calcStrategyReturn`; schon beim Laden werden alle Zeilen ohne Open entfernt, auch für Close→Close. Belege: [Indikatorfilter](/C:/dev/SeasonalEdge/landing/pages/tdom-analyse.html:1181), `:1235`, `:390`.  
   Ausgeführt mit Opens 100, 101, 110 an drei aufeinanderfolgenden Sitzungen: Ausgangsrendite 1 %; nach analytischer Entfernung der mittleren Zeile 10 %. Das ist keine Quelldatenlücke. Rechenfolge festlegen: vollständige datierte Sitzungseingabe → Nummern/Endpunkte/Gültigkeit → Renditen → Auswahlmaske → Statistik. Gültigkeit muss von den benötigten Feldern des jeweiligen Modus abhängen.

4. **Hoch — P6 über den vorhandenen Nightly-Pfad erzwingt keine vollständige neue Statistikgeneration.**  
   Tagesaktuelle Cachezeilen werden ohne Prüfung der Rechenmethode übernommen (`cache_manager.py:142,198`). Nightly rechnet ausschließlich forward (`nightly_refresh.py:137,141`). Upsert entfernt verschwundene Gruppen nicht (`supabase_client.py:379,133`); leere Ergebnisse können alte Gruppen zurücklassen. Fehlgeschlagene Stats-Upserts werden abgefangen und als normale Rückgabe beendet (`cache_manager.py:176,232`).  
   Zudem fehlen `n_luecke` und eine Methodengeneration in DDL und Serialisierung (`create_market_tables.sql:83,102`). Erforderlich sind erzwungene Berechnung, vollständige Ersetzung je Ticker/Richtung/Strategie, nachvollziehbarer Datenstand und ein veröffentlichbarer Erfolgsstatus. Die Nightly-Yahoo-Historie und die von JS gelesene DB-Historie müssen hinsichtlich Zeitraum und Eingabepopulation ausdrücklich abgeglichen werden.

5. **Hoch — Neue Tagesnummern allein korrigieren die Strategie-Monatsenden nicht.**  
   Monthly 10, Ultimate Monthly und KTI verwenden weiterhin das Maximum **beobachteter** TDOM als Monatsende (`plain_vanilla.py:487,760,835`). Fehlt die letzte Sitzung, bleiben damit die falschen „letzten zwei“ aktiv. Am aktuellen Datenrand wird eine vorhandene Zeilenliste nur um zukünftige Sitzungen ergänzt; frühere Löcher werden nicht ergänzt (`plain_vanilla.py:465`, `strategy-compute.js:721`).  
   Historische n-te/letzte Terminhelfer bleiben ebenfalls zeilenbasiert (`plain_vanilla.py:228`, `strategy-compute.js:179`). Kalendertermine müssen zunächst unabhängig von Kursen feststehen. Ein fehlender Kurs am festgelegten Termin braucht einen ausdrücklichen fehlenden Zustand; eine andere vorhandene Zeile darf nicht dessen Platz übernehmen.

6. **Hoch — V5 bleibt selbst nach korrektem Rückschreiben im gemeinsamen Header falsch.**  
   An geschlossenen Tagen übernimmt der Header die letzte Kurszeile ohne Monats-/Jahresprüfung (`app.js:877`).  
   Ausgeführte Gegenprobe: 1.2.2026, SAP.DE, letzte Zeile 30.1.2026 mit korrektem TDOM 21 → **„TDOM 21/20“**. Nach V1 müsste der neue Monat 0/20 zeigen. Entsprechend kann am Jahresbeginn ein Vorjahres-TDOY übernommen werden. [Beleg](/C:/dev/SeasonalEdge/landing/js/app.js:826).  
   Die Anzeige muss das Datum des anzuzeigenden Kalenderstands verwenden. Nummern einer anderen Periode oder eines veralteten Datenstands sind keine gleichwertige Abkürzung.

7. **Hoch — Die Mail-Auswahl wird durch den Austausch der Zählhelfer allein nicht börsenspezifisch.**  
   `top_daily_tips` enthält US- und EU-Aktien, berechnet aber einen gemeinsamen NYSE-Ziel-TDOM und übergibt ihn an alle Kandidaten (`daily_report.py:696,712,644`). Die nachträgliche Anreicherung bewahrt diesen Selektionswert ausdrücklich (`:726`). Das widerspricht auch dem Template „Börsenspezifische TDOM je Ticker“ (`daily_report.html.j2:322`).  
   Weekly zählt Mo–Fr einmal außerhalb der Tickerschleife und sucht anschließend `current_tdom+offset` (`weekly_report.py:194,207`). Am Monatswechsel sind das keine nächsten fünf Sitzungen. Kalenderdaten je Ticker vorwärts erzeugen und daraus jeweils Monat/TDOM bestimmen; verfügbare Fallzahl und fehlende Gruppen ausweisen.

8. **Mittel — Der Krypto-Vertrag verliert weiterhin gültige Tage durch Aktiengrenzen.**  
   Python-TDOM-Stats akzeptieren nur ±23 (`tdom_analysis.py:115`), JS-TDOM-Stats ebenfalls nur den Aktienbereich; JS-TDOY beendet bei 260 (`tdom-analyse.html:837`). Range-Eingaben sind auf ±23 begrenzt (`:126`).  
   Ausgeführt: 31 tägliche Januarkurszeilen ergeben im bestehenden Python-Builder nur 23 Tagesgruppen. V1 verlangt bei Krypto jedoch bis 31 Monats- und 365/366 Jahrestage. Grenzen, reverse-Bereiche, Eingaben und Beschriftungen müssen aus dem unterstützten Kalender folgen.

9. **Hoch — P2 kann die historische Begrenzung von P5 umgehen und enthält nicht alle Schreiber.**  
   Bulk-Import fehlt in P2 (`bulk_load_supabase.py:134,254`). Der bestehende `backfill_tdoy` schreibt vollständige Historien und dabei auch `close` per Upsert (`backfill_tdoy.py:133`). Completeness kann diesen Pfad automatisch anstoßen, einschließlich einer vermeintlichen Stats-Reparatur (`check_db_completeness.py:642,657,668`).  
   Die Grenze ab 2001, Börsenfreigaben und Nutzerfreigabe dürfen deshalb nicht nur im neuen P5-Skript stehen. Sie müssen alle historischen Schreibaufrufe begrenzen. Normale neue Schreiber dürfen nicht unbemerkt eine historische Migration auslösen; P5 selbst braucht ein Update ausschließlich der freigegebenen Nummernspalten.

10. **Mittel — P3/P4 und die Wirkungsmessung lassen weitere öffentliche Rechenwege aus.**  
    Watchlist, beide JS-Trifecta-Rechnungen, Python-Trifecta/Kaeppel, Konverter, ML-/Research-Terminerzeuger und Video-Monatskurven fehlen in der Phasenliste; die Bestandsliste benennt sie. `decade-compute.js` ist dabei falsch als TDOY-Spaltenleser eingeordnet: Es transportiert die Spalte, interpoliert aber Kurszeilen auf 252 Punkte (`:69,542`).  
    Beim Konverter ist zusätzlich ein realer Kalenderfehler bestätigt: Europe/Berlin, 1.1.2026 wird als offen, 2.1.2026 als geschlossen erkannt, weil lokaler Wochentag und UTC-Datum vermischt werden (`trading-day-converter.html:256`). Für die 252er Achse muss ausdrücklich entschieden werden, ob sie eine normalisierte Position bleibt oder durch echte Tagesnummern ersetzt wird; sie darf nicht als echte TDOY ausgegeben werden.

11. **Hoch — Timerstopp und Trefferzahl allein beweisen weder Schreibruhe noch die richtige Migration.**  
    Manuelle Workflows starten die Services auch ohne Timer (`nightly_refresh.yml:28`, `intraday_update.yml:27`). Das Intraday-Service dokumentiert selbst, dass ein beendeter äußerer Prozess nicht zwingend den Containerprozess beendet (`sa-intraday.service:15`). Deployment aktiviert/startet Timer wieder (`install_timers.sh:46,54`). Weitere historische Schreiber stehen in Befund 9.  
    Vor dem Lauf braucht es belegte Sperrung der Startwege, leere aktive Schreibprozesse, Prüfung der tatsächlich installierten Trigger und einen stabilen Quelldatenstand. In der Transaktion: eindeutige Manifestschlüssel, NULL-sichere alte Sollwerte, geeignete Sperre gegen konkurrierende Änderungen, Kontrolle der aktualisierten Schlüssel und Zielwerte sowie Nachweis unveränderter Nichtzielspalten. PostgreSQL zählt auch Updates ohne Wertänderung; mehrfach passende `FROM`-Zeilen sind nicht eindeutig. [PostgreSQL-Dokumentation](https://www.postgresql.org/docs/current/sql-update.html). Eine einzelne RPC könnte die Transaktion kapseln; mehrere Requests tun das nicht. [PostgREST-Transaktionen](https://docs.postgrest.org/en/stable/references/transactions.html).

12. **Mittel — Die alten Wächter widersprechen dem neuen Vertrag; die dritte Referenz braucht einen klaren Umfang.**  
    Die Prüfungen `verify_calendar_rules.py:306,313` und `verify_tdoy_2026_08.sql:12` erwarten +1 zwischen benachbarten Kurszeilen. Nach V1 muss bei fehlender offener Sitzung dagegen +2 oder mehr möglich sein; eine erste vorhandene Monatszeile muss nicht TDOM 1 haben. Diese Wächter müssen vor Aktivierung angepasst werden.  
    NumPy ist eine geeignete unabhängige **Zählalgorithmus**-Referenz, aber bei derselben Feiertagsmenge keine unabhängige Kalenderquelle. `busday_count` schließt das Enddatum aus; für Vorwärtszahlen muss der Endpunkt deshalb `d+1` sein, für rückwärts das exklusive Periodenende. [NumPy-Dokumentation](https://numpy.org/doc/stable/reference/generated/numpy.busday_count.html).  
    Ausgeführt: XETRA 4.10.2018 ergibt `(3,193)`; der offizielle Kalender bestätigt die beiden genannten Schließungen. [Handelskalender 2018](https://www.cashmarket.deutsche-boerse.com/resource/blob/154422/d8296c92db56d4ae96997246ab54d4ae/data/handelskalender-2018.pdf). Zusätzlich nötig: feste offizielle Fälle, passende Forex-/Krypto-Wochenmasken, Rückwärtszahlen, Periodenanfang, Teilhistorie, mehrere Ticker, Füllzeilen und gezielte gültige Mutationen. Mutationsläufe wurden hier wegen des Schreibverbots nicht ausgeführt.

## Auflagen vor P1

- **Unterstützten Umfang festlegen:** einheitliche Börsenkennung je Sprache, dokumentierte Zuordnung je Ticker sowie geprüfte Börsen-/Jahresbereiche; Verhalten außerhalb dieses Umfangs ohne stillen NYSE- oder Mo–Fr-Ersatz.
- **V2 präzisieren:** Datumstyp und Zeitzonenbehandlung, Reihenfolge/Zuordnung der Rückgabe, Mehrticker-Aufrufe, leere Eingaben, ungültige Daten sowie Fehlerbehandlung festlegen; vorhandene Namen `*_reverse` ausdrücklich adaptieren.
- **V3 präzisieren:** Kalender entscheidet über geschlossene Tage; unveränderte Kurse oder Nullvolumen auf einer offenen Sitzung bleiben grundsätzlich echte Beobachtungen.
- **V4 je Renditeart definieren:** Ankerdatum, benötigte OHLC-Felder, erwarteter Endpunkt, periodenübergreifende Nachbarschaft, fehlender versus noch nicht fälliger Kurs und Bedeutung von `n_luecke`; analytische Filter verändern keine Endpunkte.
- **Kurvenvertrag ergänzen:** echte Kalenderpositionen, beobachtete Endpunktwerte, erkennbare fehlende Positionen und Fallzahlen; Tagesstatistik und kumulierter Pfad verwenden unterschiedliche, ausdrücklich benannte Gültigkeitsregeln.
- **Strategietermine ergänzen:** ganze Monatskalender und Rückwärtszahlen statt beobachteter Maxima; fehlende Kurse am festgelegten Termin nicht durch andere Kurszeilen ersetzen.
- **Bestandsliste in P2–P4 übernehmen:** insbesondere Bulk-Import, Watchlist, Trifecta, Konverter, Mail-Auswahl, Research-/Blogproduktion, harte Tagesgrenzen und vorhandene Wächter.
- **Stats-Migration entwerfen:** Methodengeneration, `n_luecke`, erzwungene Berechnung beider Richtungen/all­er unterstützten Modi, vollständiger Gruppenersatz, definierter Eingabestand und nicht erfolgreicher Exit bei fehlgeschlagener Speicherung.
- **Gemeinsame Aktivierung festlegen:** P2–P4 nicht einzeln mit gemischten Generationen produktiv schalten; P5/P6 und Leserwechsel als überprüfbaren Übergang planen.
- **Historische Grenzen auf alle Schreibpfade anwenden:** automatische Reparatur und Vollimporte dürfen P5-Freigaben nicht umgehen; für vor 2001 gelesene Historien den Kalendernachweis beziehungsweise die Einschränkung der veröffentlichten Aussage festlegen.
- **Veröffentlichungsabgleich festlegen:** eingefrorene Trades bis Ende 2025, unabhängige Kalenderendpunkte, Vollpräzisions- und Zwei-Stellen-Vergleich, Kennzahlen mit Fallzahlen sowie DE-/EN-Texte, Bilder und wiederholte Blogzahlen.
- **P5-Abnahme konkretisieren:** freigegebenes eindeutiges Manifest, belegte Schreibruhe, tatsächliche Triggerprüfung, NULL-sichere Sollwertbedingungen, transaktionale Schlüssel-/Wertprüfung und unveränderte Nichtzielspalten; Ausführung weiterhin erst nach ausdrücklicher Nutzerfreigabe.
