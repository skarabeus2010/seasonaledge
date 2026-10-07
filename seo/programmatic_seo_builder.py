"""
programmatic_seo_builder.py — SEO Landingpage Generator
=========================================================
Generiert automatisch SEO-optimierte HTML-Landingpages,
sitemap.xml, robots.txt und Disclaimer aus der SYMBOLS-Datenbank.

Ausfuehren:  py seo/programmatic_seo_builder.py
Ergebnis:    seo/output/ mit HTML-Seiten + sitemap.xml + robots.txt + disclaimer.html

Abhaengigkeit: pip install Jinja2
"""

# ── Imports ──────────────────────────────────────────────────────────────────

import os
import sys
import re
import unicodedata
from datetime import datetime

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Projekt-Root finden damit shared/ importiert werden kann
_skript_ordner = os.path.dirname(os.path.abspath(__file__))
_projekt_root = os.path.dirname(_skript_ordner)
_REPO = Path(_projekt_root)
if _projekt_root not in sys.path:
    sys.path.insert(0, _projekt_root)

from shared.symbols import SYMBOLS


# ── Konfiguration ────────────────────────────────────────────────────────────

BASE_URL = "https://seasonalpha.ai"
KI_COUNT = 15

# Kategorie → SEO-Typ-Bezeichnung
KATEGORIE_TYP = {
    "US-Index":         "Index",
    "US-ETF":           "ETF",
    "US-Aktie":         "Aktie",
    "EU-Index":         "Index",
    "EU-Aktie":         "Aktie",
    "Asien-Index":      "Index",
    "Rohstoff":         "Rohstoff",
    "Futures":          "Futures",
    "Anleihen":         "Anleihe-ETF",
    "Emerging Markets": "ETF",
    "Krypto":           "Kryptowaehrung",
    "FX":               "Waehrungspaar",
}


# ── Slug-Generator ──────────────────────────────────────────────────────────

def make_slug(name: str) -> str:
    """Erzeugt einen URL-freundlichen Slug aus dem Anzeigenamen.
    'S&P 500' → 'sp-500-saisonalitaet'
    'Öl (WTI)' → 'oel-wti-saisonalitaet'
    """
    slug = name.lower()
    # Umlaute + Sonderzeichen
    slug = slug.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    slug = slug.replace("ß", "ss").replace("&", "")
    # Unicode normalisieren (z.B. Akzente entfernen)
    slug = unicodedata.normalize("NFKD", slug).encode("ascii", "ignore").decode()
    # Nur Buchstaben, Ziffern, Bindestriche
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    # Doppelte Bindestriche entfernen
    slug = re.sub(r"-{2,}", "-", slug)
    return f"{slug}-saisonalitaet"


# ── Titel-Daten aus SYMBOLS generieren ──────────────────────────────────────

def build_titel_daten() -> list[dict]:
    """Konvertiert die SYMBOLS-Datenbank in SEO-Titel-Daten.
    Verwendet Platzhalter-Statistiken (bester_monat etc.), die spaeter
    durch echte Berechnungen aus Supabase ersetzt werden koennen.
    """
    # Monatsnamen fuer zufaellige Verteilung (deterministisch per Ticker-Hash)
    monate = [
        "Januar", "Februar", "Maerz", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ]

    titel_daten = []
    for ticker, info in SYMBOLS.items():
        name = info["name"]
        kategorie = info["kategorie"]
        typ = KATEGORIE_TYP.get(kategorie, "Finanzinstrument")
        slug = make_slug(name)

        # Deterministischer Platzhalter basierend auf Ticker-Hash
        h = hash(ticker) % 12
        bester_monat = monate[h]
        win_rate = str(60 + (hash(ticker + "wr") % 18))  # 60-77%
        avg_return_val = 1.5 + (hash(ticker + "ar") % 80) / 10  # 1.5-9.5%
        avg_return = f"+{avg_return_val:.1f}%"
        jahre = str(max(10, min(30, 20 + (hash(ticker + "j") % 15))))  # 10-30

        titel_daten.append({
            "ticker":       ticker,
            "name":         name,
            "slug":         slug,
            "typ":          typ,
            "bester_monat": bester_monat,
            "win_rate":     win_rate,
            "avg_return":   avg_return,
            "jahre":        jahre,
        })

    return titel_daten


