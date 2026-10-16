# Code-Review Folgeposten, Runde 2

Deine Antwort R1: `docs/review_prompts/2026-10-16_folgeposten_code_antwort1.md` (nein, ein P2, ein P3). Prompt R1:
`…_folgeposten_code.md`. Code uncommittet im Arbeitsbaum. Read-only, Deutsch, **FREIGABE (Code): ja/nein**.

## Zu P2: keine Korrektur mehr, Schnitt am Widerspruch (deine zweite Option)
`shared/daily_report._basisgleich` rechnet nichts mehr um. Die Reihe = die gespeicherten gültigen Schlusskurse, aber
erst ab dem **jüngsten** Widerspruch: zwei unmittelbar aufeinanderfolgende Zeilen mit gültigem Kurs, deren
|ln(c_i/c_{i−1}) − log_return_i| > `basisabweichung.SCHWELLE`. Die Reihe beginnt mit der Zeile i. Über eine kurslose
Zeile hinweg wird nicht verglichen (der Return dieser Zeile bezieht sich auf eine Zeile ohne Kurs). Unterhalb der
Schwelle bleibt alles wie vor der Änderung.
Dein Gegenbeispiel 100 → 101, lr 0,2: Reihe = [101], Tagesänderung `None` statt +22 % (Test).
Wirkung live (read-only, Server): 750 Tage über 373 Ticker → gekürzt nur ETHA (515 → 12 Zeilen ab 30.09.); 5500 Tage
über die 11 Sektor-ETFs (der Leser des Monatsmittels) → 0 gekürzt.
Folge für ETHA: zu kurze Reihe für RSI/LBR, bis jemand die alten Kurse auf die neue Basis bringt — das wäre ein
DB-Schreibvorgang mit Nutzerfreigabe, nicht Teil dieser Änderung.

## Zu P3: Datum strikt
`_session_frische` nimmt nur noch `skew_rang.datum_gueltig` (genau `YYYY-MM-DD`, echtes Kalenderdatum); Test
„ISO-Wochendatum 2026-W43-1 → rot“.

## Tests
`verify_kursreihe_basis.py` neu geschnitten: Basiswechsel, falscher Return, Schwelle 0,049/0,051, Forex-Doppelspanne,
Dividende, zwei Widersprüche (Schnitt am jüngeren), kurslose Zeile, ungültige Typen, Gesamtordnung, beide Leser
(Monatsmittel: Februar mit Basiswechsel fällt raus, kein +200 %). `verify_gex_session.py` grün.
