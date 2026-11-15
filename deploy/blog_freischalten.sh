#!/bin/bash
# Einmaliger Blog-Neubau für geplante Artikel (status: scheduled + publish_date).
# Wiederholt die Blog-Schritte des Deploys (deploy.yml), ohne Container-Neubau:
# Blog DE+EN im Container, Sitemap/robots, Releasekennung, SEO-Wächter.
set -euo pipefail
cd /opt/seasonaledge
RELEASE=$(git rev-parse HEAD)
echo "Blog-Freischaltung $(date -u +%FT%TZ), Release $RELEASE"
docker compose exec -T app python3 blog/blog_builder.py --build
python3 seo/programmatic_seo_builder.py
python3 deploy/release_setzen.py "$RELEASE"
python3 scripts/verify_seo_html.py
echo "FERTIG"
