# Entwurf v4: unplausible Punkte in der Skew-Historie — Auswertung des Trockenlaufs (Plan)

Read-only, Repo `C:\dev\Seasonaledge`. Vorgänger: `2026-10-13_skew_ausreisser_plan_v2.md` + `_antwort`,
`..._phase0_antwort.md` (dein Auftrag: Schwellen an „entwicklung“ ableiten, an „pruefung“ prüfen; Varianten getrennt;
„keine belastbare Ausschlussregel gefunden“ ist ein zulässiges Ergebnis). Deutsch, Datei:Zeile, am Ende
**FREIGABE (Plan): ja/nein**.

## Messbasis
- Trockenlauf 13.10. (`scripts/research/skew_trockenlauf_probe.py`, Seed 20261013, Fenster 2025-10-13…2026-10-12):
  337 Fälle, 336 auswertbar (XLF 19.06.2026 kein Handelstag). Mengen: entwicklung 156, pruefung 163, bekannt 6,
  kontrolle_earnings 7, kontrolle_verfall 5. Acht Ticker: SPY, AAPL, XLF, JPM, BAC, C, GS, MS.
- Referenzverteilung je Ticker: Live-`options_skew_history.json` vom 16.10. (nur `cm`/`cm_extrap`, Fenster wie oben,
  n = 138…233 je Ticker). Hinweis: nicht die am 13.10. eingefrorene Datei — zwischen beiden liegen B1 (Sperre) und die
  ETHA-Reparatur; die acht Ticker sind davon nicht betroffen, die Zeilen im Fenster unverändert bis auf neue Tage.
- Auswertung: `scripts/research/skew_trockenlauf_auswertung.py` (neu, rein lesend). Auffällig = |skew − Median|/MAD
  (roh, MAD 0 → 0,1) > 6, zusätzlich > 4 berichtet. Simulation: Live nimmt die erste Kandidatengruppe (Rangfolge) mit
  zwei gültigen Legs — **geprüft an 261/261 rankbaren Fällen**. Eine Regel verwirft eine Gruppe, dann gilt die nächste;
  bleibt keine, ist der Tag nicht rankbar.
- Merkmale der gewählten Gruppe (nur Legs mit Gewicht ≠ 0): h = max(0, −w, w − 1); V = kleinstes Volumen der 25Δ-Flügel;
  D = größter Delta-Abstand der Flügel; N = kleinste Kontraktzahl in der Zielregion (Call/Put); K = größter Abstand der
  ATM-Klammer zum Forward (einseitig = ∞).

## Ergebnisse
**1. Auffälligkeit ist selten.** Basis (heutige Auswahl): entwicklung 1/124 rankbar > 6 MAD (5 > 4), pruefung 1/125
(5 > 4). Kontrollen Earnings 0/5, Verfall 0/3 > 6 (Verfall 1 > 4: SPY 18.03.2026, Klammer, Volumen 738).

**2. Die Häufung ist mit einer Marktbewegung vereinbar; ein Messfehler ist damit nicht ausgeschlossen** (Formulierung
nach Codex — taggleich ist nur SPY/XLF am 07.04.). Von 10 Zufallsfällen > 4 MAD liegen 6 im März/April 2026
(SPY 13./16.03., 07.04.; JPM 24./30.03.; XLF 07.04.) — mehrere Ticker gleichzeitig, Klammer ohne Extrapolation (h = 0),
dicke Flügel (Volumen 18…1640). Der einzige Entwicklungsfall > 6 (JPM 30.03.2026, z 7,0) gehört dazu.

