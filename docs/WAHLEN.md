# Wahlen und Börse („Buy/Sell the Election")

Kanonische Doku der Wahl-Ereignisstudie. Der von Codex freigegebene Entwurf (8 Runden, 2026-10-06) steht in
[review_prompts/2026-10-06_wahlen_plan.md](review_prompts/2026-10-06_wahlen_plan.md); bei Widersprüchen gelten die
späteren Abschnitte (10–14) vor den früheren.

## Stand

| Phase | Inhalt | Stand |
|---|---|---|
| 0 | Terminliste `landing/data/elections.json` + Kalender-Ausnahmen + Wächter | **erledigt 2026-10-06**, Codex-Freigabe nach 3 Code-Runden |
| 1a | Rechenkern `shared/elections.py` + `scripts/build_wahlen.py` → `landing/data/wahlen_study.json` | **erledigt 2026-10-06**, Probelauf auf dem Server ohne Schreiben, Codex-Freigabe nach 3 Code-Runden |
| 1b-1 | Browser-Rechenkern `landing/js/wahlen-compute.js` + Python-Zwilling `aggregiere`, Nightly-Phase J | **erledigt 2026-10-07**, Codex-Freigabe nach 2 Runden |
| 1b-2 | Seite `/wahlen` (DE+EN) unter „Events": Streuband, Mittel/Median, Vergleichslinie, Live-Linie, Tabelle, Snapshot-Ansicht | **erledigt 2026-10-07**, Codex-Freigabe nach 3 Runden |
| 1c | Blogartikel zur Midterm 2026 mit eingefrorenem Snapshot (Hauptfenster 20/20) | offen |
| 2 | Deutschland (Bundestag, DAX-Reihe vorher prüfen) | offen |
| 3 | Backtest-Engine-Ereignistyp `election` (Long), Kalender, Dashboard-Hinweis | offen |
| M | Angleichung der bestehenden Wahlstrategien (Midterm, UECS, KTI, Signalvorschau) | offen, eigener Plan |

## Daten

- **`landing/data/elections.json`** — einzige redaktionelle Quelle für Wahltermine und -ergebnisse (committet, kein
  Cron-Output). 88 Wahlen: US-Präsident 1896–2028 (34), Midterms 1898–2026 (33), Bundestag 1949–2025 (21).
  Jede gehaltene Wahl mit ≥ 2 übereinstimmenden Quellen (`verified: true`). Herkunft und alle Quellenkonflikte:
  [WAHLEN_QUELLENPRUEFUNG.md](WAHLEN_QUELLENPRUEFUNG.md).
- **`landing/data/election_calendar_exceptions.json`** — belegte Börsenschließungen nach `(calendar_id, date)`.
  NYSE am Wahltag: geschlossen **jedes Jahr bis 1968 (auch ungerade Jahre)**, danach nur 1972/1976/1980. Doppelt
  belegt für 1896–1980: NYSE-Liste + fehlender Tageskurs in `^GSPC` und `^DJI` (Supabase, Vortag und Folgetag
  vorhanden, gemessen 2026-10-06). Dazu die fünf Sonderschließungen 1972–1994 und `calendar_documented_from`.
- **Wächter:** `py -3.14 scripts/verify_elections.py` — Schema, typspezifische Pflichtfelder, Parteien je Land,
  US-Regel, DE-Sonntag, lückenlose Abdeckung, Quellenpflicht (zwei verschiedene Ergebnisquellen, Prüfdatum),
  Kammer-Stichtage, Kalender-Ausnahmen inkl. festgeschriebener Abdeckungsgrenze und Sonderschließungen, sowie
  **Termin-Parität** zu `strategy-compute.js::_electionDay` (per node) und `plain_vanilla.py::_get_election_day`.
  `scripts/verify_elections_mutation.py`: 21/21. **Grenze:** ob ein plausibel formatierter Sieger oder Kanzler
  historisch stimmt, ist redaktionelle Sachprüfung (Quellenbericht); `verified` bestätigt sie, der Wächter nicht.

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

## Seite /wahlen (Phase 1b)

- **Rechnet im Browser nur noch Auswahl, Umbasierung, Renditen und Aggregation** (`landing/js/wahlen-compute.js`);
  Anker, Sitzungen und Gültigkeit kommen aus Python. Zwilling `shared/elections.py::aggregiere` liefert dieselben
  Kurven, Kennzahlen, Einzelwerte, Ausschlüsse und die Live-Linie — `scripts/verify_wahlen_twin.py` vergleicht
  jede Zahl (8 Optionssätze, Wahltag/Folgetag, 12/12 Mutationen).
