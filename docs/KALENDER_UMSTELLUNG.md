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

## Produktionssperre (V1a, `shared/produktionssperre.py`)
- **Pflicht-Läufe** (19, Inventar `PFLICHT`/`AUSNAHMEN` im Modul) laufen in `with produktion("<name>")`: geteilter
  `flock` auf `logs/sperre/produktion.lock`. Ohne Marke `logs/sperre/AKTIVIERUNG` ändert sich nichts.
- **Import-Einstiege:** jedes Pflicht-Skript ruft auf Modulebene `modul_sperre("<name>")` (außer als `__main__`):
  bei Marke scheitert schon der Import, und ein Prozess, der vorher importiert hat, hält den geteilten Lock bis
  Prozessende — `aktivierung_setzen` wartet auf ihn. Damit sind auch Dateiausgaben importierter Bauer
  (`from scripts.build_flows_rebalancing import main; main()`) gesperrt. `produktion()` ist wiedereintrittsfähig,
  ein verschachtelter Name wird gegen die Freigabeliste geprüft.
- **Schreibschutz unabhängig vom Einstieg:** `get_client()` liefert einen geschützten Client; Schreibzugriffe auf
  `GESCHUETZTE_TABELLEN`/`GESCHUETZTE_RPC` werden beim Aufbau und bei `.execute()` geprüft — dort unter dem
  geteilten Lock, sodass eine vor der Aktivierung aufgebaute Anfrage danach nicht schreibt und
  `aktivierung_setzen` auf eine laufende Ausführung wartet. Polymarket, Optionen, `refresh_log` bleiben frei.
- **Kennung** (`SA_AKTIVIERUNG`, über `docker exec -e`) öffnet nur `AKTIVIERUNG_ERLAUBT`: Newsletter `--dry-run`
  (rendert in eine Datei, v5 nannte es `--nur-rendern`), `build_calendar_data --aktivierung`, Abnahmeproben
  `abnahme:<name>` (nur lesen). P5/P6 werden in ihrer Phase mit Schreibrecht eingetragen. Die Kennung wird nach der
  Prüfung aus der Umgebung entfernt — Kindprozesse erben sie nicht.
- **Exit 75 = geplant unterdrückt:** Nachweis in `logs/sperre/unterdrueckt.log` und `refresh_log` (`run_type =
  'produktionssperre'`, vom Health-Check nicht als Lauf gezählt); `SuccessExitStatus=75` in `sa-nightly`/`sa-intraday`,
  die Workflows mit `docker exec` eines Pflicht-Skripts bilden **nur** 75 auf Erfolg ab; `flows_update.yml` nimmt
  ein unterdrücktes Panel aus der Frischeprüfung (die übrigen bleiben geprüft).
  Auch `verify_calendar_rules.py` (importiert `fix_missing_days`) endet während einer Aktivierung mit 75.
- **V9-Abfolge:** `aktivierung_setzen(kennung, frist_s=…)` nimmt den **exklusiven** Lock (wartet auf laufende Läufe; mit Frist `TimeoutError` statt Marke), schreibt
  die Marke und **gibt den Lock sofort frei** — ab dann sperrt die Marke allein, Abnahmeläufe mit Kennung starten
  ohne Warten. Ende: `aktivierung_aufheben(kennung)` (fremde Kennung → Fehler). `install_timers.sh` startet bei
  gesetzter Marke keine Timer.
- Wächter `scripts/verify_produktionssperre.py` (Deploy-Gate, streng), Mutationstest
  `scripts/verify_produktionssperre_mutation.py` — läuft **nur** in einer isolierten Temp-Kopie und weist am Ende
  nach, dass der Projektbaum byte-gleich blieb (der frühere Lauf hatte `market_calendar.*` im Arbeitsbaum neu
  geschrieben).

## Gemessen (Vorab)
Down-Month-ToM-Reversal (Blog 2026-07-31 + Engine-Preset), SPY bis 2026-07-31: veröffentlichter Stand exakt
reproduziert (n 186/78, WR 68,3/71,8 %, PF 1,80/2,39, Sharpe 0,214/0,336, DD 22,3/18,3 %). Mit TDOM nach
NYSE-Kalender: n 186/77, WR 70,4/72,7 %, PF 1,85/2,44, Sharpe 0,223/0,345, DD 21,6/18,1 %; 181 Ereignistage verschieden.
