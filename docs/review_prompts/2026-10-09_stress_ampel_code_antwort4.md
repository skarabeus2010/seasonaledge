# Codex-Antwort: Code Stress-Ampel, Runde 4

codex
- **P2 – Rücklesefehler bei großen S-Werten bleibt möglich:** [shared/stress_score.py:139](/C:/dev/Seasonaledge/shared/stress_score.py:139), entsprechend [dash-compute.js:313](/C:/dev/Seasonaledge/landing/js/dash-compute.js:313). **Eingabefall:** 776 Schlusskurse zu 100, danach 10.000. Daraus entsteht `S = 1992.336567952312`; der Fake liefert `1992.33656795231` zurück. Der Vollauf bricht reproduzierbar ab. Die Kurse bestehen die Eingabeprüfung; der Volatilitätsanteil begrenzt S nicht auf ungefähr 40. **Änderung:** Gespeichertes S auf höchstens 15 **signifikante** Stellen normalisieren, den Rang weiterhin mit ungerundetem S berechnen und diesen Fall als Vollauf-Regression ergänzen.

Zu den beiden Prüffragen:

- **70/90:** Alle **5.783.905** möglichen Kombinationen aus Referenzgröße 756–2520 und halbzahligem Rangzähler geprüft: Python und JavaScript liefern bitidentische gerundete Scores und dieselbe korrekte Farbe. Hier besteht kein Rundungsproblem.
- **S bis etwa 40:** Zwölf Nachkommastellen reichen aus: zwei Vorkommastellen plus zwölf Nachkommastellen ergeben höchstens 14 signifikante Stellen. Ab vierstelligen S-Werten entfällt diese Garantie.

Die bestehenden Prüfungen bestanden **31/31**, mit Eingabeübergabe im Speicher wegen des schreibgeschützten Temp-Verzeichnisses. Snapshot und Mutationssuite wurden nicht erneut ausgeführt.

FREIGABE: nein
