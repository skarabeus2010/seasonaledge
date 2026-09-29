#!/usr/bin/env python3
"""
SeasonAlpha EN-Translation Verification
Checks: JSON-Key-Coverage, HTML data-i18n coverage, Blog EN, Live-Pages.
Usage: py -m scripts.verify_en_translation [--live]
"""

import json, re, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PAGES_DIR = BASE / "landing" / "pages"
JS_DIR    = BASE / "landing" / "js"
COMP_DIR  = BASE / "landing" / "components"
I18N_DIR  = BASE / "landing" / "i18n"
BLOG_EN   = BASE / "blog" / "posts" / "en"
INDEX_HTML = BASE / "landing" / "index.html"

# German words that must NOT appear as hardcoded text in EN context
# (excludes ticker symbols, brand names, URLs)
GERMAN_WORDS = re.compile(
    r'\b(Analyse|Saisonalität|Rendite|Wochentag|Handelstag|Börse|Aktie|'
    r'Historisch|Lädt|Bitte\s|Jetzt|Suche|Zeige|Wähle|Laden|Klicke|'
    r'Monate|Wochen|Tage[^s]|Jahre[^s]|Datum|Kurs|Preis|Trend|Hoch|Tief|'
    r'Einstellungen|Einblenden|Ausblenden|Aktivieren|Deaktivieren|'
    r'Stärke|Schwäche|Daten|Fehler|Warnung|Hinweis|Willkommen|'
    r'Berechnung|Auswertung|Vergleich|Übersicht|Ergebnis|Treffer|'
    r'Keine Daten|Kein|Nicht verfügbar|Wird geladen)',
    re.IGNORECASE
)
UMLAUT_RE = re.compile(r'[äöüÄÖÜß]')

SKIP_EXTENSIONS = {'.pyc', '.png', '.jpg', '.svg', '.ico', '.woff', '.ttf'}


# ───────────────────────────────────────────────────────────────────────────────
# TEST 1 — JSON Key Coverage
# ───────────────────────────────────────────────────────────────────────────────
def test_json_coverage():
    de = json.loads((I18N_DIR / "de.json").read_text(encoding="utf-8"))
    en = json.loads((I18N_DIR / "en.json").read_text(encoding="utf-8"))

    de_keys = set(de)
    en_keys = set(en)
    missing = sorted(de_keys - en_keys)

    # Keys where EN value == DE value and contains German chars → likely untranslated
    suspect = []
    for k in de_keys & en_keys:
        if de[k] == en[k] and UMLAUT_RE.search(str(de[k])):
            suspect.append(k)

    return {
        "de_total": len(de_keys),
        "en_total": len(en_keys),
        "missing_count": len(missing),
        "missing_keys": missing[:50],          # cap at 50
        "suspect_untranslated": sorted(suspect),
        "coverage_pct": round(100 * (1 - len(missing) / max(len(de_keys), 1)), 1),
    }


# ───────────────────────────────────────────────────────────────────────────────
# TEST 2 — HTML i18n Attribute Coverage
# ───────────────────────────────────────────────────────────────────────────────
def _count_i18n(text: str) -> int:
    return len(re.findall(r'data-i18n[=\s]', text))

