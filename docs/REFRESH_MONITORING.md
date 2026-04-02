# Refresh Monitoring — SeasonAlpha

> Anleitung zur Überwachung der täglichen Kurs-Updates

## Übersicht

SeasonAlpha hat zwei automatische Refresh-Jobs:

| Job | Zeitplan | Was er tut |
|---|---|---|
| **Nightly Refresh** | 22:30 MESZ (Mo-Fr) | Schlusskurse + TDOM/TDOY + Health-Check |
| **Intraday Refresh** | Stündlich :17 (Mo-Fr) | Live-Kurse während Handelszeiten |

Beide schreiben ein Protokoll in die Supabase-Tabelle `refresh_log`.

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
ssh root@178.104.75.46

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
| `run_type` | `nightly` oder `intraday` |
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

1. GitHub Actions prüfen: https://github.com/skarabeus2010/seasonaledge/actions
2. Manuell auslösen: `docker exec seasonalpha-app python3 scripts/nightly_refresh.py`
3. Log prüfen: GitHub Action → Run Details → Logs

### Problem: EU-Aktien zeigen keine Charts

Wahrscheinlich fehlende Tage in Supabase (Monatszyklus braucht ≥10 Tage pro Monat).
Fix: `fix_missing_days.py` laufen lassen.

### Problem: Intraday Refresh aktualisiert nicht

1. Prüfe ob die Börse offen ist (Zeitfenster in `intraday_refresh.py`)
2. Prüfe GitHub Action Cron: `17 * * * 1-5` (stündlich :17, Mo-Fr)
3. Manuell testen: `docker exec seasonalpha-app python3 scripts/intraday_refresh.py --group eu`

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
| `scripts/fix_missing_days.py` | Fehlende Tage finden + nachladen |
| `scripts/backfill_tdoy.py` | TDOM/TDOY neu berechnen |
| `shared/exchange_holidays.py` | Börsen-Feiertagskalender |
| `shared/symbols.py` | Ticker → Exchange Mapping |
