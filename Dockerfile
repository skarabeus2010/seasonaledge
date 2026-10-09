FROM python:3.12-slim

WORKDIR /app

# System-Abhaengigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Python-Pakete installieren (kein PyTorch mehr seit Chronos/NP Entfernung)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# Verzeichnisse fuer SEO-Seiten und statische Dateien (werden per Volume gemountet)
RUN mkdir -p /app/seo/output /app/static

# Kein Webserver mehr (Streamlit abgeschaltet 2026-10-09). Der Container ist nur
# noch der Host fuer die Crons, die per `docker exec` hineinlaufen. Der Haupt-
# prozess wartet und beendet sich sauber auf SIGTERM (docker stop ohne 10-s-Kill).
CMD ["sh", "-c", "trap 'exit 0' TERM INT; while :; do sleep 3600 & wait $!; done"]
