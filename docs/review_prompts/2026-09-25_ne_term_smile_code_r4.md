# Code-Abnahme Runde 4: NE/Term/Smile (Commit auf master, `git log -1`)

Runde 3 (`..._code_r3.md`): FREIGABE nein. Offen:

1. **MITTEL** — `(hi−lo)/2` als „±" um den Skew deckte bei asymmetrischem Intervall eine Grenze nicht ab.
   Umsetzung: `skew_ne_unsicherheit_pts = ceil(max(skew_roh − lo, hi − skew_roh))` (3 Stellen, nach außen),
   `skew_ne_intervall` nach außen gerundet; Tooltip in `skew.html::neZelle` zeigt das Intervall.
2. **NIEDRIG** — Elternprozess brach unter cp1252 ab. Umsetzung: `scripts/waechter_isolation.py` stellt
   stdout/stderr auf UTF-8 um.

Prüfe (a) ob beide behoben sind (deine Reproduktionen wiederholen, auch ohne `PYTHONUTF8`),
(b) neue Befunde. Werkzeug wie bisher (Python-Pfad, TMP/TEMP auf `.codex_tmp`, Git-Status-Hash,
Mutationstest NICHT ausführen, nichts ändern). Ausgabe: Tabelle, Befunde
`DATEI:ZEILE | SCHWERE | Was | Reproduktion | Vorschlag`, Exit-Codes der drei Wächter, Hash,
`FREIGABE: ja/nein` + ein Satz.
