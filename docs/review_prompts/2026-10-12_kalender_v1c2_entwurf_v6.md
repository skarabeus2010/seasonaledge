# Kalender-Umstellung V1c-2 — Entwurf v6 (US-Produkttermine OPEX und VIX)

Runde 5: [Entwurf v5](2026-10-12_kalender_v1c2_entwurf_v5.md) · [Antwort](2026-10-12_kalender_v1c2_entwurf_v5_antwort.md)
(P2 Projektionsgrenze). Alles aus v5 gilt, außer §2. Read-only.

<task>Ist der P2-Befund aus Runde 5 aufgelöst? Ist V1c-2 als Bauvorlage freigegeben?</task>

## §2 neu: Prüfdatum als Pflichtparameter der Abfrage
- Gespeichert (Python-Tabellen, Bundle, `produktversion`) werden nur **Fakten**: Regeln, belegte Monate je
  Belegreihe, `datenstand` je Reihe. Keine Einstufung `projektion`/Lücke — sonst hinge der Bundle-Inhalt am
  Erstellungstag, und `build_boersenkalender_js.py --pruefen` gegen HEAD wäre nicht reproduzierbar.
- Die Einstufung geschieht bei der Abfrage: `produkttermine(von, bis, art, *, pruefdatum)` (Python, Pflicht-
  argument ohne Standardwert) bzw. `SA.boersenkalender.produkttermine(von, bis, art, pruefdatum)` (JS, Pflicht;
  fehlt es → `KalenderFehler`). Regel je Feldgruppe:
  belegt → `belegt`; sonst **Regeltermin > `pruefdatum`** → `projektion`; sonst → Felder `null`, Grund
  `nicht_belegt`, in `abdeckung(pruefdatum)` gemeldet. Gleichheit (Regeltermin = Prüfdatum) → Lücke.
- `datenstand` dient nur der Aktualitätsprüfung: Wächter gelb, wenn `pruefdatum − datenstand > 200` Tage.
- Verbraucher (V3) übergeben das lokale Börsendatum des Aufrufs (`localDateStr`, nie `toISOString`); Wächter und
  Tests übergeben ein festes Datum.

## Wächterfälle (ersetzt v5 §3 b)
Datenstand 2025-06-30, Prüfdatum fest 2026-10-12: Monat 2025-09 ohne Beleg → Lücke (nicht Projektion);
Monat 2026-10 (Regeltermin 16.10.2026 > Prüfdatum) ohne Beleg → Projektion; Regeltermin = Prüfdatum → Lücke;
Monat 2027-01 → Projektion. Mutation „Vergleich mit `datenstand` statt `pruefdatum`" und „≥ statt >" müssen
gezielt an diesen Fällen scheitern. Python = JS für dieselben Fälle.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 12 Zeilen.
