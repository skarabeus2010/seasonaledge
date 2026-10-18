# Tage nach Börsenkalender — Umstellung der Leser und Seiten (P3/P4)

Stand 2026-10-11 · **Status: Bauplan freigegeben (Codex, 9 Runden), Umsetzung beginnt mit V1** · nichts aktiv.

Vorgeschichte: [Plan v1–v7](review_prompts/2026-10-10_xetra_tdoy_plan_v7.md) (P1a/P1b/P2 live, siehe CLAUDE.md v66.10/66.11).

## Nutzerentscheidungen
- 2026-10-10: Tage nach Börsenkalender ausweisen, auch Statistiken; Weg A (isoliert bauen, gemeinsam umschalten).
- 2026-10-11: veröffentlichte Zahlen, die sich ändern, **nachrechnen und mit `updated:` aktualisieren**; P3/P4 starten;
  **Umschaltung im Wartungsfenster** (einmalig ~15–20 Min.); P5 (historische DB-Spalte) bleibt eigene Freigabe.
- 2026-10-12: `/opex` und `/vixpiration` zeigen **nur belegte Termine** — OPEX ab 02/2015, VIX ab Kontrakt 09/2015;
  die Jahre davor werden in V3 **weggelassen** (nicht gekennzeichnet gezeigt). Umschalter Kalendertag ↔ Handelstag
  auf `/jahreszyklus`/`/risikozyklus` als V4-Posten. Daily Morning Briefing per systemd-Timer statt GitHub-Cron.

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
| V1 | Fundament: Ereigniskatalog (B4), Sitzungshelfer Python+JS (B1/B2/B5), Methodenschalter (Leser/Produktion), Produktionssperre, Einbindungswächter, `[ohne-deploy]`, Releasekennung + Sperre (v6–v9) | V1a live `e12d1e7` · V1b live `64ab4b8` · V1c-1 live `8f771e9`/`43664ec` · V1c-2 live `b2a6665` · V1c-3 live `5b88ffc` · V1d live `18ff46f` |
| V2 | Browserkern: `SA.holidays`-Fassade, Header, Converter | gebaut 2026-10-18 (Codex: Entwurf 3 + Code 5 Runden bis Freigabe), Deploy siehe Abschnitt V2 |
| V3 | Ereignisse: Feiertage, Dashboard-Ereignisse, OPEX/VIX (Cboe), Kalender/ICS, Flows | offen |
| V4 | Fenster/Renditen/Kurven/Strategien (P3i/P3j/P3k) mit Python-Zwillingen — inkl. **Umschalter Kalendertag ↔ Handelstag** (CDOY/TDOY, Monat CDOM/TDOM) auf `/jahreszyklus` und `/risikozyklus` (Nutzerwunsch 2026-10-12; B3.1/B3.7: Handelstag-Achse nach Börsenkalender, Kalendertag als benannte eigene Achsenmethode) | offen |
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
- **Halbtage (V1c-3):** Ereignisse `art = "halbtag"` nur aus Belegen (`shared/halbtage_belege.py`), offene Sitzung,
  weder in `get_holidays` noch in `schliessungen`; Felder `schlusszeit`/`zeitzone`/`sitzung` (NYSE 13:00
  `America/New_York`, `nyse_aktien_kernhandel` — Optionen 13:15 und Spätsitzungen nicht Inhalt), sonst `null`.
  NYSE 2013–2028: 34 Halbtage, Jahresabdeckung je Jahr mit eigener Quelle; `halbtag_status(b, j)` = `belegt` nur
  dort, sonst `ungeprueft` (alle übrigen Börsen, NYSE vor 2013/nach 2028). Quellen = unveränderliche Archivfassungen
  der amtlichen NYSE-/NYX-Kalenderseite mit SHA-256 ([Sicherung](belege/nyse_halbtage_2026-10-12.md),
  [unabhängige Gegenprüfung](belege/nyse_halbtage_2026-10-12_gegenpruefung.md)). `markt_offen`/`letzte_session`
  behandeln Halbtage weiter wie volle Tage (Betriebskonvention P3m; bleibt auch in V1d unverändert — eine Änderung nur
  gemeinsam für beide Funktionen in einer eigens benannten Betriebsphase). LSE-Halbtage später.
  Codex: Entwurf 2, Code 4 Runden ([Freigabe](review_prompts/2026-10-12_kalender_v1c3_code_r4_antwort.md)).

