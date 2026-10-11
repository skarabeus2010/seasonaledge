# Kalender-Umstellung V1c-2 — Entwurf v5 (US-Produkttermine OPEX und VIX)

Runde 4: [Entwurf v4](2026-10-12_kalender_v1c2_entwurf_v4.md) · [Antwort](2026-10-12_kalender_v1c2_entwurf_v4_antwort.md)
(1 × P1, 1 × P2). Alles aus v4 gilt, außer den folgenden Punkten. Read-only.

<task>Sind beide Befunde aus Runde 4 aufgelöst? Ist V1c-2 als Bauvorlage freigegeben?</task>

## 1 Drei Listungen, getrennt geführt (P1)
`shared/produkttermine_listung.py` führt **drei** unabhängige Belegreihen mit je eigener Quelle und eigenem
Datenstand: `SPX_STANDARD` (Monatsserien), `VX` (Futures), `VIX_OPT` (Optionen). Jedes Feld hängt an genau einer:
- OPEX-Felder ← `SPX_STANDARD`;
- `settlement`, `handelsende_futures` ← `VX`;
- `handelsende_optionen` (und ein künftiges Optionssettlement) ← `VIX_OPT`.
Ist ein Kontraktmonat in `VX` belegt, in `VIX_OPT` aber nicht, bleiben die Futures-Felder gefüllt und die
Optionsfelder `null` mit Grund `listung_optionen_ungeprueft`. Ein Ereignis existiert, sobald **mindestens eine**
seiner Belegreihen den Monat belegt (oder §2 ihn als Projektion zulässt); jede Feldgruppe trägt ihren eigenen
`listung`-Status (`belegt` / `projektion` / `ungeprueft`).

## 2 Projektion nur für die Zukunft (P2)
Jede Belegreihe hat `datenstand` (Datum der Erhebung). Für einen Monat gilt:
- belegt in der Reihe → `belegt`;
- nicht belegt und **Regeltermin > `datenstand`** → `projektion` (nach geltender Regel);
- nicht belegt und Regeltermin ≤ `datenstand` → **Lücke**: Felder `null`, Grund `nicht_belegt`, in `abdeckung()`
  gemeldet.
Damit wird ein historischer Nachlauf nach einem veralteten Datenstand nie zur Projektion. Der Wächter meldet
außerdem, wenn ein `datenstand` älter als 200 Tage ist (gelb, nicht rot).

## 3 Zusätzliche Wächterfälle
(a) VX belegt, VIX_OPT nicht → Futures gefüllt, Optionen `null`; (b) Datenstand 2025-06, Monat 2025-09 ohne Beleg →
Lücke, nicht Projektion; Monat 2027-01 → Projektion; (c) Bestand der Belegreihen vor der Code-Abnahme vollständig
erhoben (Quelle + Abrufdatum je Reihe); wo nicht vollständig erhebbar, beginnt die Abdeckung später und die
Abdeckungslücke ist gelistet.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
