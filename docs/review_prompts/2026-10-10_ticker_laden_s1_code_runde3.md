# Ticker schneller laden — S1 Code-Runde 3: Lader `SA.kurse` nach Runde 2

Runde 2: [Prompt](2026-10-10_ticker_laden_s1_code_runde2.md) · [Antwort](2026-10-10_ticker_laden_s1_code_antwort2.md) (mit Auflagen).
Read-only, nichts schreiben, Mutationstest NICHT ausführen (er schreibt).

<task>Prüfe, ob die vier Auflagen aus Runde 2 erfüllt sind und Lader + Wächter als Grundlage der Seitenmigration
freigegeben werden können.</task>

## Umsetzung
1. **Frist schließt die Wartezeit in der Schlange ein** (`kurse.js` `holeBlock`): die Frist startet vor der
   Platzvergabe; läuft sie ab, nimmt `warten.entfernen()` den noch wartenden Eintrag aus der Schlange, danach
   Abbruch des Transports (falls schon gestartet). Abschnitt 19b: vier Transporte enden nie, die fünfte Anfrage
   scheitert an der Frist (< 1 s) — ohne `AbortController` und mit ignoriertem Abbruch; Abschnitt 19c: enden die vier
   später doch, fragt die abgelaufene Wartende nie an.
2. **Verspätete Veröffentlichung vor der Wiederholung** (Abschnitt 19): Prüfung bei 250 ms — die späte Antwort kam
   bei 150 ms, die Wiederholung frühestens nach 60 ms Frist + 350 ms Wartezeit. Mutation „Frist ignoriert" ist rot.
3. **Wächter verlangt Exit 0 und Endmarker** (`verify_kurse.py`): je Abschnitt Exit 0, JSON, `ende === true`.
4. **Isolation**: jeder der 26 Abschnitte läuft in einem **eigenen node-Prozess** (`--abschnitt <nr>`, Frist 20 s
   von außen). Ein Hänger ist ein benannter Befund dieses Abschnitts (die übrigen liefen vollständig, Endmarker
   bleibt) — auch der stille Hänger, bei dem node mit leerer Ereignisschleife und Exit 0 endet (`beforeExit`).
   Ein Abbruch (Exit ≠ 0, kein JSON, Absturz) unterdrückt den Endmarker. Eine unbehandelte Ablehnung ist ein
   Befund (`KursFehler`) bzw. `[Ausnahme]` (alles andere). Der Request-Vertrag wird je Abschnitt geprüft.

## Stand
`verify_kurse.py`: 26 Abschnitte, 110 Prüfungen, 0 rot, `PROBE-ENDE`. Mutationstest **31/31**, zweimal
identisch; Gegenproben (Anker fehlt, Absturz, eingefangener `TypeError`) richtig verworfen. Neue Mutationen:
abgelaufene Wartende bleibt in der Schlange · Frist startet erst mit dem Platz (zeigt sich als Hänger in 19b) ·
Frist ignoriert (verspätete Antwort veröffentlicht).

## Fokusfragen
1. Auflagen erfüllt? 2. Ist „Hänger = benannter Befund, Lauf vollständig" richtig, oder öffnet das ein Schlupfloch
(z. B. ein Abschnitt, der vor seinen Prüfungen hängt und dadurch eine erwartete Prüfung verdeckt)? 3. Freigabe?

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 30 Zeilen.
