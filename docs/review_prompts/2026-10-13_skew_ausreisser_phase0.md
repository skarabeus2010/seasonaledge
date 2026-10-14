# Phase 0: Ausreißer der Skew-Historie nachgerechnet (2026-10-13) + Entwurf v3 — Runde 3

Read-only, Repo `C:\dev\Seasonaledge`, `88c02ff`. Plan v2 + deine Freigabe für Phase 0:
`..._skew_ausreisser_plan_v2.md`, `..._plan_v2_antwort.md`. Deutsch, Datei:Zeile, am Ende **FREIGABE (Plan): ja/nein**.

## Durchführung
Probe `scripts/research/skew_phase0_probe.py` im Container (Code `88c02ff`, `PYTHONDONTWRITEBYTECODE=1`, nur stdout):
Kontrakte ±30 % / 24 Strikes je Seite wie der Backfill, Bars `strict=True` (0 Abruffehler in allen Fällen), **alle**
Expiries der Rangliste versorgt, Live-Entscheidung = echtes `compute_options_skew._skew_cm` mit diesen Legs,
Backfill = originales `_plan` (3 Gruppen) + `_reconstruct`. IV in %, h = max(0, −w, w − 1).

| Fall | gespeichert (Modus, call/put/ATM, skew) | Backfill heute | Live-Logik heute | Mechanismus | historisch belegt? |
|---|---|---|---|---|---|
| MS 16.09.26 | cm_extrap 41,9/17,0/38,4, −24,9 | cm_extrap 31,8/39,0/39,0, +7,24 | single 32,0/32,6/31,4, +0,56 | Front-Monat 30 T. verworfen (Parität/Smile), Rest dünn (Vol 22–288) | **nein** — Zeile nicht reproduziert (älterer Codestand) |
| XLF 16.09.26 | cm_extrap 11,9/23,6/22,6, +11,68 | cm_extrap 15,9/18,3/21,0, +2,38 | cm_extrap [37,44] h=1,0: 12,5/18,9/23,9 | 30-T.-Monat verworfen; Extrapolation h=1 aus zwei Wochenverfällen mit widersprüchlichem ATM (19,95 / 16,71) | Mechanismus ja, Zeile **nicht** reproduziert |
| C 18.06.26 | cm_extrap 40,6/20,5/25,6, −20,05 | **identisch** | **identisch** | Monat 29 T. verworfen (Smile ×3); Extrapolation [36,43] h=0,86; 36-T.-Leg Vol 170: call 35,8 bei ATM 26,6 | **ja** |
| C 29.10.25 | cm 36,5/25,1/22,5, −11,38 | **identisch** | **identisch** | **Klammer h=0** [30,37]: Wochenverfälle mit Vol 138 bzw. 78; 30-T.-Leg call 36,5 bei ATM 22,5 | **ja** — keine Extrapolation |
| GS 20.10.25 | cm_extrap 35,0/23,5/36,5, −11,48 | **identisch** | single (39 T.) −4,5 | alle Wochenverfälle ≤ 32 T. verworfen; Backfill und Live wählen verschieden | ja (Backfill) |
| Vergleich MS 15.09., XLF 15.09., C 17.06./28.10.25, GS 21.10.25 | — | MS/C 28.10. identisch, XLF/GS identisch bzw. nah | | unauffällig; aber XLF 15.09. Live extrap_auf h=0,86 statt Backfill-Klammer | |

## Befunde
1. **Hauptursache ist die Qualität einzelner Stützstellen, nicht die Extrapolation.** Alle auffälligen Werte stammen
   aus Legs dünner **Wochenverfälle** mit wenigen bepreisten Kontrakten (9–19 von 48) und kleinem Volumen (22–170),
   deren letzter Trade gegen den Schlusskurs des Basiswerts invertiert wird. C 29.10.25 ist eine **reine Klammer**
   (h = 0) und trotzdem −11,38. Die Extrapolation **verstärkt** (C 18.06.: h 0,86; XLF 16.09.: h 1,0), erzeugt aber nicht.
2. **Der liquide Monatsverfall nahe 30 Tagen wird häufig verworfen** (MS, XLF, C: Parität/Smile/Delta-Toleranz),
   obwohl er das größte Volumen hat (XLF 16.09.: 13 045 Kontrakte). Dann fällt die Wahl auf dünne Wochenverfälle.
   Ob die Verwerfung dort richtig ist, ist offen — die Tagesbars dieser Kontrakte sind teils älter als der Schluss.
3. **Live und Backfill entscheiden verschieden** bei gleichen Legs (MS, XLF, GS) — bestätigt deinen Punkt aus Runde 1.
4. **MS/XLF 16.09.** sind mit heutigem Code nicht reproduzierbar: die gespeicherten Zeilen stammen aus einem älteren
   Codestand (vor den Filtern vom 19.–25.09.); ihr Rechenweg ist nicht mehr nachweisbar.
5. Abruffehler: keine. Leere Expiries (0/48 Preise) sind Kontrakte ohne Handel am Tag.

## Entwurf v3 (geändert gegenüber v2)
- **Kern statt Flügelschranke: Leg-Qualität.** Eine Expiry trägt nur, wenn (a) mindestens N bepreiste Kontrakte je
  Seite im Band um 25Δ und ATM, (b) Volumen der verwendeten Kontrakte ≥ V, (c) ATM beidseitig geklammert. N, V aus
  einem Trockenlauf (s. u.), nicht geraten. Gilt für Live und Backfill in `leg_from_prices` bzw. einem gemeinsamen
  Vorfilter — Live hat Bid/Ask im Snapshot, Backfill nur Bars; die Regel wird je Datenquelle mit eigener Messgröße
  formuliert und das ausgewiesen.
- **Extrapolation:** h ≤ H zusätzlich (Messung im Trockenlauf; Kandidat H = 0,5, der C 18.06. und XLF 16.09.
  ausschließt, die üblichen `extrap_ab` [39,67] mit h 0,32 behält).
- **Gemeinsame Entscheidung** (Plan v2 Phase 1) bleibt — die Unterschiede in Punkt 3 werden damit beseitigt.
- **Trockenlauf statt Kalibrierung an fünf Fällen:** dieselbe Probe über eine Stichprobe (8 Ticker: Banken + XLF +
  SPY/QQQ/AAPL, je 40 zufällige Handelstage aus 12 Monaten, fester Zufallsstartwert), je Tag alle Kandidaten mit
  Leg-Kennzahlen. Ergebnis: Verteilung von N/V/h für gute vs. auffällige Tage, Wirkung jeder Regelvariante auf
  Abdeckung (rankbare Tage je Ticker) und auf den Rang. Erst danach N, V, H.
- Rest von v2 unverändert (Herkunft speichern, Status statt Löschung, Sperre über Lesen–Schreiben, Aktualisierungsregel,
  10Δ, Wächter). Bestand: `nicht_pruefbar`, gezielte Neurechnung je Ticker/Datum ohne `--overwrite`.

## Prüffragen
1. Trägt die Auswertung den Schluss „Leg-Qualität vor Extrapolation“? Was ist überinterpretiert?
2. Ist der Trockenlauf (Stichprobe, Kennzahlen, Zufallsstartwert) als nächster Schritt richtig zugeschnitten?
3. Freigabe für den Trockenlauf (rein lesend, ~320 Tage, nur Massive-Abrufe)?
