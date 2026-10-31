**1. Die Lesart trägt hinsichtlich des Spots.**

Im alten Massive-Pfad wird derselbe `spot` an `_exposures`, `_walls` und `_zero_gamma` übergeben und anschließend gerundet archiviert. Auch der Yahoo-Pfad verwendet seinen archivierten Spot tatsächlich zur Berechnung. Ein zum Sitzungsschluss passender Archivwert ist deshalb relevante Evidenz gegen einen pauschalen Spot-Versatz.

Eine wichtige Präzisierung: **`bb70906^` enthält bereits B2**, also den datierten Tagesbalken statt `/prev`. Für die Altbestandsfrage ist zusätzlich der Stand **vor `326bcc8`** entscheidend. Dort wird `/prev?adjusted=true` ohne Prüfung des Balkendatums verwendet.

Die Dokumentation widerspricht sich bereits intern:

- [GEX-Spot](/C:/dev/SeasonalEdge/docs/OPTIONS.md:987) behauptet pauschal einen veralteten Spot bis 13.10.
- Der [spätere Messbericht](/C:/dev/SeasonalEdge/docs/OPTIONS.md:1094) beschränkt diesen Befund auf Abrufe vor 00:00 UTC.

Deine Messung spricht gegen den pauschalen Ausschlussgrund. Sie beweist jedoch nicht für jeden einzelnen Ticker-Tag die Herkunft des Kurses: An ruhigen Tagen können auch zwei benachbarte Schlüsse innerhalb von 0,3 % liegen.

**2. Ein passender Spot beweist keinen passenden OI-/IV-Stand.**

