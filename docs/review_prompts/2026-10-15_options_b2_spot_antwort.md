**FREIGABE (Code): nein**

Ein blockierender Befund:

**[P1] Gleiches Session-Datum beweist keinen Schlusskurs.** [Intraday-Refresh](C:/dev/Seasonaledge/scripts/intraday_refresh.py:150) schreibt auch während des Handels `close` in dieselbe Tabelle, mit demselben Schlüssel `ticker,date`. [_spot](C:/dev/Seasonaledge/scripts/snapshot_gex_massive.py:95) prüft nur Datum und gültigen Wert. Scheitern die Aktualisierungen nach Börsenschluss, bleibt ein Intraday-Wert stehen und wird als EOD-Spot verwendet. Die 60-%-Reißleine greift dann nicht zwingend; GEX kann erfolgreich mit falschem Spot schreiben.

Zu den Prüfaufträgen:

1. **Andere Session:** Die Spot-Auswahl selbst ist korrekt gebunden; weder Vor- noch Folgezeile wird ersatzweise genommen. Das tatsächliche Alter der Massive-Chain wird dadurch allerdings nicht geprüft — der Endpoint bleibt ein aktueller Snapshot ohne Session-Nachweis.

2. **Nightly-Ausfall:** Bereits vollständig geschriebene Schlusskurse bleiben trotz späterem Score-Fehler verwendbar. Fehlen Session-Zeilen tatsächlich, werden Ticker verworfen. Unter zwölf erfolgreichen Tickern von zwanzig: Exit 1, keine Schreibzugriffe, Key Levels übersprungen. Ab zwölf: Teilergebnis mit `failed`, Workflow kann grün bleiben. Alte Daten bleiben bei Gesamtausfall sichtbar; Health meldet eine Session Rückstand gelb, mehr rot. **Der oben beschriebene Intraday-Restbestand wird dagegen nicht erkannt.**

3. **Kursbasis:** „Supabase = unbereinigt“ gilt nicht allgemein. Der [Downloader](C:/dev/Seasonaledge/shared/yahoo_downloader.py:111) bevorzugt `adjclose`; der Nightly speichert diesen Wert. Für die aktuelle abgeschlossene Session bei Faktor 1 passt das zur Strike-Basis. Historische, später überschriebene Zeilen sind jedoch kein garantiert unbereinigter Schlusskurs.

Für die Freigabe braucht es einen **verlässlichen EOD-Nachweis pro Ticker und Session**, den Intraday-Schreibzugriffe nicht erzeugen können. Ergänzender Wächter: gültiger Intraday-Kurs mit richtigem Datum, aber ohne bestätigten Schluss → Ticker verworfen.

Read-only geprüft, keine Dateien geändert. Wächter/Mutation nicht erneut ausgeführt; die zusätzliche isolierte Probe scheiterte am nicht ausführbaren lokalen Python. **25/25 nicht unabhängig bestätigt.**
