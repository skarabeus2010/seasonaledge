**Urteil**

Noch keine Freigabe für V1c-1 als Bauvorlage. Tabellenkonvention und Metadaten-Hash lösen die entsprechenden Befunde aus Runde 2; die TSE-Kompatibilität bleibt widersprüchlich.

**Befunde**

- **P1 – TSE-Projektion ist zu weit ([v3 Z. 11](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_v1c_entwurf_v3.md:11)):** Sie erhält nominale Daten sämtlicher TSE-Ersatztage. Nach der geerbten Regel „verschobener Regeltermin = Ersatztag“ betrifft das auch Olympia-Verlegungen. Beispiel: Meeres-Tag 2020, regulär 20.7., verlegt auf 23.7. Die Projektion fügt den 20.7. wieder hinzu, obwohl der Bestand die regulären Olympia-Termine ausdrücklich ersetzt ([Kalendercode Z. 291](C:/dev/SeasonalEdge/shared/exchange_holidays.py:291)). Der Snapshot würde den Umbau ablehnen.
- **P2 – Datumsänderung ändert nicht zwingend beide Versionen ([v3 Z. 31](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_v1c_entwurf_v3.md:31)):** Eine Änderung nur des nominalen Datums bei gleichem wirksamen Tag verändert den Ereignisinhalt, aber keine Schließungsmenge. Gleiches gilt für wirksame Wochenenddaten, die außerhalb der Schließungsprojektion liegen.

**Auflagen**

- Nominaldaten gezielt für Furikae erhalten; Olympia-Verlegungen und nachfolgende Sonntagsersatzregeln ausdrücklich unterscheiden. Sollfälle für 2020/2021 ergänzen: ursprüngliche Regeltermine bleiben aus der Kompatibilitätsmenge ausgeschlossen.
- Versionsvertrag präzisieren: Jede Inhaltsänderung verändert `ereignisversion`; `kalenderversion` verändert sich ausschließlich bei geänderter Schließungsprojektion. Einen Test für reine Nominaldatumsänderung ergänzen.
- Nur lesend geprüft; keine Dateien geschrieben und keine Tests ausgeführt.
