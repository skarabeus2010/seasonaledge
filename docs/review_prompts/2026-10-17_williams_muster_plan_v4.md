# Prüfplan v4: Williams-Kursmuster — Änderung gegenüber v3 (2026-10-17)

Basis: [v2](2026-10-17_williams_muster_plan_v2.md) mit den Ersetzungen aus [v3](2026-10-17_williams_muster_plan_v3.md).
Codex zu v3: [ein Befund (Mittel)](2026-10-17_williams_muster_plan_v3_antwort.md) — Mehrfachtests für (c) fehlten.

## §8 (c) — ersetzt
- **Eigene Testfamilie (vorab):** die vier Nettorendite-Hypothesen N2, N4, N6, N8 zu H2, H4, H6, H8:
  `N = Mittel(R_ein) − 0,0010` (Short-Sicht für Verkauf, ohne Kontrollabzug), **nur Prüfzeitraum**.
- **Test:** einseitig `H0: N ≤ 0`, `p = (1 + #{(N* − N) ≥ N}) / (1 + B)`, gleicher stationärer Bootstrap und B wie §7.
- **Korrektur:** Holm über **alle vier** Nettorendite-Hypothesen, unabhängig davon, wie viele (b) erfüllen. Eine
  Hypothese, deren zugehöriges H (b) nicht erfüllt, kann (c) nicht erreichen, bleibt aber in der Familie (zählt als
  nicht verworfen).
- **(c) erfüllt:** (b) für das zugehörige H **und** Holm-p(N) < 0,05.
- Das 95-%-Perzentilintervall von N wird zusätzlich deskriptiv berichtet (Entdeckung und Prüfzeitraum).

Alles andere unverändert.
