# Code-Review: Streamlit aus + Ampel aus den Mails (Runde 2)

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `..._runde1.md` + `..._antwort1.md`. Nur lesen.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
Antwort auf Deutsch: je Befund Schwere + Datei:Zeile + Fall + Änderung; am Ende genau eine Zeile `FREIGABE: ja`
oder `FREIGABE: nein`.

## Korrektur zu deinem Befund (P2: Ampelfarbe in der Admin-Health-Mail)
`scripts/daily_health_check.py` Check 6 heißt jetzt „Stress-Score-Lauf (SPY)". Die Mail nennt nur den
Prüfbefund: grün „Aktuell bis <Datum>, nachgerechnet gleich", rot bei Abweichung „Gespeicherter Wert <Datum>
weicht von der Nachrechnung ab (nachgerechnet bis <Datum>) — Lauf prüfen", gelb/rot bei Rückstand. Weder Farbe
noch Score der Ampel stehen im Text. Der interne Vergleich (Score, S, Farbe) bleibt.

Wächter `verify_stress_ampel.py`: `ampel_nicht_in_mails` prüft jetzt auch `daily_health_check.py` (verbotene
Muster: `['ampel']}`, `get('ampel')}`, „Stress-Ampel (SPY)"), neue Mutation „Ampelfarbe in der Health-Mail"
(fügt `({neu['ampel']})` wieder in den grünen Text ein).

## Belege
`verify_stress_ampel.py --snapshot` 34/34. Mutationsläufe laufen.

## Bitte prüfen
Gibt es weitere Versandwege, über die die Ampel (Farbe, Score, Name) in eine Mail gelangt — etwa
`completeness_report`, `daily_health.yml`, Admin-Benachrichtigungen im Nightly, Fehlermeldungen mit Detailtext?
