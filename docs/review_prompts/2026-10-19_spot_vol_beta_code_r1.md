# Code-Review /spot-vol-beta — Runde 1

Read-only. Plan v3 mit deiner Freigabe: `docs/review_prompts/2026-10-19_spot_vol_beta_plan_v3.md` (+ v2, v1 und
Antworten). Geändert (uncommittet, `git diff` + neue Dateien):

- **neu** `landing/js/spot-vol-compute.js` (`SA.spotVol`): Achse, Frische, Renditen, OLS, Rolling, expandierendes
  Quantil, Eintritte, Forward, Buckets, VRP, Residuum, Badge, `auswerten`.
- `landing/pages/spot-vol-beta.html`: Inline-Script neu (nur Laden + Darstellung), lädt volle Historie
  (`ab 1990-01-01`, `date,close,log_return`), Zeitraum/Log/Schwellen rechnen ohne Neuladen; Container `svb-frische`,
  `svb-residuum`; OVX nur USO; Beta-Stress als Perzentil; Texte DE in der Seite.
- `landing/i18n/en.json` (EN-Texte, neue `svb.*`-Schlüssel), `landing/js/i18n.js` (`_JSON_VER` v22 → v23).
- Python-Zwilling entfernt: `shared/spot_vol_beta.py` gelöscht, Nightly-Phase E1b raus, `upsert_/fetch_spot_vol_beta`
  raus, `check_db_completeness.py` ohne `spot_vol_beta`, Stub in `verify_kalender_fehlerweitergabe.py`.
- **neu** Wächter `scripts/verify_spot_vol_beta.py` + `scripts/js/probe_spot_vol.js` (im Gate in
  `.github/workflows/deploy.yml`), Mutationstest `--mutation` (18/18 gefangen, isolierte Kopie);
  `verify_seiten_kurse.py`: Fall „normal“ für spot-vol-beta entfällt (Anzeige ändert sich absichtlich).
- `docs/ARCHITECTURE.md` nachgezogen.

Lokal: `verify_spot_vol_beta.py` 142/142, Mutationen 17/17, Seite in jsdom (`probe_seiten_kurse.js … normal`) ohne
Seitenfehler, 7 Charts, Anfragen `select=date,open,close,log_return,…&date=gte.1990-01-01`; `verify_en` FAIL 0.

**Bewusste Abweichung vom Plan v3 (bitte bewerten):** In den echten Daten hat ^VIX 2026 Phantomzeilen an vier
US-Feiertagen (25.05., 19.06., 03.07., 07.09.). Nach der Plan-Regel („vorige eigene Zeile = vorige Sitzung“) wäre die
Folgesitzung jeweils unbekannt; das Rolling-60 fiel dadurch seit dem 08.09. ganz aus (Badge nicht bestimmbar, Stress
blind). Jetzt: Sitzungsrendite = **Summe der gespeicherten `log_return` aller eigenen Zeilen nach der vorigen Sitzung
bis s** (`sitzungsRendite`); Pflicht bleibt eine eigene Zeile an der vorigen Sitzung UND an s, jede Teilrendite bekannt.
Das ist exakt (ln(c_s/c_vorS) = Σ der Zwischenrenditen), auch wenn die Phantomzeile kein reiner Kursabzug ist; echte
Lücken bleiben unbekannt. Wächter: Phantomzeile mit eigener Rendite ≠ 0, Mutation „Phantomrendite ignoriert“.
Auf echten Daten (Dump ^GSPC/^VIX ab 1990, Stand 16.10.2026): 9 266 Sitzungen, je 1 unbekannte Rendite (erste
Sitzung), OLS ab 1990 β −4,440, Residuum 16.10.: Spot −1,09 %, VIX +21,45 %, erwartet +5,26 %, +16,18 Pp, z 3,19,
86 von 9 264 Tagen weiter über der Linie, 5 Tage mit größerem VIX-Anstieg (%) bei kleinerem Rückgang — deckt sich
mit der unabhängigen pandas-Nachrechnung aus v1. Laufzeit `auswerten` 30–80 ms.

Bitte prüfen:
1. Hält die Implementierung den Vertrag aus v3 (Achse/Lückenregel inkl. Phantomzeilen und erster Sitzung,
   Frische/E, voller Historienbeginn, Eintritt/Sperre, expandierende Schwelle ohne Look-ahead, Rolling exakt 60,
   Residuum mit Training ohne E, strikte Zählungen, degenerierte Fälle, VRP-Formel)?
2. Darstellung: wird irgendwo ein unbekannter Wert als 0 gezeigt, ein älterer Tag als „letzter Tag“, eine Log-Größe
   als Prozent, oder fehlt eine Fallzahl? Tooltips/Achsen/Legenden korrekt? EN-Texte vollständig (dynamische via
   `SA.i18n.t`, Neuzeichnen bei `sa:i18n-bereit`)?
3. Ist die Referenz im Wächter wirklich unabhängig, und deckt er die Auflagen (Lücken in beiden Reihen,
   Zeitraumwechsel, beidseitig veraltet, Halbtag, s = 0, N < 3, laufende Sitzung) — findest du eine Mutation, die
   entwischt?
4. Python-Entfernung vollständig (Aufrufer, Inventare der Produktionssperre/Schreiber-Wächter, Health-Check)?
5. Leistung im Browser: volle Historie ^GSPC/^VIX ab 1990 (~9 300 Sitzungen) — `sitzungen()`, Rolling,
   expandierendes Quantil (Einfügen mit `splice`), Residuum. Vertretbar?

Antwort: Befunde (Schwere, Datei:Zeile, Beleg), Urteil „Freigabe“ / „keine Freigabe“ + Auflagen.
