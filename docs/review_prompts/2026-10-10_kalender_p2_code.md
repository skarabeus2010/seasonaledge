# P2 Schreiber nach Börsenkalender — Code-Review Runde 1

Plan: [v7](2026-10-10_xetra_tdoy_plan_v7.md) · deine Auflagen: [Antwort 7](2026-10-10_xetra_tdoy_plan_antwort7.md)
(K2 sofort aktiv bestätigt; Auflagen 1–6). Stand vorher: `2397c78` (P1a/P1b deployt).

<task>Prüfe `git diff` im Arbeitsbaum + neue Dateien `scripts/verify_schreiber_nummern.py`,
`scripts/verify_schreiber_nummern_mutation.py`. Read-only.</task>

## Umsetzung (Auflage → Stelle)
- **K1** neuer Helfer `shared/exchange_holidays.tdom_tdoy_fuer_ticker(ticker, daten)` (Ticker → Börse →
  `handelstag_nummern`, ValueError bei Zuordnungs-/Bereichsfehler). Benutzt von: Nightly Phase B
  (`nightly_refresh.py`, Nummern nur für die geschriebenen Zeilen, nicht mehr aus `preprocess()`; Fehler →
  `ticker_fehler`, Kurse ohne Nummern), Nightly-Lückenfüller (`health_check`), Intraday (ein Aufruf, keine
  DB-Abfrage der Vorzeile, keine halb berechneten Nummern mehr — die Teilnummern-Mutation aus Paket 3 entfällt
  deshalb), Onboarding, `fix_missing_days`. 0 wird geschrieben.
- **Auflage 1 (Grenze P5)**: `backfill_new_ticker` liest den Bestand (`vorhandene_daten`, seitenweise) und
  schreibt Nummern **nur für neue Zeilen**; bestehende Zeilen behalten tdom/tdoy (Upsert ohne diese Spalten).
  Lesefehler → Abbruch. `check_db_completeness --fix` ruft `backfill_tdoy` nicht mehr auf (Abschnitt 4 →
  Empfehlung als Trockenlauf; nach `backfill_new_ticker`/`fix_missing_days` kein Nachlauf mehr nötig).
- **Auflage 2 (K3)** `backfill_tdoy.py` neu: Standard Trockenlauf (Bericht je Jahr TDOM/TDOY); `--schreiben`
  nur mit genau einem `--ticker`, `--von`+`--bis`, `--von` ≥ 2001-01-01, kein Jahr mit Status `ungeprueft`,
  ≤ `--max-aenderungen` (500); alle Grenzen vor dem ersten Request; nur `{"tdom","tdoy"}` per
  `update().eq(ticker).eq(date)`, jede Antwort muss genau eine Zeile bestätigen; Exit 1 bei Verweigerung/Fehler.
- **Auflage 3 (Fehler)**: Onboarding zählt Zeilen erst nach bestätigtem Upsert, gescheiterte Chunks → `ok=False`;
  `onboard_ticker.main` → Exit 1, wenn der Backfill scheitert; `fix_missing_days` zählt nach Erfolg, `FEHLER`-Liste,
  `main()` → Exit 1.
- **Auflage 4 (K5)** Lückenfüller: je fehlendem Tag „nachgeladen“ (mit Nummern) / „ungeklärt“ (kein Kurs bei
  Yahoo — inkl. leerem Ergebnis; landet in `missing_details`, als `UNGEKLÄRT …` in `errors` → Health-Mail gelb,
  kein Erfolg über `tickers_erfolgreich`) / Fehler (Download- oder Upsertfehler → `errors` + ungeprüft).
  „Börse war zu“ gibt es nicht mehr. `daily_health_check.py` unverändert: jeder `errors`-Eintrag → gelb.
- **K4** `bulk_load_supabase.py` gelöscht (kein Aufrufer). `scripts/sql/fix_tdoy_2026_08_glitch.sql` als
  historisch markiert.
- **Auflage 5/6 (Wächter)** `verify_schreiber_nummern.py` (33): führt die echten Schreibwege offline aus (Stubs nur
  Supabase/Yahoo + die schweren Nightly-Nachbarn), vergleicht die **übergebenen Datensätze** mit einer
  unabhängigen numpy-Zählung, prüft exakte Zeilenmengen „mit/ohne Nummern“, 0-Werte, Fehlerpfade, CLI-Aufrufer
  (`onboard_ticker.main`, `fix_missing_days.main`, `backfill_tdoy.main`), die Grenzen von `backfill_tdoy` (vor 2001
  mit **belegtem** Kalender NYSE 1999, damit nicht die Statusgrenze greift) und einen **Bestand**: jede Python-Datei
  mit einem `prices`-Schreibaufruf ist bekannt (gefunden wurde dabei `fix_log_returns_may2026.py` — schreibt nur
  `log_return`); die Schreiber ohne Nummern enthalten kein `tdom`/`tdoy`-Literal. Abgefangene Abstürze in der
  Ausgabe der Skripte → `[Ausnahme]`. Alter Code (`git archive HEAD`): 6/21 mit genau den bekannten Defekten.
  Mutationstest 18/18 in zwei Läufen, Gegenproben 3/3. Leere 3.12-Umgebung mit numpy+pandas+tzdata: 33/33.
  Deploy-Gate: neuer Schritt mit `pip install pandas==2.2.3 tzdata`.
- Weiter grün: Fehlerweitergabe 15/15, Ticker 56/56, Nummern 86/86, Stress 32/32, Session-Stempel.

## Fragen
1. Auflagen 1–6 erfüllt? 2. Ändert ein Schreiber noch irgendwo bestehende Nummern außerhalb von P5 (z. B.
Nightly-7-Tage-Fenster überschreibt alte Drift-Werte — gewollt, weil „aktuell“)? 3. Ist die Absturzerkennung
über die Ausgabe tragfähig? 4. Sonst etwas vor dem Commit?

## Ausgabevertrag
**Urteil** (Freigabe / mit Auflagen / keine) · **Befunde** (Datei:Zeile, Beleg) · **Antworten** (je ≤ 6 Zeilen). ≤ 70 Zeilen.
