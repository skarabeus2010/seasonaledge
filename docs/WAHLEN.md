# Wahlen und Börse („Buy/Sell the Election")

Kanonische Doku der Wahl-Ereignisstudie. Der von Codex freigegebene Entwurf (8 Runden, 2026-10-06) steht in
[review_prompts/2026-10-06_wahlen_plan.md](review_prompts/2026-10-06_wahlen_plan.md); bei Widersprüchen gelten die
späteren Abschnitte (10–14) vor den früheren.

## Stand

| Phase | Inhalt | Stand |
|---|---|---|
| 0 | Terminliste `landing/data/elections.json` + Kalender-Ausnahmen + Wächter | **erledigt 2026-10-06** (Code-Review durch Codex steht aus) |
| 1 | Seite `/wahlen` (S&P 500, Dow): historische Studie, Referenz „Jahr ohne Wahl", Live-Linie Midterm 03.11.2026, DE+EN | offen |
| 2 | Deutschland (Bundestag, DAX-Reihe vorher prüfen) | offen |
| 3 | Backtest-Engine-Ereignistyp `election` (Long), Kalender, Dashboard-Hinweis | offen |
| M | Angleichung der bestehenden Wahlstrategien (Midterm, UECS, KTI, Signalvorschau) | offen, eigener Plan |

## Daten

- **`landing/data/elections.json`** — einzige redaktionelle Quelle für Wahltermine und -ergebnisse (committet, kein
  Cron-Output). 88 Wahlen: US-Präsident 1896–2028 (34), Midterms 1898–2026 (33), Bundestag 1949–2025 (21).
  Jede gehaltene Wahl mit ≥ 2 übereinstimmenden Quellen (`verified: true`). Herkunft und alle Quellenkonflikte:
  [WAHLEN_QUELLENPRUEFUNG.md](WAHLEN_QUELLENPRUEFUNG.md).
- **`landing/data/election_calendar_exceptions.json`** — belegte Börsenschließungen nach `(calendar_id, date)`.
  NYSE am Wahltag: geschlossen **jedes Jahr bis 1968 (auch ungerade Jahre)**, danach nur 1972/1976/1980. Ab 1928
  doppelt belegt (NYSE-Liste + fehlender S&P-500-Tageskurs, 49/49 bzw. auch alle ungeraden Jahre), davor nur die
  NYSE-Liste (`verified: false`).
- **Wächter:** `py -3.14 scripts/verify_elections.py` — Schema, US-Regel, DE-Sonntag, lückenlose Abdeckung,
  Quellenpflicht, Kammer-Stichtage, Kalender-Ausnahmen und **Termin-Parität** zu den alten Formeln
  `strategy-compute.js::_electionDay` (per node) und `plain_vanilla.py::_get_election_day`. 11/11 absichtlich
  eingebaute Fehler gefangen.

## Wichtige Definitionen

- **Bezugsschluss t0** = letzter gültiger Börsenschluss am oder vor dem Wahltermin (US bei geschlossenem Wahltag
  der Montag, DE der Freitag vor dem Wahlsonntag). Ein Ergebnis-Zeitpunkt ist das ausdrücklich nicht (2000:
  Entscheidung erst 12.12.).
- **Kammerkontrolle** = Partei des Speakers bzw. organisatorische Senatsmehrheit (inkl. Stimme des Vizepräsidenten,
  `tie_vp`); `before` = Tag vor der Wahl, `after` = Beginn des neuen Kongresses (bis 1933 4. März, ab 1935 3. Januar).
  Senat erst ab 1914.
- **Stärkste Partei ≠ Kanzlerpartei** 1969, 1976, 1980 — ein Filter „Wahlsieger" muss sagen, welches Feld er meint.
- `schedule_known_from`: US aus dem Gesetz (1845 bzw. 1872), DE vorgezogen = Auflösung; DE regulär noch nicht
  recherchiert (`null`) → für Phase 3 gilt dort „Handelbarkeit nicht nachgewiesen".

## Offen

- Vor 1928: NYSE-Wahltagsschließung gegen unsere `^DJI`-Tagesreihe prüfen (die NYSE-Liste ist in der
  Spaltenzuordnung uneindeutig: „Closed every year except 1898, 1906 and 1907" steht nahe der Election-Day-Zeile).
- Samstagshandel bis 1952 und Schließung 31.07.–27.11.1914 als Kalender-Einträge erfassen.
- Quellen für `schedule_known_from` (US-Gesetze) sind gesetzt, aber nicht abgerufen (`checked: null`).
- DE: Anordnungsdatum regulärer Bundestagswahlen recherchieren.
