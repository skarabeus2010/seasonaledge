**Urteil**

**V9 noch nicht freigegeben.** Die Gate-Korrektur und die V7-Präzisierung sind grundsätzlich tragfähig. Dokumente und relevante Produktionspfade ausschließlich lesend geprüft; nichts geschrieben.

**Befunde**

1. **Hoch — Die Aktivierung sperrt ihre eigenen Abnahmepfade.** Die Marke erzwingt für Daily/Weekly und `build_calendar_data` Exit 75 ([Plan:16](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v4.md:16)). Gleichzeitig verlangt V9 Newsletter-Trockenläufe bei gesetzter Marke. Der Deploy ruft außerdem den Kalenderbauer auf und verschluckt dessen Fehler als Warnung ([Injection:68](/C:/dev/SeasonalEdge/deploy/inject_credentials.sh:68)). Ohne ausdrücklich geregelten Aktivierungspfad scheitert die Abnahme beziehungsweise bleiben alte Kalenderausgaben stehen.

2. **Hoch — Die HTML-Wartungsseite verhindert weiterhin keinen gemischten Browserstand.** Assets bleiben erreichbar ([Plan:27](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v4.md:27)). Ein vor dem Fenster geladenes HTML kann während des Deploys neue Skripte nachladen: nginx liefert auch bei `?v=<alter Stand>` dieselbe überschreibbare Datei ([nginx:165](/C:/dev/SeasonalEdge/deploy/nginx.conf:165)). Die Leserauflage aus Runde 3 ist damit für bereits begonnene Seitenladungen offen.

3. **Hoch — Der Revert-Deploy überschreibt die bereits geprüfte Rücksicherung.** Der Prüfsummenvergleich erfolgt **vor** dem anschließenden Revert-Deploy ([Plan:36](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v4.md:36)). Dieser injiziert eine neue Cache-Kennung, baut EN, Image, Blog und SEO erneut ([Deploy:172](/C:/dev/SeasonalEdge/.github/workflows/deploy.yml:172)). Der danach ausgelieferte Stand ist deshalb nicht mehr der geprüfte Sicherungsstand. Ein gespeicherter Tagname allein garantiert zudem keinen unveränderlichen alten Image-Inhalt.

**Auflagen**

- Aktivierungseigene Build-/Abnahmepfade festlegen: Newsletter ohne Versand und Produktionswrites rendern, Kalenderausgaben kontrolliert erzeugen; gewöhnliche Starts bleiben gesperrt. Markenprüfung unter dem gemeinsamen Lock durchführen.
- Wartungsregel samt im nginx-Container sichtbarer Marke **vor V9** installieren und prüfen. Für begonnene Seitenladungen unveränderliche Release-Assets oder eine erzwungene Ablehnung mit Neuladen vorsehen.
- Rückweg umordnen: Revert-Deploy zuerst beziehungsweise ohne erneute Veröffentlichung; anschließend endgültig rücksichern und **danach** Prüfsummen, Methoden und Zeiger prüfen. Altes Image über unveränderliche ID/eigenen Sicherungstag erhalten. Fehler nach jedem Teilschritt und während DE/EN-Build proben.
- Im Gate auch `vollfehler` und `ttl` mit eigenständigen Sollwerten im neuen Baum erhalten; nur den Vergleich gegen alte Kalenderrechnungen entfernen.
- Release-Vorbedingung eindeutig formulieren: Kandidat auf `aktivierung`; erst Schritt 4 bringt ihn auf master. P5 bleibt separat freigabepflichtig.
