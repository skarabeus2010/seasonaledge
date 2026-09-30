"""
shared/seo_basis.py — gemeinsame Regeln für alles, was Suchmaschinen lesen.

Eine Quelle für: sichere JSON-LD-Serialisierung, Veröffentlichungs- und
Indexierbarkeitsregeln des Blogs, die Liste der Seiten mit EN-Fassung und die
Zahl der Basiswerte. Genutzt von blog/blog_builder.py, seo/programmatic_seo_builder.py,
landing/build_en.py und scripts/verify_seo_html.py.

Hintergrund (SEO-Review 2026-09-30, docs/SEO_UMSETZUNGSPLAN_2026-09.md): Sitemap,
Blog-Build und hreflang wandten je eigene Regeln an. Die Sitemap nahm z. B. jede
Seite als zweisprachig an (sechs URLs lieferten 404/301), zählte fehlenden Status
als „veröffentlicht" (der Blog-Build als Entwurf) und nahm `noindex`-Seiten auf.

Nur Standardbibliothek + PyYAML: läuft auch mit dem System-Python des Hosts.
"""
from __future__ import annotations

import json
from html.parser import HTMLParser
import re
from datetime import date, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE_URL = "https://seasonalpha.ai"
I18N_JS = REPO / "landing" / "js" / "i18n.js"
BLOG_POSTS_DE = REPO / "blog" / "posts"
BLOG_POSTS_EN = REPO / "blog" / "posts" / "en"


# ── JSON-LD ─────────────────────────────────────────────────────────────

_LS, _PS = chr(0x2028), chr(0x2029)   # Zeilen-/Absatztrenner: in JSON erlaubt, in JS-Strings nicht
_BS = chr(92)   # Backslash; bewusst ohne Literal, damit kein Werkzeug die Escapes umdeutet
_SCRIPT_ESCAPES = {z: _BS + "u%04x" % ord(z) for z in ("<", ">", "&", _LS, _PS)}


def json_ld(obj) -> str:
    """JSON für einen `<script type="application/ld+json">`-Block.

    Kleiner-als, größer-als und kaufmännisches Und werden als JSON-Unicode-
    Escapes ausgegeben: der Wert bleibt für jeden JSON-Parser identisch, aber ein
    `</script>` im Text kann den Block nicht mehr beenden. Das Ergebnis darf
    danach NICHT noch einmal HTML-maskiert werden (im Jinja-Template als sicher
    markieren).
    """
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return re.sub("[<>&" + _LS + _PS + "]", lambda m: _SCRIPT_ESCAPES[m.group(0)], s)


# ── Blog: Front Matter, Veröffentlichung, Indexierbarkeit ───────────────

def lies_front_matter(pfad: Path) -> tuple[dict, str]:
    """(meta, markdown) einer Blog-Datei. Ohne Front Matter: ({}, text)."""
    import yaml
    text = pfad.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    teile = text.split("---", 2)
    if len(teile) < 3:
        return {}, text
    return (yaml.safe_load(teile[1]) or {}), teile[2].strip()


def _als_datum(wert) -> date | None:
    if wert is None or wert == "":
        return None
    if isinstance(wert, datetime):
        return wert.date()
    if isinstance(wert, date):
        return wert
    return datetime.strptime(str(wert), "%Y-%m-%d").date()


def ist_veroeffentlicht(meta: dict, heute: date | None = None) -> bool:
    """Steuert, ob der Blog-Build die Seite ERZEUGT.

    Fehlender Status zählt als Entwurf (so hielt es der Blog-Build schon immer;
    der Sitemap-Builder zählte ihn als veröffentlicht). `scheduled` gilt ab dem
    `publish_date`; ohne `publish_date` sofort (bisheriges Verhalten).
    """
    if not meta.get("title") or not meta.get("slug"):
        return False
    status = meta.get("status", "draft")
    if status == "published":
        return True
    if status == "scheduled":
        pub = _als_datum(meta.get("publish_date"))
        return pub is None or pub <= (heute or date.today())
    return False


