# Planprüfung v3 — Gamma-Regime × Indikatoren × Saisonalität

Grundlage: [v2](2026-10-31_gamma_indikator_plan_v2.md), Ihre Antwort [..._v2_antwort.md](2026-10-31_gamma_indikator_plan_v2_antwort.md)
(TRAGFÄHIG MIT ÄNDERUNGEN, acht Punkte). Alle acht übernommen. Was v2 regelt und hier nicht widerrufen wird, gilt weiter.

## Inventur GEX-Archiv (gemessen auf dem Server)

`gex_history/*.json` (51 Dateien, 412 KB) je Ticker nur: `call_wall, put_wall, zero_gamma, net_gex_usd_bn, net_vanna,
net_charm, regime, skew, spot`. `gex_history_session/*.json` (11 Dateien) zusätzlich `gex_kette_vollst,
gex_horizont_tage, strike_stufe, felder`. **Keine kontraktweisen Eingaben** → der Altbestand bis 14.10. ist nicht neu
rechenbar und wird ausgeschlossen (Punkt 6). Das eingefrorene Inventar hält Hash, Session, Methodenversion und
Ausschlussgrund je Datei fest.

## Arm A — Definitionen (verbindlich)

**Richtungen.** RSI(2) < 10 → Long, > 90 → Short; RSI(14) < 30 → Long, > 70 → Short; %R(10) ≤ −95 → Long, ≥ −5 → Short;
LBR aufwärts → Long, abwärts → Short. Gerichtete Rendite = Rendite × (+1 Long / −1 Short). „Saison unterstützt“ =
Saisonänderung in Handelsrichtung (> 0 für Long, < 0 für Short), Saisonänderung exakt 0 → unbekannt (nicht
auswertbar für den Saisonkontrast).

**Indikatoren** (Schlusskurse aus `log_return` rekonstruiert, also eine Kursbasis; Hoch/Tief für %R über das
Verhältnis zum Schluss derselben Zeile, keine Division über Zeilen verschiedener Basis):
- RSI(n): Gewinne/Verluste aus `log_return`-Schlussänderungen; Start = einfaches Mittel der ersten n Änderungen, danach
  Wilder (`(alt·(n−1)+neu)/n`); gültig ab der (n+1)-ten Kurszeile. Nullfälle in dieser Reihenfolge: Mittelgewinn =
  Mittelverlust = 0 → unbekannt; Mittelverlust = 0 → 100; Mittelgewinn = 0 → 0.
- LBR: Fast = EMA(3) − EMA(10) der Schlüsse, Slow = EMA(16) der Fast; EMA mit SMA-Start über die ersten n Werte,
  α = 2/(n+1); gültig ab der ersten Slow-Zeile. Kreuzung aufwärts an `t`, wenn `F[t−1] − S[t−1] < 0` und
  `F[t] − S[t] > 0`; Gleichheit (`= 0`) zählt als keine Seite, die Kreuzung wird erst beim strikten Vorzeichenwechsel
  gemeldet.
- %R(10) = −100·(HH₁₀ − C)/(HH₁₀ − LL₁₀) über die letzten 10 Zeilen inklusive `t`; HH = LL → unbekannt.
- Lücken: fehlende Sitzung im Börsenkalender oder `log_return` ungültig → alle Indikatoren werden neu gestartet und
  sind erst nach vollem Warm-up auf zusammenhängenden Sitzungen wieder gültig.
- Eine Studienimplementierung, Handfälle gegen eine unabhängige Referenz (numpy, Formel unabhängig geschrieben).

**Saison.** Kalenderfenster der 20 Vorjahre `[J−20, J−1]`, gültig sind darin nur vollständige Jahre nach der
bestehenden Heuristik von `shared/true_seasonal.jahrVollstaendig` (übernommen, als Heuristik benannt), mindestens 10
gültige Jahre, sonst unbekannt. Kurve = Mittel der auf 100 normierten Jahreskurven auf der 365er-Achse des Kerns
(Schalttag wie dort gefaltet). Änderung von `t` bis zur 20. folgenden Sitzung = Kurve(Ziel)/Kurve(t) − 1; liegt das
Ziel im Folgejahr, wird verkettet: (Kurve_J(365)/Kurve_J(t)) · (Kurve_{J+1}(Ziel)/100) − 1, und **beide** Kurven
werden aus Jahren < J gebildet (für J+1 also ebenfalls `[J−20, J−1]`), kein Jahr ≥ J.

**Umfeld.** `VIX/VIX3M > 1` am Schluss von `t` = angespannt, sonst ruhig; fehlt einer der Werte → unbekannt.
Für ^GDAXI: der letzte US-Wert, dessen Sitzungsschluss vor dem XETRA-Schluss von `t` liegt (US-Schluss 22:00 MEZ >
XETRA 17:30 → praktisch die letzte abgeschlossene US-Sitzung vor dem Kalendertag `t`), Feiertage über den
Börsenkalender.

**Kontrollen.** Kontrolltage = alle zulässigen Tage (gültige Indikatoren, bekanntes Umfeld/Saison, vollständige
Zielperiode) **ohne** Signal derselben Regel, gleicher Ticker, gleicher Zeitabschnitt (Kalenderjahr), gleiches Umfeld,
gleiche Saisonklasse. Gerichtet wie das Signal.

**Effekte.**
`E(r,s) = mittlere gerichtete Signalrendite − mittlere gerichtete Kontrollrendite` in Zelle (Umfeld r, Saison s),
zuerst je Ticker × Jahr, dann über Jahre mit Gewicht = Signalzahl der Zelle, dann über die drei Kernreihen mit gleichem
Gewicht.
- H_U (Umfeld): `ΔU = ½·[E(a,+) + E(a,−)] − ½·[E(q,+) + E(q,−)]` (a angespannt, q ruhig, feste Gewichte ½ über die
  Saisonklassen).
