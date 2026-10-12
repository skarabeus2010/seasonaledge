# Kalender-Umstellung V1c-3 — Code-Runde 3 (Halbtage)

Runde 2: [Prompt](2026-10-12_kalender_v1c3_code_r2.md) · [Antwort](2026-10-12_kalender_v1c3_code_r2_antwort.md)
(P2: fünf ICE-Quellen ohne gesicherten Inhalt). Read-only, Arbeitsbaum.

<task>Ist der P2-Befund aus Runde 2 aufgelöst? Ist V1c-3 freigegeben? Bitte die neue Quellenwahl und die
Ausweitung auf 2013 und das nun vollständige 2016 ausdrücklich prüfen.</task>

## Quellen ersetzt: unveränderliche Archivfassungen der amtlichen NYSE-Kalenderseite
Die ICE-Mitteilungen sind nicht mehr Belegquelle (Abruf verweigert, kaum archiviert; als Gegenprobe erwähnt). Jede
Quelle ist jetzt eine **web.archive.org-Fassung** der NYSE-Kalenderseite (bis 2014 nyx.com), Inhalt per `id_`-Adresse
abgerufen und per SHA-256 gesichert; die Seite listet je Stand zwei bis drei Jahre:
nyx 2013-11-29 (2013–14) · nyse 2015-02-10 (2015–16) · 2016-02-04 (2016–17) · 2017-03-03 (2017–19) · 2018-02-02
(2018–20) · 2020-02-19 (2020–22) · 2021-02-08 (2021–23) · 2024-01-11 (2024–26) · nyse.com/trade 2026-10-12 (2026–28;
Archivfassung 2026-10-09 byte-identisch mit dem Direktabruf). Die abgerufenen Zeilen der Seiten nannten jeweils genau
die übernommenen Termine (z. B. 2015-02: 27.11.2015, 25.11.2016, 24.12.2015).
- `shared/kalender_quellen.py`: je Archiv `Archiv <id_-Adresse>; SHA-256 <…> (<Byte>)`.
- `docs/belege/nyse_halbtage_2026-10-12.md`: Tabelle Kennung, Archivadresse, Prüfsumme, Abdeckung, übernommene Termine.
- Wächter: für jede verwendete Quelle müssen Archivadresse und Prüfsumme in Quellentabelle **und** Sicherung
  übereinstimmen; Mutation „Prüfsumme weicht ab" gefangen.

## Abdeckung neu
`abdeckung` = Jahr → Archiv, dessen Seite das ganze Jahr listet: 2013–2028 lückenlos. **2013 neu** (nyx-Seite
listet 2013 vollständig: 03.07., 29.11., 24.12.). **2016 jetzt vollständig**: die Seite von Februar 2015 führt den
kompletten Kalender 2016 (einziger Halbtag 25.11.; 24.12. Samstag, 4.7. Montag). Vorher galt 2016 als ungeprüft,
weil die ICE-Mitteilung 2016 das Jahr nicht ab Januar abdeckte.

## Nachweise
`verify_boersenereignisse` 589/589 (23 868 Ereignisse) · Momentaufnahme unverändert · Mutationstest 35/35 + 2
Gegenproben, Projektbaum unverändert.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 12 Zeilen.
