**FREIGABE (Plan): nein für das Gesamtpaket.** R1b/R1d, R4 und R5 sind freigabefähig. Bei R1c und R2 bleiben konkrete Lücken; R3 braucht noch eine eindeutige Ausgabe- und Sperrspezifikation.

Read-only geprüft auf `d944a26`, einschließlich Diagnosecode und Antwort 1. Keine Dateien geändert, keine Serverabfrage ausgeführt. Die Diagnosezahlen übernehme ich aus deinem Bericht.

1. **R1 — Erzeuger ja, Bestandsreparatur noch nein.**

   Die Trennung gespeicherter Returns für RV und unveränderter Schlusskurse für Spot passt. Im Massive-Backfill dient der betreffende Lader tatsächlich nur dem Spot: [scripts/backfill_skew_massive.py:198](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:198). Bei Intermarket müssen **beide** Pfade umgestellt werden: Bewegung und SPY-RV, [shared/intermarket.py:64](C:/dev/Seasonaledge/shared/intermarket.py:64), [shared/intermarket.py:78](C:/dev/Seasonaledge/shared/intermarket.py:78).

   Zwei Vertragsdetails ausdrücklich erhalten:
   - `lade_closes` liefert bisher **`(daten, closes)`**, nicht ausschließlich `closes`: [shared/data.py:216](C:/dev/Seasonaledge/shared/data.py:216).
   - Datum, Close und Return müssen gemeinsam auf die Session gekappt werden; ungültige Returns bleiben als Lücke erhalten. Die bisherige Session-Kappung steht in [scripts/compute_options_skew.py:333](C:/dev/Seasonaledge/scripts/compute_options_skew.py:333).

   **R1c ist mit dem vorhandenen Backfill noch nicht gezielt ausführbar.** `--ticker` begrenzt nur den Ticker; die Schleife bearbeitet dessen gesamte Historie einschließlich Feldlöschungen. Datumsgrenzen fehlen: [scripts/backfill_skew_vrp.py:136](C:/dev/Seasonaledge/scripts/backfill_skew_vrp.py:136), [scripts/backfill_skew_vrp.py:314](C:/dev/Seasonaledge/scripts/backfill_skew_vrp.py:314). Ergänzen:
   - expliziter Reparaturbereich, abgeleitet aus den tatsächlich betroffenen 21-Return-Fenstern;
   - vollständiger Zeilendiff einschließlich gesetzter/gelöschter Werte, nicht nur die bisherigen fünf größten Abweichungen;
   - abgestimmter Umgang mit dem vorhandenen Verteilungs-Gate: Mindestens 200 Zeilen und positives VRP-Mittel sind für diese kleine Einzelreparatur kein geeigneter Korrektheitsnachweis ([scripts/backfill_skew_vrp.py:72](C:/dev/Seasonaledge/scripts/backfill_skew_vrp.py:72), [scripts/backfill_skew_vrp.py:259](C:/dev/Seasonaledge/scripts/backfill_skew_vrp.py:259)).

   R1d passt. Den Diagnosecode aber nicht unverändert übernehmen: Er prüft Endlichkeit nur für den Return, nicht für beide Kurse; außerdem zählt er nicht endliche Returns als ungültigen Kurs: [scripts/research/basisabweichung_diagnose.py:33](C:/dev/Seasonaledge/scripts/research/basisabweichung_diagnose.py:33). Fehler und unvollständige Abdeckung müssen sichtbar bleiben.

   **FREIGABE (Plan): R1b/R1d ja; R1c nein.** Kein Neuladen der ETHA-Kurse ist die richtige Entscheidung; „damals gehandelte Preise“ bleibt dabei eine Annahme über die Datenherkunft.

