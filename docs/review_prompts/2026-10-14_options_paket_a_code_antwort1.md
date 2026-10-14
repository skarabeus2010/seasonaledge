**Drei Befunde; davon zwei Funktionsfehler.**

1. **Mittel — Health-Check 7 meldet ungeprüfte Daten grün.**  
   [scripts/daily_health_check.py:845](C:/dev/Seasonaledge/scripts/daily_health_check.py:845): `paare` zählt auch Paare, die anschließend wegen fehlender Returns oder ungültiger Kurse übersprungen werden. Ohne Treffer landet der Check trotzdem im grünen Zweig; `ungueltiger_kurs` wird nicht einmal angezeigt.

   Mit der echten Check-Funktion reproduziert:
   - 59 Paare, alle Returns `None`: **green**, „59 Kurspaare ohne Abweichung, 59 ohne log_return“.
   - 59 Paare, alle Schlusskurse `None`: **green**, „59 Kurspaare ohne Abweichung“.

   Tatsächlich geprüfte und übersprungene Paare getrennt ausweisen. Bei null verwertbaren Vergleichen „ungeprüft“, bei unvollständiger Prüfung gelb. Entsprechende Wächterfälle und Mutationen fehlen.

2. **Mittel — R5 ist von der Ladereihenfolge des Wörterbuchs abhängig.**  
   [landing/pages/skew.html:446](C:/dev/Seasonaledge/landing/pages/skew.html:446), [landing/pages/skew.html:749](C:/dev/Seasonaledge/landing/pages/skew.html:749): Die Seite startet unabhängig von der Übersetzungsbereitschaft. Treffen die Chartdaten vor `en.json` ein, rendert die Legende den deutschen Fallback. Das spätere `sa:i18n-bereit` löst hier kein Neurendern aus. Die Gegenprobe mit verzögertem Wörterbuch bestätigt die verbleibende deutsche Legende.

   Zusätzlich bleibt am Untertitel das statische `data-i18n-html="skew.quad_sub_pctl"` stehen. Nach einem frühen Wechsel auf Rank kann `_applyDOM()` den Untertitel wieder auf Percentile setzen ([landing/js/i18n.js:162](C:/dev/Seasonaledge/landing/js/i18n.js:162)).

   Nach Wörterbuchbereitschaft den aktuellen Modus vollständig neu rendern; den Übersetzungsschlüssel des Untertitels mitführen oder dessen Übersetzung ausschließlich dynamisch verwalten. Beide Ladereihenfolgen testen.

3. **Mittel — Der neue Lader und seine tatsächliche Einbindung sind nicht abgesichert.**  
   [scripts/verify_basisabweichung.py:111](C:/dev/Seasonaledge/scripts/verify_basisabweichung.py:111), ebenso Zeilen 129 und 137: Der Wächter weist jedem Verbrauchermodul selbst `lade_kurse` zu. Damit prüft er echte Rechenfunktionen, stellt aber die Lader-Einbindung selbst her. Selbst ein fehlender Import dieses Namens würde dadurch verdeckt. Der echte Lader wird überhaupt nicht ausgeführt.

   Ergänzen: Verbraucherprüfungen mit echtem Lader und Supabase-Attrappe sowie Fälle für zweite Seite, Seitenfehler, Mindestzahl, Typumwandlung und Zeilentreue. Die Session-Prüfung in [Zeile 125](C:/dev/Seasonaledge/scripts/verify_basisabweichung.py:125) kontrolliert außerdem nur das Spot-Datum; dort auch den RV-Wert gegen das gekappte Referenzfenster prüfen.

Die übrigen Prüfaufträge ergeben:

- **R1b:** Alle ausdrücklich im freigegebenen Plan genannten Rendite-Verbraucher sind umgestellt, einschließlich beider Intermarket-Pfade. `backfill_skew_massive` verwendet den bisherigen Lader ausschließlich für Spot.
- **RV-Zuordnung:** `returns[:i+1]` ist richtig, weil gespeicherter Return `i` zum Tag `i` gehört. Die alte `rv_reihe` verwendet wegen der um eins kürzeren abgeleiteten Return-Liste `returns[:i]`. Bei vorhandenem gespeichertem Anfangsreturn kann die neue Variante bereits einen Tag früher einen Wert liefern; das ist kein Versatz. Session-Kappung, `None` im Fenster und Rückgriff auf den letzten gültigen Rohschluss passen.
- **`lade_kurse`:** Seitenbereiche, serverseitige Sortierung und Mindestzahl gültiger Schlusskurse passen. Ungültige Zahlen bleiben zeilengleich `None`. Geworfene Abfragefehler liefern keine Teilreihe zurück. Allerdings behandelt [shared/data.py:246](C:/dev/Seasonaledge/shared/data.py:246) `data=None` wie ein reguläres Seitenende: Nach einer vollen ersten Seite wird dann eine verkürzte Reihe akzeptiert. Mit Attrappe reproduziert; kein Nachweis eines solchen produktiven Supabase-Verhaltens.
- **R4:** Earnings entfernt, Dividenden mit eigenem Client erhalten; kein weiterer Befund.
- **R5:** Standard, Modusumschaltung, Tooltip und Wörterbuchtexte passen bei bereits geladenem Wörterbuch. Offen bleibt Befund 2.

**Folgeposten außerhalb des ausdrücklich benannten R1b-Umfangs:** Schlusskurs-Renditen bestehen weiterhin in den Mail-Kursanzeigen ([daily_report.py:244](C:/dev/Seasonaledge/shared/daily_report.py:244), [Zeile 422](C:/dev/Seasonaledge/shared/daily_report.py:422)), der monatlichen Sektorberechnung ([Zeile 1273](C:/dev/Seasonaledge/shared/daily_report.py:1273)) und im Yahoo-basierten Vol-Control-Proxy für `/flows` ([build_volcontrol_proxy.py:74](C:/dev/Seasonaledge/scripts/build_volcontrol_proxy.py:74)). Diese sind keine zusätzlichen Paket-A-Blocker.

Read-only geprüft. Lokal grün: neuer Wächter mit unterdrücktem Datei-Logging, `verify_realized_vol` mit 54 Fällen und JS-Tabellenprobe. Den dateiverändernden Mutationstest habe ich nicht ausgeführt; 15/15 bleibt dein berichteter Nachweis.

**FREIGABE (Code): nein.**