# ── Sitemap Generator ────────────────────────────────────────────────────────

# Prioritaeten/Ausschluesse der Landing-Seiten (Modulebene, auch fuer den Waechter)
PRIORITY_OVERRIDES = {
    # Kernstuecke
    "dashboard":          ("1.0",  "daily"),
    "jahreszyklus":       ("0.95", "daily"),
    "monatszyklus":       ("0.95", "daily"),
    "dekadenzyklus":      ("0.9",  "weekly"),
    "wochentage":         ("0.9",  "weekly"),
    "monatswechsel":      ("0.9",  "weekly"),
    "zentralbanken":      ("0.9",  "weekly"),
    "wahlen":             ("0.85", "weekly"),
    "polymarket":         ("0.95", "daily"),
    # Strategien
    "scanner":            ("0.95", "daily"),
    "trifecta":           ("0.9",  "weekly"),
    "plain-vanilla":      ("0.95", "weekly"),
    "backtest-engine":    ("0.95", "weekly"),
    # Advanced
    "ki-saisonalitaet":   ("0.9",  "daily"),
    "crash-fruehwarnung": ("0.9",  "daily"),
    # Rand
    "kriegszeiten":       ("0.7",  "monthly"),
    "overnight":          ("0.8",  "weekly"),
    # Neue Pages (KW16-18)
    "risikozyklus":       ("0.85", "weekly"),
    "vixpiration":        ("0.85", "weekly"),
    "dividend-kalender":  ("0.85", "weekly"),
    "earnings-kalender":  ("0.85", "weekly"),
    # Pricing
    "pricing":            ("0.8",  "monthly"),
}
PAGE_EXCLUDES = {
    "_disabled", "404", "index",
    "apex-demo",    # Dev/Demo-Chart, nicht produktiv
    "unsubscribe",  # Newsletter-Abmeldung, kein SEO-Ziel (noindex)
    "watchlist",    # Personalisiert, localStorage, kein SEO-Ziel (noindex)
    "profile",      # Personalisiert, eingeloggt only, kein SEO-Ziel (noindex)
}


def _git_datum(pfad: Path) -> str | None:
    """Datum (YYYY-MM-DD) des letzten Commits, der die Datei geaendert hat.

    Laeuft auf dem Host (dort liegt das Git-Repo mit voller Historie). Ohne
    verlaessliche Antwort: None -> die URL bekommt KEIN lastmod. Frueher stand
    ueberall das Build-Datum, womit lastmod nichts mehr aussagte.
    """
    import subprocess
    # SA_GIT_WURZEL: Git-Historie eines anderen Checkouts lesen (nur fuer den
    # Mutationstest, der in einer Kopie ohne .git laeuft; Pfade relativ gleich).
    wurzel = os.environ.get("SA_GIT_WURZEL") or str(_REPO)
    try:
        rel = str(Path(pfad).resolve().relative_to(_REPO.resolve()))
    except ValueError:
        return None
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel],
                           cwd=wurzel, capture_output=True, text=True, timeout=20)
    except Exception:
        return None
    d = r.stdout.strip()
    return d if r.returncode == 0 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else None


def _ist_noindex(pfad: Path) -> bool:
    m = re.search(r'<meta\s+name="robots"\s+content="([^"]*)"',
                  pfad.read_text(encoding="utf-8", errors="replace"))
    return bool(m and "noindex" in m.group(1).lower())


