**Noch nicht freigabefähig.** Read-only geprüft; keine Dateien geändert und keine Live-Datenbank angesprochen. Der freigegebene Rechenkern blieb außerhalb des Reviews.

1. **Hoch – Browser und Nightly können unterschiedliche Scores liefern.**  
   [landing/js/decade-compute.js:523](/C:/dev/Seasonaledge/landing/js/decade-compute.js:523), Aufrufer [dashboard.html:2039](/C:/dev/Seasonaledge/landing/pages/dashboard.html:2039) und [ki-saisonalitaet.html:759](/C:/dev/Seasonaledge/landing/pages/ki-saisonalitaet.html:759).  
   `mitHistorie(..., 25)` beschränkt das Nachladen auf 25 Kalenderjahre. Der Vertrag verlangt jedoch die 20 jüngsten **gültigen** Vergleichsjahre; bei Ausschlüssen reichen diese weiter zurück. Nightly und Watchlist laden vollständig. **Reproduziert mit den echten JS-Dateien:** dieselbe synthetische Reihe, Ticker und `as_of=2026-10-09`: Vollhistorie **4,2 aus 20 Jahren**, Nachladepfad **3,1 aus 14 Jahren**. Bei einer längeren ursprünglichen Zeitraumauswahl bleiben außerdem zusätzliche Jahre erhalten – der Regler kann damit weiterhin den Score verändern. Vollhistorie laden oder die Vollständigkeit der benötigten Vergleichsjahre nachweisen.

2. **Hoch – Nachladefehler werden zu scheinbar gültigen Scores.**  
   [landing/js/decade-compute.js:532](/C:/dev/Seasonaledge/landing/js/decade-compute.js:532).  
   Der Fehlerhandler löst das Promise erfolgreich mit den ursprünglichen Kursen auf. **Konkreter Fall:** Elf Jahre sind geladen, der Abruf älterer Kurse scheitert mit HTTP 503; angezeigt wird ein regulärer Score auf verkürzter Basis. Diesen Ablauf habe ich mit einem abgewiesenen Fetch reproduziert: Ergebnis `status: ok`. Bei kürzerer Ausgangsreihe erscheint stattdessen irreführend „nicht berechenbar“. Fehler weiterreichen und als Ladefehler anzeigen.

3. **Hoch – Ein fehlendes Protokoll wird durch `--resume` dauerhaft übersprungen.**  
   [shared/saison_score_betrieb.py:67](/C:/dev/Seasonaledge/shared/saison_score_betrieb.py:67), [scripts/full_scanner_run.py:53](/C:/dev/Seasonaledge/scripts/full_scanner_run.py:53).  
   Scanner und Protokoll werden in getrennten Requests geschrieben; Resume prüft ausschließlich den Scanner. **Fall:** Scanner-Upsert erfolgreich, Protokoll-Insert scheitert. Der erste Lauf meldet korrekt einen Fehler, aber `--resume` überspringt anschließend diesen Ticker und kann erfolgreich enden. Die prospektive Beobachtung fehlt weiterhin. Beide Writes atomar ausführen oder Resume ausdrücklich um die Protokollvollständigkeit ergänzen.

4. **Hoch – Der Nightly zählt Fehler vor dem Saison-Block weiterhin nicht.**  
   [scripts/nightly_refresh.py:110](/C:/dev/Seasonaledge/scripts/nightly_refresh.py:110), [scripts/nightly_refresh.py:142](/C:/dev/Seasonaledge/scripts/nightly_refresh.py:142).  
   Preis-Upsert-Fehler landen nur im Debug-Log; äußere Tickerfehler führen ohne Eintrag in `_FEHLGESCHLAGEN` zum nächsten Ticker. Leere Downloads werden ebenfalls übersprungen. **Fall:** Das Preis-Upsert scheitert, danach wird erfolgreich aus alten Supabase-Kursen ein Scanner-Eintrag mit heutigem `scan_date` geschrieben. Oder ein vorgelagerter Fehler verhindert den Saison-Block vollständig. Beides kann einen grünen Nightly ergeben. Die neue Fehleraggregation muss den gesamten erforderlichen Tickerpfad erfassen.

