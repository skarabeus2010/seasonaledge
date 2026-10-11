**Urteil**

Noch nicht freigabefähig als vollständiger Bauplan. A/B/C schließen die fachlichen Lücken; Vorbereitung, bestehendes Deploy-Gate und Aktivierung passen noch nicht zusammen.
Read-only geprüft, einschließlich einer JS-Probe im Speicher; nichts geschrieben. Shell-Kommandos konnten technisch nicht starten.

**Antworten**

1. Der Schalter trägt als befristete Übergangslösung. Methode und Generation müssen je Berechnung einmal fixiert und an Unterfunktionen weitergegeben werden. Der alte Zweig braucht auch unveränderte Abhängigkeiten.
2. V1–V8 sind grundsätzlich sinnvoll geordnet. Converter/Engine können früher vorbereitet und geprüft werden; ihre frühere Veröffentlichung widerspräche dem verbindlichen gemeinsamen Leserwechsel aus B6.11.
3. Keine weitere fachliche Paketklasse fehlt. Es fehlen jedoch ein ausführbares Aktivierungspaket und die ausdrückliche Zuordnung der Forschungs-/Chart-Erzeuger innerhalb V7.

**Befunde**

1. **Hoch — Ein Commit garantiert keine gemeinsame Laufzeitaktivierung.** [Plan:15](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v2.md:15) koppelt JS, Python, DB-Zeiger und Artikel. Der tatsächliche Deploy veröffentlicht Dateien im gemounteten Baum, baut EN, startet anschließend Python neu und erzeugt danach Blogausgaben ([Deploy:186](C:/dev/SeasonalEdge/.github/workflows/deploy.yml:186)). Leser bleiben während dieser Schritte erreichbar. Reihenfolge, Lesesperre beziehungsweise Konsistenzprüfung, Abbruchbehandlung und Wiederaufnahme fehlen; Schreibruhe allein genügt nicht.

2. **Hoch — Neue Generation bei weiterhin aktivem „alt“ ist nicht konkret ausführbar beschrieben.** Der globale Python-Schalter gilt für migrierte Verbraucher; seine Umgebungssteuerung ist nur für Tests vorgesehen. Gleichzeitig muss P6 vor dem Schalterwechsel `kalender_v1` produzieren ([Plan:11](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v2.md:11), [Plan:28](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v2.md:28)). Der Produktionslauf benötigt eine ausdrücklich gebundene Zielmethode unabhängig von der veröffentlichten Lesermethode; außerdem darf Vorbereitung keinen aktiven Zeiger wechseln.

3. **Hoch — Die unveränderte Kurslader-Seitenprobe blockiert beabsichtigte Kalenderänderungen.** Sie überlagert aktuelle Dateien mit alten Seitenfixtures und verlangt weiterhin gleiche Anzeige/Chartserien ([Wächter:225](C:/dev/SeasonalEdge/scripts/verify_seiten_kurse.py:225)). Im Speicher ausgeführt: Die echte alte TDOM-Fixture zählt den 06.07.2026 als **4**, der Kalender als **3**; die Mo–Fr-Testdaten enthalten den geschlossenen 03.07. Die Zusage „unverändert daneben“ ([Plan:39](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v2.md:39)) braucht daher einen ausdrücklich auf `alt` fixierten Testlauf oder einen Vergleich gleicher Kalenderrechnungen mit unterschiedlichen Transportwegen.

4. **Mittel — V7 beschreibt Eingänge und Faktenblätter, aber die Erzeugeränderungen nicht ausdrücklich.** Matrix A enthält unter anderem `tom_ml_filter`, `regime_clustering`, Monthly-10-Charts und dynamische Blogcharts ([Matrix:38](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_matrix_antwort1.md:38)). Ein Faktenblatt allein stellt diese Pfade nicht auf Kalenderendpunkte und Snapshoteingänge um. V7 muss deren Umbau, Offline-Einstieg und Faktenwächter ausdrücklich übernehmen.

**Auflagen**

- Aktivierung als eigenes Paket ergänzen: geprüfte Generation bereitstellen, Leserzugriffe absichern, Komponentenstände abgleichen, Fehler-/Wiederanlaufweg festlegen; Schreibruhe bis zur erfolgreichen Abnahme halten.
- Produktionsmethode und veröffentlichte Lesermethode trennen; Generationserzeugung unter `alt` sowie Ablehnung einer unpassenden Generation auf echten Pfaden prüfen.
- Kurslader-Gate vor Aktivierung methodenfest machen; Transport-, Fehler- und Wechselprüfungen erhalten. Den Kalendervergleich weiterhin gegen unabhängige Sollwerte führen.
- Jede A-Zeile einer Bauphase mit Erzeuger, Aufrufer und Abnahmenachweis zuordnen; geschützte Methoden auch nach Entfernung des Übergangszweigs unverändert reproduzieren.
- P5 bleibt ausdrücklich separat freigabepflichtig.