def sitemap_eintraege() -> list[dict]:
    """Alle Sitemap-URLs als Liste von Dicts {loc, lastmod, changefreq, priority, alternates}.

    Regeln (SEO-Review 2026-09-30, docs/SEO_UMSETZUNGSPLAN_2026-09.md):
    - nur indexierbare Seiten (kein `noindex`, veroeffentlicht);
    - EN-Fassung nur, wenn sie existiert (`_EN_PAGE_META`, Blog-Paare ueber `de_slug`);
    - hreflang je Paar in beide Richtungen, x-default = DE;
    - lastmod = letzte wesentliche Aenderung, sonst weggelassen.
    Wird auch vom Waechter (scripts/verify_seo_html.py) gelesen.
    """
    from shared.seo_basis import en_seiten_meta, blog_artikel, blog_hreflang_ziele

    en_seiten = set(en_seiten_meta())
    eintraege: list[dict] = []

    def paar(de_url: str, en_url: str | None) -> list[tuple[str, str]]:
        if not en_url:
            return []
        return [("de", de_url), ("en", en_url), ("x-default", de_url)]

    def neu(loc, lastmod, freq, prio, alternates=()):
        eintraege.append({"loc": loc, "lastmod": lastmod, "changefreq": freq,
                          "priority": prio, "alternates": list(alternates)})

    # Startseite DE + EN
    start_datum = _git_datum(_REPO / "landing" / "index.html")
    alt = paar(f"{BASE_URL}/", f"{BASE_URL}/en/")
    neu(f"{BASE_URL}/", start_datum, "weekly", "1.0", alt)
    neu(f"{BASE_URL}/en/", start_datum, "weekly", "0.9", alt)

    # Statische Seiten ohne EN-Fassung. /disclaimer fehlt bewusst: die Seite ist
    # noindex (Rechtstext), stand aber bis 2026-09-30 trotzdem in der Sitemap.
    for slug, datei, prio, freq in [
        ("ueber-uns", _REPO / "landing" / "ueber-uns.html", "0.7", "monthly"),
        ("rechtliches", _REPO / "landing" / "rechtliches.html", "0.3", "yearly"),
        ("tools/trading-day-converter", _REPO / "seo" / "tools" / "trading-day-converter.html",
         "0.9", "monthly"),
    ]:
        if _ist_noindex(datei):
            continue
        neu(f"{BASE_URL}/{slug}", _git_datum(datei), freq, prio)

    # Landing-Feature-Seiten (Auto-Discovery), ohne noindex
    for html_datei in sorted((_REPO / "landing" / "pages").glob("*.html")):
        slug = html_datei.stem
        if slug in PAGE_EXCLUDES or _ist_noindex(html_datei):
            continue
        prio, freq = PRIORITY_OVERRIDES.get(slug, ("0.85", "weekly"))
        de_url = f"{BASE_URL}/{slug}"
        en_url = f"{BASE_URL}/en/{slug}" if slug in en_seiten else None
        datum = _git_datum(html_datei)
        alt = paar(de_url, en_url)
        neu(de_url, datum, freq, prio, alt)
        if en_url:
            neu(en_url, datum, freq, str(round(float(prio) - 0.1, 2)), alt)

    # Blog: Startseite + Kategorien (beide Sprachen, gleiche Pfade)
    de_art = [a for a in blog_artikel("de") if a["indexierbar"]]
    en_art = [a for a in blog_artikel("en") if a["indexierbar"]]
    def neuester(arts):
        d = max((a["geaendert"] for a in arts), default=None)
        return d.isoformat() if d else None
    kategorien = ["", "education/", "marktausblick/", "tutorials/"]
    for pfad in kategorien:
        kat = pfad.rstrip("/")
        de_k = [a for a in de_art if not kat or a["meta"].get("category", "education") == kat]
        en_k = [a for a in en_art if not kat or a["meta"].get("category", "education") == kat]
        de_url, en_url = f"{BASE_URL}/blog/{pfad}", f"{BASE_URL}/en/blog/{pfad}"
        alt = paar(de_url, en_url)
        prio = "0.9" if not pfad else "0.8"
        neu(de_url, neuester(de_k), "weekly", prio, alt)
        neu(en_url, neuester(en_k), "weekly", str(round(float(prio) - 0.1, 2)), alt)

    # Blog-Artikel, reziprokes hreflang nach derselben Regel wie im Blog-HTML
    # (shared.seo_basis.blog_hreflang_ziele: nur indexierbare Gegenstuecke)
    de_zu_en, en_zu_de = blog_hreflang_ziele()      # wirft bei Fehlverweis
    for a in de_art:
        de_url = f"{BASE_URL}/blog/{a['slug']}/"
        e = de_zu_en.get(a["slug"])
        en_url = f"{BASE_URL}/en/blog/{e}/" if e else None
        neu(de_url, a["geaendert"].isoformat(), "monthly", "0.75", paar(de_url, en_url))
    for a in en_art:
        en_url = f"{BASE_URL}/en/blog/{a['slug']}/"
        d = en_zu_de.get(a["slug"])
        de_url = f"{BASE_URL}/blog/{d}/" if d else None
        neu(en_url, a["geaendert"].isoformat(), "monthly", "0.65",
            paar(de_url, en_url) if de_url else [])
    return eintraege


