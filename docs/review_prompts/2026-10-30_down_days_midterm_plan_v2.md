# Plan v2 — Down-Days SPY + letzte Woche vor Midterms (Codex-Auflagen R1 eingearbeitet)

Antwort R1: [2026-10-30_down_days_midterm_plan_antwort.md](2026-10-30_down_days_midterm_plan_antwort.md),
**FREIGABE MIT AUFLAGEN**. v2 vor dem Ergebnislauf festgeschrieben. Änderungen gegenüber v1:

| Befund | Umsetzung |
|---|---|
| 1 blockierend — Zufallsvergleich nicht kalibriert | **p-Werte und Holm gestrichen.** Rein beschreibend: Abstand zur Basis, Fallzahl an jeder Zahl. |
| 2 blockierend — Kern kann keine Fenster vor t0 | `shared/elections.intervall_rendite(p, a, b)` (Schluss Offset a → Schluss Offset b, None bei fehlendem Kurs im Intervall oder außerhalb des Pfads); Sitzungsrendite j = `intervall_rendite(p, j−1, j)`. Unabhängige Sollfälle im Zahlenwächter. |
| 3 — Entzerrung ändert die Frage | Heißt „chronologisch ausgedünnt“; **alle Ereignisse sind die Hauptbeschreibung**; die ausgedünnte Stichprobe ist eine Nebenansicht ohne Unabhängigkeitsbehauptung. |
| 4 — Robustheitskohorten | Krisenausschluss: weder Ereignistag noch eine Folgesitzung des Fensters im Block, gleiche Regel für die Basis. Hälften: Fenster vollständig in der Hälfte, Basis ebenso. Pfad 0…50: eine Kohorte (vollständiges 50er-Fenster) für jeden Offset, Basis ebenso. Ausdünnung nach jeder Einschränkung neu. |
| 5 — t−5→t−1 hat vier Renditen | Zusatzfenster **gestrichen**. Hauptzahl t−5 → t0 = fünf Sitzungsrenditen bis zum Referenzschluss; Tag j = c[j−1] → c[j], j = −4 … +1. „Wahltag ab 1984 geöffnet“ war falsch — im Snapshot liegt t0 seit 1970 am Wahltag (bis 1968 und 1972/76/80 geschlossen laut Ausnahmeliste; Faktenblatt zählt `t0_am_wahltag`). |
| 6 — Fallzahlen je Fenster | Eine Kohorte für Woche und Tage (alle Kurse t−5 … t+1 gültig). Erwartet laut Codex 31 Wahlen / 31 Tripel, ab 1971 13 / 13. 2026 ist im Snapshot als `scheduled` vorhanden und wird ausgeschlossen. Verwendete Wahl- und Vergleichsjahre stehen im Faktenblatt. |
| 7 — Ausführung / Risikobegriff | „beschreibende Rendite ab Ereignisschluss, ohne Ausführungsannahme“. Risiko: `min(0, F1 … F15)` = größter zwischenzeitlicher Verlust gegenüber dem Ereignisschluss, anhand von Schlusskursen; Basis gleich. |
| 8 — Widerspruch / Risikoprämie | Abweichungen zum ±20-Artikel werden mit Fenster und Kohorte erklärt; Risikoprämie nur als mögliche Erklärung. Keine Wahlwirkung, Prognose oder Handelsrendite. |
| 9 — Wiederholbarkeit, Wächter | SHA-256 des Datenstands im Faktenblatt-Code (Abbruch bei Abweichung); Jahreshäufigkeit zusätzlich je beobachteter Sitzung; der Zahlenwächter bindet Kernzahlen an ihren Kontext (Tabellenzeile/Satz), nicht nur an eine Liste erlaubter Werte. SPY = Gesamtrendite-Näherung, ^GSPC = Indexkursrendite. |

Code: `scripts/research/down_days_fakten.py`, `scripts/research/midterm_letzte_woche_fakten.py`.
