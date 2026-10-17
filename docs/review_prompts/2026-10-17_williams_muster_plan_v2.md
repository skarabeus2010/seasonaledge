# Prüfplan v2: Williams-Kursmuster als Ereignisstudie (2026-10-17)

v1: [Plan](2026-10-17_williams_muster_plan_v1.md), [Codex: KEINE FREIGABE, 8 Befunde](2026-10-17_williams_muster_plan_v1_antwort.md).
Am Ende eine Tabelle, wo jeder Befund behandelt ist. Nichts wird nach dem ersten Blick auf Ergebnisse geändert.

## 1. Frage
Haben Smash Day, Outside Day, Inside Day und ein kleiner Kerzenkörper (Blast-Off-Regel) auf unseren Aktien und ETFs
eine messbare, stabile Folgewirkung gegenüber einer passenden Kontrolle desselben Tickers? Getrennt beantwortet:
**(a)** gibt es eine Abweichung, **(b)** stützt sie die Richtung laut Quelle, **(c)** ist der modellierte Einstieg
nach Kosten positiv.

## 2. Muster (Tag t = Mustertag)
| Kürzel | Regel an t | Richtung laut Quelle | Einstieg (modelliert, Näherung ohne Tick-Abstand) |
|---|---|---|---|
| SMASH_K | `C_t < L_{t−1}` | Kauf | Buy-Stopp `H_t` an t+1, ausgelöst wenn `H_{t+1} > H_t`, Kurs `max(O_{t+1}, H_t)` |
| SMASH_V | `C_t > H_{t−1}` | Verkauf | Sell-Stopp `L_t` an t+1, ausgelöst wenn `L_{t+1} < L_t`, Kurs `min(O_{t+1}, L_t)` |
| OUT_K | `H_t > H_{t−1}`, `L_t < L_{t−1}`, `C_t < L_{t−1}` | Kauf | Open t+1 |
| OUT_V | dto., `C_t > H_{t−1}` | Verkauf (Spiegel, nicht von Williams belegt) | Open t+1 |
| INSIDE | `H_t < H_{t−1}`, `L_t > L_{t−1}` | keine | — |
| BODY | `round(|O_t − C_t| / (H_t − L_t) × 100, 1) < 20` (= Produktionsregel `newsletter_indicators.py:103`) | keine | — |

BODY heißt „kleiner Kerzenkörper“, nicht „Kompression“. **Der Mail-Score-Bonus (BODY + LBR-Richtung) ist nicht Teil
dieser Studie**; er bekommt einen eigenen Plan. OUT ⊂ SMASH: getrennt ausgewiesen, keine unabhängige Bestätigung.

## 3. Daten, Gültigkeit, Kursbasis
- **Universum:** `get_all_tickers()` ohne `-USD`, `=X`, `=F`, `^`; eingefroren als Liste mit SHA-256 vor dem Lauf.
  Survivorship (heutige Ticker) bleibt Einschränkung: der Prüfzeitraum ist ein zeitlich zurückgehaltener Test **im
  heutigen Universum**.
- **Gültige Zeile:** alle Preise endlich und > 0, `H > L`, `L ≤ min(O, C)`, `H ≥ max(O, C)`, `log_return` endlich,
  Datum = Handelstag der Börse; kein Fortschreibungsverdacht (`C = C_{vorher}` mit Volumen 0 oder `H = L`).
  Volumen > 0 gilt als Pflicht; Sensitivität ohne diese Bedingung wird ausgewiesen.
- **Gemeinsame Kursbasis (Befund 1):** für jedes benachbarte Zeilenpaar, das ein Ereignis berührt (t−1→t, t→t+1, … bis
  t+h), muss `|ln(C_t / C_{t−1}) − log_return_t| ≤ 1e-4 + 1e-4 / C_t` gelten (Toleranz deckt die Rundung auf vier
  Nachkommastellen ab). Bricht ein Paar diese Bedingung, liegt ein Basiswechsel vor → **Ereignis verworfen**, nicht
  korrigiert. Gleiche Regel für Kontrolltage. Anzahl verworfener Ereignisse je Grund wird berichtet.
- **Lückenlos:** t−1 … t+h aufeinanderfolgende Sitzungen laut Börsenkalender (`shared/sitzungen.py`); sonst
  verworfen. Halbtage zählen als Sitzung.
