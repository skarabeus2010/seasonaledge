# Codex-Code-Review: Williams-Kursmuster, Runde 1 (2026-10-17)

Nur lesen. Prüfe `scripts/research/williams_muster.py` gegen den freigegebenen Plan
([v2](2026-10-17_williams_muster_plan_v2.md) + Ersetzungen [v3](2026-10-17_williams_muster_plan_v3.md) §7/§8 +
[v4](2026-10-17_williams_muster_plan_v4.md) §8c). Wächter `scripts/verify_williams_muster.py` (handgebaute Kerzen,
unabhängige Sollwerte), Mutationstest `scripts/verify_williams_muster_mutation.py` 18/18. Noch nichts auf echten Daten
gerechnet.

## Prüffragen
1. Weicht der Code an irgendeiner Stelle vom Plan ab (Gültigkeit, Basisregel, Lückenregel, Fenster t−1…t+10,
   Muster, Stopp-/Open-Einstieg, Short-Sicht, Abschnitte mit t+10, Zellen inkl. Quintil, x_e = y_e − m_z,
   Mindestkontrolle, stationärer Bootstrap mit gemeinsamer Neuschätzung, p-Formeln, Holm, Relevanz, Abdeckung,
   Ausfall > 1 %, (a)/(b)/(c), N-Familie)?
2. Bootstrap: Stimmt die Matrixrechnung `T* = Σ_z [(EY_z·w) − m*_z (E_z·w)] / Σ_z (E_z·w)` mit `m*_z = (S_z·w)/(N_z·w)`
   über gültige Zellen? Ist die gemeinsame Datumsachse (Vereinigung der Ereignis-/Kontrolltage) richtig, oder muss
   sie die Vereinigung der Sitzungen aller Börsen sein (Tage ohne Einträge verändern die Blockstruktur)?
3. Ist die Prüfzeitraum-Sperre wirksam (Skript-Hash, Export-Hash, Einfrier-Datei nicht überschreibbar) — und rechnet
   `entdeckung()` wirklich nichts aus dem Prüfzeitraum (auch nicht in den explorativen Teilen)?
4. Vola-Quintil: Vorgeschichte nur bis t, inklusive t selbst? (Plan: „gegen die eigene Vorgeschichte bis t“.)
5. Speicher/Laufzeit auf dem Server (≈ 2 GB frei, ~300 Ticker × ~7 000 Zeilen): ein Problem?
6. Fehlt im Wächter ein Fall, der eine Planabweichung fangen müsste?

Befunde mit Datei:Zeile und Schwere, am Ende **FREIGABE** oder **KEINE FREIGABE**.
