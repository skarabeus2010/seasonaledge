# Handelstag-Nummern — Plan v4: P1a „Kalenderwahrheit in Python“ (Runde 4)

Vorgänger: [v3](2026-10-10_xetra_tdoy_plan_v3.md) · [Antwort 3](2026-10-10_xetra_tdoy_plan_antwort3.md).
Ältere: v1/v2 + Antworten 1/2 im selben Ordner.

<task>
Runde 3 hat P1 erneut zerlegt: Die Kalender selbst sind nicht belegt (LSE/TSE falsch, HKEX/KRX nur 2016–2026),
und es gibt keine gemeinsame Ticker-Zuordnung. Bevor JS irgendetwas aus Python übernimmt, muss die Python-Seite
stimmen. **P1a ist reines Backend** und ändert keine Seite. Du bist **Code-Assistent und Reviewer**:
(A) recherchiere die Sollfälle (unten), (B) prüfe den Entwurf. Read-only, Web erlaubt.
</task>

## Von mir nachgeprüft (Python, Stand 9b0e3ef)
- LSE: 2011-01-03, 2022-01-03, 2028-01-03 **offen** (1.1. fällt auf Samstag, Ersatz-Montag fehlt:
  `_monday_if_sunday`, `exchange_holidays.py:164`); 2010-12-28 und 2021-12-28 **offen** (Boxing Day auf Sonntag
  bzw. Samstag → Ersatz-Dienstag fehlt, `:194–200`). 2016-12-27 korrekt zu.
- TSE: 2020-07-23/24 offen, 2020-07-20 zu; 2021-07-22/23 und 2021-08-09 offen, 2021-07-19 und 2021-10-11 zu
  — die olympischen Verschiebungen fehlen.
- `symbols.get_exchange_for_holidays`: `NEW.DE`, `NEW.PA`, `air.pa` → NYSE (Suffix wird nur über
  `SYMBOLS` aufgelöst, sonst NYSE). `exchange_holidays.get_exchange_for_ticker`: `SAP.DE` → **NYSE**, `SAP` →
  XETRA — widerspricht `symbols`; einzige Aufrufer sind die Modul-Selbsttests (`shared/exchange_holidays.py:713`,
  Root-Kopie `exchange_holidays.py:433`).

## Entwurf P1a

**K1 Kalender korrigieren (nur belegte Fälle).** LSE: Ersatztage England & Wales vollständig (1.1. Sa/So → Mo;
25./26.12.: Sa+So → Mo+Di, So → Di für 25., Fr+Sa → Mo für 26.), dazu belegte Einmaltage (Royal Wedding
2011-04-29, Queen-Begräbnis 2022-09-19, Krönung 2023-05-08, Millennium 1999-12-31 — soweit LSE wirklich
geschlossen war). TSE: Olympia-Verschiebungen 2020/2021 und weitere Einmaltage, soweit belegt. Für jede Börse
werden **nur** Fälle geändert, die du mit offizieller Quelle belegst.

**K2 Gültigkeitsbereich je Börse.** Neue Tabelle `KALENDER_GUELTIG = {börse: (von_jahr, bis_jahr, status)}` mit
Status `belegt` (Regeln gegen offizielle Quelle geprüft), `annahme` (dokumentierte Regel, Einzelfälle
ungeprüft), `ungeprueft`. Vorschlag (bitte korrigieren): NYSE 1971–2035 belegt (WAHLEN-Arbeit), davor annahme;
XETRA 2001–2035 belegt, davor annahme; HKEX/KRX 2016–2026 belegt, sonst ungeprueft; Rest annahme bis
Prüfung. `is_trading_day` bleibt für alle Jahre rechnend (bestehende lange Historien, Runde 3 Befund 2) — der
Status ist eine **Auskunft** (`kalender_status(börse, jahr)`), die Leser in P2–P6 nutzen, um Aussagen zu
kennzeichnen oder auszuschließen. Neue Funktionen (`handelstag_nummern`) scheitern **nicht** an `annahme`.

**K3 Strenge Börse.** `get_holidays`, `is_holiday`, `is_trading_day` prüfen die Börse zuerst: unbekannt →
`ValueError` (kein NYSE-Ersatz, kein Samstag-`False`). `NASDAQ` bleibt Alias von NYSE; Groß/Klein wird
normalisiert. **Vorher**: alle Aufrufer mit nicht-literaler Börse auflisten (Auftrag A3) und prüfen, dass sie
nur gültige Werte liefern.