**3. Keine Regel trennt in der Entwicklungsmenge.** Jede Kombination im Raster (H × V × D × N × K, 810 Varianten), die
den einen Entwicklungsfall > 6 entfernt, verliert dafür ≥ 47 von 123 unauffälligen rankbaren Tagen (günstigste: D ≤ 0,04,
rankbar 76/156). *Korrigiert nach Codex-Antwort: zuerst stand hier ≥ 59 — die Sortierung priorisierte zusätzlich das
Ergebnis über 4 MAD; außerdem fehlten in der Simulation Abstandsschutz (15 Tage) und Interpolationsprüfung der
Produktion, und C 29.10.2025 stand doppelt in „bekannt“. Beides behoben, Einzelregeln unverändert.*
Einzelregeln entwicklung / pruefung (rankbar, weg > 6, weg > 4, verlorene unauffällige):
| Regel | entwicklung | pruefung |
|---|---|---|
| H ≤ 1,0 | 123 · 0 · 0 · 1 | 123 · 0 · 1 · 2 |
| H ≤ 0,75 | 116 · 0 · 0 · 8 | 118 · 1 · 3 · 6 |
| H ≤ 0,5 | 110 · 0 · 1 · 14 | 116 · 1 · 3 · 8 |
| V ≥ 5 | 96 · 0 · 1 · 28 | 97 · 0 · 1 · 28 |
| D ≤ 0,06 | 111 · 0 · 1 · 13 | 114 · 1 · 1 · 10 |
| N ≥ 2 | 87 · 0 · 2(+1 neu) · 37 | 86 · 0 · 2(+1 neu) · 39 |
| K ≤ 0,03 | 71 · 1 · 3(+2 neu) · 52 | 74 · 1 · 3 · 50 |
Volumen trennt nicht (bestätigt den Befund vom 14.10.). Klammer- und Zielregionsregeln kosten die Hälfte der Tage.

**4. H ist der einzige Kandidat mit gleichgerichteter Wirkung — aber an der Entwicklungsmenge nicht belegt.**
H ≤ 0,75 trifft in der Prüfmenge BAC 19.03.2026 (z 6,3, h 0,86, extrap_ab) und MS 19.05.2026 (h 0,86), unter den
bekannten Fällen C 18.06.2026 (z 11,4, h 0,86, Volumen 1). Nicht getroffen: C 29.10.2025 (z 7,2, Klammer mit Stützstelle
genau auf 30 Tagen, h 0), JPM 26.06.2026 (h 0,71). Kosten: 14 von 247 unauffälligen Zufallstagen (5,7 %).
Die Ableitung „an entwicklung, Prüfung an pruefung“ scheitert: in der Entwicklungsmenge entfernt H ≤ 0,75 keinen
auffälligen Fall. Bei 2 Fällen > 6 in 249 Zufallstagen ist jede Schwelle unterbestimmt.

**5. Live ≠ Backfill** an 68/336 Tagen (Befund 14.10., unverändert) — der Grund für Phase 1 hängt nicht an H.

## Vorschlag
- **Ergebnis festhalten: keine belastbare Ausschlussregel gefunden.** Kein Ausschluss aus dem Ranking aufgrund von
  H, V, D, N oder K.
- **Phase 1 (gemeinsame CM-Entscheidung Live/Backfill) und Phase 2 (Herkunft je Zeile, additiv) wie in v2/R2 geschnitten
  bauen** — mit `cm_h`, Leg-Volumen, Delta-Abstand, Klammer in der Zeile; Status `auffaellig` nur als Markierung
  (Grund: `h>0,75` bzw. `>6 MAD`), **ohne** Rankingwirkung. Damit sammelt der Cron die Messbasis, die heute fehlt.
- **Erneute Prüfung** der H-Regel, wenn ≥ 20 markierte Fälle > 6 MAD aus Live-Zeilen mit vollständiger Herkunft
  vorliegen; dann vorab festgelegte Ableitung/Prüfung wie hier.
- Phasen 3 (Bestand), 4 (Frontend „heute nicht bewertbar“) entfallen bis dahin — es gibt keine ausgeschlossene Zeile.
  Phase 5 (10Δ) bleibt unabhängig.

## Prüffragen
1. Trägt die Auswertung den Schluss „keine belastbare Ausschlussregel“? Fehler in der Simulation
   (`skew_trockenlauf_auswertung.py`: `waehle`, `merkmale`, Gewichte 1 − w / w, Referenz aus der Live-Datei)?
2. Ist „Markt statt Messfehler“ für März/April 2026 haltbar, oder brauche ich dafür einen eigenen Beleg (z. B. Zeitgleichheit
   über alle acht Ticker, Vergleich mit CBOE SKEW)?
3. Freigabe für Phase 1 + 2 (Markierung ohne Rankingwirkung) als nächsten Bauschritt?
