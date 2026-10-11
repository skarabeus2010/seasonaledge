# Antwort Codex Runde 7 — P2 Schreiber (2026-10-10)

Prompt: [2026-10-10_xetra_tdoy_plan_v7.md](2026-10-10_xetra_tdoy_plan_v7.md). model: gpt-6.1-sol

**Urteil**

**P2 v7 ist noch nicht freigabefähig.** K1 und die sofortige Aktivierung nach K2 sind tragfähig; historische Schreibgrenzen, Fehlerweitergabe und K6 brauchen Ergänzungen.
Read-only geprüft auf `2397c78`; nichts geschrieben. `verify_handelstag_nummern.py`: **86/86 bestanden**. Mutationstests wegen Schreibverbot nicht ausgeführt.

**Antworten**

1. **K2: sofort aktiv, ohne Schalter.** Kein weiterer erreichbarer Statistik-/Newsletterleser der Preisnummern gefunden.
   Der Header bleibt die bekannte sichtbare Ausnahme ([app.js:878](/C:/dev/SeasonalEdge/landing/js/app.js:878)).
   `buildTdoyStats` liest zwar `tdoy`, doch der produktive Vorlauf entfernt die Spalte ([tdom-analyse.html:373](/C:/dev/SeasonalEdge/landing/pages/tdom-analyse.html:373), `:1241`).
   Gegenprobe mit den echten JS-Funktionen: unterschiedliche DB-TDOYs ergeben nach diesem Vorlauf identische Statistiken.
   K2 gilt, solange P2 die Nummern ausschließlich für Schreibdatensätze berechnet und keine Analyse-Builder verändert.

2. **K3: einzelne `update()`-Requests sind für eine begrenzte Reparatur akzeptabel.**
   Das sind einzelne Transaktionen; eine Schleife in „Stapeln“ erzeugt keine gemeinsame Transaktion.
   Nur geänderte Nummern schreiben, eindeutige Ticker-/Datumsfilter verwenden und tatsächliche Änderungen bestätigen.
   Fehler oder null Treffer müssen einen Fehlschlag ergeben ([backfill_tdoy.py:125](/C:/dev/SeasonalEdge/scripts/backfill_tdoy.py:125)).
   Die P5-RPC bleibt der Weg für die historische Massenkorrektur.

3. **K5 gehört in P2**, weil derselbe Lückenfüller und dessen Erfolgsvertrag geändert werden.
   Leeres Yahoo-Ergebnis beweist keine Schließung ([nightly_refresh.py:238](/C:/dev/SeasonalEdge/scripts/nightly_refresh.py:238)).
   „Ungeklärt“ braucht Datumsliste, eigene Zählung, Ausschluss aus „vollständig“ und eine sichtbare Monitoring-Auswertung.
   Lade-/Upsertfehler bleiben Fehler; sie dürfen nicht bloß „ungeklärt“ werden.

4. **K6 braucht Mengennachweis, unabhängige Sollwerte, Fehlerfälle und die aufrufenden Programme.**
   Zusätzlich Preis-Upserts ohne Nummern ausdrücklich abgrenzen: [backfill_ohlc.py:73](/C:/dev/SeasonalEdge/scripts/backfill_ohlc.py:73), [backfill_log_return.py:47](/C:/dev/SeasonalEdge/scripts/backfill_log_return.py:47), [fix_ohlc_adjustment.py:76](/C:/dev/SeasonalEdge/scripts/fix_ohlc_adjustment.py:76).
   Diese berechnen heute keine Nummern; K6 muss ihr Verhalten gegenüber bestehenden Nummern berücksichtigen.
   Außerdem den historischen SQL-Schreiber als solchen kennzeichnen (`scripts/sql/fix_tdoy_2026_08_glitch.sql:3`).
   K4: Löschen des unreferenzierten Bulk-Loaders ist vertretbar; dann seine Entfernung mitprüfen.

**Befunde**

