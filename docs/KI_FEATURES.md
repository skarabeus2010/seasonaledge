# KI-Features — SeasonalEdge

> Stand: 2026-03-20 | 15 KI-Features aktiv | TODO: Alle auf Home Page verpacken

## Feature-Uebersicht

| # | Feature | Beschreibung | Page | Modul |
|---|---------|-------------|------|-------|
| 1 | TruePath KI-Score | Composite Score 0-10 aus 4 Sub-Scores (DTW, Prophet, Win-Rate, Tracking) | KI Score, Scanner, Premium | `ki_score.py` |
| 2 | DTW Pattern Matching | Findet historische Jahre mit aehnlichstem Kursverlauf (Dynamic Time Warping) | TruePath, KI Score | `ai_models.py` |
| 3 | Prophet Forecast | Saisonale Prognose 30-60 Tage in die Zukunft (Facebook Prophet) | KI Score | `ai_models.py` |
| 4 | Market Scanner | Scannt 500+ Ticker, berechnet KI-Score, rankt nach Chance | Market Scanner | `ki_score.py` |
| 5 | Outlier Manager | Erkennt/behandelt Ausreisser: IQR, Winsorize, Isolation Forest — Toggle in Sidebar | Erweiterte Analyse | `outlier_manager.py` |
| 6 | KI-Zusammenfassung | Claude generiert 3-Satz-Summary: Muster + Kontext + Ausblick | Erweiterte Analyse | `ai_models.py` |
| 7 | Anomalie-Heatmap | Isolation Forest erkennt Monat/Dekaden-Kombinationen mit ungewoehnlichen Renditen | Erweiterte Analyse | `ai_models.py` |
| 8 | Anomalie-Radar | Misst wie stark ein Ticker aktuell vom saisonalen Muster abweicht (Score 0-100) | Erweiterte Analyse | `anomaly_engine.py` |
| 9 | Crash-Fruehwarnung | Ampel-System (Gruen/Gelb/Rot) basierend auf Vola, Drawdown, Rendite-Anomalien | Home Page | `anomaly_engine.py` |
| 10 | TDoM-Anomalien | Erkennt Trading Days die sich aktuell anomal verhalten vs. historisch (Z-Score) | TDOM Analyse | `anomaly_engine.py` |
| 11 | Muster-Brueche | Findet Jahre in denen das saisonale Muster am staerksten gebrochen wurde + Event-Kontext | Erweiterte Analyse, KI Score | `anomaly_engine.py` |
| 12 | MSTL Zerlegung | Multi-Saisonalitaets-Zerlegung: Trend + Woche + Jahr + Residual (statsmodels) | Erweiterte Analyse, KI Score | `mstl_decomposition.py` |
| 13 | Chronos Forecast | Probabilistische 30d-Prognose mit Konfidenzbaendern (Amazon Chronos-Bolt-Tiny, 9M Params) | Erweiterte Analyse, KI Score | `chronos_forecast.py` |
| 14 | NeuralProphet | Explizite Saisonalitaets-Komponenten via Neural Network (Fourier-basiert) | Erweiterte Analyse | `neural_prophet_forecast.py` |
| 15 | Spot-Vol Beta | Daily + Rolling Beta (SPX vs VIX), Regime-Wendepunkte, Forward Returns nach Extremen | Spot-Vol Beta | `spot_vol_beta.py` |

---

## Detailbeschreibungen

### 1. TruePath KI-Score

**Was:** Ein Composite-Score von 0 bis 10 der anzeigt, wie bullish oder bearish die saisonale Lage fuer einen Ticker gerade ist.

**Wie:** 4 Sub-Scores werden kombiniert (je 0-2.5 Punkte):
- **DTW-Aehnlichkeit:** Wie aehnlich ist das aktuelle Jahr historisch guten/schlechten Jahren? (Dynamic Time Warping)
- **Prophet-Prognose:** Zeigt die 30-Tage-Prognose nach oben oder unten? (Facebook Prophet ML)
- **Win-Rate:** Wie oft war der aktuelle Monat historisch positiv?
- **Tracking-Qualitaet:** Folgt das aktuelle Jahr dem saisonalen Durchschnittsmuster?

**Signal:** Score >= 6.5 = Bullish | 3.5-6.5 = Neutral | <= 3.5 = Bearish

**Nutzen fuer den User:** Ein einzelner Score der sofort zeigt ob die Saisonalitaet gerade fuer oder gegen einen Ticker spricht.

---

### 2. DTW Pattern Matching

