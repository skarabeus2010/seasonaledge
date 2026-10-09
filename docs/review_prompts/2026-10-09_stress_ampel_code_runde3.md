# Code-Review Stress-Ampel, Runde 3

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `..._code_runde1-2.md` + Antworten. Prüfe die Korrektur zu deinem
Befund aus Runde 2 und den Code auf neue Fehler. Antwort auf Deutsch: je Befund Schwere + Datei:Zeile + konkreter
Eingabefall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Korrektur
`scripts/verify_stress_sql_live.py`: neue Funktion `anon_pruefung(env, anon_fabrik)`. Fehlen `SUPABASE_URL` oder
`SUPABASE_ANON_KEY` → Fehlertext. Einziger Erfolg: eine Ausnahme mit PostgreSQL-Code **42501** (insufficient_privilege,
gelesen aus `e.code` bzw. dem Fehler-Dict von postgrest-py). Jeder andere Fehler (Verbindung, anderer Code) und ein
erfolgreicher Aufruf → Fehlertext → Exit 1. Der Livetest ruft sie mit `os.environ` und `supabase.create_client` auf.

## Belege
`scripts/verify_stress_ampel.py --snapshot …` **33/33**, neu `sql_live_rechtepruefung` (fünf Fälle mit Fake-Fabrik:
Schlüssel fehlt, Verbindungsfehler, anderer Code, anon darf starten → nicht bestanden; 42501 → bestanden).
`--mutationen` **25/25** + 3/3 untaugliche verworfen (neu: „jeder Fehler gilt als Verweigerung", „fehlender Schlüssel
bestanden").
