# Kalender-Umstellung V1c — Entwurf v3 (Ereigniskatalog, vor dem Code)

Runde 2: [Entwurf v2](2026-10-11_kalender_v1c_entwurf_v2.md) · [Antwort](2026-10-11_kalender_v1c_entwurf_v2_antwort.md) (3 Befunde).
Alles aus v2/v1 gilt, außer den folgenden Punkten. Read-only.

<task>Sind die drei Befunde aus Runde 2 aufgelöst? Ist V1c-1 als Bauvorlage freigegeben?</task>

## 1 Kompatibilitätsprojektion je Börse (P1 TSE)
`get_holidays`/`is_holiday` werden NICHT pauschal aus `wirksam` gebildet, sondern über eine **ausdrückliche
Projektion je Börse**, die die heutige Menge aus denselben Regeln nachbildet:
`kompat(boerse, ereignisse) = {e.wirksam | e.art ≠ halbtag} ∪ {e.nominal | e.art == ersatztag und boerse ∈
NOMINAL_BLEIBT}` mit `NOMINAL_BLEIBT = {"TSE"}` (heute: der Sonntags-Feiertag bleibt in der Menge und der
Furikae-Tag kommt hinzu, z. B. 2023-01-01 und 2023-01-02). Für alle anderen Börsen enthält die heutige Menge nur
den wirksamen Tag (LSE 25.12.2021 Sa fehlt heute, 27.12. ist drin) — die Liste ist kein Annahmewerk, sondern wird
gegen die eingefrorene Momentaufnahme geprüft; weicht eine Börse ab, ist der Umbau rot. `schliessungen()` bleibt
die fachliche Projektion (nur wirksam, nur sonst offene Tage).

## 2 Tabellenereignisse: technische Datumskonvention (P1)
- Feld `nominal_herkunft ∈ {regel, tabelle}`. Für Tabellenereignisse gilt `nominal = wirksam = eingetragenes Datum`
  und `nominal_herkunft = "tabelle"` — ausdrücklich **kein** Beleg, dass dieses Datum der nominale Feiertag ist
  (ein Ersatztermin kann darunter sein). Seiten/Mails dürfen ein `tabelle`-Datum nie als „Feiertag am …" ausgeben,
  nur als „geschlossen (Tabelle)".
- Kennung `"<B>:tabelle:<eingetragenes Datum ISO>"`; rekonstruierbar, eindeutig je Börse (ein Tabelleneintrag je Tag).
- `art = unbestimmt`, `name = null`, `quelle = "<B>_tabelle_<jahr>"`; Status `identitaet = tabelle` → benannte
  Abnahmelücke.

## 3 Ereignisversion über aufgelöste Inhalte (P2)
`ereignisversion` = SHA-256 über die kanonische JSON-Form aller Ereignisse mit **aufgelösten** Namen (DE/EN) und
Quellen (Titel, Beleg, Abrufdatum) statt Indizes, ohne Versionsfelder. `kalenderversion` = Hash über die
Schließungsprojektion. Eine reine Namens- oder Quellenänderung ändert `ereignisversion`, nicht `kalenderversion`;
eine Datumsänderung beide.

## 4 Zusätzliche Sollfälle
TSE 2023: Ereignis `TSE.ganjitsu`, nominal 2023-01-01, wirksam 2023-01-02, `ersatztag`; `get_holidays` enthält
beide Tage, `schliessungen` nur den 2.1. · KRX 2024-04-10 (Parlamentswahl, Tabelle): `art = unbestimmt`,
`nominal_herkunft = tabelle`, Kennung `KRX:tabelle:2024-04-10`, kein Name · reine Namensänderung (im Test: Name
eines Ereignisses umbenannt) → `ereignisversion` anders, `kalenderversion` gleich; reine Quellenänderung ebenso.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 20 Zeilen.
