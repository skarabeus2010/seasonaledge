# Antwort Codex Runde 1 — XETRA TDOY/TDOM (2026-10-10)

Prompt: [2026-10-10_xetra_tdoy_plan.md](2026-10-10_xetra_tdoy_plan.md). Modell laut Log: model: gpt-6.1-sol

## Urteil

**Nicht tragfähig:** E2 lässt einen aktiven Schreibweg aus, E3 kann die zusätzlichen Änderungsklassen noch nicht freigeben, und die Wirkung auf Leser sowie der Schutz vor Teiländerungen sind unvollständig festgelegt.

## Antworten auf die Fokusfragen

1. **3.10.2011–2013 und 2018:** Die offiziellen Kalender führen den 3. Oktober **2011, 2012 und 2013 als Handelstag**; diese Tage dürfen nicht in `XETRA_SONDER`. Quellen: [2011](https://www.cashmarket.deutsche-boerse.com/resource/blob/290510/610d72b78230cf12cb2139abed3790ee/data/handelskalender-2011.pdf), [2012](https://www.cashmarket.deutsche-boerse.com/resource/blob/311704/728ce5d68a607abc09cbe24257c39bbc/data/handelskalender-2012.pdf), [2013](https://www.cashmarket.deutsche-boerse.com/resource/blob/311452/f7a34ce76b13979bfde55fda55b19966/data/handelskalender-2013.pdf).
   Der [Kalender 2018](https://www.cashmarket.deutsche-boerse.com/resource/blob/154422/d8296c92db56d4ae96997246ab54d4ae/data/handelskalender-2018.pdf) nennt **21.5. und 3.10. ausdrücklich als geschlossen**; den Oktobertermin bestätigt [Eurex-Rundschreiben 055/2018](https://www.eurex.com/ex-en/find/circulars/Trading-calendar-Adjustment-for-3-October-2018-Day-of-German-Unity--205366).
   Eine unabhängige Zählung aus dessen Feiertagsliste ergibt am 4.10.2018 **(3,193)**. Wird der 21.5. mitgezählt, entsteht **(3,194)**: passende Erklärung, aber kein Herkunftsnachweis für S.
   Dafür den ersten Wechsel von `S−N=0` auf `+1` im gespeicherten Jahresverlauf bestimmen, insbesondere unmittelbar vor/nach dem 21.5.; den Kalender nicht an S anpassen.

2. **Die 17 Teilbelegungs-Tage:** Quellenlücken sind plausibel, aber weder harmlos noch durch die 50-%-Schwelle bewiesen; die vollständige Datumsliste fehlt im Prompt.
   Trennscharf ist ein **datumsgenauer Xetra-Umsatz-/Ausführungsnachweis aus einer unabhängigen Quelle**, mit Handelsplatzkennung, neben Jahreskalender und späteren Änderungsmitteilungen.
   Positive Ausführungen beweisen Handel; fehlende Zeilen, Nullvolumen oder unveränderte Schlusskurse beweisen keine Schließung. Der [Kalender 2006](https://www.cashmarket.deutsche-boerse.com/resource/blob/311710/f06cb992acd08fb9956006745162ab73/data/handelskalender-2006.pdf) bietet eine konkrete Sollgrundlage für diese Teilgruppe.
   Jeden Tag einzeln als „offen mit Datenlücke“, „belegt geschlossen“ oder „ungeklärt“ ausweisen; für 2001-10-03 und 2002-05-28 keine neue Ausnahme ohne Beleg.

3. **Tatsächliche Leser und Recompute:** Direkter JS-Leser ist der Nicht-Handelstags-Fallback in [app.js:877](C:/dev/SeasonalEdge/landing/js/app.js:877); andere Queries laden die Spalten teilweise nur mit.
   Die TDOY-Topliste beabsichtigt DB-Nutzung, verliert `tdoy` aber zuvor im Builder: [tdom-analyse.html:373](C:/dev/SeasonalEdge/landing/pages/tdom-analyse.html:373), siehe Befund 2.
   Dashboard/Monatszyklus zählen eigene Zeilen ([dashboard.html:472](C:/dev/SeasonalEdge/landing/pages/dashboard.html:472), [monatszyklus.html:405](C:/dev/SeasonalEdge/landing/pages/monatszyklus.html:405)); TDOM-Ereignisse der Backtest-Engine zählen Mo–Fr ([backtest-engine.html:1003](C:/dev/SeasonalEdge/landing/pages/backtest-engine.html:1003)).
   `tdom_stats`/`tdoy_stats` überschreiben Eingangsnummern durch `cumcount`: [tdom_analysis.py:41](C:/dev/SeasonalEdge/shared/tdom_analysis.py:41), [tdoy_analysis.py:38](C:/dev/SeasonalEdge/shared/tdoy_analysis.py:38); Newsletter lesen diese Aggregate ([daily_report.py:176](C:/dev/SeasonalEdge/shared/daily_report.py:176), [weekly_report.py:199](C:/dev/SeasonalEdge/shared/weekly_report.py:199)).
   **Für einen reinen DB-Spalten-Backfill bleibt „kein Recompute“ richtig.** Bei Umstellung der Statistikzählung oder Sitzungsfilter dagegen neu rechnen; `preprocess()` ist zusätzlich ein Nightly-Schreiber, nicht nur ein Leser.

4. **Geschlossene Tage:** Empfehlung für diesen Reparaturschritt: den bestehenden Vertrag präzisieren und behalten — **Anzahl offener Sitzungen bis einschließlich Datum innerhalb des jeweiligen Monats/Jahres**.
   Das bedeutet häufig Vortagswerte, aber nach Periodenwechsel **0**, nicht die letzte TDOM des Vormonats: nachgerechnet 1.1.2026 → `(0,0)`, 1.2.2026 → `(0,21)`. Beleg: [backfill_tdoy.py:65](C:/dev/SeasonalEdge/scripts/backfill_tdoy.py:65).
   Füllzeilen behalten dabei ihre Kursdaten, gelten jedoch nicht als zusätzliche Sitzungen; analytische Leser müssen sie anhand des Kalenders ausschließen.
   `NULL` wäre ein neuer Vertrag mit Anpassung aller Fallbacks; „nicht anfassen“ konserviert widersprüchliche Nummern. Nullvolumen allein ist kein geeigneter Sitzungsfilter.

5. **Schreiben und Nachweis:** Einzelupdates sind technisch möglich, aber rund 25.000 HTTP-Aufrufe erzeugen lange Laufzeit und viele einzeln festgeschriebene Zwischenstände; Laufzeit vor Ort messen.
   Vorzuziehen ist eine freigegebene Änderungsliste und ein transaktionales `UPDATE … FROM` mit eindeutigen Schlüsseln, alten Sollwerten, Trefferprüfung und Abbruch bei Konflikten. [PostgreSQL UPDATE](https://www.postgresql.org/docs/current/sql-update.html)
   RPC-Stapel sind eine Alternative; **jeder PostgREST-Aufruf hat seine eigene Transaktion**, mehrere Stapel werden dadurch nicht gemeinsam atomar. [PostgREST-Transaktionen](https://docs.postgrest.org/en/stable/references/transactions.html)
   Rücklesen allein reicht nicht: zusätzlich exakte Schlüsselmenge, unabhängige Kalenderreferenz, unveränderte Nicht-Zielspalten, geschützten Zeitraum und Wiederholbarkeit prüfen; Schreibkonkurrenz tatsächlich ausschließen.

6. **Grenze 2001:** Für diesen freizugebenden Lauf ist **ab 2001** die sinnvolle Grenze; die Kalendergüte ist eine eigene Voraussetzung, die eine bessere Zählmethode nicht ersetzt.
   Vorherige Werte können falsch sein, aber eine Zählung auf einem ungeprüften Kalender ist noch keine belegte historische Korrektur. [exchange_holidays.py:110](C:/dev/SeasonalEdge/shared/exchange_holidays.py:110)
   Vor 2001 separat berichten und geschützt lassen; die belegte Schließung **3.10.2000** samt Auswirkungen bis Jahresende als eigenen späteren Umfang ausweisen.
   E2 darf diese Grenze nicht über den allgemeinen Backfill umgehen: Dieser schreibt derzeit alle geladenen Jahre. [backfill_tdoy.py:116](C:/dev/SeasonalEdge/scripts/backfill_tdoy.py:116)

7. **Weitere Schreibwege:** Zusätzlich zu E2 schreibt der **Nightly** die Nummern aus `preprocess()` zurück: [nightly_refresh.py:105](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:105); sein Lückenfüller und `fix_missing_days.py` erzeugen Zeilen ohne Nummern.
   Belege: [nightly_refresh.py:276](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:276), [fix_missing_days.py:124](C:/dev/SeasonalEdge/scripts/fix_missing_days.py:124). Beide brauchen E2 oder einen verbindlichen Reparaturschritt.
   Weiterer expliziter SQL-Schreiber: [fix_tdoy_2026_08_glitch.sql:3](C:/dev/SeasonalEdge/scripts/sql/fix_tdoy_2026_08_glitch.sql:3). Der „tdom_trigger“-Fix betrifft dagegen nur Zeitstempel der Statistiktabellen.
   Im geprüften Repo fand ich keinen Nummern berechnenden `prices`-Trigger; live ist das **ungeprüft** und muss lesend über `pg_trigger` plus Funktionsdefinitionen festgestellt werden.

## Weitere Befunde

1. **Hoch — E2 verhindert den nächsten Drift noch nicht.**  
   Der Nightly lädt Yahoo-Daten, verarbeitet sie und schreibt deren Nummern zurück ([nightly_refresh.py:73](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:73)). `preprocess()` zählt ohne vorhandene Spalten weiterhin Zeilen ([yahoo_downloader.py:267](C:/dev/SeasonalEdge/shared/yahoo_downloader.py:267)).  
   E2 braucht diesen Pfad mit explizitem Ticker/Börsenkontext. `append_today_if_missing()` hat dagegen keinen gefundenen Repo-Aufrufer; seine historische Beteiligung am aktuellen Drift ist nicht bewiesen.

2. **Hoch — Die TDOY-Topliste profitiert derzeit nicht vom Backfill.**  
   Der echte Pfad `addTdomColumns → buildTdoyStats` liefert für zwei synthetische Zeilen mit DB-TDOY **195/196** stattdessen **1/2**; unverändert erhaltene Eingangsnummern liefern korrekt 195/196.  
   Ursache: Der Builder übernimmt `tdoy` nicht ([tdom-analyse.html:373](C:/dev/SeasonalEdge/landing/pages/tdom-analyse.html:373)); danach greift die Zeilenzählung ([tdom-analyse.html:828](C:/dev/SeasonalEdge/landing/pages/tdom-analyse.html:828)). Ein Test nur des Statistikhelfers verfehlt diesen Fehler.

3. **Hoch — „Kein Recompute“ bedeutet nicht „Statistiken kalenderkorrekt“.**  
   Die historischen Statistikgruppen zählen Zeilen, während der Daily-Lookup Kalender-Sitzungen zählt ([daily_report.py:512](C:/dev/SeasonalEdge/shared/daily_report.py:512)). Fehlende Sitzungen und Füllzeilen können somit unterschiedliche Tagesnummern bezeichnen.  
   Vor Code festlegen: ausschließlich gespeicherte Metadaten reparieren oder auch diese analytische Inkonsistenz beheben. Im zweiten Fall müssen Rückwärtsnummern, Renditeintervalle und Aggregate gemeinsam geprüft werden.

4. **Mittel — Der Schreibvertrag verwirft gültige Nullzähler.**  
   Onboarding schreibt nur Werte `> 0` ([backfill_new_ticker.py:139](C:/dev/SeasonalEdge/scripts/backfill_new_ticker.py:139)). Eine Kalenderfunktion allein vereinheitlicht deshalb geschlossene Tage vor der ersten Sitzung einer Periode noch nicht.  
   Aufnahme von **0**, Behandlung fehlender Werte und Serialisierung müssen ebenfalls vereinheitlicht werden.

5. **Hoch — E3 prüft bislang weitgehend eine Eigenschaft der Klassendefinition.**  
   `S=A≠N` kann bei diesen Kalenderänderungen ohnehin erst ab einem Differenztag auftreten; die Monatsbedingung folgt ebenfalls aus den beiden Zählern. Das prüft weder die Quellenrichtigkeit von N noch die Klasse `zaehlweise`.  
   Beleg: Klassendefinition und Musterprüfung im [Review-Prompt](C:/dev/SeasonalEdge/docs/review_prompts/2026-10-10_xetra_tdoy_plan.md). Alle Änderungsklassen benötigen einen eigenen Abnahmevertrag; ungeklärte Fälle dürfen nicht durch einen grünen Korrekturblock verschwinden.

6. **Hoch — Fehlende Quelldaten werden bereits als Schließung ausgelegt.**  
   Der Nightly behandelt fehlende Yahoo-Bestätigung als „Börse war zu“ und kann anschließend Vollständigkeit melden ([nightly_refresh.py:261](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:261), [nightly_refresh.py:293](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:293)).  
   Das ist genau die unzulässige Schlussfolgerung hinter dem Oktoberverdacht. Ein fehlender Quellennachweis muss „ungeklärt/fehlend“ bleiben.

7. **Prüfumfang:** Stand `9b0e3ef`; keine Dateien geändert, keine DB-Verbindung oder Writes. Kalenderfälle und Produktionszählung mit Python 3.14, echte JS-Kalender und Frontend-Builder ausgeführt; 2018 zusätzlich unabhängig aus der offiziellen Feiertagsliste gezählt. Serverzahlen wurden als vorgelegte Messungen behandelt.

## Auflagen vor dem Code

- E1 korrigieren: 3.10.2011–2013 offen lassen; feste Sollfälle ergänzen; 2018-Verlauf zur Herkunft des Offsets untersuchen.
- Die 17 Teilbelegungstage vollständig auflisten und datumsgenau prüfen; Quellenlücken nicht zu Feiertagen erklären.
- E2 um Nightly und Lückenfüller erweitern; Nullzähler, Periodenwechsel und Berechnungsfehler verbindlich behandeln.
- Umfang der Leseränderungen festlegen; Toplistenpfad reparieren und Statistik-Recompute daraus ausdrücklich ableiten.
- E3 um unabhängige Sollwerte, vollständige Pagination, exakte Schlüsselmenge, Teil-NULLs und separate Änderungsklassen erweitern.
- E4 mit überprüfter Schreibruhe oder wirksamer Sperre, Konflikterkennung, Trefferzahl, Transaktions-/Wiederaufnahmevertrag und geschütztem Vor-2001-Bestand spezifizieren.
- Produktionspfade einschließlich Serialisierung gegen unabhängige Referenzen prüfen; Mutationen müssen ihre Anker treffen und deterministisch geschrieben werden.
- Andere Börsen anschließend nur lesend untersuchen; die XETRA-Freigabe nicht auf deren historische Kalender übertragen.
