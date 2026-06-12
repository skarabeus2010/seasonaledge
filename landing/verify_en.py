# -*- coding: utf-8 -*-
"""
verify_en.py - Verifizierung der EN-Lokalisierung (SeasonAlpha)
================================================================

Prueft, ob die *erwarteten* Ergebnisse der EN-Uebersetzung tatsaechlich
eintreten. Laeuft in zwei Phasen:

  PHASE A (Quelle + Dictionary)  -- funktioniert SOFORT, ohne Build:
    A1  Jeder data-i18n*-Key in den HTML-Pages existiert in en.json
        (fehlt einer -> heute stiller DE-Fallback = der eigentliche Bug)
    A2  en.json-Keys, die nirgends referenziert werden (tote Keys, INFO)
    A3  en.json-Wert == de.json-Wert bei laengeren deutschen Texten
        (Verdacht: vergessene Uebersetzung, WARN)
    A4  Meta-Keys (meta.<slug>.title/desc) je EN-Page vorhanden?
        (Vorbereitung "Single Source of Truth" statt _EN_PAGE_META im JS)

  PHASE B (Build-Output)  -- aktiv sobald landing/en/ existiert:
    B1  Fuer jede erwartete EN-Page existiert die gebaute Datei
    B2  lang="en" gesetzt, lang="de" nicht mehr vorhanden
    B3  og:locale = en_US, canonical zeigt auf /en/
    B4  hreflang de + en + x-default vorhanden, <title> nicht leer
    B5  FOUC-frei: EN-Wert steht STATISCH im HTML; wenn der DE-Wert noch
        da ist und der EN-Wert fehlt -> echte untranslated Stelle (FAIL)
    B6  Kein sichtbares Deutsch mehr: keine Umlaute/dt. Stoppwoerter im
        gerenderten Text und in aria-label/title/placeholder/alt

Aufruf:
    py landing/verify_en.py                 # beide Phasen (B nur wenn Build da)
    py landing/verify_en.py --sources-only  # nur Phase A
    py landing/verify_en.py --build-only    # nur Phase B
    py landing/verify_en.py --build-dir landing/en
    py landing/verify_en.py --strict        # WARN -> FAIL (CI-Modus)

Exit-Code: 0 = alle harten Checks bestanden, 1 = mind. ein FAIL
           (mit --strict zaehlen auch WARN als FAIL).

Bewusst nur Stdlib (json/re/pathlib/html) -- laeuft im Container ohne deps.
Konsolen-Ausgabe ist reines ASCII (cp1252-sicher auf Windows).
"""

import sys, re, json, html, argparse
from pathlib import Path

LANDING = Path(__file__).resolve().parent
PAGES   = LANDING / "pages"
I18N    = LANDING / "i18n"
I18N_JS = LANDING / "js" / "i18n.js"

# Pages, die KEIN EN bekommen sollen (Demo/Nur-DE) -> aus Erwartung ausgenommen
EXCLUDE_PAGES = {"apex-demo", "crash-fruehwarnung"}

# Attribut -> ob der Wert HTML (mit Tags) ist
I18N_ATTRS = {
    "data-i18n":             False,
    "data-i18n-html":        True,
    "data-i18n-placeholder": False,
    "data-i18n-title":       False,
    "data-i18n-aria":        False,
}
ATTR_RE = re.compile(r'(data-i18n(?:-[a-z]+)?)\s*=\s*"([^"]+)"')

# Sichtbare Attribute, deren Werte uebersetzt sein muessen (B6)
VISIBLE_ATTRS = ("aria-label", "title", "placeholder", "alt")
VISIBLE_ATTR_RE = re.compile(
    r'(?:' + "|".join(VISIBLE_ATTRS) + r')\s*=\s*"([^"]*)"'
)

# Deutsche Stoppwoerter als starkes Sprach-Signal (B6/A3)
DE_WORDS = re.compile(
    r'\b(?:der|die|das|und|oder|nicht|fuer|ueber|durch|wird|sind|eine|einen|'
    r'Jahre|Verlauf|Durchschnitt|Woche|Monat|Tag|Handelstag|Saisonal|'
    r'Aufschlag|Abschlag|Verzerrung|Wahrscheinlichkeit|Renditen?)\b',
    re.IGNORECASE,
)
UMLAUT_RE = re.compile(r'[äöüßÄÖÜ]')  # aeoeuess


