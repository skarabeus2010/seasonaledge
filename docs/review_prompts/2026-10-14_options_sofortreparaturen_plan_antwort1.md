**R1a ist fachlich sofort freigabefähig. R2–R5 sind sinnvoll, aber v1 braucht vor der Umsetzung die unten genannten Präzisierungen, insbesondere bei R3.**

Geprüft wurde read-only: `HEAD = origin/master = d944a26`. Keine Dateien geändert, keine Serverdiagnose ausgeführt. Die ETHA-Datenwerte übernehme ich aus deinem Befund; bestätigt ist der verursachende Codepfad.

1. **R1: `log_return` bevorzugen, Spot getrennt erhalten.**

   Der Nightly lädt die vollständige Reihe, berechnet darauf die Daten und schreibt nur das jüngste Sieben-Tage-Fenster zurück. Das stützt die vermutete Mischung verschiedener Adjustierungsstände: [scripts/nightly_refresh.py:77](C:/dev/Seasonaledge/scripts/nightly_refresh.py:77), [scripts/nightly_refresh.py:93](C:/dev/Seasonaledge/scripts/nightly_refresh.py:93). Der RV-Pfad lädt dagegen ausschließlich `date,close`: [shared/data.py:181](C:/dev/Seasonaledge/shared/data.py:181).

   Empfehlung: einen gemeinsamen Datenzugriff für Datum, Schlusskurs und gespeicherten Return schaffen; RV aus validierten `log_return` berechnen, `last_close` unverändert für Spot verwenden. Fehlende oder nicht endliche Returns dürfen weder übersprungen noch still aus den gemischten Schlusskursen ersetzt werden. `rv_aus_returns` ist bereits vorhanden, benötigt für direkte DB-Werte aber eine explizite Prüfung auf NaN/Inf: [shared/realized_vol.py:85](C:/dev/Seasonaledge/shared/realized_vol.py:85).

   **Die vorgeschlagene Rückrechnung enthält eine Richtungsfalle:**  
   `exp(log_return) · close_vorher / close_heute ≈ 1/3` passt zur Anpassung des neuen Kurses auf die alte Basis. Um ältere Kurse auf die jüngste Basis zu bringen, müssten sie mit dem Kehrwert, hier etwa **3**, multipliziert werden. Eine automatische Reparatur anhand einer Abweichungsschwelle würde außerdem Datenfehler und Kapitalmaßnahmen vermischen. Deshalb keine versteckte Änderung von `lade_closes`.

   R1a ergänzen um:
   - einen Vorgänger vor dem Zweijahresfenster, vollständige Pagination und ausgewiesene Abdeckung;
   - fehlende/ungültige Returns sowie Kurslücken separat;
   - beide Faktoren eindeutig benennen: beobachteter Basissprung und Korrekturfaktor;
   - Treffer zunächst als **Basisabweichungen**, nicht automatisch als bestätigte Splits behandeln.

   **Weitere betroffene Pfade:** [scripts/backfill_skew_vrp.py:125](C:/dev/Seasonaledge/scripts/backfill_skew_vrp.py:125), [scripts/backfill_skew_massive.py:198](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:198) und [shared/intermarket.py:64](C:/dev/Seasonaledge/shared/intermarket.py:64). Live und Options-Backfill müssen dieselbe RV-Regel erhalten.

   Für R1c: betroffene Fenster gezielt neu rechnen; falls das nicht verlässlich geht, RV/VRP leeren und den Grund speichern. Ein bloßes Ungültigkeitskennzeichen genügt nur, wenn alle Leser es beachten. Ein Voll-Backfill kann historische Schlusskurse als damalige Spot-Anker verändern; deshalb vorab prüfen, bevor damit Options-IV rekonstruiert wird. Einmaliger Backfill allein verhindert die Wiederholung beim nächsten Split nicht.

2. **R2: Session-Stempel ja; Altarchiv zunächst erhalten, neue Dateien eindeutig abgrenzen.**

   `pc_ratio.date` sollte dieselbe einmal ermittelte Session wie `out.session` verwenden: [scripts/compute_options_skew.py:1204](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1204). `generated` bleibt Laufdatum.

   Bei GEX betrifft `stamp` Summary, Profile und Archiv gemeinsam: [scripts/snapshot_gex_massive.py:231](C:/dev/Seasonaledge/scripts/snapshot_gex_massive.py:231). Zusätzlich den EOD-Zeitwächter aufnehmen: `letzte_session()` allein verhindert nicht, dass ein manueller Intraday-Snapshot fälschlich als vorheriges EOD beschriftet wird.

   **Archivleser existiert:** [scripts/compare_flashalpha_gex.py:118](C:/dev/Seasonaledge/scripts/compare_flashalpha_gex.py:118) lädt `<Datum>.json` und übernimmt dessen `date`. Eine pauschale Migration „minus ein Tag“ ist wegen Wochenenden, Feiertagen und unterschiedlichen Laufzeiten ungeeignet.

   Empfehlung: Altdateien unverändert erhalten, neue Session-Dateien in einem getrennten Archivpfad beziehungsweise einer Version ablegen und den Vergleichsleser anpassen. Nur ein Hinweis im bisherigen Ordner reicht nicht: Beim Wechsel können alte Lauftag-Dateien mit neuen Session-Dateien kollidieren. Eine spätere Migration braucht belegbare Laufzeitdaten und eine Kollisionsregel.

   Weitere Stellen: GEX-Frischeprüfung [scripts/daily_health_check.py:431](C:/dev/Seasonaledge/scripts/daily_health_check.py:431), alternativer Schreiber [scripts/snapshot_gex.py:107](C:/dev/Seasonaledge/scripts/snapshot_gex.py:107). `/options-flow` liest das P/C-Objekt, verwendet dessen Datum derzeit aber nicht ausdrücklich: [landing/pages/options-flow.html:260](C:/dev/Seasonaledge/landing/pages/options-flow.html:260).

