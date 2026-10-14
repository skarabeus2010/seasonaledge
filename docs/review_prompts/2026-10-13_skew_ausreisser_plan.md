# Entwurf v1: unplausible Punkte in der Skew-Historie (Radar /skew) — Runde 1 (Plan)

Read-only, Repo `C:\dev\Seasonaledge`, Stand `origin/master` `88c02ff`. Deutsch, echte Umlaute, Datei:Zeile, am Ende
**FREIGABE (Plan): ja/nein**. Bitte zuerst prüfen, ob meine Messungen und Annahmen stimmen, dann den Plan.

## Anlass
Plausibilitätsprüfung gegen SpotGamma (Compass, Banken + XLF, Stand ~09.10.2026): Reihenfolge und Quadranten stimmen,
die Richtung der X-Achse auch (beide RR = call_iv − put_iv). Abweichungen erklären sich zum Teil durch **einzelne
unplausible Punkte**, die den **Rang = (heute − min)/(max − min)** verschieben (`landing/pages/skew.html` `_rank`,
Standardmodus „Rank“, Fenster 1 J.).

## Messungen (Live-Datei `options_skew_history.json`, 13.10.2026; nur `cm`/`cm_extrap`, 1 J.)
- Beispiele: MS 16.09. (`cm_extrap`) put 17,0 % / call 41,9 % / ATM 38,4 %; XLF 16.09. (`cm_extrap`) call 11,9 % bei
  ATM 22,6 %; C 18.06. (`cm_extrap`) skew −20,05; C 29.10.2025 (`cm`) skew −11,38.
- Ausreißer > 6 MAD (je Ticker, skew_pts) im Universum: 359 von 27 434 (1,3 %); `cm_extrap` 151/3 669 (4,1 %),
  `cm` 208/23 765 (0,9 %).
- Quantile über alle Ticker (Vol-Punkte): putZeta `cm` 0,1 % −9,9 · 99,9 % +20,6; `cm_extrap` −24,5 · +37,1.
  callZeta `cm` −13,2 · +22,4; `cm_extrap` −31,1 · +46,0. Monatsmediane unauffällig (putZeta ≈ +1, callZeta ≈ −0,3).
- Wirkung auf den Rang (Ausreißer weg): MS RR-Rank 33 → 49, C 30 → 39, XLF 56 → 60; Percentile fast unverändert.
- Heutige `cm_extrap` (Datei `options_skew.json`): 28× `extrap_ab` monatlich [39, 67] → Gewicht (30−t1)/(t2−t1) =
  −0,32; 5× `extrap_auf` freitags [18, 25] → +1,71. Für den 16.09. ist die Gruppe nicht in der Historie gespeichert.

## Vermutete Ursachen (bitte am Code prüfen)
1. **Extrapolationsgewicht unbegrenzt** (`shared/black_scholes.cm_interp`, Gruppen aus `cm_leg_kandidaten`
   `extrap_ab`/`extrap_auf`, Aufrufer `scripts/compute_options_skew.py::_skew_cm` ~528): nur Abstand ≤ 15 Tage
   geprüft, nicht das Gewicht. Liegen zwei Stützstellen dicht beieinander, wird ihr Rauschen vervielfacht.
2. **Backfill-Rückfall `paar = got[:2]`** (`scripts/backfill_skew_massive.py::_reconstruct` ~366): nimmt beliebige zwei
   Stützstellen, wenn keine Gruppe passt.
3. **Keine Plausibilitätsprüfung der fertigen Zeile** — nur der ATM-Überhang-Check auf Leg-Ebene
   (`black_scholes`, Kommentar „3.0 liegt jenseits des 95. Perzentils“).
4. Event-Tage (Earnings) heben ATM und können legitim große negative Zetas erzeugen → eine feste Schranke darf sie
   nicht pauschal verwerfen. Bitte bewerten.

## Plan
**A. Erzeuger (eine Regel für Live und Backfill, `shared/black_scholes.py`):**
- `cm_interp`/Aufrufer: Extrapolation nur mit |Gewicht| ≤ G (Vorschlag G = 1,0; Messung aller Kombinationen im
  Trockenlauf), sonst nächste Gruppe; Backfill-Rückfall `got[:2]` entfernt bzw. derselben Regel unterworfen.
- Neue Funktion `zeile_plausibel(call_iv, put_iv, iv_atm, modus)` → (bool, grund): verwirft, wenn ein Flügel
  außerhalb [ATM − a, ATM + b] liegt; Schranken aus der gemessenen `cm`-Verteilung abgeleitet (0,1/99,9 %, mit Puffer),
  nicht geraten. Verworfene Zeile: nicht rankbar (`cm_mode = "unplausibel"` + Grund), nicht gelöscht.
- Diagnosezähler je Grund.

**B. Bestand:** einmaliges Skript, das die Historie mit derselben Funktion markiert (Trockenlauf mit Bericht je
Ticker, dann Schreiben auf dem Server mit Backup, Sperre wie Backfill-Supervisor, nach dem Cron-Fenster).

**C. Frontend:** `_isNorm` zählt nur `cm`/`cm_extrap` → markierte Zeilen fallen automatisch heraus. Optional
(Nutzerentscheidung): Standardmodus Percentile statt Rank.

**D. 10Δ in die Historie** (`put10_iv`, `call10_iv` je Zeile, Live + Backfill), damit Flügelvergleiche (SpotGamma
XLF-Smile) künftig prüfbar sind. Nur ergänzend, Rang unverändert.

**E. Wächter + Mutationen:** Fälle MS/XLF 16.09. wörtlich als Regression, Gewichtsgrenze, Earnings-Fall (ATM hoch,
beide Flügel darunter, muss bleiben, falls so entschieden), Zwilling Live = Backfill gleiche Entscheidung,
Frontend schließt markierte Zeilen aus. Wirkungsbericht vor dem Push: je Ticker verworfene Zeilen, Radarposition alt/neu.

## Prüffragen
1. Stimmen Messungen und Ursachen? Gibt es weitere Quellen (Spot, Verfallswoche, Parität)?
2. Ist eine feste Flügelschranke vertretbar, oder braucht es eine tickerbezogene/zeitliche Regel? Wie Earnings behandeln?
3. Ist |Gewicht| ≤ 1 sinnvoll, oder ein Mindestabstand der Stützstellen?
4. Fehlt etwas für die Freigabe?
