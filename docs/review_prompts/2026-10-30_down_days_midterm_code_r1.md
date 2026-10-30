# Code- und Artikelprüfung R1 — Down-Days SPY + letzte Woche vor Midterms

Plan v2 (Auflagen aus R1 eingearbeitet): [2026-10-30_down_days_midterm_plan_v2.md](2026-10-30_down_days_midterm_plan_v2.md).

Zu prüfen:
- `shared/elections.py` — neu `intervall_rendite(p, a, b, n)`.
- `scripts/research/down_days_fakten.py`, `scripts/research/midterm_letzte_woche_fakten.py` — Faktenblätter.
- `scripts/research/render_downdays_midterm_charts.py` — Charts (Bilder unter `blog/posts/images/spy-down-days/`
  und `blog/posts/images/midterm-letzte-woche/`; bitte die PNGs ansehen, wenn möglich).
- `scripts/verify_downdays_midterm_blog.py` — Zahlenwächter (Tabellen werden aus dem Faktenblatt erzeugt und müssen
  wörtlich im Text stehen; Fließtextzahlen gegen die Werte des Faktenblatts; Pflichtsätze; Mutationen 21/21).
- Artikel DE+EN:
  - `blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md`, `blog/posts/en/2026-10-30_spy-down-days-what-happens-next.md`
  - `blog/posts/2026-10-30_sp500-letzte-woche-vor-midterm-wahl.md`, `blog/posts/en/2026-10-30_sp500-last-week-before-midterm-election.md`

Fragen:
1. Rechnen die Faktenblätter das, was Plan v2 festlegt (Kohorten, Krisen-/Hälftenregel, Pfadkohorte, Risikokennzahl
   min(0, F1…F15), Ausdünnung, eine Kohorte für Woche und Tage, gepaarte Tripel)?
2. Jede Aussage in den Artikeln: durch das Faktenblatt gedeckt? Zu stark formuliert? Besonders: „die Trefferquote ist
   nicht höher“, „fast der gesamte Vorsprung stammt aus den Jahren seit 2016“, „Die Krisen ziehen das Mittel nicht nach
   oben, sondern liefern die schlechtesten Einzelfälle“, „oft mit Hilfe von Notenbank und Staat (2020)“, „Seit 1970 ist
   die Börse an Midterm-Wahltagen geöffnet … bis 1966 geschlossen“, „Elf Verlusttage im Oktober 2008“, die Einordnung
   gegen den ±20-Artikel (+2,33 Pp auf 30 Gruppen), „Negativ war die letzte Woche in sechs Wahljahren, deutlich nur 1930“.
3. Widerspricht etwas dem bestehenden Artikel `blog/posts/2026-10-07_midterm-wahltag-boerse.md`?
4. Lücken im Wächter: welche falsche Zahl oder Aussage käme durch?
5. EN-Fassungen: inhaltlich deckungsgleich mit DE?

Antwort auf Deutsch, nummerierte Befunde (blockierend / wichtig / Hinweis) mit Beleg (Datei:Zeile oder Rechnung) und
konkreter Änderung. Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT FREIGABEFÄHIG.