- **[P1] Die P5-Grenze ist über andere Wege umgehbar.**
  `check_db_completeness --fix` startet bei veralteten Tickern `backfill_new_ticker.py` ([check_db_completeness.py:651](/C:/dev/SeasonalEdge/scripts/check_db_completeness.py:651)).
  Dieser lädt und upsertet die ganze Historie ([backfill_new_ticker.py:99](/C:/dev/SeasonalEdge/scripts/backfill_new_ticker.py:99), `:154`).
  Nach K1 korrigiert damit eine automatische Tail-Reparatur historische Nummern vor P5.
  Auch K3 begrenzt bisher nur Jahre/Status: `--schreiben` ohne Ticker-/Datumsgrenzen könnte weiterhin alle zulässigen Historien ändern.

- **[P1] K6 kann korrekte Payloads bestätigen, obwohl nichts erfolgreich geschrieben wurde.**
  Onboarding fängt Batchfehler ab und liefert dennoch `ok=True` (`backfill_new_ticker.py:157`, `:162`).
  Gegenprobe: abgelehnter Upsert → **`ok=True`, `rows=0`**.
  `fix_missing_days` meldet nach abgefangenen Batchfehlern die vorbereitete Zeilenzahl als Ergebnis ([fix_missing_days.py:145](/C:/dev/SeasonalEdge/scripts/fix_missing_days.py:145), `:149`).
  Der Onboarding-Aufrufer warnt bei einem gescheiterten Kindprozess und endet trotzdem mit 0 ([onboard_ticker.py:95](/C:/dev/SeasonalEdge/scripts/onboard_ticker.py:95), `:120`).

- **[P2] K5s zusätzliche Zahl reicht für den bestehenden Betriebsvertrag nicht.**
  Gegenprobe: fehlende SPY-Sitzungen + Yahoo `None` → „Alle Ticker vollständig“, ein Erfolg, keine Fehler.
  Erfolgszählung und `refresh_log` müssen den neuen Zustand übernehmen (`nightly_refresh.py:305`, `:443`).
  Die Health-Auswertung liest keine neue Ungeklärt-Zahl und toleriert einzelne erfolglose Ticker bis zur 95-%-Grenze ([daily_health_check.py:172](/C:/dev/SeasonalEdge/scripts/daily_health_check.py:172), `:208`).

- **[P2] K6 prüft bisher hauptsächlich die Weitergabe derselben Produktionsrechnung.**
  Ein gemeinsamer Fehler in `handelstag_nummern` könnte Schreiber und Erwartung gleichzeitig verändern.
  Die unabhängige Referenz existiert bereits ([verify_handelstag_nummern.py:44](/C:/dev/SeasonalEdge/scripts/verify_handelstag_nummern.py:44), `:79`); sie muss verbindlicher Teil der Abnahme bleiben.
  Außerdem fehlen Soll-Zeilenmenge, Pagination/Batchgrenzen, gemischte erlaubte/verbotene Jahre und Fehler nach bereits vorbereiteten Nummern.

**Auflagen vor dem Code**

1. Historische Grenzen für **alle** Einstiegspfade festlegen: Tail-Reparatur darf keine Vollhistorie umnummerieren; neue Historien und bestehende Zeilen unterscheiden.
2. K3-Schreiben ausdrücklich auf Ticker, Datumsbereich und eine begrenzte Änderungsmenge beschränken; sämtliche Grenzen vor dem ersten Schreibrequest prüfen.
3. Fehler bis Rückgabestatus und Prozess-Exit weiterreichen; erfolgreiche Zeilen ausschließlich nach bestätigtem Schreiben zählen.
4. K5 für vollständiges, teilweises und leeres Yahoo-Ergebnis spezifizieren; Erfolgszählung, Log und Health-Auswertung gemeinsam ergänzen.
5. K6: exakte Sollmenge und beide Spalten einschließlich 0 prüfen; Zuordnungs-/Bereichsfehler, Batchfehler, null Update-Treffer und die tatsächlichen CLI-Aufrufer testen.
6. Schreiberwächter samt unabhängiger Nummernreferenz ins Deploy-Gate aufnehmen. Mutationen über `_atomar_schreiben`, mit gültigem Anker und erwartetem fachlichem Befund; Ausnahmen zählen nicht als Fang.