def build_sitemap(titel_daten: list[dict], output_ordner: str):
    """Schreibt sitemap.xml aus sitemap_eintraege() (titel_daten nur noch API-Rest)."""
    _ = titel_daten
    from xml.sax.saxutils import escape, quoteattr
    teile = []
    for e in sitemap_eintraege():
        z = [f"  <url>", f"    <loc>{escape(e['loc'])}</loc>"]
        for sprache, href in e["alternates"]:
            z.append(f'    <xhtml:link rel="alternate" hreflang="{sprache}" href={quoteattr(href)}/>')
        if e["lastmod"]:
            z.append(f"    <lastmod>{e['lastmod']}</lastmod>")
        z.append(f"    <changefreq>{e['changefreq']}</changefreq>")
        z.append(f"    <priority>{e['priority']}</priority>")
        z.append("  </url>")
        teile.append(chr(10).join(z))
    xml = chr(10).join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
        ' xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        *teile, "</urlset>", ""])
    path = os.path.join(output_ordner, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"  [OK] sitemap.xml ({len(teile)} URLs)")


# ── robots.txt Generator ────────────────────────────────────────────────────

def build_robots_txt(output_ordner: str):
    """Generiert robots.txt mit Sitemap-Verweis und expliziter AI-Crawler-Policy."""
    content = (
        "# SeasonAlpha — robots.txt\n"
        "# ==========================\n"
        "\n"
        "# Standard-Suchmaschinen (Google, Bing, DuckDuckGo, etc.)\n"
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "# Streamlit-App nicht crawlen (dynamische Inhalte, Authenticated)\n"
        "Disallow: /_stcore/\n"
        "Disallow: /static/\n"
        "Disallow: /app/\n"
        "\n"
        "# Interne Landing-Pfade nicht crawlen (liefern 404, keine echten Pages)\n"
        "Disallow: /landing/pages/\n"
        "\n"
        "# /landing/data/ ist bewusst NICHT gesperrt: die Seiten laden dort Daten zum\n"
        "# Rendern; nginx setzt X-Robots-Tag: noindex fuer die JSON-Dateien.\n"
        "# /analyse/ ist bewusst NICHT gesperrt: die alten Seiten liefern 410 Gone,\n"
        "# und nur ohne Sperre kann Google das sehen und sie verwerfen (2026-09-30).\n"
        "\n"
        "# ── AI-Crawler Policy ──────────────────────────────────────────────\n"
        "# Entscheidung 2026-04-10: AI-Crawler DUERFEN unsere Inhalte indexieren.\n"
        "# Begruendung: SeasonAlpha ist ein freies Tool das von Sichtbarkeit lebt.\n"
        "# Erwaehnung in ChatGPT / Claude / Perplexity Antworten = Brand Awareness.\n"
        "# Um AI-Crawler zu BLOCKIEREN: 'Allow: /' unten jeweils durch 'Disallow: /' ersetzen.\n"
        "\n"
        "# OpenAI (GPT-4, ChatGPT Browse, SearchGPT)\n"
        "User-agent: GPTBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: OAI-SearchBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: ChatGPT-User\n"
        "Allow: /\n"
        "\n"
        "# Anthropic (Claude, Claude.ai)\n"
        "User-agent: ClaudeBot\n"
        "Allow: /\n"
        "\n"
        "User-agent: Claude-Web\n"
        "Allow: /\n"
        "\n"
        "User-agent: anthropic-ai\n"
        "Allow: /\n"
        "\n"
        "# Perplexity\n"
        "User-agent: PerplexityBot\n"
        "Allow: /\n"
        "\n"
        "# Google Bard / Gemini (separater Crawler vom Google-Such-Bot)\n"
        "User-agent: Google-Extended\n"
        "Allow: /\n"
        "\n"
        "# Common Crawl (Datenquelle fuer viele LLM-Trainings)\n"
        "User-agent: CCBot\n"
        "Allow: /\n"
        "\n"
        "# Cohere\n"
        "User-agent: cohere-ai\n"
        "Allow: /\n"
        "\n"
        "# Meta AI\n"
        "User-agent: Meta-ExternalAgent\n"
        "Allow: /\n"
        "\n"
        "User-agent: FacebookBot\n"
        "Allow: /\n"
        "\n"
        "# Apple Intelligence\n"
        "User-agent: Applebot-Extended\n"
        "Allow: /\n"
        "\n"
        "# ByteDance (TikTok, Doubao)\n"
        "User-agent: Bytespider\n"
        "Allow: /\n"
        "\n"
        "# Mistral\n"
        "User-agent: MistralAI-User\n"
        "Allow: /\n"
        "\n"
        "# Crawl-delay fuer aggressive Crawler (10 Sekunden)\n"
        "User-agent: SemrushBot\n"
        "Crawl-delay: 10\n"
        "\n"
        "User-agent: AhrefsBot\n"
        "Crawl-delay: 10\n"
        "\n"
        "User-agent: MJ12bot\n"
        "Crawl-delay: 10\n"
        "\n"
        "# KI-/LLM-Crawler: kuratiertes Inhaltsverzeichnis unter /llms.txt\n"
        f"Sitemap: {BASE_URL}/sitemap.xml\n"
    )
    path = os.path.join(output_ordner, "robots.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [OK] robots.txt (mit AI-Crawler Policy)")