def ist_indexierbar(meta: dict, heute: date | None = None) -> bool:
    """Steuert die Aufnahme in die Sitemaps: veröffentlicht UND nicht `noindex`.

    Veröffentlichte `noindex`-Artikel werden weiter gebaut (mit `noindex, follow`),
    stehen aber in keiner Sitemap.
    """
    return ist_veroeffentlicht(meta, heute) and not meta.get("noindex", False)


class FrontMatterFehler(ValueError):
    pass


def veroeffentlicht_am(meta: dict) -> date:
    """`date` eines Artikels. Fehlt es, scheitert der Build.

    Kein Rückfall auf das Tagesdatum: der liess lastmod/dateModified bei jedem
    Build „neu" erscheinen, ohne dass sich etwas geändert hatte (Codex, 2026-09-30).
    """
    d = _als_datum(meta.get("date"))
    if d is None:
        raise FrontMatterFehler(f"Artikel '{meta.get('slug')}' ohne date im Front Matter")
    return d


def geaendert_am(meta: dict) -> date:
    """Letzte wesentliche Änderung eines Artikels: `updated`, sonst `date`.

    Einheitlich für Sitemap-`lastmod`, JSON-LD `dateModified` und
    `article:modified_time`. Wer einen Artikel inhaltlich überarbeitet, setzt
    `updated:` im Front Matter; Tippfehler-Korrekturen brauchen das nicht.
    """
    return _als_datum(meta.get("updated")) or veroeffentlicht_am(meta)


def blog_artikel(sprache: str, heute: date | None = None) -> list[dict]:
    """Alle veröffentlichten Artikel einer Sprache als Liste von Metadaten.

    Jeder Eintrag: slug, meta, datei, indexierbar, geaendert (date).
    """
    ordner = BLOG_POSTS_EN if sprache == "en" else BLOG_POSTS_DE
    aus = []
    for md in sorted(ordner.glob("*.md")):
        meta, _ = lies_front_matter(md)
        if not ist_veroeffentlicht(meta, heute):
            continue
        aus.append({
            "slug": str(meta["slug"]),
            "meta": meta,
            "datei": md,
            "indexierbar": ist_indexierbar(meta, heute),
            "geaendert": geaendert_am(meta),
        })
    return aus


class SprachzuordnungFehler(ValueError):
    pass


def blog_sprachpaare(heute: date | None = None) -> dict[str, str]:
    """{de_slug: en_slug} für veröffentlichte Paare.

    Wirft `SprachzuordnungFehler`, wenn ein veröffentlichter EN-Artikel per
    `de_slug` auf keinen veröffentlichten DE-Artikel zeigt oder zwei EN-Artikel
    denselben DE-Artikel beanspruchen — sonst entstehen hreflang-Verweise ins
    Leere (drei solche Fälle gefunden am 2026-09-30).
    """
    de = {a["slug"] for a in blog_artikel("de", heute)}
    paare: dict[str, str] = {}
    fehler = []
    for a in blog_artikel("en", heute):
        d = a["meta"].get("de_slug")
        if not d:
            continue
        d = str(d)
        if d not in de:
            fehler.append(f"{a['datei'].name}: de_slug '{d}' ist kein veröffentlichter DE-Artikel")
        elif d in paare:
            fehler.append(f"{a['datei'].name}: de_slug '{d}' schon von /en/blog/{paare[d]}/ belegt")
        else:
            paare[d] = a["slug"]
    if fehler:
        raise SprachzuordnungFehler("; ".join(fehler))
    return paare


