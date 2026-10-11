# Kalender-Umstellung V1c — Entwurf v4 (Ereigniskatalog, vor dem Code)

Runde 3: [Entwurf v3](2026-10-11_kalender_v1c_entwurf_v3.md) · [Antwort](2026-10-11_kalender_v1c_entwurf_v3_antwort.md) (2 Befunde).
Alles aus v3 und früher gilt, außer den folgenden Punkten. Read-only.

<task>Sind die zwei Befunde aus Runde 3 aufgelöst? Ist V1c-1 als Bauvorlage freigegeben?</task>

## 1 Drei Daten und ein Ersatzgrund (P1 TSE-Projektion)
Jedes Ereignis trägt `nominal` (Regeltermin), `rechtlich` (der gesetzlich bestimmte Tag des Feiertags in diesem Jahr)
und `wirksam` (Schließungstag) sowie `ersatzgrund ∈ {keiner, wochenende, furikae, verlegung}`:
- normaler Feiertag: nominal = rechtlich = wirksam, `keiner`;
- LSE/NYSE-Ersatz (Wochenende): nominal = rechtlich (z. B. Sa 25.12.), wirksam = Ersatztag, `wochenende`;
- TSE-Furikae: nominal = rechtlich (So), wirksam = Folgetag, `furikae`;
- Verlegung (TSE-Olympia, LSE Early May 2020, Spring Bank 2002/2012/2022): nominal = Regeltermin, rechtlich =
  verlegter Tag, `verlegung`; liegt der verlegte Tag auf einem Sonntag (TSE Yama no Hi 2021: nominal 11.8., rechtlich
  So 8.8.), folgt Furikae: wirksam = 9.8., `ersatzgrund = furikae` mit `verlegt = true`.
- `art = ersatztag` genau dann, wenn wirksam ≠ nominal (Bezug über `regel_id` + `nominal`).

**Kompatibilitätsprojektion TSE** = `{wirksam} ∪ {rechtlich | ersatzgrund == furikae}` — der Sonntags-Feiertag bleibt
(heute so), der ursprüngliche Regeltermin einer Verlegung NIE. Alle anderen Börsen: `{wirksam}`. Geprüft gegen die
eingefrorene Momentaufnahme (liegt bereits vor: `scripts/fixtures/kalender_vor_v1c.json`, aus dem unveränderten Stand
erzeugt, 14 Börsen × 216 Jahre × 3 Prüfsummen; `scripts/kalender_momentaufnahme.py --pruefen`).

Sollfälle TSE: 2020 — Umi no Hi nominal 20.7., rechtlich = wirksam 23.7. (`verlegung`), 20.7. NICHT in
`get_holidays`; Sport no Hi nominal 12.10. → 24.7., 12.10. nicht drin. 2021 — Umi nominal 19.7. → 22.7.; Yama no Hi
nominal 11.8., rechtlich 8.8. (So), wirksam 9.8.: `get_holidays` enthält 8.8. und 9.8., nicht 11.8.;
`schliessungen` nur 9.8. 2023 — Ganjitsu nominal = rechtlich 1.1. (So), wirksam 2.1. (`furikae`): beide in
`get_holidays`, `schliessungen` nur 2.1.

## 2 Versionsvertrag (P2)
- `ereignisversion` = SHA-256 über die kanonische, vollständig aufgelöste Ereignisliste (alle Felder inkl. `nominal`,
  `rechtlich`, `wirksam`, `art`, `ersatzgrund`, `nominal_herkunft`, Namen DE/EN, Quellen) ohne Versionsfelder →
  **jede** Inhaltsänderung ändert sie.
- `kalenderversion` = SHA-256 über die Schließungsprojektion (`schliessungen` je Börse/Jahr) → ändert sich
  **genau dann**, wenn sich diese Projektion ändert.
- Tests: (a) reine Nominaldatumsänderung bei gleichem wirksamen Tag → ereignisversion anders, kalenderversion gleich;
  (b) Namens- bzw. Quellenänderung → dito; (c) Änderung eines wirksamen Werktags → beide anders; (d) Änderung eines
  wirksamen Wochenenddatums (außerhalb der Projektion) → nur ereignisversion.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