**Was:** Findet die 3-5 historischen Jahre deren Kursverlauf dem aktuellen Jahr am aehnlichsten ist.

**Wie:** Dynamic Time Warping (DTW) — ein Algorithmus der zwei Zeitreihen vergleicht und dabei zeitliche Verschiebungen beruecksichtigt. Besser als einfache Korrelation, weil Muster auch dann erkannt werden wenn sie ein paar Tage frueher oder spaeter auftreten.

**Nutzen fuer den User:** "2026 sieht aus wie 2017 und 2021 — beide Jahre hatten im zweiten Halbjahr einen starken Anstieg."

---

### 3. Prophet Forecast

**Was:** Saisonale Prognose 30-60 Tage in die Zukunft mit Konfidenzintervall.

**Wie:** Facebook Prophet — ein Zeitreihen-ML-Modell das speziell fuer saisonale Muster entwickelt wurde. Erkennt automatisch Jahressaisonalitaet und Trends.

**Nutzen fuer den User:** Zeigt die erwartete Richtung und Staerke der naechsten Wochen basierend auf historischen Mustern.

---

### 4. Market Scanner

**Was:** Scannt alle 500+ Ticker gleichzeitig und erstellt ein Ranking nach KI-Score.

**Wie:** Quick-Mode: Berechnet KI-Score ohne Prophet (Korrelation statt DTW) — ca. 1-2 Sekunden pro Ticker. Ergebnis: Sortierte Tabelle mit Top-Bullish und Top-Bearish Tickern.

**Nutzen fuer den User:** "Welche Aktien/ETFs haben gerade die staerkste saisonale Rueckenwind?" — beantwortet in 5-10 Minuten statt manueller Analyse.

---

### 5. Outlier Manager

**Was:** Filtert Ausreisser-Jahre aus den Berechnungen, damit Crash-Jahre (2008, 2020) die saisonalen Muster nicht verzerren.

**Wie:** 4 Methoden zur Auswahl:
- **IQR (1.5x):** Entfernt Jahre ausserhalb des 1.5-fachen Interquartilsabstands
- **IQR (3x, streng):** Nur extreme Ausreisser
- **Winsorize (3 Sigma):** Clippt Extremwerte, entfernt nichts — alle Jahre bleiben erhalten
- **Isolation Forest (KI):** Machine Learning erkennt atypische Jahresmuster automatisch

**Nutzen fuer den User:** Toggle in der Sidebar — sofort sichtbar wie sich die Saisonalitaet aendert wenn Crash-Jahre rausfallen. "Ohne 2008 und 2020 ist der September gar nicht so schlecht."

---

### 6. KI-Zusammenfassung

**Was:** Claude (Anthropic KI) fasst die Analyse-Ergebnisse in genau 3 Saetzen zusammen.

**Wie:** Die wichtigsten Kennzahlen (Rendite, Win-Rate, Tracking) werden an die Claude API geschickt. Claude generiert:
1. Satz: Historisches Muster (bullish/bearish + Kennzahl)
2. Satz: Aktueller Kontext (wie verhaelt sich das aktuelle Jahr)
3. Satz: Ausblick (naechster Katalysator oder worauf achten)

**Nutzen fuer den User:** Sofort verstaendliche Einordnung — kein Zahlenlesen noetig. "Der Maerz zeigt fuer SPY eine historisch bullische Tendenz mit 72% Win-Rate. Das aktuelle Jahr liegt 1.3% ueber dem Saisonaldurchschnitt. Naechster Katalysator: FOMC am 19.03."

**Voraussetzung:** Anthropic API-Key (`ANTHROPIC_API_KEY`)

---

### 7. Anomalie-Heatmap

**Was:** Zeigt in welchen Monat/Dekaden-Kombinationen historisch die meisten ungewoehnlichen Renditen aufgetreten sind.

**Wie:** Isolation Forest wird ueber alle historischen Monatsrenditen trainiert. Pro Zelle (z.B. "Maerz + X6-Jahre") wird der durchschnittliche Anomalie-Score berechnet. Hohe Werte = viele Ausreisser in dieser Zelle.

**Nutzen fuer den User:** "Im Oktober der X8-Jahre (2008, 2018) war es historisch besonders unberechenbar" — hilft bei der Einschaetzung ob das aktuelle Umfeld (2026 = X6) in einem ruhigen oder turbulenten Feld liegt.

---

### 8. Anomalie-Radar

**Was:** Misst in Echtzeit wie stark sich ein Ticker gerade vom saisonalen Muster entfernt.

