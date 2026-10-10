# Antwort Codex — P1b Code Runde 1 (2026-10-10)

Prompt: [2026-10-10_kalender_p1b_code.md](2026-10-10_kalender_p1b_code.md). model: gpt-6.1-sol

**Urteil: mit Auflagen.** Keine Rechenabweichung im geprüften Bereich; vor Freigabe die folgenden Prüflücken schließen.

**Befunde**

- **Mittel – Isolation übersieht den Seitengenerator.** [verify_boersenkalender_js.py:242](/C:/dev/SeasonalEdge/scripts/verify_boersenkalender_js.py:242) beschränkt die Suche auf `.html/.js/.json`.
  Beleg: Eine im Speicher ergänzte Script-Einbindung in [build_en.py:177](/C:/dev/SeasonalEdge/landing/build_en.py:177) erscheint im erzeugten EN-Head, bleibt aber ungeprüft. Der EN-Build läuft nach dem Gate.
  Auflage: Auch Generatoren prüfen; Lesefehler nicht durch `except OSError: pass` übergehen.

- **Mittel – Abgefangene Ausnahmen zählen fälschlich als Mutationsnachweis.** [probe_boersenkalender.js:16](/C:/dev/SeasonalEdge/scripts/js/probe_boersenkalender.js:16) verpackt sämtliche API-Ausnahmen; [verify_boersenkalender_js_mutation.py:115](/C:/dev/SeasonalEdge/scripts/verify_boersenkalender_js_mutation.py:115) erkennt nur `[Ausnahme]`.
  Beleg: `null.x` im TSE-Golden-Week-Pfad wurde durch die echte Bewertungsfunktion als **„gefangen“** eingestuft.
  Auflage: Unerwartete API-Ausnahmen gesondert markieren und als ungültige Mutation werten; entsprechende Gegenprobe ergänzen.

- **Mittel – Datenende und Statusgrenzen sind nicht vollständig abgesichert.** [verify_boersenkalender_js.py:138](/C:/dev/SeasonalEdge/scripts/verify_boersenkalender_js.py:138) prüft nächste Sitzungen nur ab 2019/2020/2099; NYSE-Status 2028 fehlt ebenfalls.
  Beleg: Entfernen der Endgrenze aus [api.js:207](/C:/dev/SeasonalEdge/scripts/boersenkalender/api.js:207) lässt **58/58 Prüfungen grün**, obwohl TSE ab `2100-12-31` dann `2101-01-03` liefert.
  Auflage: Geschlossenes Datenende sowie jedes Statusintervall unmittelbar vor, auf und nach beiden Grenzen prüfen und mutieren.

- **Mittel – Dem Mutationstest fehlt die gemeinsame Sperre.** [verify_boersenkalender_js_mutation.py:82](/C:/dev/SeasonalEdge/scripts/verify_boersenkalender_js_mutation.py:82) liest Originalbytes ohne Sperre; der Import von `_atomar_schreiben` aktiviert `_exklusiver_lauf` nicht.
  Zwei gleichzeitige Läufe können mutierte Bytes als Original übernehmen und denselben temporären Schreibpfad verwenden.
  Auflage: Gemeinsame Sperre bereits **vor dem Einlesen von `ROH`** halten.

**Antworten**

1. Der Verzicht auf `art` ist für das isolierte P1b vertretbar: Die Schließungsmenge bleibt erhalten.
   `ereignisse: {}` allein definiert noch keinen P4-Vertrag. Ereigniskennung, Ereignisdatum und Schließungsbezug verbindlich beschreiben.
   „Reserviert für Schema 2“ bedeutet einen Schemawechsel; die aktuelle API lehnt Schema 2 ausdrücklich ab.

2. Im vollständigen Python-/NumPy-Vergleich keine Abweichung gefunden.
   `.F`, Groß/Klein, Schaltjahre und Bereichsgrenzen bestehen; zusätzliche Gegenproben bestätigen Reihenfolge, Duplikate und eingefrorene Nummernobjekte.
   `status` erlaubt wie Python Jahre außerhalb des Rechenbereichs und liefert dort den Standardstatus.

3. Der Zeitzonen-Hashvergleich ist tragfähig und prüft vollständige Ergebnisse einschließlich Aufrufen.
   `get()` mit dem ersten Treffer ist bei den derzeit identischen wiederholten Aufrufen unproblematisch.
   Ergänzen: Mutationen für Datenende, Statusgrenzen, Rückgabeschutz und Isolation über den EN-Generator; Ausnahmebewertung korrigieren.

4. Das neue Gate nutzt bereits vorhandene Node- und NumPy-Abhängigkeiten; lokal lief der Vergleich in **36,39 Sekunden**.
   nginx liefert die Datei über die bestehende JS-Regel aus; aktuell bindet keine Landing-Datei sie ein.
   `--pruefen` bestätigt die Arbeitsdatei und scheitert erwartungsgemäß am uncommitteten Bundle in `HEAD`; nach Commit erneut prüfen.

Read-only durchgeführt: **58/58 Prüfungen**, 13 Börsen × 78.892 Tage, sechs Zeitzonen. Übergabe und Gegenproben ausschließlich im Speicher; keine Dateien geschrieben.
