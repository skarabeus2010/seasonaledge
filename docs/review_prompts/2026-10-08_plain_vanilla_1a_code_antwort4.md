# Codex-Antwort: Code 1A, Runde 4


codex
Die Korrektur aus Runde 3 funktioniert bei sequenziellen Aufrufen; **50/50 Prüfungen bestanden**. Zwei weitere Fehler sind reproduzierbar:

1. **P2 – Gleichzeitige Auswertungen überschreiben den Börsenkontext.** [plain_vanilla.py:74](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:74)  
   **Eingabefall:** Zwei überlappende Aufrufe von `auswerten`: A setzt XETRA, danach B NYSE, bevor A seine Strategie berechnet. Mit den Dezemberkursen aus Runde 3 liefert A wieder einen offenen Post-Christmas-Trade mit Regeltermin 31.12. statt des abgeschlossenen Trades vom 30.12. Nach beiden Aufrufen bleibt außerdem ein fremder Kontext zurück. Der gemeinsame `_KONTEXT` ist durch `try/finally` nicht gegen parallele Streamlit-Sitzungen geschützt.  
   **Änderung:** Kontext pro Aufruf isolieren, beispielsweise mit `ContextVar` und Token-Reset, oder explizit an die Berechnungsfunktionen übergeben. Einen Test mit zwei gezielt überlappenden Aufrufen ergänzen.

2. **P2 – Python-Auswertung behält offene Trades veralteter Datenbestände.** [plain_vanilla.py:80](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:80)  
   **Eingabefall:** NYSE-Kurse 01.09.–31.12.2025, durchgehend Close 100, `september_avoid`, Stichtag 08.10.2026, ohne Stop. `auswerten` liefert weiterhin den offenen Trade ab 30.09.2025 mit `kurs_ausstehend` und Regeltermin 31.08.2026. Die Daten sind deutlich mehr als zehn Sitzungen veraltet; gemäß E1/E7 muss dieser Kandidat aus den aktiven Trades entfernt werden. Die entsprechende Verarbeitung des JS-Zwillings fehlt vollständig.  
   **Änderung:** Nach der Stop-Anwendung den Datenbestand anhand des Börsenkalenders prüfen; verbleibende offene Trades bei mehr als zehn ausstehenden Sitzungen als unvollständig protokollieren und aus `trades` entfernen. Bereits durch Stops geschlossene Trades behalten; Grenzfälle mit zehn und elf Sitzungen prüfen.

FREIGABE: nein