def blog_hreflang_ziele(heute: date | None = None) -> tuple[dict[str, str], dict[str, str]]:
    """hreflang-Ziele für Blog-HTML UND Sitemap — dieselbe Regel an beiden Stellen.

    Rückgabe ({de_slug: en_slug}, {en_slug: de_slug}); ein Ziel steht nur drin, wenn
    die Gegenseite veröffentlicht UND indexierbar ist. Sonst verwiese eine
    indexierbare Seite per hreflang auf eine noindex-Seite, während die Sitemap
    den Verweis weglässt (Codex, Runde 2).
    """
    paare = blog_sprachpaare(heute)
    de_idx = {a["slug"] for a in blog_artikel("de", heute) if a["indexierbar"]}
    en_idx = {a["slug"] for a in blog_artikel("en", heute) if a["indexierbar"]}
    de_zu_en = {d: e for d, e in paare.items() if e in en_idx}
    en_zu_de = {e: d for d, e in paare.items() if d in de_idx}
    return de_zu_en, en_zu_de


# ── Landing-Seiten mit EN-Fassung ──────────────────────────────────────

def en_seiten_meta() -> dict[str, tuple[str, str]]:
    """`_EN_PAGE_META` aus landing/js/i18n.js: {slug: (title, desc)}, '/' -> 'index'.

    Einzige Quelle dafür, welche Landing-Seite eine EN-Fassung hat — build_en.py
    rendert genau diese, die Sitemap und die hreflang-Tags richten sich danach.
    """
    txt = I18N_JS.read_text(encoding="utf-8")
    block = re.search(r"_EN_PAGE_META\s*=\s*\{(.*?)\n\s*\};", txt, re.S)
    if not block:
        raise ValueError("_EN_PAGE_META nicht in landing/js/i18n.js gefunden")
    eintrag = re.compile(
        r"'(/[a-z0-9-]*)'\s*:\s*\{\s*"
        r"title:\s*'((?:[^'\\]|\\.)*)'\s*,\s*"
        r"desc:\s*'((?:[^'\\]|\\.)*)'\s*\}", re.S)
    unesc = lambda s: s.replace("\\'", "'").replace('\\"', '"')
    aus = {}
    for pfad, titel, desc in eintrag.findall(block.group(1)):
        aus[pfad.strip("/") or "index"] = (unesc(titel), unesc(desc))
    return aus


# ── Google Fonts im <head> ─────────────────────────────────────────────
# Strukturell per HTMLParser (Codex R2/R3): Attribute mit/ohne Anführungszeichen,
# Kommentare zählen nicht (sind keine Tags), disabled-Links sind unwirksam.


class _KopfTags(HTMLParser):
    """Liste der Ereignisse (link / noscript-Anfang / noscript-Ende / Text) mit Quelloffsets."""

    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        # HTMLParser zählt Zeilen nur an \n (nicht splitlines: \r,   …)
        self._zeilen = [0] + [m.end() for m in re.finditer("\n", text)]
        self._text = text
        self.ereignisse: list[dict] = []
        self._ns_tiefe = 0
        self.feed(text)
        self.close()

    def _idx(self) -> int:
        zeile, spalte = self.getpos()
        return self._zeilen[zeile - 1] + spalte

    def handle_starttag(self, tag, attrs):
        start = self._idx()
        ende = start + len(self.get_starttag_text() or "")
        if tag == "noscript":
            self._ns_tiefe += 1
            self.ereignisse.append({"typ": "ns_an", "start": start, "ende": ende})
        elif tag == "link":
            self.ereignisse.append({"typ": "link", "start": start, "ende": ende, "im_ns": self._ns_tiefe > 0,
                                    "at": {k.lower(): (v or "") for k, v in attrs}})

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag == "noscript" and self._ns_tiefe:
            self._ns_tiefe -= 1
            start = self._idx()
            self.ereignisse.append({"typ": "ns_ab", "start": start, "ende": self._text.index(">", start) + 1})

    def handle_data(self, data):
        if data.strip():
            self.ereignisse.append({"typ": "text", "start": self._idx()})


