# Learnings — SeasonAlpha

> Meta-Erkenntnisse aus Ingest- und Lint-Läufen. Was hat funktioniert, was nicht?
> Wird von /sa-ingest ergänzt wenn ein Muster wiederholt auftaucht.

## Methodik

- **Normalisierte Renditen (Basis 100)** sind die SSOT für alle Chart-Vergleiche — niemals absolute Preisänderungen
- **Download-Quelle variiert:** Yahoo ab 1970, Stooq ab 1950 — bei Studien immer Yahoo-Basis verwenden

## Backtest-Methodik

- **TDOM Top-25% + technischer Filter >> reines TDOM**: Sharpe-Verbesserung bis +456% (GLD: 0.45 → 2.50). Filter eliminieren schlechte Entry-Zeitpunkte, sind kein Rauschen.
- **Walk-Forward ist Pflicht vor Produktivbetrieb**: OOS/IS-Sharpe-Ratio > 0.6 = robust. Grenzwert 3.26 bei GLD+Bollinger (OOS schlägt IS auf allen Metriken = Edge wird stärker mit der Zeit).
- **Look-Ahead-Bias bei TDOM**: Globales Kalibrierungsfenster → ~10-20% zu optimistisch. Betroffene Strategien via Stop-Loss-Sweep und Walk-Forward entlarven.
- **Stop-Loss ist signaltyp-spezifisch**: BB Bounce braucht keinen (Signal = Filter); RSI Reversal auf gestressten Assets braucht 5% Trailing (verdoppelt Return). Kein Stop rettet eine kaputte Strategie.
- **LBR vs. MACD ist nicht universell**: LBR für volatile/Growth (BTC, QQQ, AAPL); MACD für Trend-dominante Assets (NVDA, SPY, GLD). LBR hat systemisch besseren Calmar (weniger Drawdowns).

## Edge-Geographie

- **Edelmetall-Phänomen**: GLD + Bollinger Bounce Edge ist kein universeller Markteffekt. SI=F + SLV replizieren ihn (→ Robustheit), DAX nicht (→ anderer Kapitalfluss). Bei neuen Tickern erst replizieren bevor produktiv einsetzen.
- **Signalstärke-Hierarchie (Sharpe)**: D-GLD 2.50 → D-SI=F 1.91 → D-SLV 1.81 → F-BTC 1.45 → A-GLD 1.30 → C-QQQ 0.94. Unterhalb 0.6 kein robuster Edge (reines Rauschen oder Bias-Artefakt).

## Content

<!-- Learnings aus verarbeiteten Quellen werden hier ergänzt -->