## US-Produkttermine (V1c-2, `shared/produkttermine.py`)
Entwurf mit Codex in 6 Runden freigegeben ([v1](review_prompts/2026-10-12_kalender_v1c2_entwurf.md) …
[v6](review_prompts/2026-10-12_kalender_v1c2_entwurf_v6.md)), Code [R1](review_prompts/2026-10-12_kalender_v1c2_code_r1.md),
[R2](review_prompts/2026-10-12_kalender_v1c2_code_r2.md).
- **Nur im belegten Regelbereich:** OPEX ab 2015-02 (Freitagsverfall, SEC/OCC 34-69772: 3. Freitag, sonst
  vorangehender Geschäftstag), VIX ab Kontrakt 2015-09 (SR-CFE-2015-023: Referenzfreitag des Folgemonats − 30 Tage;
  Mittwoch ODER Freitag geschlossen → einmal der Geschäftstag vor dem Mittwoch; Futures enden am Settlementtag,
  Optionen am Geschäftstag davor). Früher keine Ereignisse — die Regelwechsel 2004/2005/2014 und die damaligen
  Listungszyklen sind nicht belegbar.
- **Geschäftstag = Cboe-Regelsitzung**, angenommen als NYSE-Handelstag; am Objekt als `kalenderannahme`/
  `kalenderstatus = annahme`. Alle 310 Belege 2015–2027 stimmen mit dieser Annahme.
- **Belege** (`shared/produkttermine_listung.py`, drei getrennte Reihen): VX = Cboe-Historiendatei je Kontrakt
  (Dateiname = Settlementtag, 142 Kontrakte 2015-09…2027-06); SPX-Standardverfall und VIX-Optionen = Cboe-Jahreskalender
  2020–2026 (je 84 Monate, zweimal unabhängig abgelesen, 0 Abweichungen). **Abdeckungslücken** (ausgegeben, nie
  still): OPEX 2015-02…2019-12, VIX-Optionen 2015-09…2019-12 — Kalender dieser Jahre unter dem Cboe-Muster nicht
  online.
- **Einstufung erst bei der Abfrage** mit Pflicht-`pruefdatum`: belegt → Quellenwert; unbelegt und Regeltermin
  > Prüfdatum → `projektion`; sonst Lücke (Felder `None`, Grund `nicht_belegt`). Gespeichert und gehasht
  (`produktversion`) werden nur Fakten — das Bundle bleibt reproduzierbar.
- **Verbraucher unverändert bis V3** (`get_opex_date`, Seiten, Mails, `market_events`, `ist_monatsverfall`).
  ⚠️ **Vor dem V3-Umbau** die OPEX-Momentaufnahme einfrieren (2 592 Monate, alle Rückgabefelder von
  `get_opex_date`/`get_all_opex_dates`, `populate_opex`). Nutzerentscheidung 2026-10-12: Historie vor 2015 auf
  `/opex`/`/vixpiration` **weglassen** (Umsetzung in V3).
- **Wächter (Gate):** `scripts/verify_produkttermine.py`; Mutationstest `scripts/verify_produkttermine_mutation.py`.
  `verify_calendar_rules` Regel 8 rechnet mit dem Katalog statt mit seiner früheren (additiven) Kopie.

## Sitzungshelfer (V1d, `shared/sitzungen.py`)
Entwurf mit Codex in 2 Runden freigegeben ([v1](review_prompts/2026-10-12_kalender_v1d_entwurf.md),
[v2](review_prompts/2026-10-12_kalender_v1d_entwurf_v2.md)), Code in 3 Runden
([Freigabe](review_prompts/2026-10-12_kalender_v1d_code_r3_antwort.md)). **Abgenommen 2026-10-12.**
- **Eine Offenheitsdefinition:** alle Helfer auf `is_trading_day` (Halbtage offen); Python `shared/sitzungen.py`,
  JS `SA.boersenkalender` als Zwilling. Keine Verbraucheränderung, `letzte_session`/`markt_offen` unverändert.
