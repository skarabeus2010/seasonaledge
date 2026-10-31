# Planprüfung — Gamma-Regime × Indikatoren × Saisonalität (Studie, noch kein Code)

## Auftrag des Nutzers (2026-10-31)

Prüfen, ob Indikatoren aus unserem Bestand (RSI, LBR-Oszillator, Williams %R) in Kombination mit einem Long-/Short-
Gamma-Regime und angereichert um Saisonalität profitable Handelsregeln ergeben. Ausgabe wie gewohnt: Forward-Rendite
nach 1, 5, 10, 15, 20 Handelstagen, dazu Drawdown. Universum zunächst: QQQ, SPY, DIA, DAX (^GDAXI) und die zehn größten
US-Aktien (MAG7 + drei weitere). Bitte erst den Ansatz prüfen und verbessern — gebaut wird danach.

## Datenlage (gemessen 2026-10-31, nicht angenommen)

1. **Gamma-Historie ist kurz.** `landing/data/gex_history/` (Lauftag-Stempel) 51 Dateien 2026-08-03 … 2026-10-14,
   `gex_history_session/` (Session-Stempel seit B2) 11 Dateien 2026-10-15 … 2026-10-30 → **rund 60 Sessions**, davon die
   ersten ~50 mit dem in v66.20/B2 dokumentierten Stempelversatz (Lauf nach Mitternacht UTC → eine Session daneben).
   Ticker: SPY QQQ IWM DIA AAPL MSFT NVDA AMZN GOOGL META TSLA TLT GLD SLV SMH XLF XLE XLK IBIT ETHA + `gamma_index`
   (Marktindex, `vol_regime`). **Kein DAX** (Yahoo/Massive nur US-Optionen), **keine** AVGO/BRK-B/LLY/JPM.
2. **Kein historisches Open Interest:** Massive (Options-Starter) liefert IV/Greeks/OI nur im Snapshot, Aggregates sind
   preis-only (`docs/OPTIONS.md` Z. 171). Ein GEX-Backfill wie beim Skew (BS-Inversion aus Preisen) scheitert am OI.
   Alternative laut Doku: kostenpflichtige Historie (ThetaData o. ä.) — Nutzerentscheidung.
3. **Lange Reihen vorhanden:** Kurse mit `log_return` (Supabase, Indizes Jahrzehnte), `^VIX`, `^VIX9D`, `^VIX3M`,
   `^VIX1D` (seit v66.20), Skew-/IV-Historie je Ticker (30-Tage-normiert, ab ~09/2025, `options_skew_history.json`).
4. **Indikatoren im Bestand:** `landing/js/indicators.js` (RSI, MACD, LBR 3/10/16 als MACD-Variante, SMA/EMA,
   Bollinger), `shared/newsletter_indicators.py` (Mail-Scoring LBR/RSI). **Williams %R ist nirgends implementiert**
   (`docs/research/LARRY_WILLIAMS_INDIKATOREN.md`: Formel n = 10, Primärbeleg vorhanden). Frühere Befunde: Newsletter-
   TS/Gesamt-Score für die meisten Ticker contrarian (`scripts/backtest_newsletter_scoring.py`), Smash Day ~14 Bp
   Gegenbewegung, im Prüfzeitraum nicht bestätigt (`scripts/research/williams_muster.py`).

## Mein Entwurf

**Regime — drei Stufen, weil echte GEX für einen Backtest nicht reicht:**
- R0 *echte GEX* (Netto-Gamma-Vorzeichen bzw. Spot über/unter Zero-Gamma-Flip): nur beschreibend auf ~60 Sessions,
  plus prospektive Protokollierung ab jetzt; Auswertung frühestens nach ~250 Sessions mit Session-Stempel.
- R1 *Vola-Proxy mit langer Historie* (Arbeitshypothese: Short-Gamma-Phasen fallen mit Backwardation und hoher
  Realisierter zusammen): VIX-Laufzeitstruktur `VIX/VIX3M > 1`, alternativ `VIX9D/VIX`, und `RV21 > VIX`. Vorab
  festgelegt, einmal gegen die ~60 echten Sessions auf Übereinstimmung geprüft (Trefferquote, nicht optimiert).
- R2 *ticker-eigen* für Einzelaktien: IV-Rang aus der Skew-Historie (nur ~1 Jahr).
Der DAX bekommt das US-Regime (R1) als Marktumfeld — ausdrücklich als Fremdregime gekennzeichnet — oder nur
Indikator + Saisonalität.

**Signale (vorab fest, kleines Raster):** RSI(2) < 10 / > 90, RSI(14) < 30 / > 70, LBR-Fastline kreuzt Slowline
(3/10/16), Williams %R(10) ≤ −95 / ≥ −5 (Original: < 95 % am Tief). Einstieg am Schluss des Signaltags, Bewertung nur
mit Daten bis zum Signaltag.

**Saisonalität ohne Zukunftswissen:** True Seasonal (`shared/true_seasonal.py`): Vorzeichen der Saisonkurve der
nächsten 20 Handelstage nur aus Vorjahren; zusätzlich TDOM-Fenster (Monatswechsel).

**Auswertung:** je Zelle (Ticker × Signal × Regime × Saison) Forward-Rendite 1/5/10/15/20 HT (Mittel, Median,
Trefferquote), mittlerer Zwischenverlust (max. Drawdown im Halteintervall), Basis = alle Tage desselben Regimes,
Überlappungen ausgewiesen, Fallzahl an jeder Zahl. Entdeckung bis 2018, Prüfzeitraum 2019–2026 einmalig, Familie vorab
festgelegt, Max-T/Holm wie bei `/intermarket`, Mindestfallzahl je Hälfte. Python-Studie unter `scripts/research/`,
nur lesend, Export mit SHA-256 (Muster Williams-Studie).

**Universum:** QQQ SPY DIA ^GDAXI + AAPL MSFT NVDA AMZN GOOGL META TSLA + AVGO BRK-B und eine weitere nach
Marktkapitalisierung (Vorschlag LLY; Nutzer bestätigt).

## Fragen

1. Trägt R1 als Gamma-Proxy, oder ist das eine Umetikettierung von „hohe Vola“, die man dann auch so nennen muss?
   Gibt es einen besseren, frei verfügbaren Proxy mit langer Historie (z. B. SPX-Gamma-Rekonstruktion aus Cboe-Daten)?
2. Ist das Raster klein genug? Wie groß wird die Familie (15 Ticker × 7 Signale × 2–3 Regime × 2 Saison × 5 Horizonte),
   und wie würden Sie es beschneiden, damit nach der Korrektur überhaupt etwas übrig bleiben kann?
3. Überlappende Halteintervalle (20 HT) und Clustering der Signale in Krisen — Block-Bootstrap? Wie mit dem
   gemeinsamen Marktumfeld der 15 Reihen umgehen (sie sind nicht unabhängig)?
4. Drawdown: Zwischenverlust je Trade oder Kontokurve einer Regel? Was ist für die Aussage „profitabel“ richtig?
5. Was fehlt, was ist falsch, wo stecken Look-ahead oder Survivorship (Top-10 von heute!)?

Schluss: TRAGFÄHIG, TRAGFÄHIG MIT ÄNDERUNGEN oder NICHT TRAGFÄHIG, mit konkreten Änderungen.
