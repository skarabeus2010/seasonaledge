# Kalender-Umstellung V1c-2 — Code-Runde 2

Runde 1: [Prompt](2026-10-12_kalender_v1c2_code_r1.md) · [Antwort](2026-10-12_kalender_v1c2_code_r1_antwort.md)
(2 × P2 + Auflagen). Read-only, Arbeitsbaum.

<task>Sind die Befunde und Auflagen aus Runde 1 erfüllt? Ist V1c-2 freigegeben?</task>

## P2 Produktversion
`produktversion()` hasht jetzt Termine je Monat (inkl. Triple-Kennzeichen), Grenzen `OPEX_AB/VIX_AB/BIS/VIX_BIS`,
`TRIPLE_MONATE` (neue Konstante, Python und JS-Bundle nutzen sie), Kalenderannahme/-status, Regelstände, Belege.
Wächter [Version]: je Änderung von `TRIPLE_MONATE`, `KALENDERSTATUS`, `VIX_BIS`, `REGELSTAND_OPEX` muss die Version
abweichen. Mutation „Triple-Monate nicht in der Version" entfernt **beide** Stellen (je Monat + Konstante) — nur eine
zu entfernen ist äquivalent und blieb im ersten Lauf zu Recht grün.

## P2 Unsicherheit und Herkunft am Objekt
Jedes Ereignis (Python und JS) trägt `kalenderannahme = "cboe_rth_gleich_nyse"`, `kalenderstatus = "annahme"`;
OPEX `quelle` ∈ {SPX_STANDARD, regel}; VIX `quelle_futures` ∈ {VX, regel, None}, `quelle_optionen` ∈ {VIX_OPT, regel,
None} je Feldgruppe. Wächter [Herkunft] prüft die Werte unabhängig (belegt, Projektion, Lücke); Mutationen
„Kalenderannahme fehlt (Python und JS)" und „JS: Optionsquelle aus VX" gefangen.

## Belege unabhängig bestätigt
Zweite, **blinde** Ablesung der sieben Kalender-PDFs durch einen eigenen Agenten ohne meine Werte: 0 Abweichungen
in 168 Werten (SPX_STANDARD + VIX_OPT 2020–2026). Unsichere Mischzellen dort benannt (2022-03/06, 2024-06,
2025-03/04/06, 2026-05/06) und in `produkttermine_listung.py` dokumentiert; beide Ablesungen lasen sie gleich.
VX: Dateiname = Settlementtag; „HTTP 403" heißt jetzt „kein positiver Listungsnachweis".

## OPEX-Momentaufnahme
Wird vor dem V3-Umbau eingefroren (als Posten in docs/KALENDER_UMSTELLUNG.md eingetragen).

## Nachweise
`verify_produkttermine.py` 96/96 · Mutationstest 18/18 + 2 Gegenproben verworfen, Projektbaum unverändert ·
`verify_boersenereignisse` 229/229 · `verify_boersenkalender_js` 62/62 · V1c-1-Mutationstest 24/24 (geteilte
Mechanik).

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
