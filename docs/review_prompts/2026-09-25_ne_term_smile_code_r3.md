# Code-Abnahme Runde 3: NE/Term/Smile (Commit auf master, `git log -1`)

Runde 2 (`..._code_r2.md`): FREIGABE nein, offen nur noch die Tick-Unsicherheit:

1. **Rundung vor dem Vergleich / lineare Näherung.** Umsetzung: `shared/black_scholes.skew_intervall_pts`
   invertiert die Grenzpreise beider gewählten 25Δ-Kontrakte exakt
   (`min = IV_put(p−h) − IV_call(c+h)`, `max = IV_put(p+h) − IV_call(c−h)`), nicht invertierbare Grenzen
   offen (±inf); `_laufzeiten_eigen` markiert `skew_ne_richtung_unsicher = lo <= 0 <= hi` UNGERUNDET.
   `tick_unsicherheit_pts` (linear) ist entfernt. Dein Grenzfall steht wörtlich im Wächter
   (`_pruefe_codex_grenzfall`: [−1,398; +0,001] → markiert).
2. **Kursraster.** `beobachtetes_raster(px)`: gröbstes mit dem Preis vereinbares Raster nach Cboe
   Rule 5.4 (nicht-nickliger Preis → 0,01; ≥ 3 $ und Vielfaches von 0,10 → 0,10; sonst 0,05). Begründung
   im Docstring: Klassenzugehörigkeit nicht verfügbar und aus den Kursen nicht trennbar (gemessen).

Echte Daten (40 Ketten): markiert AAPL −0,02 ± 0,21, AMD −0,10 ± 0,49, MU +0,27 ± 0,30.

Prüfe (a) ob 1 und 2 behoben sind (Reproduktionen wiederholen), (b) ob die konservative Raster-Regel
fachlich trägt (z. B. Preise ≥ 3 $ in Penny-Klassen mit 0,05-Raster), (c) neue Befunde. Werkzeug wie
bisher (Python-Pfad, TMP/TEMP auf `.codex_tmp`, Git-Status-Hash, Mutationstest NICHT ausführen, nichts
ändern). Ausgabe: Tabelle, Antwort (b), Befunde `DATEI:ZEILE | SCHWERE | Was | Reproduktion | Vorschlag`,
Exit-Codes der drei Wächter, Hash, `FREIGABE: ja/nein` + ein Satz.
