# Kalender-Umstellung V1c-3 — Code-Runde 1 (Halbtage)

Entwurf freigegeben in [v2](2026-10-12_kalender_v1c3_entwurf_v2.md) · [Antwort](2026-10-12_kalender_v1c3_entwurf_v2_antwort.md).
Auflagen v2: 2016 nur als Menge der Einzelbelege; Quellenstand reproduzierbar; Schema, Generator und JS-Decoder
gemeinsam; `sitzung` gegen einen unabhängigen Sollwert; unveränderte Momentaufnahme, Versionsprüfungen, wirksame
Mutationen. Read-only, Arbeitsbaum (nicht committet).

<task>Ist der Code V1c-3 freigegeben? Sind die Auflagen aus v2 erfüllt?</task>

## Dateien
- **neu** `shared/halbtage_belege.py` — `HALBTAGE["NYSE"]`: `schlusszeit "13:00"`, `zeitzone "America/New_York"`,
  `sitzung "nyse_aktien_kernhandel"`, `abruf 2026-10-12`, 31 Ereignisse (Datum → Kurzname + Quellenkennung je
  Mitteilung), `jahre_vollstaendig = 2014, 2015, 2017–2028` (2016 bewusst nicht). Namen DE/EN je Kurzname.
- `shared/kalender_quellen.py` — sieben Quellen (ICE-Mitteilungen 2013/2016/2017/2018/2021/2022, nyse.com) mit URL und
  Abrufdatum.
- `shared/boersenereignisse.py` — `Ereignis` hat `schlusszeit`/`zeitzone`/`sitzung` (Standard `None`, im `inhalt()`
  und damit in `ereignisversion`); `_halbtage(b, j)` erzeugt Ereignisse **nur** aus den Belegen (keine Regel), Kennung
  `NYSE:NYSE.halbtag.<kurz>:<datum>`, `art = "halbtag"`; `halbtag_status(b, j)`. `kompat`/`schliessungen` schließen
  Halbtage weiter aus.
- Generator/JS: Abweichungsschlüssel `z/tz/s` je Halbtag, Bundle `halbtage_vollstaendig`, JS-Objekte tragen die drei
  Felder (`null` bei Nicht-Halbtagen), `SA.boersenkalender.halbtag_status`.
- `scripts/verify_boersenereignisse.py` [Halbtag]: **unabhängige Jahres-Sollmengen** 2014–2028 (handgeschrieben,
  nicht importiert; 2016 nur Einzelbelege) für 1885–2100 verglichen; `halbtag_status` gegen eigene Sollmenge; keine
  Halbtage an anderen Börsen; jeder Halbtag offen, nicht in `get_holidays`/`schliessungen`; Zeit/Zone/Sitzung exakt;
  sieben Negativfälle; Nicht-Halbtage ohne die Felder; Uhrzeit-/Zonenänderung → `ereignisversion` anders,
  `kalenderversion` gleich. [Zwilling] vergleicht zusätzlich `halbtag_status`.

## Nachweise
Momentaufnahme 3 024 Börsen-Jahre 0 Abweichungen · `verify_boersenereignisse` 570/570 (23 865 Ereignisse) ·
Mutationstest 32/32 (+8 Halbtag: gelöscht, Uhrzeit, Zone, 2016 vollständig, als Schließung gezählt, ohne Beleg an
zweiter Börse, JS-Decoder ohne Schlusszeit, JS-Status) + 2 Gegenproben, Projektbaum unverändert ·
`verify_produkttermine` 96 · `verify_boersenkalender_js` 62 · V1c-2-Mutationen 18/18.
Eigener Fund: die erste Fassung der Mutation „ohne Beleg an anderen Börsen" war äquivalent (nur NYSE ruft
`_halbtage`) und blieb zu Recht grün — sie baut jetzt den Aufruf an einer zweiten Börse mit ein.

## Bewusst nicht in V1c-3
`markt_offen`/`letzte_session` bleiben bei der Betriebskonvention (Halbtag bis regulärem Schluss gesperrt) → V1d.
LSE-Halbtage → spätere Erweiterung (Seite hier nicht maschinell lesbar).

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2, Datei:Zeile) · **Auflagen**. ≤ 20 Zeilen.
