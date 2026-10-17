# Codex: Idee „Williams-Kursmuster in Morgen-Mail und Seiten“ (2026-10-17)

Nur lesen, nichts ändern. Bitte eine fachliche Einschätzung, kein Code.

## Idee des Nutzers
Die Kursmuster aus `docs/research/LARRY_WILLIAMS_INDIKATOREN.md` Abschnitt C (Nr. 20 Oops!, 21 Smash Day, 22 Hidden
Smash Day, 23 Specialist Trap, 24 Outside Day mit Abwärtsschluss, 25 Inside Day, 26 Marktstruktur-Hochs/-Tiefs) in die
tägliche Morgen-Mail aufnehmen — heute steht dort je Ticker nur Blast-Off (`shared/newsletter_indicators.py`,
`shared/daily_report.py`, Vorlage `scripts/templates/daily_report.html.j2`). Farbe grün = bullish, rot = bearish.
Und: dieselben Muster auch in die Analysen der Webseite einbauen.

## Kontext, den du prüfen sollst
- Projektregeln (CLAUDE.md): keine Kauf-/Verkaufssignale; „eine Farbskala ist eine Aussage“ (grün/rot wurde auf
  /skew, /intermarket und in der Mail-Skew-Spalte bewusst entfernt, Wächter `verify_skew_rang.py` Vorlage-Fall); der
  Saison-Score wurde validiert und zeigte keine Vorhersagekraft (Rangkorrelation 0,019) — Seiten sagen das jetzt.
- Belegstufen im Williams-Dokument: Oops/Smash/Inside B, Hidden Smash/Specialist Trap/Outside Day C; die zitierten
  Trefferquoten (93 %, 85 %) sind unbelegt. Muster 26 ist erst einen Tag später bekannt (Look-ahead).
- Daten: `prices` hat OHLC je Tag, aber (a) alte Index-Historien O=H=L=C, (b) heute gefunden: kopierte Zeilen an
  Handelstagen (Vortagsschluss fortgeschrieben, Volumen 0, z. B. SIE.DE 22.09.2025) — rund 100 je DAX-Titel seit 2000,
  (c) Krypto/FX/Futures ohne echte Eröffnungslücke (24-h-Handel), (d) Kurse dividendenbereinigt mit Stand beim
  Schreiben.
- Universum ~370 Ticker, Mail an Abonnenten, YMYL-Finanzseite.

## Fragen
1. Ist die Idee sinnvoll — und unter welchen Bedingungen? Was sind die größten Risiken (Signalwirkung, fehlender
   Beleg, Mehrfachtests über 6–7 Muster × 370 Ticker, Datenartefakte, Look-ahead, Lückenmuster ohne Lücken)?
2. Grün/rot: vertretbar oder nicht? Welche Darstellung wäre stattdessen ehrlich und trotzdem nützlich (z. B.
   „Richtung laut Williams“ + gemessene Statistik auf diesem Ticker: n, Folgerendite, Trefferquote vs. Basisrate)?
3. Welche Validierung gehört VOR die Veröffentlichung (Ereignisstudie, Horizonte, Basisrate, Hälften-Test,
   Korrektur für Mehrfachtests, Ausschluss kaputter Zeilen) — und welches Ergebnis würde gegen die Aufnahme sprechen?
4. Welche Muster eignen sich mit Tagesbalken überhaupt, welche nicht (Einstieg per Stopp am Folgetag)?
5. Webseite: wo passt es (Scanner-Spalte, Dashboard, eigene Seite als Ereignisstudie wie /index-effekt, Backtest-
   Engine als Ereignistyp)? Was nicht?
6. Reihenfolge der Arbeit (Phasen), und was du weglassen würdest.

Antwort auf Deutsch, knapp, mit einer klaren Empfehlung am Ende.
