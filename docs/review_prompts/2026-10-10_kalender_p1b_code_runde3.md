# P1b isoliert — Code-Review Runde 3 (Abnahme)

Runde 2: [Prompt](2026-10-10_kalender_p1b_code_runde2.md) · [Antwort](2026-10-10_kalender_p1b_code_antwort2.md) — mit Auflagen.

<task>Prüfe, ob die zwei Auflagen erfüllt sind und nichts Neues kaputtging. Read-only. Neue Dateien + `git diff`.</task>

## Umsetzung
1. **Ausnahmen über die Klasse**: `api.js` wirft gewollte Fehler als `KalenderFehler` (eigene Klasse,
   exportiert als `SA.boersenkalender.Fehler`). Die Probe meldet je Ausnahme `art: 'api'` (instanceof) oder
   `'absturz'`. Der Wächter macht aus **jedem** Absturz einen `[Ausnahme]`-Befund — auch an Stellen, an denen ein
   Fehler erwartet war. Neue Gegenproben: `null.x` statt des Datenende-Fehlers; `throw new TypeError('boersenkalender: …')`
   im Golden-Week-Pfad — beide richtig verworfen.
2. **Traversierungsfehler**: Isolationssuche als Funktion `isolation_scan(walk=os.walk)` mit `onerror` → Lesefehler;
   eingebaute Gegenprobe mit einem `walk`, der `PermissionError` über `onerror` meldet → Prüfung
   „Isolation meldet Traversierungsfehler“.
Ergebnis: Wächter **62/62**; Bundle-Mutationen **13/13** in zwei vollständigen Läufen, Gegenproben **5/5**.
Bundle neu erzeugt (137 155 B).

## Fragen
1. Auflagen erfüllt? 2. Sonst etwas vor dem Commit?

## Ausgabevertrag
**Urteil** · **Befunde** · **Antworten**. ≤ 30 Zeilen.
