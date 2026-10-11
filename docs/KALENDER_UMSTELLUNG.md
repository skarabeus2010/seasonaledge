# Tage nach Börsenkalender — Umstellung der Leser und Seiten (P3/P4)

Stand 2026-10-11 · **Status: Bauplan freigegeben (Codex, 9 Runden), Umsetzung beginnt mit V1** · nichts aktiv.

Vorgeschichte: [Plan v1–v7](review_prompts/2026-10-10_xetra_tdoy_plan_v7.md) (P1a/P1b/P2 live, siehe CLAUDE.md v66.10/66.11).

## Nutzerentscheidungen
- 2026-10-10: Tage nach Börsenkalender ausweisen, auch Statistiken; Weg A (isoliert bauen, gemeinsam umschalten).
- 2026-10-11: veröffentlichte Zahlen, die sich ändern, **nachrechnen und mit `updated:` aktualisieren**; P3/P4 starten;
  **Umschaltung im Wartungsfenster** (einmalig ~15–20 Min.); P5 (historische DB-Spalte) bleibt eigene Freigabe.

## Verbindliche Grundlagen
- **Matrix A, Verträge B1–B7, Prüfplan C:** [Codex-Ausarbeitung](review_prompts/2026-10-11_kalender_p3p4_matrix_antwort1.md)
  — jede Stelle, die Tagesnummern, Handelstag-Offsets, Kalenderereignisse oder Ticker→Börse nutzt (Pakete P3a–P3m),
  dazu Tagesnummer, Rendite/Fenster (V4), Kurve, Ereignis, Zieltermin, Statistikgeneration, veröffentlichte Zahlen.
- **Bauplan:** [v2](review_prompts/2026-10-11_kalender_p3p4_plan_v2.md) → [v3](review_prompts/2026-10-11_kalender_p3p4_plan_v3.md)
  (Leser-/Produktionsmethode, Erzeuger in V7, V9) → [v4](review_prompts/2026-10-11_kalender_p3p4_plan_v4.md)
  (Produktionssperre, Wartungsfenster) → [v5](review_prompts/2026-10-11_kalender_p3p4_plan_v5.md) (Aktivierungspfad,
  Assetsperre, Rückweg-Reihenfolge) → [v6](review_prompts/2026-10-11_kalender_p3p4_plan_v6.md) (Releasekennung,
  Datenartefakte, nginx-Mounts, Probe-Compose) → [v7](review_prompts/2026-10-11_kalender_p3p4_plan_v7.md) (Kennung je
  Datei, Sicherungsumfang) → [v8](review_prompts/2026-10-11_kalender_p3p4_plan_v8.md) (Bootstrap, seitenweite Sperre)
  → [v9](review_prompts/2026-10-11_kalender_p3p4_plan_v9.md) (Sperre in laufenden Ladungen) —
  [Freigabe](review_prompts/2026-10-11_kalender_p3p4_plan_v9_antwort.md). Spätere Versionen ersetzen frühere nur in
  den genannten Punkten.

## Bauphasen
| Phase | Inhalt | Status |
|---|---|---|
| V1 | Fundament: Ereigniskatalog (B4), Sitzungshelfer Python+JS (B1/B2/B5), Methodenschalter (Leser/Produktion), Produktionssperre, Einbindungswächter, `[ohne-deploy]`, Releasekennung + Sperre (v6–v9) | offen |
| V2 | Browserkern: `SA.holidays`-Fassade, Header, Converter | offen |
| V3 | Ereignisse: Feiertage, Dashboard-Ereignisse, OPEX/VIX (Cboe), Kalender/ICS, Flows | offen |
| V4 | Fenster/Renditen/Kurven/Strategien (P3i/P3j/P3k) mit Python-Zwillingen | offen |
| V5 | Backtest-Engine | offen |
| V6 | Statistikgeneration (SQL durch Nutzer), Produktion `kalender_v1`, Leser P3d | offen |
| V7 | Veröffentlichte Zahlen: Snapshots, Faktenblätter, Erzeugerumbau | offen |
| V8 | Methodenregister bestandsgeschützter Pfade | offen |
| — | P5 (Nutzerfreigabe), P6 | offen |
| V9 | Aktivierung im Wartungsfenster (Probelauf auf `/opt/seasonaledge-probe` vorher) | offen |
| — | Aufräumen (alter Zweig) | offen |

## Gemessen (Vorab)
Down-Month-ToM-Reversal (Blog 2026-07-31 + Engine-Preset), SPY bis 2026-07-31: veröffentlichter Stand exakt
reproduziert (n 186/78, WR 68,3/71,8 %, PF 1,80/2,39, Sharpe 0,214/0,336, DD 22,3/18,3 %). Mit TDOM nach
NYSE-Kalender: n 186/77, WR 70,4/72,7 %, PF 1,85/2,44, Sharpe 0,223/0,345, DD 21,6/18,1 %; 181 Ereignistage verschieden.