3. **R3: Eine Produktionsrechnung im Cron – für alle drei Fenster.**

   Vier skalare Jahreswerte reichen für die vorhandene Seite nicht. Empfehlung: im Cron je **92/183/365 Tage** Rank und Percentile berechnen und mit Session, Fenster und Stichprobengröße veröffentlichen. Mail liest 365 Tage; die Seite liest das ausgewählte Fenster. Auch die Call-/Put-Skew-Ansicht benötigt ihre Kennzahlen: [landing/pages/skew.html:351](C:/dev/Seasonaledge/landing/pages/skew.html:351).

   Vor Umsetzung ausdrücklich festlegen:

   - **Fensteranker:** Session statt Browser-Uhr. Aktuell nutzt `_normHist` `Date.now()`, nicht die Session: [landing/pages/skew.html:241](C:/dev/Seasonaledge/landing/pages/skew.html:241).
   - **IV-Definition:** Die Seite rankt das Mittel aus Put-/Call-IV, **nicht ATM-IV**: [landing/pages/skew.html:470](C:/dev/Seasonaledge/landing/pages/skew.html:470).
   - **Session-Regel nach metrikspezifischer Filterung prüfen.** Aktuell kann das Entfernen eines fehlenden letzten Skew-Werts wieder einen älteren Wert nachrücken lassen: [landing/pages/skew.html:477](C:/dev/Seasonaledge/landing/pages/skew.html:477).
   - **Rundung:** Python `round` und JS `Math.round` unterscheiden sich bei Halbwerten.
   - **Schreibreihenfolge:** erst History zusammenführen, dann daraus Kennzahlen berechnen, anschließend veröffentlichen. Der aktuelle Snapshot wird vorher geschrieben: [scripts/compute_options_skew.py:1221](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1221).

   JS kann als Testreferenz erhalten bleiben; in Produktion lesen beide Oberflächen dieselben Ergebnisse. Fixtures müssen zusätzlich konstante Reihen, Gleichstände, Halbwerte, 19/20 Punkte, Fenstergrenzen, fehlenden aktuellen Messwert und veraltete Gesamtdateien abdecken.

   Einfarbige Maildarstellung ist richtig. Fehlendes Perzentil ausdrücklich als „—“ anzeigen; derzeit verschwindet lediglich die zweite Zeile. „Hoch = ungewöhnlich put-lastig“ passt zum Vorzeichen, präziser wäre „Put-IV relativ zur Call-IV ungewöhnlich hoch gegenüber der eigenen Historie“: [scripts/templates/daily_report.html.j2:115](C:/dev/Seasonaledge/scripts/templates/daily_report.html.j2:115).

4. **R4: Entfernen ist korrekt; weitere Kalender sind betroffen.**

   Der Schreiber übernimmt tatsächlich `earningsHistory.quarter` als `report_date`: [scripts/fetch_event_data.py:164](C:/dev/Seasonaledge/scripts/fetch_event_data.py:164). Den Mailblock bei [shared/daily_report.py:948](C:/dev/Seasonaledge/shared/daily_report.py:948) entfernen.

   Weitere Leser: [landing/pages/earnings-kalender.html:256](C:/dev/Seasonaledge/landing/pages/earnings-kalender.html:256), [landing/js/kalender-compute.js:124](C:/dev/Seasonaledge/landing/js/kalender-compute.js:124) sowie Vollständigkeitsprüfungen. Diese Kalenderfehler als eigenen Folgepunkt erfassen; die Mailreparatur beseitigt sie nicht. Buyback bleibt wie vorgesehen.

5. **R5: Freigabefähig, einschließlich dynamischer Beschriftungen.**

   Tabellenlabels reagieren bereits auf den Modus: [landing/pages/skew.html:619](C:/dev/Seasonaledge/landing/pages/skew.html:619). Fest verdrahtet bleiben insbesondere Untertitel und EN-Übersetzung: [landing/pages/skew.html:285](C:/dev/Seasonaledge/landing/pages/skew.html:285), [landing/i18n/en.json:1540](C:/dev/Seasonaledge/landing/i18n/en.json:1540). Sie müssen auch nach Umschalten und Sprachwechsel stimmen. Eine Speicherung des Modus über `SA.prefs` oder `localStorage` ist in der Seite nicht vorhanden.

   Im Blog fand ich keine ausdrückliche Festlegung „Rank ist Standard“, aber eine veraltete zusätzliche 2J-Fensterangabe: [Blog DE:106](C:/dev/Seasonaledge/blog/posts/2026-09-06_vol-regime-radar-risk-reversal-iv-rank.md:106), [Blog EN:107](C:/dev/Seasonaledge/blog/posts/en/2026-09-06_vol-regime-radar-risk-reversal-iv-rank.md:107).

Die Reihenfolge passt. Der Wirkungsbericht sollte auf eingefrorenen Eingabedaten beruhen und zusätzlich Ausfälle sowie Quadrantenwechsel ausweisen. R1a kann als nächster read-only Schritt starten; R1b/c bleiben an Diagnose und konkrete Reparaturentscheidung gebunden. **Die Gesamtfreigabe für v1 fehlt wegen der noch offenen R3-Spezifikation und der Archiv-Kollisionsregel.**

**FREIGABE (Plan): nein**
