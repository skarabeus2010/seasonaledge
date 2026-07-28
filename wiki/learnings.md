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

## Infrastruktur / Betrieb

- **Supabase Free Tier schlägt still zu**: DB-Quota-Überschreitung blockt Writes ohne lauten Fehler. Nightly läuft mit Exit 0, schreibt aber nichts. Erst nach 6 Tagen durch Health-Check-Mail sichtbar. → Pro-Plan ist für Produktion Pflicht.
- **Recovery-Reihenfolge nach DB Write-Block**: 1. Nightly DB Refresh (7-Tage-Fenster füllt Preise automatisch) → 2. Full Scanner (KI-Scores alle 324 in ~3 Min) → 3. Spezial-Workflows (Brier, Polymarket, Newsletter). Regime-Scores 1/324 ist Design, kein Bug.
- **"Nightly Data Update" ist ein Altlast-Workflow**: Der korrekte Workflow ist "Nightly DB Refresh". "Nightly Data Update" ruft ein veraltetes DownloadManager-Interface auf (TypeError) und läuft scheinbar durch, tut aber nichts.
- **Completeness-JSON-URL**: `https://seasonalpha.ai/landing/data/db_completeness.json` — nicht `/data/` (404, nginx kennt keinen `/data/`-Root).
- **Polymarket-Backfill in nightly_refresh.py vs. Standalone**: Nightly-interne Phase schlägt mit DNS-Fehler fehl; der eigenständige `polymarket_daily.yml` Workflow läuft korrekt. Solange Standalone grün, kein Handlungsbedarf.

## Content

<!-- Learnings aus verarbeiteten Quellen werden hier ergänzt -->
