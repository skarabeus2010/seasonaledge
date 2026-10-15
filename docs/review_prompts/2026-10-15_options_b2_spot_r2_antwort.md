**FREIGABE (Code): nein**

**[P1] Das Datum von `regularMarketTime` ist weiterhin kein Nachweis eines finalisierten Tagesbalkens.** In [_spot](C:/dev/Seasonaledge/scripts/snapshot_gex_massive.py:113) genügt beispielsweise `regularMarketTime = Sessiontag 14:00 ET` zusammen mit einem positiven Session-`close`. Beide werden auch bei einem Lauf um 18:00 ET akzeptiert. Eine beim Anbieter stehengebliebene Intraday-Antwort besteht damit die Prüfung. Der frische HTTP-Abruf beseitigt den Supabase-Restbestand, beweist aber nicht die Aktualität des gelieferten Inhalts. Das ist ein Gegenbeispiel zur Prüfbedingung, kein Nachweis, dass Yahoo im berichteten Lesetest veraltete Daten geliefert hätte.

Zu den Prüfaufträgen:

1. **Halbtage, Feiertage, `--no-write`:** Die zeitliche Sessionauswahl ist konservativ korrekt. [Der Kalender](C:/dev/Seasonaledge/shared/exchange_holidays.py:417) behandelt Halbtage bis 16:15 ET als offen; vorher ist ein Schreiblauf gesperrt. Feiertage werden übersprungen, ein letzter Handel am Sessiontag bleibt zulässig. Während der Handelszeit verwendet `--no-write` die abgeschlossene Vorsession: Der Spot passt dazu, die aktuelle Massive-Chain muss allerdings nicht deren EOD-Stand entsprechen. Es wird nichts geschrieben.

2. **Handelsstopp:** Liegt der letzte Handel **vor** der Session, wird der Ticker korrekt verworfen. Bei Handel am Vormittag und anschließendem Stopp besteht die Prüfung. Dieser letzte Kurs kann durchaus der richtige Tagesabschluss sein; der Code kann diesen Fall aber nicht von veralteten Daten unterscheiden. Ein späteres `regularMarketTime` belegt zudem keinen Handel am angefragten Sessiontag. Fehlt dessen Balken, greift immerhin die separate Ablehnung.

3. **Wächterlücke:** Die [Yahoo-Attrappe](C:/dev/Seasonaledge/scripts/verify_gex_session.py:149) setzt den Nachweis stets auf 16:00 ET oder den Vortag. Der entscheidende Fall „richtiger Sessiontag, aber Intraday-Zeit und nicht finalisierter Kurs“ fehlt. **27/27 Mutationen belegen deshalb nicht die behauptete EOD-Garantie.** Ergänzen würde ich außerdem einen Folgetagsbalken mit abweichendem Kurs sowie fehlendes `regularMarketTime` und ungültige Schlusswerte.

Für die Freigabe unter der geforderten EOD-Garantie braucht es einen belastbaren Finalitäts-/Aktualitätsnachweis. Eine Prüfung gegen die tatsächliche Schlusszeit wäre strenger, müsste bei Handelsstopps aber bewusst konservativ verwerfen oder eine andere Bestätigung verwenden. Der erfolgreiche Vergleich aller 20 Ticker bestätigt den untersuchten Lauf, nicht diese Fehlerfälle.

Read-only geprüft, keine Dateien geändert. Tests nicht ausgeführt: Das lokale Python ist nicht ausführbar; der Mutationsrunner verändert außerdem Quelldateien. **27/27 nicht unabhängig bestätigt.**