- **Renditen:** `R_bek(h) = Σ log_return_{t+1..t+h}`. Einstieg zum Kurs P an t+1: `ln(C_{t+1}/P) + Σ log_return_{t+2..t+h}`.
  Nie `O_{t+1}/C_t`. Verkauf-Muster: Vorzeichen umgedreht (Short-Sicht) — **für Ereignis und Kontrolle gleich**.
- **Kosten:** 5 Bp je Seite = 0,0010 Log-Einheiten je Hin- und Rückweg, nur bei `R_ein`.

## 4. Kontrollen (Befund 2)
- **R_bek:** alle gültigen Tage desselben Tickers und Abschnitts, gleiche Lückenlos- und Basisregel.
- **R_ein OUT:** dieselbe Rechnung „Open t+1 → Close t+h“ auf allen gültigen Tagen des Tickers.
- **R_ein SMASH:** Kontrolle mit **derselben Stopp-Mechanik** auf allen gültigen Tagen d: Stopp `H_d` (Kauf) bzw. `L_d`
  (Verkauf) an d+1, gleiche Auslöse- und Kursregel; Kontrollmenge = ausgelöste Kontrolltage. Zusätzlich je Setup
  (inkl. nicht ausgelöster Fälle, dort Rendite 0) gegen dieselbe Größe der Kontrolle. Auslösequote Ereignis vs. Kontrolle.
- **INSIDE/BODY (Befund 5 der Antwort):** Zielgröße `|R_bek(h)|`; Kontrolle = gültige Tage desselben Tickers im **selben
  Volatilitäts-Quintil** (realisierte 20-Tage-Vola bis t, Quintil gegen die eigene Vorgeschichte des Tickers bis t,
  mindestens 250 Vortage, sonst nicht verwendet). Ergänzend explorativ: Folgespanne `ln(max H_{t+1..t+h} / min L_{t+1..t+h})`
  gegen dieselbe Kontrolle, nur bei durchgehend gültiger Kursbasis.

## 5. Zeitabschnitte (Befund 6)
- Entdeckung: Ereignistag t **und** t+10 in 2000-01-03 … 2023-12-29; Hälften: t und t+10 in 2000–2011 bzw. 2012–2023.
- Prüfzeitraum: t und t+10 in 2024-01-02 … 2026-09-30. Musterhistorie davor (t−1) ist zulässig.
- Dieselbe Ereignismenge für alle Horizonte (Bedingung t+10), damit die Stichprobe je Horizont gleich bleibt.
- **Einfrieren vor Öffnung des Prüfzeitraums:** Commit des Skripts, Universumsliste, Export der verwendeten Kurszeilen
  (Server, SHA-256 im Ergebnis), Hypothesenliste dieses Plans.

## 6. Hypothesen (Befund 3) — konfirmatorisch nur h = 5, Holm über diese 10
| # | Muster | Zielgröße | Test |
|---|---|---|---|
| H1 | SMASH_K | Überrendite R_bek | zweiseitig |
| H2 | SMASH_K | Überrendite R_ein (ausgelöst) vs. Stopp-Kontrolle | zweiseitig |
| H3 | SMASH_V | Überrendite R_bek (Short-Sicht) | zweiseitig |
| H4 | SMASH_V | Überrendite R_ein vs. Stopp-Kontrolle (Short-Sicht) | zweiseitig |
| H5 | OUT_K | Überrendite R_bek | zweiseitig |
| H6 | OUT_K | Überrendite R_ein vs. Open-Kontrolle | zweiseitig |
| H7 | OUT_V | Überrendite R_bek (Short-Sicht) | zweiseitig |
| H8 | OUT_V | Überrendite R_ein vs. Open-Kontrolle (Short-Sicht) | zweiseitig |
| H9 | INSIDE | Über-|R_bek| vs. Vola-Quintil-Kontrolle | zweiseitig |
| H10 | BODY | Über-|R_bek| vs. Vola-Quintil-Kontrolle | zweiseitig |

h = 1 und h = 10, Setup-Renditen inkl. nicht ausgelöster Fälle, Folgespanne, Median, Trefferquote, Ticker-Einzelwerte:
**explorativ/deskriptiv**, nie Grundlage einer Bestätigung.

## 7. Statistik (Befund 4, 8)
- **Statistik:** ereignisgewichtete mittlere Überrendite = Mittel(Ereignis) − Mittel(Kontrolle), je Ticker und
  Abschnitt die Kontrolle gebildet, dann gepoolt. Robustheit (deskriptiv): gleichgewichtet über Ticker.
