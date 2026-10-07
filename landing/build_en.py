# -*- coding: utf-8 -*-
"""
build_en.py - Pre-Rendering der EN-Landing-Pages (SeasonAlpha)
==============================================================

Erzeugt aus den deutschen Quell-Pages statische *englische* HTML-Dateien in
landing/en/. Damit serviert nginx /en/<slug> als fertiges Englisch:
kein Client-FOUC, korrekter SEO-Head fuer Crawler OHNE JS.

Was das Script pro Page macht:
  1. <html lang="de"> -> lang="en"
  2. SEO-Head neu generieren: EN-Title/Description, canonical=/en/...,
     reziprokes hreflang (de/en/x-default), og:locale=en_US, og:url=/en/...,
     JSON-LD (WebPage + BreadcrumbList) mit /en/-URLs + "inLanguage":"en"
  3. Body-Texte: jedes data-i18n / -html / -placeholder / -title / -aria
     wird durch den EN-Wert aus en.json ersetzt (positions-basiertes
     Splicing via stdlib html.parser -> HTML bleibt sonst unveraendert)
  4. interne Links /x -> /en/x (gleiche Skip-Regeln wie SA.i18n._applyNavLinks)

Quellen (Single Source, kein Duplikat):
  - EN-Title/Description: _EN_PAGE_META in landing/js/i18n.js
  - Body-Strings:         landing/i18n/en.json
  - Page-Typ/Kategorie:   PAGE_META aus scripts/upgrade_page_meta.py

Nur Stdlib (re/json/html/html.parser) + die o.g. Projektdateien.

Usage:
  py landing/build_en.py                      # dry-run, alle Pages
  py landing/build_en.py --page dashboard     # nur eine Page (dry-run)
  py landing/build_en.py --page dashboard --write
  py landing/build_en.py --write              # alle Pages schreiben

Danach verifizieren:  py landing/verify_en.py
"""
from __future__ import annotations
import re, sys, json, argparse
from html import unescape as html_unescape
from pathlib import Path
from html.parser import HTMLParser

LANDING = Path(__file__).resolve().parent
REPO    = LANDING.parent
PAGES   = LANDING / "pages"
I18N    = LANDING / "i18n"
I18N_JS = LANDING / "js" / "i18n.js"
OUT     = LANDING / "en"

BASE_URL  = "https://seasonalpha.ai"
OG_IMAGE  = f"{BASE_URL}/landing/assets/images/og-image.png"
TWITTER   = "@SeasonAlph4882"
MARKER    = "<!-- SA_META_V5_EN -->"
STANDARD_ROBOTS = "index, follow, max-snippet:-1, max-image-preview:large"

# Page-Registry (Typ/Kategorie) aus dem DE-Generator wiederverwenden
try:
    sys.path.insert(0, str(REPO / "scripts"))
    from upgrade_page_meta import PAGE_META as _DE_PAGE_META  # noqa
except Exception:
    _DE_PAGE_META = {}

# Link-Rewrite: diese Prefixe NICHT auf /en/ umschreiben
SKIP_PREFIXES = ("/en/", "/blog/", "/tools/", "/rechtliches", "/disclaimer",
                 "/app/", "/umami/", "http", "mailto:", "#", "javascript:",
                 "/kalender", "/profile", "/watchlist", "/pricing", "/unsubscribe",
                 "/dealer-positioning", "/flows")
HREF_RE = re.compile(r'href="(/[^"]*)"')

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}

# HTML-Elemente mit optionalem End-Tag: ein neues <tag> schliesst implizit
# offene Peers (sonst bleiben z.B. <li>/<td> ohne </li>/</td> "offen").
IMPLICIT_CLOSE = {
    "li": {"li"},
    "option": {"option"}, "optgroup": {"option", "optgroup"},
    "td": {"td", "th"}, "th": {"td", "th"}, "tr": {"td", "th", "tr"},
    "thead": {"td", "th", "tr"}, "tbody": {"td", "th", "tr"}, "tfoot": {"td", "th", "tr"},
    "dt": {"dt", "dd"}, "dd": {"dt", "dd"}, "p": {"p"},
}


