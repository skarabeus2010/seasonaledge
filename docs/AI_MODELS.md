# KI-Modelle — SeasonalEdge

## Übersicht

| Modell | Use Case | Phase |
|--------|----------|-------|
| DTW Pattern Matching | Ähnliche historische Jahre | Phase 1 |
| Prophet | Saisonale Prognose 60 Tage | Phase 1 |
| Isolation Forest | Ausreißer-Jahre erkennen | Phase 1 |
| Claude API | Natural Language Kommentar | Phase 1 |
| **KI Seasonal Score** | **Composite 0-10 aus 4 Sub-Scores** | **Phase 1 ✅** |
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
