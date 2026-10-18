# Kalender V2 — Antwort Codex auf Code Runde 1 (2026-10-18)

**Urteil**

Keine Freigabe für V2. `alt` zeigt im geprüften Umfang keine Abweichung; der neue Pfad und seine Absicherung erfüllen die Bauvorlage noch nicht vollständig.

**Befunde**

- **P2 – Typprüfung fehlt:** [holidays.js:361](/C:/dev/SeasonalEdge/landing/js/holidays.js:361). `nextTradingDay("2026", 10, 16, "NYSE")` liefert `"2026-10-16"` statt `KalenderFehler`; ebenso werden Monat und Tag als Zeichenketten akzeptiert. `_ds` verdeckt die falschen Eingabetypen vor der Bundle-Validierung. B5 verlangt ganze Zahlen.
- **P2 – EN-Einbindung wird falsch bewertet:** [verify_boersenkalender_js.py:320](/C:/dev/SeasonalEdge/scripts/verify_boersenkalender_js.py:320). Erzeugte EN-Seiten werden gegen das reine Quellenmanifest geprüft und dadurch als unerlaubt abgelehnt; mit `landing/en/dashboard.html` lesend reproduziert. Gleichzeitig schließt [verify_einbindung.py:80](/C:/dev/SeasonalEdge/scripts/verify_einbindung.py:80) EN vollständig aus. Der vereinbarte EN-Einbindungsvertrag fehlt.
- **P2 – Inventarprüfung ist keine strukturelle Prüfung:** [verify_holidays_fassade.py:264](/C:/dev/SeasonalEdge/scripts/verify_holidays_fassade.py:264). Der Zeilenregex erkennt beispielsweise neue Rückfälle mit `"NONE"` oder `"NYSE"` nicht. Zudem fehlt der ausdrücklich vorgesehene Verbraucher `strategy-compute.js:335` der gesperrten `_NYSE_SONDER`-Liste im Inventar. Damit ist „Inventar leer vor V9“ kein belastbarer Wächter.
- **P2 – Produktionspfad und Statusanzeige unzureichend geprüft:** [header_v1_probe.js:21](/C:/dev/SeasonalEdge/scripts/js/header_v1_probe.js:21) extrahiert ausschließlich die Hilfsfunktion; öffentlicher Headeraufruf, Seitenbootstrap und Tickerwechsel bleiben ungetestet. [converter_probe.js:34](/C:/dev/SeasonalEdge/scripts/js/converter_probe.js:34) überspringt den Bootstrap und lädt `methode.js` nicht. Die 57 Statusfälle prüfen nur `K.status`, nicht sämtliche vereinbarten Anzeigen in Header und Converter.

**Antworten zu „Offen“**

- Unabhängige Monatslisten einschließlich Rückwärtsnummern, Monatsüberlauf und abgezähltem TDOY-Ausgangswert sind **Bedingung für V2**: Sie waren ausdrückliche Freigabeauflage.
- Echte jsdom-Seitenproben einschließlich A→B→A und Alt-Headervergleich müssen ebenfalls vor der Abnahme vorliegen.
- NYSE vor 1971 darf als separat geführter Restposten bleiben, sofern durchgehend exploratorisch gekennzeichnet.
- Der neue Gate-Schritt ist inzwischen im Arbeitsbaum eingetragen.

**Auflagen**

- Befunde beheben und die fehlenden unabhängigen sowie produktionsnahen Prüfungen ergänzen.
- Ausgeführt mit Python 3.14: Fassadenwächter **242/242, Exit 0**; zusätzlich 20 lesende Einbindungsprüfungen bestanden. Die zusätzlichen Typfälle und EN-Gegenprobe zeigen dennoch die genannten Lücken.
- Vollständiger Bundle-/Einbindungswächter scheitert hier an gesperrten temporären Schreibzugriffen; Mutationstests deshalb nicht ausgeführt. Keine Projektdateien geändert.