- **Unsicherheit:** **stationärer Bootstrap** (Politis–Romano) auf der gemeinsamen Achse der Handelstage aller Börsen
  (Vereinigung), mittlere Blocklänge **20** Sitzungen, Sensitivität 10 und 40. Gezogen werden Ereignis- und
  Kontrolltage samt der am Originaldatum gerechneten Fenster (kein Fenster wird über Blockgrenzen neu gebildet); in
  jedem Replikat werden Ereignis- und Kontrollmittel gemeinsam neu geschätzt.
- **p-Wert:** Anteil der Replikate mit `|T* − T| ≥ |T|` (+1 im Zähler und Nenner). **20 000** Replikate; liegt p
  zwischen der Hälfte und dem Doppelten seiner Holm-Schwelle, 100 000 Replikate, Entscheidung auf diesem Lauf.
- **Mindestabdeckung:** je Hypothese ≥ 1 000 Ereignisse aus ≥ 100 Tickern im Entdeckungsabschnitt, je Hälfte ≥ 300,
  im Prüfzeitraum ≥ 150; sonst „nicht beurteilbar“.
- **Relevante Effektgröße (vorab):** gerichtet |Überrendite| ≥ 0,10 % auf 5 Sitzungen; INSIDE/BODY ≥ 5 % relativ zum
  Kontrollmittel von |R|.

## 8. Entscheidungen (Befund 5)
Je Hypothese getrennt:
- **(a) Abweichung repliziert:** Holm-p < 0,05 (Entdeckung) **und** gleiches Vorzeichen in beiden Hälften **und**
  Prüfzeitraum gleiches Vorzeichen mit einseitigem p < 0,05 (Holm über die so weitergereichten) **und** relevante Größe.
- **(b) Quellenrichtung unterstützt:** (a) erfüllt und Vorzeichen in Short-/Long-Sicht positiv (Kauf: Überrendite > 0;
  Verkauf: Short-Überrendite > 0). Nur H1–H8.
- **(c) Einstieg wirtschaftlich positiv:** (b) für die R_ein-Hypothese erfüllt und Überrendite nach Kosten mit
  unterer 95-%-Grenze > 0.
- „Nicht bestätigt“ wird nie als „wirkungslos“ formuliert; Intervall wird immer genannt.

## 9. Folgen
- Studienseite (Muster `/index-effekt`) zeigt alles, auch Nullbefunde.
- Richtungsfarbe in Mail/Scanner **nur** für Muster mit (b) — Entscheidung beim Nutzer. INSIDE/BODY nie farbig.
- Ohne (b): höchstens neutrale Angabe „Muster erkannt · Sitzung · Link zur Studie“, Entscheidung beim Nutzer.
- Prospektive Protokollierung ab Inbetriebnahme.

## 10. Technik
`scripts/research/williams_muster.py` (nur lesend, Server), Faktenblatt + JSON; Wächter
`scripts/verify_williams_muster.py` mit handgebauten Kerzenreihen (bekannte Muster, Basiswechsel, Lücke, Kopie,
Grenze zum Prüfzeitraum) gegen den echten Code, Mutationstest. Kein DB-Schreibzugriff.

## Befunde v1 → v2
| Befund | Behandlung |
|---|---|
| 1 Kursbasis bei Mustervergleich | §3 Basisregel je Zeilenpaar, Verwerfen statt Korrigieren |
| 2 Kontrolle für R_ein | §4 Open-Kontrolle, Stopp-Kontrolle mit gleicher Mechanik, Setup inkl. nicht ausgelöster |
| 3 30 statt 28 Tests | §6 konfirmatorisch nur h=5, 10 Hypothesen einzeln, Rest explorativ |
| 4 Bootstrap | §7 stationärer Bootstrap, Blocklänge 20 (10/40), gemeinsame Neuschätzung, 20 000/100 000 |
| 5 Abweichung vs. Richtung | §8 (a)/(b)/(c) getrennt |
| 6 Fenster an Abschnittsgrenzen | §5 t und t+10 im Abschnitt, Einfrieren vor Prüfzeitraum |
| 7 BLAST | §2 Produktionsregel mit Rundung, „kleiner Körper“, Score-Bonus ausgeklammert; §4 Vola-Kontrolle |
| 8 Abdeckung/Gewichtung/Effekt | §3 Gültigkeit, §7 Mindestabdeckung, Effektgröße, Gewichtung; §8 Formulierung |
