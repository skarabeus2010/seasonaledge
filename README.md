# SeasonalEdge

**Professionelle Saisonalitätsanalyse für Aktien, ETFs, Futures und Krypto**

SeasonalEdge ist eine interaktive Web-App auf Basis von Streamlit, die saisonale Muster in Finanzmärkten analysiert und mit KI-Modellen kombiniert.

---

## Features

### Basis-Analysen (13 Pages)
| Seite | Beschreibung |
|-------|-------------|
| Dashboard | Saisonalchart mit Overlays, Heute-Markierung, Zeitraum-Presets |
| Erweiterte Analyse | Präsidentenzyklus, Dekadenzyklus, War/Peace, Pressure Chart |
| Turn of the Month | Monatswechsel-Effekt, t0-normiert, Best/Worst |
| Feiertags-Effekt | 12+ NYSE-Feiertage, Kaeppel-System |
| Weekday Analyse | 4 Rendite-Modi, SMA/RSI Filter, Wochentag-Heatmap |
| Monthly Performance | Intra-Monat TDOM-Chart, Volatilität |
| Zentralbanken | Fed FOMC, ECB, BOE, BOJ — Kursreaktion |
| Mondphasen | Vollmond/Neumond-Effekt, 300+ Events |
| TruePath | KI-Pattern-Matching (DTW/Korrelation) |
| Strategien | Januar Trifecta, Kaeppel, 65+ Strategie-Bibliothek |
| OPEX | Verfallstage-Analyse |
| Intra-Decade | Dekadenzyklus (Endziffern 0-9), Stooq-Daten ab 1928 |
| Overnight vs. Intraday | Close-Open vs. Open-Close Saisonalität |

### KI-Features (4 Pages)
| Seite | Beschreibung |
|-------|-------------|
| Shock Analyzer | Trigger/Target-Analyse (Öl-DAX, VIX-S&P, Gold-S&P etc.) |
| Sector Rotation | US/EU Sektor-Heatmap, Rotation-Signale, Top/Flop Rankings |
| KI Seasonal Score | Composite Score 1-10 (DTW + Prophet + Win-Rate + Tracking) |
| Market Scanner | Multi-Ticker Scanner mit Rankings, Heatmap, CSV-Export |

### Premium Dashboard
Seasonax-Style Einzeltitel-Übersicht mit 7 Sektionen: KPIs, Saisonalkurve + KI-Score, Jahresrenditen, Monatsrenditen, Heatmap + Box-Plot, Jahres-Tabelle, Premium-Platzhalter.

---

## KI-Modelle

| Modell | Use Case |
|--------|----------|
| DTW Pattern Matching | Ähnliche historische Jahre finden |
| Facebook Prophet | Saisonale Prognose 30/60 Tage |
| Isolation Forest | Ausreißer-Jahre erkennen |
| Claude API | Natural Language Kommentar |
| KI Seasonal Score | Composite aus allen Modellen (0-10) |

---

## Installation

### Voraussetzungen
- Python 3.10+

### Setup

```powershell
git clone https://github.com/skarabeus2010/seasonaledge.git
cd seasonaledge
pip install -r requirements.txt
py -m streamlit run seasonal_app.py
```

---

## Projektstruktur

```
seasonaledge/
├── seasonal_app.py              ← Startseite
├── pages/                       ← 18 Streamlit-Pages
│   ├── 0–12                     ← Basis-Analysen
│   ├── 13_Shock_Analyzer.py
│   ├── 14_Sector_Rotation.py
│   ├── 15_KI_Score.py
│   ├── 16_Market_Scanner.py
│   ├── 17_Premium_Dashboard.py
│   └── unsubscribe.py
├── shared/                      ← Wiederverwendbare Module
│   ├── yahoo_downloader.py      ← Datenabruf (Yahoo + Stooq)
│   ├── calculations.py          ← Saisonale Berechnungen
│   ├── charts.py                ← Plotly Theme (apply_se_theme)
│   ├── ki_score.py              ← KI Score Engine
│   ├── ai_models.py             ← DTW, Prophet, Isolation Forest, Claude
│   ├── supabase_client.py       ← DB + Subscriber-Management
│   ├── distribution_charts.py   ← Box-Plots, Heatmaps
│   └── strategies/              ← 65+ Strategien
├── docs/                        ← Dokumentation
└── scripts/                     ← Utility-Skripte
```

---

## Datenquellen

- **Yahoo Finance** — Primärquelle (direkter HTTP, kein yfinance)
- **Stooq.com** — Historischer Backfill ab 1928
- **Supabase** — PostgreSQL mit 200.000+ Datensätzen (12 Indizes/FX)

## Tech-Stack

Streamlit, Plotly, Pandas, NumPy, Supabase, Brevo, GitHub Actions

---

Privates Projekt — alle Rechte vorbehalten.

*Entwickelt mit Claude (Anthropic) · v9.1 · 2026-03-19*
