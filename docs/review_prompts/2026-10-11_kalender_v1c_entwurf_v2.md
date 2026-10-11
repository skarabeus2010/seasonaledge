# Kalender-Umstellung V1c — Entwurf v2 (Ereigniskatalog, vor dem Code)

Runde 1: [Entwurf](2026-10-11_kalender_v1c_entwurf.md) · [Antwort](2026-10-11_kalender_v1c_entwurf_antwort1.md) (6 Befunde, Antworten 1–4).
Alles aus v1 gilt, außer den folgenden Punkten. Antworten 1–4 übernommen (verschobener Regeltermin = `ersatztag`,
zusätzlicher Tag = `sonderschliessung`, je Jahr belegt; Wochenendereignis erscheint; Snapshot + Offenheit + vier
Nummern; `halbtage: ungeprüft` nur Zwischenstatus). Read-only.

<task>Sind die Befunde aus Runde 1 aufgelöst? Ist V1c-1 als Bauvorlage freigegeben?</task>

## 1 Identität: genau ein Ereignis je Regeltermin (P1 Kennung)
- `ereignis_id = "<boerse>:<regel_id>:<nominal ISO>"`; ein Ereignis trägt `nominal` UND `wirksam`. `art = feiertag`
  wenn `wirksam == nominal`, `art = ersatztag` wenn dieselbe Regel auf einen anderen Tag wirkt (Bezug = gleiche
  `regel_id` + `nominal`), `sonderschliessung` für zusätzliche Tage mit eigener `regel_id`
  (`LSE.sonder.2022-06-03_platinjubilaeum`). Kein zweites Ereignis für den Ersatz → keine Kollision.
- **Mehrtägig:** je Schließungstag ein Ereignis mit eigener `regel_id` (`TSE.jahreswechsel_0102`, `…_0103`).
- **Mehrere Regeln am selben Tag** (z. B. Stockholm 2008-05-01: 1. Mai und Himmelfahrt): zwei Ereignisse, zwei
  Kennungen, ein wirksamer Tag — die Schließungsprojektion zählt ihn einmal.
- **Jahreszuordnung:** ein Ereignis gehört zum Jahr seines `nominal`; Bundle trägt volle Daten (YYYYMMDD).
- **NASDAQ:** Alias — `ereignisse("NASDAQ", j)` liefert die NYSE-Ereignisse unverändert (`boerse = "NYSE"`, gleiche
  Kennungen); dokumentiert, im Wächter geprüft.

## 2 API erhalten, Schließung als eigene Projektion (P1 Bestandsschutz)
- `get_holidays`/`is_holiday`/`is_trading_day` bleiben **unverändert** (inkl. Wochenenddaten), werden aber aus
  denselben Regeltabellen gespeist: `get_holidays = {e.wirksam | art ∈ {feiertag, ersatztag, sonderschliessung,
  unbestimmt}}` — exakt die heutige Menge.
- Neu `schliessungen(boerse, von, bis)` = eindeutige wirksame Vollschließungen auf sonst offenen Tagen (Mo–Fr bzw.
  täglich bei CRYPTO), Halbtage ausgeschlossen (B4.4, Antwort 2).
- **Bestandsschutz** gegen eine aus HEAD erzeugte, eingefrorene Momentaufnahme 1885–2100 je Börse:
  (a) `get_holidays`-Menge je Jahr, (b) `is_trading_day` je Tag, (c) alle vier Handelstagnummern je Tag
  (`handelstag_nummern`) — als Prüfsummen je Börse/Jahr in `scripts/fixtures/kalender_vor_v1c.json`.

