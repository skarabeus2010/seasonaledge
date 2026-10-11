**Urteil**

**V9 noch nicht freigegeben. Die Gate-Korrektur ist als Bauplan tragfähig.** Aktivierungspfad, Image-Sicherung und Release-Vorbedingung erfüllen die entsprechenden Auflagen aus Runde 4.

**Befunde**

1. **Hoch — Die Assetsperre schützt nur während des Fensters.** Ein vorab empfangenes HTML kann pausieren und seine Skriptanfragen erst nach Wartungsende stellen. Dann erhält `?v=<alt>` neue Dateien und kombiniert sie mit alten Inline-Rechnern. Dieser Fall wird von [v5:18](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v5.md:18) nicht erfasst; [Injection:79](/C:/dev/SeasonalEdge/deploy/inject_credentials.sh:79) erzeugt weiterhin überschreibbare Asset-URLs.

2. **Hoch — Die Daten-Ausnahme beruht auf einer falschen Annahme.** Weitere JSONs sind methodenabhängig: `flows_rebalancing.json` enthält Kalendertermine/HT-Countdowns, `index_effect_study.json` Sitzungsfenster und Offsets ([Flows:37](/C:/dev/SeasonalEdge/scripts/build_flows_rebalancing.py:37), [Index:77](/C:/dev/SeasonalEdge/scripts/build_index_effect.py:77)). Nur `market_calendar.json` zu sperren lässt alte Seiten neue Methodenausgaben laden; eine Releasebindung fehlt.

3. **Mittel — Rücksicherung auf dem Host garantiert keine Rücksicherung der HTTP-Ausgabe.** nginx bindet Sitemap, robots und llms als Einzeldateien ein ([Compose:42](/C:/dev/SeasonalEdge/docker-compose.yml:42)). Ersetzt `rsync` deren Inodes, können diese Mounts weiterhin die neuen Dateien liefern. Der App-Imagewechsel aus [v5:32](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v5.md:32) erneuert sie nicht.

4. **Mittel — Der Probe-Compose ist noch nicht ausreichend isoliert.** Ein eigener Projektname überschreibt `container_name: seasonalpha-app` nicht ([Compose:7](/C:/dev/SeasonalEdge/docker-compose.yml:7)). Mit der kopierten Konfiguration kollidiert der Probelauf mit dem Produktionscontainer.

**Auflagen**

- Alte HTML-Stände dauerhaft an unveränderliche Assets binden oder veraltete Releasekennungen auch nach Wartungsende ablehnen. Eine über das gesamte Fenster pausierte Seitenladung prüfen.
- Methodenabhängige Datenartefakte vollständig inventarisieren, gemeinsam aktivieren und beim Leser gegen dessen Release/Methode prüfen.
- Nach endgültiger Rücksicherung nginx-Mounts erneuern; anschließend auch Sitemap, robots und llms per HTTP gegen die Sicherung prüfen.
- Separate Probe-Konfiguration mit eigenem Containernamen, isolierten Mounts und kontrollierten DB-/Zeigerersatzpfaden festlegen.

Ausschließlich lesend geprüft; nichts geschrieben. Server-Probeläufe nicht ausgeführt.
