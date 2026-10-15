**FREIGABE (Code): nein**

**[P2] Die neue Radar-Erklärung verwechselt historischen Rang mit aktueller relativer IV.** Im [DE-Blog](C:/dev/Seasonaledge/blog/posts/2026-09-06_vol-regime-radar-risk-reversal-iv-rank.md:93) und entsprechend auf Englisch steht jetzt: rechts Calls teuer, Puts günstig. Das folgt nicht aus der implementierten Rangberechnung.

Gegenbeispiel, mit den tatsächlichen JavaScript-Funktionen beider Seiten ausgeführt: Eine RR-Historie von `−10, −8, −6, −4, −2` Prozentpunkten ergibt **Rank 100**, auf `/skew` auch **Percentile 100**. Der Punkt steht ganz rechts, obwohl bei aktuell Call-IV 20 % und Put-IV 22 % weiterhin **Puts die höhere IV haben**. Der neue Wächter prüft Beschriftungen und Formeltext, erkennt diese semantische Lücke aber nicht.

Zur ausdrücklichen Beschriftungsfrage: Die vier Spread-Namen passen jetzt zur gewählten **Strategierichtung** „bullish links / bearish rechts“. Die „Angst/Gier“-Beschriftung beschreibt hingegen eine **Marktinterpretation**. Beides lässt sich als bewusst konträre Strategieauswahl vereinbaren, sollte aber ausdrücklich so erklärt werden. Der historische Rang allein beweist weder die aktuell teurere Optionsseite noch Upside-/Downside-Potenzial. Für die Freigabe müssen Erklärung und Wächter diese Unterscheidung abbilden; die gewünschte Quadrantenanordnung kann bestehen bleiben.

Die übrigen Punkte:

- **GEX:** Der konkrete R2-P1 ist geschlossen. Schlusszeitvergleich, konservativer Halbtag-Fallback und die zusätzlichen Attrappenfälle passen zur vereinbarten konservativen Lösung. Die relevanten Mutationen sind vorhanden.
- **Drei VIX-Indizes:** Keine zusätzliche Beanstandung an den Registry-Ergänzungen. Onboarding und historischer Datenabgleich bleiben nachgelagerte, noch offene Nachweise.

Read-only geprüft, keine Dateien geändert. `git diff --check` ohne Fehler; JavaScript-Gegenbeispiel bestätigt. Python ließ sich lokal nicht starten. Die gemeldeten Wächter-Ergebnisse einschließlich **29/29** sind daher nicht unabhängig bestätigt; den quellverändernden Mutationsrunner habe ich nicht ausgeführt.
