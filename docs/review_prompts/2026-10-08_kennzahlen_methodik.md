# Methodische Validierung: Crash-Ampel, KI-Composite-Score, Anomalie-Radar

Repo `C:\dev\Seasonaledge` (öffentliche Website seasonalpha.ai, statisches Frontend `landing/`, Python-Backend
`shared/` + `scripts/`). **Nur lesen und bewerten — keine Dateien ändern.** Python für Messungen:
`C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe` (lokal ohne Datenbankzugang; Kurse nur
über eingefrorene Dateien, falls du welche brauchst: Schnappschuss `C:/Users/HEIKOS~1/AppData/Local/Temp/claude/c--dev-Seasonaledge/b1245851-7084-4449-b6ab-61b4ed04fde7/scratchpad/pv_kurse/*.json`
mit `{date, close}` für ^DJI, ^GSPC, SPY, QQQ, ^GDAXI, Stand 07.10.2026).

## Auftrag
Prüfe für jede der drei Kennzahlen, **was sie tatsächlich rechnet** (am Code, nicht an Kommentaren oder Seitentexten),
**wie aussagekräftig** sie ist und **ob an der Methodik etwas zu ändern ist**. Danach: weitere Vorschläge.

1. **Crash-Ampel / Crash-Frühwarnung** — Seite `landing/pages/crash-fruehwarnung.html`, Berechnung
   `scripts/compute_regime_scores.py` (Tabelle `regime_scores`: `risk_score` 0–100, `traffic_light`), Verwendung
   u. a. in `shared/daily_report.py`, `shared/weekly_report.py`, `landing/js/dash-compute.js`.
2. **KI-Composite-Score** — `landing/js/dash-compute.js` (ab Zeile ~175: 4 Sub-Scores à 0–2,5 → 0–10, Schwellen
   bullish ≥ 6,5 / bearish ≤ 3,5), Backend-Zwilling `shared/ki_score.py` mit `shared/ai_models.py`
   (`find_similar_years`, `forecast_seasonal`) und `shared/outlier_manager.py`; Seite `landing/pages/ki-saisonalitaet.html`
   und Dashboard.
3. **Anomalie-Radar** — `shared/anomaly_engine.py` (misst laut Doku nur 10 Tage), Frontend-Gegenstück in
   `landing/js/seasonal-compute.js` bzw. `decade-compute.js` (suche nach anomal*), Dashboard.

## Je Kennzahl beantworten
- **Definition:** Eingaben, Formel, Fenster, Schwellen, Gewichte — mit Datei:Zeile.
- **Zwillinge:** Rechnen Backend und Frontend dasselbe? Abweichungen mit konkretem Eingabefall.
- **Look-ahead / Datenrand:** Fließen Informationen ein, die zum Bewertungszeitpunkt nicht bekannt waren (ganze
  Jahreskurven, spätere Kurse, im Nachhinein gewählte Ähnlichkeitsjahre, Ausreißerbereinigung mit Zukunftswissen)?
  Was passiert am Datenrand und bei fehlenden Daten (Lücke oder alter Wert)?
- **Statistische Aussagekraft:** Stichprobengröße, Mehrfachtests, Überanpassung, Basisrate. Sind die Schwellen
  (z. B. 6,5/3,5, Ampelgrenzen) empirisch belegt oder gesetzt? Gibt es eine Validierung (Trefferquote, Kalibrierung,
  Vorlauf vor echten Crashs, Fehlalarme)? Wenn nein: wie müsste eine aussehen (vorab festgelegte Ereignisdefinition,
  Out-of-Sample, Vergleich mit einer naiven Basis)?
- **Darstellung:** Was suggeriert die Seite (Name „KI", „Frühwarnung", Ampelfarben, Prozentangaben) im Verhältnis zu
  dem, was gerechnet wird? Wo ist der Text stärker als die Messung?
- **Urteil:** behalten / Methodik ändern / umbenennen bzw. anders darstellen / abschalten — mit Begründung und
  Priorität (hoch/mittel/niedrig).

## Hinweise
- Bekannte Projektlehren: „KI" heißt hier seit KW16 keine ML-Pipeline mehr (stillgelegt); `ai_models.py` lebt aber
  und wird von `ki_score.py` importiert. Zwei Zwillinge haben in diesem Projekt mehrfach verschieden gerechnet.
- Behaupte nichts ohne Beleg; wo du etwas nicht prüfen kannst, sag es.
- Antwort auf Deutsch, strukturiert je Kennzahl, am Ende eine priorisierte Liste „Weitere Vorschläge".
