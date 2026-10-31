# Planprüfung v2 — Gamma-Regime × Indikatoren × Saisonalität

Grundlage: [v1](2026-10-31_gamma_indikator_plan.md), Ihre Antwort [..._antwort.md](2026-10-31_gamma_indikator_plan_antwort.md)
(TRAGFÄHIG MIT ÄNDERUNGEN, zehn Punkte). Alle zehn übernommen; neu sind die Nutzerentscheidung und eine Messung.

## Nutzerentscheidung (2026-10-31) und Messung

- **Keine neuen kostenpflichtigen Daten.** Gearbeitet wird mit dem vorhandenen GEX-Bestand; rekonstruieren nur, was
  mit dem bestehenden Massive-Zugang geht.
- **Gemessen am Massive-Zugang (lesend, vom Server):** Tagesaggregate je Kontrakt (`/v2/aggs`, `/v1/open-close`)
  liefern o/h/l/c/Volumen/VWAP, **kein Open Interest**. Der Options-Snapshot liefert OI/Greeks/IV nur für **laufende**
  Kontrakte (ein verfallener Kontrakt gibt 404, ein `date`-Parameter ändert nichts). `/v3/reference/options/contracts`
  mit `as_of` liefert die damals gelisteten Kontrakte, ohne OI. → **OI-basierte GEX ist rückwirkend nicht
  rekonstruierbar.** Rekonstruierbar wäre nur eine **volumengewichtete** Gamma-Größe (Volumen statt OI, IV per
  BS-Inversion wie beim Skew-Backfill) — das misst gehandelte, nicht offene Positionen und keine Richtung.

## Plan v2 — drei getrennte Studienarme

**Arm A — Volatilitätsumfeld × Indikator × Saison (konfirmatorisch, lange Historie).**
- Regime: genau **eine** vorab festgelegte Regel `VIX/VIX3M > 1` („Volatilitätsumfeld angespannt“), benannt als
  Volatilitätsmerkmal, nicht als Gamma. VIX9D/VIX und RV21/VIX nur explorativ. Abdeckung vor dem Bau messen
  (^VIX3M-Reihe in der DB: Beginn prüfen; Cboe-Historie VIX3M ab 2007-12).
- Kern konfirmatorisch: SPY, QQQ, DIA. Explorativ: ^GDAXI (mit dem zuletzt **vor** dem XETRA-Entscheidungszeitpunkt
  bekannten US-Regime, also dem Vortag), AAPL MSFT NVDA AMZN GOOGL META TSLA AVGO BRK-B LLY als heute ausgewählte feste
  Fallstudie (keine historische Top-10-Aussage).
- Acht gerichtete Signalregeln: RSI(2) < 10 / > 90, RSI(14) < 30 / > 70, LBR-Fastline kreuzt Slowline nach oben/unten
  (3/10/16, neue Ereignisregel, nicht der bestehende Null-Filter), Williams %R(10) ≤ −95 / ≥ −5 mit
  `%R = −100·(HH₁₀ − C)/(HH₁₀ − LL₁₀)`, Nullspanne → unbekannt. Formeln (Wilder-RSI mit SMA-Start, Warm-up,
  Nullfälle: keine Verluste → 100, flach → unbekannt, Lücken) vorab fest; **eine** Studienimplementierung gegen eine
  unabhängige Referenz geprüft; der Bestand (`indicators.js`, `shared/indicators.py`) wird nicht übernommen, seine
  Abweichungen (RSI(2) [1,2,3,4] = 99,0099) gehen als eigener Posten in die TODO-Liste.
- Saisonmerkmal: genau eines — Vorzeichen der True-Seasonal-Kurve von `t` bis zur 20. folgenden Börsensitzung, Kurve
  nur aus vollständigen Vorjahren vor `t` (mind. 10, höchstens 20), Abbildung Sitzung → Kurventag über das
  Kalenderdatum, am Jahreswechsel beide Werte aus dem Informationsstand von `t`, zu wenig Historie → unbekannt. TDOM
  nur explorativ.
- Hauptfrage = **Zusatznutzen**: (1) verbessert das Volatilitätsumfeld dieselbe Indikatorregel (Differenz
  Regel∩angespannt − Regel∩ruhig, Interaktion)? (2) verbessert das Saisonmerkmal die Regel innerhalb desselben
  Umfelds? Kontrollen je Ticker × Zeitabschnitt × Umfeld (× Saisonklasse beim bedingten Effekt); dazu die ungefilterte
  Regel. Pooling über die drei Kernreihen mit gleichem Gewicht je Reihe.
