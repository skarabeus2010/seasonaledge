Read-only geprüft. **Zehn Korrekturen sind bestätigt; bei 1 und 9 bleiben Lücken.** Keine Dateien geändert, keine Live-Datenbank angesprochen.

1. **Hoch – Die Zusammenführung kann aktuelle Kurse durch ältere Cache-Werte ersetzen.**  
   [decade-compute.js:529](/C:/dev/Seasonaledge/landing/js/decade-compute.js:529) hängt `rows` hinter die Vollhistorie. Bei gleichen Tagen gewinnt anschließend der letzte Eintrag ([Bereinigung:507](/C:/dev/Seasonaledge/landing/js/decade-compute.js:507)). Die getrennten Cache-Schlüssel für Vollhistorie und Zeitraumabfragen können unterschiedlich alte Daten enthalten ([app.js:746](/C:/dev/Seasonaledge/landing/js/app.js:746)).

   **Fehlerfall:** Die Zeitraumabfrage liegt noch vor einer Kurskorrektur im Cache, die Vollhistorie wird danach frisch geladen. Dashboard/KI-Seite überschreiben korrigierte Kurse mit alten Werten; Watchlist und Nightly verwenden die korrigierte Historie. Auch ein Zeitraumwechsel kann dadurch wieder den Score verändern.

   **Reproduziert mit den echten JS-Modulen und synthetischen Kursen:** gleicher Ticker, `as_of=2026-10-09`, jeweils 20 Vergleichsjahre: Vollhistorie **8,5**, zusammengeführte Historie **8,6**. Der Vollhistorienabruf ist korrigiert, die garantierte Gleichheit noch nicht. Überlappende Tage benötigen eine eindeutige Quellenpriorität; vorzugsweise den Score auf einer einzigen vollständigen Datenbasis rechnen.

2. **Mittel – Gleichzeitige neue Writer können eine Protokollabweichung weiterhin übersehen.**  
   [saison_score_betrieb.py:78](/C:/dev/Seasonaledge/shared/saison_score_betrieb.py:78) liest den bestehenden Eintrag **vor** dem konfliktignorierenden Insert in Zeile 87.

   **Fehlerfall:** Full-Scanner und Nightly verarbeiten denselben Ticker/Stichtag mit unterschiedlichen Kursständen. Beide lesen zunächst „kein Eintrag“. Writer A fügt sein Protokoll ein; Writer B trifft anschließend den Konflikt und schreibt nur seinen abweichenden Scannerstand. Beide geben eine leere Abweichungsliste zurück. Der erste Protokolleintrag bleibt korrekt erhalten, die zugesagte Warnung fehlt.

   Den tatsächlich gespeicherten Protokolleintrag **nach** dem Insert zurücklesen und vergleichen. Dieser Befund betrifft zwei neue Writer, unabhängig vom ausgeschlossenen Alt-/Neucode-Parallelbetrieb.

Die zwölf Korrekturen im Einzelnen:

