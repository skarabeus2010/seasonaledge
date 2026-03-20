# KI-Modelle — SeasonalEdge

## Übersicht

| Modell | Use Case | Phase |
|--------|----------|-------|
| DTW Pattern Matching | Ähnliche historische Jahre | Phase 1 |
| Prophet | Saisonale Prognose 60 Tage | Phase 1 |
| Isolation Forest | Ausreißer-Jahre erkennen | Phase 1 |
| Claude API | Natural Language Kommentar | Phase 1 |
| **KI Seasonal Score** | **Composite 0-10 aus 4 Sub-Scores** | **Phase 1** |
| **Outlier Manager** | **IQR / Winsorize / Isolation Forest Toggle** | **Phase 1.5** |
| **KI-Zusammenfassung** | **Claude 3-Satz-Summary pro Page** | **Phase 1.5** |
| **Anomalie-Heatmap** | **Isolation Forest Monat x Dekade** | **Phase 1.5** |
| **Anomalie-Radar** | **Ticker-Abweichung vom Saisonalmuster (aktuell)** | **Phase 1.5** |
| **Crash-Fruehwarnung** | **Markt-Regime Ampel (Vola/Drawdown/Rendite)** | **Phase 1.5** |
| **TDoM-Anomalien** | **Ungewoehnliche Trading Days (Z-Score)** | **Phase 1.5** |
| **Muster-Brueche** | **Jahre mit gebrochenen Saisonalmustern + Kontext** | **Phase 1.5** |
| **MSTL Zerlegung** | **Multi-Saisonalitaets-Zerlegung (Trend/Woche/Jahr)** | **Phase 1.5** |
| **Chronos-Bolt-Tiny** | **Probabilistische 30d-Prognose (Amazon, 9M Params)** | **Phase 1.5** |
| **NeuralProphet** | **Explizite Saisonalitaets-Komponenten (Fourier)** | **Phase 1.5** |
| **Spot-Vol Beta** | **Daily/Rolling Beta SPX vs VIX + Regime-Wendepunkte** | **Phase 1.5** |
| LSTM | Komplexe Mustererkennung | Phase 2 |
| XGBoost | Multi-Feature Renditeprognose | Phase 2 |
| Transformer | Attention-basierte Analyse | Phase 3 |

## DTW Pattern Matching

```python
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

def find_similar_years(current_pattern, all_years_data, top_n=3):
    scores = {}
    for year, pattern in all_years_data.items():
        dist, _ = fastdtw(current_pattern, pattern, dist=euclidean)
        scores[year] = dist
    return sorted(scores.items(), key=lambda x: x[1])[:top_n]
```

## Prophet

```python
from prophet import Prophet

def forecast_seasonal(df_prices, periods=60):
    m = Prophet(yearly_seasonality=True, weekly_seasonality=False)
    m.fit(df_prices.rename(columns={"Date": "ds", "Close": "y"}))
    future = m.make_future_dataframe(periods=periods)
    return m.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)
```

## Isolation Forest

```python
from sklearn.ensemble import IsolationForest

def detect_outlier_years(year_returns_matrix):
    clf = IsolationForest(contamination=0.1, random_state=42)
    labels = clf.fit_predict(year_returns_matrix)
    return [y for y, l in zip(years, labels) if l == -1]
```

## Claude API

```python
import anthropic

def generate_seasonal_commentary(ticker, month, avg_return, win_rate, similar_years):
    client = anthropic.Anthropic()  # Key via ANTHROPIC_API_KEY env
    msg = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=200,
        messages=[{"role": "user", "content": f"Analysiere saisonales Muster für {ticker} im {month}..."}]
    )
    return msg.content[0].text
```

## KI Seasonal Score (shared/ki_score.py)

Composite Score 0-10 aus 4 Sub-Scores (je 0-2.5 Punkte):

| Sub-Score | Logik | Gewicht |
|-----------|-------|---------|
| DTW Ähnlichkeit | Top-5 ähnliche Jahre → Anteil positiver | 2.5 |
| Prophet Prognose | 30-Tage Forecast Richtung | 2.5 |
| Win-Rate | Historische Win-Rate aktueller Monat | 2.5 |
| Tracking-Qualität | Korrelation aktuelles Jahr vs. Ø | 2.5 |

**Signal:** ≥6.5 Bullish · 3.5–6.5 Neutral · ≤3.5 Bearish

```python
from shared.ki_score import calculate_ki_score, scan_tickers

# Einzelticker (mit Prophet)
result = calculate_ki_score(ticker, df, year_data, avg, std, quick_mode=False)
# → {"score": 7.2, "signal": "Bullish", "sub_scores": {...}}

# Multi-Ticker Scanner (ohne Prophet, ~1-2s/Ticker)
results = scan_tickers(tickers, years_back=20, quick_mode=True)
# → [{"ticker": "SPY", "score": 7.2, ...}, ...]
```

### Pages
- `pages/15_🧠_KI_Score.py` — Einzelticker: Gauge + Radar + 4 Detail-Expander
- `pages/16_🔍_Market_Scanner.py` — Multi-Scanner: Top/Flop + Tabelle + Heatmap
- `pages/17_⭐_Premium_Dashboard.py` — Seasonax-Style Komplettansicht

## Outlier Manager (shared/outlier_manager.py)

Erkennt und behandelt Ausreisser in saisonalen Analysen. 4 Methoden:

| Methode | Logik | Effekt |
|---------|-------|--------|
| IQR (1.5x) | Interquartilsabstand | Entfernt moderate Ausreisser |
| IQR (3x, streng) | Nur extreme Ausreisser | Konservativ |
| Winsorize (3σ) | Clippt auf mean ± 3 Std | Behaelt alle Jahre, daempft Extreme |
| Isolation Forest (KI) | sklearn ML-Modell | Erkennt atypische Jahresmuster |

