# Kalender-Umstellung V1a — Produktionssperre (Code-Runde 2)

Runde 1: [Prompt](2026-10-11_kalender_v1a_code.md) · [Antwort](2026-10-11_kalender_v1a_code_antwort1.md) („noch nicht
freigegeben", 4 Befunde, 5 Auflagen). Read-only, nichts schreiben, Mutationstest NICHT ausführen.
Änderungen: `git diff` + neue Dateien (`shared/produktionssperre.py`, `scripts/verify_produktionssperre*.py`).

<task>Sind die fünf Auflagen erfüllt, und kann V1a deployt werden (ohne Marke: kein Verhaltenswechsel im Betrieb)?</task>

## Umsetzung je Auflage
1. **Importeinstiege:** `get_client()` liefert `_Geschuetzt(create_client(...))`; `table(n)` für
   `GESCHUETZTE_TABELLEN` (prices, tdom/tdoy/monthly_stats, seasonality, scanner_results, saison_score_protokoll,
   stress_laeufe/-scores, market_events, ki_scores) hüllt upsert/insert/update/delete, `rpc(n)` für die drei
   Stress-RPCs → `pruefe_schreiben()`. Newsletter: `pruefe_schreiben("<name>.versand")` vor dem Versandteil von
   `main()`. Bei Marke ohne schreibende Freigabe → `Gesperrt` (SystemExit 75, fängt `except Exception` nicht).
   Wächter: Inventar verlangt, dass Pflicht-Skripte keinen eigenen Client/REST-Schreibweg haben; echter
   `get_client()` mit Ersatz-Client (Import-Einstieg, geschützt/ungeschützt, Lesen frei); echte Skripte als Datei
   UND `-m`. Ungeschützt bleiben bewusst Polymarket/Optionen/`refresh_log`/Abonnenten (keine Kalendermethode,
   sollen im Fenster weiterlaufen).
2. **Freigabeliste:** `AKTIVIERUNG_ERLAUBT` = Newsletter nur mit `--dry-run` (bestehender Render-in-Datei-Modus,
   kein Versand/refresh_log — v5 nannte ihn `--nur-rendern`), `build_calendar_data` nur mit `--aktivierung`,
   `abnahme:<name>` (lesend). Alles andere mit Kennung → 75. Schreibrecht hat derzeit niemand; P5/P6 werden in ihrer
   Phase eingetragen. `produktion()` entfernt `SA_AKTIVIERUNG` aus `os.environ` (Kind erbt nichts — geprüft).
3. **Isolierter Mutationstest:** kopiert shared/scripts/deploy/.github/landing/data (ohne logs, .env) in
   `mkdtemp`, mutiert/startet nur dort, verweigert ein Temp-Verzeichnis im Projektbaum, Hash des Projektbaums vor =
   nach als Abschlussbedingung. Der Wächter selbst führt die echten Skripte ebenfalls in einer Temp-Kopie aus und
   verlangt „keine neuen Dateien" (Mutation „Kalenderbauer ohne Sperre" macht genau das rot). Nebenbefund: der Lauf
   aus Runde 1 hatte `landing/data/market_calendar.*` im Arbeitsbaum neu geschrieben — wiederhergestellt.
4. **Exit 75:** `SuccessExitStatus=75` in sa-nightly/sa-intraday; daily_newsletter/db_completeness/full_scanner/
   flows_update/weekly_newsletter_manual bilden NUR 75 auf 0 ab (weekly_manual verschluckte bisher jeden Fehler —
   jetzt rot). Nachweis: `logs/sperre/unterdrueckt.log` + `refresh_log` `run_type='produktionssperre'` (Health-Check
   filtert nach run_type), bestmöglich, ändert den Exit nie. deploy.yml (`generate_decade_data … || echo`) als
   begründete Ausnahme im Wächter.
5. **Exklusiver Lock:** `aktivierung_setzen(kennung)` = EX-Lock (wartet), Marke atomar, Lock sofort frei;
   `aktivierung_aufheben` nur mit gleicher Kennung. Wächter (Linux): setzen wartet ≥1 s auf einen SH-Halter, danach
   startet eine Abnahme sofort. Doku: docs/KALENDER_UMSTELLUNG.md „Produktionssperre".

## Nachweise
Wächter Windows 49/49 (Lock UNGEPRÜFT), Windows-venv nur numpy/pandas/tzdata (CI-ähnlich) 49/49 mit 26 echten
75ern, **Linux im Server-Container (Kopie /tmp, streng) 53/53**. Mutationstest Windows **21/21** + 2 Gegenproben
verworfen, Projektbaum-Hash vor = nach (Linux inkl. 2 Lock-Mutationen läuft parallel).
Der erste Mutationslauf fand zwei eigene Fehler: (a) der Wächter erkannte nur NEUE Dateien — der Kalenderbauer
überschreibt eine bestehende → jetzt Hash-Vergleich aller Dateien der Kopie; (b) gemischte Zeilenenden in den
Units (mein Anhängen) → normalisiert.

## Fokus
Lücken im Schreibschutz (andere Schreibwege der Pflicht-Skripte: Dateien unter landing/data, `requests` an
Supabase, Kindprozesse), Fehlalarm-Risiko im Normalbetrieb ohne Marke (Hülle vs. supabase-py-API, z. B.
`_with_retry` setzt `_client=None`), und ob `--dry-run` als Render-Modus v5 genügt.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 35 Zeilen.
