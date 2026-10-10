# Paket 3 (P1a K3+K4): eine Ticker-Zuordnung, strenge Börse, keine stillen Ersatzkalender — Code-Review Runde 1

Plan: [v4](2026-10-10_xetra_tdoy_plan_v4.md) K3/K4 · Auflagen: [Antwort 4](2026-10-10_xetra_tdoy_plan_antwort4.md)
Auflagen 1, 4, 5 und Tabelle A3. Pakete 1+2 sind committet (`4d88ac6`, `d6b683e`).

<task>
Prüfe `git diff` im Arbeitsbaum (inkl. gelöschter Root-Datei `exchange_holidays.py`) und die neuen Dateien
`scripts/verify_ticker_boerse*.py`, `scripts/fixtures/ticker_boerse_2026-10-10.json`. Read-only.
</task>

## Änderungen
- **K4** `shared/symbols.get_exchange_for_holidays` ist die einzige Zuordnung: Groß/Klein egal, `-USD`/`-USDT`
  → CRYPTO, `=X` → FOREX, SYMBOLS-Eintrag (case-insensitiv) wie bisher (Index/Future/Suffix → Kalender der
  `exchange`, sonst NYSE; `exchange` ohne Kalender → ValueError), unbekannt mit Suffix → `SUFFIX_ZU_BOERSE`,
  unbekannt ohne Punkt/^/= → NYSE, sonst ValueError. `get_holiday_calendar` und `"NONE": "NYSE"` entfernt.
  **Alle 370 Zuordnungen unverändert** (Fixture aus dem Stand vor der Änderung).
- `exchange_holidays.py`: `TICKER_TO_EXCHANGE`, `_TICKER_MAP`, `get_holidays_for_ticker`,
  `get_exchange_for_ticker` gelöscht (keine Aufrufer außer Selbsttest), Root-Kopie gelöscht (keine Importe).
- **K3** `get_holidays`, `is_holiday`, `is_trading_day` prüfen die Börse zuerst über `boerse_normalisieren`
  (unbekannt/leer → ValueError, NASDAQ → NYSE). `letzte_session`/`markt_offen`: Börse geprüft, fehlende
  Schluss-/Öffnungszeit → ValueError statt NYSE-Zeiten (alle heutigen Aufrufer übergeben "NYSE").
- **Aufrufer (A3)**: `daily_report._tdom_for_ticker` → `handelstag_nummern`, ohne NYSE/Mo–Fr-Ersatz (Aufrufer
  loggt und lässt `mw_score` leer); `build_status_line` ohne NYSE-Ersatz; `_count_trading_days_in_*` ohne
  Mo–Fr-Zweig; `central_banks_for_ticker` loggt den Zuordnungsfehler; `check_db_completeness`:
  `_is_us_listed` ohne Heuristik, `except: pass` im Ticker-Audit → roter Befund „Ticker nicht prüfbar“;
  `backfill_new_ticker` Exit 1 bei gescheitertem Ticker; `intraday_refresh`: TDOM/TDOY-Fehler → Ticker in
  `errors`, nicht mehr als Erfolg gezählt (Kurse werden weiter geschrieben). `shared/data.append_today_if_missing`
  gelöscht (kein Aufrufer, schrieb „Vortag + 1“). **Die Schreiber zählen bewusst noch wie bisher** — Umstellung
  auf `handelstag_nummern` ist das nächste Paket (P2), damit sie eine eigene Prüfung bekommt.
- **Wächter** `verify_ticker_boerse.py` 54 Prüfungen (Bestand, Regelfälle, strenge API, keine zweite
  Zuordnung); alter Code: 18/52. Mutationstest 13/13, zweimal identisch. Beide neuen Wächter
  (`verify_ticker_boerse`, `verify_handelstag_nummern` mit `pip install numpy==1.26.4`) im Deploy-Gate.
- Weiter grün: Kalender-Sollfälle 86/86, Handelstag-Nummern 86/86, Zwilling, Session-Stempel, Wahlen,
  Plain-Vanilla 1A/1B, Stress, Saison-Zwillinge. `verify_calendar_rules` meldet FAIL (SAP.DE 2026-09-08 TDOM 5→5,
  die bekannte Intraday-Drift) und WARN (^STOXX50E/RR.L Geisterzeilen) — **identisch auf dem alten Code**.
- Eigener Fehler, behoben: beim Löschen von `append_today_if_missing` ging die Klasse `KursreiheFehlt` mit;
  `verify_session_stamp` fand es (ImportError).

## Fokusfragen
1. Ändert irgendein Pfad sein Verhalten für die 370 bekannten Ticker (außer Fehlerfälle)?
2. Gibt es Aufrufer mit nicht-literaler Börse/Ticker, die jetzt eine ValueError bekommen können und sie
   verschlucken oder einen Job grün lassen? (A3 nachprüfen, auch JS-unabhängige Python-Pfade.)
3. `intraday_refresh`: Kurse trotz TDOM-Fehler schreiben + Lauf rot — richtig, oder ohne Nummern gar nicht?
4. Deploy-Gate: pip-Installation auf dem Runner tragfähig?
5. Fehlt eine Mutation?

## Ausgabevertrag
**Urteil** (Freigabe / mit Auflagen / keine) · **Befunde** (Datei:Zeile, Beleg) · **Antworten** (je ≤ 6 Zeilen). ≤ 70 Zeilen.