- **Funktionen:** `sitzungen(von, bis)` (beide Enden eingeschlossen), `naechste`/`vorherige` mit **Pflicht**-Schalter
  `einschliesslich` (B5.2), `verschiebe(sitzung, n)` statt `tdom + offset` (B5.5), `nte_im_monat`,
  `nte_von_hinten_im_monat`, `nte_im_jahr` (ungültig → Fehler, nicht vorhanden → `None`), `heute(boerse, jetzt)`,
  `zieltermin(boerse, jetzt, art)` mit `heutige_sitzung_oder_naechste` / `naechste_nach_heute` (B5.1/B5.3/B5.6),
  `sitzung_info` (`halbtag` = `true`/`false`/`null` für unbekannt, je nach `halbtag_status`).
- **Zeitpunktvertrag:** `jetzt` immer mit Zeitzone (Python `datetime` mit `tzinfo`, JS Epoch-ms oder ISO mit `Z`/
  `±HH:MM`); Börsenzone aus `_SCHLUSSZEIT`, CRYPTO/FOREX UTC, einmal ins Bundle erzeugt (`zonen`).
- **Ränder:** Rechenbereich 1885-01-01 … 2100-12-31 in jedem Helfer geprüft; Suchen enden am Rand mit Fehler, keine
  feste Tagesgrenze (B5.8). Die alten JS-Funktionen (`nterHandelstag`, `letzterHandelstag`, `nterHandelstagImJahr`,
  `naechsterHandelstag`) sind delegierende Hüllen mit unverändertem Verhalten.
- **Wächter:** `scripts/verify_sitzungen.py` — unabhängige Referenz aus `numpy.busday_offset`, jeder Tag 1885–2100 an
  13 Börsen (Suchen in beiden Modi, Positionen, `verschiebe` bis ±2520), handgeschriebene Soll-, Rand-, Eingabe- und
  Zeitzonenfälle (Sommerzeitwechsel, Mitternacht), JS = Python unter UTC, Pacific/Kiritimati, America/Adak; 399
  Prüfungen in rund 2½ Minuten, im Deploy-Gate. Unerwartete Ausnahmen meldet der Wächter als `[Absturz]`; die gemeinsame
  Mutationsmechanik (`verify_boersenereignisse_mutation.auswerten`) wertet solche Läufe als ungültig — für alle
  Mutationstests darauf. Mutationstest `scripts/verify_sitzungen_mutation.py`: 16/16, vier Gegenproben (Python-
  und JS-Absturz abgefangen, fehlender Anker, Modul kaputt) verworfen.
- **Codex-Befunde, die ich nicht sah:** JS-`heute` nahm den 30.02. an und rollte ihn auf den 2. März; abgefangene
  Abstürze zählten im Mutationstest als „gefangen“; JS-`sitzungen` war nicht vollständig gegen die Referenz
  geprüft; ein JS-Absturz in einer Vierergruppe `X,X,0,E` fiel durch das Trennen nur an `;`.

## Übergabe — nächste Schritte (Stand 2026-10-18)

