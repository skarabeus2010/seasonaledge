**FREIGABE (Plan): B1 ja · B2 ja.**

Die Änderungen schließen die Blocker aus der v3-Antwort. Geprüft gegen v3 und die betroffenen Codepfade, ausschließlich read-only.

- **B1:** History und Snapshot werden bereits in B1 unter derselben Sperre geschrieben; der bisherige vorgezogene Snapshot-Schreibweg entfällt ([compute_options_skew.py:1223](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1223)). Die verbindliche Freigabedatei mit vollständigem Vergleich des frisch berechneten Diffs schließt die Freigabelücke. Die Invariante gegen den frisch gesperrten Ausgangsstand erhält zwischenzeitliche Cron-Ergänzungen. Frisches `n_purge`, Entfernung des stillgelegten Schreibers und die vorgesehenen Negativ-Fixtures passen.

- **B2:** EOD-Schutz vor dem ersten Abruf für alle drei Erzeuger und die Sessionprüfung bei der GEX-Übernahme schließen die beiden verbleibenden Lücken ([compute_key_levels.py:148](C:/dev/Seasonaledge/scripts/compute_key_levels.py:148), [compute_key_levels.py:203](C:/dev/Seasonaledge/scripts/compute_key_levels.py:203)). Die Health-Bewertung erhält rote Abdeckungsbefunde. Eingefrorene Eingaben und der Vergleich ohne Laufzeitfelder machen die Uhrzeit-Gegenprobe aussagekräftig, einschließlich Wochenverfall.

**B3 bleibt freigegeben**; die Präzisierungen zu gültigen Zahlen und den beiden Zeta-Fallbacks passen.

Dies ist die Planfreigabe. Codeprüfung, Freigabe des konkreten Reparaturberichts und Deployment bleiben die in v3 vorgesehenen separaten Schritte. Keine Dateien geändert.
