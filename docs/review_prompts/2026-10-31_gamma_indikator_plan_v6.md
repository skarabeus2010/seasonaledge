# Planprüfung v6 — Kalibrierungsvertrag (Nachtrag zu v4/v5)

Grundlage: [v5](2026-10-31_gamma_indikator_plan_v5.md), Ihre Antwort [..._v5_antwort.md](2026-10-31_gamma_indikator_plan_v5_antwort.md)
(TRAGFÄHIG MIT ÄNDERUNGEN, vier Punkte zur Kalibrierung; Kontokurve und Strategieliste abgenommen). v4/v5 gelten,
Punkt 1 aus v5 wird durch Folgendes ersetzt:

**Generator (reproduzierbar).** 252 Sitzungen/Jahr, Tagesvarianz `v = 0,16²/252`. Innovationen
`z_i,t = √0,9·f_t + √0,1·e_i,t`, `f_t, e_i,t ~ N(0,1)` unabhängig über Zeit und Reihen.
- N1: `r_i,t = √v · z_i,t` mit `f_t ≡ 0` (also `z_i,t = e_i,t`, unabhängige Reihen), Mittel 0.
- N2: gemeinsame GARCH(1,1)-Varianz `σ²_t = ω + 0,08·(σ_{t−1} z̄_{t−1})² + 0,90·σ²_{t−1}`, `z̄ = f`,
  `ω = (1−0,08−0,90)·v`, Start `σ²_0 = v`; `r_i,t = σ_t · z_i,t`, Mittel 0.
- N3: wie N2 plus gemeinsamer Jahres-Logmittelwert `μ_y = m_y/252`, `m_y` je Jahr unabhängig gleichverteilt auf
  `[−0,10, +0,10]` (Log-Jahresdrift), für alle drei Reihen gleich. **Nullzentrierung:** die Zielrendite jeder
  Beobachtung wird um die Summe der bekannten `μ` ihrer Zielperiode bereinigt (auch über den Jahreswechsel), damit
  ΔU = ΔS = 0 bedingt auf den gezogenen Jahresverlauf. Handfall im Wächter: Zielperiode über einen Jahreswechsel mit
  `m_y = +0,10`, `m_{y+1} = −0,10` → bereinigter Erwartungswert 0.
- Signalmasken, Umfeld, Saison und Gewichte = die echten der jeweiligen Regel und des Zeitraums; Renditen nur
  simuliert. Seeds je Szenario 1…2000.

**Prüfgrößen.** Je Hypothese Verwerfungsrate vor Holm (α = 0,05) und FWER nach Holm über 16; nicht auswertbare Läufe
getrennt. Akzeptanz: obere einseitige 95-%-Clopper-Pearson-Grenze ≤ 7 % je Hypothese und Nullszenario, FWER-Grenze
≤ 7 %. Eine vollständig nicht auswertbare Familie gilt als **nicht bestanden**.

**Alternativfall A1** (auf N2): ausschließlich die berechneten gerichteten Zielrenditen der Signalbeobachtungen mit
unterstützender Saison um +0,002 erhöht, Kontrollen unverändert — ein synthetischer Test des Kontrast- und
Bootstrapverfahrens, kein handelbarer Kurspfad. Verlangt: Erkennungsrate vor Holm ≥ 50 % **für jede auswertbare
H_S einzeln**; für H_U keine Erkennungsrate (wahrer Effekt 0), dort gilt weiter die Nullgrenze.

**Bootstrapzahl.** Hauptkalibrierung B = 2 000 je Datensatz. Zusätzlich die ersten 200 Datensätze je Szenario mit
B = 100 000; berichtet werden Verwerfungsraten und Holm-Entscheidungen beider Auflösungen und die Zahl abweichender
Entscheidungen (erste Holm-Schwelle 0,003125, Auflösung bei B = 2 000 grob). Weichen mehr als 2 % der Holm-
Entscheidungen ab, gilt die B = 100 000-Teilmenge als maßgeblich für die Akzeptanz.

Fragen: Ist der Kalibrierungsvertrag jetzt eindeutig? Schluss: TRAGFÄHIG, TRAGFÄHIG MIT ÄNDERUNGEN oder NICHT TRAGFÄHIG.
