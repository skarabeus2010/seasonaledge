# Kalender-Umstellung V1c-3 — Code-Runde 4 (Halbtage)

Runde 3: [Prompt](2026-10-12_kalender_v1c3_code_r3.md) · [Antwort](2026-10-12_kalender_v1c3_code_r3_antwort.md)
(Archivquellen nicht unabhängig verifizierbar, weil dein Netz web.archive.org nicht erreicht). Read-only.

<task>Reicht die unabhängige Gegenprüfung als Abnahme der Archivquellen? Ist V1c-3 freigegeben?</task>

## Unabhängige Gegenprüfung
Die Seiten ins öffentliche Repo zu legen ist ausgeschlossen (fremde Inhalte). Stattdessen haben zwei eigens
beauftragte Prüfagenten die Archivfassungen ohne Kenntnis der Katalogwerte selbst abgerufen (nur im Speicher), die
SHA-256 der Rohbytes berechnet, die „close early"-Fußnoten vollständig gelesen und die Jahresköpfe der Tabelle
bestimmt: [docs/belege/nyse_halbtage_2026-10-12_gegenpruefung.md](../belege/nyse_halbtage_2026-10-12_gegenpruefung.md).
Ergebnis: alle acht verwendeten Archivfassungen byte-identisch mit der Sicherung (Status 200), Halbtage je Jahr
gleich der Sollmenge, jede Jahresabdeckung in den Tabellenjahren der zugeordneten Seite.

## Änderung seit Runde 3
2020 stammt jetzt aus der Fassung 2020-02-19 (Tabelle 2020/2021/2022, unabhängig bestätigt); die Fassung 2018-02-02
wurde zweimal gedrosselt (HTTP 429) und ist nicht mehr Quelle. `verify_boersenereignisse` 588/588.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 10 Zeilen.