# ---------------------------------------------------------------- helpers
def _norm(s: str) -> str:
    """Tags entfernen, DANN Entities aufloesen (sonst frisst <[^>]+> literale &lt;)."""
    s = re.sub(r"<[^>]+>", "", s or "")
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

def _strip_noise(html_text: str) -> str:
    """script/style/Kommentare raus -> nur sichtbarer Markup-Rahmen bleibt."""
    html_text = re.sub(r"<script\b.*?</script>", " ", html_text, flags=re.S | re.I)
    html_text = re.sub(r"<style\b.*?</style>",  " ", html_text, flags=re.S | re.I)
    html_text = re.sub(r"<!--.*?-->",           " ", html_text, flags=re.S)
    return html_text

def load_json(p: Path) -> dict:
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))

def expected_pages() -> dict:
    """
    Erwartete EN-Pages aus _EN_PAGE_META in i18n.js ableiten (= die deklarierte
    EN-Oberflaeche). Liefert {slug: source_path}. '/' -> index.html.
    """
    pages = {}
    if I18N_JS.exists():
        txt = I18N_JS.read_text(encoding="utf-8")
        block = re.search(r"_EN_PAGE_META\s*=\s*\{(.*?)\n\s*\};", txt, re.S)
        scope = block.group(1) if block else txt
        for path in re.findall(r"'(/[a-z0-9-]*)'\s*:\s*\{", scope):
            slug = path.strip("/") or "index"
            if slug in EXCLUDE_PAGES:
                continue
            src = (LANDING / "index.html") if slug == "index" else (PAGES / f"{slug}.html")
            pages[slug] = src
    if not pages:  # Fallback: alle Pages auf der Platte
        for f in sorted(PAGES.glob("*.html")):
            if f.stem not in EXCLUDE_PAGES:
                pages[f.stem] = f
        pages["index"] = LANDING / "index.html"
    return pages

def collect_keys(html_text: str):
    """[(attr, key, is_html), ...] aus einer HTML-Quelle."""
    out = []
    for attr, key in ATTR_RE.findall(html_text):
        is_html = I18N_ATTRS.get(attr, False)
        out.append((attr, key, is_html))
    return out


# ---------------------------------------------------------------- report
class Report:
    def __init__(self, strict):
        self.fail = 0
        self.warn = 0
        self.strict = strict
    def ok(self, msg):   print(f"  [OK]   {msg}")
    def info(self, msg): print(f"  [INFO] {msg}")
    def warned(self, msg):
        self.warn += 1
        print(f"  [WARN] {msg}")
    def failed(self, msg):
        self.fail += 1
        print(f"  [FAIL] {msg}")
    def section(self, title):
        print(f"\n=== {title} ===")
    @property
    def exit_code(self):
        return 1 if (self.fail or (self.strict and self.warn)) else 0


