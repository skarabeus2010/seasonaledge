# Codex-Antwort (Schlussantwort; Rohprotokoll nicht im Repo)

1. **Mittel – Rang-Balken im Dashboard bleibt unsichtbar.**  
   [dashboard.html:1436](C:/dev/Seasonaledge/landing/pages/dashboard.html:1436): `renderAnomalyCard()` ruft `anomalieHtml()` auf, aber nicht `_ensureAnomalyCss()`. Die Balken-Styles werden ausschließlich durch `renderAnomalyInto()` eingebunden, das im Dashboard nicht läuft.  
   **Fall:** Berechenbarer Radarwert mit `rang: 75`: „75 / 100“ erscheint; Balken und Markierung fehlen wegen fehlender Höhe, Hintergrundfarbe und Positionierung. Am tatsächlichen Dashboard-Renderer bestätigt: Balken-HTML vorhanden, CSS-Initialisierung **0 Aufrufe**.  
   **Änderung:** `_ensureAnomalyCss()` im Dashboard vor dem Rendern aufrufen. Den Darstellungstest um die CSS-Initialisierung ergänzen; die Prüfung auf vorhandene HTML-Klassen reicht nicht.

Die übrigen Korrekturen sind nachvollzogen. Validierung: Radar **31/31 ohne Snapshot**, vollständiger Zwillingswächter einschließlich sechs Zeitzonen bestanden. Snapshot- und Mutationstests nicht erneut ausgeführt. Keine Dateien geändert.

FREIGABE: nein
