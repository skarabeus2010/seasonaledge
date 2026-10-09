# Code-Review Saison-Score D3 (Betrieb) + D4 (Oberflächen, Mails) + Migration — Runde 1

Du prüfst read-only im Repo `C:\dev\Seasonaledge` den **uncommitteten Arbeitsbaum** (`git diff` und neue
Dateien). Plan v1–v3 mit Freigabe: `docs/review_prompts/2026-10-09_saison_score_anomalie_plan*.md`.
Rechenkern (committet, freigegeben, NICHT Gegenstand): `shared/saison_score.py`, `landing/js/saison-score.js`.
Validierung D5 ist gelaufen (`scripts/research/saison_score_validierung_ergebnis.json`): mittlerer Spearman 0,019,
95-%-Intervall −0,035…0,084 → kein Rangzusammenhang. Laut Protokoll kommen Bullish/Bearish nicht zurück.

Antworte Deutsch, echte Umlaute. Jeder Befund mit Datei:Zeile, Mechanismus, konkretem Fehlerfall und Schwere
(kritisch/hoch/mittel/niedrig). Am Ende **FREIGABE: ja/nein**. Bestätigtes kurz auflisten.

## Was geändert wurde

**D3 Betrieb**
- `shared/saison_score_betrieb.py` (neu): `fuer_ticker` (Kurse via `shared/stress_score.lade_kurse`),
  `scanner_zeile`, `protokoll_zeile`, `schreibe` (Scanner-Upsert `ticker,scan_date`; Protokoll-Upsert
  `ignore_duplicates=True` auf `methode,ticker,as_of`).
- `scripts/nightly_refresh.py`: KI-Block → Saison-Block; Fehler zählen in `_FEHLGESCHLAGEN`.
- `scripts/full_scanner_run.py`: `scan_ticker` über das Betriebsmodul, `--resume` nur `methode=saison_v1`,
  jeder Fehler → Exit 1.
- `shared/cache_manager.py`, `shared/supabase_client.py`: KI-Score-Funktionen weg; `fetch_scanner_results`
  liest nur `methode=saison_v1`, jüngstes Datum dieser Methode, paginiert.
- `scripts/check_db_completeness.py`: `ki_scores` raus, `scanner_results` gefiltert auf `saison_v1`.
- `shared/ki_score.py`, `shared/ai_models.py` gelöscht.
- **Migration** `scripts/sql/scanner_saison_score_2026_10.sql` (Entwurf, noch nicht ausgeführt):
  `scanner_results` neue Spalten + `score`/`signal` nullable; Tabelle `saison_score_protokoll` insert-only.

**D4 Oberflächen und Mails**
- `landing/pages/scanner.html`: Lader zweistufig (jüngstes `scan_date` der Methode, dann deren Zeilen,
  `order=score.desc.nullslast`), kein Signalfilter, Spalten Score/Trefferquote k/n/Ø 30 T./Musterjahre,
  nicht berechenbare Zeilen mit Grund am Ende, Abdeckung „x von y" gegen `tickers.json`, Methodik inkl.
  Validierungssatz, FAQ/JSON-LD neu.
- `landing/pages/dashboard.html`: `computeKiScore`-Kopie weg; Karte rechnet `SA.saisonScore.berechne` auf
  `SA.decadeCompute.mitHistorie(rawRows, ticker, 25)` (neu in `decade-compute.js`), Ladekennung gegen
  Ticker-Rennen. TruePath-Chart nutzt weiter die lokalen `findMatchingYears`/`computeTruePath` (nur Anzeige).
- `landing/pages/watchlist.html`: `SA.saisonScore` auf voller Historie, kein Signalfilter.
- `landing/pages/ki-saisonalitaet.html`: „Saison-Score & Musterjahre", Score fest (eigene Historie),
  Regler nur für Musterpfad/Tabelle, Ladekennung.
- `landing/js/dash-compute.js`: `computeKiScore` entfernt.
- Textdurchgang: nav/footer/index/tour/pricing/profile/ueber-uns/i18n.js-Meta/seo-Builder, de.json/en.json,
  `_JSON_VER` v12. `seo/seo_template.html` gelöscht (kein Aufrufer, enthielt „72 % Wahrscheinlichkeit").
- `shared/daily_report.py` + Template: keine Score-Schwelle mehr (Stufen nur Multi-Window 3/2/0), Sortierung
  MW dann Saison-Score (None zuletzt), Urteil „k/4 TDOM-Fenster positiv" statt bullish, Warum-Zeile
  „Saison nächste 30 Tage: k/n Vorjahre positiv" getrennt von der TDOM-Fallzahl.
- `shared/weekly_report.py` + Template: Abschnitt „Top Saison-Scores", nur `status ok`, Spalte „30 T. positiv"
  statt Signal; Intro ohne „131 Jahre … 15 KI-Modelle".

## Prüffragen (bitte jede beantworten)

1. **Migration:** idempotent? Bestehende Zeilen (methode NULL) unberührt und für Leser unsichtbar? Rechte:
   anon liest `scanner_results` weiter (Seite), aber `saison_score_protokoll` nicht? Kann `service_role`
   eine Protokollzeile wirklich nicht ändern/löschen (REVOKE + Trigger), und scheitert der Nightly NICHT am
   `ON CONFLICT DO NOTHING`-Weg (braucht `ignore_duplicates` ein UPDATE-Recht)? Funktionierender
   Unique-Constraint für `on_conflict=ticker,scan_date` vorhanden? `NOTIFY pgrst`?
2. **Reihenfolge Deploy/Migration:** Was passiert, wenn der Code vor der Migration live geht (neue Spalten
   fehlen) — lautes Scheitern oder stille Teilschreibung? Was, wenn die Migration läuft und der alte Code
   noch schreibt (score NOT NULL entfällt)?
3. **Stille Fehler:** Kann ein Lade- oder Schreibfehler irgendwo als „nicht berechenbar" oder als Erfolg
   durchgehen? Meldet der Nightly ihn rot?
4. **Zwillinge:** Rechnen Browser (Dashboard/Watchlist/KI-Seite) und Nightly für denselben Ticker und dasselbe
   `as_of` denselben Score? Gleiche Kursbasis (Supabase `prices`), gleiche Bereinigung, gleiche Historientiefe
   (`mitHistorie` 25 Jahre vs. `lade_kurse`)? Kann der Zeitraum-Regler den Score noch beeinflussen?
5. **Scanner-Lader:** `order=score.desc.nullslast` in PostgREST korrekt? `limit=2000` ausreichend? Zeigt die
   Seite einen alten Lauf, wenn der jüngste nur teilweise geschrieben ist (Teilstand) — und sollte sie?
6. **Mails:** Kann die Daily-Auswahl ohne Score-Schwelle Unsinn liefern (z. B. Ticker ohne Saison-Score oben)?
   Stimmt jede Fallzahl zu ihrer Prozent-/Quote-Angabe? Bleibt irgendwo ein Bullish/Bearish oder „KI"?
7. **Texte:** Behauptet irgendein Text (DE/EN, Meta, JSON-LD, Tour, FAQ) eine Vorhersagekraft oder eine
   Wahrscheinlichkeit, die die Validierung nicht deckt? Fehlende EN-Schlüssel (`data-i18n` ohne en.json)?
8. **Reste:** Weitere Importeure/Leser von `ki_score`, `ai_models`, `computeKiScore`, `ki_scores`,
   `scanner_results.signal`, `store_scanner_results` irgendwo im Repo (Skripte, Workflows, Health-Check,
   Video-Pipeline, Blog-Builder)?
