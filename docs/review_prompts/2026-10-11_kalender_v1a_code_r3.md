# Kalender-Umstellung V1a — Produktionssperre (Code-Runde 3)

Runde 2: [Prompt](2026-10-11_kalender_v1a_code_r2.md) · [Antwort](2026-10-11_kalender_v1a_code_antwort2.md) (3 Befunde).
Read-only, nichts schreiben, Mutationstest NICHT ausführen. Änderungen: `git diff` + neue Dateien.

<task>Sind die drei Befunde aus Runde 2 behoben, und kann V1a deployt werden?</task>

## Umsetzung
1. **Importierte Dateischreiber / Import-Einstiege:** jedes der 19 Pflicht-Skripte ruft auf Modulebene, vor der
   ersten Definition, `if __name__ != "__main__": modul_sperre("<name>")`. `modul_sperre` betritt `produktion(name)`
   über einen modulweiten `ExitStack` und hält den geteilten Lock bis Prozessende: bei Marke scheitert schon der
   Import (Exit 75, also auch `from scripts.build_flows_rebalancing import main; main()`), und ein Prozess, der
   vorher importiert hat, blockiert `aktivierung_setzen`. `produktion()` ist wiedereintrittsfähig (ein Lock je
   Prozess); ein verschachtelter Name wird bei Marke erneut gegen `AKTIVIERUNG_ERLAUBT` geprüft, Schreibrecht nur,
   wenn alle beteiligten Läufe es haben. Der erlaubte Kalender-Build bleibt (`--aktivierung` + Kennung).
2. **Anfrage vor, Ausführung nach der Aktivierung:** der Client hüllt den Builder (`_GeschuetzteAnfrage`), die Kette
   bleibt gehüllt, `.execute()` läuft unter `schreibsperre(kanal)` — außerhalb eines Produktionslaufs nimmt sie den
   geteilten Lock für die Ausführung und prüft die Marke darunter; innerhalb (Lock schon gehalten) nur die Marke.
   Geschützte RPCs ebenso. Newsletter-Versand: das Modul hält den Lock über `modul_sperre`/`produktion` die ganze
   Laufzeit. `aktivierung_setzen(kennung, frist_s=None)`: mit Frist `TimeoutError` statt Marke.
3. **Flows:** `flows_update.yml` sammelt `pruefen+=("${s#build_}.json")` nur für Panels ohne 75 (`; continue`) und
   ruft `check_flows_freshness.py --files "${pruefen[@]}"`; sind alle unterdrückt, entfällt die Prüfung.
   Nebenwirkung, dokumentiert: `verify_calendar_rules.py` importiert `fix_missing_days` und endet in einer
   Aktivierung ebenfalls mit 75.

## Nachweise (neu im Wächter)
Einbau „sperrt beim Import" (AST, je Skript); echte Skripte zusätzlich als `python -c "import scripts.<x>"` (Windows
57× Exit 75 über Datei/-m/Import, keine Datei der isolierten Kopie verändert); verschachtelter nicht freigegebener
Lauf → 75; Anfrage ohne Marke aufgebaut, Marke gesetzt, `.execute()` → gesperrt; Linux: Import-Einstieg und eine
laufende Ausführung halten `aktivierung_setzen` ≥ 1 s auf, Frist setzt keine Marke; Flows-Ausschluss.
Windows 71/71 (3 Lock-Prüfungen UNGEPRÜFT). Bestehende Wächter mit Importen der Pflicht-Module unverändert grün
(`verify_schreiber_nummern` 36/36, `verify_wahlen_build`, `verify_wahlen_twin`, `verify_kalender_fehlerweitergabe` 15/15).
Mutationstest: 24 + 5 Linux-Mutationen (u. a. Import ohne Sperre, Ausführung prüft nicht, Ausführung ohne Lock,
Modul-Sperre hält den Lock nicht, Frist ignoriert, verschachtelter Lauf, Flows): Windows **25/25** + 2 Gegenproben
verworfen; Linux-Wächter streng **78/78**; Linux-Mutationstest (inkl. 5 Lock-Mutationen) läuft parallel.

## Fokus
Kann `modul_sperre` den Normalbetrieb ohne Marke stören (Prozesse, die Pflicht-Module importieren und lange laufen;
Lock-Reihenfolge Import-Lock vor `__main__`-Lock; Kindprozesse)? Bleibt ein Schreibweg eines Pflicht-Skripts, der
weder über den Import noch über `__main__` geht?

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 30 Zeilen.
