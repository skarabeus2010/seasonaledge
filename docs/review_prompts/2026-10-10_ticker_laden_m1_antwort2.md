**Urteil**

Deployfreigabe für M1 unter der Commit-Auflage unten. Die beiden Fehlerkopplungen aus Runde 1 sind behoben; keine weiteren blockierenden Befunde.

**Befunde**

- Rückfallregel korrekt: laufende Ladung, wartende Vereinigung und TTL-Neuladung sind abgedeckt; bei identischem Bedarf erfolgt kein zusätzlicher Ladeversuch.
- Unabhängige Parallelprobe: sechs engere Verbraucher erhalten sechs eigene Rückfallladungen; maximal vier Netzanfragen gleichzeitig, Bestand unverändert. Das verursacht zusätzliche Last im Fehlerfall, entspricht aber der festgelegten Regel.
- Generationenprobe: Ein gemeinsamer Erfolg während eines laufenden Rückfalls erhält Generation 2, der später abgeschlossene Rückfall Generation 3; der Bestand bleibt bei Generation 2.
- **119/119 Koordinatorprüfungen, 65/65 Hüllenprüfungen und 36/36 Dashboardprüfungen bestanden.** Texte und Chart-Serien stimmen für normal, Vollhistorienfehler und TTL überein.
- Vorher-Fixtures stimmen mit `05e6310` überein. Einbindung korrekt in **44/44 DE- und 37/37 vorhandenen EN-Seiten**; Deploy-Gate vorhanden.
- Dashboard plus Hüllenprobe reicht für diesen M1-Umfang. Die weiteren Seiten ändern ausschließlich die Skripteinbindung.

**Auflagen**

Die Hüllenprobe, beide Fixture-Sätze, Seitenprobe samt Python-Wächter und `scripts/perf/package*.json` sind weiterhin **untracked**. Sie müssen gemeinsam mit den Produktionsänderungen in den Deploy-Commit; diese Auflage ist noch offen.

Nichts geschrieben; Mutationstests nicht ausgeführt. Den Dashboard-Vorher-Stand ausschließlich im Speicher hergestellt.
