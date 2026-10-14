# Entwurf v2: Options-Sofortreparaturen + Radar-Standard Percentile — Runde 2 (Plan)

Read-only, Repo `C:\dev\Seasonaledge`, `d944a26` + ungetrackt `scripts/research/basisabweichung_diagnose.py`. Deine
Runde 1: `docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_antwort1.md`. Deutsch, Datei:Zeile,
**FREIGABE (Plan): ja/nein** — gern getrennt je R.

## R1 — Basisabweichungen / ETHA
**R1a erledigt (Server, nur lesen, `scripts/research/basisabweichung_diagnose.py`):** alle 370 Ticker aus
`symbols.get_all_tickers()`, Fenster 2024-10-14 … heute mit Vorgänger ab 2024-10-01, vollständige Pagination:
191 146 Zeilen, 187 813 Paare, **0** ohne `log_return`, 0 ungültige Kurse, 1 Lücke > 7 Kalendertage.
**Genau eine Basisabweichung** (|ln(c_t/c_{t−1}) − log_return_t| > 0,05): ETHA 2026-09-30, Schluss 20,28 → 60,36,
log_return −0,0079; beobachteter Basissprung ×3,0, Korrekturfaktor für **ältere** Kurse auf die neue Basis ×3,0.
Als Basisabweichung geführt, Ursache (Reverse-Split 1:3) laut Kursverlauf bei Yahoo plausibel, nicht separat belegt.

**R1b (Erzeuger):** neuer gemeinsamer Lader `shared.data.lade_kurse(ticker, ab, mindestens)` → (daten, closes,
log_returns); `lade_closes` bleibt als Hülle (nur closes) für bestehende Leser. RV = `realized_vol.rv_aus_returns`
über die **gespeicherten** `log_return` (explizite Prüfung NaN/Inf/None → Fenster ohne RV, nicht überspringen, nicht
aus Kursen ersetzen); `last_close`/`close_datum` bleiben Spot aus `close`. Gleiche Regel in: `compute_options_skew._realized_vol`
(:277), `backfill_skew_vrp.py` (:125), `backfill_skew_massive.py` (:198, nur falls dort RV entsteht — sonst nur Spot,
unverändert), `shared/intermarket.py` (:64, Returns für das Briefing-Signal). Keine automatische Kursreparatur in
`lade_closes`.
**R1c (Bestand):** **kein** Neuladen der ETHA-Kurse — die Schlusskurse vor dem 30.09. sind die damals gehandelten
Preise und dienen im Backfill als Spot-Anker der IV-Rekonstruktion; sie zu ändern würde die Skew-Historie
verfälschen. Stattdessen: ETHA-History-Zeilen ab 2026-09-30 bis zum Ende des 21-T.-Fensters (≈ 2026-10-28):
`vrp_pts` aus RV(log_return) neu rechnen, und zwar durch das bestehende `backfill_skew_vrp.py` mit neuer Regel,
Trockenlauf zuerst (Diff je Zeile), Schreiben nur ETHA, unter der Dateisperre des Skew-Crons (s. R3). `options_skew.json`
erneuert sich mit dem nächsten Cron.
**R1d (Wiederholung verhindern):** der Health-Check bekommt eine Basisabweichungs-Prüfung (dieselbe Regel, letzte 30
Tage, alle Ticker) → gelb mit Ticker/Datum/Faktor; kein automatischer Eingriff.
Wächter: Kursreihe mit ×3-Sprung bei korrektem log_return → RV plausibel und = RV der bereinigten Reihe; None/NaN im
Fenster → keine RV; Spot = letzter Rohschluss. Mutationen: RV wieder aus closes; None übersprungen; Spot aus
bereinigter Reihe.

## R2 — Session-Stempel
- `compute_options_skew.py:1204` `pc_ratio.date` = dieselbe einmal ermittelte Session wie `out["session"]`; `generated`
  bleibt Lauftag.
- `snapshot_gex_massive.py:231`: `stamp` = Session aus `letzte_session()` **plus EOD-Wächter**
  (`exchange_holidays.pruefe_eod_fenster` o. ä.: läuft der Snapshot vor US-Schluss, bricht er ab statt einen
  Intraday-Stand als Vortag-EOD zu stempeln; `--snapshot <datum>` für Archivläufe bleibt). Feld `stempel_art:
  "session"` in Summary, Profilen, Archiv.
- **Archiv:** Altdateien `landing/data/gex_history/<lauftag>.json` bleiben unverändert; neue Dateien unter
  `landing/data/gex_history_session/<session>.json` (gitignored wie das alte). Keine Migration.
  Leser: `scripts/compare_flashalpha_gex.py:118` liest beide Ordner, bevorzugt `gex_history_session`, kennzeichnet die
  Herkunft. `snapshot_gex.py:107` (alternativer Schreiber): gleiche Stempelregel — bitte prüfen, ob er noch läuft;
  wenn nicht, nur Kommentar.
- `daily_health_check.py:431` GEX-Frische: vergleicht künftig `date` mit der erwarteten Session statt mit „heute“.
- `/dealer-positioning` (`:316`) zeigt dann „Stand: <Session> (EOD)“ korrekt; keine Codeänderung nötig.

