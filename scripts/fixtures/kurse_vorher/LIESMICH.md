# Stand VOR der Umstellung auf SA.kurse (git 05e6310)

Wörtliche Kopien der Dateien, die die Kurslader-Migration ändert — Referenz „vorher" für
`scripts/verify_seiten_kurse.py`. Der Vorher-Baum = aktueller `landing/` + diese Dateien, ohne `js/kurse.js` und
ohne dessen `<script>`-Einbindung. Pfade relativ zu `landing/`.

Ändert ein späterer Commit eine dieser Dateien aus einem anderen Grund, meldet die Seitenprobe einen Unterschied;
dann die Änderung hier nachziehen (nur die fachfremde, nicht die Lader-Umstellung).

Nachgezogen 2026-10-11 (fachfremd, V1b Releasekennung): Bootstrap (`window.__SA_RELEASE`/`__SA_METHODE` + `methode.js`)
in den Seiten und die Prüfzeile `window.SA.__release(…)` in `js/app.js` und `js/decade-compute.js` — wie im Arbeitsbaum.

Nachgezogen 2026-10-21 (fachfremd, zwei falsche Nenner im Dashboard): der Nenner der
TDOM-Kachel kommt jetzt aus dem Boersenkalender des laufenden Monats statt aus dem
Maximum aller Jahre, und `computeTwoWeekPhases` ueberspringt ein Jahr ohne Abdeckung
mit `continue` statt die ganze Phase mit `return` zu verwerfen (Dezember H2).

Nachgezogen 2026-10-21 (fachfremd, Kachel-Erklaerungen): Info-Badges auf den sechs
Stat-Kacheln, `position:relative` auf `.bento-stat6`, kurze Wochentage in der
Overnight-Kachel (`_wdKurz`) und Unterzeilen, die die Rechnung nennen statt nur die
Fallzahl.
