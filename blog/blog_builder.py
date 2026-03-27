"""
blog_builder.py — SeasonAlpha Blog Engine
==========================================
Generiert statische HTML-Blog-Posts aus Markdown-Dateien.
Unterstuetzt Chart-Einbettung, Social-Media-Generierung und
KI-gestuetzte Content-Erstellung.

Verwendung:
  python blog/blog_builder.py --build                    # Alle Posts bauen
  python blog/blog_builder.py --generate "Titel" --ticker ^GSPC --category marktausblick
"""

import os
import sys
import re
import argparse
import yaml
from datetime import datetime, date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# ── Projekt-Root ──────────────────────────────────────────
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


# ── Konfiguration ────────────────────────────────────────
BASE_URL = "https://seasonalpha.ai"
POSTS_DIR = _script_dir / "posts"
TEMPLATES_DIR = _script_dir / "templates"
OUTPUT_DIR = _script_dir / "output"
PROMPTS_DIR = _script_dir / "prompts"

CATEGORY_LABELS = {
    "education": "Education",
    "marktausblick": "Marktausblick",
    "tutorials": "Tutorials",
}

MONTHS_DE = ["", "Januar", "Februar", "Maerz", "April", "Mai", "Juni",
             "Juli", "August", "September", "Oktober", "November", "Dezember"]


# ── Markdown Parser ──────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parsed YAML-Frontmatter und Markdown-Content."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    content = parts[2].strip()
    return meta, content