- Konfirmatorisch nur **5 HT**; 1/10/15/20 HT beschreibend. Familie Kern: 8 Regeln × 2 Zusatznutzen-Fragen = 16
  Hypothesen, Holm über 16, Nullhypothese „Differenz = 0“, p aus einem **gemeinsamen stationären Datumsbootstrap**
  (erwartete Blocklänge 40, Sensitivität 20/60), dieselben Ziehungen für alle Reihen und Hypothesen, Kontrollmittel je
  Ziehung neu. Zusätzlich Zahl unabhängiger Episoden je Zelle.
- Zeitplan: Entdeckung bis 2018-12-31 (vor der Aufbereitung abgeschnitten), Prüfzeitraum 2019-01 … letzte
  abgeschlossene Sitzung einmalig nach Einfrieren aller Varianten an einem Commit; als „reservierter historischer
  Test“ bezeichnet, nicht als unberührt.

**Arm B — OI-basierte GEX-Schätzung (beschreibend, kurz).**
- Benennung „OI-basierte GEX-Schätzung mit festen Dealer-Annahmen“. Klassifikation nur das ungerundete
  Netto-GEX-Vorzeichen je Titel; `gamma_index` getrennt und nur beschreibend.
- Vorher ein eingefrorenes Inventar (Hash, Session, Abrufzeit, Methodenversion, Spot-Herkunft, Abdeckung,
  Ausschlussgrund). Ausgeschlossen: alles vor B2 (Stempelversatz **und** veralteter Spot bis 13.10.), die nachgeholte
  Session 20.10. (IV vom Folgemorgen); 19.10. fehlt → unbekannt. Verbleibend etwa 9–10 saubere Sessions.
- Ausgabe: Forward-Renditen 1/5/10/15/20 HT der vorhandenen Sessions je Regime mit Fallzahl, ohne Test, ohne
  Handelsaussage; Konfusionsmatrix Arm-A-Umfeld gegen GEX-Vorzeichen mit Mehrheitsklassen-Baseline. Prospektive
  Fortschreibung; ein erster Prüfpunkt erst bei ausreichend getrennten Episoden in beiden Regimen.
- Frage an Sie: lohnt der Altbestand 03.08.–14.10. eine Neubewertung, falls die Archive die Rohketten oder Strike-
  Profile mit Abrufzeit enthalten (mit korrigiertem Spot neu rechnen)? Ich prüfe vor dem Bau, was die Dateien tragen.

**Arm C — volumengewichtete Gamma-Größe (explorativ, optional).** Rekonstruierbar für SPY/QQQ/DIA über die Skew-
Backfill-Mechanik (Aggregates + BS-Inversion), Volumen statt OI. Nur als Aktivitätsmaß, ausdrücklich keine
Positionierung. Ich würde Arm C erst nach Arm A angehen — oder ganz weglassen? Bitte Ihre Einschätzung.

**Handelsmodell und Drawdown (alle Arme).**
- Zwei getrennte Ausgaben: Ereignisdiagnostik Schluss `t` → Schluss `t+h` (ohne Ausführbarkeitsbehauptung) und
  Handelsregel mit Einstieg am nächsten regulären Open nach Verfügbarkeit aller Eingaben. Open-Einstieg ohne Division
  über verschiedene Bereinigungsbasen (Muster Williams-Studie: Intraday-Anteil der Einstiegssitzung über das
  Residuum).
- Je Ereignis MAE ab Einstieg und Peak-to-Trough-Drawdown (Schlusskurse; intraday kann es mehr sein). Je Regel eine
  Kontokurve: eine Position je Reihe, kein Nachkauf bei Wiederholungssignal, Kapital gleich auf die Kernreihen
  verteilt, Kosten 2 Bp je Seite, Belastungstest 10 Bp, Shorts ohne Leihekosten-Annahme nur beschreibend; ^GDAXI als
  nicht direkt handelbar gekennzeichnet.

**Umsetzung:** `scripts/research/gamma_indikator.py`, nur lesend, Export `logs/gamma_indikator/` mit SHA-256,
Wächter mit Handfällen und Mutationstest wie bei der Williams-Studie. Keine Seite, keine Mail, bis der Prüfzeitraum
geöffnet und ausgewertet ist.

Fragen: Sind die zehn Punkte richtig umgesetzt? Ist die Hauptfamilie (16 Hypothesen) so sinnvoll und die
Interaktion richtig formuliert? Arm C ja/nein? Was fehlt noch vor dem Bau? Schluss: TRAGFÄHIG, TRAGFÄHIG MIT
ÄNDERUNGEN oder NICHT TRAGFÄHIG.
