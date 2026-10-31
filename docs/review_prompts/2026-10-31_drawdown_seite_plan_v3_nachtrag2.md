# Nachtrag 2 — fehlende Kurszeilen nur mit nachgewiesener Renditebrücke

Antwort Nachtrag 1: [..._nachtrag_antwort.md](2026-10-31_drawdown_seite_plan_v3_nachtrag_antwort.md) — NICHT
TRAGFÄHIG. Die Gegenbeispiele treffen: (1) Krypto ist immer `konvention`, eine fehlende Zeile eines −50-%-Tages
ließe die Episode verschwinden; (2) fehlende Zeilen am Reihenende ließen einen alten Wert als aktuell gelten.
Dein Befund 3 zeigt zugleich, was die echten Fehlstellen von deinem Gegenbeispiel unterscheidet: bei **allen 240
DAX- und 197 EURUSD-Paaren überbrückt der gespeicherte `log_return` der Folgezeile beide Tage** (Abweichung zu
ln(Schluss_nach/Schluss_vor) < 5·10⁻⁹). Der Indexpfad ist über die Fehlstelle also bekannt; unbekannt bleibt nur der
Schluss des fehlenden Tages selbst. In deinem Gegenbeispiel fehlt genau diese Brücke.

## Regel (ersetzt Nachtrag 1)
Eine fehlende Kurszeile an einer Kalendersitzung s wird **überbrückt** (s entfällt aus der Achse, die Rendite der
nächsten vorhandenen Sitzung trägt beide Tage), nur wenn ALLE Bedingungen gelten:
1. Kalenderstatus des Jahres von s ist `ungeprueft` oder `annahme` (nicht `belegt`, **nicht** CRYPTO; FOREX ist
   `konvention` und wird wie `annahme` behandelt, CRYPTO nie).
2. **Brücke nachgewiesen:** für die nächste vorhandene Zeile n und die vorige vorhandene Sitzungszeile v gilt
   |Σ log_return (Zeilen nach v bis n) − ln(close_n / close_v)| ≤ 1e-6, beide `close` > 0 und endlich.
3. Höchstens **2** aufeinanderfolgende fehlende Sitzungen (gemessen: Maximum in beiden Reihen = 2).
4. Die Fehlstelle liegt **nicht am Reihenende**: fehlt die Zeile an E oder an Sitzungen unmittelbar vor E ohne
   spätere vorhandene Zeile, ist der aktuelle Wert unbekannt (Status „nicht aktuell“, kein laufender Drawdown,
   keine Ränge) — unabhängig vom Kalenderstatus.
Sonst bleibt die Fehlstelle eine echte Lücke (globaler Pfad ab dort unbekannt, wie v3).

## Kennzeichnung
„n Sitzungen ohne Kurs überbrückt (Rendite der Folgezeile deckt beide Tage; ein Hoch oder Tief an genau diesen Tagen
ist nicht erfasst)“, mit Jahresbereich. Sitzungszählungen zählen die überbrückten Sitzungen nicht mit.

## Wächterfälle (zusätzlich)
Dein Krypto-Gegenbeispiel (−50 %, Zeile fehlt) → echte Lücke; dieselbe Fehlstelle mit korrekter Brücke in einem
`ungeprueft`-Jahr → überbrückt, Episode bleibt bis auf den unbeobachteten Tag erhalten; Brücke falsch (Abweichung
1e-3) → Lücke; drei aufeinanderfolgende → Lücke; fehlende Endzeilen → nicht aktuell; FOREX mit Brücke → überbrückt.

Frage: tragfähig? Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT TRAGFÄHIG.
