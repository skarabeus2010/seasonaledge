# Handelstag-Nummern nach Börsenkalender — Plan v3 (Runde 3)

Vorgänger: [v1](2026-10-10_xetra_tdoy_plan.md) · [Antwort 1](2026-10-10_xetra_tdoy_plan_antwort1.md) ·
[v2](2026-10-10_xetra_tdoy_plan_v2.md) · [Antwort 2](2026-10-10_xetra_tdoy_plan_antwort2.md) (Bestandsliste).

<task>
Nutzerentscheidung: Tage werden **nach dem Börsenkalender** ausgewiesen. Runde 2 hat gezeigt, dass das ein
Umbau über ~200 Stellen ist und dass die erste Voraussetzung fehlt: **Python und JS haben nicht denselben
Kalender.** Diese Runde legt nur **P1** fest — die gemeinsame Grundlage, die selbst nichts aktiviert — und den
Übergangsplan für alles danach. Prüfe P1 so genau, dass ich danach Code schreiben kann. Read-only.
</task>

## Neu gemessen (lokal, Stand 9b0e3ef)
- `symbols.py`: NYSE 267 · XETRA 45 · EURONEXT 21 · FOREX 11 · SIX 6 · CRYPTO 6 · MILAN 4 · LSE 3 ·
  STOCKHOLM 3 · TSE/HKEX/KRX/OSLO je 1.
- JS `SA.holidays.detect()` kennt nur NYSE/XETRA/LSE/NONE: `AIR.PA`, `^STOXX50E`, `NESN.SW`, `^N225`, `NEL.OL`
  und auch **`ENR.F`/`RHM.F`** (Python: XETRA) → `NYSE`; Forex → `NONE` = 7 Tage/Woche (Python: Mo–Fr).
  **53 Ticker rechnen auf den Seiten heute mit einem fremden Kalender** — unabhängig von der Zählweise.
- Alle 13 Python-Feiertagslisten 1950–2035 als kompakte Zeichenkette (`MMDD…` je Jahr): **48 415 B roh,
  5 510 B gzip.**

## P1 — Entwurf

**P1.1 Eine Kalenderquelle: Python erzeugt, JS liest.** Statt die zehn fehlenden Kalender in `holidays.js` von
Hand nachzubauen (der nächste Zwilling, der driftet — Lesson 1B: zwei Zwillinge können derselben falschen Regel
folgen), erzeugt `scripts/build_boersenkalender_js.py` die Datei `landing/js/boersenkalender-daten.js`:
```
window.SA = window.SA || {};
SA.KALENDER_DATEN = { version: "<sha256 der Nutzdaten>", von: 1950, bis: 2035,
  woche: { NYSE:"MoFr", …, FOREX:"MoFr", CRYPTO:"taeglich" },
  feiertage: { NYSE: { "1950": "0102…", … }, XETRA: {…}, … },
  ticker: { "ENR.F":"XETRA", "AIR.PA":"EURONEXT", … },      // aus symbols.get_exchange_for_holidays
  suffix: [ [".DE","XETRA"], [".PA","EURONEXT"], … ] }      // dieselbe Regel für unbekannte Ticker
```
Synchron geladen vor `holidays.js` (Seiten binden heute 29× `holidays.js` ein → je ein `<script>` davor;
`components`/`inject_credentials.sh` hängt `?v=` an). Die Datei ist **getrackt und deterministisch** (kein
Cron-Output — sie hängt nur am Code); der Deploy-Wächter erzeugt sie neu und bricht ab, wenn sie vom
Commit abweicht (Muster `_JSON_VER`). `holidays.js` behält seine öffentliche API (`detect`, `isTradingDay`,
`nthTradingDay`, `lastTradingDay`, `nthTradingDayOfYear`, `nextTradingDay`, `get`, `getMap`), liest aber nur
noch die Daten; die eigenen Regeln `_nyse/_xetra/_lse` entfallen. Außerhalb `von..bis` und für eine unbekannte
Börse: **Fehler** (Ausnahme bzw. `null` mit Grund), kein stiller NYSE-/Mo–Fr-Ersatz.

**P1.2 Börsenkennung.** Einheitlich die Python-Namen (`NYSE, XETRA, LSE, EURONEXT, SIX, MILAN, STOCKHOLM, OSLO,
TSE, HKEX, KRX, FOREX, CRYPTO`); `NASDAQ` wird beim Erzeugen auf `NYSE` abgebildet. Der alte JS-Wert `NONE`
bleibt als Alias, der eine Warnung in der Konsole auslöst und auf `CRYPTO` zeigt (Aufrufer mit `NONE`
werden in P4 umgestellt; Liste aus der Bestandsliste).

**P1.3 Nummernfunktion (beide Sprachen, gleiche Semantik).**
- Python `shared/exchange_holidays.handelstag_nummern(daten: Sequence[date|str], exchange: str) ->
  list[Nummer]` mit `Nummer = (tdom: int, tdoy: int, tdom_rev: int|None, tdoy_rev: int|None, offen: bool)`,
  Reihenfolge = Eingabereihenfolge, ein Ticker/eine Börse je Aufruf, `str` nur ISO `YYYY-MM-DD`, keine
  Zeitzonenumrechnung (Datum ist Börsendatum), leere Eingabe → leere Liste, ungültiges Datum/Börse/Bereich →
  `ValueError`.
