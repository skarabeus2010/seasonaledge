# Codex-Code-Review: Williams-Kursmuster, Runde 3 (2026-10-17)

Nur lesen. Runde 2: [Antwort, ein Befund](2026-10-17_williams_muster_code_r2_antwort.md) — Feinziehung der N-Familie
prüfte gegen `holm(nps)` statt gegen die bereinigte Familie.

## Änderung
`netto_ps()` (p = None ohne (b)), `netto_familie()` = Holm darüber, neu `fein_noetig(ps, hl, nps, b)` prüft H und N mit
denselben bereinigten Schwellen wie die Entscheidung; `pruefzeitraum()` ruft nur noch `fein_noetig`. Wächterfall mit
deinem Beispiel (N2 0,007 / N4 0,00001 ohne (b) → Feinziehung), Mutation „Feinziehung mit unbereinigter N-Familie“;
Mutationstest 23/23.

Ist der Befund behoben, gibt es neue Probleme? Am Ende **FREIGABE** oder **KEINE FREIGABE**.
