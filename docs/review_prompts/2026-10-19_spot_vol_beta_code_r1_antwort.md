**Keine Freigabe.** Drei Befunde:

- **P2 – konstante Renditen ergeben gültiges Beta:** [spot-vol-compute.js:125](/C:/dev/SeasonalEdge/landing/js/spot-vol-compute.js:125). Rundungsreste umgehen `sxx > 0`. Reproduziert: OLS mit `x=[0.1,0.1,0.1]` liefert β≈0,0417; Rolling mit 60 konstanten Spot-Renditen ebenfalls einen Zahlenwert. **Auflage:** Degeneration numerisch robust erkennen und Dezimalfälle testen.

- **P2 – ein VRP-Wert lässt die Darstellung abstürzen:** [spot-vol-beta.html:695](/C:/dev/SeasonalEdge/landing/pages/spot-vol-beta.html:695). Bei genau einem gültigen VRP-Wert liefert `quantil()` `null`; `zahlFmt(med)` wirft einen `TypeError`. Dadurch entfällt auch die anschließende Ereignisdarstellung. **Auflage:** unbekannte Quantile abfangen, Render-Test ergänzen.

- **P2 – Bucket-Horizonte unzureichend geprüft:** [verify_spot_vol_beta.py:415](/C:/dev/SeasonalEdge/scripts/verify_spot_vol_beta.py:415). Verglichen wird nur `f1`. Die im Speicher ausgeführte Mutation `f5: forward(i,5) → forward(i−1,5)` **entwischt: weiterhin 142/142 grün**. **Auflage:** sämtliche ausgegebenen Horizonte und Statistiken unabhängig prüfen.

Baseline: 142 Prüfungen bestanden; normale Seitenprobe ohne Seitenfehler, sieben Charts. Phantomrenditen-Summierung und Backend-Entfernung sind nachvollziehbar. Die bekannte `<`-Warnung ist ausgenommen. Keine Dateien geändert.
tokens used
131.379
