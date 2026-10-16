# Code-Review B3b: IV/RV-Verhältnis + neutrale Extremlisten

Plan (freigegeben R2): `docs/review_prompts/2026-10-16_options_b3b_plan_v2.md` + `…_plan_antwort2.md` (P3: die tiefe
Liste nimmt nie einen Ticker der hohen — umgesetzt). Code uncommittet im Arbeitsbaum (`git diff`). Read-only, Deutsch,
**FREIGABE (Code): ja/nein**, Befunde P1/P2/P3.

## Dateien
- `shared/skew_rang.py`: `ivrv_wert` (iv_atm > 0, rv_1m ≥ 0,01, Typen), Metrik `ivrv` aus GESPEICHERTEM `rv_1m`,
  `_zusatz` (neu_rand strikt aus den Werten, vorher_datum = letzter gültiger Wert, sprung/sprung_beurteilbar mit
  Median über ALLE Änderungen einschließlich der aktuellen), `status_ticker`/`rang_status_gesamt` (zu_kurz, kein_wert,
  gesperrt), `_im_fenster` (eine Fensterregel für Rang und Status). `rang` bleibt im B3a-Format, nur um Felder ergänzt.
- `scripts/js/skew_rang_ref.js`: unabhängige Referenz derselben Verträge (`mit_status` liefert {rang, status}).
- `scripts/compute_options_skew.py`: `rv_1m` in die History-Zeile (nur an normierten Tagen), `ivrv` je Ticker in den
  Snapshot (nur mit `cm_mode`, aus `cm_iv_atm`), `rang_status` neben `rang`.
- `landing/pages/skew.html`: Spalte IV/RV nach VRP (Wert „1.25×“, Tooltip Rang/Percentile/n oder Statusgrund),
  Block „Am Rand der eigenen Historie“ unter dem Radar (vier Metriken × höchste/niedrigste 8, immer nach Percentile,
  Gleichstand nach Ticker, tief ohne Überschneidung, Kategorie-Filter, Markierungen neues Hoch/Tief und „Sprung zum
  letzten gültigen Wert (Datum) — Messung prüfen“, Aufbauhinweis für IV/RV, Datenstand der Session, `SKEW_STATUS` nur
  mit Rang derselben Session); neu gezeichnet bei Fenster/Kategorie/Modus/Wörterbuch und mit jedem Snapshot.
- `landing/i18n/en.json` (+18 Keys), `landing/js/i18n.js` `_JSON_VER` v17 → v18.
- Tests: `scripts/verify_skew_rang.py` (Abschnitte 1b, Cron, 3b), `scripts/js/probe_skew_rang_seite.js` (Kategorie und
  Zweit-Snapshot per Umgebung; `renderSkew` wird für den Test aus dem IIFE gereicht, Logik unverändert),
  `scripts/verify_skew_rang_mutation.py` (+20 B3b-Mutationen).

## Was ich bewusst so gemacht habe
- Die Listen lesen nur `rang` (Percentile ist dort schon das Fenster des Tickers); keine Browser-Rechnung.
- `vorher_datum` wird immer gezeigt, nicht nur wenn es nicht die Vorsession ist (die Seite kennt keinen Kalender).
- IV/RV-Werte „1.25×“ mit Punkt (wie die übrigen Tabellenzahlen der Seite).
- Live erwartet: IV/RV-Rang zunächst bei keinem Ticker (rv_1m erst ab dem nächsten Cron gespeichert) → Aufbauhinweis.

## Bitte besonders prüfen
1. Zwilling Python = JS für alle neuen Felder inkl. Status (Test vergleicht beide Ausgaben vollständig).
2. Ob ein B3a-Leser (Mail `skew_pctl_map`, /skew Radar/Spalten) durch die Zusatzfelder anders reagiert.
3. HTML-Ausgabe der Liste: Werte stammen aus der eigenen Datei, Ticker sind Symbole aus dem Universum — trotzdem:
   fehlt eine Maskierung, die nötig wäre?
4. Lücken in den Tests gegen die Verträge aus Plan v2.

## Prüfstand
`verify_skew_rang.py` grün, Mutationstest **41/41** (davon 20 B3b; eine B3b-Mutation „Median ohne aktuelle Änderung“
war im ersten Lauf unbemerkt → Fall `median_mit_aktueller` ergänzt; die Duplikatprüfung liegt jetzt in `_doppelt`,
die Fensterregel in `_im_fenster`, damit Rang und Status je eine Regel teilen).
Live-History (Session 15.10., lokal, nichts geschrieben): 150 Ticker mit Rang; Sprungmarken skew/rr 11 · 5 · 6, iv
4 · 3 · 3 (3 M · 6 M · 1 J), neuer Rand skew/rr 15 · 6 · 2; ivrv überall `kein_wert` (noch kein gespeichertes rv_1m).
