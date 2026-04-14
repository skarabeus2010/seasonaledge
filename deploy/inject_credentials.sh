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

# .env laden (SUPABASE_URL, SUPABASE_KEY)
source "$ENV_FILE"

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "WARNUNG: SUPABASE_URL oder SUPABASE_KEY leer — Credentials nicht injiziert"
    exit 0
fi

# Placeholder in allen Landing-HTML-Dateien ersetzen
COUNT=$(grep -rl '%%SUPABASE_URL%%\|%%SUPABASE_ANON_KEY%%\|%%UMAMI_WEBSITE_ID%%' "$REPO_DIR/landing/" 2>/dev/null | wc -l)

if [ "$COUNT" -eq 0 ]; then
    echo "Keine Placeholder gefunden — bereits injiziert oder keine Landing-Dateien"
else
    # Umami Website-ID (optional, Fallback auf leeren String)
    UMAMI_ID="${UMAMI_WEBSITE_ID:-}"
    find "$REPO_DIR/landing" -name "*.html" -exec sed -i \
        "s|%%SUPABASE_URL%%|${SUPABASE_URL}|g; s|%%SUPABASE_ANON_KEY%%|${SUPABASE_KEY}|g; s|%%UMAMI_WEBSITE_ID%%|${UMAMI_ID}|g" {} +
    echo "Credentials injiziert in $COUNT Datei(en) (Supabase + Umami)"
fi

# ── Cache-Busting fuer CSS und JS ────────────────────────────
# Haengt ?v=<git-sha> an alle /landing/css/*.css und /landing/js/*.js Refs
# in HTML, damit Browser bei jedem Deploy zwingend neu laden (egal welcher
# Cache-Header). Wirkt auch wenn Mobile Safari auf altem max-age=86400 haengt.
GIT_SHA=$(cd "$REPO_DIR" && git rev-parse --short HEAD 2>/dev/null || date +%s)
echo "Cache-Busting Version: $GIT_SHA"

find "$REPO_DIR/landing" -name "*.html" -exec sed -i -E \
    "s#(/landing/(css|js)/[a-zA-Z0-9_./-]+\.(css|js))(\?v=[a-zA-Z0-9]+)?#\1?v=${GIT_SHA}#g" {} +

echo "Cache-Busting auf alle CSS/JS-Refs angewendet"
