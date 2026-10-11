**Urteil**

Noch keine Freigabe für V1c-1 als Bauvorlage. Runde 1 ist weitgehend bearbeitet; der Bestandsschutz bleibt widersprüchlich und Tabellenereignisse sind noch nicht vollständig definiert.

**Befunde**

- **P1 – TSE verliert nominale Feiertagsdaten (v2 Z. 11–14, 23–25):** Der Bestand enthält nationale Feiertage **und** deren Ersatztermine (`shared/exchange_holidays.py:314–327`). Beispielsweise bleiben 2023-01-01 und 2023-01-02 enthalten. Genau ein Neujahrsereignis mit `wirksam=2023-01-02` und die Projektion ausschließlich über `wirksam` entfernen den 1. Januar. Das verletzt die zugesagte unveränderte `get_holidays`-/`is_holiday`-API, obwohl die Sitzungen unverändert bleiben.
- **P1 – Nominaldatum unbekannter Tabellenereignisse fehlt (Z. 33–35, 44–46):** Art und Name bleiben korrekt unbekannt, aber Kennung und Transport verlangen weiterhin ein nominales Datum. Die Tabelle liefert nur das eingetragene Datum. Ohne verbindliche Konvention ist weder die Kennung rekonstruierbar noch ausgeschlossen, dass ein wirksamer Ersatztermin als nominaler Feiertag ausgegeben wird.
- **P2 – Ereignisversion erfasst Metadaten nicht vollständig (Z. 44–49):** Ein Hash ausschließlich über Ereignislisten mit `name_idx`/`quelle_idx` bleibt bei Änderungen der referenzierten Namen oder Quellenbelege unverändert. Der Bundlehash erkennt diese Änderungen, die Ereignisversion dagegen nicht.

Kennungskollision, NASDAQ-Alias, Transportfelder und phasenbezogener Abnahmeumfang sind ansonsten ausreichend präzisiert. Die Tabellenidentitäten bleiben ausdrücklich eine akzeptierte Abnahmelücke; vollständige B4-Abnahme ist später vorgesehen.

**Auflagen**

- Die bestehende Feiertagsmenge als eigene Kompatibilitätsprojektion aus denselben Regeln erhalten; nominale TSE-Daten gezielt berücksichtigen, ohne sie pauschal bei anderen Börsen hinzuzufügen.
- Für Tabellenereignisse Nominaldatum und Kennungsbildung ausdrücklich definieren; eine technische Datumskonvention muss als solche erkennbar bleiben.
- Die Ereignisversion über kanonische, aufgelöste Ereignisinhalte einschließlich referenzierter Namen und Quellen bilden; eigene Versionsfelder ausschließen.
- Unabhängige Sollfälle für TSE 2023-01-01/02, ein unbekanntes Tabellenereignis und reine Namen-/Quellenänderungen ergänzen.
- Nur lesend geprüft; keine Dateien geschrieben und keine Tests ausgeführt.