**Wie:** Isolation Forest vergleicht die Renditen der letzten 10 Handelstage mit historischen Fenstern am gleichen Kalenderzeitpunkt (20 Jahre). Score 0-100: je hoeher, desto anomaler.

**Nutzen fuer den User:** "AAPL hat einen Anomalie-Score von 78 — die aktuelle Bewegung ist ungewoehnlich fuer diese Jahreszeit." Fruehwarnung dass sich etwas aendert, bevor es in den Nachrichten steht.

---

### 9. Crash-Fruehwarnung

**Was:** Ampel-System auf der Home Page das sofort zeigt ob der Markt sich "normal" verhaelt oder ob Stresssignale vorliegen.

**Wie:** Isolation Forest analysiert 7 Features des aktuellen Markttages:
- Tagesrendite, 5d/10d/20d-Volatilitaet, 5d/20d-Rendite, Drawdown vom 20-Tage-Hoch

Daraus entsteht ein Risk-Score (0-100) und eine Ampel:
- 🟢 **Gruen (0-39):** Ruhig — Markt verhaelt sich normal
- 🟡 **Gelb (40-69):** Erhoehte Vorsicht — ungewoehnliche Muster erkannt
- 🔴 **Rot (70-100):** Stress-Regime — historisch selten, stark anomal

**Nutzen fuer den User:** Beim Oeffnen der App sofort sehen ob heute ein "normaler" Tag ist oder ob erhoehte Aufmerksamkeit noetig ist. Basiert auf SPY als Leitindex.

---

### 10. TDoM-Anomalien

**Was:** Erkennt welche Trading Days of the Month sich aktuell anomal verhalten.

**Wie:** Vergleicht die TDoM-Renditen der letzten 3 Monate mit dem historischen Durchschnitt via Z-Score. Ein Z-Score von +2.0 bedeutet: "Dieser TDoM war in den letzten 3 Monaten 2 Standardabweichungen ueber dem historischen Mittel."

**Nutzen fuer den User:** "TDoM 1 war die letzten 3 Monate negativ — das ist ungewoehnlich und passierte historisch nur 2x in 30 Jahren. Entweder normalisiert es sich, oder es signalisiert einen Regimewechsel."

---

### 11. Muster-Brueche

**Was:** Identifiziert die Jahre in denen das saisonale Muster am staerksten gebrochen wurde — und zeigt warum.

**Wie:** Isolation Forest bewertet jedes Jahr anhand von 4 Features:
- Korrelation mit dem saisonalen Durchschnitt
- Mittlere Abweichung (MAE)
- Jahresrendite
- Maximaler Drawdown

Die Top-7 Ausreisser werden angezeigt, mit historischem Kontext (COVID, Lehman, 9/11 etc.).

**Nutzen fuer den User:** Verstaendnis wann und warum Saisonalitaet NICHT funktioniert hat. "2020 hatte einen Bruch-Score von 85 wegen COVID — die Saisonalitaet war in Pandemie-Jahren nicht vorhersagbar." Hilft bei der realistischen Einschaetzung der Zuverlaessigkeit.

---

## Technische Module

| Modul | Features | Abhaengigkeiten |
|-------|----------|-----------------|
| `shared/ki_score.py` | TruePath Score, Scanner | DTW, Prophet, calculations |
| `shared/ai_models.py` | DTW, Prophet, IF, Claude, Heatmap, Summary | fastdtw, prophet, sklearn, anthropic |
| `shared/outlier_manager.py` | Outlier Filter (4 Methoden) | sklearn (optional) |
| `shared/anomaly_engine.py` | Radar, Crash-Ampel, TDoM, Muster-Brueche | sklearn |

## Pakete

| Paket | Features die es nutzen |
|-------|----------------------|
| `scikit-learn` | Isolation Forest (5, 7, 8, 9, 10, 11) |
| `fastdtw` + `scipy` | DTW Pattern Matching (1, 2) |
| `prophet` | Prophet Forecast (1, 3) |
| `anthropic` | KI-Zusammenfassung (6) |

## TODO: Home Page Integration

Alle KI-Features muessen auf der Home Page sichtbar/verlinkt sein:
- [ ] Feature-Cards fuer alle 11 KI-Features
- [ ] Crash-Fruehwarnung prominent oben (bereits integriert)
- [ ] Quick-Links zu den Pages mit den jeweiligen Features
- [ ] "KI-Status" Sektion: Welche Features aktiv, welche API-Keys gesetzt
