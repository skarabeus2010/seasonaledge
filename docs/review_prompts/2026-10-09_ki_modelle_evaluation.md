# Evaluation: Mit welchen KI-Modellen können wir auf seasonalpha.ai etwas Sinnvolles bauen?

Repo `C:\dev\Seasonaledge`. **Nur lesen, nichts ändern, keine Datenbank, keine Netzwerk-Schreibzugriffe.**
Python für eigene Messungen: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
Antwort auf Deutsch, Belege mit Datei:Zeile, Behauptungen über externe Modelle mit Quelle (oder als
„nicht geprüft" markieren). Am Ende eine priorisierte Liste.

## Kontext

SeasonAlpha ist eine Seite für saisonale Marktanalyse (Saisonalität, Kalendereffekte, Optionen/Skew,
Flows, Intermarket, Wahlen, Polymarket). Statisches Frontend (`landing/`, ApexCharts), Python-Crons in
einem Docker-Container auf einem kleinen VPS (rund 3,8 GB RAM, keine GPU, Python 3.12), Supabase.
Zielgruppe: Privatanleger und Trader, deutsch und englisch. Finanzseite — eine nicht gedeckte
Prognosebehauptung ist das größte Risiko.

**Was bisher mit „KI" passiert ist — und warum diese Frage jetzt kommt:**
- Eine ML-Pipeline (Chronos, NeuralProphet, MSTL) wurde in KW16 stillgelegt; Reste in `shared/ai_models.py`
  (Prophet, fastdtw — beide nicht in `requirements.txt`, stille Rückfälle).
- Der „KI-Score" (vier Bausteine, 0–10, Bullish/Bearish) wird gerade umbenannt in „Saison-Score", weil
  ein Walk-forward-Test **keine Vorhersagekraft** für die folgenden 30 Tage zeigte (Spearman ^GSPC 0,015,
  SPY −0,017, ^GDAXI 0,071) und keine KI darin steckt. Bericht:
  `docs/review_prompts/2026-10-08_kennzahlen_methodik_codex.md` und `..._claude.md`.
- Die „Crash-Ampel" (Isolation Forest, Vorzeichen vertauscht) wurde durch eine transparente
  Stress-Ampel ersetzt (`shared/stress_score.py`).
- Die Intermarket-Matrix ergab nach Mehrfachtest-Korrektur **null** Befunde — und das wurde als Ergebnis
  veröffentlicht. Diese Haltung soll bleiben: lieber eine belegte kleine Aussage als eine große ungedeckte.

**Verfügbare Daten (prüfen, was wirklich da ist):** tägliche OHLC für rund 370 Ticker (teils seit 1928),
Options-Ketten-Snapshots (Massive, IV/Greeks/OI) für ~165 US-Ticker, Skew-/IV-Historie, GEX, COT,
ETF-Flows, Polymarket-Preise, Wahltermine, Fed-Termine, CPI. Ein `ANTHROPIC_API_KEY` ist in der
Container-Umgebung vorgesehen (`docker-compose.yml`) — prüfen, ob und wofür er genutzt wird.

## Was ich wissen will

1. **Bestandsaufnahme:** Wo im Repo wird heute ein Modell (ML oder LLM) genutzt oder angedeutet, und was
   davon ist echt, tot oder irreführend beschriftet? (u. a. `shared/ai_models.py`, `scripts/ml/`,
   `scripts/video/`, Blog-Werkzeuge, Seitentexte mit „KI"/„AI"/„Machine Learning").
2. **Kandidaten** — bewerte mindestens diese Klassen, und ergänze, was fehlt:
   - Sprachmodelle (Claude u. a.) für **erklärende** Aufgaben: tägliche Zusammenfassung der eigenen
     Kennzahlen in Worten, Erklärtexte je Ticker, Übersetzung, Beantwortung von Fragen zu den eigenen
     Daten, Qualitätsprüfung von Texten gegen Faktenblätter.
   - **Volatilitäts- statt Renditeprognose** (Volatilität ist nachweislich prognostizierbar, Renditen kaum):
     HAR-RV, GARCH, Quantilregression, Zeitreihen-Grundmodelle (Chronos-Bolt, TimesFM, Moirai) — gegen
     eine einfache Basis (HAR, gleitender Mittelwert, implizite Vola).
   - Regime-Erkennung (Hidden-Markov, Clustering) — beschreibend, mit Stabilitätsprüfung.
   - Konforme Vorhersageintervalle / Kalibrierung für bestehende Kennzahlen.
   - Textmodelle auf Fed-Statements, Earnings-Calls, Nachrichten (Datenzugang realistisch?).
   - Anomalie-/Ähnlichkeitssuche über viele Ticker (z. B. „welche Ticker verhalten sich gerade wie X").
3. Je Kandidat: **Nutzen für den Leser** (was sieht er auf welcher Seite?), **Datenlage** (vorhanden /
   beschaffbar / nicht), **Betrieb** (RAM, CPU, Laufzeit im Nightly, API-Kosten pro Monat grob),
   **Validierungsprotokoll** vorab (Ziel, Horizont, naive Basis, Out-of-Sample-Zeitraum, Erfolgs- und
   **Abbruchkriterium**), **Risiko der Darstellung** (welche Behauptung wäre gedeckt, welche nicht).
4. **Empfehlung:** die zwei bis drei Vorhaben mit dem besten Verhältnis aus Lesernutzen, Belegbarkeit und
   Aufwand, mit einer ersten Ausbaustufe, die in wenigen Tagen machbar ist — und klar benannt, wovon wir
   die Finger lassen sollten und warum.

Wenn du eine Annahme durch eine kleine Messung auf vorhandenen Dateien prüfen kannst (z. B. ob HAR die
Vola von SPY besser trifft als die 20-Tage-Vola), tu es und nenne Methode und Zahl. Spekulation als
solche kennzeichnen.