| Nr. | Prüfung am Code | Ergebnis |
|---|---|---|
| 1 | [Vollhistorie:525](/C:/dev/Seasonaledge/landing/js/decade-compute.js:525), Aufrufer [Dashboard:2040](/C:/dev/Seasonaledge/landing/pages/dashboard.html:2040) und [KI-Seite:760](/C:/dev/Seasonaledge/landing/pages/ki-saisonalitaet.html:760) ohne Jahresparameter | Abruf bestätigt; Zusammenführung siehe Befund 1. |
| 2 | Leere Antwort wirft in Zeile 528; Aufrufer zeigen `ladefehler` in Dashboard:2043 und KI-Seite:763; [EN-Schlüssel:948](/C:/dev/Seasonaledge/landing/i18n/en.json:948) vorhanden | Bestätigt. Leere Antwort und abgewiesener Fetch auch dynamisch geprüft. |
| 3 | [Protokoll vor Scanner:86](/C:/dev/Seasonaledge/shared/saison_score_betrieb.py:86), [Resume:53](/C:/dev/Seasonaledge/scripts/full_scanner_run.py:53) nach heutigem Datum und Methode | Bestätigt. Ein fehlgeschlagener Protokollwrite verhindert den nachfolgenden Scannerwrite. |
| 4 | [Nightly:75](/C:/dev/Seasonaledge/scripts/nightly_refresh.py:75), :81, :116, :151 erfassen die genannten Fehler; Aggregation :157/:159, Fehlerexit :519 | Bestätigt, einschließlich `continue` nach Kurs-Upsert-Fehler. |
| 5 | [Daily:549](/C:/dev/Seasonaledge/shared/daily_report.py:549), Prüfung auswertbarer Fenster :648 | Bestätigt: `status == 'ok'`, Score vorhanden, mindestens ein Fenster mit Fallzahl. |
| 6 | [Daily-Template:121](/C:/dev/Seasonaledge/scripts/templates/daily_report.html.j2:121) | „je Fenster mind. n=…“ bestätigt. |
| 7 | [Health-Check:336](/C:/dev/Seasonaledge/scripts/daily_health_check.py:336) | Methodenfilter bestätigt. |
| 8 | [Scanner:429](/C:/dev/Seasonaledge/landing/pages/scanner.html:429) | Verarbeitet/Universum getrennt; Differenzmenge, erste zwölf Ticker und vollständiger Tooltip bestätigt. |
| 9 | [Abgleich:78](/C:/dev/Seasonaledge/shared/saison_score_betrieb.py:78), [Nightly-Warnung:130](/C:/dev/Seasonaledge/scripts/nightly_refresh.py:130), [Full-Scanner-Ausgabe:67](/C:/dev/Seasonaledge/scripts/full_scanner_run.py:67) | Für aufeinanderfolgende erfolgreiche Writes bestätigt; Parallelfall siehe Befund 2. Full-Scanner verwendet `print`, keinen Logger-Warnlevel. |
| 10 | [Watchlist:541](/C:/dev/Seasonaledge/landing/pages/watchlist.html:541), Ausgabe :635 | Grund, vier Bausteine und separate Musterkonformität bestätigt. |
| 11 | [SEO-Generator:423](/C:/dev/Seasonaledge/seo/programmatic_seo_builder.py:423), :437 | Saison-Score und „350+“ bestätigt. |
| 12 | [Full-Scanner:189](/C:/dev/Seasonaledge/scripts/full_scanner_run.py:189) | Gespeicherte nicht berechenbare Ergebnisse verhindern Exit 2; Schreib-/Ladefehler bleiben erfolglos. |

**Weekly:** Für den regulären Versand reicht die bestehende Absicherung. Der Leser protokolliert den Abruffehler ([weekly_report.py:91](/C:/dev/Seasonaledge/shared/weekly_report.py:91)); leeres `top_ki` führt vor der Empfängerermittlung zu einem Fehlerprotokoll und **Exit 3** ([weekly_newsletter.py:148](/C:/dev/Seasonaledge/scripts/weekly_newsletter.py:148)). `--test` und `--to` dürfen weiterhin einen leeren Report versenden; die Aussage „Versand bricht ab“ gilt deshalb nur für den regulären Lauf.

**Migration → Deploy:** Unter deinen genannten Voraussetzungen ist deine Einschätzung richtig: Vor dem ersten neuen Writer existiert keine neue Scannerzeile, die alter Code überschreiben könnte. Die Migration erzeugt selbst keine solchen Zeilen. Der dokumentierte Deploy ersetzt den festen App-Container ([deploy.yml:142](/C:/dev/Seasonaledge/.github/workflows/deploy.yml:142)); Nightly läuft darin über `docker exec` ([sa-nightly.service:16](/C:/dev/Seasonaledge/deploy/systemd/sa-nightly.service:16)). Damit entsteht durch das reine Fenster Migration→Deploy kein zusätzlicher Überschreibungsbefund. Den tatsächlichen VPS-Prozessstand habe ich nicht geprüft.

Bullish-Bias und Videoskript bleiben wie vereinbart ausgenommen. Neun Inline-Skripte der vier betroffenen Seiten, deren JSON-LD und beide Sprachdateien ließen sich parsen. Python-Laufzeittests waren wegen des nicht ausführbaren Python-Launchers nicht möglich; die Python-Prüfung erfolgte statisch.

**FREIGABE: nein**
