# Prüfplan v1: Williams-Kursmuster als Ereignisstudie (2026-10-17)

Vorgeschichte: [Idee + Codex-Einschätzung](2026-10-17_williams_muster_idee.md) — Untersuchung ja, grün/rote
Mail-Erweiterung vorerst nein. Nutzerentscheidung 2026-10-17: Prüfplan schreiben und von Codex freigeben lassen,
**bevor** gerechnet wird. Nichts an diesem Plan wird nach dem ersten Blick auf Ergebnisse geändert; Änderungen danach
werden als solche benannt und neu geprüft.

## 1. Frage
Haben die Tagesmuster Smash Day, Outside Day und Inside Day sowie Blast-Off auf unseren Aktien und ETFs eine
messbare, stabile Folgewirkung gegenüber der Basisrate desselben Tickers?

## 2. Muster (feste Definitionen, Tag t = Mustertag, alle Werte aus `prices`)
| Kürzel | Regel an t | Richtung laut Quelle | Bekannt | Einstieg (modelliert) |
|---|---|---|---|---|
| SMASH_K | `C_t < L_{t−1}` | Kauf-Setup | Schluss t | Buy-Stopp `H_t` an t+1: ausgelöst wenn `H_{t+1} > H_t`; Kurs `max(O_{t+1}, H_t)` |
| SMASH_V | `C_t > H_{t−1}` | Verkauf-Setup | Schluss t | Sell-Stopp `L_t` an t+1: ausgelöst wenn `L_{t+1} < L_t`; Kurs `min(O_{t+1}, L_t)` |
| OUT_K | `H_t > H_{t−1}`, `L_t < L_{t−1}`, `C_t < L_{t−1}` | Kauf | Schluss t | Open t+1 |
| OUT_V | `H_t > H_{t−1}`, `L_t < L_{t−1}`, `C_t > H_{t−1}` | Verkauf (Spiegel, nicht von Williams belegt) | Schluss t | Open t+1 |
| INSIDE | `H_t < H_{t−1}`, `L_t > L_{t−1}` | keine | Schluss t | — |
| BLAST | `|O_t − C_t| / (H_t − L_t) < 0,20` (wie `shared/newsletter_indicators.py`) | keine (Kompression) | Schluss t | — |

OUT_K/OUT_V sind Teilmengen von SMASH_K/SMASH_V — sie werden getrennt ausgewiesen, aber nicht als unabhängige
Bestätigung gezählt. Hidden Smash, Specialist Trap, Oops!, Marktstruktur: nicht Teil dieser Studie.

## 3. Daten und Ausschlüsse
- **Universum:** `symbols.get_all_tickers()` ohne Krypto (`-USD`), Devisen (`=X`), Futures (`=F`), Indizes (`^`).
  Nur Aktien und ETFs. Universum fest zum Stand 2026-10-17 → **Survivorship** (heutige Ticker) wird benannt, nicht
  korrigiert.
- **Zeitraum:** Entdeckung 2000-01-01 … 2023-12-31, Hälften 2000–2011 / 2012–2023. **Unangetasteter Prüfzeitraum**
  2024-01-01 … 2026-09-30 — wird erst nach Freigabe der Entdeckungsergebnisse ausgewertet, mit unveränderter Rechnung.
- **Gültige Zeile:** `H > L`, `L ≤ min(O, C)`, `H ≥ max(O, C)`, Volumen > 0, kein Fortschreibungsverdacht
  (`H = L` oder `C = C_{t−1}` mit Volumen 0), Datum ist Handelstag der Börse (`shared/exchange_holidays`).
- **Gültiges Ereignis:** Zeilen t−1, t, t+1 … t+h gültig **und** lückenlos (keine fehlende Sitzung laut
  Börsenkalender dazwischen). Sonst wird das Ereignis verworfen, nicht verschoben. Gleiche Regel für die Basisrate.
- **Kursbasis:** Renditen nur aus `log_return` (Close→Close) und `ln(C/O)` derselben Zeile — nie `O_{t+1}/C_t`
  (unterschiedliche Bereinigungsstände). Einstieg am Open t+1: `ln(C_{t+1}/O_{t+1}) + Σ log_return_{t+2..t+h}`;
  Stopp-Einstieg analog mit `ln(C_{t+1}/Kurs)`.

