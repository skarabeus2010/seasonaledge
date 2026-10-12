# Unabhängige Gegenprüfung der Halbtagsbelege NYSE (V1c-3) — 2026-10-12

Zwei eigens beauftragte Prüfagenten haben die Archivfassungen aus `nyse_halbtage_2026-10-12.md` ohne Kenntnis der
Katalogwerte selbst abgerufen (nur im Speicher, `py -3.14 -I`, urllib), die SHA-256 der Rohbytes berechnet, die
Fußnoten „close early" vollständig gelesen und die Jahresköpfe der Feiertagstabelle bestimmt. Das Internet Archive
drosselte mehrfach (HTTP 429); gewertet sind nur Antworten mit Status 200.

| Archivfassung | Status | Byte | SHA-256 = Sicherung | Tabellenjahre | Halbtage laut Fußnoten |
|---|---|---|---|---|---|
| nyx.com 2013-11-29 | 200 | 42 317 | ja | 2013, 2014 | 2013-07-03, 2013-11-29, 2013-12-24, 2014-07-03, 2014-11-28, 2014-12-24 |
| nyse.com 2015-02-10 | 200 | 30 312 | ja | 2015, 2016 | 2015-11-27, 2015-12-24, 2016-11-25 |
| nyse.com 2016-02-04 | 200 | 78 758 | ja | 2016, 2017 | 2016-11-25, 2017-07-03, 2017-11-24 |
| nyse.com 2017-03-03 | 200 | 232 865 | ja | 2017, 2018, 2019 | 2017-07-03, 2017-11-24, 2018-07-03, 2018-11-23, 2018-12-24, 2019-07-03, 2019-11-29, 2019-12-24 |
| nyse.com 2020-02-19 | 200 | 183 790 | ja | 2020, 2021, 2022 | 2020-11-27, 2020-12-24, 2021-11-26, 2022-11-25 |
| nyse.com 2021-02-08 | 200 | 93 533 | ja | 2021, 2022, 2023 | 2021-11-26, 2022-11-25, 2023-07-03, 2023-11-24 |
| nyse.com 2024-01-11 | 200 | 127 218 | ja | 2024, 2025, 2026 | 2024-07-03, 2024-11-29, 2024-12-24, 2025-07-03, 2025-11-28, 2025-12-24, 2026-11-27, 2026-12-24 |
| nyse.com/trade 2026-10-09 | 200 | 109 229 | ja | 2026, 2027, 2028 | 2026-11-27, 2026-12-24, 2027-11-26, 2028-07-03, 2028-11-24 |

Ergebnis: alle acht verwendeten Quellen byte-identisch mit der Sicherung; Halbtage je Jahr gleich der Sollmenge des
Wächters; jede zugeordnete Abdeckung (2013–2028) liegt in den Tabellenjahren der zugeordneten Seite. Die Seite
2024-01-11 nennt 2026-07-03 ausdrücklich als Vollschließung („Independence Day observed"), nicht als Halbtag.
Die früher genannte Fassung 2018-02-02 wird nicht mehr verwendet (2020 jetzt aus 2020-02-19).
