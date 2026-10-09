# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

1. **Hoch – [dekadenzyklus.html:295](C:/dev/Seasonaledge/landing/pages/dekadenzyklus.html:295): Rückwechsel lässt das Ladeoverlay dauerhaft stehen.**  
   **Fall:** A ist geladen, B startet, anschließend wird A erneut gewählt. A wird aus `tickerCache` wiederhergestellt, aber der Cachepfad beendet sich ohne `hideLoading()`. Die neue Kennung verwirft anschließend beide möglichen Rückrufe von B einschließlich deren Aufräumen. Das Overlay „Lade B …“ verdeckt dauerhaft die Ansicht. Am tatsächlichen `loadTicker`-Code mit Speicher-Stubs für Erfolg und Fehler von B reproduziert.  
   **Änderung:** Im Cachepfad nach `init()` und vor `return` ebenfalls `hideLoading()` aufrufen. Den Ablauf A → B → A mit noch ausstehendem B als Verhaltenstest ergänzen.

Die übrigen R5-Korrekturen sind vorhanden. 23 Inline-Skripte syntaktisch geprüft; `git diff --check` sauber. Die gemeldeten 38/38 und 22/22 wurden nicht erneut ausgeführt. Nur gelesen; Teil D ausgeschlossen.

FREIGABE: nein
