# Wahlen und Börse („Buy/Sell the Election")

Kanonische Doku der Wahl-Ereignisstudie. Der von Codex freigegebene Entwurf (8 Runden, 2026-10-06) steht in
[review_prompts/2026-10-06_wahlen_plan.md](review_prompts/2026-10-06_wahlen_plan.md); bei Widersprüchen gelten die
späteren Abschnitte (10–14) vor den früheren.

## Stand

| Phase | Inhalt | Stand |
|---|---|---|
| 0 | Terminliste `landing/data/elections.json` + Kalender-Ausnahmen + Wächter | **erledigt 2026-10-06** (Code-Review durch Codex steht aus) |
| 1a | Rechenkern `shared/elections.py` + `scripts/build_wahlen.py` → `landing/data/wahlen_study.json` | **erledigt 2026-10-06**, Probelauf auf dem Server ohne Schreiben (Code-Review durch Codex steht aus) |
| 1b | Seite `/wahlen` (S&P 500, Dow): historische Studie, Referenz „Jahr ohne Wahl", Live-Linie Midterm 03.11.2026, DE+EN; Build im Nightly | offen |
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

## Rechenkern (Phase 1a)

- `shared/elections.py`: Anker t0 (letzter Kurs am/vor dem Termin, ≤ 4 Kalendertage), Pfad −60…+60 als **Kurse**
  mit Gültigkeit je Offset, Live-Pfad mit projiziertem t0, Kontrolljahre (angrenzende ungerade Jahre,
  Pseudotermin nach US-Regel), `fenster_rendite` als Referenz für den Browser.
- **Kalender:** belegt ab 1971 — Regelkalender `shared/nyse_holidays.py` + Ausnahmen aus
  `election_calendar_exceptions.json`. Gemessen: ab 1971 stimmen Kalender und Kurszeilen von `^GSPC` und `^DJI`
  überein bis auf fünf Sonderschließungen (1972-12-28 Truman, 1973-01-25 Johnson, 1977-07-14 Stromausfall,
  1985-09-27 Hurrikan Gloria, 1994-04-27 Nixon), die jetzt als Ausnahmen eingetragen sind. Davor gilt die
  Kurszeilenfolge der Reihe; Lücken > 4 Kalendertage machen die weiter entfernten Offsets ungültig.
- **Offsets = Kurszeilen der Reihe.** `^GSPC` hat bis 1952 Samstage, `^DJI` vor 1928 nicht — „20 Handelstage" sind
  vor 1953 je Reihe leicht verschieden lange Kalenderzeiträume.
- **Wächter:** `scripts/verify_wahlen_build.py` (14 Fälle inkl. aller Pflichtfälle des Plans und eines
  End-to-End-Laufs von `baue()`), `scripts/verify_wahlen_mutation.py` (10/10 eingebaute Fehler gefangen).
- **Probelauf 2026-10-06** (Server, echte Kurse, nicht geschrieben): 67 US-Wahlen, 132 von 134 Pfaden; ausgeschlossen
  nur 1914 (Börse 31.07.–27.11. geschlossen). Datei kompakt ≈ 390 KB. Live-Linie Midterm 2026: letzter Kurs bei
  Offset −21. Erste Zahlen Hauptfenster (t0 → +20, **noch nicht zur Veröffentlichung**, Review steht aus):
  S&P 500 Präsident n=32 Mittel +0,49 % / Referenz +0,17 %; Midterm n=30 +0,72 % / +0,39 %.

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
