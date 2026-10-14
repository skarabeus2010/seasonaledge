# Code-Review Paket A, Runde 2

Deine Antwort Runde 1: `docs/review_prompts/2026-10-14_options_paket_a_code_antwort1.md` (FREIGABE nein, drei
mittlere Befunde). Prompt Runde 1: `docs/review_prompts/2026-10-14_options_paket_a_code.md`. Code weiterhin
uncommittet im Arbeitsbaum (`git diff` + neue Dateien). Python:
`C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`, `PYTHONUTF8=1`.

## Umsetzung der Befunde

**1 — Health-Check 7 grün trotz ungeprüfter Paare.** `shared/basisabweichung.py` zählt jetzt `geprueft`
(= tatsächlich verglichene Paare). `scripts/daily_health_check.py` Check 7: 0 Paare → gelb „ungeprüft“;
0 geprüft → gelb „ungeprüft — kein Kurspaar vergleichbar (… ohne log_return, … mit ungültigem Kurs)“; übersprungene
Paare ohne Treffer → gelb „unvollständig — g von p geprüft“; Treffer → gelb, Übersprungene angehängt; grün nur, wenn
jedes Paar geprüft wurde. (Die Serverdiagnose fand über zwei Jahre 0 Paare ohne Return, das erzeugt also kein
tägliches Gelb.) Wächterfälle: alle Returns None, alle Schlüsse None, teilweise übersprungen mit Zählung.

**2 — /skew von der Ladereihenfolge abhängig.** `landing/pages/skew.html`: `_updateQuadSub` setzt den aktuellen
Schlüssel als `data-i18n-html` am Element (quad_sub / quad_sub_pctl / quad_sub_cs), damit `_applyDOM` den Modus nicht
zurücksetzt; neuer Listener `sa:i18n-bereit` zeichnet Untertitel, Schalter, Radar (nur mit geladener Historie),
Vol-Trigger, Tabelle und VRP neu. Neue Probe `scripts/js/probe_skew_sprache.js` (Seiten-JS aus der Datei, beide
Reihenfolgen, früher Wechsel auf Rank, `_applyDOM` nachgestellt); beide Defekte einzeln wieder eingebaut → Probe rot.
Hinweis: wie `probe_skew_tabelle.js` braucht sie die gitignorten Cron-JSONs unter `landing/data/`, läuft daher lokal,
nicht im Gate.

**3 — Lader-Einbindung selbst hergestellt.** Der Wächter setzt kein `lade_kurse` mehr in Verbrauchermodulen; alle
Verbraucher laufen über den ECHTEN `shared.data.lade_kurse` mit einer PostgREST-Attrappe (eq/gte/range, 1000er-Seiten).
Neue Laderfälle: Zeilentreue, drei Seiten (2500 Zeilen), Text→Zahl, nan/negativ → None mit erhaltener Zeile,
None/inf-Return → None, `ab=`, Seitenfehler → Ausnahme ohne Teilreihe, `data=None` → KursreiheFehlt, Mindestzahl,
doppeltes Datum. Session-Kappung prüft jetzt Datum, Spot und RV-Wert gegen `rv_aus_returns(returns[:46])`.
`lade_kurse` selbst: `data=None` → KursreiheFehlt (nicht mehr als Seitenende), Zeile ohne Datum → KursreiheFehlt
statt still übersprungen, nicht aufsteigende/doppelte Daten → KursreiheFehlt.

Mutationstest jetzt 23/23 (neu: geprüft-Zählung, drei Health-Zweige, data=None, Duplikate, nicht endlicher Return,
fehlende Session-Kappung). Docstring `_realized_vol` nennt jetzt `log_return` statt ln(P_t/P_{t-1}).

Folgeposten aus deiner Runde 1 (Mail-Kursanzeigen, Sektor-Monat, Vol-Control-Proxy) notiere ich für Plan v3, nicht
in diesem Paket.

## Nachweise lokal
verify_basisabweichung grün (auch in einem venv ohne streamlit wie im Gate), Mutation 23/23, verify_realized_vol 54,
verify_intermarket 22, verify_briefing_versand 77/77, verify_skew_anzeige/laufzeiten PASS, verify_i18n_cache_version,
verify_en FAIL 0, probe_skew_tabelle + probe_skew_sprache grün.

Bitte prüfe die Umsetzung und ob neue Lücken entstanden sind. Am Ende **FREIGABE (Code): ja/nein**.
