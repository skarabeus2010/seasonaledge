# Code-Abnahme Runde 5: NE/Term/Smile (Commit auf master, `git log -1`)

Runde 4 (`..._code_r4.md`): FREIGABE nein, ein Rest (NIEDRIG): `skew_ne_unsicherheit_pts` war um den
ungerundeten Skew gerechnet, ausgegeben wird der gerundete. Umsetzung: `compute_options_skew.py`
(NE-Block) rechnet U aus `skew_ne_pts` (ausgegeben) und den nach außen gerundeten Grenzen
(`lo_r = floor(lo·1000)/1000`, `hi_r = ceil(hi·1000)/1000`), `U = ceil(max(sk − lo_r, hi_r − sk)·1000 − 1e-9)/1000`.
Der Wächter prüft die Abdeckung ohne Toleranz an drei Asymmetrien.

Prüfe (a) ob der Rest behoben ist (deine Reproduktion wiederholen), (b) neue Befunde — insbesondere,
ob das `− 1e-9` im `ceil` eine Unterdeckung zulassen kann. Werkzeug wie bisher (Python-Pfad,
TMP/TEMP auf `.codex_tmp`, Git-Status-Hash, Mutationstest NICHT ausführen, nichts ändern). Ausgabe:
Tabelle, Befunde `DATEI:ZEILE | SCHWERE | Was | Reproduktion | Vorschlag`, Exit-Codes der drei Wächter,
Hash, `FREIGABE: ja/nein` + ein Satz.
