# Review-Auftrag: Wahlen — Phase 1b-1, Runde 2

Repo `C:\dev\Seasonaledge`. Fortsetzung von `2026-10-07_wahlen_1b1_runde1.md`. Prüfe den letzten Commit
(`git show HEAD`) gegen deine drei Befunde. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung,
am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Umsetzung
1. Live-Wahl chronologisch: unter den nicht gehaltenen Wahlen des Filters gewinnt das früheste Datum
   (JS und Python gleich). Test: Option „alle" → `us-midterm-2026`, nicht 2028.
2. Datenstand nach dem Wahltag: `stichtag` fällt auf `st.letzte_session`, `letzter_kurs` auf
   `st.reihen[reihe].letzter_kurs` zurück, wenn der Pfad schon historisch ist; `t0_projiziert` wird mitgegeben.
   Test `pruefe_wahltag`: Studie mit Stichtag 03.11.2026 und 04.11.2026, Status unverändert `scheduled` —
   Datenstand = Stichtag, t0 = 03.11., t0-Kurs vorhanden, JS = Python.
3. Zwillingsvertrag vollständig: `aggregiere` liefert jetzt auch `einzel` (id, t0, Kurve, Vor-/Nachlauf,
   Fenster, Basisdatum), `ausgeschlossen` (id, Grund) und `live` (alle Felder + Kurve); die Probe gibt dieselben
   Strukturen aus, `gleich()` vergleicht Zahlen, Strings und Booleans. Basisdaten werden für alle Optionen und
   beide Basen gegen eine unabhängige Rechnung aus `tage` geprüft, Live-Werte gegen Kurs/Kurs(t−X).
   Mutationen 12/12, darunter deine Gegenprobe „Live-Werte alle 100", „Live in Dateireihenfolge",
   „Datenstand nach Wahltag verloren", „Basisdatum t−X falsch", „Ausschlussgrund verloren".
