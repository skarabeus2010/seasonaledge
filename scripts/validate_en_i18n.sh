#!/usr/bin/env bash
# =============================================================================
# validate_en_i18n.sh — Automatischer Validierungscheck für EN-Lokalisierung
# Aufruf: bash scripts/validate_en_i18n.sh [--local] [--phase 1]
# --local  : testet gegen http://localhost (Entwicklung)
# --phase N: testet nur eine bestimmte Phase (1-5)
# =============================================================================

BASE="https://seasonalpha.ai"
PHASE_FILTER=""

for arg in "$@"; do
  case $arg in
    --local) BASE="http://localhost" ;;
    --phase) shift; PHASE_FILTER="$1" ;;
  esac
done

PASS=0
FAIL=0
SKIP=0
ERRORS=()

# ── Farben ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC} $1"; ((PASS++)); }
fail() { echo -e "  ${RED}✗${NC} $1"; ((FAIL++)); ERRORS+=("$1"); }
skip() { echo -e "  ${YELLOW}–${NC} $1 (manuell prüfen)"; ((SKIP++)); }
head() { echo -e "\n${BLUE}${BOLD}── $1 ──${NC}"; }

# ── Helper ────────────────────────────────────────────────────────────────────
http_status() { curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$1"; }
body_contains() { curl -s --max-time 10 "$1" | grep -q "$2"; }

# =============================================================================
# PHASE 1 — Infrastruktur
# =============================================================================
run_phase1() {
  head "PHASE 1 — Infrastruktur (nginx, i18n.js, JSON-Dateien)"

  # nginx: EN-URLs antworten mit 200
  for slug in "" "dashboard" "scanner" "backtest-engine" "ki-saisonalitaet" \
              "jahreszyklus" "dekadenzyklus" "monatszyklus" "wochentage" \
              "plain-vanilla" "trifecta" "polymarket" "zentralbanken" \
              "crash-fruehwarnung" "sektor-rotation" "overnight" "tdom-analyse" \
              "spot-vol-beta" "opex" "vixpiration" "feiertage" "mondphasen" \
              "monatswechsel" "intermarket-shocks" "kriegszeiten" "risikozyklus" \
              "dividend-kalender" "earnings-kalender" "watchlist" "pricing"; do
    if [ -z "$slug" ]; then
      url="$BASE/en/"
      label="/en/"
    else
      url="$BASE/en/$slug"
      label="/en/$slug"
    fi
    status=$(http_status "$url")
    if [ "$status" = "200" ]; then
      ok "HTTP 200 für $label"
    else
      fail "HTTP $status für $label (erwartet 200)"
    fi
  done

  # EN-JSON-Datei erreichbar
  status=$(http_status "$BASE/landing/i18n/en.json")
  [ "$status" = "200" ] && ok "en.json erreichbar ($BASE/landing/i18n/en.json)" \
                         || fail "en.json nicht erreichbar (HTTP $status)"

  # DE-JSON noch erreichbar
  status=$(http_status "$BASE/landing/i18n/de.json")
  [ "$status" = "200" ] && ok "de.json erreichbar" \
                         || fail "de.json nicht erreichbar (HTTP $status)"

  # i18n.js erreichbar
  status=$(http_status "$BASE/landing/js/i18n.js")
  [ "$status" = "200" ] && ok "i18n.js erreichbar" \
                         || fail "i18n.js nicht erreichbar (HTTP $status)"

  # DE-Seiten weiterhin funktionsfähig (Regression)
  for slug in "" "dashboard" "jahreszyklus" "scanner" "backtest-engine"; do
    url="$BASE/${slug}"
    label="/${slug:-''}"
    status=$(http_status "$url")
    [ "$status" = "200" ] && ok "DE-Regression OK: $label" \
                           || fail "DE-Regression FEHLER: $label → HTTP $status"
  done

  # Blog noch erreichbar
  status=$(http_status "$BASE/blog/")
  [ "$status" = "200" ] && ok "Blog /blog/ erreichbar" \
                         || fail "Blog /blog/ nicht erreichbar (HTTP $status)"
}

# =============================================================================
# PHASE 2+3 — Seitenübersetzung
# =============================================================================
run_phase2() {
  head "PHASE 2+3 — Seitenübersetzung (data-i18n, lang-Attribut)"

  # <html lang="en"> auf EN-Seiten
  for slug in "" "dashboard" "scanner" "backtest-engine" "ki-saisonalitaet" \
              "jahreszyklus" "dekadenzyklus" "monatszyklus" "plain-vanilla"; do
    url="$BASE/en/${slug}"
    label="/en/${slug:-index}"
    if body_contains "$url" 'lang="en"'; then
      ok "lang=\"en\" gesetzt: $label"
    else
      fail "lang=\"en\" FEHLT auf $label"
    fi
  done

  # <html lang="de"> auf DE-Seiten (Regression)
  for slug in "" "dashboard" "jahreszyklus"; do
    url="$BASE/${slug}"
    label="/${slug:-index} (DE)"
    if body_contains "$url" 'lang="de"'; then
      ok "lang=\"de\" erhalten: $label"
    else
      fail "lang=\"de\" FEHLT auf $label (Regression!)"
    fi
  done

  # data-i18n-Attribute in EN-Pages vorhanden
  for slug in "dashboard" "scanner" "jahreszyklus"; do
    url="$BASE/en/$slug"
    if body_contains "$url" 'data-i18n='; then
      ok "data-i18n-Attribute vorhanden: /en/$slug"
    else
      fail "data-i18n-Attribute FEHLEN in /en/$slug"
    fi
  done

  # Language Switcher in nav.html (async-geladen, daher nicht in serviertem HTML)
  if curl -sf --max-time 15 "$BASE/landing/components/nav.html" 2>/dev/null | grep -q 'nav__lang\|data-lang'; then
    ok "Language Switcher in nav.html gefunden (async component)"
  else
    fail "Language Switcher NICHT in nav.html gefunden"
  fi

  # Kein hartkodierter deutscher Schlüsselwörter-Crash-Test
  # (grobe Heuristik: Prüfe ob typische DE-Wörter als sichtbarer Text bleiben)
  DE_LEAKWORDS=("Saisonalität" "Handelstag" "Wochentage" "Dekadenzyklus" "Jahreszyklus")
  for word in "${DE_LEAKWORDS[@]}"; do
    # Prüfe ob das Wort als data-i18n-Value oder als Rohtext vorkommt
    # (data-i18n-Fallback ist ok, sichtbarer Text ist ein Fehler)
    if curl -s --max-time 10 "$BASE/en/dashboard" | grep -q ">${word}<"; then
      fail "Deutsches Wort als sichtbarer Text: \"$word\" auf /en/dashboard"
    else
      ok "Kein DE-Leak: \"$word\" nicht als sichtbarer Text auf /en/dashboard"
    fi
  done

  # EN-Titel-Check auf Dashboard
  if body_contains "$BASE/en/dashboard" '<title>' ; then
    title_de=$(curl -s --max-time 10 "$BASE/en/dashboard" | grep -oP '(?<=<title>)[^<]+')
    if echo "$title_de" | grep -q "Saisonalität\|Ticker Dashboard"; then
      skip "EN-<title> noch auf Deutsch (JS-rendered, manuell prüfen): $title_de"
    else
      ok "EN-<title> kein offensichtlicher DE-Text"
    fi
  fi
}

# =============================================================================
# PHASE 4 — JS-Module (JS-rendered → nur strukturell prüfbar)
# =============================================================================
run_phase4() {
  head "PHASE 4 — JS-Module (tour-config, Chart-Labels)"

  # tour-config.js: sollte i18n-Keys referenzieren, nicht DE-Strings
  status=$(http_status "$BASE/landing/js/tour-config.js")
  [ "$status" = "200" ] && ok "tour-config.js erreichbar" \
                         || fail "tour-config.js nicht erreichbar (HTTP $status)"

  if body_contains "$BASE/landing/js/tour-config.js" 'i18n\|t("tour\|tour\.'; then
    ok "tour-config.js referenziert i18n-Keys"
  else
    skip "tour-config.js: i18n-Integration nicht verifizierbar ohne Browser"
  fi

  # i18n.js enthält SA.i18n.init-Funktion
  if body_contains "$BASE/landing/js/i18n.js" 'SA.i18n\|sa_i18n\|init'; then
    ok "i18n.js enthält SA.i18n-Implementierung"
  else
    fail "i18n.js hat kein SA.i18n-Objekt"
  fi

  # Manuell zu prüfende JS-Inhalte
  skip "Tour 26 Steps durchklicken (Browser)"
  skip "Dashboard Chart-Labels auf EN prüfen (Browser)"
  skip "Scanner Sidebar-Labels auf EN prüfen (Browser)"
  skip "Backtest Tooltips auf EN prüfen (Browser)"
  skip "Loading-States (\"Calculating...\" statt \"Wird berechnet...\") (Browser)"
}

# =============================================================================
# PHASE 5 — SEO
# =============================================================================
run_phase5() {
  head "PHASE 5 — SEO (hreflang, og:locale, Sitemap)"

  # hreflang auf EN-Seiten
  for slug in "dashboard" "jahreszyklus" "scanner"; do
    if body_contains "$BASE/en/$slug" 'hreflang'; then
      ok "hreflang vorhanden: /en/$slug"
    else
      fail "hreflang FEHLT auf /en/$slug"
    fi
    # Prüfe ob hreflang="de" UND hreflang="en" beide da sind
    if body_contains "$BASE/en/$slug" 'hreflang="de"' && \
       body_contains "$BASE/en/$slug" 'hreflang="en"'; then
      ok "hreflang DE+EN beide vorhanden: /en/$slug"
    else
      fail "hreflang DE oder EN fehlt auf /en/$slug"
    fi
  done

  # hreflang auf DE-Seiten (Gegenstück)
  for slug in "dashboard" "jahreszyklus"; do
    if body_contains "$BASE/$slug" 'hreflang="en"'; then
      ok "hreflang=\"en\" Alternate auf DE-Seite /$slug"
    else
      fail "hreflang=\"en\" fehlt auf DE-Seite /$slug"
    fi
  done

  # og:locale auf EN-Seiten
  if body_contains "$BASE/en/dashboard" 'og:locale.*en_US\|og:locale.*en-'; then
    ok "og:locale=en auf /en/dashboard"
  else
    fail "og:locale auf /en/dashboard nicht auf EN gesetzt"
  fi

  # EN-URLs in Sitemap
  sitemap_en_count=$(curl -s --max-time 15 "$BASE/sitemap.xml" | grep -c "/en/")
  if [ "$sitemap_en_count" -gt 5 ]; then
    ok "Sitemap enthält $sitemap_en_count /en/-URLs"
  elif [ "$sitemap_en_count" -gt 0 ]; then
    fail "Sitemap enthält nur $sitemap_en_count /en/-URLs (erwartet >5)"
  else
    fail "Sitemap enthält KEINE /en/-URLs"
  fi

  # xhtml:link Alternates in Sitemap
  if body_contains "$BASE/sitemap.xml" 'xhtml:link\|hreflang'; then
    ok "Sitemap enthält hreflang xhtml:link Alternates"
  else
    fail "Sitemap hat keine hreflang xhtml:link Alternates"
  fi

  # robots.txt erlaubt /en/
  if body_contains "$BASE/robots.txt" 'Disallow: /en'; then
    fail "robots.txt blockiert /en/ (sollte erlaubt sein)"
  else
    ok "robots.txt blockiert /en/ nicht"
  fi

  # IndexNow-Key noch vorhanden (Regression)
  status=$(http_status "$BASE/c0d4540dc5a10d464d473960f4d20be3.txt")
  [ "$status" = "200" ] && ok "IndexNow-Key erreichbar" \
                         || fail "IndexNow-Key nicht erreichbar (HTTP $status)"

  # GSC-Hinweise (manuell)
  skip "GSC: /en/ als neue Property einrichten"
  skip "GSC: Coverage nach 2 Wochen prüfen (EN-URLs indexiert?)"
  skip "Google Rich Results Test auf 3 EN-Pages"
}

# =============================================================================
# PHASE — Regression (immer laufen)
# =============================================================================
run_regression() {
  head "REGRESSION — Bestehende DE-Funktionen"

  # Wichtige DE-Pages: alle 200
  critical_de=("" "dashboard" "jahreszyklus" "monatszyklus" "wochentage"
               "scanner" "backtest-engine" "ki-saisonalitaet" "plain-vanilla"
               "trifecta" "polymarket" "zentralbanken" "crash-fruehwarnung"
               "blog/" "pricing" "watchlist")
  for slug in "${critical_de[@]}"; do
    url="$BASE/${slug}"
    status=$(http_status "$url")
    [ "$status" = "200" ] && ok "DE /${slug:-index}: 200 OK" \
                           || fail "DE /${slug:-index}: HTTP $status"
  done

  # Auth-Endpoints
  skip "Auth/Login auf DE-Seiten testen (Browser, Google OAuth)"
  skip "Watchlist Cloud-Sync nach EN-Umbau (Browser, Supabase)"
  skip "Newsletter-Subscribe auf Landing (Browser)"
  skip "Nightly-Refresh nach nginx-Änderung (GitHub Actions Log)"
}

# =============================================================================
# MAIN
# =============================================================================
echo -e "${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  SeasonAlpha — EN Lokalisierung Validierungscheck   ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo -e "Basis-URL: ${BLUE}$BASE${NC}"
echo -e "Datum:     $(date '+%Y-%m-%d %H:%M')"

case "$PHASE_FILTER" in
  1) run_phase1 ;;
  2) run_phase2 ;;
  4) run_phase4 ;;
  5) run_phase5 ;;
  *) run_phase1; run_phase2; run_phase4; run_phase5; run_regression ;;
