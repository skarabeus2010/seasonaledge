# Plan Phase 1B /plain-vanilla — Hebel, Kalender, Kurslücken, tägliche Equity (v3)

## v3 — Festlegungen zu den Einwänden aus Runde 2 (`..._1b_plan_antwort2.md`), gehen v2 vor

**V1 Näherung (Einwand 1).** `naeherung = true`, sobald ein Trade **irgendwo einen Hebel ≠ 1** hat (UHTS-Regelpfad
oder `leverage ≠ 1`) und **mindestens ein Intervall mit fehlender Sitzung oder auffälligem Abstand** enthält —
unabhängig davon, ob das Lückenintervall selbst 1x oder 2x trägt. Damit ist auch der übersprungene Hebelwechsel
(a < wahres S⁻1 < b) abgedeckt. „Exakt" nur bei durchgehendem 1x-Regelpfad. Wächter: dein Fall 26.11.2024 = 100,
27.11. fehlt, 29.11. = 121 → `naeherung = true`. **Berichtigt in Code-Runde 1:** S⁻k zählt nach Zeilen (L4), S⁻1 ist dann
der 26.11. und das Ersatzintervall 26.→29.11. trägt 2x → **+42 %** (nicht 21 %); zusätzlich Fall (b) mit Lücke im 1x-Teil.
Mutation „Näherung nur bei h = 2 im Lückenintervall" muss scheitern.

**V2 Python-Feiertagsanker (Einwand 2).** Umfang begrenzt: nur One-Day-Holiday und UHTS wechseln auf die exakten
NYSE-Feiertage. Die Näherungsliste bleibt für `_is_near_holiday` (Ultimate Monthly) und `_compute_kti_daily`,
umbenannt in `_US_HOLIDAYS_NAEHERUNG_LEGACY` mit Kommentar „Legacy, Phase 3"; deren Ergebnisse ändern sich nicht
(Wächter: Trades von ultimate_monthly und KTI vor/nach identisch). T1-Satz „betraf One-Day-Holiday und UHTS" wird
zu „betrifft u. a. …".