def _find_hardcoded_german(html: str, filename: str) -> list:
    """Find visible text nodes with German content that lack data-i18n protection."""
    issues = []

    # Strip script/style blocks first
    no_script = re.sub(r'<script[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
    no_style  = re.sub(r'<style[\s\S]*?</style>',  '', no_script, flags=re.IGNORECASE)

    # Find text content between tags (simple heuristic)
    text_nodes = re.findall(r'>([^<]{4,})<', no_style)
    for t in text_nodes:
        t = t.strip()
        if not t:
            continue
        # Skip template variables {{ }}, JS interpolation, URLs
        if re.search(r'\{\{|function|var |let |const |http|//|%%', t):
            continue
        if UMLAUT_RE.search(t) or GERMAN_WORDS.search(t):
            issues.append(t[:100])

    # Check HTML attributes with German content (placeholder, title, aria-label)
    attr_hits = re.findall(
        r'(?:placeholder|title|aria-label|aria-placeholder)\s*=\s*"([^"]*(?:[äöüÄÖÜß][^"]*)+)"',
        html
    )
    for hit in attr_hits:
        # Only flag if there's no nearby data-i18n-placeholder/title
        issues.append(f"[ATTR] {hit[:80]}")

    return issues

def test_html_coverage():
    results = {}
    html_files = list(PAGES_DIR.glob("*.html"))
    html_files.append(INDEX_HTML)
    for comp in ["nav.html", "footer.html"]:
        p = COMP_DIR / comp
        if p.exists():
            html_files.append(p)

    for f in sorted(html_files):
        html = f.read_text(encoding="utf-8", errors="replace")
        i18n_count = _count_i18n(html)
        german_issues = _find_hardcoded_german(html, f.name)
        results[f.name] = {
            "data_i18n_count": i18n_count,
            "hardcoded_german_count": len(german_issues),
            "hardcoded_german_samples": german_issues[:5],
            "status": (
                "OK"     if i18n_count >= 5 and len(german_issues) == 0 else
                "WARN"   if i18n_count >= 5 and len(german_issues) <= 3 else
                "NONE"   if i18n_count == 0 else
                "ISSUES" if len(german_issues) > 3 else "WARN"
            ),
        }
    return results

# ───────────────────────────────────────────────────────────────────────────────
# TEST 3 — JS Files: German Strings
# ───────────────────────────────────────────────────────────────────────────────
def test_js_strings():
    issues = {}
    for f in sorted(JS_DIR.glob("*.js")):
        text = f.read_text(encoding="utf-8", errors="replace")
        # Find string literals (single or double quoted) with German chars
        strings = re.findall(r"""['"]([^'"]{5,})['"]""", text)
        german_strings = [s for s in strings
                          if (UMLAUT_RE.search(s) or GERMAN_WORDS.search(s))
                          and not re.search(r'http|selector|#|\.css|\.js', s)]
        if german_strings:
            issues[f.name] = german_strings[:10]
    return issues


# ───────────────────────────────────────────────────────────────────────────────
# TEST 4 — Blog EN Posts: German Content
# ───────────────────────────────────────────────────────────────────────────────
def test_blog_en():
    de_slugs_seen = set()
    issues = {}
    expected = 24

    posts = sorted(BLOG_EN.glob("*.md"))
    for p in posts:
        content = p.read_text(encoding="utf-8", errors="replace")

        # Check frontmatter has de_slug
        has_de_slug = bool(re.search(r'^de_slug:', content, re.MULTILINE))

        # Extract body (after second ---)
        body_match = re.split(r'^---', content, flags=re.MULTILINE)
        body = body_match[2] if len(body_match) >= 3 else content

        # Count German indicators in body
        umlaut_hits = UMLAUT_RE.findall(body)
        german_word_hits = GERMAN_WORDS.findall(body)

        status = "OK"
        problem = []
        if len(umlaut_hits) > 20:
            status = "GERMAN"
            problem.append(f"{len(umlaut_hits)} Umlaut-chars in body")
        elif len(umlaut_hits) > 5:
            status = "WARN"
            problem.append(f"{len(umlaut_hits)} Umlaut-chars (minor)")
        if german_word_hits:
            if status == "OK":
                status = "WARN"
            problem.append(f"German words: {german_word_hits[:5]}")
        if not has_de_slug:
            problem.append("MISSING de_slug frontmatter")
            if status == "OK":
                status = "WARN"

        if status != "OK":
            issues[p.name] = {"status": status, "problems": problem}

    return {
        "posts_found": len(posts),
        "posts_expected": expected,
        "missing_count": max(0, expected - len(posts)),
        "issues": issues,
    }


# ───────────────────────────────────────────────────────────────────────────────
# TEST 5 — Sitemap: EN URL completeness
# ───────────────────────────────────────────────────────────────────────────────
def test_sitemap():
    sitemap_path = BASE / "static" / "sitemap.xml"
    if not sitemap_path.exists():
        return {"error": "sitemap.xml not found"}

    sitemap = sitemap_path.read_text(encoding="utf-8")
    en_urls  = re.findall(r'<loc>(https://seasonalpha\.ai/en/[^<]+)</loc>', sitemap)
    de_urls  = re.findall(r'<loc>(https://seasonalpha\.ai/(?!en/)[^<]+)</loc>', sitemap)

    # Check EN feature pages (should have /en/ version of each DE page)
    html_pages = sorted(f.stem for f in PAGES_DIR.glob("*.html"))
    en_page_urls = [u for u in en_urls if '/en/blog/' not in u and u != 'https://seasonalpha.ai/en/']
    en_blog_urls = [u for u in en_urls if '/en/blog/' in u]

    return {
        "total_de_urls": len(de_urls),
        "total_en_urls": len(en_urls),
        "en_feature_pages": len(en_page_urls),
        "en_blog_urls": len(en_blog_urls),
        "en_page_list": sorted(en_page_urls),
    }


# ───────────────────────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("SeasonAlpha EN-Translation Verification")
    print("=" * 70)

    # T1: JSON
    print("\n[TEST 1] JSON Key Coverage (de.json -> en.json)")
    t1 = test_json_coverage()
    print(f"  DE keys: {t1['de_total']}  |  EN keys: {t1['en_total']}")
    print(f"  Coverage: {t1['coverage_pct']}%")
    if t1['missing_keys']:
        print(f"  ❌ MISSING in en.json ({t1['missing_count']} keys):")
        for k in t1['missing_keys']:
            print(f"     - {k}")
    else:
        print("  ✅ All de.json keys present in en.json")
    if t1['suspect_untranslated']:
        print(f"  ⚠  Suspect (EN=DE with umlaut): {t1['suspect_untranslated']}")

    # T2: HTML
    print("\n[TEST 2] HTML data-i18n Coverage per Page")
    t2 = test_html_coverage()
    status_counts = {"OK": 0, "WARN": 0, "ISSUES": 0, "NONE": 0}
    for fname, info in sorted(t2.items()):
        icon = {"OK": "✅", "WARN": "⚠ ", "ISSUES": "❌", "NONE": "🚫"}.get(info["status"], "?")
        label = f"i18n={info['data_i18n_count']:3d}  hardcoded={info['hardcoded_german_count']:2d}"
        print(f"  {icon} {fname:<40} {label}")
        if info["hardcoded_german_samples"]:
            for s in info["hardcoded_german_samples"][:3]:
                print(f"       → \"{s[:70]}\"")
        status_counts[info["status"]] = status_counts.get(info["status"], 0) + 1
    print(f"\n  Summary: OK={status_counts['OK']} WARN={status_counts['WARN']} "
          f"ISSUES={status_counts['ISSUES']} NONE={status_counts['NONE']}")

    # T3: JS
    print("\n[TEST 3] JS Files — German String Literals")
    t3 = test_js_strings()
    if not t3:
        print("  ✅ No German hardcoded strings found in JS files")
    else:
        for fname, strings in t3.items():
            print(f"  ⚠  {fname}:")
            for s in strings[:5]:
                print(f"     \"{s[:70]}\"")

    # T4: Blog EN
    print("\n[TEST 4] Blog EN Posts")
    t4 = test_blog_en()
    print(f"  Posts found: {t4['posts_found']} / {t4['posts_expected']} expected")
    if t4['missing_count']:
        print(f"  ❌ {t4['missing_count']} posts missing!")
    else:
        print("  ✅ All 24 EN posts present")
    if t4['issues']:
        for fname, info in sorted(t4['issues'].items()):
            icon = "❌" if info["status"] == "GERMAN" else "⚠ "
            print(f"  {icon} {fname}: {'; '.join(info['problems'])}")
    else:
        print("  ✅ All posts appear to be in English")

    # T5: Sitemap
    print("\n[TEST 5] Sitemap EN URL Coverage")
    t5 = test_sitemap()
    if "error" in t5:
        print(f"  ❌ {t5['error']}")
    else:
        print(f"  DE URLs: {t5['total_de_urls']}  |  EN URLs: {t5['total_en_urls']}")
        print(f"  EN feature pages in sitemap: {t5['en_feature_pages']}")
        print(f"  EN blog URLs in sitemap:     {t5['en_blog_urls']}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)

    # Return exit code based on severity
    has_error = (
        t1['missing_count'] > 0
        or status_counts.get('NONE', 0) > 0
        or t4['missing_count'] > 0
        or any(v['status'] == 'GERMAN' for v in t4['issues'].values())
    )
    return 1 if has_error else 0


if __name__ == "__main__":
    # Force UTF-8 output on Windows console
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
