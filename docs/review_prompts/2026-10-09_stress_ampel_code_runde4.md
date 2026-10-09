# Code-Review Stress-Ampel, Runde 4 (Nachtrag nach Freigabe R3)

Repo `C:\dev\Seasonaledge`, Arbeitsstand auf `85f212b` (R3-Stand, deployed). Antwort auf Deutsch: je Befund Schwere +
Datei:Zeile + Eingabefall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Was passiert ist
SQL ausgeführt, `verify_stress_sql_live.py` auf dem Server **BESTANDEN** (inkl. 42501 für anon). Deploy grün. Erster
Vollauf SPY (8481 Kurse, Zählung gleich): **Rücklesevergleich gescheitert, Lauf abgebrochen, nichts veröffentlicht** —
PostgREST liefert double precision nur auf **15 signifikante Stellen** (`88.35978835978835` → `88.3597883597884`).

## Änderung
`shared/stress_score.py` + `landing/js/dash-compute.js`: Score auf 10, S auf 12 Nachkommastellen gerundet, **bevor** die
Ampel bestimmt wird (Python `round`, JS `Math.round(x·10^k)/10^k`); der Rang nutzt weiter das ungerundete S. Damit
übersteht der gespeicherte Wert das Rücklesen exakt, und Farbe, Anzeige und Datenbank beziehen sich auf dieselbe Zahl
(sonst: 89,99999999999999 gelb, Rücklesen „90"). Der Fake im Wächter gibt `stress_scores` jetzt wie PostgreSQL mit 15
Stellen zurück; neue Mutation „Score ungerundet gespeichert" reißt `db_vollauf`.

## Belege
`verify_stress_ampel.py --snapshot …` **33/33** (Python = JS jeden Tag auf fünf Tickern inkl. Ampel), `--mutationen`
**26/26** + 3/3. Bitte besonders prüfen: Kann die unterschiedliche Rundung (Python dezimal korrekt, JS über
Multiplikation) an 70/90 eine andere Farbe ergeben, und reicht 12 Stellen für S bei großen Drawdowns (S bis ~40)?
