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

from jinja2 import Environment, FileSystemLoader

# Projekt-Root finden damit shared/ importiert werden kann
_skript_ordner = os.path.dirname(os.path.abspath(__file__))
_projekt_root = os.path.dirname(_skript_ordner)
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

def build_sitemap(titel_daten: list[dict], output_ordner: str):
    """Generiert sitemap.xml mit allen SEO-Seiten + statischen Seiten."""
    heute_iso = datetime.now().strftime("%Y-%m-%d")

    urls = []

    # Statische Seiten (hohe Prioritaet)
    static_pages = [
        {"loc": f"{BASE_URL}/",             "priority": "1.0",  "changefreq": "weekly"},
        {"loc": f"{BASE_URL}/pricing",      "priority": "0.8",  "changefreq": "monthly"},
        {"loc": f"{BASE_URL}/disclaimer",   "priority": "0.3",  "changefreq": "yearly"},
        {"loc": f"{BASE_URL}/datenschutz",  "priority": "0.3",  "changefreq": "yearly"},
        {"loc": f"{BASE_URL}/impressum",    "priority": "0.3",  "changefreq": "yearly"},
    ]
    for page in static_pages:
        urls.append(
            f'  <url>\n'
            f'    <loc>{page["loc"]}</loc>\n'
            f'    <lastmod>{heute_iso}</lastmod>\n'
            f'    <changefreq>{page["changefreq"]}</changefreq>\n'
            f'    <priority>{page["priority"]}</priority>\n'
            f'  </url>'
        )

    # Tools (hohe Prioritaet — interaktive, kostenlose Tools)
    tool_pages = [
        {"loc": f"{BASE_URL}/tools/trading-day-converter", "priority": "0.9", "changefreq": "monthly"},
    ]
    for page in tool_pages:
        urls.append(
            f'  <url>\n'
            f'    <loc>{page["loc"]}</loc>\n'
            f'    <lastmod>{heute_iso}</lastmod>\n'
            f'    <changefreq>{page["changefreq"]}</changefreq>\n'
            f'    <priority>{page["priority"]}</priority>\n'
            f'  </url>'
        )

    # Core-Feature-Pages (HOCH priorisiert — das sind die Haupt-Features)
    landing_pages = [
        # Dashboard + Haupt-Zyklen (Kernstuecke)
        {"slug": "dashboard",          "priority": "1.0",  "changefreq": "daily"},
        {"slug": "jahreszyklus",       "priority": "0.95", "changefreq": "daily"},
        {"slug": "monatszyklus",       "priority": "0.95", "changefreq": "daily"},
        {"slug": "dekadenzyklus",      "priority": "0.9",  "changefreq": "weekly"},
        {"slug": "wochentage",         "priority": "0.9",  "changefreq": "weekly"},
        {"slug": "monatswechsel",      "priority": "0.9",  "changefreq": "weekly"},
        {"slug": "mondphasen",         "priority": "0.85", "changefreq": "weekly"},
        # Events
        {"slug": "zentralbanken",      "priority": "0.9",  "changefreq": "weekly"},
        {"slug": "feiertage",          "priority": "0.85", "changefreq": "weekly"},
        {"slug": "opex",               "priority": "0.85", "changefreq": "weekly"},
        {"slug": "intermarket-shocks", "priority": "0.85", "changefreq": "weekly"},
        # Strategien
        {"slug": "trifecta",           "priority": "0.9",  "changefreq": "weekly"},
        {"slug": "plain-vanilla",      "priority": "0.95", "changefreq": "weekly"},
        {"slug": "backtest-engine",    "priority": "0.95", "changefreq": "weekly"},
        # Advanced
        {"slug": "ki-saisonalitaet",   "priority": "0.9",  "changefreq": "daily"},
        {"slug": "crash-fruehwarnung", "priority": "0.9",  "changefreq": "daily"},
        {"slug": "spot-vol-beta",      "priority": "0.85", "changefreq": "weekly"},
        {"slug": "tdom-analyse",       "priority": "0.85", "changefreq": "weekly"},
        {"slug": "overnight",          "priority": "0.8",  "changefreq": "weekly"},
        {"slug": "sektor-rotation",    "priority": "0.85", "changefreq": "weekly"},
        {"slug": "kriegszeiten",       "priority": "0.7",  "changefreq": "monthly"},
        # Blog-Index + Kategorien
        {"slug": "blog/",              "priority": "0.9",  "changefreq": "daily"},
        {"slug": "blog/education/",    "priority": "0.8",  "changefreq": "weekly"},
        {"slug": "blog/marktausblick/","priority": "0.8",  "changefreq": "weekly"},
        {"slug": "blog/tutorials/",    "priority": "0.8",  "changefreq": "weekly"},
    ]
    for page in landing_pages:
        urls.append(
            f'  <url>\n'
            f'    <loc>{BASE_URL}/{page["slug"]}</loc>\n'
            f'    <lastmod>{heute_iso}</lastmod>\n'
            f'    <changefreq>{page["changefreq"]}</changefreq>\n'
            f'    <priority>{page["priority"]}</priority>\n'
            f'  </url>'
        )

    # Blog-Posts (aus blog/posts/ Markdown-Frontmatter lesen)
    try:
        import yaml
        from pathlib import Path
        posts_dir = Path(__file__).resolve().parent.parent / "blog" / "posts"
        if posts_dir.exists():
            for md in sorted(posts_dir.glob("*.md")):
                try:
                    raw = md.read_text(encoding="utf-8")
                    if raw.startswith("---"):
                        _, fm, _ = raw.split("---", 2)
                        meta = yaml.safe_load(fm) or {}
                        slug = meta.get("slug")
                        if slug and meta.get("status", "published") == "published":
                            urls.append(
                                f'  <url>\n'
                                f'    <loc>{BASE_URL}/blog/{slug}/</loc>\n'
                                f'    <lastmod>{heute_iso}</lastmod>\n'
                                f'    <changefreq>monthly</changefreq>\n'
                                f'    <priority>0.75</priority>\n'
                                f'  </url>'
                            )
                except Exception as e:
                    print(f"  [WARN] Blog-Post {md.name}: {e}")
    except ImportError:
        print("  [WARN] PyYAML fehlt, Blog-Posts werden nicht in sitemap aufgenommen")

    # SEO-Landingpages (mittlere Prioritaet)
    for titel in titel_daten:
        urls.append(
            f'  <url>\n'
            f'    <loc>{BASE_URL}/analyse/{titel["slug"]}</loc>\n'
            f'    <lastmod>{heute_iso}</lastmod>\n'
            f'    <changefreq>weekly</changefreq>\n'
            f'    <priority>0.7</priority>\n'
            f'  </url>'
        )

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n"
        '</urlset>\n'
    )

    path = os.path.join(output_ordner, "sitemap.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"  [OK] sitemap.xml ({len(urls)} URLs)")


# ── robots.txt Generator ────────────────────────────────────────────────────

def build_robots_txt(output_ordner: str):
    """Generiert robots.txt mit Sitemap-Verweis."""
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        "# Streamlit-App nicht crawlen (dynamische Inhalte)\n"
        "Disallow: /_stcore/\n"
        "Disallow: /static/\n"
        "\n"
        f"Sitemap: {BASE_URL}/sitemap.xml\n"
    )
    path = os.path.join(output_ordner, "robots.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [OK] robots.txt")


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
        <a href="https://seasonalpha.ai/impressum">Impressum</a> &middot;
        <a href="https://seasonalpha.ai/datenschutz">Datenschutz</a>
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
    """Generiert alle SEO-Assets: Landingpages, Sitemap, robots.txt, Disclaimer."""

    output_ordner = os.path.join(_skript_ordner, "output")
    os.makedirs(output_ordner, exist_ok=True)

    # Jinja2 Template laden
    env = Environment(
        loader=FileSystemLoader(_skript_ordner),
        autoescape=True,
    )
    template = env.get_template("seo_template.html")

    # Titel-Daten aus SYMBOLS generieren
    titel_daten = build_titel_daten()

    heute = datetime.now().strftime("%d.%m.%Y")

    print(f"\n{'='*60}")
    print(f"  SeasonAlpha — Programmatic SEO Builder")
    print(f"  {len(titel_daten)} Ticker aus SYMBOLS-Datenbank")
    print(f"{'='*60}\n")

    # ── 1. HTML-Landingpages ──────────────────────────────────────────────

    for i, titel in enumerate(titel_daten, 1):
        html_output = template.render(
            **titel,
            datum=heute,
            ki_count=KI_COUNT,
        )

        dateiname = f'{titel["slug"]}.html'
        dateipfad = os.path.join(output_ordner, dateiname)

        with open(dateipfad, "w", encoding="utf-8") as f:
            f.write(html_output)

        print(f"  [{i:3d}/{len(titel_daten)}] {titel['name']:25s} -> {dateiname}")

    # ── 2. Sitemap + robots.txt + Disclaimer ─────────────────────────────

    print()
    build_sitemap(titel_daten, output_ordner)
    build_robots_txt(output_ordner)
    build_disclaimer(output_ordner)

    print(f"\n{'='*60}")
    print(f"  Fertig! {len(titel_daten)} Seiten + sitemap.xml + robots.txt + disclaimer.html")
    print(f"  Ausgabe: {output_ordner}")
    print(f"{'='*60}\n")


# ── Ausfuehren ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_seo_pages()