5. **Mittel – Daily nimmt nicht berechenbare Kandidaten weiterhin auf.**  
   [shared/daily_report.py:549](/C:/dev/Seasonaledge/shared/daily_report.py:549), [shared/daily_report.py:668](/C:/dev/Seasonaledge/shared/daily_report.py:668).  
   Der Precheck verlangt nur Universumszugehörigkeit. `None` wird lediglich **innerhalb derselben MW-Punktzahl** nach hinten sortiert. **Fall:** Ticker A ohne Saison-Score mit MW=4 steht vor Ticker B mit gültigem Saison-Score und MW=3. Im Fallback können sogar Kandidaten ohne auswertbare TDOM-Fenster erscheinen, weil fehlende Fenster MW=0 ergeben. Das widerspricht der Festlegung „Mails lassen nicht berechenbare Ticker weg“. Gültigkeitsprüfung von der bewusst entfernten numerischen Score-Schwelle trennen.

6. **Mittel – Die Daily-Fallzahl stimmt nicht zwingend zu allen angezeigten Renditen.**  
   [shared/daily_report.py:629](/C:/dev/Seasonaledge/shared/daily_report.py:629), [scripts/templates/daily_report.html.j2:121](/C:/dev/Seasonaledge/scripts/templates/daily_report.html.j2:121).  
   Vier Fenster erhalten gemeinsam `n=min(counts)`; die einzelnen Fallzahlen werden beim Aufbau der Anzeige verworfen. **Fall:** O→C basiert auf 240 Beobachtungen, die Folgefenster auf 239. Hinter allen vier Renditen steht unqualifiziert `n=239`. B1 ist jetzt korrekt getrennt, die TDOM-Angabe bleibt aber mehrdeutig. Fallzahlen je Fenster anzeigen oder ausdrücklich „mindestens n“ schreiben.

7. **Mittel – Der Daily-Health-Check akzeptiert weiterhin alte Methoden.**  
   [scripts/daily_health_check.py:334](/C:/dev/Seasonaledge/scripts/daily_health_check.py:334).  
   Der Abruf bestimmt das jüngste Scanner-Datum ohne Methodenfilter. **Fall:** Es existieren aktuelle Altzeilen mit `methode NULL`, aber noch keine `saison_v1`-Zeile. Check 4 meldet trotzdem grün. Das ist ein verbliebener produktiver Leser, obwohl `check_db_completeness` bereits umgestellt wurde.

8. **Mittel – Teilstände zeigen keine Liste fehlender Ticker.**  
   [landing/pages/scanner.html:423](/C:/dev/Seasonaledge/landing/pages/scanner.html:423).  
   Die Zusammenfassung zählt berechenbare und nicht berechenbare vorhandene Zeilen, bildet aber keine Differenzmenge zum erwarteten Universum. **Fall:** 300 von 370 Tickern wurden geschrieben; die übrigen 70 verschwinden vollständig aus Tabelle und Kategorien. Eine Zahl macht die Lücke erkennbar, aber nicht ihre Mitglieder. Plan v2 fordert ausdrücklich die Liste fehlender Ticker. Zusätzlich sollten „verarbeitet“ und „berechenbar“ getrennte Abdeckungen erhalten.

9. **Mittel – Abweichende Wiederholungsergebnisse bleiben unbemerkt.**  
   [shared/saison_score_betrieb.py:70](/C:/dev/Seasonaledge/shared/saison_score_betrieb.py:70).  
   `ignore_duplicates=True` bewahrt richtig den ersten Protokolleintrag, vergleicht ihn aber nicht mit dem neuen Ergebnis. **Fall:** Eine historische Kurskorrektur verändert bei unverändertem `as_of` Hash und Score. Der Scanner wird aktualisiert, das Protokoll bleibt alt, ohne den in Plan v3 zugesagten Abweichungslog. Den bestehenden Eintrag vergleichen und Abweichungen protokollieren.

