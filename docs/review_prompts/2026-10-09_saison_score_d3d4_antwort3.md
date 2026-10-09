**Keine neuen freigabeblockierenden Befunde. Beide offenen Befunde aus Runde 2 sind behoben.**

1. **Zusammenführung bestätigt:** [decade-compute.js:529](/C:/dev/Seasonaledge/landing/js/decade-compute.js:529) übernimmt die Vollhistorie und ergänzt ausschließlich Tage nach deren Ende. Die dafür vorausgesetzte Sortierung liefert [app.js:756](/C:/dev/Seasonaledge/landing/js/app.js:756). Node-Probe bestanden: Vollhistorie gewinnt bei Überlappung, jüngerer Tag wird ergänzt; leere Antwort, Ladefehler und fehlende Kursquelle lehnen ab.

2. **Abgleich nach dem Schreiben bestätigt:** [saison_score_betrieb.py:78](/C:/dev/Seasonaledge/shared/saison_score_betrieb.py:78) schreibt zuerst konfliktignorierend, liest anschließend den gespeicherten Eintrag und vergleicht ihn. Damit erkennt auch der unterlegene parallele Writer seine Abweichung. Ein fehlender Eintrag löst vor dem Scanner-Upsert einen `RuntimeError` aus.

3. **Kein Transportgenauigkeitsproblem beim Score:** Die Migration verwendet [DOUBLE PRECISION:46](/C:/dev/Seasonaledge/scripts/sql/scanner_saison_score_2026_10.sql:46). Der Rechenkern liefert bereits [auf eine Dezimalstelle gerundete Scores:258](/C:/dev/Seasonaledge/shared/saison_score.py:258); alle 101 möglichen Werte von 0 bis 10 bestanden die Node-Roundtrip-Probe mit 15 signifikanten Stellen. Zusätzlich toleriert der [Rücklesevergleich:90](/C:/dev/Seasonaledge/shared/saison_score_betrieb.py:90) Differenzen unter `1e-9`. Echte Score-Schritte von `0,1` bleiben erkennbar; `None` wird nicht mit einer Zahl gleichgesetzt.

4. **Code-Version verhält sich wie gewünscht:** [code_version():10](/C:/dev/Seasonaledge/shared/saison_score_betrieb.py:10) bildet einen Inhaltshash des Rechenkerns. Ändert sich dieser bei gleichem Protokollschlüssel, meldet der [Vergleich:64](/C:/dev/Seasonaledge/shared/saison_score_betrieb.py:64) eine Abweichung; der erste Eintrag bleibt erhalten. Das ist die ausdrücklich gewünschte Meldung. Änderungen außerhalb des Rechenkerns ändern diese Version nicht.

Read-only geprüft, keine Dateien geändert und keine Live-Datenbank angesprochen. Python-Laufzeittests waren wegen des nicht ausführbaren Python-Launchers nicht möglich; Schreibreihenfolge und Fehlerpfade wurden statisch geprüft.

**FREIGABE: ja**
