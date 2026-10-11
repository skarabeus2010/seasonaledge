# Kalender-Umstellung V1c-1 — Code-Runde 1 (Ereigniskatalog)

Entwurf freigegeben in [v4](2026-10-11_kalender_v1c_entwurf_v4.md) · [Antwort](2026-10-11_kalender_v1c_entwurf_v4_antwort.md).
Auflagen aus v4: (1) neue Felder inkl. `verlegt` vollständig in Modell, Bundle und Python/JS-Objektvergleich;
(2) eingefrorener Snapshot unverändert, unabhängige Sollfälle und Versionsänderungstests nachgewiesen;
Tabellenidentitäten als Abnahmelücke ausgewiesen. Read-only, nicht committet (Arbeitsbaum).

<task>Ist der Code V1c-1 freigegeben? Sind die Auflagen aus v4 erfüllt? Gibt es Abweichungen vom Entwurf (v2–v4) oder
Lücken im Wächter, die einen falschen Katalog grün durchließen?</task>

## Geänderte/neue Dateien
- **neu** `shared/boersenereignisse.py` — `Ereignis` (frozen dataclass: boerse, regel_id, art, nominal, rechtlich,
  wirksam, ersatzgrund, verlegt, nominal_herkunft, name_de, name_en, quelle; `ereignis_id`, `als_dict()`), Regeln je
  Börse (NYSE, XETRA, LSE, EURONEXT, MILAN, SIX, STOCKHOLM, OSLO, TSE, HKEX, KRX, FOREX/CRYPTO leer), `ereignisse()`,
  `kompat()` (TSE behält den rechtlichen Sonntag bei Furikae), `schliessungen()`, `identitaet()`, `abnahmeluecken()`,
  `ereignisversion()`, `kalenderversion()`.
- **neu** `shared/kalender_quellen.py` — Quellentabelle (Titel, Beleg, Prüfstand), aus den Codekommentaren übernommen.
- `shared/exchange_holidays.py`, `shared/nyse_holidays.py` — `_compute_*_holidays` sind dünne Hüllen
  `sorted(kompat(B, year))` (Docstrings bleiben; Datentabellen `XETRA_SONDER`, `_TSE_*`, `_HKEX/_KRX_HOLIDAYS`,
  `_NYSE_SPECIAL_CLOSURES` und die Datumshelfer bleiben dort, der Katalog importiert sie).
- `scripts/build_boersenkalender_js.py` — Schema 2: `ereignisse` kompakt `[regel_idx, "MMDD", {Abweichungen a/r/w/g/v/h/n/q}]`
  gegen den Standard je Regel (häufigste Kombination art/Name/Quelle), `regeln`, `namen`, `quellen`, `identitaet`,
  `ereignisversion`, `kalenderversion`. Bundle 137 → 480 KB roh, 37 KB gzip; keine Seite bindet es ein (P4).
- `scripts/boersenkalender/api.js` → `landing/js/boersenkalender.js` — `ereignisse(j, b)` (unveränderliche Objekte
  = `als_dict()`), `schliessungen(j, b)` jetzt die **fachliche Projektion** wie Python, die bisherige Menge heißt
  `feiertagsmenge(j, b)` (= `get_holidays`), `identitaet(b, j)`, `ereignisversion`, `kalenderversion`.
- `scripts/verify_boersenkalender_js.py` — prüft `feiertagsmenge` gegen `get_holidays` und `schliessungen` gegen Python.
- **neu** `scripts/verify_boersenereignisse.py` (+ `scripts/js/probe_boersenereignisse.js`), im Deploy-Gate:
  [Bestand] `kalender_momentaufnahme.py --pruefen` · [Kompat] Hüllen = `kompat` = `get_holidays` · [Invariante]
  · [Sollfall] 25 Ereignisfälle + 16 Mengenfälle mit Quelle · [Version] a–d · [Zwilling] vollständige Objektgleichheit
  1885–2100 aller Börsen unter UTC und America/Adak, Alias, Unveränderlichkeit · Abnahmelücken HKEX/KRX 2016–2026 ausgegeben.
- **neu** `scripts/verify_boersenereignisse_mutation.py` — isolierte Kopie, 20 Mutationen (Katalog, Projektionen,
  Versionen, Generator, JS) + 2 Gegenproben; JS/Generator-Mutationen erzeugen das Bundle in der Kopie neu.

## Nachweise (lokal)
- `kalender_momentaufnahme.py --pruefen`: 3024 Börsen-Jahre, 0 Abweichungen (vor und nach der Hüllen-Umstellung).
- `verify_boersenereignisse.py`: 213/213, 23 834 Ereignisse, Kennungen eindeutig.
- `verify_boersenereignisse_mutation.py`: 20/20 gefangen, beide Gegenproben verworfen, Projektbaum unverändert.
- unverändert grün: `verify_kalender_sollfaelle` 86/86, `verify_handelstag_nummern` 86/86,
  `verify_boersenkalender_js` 62/62, `verify_kalender_zwilling` 0 Fehler, `verify_ticker_boerse` 56/56,
  `verify_schreiber_nummern` 36/36, `verify_einbindung` 24/24, `verify_seasonal_twins` OK.
  `verify_calendar_rules` 11 PASS/1 WARN/1 FAIL — identisch zu HEAD (SAP.DE-TDOM-Drift, bekannt).

## Bewusste Entscheidungen — bitte prüfen
1. Jahr eines Ereignisses = Jahr von `nominal`; der Generator bricht ab, falls ein Ereignis ein anderes Jahr hätte.
2. NYSE-Sonderschließungen und XETRA-Sonderschließungen bekommen ihren Kurznamen aus einer Tabelle bzw. aus der Regel
   (Pfingstmontag = `_whit_monday`, 3.10., 31.10.; sonst `ValueError`).
3. LSE 2022: Boxing Day 26.12. `feiertag`, Christmas (So) → 27.12. `ersatztag` (gov.uk). LSE 2021: Christmas → 27.,
   Boxing → 28. Spring Bank 2002/2012/2022 `verlegung` + Jubiläum als `sonderschliessung`.
4. TSE: Olympia-Verlegungen `verlegung` (Yama 2021 → `furikae` mit `verlegt=True`), Kokumin no Kyujitsu und die drei
   Jahreswechseltage als eigene Regeln, Systemausfall 2020-10-01 als `sonderschliessung`.
5. HKEX/KRX außerhalb der Tabellenjahre: Regelereignisse mit Quelle `…konvention` (Status bleibt wie bisher).
6. `halbtag` ist als Art erlaubt, aber noch nicht erzeugt (V1c-3); alle Projektionen schließen ihn aus.

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2 mit Datei:Zeile) · **Auflagen**. ≤ 25 Zeilen.
