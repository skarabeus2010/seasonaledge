# KI-Modelle und Analysen für SeasonAlpha — Katalog mit Vorschlägen (2026-10-09)

Du arbeitest read-only im Repo `C:\dev\Seasonaledge`, **mit Websuche**, Deutsch mit echten Umlauten. Belege
Modelle, Versionen, Lizenzen und Preise mit Quellen (URL); kennzeichne, was du nicht prüfen konntest.

## Frage des Nutzers (wörtlich sinngemäß)

„Welche Modelle gibt es, die wir für Analysen benutzen können — und welche Analysen können wir damit machen?“
Es geht ausdrücklich um **Analysen** (Forschung, Studien, Seiten-Features, Blogartikel), nicht um Marketing-KI.

## Was schon existiert (bitte lesen, nicht wiederholen)

- `docs/review_prompts/2026-10-09_ki_modelle_evaluation_antwort.md` — erste Runde: Erklärtexte, HAR/EWMA-Vola,
  Ähnlichkeitssuche; HMM, Chronos/TimesFM/Moirai, Chat, News-Sentiment zurückgestellt.
- `docs/review_prompts/2026-10-09_ki_markt_analyse_codex.md` und `..._agent.md` — Marktanalyse (Wettbewerber,
  Regulierung, Nutzer).
- Validierung Saison-Score: `scripts/research/saison_score_validierung_ergebnis.json` — kein Rangzusammenhang
  (Spearman 0,019). Lehre: Renditeprognosen aus Saisonalität tragen nicht; jede neue Analyse braucht ein vorab
  festgelegtes Protokoll und einen Vergleich gegen einfache Referenzen.

## Unsere Daten (am Code prüfen)

Tagesschlusskurse + OHLC + log_return für ~370 Ticker in Supabase (`prices`, teils ab 1895), TDOM/TDOY-Statistiken,
Optionsdaten (Skew, IV, Term-Struktur, GEX, OI je Strike, `options_skew_history.json`), Polymarket-Preise und
Auflösungen, Intermarket-Matrix, Wahlen, Börsenkalender/Ereignisse (OPEX, FOMC, Feiertage), Stress-Score.
Rechner: VPS 4 GB RAM, keine GPU; lokal Windows ohne GPU-Annahme. Budget klein.

## Gewünschte Ausgabe

1. **Modellkatalog** nach Familien, je Familie die konkreten, heute verfügbaren Modelle/Bibliotheken mit Version,
   Lizenz, Kosten, Hardwarebedarf (läuft es auf 4 GB CPU?) und Quelle. Mindestens:
   - Zeitreihen-Foundation-Modelle (z. B. Chronos/Chronos-Bolt/Chronos-2, TimesFM, Moirai, Lag-Llama, TiRex,
     Toto, TabPFN-TS — prüfe, was 2026 aktuell ist),
   - klassische Statistik/Ökonometrie (GARCH-Familie, HAR, Zustandsraum, Changepoint/Bayesian Online CPD, HMM/
     Regime-Switching, Quantilregression, Conformal Prediction),
   - Machine Learning auf Tabellen (Gradient Boosting, Random Forest, TabPFN) inkl. Erklärbarkeit (SHAP),
   - unüberwachtes Lernen (Clustering, Ähnlichkeitssuche/DTW, Matrix Profile, Isolation Forest),
   - Sprachmodelle (Claude, GPT, Gemini, offene Modelle wie Llama/Qwen/Mistral) für Text, Extraktion,
     Faktenblatt-Erklärungen, Code-/Forschungsassistenz; Embedding-Modelle,
   - Kausal-/Ereignisstudien-Methoden (Synthetic Control, Difference-in-Differences) falls sinnvoll.
2. **Analysekatalog:** konkrete Analysen, die mit UNSEREN Daten möglich sind — je Analyse: Frage, Daten, Modell(e),
   einfache Referenz, Zielgröße, Protokoll (Zeitraum, Walk-forward, Mehrfachtest), erwarteter Nutzen für Seite/Blog,
   Aufwand (Tage), Risiko (Overfitting, Regulierung, Missverständnis beim Leser). Mindestens 12 Analysen über
   Saisonalität, Volatilität, Optionen/Skew, Regime, Intermarket, Polymarket, Ereignisse, Datenqualität.
3. **Priorisierung:** Top 5 mit Begründung, je mit einem ersten Experiment (eine Woche), Abbruchkriterium und
   was auf der Seite erscheinen dürfte — beschreibend vs. prognostisch klar getrennt.
4. **Was wir NICHT tun sollten** und warum (mit Beleg).

Schreibe so, dass das Ergebnis direkt als Projektdokument `docs/KI_ANALYSEN.md` dienen kann.
