#!/bin/bash
# Fix nginx routes for new HTML pages
# Run on server: bash scripts/fix_nginx_routes.sh

CONF="deploy/nginx.conf"

# Remove any existing entries for the 3 new pages (alias or rewrite)
sed -i '/location = \/crash-fruehwarnung/,/}/d' "$CONF"
sed -i '/location = \/plain-vanilla/,/}/d' "$CONF"
sed -i '/location = \/trifecta/,/}/d' "$CONF"

# Remove empty lines left behind (max 3 consecutive)
sed -i '/^$/N;/^\n$/d' "$CONF"

# Find the line number of the monatswechsel closing brace to insert after
INSERT_AFTER=$(grep -n "location = /monatswechsel" "$CONF" | head -1 | cut -d: -f1)
if [ -z "$INSERT_AFTER" ]; then
    echo "ERROR: /monatswechsel not found in $CONF"
    exit 1
fi

# Find the closing brace of the monatswechsel block
END_LINE=$(tail -n +"$INSERT_AFTER" "$CONF" | grep -n "}" | head -1 | cut -d: -f1)
INSERT_LINE=$((INSERT_AFTER + END_LINE - 1))

echo "Inserting new routes after line $INSERT_LINE (monatswechsel block end)"

# Insert the 3 new location blocks
sed -i "${INSERT_LINE}a\\
\\
    location = /crash-fruehwarnung {\\
        rewrite ^ /landing/pages/crash-fruehwarnung.html break;\\
        root /app;\\
        add_header Cache-Control \"public, max-age=3600\";\\
    }\\
    location = /plain-vanilla {\\
        rewrite ^ /landing/pages/plain-vanilla.html break;\\
        root /app;\\
        add_header Cache-Control \"public, max-age=3600\";\\
    }\\
    location = /trifecta {\\
        rewrite ^ /landing/pages/trifecta.html break;\\
        root /app;\\
        add_header Cache-Control \"public, max-age=3600\";\\
    }" "$CONF"

echo "Routes added. Verifying..."
grep -n "crash-fruehwarnung\|plain-vanilla\|trifecta" "$CONF"

echo ""
echo "Testing nginx config..."
docker exec seasonalpha-nginx nginx -t

echo ""
echo "Rebuilding nginx..."
docker compose up -d --build nginx

echo ""
echo "Testing URLs..."
sleep 5
for URL in crash-fruehwarnung plain-vanilla trifecta; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://seasonalpha.ai/$URL")
    SIZE=$(curl -s -w "%{size_download}" -o /dev/null "https://seasonalpha.ai/$URL")
    echo "  /$URL -> HTTP $CODE (${SIZE} bytes)"
done

echo "Done!"
