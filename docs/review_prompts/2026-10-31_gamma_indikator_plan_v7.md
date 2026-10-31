# Planprüfung v7 — Kalibrierungsvertrag, letzte Korrekturen (Nachtrag zu v6)

Grundlage: [v6](2026-10-31_gamma_indikator_plan_v6.md), Ihre Antwort [..._v6_antwort.md](2026-10-31_gamma_indikator_plan_v6_antwort.md).
Alle drei Punkte wörtlich übernommen, eine Zahl angepasst:

1. **Feste Abnahmeregel.** Die ersten **1 000** (statt 200) Datensätze je Nullszenario und Zeitraum werden zusätzlich
   mit B = 100 000 ausgewertet — bei 200 läge schon die erwartete Rate 5 % (10/200) mit der oberen Grenze 8,33 % über
   7 %; bei 50/1000 sind es 6,29 % (nachgerechnet, Clopper-Pearson einseitig 95 %). Beide Bootstrapzahlen müssen ihre
   jeweiligen Akzeptanzgrenzen erfüllen. Verglichen werden je Hypothese Entscheidungen vor und nach Holm sowie je
   Datensatz das Auftreten mindestens einer falschen Holm-Verwerfung. Abweichungen werden berichtet; sie bestimmen
   nicht nachträglich das maßgebliche Abnahmekriterium. Die 2-%-Regel entfällt.
2. **N1:** unabhängig von der Faktorformel direkt `z_i,t = e_i,t` und `r_i,t = √v · e_i,t`. Die Faktorformel gilt nur
   für N2/N3.
3. **Auswertbarkeit und Nenner.** Die Besetzungsinventur legt je Zeitraum vorab fest, welche Hypothesen kalibriert
   werden müssen. Für A1 ist die Erkennungsrate jeder dieser H_S = Verwerfungen / alle 2 000 Datensätze; nicht
   auswertbare Läufe zählen als Nichterkennung. Gibt es keine kalibrierbare H_S, ist die Leistung des Saisonverfahrens
   nicht nachgewiesen. Für Nullverwerfungsraten und FWER sind ebenfalls alle geplanten Datensätze der Nenner; Ausfälle
   und bedingte Raten unter auswertbaren Läufen werden zusätzlich berichtet.

Frage: Freigabe des Plans (v4 + v5 + v6 + v7) für den Bau des Studienkerns? Schluss: FREIGABE, TRAGFÄHIG MIT
ÄNDERUNGEN oder NICHT TRAGFÄHIG.
