# Paket 1 (K1): Kalenderkorrekturen — Code-Review Runde 2 (Abnahme der Auflagen)

Runde 1: [Prompt](2026-10-10_kalender_paket1_code.md) · [Antwort](2026-10-10_kalender_paket1_code_antwort1.md) — „Freigabe mit Auflagen“.

<task>
Prüfe, ob die vier Auflagen erfüllt sind und ob dabei etwas Neues kaputtging. Read-only. Diff: `git diff`
im Arbeitsbaum plus die neuen Dateien `scripts/verify_kalender_sollfaelle*.py`.
</task>

## Umsetzung
1. **Brückentage** (Befund 1): Sollfälle TSE 2009-09-22, 2015-09-22, 2026-09-22 zu, 2010-09-21 offen;
   Mutation „Brückentag nur im Thronwechseljahr“ an `[TSE 2015-09-22]` gebunden.
2. **Regelgrenzen** (Befund 2): deine vier Paare als Sollfälle (1971-10-11/1973-04-30, 1995-07-20,
   1999-01-11/1999-01-15, 1997-10-10/1997-10-13) + vier Mutationen (Ersatz vor 1973, Meerestag vor 1996,
   Seijin immer 2. Mo, Taiiku historisch 2. Mo), je an eine benannte Prüfung gebunden.
   Ergebnis: **86/86** Sollfälle, Mutationen **18/18**, zwei vollständige Läufe identisch, Gegenproben 2/2.
3. **Wirkungszahl** (Befund 3): deine Zahl stimmt — TSE **281** Tage (254 vor 2000, 27 ab 2000). Meine 271
   stammten aus einem Lauf **vor** der Begrenzung auf 1966/1973. Reproduktion: alter Stand per
   `git show HEAD:shared/exchange_holidays.py` + `HEAD:shared/nyse_holidays.py`, je Tag 1950-01-01..2035-12-31
   und Börse `is_trading_day` alt gegen neu.
4. **Bytecode-Cache** (Befund 4): neuer gemeinsamer Helfer `python_probe()` in
   `scripts/verify_twins_mutation.py` (frisches `PYTHONPYCACHEPREFIX` je Unterprozess). Umgestellt:
   Kalender-, Discovery-, Preisqualitäts-, Zwillings-, Session- und der Zwillings-Mutationstest selbst.
   Alle nach der Umstellung grün: Discovery 12/12, Preisqualität 16/16, Polymarket-Zwillinge 15/15,
   Session 44/44, Twins 18/18. Nicht umgestellt: `verify_i18n_cache_mutation.py` (mutiert JS/JSON),
   `verify_seo_mutation.py` (arbeitet je Mutation in einer frischen Baumkopie).
5. Zusätzlich: `deploy.yml` bekommt den Schritt „Boersenkalender gegen belegte Sollfaelle“ vor dem SSH-Deploy.

## Fragen
1. Auflagen erfüllt? 2. Ist `verify_seo_mutation.py` wirklich sicher (`copytree` mit `copy2` erhält mtimes;
liegt ein `__pycache__` in der Kopie)? 3. Sonst etwas vor dem Commit?

## Ausgabevertrag
**Urteil** (Freigabe / Freigabe mit Auflagen / keine Freigabe) · **Befunde** · **Antworten**. ≤ 50 Zeilen.