Der alte Code übernimmt `open_interest` und `implied_volatility` aus dem jeweils aktuellen Snapshot. Er prüft deren zeitliche Zuordnung nicht. Massive beschreibt OI als Bestand zum Ende des letzten Handelstags; daraus folgt keine Garantie, wann dieser Bestand im konkreten Nachtabruf bereits aktualisiert war. [Massive: Option Chain Snapshot](https://massive.com/docs/rest/options/snapshots/option-chain-snapshot)

Daher sind beispielsweise möglich:

- Schlusskurs der Session S mit noch älterem OI;
- Schlusskurs S mit später aktualisierter IV;
- unterschiedliche Aktualisierungsstände innerhalb der paginierten Chain.

Das sind **mögliche Mechanismen, keine nachgewiesenen Fehler der Altdateien**. Ohne historische Rohantworten oder passende Laufbelege lassen sie sich rückwirkend nicht vollständig klären. Das rechtfertigt eine Qualitätskennzeichnung, aber keinen erfundenen generellen Sitzungsschritt zurück.

Zusätzlich konnte der alte Massive-Abruf bei Seiten-Cap oder bestimmten unbrauchbaren Antworten eine Teilkette zurückgeben. Der Vollständigkeitszustand wurde erst mit `0d2b2df` ausdrücklich erfasst. Auch ein passender Spot und ausreichend viele Kontrakte schließen eine Teilkette nicht aus.

**3. Regel 1 und 3 brauchen einen belastbareren Zeitbeleg.**

Die Annahme „birth ändert sich beim Überschreiben“ ist für den hier relevanten Linux-Fall falsch: `btime` bezeichnet die Inode-Erstellung und bleibt bei anschließendem Schreiben erhalten. Bei Ersatz durch eine neue Datei kann ein neuer Erstellungszeitpunkt entstehen. [Linux-Dokumentation: inode(7)](https://man7.org/linux/man-pages/man7/inode.7.html)

Gerade die alten Schreiber nutzen `Path.write_text()`. Damit kann ein späterer Inhalt weiterhin die ursprüngliche birth-Zeit tragen.

**Änderung:**

> Session wird aus dem belegten Abruf-/Laufzeitfenster abgeleitet. Birth dient als Indiz und wird mit mtime, vorhandenen Laufprotokollen und gegebenenfalls gesicherten `generated_at`-Werten abgeglichen. Nicht eindeutig zuordenbare Inhalte erhalten `zeitzuordnung_unbelegt`.

Die Dateischreibzeit liegt außerdem nach den Abrufen. Überschreitet ein Lauf eine relevante Zeitgrenze, genügt sie allein nicht.

Für Dubletten:

> Je Session wird der früheste zeitlich belegte, zulässige Lauf gewählt; spätere Läufe ersetzen ihn nicht stillschweigend. Fehlende Ticker werden nicht aus späteren Läufen ergänzt.

Die Dateien vom 05./06./08.09. sind **Mehrfachbeobachtungen derselben Session**, nicht zwingend identische Messungen: Laufzeit, OI, IV und Bewertungsdatum können sich unterscheiden. Abweichende Regime unter diesen Dateien gehören ins Inventar.

**4. Regel 4 unterschätzt die Methodenunterschiede.**

Yahoo und Massive sollten **primär getrennt**, ergänzend gemeinsam als ausdrücklich heterogener Bestand beschrieben werden. Eine gemeinsame Tabelle ist zulässig; eine bloße Kennzeichnung der Zusammenfassung reicht methodisch nicht.

Im Code bestehen folgende Unterschiede:

| Merkmal | Yahoo | Massive vor B2 |
|---|---|---|
| Restlaufzeit | Sekunden bis zum gelieferten Verfallszeitpunkt | Ganze Kalendertage gegen `date.today()` |
| Dividendenrendite | Yahoo-Wert | Fest `q = 0` |
| IV-Filter | `iv > 0` | `0,01 ≤ iv ≤ 5` |
| Kettenprüfung | OI-Plausibilitätsquote, erst ab 13.08. | Mindestzahl brauchbarer Kontrakte |

Vor allem ist „DTE einen Tag kleiner“ zu ersetzen durch:

> Mit Δ = Bewertungsdatum minus Sessiondatum in Kalendertagen gilt im alten Massive-Pfad `DTE_alt = DTE_session − Δ`; die obere Horizontgrenze liegt entsprechend um Δ Kalendertage weiter hinten.

Für Session 04.09. und Lauftag 08.09. beträgt Δ beispielsweise **vier Tage**. Die Abweichung verändert die Gamma-Gewichte und kann auch das Netto-Vorzeichen ändern. Umdatieren stellt deshalb keine methodisch identische Sessionberechnung her.

Ergänze neben den drei groben Versionsgruppen **Codeversion und Bewertungsdatum je Lauf**. Für Walls und Flip sind außerdem die Änderungen vom 10.09. relevant; sie betreffen nicht automatisch das Netto-GEX-Regime.

**5. Den Spotfilter beibehalten, seine Aussage begrenzen.**

Die 0,3-%-Grenze ist als vorab festgelegter Konsistenzfilter brauchbar. Sie ist kein Datumsnachweis und keine Garantie für ein stabiles GEX-Vorzeichen.

Erforderliche Ergänzungen:

- Referenzschluss endlich, positiv, tatsächlicher EOD-Wert und auf derselben Kursbasis; Supabase kann laut Projektdoku auch Intraday-Reststände enthalten.
- Referenzexport samt Hash einfrieren.
- Abstände zur zugeordneten Session **und zur Vorsitzung** speichern; mehrdeutige Treffer kennzeichnen.
- Die Session niemals nach dem am besten passenden Schluss auswählen.
- Engere Spotgrenzen ergänzend als Sensitivität ausweisen, ohne danach die Hauptregel auszuwählen.

Archiviertes Regime und gerundete Null wie vorgeschlagen behandeln. Zusätzlich fehlende, nicht endliche oder widersprüchliche GEX-/Regime-Werte ausdrücklich ausschließen.

**6. Inventar und Studienaussage ergänzen.**

Zusätzlich zu deinen Feldern gehören hinein: Zeitbeleg und dessen Quelle, mtime/birth, Laufzeitfenster soweit bekannt, Bewertungsdatum, Δ, Codeversion, Auswahlentscheidung unter Mehrfachläufen sowie OI-/IV-Zeitstand und Kettenvollständigkeit jeweils mit dem zulässigen Wert **„unbelegt“**.

Das Inventar und die Regeln werden **vor Betrachtung der Forward-Renditen** eingefroren. Arm B bleibt gemäß Studienplan beschreibend: keine Tests und keine Handelsaussage. Nachts verfügbare Werte dürfen insbesondere nicht als bereits zum vorherigen Schluss handelbar dargestellt werden. Fallzahlen getrennt als Sessions und Ticker-Sessions nennen; „rund 50“ bleibt bis zur Inventur eine Erwartung.

**Dokumentationskorrektur: ja.** Vorschlag für die historische Aussage:

> Der frühere Massive-Pfad verwendete `/prev` ohne Prüfung des Balkendatums. Dessen Sitzungszuordnung hängt vom Abrufzeitpunkt ab. Die pauschale Aussage, sämtliche GEX-Berechnungen bis 13.10. hätten einen um eine Sitzung veralteten Spot verwendet, ist nicht belegt. Der nachträgliche Archivabgleich spricht für überwiegend passende Schlusskurse bei teilweise verschobenen Dateistempeln. Eine Wiederverwendung erfordert eine datei- und tickerbezogene Prüfung; sie stellt keine Gleichwertigkeit von Bewertungsdatum, OI-/IV-Zeitstand und Kettenumfang her.

Die gemessenen Fallzahlen und Ausschlüsse sollten diese Passage anschließend belegen. Auch die entsprechende Behauptung in `CLAUDE.md` braucht einen Korrekturhinweis.

**Schluss: TRAGFÄHIG MIT ÄNDERUNGEN.** Der pauschale Altbestandsausschluss wegen angeblich durchgehend veralteten Spots ist nicht haltbar. Die Wiederaufnahme trägt als dokumentierte, nach Methoden getrennte Erweiterung des beschreibenden Arms B — mit belastbarer Zeitzuordnung und ausdrücklich ausgewiesenen verbleibenden Unsicherheiten.
