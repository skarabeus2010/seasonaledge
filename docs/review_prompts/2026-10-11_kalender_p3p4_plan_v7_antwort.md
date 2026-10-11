**Urteil**

**V9 noch nicht als Bauplan freigegeben.** Der erweiterte Sicherungsumfang schließt den zweiten Befund aus Runde 6. Die Releasebindung hat noch zwei Lücken.

**Befunde**

1. **Hoch — Der Bootstrap ruft sich vor seiner Initialisierung auf.** Auch `methode.js` fällt unter „jede eigene JS-Datei“ und muss zunächst `SA.__release(...)` aufrufen, obwohl es diese Funktion selbst bereitstellt ([v7:9](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v7.md:9)). Die jsdom-Vertragsprobe endet mit `TypeError`; der Prüfer wird nicht definiert.

2. **Hoch — Ein Releasefehler stoppt nur das betroffene Skript.** Bereits registrierte Rechner und nachfolgende Inline-Skripte bleiben ausführbar ([v7:12](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v7.md:12)). Im Speicher lieferte der echte Inline-Enginekern nach einer späten Abweichung weiterhin ein Ergebnis — selbst mit `releaseOk=false` und sichtbarem Fehler beim zweiten Ladeversuch.

**Auflagen**

- Bootstrap gesondert festlegen: Prüfer initialisieren, anschließend seine eigene Kennung prüfen; die Ausnahme im Einbindungswächter ausdrücklich abbilden.
- Releasefehler dauerhaft für die gesamte Seite sperren: Inline-Rechner, bestehende Callbacks und laufende Berechnungen absichern. Späte Abweichung und zweiten Ladeversuch ausdrücklich mit „keine Rechnung/Ergebnisübernahme“ prüfen.

Ausschließlich gelesen und jsdom-Vertragsproben im Speicher ausgeführt; nichts geschrieben. Keine Server-Probeläufe.
