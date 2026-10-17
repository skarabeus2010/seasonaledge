# Codex-Antwort Runde 2 (/skew, 2026-10-17)

- **P2 – Gescheiterte Ticker können über erhaltene Session-Ränge wieder erscheinen:** [skew.html:816](C:/dev/SeasonalEdge/landing/pages/skew.html:816). Bei einem erneuten Cron-Lauf für dieselbe Session bleibt die frühere Historienzeile eines inzwischen gescheiterten Tickers erhalten; `rang_gesamt` berechnet daraus weiterhin Ränge. Die neue CATMAP-Ergänzung lässt diesen Ticker nun auch im Kategorie-Radar und den Extremlisten erscheinen. Weil er im Radar steht, verschwindet er zugleich aus der Fehlliste. Reproduziert mit A/B als Messwertzeilen und gescheitertem C: Anzeige **„2 von 3 Tickern“**, C in Radar und Extremliste, aber ohne Fehlermeldung und ohne Tabellenzeile. Radar und Extremlisten sollten zusätzlich die Zugehörigkeit zum aktuellen Messwertbestand prüfen. Ein Wächterfall „erfolgreicher Lauf, danach Ausfall derselben Session“ fehlt.

Keine weiteren Befunde: Die zusätzlichen `cats`-Felder brechen keinen gefundenen Verbraucher. Die Sticky-Zelle ist durch Kartenhintergrund und Gradient deckend; die Hervorhebung bleibt erhalten. Tabellen- und Sprachproben bestehen, ebenso die ergänzenden lesenden Kategorieproben. Den schreibenden Mutationstest habe ich gemäß Read-only-Vorgabe nicht ausgeführt.

**KEINE FREIGABE**