- H_S (Saison): `ΔS = ½·[E(a,+) + E(q,+)] − ½·[E(a,−) + E(q,−)]` (+ unterstützt, − gegen).
- Pro Regel genau H_U und H_S → **16 Hypothesen**. Umfeldspezifische Saisonergebnisse nur beschreibend.
- Erwartete Richtung vorab: ΔS > 0 (Saison in Handelsrichtung hilft). Für ΔU keine Richtung vorab (Mean-Reversion-
  Regeln könnten in Stress besser, Trendregeln schlechter laufen) → H_U zweiseitig als „Abhängigkeit“, H_S einseitig
  als „Verbesserung“.

**Test.** Gemeinsamer stationärer Datumsbootstrap auf der Sitzungsachse aller Reihen (Blocklänge erwartet 40,
Sensitivität 20/60), B = 10 000 Ziehungen, Seed fest; Feinziehung auf 100 000 nur für Hypothesen mit p im
Holm-Grenzbereich ±50 %, vorab geregelt. Alle Hypothesen nutzen dieselben Ziehungen, Kontrollmittel je Ziehung neu.
p zweiseitig über die nullzentrierte Abweichung `|T* − T| ≥ |T|`, einseitig `T* − T ≥ T`, jeweils `(1+#)/(1+B)`.
Mindestbesetzung: jede der vier Zellen (a/q × +/−) je Kernreihe ≥ 20 Signale und ≥ 200 Kontrolltage im jeweiligen
Zeitraum, sonst ist die Hypothese **nicht auswertbar**, bleibt in der 16er-Familie (zählt für Holm) und kann nicht
verworfen werden; fehlt eine Kernreihe in einer Zelle, wird nicht umgewichtet, sondern die Hypothese ist nicht
auswertbar. Bootstrap-Ziehungen mit leerer Zelle werden gezählt und als extrem (gegen H₀ sprechend nicht) gewertet,
also konservativ zur Nullverteilung hinzugenommen; Anteil > 5 % → Hypothese nicht auswertbar.
Episoden: aufeinanderfolgende Signaltage derselben Regel und Reihe mit Abstand < 5 Sitzungen = eine Episode
(„zeitlich getrennte Episoden“), je Zelle ausgewiesen.

**Zeiträume.** Datenende fest: **2026-10-30** (letzte abgeschlossene Sitzung beim Plan), Export-Hash eingefroren.
Entdeckung: Signaltage bis 2018-12-31, deren Zielperiode (5 HT bzw. Horizont h) vollständig bis 2018-12-31 endet;
Prüfzeitraum: Signaltage ab 2019-01-01, Warm-up darf auf Daten vor 2019 zurückgreifen, Ergebnisse der Entdeckung
nehmen keine Daten ab 2019 auf. Pro Horizont nur Ereignisse mit vollständiger Zielperiode; offene separat gezählt.
Bestätigt ist eine Hypothese, wenn sie in der Entdeckung (Holm über 16) verworfen wird **und** im Prüfzeitraum mit
derselben Richtung bei Holm über die dort geprüften Hypothesen verworfen wird.

## Handelsmodell (nur Arm A)

Einstieg: nächstes reguläres Open nach dem Signalschluss (Rendite der Einstiegssitzung über den Intraday-Anteil wie
in der Williams-Studie). Primäre Kontokurve: Ausstieg am Schluss der 5. gehaltenen Sitzung; je Horizont eine eigene
beschreibende Kurve. Gegensignal während der Haltezeit: ignoriert (fester Ausstieg); Wiederholungssignal: kein
Nachkauf; neues Signal erst ab dem Tag nach dem Ausstieg wirksam. Kapital: je Kernreihe ein Drittel, je Position
das volle Reihenkapital, freie Liquidität 0 % Zins, kein Rebalancing zwischen den Reihen. Kosten 2 Bp je Seite,
Belastungstest **10 Bp je Seite**. MAE und Peak-to-Trough aus der tatsächlichen Position ab dem Einstiegspunkt
(Schlusskursbasis, Einstiegssitzung über Open-Anteil). Shorts ohne Leihe nur beschreibend. ^GDAXI nicht handelbar.

## Arm B (GEX) — beschreibend

Nur Sessions ab 2026-10-15 mit Session-Stempel; ohne 19.10. (fehlt) und 20.10. (nachgeholt, IV vom Folgemorgen).
Klassifikation = archiviertes `regime`, sofern für die Methodenversion belegt ist, dass es aus dem ungerundeten
Netto-GEX stammt (`snapshot_gex_massive.py:465`); `net_gex_usd_bn == 0.0` (gerundet) → unbekannt. Ausgabe:
Forward-Renditen 1/5/10/15/20 HT mit Fallzahl, keine Tests, keine Handelsaussage. Neu: der GEX-Lauf schreibt ab
sofort zusätzlich den ungerundeten Wert und einen Nullzustand in ein Forschungsprotokoll (eigene kleine Änderung,
eigener Commit).

## Arm C — gestrichen (Ihre Empfehlung).

Fragen: Sind die acht Punkte nun operationalisiert? Insbesondere: die Behandlung leerer Bootstrap-Zellen, die
Gewichtung von E(r,s), die Saisonverkettung am Jahreswechsel. Was fehlt noch vor dem Studiencode? Schluss: TRAGFÄHIG,
TRAGFÄHIG MIT ÄNDERUNGEN oder NICHT TRAGFÄHIG.
