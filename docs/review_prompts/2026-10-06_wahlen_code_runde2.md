# Review-Auftrag: Wahlen — CODE Phase 0 + 1a, Runde 2

Repo `C:\dev\Seasonaledge`. Fortsetzung von `2026-10-06_wahlen_code_runde1.md`. Prüfe den letzten Commit
(`git show HEAD`) gegen deine sieben Befunde. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung,
am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Umsetzung
1. Nicht-Sitzungen: `_schritt_ok` prüft beide Endpunkte zuerst, dann fehlende belegte Sitzungen (auch über die
   Grenze 1970/71), die 4-Tage-Regel nur bei mindestens einem unbelegten Endpunkt. Tests: Samstag bei −7
   (rückwärts), Samstag 02.01.1971 an der Grenze, belegte lange Schließung 11.–14.09.2001 bleibt gültig.
2. Datum je Offset: `tage` (Kalendertage relativ zu t0, int) parallel zu `c` in historischen, Kontroll- und
   Live-Pfaden — kompakter als ISO-Strings, Browser rechnet t0 + tage.
3. Live: Offsets zählen jetzt erwartete Sitzungen des belegten Kalenders (Kurse per Datum zugeordnet), `stichtag`
   wird übergeben; ≤ Stichtag ohne Kurs → `fehlende_sitzung` (nur dieser Offset), danach `zukunft`; Kurse an
   Nicht-Sitzungen im Bereich werden in `kurse_an_nicht_sitzungen` gemeldet. Test: verzögerter Refresh.
4. `machtwechsel` nur bei zwei bekannten Parteien, sonst `null`; Kammerparteien `unknown` → `null`. Test.
5. `verify_elections.py`: Pflichtfelder je Typ, Parteien je Land (+ `unknown`), zwei verschiedene
   Ergebnisquellen, Terminquelle, `checked` je Quelle, `unknown` ⇒ nicht verified; Grenze im Docstring.
6. Kalender: `calendar_documented_from` und die fünf Sonderschließungen festgeschrieben, eindeutige Schlüssel,
   `evidence` bei verified. Neue dauerhafte Mutationsprobe `scripts/verify_elections_mutation.py` 18/18 inkl.
   deiner Gegenproben.
7. Doku: Belegstand nachgetragen, offene Punkte bereinigt, Hinweis zur Artefakt-Ablage im Quellenbericht.

Belege: `verify_elections.py` 0 Fehler; `verify_elections_mutation.py` 18/18; `verify_wahlen_build.py` 17 Fälle
0 Fehler; `verify_wahlen_mutation.py` 14/14.
