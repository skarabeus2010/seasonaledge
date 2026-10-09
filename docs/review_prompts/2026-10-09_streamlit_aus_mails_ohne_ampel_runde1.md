# Code-Review: Streamlit abgeschaltet + Ampel aus den Mails + `regime_scores` löschen (Runde 1)

Repo `C:\dev\Seasonaledge`, **Arbeitsstand (uncommittet)** gegen HEAD `08aaebf`. Nur lesen.
Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
Antwort auf Deutsch: je Befund Schwere + Datei:Zeile + konkreter Fall + Änderung; am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`.

## Nutzerentscheidungen (2026-10-09)
1. `regime_scores` löschen und die Ampel aus **allen** Mails entfernen (Weekly hatte eine Spalte „Regime" in der
   KI-Tabelle und einen Abschnitt „Stress-Ampel"; Daily nur eine leere Hülle `market_regime: {}`).
2. Kein Streamlit mehr: die Alt-App lief unter `/app/` (nicht verlinkt, aber erreichbar, mit schreibendem
   Formular), Port 8501 war zusätzlich am Host freigegeben.

## Änderungen
- **Gelöscht:** `seasonal_app.py`, `pages/` (alle Streamlit-Seiten), `.streamlit/config.toml`,
  `.github/workflows/nightly_update.yml` (Altlast, tat nichts), und 24 `shared`-Module — 17 nur von Streamlit
  importiert, 7 von niemandem. Bestimmt per AST-Importgraph (transitive Hülle aller Nicht-Streamlit-Dateien),
  dazu Textsuche nach Pfad-/Namensverweisen (nur Kommentare „Port von …" in JS) und Prüfung aller
  `importlib`-Ladepfade (laden nur Forschungsskripte). Danach: jedes verbliebene `shared`-Modul importiert ohne
  fehlendes `shared.*`, alle Skripte kompilieren.
- **Dockerfile:** kein `EXPOSE`/`HEALTHCHECK`, `CMD` = Warteschleife mit `trap` auf TERM. **docker-compose:**
  Port 8501, Healthcheck und `secrets.toml`-Mount entfernt. Die Streamlit-Bibliothek bleibt installiert, weil
  `shared/yahoo_downloader.py` `st.cache_data` nutzt (funktioniert ohne Laufzeit, gemessen).
- **nginx:** `/app/`, `/app`, `/_stcore/`, `/static/`, `/vendor/`, `/component/` → 410. `robots.txt`,
  `sitemap.xml`, `llms.txt` liefert nginx weiter aus eigenem Mount (`location =` mit `alias`).
  `nginx-initial.conf` (Ersteinrichtung) liefert 503 statt Proxy auf 8501; `setup_vps.sh` ohne `secrets.toml`.
- **Mails:** `shared/weekly_report.regime_status` + Kontext `regimes` + Template-Spalte + Abschnitt 4 entfernt;
  `daily_report` ohne `market_regime`; Workflow-Kommentar.
- **Wächter:** `verify_stress_ampel.py` prüft jetzt umgekehrt, dass die Ampel in KEINER Mail steht
  (`ampel_nicht_in_mails`, neue Mutation). `verify_plain_vanilla_1a/1b.py`: die drei Streamlit-Prüfungen samt
  Mutationen entfallen. `verify_security.py`: `regime_scores` aus dem Soll-Manifest.
- **SQL** `scripts/sql/drop_regime_scores_2026_10.sql` (führt der Nutzer aus): Abhängigkeitsabfrage, `DROP TABLE`
  **ohne** CASCADE, `NOTIFY pgrst`, Abnahme.

## Belege
Wächter: Stress-Ampel 34/34 (mit Snapshot), /plain-vanilla 1A 50/50, 1B 42/42 (Snapshot). Weekly-Vorlage rendert
mit `StrictUndefined` und Dummy-Kontext ohne Fehler, ohne „Ampel"/„Regime".

## Bitte besonders prüfen
1. Gibt es einen **Laufzeitpfad**, den mein statischer Importgraph nicht sieht (Strings, `exec`, Workflows, die
   Python inline ausführen — `grep "from shared" .github/workflows`, systemd-Units, `deploy/*.sh`)?
2. Bricht der Deploy oder ein Timer an der Container-Änderung (Healthcheck-Abhängigkeit, `depends_on: condition`,
   `docker compose up --wait`, Skripte, die auf `healthy` warten)?
3. Die nginx-Regex-`location` `~ ^/(_stcore|static|vendor|component)/` — überdeckt sie einen legitimen Pfad?
   Reihenfolge Regex vs. Präfix beachten.
4. Fehlt eine Stelle, an der die Ampel noch in einer Mail auftaucht oder `regime_scores` noch gelesen wird
   (inkl. SQL-Funktionen/RPCs in `scripts/sql/`)?
5. Wirkt das Löschen von `.streamlit/config.toml` auf `st.cache_data` in Crons?
