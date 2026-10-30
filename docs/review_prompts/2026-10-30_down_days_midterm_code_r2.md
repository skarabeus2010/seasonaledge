# Code- und Artikelprüfung R2 — Down-Days SPY + letzte Woche vor Midterms

Antwort R1: [2026-10-30_down_days_midterm_code_r1_antwort.md](2026-10-30_down_days_midterm_code_r1_antwort.md) — NICHT FREIGABEFÄHIG.

Umsetzung je Befund:

1. **„Am Wahltag“ falsche Kohorte** — Tabelle und Chart heißen jetzt „t0 (Referenztag)“; neuer Faktenblattwert
   `wahltag_offen` (nur Wahlen mit t0 = Wahltag): +0,44 %, 10 von 14. Text „Tag für Tag“ und FAQ DE/EN nennen diese
   Kohorte für den echten Wahltag und +0,37 % nur noch als Referenztag t0.
2. **Wächter bindet Fließtext nicht an Inhalt** — die Werteliste ist ersetzt durch **Kontextverträge**
   (`vertraege()`): jede Zahl mit Einheit muss genau einem Faktenblattwert in der geschriebenen Form entsprechen UND im
   selben Satz die Bezugswörter dieses Werts tragen (Horizont, Schwelle, Kohorte). Dazu Pflichtsätze für die Aussagen
   ohne Einheit („nicht höher, sondern leicht niedriger“, „2008 brachte allein 39 Tage“, „2008 gab es 39 solcher
   Tage“, „2017 keinen“, „in sechs Wahljahren“, „deutlich nur 1930“, echte Wahltage mit Fallzahl). Alle fünf
   Gegenproben aus R1 sind als Mutationen eingebaut und werden gefangen; dazu „Pp-Werte vertauscht“ und „Abstände
   1898/1971 vertauscht“. Stand **37/37**.
3. **Midterm-Snapshot ohne Prüfsumme** — SHA-256 im Faktenblatt, Prüfung vor dem Parsen; Mutation „Inhalt verändert,
   Kennung gleich“ für SPY und Snapshot. `.gitattributes`: `-text` für beide Datenstände.
4. **Ausschlussgrund ±20** — „im längeren Fenster fällt die Wahl von 1930 weg, weil der eingefrorene Datenstand den
   Pfad eines ihrer Vergleichsjahre (1929) im Nachlauf als ungültig markiert“.
5. **Krisenaussage** — „Zusammen senken die beiden Krisenblöcke das Mittel. Sie enthalten aber sowohl die schlechtesten
   Fälle (Herbst 2008) als auch besonders starke Erholungen (März 2020).“
6. **Erklärungen aus Sensitivität** — Ausdünnung: „zeigt, wie stark das Ergebnis davon abhängt, welche Tage innerhalb
   einer Häufung man zählt“; Notenbank-Satz gestrichen („Warum, untersucht diese Auswertung nicht“).
7. **Fallzahlen** — Rendite-/Risikochart: n je Säule an der Achse; Pfadchart: Ereignis- und Basiskohorte im
   Untertitel; Basis-n je Horizont (5 016 / 5 001) im Text unter der Mitteltabelle.
8. „Elf Tage mit mindestens 2 % Verlust im Oktober 2008“; „größter ETF“ gestrichen; schlechtester Fall jetzt mit Datum
   (22.09.2008).

Bitte erneut prüfen wie in R1 ([R1-Auftrag](2026-10-30_down_days_midterm_code_r1.md)), insbesondere: hält der
Kontextvertrag, welche falsche Aussage käme jetzt noch durch, und sind die geänderten Sätze korrekt?
Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT FREIGABEFÄHIG.
