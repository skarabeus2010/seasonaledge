#!/bin/bash
# ============================================================
# SeasonAlpha VPS Setup Script
# Ausfuehren auf dem Hetzner VPS als root:
#   curl -sL https://raw.githubusercontent.com/skarabeus2010/seasonaledge/master/deploy/setup_vps.sh | bash
# Oder manuell:
#   chmod +x setup_vps.sh && ./setup_vps.sh
# ============================================================

set -e

echo "============================================"
echo "  SeasonAlpha VPS Setup"
echo "============================================"

# ── 1. System Update ──────────────────────────────────
echo "[1/6] System Update..."
apt-get update && apt-get upgrade -y

# ── 2. Docker installieren ────────────────────────────
echo "[2/6] Docker installieren..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Docker Compose Plugin
if ! docker compose version &> /dev/null; then
    apt-get install -y docker-compose-plugin
fi

echo "Docker Version: $(docker --version)"
echo "Docker Compose: $(docker compose version)"

# ── 3. Firewall (UFW) ────────────────────────────────
echo "[3/6] Firewall konfigurieren..."
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

# ── 4. Projekt klonen ─────────────────────────────────
echo "[4/6] Projekt klonen..."
cd /opt
if [ -d "seasonaledge" ]; then
    cd seasonaledge && git pull
else
    git clone https://github.com/skarabeus2010/seasonaledge.git
    cd seasonaledge
fi

# ── 5. Environment-Datei erstellen ────────────────────
echo "[5/6] Environment konfigurieren..."
if [ ! -f ".env" ]; then
    cat > .env << 'ENVEOF'
# SeasonAlpha Environment
# Bitte diese Werte ausfuellen:
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx
ANTHROPIC_API_KEY=
ENVEOF
    echo "WICHTIG: .env Datei erstellt — bitte Supabase-Credentials eintragen!"
    echo "  nano /opt/seasonaledge/.env"
fi

# Streamlit Secrets
mkdir -p .streamlit
if [ ! -f ".streamlit/secrets.toml" ]; then
    cat > .streamlit/secrets.toml << 'SECEOF'
# Streamlit Secrets
SUPABASE_URL = "https://xxx.supabase.co"
SUPABASE_KEY = "eyJxxx"
ANTHROPIC_API_KEY = ""
SECEOF
    echo "WICHTIG: .streamlit/secrets.toml erstellt — bitte Credentials eintragen!"
fi

# Certbot-Verzeichnisse
mkdir -p deploy/certbot/conf deploy/certbot/www

# ── 6. Hinweise ───────────────────────────────────────
echo ""
echo "============================================"
echo "  Setup abgeschlossen!"
echo "============================================"
echo ""
echo "Naechste Schritte:"
echo ""
echo "1. Credentials eintragen:"
echo "   nano /opt/seasonaledge/.env"
echo "   nano /opt/seasonaledge/.streamlit/secrets.toml"
echo ""
echo "2. SSL-Zertifikat holen (Domain muss auf diese IP zeigen!):"
echo "   docker compose up -d nginx"
echo "   docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d seasonalpha.ai -d www.seasonalpha.ai --email deine@email.de --agree-tos --no-eff-email"
echo ""
echo "3. App starten:"
echo "   docker compose up -d"
echo ""
echo "4. Pruefen:"
echo "   docker compose ps"
echo "   curl http://localhost:8501/_stcore/health"
echo ""
echo "Die App ist dann erreichbar unter: https://seasonalpha.ai"
echo ""