# ---------------------------------------------------------------- Phase A
def phase_a(rep: Report, pages: dict, en: dict, de: dict):
    rep.section("PHASE A - Quelle + Dictionary")

    referenced = {}   # key -> set(slug)
    missing    = {}   # key -> set(slug)
    for slug, src in pages.items():
        if not src.exists():
            rep.failed(f"A1  Quell-Page fehlt auf der Platte: {src}")
            continue
        for _attr, key, _ in collect_keys(src.read_text(encoding="utf-8")):
            referenced.setdefault(key, set()).add(slug)
            if key not in en:
                missing.setdefault(key, set()).add(slug)

    # A1 - fehlende EN-Keys (HART)
    if missing:
        for key in sorted(missing):
            locs = ", ".join(sorted(missing[key]))
            rep.failed(f"A1  Key fehlt in en.json: '{key}'  (in: {locs})")
    else:
        rep.ok(f"A1  Alle {len(referenced)} referenzierten Keys existieren in en.json")

    # A2 - tote Keys (INFO)
    dead = sorted(set(en) - set(referenced) - _meta_keys(en))
    if dead:
        rep.info(f"A2  {len(dead)} en.json-Keys werden nirgends referenziert "
                 f"(z.B. {', '.join(dead[:5])}{' ...' if len(dead) > 5 else ''})")
    else:
        rep.ok("A2  Keine toten en.json-Keys")

    # A3 - identische DE==EN bei deutschem Text (WARN)
    if de:
        suspects = []
        for key in referenced:
            ev, dv = en.get(key), de.get(key)
            if ev and dv and ev == dv and (UMLAUT_RE.search(ev) or
               (DE_WORDS.search(ev) and len(ev.split()) >= 3)):
                suspects.append(key)
        if suspects:
            for key in sorted(suspects)[:20]:
                rep.warned(f"A3  en==de, vermutlich unuebersetzt: '{key}'")
            if len(suspects) > 20:
                rep.info(f"A3  ... und {len(suspects) - 20} weitere")
        else:
            rep.ok("A3  Keine verdaechtig identischen DE/EN-Werte")
    else:
        rep.info("A3  de.json nicht gefunden - DE/EN-Vergleich uebersprungen")

    # A5 - mis-markiertes data-i18n: Wert enthaelt HTML-Tags, Element ist aber
    #      Text-Modus -> Laufzeit + Build uebersetzen nur teilweise. MUSS -html sein.
    mismarked = {}
    for slug, src in pages.items():
        if not src.exists():
            continue
        for attr, key, _ in collect_keys(_strip_noise(src.read_text(encoding="utf-8"))):
            if attr == "data-i18n" and "<" in en.get(key, ""):
                mismarked.setdefault(key, set()).add(slug)
    if mismarked:
        for key in sorted(mismarked):
            locs = ", ".join(sorted(mismarked[key]))
            rep.failed(f"A5  data-i18n mit HTML-Wert -> muss data-i18n-html sein: "
                       f"'{key}'  ({locs})")
    else:
        rep.ok("A5  Kein mis-markiertes data-i18n (HTML-Wert im Text-Modus)")

    # A6 - data-i18n (Text-Modus) auf Element MIT Inline-Kind (<b>/<a>/<em>...).
    #      Laufzeit + Build ersetzen nur den letzten Textknoten -> fuehrender
    #      deutscher Teil bleibt stehen. Auch live halb uebersetzt.
    mixed_re = re.compile(
        r'data-i18n="([^"]+)"[^>]*>[^<]*<(?:b|a|em|strong|code|i|span|sup|sub|br)\b')
    mixed = {}
    for slug, src in pages.items():
        if not src.exists():
            continue
        for key in mixed_re.findall(_strip_noise(src.read_text(encoding="utf-8"))):
            mixed.setdefault(key, set()).add(slug)
    if mixed:
        bypage = {}
        for key, slugs in mixed.items():
            for s in slugs:
                bypage.setdefault(s, []).append(key)
        rep.warned(f"A6  {len(mixed)} data-i18n auf Mixed-Content (Inline-Kind) - "
                   f"Kandidaten fuer Teil-Uebersetzung, via B6 im Output bestaetigen:")
        for s in sorted(bypage):
            rep.info(f"      {s}: {len(bypage[s])} ({', '.join(sorted(bypage[s])[:4])}"
                     f"{' ...' if len(bypage[s]) > 4 else ''})")
    else:
        rep.ok("A6  Kein data-i18n auf Mixed-Content")

    # A4 - Meta-Keys je Page (Vorbereitung Single-Source-of-Truth)
    miss_meta = [s for s in pages if f"meta.{s}.title" not in en]
    if miss_meta:
        rep.info(f"A4  {len(miss_meta)}/{len(pages)} Pages ohne 'meta.<slug>.title' "
                 f"in en.json (heute noch in _EN_PAGE_META im JS): "
                 f"{', '.join(sorted(miss_meta)[:6])}"
                 f"{' ...' if len(miss_meta) > 6 else ''}")
    else:
        rep.ok("A4  Alle Pages haben meta.<slug>.title in en.json")

    return referenced

def _meta_keys(en: dict):
    return {k for k in en if k.startswith("meta.")}


