# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

1. **Hoch — [dashboard.html:2277](C:/dev/Seasonaledge/landing/pages/dashboard.html:2277): Vorzeitiger Rücksprung entwertet laufende Arbeit.**  
   **Fall:** A ist geladen, B startet, anschließend wird A erneut ausgewählt. Die neue Kennung verwirft B, aber der Rücksprung wegen `ticker === currentTicker` lässt das Dashboard dauerhaft ausgeblendet mit „Lade B…“. Auch erneutes Auswählen von A während dessen Radar-Nachladen entwertet das Ergebnis und lässt „Wird berechnet…“ stehen. Beide Fälle am tatsächlichen Funktionscode mit Speicher-Stubs reproduziert.  
   **Änderung:** Angezeigten und angeforderten Ticker unterscheiden. Identische Auswahl ohne laufenden Wechsel darf die Kennung nicht ändern; Rückwechsel müssen laufende Abrufe entwerten und Ansicht sowie Radar wiederherstellen. Entsprechende Rücksprünge in Monats- und Dekadenzyklus mitprüfen.

2. **Mittel — [dashboard.html:2304](C:/dev/Seasonaledge/landing/pages/dashboard.html:2304), [overnight.html:676](C:/dev/Seasonaledge/landing/pages/overnight.html:676): Fehler-Rückrufe bleiben ungeschützt.**  
   **Fall:** B startet, C startet und wird erfolgreich angezeigt; anschließend scheitert B. Dessen `catch` zeigt trotzdem einen Fehler in der C-Ansicht. Im Dashboard reproduziert. Alle sieben Seiten prüfen die Kennung ausschließlich im Erfolgszweig; alte Fehler können auch den Ladeindikator eines neueren Abrufs ausblenden.  
   **Änderung:** Auch jeden zugehörigen Fehler-Rückruf vor UI-Änderungen mit `SA.ladeKennung.aktuell(_lk)` absichern.

Cache-Zusammenführung, Schalttagfilter und Fehler-Fallback durch Speicherproben bestätigt; 23 Inline-Skripte syntaktisch geprüft, `git diff --check` sauber. Die gemeldeten 37/37 und 21/21 nicht erneut ausgeführt. Ausschließlich gelesen; Teil D ausgeschlossen.

FREIGABE: nein
