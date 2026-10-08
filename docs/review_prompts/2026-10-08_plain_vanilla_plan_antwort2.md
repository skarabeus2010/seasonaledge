# Codex-Antwort: Plan /plain-vanilla, Runde 2


codex
**v2 ist noch nicht freigabefähig.** Die Trennung realisierter und täglich bewerteter Kennzahlen trägt grundsätzlich. Offen bleiben insbesondere der tatsächlich verwendete Kalender und ein durchgängiger Hebelvertrag.

Geprüft wurden die beiden Vorreviews, die betroffenen Module und die vorhandene Basislinie. Keine Dateien verändert. `plain_vanilla_phase0.json` enthält die angekündigten fünf Ticker und sechs Zeitraum-/Stop-Kombinationen, ohne protokollierte Strategiefehler.

1. **Hoch — 1a: Der Kalendernachweis gilt für einen anderen Kalender.**  
   Die dokumentierte NYSE-Abdeckung ab 1971 bezieht sich ausdrücklich auf `shared/nyse_holidays.py` **plus** `election_calendar_exceptions.json`. `SA.holidays` verwendet diese Kombination nicht: `holidays.js` setzt beispielsweise MLK und Juneteenth ohne historische Jahresgrenzen an und lädt die Sonderausnahmen nicht. Auch für XETRA enthält es keine belegte historische Gültigkeitsgrenze.  
   **Änderung:** Vor 1a einen identischen, versionierten Kalendervertrag für JS und Python festlegen und dessen tatsächliche Sitzungsmenge prüfen. Den NYSE-Nachweis nur auf die nachgewiesene Implementierung übertragen; die XETRA-Messung vor Kalenderintegration abschließen. Zeilenzählung vor belegter Abdeckung ist als ausdrücklich unsichere historische Methode vertretbar. Die Kennzeichnung muss auch im Ergebnis sichtbar bleiben, nicht nur im Messlauf.

2. **Hoch — 1a/1d/1e: Kurslücken innerhalb einer Position bleiben ungeregelt.**  
   Der Plan behandelt fehlende Ein- und Ausstiegskurse, aber nicht fehlende Sitzungen dazwischen. Diese können Stops, LBR-Signale und täglichen Drawdown verändern. Auch „offen, bewertet zum letzten Kurs“ wäre irreführend, wenn vor dem Stichtag erwartete Sitzungen fehlen. Die Terminsuchliste erfasst außerdem direkte Indexarithmetik nicht ausdrücklich, etwa `entryIdx + HOLD` bei Down-Month-ToM.  
   **Änderung:** Abdeckungsprüfung auf Haltedauer, Bewertung und benötigte Signalhistorie ausweiten; fehlende oder ungültige Kurse dürfen nicht still überbrückt werden. Verbindlich festlegen, welche Ergebnisse dann ausgeschlossen oder als unvollständig ausgewiesen werden. Auch direkte Sitzungs-Offsets inventarisieren. Stichtag und letzter vorhandener Kurs müssen getrennte Größen bleiben.

3. **Hoch — 1e: Täglicher Hebel und bisherige Trade-Rendite passen nicht zusammen.**  
   JS-UHTS multipliziert bislang die gesamte Kursrendite mit 1,5; Python verwendet sogar eine andere Aufteilung. Tägliches Hebeln bedeutet dagegen tägliches Rebalancing. Beispiel `100→80→110`: Gesamtbewegung × 1,5 ergibt **+15 %**, tägliche Verkettung ergibt `0,70 × 1,5625 − 1 = +9,375 %`. Damit könnten Chart und realisierte Handelsstatistik denselben geschlossenen Trade unterschiedlich bewerten.  
   **Änderung:** Das Hebelmodell ausdrücklich auswählen. Beim vorgeschlagenen Tagesmodell müssen auch sämtliche Trade-Renditen, Stop-Renditen und beide Zwillinge dieselbe tägliche Verkettung verwenden. Festlegen: erste Rendite nach dem Einstiegs-Close, letzte bis einschließlich Ausstiegs-Close; Stopgrenze auf Basiswert oder Positionswert; Verhalten bei Kapital ≤ 0. Den Hebelfall als eigene fachliche Korrektur mit Zwischenlauf aufnehmen.

