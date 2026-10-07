# Review-Auftrag: Seite /polymarket — Prüfung + Erweiterungsvorschläge, Runde 1

Repo `C:\dev\Seasonaledge` (öffentliches Repo; keine Server-Interna in die Antwort). Antwort auf Deutsch. Live-Seite:
https://seasonalpha.ai/polymarket und https://seasonalpha.ai/en/polymarket (Websuche/Abruf erlaubt, nur lesend).
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

## Gegenstand
- Frontend: `landing/pages/polymarket.html`, `landing/js/polymarket.js`; i18n `landing/i18n/de.json`/`en.json`.
- Daten: `shared/polymarket_data.py`, `shared/polymarket_markets.yaml`, `shared/brier_score.py`,
  `scripts/polymarket_refresh.py`, `polymarket_discover.py`, `polymarket_backfill.py`, `polymarket_scrape_resolved.py`,
  `compute_brier_stats.py`, SQL `scripts/create_polymarket*_tables.sql`; Betrieb: `.github/workflows/polymarket_*.yml`,
  `brier_compute.yml`, `deploy/systemd/sa-polymarket-intraday.*`. Doku: `docs/POLYMARKET.md`.
- Kontext: `docs/research/PREDICTION_MARKETS_2026-10.md` (heute erstellt: Polymarket sperrt Deutschland, GGL stuft
  Gesellschaftswetten als illegal ein, Teilnahme strafbar; Kalshi-/Polymarket-Gebühren; Auflösungsregeln
  unterscheiden sich zwischen Plattformen).

## Teil A — Review (je Befund Schwere + Datei:Zeile + Änderung)
Die drei Standardfragen unseres Hauses:
1. **Zwillinge:** Rechnen Python und JS dasselbe (Divergenz-Score, Brier, Wahrscheinlichkeiten, Zeitreihen)?
2. **Fehlende Daten:** Wird ein fehlender/alter Wert als aktuell angezeigt? Wie alt dürfen Kurse sein, wird das Alter
   gezeigt? Was bei aufgelösten, pausierten oder aus der API verschwundenen Märkten?
3. **Fehlschläge:** Meldet ein gescheiterter Refresh sich als Fehler (Exit-Code, refresh_log, Health-Check) oder als
   grüner Lauf mit alten Zahlen?
Dazu:
4. **Methodik:** Brier-Score/Kalibrierung korrekt (welche Wahrscheinlichkeit zu welchem Zeitpunkt vor Auflösung,
   Stichprobenauswahl, Survivorship)? Divergenz-Score: was misst er, ist die Aussage gedeckt? Mittelkurs vs. letzter
   Trade vs. Bid/Ask; dünne Märkte.
5. **Texte und Recht:** Angesichts der deutschen Rechtslage — gibt es Formulierungen, Links oder Buttons, die zur
   Teilnahme auffordern oder sie erleichtern (Affiliate, „jetzt handeln", Referral)? Ist klar, dass die Seite Daten
   zeigt und kein Angebot ist? Hinweis zur Rechtslage für deutsche Nutzer vorhanden/angemessen? Zu starke Aussagen
   („der Markt weiß", „Prognose")? Kein KI-Duktus, echte Umlaute.
6. **EN-Fassung, SEO, Barrierefreiheit, Mobile, XSS** (Marktnamen kommen von außen → Escaping in innerHTML und
   ApexCharts-Seriennamen).

## Teil B — Erweiterungen (priorisiert)
Schlage Erweiterungen vor, je mit Nutzen für den Leser, Datenquelle (frei/kostenpflichtig, API-Bedingungen), Aufwand
(S/M/L), Risiko. Denk insbesondere an:
- Vergleich mit Kalshi (öffentliche Marktdaten-API?) als **reine Daten** — Preisabstand je Ereignis plus
  Gegenüberstellung der Auflösungsregeln; Hinweis, dass ein Abstand keine Arbitrage ist.
- Verknüpfung mit unseren Daten: Fed-Märkte gegen FedWatch/Fed-Funds-Futures, Krypto-Märkte gegen Optionen (implizite
  Wahrscheinlichkeit aus unserem Options-Stack), Wahl-Märkte gegen die neue Studie `/wahlen`, Inflationsmärkte gegen
  CPI-Saisonalität.
- Kalibrierung über die Zeit („wie gut lagen Märkte 30/7/1 Tage vor Auflösung"), Liquidität/Volumen-Filter,
  Alerts, Newsletter-Integration, Blog-Snapshots.
Bewerte auch, was wir **nicht** bauen sollten (Rechtslage, Datenqualität, Wartungsaufwand).

Am Ende: Top-5-Prioritätenliste und genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein` (Freigabe = keine Befunde
der Schwere hoch in Teil A).
