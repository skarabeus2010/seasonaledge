# Code-Review Stress-Ampel, Runde 1

Repo `C:\dev\Seasonaledge`, Arbeitsstand (uncommittet) auf `95209ec`. Plan: `docs/review_prompts/2026-10-09_stress_ampel_plan.md`
(v5, deine Freigabe in Runde 5; Antworten `..._plan_antwort1-5.md`). Prüfe die Umsetzung gegen den Plan und auf neue Fehler.
Antwort auf Deutsch: je Befund Schwere + Datei:Zeile + konkreter Eingabefall + Änderung; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`. Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
Snapshot: `C:/Users/HEIKOS~1/AppData/Local/Temp/claude/c--dev-Seasonaledge/b1245851-7084-4449-b6ab-61b4ed04fde7/scratchpad/pv_kurse`.

## Umsetzung
- **Rechnung:** `shared/stress_score.py` (`bereinigen`, `stress_reihe`, `stress_aktuell`, `ampel`, `anzeige`, `lade_kurse`,
  `stress_fuer_ticker`, `sollmenge`, `vollauf`, `lese_lauf`, `aufraeumen`, `letzter_fertiger_lauf`); JS-Zwilling
  `landing/js/dash-compute.js` (`stressReihe`, `computeStress`, `stressAmpel`, `stressAnzeige`, `stressAnzeigeWerte`,
  `STRESS`), gleiche Rechenreihenfolge. Sortiertes Fenster per Bisektion, Abbau von S_{t−2520} nach dem Einfügen von S_t.
- **SQL:** `scripts/sql/stress_scores_schema_2026_10.sql` (noch nicht ausgeführt — der Nutzer führt sie vor dem Deploy im
  SQL-Editor aus): `stress_laeufe` (partieller Unique-Index `WHERE status = 'laeuft'`, Lease 30 min), `stress_scores`
  (double precision, PK `(lauf_id, date)`), Funktionen `stress_lauf_starten` / `_veroeffentlichen` / `_abbrechen`
  (SECURITY DEFINER, EXECUTE nur service_role, Abbrechen nur aus `laeuft`), RLS anon SELECT.
- **Schreiber:** `scripts/compute_regime_scores.py` (Vollauf, `--trocken`), `scripts/nightly_refresh.py` Phase E
  (`vollauf("SPY")`), beide ohne sklearn. `shared/anomaly_engine.compute_market_regime` leitet auf `stress_aktuell` um.
- **Leser:** `landing/pages/crash-fruehwarnung.html` (Titel/Meta/JSON-LD/FAQ/Texte neu, Kurse ab heute − 13 J.,
  `stressAnzeigeWerte`: DB nur bei Lückenlosigkeit bis zur letzten Kurszeile), `dashboard.html` (Inline-Kopie entfernt,
  `dash-compute.js` eingebunden, „zu kurze Historie"), `watchlist.html` (Summe „x / y berechenbaren", Nullwerte),
  Wochenreport `shared/weekly_report.regime_status` live über `stress_fuer_ticker` + Template, Health-Check Check 6
  (Nachrechnung der letzten Zeile), Completeness (`stress_scores` statt `regime_scores`, keine Universumsabdeckung),
  `scripts/verify_security.py` (neue Tabellen öffentlich lesbar). Namen: Nav/Footer/Startseite/Tour/Pricing/flows/llms,
  i18n DE+EN (`_JSON_VER` v9; die Seite ist DE-only).

## Belege
- `scripts/verify_stress_ampel.py --snapshot …` **29/29**: Python und JS gegen eine dritte, naive Referenz
  (`statistics.stdev`, Rang per Schleife) auf einer Zufallsreihe mit Gleichständen; 776/777; Fenster 2520; ungültige
  Kurse; konstant (Score 50); monoton fallend (S = 0,4·|dd20|); Präfixinvarianz; aktuell = letzte Zeile; Grenzen und
  Anzeige inkl. float32; Anzeige-Regel DB/Browser; DB-Fake mit den SQL-Regeln (Erfolg, Kurskorrektur + entfernte
  Kurszeile → neue Sollmenge, Batchfehler mitten im Lauf, Rücklesefehler, Lease, Sperre + Übernahme, verlorene Antwort nach
  Veröffentlichung, Aufräumen mit laufendem Lauf, Zählabweichung und Netzwerkfehler ohne Write, Längen 0/6/20/21/29/777,
  veraltet); statische Prüfungen; Snapshot: Python = JS an jedem Tag auf fünf Tickern, Plausibilitätsdaten.
- `--mutationen` **20/20**, 3/3 untaugliche verworfen.
- Schreibender Live-Test der SQL-Funktionen `scripts/verify_stress_sql_live.py` (Ticker `__TEST__`, räumt immer auf) —
  läuft nach dem Anlegen der Tabellen auf dem Server.
- Unabhängig von deiner Rechnung aus Plan-R1: Anteile SPY 66,68/20,02/13,30 %, SPY 07.10.2026 = 25,75 — identisch.
- `verify_en.py` FAIL 0, `verify_seo_html.py` 0 Fehler, `verify_security.py` unverändert gegenüber dem Stand vorher
  (8 bekannte, vorbestehende Befunde aus dem Sicherheits-Audit, keiner davon neu).
- Einordnung (nicht auf der Seite): Rückgang ≥ 10 % binnen 20 Sitzungen nach Rot 15,0 % (SPY, 154/1025), Basisrate 4,3 %
  (333/7684); ^GSPC 13,4 % vs. 4,0 %; ^GDAXI 17,4 % vs. 5,0 %; überlappende Tage abhängig.

## Ablauf nach Freigabe (bitte mitprüfen)
1. Nutzer führt die SQL-Datei aus. 2. Commit/Push/Deploy. 3. Auf dem Server `verify_stress_sql_live.py`, dann
`compute_regime_scores.py --ticker SPY` (Vollauf), Rücklesen. 4. Seite live prüfen. Bis Schritt 3 zeigt die neue Seite die
Browserrechnung (Tabelle leer), `regime_scores` bleibt unangetastet.

## Bewusst offen
Blogartikel mit veralteten Aussagen über die Ampel (Plan P, Nutzerentscheidung). `regime_scores` löschen (später).
Watchlist zeigt `vol_20d` als „%" ohne Annualisierung (vorbestehend, nicht Teil dieser Änderung).
