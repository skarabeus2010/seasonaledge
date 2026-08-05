# Mail-Versand testen

Runbook für die zwei Mail-Pipelines (Daily Health Check + Weekly Newsletter). Beide laufen im `seasonalpha-app`-Container und nutzen Brevo als Versand-Provider.

## Voraussetzungen

`.env` auf dem Server (`/opt/seasonaledge/.env`) braucht:

```
BREVO_API_KEY=xkeysib-...
ADMIN_EMAIL=heiko.seibel@gmail.com
SENDER_EMAIL=noreply@seasonalpha.ai
SENDER_NAME=SeasonAlpha
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<service_role-JWT>
```

Alles andere (`UNSUBSCRIBE_SECRET`, `ANTHROPIC_API_KEY`) hat Code-Defaults.

Check ob der Container die Vars sieht:

```bash
ssh root@178.104.75.46
docker exec seasonalpha-app env | grep -E "BREVO_API_KEY|ADMIN_EMAIL|SENDER_EMAIL" | sed 's/=.\{10\}.*/=***/'
```

Erwartet: 3 Zeilen mit `=***`. Wenn leer → `.env` ergänzen und dann `cd /opt/seasonaledge && docker compose up -d --force-recreate app`.

## A) Daily Health Check

Tägliches Monitoring um 07:00 UTC. 6 Systemchecks (Nightly, prices SPY/BTC, Scanner, Polymarket, Regime), Ampel grün/gelb/rot.

### Test per GitHub Action (kein SSH nötig)

1. https://github.com/skarabeus2010/seasonaledge/actions
2. Sidebar: **"Daily Health Check"**
3. Rechts oben: **"Run workflow"** → Branch `master` → **"Run workflow"**
4. ~30s warten, dann landet die Mail bei `ADMIN_EMAIL`

### Test per SSH (direkt auf dem Server)

```bash
ssh root@178.104.75.46

# Live an ADMIN_EMAIL
docker exec seasonalpha-app python3 scripts/daily_health_check.py 2>&1 | tail -15

# Dry-Run (HTML auf Disk, keine Mail)
docker exec seasonalpha-app python3 scripts/daily_health_check.py --dry-run

# An anderen Empfänger
docker exec seasonalpha-app python3 scripts/daily_health_check.py --to test@example.com 2>&1 | tail -15
```

Erwartet: `[health] Done in Xs: OK` plus `[brevo] status=201 messageId=...`.

## B) Weekly Newsletter

Rollt Sonntags 17:00 UTC automatisch via Phase F (`scripts/nightly_refresh.py`). Zum manuellen Test drei Modi.

### Test per GitHub Action (kein SSH nötig)

1. https://github.com/skarabeus2010/seasonaledge/actions
2. Sidebar: **"Weekly Newsletter (Manual Trigger)"**
3. **"Run workflow"** → Dropdown:
   - **`test`** — nur an `ADMIN_EMAIL` (empfohlen für Inhalt-Checks)
   - **`dry-run`** — HTML auf Server, kein Versand
   - **`live`** — an ALLE aktiven Subscriber (nur wenn Content-Review fertig!)
4. Run starten

### Test per SSH

```bash
ssh root@178.104.75.46

# Test-Modus: nur an ADMIN_EMAIL
docker exec seasonalpha-app python3 scripts/weekly_newsletter.py --test 2>&1 | tail -10

# Dry-Run: HTML nach /opt/seasonaledge/weekly_report_preview.html
docker exec seasonalpha-app python3 scripts/weekly_newsletter.py --dry-run
cat /opt/seasonaledge/weekly_report_preview.html | head -30   # schneller Peek

# Einzelner Empfänger
docker exec seasonalpha-app python3 scripts/weekly_newsletter.py --to andre@beispiel.de 2>&1 | tail -10

# LIVE an alle Subscriber — vorher immer Dry-Run + Test-Send!
docker exec seasonalpha-app python3 scripts/weekly_newsletter.py 2>&1 | tail -20
```

Erwartet im Live-Modus: Progress-Log alle 50 Mails, am Ende `[weekly] Done in Xs: Y sent, Z failed`.

## Versand verifizieren

