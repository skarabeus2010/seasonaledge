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

def load_en() -> dict:
    return json.loads((I18N / "en.json").read_text(encoding="utf-8"))

def load_en_page_meta() -> dict:
    """_EN_PAGE_META aus i18n.js parsen -> {slug: (title, desc)}. '/' -> 'index'."""
    txt = I18N_JS.read_text(encoding="utf-8")
    block = re.search(r"_EN_PAGE_META\s*=\s*\{(.*?)\n\s*\};", txt, re.S)
    scope = block.group(1) if block else txt
    entry = re.compile(
        r"'(/[a-z0-9-]*)'\s*:\s*\{\s*"
        r"title:\s*'((?:[^'\\]|\\.)*)'\s*,\s*"
        r"desc:\s*'((?:[^'\\]|\\.)*)'\s*\}", re.S)
    out = {}
    for path, title, desc in entry.findall(scope):
        slug = path.strip("/") or "index"
        unesc = lambda s: s.replace("\\'", "'").replace('\\"', '"')
        out[slug] = (unesc(title), unesc(desc))
    return out


# ---------------------------------------------------------------- SEO head
def build_en_head(slug: str, title: str, desc: str, og_type: str) -> str:
    de_url = f"{BASE_URL}/{slug}"
    en_url = f"{BASE_URL}/en/{slug}"
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
    jd = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    t, d = esc_attr(title), esc_attr(desc)

    return f"""  {MARKER}
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{t}</title>
  <meta name="description" content="{d}">
  <meta name="author" content="SeasonAlpha">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <meta name="theme-color" content="#000000">
  <link rel="canonical" href="{en_url}">
  <link rel="alternate" hreflang="de" href="{de_url}">
  <link rel="alternate" hreflang="en" href="{en_url}">
  <link rel="alternate" hreflang="x-default" href="{de_url}">

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


def replace_head(html: str, slug: str, title: str, desc: str, og_type: str):
    m = re.search(
        r"<head>(.*?)(<link\s+rel=\"stylesheet\"\s+href=\"/landing/css/app\.css\">)",
        html, re.S)
    if not m:
        return html, False
    fonts = re.search(
        r'(<link\s+href="https://fonts\.googleapis\.com[^"]*"\s+rel="stylesheet">)', html)
    new_head = "<head>\n" + build_en_head(slug, title, desc, og_type)
    if fonts:
        new_head += f"\n  {fonts.group(1)}"
    new_head += '\n  <link rel="stylesheet" href="/landing/css/app.css">'
    return html.replace(m.group(0), new_head), True


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
# Organization/FAQPage) -> Englisch. Map auf DEKODIERTE Strings (json.loads
# loest \u-Escapes auf), daher escape-unabhaengig.
_INDEX_JSONLD_DE2EN = {
    "de-DE": "en-US",
    "SeasonAlpha — Saisonale Börsenanalyse": "SeasonAlpha — Seasonal Stock Market Analysis",
    "Saisonale Börsenanalyse mit bis zu 131 Jahren Marktdaten und 15 KI-Modellen. Über 500 Basiswerte.":
        "Seasonal stock market analysis with up to 131 years of market data and 15 AI models. Over 500 assets.",
    "Datengetriebene saisonale Börsenanalyse mit KI":
        "Data-driven seasonal stock market analysis with AI",
    "Was ist saisonale Boersenanalyse?": "What is seasonal stock market analysis?",
    "Saisonale Boersenanalyse untersucht wiederkehrende Muster in Aktienkursen ueber Jahrzehnte. "
    "SeasonAlpha nutzt bis zu 131 Jahre Marktdaten und 15 KI-Modelle.":
        "Seasonal stock market analysis examines recurring patterns in stock prices over decades. "
        "SeasonAlpha uses up to 131 years of market data and 15 AI models.",
    "Ist SeasonAlpha kostenlos?": "Is SeasonAlpha free?",
    "Ja. Alle Analyse-Module, ueber 500 Basiswerte und interaktive Charts sind frei verfuegbar.":
        "Yes. All analysis modules, over 500 assets and interactive charts are freely available.",
    "Welche Basiswerte werden unterstuetzt?": "Which assets are supported?",
    "Ueber 500 Basiswerte: US- und EU-Aktien, ETFs, Indizes, Rohstoffe, Kryptowaehrungen und Anleihen.":
        "Over 500 assets: US and EU stocks, ETFs, indices, commodities, cryptocurrencies and bonds.",
    "Was bedeutet The Beauty of Noise?": "What does The Beauty of Noise mean?",
    "Boersenkurse erscheinen chaotisch (Noise). SeasonAlpha extrahiert daraus statistisch "
    "signifikante saisonale Muster (Signal) — das ist die Schoenheit im Rauschen.":
        "Stock prices appear chaotic (noise). SeasonAlpha extracts statistically significant "
        "seasonal patterns (signal) from it — that is the beauty in the noise.",
}


def localize_index_jsonld(html_doc: str) -> str:
    """JSON-LD-Bloecke parsen, bekannte dt. Werte -> EN, re-serialisieren."""
    def walk(o):
        if isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(x) for x in o]
        if isinstance(o, str):
            return _INDEX_JSONLD_DE2EN.get(o, o)
        return o

    def repl(m):
        try:
            data = json.loads(m.group(1))
        except Exception:
            return m.group(0)
        return ('<script type="application/ld+json">'
                + json.dumps(walk(data), ensure_ascii=True, separators=(",", ":"))
                + "</script>")

    return re.sub(r'<script type="application/ld\+json">(.*?)</script>',
                  repl, html_doc, flags=re.S)


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
    idx = html.find("<body")
    if idx < 0:
        return html
    head, body = html[:idx], html[idx:]

    def repl(m):
        href = m.group(1)
        if any(href.startswith(p) for p in SKIP_PREFIXES):
            return m.group(0)
        return f'href="/en{href}"'

    return head + HREF_RE.sub(repl, body)


# ---------------------------------------------------------------- per page
def build_page(slug: str, title: str, desc: str, en: dict, write: bool):
    src = (LANDING / "index.html") if slug == "index" else (PAGES / f"{slug}.html")
    if not src.exists():
        return f"[MISS] {slug}: Quelle fehlt ({src})"

    html = src.read_text(encoding="utf-8")
    og_type = _DE_PAGE_META.get(f"{slug}.html", {}).get("type", "website")

    if slug == "index":
        en_url, de_url = f"{BASE_URL}/en/", f"{BASE_URL}/"
    else:
        en_url, de_url = f"{BASE_URL}/en/{slug}", f"{BASE_URL}/{slug}"

    html = re.sub(r'<html\s+lang="de"', '<html lang="en"', html, count=1)
    html, head_ok = replace_head(html, slug, title, desc, og_type)
    head_mode = "regen"
    if not head_ok:
        html = localize_head_targeted(html, en_url, de_url, title, desc)
        head_ok, head_mode = True, "targeted"

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
        out = OUT / ("index.html" if slug == "index" else f"{slug}.html")
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

    slugs = [args.page] if args.page else sorted(meta.keys())
    for slug in slugs:
        if slug not in meta:
            print(f"  [SKIP] {slug}: kein _EN_PAGE_META-Eintrag")
            continue
        title, desc = meta[slug]
        print("  " + build_page(slug, title, desc, en, args.write))

    if not args.write:
        print("\n  -> Mit --write schreiben, danach: py landing/verify_en.py")


if __name__ == "__main__":
    main()
