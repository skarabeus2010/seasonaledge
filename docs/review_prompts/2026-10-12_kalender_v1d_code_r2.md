# Kalender-Umstellung V1d — Code-Runde 2 (Sitzungshelfer)

Runde 1: [Prompt](2026-10-12_kalender_v1d_code_r1.md) · [Antwort](2026-10-12_kalender_v1d_code_r1_antwort.md)
(3 × P2). Read-only, Arbeitsbaum (V1d-Dateien nicht committet; der Achsen-Commit `f760b34` ist davon unabhängig).

<task>Sind die drei Befunde aus Runde 1 aufgelöst? Ist V1d freigegeben?</task>

## P2 `heute` in JS (api.js `heuteBerechnen`)
ISO-Bestandteile werden VOR `Date.parse` geprüft: Datum (Monat 1–12, Tag ≤ Monatslänge), Stunde ≤ 23, Minute/Sekunde
≤ 59, Versatz-Stunde ≤ 23 und -Minute ≤ 59; Epoch nur als `Number.isSafeInteger`, Betrag ≤ 8,64e15. Fehler immer
`KalenderFehler`. Neue Fälle (Python und JS, Soll „FEHLER“): 30.02., 24:00, Versatz +25:00, Epoch 8640000000000001,
Epoch 1.5. Mutation „JS: heute rollt ungültiges Datum“ gefangen.

## P2 Abstürze sind kein Nachweis
`verify_sitzungen` sammelt jede unerwartete Ausnahme (Python und JS, Raster `X` und Fälle `absturz`) und meldet sie
als `FEHL [Absturz] …`. Die gemeinsame Mechanik `verify_boersenereignisse_mutation.auswerten` wertet jeden Lauf mit
`[Absturz]` als **ungültig** (gilt damit für alle Mutationstests auf dieser Mechanik). Neue Gegenprobe: absichtlicher
`RuntimeError` in `sitzung_info` → „richtig verworfen“.

## P2 JS-`sitzungen` vollständig
Die Probe liefert je Börse `K.sitzungen('1885-01-01','2100-12-31',b)`; der Wächter vergleicht sie mit der
numpy-Referenzfolge (UTC und Pacific/Kiritimati). Mutation „JS: sitzungen lässt den Rand weg“ gefangen.

## Nachweise
`verify_sitzungen` 445/445 · Mutationstest 16/16 + 3 Gegenproben verworfen, Projektbaum unverändert ·
`verify_boersenkalender_js` 62/62.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 12 Zeilen.