## R3 — eine Rangrechnung im Cron, für alle Fenster
**Spezifikation (Python, `shared/skew_rang.py`, neu):**
- Eingabe: History eines Tickers (nach dem Zusammenführen des heutigen Punkts), Session S, Fenster W ∈ {92, 183, 365}.
- Zeilen: `date ≥ S − W` (Kalendertage, Anker = **Session**, nicht Uhr) und `cm_mode ∈ {cm, cm_extrap}`.
- Metriken je Zeile: `rr = call_iv − put_iv`, `iv = (put_iv + call_iv)/2` (wie Seite, **nicht** ATM), `skew = skew_pts`,
  `cz = call_zeta_pts`, `pz = put_zeta_pts` (Zeta nur mit `iv_atm`, sonst wie `skew.html:351` aus iv_atm abgeleitet,
  ohne Antidiagonal-Näherung).
- Je Metrik **erst** auf gültige Werte filtern, **dann** Session-Regel: letzter gültiger Wert muss Datum = S haben,
  sonst kein Wert (kein Nachrücken älterer Tage); n ≥ `MIN_NORM` = 20 (Zeta-Paare: n Paare ≥ 20).
- Rank = (x_S − min)/(max − min)·100, bei max = min → 50; Percentile = #{x_i < x_S, i < S}/(n−1)·100. Rundung
  „halb nach oben“ wie `Math.round` (`floor(v + 0.5)`), nicht Python-`round`.
- Ausgabe in `options_skew.json`: `rang[ticker][W] = {n, rr:{rank,pctl}, iv:{…}, skew:{…}, cz:{…}, pz:{…}}` + oben
  `rang_session = S`. Fehlt etwas → Feld fehlt (Leser zeigen „—“).
- Reihenfolge im Cron: History zusammenführen → Rang daraus → **erst dann** beide Dateien schreiben (History zuerst,
  dann Snapshot, beide atomar); bisher wird der Snapshot vorher geschrieben (`:1221`).
**Leser:** `/skew` liest `rang` für das gewählte Fenster (Radar beider Ansichten, Tabellenspalten), rechnet in
Produktion nichts mehr selbst; die bisherige JS-Rechnung wandert in `scripts/js/` als Referenz für den Zwillingstest.
Die Seite verwirft `rang`, wenn `rang_session` ≠ `session` der Datei (veraltete Gesamtdatei → „—“). Mail:
`daily_report.skew_pctl_map` liest `rang[t]["365"].skew.pctl`; `skew_map` unverändert. Template `:115` einfarbig
(neutrale Klasse), fehlendes Perzentil sichtbar „—“, Tooltip „Put-IV relativ zur Call-IV im Vergleich zur eigenen
Historie (hoch = ungewöhnlich hoch)“.
**Zwilling:** Python `skew_rang` = JS-Referenz auf Fixtures: konstante Reihe, Gleichstände, Halbwerte (x,5), 19/20
Punkte, Fenstergrenze genau S−W, fehlender aktueller Messwert (eine Metrik), veraltete Datei, Zeta ohne iv_atm.
Mutationen: Uhr statt Session, Filter-nach-Session, `round` statt halb-nach-oben, n ≥ 19, ATM statt Flügelmittel.
**Sperre:** alle Schreiber von `options_skew_history.json` (Cron, `backfill_skew_massive`, `backfill_skew_vrp`,
Migrationen) nehmen eine gemeinsame `flock`-Sperre über **Lesen → Zusammenführen → Schreiben**
(`shared/atomic_json` bekommt den Helfer); bitte prüfen, ob das hier schon nötig ist oder ins Skew-Ausreißer-Vorhaben
(Phase 3) gehört.

## R4 — Earnings
Mailblock `shared/daily_report.py:943-966` entfernen (Kommentar mit Grund). Folgeposten (nicht Teil dieser Stufe):
`landing/pages/earnings-kalender.html:256`, `landing/js/kalender-compute.js:124`, Vollständigkeitsprüfungen — dieselbe
falsche Semantik; in `docs/OPTIONS_OFFEN_2026-10-13.md` notiert. Wächter: Mail-Ereignisliste enthält nichts aus
`earnings_events`.

## R5 — Radar Standard Percentile
`skew.html:222` → `'pctl'`; Untertitel `:285` und `en.json:1540` (`skew.quad_sub`, `skew.quad_sub_cs`) nennen den
Modus dynamisch (DE/EN, auch nach Umschalten und Sprachwechsel); `_JSON_VER` erhöhen. Blog DE/EN „Vol-Regime-Radar“
(`:106`/`:107`): veraltete 2J-Fensterangabe korrigieren, `updated:` setzen.

## Reihenfolge / Deploy
Paket 1 (klein): R5, R4, R2, R1b+R1d. Paket 2: R3. R1c nach Paket 1 (Trockenlauf → Nutzer). Wirkungsbericht vor
jedem Push auf eingefrorenen Eingaben: Mailspalte alt/neu, Radarpositionen Rank/Percentile je Fenster, Ausfälle,
Quadrantenwechsel.
