# Refresh Monitoring — SeasonAlpha

> Anleitung zur Überwachung der täglichen Kurs-Updates

## Übersicht

SeasonAlpha hat zwei automatische Refresh-Jobs:

| Job | Zeitplan | Was er tut |
|---|---|---|
| **Nightly Refresh** | Täglich 16:45 New Yorker Zeit (Sommer 20:45 UTC, Winter 21:45 UTC), `sa-nightly.timer` | Schlusskurse + TDOM/TDOY + KI-Scores/Regime; sonntags Weekly Newsletter (wenn `WEEKLY_NEWSLETTER_AN`) |
| **Intraday Refresh** | Stündlich :17 UTC, jeden Tag (systemd-Timer auf dem VPS) | Live-Kurse der gerade offenen Börsen; Krypto rund um die Uhr |
| **Polymarket-Intraday** | Stündlich :23 UTC (systemd-Timer) | Snapshot im FOMC-Fenster, sonst nur eine Skip-Zeile |
| **Daily Morning Briefing** | Mo–Fr 07:30 Berliner Zeit (Sommer 05:30, Winter 06:30 UTC), `sa-daily-briefing.timer` (seit 2026-10-12) | Versand an `daily_subscribers`; `refresh_log` run_type `daily_newsletter`. GitHub-Cron `0 6 * * 1-5` kam zuletzt erst 11:48–14:18 UTC an; `daily_newsletter.yml` ist nur noch manuell (Test, Trockenlauf, Einzelempfänger). **Ein Live-Versand je Berliner Datum** (`shared/versandsperre.py`, Zustand in `logs/versand/`): zweiter Lauf nach Abschluss → Exit 0 ohne Versand; abgebrochener Versand → Admin-Alarm, Fortsetzen nur mit `--wiederaufnahme`. **Journal in zwei Stufen** (`? <hash>` VOR dem Versand, danach `+` angenommen / `-` sicher nicht versandt, chronologisch ausgewertet): die Wiederaufnahme überspringt angenommene UND ungeklärte Empfänger (lieber eine Mail zu wenig als eine doppelt) und meldet die Ungeklärten. Der Mailadapter `shared/email_brevo.send_html_ergebnis` unterscheidet `angenommen` (nur HTTP 2xx), `abgelehnt` (kein Schlüssel, Verbindungsaufbau gescheitert, 4xx) und `unklar` (5xx, Lese-Timeout, Abbruch, 1xx/3xx). Ein Journal-Schreibfehler beendet den Lauf. `missing_details.modus` = live/test/einzel; Health-Check zählt nur live und meldet werktags ab 10:00 Berlin ohne heutigen Live-Lauf rot; dazu **`sa-briefing-frist.timer`** Mo–Fr 10:15 Berlin (`daily_health_check.py --briefing-frist`, Admin-Alarm nur bei Verstoß — die Health-Mail um 05:00 UTC liegt vor der Frist). Wächter `verify_briefing_versand.py` (+ Mutationstest), Codex-Freigabe nach 5 Runden |

Alle schreiben ein Protokoll in die Supabase-Tabelle `refresh_log`.

> **Seit 2026-09-29 laufen die stündlichen Jobs NICHT mehr über GitHub Actions.** GitHub startete die
> stündlichen Crons ab dem 26.08.2026 nur noch 4–8× pro Tag statt 24× (Workflow unverändert, alle
> gestarteten Läufe grün — die Läufe kamen schlicht nicht an). Die Units liegen in `deploy/systemd/`,
> `deploy/install_timers.sh` installiert sie bei jedem Deploy. Die Workflows `intraday_update.yml` und
> `polymarket_intraday.yml` sind nur noch manuelle Notauslöser und starten dieselbe systemd-Unit.

---

## 1. Supabase-Tabelle anlegen

Im **Supabase Dashboard** → SQL Editor ausführen:

```sql
CREATE TABLE IF NOT EXISTS refresh_log (
    id SERIAL PRIMARY KEY,
    run_date DATE NOT NULL,
    run_type TEXT NOT NULL,
    tickers_total INTEGER DEFAULT 0,
    tickers_success INTEGER DEFAULT 0,
    tickers_missing INTEGER DEFAULT 0,
    missing_details JSONB DEFAULT '{}',
    auto_fixed INTEGER DEFAULT 0,
    duration_seconds REAL DEFAULT 0,
    errors JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_refresh_log_date ON refresh_log(run_date DESC);
CREATE INDEX IF NOT EXISTS idx_refresh_log_type ON refresh_log(run_type);
```

---

## 2. Tägliche Checks

### Schnell-Check: Letzte 5 Runs

