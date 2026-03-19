# KI-Modelle — SeasonalEdge

## Übersicht

| Modell | Use Case | Phase |
|--------|----------|-------|
| DTW Pattern Matching | Ähnliche historische Jahre | Phase 1 |
| Prophet | Saisonale Prognose 60 Tage | Phase 1 |
| Isolation Forest | Ausreißer-Jahre erkennen | Phase 1 |
| Claude API | Natural Language Kommentar | Phase 1 |
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