Bei jedem erfolgreichen Send loggt der Code die Brevo-`messageId`:

```
[brevo] to=... status=201 messageId=<202604210620.54698944798@smtp-relay.mailin.fr>
```

### Status in Brevo prüfen

201 von Brevo heißt **angenommen**, nicht automatisch **zugestellt**. Für echten Zustellstatus:

1. https://app.brevo.com/ → **Statistics → Email Activity**
2. Nach `messageId` oder Empfänger-Adresse filtern
3. Status:
   - **Delivered** — beim Empfänger angekommen
   - **Opened** — geöffnet (Pixel-Tracking)
   - **Soft bounce** — temporär nicht zustellbar
   - **Hard bounce** — Adresse ungültig
   - **Blocked** — von Brevo rejected (oft Sender-Auth-Problem)

### Spam-Ordner checken

Besonders beim ersten Versand landet die Mail gerne im Spam. Einmalig als „nicht Spam" markieren, dann lernt Gmail.

## Troubleshooting

### `BREVO_API_KEY nicht gesetzt`

Container sieht den Key nicht. Check:

```bash
# Ist der Key in .env?
grep BREVO_API_KEY /opt/seasonaledge/.env | sed 's/=.\{10\}.*/=***/'

# Ist env_file: .env in docker-compose.yml?
grep -A1 env_file /opt/seasonaledge/docker-compose.yml

# Ist er im Container?
docker exec seasonalpha-app env | grep BREVO_API_KEY
```

Fix wenn fehlt: `.env` ergänzen, dann `cd /opt/seasonaledge && docker compose up -d --force-recreate app`.

### `Sender not valid`

Brevo lehnt den Sender ab. Zwei Ursachen:

1. **Single-Sender nicht verifiziert** — Brevo Dashboard → **Senders, Domains & Dedicated IPs** → Sender hinzufügen + Verify-Mail
2. **Domain nicht authentifiziert** — für Broadcast (Newsletter) Pflicht. SPF + DKIM + DMARC DNS-Einträge setzen. Sobald Domain auth ist, wirkt sie für jede `@seasonalpha.ai`-Adresse automatisch.

### `permission denied for table …`

Supabase-GRANT-Problem, siehe [incident_grant_loss_2026_04_21.md](../../.claude/projects/C--dev-SeasonalEdge/memory/incident_grant_loss_2026_04_21.md) bzw. `memory/`.

### Mail kommt nicht an, aber Brevo zeigt „Delivered"

Empfänger-Server blockt still. Andere Test-Adresse nutzen oder Brevo-Dashboard auf **Blocked/Invalid Contacts**-Liste checken (dort Empfänger ggf. aus Blocked-Liste entfernen).

### `Could not find the 'X' column of 'Y' in the schema cache`

Supabase-Schema aus Code und DB sind auseinandergelaufen. Entweder im Code falsche Spalte oder Migration wurde nicht ausgeführt.

## Security: API-Key rotieren

Wenn der Brevo-Key geleakt wurde (z. B. in Chat/Repo):

```bash
# 1. Brevo Dashboard → SMTP & API → API Keys → "Generate a new API key"
#    Brevo zeigt den vollen Wert NUR EINMAL direkt nach der Erzeugung.

# 2. In BEIDEN .env austauschen — der Deploy überträgt .env NICHT (gitignored)!
#    a) lokal:  c:\dev\SeasonalEdge\.env  (Zeile BREVO_API_KEY)
#    b) Server: /opt/seasonaledge/.env
#    Sauber vom lokalen Stand aus (der Key-Wert erscheint nicht im Klartext im Befehl):
NEWKEY=$(grep -E '^BREVO_API_KEY=' /c/dev/SeasonalEdge/.env)
ssh root@178.104.75.46 "cd /opt/seasonaledge && sed -i.bak 's#^BREVO_API_KEY=.*#$NEWKEY#' .env && docker compose up -d --force-recreate app"

# 3. 1-2 Min warten (Container-Neustart), dann Test-Send VOM SERVER (nicht lokal!):
ssh root@178.104.75.46 "docker exec seasonalpha-app python3 scripts/daily_newsletter.py --test 2>&1 | tail -5"

# 4. Kam die Mail an → alten Key im Brevo-Dashboard LÖSCHEN + Server-Backup entfernen:
ssh root@178.104.75.46 "rm -f /opt/seasonaledge/.env.bak"
```