# ---------------------------------------------------------------- helpers
def esc_attr(s: str) -> str:
    return (s.replace("&", "&amp;").replace('"', "&quot;")
             .replace("<", "&lt;").replace(">", "&gt;"))

def esc_text(s: str) -> str:
    s = re.sub(r"&(?!#?\w+;)", "&amp;", s)   # nur freistehende & escapen
    return s.replace("<", "&lt;").replace(">", "&gt;")

def _json_ld(obj) -> str:
    """JSON-LD ueber shared.seo_basis (Script-Kontext-Escapes, eine Quelle)."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from shared.seo_basis import json_ld
    return json_ld(obj)


def load_en() -> dict:
    return json.loads((I18N / "en.json").read_text(encoding="utf-8"))

def load_en_page_meta() -> dict:
    """_EN_PAGE_META aus i18n.js -> {slug: (title, desc)}. '/' -> 'index'.

    Liegt in shared/seo_basis.py, damit Sitemap, hreflang-Pruefung und dieser
    EN-Build dieselbe Liste lesen (SEO-Review 2026-09-30).
    """
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from shared.seo_basis import en_seiten_meta
    return en_seiten_meta()


# ---------------------------------------------------------------- SEO head
def build_en_head(slug: str, title: str, desc: str, og_type: str,
                  robots: str = STANDARD_ROBOTS) -> str:
    from shared.seo_basis import en_url as _en_url
    de_url = f"{BASE_URL}/{slug}"
    en_url = _en_url(slug)
    short  = re.sub(r"\s*[|—-]\s*SeasonAlpha\s*$", "", title).strip() or title

    webpage = {
        "@context": "https://schema.org", "@type": "WebPage",
        "name": short, "url": en_url, "description": desc, "inLanguage": "en",
        "isPartOf": {"@type": "WebSite", "name": "SeasonAlpha", "url": BASE_URL},
        "publisher": {"@type": "Organization", "name": "SeasonAlpha", "url": BASE_URL,
                      "logo": {"@type": "ImageObject", "url": OG_IMAGE}},
    }
    breadcrumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/en/"},
            {"@type": "ListItem", "position": 2, "name": short, "item": en_url},
        ],
    }
    jd = _json_ld
    t, d = esc_attr(title), esc_attr(desc)
    # noindex-Seiten (profile, watchlist, unsubscribe) bleiben noindex und bekommen
    # keine hreflang-Verweise — sie sollen nicht als Sprachpartner dienen.
    if "noindex" in robots.lower():
        sprachen = ""
    else:
        nl = chr(10)
        sprachen = (f'  <link rel="alternate" hreflang="de" href="{de_url}">{nl}'
                    f'  <link rel="alternate" hreflang="en" href="{en_url}">{nl}'
                    f'  <link rel="alternate" hreflang="x-default" href="{de_url}">{nl}')

    return f"""  {MARKER}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{t}</title>
  <meta name="description" content="{d}">
  <meta name="author" content="SeasonAlpha">
  <meta name="robots" content="{esc_attr(robots)}">
  <meta name="theme-color" content="#000000">
  <link rel="canonical" href="{en_url}">
{sprachen}
  <!-- Open Graph / Facebook / LinkedIn / WhatsApp / iMessage -->
  <meta property="og:type" content="{og_type}">
  <meta property="og:url" content="{en_url}">
  <meta property="og:title" content="{t}">
  <meta property="og:description" content="{d}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:site_name" content="SeasonAlpha">
  <meta property="og:locale" content="en_US">

  <!-- Twitter -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:site" content="{TWITTER}">
  <meta name="twitter:creator" content="{TWITTER}">
  <meta name="twitter:title" content="{t}">
  <meta name="twitter:description" content="{d}">
  <meta name="twitter:image" content="{OG_IMAGE}">

  <!-- Icons -->
  <link rel="icon" type="image/svg+xml" href="/landing/assets/images/favicon.svg">
  <link rel="icon" type="image/png" sizes="32x32" href="/landing/assets/images/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/landing/assets/images/favicon-16x16.png">
  <link rel="apple-touch-icon" sizes="180x180" href="/landing/assets/images/apple-touch-icon.png">

  <!-- Structured Data: WebPage -->
  <script type="application/ld+json">{jd(webpage)}</script>
  <!-- Structured Data: BreadcrumbList (SERP Rich Result) -->
  <script type="application/ld+json">{jd(breadcrumb)}</script>
