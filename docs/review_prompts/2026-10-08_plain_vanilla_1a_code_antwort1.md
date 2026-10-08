# Codex-Antwort: Code 1A, Runde 1


codex
Die 34 Wächterprüfungen bestehen; auch der Kalendervergleich 2000–2035 ergibt keine Abweichungen. Folgende Fehler bleiben:

1. **P2 – Sonderschließungen erzeugen doppelte Feiertagstrades.** [strategy-compute.js:287](C:/dev/Seasonaledge/landing/js/strategy-compute.js:287)  
   **Eingabe:** NYSE-Kursreihe für 2001. Die vier Schließtage 11.–14. September erzeugen in `calc_one_day_holiday` vier identische Trades vom 07.09. zum 10.09.; Rendite und Tradezahl werden mehrfach verbucht. UHTS ist ebenfalls betroffen. **Änderung:** Sitzungskalender und Strategie-Feiertagsliste trennen; außerplanmäßige Schließungen nicht automatisch als vorhersehbare Handelsanlässe übernehmen.

2. **P2 – Historische Termine im letzten Datenmonat werden entgegen E1 umgestellt.** [strategy-compute.js:145](C:/dev/Seasonaledge/landing/js/strategy-compute.js:145)  
   **Eingabe:** NYSE-Zeilen September bis 07.10.2026, jedoch ohne 01.10. Der bisherige Zweiter-Handelstag-Trade 02.10.→05.10. entfällt: `_amRand` aktiviert den Kalender für den gesamten Oktober, und der kalendarische Einstieg wird als fehlend verworfen. **Änderung:** Bereits historische Ziele weiterhin anhand der Kurszeilen bestimmen; Kalenderentscheidungen auf tatsächlich am/hinter dem Datenrand liegende Ziele begrenzen. Ebenso im Python-Zwilling.

3. **P2 – Stops können ungültige Ausführungskurse realisieren.** [strategy-compute.js:950](C:/dev/Seasonaledge/landing/js/strategy-compute.js:950), [strategy-compute.js:988](C:/dev/Seasonaledge/landing/js/strategy-compute.js:988)  
   **Eingabe:** Close-Reihe `100, 0, 110`, Einstieg erste und regulärer Ausstieg letzte Zeile, Stop 8 %. Beide Stoparten erzeugen einen abgeschlossenen Trade zum Preis 0 mit −100 %. `null` löst ebenfalls aus. **Änderung:** Auch Stopkurse vor Auslösung/Ausführung auf endliche positive Zahlen prüfen und ungültige Fälle protokollieren.

4. **P2 – Stopwechsel aktualisiert die sichtbare Signal-Streak nicht (E9).** [plain-vanilla.html:221](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:221)  
   **Eingabe:** Letzter geschlossener Trade +10 %, danach offener Trade −20 %; anschließend Fixed-Stop 8 % einschalten. Die Kennzahlen berücksichtigen den realisierten Verlust, die Signaltabelle behält ihre zuvor gerenderte Gewinnserie. Alle drei Stop-Handler rufen nur `renderSelected()` auf. **Änderung:** Auch `renderSignals()` aktualisieren und den tatsächlichen Ereignispfad im Wächter prüfen.

5. **P2 – Veraltete Daten unterdrücken weiterhin keine Signale (E1/E7).** [plain-vanilla.html:498](C:/dev/Seasonaledge/landing/pages/plain-vanilla.html:498)  
   **Eingabe:** SPY-Kurse bis 31.12.2025, Stichtag 08.10.2026. `auswerten()` liefert `veraltet:true`; der ausgeführte Seitenrenderer zeigt trotzdem 54 kommende Signale. Er übernimmt ausschließlich die Streak. **Änderung:** Den Veraltet-Status vor der Signalerzeugung auswerten und die aktive Signaldarstellung entsprechend unterdrücken.

6. **P2 – Python erzeugt einen Santa-Einstieg bereits im Oktober.** [plain_vanilla.py:170](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:170), [plain_vanilla.py:393](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:393)  
   **Eingabe:** NYSE-Kurse 01.01.–07.10.2026. Python liefert jetzt einen offenen Santa-Trade ab 05.10.2026: Der unveränderte Einstieg nimmt die drittletzte vorhandene Zeile; der neue Exit-Zustand macht daraus erstmals einen Trade. JS liefert korrekt keinen Einstieg. **Änderung:** Den Santa-Einstieg am Datenrand ebenfalls zustandsbewusst relativ zu Thanksgiving bestimmen.

7. **P2 – Neuer Python-Zustandstyp lässt Ultimate Monthly abstürzen.** [plain_vanilla.py:112](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:112), [plain_vanilla.py:621](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:621)  
   **Eingabe:** NYSE-DataFrame bis 07.10.2026 mit `Close`, `year`, `month`. `calc_ultimate_monthly()` vergleicht einen `Timestamp` mit `jan5_next == "noch_nicht_faellig"` und wirft `TypeError`. **Änderung:** Sämtliche direkten Konsumenten der geänderten Helfer auf Zustandstexte anpassen; diese dürfen nicht in Datumsvergleiche gelangen.

8. **P2 – `None`-Sharpe bricht den Python-Seitenkonsumenten.** [plain_vanilla.py:1275](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:1275), [09_Plain_Vanilla_Strategien.py:318](C:/dev/Seasonaledge/pages/09_Plain_Vanilla_Strategien.py:318)  
   **Eingabe:** Strategie mit einem bis vier abgeschlossenen Trades im Vergleichsbereich. `stats.get("sharpe", 0)` liefert `None`; `:.2f` wirft `TypeError`. **Änderung:** Auch diesen Konsumenten auf eine explizite `None`-Anzeige umstellen.

9. **P2 – Der verpflichtende Kandidatenvertrag E8 fehlt.** [strategy-compute.js:243](C:/dev/Seasonaledge/landing/js/strategy-compute.js:243), [probe_plain_vanilla_messlauf.js:92](C:/dev/Seasonaledge/scripts/js/probe_plain_vanilla_messlauf.js:92)  
   **Eingabe:** Offener September-Vermeidungs-Trade bis 07.10.2026. Es fehlen `zustand_einstieg`, Regeltermin, Bewertungsstichtag und letztes Kursdatum am Kandidaten; geschlossene Trades besitzen auch keinen expliziten Ausstiegszustand. Nicht ausgeführte Einstiege werden ohne Regeltermin protokolliert. **Änderung:** Die E8-Felder bei der Terminauflösung erhalten und vollständig ins Messformat übernehmen; entsprechend auch in Python.

10. **P2 – Messlauf umgeht die neue Datenende-Auswertung.** [probe_plain_vanilla_messlauf.js:86](C:/dev/Seasonaledge/scripts/js/probe_plain_vanilla_messlauf.js:86)  
    **Eingabe:** Snapshot-Stichtag mehr als zehn Sitzungen nach letzter Kurszeile, laufender Trade ohne Stopauslösung. Die Seite entfernt ihn über `auswerten()`; der Messlauf zählt ihn weiterhin als offen, weil er direkt Strategie und Stops aufruft. **Änderung:** Den aktuellen Messlauf über `auswerten()` führen und `unvollstaendig`, Veraltet-Status sowie Ausschlussgründe ausgeben.

FREIGABE: nein
