# Antwort Codex Runde 6 — P1b isoliert (2026-10-10)

Prompt: [2026-10-10_xetra_tdoy_plan_v6.md](2026-10-10_xetra_tdoy_plan_v6.md). model: gpt-6.1-sol

**Urteil: mit Auflagen.** Weg A erfüllt die zentrale Auflage aus Runde 5: Der neue Kalender bleibt bis zur gemeinsamen Aktivierung ohne Seitenwirkung. Vor dem Code fehlen noch Präzisierungen am Daten- und Prüfvertrag.

**Antworten**

1. I1–I4 lösen Isolation, gemeinsame Generation, strenge Börsenprüfung, Zeitzonenarithmetik und LF-Festlegung (`2026-10-10_xetra_tdoy_plan_v6.md:14–41`).  
   Ereigniskennungen dürfen bis P4 warten; ihre spätere Darstellung sollte jetzt feststehen: stabile Kennung, Ereignisdatum und Bezug zur Schließung.  
   Eine eigene, optional ergänzbare Ereignistabelle ermöglicht das ohne Schema-Bruch. `{d, art}` allein reicht für historische Ereignisvergleiche nicht (`feiertage.html:265`, `dashboard.html:1295`).

2. **Zeitzonenfehler jetzt separat beheben**, einschließlich der Datumsiteration. Unter Apia ist 30.12.2011 für NYSE/XETRA/LSE fälschlich geschlossen; Monatsende wird 29.12. statt 30.12. (`holidays.js:261,293,310`).  
   Konkrete Wirkung: Die echte Strategieprobe macht am Datenrand einen noch ausstehenden Monatsausstieg zum vorhandenen Kursindex (`strategy-compute.js:195`); auch Dashboard-Regeltermine verwenden den falschen Termin (`dashboard.html:1146`).  
   Die 10-Tage-Grenze ist dagegen mit den heutigen drei Legacy-Kalendern **latent**: maximale Schließungsketten 1885–2100 sind NYSE 6, XETRA 5, LSE 4 Tage.  
   Die TSE-Gegenprobe aus Runde 5 verwendete zusätzliche Kalenderdaten. Die Grenze kann separat gehärtet werden; eine heutige NYSE-/XETRA-/LSE-Fehlwirkung ist damit nicht belegt (`holidays.js:326`).

3. Die sechs Zonen reichen für diese Kalenderprüfung: positive/negative Offsets, Sommerzeit und übersprungener Kalendertag (`2026-10-10_xetra_tdoy_plan_v6.md:48`).  
   Je Zone einen eigenen Node-Prozess starten und **vor Date-Nutzung und Bundle-Laden** `process.env.TZ = process.argv[2]` setzen (`scripts/js/tz_probe.js:14`).  
   Python `subprocess.run([...])` vermeidet Git-Bash-Pfadkonvertierung; keine Shell-Zuweisung `TZ=Europe/Berlin` verwenden.  
   Januar-/Juli-Offsets und Apias Datumswechsel ausdrücklich nachweisen. Das Setzen funktioniert hier unter Windows mit Node 24.14.0; die verwendete Laufzeit muss bei unwirksamer Zone scheitern.

4. Keine grundsätzlichen Größenbedenken, aber die frühere Schätzung ist überholt.  
   Speicherprototyp nach I2: **24.017 Einträge**, 370 Ticker, **752.977 Byte roh / 44.074 Byte gzip**, vor API-Code; dabei überall `art="feiertag"` als Größenansatz (`2026-10-10_xetra_tdoy_plan_v6.md:23`).  
   Das ist für eine gemeinsam geladene Datei vertretbar. Prüfungen nach Börse/Jahr bündeln und Jahresnummern cachen.

**Befunde**

- **Mittel — I5 prüft zwei öffentliche APIs und entscheidende Metadaten nicht ausdrücklich.**  
  `schliessungen()` und `status()` fehlen im API-Vergleich. Falsches `art` oder falsche Statusintervalle können alle Offen-/Nummernvergleiche bestehen (`2026-10-10_xetra_tdoy_plan_v6.md:43–52`). Der Bytevergleich gegen denselben Erzeuger liefert dafür keinen unabhängigen Fachbeweis.

- **Mittel — Der neue Nummerierungsbereich braucht eine dritte Zählreferenz.**  
  I5(c,d) nennt ausschließlich Python-Vergleiche. Der vorhandene NumPy-Wächter deckt 1950–2035 ab, das neue Bundle 1885–2100 (`verify_handelstag_nummern.py:66`). Die unabhängige Zählung muss den erweiterten Bereich und die daraus abgeleiteten Termin-APIs einschließen.

- **Mittel — Schließungsart ist keine Ereignisidentität.**  
  Verschobene Feiertage, Ersatztermine und einmalige Ereignisse bleiben mit `{d, art}` ununterscheidbar. Außerdem gibt es regelmäßig geschlossene Börsentage ohne Nationalfeiertag, etwa TSE 2./3. Januar und 31. Dezember (`exchange_holidays.py:338`). Klassifikation, Überschneidungen und spätere Ereigniserweiterung sind noch festzulegen (`2026-10-10_xetra_tdoy_plan_v6.md:23–28`).

- **Mittel — Termin-Rückgaben sind noch nicht vollständig spezifiziert.**  
  „Validierung zuerst“ klärt nicht, was positive, aber nicht vorhandene Positionen liefern, ob der nächste Handelstag das Eingabedatum einschließt und wie Rückgaben gegen Cache-Mutation geschützt werden (`2026-10-10_xetra_tdoy_plan_v6.md:35–38`). Die bestehenden Monats-APIs liefern bei fehlender Position `null` (`holidays.js:283,299`).

**Auflagen vor dem Code**

- Ereigniserweiterung verbindlich beschreiben; Kennungen können bis P4 unbefüllt bleiben. Ereignisse nicht aus Listenposition oder `art` rekonstruieren.
- Klassifikation sämtlicher Schließungen zentral in Python festlegen; bestehende Produktions-Schließungsmengen unverändert nachweisen.
- I5 um `schliessungen`, Statusgrenzen, Prüfdatum, Klassifikations-Sollfälle und unabhängige NumPy-Zählung 1885–2100 ergänzen.
- Terminvertrag festlegen: positive ganzzahlige Positionen, fehlende Position → `null`, nächste Sitzung **ab einschließlich** Datum, Datenende → Fehler; unveränderliche beziehungsweise kopierte Rückgaben.
- Mutationen deterministisch über `_atomar_schreiben`; fachliche Mutationen müssen ihre benannte Prüfung treffen, nicht lediglich den Aktualitätsvergleich.

Read-only geprüft: Python-Sollfälle **86/86 bestanden**, echte JS- und Strategiegegenproben im Speicher, versionierter Arbeitsbaum unverändert. Keine Dateien geschrieben; schreibende Mutationstests nicht ausgeführt.
