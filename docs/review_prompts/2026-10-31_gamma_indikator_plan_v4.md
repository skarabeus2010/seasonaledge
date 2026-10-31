# Planprüfung v4 — Gamma-Regime × Indikatoren × Saisonalität

Grundlage: [v3](2026-10-31_gamma_indikator_plan_v3.md), Ihre Antwort [..._v3_antwort.md](2026-10-31_gamma_indikator_plan_v3_antwort.md)
(TRAGFÄHIG MIT ÄNDERUNGEN, acht Punkte). Alle acht übernommen; was v3 regelt und hier nicht ersetzt wird, gilt weiter.

## Ersetzt in v3

**1. Kontraste je Ticker × Jahr, gemeinsame Gewichte.**
`ΔU_i,y = ½·(E_i,y(a,+) + E_i,y(a,−) − E_i,y(q,+) − E_i,y(q,−))`,
`ΔS_i,y = ½·(E_i,y(a,+) + E_i,y(q,+) − E_i,y(a,−) − E_i,y(q,−))`.
Aggregation: gleiches Gewicht je zulässigem Jahr innerhalb des Tickers, danach je ein Drittel über SPY/QQQ/DIA.
Dieselbe Regel im Prüfzeitraum. (Ihr Gegenbeispiel 180/20 vs. 20/180 → ΔU = 0 als Handfall im Wächter.)

**2. Gemeinsame Jahresmenge.** Je Regel × Ticker sind nur Jahre zulässig, in denen alle vier Signalmittel und alle
vier Kontrollmittel (a/q × +/−) bestimmbar sind (≥ 1 Signal, ≥ 1 Kontrolltag je Zelle); dieselbe Jahresmenge trägt
ΔU und ΔS. Ausgeschlossene Jahre mit Grund ausweisen, nichts durch 0 ersetzen. Zusätzlich gilt die Mindestbesetzung
aus v3 über die **zulässigen** Jahre (je Zelle und Kernreihe ≥ 20 Signale, ≥ 200 Kontrolltage) und mindestens 3
zulässige Jahre je Kernreihe, sonst nicht auswertbar.
**Besetzungsinventur zuerst:** gültige Saisonjahre, Signal-/Kontrollzahlen, Episoden und zulässige Jahre je Zelle —
gerechnet **ohne Renditen**, als eigener Export mit Hash, bevor eine Rendite angesehen wird. Reicht die Besetzung
nicht, lautet das Ergebnis „nicht auswertbar“; keine Schwelle wird nachträglich gelockert.

**3. Ungültige Ziehungen erhöhen p.** `p = (1 + gültige Überschreitungen + ungültige Ziehungen)/(1 + B)`. Ungültig =
ein benötigtes Mittel einer zulässigen Jahreszelle ist in der Ziehung nicht bestimmbar (die Jahresmenge bleibt die
der Originaldaten). Nicht verwerfen, nicht nachziehen, nicht umgewichten. > 5 % ungültig → nicht auswertbar, p = 1
für Holm.

**4. Bootstrap-Vertrag.** Signale, Saisonklassen, Umfeld und vollständige Zielrenditen werden einmal auf der
ursprünglichen Sitzungsachse berechnet (je Beobachtung: Datum, Ticker, Jahr, Zelle, Signal ja/nein, Zielrendite).
Gezogen werden gemeinsame Datumsblöcke (stationär, erwartete Blocklänge 40, zirkulär über die Datumsachse des
jeweiligen Zeitraums); jede gezogene Beobachtung behält Ticker-, Jahres- und Zellzuordnung; Mittel und Kontraste
werden je Ziehung neu bestimmt. Keine Neuberechnung von Indikatoren oder Forward-Renditen über Blockübergänge.
**B = 100 000 gemeinsame Ziehungen für alle 16 Hypothesen, Seed 20261031**, keine Feinziehung. Blocklänge 20/60 nur
als Sensitivität, ersetzt kein Hauptergebnis. Vorab synthetische Nullfälle (AR(1)-Renditen mit Jahresniveau-Sprüngen,
kein Signaleffekt): die Verwerfungsrate bei α = 0,05 muss ≤ 0,07 liegen, sonst wird der Test vor der Auswertung
überarbeitet.

**5. Saison:** eine am Signalzeitpunkt eingefrorene Kurve (beide Jahresteile identisch). Aufruf des Kerns mit
`min_jahre=10` ausdrücklich. Handfälle: 108 → 110 → 102 ergibt +3,8889 %; Änderung von Daten ab Jahr J ändert die
Saisonklasse eines Signals aus J nicht.

**6. LBR / Renditen / %R.** Nachbarregel bestätigt: Kreuzung nur bei `F−S < 0` an `t−1` und `> 0` an `t` (bzw.
umgekehrt); die Folge −1, 0, +1 erzeugt **kein** Signal. RSI aus Differenzen der aus `log_return` rekonstruierten
Kursstände (klassischer Wilder-RSI). Primäres Renditemaß der Tests: **gerichtete Logrendite** (Long +r, Short −r);
einfache Renditen nur in der Kontokurve. %R unbekannt, wenn Hoch/Tief fehlen oder `Tief ≤ Schluss ≤ Hoch` bzw.
`Tief ≤ Hoch` verletzt ist.

**7. Kontokurve.** Stückzahl beim Einstieg = Reihenkapital / Einstiegskurs, gehalten bis zum Ausstieg; P&L Long =
Stück·(Kurs − Einstieg), Short = Stück·(Einstieg − Kurs); Kapital = Barbestand + P&L der offenen Position, tägliche
Bewertung zum Schluss. Fehlender Einstiegs-Open → Trade entfällt und wird gezählt; fehlende Bewertung oder fehlender
Ausstiegskurs (Lücke im Börsenkalender oder ungültige Zeile) → Ausstieg zum ersten gültigen Schluss danach, als
„verschobener Ausstieg“ gezählt und ausgewiesen; keine stille Fortschreibung.

**8. Arm B.** `net_gex_usd_bn == 0.0` bleibt ausgeschlossen, auch wenn das archivierte `regime` ein Vorzeichen trägt
(gerundete Null beweist keinen Nullzustand). Forschungsprotokoll speichert Rohwert, echten Nullzustand, Session,
Abrufzeit und Methodenversion gemeinsam.

## Baufolge

1. GEX-Forschungsprotokoll (klein, eigener Commit).
2. Studienkern + Wächter (Handfälle: Indikatoren, Saisonverkettung, ΔU-Gegenbeispiel, ungültige Ziehungen, Short-P&L,
   synthetische Nullfälle) + Mutationstest.
3. Besetzungsinventur (ohne Renditen) → Ihnen und dem Nutzer vorlegen.
4. Einfrieren an einem Commit, Entdeckung auswerten, Prüfzeitraum einmalig öffnen.

Fragen: Ist der Plan jetzt ausführbar? Schluss: TRAGFÄHIG, TRAGFÄHIG MIT ÄNDERUNGEN oder NICHT TRAGFÄHIG.
