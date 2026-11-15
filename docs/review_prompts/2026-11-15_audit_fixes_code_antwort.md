# Codex-Antwort (2026-11-15_audit_fixes_code_antwort)

**NICHT FREIGABEFÄHIG.** Die Reparaturen greifen im Normalfall, aber die zentrale Lücke „Nightly rot, Health grün“ bleibt offen.

1. **Hoch — fehlgeschlagener Lauf ohne Logzeile bleibt grün.**  
   [nightly_refresh.py:598](../../scripts/nightly_refresh.py#L598), [daily_health_check.py:193](../../scripts/daily_health_check.py#L193)  
   Scheitert das `refresh_log`-Insert, endet der Nightly mit Exit 1. Die Health-Abfrage findet weiterhin die erfolgreiche Vortageszeile; deren Alter von einem Tag erlaubt ausdrücklich Grün. Reproduziert: erfolgreicher Eintrag vom 14.11. → am 15.11. weiterhin `green`, obwohl das aktuelle Insert gescheitert ist. Frische Ausgabedateien schließen diese Lücke ebenfalls nicht. Ein Prozessabbruch vor dem neuen Logpunkt hat denselben Effekt.  
   **Erforderlich:** fehlenden Abschluss anhand des erwarteten Lauftermins erkennen; beispielsweise Start und Abschluss protokollieren und überfällige beziehungsweise unvollständige Läufe auswerten. Der Wächter prüft beim Insert-Fehler bisher nur Exit 1, nicht die anschließende Health-Bewertung.

2. **Mittel — Indikator-Zwillinge behandeln fehlende Kurse unterschiedlich.**  
   [indicators.py:25](../../shared/indicators.py#L25), [indicators.py:56](../../shared/indicators.py#L56), [indicators.js:34](../../landing/js/indicators.js#L34), [indicators.js:50](../../landing/js/indicators.js#L50)  
   Python überspringt NaN-Werte und rechnet über die verbleibenden Kurse. JS verarbeitet `null` rechnerisch als null; `NaN` vergiftet die EMA-Folge, während RSI betroffene Änderungen als null behandelt.  
   Konkrete Reihe `[1, 2, fehlend, 1, 3, 2]`, Periode 2: letzter RSI in Python **50**, in JS mit `null` **52,380952**, mit `NaN` **52,941176**. Damit ist die Angleichung bei Lücken unvollständig.  
   **Erforderlich:** gemeinsamen Vertrag für fehlende Kurse festlegen und führende, innere sowie abschließende Lücken prüfen. Einen betroffenen Live-Datensatz habe ich hierfür nicht nachgewiesen.

3. **Mittel — produktiv verwendetes LBR-Histogramm bleibt ungeprüft.**  
   [verify_indikator_zwillinge.py:43](../../scripts/verify_indikator_zwillinge.py#L43), [verify_indikator_zwillinge.py:67](../../scripts/verify_indikator_zwillinge.py#L67)  
   Der Wächter vergleicht MACD/LBR-Linien, aber keine Histogramme. Die Plain-Vanilla-Strategie verwendet gerade das [LBR-Histogramm](../../shared/strategies/plain_vanilla.py#L354) für ihre Handelsentscheidungen. Eine Gegenprobe ausschließlich im Arbeitsspeicher mit umgekehrtem Histogramm-Vorzeichen ließ weiterhin **74/74 Prüfungen bestehen**.  
   **Erforderlich:** Histogramme mit unabhängigem Sollwert prüfen und eine entsprechende Vorzeichenmutation ergänzen.

Die übrigen Fokusfragen:

- **Reihenfolge/Weekly:** Keine neue Abhängigkeit vom früheren Nightly-Logpunkt gefunden. Phase F bleibt davor und ist derzeit abgeschaltet. Die neuen Stress-Fehlermeldungen enthalten keinen Score oder Ampelzustand.
- **`getAll`:** Beide genannten Seiten behandeln die Ablehnung: `/polymarket` zeigt einen Ladefehler, `/crash-fruehwarnung` blendet den Polymarket-Abschnitt aus. Kein unbehandelter Fehlerpfad gefunden.
- **Indikatoren ohne Lücken:** SMA-Start, Wilder-Start und MACD-Signal stimmen. Zusätzlich gegen eine unabhängig hergeleitete Referenz mit exakten rationalen Gewichtssummen geprüft, einschließlich MACD/LBR-Histogrammen. Backtests und Plain Vanilla übernehmen die geänderten Definitionen automatisch.

Validierung: **74/74 Indikatorprüfungen**, **19/19 Nightly-Prüfungen** und **10/10 Health-Prüfungen** bestanden; Dateitests liefen mit einem Dateisystem im Arbeitsspeicher. Die schreibenden Mutationsskripte und Live-Serverläufe wurden nicht ausgeführt. **Keine Dateien geändert.**