"""


class HeadFehler(ValueError):
    pass


def replace_head(html: str, slug: str, title: str, desc: str, og_type: str):
    """Head einer Feature-Seite neu bauen (EN-Canonical, EN-JSON-LD, EN-OG).

    Ersetzt wird der Bereich von <head> bis einschliesslich des app.css-Links.
    Seit 2026-09-30 (SEO-Plan, EN-Duplikate):
    - Der CSS-Link darf den Cache-Buster tragen (`app.css?v=<sha>`, gesetzt von
      deploy/inject_credentials.sh VOR diesem Build) und wird unveraendert
      uebernommen. Vorher verlangte die Regex den Link OHNE Query — auf dem Server
      griff sie deshalb nie, und jede EN-Seite behielt deutsches JSON-LD mit
      DE-URLs (GSC: 18 EN-Seiten als "Duplikat").
    - Google Fonts: der nicht-blockierende Link (media="print" + onload) samt
      folgendem <noscript> wird woertlich uebernommen. Vorher traf die Regex den
      Fallback-Link IM <noscript> und baute ihn als render-blockierendes Stylesheet
      ein. Eine Quelle ohne Fonts (z. B. unsubscribe) ist gueltig; eine
      ausschliesslich blockierende Einbindung ist ein Fehler.
    - preconnect-Links und robots (noindex!) kommen aus der Quelle.
    """
    m = re.search(
        r'<head>(.*?)(<link\s+rel="stylesheet"\s+href="/landing/css/app\.css(?:\?v=[^"]*)?">)',
        html, re.S)
    if not m:
        return html, False
    bereich, css_link = m.group(1), m.group(2)
    rob = re.search(r'<meta\s+name="robots"\s+content="([^"]*)"', bereich)
    robots = html_unescape(rob.group(1)) if rob else STANDARD_ROBOTS
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from shared.seo_basis import google_fonts_pruefung
    fonts_paar, font_probleme = google_fonts_pruefung(bereich)
    if font_probleme:
        # Quelle fehlerhaft (blockierend, ohne onload oder ohne noscript) -> lieber
        # scheitern als eine haengende oder schriftlose EN-Seite ausliefern.
        raise HeadFehler(f"{slug}: " + "; ".join(font_probleme))
    preconnect = re.findall(r'<link\b[^>]*\brel="preconnect"[^>]*>', bereich)
    nl = chr(10)
    neu = "<head>" + nl + build_en_head(slug, title, desc, og_type, robots)
    for pc in preconnect:
        neu += f"{nl}  {pc}"
    if fonts_paar:
        neu += f"{nl}  {fonts_paar.strip()}"
    neu += f"{nl}  {css_link}"
    return html.replace(m.group(0), neu), True


def localize_head_targeted(html: str, en_url: str, de_url: str,
                           title: str, desc: str) -> str:
    """
    Fallback fuer Pages mit handgebautem Head (z.B. index.html): nur die
    sprach-/URL-spezifischen Felder ersetzen, reichen Head (JSON-LD, og-Marketing,
    site-verification) erhalten. hreflang bleibt unveraendert (dort schon korrekt).
    """
    t, d = esc_attr(title), esc_attr(desc)

    def sub1(pattern, repl):
        return re.sub(pattern, lambda m: m.group(1) + repl + m.group(2),
                      html, count=1, flags=re.S)

    html = re.sub(r"<title>.*?</title>", f"<title>{t}</title>", html, count=1, flags=re.S)
    html = sub1(r'(<meta\s+name="description"\s+content=")[^"]*(")', d)
    html = sub1(r'(<link\s+rel="canonical"\s+href=")[^"]*(")', en_url)
    html = sub1(r'(<meta\s+property="og:url"\s+content=")[^"]*(")', en_url)
    html = html.replace('content="de_DE"', 'content="en_US"')
    for prop in ("og:title", "twitter:title"):
        html = sub1(r'(<meta\s+(?:property|name)="' + prop + r'"\s+content=")[^"]*(")', t)
    for prop in ("og:description", "twitter:description"):
        html = sub1(r'(<meta\s+(?:property|name)="' + prop + r'"\s+content=")[^"]*(")', d)
    html = html.replace('"inLanguage":"de-DE"', '"inLanguage":"en-US"')
    return html


# ---------------------------------------------------------------- body splice
class Splicer(HTMLParser):
    """Ersetzt data-i18n*-Inhalte positions-basiert; restliches HTML bleibt gleich."""
    def __init__(self, src: str, en: dict):
        super().__init__(convert_charrefs=False)
        self.src = src
        self.en = en
        self.edits = []          # (start, end, replacement)
        self.stack = []          # offene Element-Frames
        self.skipped_mixed = 0
        self.baked = 0
        self.line_starts = [0]
        for i, ch in enumerate(src):
            if ch == "\n":
                self.line_starts.append(i + 1)

    def _off(self) -> int:
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def _set_attr(self, raw: str, attr: str, val: str) -> str:
        ev = esc_attr(val)
        pat = re.compile(r'(\b' + attr + r'=")[^"]*(")')
        if pat.search(raw):
            return pat.sub(lambda m: m.group(1) + ev + m.group(2), raw, count=1)
        if raw.rstrip().endswith("/>"):
            return re.sub(r"/>\s*$", f' {attr}="{ev}"/>', raw)
        return re.sub(r">\s*$", f' {attr}="{ev}">', raw)

    def _close_frame(self, frame, content_end, end_full):
        """Edit fuer ein geschlossenes Element erzeugen + Child-Span am Parent vermerken."""
        tgt = frame["target"]
        if tgt and not frame["in_suppressed"]:
            kind, key = tgt
            val = self.en.get(key)
            if val is not None:
                if kind == "html":
                    self.edits.append((frame["content_start"], content_end, val))
                    self.baked += 1
                elif frame["children"]:
                    if self._replace_last_text(frame, content_end, val):
                        self.baked += 1
                    else:
                        self.skipped_mixed += 1
                else:
                    self.edits.append((frame["content_start"], content_end,
                                       esc_text(val)))
                    self.baked += 1
        if self.stack and self.stack[-1]["target"] and \
           self.stack[-1]["target"][0] == "text":
            self.stack[-1]["children"].append((frame["start"], end_full))

    def _starttag(self, tag, attrs, selfclose):
        start = self._off()
        # Peers mit optionalem End-Tag implizit schliessen (<li>, <td>, ...)
        while self.stack and self.stack[-1]["tag"] in IMPLICIT_CLOSE.get(tag, ()):
            self._close_frame(self.stack.pop(), start, start)

        raw   = self.get_starttag_text()
        end   = start + len(raw)
        ad    = dict(attrs)
        # in_suppressed = liegt INNERHALB eines data-i18n-html-Targets (nicht anfassen)
        in_suppressed = any(f["suppress_children"] for f in self.stack)

        # Attribut-Targets (placeholder/title/aria) am Start-Tag ersetzen
        if not in_suppressed:
            newraw = raw
            for a, real in (("data-i18n-placeholder", "placeholder"),
                            ("data-i18n-title", "title"),
                            ("data-i18n-aria", "aria-label")):
                if a in ad and self.en.get(ad[a]) is not None:
                    newraw = self._set_attr(newraw, real, self.en[ad[a]])
                    self.baked += 1
            if newraw != raw:
                self.edits.append((start, end, newraw))

        target = None
        if "data-i18n-html" in ad:
            target = ("html", ad["data-i18n-html"])
        elif "data-i18n" in ad:
            target = ("text", ad["data-i18n"])

        is_void = selfclose or tag in VOID or raw.rstrip().endswith("/>")
        frame = {"tag": tag, "start": start, "content_start": end,
                 "target": target, "children": [],
                 "in_suppressed": in_suppressed,
                 "suppress_children": in_suppressed or bool(target and target[0] == "html")}
        if is_void:
            if self.stack and self.stack[-1]["target"] and \
               self.stack[-1]["target"][0] == "text":
                self.stack[-1]["children"].append((start, end))
        else:
            self.stack.append(frame)

    def handle_starttag(self, tag, attrs):
        self._starttag(tag, attrs, selfclose=False)

    def handle_startendtag(self, tag, attrs):
        self._starttag(tag, attrs, selfclose=True)

    def handle_endtag(self, tag):
        if all(f["tag"] != tag for f in self.stack):
            return  # streunendes End-Tag ohne offenes Pendant
        endpos = self._off()
        while self.stack:
            frame = self.stack.pop()
            is_match = frame["tag"] == tag
            end_full = endpos + (len(f"</{tag}>") if is_match else 0)
            self._close_frame(frame, endpos, end_full)
            if is_match:
                break

    def _replace_last_text(self, frame, content_end, val) -> bool:
        """Mixed content: nur den letzten direkten Textknoten ersetzen."""
        gaps, cur = [], frame["content_start"]
        for cs, ce in sorted(frame["children"]):
            if cs > cur:
                gaps.append((cur, cs))
            cur = ce
        if content_end > cur:
            gaps.append((cur, content_end))
        for gs, ge in reversed(gaps):
            text = self.src[gs:ge]
            if text.strip():
                lead = re.match(r"\s*", text).group(0)
                self.edits.append((gs, ge, lead + esc_text(val)))
                return True
        return False

    def apply(self) -> str:
        self.feed(self.src)
        out = self.src
        for start, end, rep in sorted(self.edits, key=lambda e: -e[0]):
            out = out[:start] + rep + out[end:]
        return out


# index.html JSON-LD: deutsche Structured Data (WebSite/SoftwareApplication/
# Organization) -> Englisch. Map auf DEKODIERTE Strings (json.loads loest
# Unicode-Escapes auf), daher escape-unabhaengig. Die FAQPage der Startseite ist
# seit 2026-09-30 entfernt (unsichtbar, inhaltlich falsch, FAQ-Rich-Results gibt
# es bei Google seit 07.05.2026 nicht mehr).
_INDEX_JSONLD_DE2EN = {
    "de-DE": "en-US",
    "SeasonAlpha — Saisonale Börsenanalyse": "SeasonAlpha — Seasonal Stock Market Analysis",
    "Saisonale Börsenanalyse mit bis zu 131 Jahren Marktdaten. Über 350 Basiswerte.":
        "Seasonal stock market analysis with up to 131 years of market data. Over 350 assets.",
    "Datengetriebene saisonale Börsenanalyse mit KI":
        "Data-driven seasonal stock market analysis with AI",
}
# Felder, deren Text sprachabhaengig ist. Alles andere (URLs, @type, Preise,
# Kategorien) ist neutral. Ein Text in diesen Feldern ohne Uebersetzung laesst
# den EN-Build scheitern — sonst stuende nach einer DE-Textaenderung still
# Deutsch im EN-Schema (Codex, SEO-Review 2026-09-30).
_INDEX_JSONLD_SPRACHFELDER = {"name", "alternateName", "description", "inLanguage"}
_INDEX_JSONLD_NEUTRAL = {"SeasonAlpha"}


class UnuebersetztesSchema(ValueError):
    pass


def localize_index_jsonld(html_doc: str) -> str:
    """JSON-LD-Bloecke parsen, sprachabhaengige Felder DE -> EN, re-serialisieren.

    Wirft `UnuebersetztesSchema`, wenn ein sprachabhaengiges Feld keinen Eintrag
    in `_INDEX_JSONLD_DE2EN` hat.
    """
    fehlend = []

    def walk(o, feld=None):
        if isinstance(o, dict):
            neu = {k: walk(v, k) for k, v in o.items()}
            # Seiten-/Suchziele sprachabhaengig; Organisations-Identitaet bleibt Domainwurzel
            if neu.get("@type") == "WebSite" and neu.get("url") == f"{BASE_URL}/":
                neu["url"] = f"{BASE_URL}/en/"
            if isinstance(neu.get("urlTemplate"), str) and neu["urlTemplate"].startswith(f"{BASE_URL}/dashboard"):
                neu["urlTemplate"] = f"{BASE_URL}/en" + neu["urlTemplate"][len(BASE_URL):]
            return neu
        if isinstance(o, list):
            return [walk(x, feld) for x in o]
        if isinstance(o, str) and feld in _INDEX_JSONLD_SPRACHFELDER:
            if o in _INDEX_JSONLD_DE2EN:
                return _INDEX_JSONLD_DE2EN[o]
            # schon englisch (z. B. inLanguage, das localize_head_targeted vorab umsetzt)
            if o not in _INDEX_JSONLD_NEUTRAL and o not in _INDEX_JSONLD_DE2EN.values():
                fehlend.append(f"{feld}: {o!r}")
        return o

    def repl(m):
        data = json.loads(m.group(1))   # ungueltiges JSON soll hier scheitern, nicht still durchgehen
        return ('<script type="application/ld+json">'
                + json.dumps(walk(data), ensure_ascii=True, separators=(",", ":"))
                + "</script>")

    aus = re.sub(r'<script type="application/ld\+json">(.*?)</script>',
                 repl, html_doc, flags=re.S)
    if fehlend:
        raise UnuebersetztesSchema("Startseiten-Schema ohne EN-Uebersetzung: " + "; ".join(fehlend))
    return aus


def strip_en_hidden(html: str) -> str:
    """
    Entfernt Elemente mit data-en-hide aus dem EN-Output. Fuer DE-only-Bloecke,
    die bereits einen englischen Geschwister-Block haben (z.B. der zweisprachige
    Footer-Rechtstext: dt. Absatz + engl. Absatz -> auf EN nur der englische).
    Annahme: kein verschachteltes gleichnamiges Tag im Element.
    """
    return re.sub(r'<(\w+)[^>]*\bdata-en-hide\b[^>]*>.*?</\1>\s*', '',
                  html, flags=re.S)


def rewrite_body_links(html: str) -> str:
    """Links im Body auf /en/ umschreiben — NUR fuer Seiten mit EN-Fassung.

    Vorher pauschal mit Ausnahmeliste (SKIP_PREFIXES): die EN-Startseite verlinkte
    so /en/crash-fruehwarnung und /en/ueber-uns (404) sowie /en/congress und
    /en/index-effekt (301). Massgeblich ist jetzt _EN_PAGE_META (SEO-Plan 1b, G2).
    """
    idx = html.find("<body")
    if idx < 0:
        return html
    head, body = html[:idx], html[idx:]
    from shared.seo_basis import en_slug
    # DE-Pfad -> EN-Pfad (ohne /en); abweichende EN-Adressen aus _EN_SLUGS (z. B. /wahlen -> /elections)
    en_pfade = {("/" if s == "index" else f"/{s}"): ("/" if s == "index" else f"/{en_slug(s)}")
                for s in load_en_page_meta()}

    def repl(m):
        href = m.group(1)
        if any(href.startswith(p) for p in SKIP_PREFIXES):
            return m.group(0)
        pfad = re.split(r"[?#]", href, maxsplit=1)[0]
        if len(pfad) > 1 and pfad.endswith("/"):
            pfad = pfad[:-1]
        if pfad not in en_pfade:
            return m.group(0)
        # Query/Fragment erhalten, abschliessenden Schrägstrich verwerfen (/en/x/ wäre 404)
        rest = re.match(r"[^?#]*(.*)", href).group(1)
        return f'href="/en{en_pfade[pfad]}{rest}"'

    return head + HREF_RE.sub(repl, body)


# ---------------------------------------------------------------- per page
def build_page(slug: str, title: str, desc: str, en: dict, write: bool):
    src = (LANDING / "index.html") if slug == "index" else (PAGES / f"{slug}.html")
    if not src.exists():
        return f"[MISS] {slug}: Quelle fehlt ({src})"

    html = src.read_text(encoding="utf-8")
    og_type = _DE_PAGE_META.get(f"{slug}.html", {}).get("type", "website")

    from shared.seo_basis import en_url as _en_url, en_slug
    en_url = _en_url(slug)
    de_url = f"{BASE_URL}/" if slug == "index" else f"{BASE_URL}/{slug}"

    html = re.sub(r'<html\s+lang="de"', '<html lang="en"', html, count=1)
    if slug == "index":
        # Startseite: eigener, reicher Head (Umami, site-verification, eigenes
        # JSON-LD) -> gezielt lokalisieren statt neu bauen.
        html = localize_head_targeted(html, en_url, de_url, title, desc)
        head_ok, head_mode = True, "targeted"
    else:
        html, head_ok = replace_head(html, slug, title, desc, og_type)
        head_mode = "regen"
        if not head_ok:
            # Frueher stiller Rueckfall auf localize_head_targeted -> deutsches
            # JSON-LD mit DE-URLs auf der EN-Seite. Jetzt ein Build-Fehler.
            raise HeadFehler(f"{slug}: Head-Bereich bis app.css nicht gefunden")

    if slug == "index":
        html = localize_index_jsonld(html)
    html = strip_en_hidden(html)
    sp = Splicer(html, en)
    html = sp.apply()
    html = rewrite_body_links(html)

    note = "" if head_mode == "regen" else " [head: targeted]"
    if sp.skipped_mixed:
        note += f" [WARN: {sp.skipped_mixed} mixed-content uebersprungen]"

    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        out = OUT / f"{en_slug(slug)}.html"
        out.write_text(html, encoding="utf-8")
        return f"[WRITE] {slug}: {sp.baked} Strings gebacken -> {out}{note}"
    return f"[DRY]   {slug}: {sp.baked} Strings (head={'ok' if head_ok else 'FAIL'}){note}"


def main():
    ap = argparse.ArgumentParser(description="EN-Landing-Pages pre-rendern")
    ap.add_argument("--page", help="nur dieser Slug (z.B. dashboard)")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    en   = load_en()
    meta = load_en_page_meta()
    print(f"=== build_en.py ({'WRITE' if args.write else 'DRY-RUN'}) | "
          f"{len(meta)} Pages bekannt | {len(en)} en.json-Keys ===")

    from shared.seo_basis import pruefe_en_slugs
    konflikte = pruefe_en_slugs(meta)
    if konflikte:
        raise SystemExit("EN-Adressen nicht eindeutig: " + "; ".join(konflikte))
    slugs = [args.page] if args.page else sorted(meta.keys())
    for slug in slugs:
        if slug not in meta:
            print(f"  [SKIP] {slug}: kein _EN_PAGE_META-Eintrag")
            continue
        title, desc = meta[slug]
        print("  " + build_page(slug, title, desc, en, args.write))

    # Verwaiste EN-Dateien entfernen: landing/en/ ist gitignored und wurde nie
    # aufgeräumt. Nach dem Löschen von /studien lag landing/en/studien.html weiter
    # auf dem Server, verlinkte /en/index-effekt (existiert nicht) und liess den
    # Deploy am Wächter scheitern (2026-09-30). Nur beim Vollbau, nie mit --page.
    if args.write and not args.page and OUT.exists():
        from shared.seo_basis import en_slug
        soll = {f"{en_slug(s)}.html" for s in meta}
        for datei in sorted(OUT.glob("*.html")):
            if datei.name not in soll:
                datei.unlink()
                print(f"  [DEL]   {datei.name}: kein _EN_PAGE_META-Eintrag (verwaist)")

    if not args.write:
        print("\n  -> Mit --write schreiben, danach: py landing/verify_en.py")


if __name__ == "__main__":
    main()