# ---------------------------------------------------------------- Phase B
def phase_b(rep: Report, pages: dict, en: dict, de: dict, build_dir: Path):
    rep.section(f"PHASE B - Build-Output ({build_dir})")

    if not build_dir.exists():
        rep.info(f"Build-Verzeichnis {build_dir} existiert noch nicht - "
                 f"Phase B uebersprungen (erst nach dem EN-Build aktiv).")
        return

    for slug, src in sorted(pages.items()):
        out = build_dir / ("index.html" if slug == "index" else f"{slug}.html")
        if not out.exists():
            rep.failed(f"B1  EN-Datei fehlt: {out}")
            continue
        doc = out.read_text(encoding="utf-8")

        # B2 - lang (hreflang="de" NICHT als Treffer werten -> Lookbehind)
        if 'lang="en"' not in doc:
            rep.failed(f"B2  [{slug}] lang=\"en\" fehlt")
        if re.search(r'(?<![\w-])lang="de"', doc):
            rep.failed(f"B2  [{slug}] lang=\"de\" noch vorhanden")

        # B3 - og:locale + canonical
        if "en_US" not in doc or "de_DE" in doc:
            rep.failed(f"B3  [{slug}] og:locale nicht auf en_US umgestellt")
        canon = re.search(r'rel="canonical"\s+href="([^"]+)"', doc) or \
                re.search(r'href="([^"]+)"\s+rel="canonical"', doc)
        if canon and "/en/" not in canon.group(1):
            rep.failed(f"B3  [{slug}] canonical zeigt nicht auf /en/: {canon.group(1)}")

        # B4 - hreflang + title
        hreflangs = set(re.findall(r'hreflang="([^"]+)"', doc))
        for need in ("de", "en", "x-default"):
            if need not in hreflangs:
                rep.failed(f"B4  [{slug}] hreflang '{need}' fehlt")
        title = re.search(r"<title>(.*?)</title>", doc, re.S)
        if not title or not title.group(1).strip():
            rep.failed(f"B4  [{slug}] <title> leer")

        # B5 - statische EN-Texte vorhanden (FOUC-frei)
        # Keys aus <script>-Templates sind dynamisch (JS), nicht statisch backbar
        # -> vor dem Sammeln Script/Style entfernen.
        rendered = _norm(_strip_noise(doc))
        doc_unesc = html.unescape(doc)   # fuer Attribut-Werte (placeholder/title/aria)
        attr_targets = {"data-i18n-placeholder", "data-i18n-title", "data-i18n-aria"}
        src_static = _strip_noise(src.read_text(encoding="utf-8"))
        miss_static = []
        for attr, key, is_html in collect_keys(src_static):
            ev = en.get(key)
            if not ev:
                continue
            needle = _norm(ev)
            if not needle:
                continue
            # Attribut-Targets im rohen (unescapten) Doc suchen, Text-Targets im Render
            if attr in attr_targets:
                if needle in html.unescape(_strip_noise(doc)) or ev in doc_unesc:
                    continue
            elif needle in rendered:
                continue
            dv = _norm(de.get(key, "")) if de else ""
            if dv and dv in rendered:
                rep.failed(f"B5  [{slug}] untranslated: '{key}' "
                           f"(DE noch im Output, EN fehlt)")
            else:
                miss_static.append(key)
        if miss_static:
            rep.warned(f"B5  [{slug}] {len(miss_static)} EN-Werte nicht statisch "
                       f"auffindbar (evtl. dynamisch/Attribut): "
                       f"{', '.join(miss_static[:4])}"
                       f"{' ...' if len(miss_static) > 4 else ''}")

        # B6 - kein sichtbares Deutsch im gerenderten Text
        leaks = sorted(set(m.group(0) for m in DE_WORDS.finditer(rendered)))
        umlauts = UMLAUT_RE.findall(rendered)
        if umlauts:
            sample = "".join(sorted(set(umlauts)))
            rep.warned(f"B6  [{slug}] Umlaute im sichtbaren Text ({sample}) "
                       f"-> wahrscheinlich untranslated")
        if leaks:
            rep.warned(f"B6  [{slug}] dt. Woerter im Text: "
                       f"{', '.join(leaks[:6])}{' ...' if len(leaks) > 6 else ''}")

        # B6b - sichtbare Attribute (aria-label/title/placeholder/alt)
        # Scripts strippen: dt. Literale in JS-Buildern sind Source-Defaults
        # (via SA.i18n.t zur Laufzeit uebersetzt), keine statischen Defekte.
        attr_de = []
        for val in VISIBLE_ATTR_RE.findall(_strip_noise(doc)):
            uval = html.unescape(val)   # &auml; etc. aufloesen, sonst uebersehen
            if UMLAUT_RE.search(uval) or DE_WORDS.search(uval):
                attr_de.append(uval.strip())
        if attr_de:
            rep.warned(f"B6  [{slug}] deutsche sichtbare Attribute "
                       f"(aria-label/title/...): \"{attr_de[0][:50]}\""
                       f"{f' (+{len(attr_de)-1})' if len(attr_de) > 1 else ''}")

        # B7 - SEO-Head: Meta/og/twitter muessen EN sein (nicht JS-abhaengig),
        #      og:url/canonical muessen auf /en/ zeigen. Crawler ohne JS sehen NUR das.
        seo_issues = []
        for prop in ('name="description"', 'property="og:title"',
                     'property="og:description"', 'name="twitter:title"',
                     'name="twitter:description"'):
            m = re.search(prop + r'[^>]*?content="([^"]*)"', doc) or \
                re.search(r'content="([^"]*)"[^>]*?' + prop, doc)
            if m and (UMLAUT_RE.search(m.group(1)) or DE_WORDS.search(m.group(1))):
                tag = prop.split('"')[1]
                seo_issues.append(f"{tag} noch deutsch")
        ogurl = re.search(r'property="og:url"[^>]*?content="([^"]+)"', doc)
        if ogurl and "/en/" not in ogurl.group(1):
            seo_issues.append("og:url zeigt nicht auf /en/")
        for issue in seo_issues:
            rep.failed(f"B7  [{slug}] SEO-Head: {issue}")

        # B8 - JSON-LD Structured Data nicht deutsch (erscheint in Rich Results)
        jsonld_de = False
        de_jsonld = re.compile(r'[äöüßÄÖÜ]|\b(saisonale|Boersen\w*|Boerse|verf[uü]gbar|'
                               r'wiederkehrende|unterst[uü]tzt|Schoenheit|Rauschen|'
                               r'Marktdaten|Basiswerte)\b', re.I)
        for jb in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                             doc, re.S):
            try:
                txt = json.dumps(json.loads(jb), ensure_ascii=False)
            except Exception:
                txt = html.unescape(jb)
            if de_jsonld.search(txt):
                rep.failed(f"B8  [{slug}] JSON-LD enthaelt Deutsch (Rich Results)")
                jsonld_de = True
                break

        if not (miss_static or umlauts or leaks or attr_de or seo_issues or jsonld_de):
            rep.ok(f"B*  [{slug}] sauber (SEO-Head + EN-Texte + kein Deutsch)")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="EN-Lokalisierung verifizieren")
    ap.add_argument("--sources-only", action="store_true")
    ap.add_argument("--build-only",   action="store_true")
    ap.add_argument("--build-dir",    default=str(LANDING / "en"))
    ap.add_argument("--only",         help="nur diesen Slug pruefen (Iteration)")
    ap.add_argument("--strict",       action="store_true",
                    help="WARN als FAIL werten (CI)")
    args = ap.parse_args()

    rep   = Report(strict=args.strict)
    pages = expected_pages()
    if args.only:
        pages = {k: v for k, v in pages.items() if k == args.only}
    en    = load_json(I18N / "en.json")
    de    = load_json(I18N / "de.json")

    print(f"EN-Verifizierung | {len(pages)} erwartete Pages | "
          f"{len(en)} en.json-Keys | de.json: {'ja' if de else 'nein'}")
    if not en:
        print("  [FAIL] en.json nicht gefunden/leer - Abbruch")
        sys.exit(1)

    if not args.build_only:
        phase_a(rep, pages, en, de)
    if not args.sources_only:
        phase_b(rep, pages, en, de, Path(args.build_dir))

    rep.section("ERGEBNIS")
    print(f"  FAIL: {rep.fail}   WARN: {rep.warn}   "
          f"-> {'BESTANDEN' if rep.exit_code == 0 else 'FEHLGESCHLAGEN'}")
    sys.exit(rep.exit_code)


if __name__ == "__main__":
    main()