## 3 Tabellen ohne Regel: keine geratene Identität (P1 Quellen)
- HKEX/KRX 2016–2026 sind Datumstabellen (teils einst aus Kurslücken). Jeder Eintrag wird ein Ereignis mit
  `art = unbestimmt`, `regel_id = "<B>.tabelle"`, `name = null`, `quelle = "<B>_tabelle_<jahr>"` (B4.10: nichts
  raten). Er zählt als Schließung (Bestandsschutz). Der Katalog-Status je Börse/Jahr bekommt das Feld
  `identitaet ∈ {regel, tabelle}`; alle `tabelle`-Jahre stehen im Wächter als **benannte Abnahmelücke** (Liste,
  nicht stillschweigend grün). Die Fallback-Jahre außerhalb der Tabelle haben Regeln (Neujahr …) mit Status
  `konvention` wie heute.
- Jedes Ereignis trägt `quelle` (Kennung in einer Quellentabelle `shared/kalender_quellen.py`: Titel, URL/Beleg,
  Abrufdatum) — übernommen aus den bestehenden Codekommentaren und Belegdateien; wo nur „Regel ohne Einzelbeleg"
  existiert, `quelle = "<B>.regelwerk"` mit dem Regelwerksbeleg.

## 4 Transport (P1 Bundle) und Versionen (P2)
- Bundle: `ereignisse[boerse][jahr] = [[regel_id, art, nominal YYYYMMDD, wirksam YYYYMMDD, name_idx|-1,
  quelle_idx]]`, dazu `namen` (DE/EN), `quellen`, `status` (bestehend) + `identitaet`. Die JS-API rekonstruiert
  `ereignis_id` nach derselben Formel; Python liefert dieselbe Struktur über `als_dict()`.
- Versionen: `kalenderversion` = Hash über die Schließungsmengen (unabhängig vom Katalog); `ereignisversion` = Hash
  über die Ereignislisten OHNE Versionsfelder; Ereignisse tragen nur `kalenderversion` (keine Selbstreferenz). Der
  Bundle-Gesamthash bleibt Hash über alles.

## 5 Prüfmatrix B4 → Teilphasen (P2 Abnahmeumfang)
| B4 | V1c-1 | V1c-2 | V1c-3 | V3/V4 (Verbraucher) |
|---|---|---|---|---|
| 1 Felder | ✓ | ✓ (Produkte) | ✓ | |
| 2 Arten | feiertag/ersatztag/sonder/unbestimmt | | halbtag (offen) | |
| 3 Identität statt Position | Katalog + Bundle | | | Seiten, Mails |
| 4 Ersatzbezug, Schließungszahl | ✓ (Projektion) | | ✓ (Halbtag ausgeschlossen) | |
| 5–7 Ticker unabhängig, t0, Anker | | | | ✓ |
| 8–9 OPEX/VIX | | ✓ | | ✓ |
| 10 gleiche Kennungen | Katalog, Bundle, Python=JS | | | JSON/DB/ICS/Mails/Seiten |

## 6 Unabhängige Sollfälle (handgeschrieben mit Quelle, nicht aus dem Code abgeleitet)
LSE 2021 (25.12. Sa → 27.12. Mo `christmas`-Ersatz, 26.12. So → 28.12. Di `boxing`-Ersatz), LSE 2022 (26.12. Mo
`boxing` Feiertag, 27.12. Di `christmas`-Ersatz — gov.uk), LSE 2020 Early May → 8.5. Ersatz, LSE 2022 Spring Bank →
2.6. Ersatz + 3.6. Sonderschließung, NYSE 2025-01-09 Sonderschließung (nicht MLK), TSE Furikae (2023-01-02) und
Kokumin no Kyujitsu (2015-09-22), TSE Jahreswechsel 31.12./2.1./3.1., XETRA 25.12.2021 (Sa, Ereignis ja,
Schließung nein), Stockholm 2008-05-01 (zwei Regeln, eine Schließung), Jahresgrenze LSE 2022-01-03 (Neujahr Sa →
Mo, `nominal` 2022-01-01). Python = JS als **vollständige Objektgleichheit** je Börse/Jahr 1885–2100.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 30 Zeilen.
