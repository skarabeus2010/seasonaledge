# Kalender-Umstellung V1c-3 — Code-Runde 2 (Halbtage)

Runde 1: [Prompt](2026-10-12_kalender_v1c3_code_r1.md) · [Antwort](2026-10-12_kalender_v1c3_code_r1_antwort.md)
(2 × P2). Read-only, Arbeitsbaum.

<task>Sind beide Befunde aus Runde 1 aufgelöst? Ist V1c-3 freigegeben?</task>

## P2 Quellenstand reproduzierbar
Neu `docs/belege/nyse_halbtage_2026-10-12.md`: je Quelle Adresse, Abrufweg, Sicherung und die übernommenen Fakten
(Datum, Uhrzeit; bewusst keine wörtlichen Absätze). NYSE-Seite direkt abgerufen: SHA-256 des Inhalts
`79602f7b…19bad` (109 229 Byte) + Archivfassung web.archive.org 2026-10-09. ICE-Mitteilungen verweigern den direkten
Abruf (HTTP 403) — dort Abrufweg „Abrufwerkzeug", Archivfassung nur für ice2021 gefunden; die Grenze ist in der
Datei benannt (Pflege halbjährlich, Archive erneut suchen). Jede Quellenkennung in `shared/kalender_quellen.py`
verweist auf die Sicherung. Wächter: Sicherung existiert, nennt jede Quellenkennung und jeden Halbtag und die
NYSE-Prüfsumme.

## P2 Jahresabdeckung als eigener Beleg
`HALBTAGE["NYSE"]["abdeckung"]`: Jahr → Quelle, die das ganze Jahr nennt (2014/15 ice2013, 2017 ice2016, 2018
ice2017, 2019–2021 ice2018, 2022 ice2021, 2023–2025 ice2022, 2026–2028 nyse2026); `halbtag_status` liest nur daraus,
2016 fehlt. Wächter: unabhängige Soll-Zuordnung Jahr → Quelle (handgeschrieben), jede Quelle mit Abrufdatum in der
Quellentabelle. Mutationen „2016 fälschlich vollständig", „Abdeckungsquelle falsch zugeordnet", „Sicherung fehlt"
gefangen.

## Nachweise
`verify_boersenereignisse` 575/575 · Momentaufnahme unverändert · Mutationstest 34/34 + 2 Gegenproben, Projektbaum
unverändert (die isolierte Kopie enthält jetzt `docs/belege/`).

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 12 Zeilen.
