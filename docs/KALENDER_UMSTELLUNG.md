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

## Releasekennung und Seitensperre (V1b, `landing/js/methode.js`)
Entwurf mit Codex in 6 Runden freigegeben ([v1](review_prompts/2026-10-11_kalender_v1b_entwurf.md) …
[v6](review_prompts/2026-10-11_kalender_v1b_entwurf_v6.md)).
- **Methode:** `SA.kalenderMethode` (JS, unveränderbar) = `shared/kalender_methode.LESER` (Python) = `__SA_METHODE`
  jeder Seite — heute `alt`; gewechselt wird nur in V9.
- **Kennung:** jedes HTML setzt `window.__SA_RELEASE` + `__SA_METHODE` und bindet `methode.js` als erstes eigenes
  Skript ein; jede eigene JS-Datei beginnt mit `window.SA.__release('<kennung>')` (`methode.js` prüft sich zuletzt,
  `boersenkalender.js` erhält die Zeile vom Generator). Lokal bleiben Platzhalter stehen — gleich, keine Sperre.
- **Deploy:** `RELEASE` = voller Commit-Hash, einmal bestimmt; `deploy/release_setzen.py` normalisiert direkt nach
  dem Vorspulen (alte EN-/Blog-Ausgaben, auch ohne Bootstrap), setzt die Kennung als letzten Schritt aller
  HTML-Erzeuger und in der EXIT-Falle; verweigert (Exit 3, nichts geschrieben), wenn eine Ausgabe eine andere Methode
  trägt. nginx: `/rechtliches`, `/ueber-uns`, `/landing/*.html` mit `must-revalidate`.
- **Sperre** (bei abweichender Kennung, endgültig): keine Datenanfrage (`fetch`-Hülle; Lader `kurse.js` und
  `SA.supabase` prüfen zusätzlich selbst, `ReleaseFehler` endgültig — keine Wiederholung, kein Rückfall, keine
  Übernahme), kein Speicher-Schreibzugriff, keine Einfügung ins Dokument (synchron + Beobachter), kein Chart
  (ApexCharts-Hülle, auch bei später geladener Bibliothek), Dokument durch Hinweis ersetzt, Neuladen höchstens alle
  120 s (Marke in `sessionStorage`, Speicherfehler → Hinweis). Ressourcen (Bilder, CSS, Fremdskripte) sind bewusst
  NICHT Teil der Netz-Zusage (Entwurf v6). Vertrag im Deploy-Fenster: zeitweilige Sperre mit Wiederherstellung.
- **Wächter (Gate):** `scripts/verify_einbindung.py` (ersetzt das Isolations-Gate C P3a), `scripts/verify_release_sperre.py`
  (Transport je Lader mit und ohne Hülle + echtes Dashboard in jsdom, je Fall mit positiver Kontrolle);
  Mutationstest `scripts/verify_release_mutation.py` (isolierte Kopie). Harnesse laden `methode.js` über
  `scripts/js/release_harness.js`.

## Ereigniskatalog (V1c-1, `shared/boersenereignisse.py`)
Entwurf mit Codex in 4 Runden freigegeben ([v1](review_prompts/2026-10-11_kalender_v1c_entwurf.md) …
[v4](review_prompts/2026-10-11_kalender_v1c_entwurf_v4.md)), Code nach 2 Runden
([R1](review_prompts/2026-10-12_kalender_v1c_code_r1.md), [R2](review_prompts/2026-10-12_kalender_v1c_code_r2.md)).
- **Eine Quelle der Schließungsregeln:** `_compute_*_holidays` in `exchange_holidays.py`/`nyse_holidays.py` sind dünne
  Hüllen über `kompat()`; Datentabellen und Datumshelfer bleiben dort, der Katalog importiert sie.
- **Ereignis je Regeltermin:** `nominal` (Regeltermin) · `rechtlich` (gesetzlicher Tag, ≠ nominal nur bei
  Verlegung) · `wirksam` (Schließungstag) · `ersatzgrund` keiner/wochenende (NYSE, LSE)/furikae (TSE)/verlegung ·
  `verlegt` · `art` feiertag/ersatztag (wirksam ≠ nominal)/sonderschliessung/unbestimmt (Tabelle) · Namen DE/EN ·
  Quelle (`shared/kalender_quellen.py`). Kennung `<B>:<regel_id>:<nominal>`, Tabelle `<B>:tabelle:<Datum>`. Jahr =
  Jahr von `nominal`. NASDAQ = Alias von NYSE.
- **Projektionen:** `kompat()` = die bisherige Menge (`get_holidays`, inkl. Wochenenden; TSE behält bei Furikae den
  rechtlichen Sonntag, ein Regeltermin einer Verlegung zählt nie). `schliessungen()` = eindeutige wirksame
  Vollschließungen Mo–Fr — das fachliche Maß für spätere Leser.
- **Versionen:** `ereignisversion()` über `inhalt()` (alle Felder, aufgelöste Namen/Quellen, ohne Versionsfelder);
  `kalenderversion()` über `schliessungen()`. Jedes Objekt (`als_dict()`, JS) trägt die `kalenderversion`.
- **JS:** `landing/js/boersenkalender.js` Schema 2 — `ereignisse(j, b)` (unveränderliche Objekte = `als_dict()`),
  `schliessungen(j, b)` (fachlich, wie Python), `feiertagsmenge(j, b)` (= `get_holidays`), `identitaet`, beide Versionen.
  Weiterhin von keiner Seite eingebunden (P4).
- **Abnahmelücke (benannt):** HKEX und KRX 2016–2026 sind Datumstabellen ohne Regelidentität — Ausgabe nur als
  „geschlossen (Tabelle)", nie als „Feiertag am …".
- **Wächter (Gate):** `scripts/verify_boersenereignisse.py` — eingefrorener Bestand
  (`scripts/kalender_momentaufnahme.py`, `scripts/fixtures/kalender_vor_v1c.json`, 3024 Börsen-Jahre), Invarianten,
  handgeschriebene Sollfälle mit Quelle (u. a. LSE 2002/2012/2020/2021/2022, TSE 2015/2020/2021/2023, NYSE 2025),
  Versionsvertrag a–d, vollständige Objektgleichheit Python = JS unter zwei Zeitzonen. Mutationstest
  `scripts/verify_boersenereignisse_mutation.py` (isolierte Kopie, Bundle in der Kopie neu erzeugt).
- **Folgt:** V1c-2 OPEX/VIX nach Cboe, V1c-3 Halbtage mit Quellen.

## Gemessen (Vorab)
Down-Month-ToM-Reversal (Blog 2026-07-31 + Engine-Preset), SPY bis 2026-07-31: veröffentlichter Stand exakt
reproduziert (n 186/78, WR 68,3/71,8 %, PF 1,80/2,39, Sharpe 0,214/0,336, DD 22,3/18,3 %). Mit TDOM nach
NYSE-Kalender: n 186/77, WR 70,4/72,7 %, PF 1,85/2,44, Sharpe 0,223/0,345, DD 21,6/18,1 %; 181 Ereignistage verschieden.
