# Planprüfung v5 — Gamma-Regime × Indikatoren × Saisonalität (Nachtrag zu v4)

Grundlage: [v4](2026-10-31_gamma_indikator_plan_v4.md), Ihre Antwort [..._v4_antwort.md](2026-10-31_gamma_indikator_plan_v4_antwort.md)
(TRAGFÄHIG MIT ÄNDERUNGEN, drei Punkte). v4 gilt unverändert, ergänzt um:

**1. Kalibrierungsvertrag des Bootstraps.**
- Nullszenarien (je 2 000 unabhängige Datensätze, Seeds 1…2000 je Szenario, Länge und Kalender wie SPY/QQQ/DIA im
  jeweiligen Zeitraum):
  N1 i.i.d.-Normal; N2 gemeinsamer Marktfaktor (Korrelation 0,9 zwischen den drei Reihen) + GARCH(1,1)
  (ω so, dass die Jahresvola 16 %, α = 0,08, β = 0,90); N3 wie N2 mit Jahresniveau-Sprüngen des Mittelwerts
  (±10 % p. a., zufällig je Jahr) und dem **echten** Umfeld-Kalender (VIX/VIX3M), damit die Zellbesetzung so ungleich
  ist wie in den Daten.
  Die Nullhypothese wird **hergestellt, nicht angenommen:** Signale werden in den Simulationen nicht aus den
  simulierten Kursen gebildet, sondern unabhängig von den Zielrenditen gezogen (Signaldaten = die echten Signaldaten
  der jeweiligen Regel, Umfeld/Saison = echter Kalender, Renditen = simuliert und unabhängig von beiden). Damit sind
  ΔU = ΔS = 0 per Konstruktion; die Abhängigkeit zwischen Signal und Umfeld bleibt wie in den Daten.
- Berichtet: Verwerfungsrate je Hypothese vor Holm (α = 0,05) und FWER nach Holm über 16; nicht auswertbare Läufe
  getrennt gezählt.
- Akzeptanz: obere einseitige 95-%-Clopper-Pearson-Grenze der Verwerfungsrate ≤ 7 % je Hypothese und Szenario, FWER
  nach Holm (obere Grenze) ≤ 7 %.
- Alternativfall A1: in N2 ein eingebauter Kontrast ΔS = +20 Bp auf 5 HT in allen Kernreihen (gerichtete Rendite der
  Signale mit unterstützender Saison um 20 Bp erhöht); Erkennungsrate vor Holm ≥ 50 % verlangt, sonst ist das
  Verfahren zu schwach (ein Verfahren mit p ≡ 1 besteht nicht).
- Wegen der Rechenzeit (2 000 × 100 000 Ziehungen) wird die Kalibrierung mit B = 2 000 Ziehungen je Datensatz
  gerechnet; die p-Werte-Auflösung reicht für α = 0,05. Das ist eine vorab festgelegte Abweichung nur für die
  Kalibrierung.

**2. Kontokurve bei Lücken.** Kapital(t) = Kapital vor Einstieg − bisherige Kosten + Richtung·Stück·(Kurs(t) −
Einstiegskurs), auf derselben rekonstruierten Kursbasis. Handfall ohne Kosten: 100 / Einstieg 100 / Bewertung 110 →
Long 110, Short 90. Kosten in Bp auf den Nominalwert je Seite (Einstieg und Ausstieg). Fehlt während einer offenen
Position ein gültiger Bewertungskurs: Kapital an diesen Tagen unbekannt, Drawdown/MAE der Position als nicht
vollständig bestimmbar markiert, keine Interpolation; Position bleibt bis zum ersten gültigen Schluss offen und
blockiert neue Einstiege. Liegt dieser Schluss außerhalb des Auswertungszeitraums → Trade zensiert, keine späteren
Daten. Fällt das Reihenkapital auf ≤ 0 (Short), endet die Reihe („ruiniert“), keine Neueinstiege; ausgewiesen.

**3. Feste Strategieliste (beschreibend, vor Öffnung des Prüfzeitraums eingefroren).** Je gerichteter Regel fünf
Varianten: ungefiltert; angespannt∩Saison unterstützt; angespannt∩Saison gegen; ruhig∩Saison unterstützt;
ruhig∩Saison gegen → 8 × 5 = 40 Kontokurven je Zeitraum, jede mit eigener Positionsführung, Kosten 2 Bp (Belastung
10 Bp) je Seite, Haltedauer 5 HT primär. Keine nachträgliche Auswahl der besten Kombination als Ergebnis; die
Kurven sind Beschreibung, der Nachweis bleibt bei ΔU/ΔS. Ein bestätigter Zusatznutzen wird nicht als positive
Nettorendite ausgegeben.

Fragen: Trägt die Herstellung der Nullhypothese (echte Signaldaten, simulierte unabhängige Renditen)? Ist der Plan
jetzt ausführbar? Schluss: TRAGFÄHIG, TRAGFÄHIG MIT ÄNDERUNGEN oder NICHT TRAGFÄHIG.
