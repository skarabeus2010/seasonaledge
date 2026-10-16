**FREIGABE (Code): nein.**

Keine P1-Befunde. Ein P2-Befund und eine P3-Testlücke.

- **P2 – IV/RV wird auch für `single` ausgegeben.** In [compute_options_skew.py:1215](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1215) genügt ein gesetzter `cm_mode`. `_cm_out("single", …)` kann aber eine gültige `cm_iv_atm` liefern. Beispiel: `single`, ATM-IV `0.22`, RV `0.18` ergibt `ivrv=1.2222`, obwohl der Plan ausschließlich `cm`/`cm_extrap` zulässt. Die Seite zeigt diesen Wert als 30-Tage-IV/RV, während die übrigen normierten Spalten leer bleiben. Auch [die neue History-Zuweisung](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1300) übernimmt RV für `single`, weil `cm_ok` lediglich auf `is not None` prüft. **Für beide neuen Felder `_rankbar(t)` verwenden**, ohne die bestehende History-Fallbacklogik pauschal zu ändern. Cron-Test mit `single` **und vorhandener ATM-IV** ergänzen.

- **P3 – Die zugesagte Leserregression und Sprachwechselprüfung fehlen als ausdrückliche Tests.** Die [Mail-Fixture](C:/dev/Seasonaledge/scripts/verify_skew_rang.py:460) enthält weiterhin nur B3a-Felder; ein Vorher-/Nachhervergleich mit B3b-Zusätzen fehlt. Die [Seitenprobe](C:/dev/Seasonaledge/scripts/js/probe_skew_rang_seite.js:32) verwirft `addEventListener`-Registrierungen und kann deshalb den Wörterbuchwechsel nicht prüfen. Ergänzen: identische Mail-/Radar-/Bestandsspaltenwerte mit erweiterten Fixtures sowie tatsächliches Auslösen von `sa:i18n-bereit`.

Die übrige Prüfung ergibt:

- Python und JS setzen die neuen Rang-/Statusverträge bei statischer Prüfung übereinstimmend um. Strikter Randvergleich, letzter gültiger Vorgänger, Median einschließlich aktueller Änderung und gemeinsame Fensterregel passen.
- Bestehende Leser greifen gezielt auf bekannte Felder zu; keine konkrete B3a-Regression gefunden.
- Listen sortieren nach Percentile und schließen Überschneidungen auch bei 18 Gleichständen aus. Dies sowie die IV/RV-Zelle habe ich mit dem echten Seiten-JS im Speicher geprüft.
- HTML-Werte werden teilweise unmaskiert eingesetzt. Für die beschriebenen Quellen — kontrollierte Universumssymbole, validierte Datumswerte, numerische Rangfelder und eigene Übersetzungen — sehe ich keinen konkreten Injection-Befund.

**Prüfgrenze:** Python war hier nicht ausführbar; den vollständigen Zwillingstest konnte ich daher nicht erneut ausführen. Den dateiverändernden Mutationstest habe ich wegen Read-only nicht gestartet. Die gemeldeten 41/41 sind somit nicht unabhängig bestätigt. Keine Dateien geändert.