10. **Niedrig – Die Watchlist verschweigt den Nichtberechenbarkeitsgrund.**  
    [landing/pages/watchlist.html:624](/C:/dev/Seasonaledge/landing/pages/watchlist.html:624).  
    Die Karte zeigt lediglich „nicht berechenbar“, obwohl `ss.grund_code` vorliegt. **Fall:** Eine zu junge Historie und ein unvollständiges laufendes Jahr sehen identisch aus. Außerdem fehlen dort die zugesagten vier Bausteine und die separate Musterkonformität. Die vorhandenen Ergebnisfelder darstellen.

11. **Niedrig – Der SEO-Builder veröffentlicht weiterhin den alten Produkttext.**  
    [seo/programmatic_seo_builder.py:423](/C:/dev/Seasonaledge/seo/programmatic_seo_builder.py:423), [seo/programmatic_seo_builder.py:437](/C:/dev/Seasonaledge/seo/programmatic_seo_builder.py:437).  
    Der Generator enthält weiterhin „KI-Composite-Score“, insbesondere für den Scanner. **Fall:** Der nächste Build erzeugt daraus erneut ein widersprüchliches `llms.txt`, obwohl die Seite bereits Saison-Score heißt. Beide verbliebenen Texte umstellen.

12. **Niedrig – Ein ausschließlich nicht berechenbarer Full-Scan meldet einen Fehler.**  
    [scripts/full_scanner_run.py:188](/C:/dev/Seasonaledge/scripts/full_scanner_run.py:188).  
    `success` zählt ausschließlich berechnete Scores; bei null Erfolgen folgt Exit 2, auch wenn alle Statuszeilen korrekt geschrieben wurden. **Fall:** `--only` für einen jungen Ticker endet trotz erfolgreicher Verarbeitung rot. Das widerspricht „Rechenmangel ist kein Betriebsfehler“. Erfolgreich gespeicherte Nichtberechenbarkeit berücksichtigen.

Zu den acht Prüffragen:

1. **Migration:** Auf dem vorgesehenen Ausgangsschema wiederholbar; die Migration selbst verändert keine Altzeilen. Die neuen Methodenfilter blenden diese aus – Ausnahme Health-Check, siehe Befund 7. Bestehende Scanner-Leserechte bleiben erhalten; das Protokoll entzieht `PUBLIC`, `anon` und `authenticated` die Tabellenrechte. `service_role` verliert UPDATE/DELETE/TRUNCATE; der Trigger verhindert zusätzlich Zeilenänderungen und Löschungen. **`DO NOTHING` benötigt kein UPDATE-Recht**; SELECT und INSERT sind gewährt. Das entspricht der [PostgreSQL-Dokumentation](https://www.postgresql.org/docs/current/sql-insert.html) und dem [PostgREST-Konfliktmodus](https://docs.postgrest.org/en/stable/references/api/tables_views.html#upsert). `UNIQUE(ticker, scan_date)` steht bereits in [create_market_tables.sql:76](/C:/dev/Seasonaledge/scripts/create_market_tables.sql:76); `NOTIFY pgrst` ist vorhanden. **Der tatsächliche Live-Schema- und Rollenstand wurde nicht verifiziert.**

2. **Deploy/Migration:** Neuer Code vor Migration scheitert beim Scanner-Request laut an fehlenden Spalten; dieser Request schreibt nicht teilweise. Vorherige Preis-/Statistik-Writes können dennoch bereits erfolgt sein. Migration vor ausschließlich altem Code bleibt zunächst kompatibel: neue Altzeilen haben `methode NULL`. **Parallelbetrieb ist gefährlich:** Ein alter Writer kann eine bereits neue Zeile desselben Tickers/Tages treffen und deren Score/Signal überschreiben, während `methode`, Status und Bausteine erhalten bleiben. Der Constraint in [scanner_saison_score_2026_10.sql:29](/C:/dev/Seasonaledge/scripts/sql/scanner_saison_score_2026_10.sql:29) verhindert das nicht. Alte Writer vor Aufnahme der neuen Writes beenden.

3. **Stille Fehler:** Innerhalb des neuen Python-Betriebsmoduls werden Abruf-/Schreibfehler weitergereicht und im Saison-Block rot aggregiert. Insgesamt aber **nicht lückenlos**, siehe Befunde 2–4. Auch der Weekly-Leser wandelt Abruffehler in eine leere Ergebnisliste um.

4. **Zwillinge:** Gleiche Quelle `prices` und grundsätzlich passende Bereinigung; Watchlist und Nightly verwenden Vollhistorie. **Keine garantierte Gleichheit** für Dashboard/KI-Seite wegen Befunden 1–2. Top-N-, Glättungs- und Methodenregler gehen nicht mehr direkt in den Score ein; die Zeitraumunabhängigkeit ist noch nicht erfüllt.

5. **Scanner-Lader:** `score.desc.nullslast` ist [gültige PostgREST-Syntax](https://docs.postgrest.org/en/stable/references/api/tables_views.html#ordering). Für aktuell **370 Einträge in `tickers.json`** reicht 2000; ein niedrigeres serverseitiges Maximum bleibt maßgeblich. Der Lader zeigt den jüngsten vorhandenen Methoden-Teilstand, **keinen älteren vollständigen Lauf**. Das entspricht Plan v2; die fehlende Tickerliste muss ergänzt werden.

6. **Mails:** Keine numerische Saison-Score-Schwelle mehr; Weekly filtert korrekt auf `status ok`. Daily hat die Befunde 5–6. Die abschließende Daily-Sortierung verwendet weiterhin zuerst den kombinierten technischen Gesamtwert, nicht ausschließlich MW und Saison-Score. Saison-Bullish/Bearish-Urteile sind entfernt; andere Daily-Texte enthalten weiterhin „Bullish-Bias“, etwa [daily_report.py:1252](/C:/dev/Seasonaledge/shared/daily_report.py:1252), unabhängig vom Saison-Score.

7. **Texte/EN:** In den geänderten Saison-Score-Texten fand ich keine neue Vorhersage- oder Wahrscheinlichkeitszusage; die Validierungszahlen stehen im Scanner. Keine fehlenden EN-Schlüssel bei den geprüften `data-i18n`-Attributen und literalen Übersetzungsaufrufen der geänderten Dateien. SEO-Rest siehe Befund 11. Das ausdrücklich ausgenommene [Videoskript:9](/C:/dev/Seasonaledge/scripts/video/scripts/qqq-truepath-ki-saisonalitaet.json:9) enthält weiterhin „KI sagt +40 %“; Blog-/Video-Alttexte sind damit nicht bereinigt.

8. **Reste:** Keine aktiven Importe der gelöschten Module und keine verbliebenen Aufrufe von `computeKiScore`, `store_scanner_results` oder `upsert_scanner_results` gefunden. Relevanter Leserrest: Health-Check. `ki_scores` bleibt im ursprünglichen Schema und in der Security-Prüfliste; `top_ki_scores` bleibt als interner Funktionsname mit neuer Implementierung erhalten.

Kurz bestätigt: explizites `signal=None`, Speicherung nicht berechenbarer Scanner-Zeilen, Methodenfilter in Hauptleser/Resume, Weekly-k/n aus B1, Ladekennungen gegen Ticker-Rennen und Cache-Version **v11 → v12**. **22 geänderte JS-/Inline-Skripte** ließen sich syntaktisch parsen; die geprüften JSON-LD-Blöcke ebenfalls. Die Python-Wächter konnten hier nicht starten, weil die verfügbaren `python`-/`py`-Launcher nicht ausführbar waren.

**FREIGABE: nein**