```sql
SELECT run_date, run_type, tickers_total, tickers_success,
       tickers_missing, auto_fixed, duration_seconds
FROM refresh_log
ORDER BY created_at DESC
LIMIT 5;
```

### Nur Runs mit Problemen

```sql
SELECT run_date, run_type, tickers_missing, missing_details, errors
FROM refresh_log
WHERE tickers_missing > 0 OR jsonb_array_length(errors) > 0
ORDER BY created_at DESC
LIMIT 10;
```

### Fehlende Ticker-Details anzeigen

```sql
SELECT run_date, key AS ticker, value AS fehlende_tage
FROM refresh_log,
     jsonb_each(missing_details)
WHERE tickers_missing > 0
ORDER BY run_date DESC
LIMIT 20;
```

### Wochenübersicht

```sql
SELECT run_date,
       SUM(tickers_success) AS total_success,
       SUM(tickers_missing) AS total_missing,
       SUM(auto_fixed) AS total_auto_fixed
FROM refresh_log
WHERE run_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY run_date
ORDER BY run_date DESC;
```

---

## 3. Manuell fehlende Tage nachladen

Falls der automatische Fix nicht greift:

### Auf dem Server (SSH):

```bash
ssh root@<VPS-IP>

# Alle Ticker prüfen + fehlende Tage nachladen
docker exec seasonalpha-app python3 scripts/fix_missing_days.py

# Nur prüfen (nichts schreiben)
docker exec seasonalpha-app python3 scripts/fix_missing_days.py --dry-run

# Einzelnen Ticker prüfen
docker exec seasonalpha-app python3 scripts/fix_missing_days.py --ticker AAPL

# Bestimmtes Jahr prüfen
docker exec seasonalpha-app python3 scripts/fix_missing_days.py --year 2025
```

### Danach TDOM/TDOY neu berechnen:

```bash
# Alle Ticker
nohup docker exec seasonalpha-app python3 -u scripts/backfill_tdoy.py > /root/backfill_tdoy.log 2>&1 &

# Einzelner Ticker
docker exec seasonalpha-app python3 scripts/backfill_tdoy.py --ticker AAPL
```

### App-Cache leeren:

```bash
docker restart seasonalpha-app
```

---

## 4. Automatischer Health-Check

Der Nightly-Refresh prüft am Ende jedes Runs automatisch:

1. **Für jeden Ticker**: Ist heute ein Handelstag? Steht ein Kurs in der DB?
2. **Letzte 7 Tage**: Fehlen Handelstage?
3. **Auto-Fix**: Fehlende Tage werden sofort von Yahoo nachgeladen
4. **Logging**: Ergebnis wird in `refresh_log` geschrieben

### Was wird geloggt?

| Feld | Beschreibung |
|---|---|
| `run_date` | Datum des Runs |
| `run_type` | `nightly`, `intraday`, `polymarket_intraday` (u. a.) |
| `tickers_total` | Anzahl geprüfter Ticker |
| `tickers_success` | Ticker ohne Lücken |
| `tickers_missing` | Ticker mit fehlenden Tagen |
| `missing_details` | JSON: `{"AAPL": ["2026-03-19"], ...}` |
| `auto_fixed` | Automatisch nachgeladene Tage |
| `duration_seconds` | Laufzeit des Runs |
| `errors` | JSON-Array mit Fehlermeldungen |

---

## 5. Troubleshooting

### Problem: Ticker zeigt falsche TDOM/TDOY

1. Prüfe ob Tage fehlen: `fix_missing_days.py --ticker XXX`
2. Nachladen: `fix_missing_days.py --ticker XXX`
3. TDOY neu berechnen: `backfill_tdoy.py --ticker XXX`
4. App neustarten: `docker restart seasonalpha-app`

### Problem: Nightly Refresh läuft nicht

