# 🌊 SeasonalEdge

**Professionelle Saisonalitätsanalyse für Aktien, ETFs, Futures und Krypto**

SeasonalEdge ist eine interaktive Web-App auf Basis von Streamlit, die saisonale Muster in Finanzmärkten analysiert und visualisiert.

---

## 🚀 Features

| Seite | Beschreibung |
|-------|-------------|
| 📈 Dashboard | Saisonalchart mit Overlays, Heute-Markierung, Zeitraum-Presets |
| 📊 Yearly Seasonals | Jahreszyklus, Präsidentenzyklus, Dekadenzyklus, War/Peace, Heatmap |
| 📆 Monthly Seasonals | Intra-Monat TDOM-Chart, Two-Week Performance, Volatilität |
| 📅 Weekday Seasonals | 4 Rendite-Modi, SMA/RSI Filter, Wochentag-Heatmap |
| 🔄 Turn of the Month | Monatswechsel-Effekt, t0-normiert, Best/Worst |
| 📅 Feiertags-Effekt | 12+ NYSE-Feiertage, Kaeppel-System |
| 🏛️ Zentralbanken | Fed FOMC, ECB, BOE, BOJ — Kursreaktion rund um Entscheidungen |
| 🌕 Mondphasen | Vollmond/Neumond-Effekt, 300+ Events |
| 🔮 TruePath | KI-Pattern-Matching (DTW/Korrelation), SeasonalEdge Score |
| 🚦 Strategien | Januar Trifecta Ampel, Kaeppel-Strategien, 65+ Strategie-Bibliothek |
| 📅 OPEX | Verfallstage-Analyse |
| 📊 Intra-Decade | Dekadenzyklus (Endziffern 0–9), Stooq-Langzeitdaten ab 1928 |
| 🌙 Overnight vs. Intraday | Close→Open vs. Open→Close Saisonalität |

---

## 🛠️ Installation

### Voraussetzungen
- Python 3.10+
- pip

### Setup

```powershell
# Repository klonen
git clone https://github.com/DEIN-USERNAME/seasonaledge.git
cd seasonaledge

# Virtuelle Umgebung (empfohlen)
python -m venv venv
venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# App starten
python -m streamlit run seasonal_app.py
```

---

## 📦 Abhängigkeiten

```
streamlit
pandas
numpy
plotly
requests
scipy
```

---

## 📁 Projektstruktur

```
seasonaledge/
├── seasonal_app.py          ← Hauptapp (Dashboard)
├── pages/                   ← Streamlit Multipage
│   ├── 0_🏠_Home.py
│   ├── 1_📊_Yearly_Seasonals.py
│   ├── 2_📆_Monthly_Seasonals.py
│   ├── 3_📅_Weekday_Seasonals.py
│   ├── 4_🔄_Turn_of_the_Month.py
│   ├── 5_📅_Feiertags_Effekt.py
│   ├── 6_🏛️_Zentralbanken.py
│   ├── 7_🌕_Mondphasen.py
│   ├── 8_🔮_TruePath.py
│   ├── 9_🚦_Strategien.py
│   ├── 10_📅_OPEX.py
│   ├── 11_📊_Intra_Decade_Seasonality.py
│   └── 12_🌙_Overnight_vs_Intraday.py
└── shared/                  ← Wiederverwendbare Module
    ├── yahoo_downloader.py  ← Datenabruf (Yahoo + Stooq-Backfill)
    ├── data.py              ← Wrapper
    ├── calculations.py      ← Saisonale Berechnungen
    ├── charts.py            ← Plotly Charts
    ├── constants.py         ← Konfiguration
    ├── central_banks.py     ← Fed/ECB/BOE/BOJ Datentabellen
    ├── nyse_holidays.py     ← NYSE-Feiertage
    └── strategies/          ← Strategie-Module
        ├── definitions.py
        ├── januar_trifecta.py
        └── kaeppel.py
```

---

## 📊 Datenquellen

- **Yahoo Finance** — Primärquelle für tägliche OHLCV-Daten (direkter HTTP, kein yfinance)
- **Stooq.com** — Historischer Backfill für Indizes ab 1928 (^DJI, ^GSPC, ^DAX etc.)

---

## 📝 Lizenz

Privates Projekt — alle Rechte vorbehalten.

---

*Entwickelt mit Claude (Anthropic) · v8.3 · 2026*
