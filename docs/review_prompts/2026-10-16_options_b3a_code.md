# Code-Review B3a — Skew-Rang einmal im Cron, /skew und Mail lesen ihn

Plan: `docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3.md` (B3) + `_v4.md` (Präzisierungen gültige
Zahl / Zeta-Fallback); deine Freigabe B3 in `…_plan_v3_antwort.md`/`…_plan_v4_antwort.md`. B1/B2 sind live. Code
uncommittet im Arbeitsbaum (`git diff` + neue Dateien `shared/skew_rang.py`, `scripts/js/skew_rang_ref.js`,
`scripts/js/probe_skew_rang_seite.js`, `scripts/verify_skew_rang.py`, `scripts/verify_skew_rang_mutation.py`). Python:
`C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`, `PYTHONUTF8=1`. Read-only, Deutsch,
Datei:Zeile, Schwere, am Ende **FREIGABE (Code): ja/nein**.

B3 aufgeteilt: **B3a** (hier) = Rang wie im Plan; **B3b** (später, eigener Plan) = IV/RV-Verhältnis + neutrale
Extremlisten (Nutzerwunsch 15.10.).

## Umsetzung
- `shared/skew_rang.py`: `rang_ticker(arr, session, fenster)`, `rang_gesamt(hist, session)` genau nach Vertrag
  (Fenster S−W ≤ date ≤ S ab der Session, cm/cm_extrap, sortiert, doppelte Daten → None, je Metrik eigenes n:
  gültig filtern → letzter gültiger Wert = Session → n ≥ 20; rr = call−put, iv = (put+call)/2, skew, Zeta-Paar mit
  Fallback (IV − iv_atm)·100; Rank/Percentile halb nach oben; Ausgabe mit `wert`).
- `scripts/js/skew_rang_ref.js`: unabhängige JS-Referenz nach Spezifikation (nicht aus der Seite kopiert).
- `scripts/compute_options_skew.py`: im Sperrblock nach dem Zusammenführen `out["rang_session"] = session`,
  `out["rang"] = rang_gesamt(hist, session)`; der Snapshot wird danach unter derselben Sperre geschrieben (B1).
- `landing/pages/skew.html`: eigene Rechnung (`_normHist`, `_rank`, `_pctl`, `MIN_NORM`, Fenster ab `Date.now()`)
  entfernt; `SKEW_RANG = d.rang` nur bei `rang_session === session`; Radar (beide Ansichten) und die Spalten IV-Rank /
  Skew-Rk lesen `rang[t][Fenster][Metrik]` je Modus. Der Radar wird jetzt aus dem Snapshot gezeichnet (wartet nicht mehr
  auf die History; die History dient nur noch der Detailansicht).
- `shared/daily_report.py::skew_pctl_map`: `rang[t]["365"]["skew"]["pctl"]`, nur bei `rang_session == session ==
  letzte_session("NYSE")` zum Versandzeitpunkt; Test-Haken `_SNAPSHOT_PFAD`. Vorlage: Skew-Zelle einfarbig (`nu`),
  fehlendes Perzentil sichtbar „P—“, Tooltip „Put-IV relativ zur Call-IV im Vergleich zur eigenen Historie“.

## Nachweise
- `verify_skew_rang.py` (im Gate): Sollwerte (konstant, steigend, x,5-Percentile 12,5 → 13, 19/20 Punkte, Grenze S−92,
  fehlender aktueller Wert in einer Metrik, veraltete Reihe, Zeta ohne iv_atm, doppeltes Datum, nicht normierte Zeilen,
  bool/Text), Python = JS-Referenz auf allen Fixtures, Cron (rang_session, heutiger Punkt drin), Seite (echtes Seiten-JS:
  Percentile/Rank, 3 M./1 J., beide Ansichten, Session-Abweichung → keine Punkte), Mail (Session-Abgleich, Fenster) und
  Vorlage. Core-Fixtures mit Session ≠ heute, Cron mit eigener Uhr (sonst fiele „Fenster ab der Uhr“ nicht auf).
- Mutationstest **17/17**.
- Python = JS auf der echten Live-History (150 Ticker, Session 15.10.) identisch.
- Wirkungsbericht `docs/review_prompts/2026-10-16_options_b3a_wirkung.md` (alt = Seitenrechnung aus HEAD).

## Prüfaufträge
1. Vertrag eingehalten (auch: Ticker, die nur in der History, nicht im Snapshot stehen; Zeitzone/Datumsformat)?
2. Seite: bleibt irgendwo eine eigene Rangrechnung oder ein Uhrbezug? Verhalten bei fehlendem `rang` (Altdatei).
3. Mail: Versand am Montag/nach Feiertag (erwartete Session), Snapshot vom Wochenendlauf.
4. Wächter: echte Funktionen? Fehlende Mutationen?

## Nachtrag
Ganzes Gate lokal grün (26 Prüfskripte + drei lokale Seitenproben). `verify_radar_quadranten.py` angepasst: die X-Größe steht jetzt in `shared/skew_rang.py` (`"rr": _diff(ci, pi)`), die Seite trägt `rr` auf X ab — vorher prüfte der Wächter die entfernte Seitenformel.