## 4. Messgrößen
- **Horizonte:** h = 1, 5, 10 Sitzungen; **Hauptauswertung h = 5**.
- **R_bek:** Rendite ab Bekanntwerden (Close t → Close t+h).
- **R_ein:** Rendite ab modelliertem Einstieg bis Close t+h (nur SMASH/OUT; bei SMASH nur ausgelöste Fälle,
  Auslösequote wird berichtet). Verkauf-Setups mit umgekehrtem Vorzeichen (Short-Sicht), separat ausgewiesen.
- **INSIDE/BLAST (richtungslos):** Hauptgröße `|R_bek|` gegen die Basisrate von `|R|` (Ausdehnung nach
  Kompression); signierte Rendite nur beschreibend.
- **Basisrate:** alle gültigen Tage desselben Tickers im selben Zeitraum, gleiche Horizonte und Gültigkeitsregel.
- **Überrendite je Ereignis:** Ereignisrendite − Basismittel des Tickers (im jeweiligen Zeitabschnitt).
- **Kosten:** 2 × 5 Basispunkte je Ein-/Ausstieg als Abzug in einer zweiten Zeile (keine Hauptgröße).

## 5. Statistik
- Gepoolt über Ticker: mittlere Überrendite, Median, Anteil positiv gegen Anteil positiv der Basis.
- **Unsicherheit:** Block-Bootstrap über **Kalendermonate** (zieht ganze Monate mit allen Tickern → erfasst
  Gleichzeitigkeit über Ticker und Überlappung der Fenster), 2000 Wiederholungen, 95-%-Intervall und zweiseitiges p.
- **Testfamilie (vorab, vollständig):** 6 Muster × 3 Horizonte × {R_bek; R_ein wo definiert} = **28 Tests**.
  Holm-Korrektur über alle 28.
- **Bestätigt** heißt: Holm-p < 0,05 in der Entdeckung **und** gleiches Vorzeichen in beiden Hälften **und** im
  Prüfzeitraum gleiches Vorzeichen mit einseitigem p < 0,05 (ein Test je bestätigtem Kandidaten, Holm über diese)
  **und** Überrendite nach Kosten > 0 (bei R_ein).
- **Je Ticker:** nur beschreibend (n, Mittel, Intervall), nie als Signal; Ticker mit n < 30 ohne Zahl.

## 6. Abbruch und Folgen
- Kein Muster bestätigt → Ergebnis als Nullbefund auf einer Studienseite (Muster `/index-effekt`); **keine**
  Richtungsfarbe, kein Musterpunkt im Score. Ob die Mail neutral „Muster erkannt“ zeigt, entscheidet der Nutzer.
- Muster bestätigt → Studienseite + neutrale Anzeige mit Messwerten; Richtungsfarbe nur für bestätigte Muster,
  Entscheidung beim Nutzer.
- **Blast-Off** ist bereits mit ±1 im Mail-Score (`newsletter_indicators.py:130`). Fällt BLAST ohne Wirkung aus,
  wird vorgeschlagen, den Bonus zu entfernen.
- Prospektive Protokollierung ab Inbetriebnahme (Muster je Sitzung festschreiben, später nachmessen).

## 7. Technik
- Rechnung in `scripts/research/williams_muster.py` (nur lesend aus Supabase, Ausgabe JSON + Faktenblatt), läuft
  auf dem Server. Unabhängige Referenzfälle (handgebaute Kerzenreihen mit bekanntem Ergebnis) im Wächter
  `scripts/verify_williams_muster.py`, Mutationstest. Keine DB-Schreibzugriffe.
- Die Datenreparatur der kopierten Zeilen ist **keine** Voraussetzung (Ausschlussregel in §3 greift), wird aber
  getrennt gemessen; ihr Ergebnis ändert die Studie nicht nachträglich.

## Fragen an Codex
1. Ist die Testfamilie vollständig und die Bestätigungsregel streng genug — oder zu streng (Teststärke)?
2. Ist der Monats-Block-Bootstrap die richtige Antwort auf Gleichzeitigkeit und Überlappung? Alternativen?
3. Stimmen Muster-, Einstiegs- und Renditedefinitionen (insbesondere Stopp-Kurs bei Lücke, Kursbasis)?
4. Fehlt ein Ausschluss oder eine Verzerrung (Survivorship, Splits, Ex-Tage, Halbtage, Volumen 0 bei ETFs)?
5. Ist INSIDE/BLAST über `|R|` sinnvoll, oder sollte die Folgespanne (`H−L`) gemessen werden?
6. Freigabe oder nicht?
