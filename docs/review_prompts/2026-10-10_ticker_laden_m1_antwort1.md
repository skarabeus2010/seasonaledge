**Urteil**  
Keine Deployfreigabe für M1: Die Migration verändert zusätzlich Rückgaben und Ablehnungen durch die gemeinsame Fehlerbehandlung.

**Befunde**

- **[P2] Radar übernimmt einen fremden Ladefehler.** Im Dashboard startet der Saison-Score die Vollhistorie; das Radar hängt sich daran. Scheitert diese Ladung, rechnet `anomalieMitHistorie` still auf den ursprünglichen 30-Jahres-Kursen. Reproduziert mit echten alten/neuen Ladern und identischen synthetischen Kursen: vorher **n=30, z=0,6760**, nachher **n=29, z=0,6551**; beide Ergebnisse melden „normal“. Ursache: [gemeinsamer Vollhistorienlader](C:/dev/SeasonalEdge/landing/js/decade-compute.js:534) und bestehender Fehlerfallback.
- **[P2] Engere Anfragen können neu abgelehnt werden.** Nach einer erfolgreichen Vollhistorie und TTL-Ablauf lädt eine 30-Jahres-Anfrage erneut die gesamte Historie, weil der alte Bestand vereinigt wird. Reproduziert: Vollabruf HTTP 500, begrenzter Abruf erfolgreich → vorher **7.827 Zeilen**, nachher **Ablehnung**. Siehe [Bedarfsvereinigung](C:/dev/SeasonalEdge/landing/js/kurse.js:304). Das folgt S1, ist aber eine weitere Änderung des Aufruferverhaltens.
- Weitere Änderungen: Vollhistorie jetzt fünf statt vier HTTP-Versuche, Netzwerk-/JSON-Retries, Zeitlimits einschließlich Pool-Wartezeit, strengere Datenprüfung und Cache für leere Reihen. Keine Abhängigkeit der Aufrufer von der Fehlerklasse gefunden.
- Positiv: **65/65 Hüllenprüfungen**, **110/110 Koordinatorprüfungen** bestanden; Baseline-Lader wörtlich bestätigt; Einbindung in **44/44 DE- und 37/37 erzeugten EN-Seiten** korrekt.

**Auflagen**

1. Die beiden Fehlerkopplungen vor dem Deploy auflösen oder ausdrücklich in den Verhaltensvertrag aufnehmen; verkürzte Radar-Ergebnisse dürfen nicht unbemerkt entstehen.
2. Der Hüllennachweis allein reicht hier nicht. Eine Probe der echten Dashboard-Seite nach A4 muss gemeinsame Ladung, Vollhistorienfehler und TTL-Ablauf abdecken.
3. Hüllenprobe und Fixture sind untracked und müssen zum Deploy-Commit gehören.

Nichts geschrieben; Mutationstest nicht ausgeführt.
