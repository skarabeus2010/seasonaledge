# P1b isoliert — Code-Review Runde 4 (Abnahme)

Runde 3: [Prompt](2026-10-10_kalender_p1b_code_runde3.md) · [Antwort](2026-10-10_kalender_p1b_code_antwort3.md) — mit Auflagen.

<task>Prüfe, ob die Auflage erfüllt ist und nichts Neues kaputtging. Read-only. Neue Dateien + `git diff`.</task>

## Umsetzung
Abstürze werden jetzt in **allen sechs Zonen** gekennzeichnet: für jede Nicht-UTC-Zone läuft dieselbe
Klassifikation über alle Aufrufe (`art != 'api'` → `[Ausnahme] API <Zone> …`), bevor die Zonen per Hash mit
UTC verglichen werden. Neue Gegenprobe: `TypeError('boersenkalender: getarnt')` nur bei Offset −780
(Pacific/Apia) im Golden-Week-Pfad → richtig verworfen.
Ergebnis: Wächter **62/62**; Bundle-Mutationen **13/13** in zwei vollständigen Läufen; Gegenproben **6/6**.

## Fragen
1. Auflage erfüllt? 2. Sonst etwas vor dem Commit?

## Ausgabevertrag
**Urteil** · **Befunde** · **Antworten**. ≤ 25 Zeilen.