4. **Hoch — 1d/Phase 3: Die Close-Stop-Korrektur ist zeitlich und fachlich nicht eindeutig eingeplant.**  
   „Seite Close-basiert“ benennt noch nicht ausdrücklich die Korrektur des Fixed-Stops: Der aktuelle JS-Pfad steigt weiterhin rechnerisch zum Stopniveau aus. Beide Stopfunktionen erzeugen neue Objekte und verlieren dabei unter anderem den Hebelfaktor. Das betrifft bereits die Equity-Abnahme in Phase 1.  
   **Änderung:** Für Phase 1 verbindlich festlegen: Ausführung zum beobachteten auslösenden Close, Erhalt der relevanten Trade-Metadaten, geschlossener Status nach Stop und Rendite nach dem gewählten Hebelmodell. Ein gestoppter ursprünglich offener Trade zählt anschließend realisiert. Die separaten OHLC-Korrekturen können in Phase 3 bleiben.

5. **Mittel — 1e/1f: Überschneidungen und verbleibende Kennzahlen brauchen einen gemeinsamen Vertrag.**  
   „Zweite Position verworfen“ lässt Reihenfolge, gleichzeitige Termine und durch Stops frei werdendes Kapital offen. Unklar bleibt außerdem die Zuordnung der vorhandenen Kennzahlen `final_equity`, `total_return` und CAGR. Diese dürfen nicht weiterhin aus einer anderen Tradefolge als der Chart entstehen.  
   **Änderung:** Eine chronologische Ausführung mit deterministischer Gleichstandsregel definieren; Überschneidungen anhand des tatsächlichen Ausstiegs einschließlich Stop behandeln. Dieselben akzeptierten Trades für Equity, realisierte Statistik und Streak verwenden. Endkapital, Gesamtrendite und CAGR ausdrücklich einer Kennzahlenfamilie samt Berechnungszeitraum zuordnen.

6. **Mittel — 0: Der eingefrorene Messrahmen ist noch nicht vollständig reproduzierbar nachgewiesen.**  
   Der Loader schreibt kein `snapshot.json`; der Messlauf übernimmt dessen Hash ungeprüft. Unter `scripts` fand ich keine Snapshot-Metadatei. Die vorhandene Ergebnisdatei belegt daher den protokollierten Hash, aber nicht die überprüfbare Unverändertheit ihrer Eingabedaten. Außerdem fehlen in den archivierten Trade-Tupeln Preise und Hebel.  
   **Änderung:** Snapshot-Pfad und Erzeugungs-/Hashverfahren dokumentieren, den Hash vor jedem Lauf neu prüfen und Abweichungen zum Abbruch bringen. Harness und relevante Seitenlogik mit versionieren. Preise, Hebel, Kalender-/Lückenstatus und Ausschlussgründe im Vergleichsformat aufnehmen. Strategiefehler müssen einen Lauf als ungültig markieren.

7. **Mittel — 1d/Phase 3: Die Indikatorregeln werden angekündigt, aber noch nicht entschieden.**  
   „Verbindlich Seed, Warm-up, Signal-Start, ungültige Werte“ nennt die offenen Entscheidungen, beantwortet sie jedoch nicht. Gleiches gilt für Mindesthistorie und Gleichstände beim Regime.  
   **Änderung:** Konkrete Regeln und kleine erwartete Ergebnisvektoren vor der jeweiligen Implementierung festhalten. Beim fehlenden Indikatorwert muss die Gültigkeitsprüfung vor dem Vergleich greifen, auch für `!=` und negierte Bedingungen.

**Vorbereitende Messungen können beginnen.** Für die produktive Umsetzung von Phase 1 müssen insbesondere Kalenderintegration, Lückenbehandlung, Hebelmodell und Close-Stops vorher entschieden sein; die für v3 angekündigten Nachweise sind dafür Voraussetzungen.

FREIGABE: nein
