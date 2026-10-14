**Phase 0 ist freigabefähig.** Die neue Gate-Reihenfolge ist richtig. Phasen 1–5 sind fachlich sinnvoll, aber in der genannten Reihenfolge noch nicht unabhängig produktiv deploybar.

Geprüft gegen `88c02ff`; Runde 1 gelesen. Keine Dateien geändert, keine Server-Probe ausgeführt. Die eingefrorenen JSON-Dateien und ihre Zahlen habe ich hier nicht unabhängig nachgeprüft.

**1. Erst Diagnose, dann Regel: ja**

Die Tagesbar-Rekonstruktion ist **als Mechanismusnachweis brauchbar**, als vollständiger Beweis der damaligen Live-Ursache eingeschränkt. Auch Live verwendet für `own_bs` den Tages-Schlusskurs aus dem Snapshot; deshalb ist die Näherung sachlich begründet. Ohne Originalsnapshot bleiben Kontraktbestand, damaliger Datenstand und tatsächlich ausgewählte Stützstellen unsicher. Siehe [compute_options_skew.py:481](C:/dev/Seasonaledge/scripts/compute_options_skew.py:481) und [compute_options_skew.py:500](C:/dev/Seasonaledge/scripts/compute_options_skew.py:500).

Im Bericht würde ich getrennt ausweisen:

- **Mechanismus reproduziert:** Diese Eingaben erzeugen über diesen Rechenweg den auffälligen Wert.
- **Historische Ursache belegt/unbelegt:** Sind diese Eingaben und der damalige Rechenweg tatsächlich nachgewiesen?
- **Abweichung zur gespeicherten Zeile:** Einzel-IVs, ATM, Skew und Modus; Übereinstimmung allein beweist keine identischen Eingaben.

Ein Replay mit `88c02ff` ist zunächst eine Nachrechnung mit dem **heutigen geprüften Code**, nicht automatisch mit der damals eingesetzten Version.

Für Phase 0 sind folgende Präzisierungen wichtig:

- **Alle Kandidatengruppen tatsächlich versorgen.** Unverändertes `_plan` lädt nur die ersten drei. Die Probe braucht sowohl den originalen Backfill-Ablauf als Vergleich als auch eine ausdrücklich gekennzeichnete Diagnose mit vollständiger Kandidatenversorgung. Sonst sind spätere Gruppen nicht prüfbar. [backfill_skew_massive.py:278](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:278)
- **Abruffehler von fehlenden Bars unterscheiden:** `_bars(..., strict=True)` verwenden. Andernfalls wird ein Abruffehler zur leeren Datenmenge. [backfill_skew_massive.py:120](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:120)
- **Rohpreise, Volumen, Spotquelle und Vorfilter mitprotokollieren.** Tagesbars liefern keinen verlässlichen Zeitpunkt des letzten Einzeltrades; gleiche Session garantiert keine synchronen Preise. [backfill_skew_massive.py:136](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:136)
- **Un gerundete Diagnose vor der Rückgabe erfassen:** `cm_interp` rundet bereits auf vier Nachkommastellen, ebenso die ATM-IV des Legs. Rückgabewerte allein erfüllen die geplanten ungerundeten Fixtures nicht. [black_scholes.py:125](C:/dev/Seasonaledge/shared/black_scholes.py:125), [black_scholes.py:504](C:/dev/Seasonaledge/shared/black_scholes.py:504)

Die fünf Fälle plus Vergleichstage reichen zum Einstieg, **nicht allein zur Kalibrierung eines allgemeinen H**. Plan v3 sollte zusätzlich die Wirkung über den eingefrorenen Bestand und gezielte Earnings-Kontrollen zeigen. Bei unbelegten Fällen darf das Ergebnis ausdrücklich „keine belastbare Ausschlussregel gefunden“ lauten.

**2. Phasen 1–5: vollständig im Kern, Deployments anders schneiden**

**Gemeinsame Entscheidung:** Die Eingabe muss das vollständige Expiry-/DTE-Universum einschließlich fehlgeschlagener Legs enthalten. Nur erfolgreiche Legs zu übergeben würde die heutige Neugenerierung der Backfill-Rangliste fortsetzen. Bei verzögertem Laden braucht es unterscheidbare Zustände „noch nicht geladen“ und „verworfen“. [backfill_skew_massive.py:355](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:355)

**Qualitätsstatus:** `auffaellig` bedeutet weiterhin bewertbar, solange keine validierte Ausschlussregel greift. Deshalb darf „markierte aktuelle Session → heute nicht bewertbar“ **nur für tatsächlich ausgeschlossene Zeilen** gelten. `nicht_pruefbar` allein erzeugt ebenfalls keinen zusätzlichen Ausschluss; bestehende Voraussetzungen wie `cm`/`cm_extrap` bleiben bestehen.

Das ist auch technisch relevant: `_isNorm` prüft aktuell ausschließlich den Modus. Wird `cm_mode` bewahrt, ignoriert das Frontend einen separaten Ausschlussstatus zunächst vollständig. [skew.html:239](C:/dev/Seasonaledge/landing/pages/skew.html:239)

Ich würde die produktiven Schritte deshalb so schneiden:

1. Gemeinsame Entscheidung zunächst im Vergleichsbetrieb; Herkunft und Status additiv speichern.
2. Alle Schreiber und Leser auf denselben Status- und Versionsvertrag bringen; Frontend einschließlich „heute nicht bewertbar“ bereitstellen.
3. Validierte Regeln aktivieren.
4. Bestand gezielt migrieren.
5. 10Δ ergänzen; ohne Einfluss auf die 25Δ-Entscheidung.

**Aktualisierung:** Die neue Ersetzungsregel muss zusätzlich verhindern, dass ein älterer Regellauf später eine ausgeschlossene Zeile wieder rankbar macht. Außerdem festlegen, wie neuere Versionen bei gleicher Rankbarkeit und Wiederholungen derselben Version behandelt werden. Der heutige Vorrang „rankbar ersetzt nicht rankbar“ genügt dafür nicht. [compute_options_skew.py:1256](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1256)

**Sperre:** Sie muss den gesamten Ablauf **Lesen → Hashprüfung → Zusammenführen → atomar Schreiben** schützen. Nur das Schreiben zu sperren verhindert keine verlorenen Aktualisierungen: Backfill lädt den Bestand vor der Tickerschleife. Auch der VRP-Backfill ist ein History-Schreiber. [backfill_skew_massive.py:850](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:850), [backfill_skew_vrp.py:354](C:/dev/Seasonaledge/scripts/backfill_skew_vrp.py:354)

Für gezielte Reparaturen nicht ungeprüft `--overwrite` übernehmen: Dieser Pfad entfernt zunächst sämtliche `src="massive"`-Zeilen eines Tickers. Die Migration braucht Ersetzungen je Ticker/Datum und muss bei bloßem Abruffehler den Bestand erhalten. [backfill_skew_massive.py:438](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:438)

**3. Freigabe für Phase 0: ja**

Freigegeben ist die beschriebene Diagnose über lesende Helfer, mit Ergebnissen im Speicher beziehungsweise auf stdout. Python mit deaktiviertem Bytecode-Schreiben starten; keine produktiven Schreibpfade aufrufen.

Die Freigabe umfasst **noch keine Wahl von H, Regelaktivierung oder Bestandsänderung**. Dafür ist der angekündigte Plan v3 mit Wirkungszahlen der richtige nächste Entscheidungspunkt.

**FREIGABE (Plan): ja**
