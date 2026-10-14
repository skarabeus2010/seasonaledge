# Code-Review Paket A (R1b, R1d, R4, R5) — Options-Sofortreparaturen

Du bist Prüfer (read-only). Grundlage ist dein Plan-Urteil in
`docs/review_prompts/2026-10-14_options_sofortreparaturen_plan_v2_antwort.md`: FREIGABE (Plan) für R1b/R1d, R4, R5.
R1c, R2, R3 sind NICHT Teil dieses Pakets (kommen mit Plan v3).

Der Code ist uncommittet im Arbeitsbaum: `git diff` und die neuen Dateien
`shared/basisabweichung.py`, `scripts/verify_basisabweichung.py`, `scripts/verify_basisabweichung_mutation.py`,
`scripts/research/basisabweichung_diagnose.py`. Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`
(mit `PYTHONUTF8=1`). Lokal gibt es keine Supabase-Zugangsdaten — die Wächter laufen offline mit Attrappen.

## Was umgesetzt ist

**R1b — Renditen aus gespeicherten Tagesreturns, Spot aus dem Rohschluss.**
- `shared/data.py::lade_kurse(ticker, ab, mindestens)` → `(daten, closes, returns)` zeilengleich, ungültig = None.
- `shared/realized_vol.py`: `rv_aus_returns` verwirft jetzt auch nicht endliche Werte; neu `rv_reihe_aus_returns`
  (Wert am Tag i nutzt `returns[:i+1]`) und `kappe_reihen`.
- `scripts/compute_options_skew.py::_realized_vol`: RV aus `log_return` bis zum letzten gültigen Schluss, Spot und
  Spot-Datum = letzter gültiger Rohschluss.
- `scripts/backfill_skew_vrp.py`: VRP aus `rv_reihe_aus_returns` (Schreiben weiterhin nur mit dem bestehenden Gate;
  ETHA-Reparatur = R1c, nicht hier).
- `shared/intermarket.py`: `_bewegung` = exp(Σ log_return der letzten n) − 1, `_spy_vola` aus `log_return`.

**R1d — Prüfung, keine Reparatur.** `shared/basisabweichung.py` (|ln(c_t/c_{t−1}) − lr_t| > 0,05 je Ticker,
Faktor, Zählung unbrauchbarer Paare). Health-Check 7 „Kursbasis (Basisabweichungen)“ in
`scripts/daily_health_check.py`: letzte 45 Tage seitenweise, gelb bei Treffer, gelb „ungeprüft“ bei 0 Zeilen/Fehler.
Diagnoseskript: deine Auflage umgesetzt (Kurse auf Endlichkeit, nicht endlicher Return zählt als ohne Return).

**R4** — Earnings-Block aus `shared/daily_report.py::events_today_tomorrow` entfernt. **Eigener Fund dabei:** der
entfernte Block legte `client` an, den der Dividendenblock danach benutzte → NameError, still verschluckt, Dividenden
wären aus der Mail verschwunden. Behoben (Dividendenblock holt seinen Client selbst), Wächterfall + Mutation.

**R5** — `/skew`: Standard `SKEW_MODE='pctl'`, Untertitel im HTML und beim Umschalten je Modus, Tooltip und Legende
mit Modusnamen; die Legende läuft jetzt über das Wörterbuch (war auf /en/skew deutsch). `en.json` + `_JSON_VER` v17.

## Nachweise (lokal)
- `verify_basisabweichung.py` grün (auch ohne streamlit, wie im Gate — Attrappe nur für `st.cache_data`).
- `verify_basisabweichung_mutation.py` 15/15 erkannt.
- `verify_realized_vol`, `verify_intermarket`, `verify_skew_anzeige`, `verify_skew_laufzeiten`,
  `verify_briefing_versand` 77/77, `verify_produktionssperre` 75, `verify_seiten_kurse` 313, `verify_seo_html` 0,
  `verify_en` FAIL 0, `verify_i18n_cache_version`, `node scripts/js/probe_skew_tabelle.js` grün.
- Browser lokal: /skew und /en/skew öffnen in Percentile, Untertitel/Legende passend, EN-Legende englisch.
- Gate: neuer Schritt „Waechter - Kursbasis und realisierte Vola“ in `.github/workflows/deploy.yml`.

## Prüfaufträge
1. Rechnen alle Verbraucher der alten Schlusskurs-Renditen jetzt aus `log_return`? Gibt es weitere Stellen
   (Python oder JS), die für /skew, /flows, Intermarket oder die Mail Renditen aus Schlusskursen bilden? Nur nennen,
   was im Umfang R1b liegt; Weiteres als Posten.
2. `_realized_vol`: Fenstergrenze, Kappung auf die Session, Verhalten bei None im Fenster, Spot bei ungültigem
   letztem Schluss. Stimmt die Definition „Wert am Tag i nutzt returns[:i+1]“ mit der bisherigen `rv_reihe` überein?
3. `lade_kurse`: Paginierung, Sortierung, Mindestzahl, Typumwandlung — kann ein Fehler still zu einer kürzeren Reihe
   werden?
4. Health-Check 7: kann er grün melden, obwohl nichts oder nur ein Teil geprüft wurde?
5. R4/R5 vollständig? Sprachwechsel und Umschalten Rank↔Percentile.
6. Wächter: prüft er die echten Funktionen, oder gibt es Stellen, an denen er sich die Einbindung selbst herstellt?
   Fehlen Mutationen für Fehler, die du für wahrscheinlich hältst?

Antwort: Befunde mit Datei:Zeile, je Befund schwer/mittel/leicht, am Ende **FREIGABE (Code): ja/nein**.