**V3 Geltungsbereich Hebel (Einwand 3).** Drei Fälle, in beiden Sprachen gleich:
(a) Trade mit Regelpfad `hebel` (UHTS) → gehebelter Pfad in Trade-Rendite, Stop und Tageskurve;
(b) Trade mit `leverage ≠ 1` **ohne** Pfad (Python `calc_kti_leveraged`) → Stop-Rendite = Kursrendite bis Stop-Tag ×
`leverage` (wie JS in 1A), **`taeglich = null`** für die ganze Strategie (Anzeige „—" mit Hinweis „kein täglicher
Hebelpfad"), kein scheinbar gültiger 1x-Kontowert;
(c) sonst 1x. Wächter: KTI-Hebel liefert `taeglich = null`; Mutation „Rückfall auf 1x" muss scheitern.

**V4 Kalender-Sollwerte (Einwand 4).** K3 prüft getrennt `ist_feiertag` (Liste der Börse) und `ist_handelstag`, mit
**konkreten Paaren** statt pauschaler Nachbarn: jedes K1-Datum → Feiertag ja, Handelstag nein; 03.10.2020 (Sa) und
03.10.2021 (So) → Feiertag nein, Handelstag nein; 03.10.2022–2025 und Pfingstmontag 2022–2025 → Feiertag nein,
Handelstag ja (sofern Werktag); 23.12./27.12./30.12. der Jahre 2001–2010, soweit Werktag und nicht 25./26.12. →
Handelstag ja; Tag nach Pfingstmontag (Dienstag) 2015–2021 → Handelstag ja. Die Liste steht wörtlich im Wächter.

**V5 Reichweite der Kalenderkorrektur (Einwand 5).** Die Korrektur gilt **ab 2001**: 24./31.12. geschlossen für
Jahr ≥ 2001 (2001 als dokumentierte Annahme, „^GDAXI 0 fehlende Sitzungen" heißt „unter dieser Annahme"), vor 2001
bleibt das bisherige Verhalten (offen) unverändert; die Sonderliste beginnt mit 03.10.2000 (belegt). Vor 2001 ändert
sich am gemeinsamen Kalender damit nichts außer dem 03.10.2000.
**Backfill:** zuerst Trockenlauf auf dem Server, der für alle XETRA-Ticker TDOM und TDOY mit neuem Code berechnet und
gegen die gespeicherten Werte **inhaltlich** vergleicht: Anzahl geänderter Zeilen getrennt für TDOM und TDOY, je
Jahr. Erwartung: Änderungen nur in Jahren mit Korrekturdatum, TDOY bis Jahresende, TDOM bis Monatsende, kumulativ.
Nur bei passendem Muster schreiben (Routine-Recompute), sonst Rückmeldung an den Nutzer. `tdom_stats`/`tdoy_stats`
zählen Kurszeilen selbst und brauchen keinen Recompute — so im Plan festgehalten.

**V6 Messung (Nebenbefund).** Zusätzlicher Messschritt **S — Python OHLC → Close-Stops** (betrifft nur die
Streamlit-Seite und den Zwilling; JS rechnet seit 1A im Close-Modus).

---

Repo `C:\dev\Seasonaledge`, Stand `6170252` (Phase 1A live). Nutzerentscheidungen vom 08.10.2026: (1) UHTS-Hebel nach
Regel, (2) vor 2000 bleiben die Kurszeilen der Kalender, XETRA vorher gegen Quellen klären, (3) Kurslücken markieren
statt Trades herausnehmen, (4) tägliche Equity mit dem Trade-Drawdown daneben.
v1 und deine Einwände: `..._1b_plan_antwort1.md` (7). Prüfe **diesen Plan vor dem Code**. Antwort auf Deutsch: je
Einwand Schwere + Planpunkt + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

Messungen (Snapshot `a563a159fc2da067`, Stichtag 07.10.2026) wie in v1: 2000–2025 fehlen bei SPY/QQQ/^DJI/^GSPC
0 Sitzungen, bei ^GDAXI 31 — genau die Tage, die deine Recherche als geschlossen belegt (bzw. 2001 offen lässt).
Überschneidungen: UHTS 23–114 je Ticker, One-Day-Holiday ^DJI/^GSPC je 1.

## K — Kalender zuerst (Einwand 7)

K1. **XETRA-Korrektur in beiden Kalendern** (`shared/exchange_holidays.py::_compute_xetra_holidays`,
    `landing/js/holidays.js::_xetra`): 24.12. und 31.12. **in jedem Jahr** geschlossen (die Bedingung `year >= 2011`
    entfällt; ich hatte JS in 1A an diese falsche Python-Regel angeglichen). Zusätzlich Sonderschließungen als feste
    Liste `XETRA_SONDER` (beide Sprachen, Kommentar mit Quelle je Datum aus deiner Tabelle): 03.10.2000, 28.05.2007,
    03.10.2014, 25.05.2015, 16.05.2016, 03.10.2016, 05.06.2017, 03.10.2017, 31.10.2017, 21.05.2018, 03.10.2018,
    10.06.2019, 03.10.2019, 01.06.2020, 24.05.2021. Docstring („Pfingstmontag/3. Oktober handelt Xetra") wird auf
    „in der Regel; Ausnahmen siehe Liste" korrigiert.
K2. **24.12.2001** ohne Primärquelle: geschlossen geführt, Begründung im Kommentar und in
    `docs/TRADING_CALENDAR_RULES.md`: Kalender 2002–2010 alle geschlossen, 31.12.2001 durch UPI belegt, Kursbestand
    hat keine Zeile. Ausdrücklich als „nicht primär belegt" markiert. Falls du das anders wertest: Alternative ist
    „offen + als Datenlücke markiert".
K3. Wächter `verify_kalender_zwilling.py`: zusätzlich **feste Sollwerte** (jedes Datum aus K1/K2 = geschlossen, die
    Nachbartage = offen, Pfingstmontag 2022–2025 und 03.10.2020–2025 = offen) in beiden Sprachen, nicht nur JS = Python.
    Danach Lückenmessung wiederholen: Soll ^GDAXI 0 fehlende Sitzungen 2000–2025.
K4. **Folge außerhalb dieser Seite:** `is_trading_day` speist TDOY/TDOM aller `.DE`-Ticker (Backend) und
    `SA.holidays` das Frontend. Die Korrektur verschiebt in den betroffenen Jahren die Zähler hinter den Tagen um eins
    (vorher zählte der Kalender eine Sitzung ohne Kurs). Nach dem Deploy auf dem Server `backfill_tdoy` für die
    XETRA-Ticker (Routine-Recompute laut CLAUDE.md, kein Offset), vorher/nachher-Zählung der geänderten Zeilen.
K5. Vor 2000 und außerhalb NYSE/XETRA bleiben die Kurszeilen der Kalender (wie 1A).

## T — Feiertagsstrategien: Termine (Einwand 1, ausdrücklich Korrektur gegenüber 1A)

T1. **Gemeinsame Anker:** beide Sprachen nehmen die exakten NYSE-Feiertage des Jahres ohne Sonderschließungen
    (JS `_nyseHolidays`, Python neu aus `shared.nyse_holidays._compute_nyse_holidays` minus `_NYSE_SPECIAL_CLOSURES`).
    Die Python-Liste `_US_HOLIDAYS_MONTH_DAY` mit Näherungen („25.11. Thanksgiving ca.") entfällt — sie betraf
    One-Day-Holiday und UHTS auf der Streamlit-Seite.
T2. **Termine als Sitzungszählung relativ zum Feiertag F**, getrennt von der Rendite geprüft:
    - S⁻k = k-te Sitzung **vor** F (Sitzungen < F), S⁺k = k-te Sitzung **nach** F (Sitzungen > F).
    - One-Day-Holiday: Einstieg S⁻2, Ausstieg S⁻1 (unverändert).
    - UHTS: Einstieg S⁻3, Ausstieg **S⁺3** (heute JS S⁺4 durch `_sitzung(…, 3, 'nach')` mit Basis ≥ F, Python S⁺3).
      Beispiel Thanksgiving 28.11.2024: Ausstieg 03.12.2024 statt 04.12.2024.
    - Liegt F an der Börse des Tickers auf einem Handelstag (^GDAXI an Thanksgiving), zählt F selbst weder als S⁻ noch
      als S⁺; F ist eine Sitzung im Trade (T3).
    Am Datenrand gelten die 1A-Zustände (Kalender 2000–2035).
T3. **Hebelpfad UHTS:** Aufstockung zum Schluss von S⁻1. Für jedes beobachtete Kursintervall (Zeile a → nächste
    Zeile b) im Trade gilt der Hebel, der **nach dem Schluss von a** gehalten wird: h = 1, wenn a < S⁻1, sonst h = 2.
    Damit trägt bei ^GDAXI auch das Intervall S⁻1 → F (Feiertag dort Handelstag) bereits 2x.
    Trade-Rendite = Π(1 + h · (Close_b/Close_a − 1)). Tägliches Rebalancing, keine Finanzierungskosten (ein Satz auf
    der Seite). `trade.leverage = 2` beschreibend, `trade.hebel = [[datum_b, h], …]` für E.

## S — Stops in Python im Close-Modus (Einwand 2)

S1. Neu `apply_stop_close(df, trades, pct, typ)` in Python als Zwilling von `applyStopLoss`/`applyTrailingStop` (JS,
    Close-Modus aus 1A/E4/E5): Fixed löst aus, wenn Close ≤ Einstieg · (1 − p); Trailing, wenn Close ≤ Höchster
    Close seit Einstieg (einschließlich Einstiegs-Close) · (1 − p); Prüfung ab der Sitzung nach dem Einstieg bis
    einschließlich Ausstiegstag; Ausstieg zum Close des Auslösetags; ungültige Closes übersprungen.
S2. Gestoppte Trades: Metadaten bleiben (Hebel, Strategiefelder), `hebel` und `luecken` werden auf den Pfad bis zum
    Stop-Tag gekürzt, Rendite = gehebelter Pfad bis zum Stop-Tag. In **beiden** Sprachen.
S3. `plain_vanilla.auswerten` nutzt `apply_stop_close`; die OHLC-Funktion `apply_stop_loss` bleibt unverändert für
    Phase 3 und wird von keiner Seite mehr gerufen. Zwillingsgleichheit damit **auch mit Stop**.

## L — Kurslücken (Einwand 3)

L1. Je **Kursintervall** a → b im Trade (bis Ausstieg bzw. Stop-Tag), getrennt bewertet, damit ein Trade über
    1999/2000 richtig gezählt wird:
    - liegen a und b im geprüften Bereich (NYSE/XETRA, 2000–2035): `fehlende_sitzungen` += Anzahl Kalendersitzungen
      strikt zwischen a und b;
    - sonst: `auffaellige_abstaende` += 1, wenn b − a > 4 Kalendertage (Warnheuristik; beweist weder Lücke noch
      Vollständigkeit).
L2. Ein Intervall mit fehlender Sitzung oder auffälligem Abstand bei **h = 2** macht die Rendite zur Näherung
    (`naeherung = true`), weil der tägliche gehebelte Pfad nicht rekonstruierbar ist; bewertet wird das beobachtete
    Intervall einmal mit h (T3). Bei h = 1 ist das Intervallprodukt exakt (Kursquotienten heben sich auf).
L3. Trades bleiben in Liste und Kennzahlen. Seite: „n von N Trades mit fehlender Sitzung" bzw. „… mit auffälligem
    Kursabstand", Markierung in der Tradetabelle mit Tooltip („Börse geschlossen oder Daten fehlen" nur für die
    Heuristik), „Näherung" bei L2. i18n DE+EN.
L4. Feste Zeilen-Offsets werden nicht umgerechnet; eine längere Haltedauer über eine Lücke ist durch L1 sichtbar.

## E — Tägliche Equity (Einwände 4, 5, 6)

E1. `tagesEquity(rows, trades, start)` / `tages_equity(df, trades, start)`, nur **geschlossene** Trades. Je
    Kursintervall a → b der Zeilen: Exposure h = Maximum der Hebel aller geschlossenen Trades, die das Intervall halten
    (Einstieg ≤ a, b ≤ Ausstieg/Stop-Tag; Hebel aus `trade.hebel`, sonst 1); Equity_b = Equity_a · (1 + h · r_ab).
    **Positionsregel „ein Konto, höchstens die größte gleichzeitige Position, keine Stapelung"** — sichtbar auf der
    Seite genannt; PF/Sharpe/Trefferquote beschreiben weiter die einzelnen Fenster, nicht das Konto.
E2. **Ergebnisvertrag, kein Bedeutungswechsel:** `max_drawdown`, `final_equity`, `total_return`, `cagr` behalten
    überall ihre heutige (trade-basierte) Bedeutung. `auswerten` ergänzt `stats.taeglich = {max_dd, final_equity,
    total_return, cagr}`. Seite, Equity-Chart, beide Streamlit-Ansichten, Messlauf und Differenzbericht lesen
    ausdrücklich `taeglich.*` bzw. die alten Schlüssel; kein Konsument wechselt die Bedeutung still.
    CAGR täglich = (Endwert/Start)^(1/Jahre) − 1 mit Jahre = (letzter Ausstieg − erster Einstieg)/365,25 wie heute.
E3. „Täglicher Drawdown" heißt auf der Seite „Max. Drawdown (Schlusskurse)": Rückgang der Kontokurve über die
    beobachteten Schlusskurse; bei fehlenden Kursen kann der wahre Rückgang größer sein.
E4. `computeStats` bleibt für `/opex`, `/tdom-analyse`, `/vixpiration` unverändert (Notiz für Phase 3).

## Wächter (`scripts/verify_plain_vanilla_1b.py` + `scripts/js/probe_plain_vanilla_1b.js`, echte Module)
- K: feste Sollwerte K3; Lückenmessung ^GDAXI = 0.
- T: Thanksgiving 2024 UHTS NYSE → 25.11.→03.12.; ^GDAXI-Kalender Thanksgiving 2024 (Xetra offen) → Intervall
  27.11.→28.11. mit h = 2; Python-Anker = JS-Anker für alle Jahre 2000–2035; One-Day-Holiday unverändert.
- H: Kurstreppe mit Handrechnung (1x bis S⁻1, 2x danach); Stop am 2x-Tag (Fixed und Trailing) → gekürzter Pfad;
  offener UHTS am Rand nicht in den Kennzahlen.
- S: Python = JS mit Fixed- und Trailing-Stop auf allen Snapshot-Tickern; Codex-Fall Open 100/Low 90/Close 105 → kein
  Stop im Close-Modus.
- L: synthetische Lücke an einem **echten** Handelstag 2015 → 1 fehlende Sitzung; vor 2000 Abstand 5 → 1, 4 → 0;
  Trade über 1999/2000 (je ein Abschnitt); Lücke bei h = 2 → `naeherung`, bei h = 1 nicht; Python = JS.
- E: (1) **Referenzlogik von `monthly10_blogzahlen.py` im Wächter auf denselben Snapshot-Zeilen 1994–2025** (aktive
  Tage aus den Blöcken, Close/Vorclose): Endwert, Max-DD und CAGR **beide Konventionen** (32 Jahre bzw. Handels-
  spanne) gegen `tagesEquity` auf 1e-9; (2) getrennt der Abgleich mit den veröffentlichten Werten mit dokumentierter
  Datenstandsabweichung (Snapshot 56.885,28 gegen veröffentlicht 56.883) — Information, kein Bestehen-Kriterium;
  (3) überlappende 1x/2x-Fenster → 2x, nicht 3x; Stop nur eines überlappenden Fensters; (4) −30 %-Zwischentief,
  +5 % Ausstieg → `taeglich.max_dd` ≈ −30 %, `max_drawdown` 0; (5) Python = JS auf allen Snapshot-Tickern.
- Statisch: Seite liest `taeglich.max_dd`/`taeglich.final_equity`, Chart aus `tagesEquity`, Streamlit ebenso.
- Mutationen je Punkt (Regel `>= 2011` zurück, eine Sonderschließung entfernt, Python-Näherungsanker, S⁺4 statt S⁺3,
  Hebel 1,5 pauschal, 2x ab Einstieg, Stapelung statt Maximum, offene Trades in der Tageskurve, Lückengrenze 4/5,
  Kalenderzähler aus, `naeherung` bei h = 1, OHLC-Stop in `auswerten`, Seite zeigt Trade-DD als Hauptwert) +
  untaugliche Mutationen wie in 1A.

## Messung (Einwand 6)
Messlauf um `fehlende_sitzungen`, `auffaellige_abstaende`, `naeherung`, `hebel`, `taeglich.*` erweitert; Bericht
alt (6170252) → neu **nach Ursache getrennt** (je Schritt ein Zwischenlauf): K Kalender (XETRA-Ticker: Termine
um die Sonderschließungen), T Termine (UHTS-Ausstieg; Python-Anker nur Streamlit), H Hebelpfad, E neue Tageswerte
(alte Schlüssel unverändert, außer durch K/T/H). Keine Pauschalannahme „unverändert" — jede Abweichung wird einer
Ursache zugeordnet.

## Prüfe besonders
- K2: 24.12.2001 geschlossen führen oder offen + markieren?
- T3: Hebelzuordnung „nach dem Schluss von a" auch für die erste Sitzung nach dem Einstieg und über Wochenenden.
- E1: Intervallmodell mit Maximum — Fall, in dem ein gestopptes Fenster und ein laufendes 2x-Fenster überlappen.
- K4: reicht `backfill_tdoy` für XETRA-Ticker, oder hängen weitere gespeicherte Größen an `is_trading_day`?
