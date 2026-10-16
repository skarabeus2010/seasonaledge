**Ein P2-Befund bleibt: Der Rückfall im True-Modus liefert auf Seite und Embed unterschiedliche Kurven.**

[embed.html:105](C:/dev/SeasonalEdge/landing/embed.html:105) berechnet den ungefilterten Durchschnitt aller geladenen Jahre. Bei unterschrittener Mindestmenge ergänzt [embed.html:120](C:/dev/SeasonalEdge/landing/embed.html:120) lediglich den Hinweis. Die Seite verwendet dagegen den gefilterten Durchschnitt innerhalb ihres Zeitfensters ([jahreszyklus.html:1912](C:/dev/SeasonalEdge/landing/pages/jahreszyklus.html:1912)).

Gegenprobe auf den echten Seitenpfaden, `years=10`, IQR, drei Ausreißer, **7/8 vollständige Vorjahre**:

| | Seite | Embed |
|---|---:|---:|
| Durchschnitt aus | 8 Jahren | 12 Jahren |
| Kurvenwert Tag 101 | 100,91 | 100,06 |

Das betrifft den neuen Pfad `saison=true`. Der ausdrücklich ausgenommene bestehende Durchschnittsmodus muss dafür nicht geändert werden. Der neue Rückfalltest prüft nur Reihenname und Hinweis, keine Kurvengleichheit ([verify_true_seasonal_seite.py:126](C:/dev/SeasonalEdge/scripts/verify_true_seasonal_seite.py:126)).

Zu den Prüffragen:

1. **Teilweise behoben.** „Max“ berücksichtigt jetzt Jahre vor 1900: Gegenprobe mit 1897–2025 ergibt auf beiden Seiten **129 Modelljahre**. Auch erfolgreiche IQR-Auswahl stimmt überein: **9 Modelljahre, alle 365 Kurvenwerte identisch**. Der Rückfall bleibt jedoch unterschiedlich. Pressure-Beschriftung und präzisierte Jahresende-Angabe sind vorhanden.

2. **Ja, der Kennzahltest ist jetzt ausreichend unabhängig.** Monatsgrenzen stehen wörtlich im Test; Änderungen und Sollkorrelation werden unabhängig vorgegeben beziehungsweise berechnet ([verify_seasonal_twins.py:796](C:/dev/SeasonalEdge/scripts/verify_seasonal_twins.py:796)). Meine erneute Mutation **„erste elf Monatsgrenzen −1“ in beiden Implementierungen gleichzeitig** wird erkannt: statt Soll **r = 0,6914, 8 Treffer, 7× Plus** entstehen **r ≈ 0,68467, 9 Treffer, 8× Plus**. Auch der Schaltjahrtest schlägt fehl.

3. **Noch keine Freigabe**, bis der True-Modus auch beim Rückfall dieselbe Durchschnittskurve einbettet und eine Seitenprobe das absichert.

Validierung: **43 Seitenprüfungen bestanden**, Block 8 bestanden, `git diff --check` unauffällig. Zusätzliche Gegenproben und Mutationen ausschließlich im Speicher; keine Dateien geändert.

**FREIGABE (Code): nein**