esac

# ── Zusammenfassung ───────────────────────────────────────────────────────────
echo -e "\n${BOLD}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}Ergebnis:${NC}  ${GREEN}$PASS bestanden${NC}  |  ${RED}$FAIL fehlgeschlagen${NC}  |  ${YELLOW}$SKIP manuell${NC}"

if [ ${#ERRORS[@]} -gt 0 ]; then
  echo -e "\n${RED}${BOLD}Fehlgeschlagene Tests:${NC}"
  for err in "${ERRORS[@]}"; do
    echo -e "  ${RED}✗${NC} $err"
  done
fi

echo -e "\n${YELLOW}${BOLD}Manuelle Schritte nach diesem Script:${NC}"
echo -e "  1. Browser: /en/dashboard aufrufen, Sprache visuell prüfen"
echo -e "  2. Language Switcher DE↔EN testen"
echo -e "  3. Tour (26 Steps) auf EN durchklicken"
echo -e "  4. Auth/Login + Watchlist auf EN-Seiten testen"
echo -e "  5. Mobile (375px): Language Switcher + Navigation"
echo -e "  6. PageSpeed Insights: /en/dashboard (LCP, CLS nicht verschlechtert)"
echo -e "  7. GSC: /en/ als separate Property einrichten"
echo -e "  8. Google Rich Results Test auf 3 EN-Pages"
echo -e "${BOLD}══════════════════════════════════════════════════════${NC}\n"

[ "$FAIL" -gt 0 ] && exit 1 || exit 0
