# Code-Review Paket B2 — Session als Stempel und Bewertungsdatum (GEX, Key Levels, IV-Surface)

Plan: `docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3.md` + `_v4.md` (Freigabe B2 in
`…_plan_v4_antwort.md`). B1 ist live (`1080a55`). Code uncommittet im Arbeitsbaum (`git diff` + neue Dateien
`scripts/verify_gex_session.py`, `scripts/verify_gex_session_mutation.py`). Python:
`C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`, `PYTHONUTF8=1`. Read-only, Deutsch,
Datei:Zeile, Schwere, am Ende **FREIGABE (Code): ja/nein**.

## Umsetzung
- `scripts/snapshot_gex_massive.py`: `session = letzte_session("NYSE")` einmal in `main`; Schreiblauf →
  `pruefe_eod_fenster` vor dem ersten Abruf (MarktOffen → Exit 2). `analyze_massive(…, session=)` (Pflicht),
  `_fetch_chain(…, session)` Horizont ab S, `_map(raw, session)` DTE ab S, **`exp ≤ S` raus**. Felder `date`,
  `session`, `bewertung`, `stempel_art: "session"` in Summary, Profilen, Archiv; je Ticker `session`. Archiv nur noch
  `landing/data/gex_history_session/<S>.json` (gitignored), alter Ordner unverändert.
  **Über den Plan hinaus (bitte mitprüfen):** der Spot kam aus `/v2/aggs/…/prev`, dessen „Vortag“ von der Abrufzeit
  abhängt; jetzt der Tagesbalken der Session `range/1/day/S/S` (live geprüft: SPY 13.10. = 778,01, identisch mit /prev
  heute; der laufende Tag liefert während der Handelszeit 403), Balken eines anderen Datums → Ticker verworfen.
- `scripts/compute_key_levels.py`: Session + EOD-Schutz vor dem ersten Abruf (`build`, Exit 2 in `main`), `_chain`/
  `_by_exp` ab S, `_load_gex(session) → (dict, status)` übernimmt nur `stempel_art == "session"` und `session == S`;
  sonst keine Spot/Flip/Walls/Regime-Felder, `gex_status` ∈ {ok, fehlt, alter_stempel, andere_session:<d>, defekt};
  Ausgabe `session`, `gex_status`.
- `scripts/compute_iv_surface.py`: Session + EOD-Schutz, `_chain`/`_byexp` ab S, Ausgabe `session`.
- `scripts/compute_options_skew.py`: `pc_ratio.date` = dieselbe Session wie `out["session"]` (einmal bestimmt).
- `scripts/snapshot_gex.py` (Yahoo): `main` bricht ab (Exit 1, nichts geschrieben); Modul bleibt, weil
  `snapshot_gex_massive` UNIVERSE/CHART_TICKERS/MAX_DAYS importiert. Betriebsprüfung: keine Crontab, keine Unit,
  kein Workflow ruft ihn.
- `scripts/compare_flashalpha_gex.py::_from_snapshot`: erst `gex_history_session`, dann `gex_history`, `_herkunft`.
- `scripts/daily_health_check.py`: neue Funktion `_gex_bewertung(gd, erwartet)` (Sessions zwischen `date` und
  `letzte_session("NYSE")` über `is_trading_day`; 0 grün, 1 gelb, mehr rot; kein `stempel_art` mindestens gelb;
  Abdeckung wie bisher; Status = schlechter aus beiden).

## Nachweise
- `verify_gex_session.py` grün: Uhrzeit-Gegenprobe 22:30 vs 01:30 UTC derselben Session (Freitag 16.10.2026 mit
  Monatsverfall, eingefrorene Chain/Spot über eine `_get`-Attrappe) → Summary, Profile und Archiv ohne Laufzeitfelder
  identisch; DTE/Horizont ab Session für alle drei Erzeuger; Handelszeit → kein Abruf, keine Datei; Key Levels mit
  GEX der Vorsession/altem Stempel/fehlend; pc_ratio; Archivleser; sieben Health-Fälle; Yahoo-Schreiber.
- Mutationstest: siehe Nachtrag unten.

## Prüfaufträge
1. Bleibt irgendwo ein Lauftag als Bewertungs- oder Stempeldatum in diesen Erzeugern (auch Profile, Workflow
   `gex_snapshot.yml`, Seite `/dealer-positioning`, `/key-levels`)?
2. Spot-Umstellung: Risiko, wenn der Tagesbalken der Session spät verfügbar ist (Cron 22:15 UTC ≈ 2 h nach Schluss)?
   Reißleine 60 % greift dann — ist das richtig?
3. Health: Randfälle (Feiertag, erwartete Session vor dem Datum, Wochenende).
4. Wächter: echte Funktionen oder selbst hergestellte Einbindung? Fehlende Mutationen?

## Nachtrag Nachweise
- Mutationstest `verify_gex_session_mutation.py` **20/20** (DTE/Stempel/Horizont ab Lauftag je Erzeuger, verfallene
  Kontrakte, Archivordner, EOD-Schutz je Erzeuger, Spot-Balkendatum, GEX anderer Session/alter Stempel, pc_ratio,
  Archivreihenfolge, drei Health-Fehler, Yahoo-Schreiber).
- Ins Gate (`deploy.yml`, mit `scipy==1.18.1` wie im Container); in einer Umgebung wie im Gate (ohne streamlit) grün.
- Unverändert grün: `verify_session_stamp`, `verify_skew_anzeige`, `verify_skew_laufzeiten`,
  `verify_skew_historie_sperre`, `verify_produktionssperre`, `verify_briefing_versand`, `verify_basisabweichung`.
