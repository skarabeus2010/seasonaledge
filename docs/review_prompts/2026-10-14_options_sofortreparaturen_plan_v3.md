# Entwurf v3: Options-Sofortreparaturen, Rest (Schreibsperre, R1c, R2, R3) — Plan

Read-only, Repo `C:\dev\Seasonaledge`, Stand `4732437` (Paket A live: `1c0412f`). Deine Antworten:
[Plan v2](2026-10-14_options_sofortreparaturen_plan_v2_antwort.md) (R1b/R1d/R4/R5 frei, R1c/R2/R3 nein),
[Code R1](2026-10-14_options_paket_a_code_antwort1.md), [Code R2](2026-10-14_options_paket_a_code_r2_antwort.md).
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`, `PYTHONUTF8=1`.
Deutsch, Datei:Zeile, **FREIGABE (Plan): ja/nein je Paket**.

## Neue Befunde seit v2 (beim Lesen für diesen Plan)

1. **Unlesbare History wird zur leeren und überschrieben.** `compute_options_skew.py:1238-1240`,
   `backfill_skew_massive.py:851-855`, `backfill_skew_history.py:148-150`: `except Exception: hist = {}`, danach
   `write_json_atomic` → die ganze Radar-Historie wäre durch die Punkte eines einzigen Laufs ersetzt. `atomic_json`
   verhindert halbe Dateien, aber nicht diesen Pfad (z. B. Speicher voll beim vorigen Schreiben, manuelles Editieren,
   ein künftiger Schreiber ohne atomares Schreiben).
2. **GEX-Archiv ist systematisch eine Session zu spät gestempelt — belegt.** Server: `gex_summary.json`
   `"date": "2026-10-14"`, `"generated_at": "2026-10-14T01:21:24+00:00"` → Daten der Session 13.10. Archivnamen
   `2026-10-10.json` (Sa) und `2026-10-13.json` (Di) usw. Der GitHub-Cron `15 22 * * 1-5` startet regelmäßig nach
   Mitternacht UTC. Betriebsprüfung zu `snapshot_gex.py` (v2-Auflage): Crontab des Hosts ohne GEX-Eintrag, keine
   `sa-*`-Unit dafür, kein Workflow → **nur `snapshot_gex_massive.py` läuft**.
3. **Dieselbe Bewertungsdatum-Frage** in `compute_key_levels.py:61/76` und `compute_iv_surface.py:68/87`
   (`date.today()` für Horizont und DTE). `compute_options_flow.py:98/335` macht es bereits richtig (Muster).
4. **Verfall am Sessiontag hängt von der Uhrzeit ab:** `snapshot_gex_massive._map` verwirft `dte < 0`. Läuft der Cron
   vor Mitternacht UTC, bleiben am Session-Tag verfallene Kontrakte mit `T = 1e-6` drin (Gamma maximal), danach nicht.
   Dieselbe Session ergibt je nach GitHub-Verzug andere Walls/Flip — besonders freitags (Wochenverfall).

## Paket B1 — Schreibsperre der Skew-History (vor allem anderen) + R1c

**Helfer** `shared/atomic_json.py::history_aktualisieren(pfad, aendern, *, sperre, frist_s=600, neu_erlaubt=False)`:
1. `flock(LOCK_EX)` auf eigener Sperrdatei `logs/sperre/skew_historie.lock` (gleicher Mount wie
   `logs/sperre/produktion.lock`, also Host + Container); Wartezeit `frist_s`, danach `SperreBelegt` (Exit ≠ 0, nichts
   geschrieben). Unter Windows (nur lokale Tests) explizit `ungeprüft`-Modus mit Warnung; die Parallelität wird nur unter
   Linux (Gate) geprüft, Gate verlangt `--streng`.
2. **Unter der Sperre frisch lesen.** Fehlt die Datei → nur mit `neu_erlaubt` `{}`; unlesbar/kein dict → `HistorieDefekt`,
   nichts geschrieben (Befund 1).
3. `aendern(hist)` auf dem frisch gelesenen Stand, danach `write_json_atomic`, dann Sperre lösen.
4. Optional `danach(hist)` noch unter der Sperre (für den Cron: Snapshot schreiben, siehe R3).

**Schreiber umstellen:**
- `compute_options_skew.py` (Cron): Zeilen je Ticker werden wie bisher außerhalb gerechnet; unter der Sperre:
  `_fix_session_dates`, Zusammenführen (Regel „rankbar ersetzt nicht-rankbar“ unverändert), `__CORR`/`__PCR`, Schreiben —
  und (ab B3) Rang + Snapshot. Sperre bis nach dem Snapshot gehalten (deine Auflage).
- `backfill_skew_massive.py`: `run_ticker` trennt **Rechnen** (`rekonstruiere(sym, …) → neue Zeilen, n_purge`) von
  **Anwenden** (`anwenden(arr, neue, overwrite) → arr`, rein, heute Zeilen 436-487 inkl. Purge `src=="massive"`,
  Abbruch bei 0 Punkten, Dedup „neue gewinnt“, Kappung 900). Je Ticker: rechnen ohne Sperre, dann
  `history_aktualisieren` mit `anwenden` auf dem **frischen** Stand — keine alte Gesamtstruktur mehr zurückschreiben.
  `have`/`todo` aus einem frischen Lesen vor dem Rechnen (nur Planung, kein Schreiben).
- `backfill_skew_vrp.py`: RV je Ticker/Datum ohne Sperre laden; Anwenden der VRP-Felder (und Gate-Statistik) unter der
  Sperre auf dem frischen Stand. Das Gate rechnet über die Zeilen, die tatsächlich geändert würden.
- `backfill_skew_history.py` (marketdata, seit v53 stillgelegt): Schreibweg über denselben Helfer **und** ohne
  `--ich-weiss-dass-stillgelegt` Abbruch vor jedem API-Abruf. (Alternativ löschen — deine Wahl.)
- `scripts/skew_repair_runner.sh`/`backfill_supervisor.sh`: unverändert, die Sperre sitzt im Erzeuger.

**R1c — ETHA-VRP, Reparaturmodus** in `backfill_skew_vrp.py`:
`--reparatur --ticker ETHA --von 2026-09-30 --bis 2026-10-13`:
- Nur Zeilen dieses Tickers im Datumsbereich; neu `vrp_pts = round((iv_atm − RV_log_return)·100, 2)` mit derselben
  Regel wie der Live-Pfad (nur `cm`/`cm_extrap` mit `iv_atm`; sonst Feld unverändert, gemeldet).
- **Vollständiger Diff** je Zeile (Datum, cm_mode, iv_atm, RV alt/neu, vrp alt/neu) in der Ausgabe und als Datei
  `logs/reparatur/etha_vrp_<zeit>.json`; ohne `--schreiben` nichts geschrieben.
- Invarianten vor dem Schreiben (statt des statistischen Gates, das für 10 Zeilen nichts aussagt): außerhalb des
  Bereichs und außer `vrp_pts` ist die History **byte-gleich im Inhalt** (Vergleich der kanonischen JSON-Darstellung
  aller übrigen Felder/Zeilen/Ticker); jede geänderte Zeile hat eine RV; neue RV ∈ (0, 3).
- Schreiben unter der Sperre, auf dem frischen Stand (der Diff wird dort neu gebildet und muss dem gezeigten gleichen,
  sonst Abbruch). **Nutzer gibt den Diff frei**, dann ein Lauf mit `--schreiben`.
- Warum bis 13.10.: seit dem Deploy `1c0412f` schreibt der Cron (ab Session 14.10.) die RV aus `log_return`.

**Wächter** (`verify_skew_historie_sperre.py`): unlesbare Datei → Abbruch, Datei unverändert; fehlende Datei ohne
`neu_erlaubt` → Abbruch; zwei parallele Schreiber (Barriere, wie `verify_produktionssperre`) → beide Änderungen
erhalten (Linux); Backfill-`anwenden` auf frischem Stand behält einen zwischenzeitlich eingefügten Cron-Punkt;
Reparaturmodus: Diff exakt, Invariante greift bei einer zusätzlichen Fremdänderung, ohne `--schreiben` keine Änderung.
Mutationen u. a.: `except: {}` zurück, Lesen vor statt unter der Sperre, alte Struktur zurückschreiben, Sperre vor dem
Snapshot lösen, Reparatur ohne Invariante. Ins Gate.

**Nebenbei (aus R5 freigegeben, nicht erledigt):** Blog „Vol-Regime-Radar“ DE `:106`/EN `:107` — die Fensterangabe
„2J“ korrigieren (Fenster seit 2026-09-25: 3M/6M/1J), `updated:` setzen.

## Paket B2 — R2: Session als Stempel **und** Bewertungsdatum

- `snapshot_gex_massive.py`: `S = letzte_session("NYSE")` einmal am Start; `pruefe_eod_fenster` vor dem Schreiben
  (`--no-write` bleibt erlaubt). `_fetch_chain(hi = S + h)`, `_map(raw, S)`: `dte = (exp − S)`, **Kontrakte mit
  `exp ≤ S` raus** (am Sessionschluss verfallen; Befund 4 — macht das Ergebnis unabhängig von der Startzeit).
  `stamp = S`. Felder in Summary, Profilen und Archiv: `date = S`, `session = S`, `bewertung = S`,
  `stempel_art = "session"`, `generated_at` bleibt Laufzeit.
- **Archiv:** neue Dateien nur noch `landing/data/gex_history_session/<S>.json` (in `.gitignore`); der alte Ordner
  `gex_history/` bleibt unverändert und bekommt nichts mehr. Keine Migration (die Zuordnung Lauftag → Session ist nur
  aus `generated_at` ableitbar, das das schlanke Archiv nicht trägt).
- `compare_flashalpha_gex.py:118-131` (Archiv-**Lesemodus** `--snapshot <datum>`): liest erst `gex_history_session`,
  dann `gex_history`, gibt die Herkunft aus (`session` / `lauftag`).
- `compute_key_levels.py`, `compute_iv_surface.py`: Bewertungsdatum = `letzte_session("NYSE")` für Horizont und DTE,
  Feld `session`; `generated` bleibt (Health-Check liest es).
- `compute_options_skew.py:1206`: `pc_ratio.date = out["session"]`.
- `snapshot_gex.py` (Yahoo, läuft nicht — Befund 2): Abbruch vor dem Schreiben („stillgelegt, Massive-Schreiber
  nutzen“), damit kein zweiter Stempelweg mehr existiert.
- `daily_health_check.py:430-437` GEX-Frische in **Sessions**: erwartet `letzte_session` zum Prüfzeitpunkt;
  `date == erwartet` → grün, eine Session dahinter → gelb, mehr → rot; fehlt `stempel_art` → gelb „alter Stempel“.
- Wächter: Sessions-/Bewertungsfälle mit fester Uhr (vor/nach Mitternacht UTC, Freitag mit Wochenverfall, Feiertag,
  Lauf in der Handelszeit → MarktOffen), gleiche Ausgabe für 22:30 und 01:30 UTC derselben Session; Archivpfad;
  Leser mit beiden Ordnern; Health-Frische. Mutationen: `date.today()` zurück, `exp < S` statt `≤`, Stempel ohne
  Bewertung, Archiv im alten Ordner.
- Wirkungsbericht: GEX für eine Session einmal mit alter und neuer Bewertung (Walls/Flip/Gamma-Index je Ticker).

## Paket B3 — R3: eine Rangrechnung im Cron

Spezifikation `shared/skew_rang.py` (wie v2, mit deinen Präzisierungen):
- Eingabe: History eines Tickers (nach dem Zusammenführen unter der Sperre), Session S, Fenster W ∈ {92, 183, 365}.
- Zeilen: `S − W ≤ date ≤ S` (Kalendertage, Anker Session), `cm_mode ∈ {cm, cm_extrap}`, nach Datum sortiert;
  doppelte Daten → Ticker ohne Rang + Meldung (der Cron dedupliziert, also ein Defekt).
- Metriken: `rr = call_iv − put_iv`, `iv = (put_iv + call_iv)/2`, `skew = skew_pts`, `cz`/`pz` = `call_zeta_pts`/
  `put_zeta_pts`, sonst aus `iv_atm` (`(call_iv − iv_atm)·100`), ohne `iv_atm` keine Zeta.
- **Je Metrik eigenes n:** erst gültige Werte der Metrik filtern, dann Session-Regel (letzter gültiger Wert hat
  Datum S, sonst kein Wert), dann `n ≥ MIN_NORM = 20`. Zeta als Paar: beide gültig.
- Rank = round((x_S − min)/(max − min)·100), max = min → 50; Percentile = round(#{x_i < x_S, i vor S}/(n − 1)·100);
  round = halb nach oben (`floor(v + 0.5)`) wie `Math.round`.
- Ausgabe `options_skew.json`: `rang_session = S`, `rang[ticker][W] = {rr:{n,rank,pctl}, iv:{…}, skew:{…},
  zeta:{n, cz:{rank,pctl}, pz:{rank,pctl}}}`; fehlende Metrik → Schlüssel fehlt.
- Reihenfolge im Cron unter **einer** Sperre: History frisch lesen → zusammenführen → Rang → History schreiben →
  Snapshot schreiben → Sperre lösen. Zwei atomare Schreibvorgänge sind keine Transaktion: bricht der Lauf zwischen
  beiden ab, steht eine neue History neben dem alten Snapshot; der alte Snapshot ist in sich konsistent
  (`rang_session == session`), Leser zeigen den alten Stand. Fixture dafür.

Leser:
- `/skew`: liest `rang[t][W]` für Radar (beide Ansichten) und Tabellenspalten; verwirft `rang`, wenn
  `rang_session ≠ session` (→ „—“). Rechnet in Produktion nichts mehr. Die JS-Referenz `scripts/js/skew_rang_ref.js`
  wird **nach der neuen Spezifikation geschrieben**, nicht aus `skew.html:241/:477` kopiert (deine Auflage).
- Mail `daily_report.skew_pctl_map`: liest `rang[t]["365"].skew.pctl`, nur wenn `rang_session == session ==
  letzte_session("NYSE")` zum Versandzeitpunkt, sonst „—“ für alle. Template `daily_report.html.j2:115` einfarbig,
  fehlender Wert sichtbar „—“.
- Zwilling Python = JS-Referenz auf Fixtures (konstant, Gleichstände, x,5-Werte, 19/20 Punkte je Metrik, Grenze genau
  S − W, fehlender aktueller Wert in einer Metrik, veraltete Datei, Zeta ohne iv_atm, doppeltes Datum, Abbruch zwischen
  den Schreibvorgängen). Mutationen: Uhr statt Session, Session-Regel vor dem Metrikfilter, `round` statt halb-nach-
  oben, n ≥ 19, ATM statt Flügelmittel, gemeinsames n.
- Wirkungsbericht auf eingefrorener History: Radarpositionen alt (Seiten-JS) / neu je Fenster und Modus,
  Quadrantenwechsel, Ausfälle, Mailspalte alt/neu.

## Folgeposten (nicht in B1–B3, nur zur Kenntnis)
Renditen aus Schlusskursen in Mail-Kursanzeigen (`daily_report.py` ~244, ~422), Sektor-Monat (~1273), Vol-Control-Proxy
(`build_volcontrol_proxy.py:74`); Kalenderseite + `kalender-compute.js:124` mit `earnings_events.report_date`.

## Reihenfolge
B1 (Sperre, dann R1c-Trockenlauf → Nutzerfreigabe → Schreiben) → B2 → B3. Je Paket Code-Review bis Freigabe,
Wirkungsbericht, Push nur ohne laufenden Container-Job.
