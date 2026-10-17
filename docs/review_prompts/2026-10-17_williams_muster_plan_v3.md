# Prüfplan v3: Williams-Kursmuster — Änderungen gegenüber v2 (2026-10-17)

Basis: [v2](2026-10-17_williams_muster_plan_v2.md) gilt vollständig, außer den folgenden Abschnitten, die v2 **ersetzen**.
Codex zu v2: [KEINE FREIGABE, 4 Befunde](2026-10-17_williams_muster_plan_v2_antwort.md).

## §7 Statistik — ersetzt
- **Zellen:** gerichtete Hypothesen H1–H8: Zelle = Ticker × Abschnitt. INSIDE/BODY (H9, H10): Zelle = Ticker × Abschnitt
  × Vola-Quintil (Quintil wie v2 §4).
- **Überrendite je Ereignis e in Zelle z:** `x_e = y_e − m_z`, wobei `y_e` die Zielgröße des Ereignisses
  (R_bek, R_ein oder |R_bek|) und `m_z` das ungewichtete Mittel derselben Zielgröße über die gültigen Kontrolltage der
  Zelle z ist. **Statistik T = Mittel der x_e über alle Ereignisse** (ereignisgewichtet; jede Zelle geht damit mit
  ihrer Ereigniszahl ein, die Kontrolle wird je Zelle passend abgezogen — kein separat gepooltes Kontrollmittel).
- **Leere/dünne Zellen:** Zellen mit < 20 Kontrolltagen im Original werden samt ihren Ereignissen ausgeschlossen
  (Zahl berichtet). Im Bootstrap-Replikat wird `m_z` aus den gezogenen Kontrolltagen der Zelle neu geschätzt; hat die
  Zelle im Replikat 0 Kontrolltage, fallen ihre Ereignisse aus diesem Replikat. Anteil solcher Ausfälle wird berichtet;
  liegt er über 1 % der Ereignisse im Mittel, wird die Hypothese als „nicht beurteilbar“ markiert.
- **Bootstrap:** stationär (Politis–Romano) auf der gemeinsamen Handelstagachse, mittlere Blocklänge 20 (Sensitivität
  10/40), B = 20 000 (100 000 nahe der Schwelle, wie v2). Ereignisse und Kontrolltage werden mit ihren am Original
  berechneten Werten gezogen.
- **p zweiseitig (Entdeckung):** `p = (1 + #{|T* − T| ≥ |T|}) / (1 + B)`.
- **Richtung einfrieren:** `d = sign(T_Entdeckung)`, festgeschrieben vor Öffnung des Prüfzeitraums.
- **p einseitig (Prüfzeitraum, in Richtung d):** `p = (1 + #{d·(T*_P − T_P) ≥ d·T_P}) / (1 + B)`, B wie oben auf den
  Daten des Prüfzeitraums.
- **Konfidenzintervalle:** 95-%-Perzentilintervall der T* (2,5 % / 97,5 %), je Abschnitt.
- **Relevanz (vorab):** im **Entdeckungsabschnitt** gerichtet `|T| ≥ 0,10 %` (5 Sitzungen, Log-Einheiten 0,0010);
  INSIDE/BODY `|T| / K ≥ 5 %`, mit `K` = ereignisgewichtetes Mittel der zugeordneten `m_z` — **beide Richtungen**
  (Zunahme und Abnahme von |R|) zählen. Im Prüfzeitraum keine Größenschwelle, nur Vorzeichen d und einseitiges p.
- Mindestabdeckung wie v2.

## §8 Entscheidungen — ersetzt
- **(a) Abweichung repliziert:** Holm-p (zweiseitig, über H1–H10) < 0,05 in der Entdeckung **und** gleiches Vorzeichen
  in beiden Hälften **und** Relevanz erfüllt **und** im Prüfzeitraum einseitiges p < 0,05 in Richtung d (Holm über alle
  in den Prüfzeitraum weitergereichten Hypothesen).
- **(b) Quellenrichtung unterstützt (H1–H8):** (a) erfüllt und d = +1 in der jeweiligen Sicht (Kauf: Long-Überrendite
  > 0; Verkauf: Short-Überrendite > 0).
- **(c) Einstieg wirtschaftlich positiv (H2, H4, H6, H8):** (b) für diese Hypothese erfüllt **und** die **absolute**
  mittlere Einstiegsrendite nach Kosten (`Mittel(R_ein) − 0,0010`, Short-Sicht für Verkauf, ohne Kontrollabzug) hat im
  Prüfzeitraum eine untere 95-%-Grenze > 0 (Perzentilintervall, gleicher Bootstrap). In der Entdeckung wird dieselbe
  Größe berichtet, entscheidet aber nicht.
- „Nicht bestätigt“ ≠ „wirkungslos“; Intervall immer genannt.

## Befunde v2 → v3
| Befund | Behandlung |
|---|---|
| 1 (c) prüft Überrendite statt absolute Rendite | §8 (c) absolute R_ein nach Kosten, untere Grenze > 0 im Prüfzeitraum |
| 2 Vola-Kontrolle nicht eindeutig | §7 Zellen, x_e = y_e − m_z, ereignisgewichtet, leere Zellen im Original und im Replikat geregelt |
| 3 einseitiges p / Intervalle | §7 Formeln, Richtung d vor Öffnung eingefroren, Perzentilintervall |
| 4 Relevanzschwelle | §7 nur im Entdeckungsabschnitt, Betrag, INSIDE/BODY beidseitig über K |