**Lessons Learned (Rotation 2026-08-06):**

- **⚠️ Brevo-Keys teilen den Account-Präfix.** Alter und neuer Key desselben Kontos beginnen IDENTISCH (`xkeysib-5440ec2afed4…`). **Keys NUR an der Endung (letzte ~6 Zeichen) unterscheiden, NIE am Präfix** — sonst hält man einen neuen Key fälschlich für den alten (genau das passierte hier: Präfix-Vergleich sagte fälschlich „alter Key", die Endung `…WbWkUe` vs `…lylWgh` war der echte Unterschied).
- **Brevo „Authorised IPs" → 401 ist KEIN Key-Fehler.** Ist im Konto die IP-Whitelist aktiv (Account → Security → Authorised IPs), liefert ein API-Call von einer nicht-freigegebenen IP `401 {"message":"…unrecognised IP address…"}`. Das heißt NICHT, dass der Key ungültig ist. Ein Key lässt sich daher **nur von der freigegebenen Server-IP** testen — lokale `/v3/account`-Checks scheitern an der IP, nicht am Key.
- **Deploy überträgt `.env` nicht** (gitignored) → Server-`.env` immer separat aktualisieren, sonst läuft die Produktion mit dem alten Key weiter.
- **SSH aus der Claude-Umgebung = `permission denied`** (kein VPS-Key hinterlegt) → Server-Schritte macht der User; Claude liefert nur die Copy-Paste-Befehle.
- `.env.bak` (von `sed -i.bak`) enthält den ALTEN Key → nach erfolgreicher Rotation löschen.

## Daten-Freshness prüfen (vor Weekly-Versand)

Bevor du einen Live-Newsletter rausschickst, sicherstellen dass die Daten frisch sind:

```bash
# Nightly vom Vortag gelaufen?
docker exec seasonalpha-app python3 -c "
from shared.supabase_client import get_client
r = get_client().table('refresh_log').select('run_date,duration_seconds,errors').order('created_at', desc=True).limit(1).execute()
print(r.data)
"

# oder einfacher: vorher einen Health-Check laufen lassen
docker exec seasonalpha-app python3 scripts/daily_health_check.py --dry-run
```

Nur bei grünem Status live senden.

## Dateien-Referenz

| Datei | Zweck |
|---|---|
| `scripts/daily_health_check.py` | CLI — täglicher System-Health-Report |
| `scripts/weekly_newsletter.py` | CLI — wöchentlicher Saisonalitäts-Newsletter |
| `scripts/templates/health_report.html.j2` | Jinja2-Template Health-Mail |
| `scripts/templates/weekly_report.html.j2` | Jinja2-Template Weekly-Newsletter |
| `shared/email_brevo.py` | Brevo-API-Wrapper (`send_html`, `send_transactional`) |
| `shared/weekly_report.py` | Newsletter-Content-Builder (Top-KI, Events, Regime, TDoM) |
| `shared/unsubscribe_token.py` | HMAC-Token für Unsubscribe-Links |
| `.github/workflows/daily_health.yml` | Cron 07:00 UTC + workflow_dispatch |
| `.github/workflows/weekly_newsletter_manual.yml` | Manual-Trigger Weekly (test/dry-run/live) |
| `docker-compose.yml` → `env_file: .env` | Reicht alle `.env`-Vars in den Container |

## Gotchas (Quick-Ref aus CLAUDE.md)

- **Secrets ohne Streamlit-Runtime:** TOML-Fallback via `tomllib`, sucht in `<project>/.streamlit/secrets.toml` und `~/.streamlit/secrets.toml`, beide Key-Cases (`BREVO_API_KEY`/`brevo_api_key`).
- **`pgcrypto` liegt in Supabase im `extensions`-Schema, nicht `public`** → `SET search_path=public,extensions,pg_temp` + expliziter `extensions.digest()`-Call.
- **Newsletter-Subprocess: `capture_output=False`** — sonst Output komplett unsichtbar in docker logs.
- `messageId` aus Brevo-Response loggen für Debug.
