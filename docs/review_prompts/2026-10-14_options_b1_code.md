# Code-Review Paket B1 — Schreibsperre der Skew-History + R1c-Reparaturmodus

Plan: `docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3.md` + `_v4.md` (deine Freigabe B1:
`…_plan_v4_antwort.md`). Code uncommittet im Arbeitsbaum (`git diff` + neue Dateien
`scripts/verify_skew_historie_sperre.py`, `scripts/verify_skew_historie_sperre_mutation.py`; gelöscht
`scripts/backfill_skew_history.py`). Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`,
`PYTHONUTF8=1`. Read-only, Deutsch, Datei:Zeile, Schwere, am Ende **FREIGABE (Code): ja/nein**.

## Umsetzung
- `shared/atomic_json.py`: `SperreBelegt`, `HistorieDefekt`, `sperrdatei_skew_historie()` (= `SA_SPERR_DIR` bzw.
  `logs/sperre/skew_historie.lock` über `produktionssperre.sperr_verzeichnis`), `history_lesen(pfad, neu_erlaubt)`,
  `history_aktualisieren(pfad, aendern, danach, frist_s=600, neu_erlaubt, sperrdatei)`: flock LOCK_EX mit Frist →
  frisch lesen (defekt/fehlt → Abbruch) → `aendern` (False = nicht schreiben) → atomar schreiben → `danach` → lösen.
  Ohne fcntl einmalige Warnung „ungeprüft“.
- `scripts/compute_options_skew.py::build`: Zusammenführen als `_zusammenfuehren(hist)` (Inhalt unverändert, nur
  eingerückt), `history_aktualisieren(hp, _zusammenfuehren, danach=lambda _h: write_json_atomic(p, out))` — der
  Snapshot wird erst nach der History und unter derselben Sperre geschrieben; defekte/fehlende History → keine Datei.
- `scripts/backfill_skew_massive.py`: `run_ticker` gibt nur noch neue Zeilen zurück (Planung auf einem frischen
  Lesestand), neues reines `anwenden(hist, sym, neue, overwrite)` (Purge `src=="massive"` + `n_purge` aus dem frischen
  Bestand; ohne overwrite nur fehlende Daten; overwrite ohne Punkte → False). `main` wendet je Ticker unter der Sperre
  an; HistorieDefekt/SperreBelegt → Exit 1.
- `scripts/backfill_skew_vrp.py`: `rv_laden` (ohne Sperre) / `anwenden` (unter der Sperre, frischer Stand; Gate über
  genau diese Zeilen); `nachrechnen` = beide Phasen (Tests). Reparaturmodus `--reparatur --ticker T --von --bis`
  [`--schreiben --freigabe-datei`]: `reparatur_diff` (nur cm/cm_extrap mit endlichem iv_atm und RV; sonst Grund),
  `zielhash` = SHA-256 der kanonischen Zielzeilen, `reparatur_pruefen` (RV in (0, 3), mindestens eine Zeile),
  Trockenlauf schreibt nur `logs/reparatur/vrp_<T>_<von>_<bis>_<zeit>.json`; Schreiblauf vergleicht unter der Sperre
  den frisch gebildeten Diff vollständig mit dem Bericht und setzt nur `vrp_pts`; Invariante gegen den frisch gesperrten
  Stand.
- `scripts/backfill_skew_history.py` gelöscht (+ Inventar `shared/produktionssperre.py`, Hinweis `docs/OPTIONS.md`).
- `scripts/skew_repair_runner.sh`: der separat gestartete Backfill-Container bekommt `-v $APP_DIR/logs:/app/logs` —
  ohne den Mount hätte er gegen eine eigene Sperrdatei gesperrt (eigener Fund).
- Wächter angepasst: `verify_session_stamp.py`, `verify_skew_anzeige.py` setzen `SA_SPERR_DIR` ins Temp-Verzeichnis
  und legen je Wurzel eine leere History an (Produktion hat immer eine); `_dateien` blendet die unveränderte Saat aus.
  `verify_basisabweichung_mutation.py`: Anker nachgezogen.
- Gate: `verify_skew_historie_sperre.py --streng` in `deploy.yml`.
- Blog „Vol-Regime-Radar“ DE/EN: „2-Jahres-Fenster“ → „1-Jahres-Fenster“, `updated: 2026-10-14` (aus R5 freigegeben).

## Nachweise
- `verify_skew_historie_sperre.py`: Windows grün (Parallelität ungeprüft), **Linux `--streng` grün** (isolierter
  Container auf dem Server aus einer Kopie des Arbeitsbaums, nicht der Produktionscontainer).
- Mutationstest **18/18 unter Linux `--streng`** (lokal 16/16 + 2 nur-Linux ungeprüft).
- `verify_session_stamp` PASS, `verify_session_mutation` 44/44, `verify_skew_anzeige`/`_laufzeiten` PASS,
  `verify_basisabweichung` grün + Mutation 24/24, `verify_produktionssperre` 75, `verify_seiten_kurse` 313,
  `verify_briefing_versand` 77/77, `verify_seo_html` 0.

## Prüfaufträge
1. Sperre: Frist/Freigabe/Fehlerpfade, `danach` wirklich unter der Sperre, kein Pfad, der ohne Sperre schreibt
   (alle Schreiber von `options_skew_history.json` — auch außerhalb der vier genannten?).
2. Cron: verändert die Umstellung das Ergebnis des Zusammenführens (Einrückung, Closure über `per`/`out`/`pc_ratio`/
   `corr`)? Was passiert bei SperreBelegt um 23:00 (Workflow-Exit, Health)?
3. Backfill: Semantik von `anwenden` gegenüber der alten Dedup-Regel; `skew_repair_runner.sh` wertet „+N Punkte“ aus —
   passt die neue Ausgabe; Verhalten bei Hartstopp mitten im Schreiben.
4. Reparatur: kann ein Schreiblauf etwas anderes schreiben als freigegeben? Float-Vergleich nach JSON-Rundreise.
5. Wächter: echte Funktionen oder selbst hergestellte Einbindung? Fehlende Mutationen?