# ── llms.txt Generator (GEO / KI-Suchmaschinen) ─────────────────────────────

def build_llms_txt(output_ordner: str):
    """Generiert /llms.txt — kuratiertes Inhaltsverzeichnis fuer KI-Crawler
    (ChatGPT-Search, Perplexity, Claude, Google AI Overviews). Konvention nach
    llmstxt.org: H1 + Blockquote-Summary + Link-Sektionen (Markdown)."""
    b = BASE_URL
    content = f"""# SeasonAlpha

> Datengetriebene saisonale Börsenanalyse mit bis zu 131 Jahren Marktdaten,
> 270+ Basiswerten (Aktien, ETFs, Futures, Crypto, FX) und KI-Composite-Score.
> Kostenlos. Deutsch: {b}/ · English: {b}/en/

SeasonAlpha findet wiederkehrende saisonale Muster in Finanzmärkten — Jahres-
und Dekadenzyklus, Monatswechsel, Handelstag-Effekte (TDoM), OPEX, Zentralbank-
Termine, Mondphasen u.v.m. Methodik: normalisierte Renditen (jedes Jahr startet
bei 100, tägliche Returns kumulieren) — keine absoluten Preisänderungen.

## Kern-Tools
- [Dashboard]({b}/dashboard): Alle Saisonal-Signale für einen Ticker auf einen Blick — KI-Score, Crash-Ampel, Jahreschart, TruePath-Muster, Strategien, Events.
- [Jahreszyklus]({b}/jahreszyklus): Saisonaler Jahresverlauf mit Perzentil-Bändern, Monats-/Quartals-Performance und Mustervergleich.
- [Dekadenzyklus]({b}/dekadenzyklus): 131 Jahre Dow-Jones-Muster nach Jahresend-Ziffer + Anomalie-Radar.
- [KI-Saisonalität]({b}/ki-saisonalitaet): Composite-Score 0-10 aus 4 Sub-Scores + TruePath-Mustervergleich mit Sigma-Cone-Projektion.
- [Backtest-Engine]({b}/backtest-engine): Saisonale Event-Strategien testen (OPEX, FOMC, Mondphasen, Feiertage) — Equity-Kurve, Sharpe, Max DD, look-ahead-bias-frei.
- [Saisonal-Scanner]({b}/scanner): 270+ Ticker nach KI-Composite-Score sortiert, filterbar.
- [Polymarket]({b}/polymarket): Prognosemarkt-Wahrscheinlichkeiten (Fed-Pfad, Crypto) neben historischer Saisonalität + Brier-Score-Kalibrierung.

## Themen-Tools
- [OPEX & Triple Witching]({b}/opex), [Zentralbank-Effekt]({b}/zentralbanken), [Monatswechsel]({b}/monatswechsel), [Wochentage]({b}/wochentage), [Mondphasen]({b}/mondphasen), [Feiertage]({b}/feiertage), [TDoM-Analyse]({b}/tdom-analyse), [Spot-Vol-Beta]({b}/spot-vol-beta), [VIXpiration]({b}/vixpiration), [Sektor-Rotation]({b}/sektor-rotation), [Intermarket-Shocks]({b}/intermarket-shocks), [Risikozyklus]({b}/risikozyklus).

## Blog
- [Blog]({b}/blog/): Saisonalitäts-Analysen mit eigenen Daten (Fed, CPI, Polymarket, Sell-in-May u.a.).

## English
- [English version]({b}/en/): All tools and the blog are available in English under /en/.

## Hinweis
Keine Anlageberatung. Vergangene Ergebnisse und saisonale Muster garantieren
keine zukünftigen Erträge. Details: [Disclaimer]({b}/disclaimer).
"""
    path = os.path.join(output_ordner, "llms.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [OK] llms.txt (KI-Crawler Inhaltsverzeichnis)")


