# Codex-Code-Review: Williams-Kursmuster, Runde 2 (2026-10-17)

Nur lesen. Runde 1: [Prompt](2026-10-17_williams_muster_code_r1.md), [Antwort: 8 Befunde](2026-10-17_williams_muster_code_r1_antwort.md).
`scripts/research/williams_muster.py` wurde umgebaut; Wächter `scripts/verify_williams_muster.py` grün, Mutationstest
`scripts/verify_williams_muster_mutation.py` 22/22.

## Behandlung der Befunde
| R1 | Änderung |
|---|---|
| 1 Speicher | Einträge als numpy-Arrays (`zelle` int32, `datum` int32, `y`, `ev`), Ereignisse ⊂ Kontrolle (ein Array je Hypothese), Zellnummern über `Zellen`; Hälften und explorative Teile nacheinander, Hauptdaten nach Gebrauch gelöscht |
| 2 N-Familie | `netto_familie()`: N ohne (b) → p = None vor Holm, Familie bleibt viergliedrig; Wächterfall „N4 mit winzigem p verschiebt N2 nicht“ |
| 3 Achse | `achse_fuer(sitzungen, boersen, abschnitt)` = Vereinigung der Sitzungen aller beteiligten Börsen im Abschnitt; Nullspalten bleiben; Wächter mit zwei leeren Sitzungen |
| 4 Feinziehung Prüfzeitraum | `pruefzeitraum()` prüft `nahe_schwelle` für H (einseitig, Holm) und N; dann 100 000 |
| 5 Phasentrennung | `export_lesen(bis=ENTDECKUNG_BIS)` kürzt die Zeilen VOR der Aufbereitung; Diagnostik nur im Abschnitt; Wächter mit ungültiger Zeile im Februar 2024 |
| 6 Quintil inkl. t | `insort` vor der Rangbildung, Mindestzahl weiter auf Vorwerte ohne t; Wächter gegen unabhängige Referenz an allen Tagen |
| 7 Berichte | Auslösequote Ereignis/Kontrolle (H2/H4), Anteil positiv Ereignis/Kontrolle, Ticker-Einzelwerte ab n = 30, Netto-N mit Intervall in der Entdeckung (beschreibend), `diagnostik()` = Zeilen je Grund + verworfene Musterkandidaten je Grund |
| 8 Einfrieren | `open(..., "x")`; Wächter: zweiter Aufruf scheitert, Inhalt unverändert |

Zusätzlich: Ausfallregel jetzt auch im Prüfzeitraum; Grund-Vorrang Kopie vor Volumen in der Diagnostik.
Probelauf auf synthetischem Export (3 Ticker 1998–2026) über alle Phasen ohne Absturz; Zufallsreihen (25 Ticker,
3 Startwerte) ohne systematische Überrendite bei H2/H4 (±4 Bp, Schwelle 10 Bp).

## Prüffragen
1. Sind alle acht Befunde vollständig behoben? Neue Abweichungen vom Plan?
2. Ist `T*` nach dem Umbau weiter korrekt (`_matrizen`: Zellen < 20 entfernt und kompakt nummeriert)?
3. Hält der Speicher jetzt (300 Ticker × ~7 000 Zeilen, ≈ 2 GB frei)? Grobe Abschätzung genügt.
4. Laufzeit: 20 000 bzw. 100 000 Replikate über D ≈ 6 000 Tage und 10 + 4 Matrizen — vertretbar?

Befunde mit Datei:Zeile und Schwere, am Ende **FREIGABE** oder **KEINE FREIGABE**.