def aktive_stylesheets(html_teil: str) -> list[str]:
    """href aller aktiven Stylesheet-Links außerhalb von <noscript>, strukturell geparst.
    Ein Link, der z. B. durch ein kaputtes End-Tag verschluckt wurde, fehlt hier (Codex R4)."""
    return [e["at"].get("href", "") for e in _KopfTags(html_teil).ereignisse
            if e["typ"] == "link" and not e["im_ns"] and _ist_stylesheet(e["at"])]


def _ist_stylesheet(at: dict[str, str]) -> bool:
    tokens = at.get("rel", "").lower().split()
    return "stylesheet" in tokens and "alternate" not in tokens and "disabled" not in at


def _medium_wirksam(at: dict[str, str]) -> bool:
    return at.get("media", "").strip().lower() in ("", "all", "screen")


def google_fonts_pruefung(html_teil: str) -> tuple[str | None, list[str]]:
    """Google-Fonts-Einbindung eines HTML-Abschnitts prüfen.

    Rückgabe (Paar, Probleme): Paar = Quelltext des nicht-blockierenden Links
    (rel=stylesheet, media=print, onload) bis zum Ende des direkt folgenden <noscript>,
    oder None, wenn es keins gibt. Probleme: blockierende Einbindung außerhalb von
    <noscript>, fehlendes onload (Fonts würden nie aktiv), fehlender oder unwirksamer
    <noscript>-Fallback (verlangt: aktiver Stylesheet-Link auf dieselbe Font-URL mit
    wirksamem Medium). Keine Fonts ist gültig. (CLAUDE.md: blockierendes Dritt-CSS kann
    Seiten hängen lassen.)
    """
    ev = _KopfTags(html_teil).ereignisse
    paar, probleme = None, []
    for i, e in enumerate(ev):
        if e["typ"] != "link" or e["im_ns"]:
            continue
        at = e["at"]
        if "fonts.googleapis.com" not in at.get("href", "") or not _ist_stylesheet(at):
            continue
        if at.get("media", "").strip().lower() != "print":
            probleme.append(f"render-blockierendes Google-Fonts-Stylesheet: {html_teil[e['start']:e['ende']][:80]}")
            continue
        if "onload" not in at:
            probleme.append("Google-Fonts-Link mit media=print ohne onload (Fonts würden nie aktiv)")
            continue
        wirksam, ns_ende = False, None
        if i + 1 < len(ev) and ev[i + 1]["typ"] == "ns_an":
            for f in ev[i + 2:]:
                if f["typ"] == "ns_ab":
                    ns_ende = f["ende"]
                    break
                if (f["typ"] == "link" and _ist_stylesheet(f["at"])
                        and f["at"].get("href") == at["href"] and _medium_wirksam(f["at"])):
                    wirksam = True
        if not wirksam or ns_ende is None:
            probleme.append("nicht-blockierender Google-Fonts-Link ohne wirksamen <noscript>-Fallback")
            continue
        if paar is None:
            paar = html_teil[e["start"]:ns_ende]
    return paar, probleme


def schema_knoten(obj) -> list[dict]:
    """Schema-Knoten eines JSON-LD-Blocks: oberste Objekte, Listen und @graph-Mitglieder."""
    aus = []
    if isinstance(obj, list):
        for x in obj:
            aus += schema_knoten(x)
    elif isinstance(obj, dict):
        if "@graph" in obj:
            aus += schema_knoten(obj["@graph"])
        if "@type" in obj:
            aus.append(obj)
    return aus


def schema_typen(knoten: dict) -> list[str]:
    t = knoten.get("@type")
    return [t] if isinstance(t, str) else list(t or [])


# ── Kennzahlen ─────────────────────────────────────────────────────────

def anzahl_basiswerte() -> int:
    """Zahl der Basiswerte (shared/symbols.py = einzige Quelle der Wahrheit)."""
    from shared.symbols import SYMBOLS
    return len(SYMBOLS)
