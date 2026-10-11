**Urteil**

**Nicht als vollständiger Bauplan freigegeben.** Methodentrennung, V7-Erzeugerumbau und dauerhafte Reproduktionswächter erfüllen die entsprechenden Auflagen aus Runde 2. V9 hat noch drei Lücken. Read-only geprüft, einschließlich einer JS-Probe im Speicher; nichts geschrieben.

**Befunde**

1. **Hoch — Die vorausgesetzte gemeinsame Schreibsperre fehlt.** [Plan:33](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v3.md:33) verweist auf eine „vorhandene Sperre“. Nightly, Intraday und Onboarding verwenden keine gemeinsame Produktionssperre; die systemd-Units starten sie direkt. Timer anzuhalten sperrt weder manuelle Starts noch bereits laufende Prozesse. Außerdem startet [install_timers.sh:44](/C:/dev/SeasonalEdge/deploy/install_timers.sh:44) die Timer beim normalen Deploy wieder.

2. **Hoch — Die Leserabsicherung ist weiterhin unvollständig.** Zwischen Zeigerwechsel und Containerwechsel können alte Python-Leser laufen: [Daily-Workflow:115](/C:/dev/SeasonalEdge/.github/workflows/daily_newsletter.yml:115) startet unabhängig von den angehaltenen Timern. Die Aussage „Python liest ab (c)“ reicht deshalb nicht. Auch Schritt (d) veröffentlicht mehrere Dateien: altes HTML mit Inline-Rechnern kann neue Skripte laden. Ein `?v=` bindet hier keinen unveränderlichen Dateistand ([Injection:79](/C:/dev/SeasonalEdge/deploy/inject_credentials.sh:79)). Der einmal gelesene Methodenschalter verhindert diese Mischung nicht.

3. **Hoch — Der Rückweg stellt veröffentlichte Blogausgaben nicht vollständig wieder her.** [Plan:42](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v3.md:42) nennt Generation, Container und Dateien des vorherigen Commits. Der Blogbuilder überschreibt jedoch persistierte DE-/EN-Ausgaben und Bilder schrittweise ([Builder:1297](/C:/dev/SeasonalEdge/blog/blog_builder.py:1297), [EN:1373](/C:/dev/SeasonalEdge/blog/blog_builder.py:1373)). Diese generierten Ausgaben werden durch einen Commit-Rückwechsel nicht zurückgesetzt. Ein Fehler während (e) hinterlässt neue und alte Veröffentlichungen nebeneinander.

**Auflagen**

- Eine gemeinsame Produktionssperre konkret einplanen: alle Schreibzugänge einschließlich manueller Starts erfassen, laufende Prozesse abwarten und die Sperre über Containerwechsel hinweg halten. Timer erst nach Abnahme wieder starten.
- Newsletter-Läufe während V9 sperren beziehungsweise vollständig ablaufen lassen. HTML, Skripte, EN und Artikel aus einem geprüften Veröffentlichungsstand ausliefern; dafür eine Lesesperre oder unveränderliche, versionierte Ausgaben vorsehen.
- Rückweg und Wiederanlauf auf den gesamten Veröffentlichungsstand erweitern, einschließlich generierter Blogausgaben/Bilder. Fehler nach jedem Aktivierungsschritt und während DE-/EN-Build prüfen.
- Beim Kurslader-Gate ausdrücklich die Kalenderrechnung der alten Transport-Fixtures nachziehen: Die bestehende TDOM-Fixture zählt im Speicher trotz `kalender_v1` den 06.07.2026 als 4 statt 3. Beide Vergleichsbäume müssen tatsächlich dieselbe Rechnung ausführen.
- V7: Exakte Alt-Reproduktion nur bei belegtem ursprünglichem Eingang verlangen; sonst die verbindliche Neuberechnungsregel B7.4 anwenden. P5 bleibt separat freigabepflichtig.