- **Kennzahl „Differenz Wahl − ohne Wahl"** ist gepaart je Wahl und in Prozentpunkten; die graue Linie mittelt nur
  Wahlen mit beiden Vergleichsjahren, ihr Abstand zur goldenen Linie kann deshalb abweichen (steht im Chart-Hinweis).
- **Datenstand** steht in einer eigenen Zeile, unabhängig von Filtern; Fenster, die vor 1971 beginnen, tragen einen
  Stern (Kalender ungeprüft). **Hauptfenster 20/20** ist gekennzeichnet, alles andere heißt „Exploration".
- **Snapshot-Ansicht** `?snapshot=<id>` lädt ausschließlich `/landing/data/wahlen_snapshots/<id>.json` und dessen
  gespeicherte Ansicht; ungültig oder fehlend → sichtbarer Fehler, nie die aktuelle Datei.
- **i18n:** `landing/js/i18n.js` meldet jetzt `sa:i18n-bereit` und `bereit()`; `_JSON_VER` v5. Seiten mit
  dynamischen Texten warten darauf, sonst bleiben Zahlen/Wörter auf `/en/` deutsch (Codex-Fund).
- **Seitentest** `scripts/js/probe_wahlen_seite.js`: führt das echte Seitenskript in node aus (DE, EN mit spätem
  Wörterbuch, XSS in Namen und Seriennamen, Snapshot gültig/fehlend/ungültig in fünf Formen, spätes Ergebnis 2000).
- **Gefunden in den Reviews:** Seriennamen gingen ungeschützt in die ApexCharts-Legende (innerHTML); die EN-Seite
  hätte deutsche Zahlen gezeigt, weil `SA.i18n.current` nicht existiert; „alle Wahlen" nahm die Live-Wahl in
  Dateireihenfolge (2028 vor 2026).

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

- Samstagshandel bis 1952 und Schließung 31.07.–27.11.1914 sind nicht als Kalender-Einträge erfasst — nötig ist
  das erst, wenn der Kalender vor 1971 als belegt gelten soll (heute: Kurszeilenfolge + 4-Tage-Regel).
- Quellen für `schedule_known_from` (US-Gesetze) sind gesetzt, aber nicht abgerufen (`checked: null`).
- DE: Anordnungsdatum regulärer Bundestagswahlen recherchieren.

## Lessons (2026-10-06)

- **Den Entwurf reviewen lassen, bevor Code entsteht** — 8 Runden am Plan (13 → 7 → 5 → 4 → 2 → 2 → 1 → 0 Befunde)
  haben die schweren Fragen (Anker bei geschlossenem Wahltag, Kontrolljahre, kein p-Wert bei n≈30, „Sell" ≠ Short,
  Snapshots für Blogzahlen) vor der ersten Codezeile geklärt; die Code-Runden fanden danach nur noch Präzisierungen.
- **Zuschnitt statt Vollausbau:** Runde 3 zeigte, dass Phase 1 nicht gleichzeitig die alten Wahlstrategien umziehen
  darf. Die Uneinigkeit von JS, Python und Engine bei geschlossenem Wahltag (t−5→t+4 / t−4→t+3 / t−4→t+4) ist
  festgehalten und bekommt eine eigene Phase M; bis dahin hält ein Wächter nur die **Termine** gleich.
- **Uneindeutige Quellen mit Daten auflösen:** Die NYSE-Liste ließ offen, worauf „except 1898, 1906 and 1907" sich
  bezieht. Die Kurslücken in zwei Reihen (`^GSPC`, `^DJI`) an jedem Wahltag 1896–1968 klärten es in einem Lauf.
- **Ein Kalender ist nur so weit belegt, wie man ihn gemessen hat.** Unser Regelkalender stimmt erst ab 1971; davor
  hätte er 1968 allein 29 „fehlende" Sitzungen gemeldet. Die Grenze ist jetzt Messwert und im Wächter festgeschrieben.
- **Grün beim ersten Lauf heißt nichts:** die Tests waren sofort grün, die Mutationsprobe fand zwei Lücken
  (Lückengrenze, Kontrolljahre). Codex fand drei weitere Wege, auf denen fehlerhafte Daten den Wächter passierten.
- **Shell-Heredocs deuten Backslashes um** (`\1` wurde wieder zum Steuerzeichen) — Ersetzungen mit Rückverweisen
  über das Edit-Werkzeug oder `\g<1>` schreiben und die geschriebene Datei prüfen.

