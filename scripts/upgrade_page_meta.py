"""
upgrade_page_meta.py — Erweitert die Meta-Tag-Bloecke der 21 Landing-Pages.

Vorher (minimal):
  <meta name="description" content="...">
  <meta property="og:title" content="...">
  <meta property="og:url" content="...">
  <link rel="canonical" href="...">
  <link rel="icon" href="...">

Nachher (voll ausgestattet):
  - description
  - canonical
  - robots
  - author
  - theme-color
  - og:title / og:description / og:url / og:type / og:image / og:site_name / og:locale
  - twitter:card / twitter:site / twitter:title / twitter:description / twitter:image
  - apple-touch-icon + PNG-Favicon fallback
  - JSON-LD WebPage schema

Idempotent: laeuft mehrfach ohne Duplikate. Erkennt ob schon ein "<!-- SA_META_V2 -->"
Marker drin ist und skippt dann.

Usage:
  py scripts/upgrade_page_meta.py           # dry-run, nur Preview
  py scripts/upgrade_page_meta.py --write   # schreibt die Dateien
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGES_DIR = REPO / "landing" / "pages"
BASE_URL = "https://seasonalpha.ai"
TWITTER_HANDLE = "@SeasonAlph4882"
OG_IMAGE = f"{BASE_URL}/landing/assets/images/og-image.png"
MARKER = "<!-- SA_META_V5 -->"  # V5 = SEO-optimierte Titles eingetragen (nach optimize_page_titles.py)

# Slug -> { slug, type, category } pro Page.
# category = Nav-Gruppe fuer Breadcrumb (Zyklen / Events / Strategien / Mehr)
# Dashboard ist top-level ohne Kategorie.
PAGE_META = {
    "dashboard.html":           {"slug": "dashboard",          "type": "website", "cat": None},
    # Zyklen
    "dekadenzyklus.html":       {"slug": "dekadenzyklus",      "type": "website", "cat": "Zyklen"},
    "jahreszyklus.html":        {"slug": "jahreszyklus",       "type": "website", "cat": "Zyklen"},
    "monatszyklus.html":        {"slug": "monatszyklus",       "type": "website", "cat": "Zyklen"},
    "wochentage.html":          {"slug": "wochentage",         "type": "website", "cat": "Zyklen"},
    "monatswechsel.html":       {"slug": "monatswechsel",      "type": "website", "cat": "Zyklen"},
    "mondphasen.html":          {"slug": "mondphasen",         "type": "website", "cat": "Zyklen"},
    # Events
    "zentralbanken.html":       {"slug": "zentralbanken",      "type": "website", "cat": "Events"},
    "feiertage.html":           {"slug": "feiertage",          "type": "website", "cat": "Events"},
    "opex.html":                {"slug": "opex",               "type": "website", "cat": "Events"},
    "intermarket-shocks.html":  {"slug": "intermarket-shocks", "type": "website", "cat": "Events"},
    # Strategien
    "trifecta.html":            {"slug": "trifecta",           "type": "website", "cat": "Strategien"},
    "plain-vanilla.html":       {"slug": "plain-vanilla",      "type": "website", "cat": "Strategien"},
    "backtest-engine.html":     {"slug": "backtest-engine",    "type": "website", "cat": "Strategien"},
    # Mehr / Advanced
    "ki-saisonalitaet.html":    {"slug": "ki-saisonalitaet",   "type": "website", "cat": "Mehr"},
    "crash-fruehwarnung.html":  {"slug": "crash-fruehwarnung", "type": "website", "cat": "Mehr"},
    "spot-vol-beta.html":       {"slug": "spot-vol-beta",      "type": "website", "cat": "Mehr"},
    "tdom-analyse.html":        {"slug": "tdom-analyse",       "type": "website", "cat": "Mehr"},
    "overnight.html":           {"slug": "overnight",          "type": "website", "cat": "Mehr"},
    "sektor-rotation.html":     {"slug": "sektor-rotation",    "type": "website", "cat": "Mehr"},
    "kriegszeiten.html":        {"slug": "kriegszeiten",       "type": "website", "cat": "Mehr"},
}


def extract_existing(html: str) -> dict:
    """Liest title + description + og:title aus dem bestehenden HTML."""
    out = {}
    m = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    if m:
        out["title"] = m.group(1).strip()
    m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
    if m:
        out["description"] = m.group(1)
    m = re.search(r'<meta\s+property="og:title"\s+content="([^"]*)"', html)
    if m:
        out["og_title"] = m.group(1)
    return out


def build_meta_block(slug: str, title: str, description: str, og_type: str, category: str | None) -> str:
    """Generiert den vollen Meta-Tag-Block inkl. WebPage + BreadcrumbList JSON-LD."""
    url = f"{BASE_URL}/{slug}"
    og_title = title
    # Shortened title fuer OG (ohne "— SeasonAlpha" suffix)
    short_title = re.sub(r"\s*(?:&mdash;|—|-)?\s*SeasonAlpha\s*$", "", title).strip()
    if short_title:
        og_title = f"{short_title} &mdash; SeasonAlpha"

    # BreadcrumbList: Home -> Page (2-Level)
    # Die Nav-Kategorien (Zyklen/Events/Strategien/Mehr) haben keine eigenen URLs
    # (sind nur Dropdown-Gruppen). Google's Validator verlangt fuer jedes ListItem
    # eine item-URL. name-only Zwischenschritte loesen "kritisches Problem" aus.
    # Loesung: Kategorie weglassen, nur Home -> Page.
    # (category-Parameter bleibt im API-Vertrag fuer spaetere Erweiterung, wird hier
    #  aktuell nicht genutzt.)
    _ = category
    breadcrumb_items = [
        f'{{"@type":"ListItem","position":1,"name":"Home","item":"{BASE_URL}/"}}',
        f'{{"@type":"ListItem","position":2,"name":"{short_title}","item":"{url}"}}',
    ]
    breadcrumb_json = (
        '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
        + ",".join(breadcrumb_items)
        + "]}"
    )

    webpage_json = (
        '{"@context":"https://schema.org","@type":"WebPage","name":"'
        + short_title + '","url":"' + url + '","description":"' + description + '",'
        '"isPartOf":{"@type":"WebSite","name":"SeasonAlpha","url":"' + BASE_URL + '"},'
        '"publisher":{"@type":"Organization","name":"SeasonAlpha","url":"' + BASE_URL + '",'
        '"logo":{"@type":"ImageObject","url":"' + OG_IMAGE + '"}}}'
    )

    return f"""  {MARKER}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <meta name="author" content="SeasonAlpha">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <meta name="theme-color" content="#000000">
  <link rel="canonical" href="{url}">

  <!-- Open Graph / Facebook / LinkedIn / WhatsApp / iMessage -->
  <meta property="og:type" content="{og_type}">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{og_title}">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="SeasonAlpha">
  <meta property="og:locale" content="de_DE">

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="{TWITTER_HANDLE}">
  <meta name="twitter:creator" content="{TWITTER_HANDLE}">
  <meta name="twitter:title" content="{og_title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{OG_IMAGE}">

  <!-- Icons -->
  <link rel="icon" type="image/svg+xml" href="/landing/assets/images/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="/landing/assets/images/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/landing/assets/images/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/landing/assets/images/apple-touch-icon.png">

  <!-- Structured Data: WebPage -->
  <script type="application/ld+json">{webpage_json}</script>
  <!-- Structured Data: BreadcrumbList (SERP Rich Result) -->
  <script type="application/ld+json">{breadcrumb_json}</script>