- JS `SA.holidays.handelstagNummern(isoDaten, exchange)` → Array von `{tdom, tdoy, tdom_rev, tdoy_rev, offen}`,
  nur ISO-Strings (nie `Date`-Objekte — Lesson v66.8 UTC), Fehler per `throw`.
- Semantik V1 aus v2: vorwärts = Handelstage ab Periodenbeginn bis einschließlich `d`; geschlossener Tag →
  Wert des letzten Handelstags davor in derselben Periode, sonst 0; rückwärts nur für offene Tage
  (−1 = letzter Handelstag der Periode), sonst `None`/`null`. Krypto bis 31/366.
- Bestehende Namen `tdom_reverse`/`tdoy_reverse` in Python-DataFrames = `tdom_rev`/`tdoy_rev` (Abbildung
  erst in P3).

**P1.4 Prüfung.** `scripts/verify_handelstag_nummern.py`:
(a) **Python == JS** über alle 13 Börsen × jeden Kalendertag 1950–2035 (node führt die echte `holidays.js`
mit der echten Datendatei aus); (b) **unabhängige Zählung** mit `numpy.busday_count` (Endpunkt `d+1` vorwärts,
exklusives Periodenende rückwärts; Wochenmaske je Börse) über alle Börsen/Tage; (c) **feste Sollfälle aus
offiziellen Kalendern**, wörtlich im Wächter: XETRA 2012-10-03 offen, 2018-10-04 = (3,193), 2018-05-21 zu,
2008-12-24 zu; NYSE 2025-01-09 zu (Carter); Forex Sa 2026-10-10 zu; Krypto 2026-01-31 tdom 31;
(d) Datei aktuell (Neuerzeugung == Commit); (e) `detect()` == Python für alle 366 Ticker aus `symbols.py`
und für Suffix-Beispiele außerhalb.
`scripts/verify_handelstag_nummern_mutation.py`: deterministisch über `_atomar_schreiben`, Anker-Prüfung
(nicht greifende Mutation = ungültig), u. a.: Endpunkt `d` statt `d+1`, Rückwärtszahl ab 0, Feiertag einer
Börse gestrichen, Ticker-Map `ENR.F→NYSE`, Suffix-Reihenfolge, `NONE`-Alias auf Mo–Fr, Bereichsgrenze still.

**P1 aktiviert nichts:** keine Seite, kein Schreiber nutzt die Nummernfunktion. Einzige sichtbare Wirkung:
`detect()`/`isTradingDay()` liefern für die 53 Ticker den richtigen Kalender — **das ändert heute angezeigte
TDOM-Werte und Kalenderanzeigen auf den Seiten.** Frage 2 unten.

## Übergang nach P1 (Rahmen, wird je Phase eigens geprüft)
Runde 2, Frage 2: P2–P4 **nicht** einzeln produktiv schalten. Reihenfolge: P2/P3/P4 vorbereiten hinter einer
Methodengeneration (`methode='kalender_v1'` in `tdom_stats`/`tdoy_stats`, Leser wählen genau eine Generation),
dann in einem Fenster: Schreibruhe → P5 (Spalte `prices`, ab 2001, Manifest + eine Transaktion, Nutzerfreigabe)
→ P6 (Stats vollständig neu, beide Richtungen, alle Modi, Gruppenersatz) → Leser umschalten. Veröffentlichte
Zahlen (Monthly 10, ToM-Artikel, Down-Month-Reversal) werden vorher eingefroren nachgerechnet und dem Nutzer
als Liste vorgelegt; ein Blogtext ändert sich nur nach Entscheidung.
Alle Auflagen „vor P1“ aus Runde 2, die P2–P6 betreffen (V4 je Renditeart, Kurvenvertrag, Strategietermine,
Stats-Migration, Schreibpfade, P5-Abnahme), gehen in die jeweilige Phasenprüfung — notiert, nicht vergessen.

## Fokusfragen
1. P1.1: Erzeugte Datendatei statt nachgebauter JS-Regeln — tragfähig? Risiken (Ladereihenfolge, Seiten ohne
   `holidays.js`, EN-Build `build_en.py`, `inject_credentials.sh`-Cache-Buster, CSP)? Wo im Deploy soll der
   Aktualitätswächter laufen?
2. Die Kalenderkorrektur für die 53 Ticker ändert sichtbare Werte sofort. Ist das ein Fehlerfix, der mit P1
   ausgeliefert werden soll, oder muss er in den gemeinsamen Wechsel? (Meine Sicht: Fehlerfix — heute zeigt
   `/dashboard` für `AIR.PA` am 1. Mai einen NYSE-Handelstag.) Welche Seiten-/Mailstellen ändern sich dadurch?
3. P1.3: Vertrag vollständig? Insbesondere `offen`-Flag, Fehlerverhalten, Krypto/Forex, Mehrticker-Aufrufer.
4. P1.4: Reicht (a)–(e) als Abnahme? Was würde trotz Grün falsch sein können?
5. `get_holidays()` fällt bei unbekannter Börse auf NYSE zurück (`exchange_holidays.py:496`), ebenso
   `is_holiday`. Mit P1 abschaffen (Fehler) oder Aufrufer zuerst prüfen?

## Ausgabevertrag
**Urteil** (ein Satz) · **Antworten Fokusfragen** (je ≤ 8 Zeilen, Datei:Zeile) · **Befunde** (nummeriert,
Beleg) · **Auflagen vor dem P1-Code** (Liste). Höchstens 120 Zeilen.
