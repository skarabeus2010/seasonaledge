**Urteil: mit Auflagen.** Noch keine Freigabe für die Seitenmigration. Die Korrekturen aus Runde 1 sind vorhanden; die unveränderte Node-Probe besteht **80/80**, mit Endmarker. Nichts geschrieben, Mutationstest nicht ausgeführt.

**Befunde**

1. **P2 – Poolwartende Anfragen haben keine Frist.** [kurse.js:135](C:/dev/SeasonalEdge/landing/js/kurse.js:135): Die Timeout-Uhr startet erst nach der Platzvergabe. Enden vier Transporte nie, hängen weitere Anfragen und Wiederholungen dauerhaft. Zusatzprobe mit 20-ms-Frist ohne Wiederholungen: vier Ablehnungen, fünfter Aufrufer bleibt wartend — sowohl ohne `AbortController` als auch bei ignoriertem Abbruch. Mit einer Wiederholung bleiben alle fünf Aufrufer wartend.

2. **P2 – Nachweis gegen verspätete Veröffentlichung greift zu spät.** [probe_kurse.js:410](C:/dev/SeasonalEdge/scripts/js/probe_kurse.js:410): Die Vergleichsgeneration wird erst nach Abschluss aller Ladungen erfasst. Eine verspätete Antwort könnte zuvor einen Bestand veröffentlichen, den die erfolgreiche Wiederholung anschließend ersetzt. Die Prüfung bliebe grün. Im aktuellen Produktionscode sehe ich diese Veröffentlichung nicht; der Wächter beweist ihren Ausschluss jedoch nicht.

3. **P2 – Wächter verlangt weder erfolgreichen Prozessabschluss noch Endmarker.** [verify_kurse.py:49](C:/dev/SeasonalEdge/scripts/verify_kurse.py:49): Gültiges JSON mit mindestens 77 grünen Prüfungen genügt, auch bei Exit ≠ 0 oder fehlendem `ende`. Das widerspricht dem geforderten vollständigen Abschluss.

4. **P2 – Abschnittsfrist isoliert einen Hänger nicht.** [probe_kurse.js:494](C:/dev/SeasonalEdge/scripts/js/probe_kurse.js:494): `Promise.race` beendet `fn()` nicht. Nach Fristablauf kann der alte Abschnitt weiterlaufen und nach `neu()` Netz-, Pool- und Prüfzustand späterer Abschnitte verändern. Acht Sekunden bieten nominal genügend Abstand zu den 1-s-Wartezeiten und `spaet:150`; unter starker Rechnerlast ist die Fortsetzung dennoch nicht robust.

**Auflagen**

- Poolwartezeit begrenzen und abgelaufene Wartende entfernen; dauerhaft offene Transporte mit beiden Abbruchvarianten prüfen.
- Verspätete Veröffentlichung **vor** erfolgreicher Wiederholung prüfen; hierfür eine gezielte Mutation ergänzen.
- Exit 0 und `ende === true` zwingend verlangen.
- Abschnitte mit eigenem Zustand isolieren; verspätete Fortsetzungen dürfen Folgeprüfungen nicht beeinflussen. Timer möglichst kontrolliert prüfen, reale Wartezeit separat messen.
- Danach erneute Abnahme vor der Seitenmigration. Die gemeldeten **28/28 Mutationen** wurden hier nicht nachgeprüft.
