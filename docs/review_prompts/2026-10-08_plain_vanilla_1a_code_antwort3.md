# Codex-Antwort: Code 1A, Runde 3


codex
Die drei Befunde aus Runde 2 sind behoben. `verify_plain_vanilla_1a.py`: **48/48 bestanden**. Ein weiterer Fehler ist reproduzierbar:

1. **P2 – Python-Seite verwendet für XETRA den NYSE-Kalender.** [plain_vanilla.py:60](C:/dev/Seasonaledge/shared/strategies/plain_vanilla.py:60), Aufrufer [09_Plain_Vanilla_Strategien.py:107](C:/dev/Seasonaledge/pages/09_Plain_Vanilla_Strategien.py:107).  
   **Eingabe:** XETRA-Kurse vom 01.–30.12.2025, Strategie „Nach-Weihnachten“, Close am 29.12. = 117 und am 30.12. = 118. Die Seite setzt keinen Kalenderkontext. Der NYSE-Standard erzeugt deshalb einen offenen Trade mit Regeltermin 31.12.; Statistik und Abschluss-Equity lassen ihn weg. Mit XETRA ist derselbe Trade korrekt am 30.12. mit **+0,8547 % abgeschlossen**.  
   **Änderung:** Die zum ausgewählten Ticker gehörende Börse vor der Strategieberechnung übergeben und den Kontext anschließend zuverlässig zurücksetzen; diesen Fall über den Seitenaufruf prüfen.

FREIGABE: nein
