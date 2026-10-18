# Kalender V2 — Antwort Codex auf Entwurf v2 (2026-10-18)

**Urteil**
Noch keine Freigabe als Bauvorlage. Die sieben Befunde aus Runde 1 sind im Entwurf aufgegriffen; drei Vertragslücken bleiben. B1, B5, B6 und B7 sind konzeptionell erledigt.

**Befunde (P1/P2)**

- **P2 – Converter-Prüfung am falschen Auslieferungspfad:** B2/B3 verlangen `seo/output/…`. Tatsächlich bedient nginx `/tools/` direkt aus `seo/tools/` ([nginx.conf:295](/C:/dev/SeasonalEdge/deploy/nginx.conf:295)). Einbindungs-, Release- und jsdom-Prüfung müssen diese tatsächlich ausgelieferte Datei erfassen; ein neuer Build-Schritt muss sie dort erzeugen.
- **P2 – Bundle-Spannen gelten nicht für `alt`:** B3 erklärt sie methodenneutral. Im ausgeführten Original-Converter ergibt 2023 jedoch TDOY 260, im Bundle 250; dessen NYSE-Jahresspanne über 2000–2030 beträgt 248–253. Ursache ist die auf 2024–2027 begrenzte Alt-Liste ([Converter:237](/C:/dev/SeasonalEdge/seo/tools/trading-day-converter.html:237)). Texte müssen Methode und Messzeitraum benennen oder auf solche Spannen verzichten.
- **P2 – Statusgrenzen unvollständig:** „Erstes/letztes `belegt`-Jahr je Börse“ ist für EURONEXT, MILAN, SIX, STOCKHOLM, OSLO und KRX unmöglich; CRYPTO/FOREX bleiben `konvention` ([exchange_holidays.py:474](/C:/dev/SeasonalEdge/shared/exchange_holidays.py:474)). Alle vorhandenen Statusübergänge samt Nachbarjahren und konstante Statusfälle ausdrücklich prüfen.

**Antworten 1–3**

1. Ja, die drei Ebenen reichen nach Ergänzung der Statusfälle. Die unabhängigen Sitzungslisten müssen auch Nummern, Rückwärtsnummern, inverse Helfer und Periodensummen bestimmen, nicht nur Offenheit.
2. Ja, als zusätzliche unabhängige Referenz neben den bestehenden historischen Sollfällen. Für CRYPTO/FOREX ist die dokumentierte Konvention die Referenz.
3. Ja, Texte bereits in V2 korrigieren; die geplanten Bundle-Spannen sind jedoch keine methodenneutralen Grenzen.

**Auflagen**

- Die drei Befunde im Bauvertrag berichtigen; danach ist die Architektur als Bauvorlage tragfähig.
- Alt-Momentaufnahme vor Änderungen einfrieren; Rechnerausgabe und ausdrücklich freigegebene Textänderungen getrennt prüfen.
- Bestehende Kalenderwächter erhalten; Mutationen müssen benannte Vertragsverletzungen nachweisen.
- Read-only geprüft und Original-JS ausgeführt; keine Dateien geändert. Vollständige Gate-/Mutationstests waren nicht Gegenstand dieser Entwurfsprüfung.
