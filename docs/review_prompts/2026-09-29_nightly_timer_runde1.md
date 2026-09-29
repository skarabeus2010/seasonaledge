# Review-Auftrag: Nightly auf systemd-Timer + Unterprozess-Umgebung (Runde 1, CODE)

Repo `C:\dev\Seasonaledge`. Fortsetzung der Timer-Arbeit von heute (Intraday/Polymarket, deine Freigabe
in `docs/review_prompts/2026-09-29_intraday_timer_runde2.md`, Muster in `deploy/systemd/`).
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau eine Zeile
`FREIGABE: ja` oder `FREIGABE: nein`. Prüfe mit `git diff` und den neuen Dateien.

## Befunde (gemessen auf dem Server, 2026-09-29)

1. **Nightly lief täglich doppelt:** Root-Crontab `30 20 * * * docker exec … nightly_refresh.py >> /var/log/seasonalpha-refresh.log`
   UND GitHub `nightly_refresh.yml` (real 23:00–00:30 UTC). Am 27.09. überlappend (20:34 und 20:39).
2. **Alle Kind-Skripte des Nightly scheiterten an DNS** (`[Errno -2] Name or service not known` auf dem
   Supabase-Host): Weekly Newsletter (Phase F, **20 von 20 Sonntagen seit Juni, 0 Erfolge**), Polymarket-Snapshot
   und -Backfill (Phase G, **jeden Tag**), Brier (Phase H). Beide Scheduler betroffen. Nachgestellt durch einen
   manuellen Nightly-Lauf. **Ursache per Messsonde belegt** (Umgebung kurz vor Phase G gegen Laufbeginn):
   `SUPABASE_URL`, `SUPABASE_KEY`, `brevo_api_key`, `brevo_list_id` waren zur Laufzeit neu gesetzt — auf ein
   **altes Supabase-Projekt**, dessen Host nicht mehr auflöst. Quelle: `shared/cpi_data.py` (Phase A2) griff auf
   `st.secrets` zu; Streamlit kopiert dabei die obersten Einträge der `.streamlit/secrets.toml` (vom 02.04.,
   per docker-compose ro gemountet) in `os.environ`. Der Hauptprozess nutzte seinen schon gebauten Client
   weiter, jedes Kind erbte die alte Adresse.
3. `nightly_refresh.py` endete immer mit Exit 0 — deshalb fiel der Newsletter-Ausfall fünf Monate nicht auf.
4. Der alte Termin 20:30 UTC liegt im Winter (US-Schluss 21:00 UTC) VOR dem Börsenschluss.

## Bereits erledigt (nicht Teil des Diffs)
- Server-`secrets.toml` geleert (Nutzerentscheidung; enthielt nur veraltete Werte inkl. eines rotierten Brevo-Schlüssels).
  Nachweis: `st.secrets.get(...)` verändert danach keine Umgebungsvariable.
- Test-Mail `weekly_newsletter.py --test` an die Admin-Adresse: Brevo 201. Nutzer will den Versand an
  Abonnenten erst nach Abnahme dieser Test-Mail → Schalter `WEEKLY_NEWSLETTER_AN = False`.

## Änderungen
- `scripts/nightly_refresh.py`: `_KIND_UMGEBUNG = dict(os.environ)` beim Modulimport, alle fünf Kind-Aufrufe mit
  `env=_KIND_UMGEBUNG`; gescheiterte Kind-Phasen (Exit ≠ 0 oder Exception) in `_FEHLGESCHLAGEN`, am Ende Exit 1;
  Phase F nur bei `WEEKLY_NEWSLETTER_AN`.
- `shared/cpi_data.py`, `shared/ai_models.py`: `st.secrets`-Rückfall entfernt (Streamlit produktiv ungenutzt, Schlüssel aus der Umgebung).
- `shared/constants.py`: `WEEKLY_NEWSLETTER_AN = False`.
- `scripts/weekly_newsletter.py`: nur im Live-Modus eine `refresh_log`-Zeile `run_type='weekly_newsletter'`,
  auch bei Fehlschlag (Kontext/Abonnentenliste/kein Inhalt); keine E-Mail-Adressen im Log.
- `scripts/daily_health_check.py`: `bewerte_weekly_newsletter` + Check 6d (aus → gelb; an → rot bei > 8 Tagen,
  0 gesendet oder Fehlern; an ohne Zeile → gelb).
- `deploy/systemd/sa-nightly.{service,timer}`: `OnCalendar=*-*-* 16:45:00 America/New_York` (auf dem Server geprüft:
  Sommer 20:45 UTC, 02.11. 21:45 UTC), `Persistent=true`, Timeout im Container 90 min, außen 95 min.
- `deploy/install_timers.sh`: Nightly-Units ergänzt; Schritt 5 entfernt die Crontab-Zeile mit
  `scripts/nightly_refresh.py`, erst nachdem Schritt 4 den Timer nachgewiesen hat; andere Zeilen bleiben.
  Schritt 3 ohne Pipe (`grep -q` + pipefail).
- `.github/workflows/nightly_refresh.yml`: nur noch `workflow_dispatch` → `systemctl start sa-nightly.service`.

## Tests (lokal)
`bewerte_weekly_newsletter` 7 Fälle; Schutz der Kind-Umgebung: nach künstlicher Verschmutzung von
`SUPABASE_URL` sieht ein Kind mit `env=_KIND_UMGEBUNG` die richtige Adresse, ohne `env=` die falsche.

## Prüfe besonders
- Deckt `_KIND_UMGEBUNG` beim Modulimport wirklich den Zustand VOR jeder Verschmutzung ab (Importreihenfolge,
  `shared/__init__.py` lädt `.env`)? Gibt es weitere Wege, auf denen der Nightly selbst mit falschen Werten arbeitet?
- Exit 1 bei gescheiterten Kind-Phasen: sinnvoll abgegrenzt (Phasen A–E melden nur per print)?
- `Persistent=true` + Deploy-Neustart des Timers: kann das einen ungewollten Sofortlauf auslösen?
- Crontab-Bereinigung: Risiken, Reihenfolge.
- Phase G läuft nach dem Fix erstmals wirklich — Doppelung mit `polymarket_daily.yml`?