**Stand:** V1 (Fundament) ist komplett live: Produktionssperre, Releasekennung/Seitensperre, Ereigniskatalog,
OPEX/VIX nach Cboe, NYSE-Halbtage, Sitzungshelfer. **Noch keine Seite und kein Leser nutzt die neuen Bausteine** —
alle Anzeigen rechnen weiter nach der alten Methode (`SA.kalenderMethode = 'alt'`). Nebenher live: Briefing-Timer
und „Deploy wartet“ ([REFRESH_MONITORING](REFRESH_MONITORING.md#daily-morning-briefing-bedienung-und-prüfliste-seit-2026-10-12)).

**Vorgehen je Phase (bewährt in V1):** Entwurf schreiben → Codex prüft den Entwurf (bis Freigabe) → Code →
Wächter mit unabhängiger Referenz + Mutationstest in isolierter Kopie → Codex-Coderunden bis Freigabe → GANZES Gate
lokal → vor dem Push prüfen, dass kein Nicht-Pflicht-Job läuft (Brier So ~08–09 UTC) → Push → Deploy beobachten
(`docker exec seasonalpha-app grep …` statt Commit-Hash). Patch-Skripte mit dem Write-Tool, nie per Heredoc.

### V2 Browserkern (gebaut 2026-10-18)
Entwurf mit Codex in 3 Runden freigegeben ([v1](review_prompts/2026-10-18_kalender_v2_entwurf.md) …
[v3](review_prompts/2026-10-18_kalender_v2_entwurf_v3.md)), Code in 5 Runden
([Freigabe](review_prompts/2026-10-18_kalender_v2_code_r5_antwort.md)). **Unter `alt` ändert sich nichts Sichtbares.**
- **Gemessen vorher:** `detect()` gab 41 Tickern den NYSE-Kalender (Euronext 21, SIX 6, Mailand 4, Stockholm 3,
  Oslo 1, TSE/HKEX/KRX je 1, ENR.F/RHM.F), 11 Forex-Paaren 7 Tage, LSE wich an 36 Tagen 2000–2026 ab. Die alte
  `holidays.js` und der alte Converter sind **nicht zeitzonenfrei** (Kiritimati 1994/95; Converter in New York CDOY
  −1 in der Sommerzeit, in Kiritimati zählt der 03.07.2026 als Handelstag).
- **Fassade** (`landing/js/holidays.js`, IIFE am Ende): nur unter `kalender_v1` reine Delegation an
  `SA.boersenkalender` (`detect`→`boerse`, `isTradingDay`→`istHandelstag`, `get`→`feiertagsmenge`, `nth…`→`nte…`,
  `nextTradingDay`→`naechste(…, true)` ohne Tagesgrenze); Fehlervertrag B5 (Börse fehlt/`NONE`/unbekannt, ungültiges
  Datum, keine ganze Zahl, `n < 1` → `KalenderFehler`; `n` > Summe → `null`; unbekannter einfacher Ticker → NYSE nach
  Listingregel); werfende Getter für die alten Regeln (`_NYSE_SONDER` …). Datumsarithmetik bleibt.
- **Einbindung:** `boersenkalender.js` nach `methode.js`, vor `holidays.js` auf 26 Seiten + Converter, Manifest
  `scripts/fixtures/einbindung_manifest.json` (EN-Fassungen unter ihrer EN-Adresse eingeschlossen). nginx liefert
  JS/CSS seit 18.10. mit gzip (Bundle 509 KB → 53 KB).
- **Fehlerfänger** in dashboard/monatszyklus/watchlist werfen unter `kalender_v1` weiter (unter `alt` unverändert).
- **Inventar** `scripts/fixtures/kalender_v2_inventar.json`: 66 Code-Stellen mit altem Börsenalphabet, je mit Phase
  (V3 25, V4 20, V5 2, Aufräumen 19) — **muss vor V9 leer sein**.
- **Header** `SA._headerKalenderV1` (`app.js`): alle Felder aus einem Börsendatum (`heute(b, jetzt)`), Zähler aus
  `nummern` (geschlossen kumuliert, keine DB-Zeile), TWOY-Summe aus dem ISO-Jahr der Woche, Status/Konvention
  sichtbar, Ticker ohne Kalender → Hinweis; Körbe übergeben einen Kalenderticker (sektor-rotation).
- **Converter** (`seo/tools/…`, nginx liefert `/tools/` direkt): Bootstrap + Bundle, Börsenwahl (unter `alt`
  verborgen), Rechnung nur über das Bundle, Texte ohne feste Grenzen. Deploy setzt `seo/tools/` vor dem Vorspulen
  zurück (Kennung und Cache-Buster sind In-Place) — sonst bräche der Folgedeploy an der Sauberkeitsprüfung.
- **Wächter** `scripts/verify_holidays_fassade.py` (Gate, hinter der Seitenprobe; 2265 Prüfungen, ~2 min):
  Momentaufnahmen `alt` (`holidays_alt.json` je Zone, `converter_alt.json`, `header_alt_seiten.json` — alle aus dem
  Stand vor V2), Delegation (602 247 Vergleiche), 86 Sollfälle mit Quelle, Fehlervertrag, 57 Statusfälle durch
  Header **und** Converter, **unabhängige Monatslisten** je Börse aus dem veröffentlichten Börsenkalender
  (`kalender_monatslisten_2026.json`, 11 Börsen + CRYPTO/FOREX-Konvention, inkl. belegtem Monatsübergang; alle
  gleich unserem Kalender), echte Seiten in jsdom (23 Header-Seiten, A→B→A, Converter mit Bootstrap), Inventar.
  Mutationstest `scripts/verify_holidays_fassade_mutation.py` (21 + 2 Gegenproben).
- **Dabei aufgefallen (eigener Posten, nicht V2):** NYSE 1960 (`ungeprueft`) setzt Presidents Day auf den 15.02.
  (damals 22.02.) und kennt den Wahltag-Schluss 08.11.1960 nicht (belegt in `election_calendar_exceptions.json`).
- **Nach dem Deploy prüfen:** `/tools/trading-day-converter` und eine Header-Seite per HTTP — Kennung, Skriptreihenfolge,
  Bundle mit `Content-Encoding: gzip`; EN-Seiten laden das Bundle (`verify_einbindung.py --mit-en` auf dem Host).

### Danach
- [ ] **V3 Ereignisse** — vorher OPEX-Momentaufnahme einfrieren; `/opex`/`/vixpiration` nur belegte Termine (OPEX ab
      02/2015, VIX ab 09/2015, davor weglassen); die 14 Abweichungen aus der V1c-2-Bestandsaufnahme beheben
      (Backtest-Engine ohne Feiertag, Daily „Bis Fr 19.06.“, „Good Friday“ als Grund für Juneteenth u. a.).
- [ ] **V4** inkl. Umschalter Kalendertag ↔ Handelstag auf `/jahreszyklus` und `/risikozyklus` (Nutzerwunsch).
  Dabei die Heuristik „vollständiges Jahr“ des True Seasonal (`jahrVollstaendig` in `shared/true_seasonal.py` +
  `seasonal-compute.js`: Anfang ≤ Tag 7, Ende ≥ Tag 362, Lücke ≤ 14 Tage) durch die Sitzungsprüfung gegen den
  Börsenkalender ersetzen ([KERNMETHODIK.md Abschnitt 7](KERNMETHODIK.md#7-williams-true-seasonal-2026-10-16)).
- [ ] **P3 Nutzerentscheidung:** Liste der veröffentlichten Zahlen, die sich durch die Umstellung ändern (Monthly 10,
      ToM-Artikel, Down-Month-Reversal) vorlegen, bevor gerechnet wird.
- [ ] **LSE-Halbtage** belegen (Quelle als Archivfassung + Prüfsumme wie NYSE).
- [ ] V5–V8, P5 (Nutzerfreigabe der DB-Spalte), P6, **V9 im Wartungsfenster** (Probelauf auf `/opt/seasonaledge-probe`).

## Gemessen (Vorab)
Down-Month-ToM-Reversal (Blog 2026-07-31 + Engine-Preset), SPY bis 2026-07-31: veröffentlichter Stand exakt
reproduziert (n 186/78, WR 68,3/71,8 %, PF 1,80/2,39, Sharpe 0,214/0,336, DD 22,3/18,3 %). Mit TDOM nach
NYSE-Kalender: n 186/77, WR 70,4/72,7 %, PF 1,85/2,44, Sharpe 0,223/0,345, DD 21,6/18,1 %; 181 Ereignistage verschieden.
