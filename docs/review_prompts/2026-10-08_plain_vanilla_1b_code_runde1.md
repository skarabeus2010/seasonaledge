# Code-Review Phase 1B /plain-vanilla, Runde 1

Repo `C:\dev\Seasonaledge`, Arbeitsstand (uncommittet) auf Basis `6170252`. Plan: `docs/review_prompts/
2026-10-08_plain_vanilla_1b_plan.md` (v3, deine Freigabe in Plan-Runde 3, Antworten `..._1b_plan_antwort1-3.md`).
Prüfe die Umsetzung gegen den Plan und auf neue Fehler. Antwort auf Deutsch: je Befund Schwere + Datei:Zeile +
konkreter Eingabefall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`. Kurs-Snapshot (eingefroren, Hash
`a563a159fc2da067`): `C:/Users/HEIKOS~1/AppData/Local/Temp/claude/c--dev-Seasonaledge/b1245851-7084-4449-b6ab-61b4ed04fde7/scratchpad/pv_kurse`.

## Umsetzung (Dateien)
- **K:** `shared/exchange_holidays.py::_compute_xetra_holidays` + `XETRA_SONDER` (Quellen je Datum),
  `landing/js/holidays.js::_xetra` + `_XETRA_SONDER`; 24./31.12. ab 2001, vor 2001 unverändert.
  `scripts/verify_kalender_zwilling.py`: feste Sollwerte V4 (Handelstag- und Feiertagsstatus getrennt, Liste wörtlich),
  0 Fehler, Mutationen 9/9 (u. a. alte Regel `>= 2011`, Sonderliste leer/ein Datum fehlt, Pfingstmontag jedes Jahr).
  Lückenmessung danach: ^GDAXI 2000–2025 **0** fehlende Sitzungen (unter der Annahme 24.12.2001), vorher 31.
  `scripts/verify_calendar_rules.py` weiter 9 PASS.
- **T/H:** JS `calc_uhts` (S⁻3 → S⁺3 über `_sitzung(F+1, 2)`, Aufstockung S⁻1), neu `_hebelPfad`; Python
  `calc_uhts`/`_hebel_pfad`, `calc_one_day_holiday` und UHTS auf `_nyse_feiertage` (exakte NYSE-Feiertage ohne
  Sonderschließungen, **nur Werktage** — die Python-Liste führte Neujahr an einem Samstag als Feiertag, JS nicht;
  gemessen in 18 Jahren 1896–2026, sonst identisch). Näherungsliste umbenannt `_US_HOLIDAYS_NAEHERUNG_LEGACY`, nur noch
  Ultimate Monthly und KTI.
- **S:** Python `apply_stop_close` + `_stop_ausstieg` (Zwilling der JS-Stops), `auswerten` ruft sie; JS
  `_stopAusstieg` kürzt den Hebelpfad, Hebel ohne Pfad → Kursrendite × leverage.
- **L:** JS `_lueckenMarkieren`, Python `_luecken_markieren`, je Kursintervall; `naeherung` nach V1.
- **E:** JS `tagesEquity`, Python `tages_equity`; `auswerten` ergänzt `stats.taeglich` (inkl. `kurve`) und
  `stats.luecken`; alte Schlüssel unverändert. Seite `landing/pages/plain-vanilla.html`: KPIs CAGR/Endwert/Max DD
  (Schlusskurse) aus `taeglich`, „Max DD (Trades)" daneben, Hinweiszeile (Lücken, Näherung, Kontoregel), Chart aus der
  Tageskurve (für die Darstellung auf ≤ ~3000 Punkte ausgedünnt, Hoch/Tief/letzter Punkt aus der vollen Kurve),
  Kachel-CAGR aus `taeglich`, Lückenmarke und „≈" in der Tradetabelle, UHTS-Hebeltext; i18n DE+EN, `_JSON_VER` v7.
  Streamlit `pages/09_Plain_Vanilla_Strategien.py` liest ebenfalls `taeglich` (kein `build_equity_curve` mehr).
- **Messlauf** `scripts/js/probe_plain_vanilla_messlauf.js`: Tupel um Spalten 11–13 (fehlend, Abstand, Näherung)
  erweitert, `taeglich` ohne Kurve. Neu `scripts/research/plain_vanilla_zwilling.py` (Python gegen JS-Messlauf).

## Abweichung vom Plan, bitte bewerten
V1-Wächterfall „26.11.2024 = 100, 27.11. fehlt, 29.11. = 121 → 21 %": S⁻k wird wie in 1A nach **Zeilen** gezählt
(L4: Offsets werden über Lücken nicht umgerechnet). Fehlt der 27.11., ist die letzte vorhandene Zeile vor F der 26.11.,
also Aufstockung 26.11., Einstieg 22.11. statt 25.11., Ersatzintervall 26.→29.11. mit 2x → **+42 %**, `naeherung =
true`. Zusätzlich Fall (b): 26.11. fehlt → Lückenintervall 25.→27.11. mit 1x, Hebel später → `naeherung = true`
(fängt die Mutation „Näherung nur bei 2x im Lückenintervall").

## Belege
`scripts/verify_plain_vanilla_1b.py --snapshot <ordner>` **41/41** (JS-Probe `scripts/js/probe_plain_vanilla_1b.js`
15 Fälle, Python-Zwilling mit Werten gegen JS auf 1e-9, Feiertagsanker 2000–2035 = JS, Legacy-Konsumenten gegen
`6170252` unverändert, Kalender, statische Prüfungen, Snapshot). Snapshot-Teil:
- Monthly 10 SPY 1994–2025 gegen die Referenzlogik `monthly10_blogzahlen.py` auf denselben Zeilen: Endfaktor,
  Max-DD, CAGR (32 Jahre und Handelsspanne) in JS **und** Python auf 1e-9 gleich. Information: Snapshot ergibt aus
  10.000 **56.885,28** (veröffentlicht 56.883), Max-DD −41,05 % (−41,0 %), CAGR 5,58 % (5,58 %).
- Zwilling Python = JS (`plain_vanilla_zwilling.py`) für alle gemeinsamen Strategien außer LBR, Midterm, UECS
  (Phase 3, bekannte Unterschiede) in 10 J./max × aus/fixed8/trailing8 auf allen fünf Tickern.
`verify_plain_vanilla_1a.py` weiter 52/52. `--mutationen` (1B): **27/27** gefangen, 3/3 untaugliche verworfen; Kalender-Wächter 9/9.

**Messung alt (6170252) → neu, JS-Seite:** Trades und alte Kennzahlen unverändert bei **allen** Strategien außer
UHTS (30 von 30 Kombinationen UHTS geändert: Termine T + Hebelpfad H). Die Kalenderkorrektur K verschiebt keinen
historischen Trade (die Tage hatten bei ^GDAXI ohnehin keine Kurszeile); S betrifft nur Python. Neu sind die Tageswerte;
Beispiel SPY max: Sell in May Max-DD Trades −12,6 % → Schlusskurse −34,8 %, Monthly 10 −41,0 % → −41,0 %.

## Bekannte, bewusst offene Punkte (nicht Teil von 1B)
LBR/Midterm/UECS-Zwillingsunterschiede (Phase 3), `computeStats` auf `/opex`, `/tdom-analyse`, `/vixpiration`
unverändert trade-basiert, OHLC-Funktion `apply_stop_loss` ungenutzt erhalten, Backfill TDOM/TDOY für XETRA-Ticker erst
nach dem Deploy mit Trockenlauf (V5).
