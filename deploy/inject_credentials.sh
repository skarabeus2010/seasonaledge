#!/bin/bash
# ══════════════════════════════════════════════════════════════
# inject_credentials.sh — Supabase Credentials in Landing HTML
# ══════════════════════════════════════════════════════════════
# Ersetzt %%SUPABASE_URL%% und %%SUPABASE_ANON_KEY%% Placeholder
# in allen HTML-Dateien unter landing/.
#
# Wird im Deploy-Workflow NACH git pull, VOR docker compose aufgerufen.
# Liest Credentials aus .env (auf dem VPS).
#
# Aufruf: bash deploy/inject_credentials.sh

set -e

REPO_DIR="${1:-/opt/seasonaledge}"
ENV_FILE="$REPO_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "WARNUNG: $ENV_FILE nicht gefunden — Credentials nicht injiziert"
    exit 0
fi

# .env laden (SUPABASE_URL, SUPABASE_KEY = service-role fuer Backend,
# SUPABASE_ANON_KEY = anon fuer Frontend-Injection)
source "$ENV_FILE"

if [ -z "$SUPABASE_URL" ]; then
    echo "WARNUNG: SUPABASE_URL leer — Credentials nicht injiziert"
    exit 0
fi

# Frontend-Key: NIEMALS den Service-Role-Key in HTML schreiben!
# Bevorzugt SUPABASE_ANON_KEY (explizit). Fallback: SUPABASE_KEY nur wenn
# per JWT-Role-Check nachweislich "anon" (Rueckwaertskompat. zum alten Setup).
FRONTEND_KEY="${SUPABASE_ANON_KEY:-}"
if [ -z "$FRONTEND_KEY" ]; then
    if [ -z "$SUPABASE_KEY" ]; then
        echo "FEHLER: Weder SUPABASE_ANON_KEY noch SUPABASE_KEY in .env gesetzt"
        exit 1
    fi
    # JWT decoden: Payload-Segment (nach 1. Punkt) base64-decode, role-Feld auslesen
    ROLE=$(echo "$SUPABASE_KEY" | awk -F'.' '{print $2}' | base64 -d 2>/dev/null | grep -o '"role":"[^"]*"' | cut -d'"' -f4 || true)
    if [ "$ROLE" = "anon" ]; then
        echo "Hinweis: kein SUPABASE_ANON_KEY in .env — SUPABASE_KEY ist anon, wird als Fallback genutzt"
        FRONTEND_KEY="$SUPABASE_KEY"
    else
        echo "FEHLER: SUPABASE_ANON_KEY fehlt und SUPABASE_KEY ist nicht anon (role=$ROLE)"
        echo "        => Setze in .env:  SUPABASE_ANON_KEY=<anon-jwt>"
        echo "        NIEMALS den Service-Role-Key in Frontend-HTML schreiben!"
        exit 1
    fi
fi

# Placeholder in allen Landing-HTML-Dateien ersetzen
COUNT=$(grep -rl '%%SUPABASE_URL%%\|%%SUPABASE_ANON_KEY%%\|%%UMAMI_WEBSITE_ID%%' "$REPO_DIR/landing/" 2>/dev/null | wc -l)

if [ "$COUNT" -eq 0 ]; then
    echo "Keine Placeholder gefunden — bereits injiziert oder keine Landing-Dateien"
else
    # Umami Website-ID (optional, Fallback auf leeren String)
    UMAMI_ID="${UMAMI_WEBSITE_ID:-}"
    find "$REPO_DIR/landing" -name "*.html" -exec sed -i \
        "s|%%SUPABASE_URL%%|${SUPABASE_URL}|g; s|%%SUPABASE_ANON_KEY%%|${FRONTEND_KEY}|g; s|%%UMAMI_WEBSITE_ID%%|${UMAMI_ID}|g" {} +
    echo "Credentials injiziert in $COUNT Datei(en) (Supabase + Umami)"
fi

# ── Marktkalender-Daten bauen (JSON + ICS) ───────────────────
python3 "$REPO_DIR/scripts/build_calendar_data.py" \
    && echo "Marktkalender-Daten generiert" \
    || echo "WARNUNG: build_calendar_data.py fehlgeschlagen — Kalender-Daten nicht aktualisiert"

# ── Cache-Busting fuer CSS und JS ────────────────────────────
# Haengt ?v=<git-sha> an alle /landing/css/*.css und /landing/js/*.js Refs
# in HTML, damit Browser bei jedem Deploy zwingend neu laden (egal welcher
# Cache-Header). Wirkt auch wenn Mobile Safari auf altem max-age=86400 haengt.
GIT_SHA=$(cd "$REPO_DIR" && git rev-parse --short HEAD 2>/dev/null || date +%s)
echo "Cache-Busting Version: $GIT_SHA"

find "$REPO_DIR/landing" -name "*.html" -exec sed -i -E \
    "s#(/landing/(css|js)/[a-zA-Z0-9_./-]+\.(css|js))(\?v=[a-zA-Z0-9]+)?#\1?v=${GIT_SHA}#g" {} +

echo "Cache-Busting auf alle CSS/JS-Refs angewendet"
