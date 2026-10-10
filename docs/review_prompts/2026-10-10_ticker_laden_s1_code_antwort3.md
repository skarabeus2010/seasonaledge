**Urteil:** Mit Auflagen, noch keine Freigabe für die Seitenmigration. Die vier R2-Korrekturen sind eingebaut. Unveränderte Node-Proben: **110/110 Prüfungen**, 26 Abschnitte, jeweils Exit 0 und `ende: true`. Zusätzliche Poolprobe mit Wiederholung besteht in beiden Abbruchvarianten.

**Befunde**

1. **P2 – Eingefangener Absturz zählt als fachlicher Nachweis.** [probe_kurse.js:283](C:/dev/SeasonalEdge/scripts/js/probe_kurse.js:283): Beide `.catch(x => x)` umgehen die Ausnahmeprüfung. Zusatzprobe mit `TypeError` beim Lesen von `open`: „wartende Vereinigung zweier Grenzen“ wird rot, aber `ausnahmen` bleibt leer und `ende` wahr. Der Mutationstest würde diesen Absturz als gefangen akzeptieren.

2. **P2 – Unbehandelte Ablehnung am Abschluss verschwindet.** [probe_kurse.js:523](C:/dev/SeasonalEdge/scripts/js/probe_kurse.js:523): `process.exit(0)` kann vor dem Ereignis `unhandledRejection` laufen. Zusatzprobe in Abschnitt 9: unbehandelte `TypeError`-Ablehnung, trotzdem **3/3 grün**, `ausnahmen: []`, `ende: true`. Der neue Handler greift hier nicht.

Ein isolierter Hänger darf als eigener roter Befund zählen, auch vor den Fachprüfungen: Er macht den Lauf bereits erfolglos. Die übersprungenen Prüfungen gelten dadurch allerdings nicht als bestanden.

**Auflagen**

- Alle abgefangenen Nicht-`KursFehler` als Ausnahme erfassen, einschließlich Abschnitt 10b.
- Vor dem Abschluss mindestens einen Ereignisschleifendurchlauf zulassen und unbehandelte Ablehnungen auswerten; beide Gegenproben müssen zuverlässig scheitern.
- Danach erneute Abnahme.

Nichts geschrieben; Mutationstest nicht ausgeführt. Die gemeldeten **31/31 Mutationen** wurden nicht nachgeprüft.
