# Kalender-Umstellung V1c-1 — Code-Runde 2

Runde 1: [Prompt](2026-10-12_kalender_v1c_code_r1.md) · [Antwort](2026-10-12_kalender_v1c_code_r1_antwort.md) (2 × P2).
Read-only, Arbeitsbaum.

<task>Sind beide Befunde aus Runde 1 aufgelöst? Ist V1c-1 freigegeben?</task>

## P2 kalenderversion am Ereignis
- `Ereignis.inhalt()` = aufgelöster Inhalt ohne Versionsfelder (Grundlage der `ereignisversion`);
  `Ereignis.als_dict()` = `inhalt()` + `kalenderversion` (Hash der Schließungsprojektion des ganzen Katalogs,
  `_kalenderversion_gesamt()`, gecacht). JS-Objekte tragen `kalenderversion: DATEN.kalenderversion`.
- Wächter [Invariante]: jedes Objekt trägt die aktuelle `kalenderversion()`, `inhalt()` enthält sie nicht,
  `ereignisversion()` == unabhängig gebildeter Hash über die Inhalte. [Zwilling] vergleicht `als_dict()` inkl. Version.
  Mutationen: „ereignisversion hasht die Version mit" → [Invariante], „JS ohne kalenderversion" → [Zwilling].

## P2 Jubiläumsidentitäten 2002/2012
- Sollfälle mit Quelle: 2002 `LSE.spring_bank` nominal 27.5. → rechtlich = wirksam 4.6. (`verlegung`),
  `LSE.sonder.2002-06-03_golden_jubilee`; 2012 nominal 28.5. → 4.6., `LSE.sonder.2012-06-05_diamond_jubilee`.
- Mutationen „2002 vertauscht" und „2012 vertauscht" (Schließungsmenge gleich, Bundle in der Kopie neu erzeugt)
  → beide [Sollfall].

## Nachweise
`verify_boersenereignisse.py` 229/229 · Mutationstest 24/24 + 2 Gegenproben verworfen, Projektbaum unverändert ·
`kalender_momentaufnahme --pruefen` 0 Abweichungen · `verify_boersenkalender_js` 62/62.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
