# Review-Auftrag: Wahlen — CODE Phase 0 + 1a, Runde 1

Repo `C:\dev\Seasonaledge`. Umsetzung des freigegebenen Entwurfs `docs/review_prompts/2026-10-06_wahlen_plan.md`
(Abschnitte 10–14 maßgeblich). Prüfe die Commits `76702eb` (Phase 0) und `809905b` (Phase 1a):
`git show 76702eb --stat`, `git show 809905b`. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung,
am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Umfang
- `landing/data/elections.json` (88 Wahlen, Schema laut Plan Abschnitt 1/10), `landing/data/election_calendar_exceptions.json`
  (NYSE-Wahltage bis 1968 jedes Jahr + 1972/76/80, fünf Sonderschließungen 1972–1994, `calendar_documented_from` 1971).
- `scripts/verify_elections.py` (Schema, US-Regel, DE-Sonntag, Abdeckung, Quellen, Stichtage, Kalender-Ausnahmen,
  Termin-Parität zu `_electionDay`/`_get_election_day`).
- `shared/elections.py` (Anker, Pfad mit Gültigkeit je Offset, Live-Pfad, Kontrolljahre, `fenster_rendite`),
  `scripts/build_wahlen.py`, `scripts/verify_wahlen_build.py` (14 Fälle), `scripts/verify_wahlen_mutation.py` (10/10).
- Doku `docs/WAHLEN.md`, Quellenbericht `docs/WAHLEN_QUELLENPRUEFUNG.md`.

## Belege
- `py -3.14 scripts/verify_elections.py`: 0 Fehler; 11 Mutationen (inline) gefangen.
- `py -3.14 scripts/verify_wahlen_build.py`: 14/14; `verify_wahlen_mutation.py`: 10/10.
- Messung auf dem Server (echte Supabase-Kurse): ab 1971 stimmen Regelkalender + Ausnahmen mit den Kurszeilen von
  `^GSPC`/`^DJI` überein; vor 1971 viele Abweichungen (1968: 29 fehlende Sitzungen), deshalb dort nur
  Kurszeilenfolge + 4-Tage-Lückenregel. In beiden Reihen fehlt jeder Wahltag 1896–1968 (Vortag/Folgetag da).
  `^GSPC` hat bis 1952 Samstage, `^DJI` vor 1928 nicht; `^DJI` hat eine Phantomzeile Sa 1979-06-02.
- Probelauf `build_wahlen.py --no-write` auf dem Server: 67 Wahlen, 132/134 Pfade (aus: 1914), ≈ 390 KB kompakt.

## Prüfe besonders
- `anker`/`_schritt_ok`/`pfad`: Gültigkeitsregeln je Offset, Grenze belegt/unbelegt (ein Fenster, das 1971 überspannt),
  Fall „Wahltag laut Kalender Sitzung, Kurs fehlt".
- `live_pfad`: Positionierung über erwartete Sitzungen, Verhalten am Tag der Wahl selbst (vor/nach Schluss —
  `letzte_session` kappt laufende Sessions), Übergang scheduled → held.
- Kontrollvergleich: ist die Blockbildung (Wahl + zwei angrenzende ungerade Jahre) so umgesetzt, dass der Browser die
  vollständigen Tripel je X/Y bilden kann? Fehlt etwas im Export?
- `verify_elections.py`: kann ein Fehler in `elections.json` durchrutschen (z. B. falscher Sieger, falscher Kanzler)?
  Die Quellenprüfung ist redaktionell — ist das im Wächter ehrlich abgegrenzt?
- Exportformat für die Seite (Phase 1b): reicht es für Umbasierung t0/t−X, Renditen, Band, Tabelle, Filter?