**K4 Eine Ticker-Zuordnung.** `shared/symbols.get_exchange_for_holidays(ticker)` bleibt die einzige Funktion,
Regel in dieser Reihenfolge: (1) exakter Eintrag in `SYMBOLS` (Großschreibung normalisiert) → dessen Börse;
(2) `-USD`/`-USDT` am Ende → CRYPTO; (3) `=X` → FOREX; (4) Suffix-Tabelle `.DE/.F→XETRA, .PA/.AS/.MC/.BR/.LS→
EURONEXT, .L→LSE, .SW→SIX, .MI→MILAN, .ST→STOCKHOLM, .OL→OSLO, .T→TSE, .HK→HKEX, .KS→KRX`; (5) ohne Punkt und
ohne `^` → NYSE (US-Listing inkl. ADRs, CLAUDE.md); (6) sonst `ValueError`. `get_exchange_for_ticker` wird
gelöscht (keine Aufrufer außer Selbsttest), die Root-Kopie `exchange_holidays.py` ebenfalls, falls nichts sie
importiert. Die Suffix-Tabelle wird später nach JS exportiert.

**K5 `handelstag_nummern`** wie v3 P1.3 plus Runde-3-Auflagen: nur `date` (kein `datetime`) oder strenges
`YYYY-MM-DD` (Regex vor `fromisoformat`), Börse vor allem anderen prüfen, auch bei leerer Eingabe;
Reihenfolge/Duplikate erhalten; geschlossene Tage: `offen=False`, beide `*_rev=None`; offene Tage:
`rev = −(Periodensumme − vorwärts + 1)`. Kalender je (Jahr, Börse) gecacht.

**K6 Prüfung** `scripts/verify_handelstag_nummern.py`: (a) `numpy.busday_count`-Zählung, alle Börsen,
1950–2035, alle fünf Felder; (b) **Sollfälle je Börse aus Auftrag A1, wörtlich mit Quelle**; (c) Ticker-
Zuordnung für alle `SYMBOLS` gegen den bisherigen Stand (Abweichungsliste muss leer sein — K4 darf für
bekannte Ticker nichts ändern) plus Suffix-/Fehlerfälle; (d) Validierung (ungültige Börse, `datetime`,
`20260131`, `2026-W05-6`, leere Liste mit ungültiger Börse). Mutationstest deterministisch
(`_atomar_schreiben`), Anker-Pflicht, fachlich wirksame Mutationen (u. a. Ersatz-Montag weg, Olympia 2021 weg,
Suffix `.F` weg, `busday`-Endpunkt `d`, Rückwärtszahl ab 0).

**K7 Wirkungsbericht.** Vorher/nachher je Börse: welche Tage wechseln offen/zu; welche Ticker sind betroffen
(erwartet: `^FTSE`, `RR.L`, `BA.L`, `^N225`); was ändert sich in `tdom_stats`/Daily-Mail (keine
Neuberechnung in P1a — nur Bericht).

## Auftrag A (Code-Assistent)
- **A1 Sollfälle:** Für LSE und TSE vollständig 2000–2030: Liste aller **Abweichungen** zwischen offizieller
  Quelle und `is_trading_day` (Datum, offiziell, Python, Quelle). Für EURONEXT, SIX, MILAN, STOCKHOLM, OSLO,
  HKEX, KRX je mindestens die Jahre 2015–2026 stichprobenhaft gegen offizielle Kalender: jede gefundene
  Abweichung mit Quelle. Für NYSE/XETRA nur, was dir auffällt.
- **A2 Gültigkeit:** Vorschlag `KALENDER_GUELTIG` je Börse mit Begründung.
- **A3 Aufrufer:** jede Stelle, die `get_holidays`/`is_holiday`/`is_trading_day`/`get_exchange_for_*` mit einer
  nicht literalen Börse oder einem Ticker aufruft (Datei:Zeile), und was sie bei `ValueError` heute täte.

## Fokusfragen
1. K1–K6 tragfähig? Fehlt etwas, das P1a allein (ohne JS) braucht?
2. K2: Ist „rechnen für alle Jahre, Status als Auskunft“ richtig, oder muss `handelstag_nummern` außerhalb
   `belegt` scheitern?
3. K4 Regel (6) `ValueError` für Indizes ohne `SYMBOLS`-Eintrag (`^XYZ`) — richtig, oder NYSE?

## Ausgabevertrag
**Urteil** · **A1 Abweichungstabelle** (vollständig, Länge egal) · **A2** · **A3** (Tabelle) ·
**Antworten Fokusfragen** (je ≤ 6 Zeilen) · **Befunde** · **Auflagen vor dem P1a-Code**.
