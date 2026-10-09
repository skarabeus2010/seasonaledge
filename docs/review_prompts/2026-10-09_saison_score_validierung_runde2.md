# Review VOR dem Lauf: Validierung Saison-Score — Runde 2

Repo `C:\dev\Seasonaledge`, HEAD 7e46729. Nur lesen, **`--lauf` NICHT ausführen**. Vorgeschichte: `..._validierung_runde1.md`
+ Antwort. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Fall + Änderung; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`.

## Korrekturen zu R1 (Commit 28a58a1, Protokoll 7e46729)
1. **Gültigkeit je Kennzahl getrennt:** dieselben 2000 Jahresziehungen; `bootstrap` zählt Verwerfungen je Kennzahl,
   der gepaarte Vergleich nur Ziehungen mit Score UND Vergleichsscore; Auswertbarkeit je Kennzahl (> 5 % → nicht
   auswertbar). Im Protokoll unter `gueltigkeit`.
2. **Skript festgeschrieben:** `skript_sha256` + `parameter` im Protokoll; `--lauf` verweigert bei abweichendem Skript,
   Parameter, Kern oder Daten. Protokoll und Skript sind committet (28a58a1, 7e46729); der Kern ist b7b01da unverändert.
3. **Nicht auswertbar ≠ nein:** `rangzusammenhang = null`, Konsole „nicht auswertbar"; gepaart mit eigenem Status.
4. **Positivrate:** je Reihe k/n Ziel > 0, Mittel der Raten über die Reihen (gleich gewichtet), explorativ die Rate
   im obersten Score-Quintil je Reihe; Abschnitt B ebenfalls.

Hinweis: die D3-Betriebsfunktionen liegen jetzt in `shared/saison_score_betrieb.py` (nicht Gegenstand), damit der
Rechenkern exakt der freigegebene Stand bleibt.