# ── Disclaimer Generator ────────────────────────────────────────────────────

def build_disclaimer(output_ordner: str):
    """Generiert eine rechtliche Disclaimer-Seite (YMYL-konform)."""
    html = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Haftungsausschluss | SeasonAlpha</title>
    <meta name="description" content="Rechtlicher Haftungsausschluss fuer SeasonAlpha. Keine Anlageberatung. Historische Daten garantieren keine zukuenftigen Ergebnisse.">
    <meta name="google-site-verification" content="46lbAINaqCQSU5pWAplt6WioigjnIc3mmLMBnCteMwk">
    <meta name="robots" content="noindex, follow">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', -apple-system, sans-serif;
            background: #080c12; color: #c8d6e5; line-height: 1.8;
        }
        .container { max-width: 800px; margin: 0 auto; padding: 2rem 1.5rem; }
        h1 { font-size: 2rem; font-weight: 800; color: #e8edf5; margin-bottom: 1.5rem; }
        h2 {
            font-size: 1.2rem; font-weight: 700; color: #e8edf5;
            margin: 2rem 0 0.8rem; padding-top: 1rem; border-top: 1px solid #1c2a3e;
        }
        p, li { margin-bottom: 0.8rem; color: #a0b0c5; }
        ul { padding-left: 1.5rem; }
        .highlight {
            background: #0f1923; border: 1px solid #1c2a3e; border-radius: 12px;
            padding: 1.5rem; margin: 1.5rem 0;
        }
        .highlight strong { color: #ff6b6b; }
        .breadcrumb { font-size: 0.85rem; color: #5a6e85; margin-bottom: 1.5rem; }
        .breadcrumb a { color: #4d9fff; text-decoration: none; }
        .footer {
            margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #1c2a3e;
            font-size: 0.8rem; color: #3a4a5e; text-align: center;
        }
        .footer a { color: #4d9fff; text-decoration: none; }
        .update-date { color: #5a6e85; font-size: 0.85rem; margin-bottom: 2rem; }
    </style>
</head>
<body>
<div class="container">

    <nav class="breadcrumb">
        <a href="https://seasonalpha.ai">SeasonAlpha</a> &rsaquo; Haftungsausschluss
    </nav>

    <h1>Haftungsausschluss &amp; rechtliche Hinweise</h1>
    <p class="update-date">Letzte Aktualisierung: """ + datetime.now().strftime("%d.%m.%Y") + """</p>

    <!-- ── 1. Keine Anlageberatung ─────────────────────────────────── -->

    <div class="highlight">
        <strong>Wichtiger Hinweis:</strong> SeasonAlpha bietet <strong>keine Anlageberatung</strong>
        und gibt <strong>keine Kauf- oder Verkaufsempfehlungen</strong> ab. Alle auf dieser Plattform
        bereitgestellten Informationen dienen ausschliesslich zu Informations- und Bildungszwecken.
    </div>

    <h2>1. Keine Anlageberatung</h2>
    <p>
        Die auf SeasonAlpha dargestellten Analysen, Statistiken, Prognosen und Bewertungen
        stellen keine individuelle Anlageberatung im Sinne des Wertpapierhandelsgesetzes (WpHG)
        oder des Kreditwesengesetzes (KWG) dar. SeasonAlpha ist kein zugelassener Finanzberater,
        Vermoegensverwalter oder Anlageberater gemaess &sect; 34f GewO.
    </p>
    <ul>
        <li>Wir geben keine Empfehlungen zum Kauf, Verkauf oder Halten von Finanzinstrumenten.</li>
        <li>Jede Anlageentscheidung liegt ausschliesslich in der Verantwortung des Nutzers.</li>
        <li>Wir empfehlen, vor jeder Investition einen zugelassenen Finanzberater zu konsultieren.</li>
    </ul>

    <!-- ── 2. Historische Daten ────────────────────────────────────── -->

    <h2>2. Historische Daten &amp; Saisonalitaet</h2>
    <p>
        SeasonAlpha analysiert historische Kursdaten, um saisonale Muster und statistische
        Wahrscheinlichkeiten zu identifizieren. Dabei gilt:
    </p>
    <ul>
        <li><strong>Vergangene Wertentwicklungen sind kein zuverlaessiger Indikator fuer
            zukuenftige Ergebnisse.</strong></li>
        <li>Saisonale Muster koennen sich jederzeit aendern oder vollstaendig ausbleiben.</li>
        <li>Statistische Wahrscheinlichkeiten beschreiben historische Haeufigkeiten,
            keine Vorhersagen.</li>
        <li>Maerkte werden von unvorhersehbaren Ereignissen (Krisen, Pandemien, politische
            Entscheidungen) beeinflusst, die historische Muster durchbrechen koennen.</li>
    </ul>

    <!-- ── 3. KI-Modelle ──────────────────────────────────────────── -->

    <h2>3. Kuenstliche Intelligenz &amp; Modell-Limitierungen</h2>
    <p>
        SeasonAlpha setzt verschiedene KI-Modelle und maschinelle Lernverfahren ein
        (u.a. Isolation Forest, DTW, Prophet, Chronos, NeuralProphet). Fuer diese gilt:
    </p>
    <ul>
        <li><strong>KI-Modelle koennen fehlerhafte oder irrefuehrende Ergebnisse liefern
            (sog. &quot;Halluzinationen&quot;).</strong></li>
        <li>Modellprognosen basieren auf mathematischen Berechnungen, nicht auf Marktverstaendnis.</li>
        <li>Die Genauigkeit von KI-Vorhersagen ist prinzipiell begrenzt und kann nicht
            garantiert werden.</li>
        <li>KI-generierte Texte und Zusammenfassungen koennen inhaltliche Fehler enthalten.</li>
        <li>Kein KI-Modell kann Marktbewegungen zuverlaessig vorhersagen.</li>
    </ul>

    <!-- ── 4. Datenquellen ────────────────────────────────────────── -->

    <h2>4. Datenquellen &amp; Genauigkeit</h2>
    <p>
        Die auf SeasonAlpha verwendeten Marktdaten stammen aus oeffentlich zugaenglichen
        Quellen (u.a. Yahoo Finance, Stooq). Wir bemuehen uns um Genauigkeit, koennen aber
        keine Gewaehr fuer die Vollstaendigkeit, Aktualitaet oder Richtigkeit der Daten
        uebernehmen.
    </p>
    <ul>
        <li>Datenluecken, Adjustierungsfehler oder verzoegerte Kurse sind moeglich.</li>
        <li>Split- und Dividenden-Adjustierungen erfolgen automatisiert und koennen
            in Einzelfaellen fehlerhaft sein.</li>
        <li>Echtzeit-Daten werden nicht angeboten — alle Daten sind zeitversetzt.</li>
    </ul>

    <!-- ── 5. Haftungsbeschraenkung ───────────────────────────────── -->

    <h2>5. Haftungsbeschraenkung</h2>
    <p>
        SeasonAlpha haftet nicht fuer Verluste oder Schaeden, die aus der Nutzung der
        Plattform, ihrer Analysen oder Prognosen entstehen. Dies umfasst insbesondere:
    </p>
    <ul>
        <li>Finanzielle Verluste durch Anlageentscheidungen, die auf Informationen
            dieser Plattform basieren.</li>
        <li>Schaeden durch technische Stoerungen, Datenfehler oder Serverausfaelle.</li>
        <li>Indirekte Schaeden, entgangene Gewinne oder Folgeschaeden jeglicher Art.</li>
    </ul>

    <!-- ── 6. Interessenkonflikte ─────────────────────────────────── -->

    <h2>6. Interessenkonflikte</h2>
    <p>
        Die Betreiber von SeasonAlpha koennen selbst in Finanzinstrumente investiert
        sein, die auf der Plattform analysiert werden. Dies kann zu Interessenkonflikten
        fuehren. Analysen und Bewertungen werden unabhaengig von persoenlichen Positionen
        erstellt.
    </p>

    <!-- ── 7. Anwendbares Recht ───────────────────────────────────── -->

    <h2>7. Anwendbares Recht</h2>
    <p>
        Es gilt das Recht der Bundesrepublik Deutschland. Gerichtsstand ist, soweit
        gesetzlich zulaessig, der Sitz des Betreibers.
    </p>

    <div class="footer">
        &copy; 2026 SeasonAlpha &middot;
        <a href="https://seasonalpha.ai/rechtliches">Impressum &amp; Datenschutz</a>
    </div>

</div>
</body>
</html>"""

    path = os.path.join(output_ordner, "disclaimer.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  [OK] disclaimer.html")


# ── Hauptfunktion ────────────────────────────────────────────────────────────

def build_seo_pages():
    """
    Generiert SEO-Assets: Sitemap, robots.txt, Disclaimer.

    HINWEIS: Die 94 programmatischen /analyse/{slug}.html Landingpages wurden
    am 2026-04-18 endgueltig entfernt (Thin-Content-Experiment beerdigt).
    Nginx liefert fuer /analyse/* ein 410 Gone aus (siehe deploy/nginx.conf).
    Dieser Build-Schritt loescht nun existierende /analyse/*.html-Dateien
    aus seo/output/ statt sie neu zu erzeugen.
    """

    output_ordner = os.path.join(_skript_ordner, "output")
    os.makedirs(output_ordner, exist_ok=True)

    # Titel-Daten weiterhin laden (wird fuer sitemap-Erzeugung + Slug-Liste gebraucht)
    titel_daten = build_titel_daten()

    print(f"\n{'='*60}")
    print(f"  SeasonAlpha — Programmatic SEO Builder")
    print(f"  {len(titel_daten)} Ticker (Sitemap/Robots), keine Landingpages mehr")
    print(f"{'='*60}\n")

    # ── 1. Cleanup: alte /analyse/{slug}.html Files loeschen ─────────────
    # Diese wurden bis 2026-04-18 automatisch erzeugt. Jetzt unerwuenscht.
    # Zu loeschen sind exakt die HTML-Files mit Slugs aus titel_daten.
    # Alles andere (disclaimer.html, google<hash>.html) bleibt.
    slugs_to_delete = {f'{t["slug"]}.html' for t in titel_daten}
    removed = 0
    for fname in slugs_to_delete:
        full = os.path.join(output_ordner, fname)
        if os.path.exists(full):
            try:
                os.remove(full)
                removed += 1
            except OSError as e:
                print(f"  [WARN] konnte {fname} nicht loeschen: {e}")
    if removed:
        print(f"  [CLEANUP] {removed} alte /analyse/*.html Files aus output/ entfernt")
    else:
        print(f"  [CLEANUP] keine alten /analyse/*.html Files gefunden")

    # ── 2. Sitemap + robots.txt + Disclaimer ─────────────────────────────
    # titel_daten wird an build_sitemap uebergeben, landet aber nicht mehr
    # in der Sitemap (ENABLE_PROGRAMMATIC_IN_SITEMAP = False).

    print()
    build_sitemap(titel_daten, output_ordner)
    build_robots_txt(output_ordner)
    build_llms_txt(output_ordner)
    build_disclaimer(output_ordner)

    print(f"\n{'='*60}")
    print(f"  Fertig! sitemap.xml + robots.txt + llms.txt + disclaimer.html")
    print(f"  Ausgabe: {output_ordner}")
    print(f"{'='*60}\n")


# ── Ausfuehren ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_seo_pages()
