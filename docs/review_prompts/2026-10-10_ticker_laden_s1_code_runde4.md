# Ticker schneller laden — S1 Code-Runde 4: Abnahme des Laders `SA.kurse`

Runde 3: [Prompt](2026-10-10_ticker_laden_s1_code_runde3.md) · [Antwort](2026-10-10_ticker_laden_s1_code_antwort3.md) (mit Auflagen).
Read-only, nichts schreiben, Mutationstest NICHT ausführen.

<task>Prüfe die zwei Auflagen aus Runde 3 und gib Lader + Wächter frei oder nenne, was fehlt.</task>

## Umsetzung
1. **Kein `.catch(x => x)` mehr** in der Probe: Abschnitt 10b nutzt `ergebnisOderFehler`, das wie `fehlerVon` jeden
   Nicht-`KursFehler` als `[Ausnahme]` erfasst. Gegenprobe „eingefangener TypeError in der Sicht" (Absturz beim
   Lesen von `open` genau in 10b) wird jetzt als ungültig verworfen.
2. **Ereignisschleife vor dem Abschluss**: nach dem Abschnitt `setTimeout(20)` + `setImmediate`, dann erst
   `ausgeben`. Gegenprobe „unbehandelte TypeError-Ablehnung" (in `laden()`, trifft jeden Abschnitt) wird
   verworfen.

## Stand
`verify_kurse.py`: 26 Abschnitte, 110 Prüfungen, 0 rot, `PROBE-ENDE`. Mutationstest zweimal **31/31**, fünf
Gegenproben (Anker fehlt, Absturz, eingefangener TypeError in der Sicht, unbehandelte TypeError-Ablehnung,
eingefangener Absturz im Teilfehler-Pfad) jeweils richtig verworfen.

## Ausgabevertrag
**Urteil** (Freigabe / mit Auflagen) · **Befunde** · **Auflagen**. ≤ 25 Zeilen.
