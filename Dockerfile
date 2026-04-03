FROM python:3.12-slim

WORKDIR /app

# System-Abhaengigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Python-Pakete installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY . .

# Streamlit Config
RUN mkdir -p /app/.streamlit

# Verzeichnisse fuer SEO-Seiten und statische Dateien (werden per Volume gemountet)
RUN mkdir -p /app/seo/output /app/static

# Port 8501 (Streamlit Standard)
EXPOSE 8501

# Health-Check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start
CMD ["streamlit", "run", "seasonal_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.baseUrlPath=/app", \
     "--browser.gatherUsageStats=false", \
     "--server.maxUploadSize=5"]