def markdown_to_html(md_text: str, post_slug: str = "") -> str:
    """Einfacher Markdown ->HTML Converter (kein externes Package noetig)."""
    lines = md_text.split("\n")
    html_parts = []
    in_list = False
    in_ol = False
    in_blockquote = False

    for line in lines:
        stripped = line.strip()

        # Leere Zeile
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if in_blockquote:
                html_parts.append("</blockquote>")
                in_blockquote = False
            continue

        # Headings
        if stripped.startswith("### "):
            html_parts.append(f"<h3>{_inline(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            html_parts.append(f"<h2>{_inline(stripped[3:])}</h2>")
            continue

        # Blockquote
        if stripped.startswith("> "):
            if not in_blockquote:
                html_parts.append("<blockquote>")
                in_blockquote = True
            html_parts.append(f"<p>{_inline(stripped[2:])}</p>")
            continue

        # Unordered list
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{_inline(stripped[2:])}</li>")
            continue

        # Ordered list
        ol_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ol_match:
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            html_parts.append(f"<li>{_inline(ol_match.group(1))}</li>")
            continue

        # Chart tags
        chart_match = re.match(r"\{\{chart:(\w+):([^:]+):(\d+)\}\}", stripped)
        if chart_match:
            chart_type, ticker, years = chart_match.groups()
            if post_slug:
                html_parts.append(_build_chart_image(chart_type, ticker, int(years), post_slug))
            else:
                html_parts.append(_build_chart_placeholder(chart_type, ticker, int(years)))
            continue

        # Regular paragraph
        html_parts.append(f"<p>{_inline(stripped)}</p>")

    if in_list:
        html_parts.append("</ul>")
    if in_ol:
        html_parts.append("</ol>")
    if in_blockquote:
        html_parts.append("</blockquote>")

    return "\n".join(html_parts)


def _inline(text: str) -> str:
    """Inline-Markdown: **bold**, *italic*, `code`, [link](url)."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


# ── Chart-Generierung ─────────────────────────────────────

# Cache fuer heruntergeladene Ticker-Daten (vermeidet Mehrfach-Downloads)
_ticker_cache: dict = {}

# Konstanten fuer Charts (aus pages/02_Jahreszyklus.py)
_MONTH_STARTS = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
_MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "Mai", "Jun",
                 "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
_MONTH_DOY = {
    1: (1, 31), 2: (32, 59), 3: (60, 90), 4: (91, 120),
    5: (121, 151), 6: (152, 181), 7: (182, 212), 8: (213, 243),
    9: (244, 273), 10: (274, 304), 11: (305, 334), 12: (335, 365),
}
_MONTH_NAMES_DE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                   "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]


def _get_ticker_data(ticker: str) -> pd.DataFrame | None:
    """Laedt Ticker-Daten mit Cache."""
    if ticker in _ticker_cache:
        return _ticker_cache[ticker]
    try:
        from shared.yahoo_downloader import download_data, preprocess
        df = download_data(ticker)
        if df is not None and len(df) > 0:
            df = preprocess(df)
            _ticker_cache[ticker] = df
            return df
    except Exception as e:
        print(f"    [WARN] Daten fuer {ticker} nicht verfuegbar: {e}")
    return None


def _build_seasonal_yearly_chart(ticker: str, years: int) -> "go.Figure | None":
    """Baut einen saisonalen Jahresverlauf-Chart."""
    import plotly.graph_objects as go
    from shared.calculations import build_year_data, calculate_seasonal_average
    from shared.charts import apply_se_theme
    from shared.constants import SE_COLORS

    df = _get_ticker_data(ticker)
    if df is None:
        return None

    current_year = date.today().year
    all_years = sorted(df["year"].unique())
    selected = [y for y in all_years if y >= current_year - years]
    if not selected:
        return None

    year_data = build_year_data(df, selected)
    if not year_data:
        return None
    avg, std = calculate_seasonal_average(year_data)

    fig = go.Figure()
    x_days = list(range(1, 366))

    # Konfidenzband (±1 Sigma)
    if std:
        upper = [avg[i] + std[i] for i in range(365)]
        lower = [avg[i] - std[i] for i in range(365)]
        fig.add_trace(go.Scatter(
            x=x_days, y=upper, mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=x_days, y=lower, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(77,159,255,0.12)",
            name="±1 Sigma", hoverinfo="skip",
        ))

    # Saisonaler Durchschnitt
    fig.add_trace(go.Scatter(
        x=x_days, y=avg, mode="lines",
        line=dict(color=SE_COLORS["accent_blue"], width=3),
        name=f"Saisonaler Ø ({len(year_data)} Jahre)",
    ))

    fig.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.2)", line_width=1)

    fig = apply_se_theme(
        fig,
        title=f"{ticker} — Saisonaler Jahresverlauf ({len(year_data)} Jahre)",
        height=520, show_watermark=True,
    )
    fig.update_xaxes(
        tickmode="array", tickvals=_MONTH_STARTS, ticktext=_MONTH_LABELS,
        range=[1, 365],
    )
    fig.update_yaxes(title="Normalisiert (Start = 100)")
    return fig


def _build_monthly_heatmap_chart(ticker: str, years: int) -> "go.Figure | None":
    """Baut eine Monats-Rendite Heatmap."""
    import plotly.graph_objects as go
    from shared.calculations import build_year_data
    from shared.charts import apply_se_heatmap_theme
    from shared.constants import SE_COLORS, SE_HEATMAP_COLORSCALE, SE_HEATMAP_TEXT_COLOR

    df = _get_ticker_data(ticker)
    if df is None:
        return None

    current_year = date.today().year
    all_years = sorted(df["year"].unique(), reverse=True)
    selected = [y for y in all_years if y >= current_year - years][:years]
    if not selected:
        return None

    year_data = build_year_data(df, selected)
    if not year_data:
        return None

    sorted_years = sorted(year_data.keys(), reverse=True)[:10]
    z_data = []
    y_labels = []
    for year in sorted_years:
        row = []
        for m in range(1, 13):
            s, e = _MONTH_DOY[m]
            yd = year_data[year]
            start_val = yd["full_365"][s - 1]
            end_val = yd["full_365"][min(e - 1, 364)]
            ret = (end_val - start_val) / start_val * 100 if start_val != 0 else 0
            row.append(round(ret, 2))
        z_data.append(row)
        y_labels.append(str(year))

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=_MONTH_NAMES_DE,
        y=y_labels,
        colorscale=SE_HEATMAP_COLORSCALE,
        zmid=0,
        text=[[f"{v:+.1f}%" for v in row] for row in z_data],
        texttemplate="%{text}",
        textfont=dict(size=11, color=SE_HEATMAP_TEXT_COLOR),
        hovertemplate="<b>%{y} — %{x}</b><br>Rendite: %{z:+.2f}%<extra></extra>",
        colorbar=dict(
            title=dict(text="Rendite %", font=dict(color=SE_COLORS["text_muted"], size=11)),
            tickfont=dict(color=SE_COLORS["text_muted"], size=10),
            ticksuffix="%",
        ),
    ))

    fig = apply_se_heatmap_theme(
        fig,
        title=f"{ticker} — Monats-Heatmap ({len(sorted_years)} Jahre)",
        height=max(300, len(sorted_years) * 28 + 100),
    )
    fig.update_yaxes(autorange="reversed", dtick=1)
    return fig


_CHART_BUILDERS = {
    "seasonal_yearly": _build_seasonal_yearly_chart,
    "monthly_heatmap": _build_monthly_heatmap_chart,
}


def _build_chart_image(chart_type: str, ticker: str, years: int,
                       post_slug: str) -> str:
    """Generiert interaktiven Plotly-Chart als HTML-Div. Fallback auf Platzhalter."""
    builder = _CHART_BUILDERS.get(chart_type)
    if not builder:
        return _build_chart_placeholder(chart_type, ticker, years)

    try:
        fig = builder(ticker, years)
        if fig is None:
            return _build_chart_placeholder(chart_type, ticker, years)

        import plotly.io as pio
        # Interaktives HTML-Div (mit Plotly.js CDN, ohne full_html)
        chart_html = pio.to_html(
            fig, include_plotlyjs="cdn", full_html=False,
            config={"displayModeBar": False, "scrollZoom": False},
        )
        return f'<div class="chart-container">{chart_html}</div>'
    except Exception as e:
        print(f"    [WARN] Chart {chart_type}/{ticker} fehlgeschlagen: {e}")
        return _build_chart_placeholder(chart_type, ticker, years)


def _build_chart_placeholder(chart_type: str, ticker: str, years: int) -> str:
    """Fallback-Platzhalter wenn Chart-Generierung fehlschlaegt."""
    labels = {
        "seasonal_yearly": "Saisonaler Jahresverlauf",
        "monthly_heatmap": "Monats-Rendite Heatmap",
        "weekday_bars": "Wochentag-Performance",
        "tom_effect": "Turn-of-Month Effekt",
    }
    label = labels.get(chart_type, chart_type)
    return (
        f'<div class="chart-container" data-chart-type="{chart_type}" '
        f'data-ticker="{ticker}" data-years="{years}">'
        f'<div style="padding:3rem 2rem; text-align:center;">'
        f'<div style="font-size:2.5rem; margin-bottom:0.75rem;">📊</div>'
        f'<div style="color:#5a6e85; font-size:0.9rem;">'
        f'{label} — {ticker} ({years} Jahre)</div>'
        f'<div style="color:#3a4a5e; font-size:0.8rem; margin-top:0.5rem;">'
        f'Chart wird beim naechsten Build generiert</div>'
        f'</div></div>'
    )


# ── Post laden ───────────────────────────────────────────

def load_posts() -> list[dict]:
    """Laedt alle Markdown-Posts aus blog/posts/."""
    posts = []
    if not POSTS_DIR.exists():
        return posts

    for md_file in sorted(POSTS_DIR.glob("*.md")):
        with open(md_file, "r", encoding="utf-8") as f:
            raw = f.read()

        meta, content = parse_frontmatter(raw)
        if not meta.get("title") or not meta.get("slug"):
            print(f"  [SKIP] {md_file.name} — kein title/slug")
            continue

        status = meta.get("status", "draft")

        # Draft: nicht generieren
        if status == "draft":
            print(f"  [DRAFT] {md_file.name}")
            continue

        # Scheduled: nur wenn publish_date <= heute
        if status == "scheduled":
            pub_date = meta.get("publish_date")
            if pub_date:
                if isinstance(pub_date, str):
                    pub_date = datetime.strptime(pub_date, "%Y-%m-%d").date()
                if pub_date > date.today():
                    print(f"  [SCHEDULED] {md_file.name} ->{pub_date}")
                    continue

        # Content zu HTML (mit Chart-Generierung)
        html_content = markdown_to_html(content, post_slug=meta.get("slug", ""))

        # Reading time
        word_count = len(content.split())
        reading_time = max(1, round(word_count / 200))

        # Date formatting
        post_date = meta.get("date", date.today())
        if isinstance(post_date, str):
            post_date = datetime.strptime(post_date, "%Y-%m-%d").date()

        date_formatted = f"{post_date.day}. {MONTHS_DE[post_date.month]} {post_date.year}"

        category = meta.get("category", "education")
        tags = meta.get("tags", [])

        post = {
            "title": meta["title"],
            "slug": meta["slug"],
            "date": str(post_date),
            "date_obj": post_date,
            "date_formatted": date_formatted,
            "category": category,
            "category_label": CATEGORY_LABELS.get(category, category),
            "tags": tags,
            "description": meta.get("description", ""),
            "ticker": meta.get("ticker", ""),
            "status": status,
            "content": html_content,
            "reading_time": reading_time,
            "file": md_file.name,
        }
        posts.append(post)

    # Sortiert nach Datum (neueste zuerst)
    posts.sort(key=lambda p: p["date_obj"], reverse=True)
    return posts


# ── HTML generieren ──────────────────────────────────────

def build_all():
    """Generiert alle Blog-HTMLs."""
    print("=" * 60)
    print("  SeasonAlpha — Blog Builder")
    print("=" * 60)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    post_tpl = env.get_template("blog_post.html")
    index_tpl = env.get_template("blog_index.html")

    # Output-Verzeichnis
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Posts laden
    posts = load_posts()
    print(f"\n  {len(posts)} Posts zum Generieren\n")

    # Einzelne Posts
    for i, post in enumerate(posts):
        slug = post["slug"]
        post_dir = OUTPUT_DIR / slug
        post_dir.mkdir(parents=True, exist_ok=True)

        # Social-Verzeichnis
        social_dir = post_dir / "social"
        social_dir.mkdir(exist_ok=True)
        youtube_dir = post_dir / "youtube"
        youtube_dir.mkdir(exist_ok=True)

        # Related Posts (bis zu 3, gleiche Kategorie bevorzugt)
        related = [p for p in posts if p["slug"] != slug]
        same_cat = [p for p in related if p["category"] == post["category"]]
        other = [p for p in related if p["category"] != post["category"]]
        related_posts = (same_cat + other)[:3]

        # HTML rendern
        html = post_tpl.render(
            **post,
            related_posts=related_posts,
        )
        out_file = post_dir / "index.html"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html)

        # Social-Media Texte generieren
        _generate_social(post, social_dir)

        # YouTube-Dateien generieren
        _generate_youtube(post, youtube_dir)

        print(f"  [{i+1:3d}/{len(posts)}] {post['title'][:50]:50s} ->{slug}/")

    # Index-Seiten
    _build_index(index_tpl, posts, "all", OUTPUT_DIR / "index.html")
    for cat_slug, cat_label in CATEGORY_LABELS.items():
        cat_dir = OUTPUT_DIR / cat_slug
        cat_dir.mkdir(exist_ok=True)
        cat_posts = [p for p in posts if p["category"] == cat_slug]
        _build_index(index_tpl, cat_posts, cat_slug, cat_dir / "index.html",
                     hero_title=cat_label,
                     hero_subtitle=_category_subtitle(cat_slug))

    # Sitemap erweitern
    _build_blog_sitemap(posts)

    print(f"\n  Fertig! {len(posts)} Posts + Index + Kategorie-Seiten + Sitemap")
    print("=" * 60)


def _build_index(tpl, posts, active_cat, out_path, hero_title=None, hero_subtitle=None):
    """Rendert eine Index-Seite (Haupt oder Kategorie)."""
    html = tpl.render(
        posts=posts,
        active_category=active_cat,
        hero_title=hero_title or "SeasonAlpha Blog",
        hero_subtitle=hero_subtitle or "Datenbasierte saisonale Analysen, Trading-Strategien und Tutorials.",
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)


def _category_subtitle(cat: str) -> str:
    subs = {
        "education": "Grundlagen, Theorie und Wissen rund um saisonale Boersenanalyse.",
        "marktausblick": "Aktuelle saisonale Analysen und datenbasierte Marktprognosen.",
        "tutorials": "Schritt-fuer-Schritt Anleitungen fuer SeasonAlpha Features.",
    }
    return subs.get(cat, "")


# ── Social-Media Generierung ────────────────────────────

def _generate_social(post: dict, social_dir: Path):
    """Generiert Social-Media Texte (ohne Claude API — Template-basiert)."""

    title = post["title"]
    desc = post["description"]
    slug = post["slug"]
    ticker = post.get("ticker", "")
    url = f"{BASE_URL}/blog/{slug}/"

    # Twitter: 3 Varianten
    tweets = [
        f"📊 {title}\n\n{desc}\n\n{url}\n\n#Saisonalitaet #Trading #Boerse",
        f"🔍 Neue Analyse: {title}\n\nDatenbasierte Insights auf SeasonAlpha 👇\n{url}",
    ]
    if ticker:
        tweets.append(
            f"📈 {ticker} Saisonalitaet: {title}\n\n"
            f"Was sagen 20+ Jahre Daten?\n{url}\n\n#SeasonAlpha #{ticker.replace('^','')}"
        )
    else:
        tweets.append(
            f"💡 {title}\n\nMehr auf dem SeasonAlpha Blog:\n{url}"
        )

    with open(social_dir / "twitter_posts.txt", "w", encoding="utf-8") as f:
        for i, tweet in enumerate(tweets):
            f.write(f"=== Variante {i+1} ({len(tweet)} Zeichen) ===\n\n")
            f.write(tweet)
            f.write("\n\n")

    # LinkedIn
    linkedin = (
        f"📊 {title}\n\n"
        f"{desc}\n\n"
        f"In unserer neuesten Analyse auf dem SeasonAlpha Blog schauen wir uns "
        f"die historischen Daten genauer an"
        f"{f' — mit Fokus auf {ticker}' if ticker else ''}.\n\n"
        f"Die wichtigsten Erkenntnisse:\n"
        f"- Datenbasierte saisonale Muster\n"
        f"- Historische Win-Rates und Durchschnittsrenditen\n"
        f"- Interaktive Charts zur eigenen Analyse\n\n"
        f"Zum vollstaendigen Beitrag: {url}\n\n"
        f"#Saisonalitaet #Trading #Boersenanalyse #SeasonAlpha #Finanzmarkt"
    )

    with open(social_dir / "linkedin_post.txt", "w", encoding="utf-8") as f:
        f.write(linkedin)


# ── YouTube Generierung ─────────────────────────────────

def _generate_youtube(post: dict, youtube_dir: Path):
    """Generiert YouTube-Dateien (Template-basiert)."""

    title = post["title"]
    desc = post["description"]
    slug = post["slug"]
    ticker = post.get("ticker", "")
    url = f"{BASE_URL}/blog/{slug}/"
    category = post.get("category_label", "")

    # Video-Script
    script = (
        f"=== VIDEO SCRIPT: {title} ===\n"
        f"Kategorie: {category} | Geschaetzte Laenge: 5-8 Minuten\n\n"
        f"[INTRO — 15 Sekunden]\n"
        f"Hook: \"{title} — was sagen die Daten wirklich?\"\n"
        f"\"In diesem Video schauen wir uns die historischen Zahlen an.\"\n\n"
        f"[HAUPTTEIL — 3-5 Minuten]\n"
        f"{desc}\n\n"
    )
    if ticker:
        script += (
            f"Chart 1: Saisonaler Jahresverlauf von {ticker}\n"
            f"→ SeasonAlpha App oeffnen ->Jahreszyklus ->{ticker} auswaehlen\n"
            f"→ Zeige den normalisierten Verlauf ueber 20 Jahre\n\n"
            f"Chart 2: Monats-Heatmap von {ticker}\n"
            f"→ Monatszyklus Page ->10-Jahres Heatmap zeigen\n"
            f"→ Erklaere die staerksten und schwaechsten Monate\n\n"
        )
    script += (
        f"[FAZIT — 1-2 Minuten]\n"
        f"Zusammenfassung der wichtigsten Erkenntnisse.\n"
        f"\"Analysiere es selbst auf seasonalpha.ai — Link in der Beschreibung.\"\n\n"
        f"[OUTRO — 15 Sekunden]\n"
        f"\"Wenn dir das Video gefallen hat, lass ein Like da und abonniere den Kanal.\"\n"
        f"\"Schreib in die Kommentare, welchen Ticker wir als naechstes analysieren sollen.\"\n"
    )
    with open(youtube_dir / "video_script.txt", "w", encoding="utf-8") as f:
        f.write(script)

    # Shorts-Script (60 Sek)
    short = (
        f"=== YOUTUBE SHORT (60 Sek): {title} ===\n\n"
        f"[0-5 Sek] Hook: \"Wusstest du das ueber"
        f"{f' {ticker}' if ticker else ' die Boerse'}?\"\n\n"
        f"[5-45 Sek] {desc}\n"
        f"→ Zeige den Chart in der SeasonAlpha App\n"
        f"→ Nenne die wichtigste Zahl (Win-Rate, Avg Return)\n\n"
        f"[45-60 Sek] CTA: \"Mehr Analysen auf seasonalpha.ai\"\n"
    )
    with open(youtube_dir / "video_script_short.txt", "w", encoding="utf-8") as f:
        f.write(short)

    # YouTube-Beschreibung
    yt_desc = (
        f"{title}\n\n"
        f"{desc}\n\n"
        f"📊 Interaktive Analyse: {BASE_URL}\n"
        f"📝 Blog-Beitrag: {url}\n\n"
        f"--- Timestamps ---\n"
        f"0:00 Intro\n"
        f"0:15 Analyse\n"
        f"4:00 Fazit\n\n"
        f"--- Links ---\n"
        f"SeasonAlpha App: {BASE_URL}\n"
        f"Blog: {BASE_URL}/blog/\n\n"
        f"#Saisonalitaet #Trading #Boerse"
        f"{f' #{ticker.replace(chr(94),"")}' if ticker else ''}"
        f" #SeasonAlpha\n\n"
        f"--- Disclaimer ---\n"
        f"Keine Anlageberatung. Historische Daten garantieren keine zukuenftigen Ergebnisse."
    )
    with open(youtube_dir / "description.txt", "w", encoding="utf-8") as f:
        f.write(yt_desc)

    # Tags
    tags = [
        "Saisonalitaet", "Boerse", "Trading", "Aktien", "ETF",
        "Saisonale Analyse", "SeasonAlpha", "Sell in May",
        "Technische Analyse", "Datenanalyse",
    ]
    if ticker:
        tags.insert(0, ticker.replace("^", ""))
    with open(youtube_dir / "tags.txt", "w", encoding="utf-8") as f:
        f.write(", ".join(tags))


# ── Sitemap ──────────────────────────────────────────────

def _build_blog_sitemap(posts: list[dict]):
    """Generiert Blog-Sitemap-Eintraege."""
    sitemap_path = OUTPUT_DIR / "sitemap_blog.xml"
    today = date.today().isoformat()

    urls = [
        f'  <url><loc>{BASE_URL}/blog/</loc><lastmod>{today}</lastmod>'
        f'<changefreq>weekly</changefreq><priority>0.8</priority></url>',
    ]
    for cat_slug in CATEGORY_LABELS:
        urls.append(
            f'  <url><loc>{BASE_URL}/blog/{cat_slug}/</loc><lastmod>{today}</lastmod>'
            f'<changefreq>weekly</changefreq><priority>0.7</priority></url>'
        )
    for post in posts:
        urls.append(
            f'  <url><loc>{BASE_URL}/blog/{post["slug"]}/</loc>'
            f'<lastmod>{post["date"]}</lastmod>'
            f'<changefreq>monthly</changefreq><priority>0.6</priority></url>'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n"
        '</urlset>\n'
    )
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"  [OK] sitemap_blog.xml ({len(urls)} URLs)")


# ── KI-Content-Generierung (--generate) ─────────────────

def generate_post(title: str, ticker: str = "", category: str = "marktausblick"):
    """Generiert einen Blog-Post-Entwurf als Markdown."""
    today = date.today()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower().strip()).strip("-")
    filename = f"{today.isoformat()}_{slug}.md"
    filepath = POSTS_DIR / filename

    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    # Chart-Tags basierend auf Kategorie
    charts = ""
    if ticker:
        charts = (
            f"\n{{{{chart:seasonal_yearly:{ticker}:20}}}}\n\n"
            f"Der saisonale Verlauf zeigt...\n\n"
            f"{{{{chart:monthly_heatmap:{ticker}:10}}}}\n\n"
            f"Die Monats-Heatmap verdeutlicht...\n"
        )

    md = (
        f"---\n"
        f"title: \"{title}\"\n"
        f"slug: {slug}\n"
        f"date: {today.isoformat()}\n"
        f"category: {category}\n"
        f"tags: [saisonalitaet]\n"
        f"description: \"TODO: Meta-Description (max 160 Zeichen)\"\n"
        f"ticker: {ticker}\n"
        f"status: draft\n"
        f"---\n\n"
        f"## Einleitung\n\n"
        f"TODO: Einleitungstext\n"
        f"{charts}\n"
        f"## Analyse\n\n"
        f"TODO: Hauptteil\n\n"
        f"## Fazit\n\n"
        f"TODO: Zusammenfassung und Handlungsempfehlung\n"
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"  [OK] Entwurf erstellt: {filepath}")
    print(f"       Status: draft (auf 'published' setzen zum Veroeffentlichen)")


# ── CLI ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SeasonAlpha Blog Builder")
    parser.add_argument("--build", action="store_true", help="Alle Posts bauen")
    parser.add_argument("--generate", type=str, help="Post-Entwurf generieren (Titel)")
    parser.add_argument("--ticker", type=str, default="", help="Ticker fuer --generate")
    parser.add_argument("--category", type=str, default="marktausblick",
                        choices=list(CATEGORY_LABELS.keys()),
                        help="Kategorie fuer --generate")

    args = parser.parse_args()

    if args.generate:
        generate_post(args.generate, args.ticker, args.category)
    elif args.build:
        build_all()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