1. Timer: `systemctl list-timers sa-nightly.timer` · letzter Lauf: `journalctl -u sa-nightly.service -n 100`
2. Manuell auslösen: `systemctl start sa-nightly.service` (oder GitHub-Workflow „Nightly DB Refresh")
3. Exit 1 heißt: eine Kind-Phase ist gescheitert (Weekly Newsletter, Landing-Chart) — Zeile „Gescheiterte Phasen:" im Journal.

Früher lief der Nightly zusätzlich aus der Root-Crontab (Log `/var/log/seasonalpha-refresh.log`, seit 29.09.2026 stillgelegt).

### Falle: Kind-Prozesse erben verbogene Umgebung (2026-09-29)

Der Nightly startet Teilaufgaben als eigene Python-Prozesse. Ein Zugriff auf `st.secrets` kopiert alle Einträge
der `.streamlit/secrets.toml` in `os.environ` — lag dort eine alte `SUPABASE_URL`, arbeitete der Hauptprozess mit
seinem fertigen Client korrekt weiter, jedes Kind aber gegen einen nicht mehr existierenden Host
(`[Errno -2] Name or service not known`). So lief der Weekly Newsletter von Juni bis September **nie**.
Heute: `secrets.toml` auf dem Server leer, kein `st.secrets` mehr in `shared/`, und die Kinder bekommen
`env=_KIND_UMGEBUNG` (Umgebung vom Laufbeginn). **Symptom zum Wiedererkennen:** ein Skript läuft per
`docker exec` einwandfrei und scheitert nur als Kind eines langlaufenden Prozesses.

### Problem: EU-Aktien zeigen keine Charts

Wahrscheinlich fehlende Tage in Supabase (Monatszyklus braucht ≥10 Tage pro Monat).
Fix: `fix_missing_days.py` laufen lassen.

### Problem: Intraday Refresh aktualisiert nicht

1. Timer aktiv? `systemctl list-timers 'sa-*'` — beide mit nächstem Termin
2. Letzte Läufe: `journalctl -u sa-intraday.service -n 50` · gescheiterte Units: `systemctl --failed`
3. Timer neu installieren: `bash /opt/seasonaledge/deploy/install_timers.sh`
4. Einen Lauf sofort auslösen: `systemctl start sa-intraday.service` (oder GitHub-Workflow „Intraday Price Update" manuell)
5. Zeitfenster der Gruppen: `intraday_refresh.py` (Tabelle unten)

**Exit-Codes** (`intraday_refresh.py`): 0 ok · 1 gescheitert (`refresh_log` nicht geschrieben, oder mehr als
max(2, 10 %) der Ticker ausgefallen — leerer Download und DB-Fehler zählen seit 2026-09-29 als Ausfall) ·
2 unbekannte `--group`. `polymarket_refresh.py --near-fomc-only`: 1, wenn im FOMC-Fenster kein Snapshot
geschrieben wurde oder das Log scheitert.

**Health-Check** (`daily_health_check.py`): Intraday grün ab 20 Läufen in 24 h an **jedem** Wochentag
(die Krypto-Gruppe ist immer aktiv, also schreibt jeder Lauf eine Zeile), gelb 12–19, rot darunter oder
wenn der letzte Lauf älter als 2,5 h ist. Polymarket-Timer: rot ohne Zeile, bei Alter > 2,5 h oder bei
einem echten Lauf ohne Snapshot. Ein verlorener Stundenslot (Deploy baut den Container neu, der Lauf
wartet max. 2 min) ist normal.

**Timeout:** sitzt im Container (`timeout --kill-after=30s 8m`). systemd beendet bei seinem eigenen Timeout
nur den `docker exec`-Client, der Prozess im Container liefe weiter — am 29.09.2026 auf dem Server nachgewiesen.

---

## 6. Zeitfenster Intraday Refresh

| Gruppe | Zeitfenster (UTC) | Zeitfenster (MESZ) | Ticker |
|---|---|---|---|
| EU | 07:00 - 16:00 | 09:00 - 18:00 | SAP, SIE.DE, BMW.DE, ^GDAXI... |
| US | 13:30 - 21:00 | 15:30 - 23:00 | AAPL, SPY, ^GSPC... |
| Asien | 00:00 - 08:00 | 02:00 - 10:00 | ^N225, ^HSI... |
| FX | 06:00 - 20:00 | 08:00 - 22:00 | EURUSD=X... |
| Crypto | 00:00 - 23:59 | immer | BTC-USD, ETH-USD... |

---

## 7. Wichtige Dateien

| Datei | Beschreibung |
|---|---|
| `scripts/nightly_refresh.py` | Nightly Job + Health-Check |
| `scripts/intraday_refresh.py` | Intraday Updates |
| `deploy/systemd/` + `deploy/install_timers.sh` | Timer: stündlich (Intraday, Polymarket), Nightly, Daily Morning Briefing |
| `scripts/fix_missing_days.py` | Fehlende Tage finden + nachladen |
| `scripts/backfill_tdoy.py` | TDOM/TDOY neu berechnen |
| `shared/exchange_holidays.py` | Börsen-Feiertagskalender |
| `shared/symbols.py` | Ticker → Exchange Mapping |

## Deploy wartet auf laufende Pflicht-Läufe (seit 2026-10-12)

Ein Push baut den App-Container neu, und `docker compose up` beendete bisher jeden laufenden `docker exec`-Job per
SIGKILL (Brier 11.10.2026, Exit 137). Jetzt: `docker compose build` (der laufende Container bleibt), danach
`flock -x -w 2700 logs/sperre/produktion.lock docker compose up -d`. Jeder Lauf aus dem Pflicht-Inventar der
Produktionssperre (`shared/produktionssperre.py`) hält dieselbe Datei geteilt; der Austausch wartet also, bis keiner
mehr läuft, höchstens 45 min, dann wird der Deploy rot. Die ssh-action hat dafür `command_timeout: 75m`.
**Nicht erfasst** sind Läufe außerhalb des Inventars (Brier-Scraper) — für sie gilt weiter: nicht pushen, während sie
laufen. Wächter: `verify_produktionssperre.py` (Betrieb).

## Daily Morning Briefing: Bedienung und Prüfliste (seit 2026-10-12)

**Zeitplan:** `sa-daily-briefing.timer` Mo–Fr 07:30 Europe/Berlin (Sommer 05:30 UTC, Winter 06:30 UTC),
`sa-briefing-frist.timer` Mo–Fr 10:15 Europe/Berlin. `daily_newsletter.yml` hat keinen Zeitplan mehr (nur manuell).

**Zustand eines Tages** liegt in `/opt/seasonaledge/logs/versand/` (im Container `/app/logs/versand/`):

| Datei | Inhalt |
|---|---|
| `daily_newsletter_<YYYY-MM-DD>.json` | `laeuft` (läuft oder abgebrochen) / `fertig` mit `gesendet`, `fehlgeschlagen`, `ungeklaert` |
| `daily_newsletter_<YYYY-MM-DD>.gesendet` | Journal, je Zeile `? <hash>` (vor dem Versand), `+ <hash>` (angenommen), `- <hash>` (sicher nicht versandt); nur Hashes, keine Adressen |
| `daily_newsletter_<YYYY-MM-DD>.lock` | `flock` gegen parallele Live-Läufe |

**Prüfliste nach einem Lauf** (SSH auf den Server, Key per `ls ~/.ssh/`):
```bash
journalctl -u sa-daily-briefing.service -n 30 --no-pager      # Exit 0?
cat /opt/seasonaledge/logs/versand/daily_newsletter_$(TZ=Europe/Berlin date +%F).json   # status fertig, ungeklaert 0?
journalctl -u sa-briefing-frist.service -n 10 --no-pager       # 10:15: Exit 0, „Live-Versand von heute vorhanden“
systemctl list-timers 'sa-*' --no-pager                         # nächste Termine
```
Dazu in `refresh_log` die jüngste Zeile `run_type='daily_newsletter'`: `missing_details` enthält `"modus": "live"`.

**Wenn ein Versand abgebrochen ist** (Status `laeuft`, Admin-Alarm „wurde abgebrochen“): erst prüfen, ob kein Lauf mehr
aktiv ist (`systemctl is-active sa-daily-briefing.service`), dann bewusst fortsetzen:
```bash
docker exec seasonalpha-app timeout 15m python3 -u scripts/daily_newsletter.py --wiederaufnahme
```
Die Wiederaufnahme überspringt angenommene UND ungeklärte Empfänger und meldet die Zahl der ungeklärten per
Admin-Alarm. Ungeklärte (Netzwerkfehler nach dem Absenden, 5xx, 3xx) bekommen bewusst keine zweite Mail — im
Brevo-Dashboard („Email Activity“) lässt sich nachsehen, ob sie angekommen ist.

**Wenn die Fristprüfung alarmiert** („bis 10:00 kein Live-Versand“): `journalctl -u sa-daily-briefing.service` lesen.
Lief der Timer gar nicht → `systemctl status sa-daily-briefing.timer`. Lief er rot → Ursache beheben und manuell
starten (`systemctl start sa-daily-briefing.service`; ein schon `fertig` gemeldeter Tag versendet nicht erneut).

**Testversand** ohne Einfluss auf Sperre und Health-Check: GitHub „Daily Morning Briefing“ manuell mit `test`
bzw. `--to`, oder `docker exec seasonalpha-app python3 scripts/daily_newsletter.py --test`. Diese Läufe stehen mit
`modus: test`/`einzel` im `refresh_log` und zählen NICHT als Live-Versand.

**Wächter:** `scripts/verify_briefing_versand.py` (im Deploy-Gate mit `--streng`; führt `daily_newsletter.main()`,
`collect_health_data()` und den echten Mailadapter mit Attrappen aus) + `verify_briefing_versand_mutation.py`
(36/36). Review: [R1](review_prompts/2026-10-12_briefing_timer.md) …
[Freigabe R5](review_prompts/2026-10-12_briefing_timer_r5_antwort.md).
