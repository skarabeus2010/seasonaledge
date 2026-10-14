**FREIGABE (Plan): B1 nein · B2 nein · B3 ja.**

Read-only auf `4732437` geprüft, einschließlich der drei bisherigen Antworten. Keine Dateien geändert. Serverbefunde und Deployment-Zeitpunkt übernehme ich aus deinem Bericht; keine Betriebsprüfung wiederholt.

1. **B1 — Sperrkonzept passt; Reparaturfreigabe und Snapshot-Reihenfolge noch präzisieren.**

   Die Verlustpfade sind bestätigt: beispielsweise [compute_options_skew.py:1240](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1240) und [backfill_skew_massive.py:854](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:854). Frisches Lesen unter gemeinsamer Sperre, Abbruch bei defekter History und tickerweises Anwenden vorberechneter Ergebnisse schließen diese Lücke sinnvoll.

   Zwei Punkte verhindern die Freigabe der vorliegenden Fassung:

   - **Den freigegebenen Diff zwischen den beiden Läufen verbindlich referenzieren.** „Muss dem gezeigten gleichen“ beschreibt das Ziel, aber `--schreiben` allein benennt keinen zuvor freigegebenen Bericht ([Plan:63](C:/dev/Seasonaledge/docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3.md:63)). Beispielsweise `--schreiben --freigabe-datei <bericht.json>` vorsehen. Unter der Sperre den neu berechneten Diff einschließlich Ticker, Bereich, Ausgangswerten und neuer RV gegen genau dieses Artefakt prüfen; Abweichung bedeutet Abbruch. Ein Vergleich mit einer erst im Schreiblauf erzeugten Vorschau genügt nicht. Fixture: geänderte Zielzeile oder geänderte RV zwischen Trocken- und Schreiblauf.
   - **Snapshot bereits in B1 unter die Sperre verlegen.** „Ab B3 Rang + Snapshot“ und „Sperre bis nach dem Snapshot“ widersprechen sich ([Plan:42](C:/dev/Seasonaledge/docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v3.md:42)). Heute wird der Snapshot sogar vor dem History-Lesen geschrieben ([compute_options_skew.py:1223](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1223)). Festlegen: B1 schreibt History → Snapshot unter derselben Sperre; B3 ergänzt dort die Rangrechnung. Bei defekter History bleibt damit auch der Snapshot unangetastet.

   Weitere Umsetzungsdetails: `n_purge` erst beim Anwenden aus dem frischen Bestand bestimmen. Die Reparatur-Invariante vergleicht den frisch gesperrten Ausgangsstand mit dem Ergebnis; zwischenzeitliche legitime Cron-Ergänzungen außerhalb des Reparaturbereichs sollen erhalten bleiben. „Ohne `--schreiben` nichts geschrieben“ auf **Produktionsdaten** beziehen, damit der verlangte Prüfbericht trotzdem gespeichert werden darf.

   Für den stillgelegten Marketdata-Schreiber bevorzuge ich die angebotene Entfernung. Blogkorrektur bleibt freigegeben.

   **FREIGABE (Plan): B1 nein**, bis die beiden Punkte eindeutig festgelegt sind.

2. **B2 — GEX-Kern freigabefähig; die neu einbezogenen Erzeuger brauchen denselben Session-Schutz.**

   Session als Bewertungsdatum, Ausschluss `exp ≤ S`, Archivtrennung und gekennzeichneter Altarchiv-Fallback passen. Die bisherigen Uhrabhängigkeiten stehen in [snapshot_gex_massive.py:97](C:/dev/Seasonaledge/scripts/snapshot_gex_massive.py:97) und [Zeile 124](C:/dev/Seasonaledge/scripts/snapshot_gex_massive.py:124).

   Zwei Lücken bleiben:

   - **EOD-Schutz auch für Key Levels und IV-Surface.** Beide laden aktuelle Chains, haben derzeit aber keinen `pruefe_eod_fenster`-Schutz: [compute_key_levels.py:203](C:/dev/Seasonaledge/scripts/compute_key_levels.py:203), [compute_iv_surface.py:193](C:/dev/Seasonaledge/scripts/compute_iv_surface.py:193). Nur `letzte_session()` einzubauen würde während der Handelszeit aktuelle Intraday-Daten mit dem Datum der Vorsession veröffentlichen. Je Erzeuger Session einmal bestimmen und Schreibläufe bereits vor dem Datenabruf gegen das EOD-Fenster prüfen; lesende Läufe bleiben erlaubt. Entsprechende Fixtures für alle drei Erzeuger.
   - **Key Levels darf alte GEX-Werte nicht als aktuelle Session ausgeben.** `_load_gex()` verwirft bislang sämtliche Datumsmetadaten und übernimmt Flip/Walls ungeprüft ([compute_key_levels.py:148](C:/dev/Seasonaledge/scripts/compute_key_levels.py:148)). Nach einem ausgefallenen GEX-Lauf würden alte Walls mit neu berechnetem Max-Pain unter `session=S` erscheinen. Nur GEX mit passenden Session-/Bewertungsmetadaten übernehmen; andernfalls GEX-Felder auslassen und den Grund melden. Fixture: GEX der Vorsession, aktuelle Chain.

   Für den Health-Check die bestehenden Abdeckungsprüfungen erhalten: Ein aktuelles Datum darf die rote Bewertung bei zu wenigen Tickern nicht aufheben ([daily_health_check.py:434](C:/dev/Seasonaledge/scripts/daily_health_check.py:434)). „Alter Stempel“ darf eine bereits rote Bewertung ebenfalls nicht auf gelb verbessern.

   Die Uhrzeit-Gegenprobe muss identische eingefrorene Chain-/Spot-Eingaben verwenden und Laufzeitfelder vom Gleichheitsvergleich ausnehmen. Sie belegt dann die Unabhängigkeit der Berechnung von der Startzeit.

   **FREIGABE (Plan): B2 nein**, bis EOD-Schutz und GEX-Sessionprüfung ergänzt sind.

3. **B3 — die offenen Vertragsdetails aus v2 sind geschlossen.**

   Metrikweises `n`, Sessionprüfung nach Wertefilterung, inklusive Fenstergrenze, Rundung, eigenständige JS-Referenz und vollständige Rangwerte im Snapshot ergeben einen konsistenten Vertrag. Die heutigen Schwachstellen liegen tatsächlich in [skew.html:244](C:/dev/Seasonaledge/landing/pages/skew.html:244) und [skew.html:484](C:/dev/Seasonaledge/landing/pages/skew.html:484).

   Bei der Umsetzung „gültig“ ausdrücklich als endliche numerische Werte behandeln; `null`, boolesche Werte und nicht endliche Zahlen dürfen weder in Python noch durch JS-Typumwandlung zu Messwerten werden. Den Put-Zeta-Fallback ausdrücklich als `(put_iv − iv_atm)·100` festhalten.

   **FREIGABE (Plan): B3 ja**, mit der vorgesehenen Abhängigkeit von der fertig geprüften B1-Sperre. Die Bestandsreparatur und spätere Code-/Deployment-Freigaben sind damit nicht vorweggenommen.
