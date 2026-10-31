# Nachtrag 3 — Auswertung auf beobachteten Schlusskursen (Nutzerentscheidung „Variante B“, 2026-10-31)

Antwort Nachtrag 2: [..._nachtrag2_antwort.md](2026-10-31_drawdown_seite_plan_v3_nachtrag2_antwort.md) — NICHT
TRAGFÄHIG, berechtigt: eine Brücke beweist keinen vollständigen Pfad, wenn der fehlende Tag ein Handelstag war
(100 → 200 → 90 → 100). Der Nutzer hat zwischen A (streng: Auswertung erst nach der letzten ungeklärten Fehlstelle;
DAX erst ab 2000, EURUSD praktisch keine Historie) und **B (beobachtete Schlusskurse)** entschieden: **B**.

## Vertrag B (eigener, benannter Vertrag — nicht „uneingeschränkt globale“ Kennzahlen)
Gegenstand der Seite ist der Drawdown **auf den beobachteten Schlusskursen** des Tickers. Ein Tag ohne Kurs ist
kein Teil der Reihe — dieselbe Art Unschärfe wie Intraday-Extreme, die ein Schlusskurs-Drawdown ohnehin nicht sieht.
1. Achse = Kalendersitzungen bis E, aus denen Sitzungen ohne Kurszeile entfallen, wenn:
   (a) das Jahr nicht `belegt` ist (`ungeprueft`/`annahme`; FOREX-Konvention zählt dazu; **CRYPTO nie**),
   (b) höchstens 2 Sitzungen in Folge fehlen,
   (c) eine spätere Zeile existiert (nicht Reihenende) und
   (d) Konsistenzprüfung: Σ log_return (v, n] = ln(close_n/close_v) auf 1e-6 (sonst Datenfehler → echte Lücke).
   In `belegt`-Jahren, bei CRYPTO, bei > 2 in Folge oder fehlgeschlagener Konsistenz: echte Lücke, globaler Pfad ab
   dort unbekannt (v3). Fehlende Endzeilen vor E: „nicht aktuell“ (kein laufender Drawdown, keine Ränge).
2. **Alle Sitzungszählungen heißen „Handelstage mit Kurs“** (Drawdown-Dauer, Peak to Trough, Time to Recovery,
   KM-Zeit, Forward-Horizonte 20/60/120). Kalendertage bleiben echte Kalendertage. Damit gilt dein Befund 2 (20
   Achsenschritte ≠ 20 Börsensitzungen) als benannte Definition, nicht als stiller Bruch.
3. **Kennzeichnung**, sobald n > 0: „n Tage ohne Kurs (Jahre a–b) als geschlossen behandelt. Waren es Handelstage,
   sind Hoch oder Tief an diesen Tagen nicht erfasst; Peaks, Drawdowns und Dauern können dann abweichen.“ Im
   Methodiktext dieselbe Definition; in der Mail (Phase 2) ein Kennzeichen am Ticker, wenn n > 0 im ausgewerteten
   Zeitraum.
4. Ränge/Gruppen/KM/Forward unverändert auf dieser Achse.

## Wächterfälle
Deine beiden Gegenbeispiele (−50 % fehlt; neues Hoch 200 fehlt) in einem `ungeprueft`-Jahr → Ergebnis = Rechnung auf
den beobachteten Schlüssen (−10 % / abgeschlossen), **mit** Kennzeichnung n = 1; dieselben in einem `belegt`-Jahr und
bei CRYPTO → echte Lücke; Konsistenz verletzt → Lücke; 3 in Folge → Lücke; fehlende Endzeilen → nicht aktuell;
Zählung „Handelstage mit Kurs“ an einem Forward-Fall über eine überbrückte Sitzung.

Frage: Ist B so als benannter Vertrag tragfähig (Bezeichnung, Kennzeichnung, Schutzregeln)?
Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT TRAGFÄHIG.