```python
from shared.outlier_manager import filter_year_data, outlier_sidebar, outlier_info_box

# In Sidebar: Toggle-Widget
method = outlier_sidebar()

# Nach build_year_data(), vor calculate_seasonal_average():
year_data, outlier_years = filter_year_data(year_data, method=method)
outlier_info_box(outlier_years, method)
```

## KI-Zusammenfassung (shared/ai_models.py)

Claude generiert eine 3-Satz-Zusammenfassung pro Page:
1. Historisches Muster (bullish/bearish + Kennzahl)
2. Aktueller Kontext (Tracking vs. Saisonalmuster)
3. Naechster Katalysator / Ausblick

```python
from shared.ai_models import generate_page_summary

summary = generate_page_summary(
    ticker="SPY",
    page_name="Saisonale Analyse",
    stats={"avg_return": 1.2, "win_rate": "68%", "period": "Maerz", ...}
)
# → "Der Maerz zeigt fuer SPY eine historisch bullische Tendenz mit 68% Win-Rate..."
```

Benoetigter Key: `ANTHROPIC_API_KEY` in `.streamlit/secrets.toml` oder Environment.

## Anomalie-Heatmap (shared/ai_models.py)

Isolation Forest pro Monat × Dekaden-Endziffer erkennt die groessten Muster-Brueche.

```python
from shared.ai_models import build_anomaly_matrix, build_anomaly_heatmap_figure

matrix, months, digits = build_anomaly_matrix(df, contamination=0.1)
fig = build_anomaly_heatmap_figure(matrix, months, digits, ticker="SPY")
# matrix[monat][digit] = Ausreisser-Anteil in % (0-100)
```

Benoetigtes Paket: `scikit-learn` (sklearn).

## Anomaly Engine (shared/anomaly_engine.py)

4 Isolation-Forest-Features in einem Modul:

### 1. Anomalie-Radar
Erkennt ob ein Ticker sich **gerade jetzt** anomal verhaelt vs. saisonalem Muster.
IF trainiert auf historischen Fenster-Renditen am gleichen Kalenderzeitpunkt.

```python
from shared.anomaly_engine import compute_ticker_anomaly_score
result = compute_ticker_anomaly_score(df, lookback_days=10)
# → {"anomaly_score": 72.3, "direction": "bearish_anomaly", "current_return": -3.2, ...}
```

Integriert in: Erweiterte Analyse (Expander)

### 2. Crash-Fruehwarnung
IF auf Rendite/Volatilitaet/Drawdown-Features → Ampel-System (Gruen/Gelb/Rot).

```python
from shared.anomaly_engine import compute_market_regime, TRAFFIC_LIGHT_LABELS
regime = compute_market_regime(df)
# → {"regime": "caution", "risk_score": 55, "traffic_light": "yellow", ...}
```

Integriert in: Home Page (SPY-basiert)

### 3. TDoM-Anomalien
Vergleicht letzte 3 Monate TDoM-Renditen mit historischem Durchschnitt via Z-Score.

```python
from shared.anomaly_engine import detect_tdom_anomalies
anomalies = detect_tdom_anomalies(df, strategy="open_to_close", recent_months=3)
# → [{"tdom": 1, "z_score": -2.3, "direction": "bearish", ...}, ...]
```

Integriert in: TDOM Analyse (Expander)

### 4. Saisonale Muster-Brueche
IF erkennt Jahre mit gebrochenen Saisonalmustern. Inkl. historischem Event-Kontext.

```python
from shared.anomaly_engine import detect_pattern_breaks
breaks = detect_pattern_breaks(year_data, avg, top_n=7)
# → [{"year": 2020, "break_strength": 85, "event": "COVID-19 Pandemie", ...}, ...]
```

Integriert in: Erweiterte Analyse, KI Score (Expander)

## MSTL Zerlegung (shared/mstl_decomposition.py)

Zerlegt Kursreihe in Trend + Wochensaisonalitaet + Jahressaisonalitaet + Residual.
Nutzt statsmodels MSTL. Millisekunden pro Ticker, keine GPU noetig.

```python
from shared.mstl_decomposition import decompose_mstl, build_decomposition_figure
result = decompose_mstl(df, periods=[5, 252])
fig = build_decomposition_figure(result, ticker="SPY")
```

## Chronos-Bolt-Tiny (shared/chronos_forecast.py)

Amazon Chronos Foundation Model (9M Parameter). Probabilistische Prognose mit Konfidenzbaendern.
Laeuft auf CPU in < 1 Sekunde.

```python
from shared.chronos_forecast import forecast_chronos, build_chronos_chart
forecast = forecast_chronos(df, periods=30)
# forecast.attrs["expected_return"], forecast.attrs["p_positive"]
```

## NeuralProphet (shared/neural_prophet_forecast.py)

PyTorch mit expliziten Fourier-Saisonalitaetskomponenten. Benoetigt Python <= 3.12.

## Spot-Vol Beta (shared/spot_vol_beta.py)

SPX vs VIX: Daily Beta, Rolling Beta, OLS-Regression, Regime-Wendepunkte.
DB-Tabelle `spot_vol_beta` (9120 Rows).

```python
from shared.spot_vol_beta import load_spot_vol_data, compute_spot_vol_beta, analyze_vix_extremes
df = load_spot_vol_data("^GSPC", "^VIX")
df_calc, metrics = compute_spot_vol_beta(df, rolling_window=60)
extremes = analyze_vix_extremes(df_calc, vix_spike_threshold=30)
```