"""


def upgrade_file(path: Path, *, write: bool) -> tuple[bool, str]:
    """Gibt (changed, reason) zurueck."""
    try:
        html = path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"read error: {e}"

    if MARKER in html:
        return False, "already upgraded"

    meta = PAGE_META.get(path.name)
    if not meta:
        return False, "not in PAGE_META"

    existing = extract_existing(html)
    if not existing.get("title") or not existing.get("description"):
        return False, "missing title or description in source"

    # Ersetze den Bereich von <meta charset> bis inkl. dem letzten <link rel="canonical"...>
    # Wir nehmen einen konservativen Ansatz: alles zwischen <head> und dem ersten <style>
    # oder <link rel="stylesheet" href="/landing/css/app.css"> ersetzen.
    head_match = re.search(r"<head>(.*?)(<link\s+rel=\"stylesheet\"\s+href=\"/landing/css/app\.css\">)", html, re.DOTALL)
    if not head_match:
        return False, "could not locate head boundary"

    new_block = build_meta_block(
        slug=meta["slug"],
        title=existing["title"],
        description=existing["description"],
        og_type=meta["type"],
        category=meta.get("cat"),
    )

    # Neue Head-Section: unser Block + Fonts + app.css Link
    # Finde die Fonts-Zeile
    fonts_match = re.search(r'(<link\s+href="https://fonts\.googleapis\.com[^"]*"\s+rel="stylesheet">)', html)
    fonts_line = fonts_match.group(1) if fonts_match else ""
    css_line = '<link rel="stylesheet" href="/landing/css/app.css">'

    new_head_content = (
        "\n" + new_block
        + (f"\n  {fonts_line}" if fonts_line else "")
        + f"\n  {css_line}\n  "
    )

    new_html = html.replace(head_match.group(0), f"<head>{new_head_content}")

    if write:
        path.write_text(new_html, encoding="utf-8")
    return True, "upgraded"


def main() -> None:
    write = "--write" in sys.argv
    mode = "WRITE" if write else "DRY-RUN"
    print(f"=== upgrade_page_meta.py ({mode}) ===")

    changed = 0
    skipped = 0
    errors = 0

    for fname in sorted(PAGE_META.keys()):
        path = PAGES_DIR / fname
        if not path.exists():
            print(f"  [MISS] {fname}")
            errors += 1
            continue
        ok, reason = upgrade_file(path, write=write)
        if ok:
            print(f"  [{mode}] {fname}: {reason}")
            changed += 1
        else:
            print(f"  [SKIP] {fname}: {reason}")
            skipped += 1

    print()
    print(f"  changed: {changed}")
    print(f"  skipped: {skipped}")
    print(f"  errors:  {errors}")
    if not write and changed > 0:
        print()
        print("  -> Run with --write to apply changes.")


if __name__ == "__main__":
    main()