2. **R2 — Session-Stempel richtig, Berechnungsdatum noch offen.**

   GEX verwendet den Lauftag auch zur Berechnung von Restlaufzeit und `T`: [scripts/snapshot_gex_massive.py:113](C:/dev/Seasonaledge/scripts/snapshot_gex_massive.py:113), [scripts/snapshot_gex_massive.py:124](C:/dev/Seasonaledge/scripts/snapshot_gex_massive.py:124). Ein Wochenendlauf kann daher unter derselben Freitags-Session andere berechnete Werte archivieren. **Die einmal ermittelte Session muss auch Bewertungsdatum für DTE/T und die darauf beruhende Laufzeitselektion sein.** Nur das Etikett zu ändern reicht für „Stand: Session (EOD)“ nicht.

   Außerdem existiert `--snapshot <datum>` beim **Vergleichsleser**, nicht beim Massive-Schreiber: [scripts/compare_flashalpha_gex.py:240](C:/dev/Seasonaledge/scripts/compare_flashalpha_gex.py:240), [scripts/snapshot_gex_massive.py:176](C:/dev/Seasonaledge/scripts/snapshot_gex_massive.py:176). Im Plan als Archiv-*Lesemodus* bezeichnen.

   Der eingecheckte Workflow startet Massive: [.github/workflows/gex_snapshot.yml:31](C:/dev/Seasonaledge/.github/workflows/gex_snapshot.yml:31). Für `snapshot_gex.py` fand ich keinen weiteren eingecheckten Aufrufer; zusätzliche Serverjobs sind damit nicht ausgeschlossen. „Nur Kommentar“ ist erst nach dieser Betriebsprüfung belastbar.

   **FREIGABE (Plan): nein**, bis das Bewertungsdatum mit umfasst ist. Archivtrennung und Frischeprüfung passen.

3. **R3 — Rechenregeln weitgehend vollständig; Sperre jetzt erforderlich.**

   **Die Sperre gehört vor R1c, nicht erst in Phase 3.** Der bekannte Überschreibverlust ist bereits dokumentiert: [scripts/backfill_supervisor.sh:4](C:/dev/Seasonaledge/scripts/backfill_supervisor.sh:4). Atomarer Dateiersatz verhindert keine konkurrierenden Änderungen: [shared/atomic_json.py:56](C:/dev/Seasonaledge/shared/atomic_json.py:56).

   Deshalb Sperrhelfer und Umstellung aller Schreiber in Paket 1 vorziehen. Auch `backfill_skew_history.py` einschließen: [scripts/backfill_skew_history.py:150](C:/dev/Seasonaledge/scripts/backfill_skew_history.py:150). Eine separate, gemeinsam gemountete Sperrdatei verwenden; beim Cron bis nach Veröffentlichung des Snapshots halten. Bei langen Backfills Ergebnisse vorberechnen und unter Sperre die aktuelle History erneut lesen und zusammenführen — keine alte Gesamtstruktur zurückschreiben.

   Noch präzisieren:
   - **`n` je Metrik**, da die gültigen Stichproben unterschiedlich groß sein können; etwa `rr:{n,rank,pctl}`, entsprechend für die anderen Metriken.
   - Fenster ausdrücklich **`S−W ≤ date ≤ S`**, sortiert und datumseindeutig.
   - Session-Konsistenzprüfung auch im Mailleser.
   - JS-Referenz an die neue Spezifikation anpassen. Unverändert kopierter Altcode enthält gerade die zu beseitigenden Fehler: [landing/pages/skew.html:241](C:/dev/Seasonaledge/landing/pages/skew.html:241), [landing/pages/skew.html:477](C:/dev/Seasonaledge/landing/pages/skew.html:477).

   Zwei atomare Schreibvorgänge sind keine gemeinsame Transaktion. Die vorgeschlagene Reihenfolge ist dennoch geeignet, weil die Rangwerte vollständig im Snapshot stehen. Ein Abbruch zwischen beiden Schreibvorgängen sollte als Fixture abgedeckt werden.

   **FREIGABE (Plan): nein**, bis diese Vertragsdetails und die vorgezogene Sperre feststehen.

4. **R4 — FREIGABE (Plan): ja.**

   Mailblock entfernen, Folgefehler dokumentieren, Ereignisliste gegen Einspeisung aus `earnings_events` absichern. Die Abgrenzung passt: [shared/daily_report.py:948](C:/dev/Seasonaledge/shared/daily_report.py:948).

5. **R5 — FREIGABE (Plan): ja.**

   Zusätzlich zu den genannten Untertiteln die Radarlegende einbeziehen: Dort bleibt „Y-Achse (IV-Rank)“ fest verdrahtet, [landing/pages/skew.html:451](C:/dev/Seasonaledge/landing/pages/skew.html:451). Initiales HTML, Umschalten und Sprachwechsel gemeinsam prüfen.

Die Paketaufteilung passt **mit vorgezogener Schreibsperre und erweitertem Reparaturmodus vor R1c**. Der Wirkungsbericht auf eingefrorenen Eingaben ist sinnvoll; für Paket 1 zusätzlich RV/VRP alt–neu und GEX-Session/Bewertungsdatum ausweisen.
