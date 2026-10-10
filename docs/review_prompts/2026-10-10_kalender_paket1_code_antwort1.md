# Antwort Codex — Paket 1 Code Runde 1 (2026-10-10)

Prompt: [2026-10-10_kalender_paket1_code.md](2026-10-10_kalender_paket1_code.md). model: gpt-6.1-sol

**Urteil: Freigabe mit Auflagen.** Vor dem Commit die fehlenden Sollfälle samt Mutationen ergänzen und die TSE-Wirkungszahl korrigieren. Keine zusätzliche Kalenderabweichung im geprüften Zeitraum gefunden.

Python 3.14.3: neuer Code **75/75**, HEAD **23/75**, Exit 1. Im Speicher: **13/13** vorhandene Mutationen erkannt, **2/2** Gegenproben korrekt verworfen. Der schreibende Mutationstest wurde nicht ausgeführt; keine Dateien oder Datenbanken verändert.

**Befunde**

1. **[P2] Allgemeine Brückentage sind nicht abgesichert** — [verify_kalender_sollfaelle.py:65](C:/dev/SeasonalEdge/scripts/verify_kalender_sollfaelle.py:65).
   Die Mutation `year == 2019 and …` an [exchange_holidays.py:373](C:/dev/SeasonalEdge/shared/exchange_holidays.py:373) lässt **75/75** bestehen, obwohl 2009-09-22, 2015-09-22 und 2026-09-22 anschließend fälschlich offen sind.
   Diese drei geschlossenen Tage und eine offene Gegenprobe aufnehmen; Mutation an eine benannte Prüfung binden. [Amtliche Regel und Beispiele](https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html), [NAOJ 2009](https://eco.mtk.nao.ac.jp/koyomi/yoko/2009/rekiyou091.html).

2. **[P2] Geänderte historische Regeln bleiben ungetestet** — [verify_kalender_sollfaelle.py:55](C:/dev/SeasonalEdge/scripts/verify_kalender_sollfaelle.py:55).
   **4/4** zusätzliche Mutationen entkommen: Ersatz vor 1973, Meerestag vor 1996, Seijin immer am zweiten Montag, Taiiku historisch am zweiten Montag.
   Geeignete Sollpaare: 1971-10-11 offen / 1973-04-30 zu; 1995-07-20 offen / 2000-07-20 zu; 1999-01-11 offen / 1999-01-15 zu; 1997-10-13 offen / 1997-10-10 zu.
   Einzelne belegte Sollfälle bestätigen dabei keinen vollständigen historischen Börsenkalender. [Gesetzesänderungen](https://eco.mtk.nao.ac.jp/koyomi/yoko/appendix.html).

3. **[P2] Wirkungszahl ist nicht reproduzierbar** — [Review-Prompt:31](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_kalender_paket1_code.md:31).
   Direkter Vergleich von `is_trading_day` für **31.411 Tage 1950–2035**: TSE **281**, davon **254 vor 2000** und **27 ab 2000**; angegeben sind 271.
   NYSE 8, LSE 26, HKEX 1, KRX 5 und die übrigen Börsen 0 bestätigt. Messung korrigieren und den Reproduktionsweg angeben.

4. **[P2, bestehender Defekt] Weitere Python-Mutationsläufe können alten Bytecode prüfen** — beispielsweise [verify_polymarket_preisqualitaet_mutation.py:182](C:/dev/SeasonalEdge/scripts/verify_polymarket_preisqualitaet_mutation.py:182).
   Ohne Schreiben nachgewiesen: CPythons Zeitstempelprüfung akzeptiert alten Bytecode bei gleicher Quellgröße und gleicher Zeitstempelsekunde trotz geändertem Verhalten.
   Discovery, Preisqualität und Zwillinge importieren mutierten Python-Code ohne frischen Cache. Die neue Kalenderprobe isoliert ihren Cache korrekt.

**Antworten**

1. **TSE 2000–2030:** Keine weitere fehlende Regel gefunden.
   Gegen die jährlichen NAOJ-Listen: **0 Abweichungen an 9.861 Tagen 2001–2027**, einschließlich September-Brücken, Thronwechsel und Olympia.
   Für 2000 sind die Sollfälle und Regelgrenzen bestätigt; der Jahresscan war nicht vollständig textlich auslesbar.
   2028–2030: **0 Abweichungen an 1.096 Tagen** gegen eine getrennte Regelreferenz; das bleibt eine [Regelprojektion mit vorausberechneten Tagundnachtgleichen](https://www.nao.ac.jp/faq/a0301.html).

2. **LSE-Ersatzregel:** Ja.
   Weihnachten Fr → 25./28. geschlossen; Sa → 27./28.; So → 26./27.
   Neujahr Sa oder So → folgender Montag geschlossen. Die teilweise falschen Anlasskommentare ändern die richtigen Datumsresultate nicht. [Amtlicher Kalender und Ersatzregel](https://www.gov.uk/bank-holidays).

3. **Sofortige Wirkung:** Daily-TDOM/Statuszeilen, Sitzungsermittlung, Vollständigkeitsprüfungen, Python-Strategiepfade und Kalendererzeuger verwenden die neuen Regeln.
   Der [Intraday-Schreiber:167](C:/dev/SeasonalEdge/scripts/intraday_refresh.py:167) nutzt sie bereits für neue Nummern; historische `prices` werden durch K1 nicht automatisch neu nummeriert. `tdom_stats` zählen weiterhin Kurszeilen.
   Vor dem Commit diese Mischung dokumentieren; einen DB-Backfill verlangt K1 nicht. Neu erkannte fehlende KRX-Sitzungen als Datenlücken behandeln. Konkrete DB-Betroffenheit wurde nicht geprüft.

4. **Mutationstest:** Die vorhandenen Mutationen sind fachlich wirksam; die Abdeckung reicht noch nicht.
   Die **5/5** entkommenen Zusatzmutationen aus Befund 1/2 ergänzen.
   Die Speicherprüfung bestätigt Anker und Klassifizierung, ersetzt aber keinen erneuten vollständigen Lauf des schreibenden Tests nach der Ergänzung.

5. **Gemeinsamer Cache-Helfer:** Ja, für Proben, die mutierten Python-Code importieren.
   Einen gemeinsamen Python-Probelauf in [verify_twins_mutation.py:199](C:/dev/SeasonalEdge/scripts/verify_twins_mutation.py:199) einführen: frischer Cache je Unterprozess, genutzt auch vom neuen Kalendertest.
   Die Isolation gehört zum Prozessstart. `-B` verhindert lediglich [Bytecode-Schreiben](https://docs.python.org/3.14/using/cmdline.html#cmdoption-B).
   Das genannte Suchmuster findet **vier andere Dateien**; i18n liest mutierte JS/JSON-Dateien und ist deshalb kein Beleg für diesen Defekt. Auch die `sys.executable`-Proben prüfen.
