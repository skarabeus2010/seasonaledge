#!/usr/bin/env python3
"""
verify_seo_html.py — prüft die GEBAUTEN Seiten und die Sitemap (SEO-Review 2026-09-30).

Läuft im Deploy nach allen Builds (Host-Python, nur Standardbibliothek + PyYAML):

    python3 scripts/verify_seo_html.py            # gebaute Dateien + seo/output/sitemap.xml
    python3 scripts/verify_seo_html.py --live     # zusätzlich jede Sitemap-URL live: 200 ohne Redirect

Prüfungen (Plan: docs/SEO_UMSETZUNGSPLAN_2026-09.md, 1e):
  1. Zuordnung öffentliche URL -> Artefakt: jede Sitemap-URL hat eine gebaute Datei
     (fehlende Seite = Fehler, nicht „übersprungen").
  2. Die geschriebene sitemap.xml entspricht genau sitemap_eintraege() und ist gültiges XML.
  3. Syntax in ALLEN Artefakten: keine Fremdattribute in <meta> (Symptom eines
     ungeschützten Anführungszeichens), jeder JSON-LD-Block parsebar.
  4. Werte: Blog-Artikel tragen die Beschreibung/den Titel aus dem Front Matter
     dekodiert unverändert in description, og:description, twitter:description und
     im BlogPosting; EN-Landing-Seiten die Beschreibung aus _EN_PAGE_META.
  5. Nach Seitentyp: indexierbare Seiten (= in der Sitemap) haben Canonical = eigene
     URL, kein noindex, und jedes hreflang-Ziel ist selbst eine Sitemap-URL.
     Farbvorschauen und embed.html sind ausdrücklich ausgenommen (kein Canonical,
     nicht in der Sitemap).

Exit 0 = alles grün, 1 = mindestens ein Fehler.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "seo"))

from shared.seo_basis import (BASE_URL, blog_artikel, en_seiten_meta,  # noqa: E402
                               geaendert_am, veroeffentlicht_am)

AUSGENOMMEN = {"colorscheme-preview.html", "colorscheme-v2-futuristic.html",
               "colorscheme-v3-ultra.html", "embed.html"}
META_ATTRS = {"name", "property", "content", "charset", "http-equiv", "itemprop", "media"}


class Seite(HTMLParser):
    """Liest Meta-Tags, Links, JSON-LD und <title> einer Seite."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metas: list[list[tuple[str, str | None]]] = []
        self.canonical: list[str] = []
        self.hreflang: list[tuple[str, str]] = []
        self.ld_roh: list[str] = []
        self.titel = ""
        self._ld = False
        self._titel = False
        self._buf = ""

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "meta":
            self.metas.append(attrs)
        elif tag == "link" and d.get("rel") == "canonical":
            self.canonical.append(d.get("href") or "")
        elif tag == "link" and d.get("rel") == "alternate" and d.get("hreflang"):
            self.hreflang.append((d["hreflang"], d.get("href") or ""))
        elif tag == "script" and d.get("type") == "application/ld+json":
            self._ld, self._buf = True, ""
        elif tag == "title":
            self._titel = True

    def handle_endtag(self, tag):
        if tag == "script" and self._ld:
            self.ld_roh.append(self._buf)
            self._ld = False
        elif tag == "title":
            self._titel = False

    def handle_data(self, data):
        if self._ld:
            self._buf += data
        elif self._titel:
            self.titel += data

    def meta(self, schluessel: str) -> str | None:
        for attrs in self.metas:
            d = dict(attrs)
            if d.get("name") == schluessel or d.get("property") == schluessel:
                return d.get("content")
        return None

    def robots(self) -> str:
        return (self.meta("robots") or "").lower()


def lies(pfad: Path) -> Seite:
    s = Seite()
    s.feed(pfad.read_text(encoding="utf-8", errors="replace"))
    return s


def artefakt(url: str) -> Path | None:
    """Öffentliche URL -> gebaute Datei (entspricht deploy/nginx.conf)."""
    pfad = url[len(BASE_URL):]
    if pfad in ("", "/"):
        return REPO / "landing" / "index.html"
    if pfad == "/en/":
        return REPO / "landing" / "en" / "index.html"
    if pfad.startswith("/en/blog/"):
        return REPO / "blog" / "output" / "en" / pfad[len("/en/blog/"):] / "index.html"
    if pfad.startswith("/blog/"):
        return REPO / "blog" / "output" / pfad[len("/blog/"):] / "index.html"
    if pfad == "/disclaimer":
        return REPO / "seo" / "output" / "disclaimer.html"
    if pfad.startswith("/tools/"):
        return REPO / "seo" / "tools" / (pfad[len("/tools/"):] + ".html")
    if pfad.startswith("/en/"):
        return REPO / "landing" / "en" / (pfad[len("/en/"):] + ".html")
    slug = pfad.strip("/")
    if slug in ("ueber-uns", "rechtliches"):
        return REPO / "landing" / f"{slug}.html"
    return REPO / "landing" / "pages" / f"{slug}.html"


def pflicht_artefakte(sitemap_urls: list[str]) -> dict[Path, str]:
    """Dateien, die nach einem vollständigen Build existieren MÜSSEN — unabhängig davon,
    ob sie in der Sitemap stehen (auch veröffentlichte noindex-Seiten, der Disclaimer,
    EN-Seiten mit noindex). Fehlt eine, ist das ein Fehler, kein Überspringen.
    """
    pflicht: dict[Path, str] = {}
    for url in sitemap_urls:
        pfad = artefakt(url)
        if pfad is not None:
            pflicht[pfad] = f"Sitemap-URL {url}"
    for sprache, basis in (("de", REPO / "blog" / "output"), ("en", REPO / "blog" / "output" / "en")):
        for a in blog_artikel(sprache):
            pflicht[basis / a["slug"] / "index.html"] = f"veröffentlichter Artikel ({sprache})"
        for kat in ("", "education/", "marktausblick/", "tutorials/"):
            pflicht[basis / kat / "index.html"] = f"Blog-Übersicht {sprache} /{kat}"
    en_meta = en_seiten_meta()
    for slug in en_meta:
        from shared.seo_basis import en_slug as _en_slug
        pflicht[REPO / "landing" / "en" / f"{_en_slug(slug)}.html"] =             "EN-Seite laut _EN_PAGE_META"
    # DE-Seiten aus unabhängigen Quellen (nicht aus dem Dateibestand, nicht aus der
    # Sitemap): jede EN-Seite braucht ihre DE-Quelle, und jedes Ziel aus Navigation
    # und Footer muss existieren — auch noindex-Seiten wie /kalender, /profile.
    import re as _re
    for slug in en_meta:
        pflicht[artefakt(BASE_URL + ("/" if slug == "index" else f"/{slug}"))] = "DE-Quelle einer EN-Seite"
    for komp in ("nav.html", "footer.html"):
        txt = (REPO / "landing" / "components" / komp).read_text(encoding="utf-8")
        for slug in set(_re.findall(r'href="/([a-z0-9-]+)"', txt)):
            pflicht[artefakt(f"{BASE_URL}/{slug}")] = f"verlinkt in components/{komp}"
    for rel in ("landing/index.html", "landing/ueber-uns.html", "landing/rechtliches.html",
                "seo/output/disclaimer.html", "seo/tools/trading-day-converter.html"):
        pflicht[REPO / rel] = "feste Seite"
    return pflicht


def alle_artefakte() -> list[Path]:
    """Jede vorhandene ausgelieferte HTML-Datei (Syntax für alle)."""
    dateien = list((REPO / "landing").glob("*.html"))
    dateien += list((REPO / "landing" / "pages").glob("*.html"))
    dateien += list((REPO / "landing" / "en").glob("*.html"))
    dateien += list((REPO / "blog" / "output").rglob("index.html"))
    dateien += [REPO / "seo" / "output" / "disclaimer.html"]
    dateien += list((REPO / "seo" / "tools").glob("*.html"))
    return sorted(set(p for p in dateien if p.exists()))


SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML_NS = "http://www.w3.org/1999/xhtml"


def sitemap_ist(pfad: Path) -> tuple[list[dict] | None, str | None]:
    """Geschriebene sitemap.xml -> Einträge im Format von sitemap_eintraege(), oder Fehlertext."""
    import xml.etree.ElementTree as ET
    try:
        wurzel = ET.parse(pfad).getroot()
    except ET.ParseError as e:
        return None, f"sitemap.xml ungültiges XML: {e}"
    if wurzel.tag != f"{{{SITEMAP_NS}}}urlset":
        return None, f"sitemap.xml: Wurzel {wurzel.tag} statt urlset im Sitemap-Namespace"
    ns = {"s": SITEMAP_NS, "x": XHTML_NS}
    aus = []
    for u in wurzel.findall("s:url", ns):
        aus.append({
            "loc": u.findtext("s:loc", namespaces=ns),
            "lastmod": u.findtext("s:lastmod", namespaces=ns),
            "alternates": [(l.get("hreflang"), l.get("href")) for l in u.findall("x:link", ns)],
        })
    return aus, None


def pruefe(live: bool) -> list[str]:
    import programmatic_seo_builder as builder  # seo/, liefert die erwarteten URLs
    fehler: list[str] = []
    # EN-Adressen eindeutig (_EN_SLUGS, Codex EN-Slugs R1)
    from shared.seo_basis import pruefe_en_slugs
    fehler += [f"landing/js/i18n.js: {x}" for x in pruefe_en_slugs(en_seiten_meta())]

    # 1 + 2: Sitemap-Soll gegen geschriebene Datei und gegen gebaute Artefakte
    soll = builder.sitemap_eintraege()
    soll_urls = [e["loc"] for e in soll]
    sitemap = REPO / "seo" / "output" / "sitemap.xml"
    if not sitemap.exists():
        fehler.append("seo/output/sitemap.xml fehlt")
    else:
        ist, problem = sitemap_ist(sitemap)
        if problem:
            fehler.append(problem)
        else:
            # Vollständiger Vergleich, auch bei leerer Liste: URL-Folge, lastmod, hreflang
            ist_urls = [e["loc"] for e in ist]
            if ist_urls != soll_urls:
                fehlt = sorted(set(soll_urls) - set(ist_urls))
                extra = sorted(set(ist_urls) - set(soll_urls))
                fehler.append(f"sitemap.xml weicht vom Soll ab ({len(ist_urls)} statt {len(soll_urls)} URLs; "
                              f"fehlt {fehlt[:3]}, zu viel {extra[:3]})")
            else:
                for e_ist, e_soll in zip(ist, soll):
                    if e_ist["lastmod"] != e_soll["lastmod"]:
                        fehler.append(f"sitemap.xml {e_soll['loc']}: lastmod {e_ist['lastmod']} statt {e_soll['lastmod']}")
                    if e_ist["alternates"] != e_soll["alternates"]:
                        fehler.append(f"sitemap.xml {e_soll['loc']}: hreflang weicht vom Soll ab")
    sitemap_set = set(soll_urls)
    for pfad, grund in pflicht_artefakte(soll_urls).items():
        if not pfad.exists():
            fehler.append(f"{pfad.relative_to(REPO).as_posix()}: fehlt ({grund})")

    # 3: Syntax in allen Artefakten
    geparst: dict[Path, Seite] = {}
    for pfad in alle_artefakte():
        rel = pfad.relative_to(REPO).as_posix()
        s = lies(pfad)
        geparst[pfad] = s
        for attrs in s.metas:
            namen = [k for k, _ in attrs]
            fremd = [k for k in namen if k not in META_ATTRS]
            if fremd and ("name" in namen or "property" in namen):
                d = dict(attrs)
                fehler.append(f"{rel}: <meta {d.get('name') or d.get('property')}> mit Fremdattributen {fremd[:3]}")
        for i, roh in enumerate(s.ld_roh, 1):
            try:
                json.loads(roh)
            except json.JSONDecodeError as e:
                fehler.append(f"{rel}: JSON-LD-Block {i} ungültig ({e.msg}, Zeichen {e.pos})")

    # 4a: Blog-Werte gegen Front Matter
    for sprache, basis in (("de", "blog/output"), ("en", "blog/output/en")):
        for a in blog_artikel(sprache):
            pfad = REPO / basis / a["slug"] / "index.html"
            if pfad not in geparst:
                fehler.append(f"{pfad.relative_to(REPO)}: Artikel gebaut erwartet, fehlt")
                continue
            s, m = geparst[pfad], a["meta"]
            desc, titel = str(m.get("description", "")), str(m["title"])
            for k in ("description", "og:description", "twitter:description"):
                if s.meta(k) != desc:
                    fehler.append(f"{pfad.relative_to(REPO)}: {k} weicht vom Front Matter ab")
            seo_titel = str(m.get("seo_title") or titel)
            erwartet = {
                "<title>": (s.titel.strip(), f"{seo_titel} | SeasonAlpha Blog"),
                "og:title": (s.meta("og:title"), titel),
                "twitter:title": (s.meta("twitter:title"), seo_titel),
                "article:published_time": (s.meta("article:published_time"),
                                           f"{veroeffentlicht_am(m).isoformat()}T08:00:00+02:00"),
                "article:modified_time": (s.meta("article:modified_time"),
                                          f"{geaendert_am(m).isoformat()}T08:00:00+02:00"),
            }
            for feld, (ist_w, soll_w) in erwartet.items():
                if ist_w != soll_w:
                    fehler.append(f"{pfad.relative_to(REPO)}: {feld} {ist_w!r} statt {soll_w!r}")
            posting = [j for j in (json.loads(r) for r in s.ld_roh if _parsebar(r))
                       if isinstance(j, dict) and j.get("@type") == "BlogPosting"]
            if len(posting) != 1:
                fehler.append(f"{pfad.relative_to(REPO)}: {len(posting)} BlogPosting-Blöcke statt 1")
            else:
                bp = posting[0]
                soll_bp = {"description": desc, "headline": titel,
                           "datePublished": erwartet["article:published_time"][1],
                           "dateModified": erwartet["article:modified_time"][1]}
                for k, v in soll_bp.items():
                    if bp.get(k) != v:
                        fehler.append(f"{pfad.relative_to(REPO)}: BlogPosting.{k} {bp.get(k)!r} statt {v!r}")
            erwartet_robots = "noindex" if m.get("noindex") else "index"
            if erwartet_robots not in s.robots():
                fehler.append(f"{pfad.relative_to(REPO)}: robots '{s.robots()}' passt nicht zu noindex={bool(m.get('noindex'))}")

    # 4b: EN-Landing-Seiten gegen _EN_PAGE_META
    for slug, (_titel, desc) in en_seiten_meta().items():
        from shared.seo_basis import en_slug
        pfad = REPO / "landing" / "en" / f"{en_slug(slug)}.html"
        if pfad not in geparst:
            fehler.append(f"landing/en/{pfad.name}: EN-Seite laut _EN_PAGE_META erwartet, fehlt")
            continue
        # HTMLParser dekodiert Attributwerte bereits; ein weiteres unescape würde
        # eine Doppelmaskierung (&amp;amp;) verdecken (Codex, Runde 1).
        if (geparst[pfad].meta("description") or "") != desc:
            fehler.append(f"landing/en/{pfad.name}: description weicht von _EN_PAGE_META ab")

    # 5: Seitentyp-Regeln für indexierbare Seiten (= Sitemap-URLs)
    for url in soll_urls:
        pfad = artefakt(url)
        if pfad is None or pfad not in geparst or pfad.name in AUSGENOMMEN:
            continue
        s, rel = geparst[pfad], pfad.relative_to(REPO).as_posix()
        if "noindex" in s.robots():
            fehler.append(f"{url}: steht in der Sitemap, ist aber noindex")
        if s.canonical != [url]:
            fehler.append(f"{url}: Canonical {s.canonical} statt der eigenen URL")
        for sprache, ziel in s.hreflang:
            if ziel not in sitemap_set:
                fehler.append(f"{url}: hreflang {sprache} -> {ziel} ist keine indexierbare Seite")

    # 6: Kennzahlen gegen den Bestand (Startseite, Pricing, Tour, EN-Texte)
    fehler += pruefe_kennzahlen(soll_urls)

    # 7: interne /en/-Links in allen gebauten Seiten zeigen auf eine existierende Seite
    #    (SEO-Plan 1b, G2: die EN-Startseite verlinkte /en/crash-fruehwarnung und
    #    /en/ueber-uns (404) sowie zwei weiterleitende URLs). Die Laufzeit-Umschreibung
    #    in i18n.js prüft scripts/js/probe_i18n_sprache.js (braucht node, läuft lokal).
    import re as _re
    for pfad, s in geparst.items():
        if pfad.name in AUSGENOMMEN:
            continue
        roh = pfad.read_text(encoding="utf-8", errors="replace")
        for href in sorted(set(_re.findall(r'href="(/en/[^"#?]*)', roh))):
            ziel = artefakt(BASE_URL + href)
            if ziel is None or not ziel.exists():
                fehler.append(f"{pfad.relative_to(REPO).as_posix()}: Link {href} zeigt auf keine gebaute Seite")

    # 9: EN-Köpfe (Serverpfad!) gegen Regeln und DE-Quelle; html lang + OG + hreflang
    #    der indexierbaren DE-Landingseiten; blockierende Fonts auf allen Seiten.
    for slug in en_seiten_meta():
        from shared.seo_basis import en_slug as _en_slug
        en_pfad = REPO / "landing" / "en" / f"{_en_slug(slug)}.html"
        de_pfad = REPO / "landing" / ("index.html" if slug == "index" else f"pages/{slug}.html")
        if en_pfad.exists() and de_pfad.exists():
            fehler += pruefe_en_kopf(slug, en_pfad.read_text(encoding="utf-8"),
                                     de_pfad.read_text(encoding="utf-8"))
    en_meta = en_seiten_meta()
    for url in soll_urls:
        pfad = artefakt(url)
        if pfad is None or not pfad.exists() or "/en/" in url or "/blog/" in url or pfad.name in AUSGENOMMEN:
            continue
        roh = pfad.read_text(encoding="utf-8")
        s = geparst.get(pfad) or lies(pfad)
        rel = pfad.relative_to(REPO).as_posix()
        if not re.search(r'<html\s+lang="de"', roh):
            fehler.append(f"{rel}: <html lang> ist nicht de")
        if s.meta("og:url") not in (url, None) or s.meta("og:url") is None:
            fehler.append(f"{rel}: og:url {s.meta('og:url')!r} statt {url}")
        if s.meta("og:locale") != "de_DE":
            fehler.append(f"{rel}: og:locale {s.meta('og:locale')!r} statt de_DE")
        slug = "index" if url.rstrip("/") == BASE_URL else url.rsplit("/", 1)[1]
        if slug in en_meta:
            from shared.seo_basis import en_url as _en_url
            en_url = _en_url(slug)
            soll = {("de", url), ("en", en_url), ("x-default", url)}
            if set(s.hreflang) != soll:
                fehler.append(f"{rel}: hreflang {sorted(s.hreflang)} statt {sorted(soll)}")
    for pfad in geparst:
        if pfad.name in AUSGENOMMEN:
            continue
        for b in blockierende_fonts(pfad.read_text(encoding="utf-8", errors="replace")):
            fehler.append(f"{pfad.relative_to(REPO).as_posix()}: {b}")

    # 8: robots.txt sperrt nichts, was Google sehen muss
    robots = REPO / "seo" / "output" / "robots.txt"
    if not robots.exists():
        fehler.append("seo/output/robots.txt fehlt")
    else:
        for zeile in robots.read_text(encoding="utf-8").splitlines():
            z = zeile.strip()
            if z.lower().startswith("disallow:") and z.split(":", 1)[1].strip() in ("/analyse/", "/landing/data/"):
                fehler.append(f"robots.txt: '{z}' — Google muss dort 410 bzw. Render-Ressourcen abrufen können")

    # Live-Prüfung
    if live:
        fehler += _live(soll_urls)
    return fehler


KENNZAHL_DATEIEN = ["landing/index.html", "landing/en/index.html", "landing/pages/pricing.html",
                    "landing/i18n/de.json", "landing/i18n/en.json", "landing/js/i18n.js",
                    "landing/js/tour-config.js"]
# Erlaubter Rückstand einer gerundeten Angabe hinter dem Bestand („350+" bei 370).
KENNZAHL_TOLERANZ = {"basiswerte": 60, "tools": 10}
# Angaben, die sich auf eine seitenspezifische Teilmenge beziehen, nicht auf das
# Universum. Nur mit Begründung eintragen.
KENNZAHL_AUSNAHMEN = {
    ("landing/js/i18n.js", "300+ tickers"):
        "/vola-saisonalitaet: eigene Teilmenge (333 Profile in vol_saisonalitaet.json)",
}


def pruefe_kennzahlen(sitemap_urls: list[str]) -> list[str]:
    """Zahlenangaben im Seitentext gegen den Bestand (SEO-Review 2026-09-30).

    Vorher stand „über 500 Basiswerte" (DE) neben „270+ tickers" (EN) bei
    tatsächlich 370, „24 Strategien" bei 22 und „22 Tools" bei 38.
    Gerundete Untergrenzen sind erlaubt, solange sie nicht über dem Bestand und
    nicht mehr als die Toleranz darunter liegen; Strategien müssen exakt stimmen.
    „bis zu"/„up to" vor der Zahl ist eine Obergrenze einer anderen Sache
    (z. B. Watchlist-Limit) und wird übersprungen.
    """
    import re
    from shared.seo_basis import anzahl_basiswerte

    basis = anzahl_basiswerte()
    strat_js = (REPO / "landing" / "js" / "strategy-compute.js").read_text(encoding="utf-8")
    block = re.search(r"SA\.STRATEGIES\s*=\s*\{(.*?)\n\s*\};", strat_js, re.S)
    strategien = len(re.findall(r"^\s*\w+\s*:\s*\{", block.group(1), re.M)) if block else -1
    # Werkzeuge = indexierbare DE-Feature-Seiten (ohne Preis-, Rechts-, Über-uns-Seite)
    tools = sum(1 for u in sitemap_urls
                if u.count("/") == 3 and "/blog/" not in u and "/en/" not in u
                and u.rsplit("/", 1)[1] not in ("", "pricing", "rechtliches", "ueber-uns", "disclaimer"))

    regeln = [
        ("basiswerte", r"(\d{2,4})\s*\+?\s*(?:Basiswerte|Ticker|tickers|Tickers|assets)\b", basis),
        ("tools", r"(\d{2,3})\s*\+?\s*(?:Analyse-Tools|Tools|analysis tools)\b", tools),
        ("strategien", r"(\d{1,3})\s*(?:Strategien|strategies)\b", strategien),
    ]
    fehler = []
    for rel in KENNZAHL_DATEIEN:
        pfad = REPO / rel
        if not pfad.exists():
            continue
        text = html.unescape(pfad.read_text(encoding="utf-8"))
        for art, muster, ist in regeln:
            for m in re.finditer(muster, text):
                davor = text[max(0, m.start() - 12):m.start()].lower()
                if any(w in davor for w in ("bis zu", "up to", "max.", "maximal")):
                    continue
                if (rel, m.group(0)) in KENNZAHL_AUSNAHMEN:
                    continue
                n = int(m.group(1))
                if art == "strategien":
                    ok = n == ist
                else:
                    ok = ist - KENNZAHL_TOLERANZ[art] <= n <= ist
                if not ok:
                    fehler.append(f"{rel}: „{m.group(0)}“ passt nicht zum Bestand ({art}: {ist})")
        # Historie: 131 Jahre gibt es nur für einzelne Reihen (Dow Jones). Allgemein
        # formuliert muss „bis zu"/„up to" davorstehen; in Zeilen über den Dow bzw.
        # den Dekadenzyklus ist die Zahl wörtlich richtig.
        for zeile in text.splitlines():
            for m in re.finditer(r"131\s*(?:Jahre|Jahren|years|Years)", zeile):
                davor = zeile[max(0, m.start() - 12):m.start()].lower()
                if "bis zu" in davor or "up to" in davor:
                    continue
                if re.search(r"Dow|DJI|Dekaden|Decade", zeile):
                    continue
                fehler.append(f"{rel}: „{m.group(0)}“ ohne „bis zu/up to“ (gilt nur für einzelne Reihen)")
    return fehler


# reihenfolgeunabhängig (Codex R1: rel vor href ist genauso gültig)
PRECONNECT = re.compile(r'<link\b[^>]*\brel="preconnect"[^>]*>')


def blockierende_fonts(roh: str) -> list[str]:
    """Probleme der Google-Fonts-Einbindung (blockierend, ohne onload, ohne <noscript>).
    Gemeinsame Regel mit build_en (shared.seo_basis.google_fonts_pruefung)."""
    from shared.seo_basis import google_fonts_pruefung
    kopf = roh.split("</head>", 1)[0]
    return google_fonts_pruefung(kopf)[1]


def pruefe_en_kopf(slug: str, en_roh: str, de_roh: str) -> list[str]:
    """Kopf einer gebauten EN-Seite gegen Regeln und gegen ihre DE-Quelle.

    SEO-Plan „EN-Duplikate" (2026-09-30): auf dem Server trugen alle EN-Seiten das
    deutsche JSON-LD mit DE-URLs, weil build_en.replace_head den Cache-Buster am
    CSS-Link nicht erkannte. Wird auch von scripts/verify_en_serverpfad.py genutzt.
    """
    f: list[str] = []
    from shared.seo_basis import en_slug, en_url as _en_url
    rel = f"landing/en/{en_slug(slug)}.html"
    kanon = _en_url(slug)
    s = Seite()
    s.feed(en_roh)
    if not re.search(r'<html\s+lang="en"', en_roh):
        f.append(f"{rel}: <html lang> ist nicht en")
    if s.canonical != [kanon]:
        f.append(f"{rel}: Canonical {s.canonical} statt {kanon}")
    if s.meta("og:url") != kanon:
        f.append(f"{rel}: og:url {s.meta('og:url')!r} statt {kanon}")
    if s.meta("og:locale") != "en_US":
        f.append(f"{rel}: og:locale {s.meta('og:locale')!r} statt en_US")
    from shared.seo_basis import schema_knoten, schema_typen
    # alle Schema-Knoten, auch in @graph und Listen (Codex R1)
    blocks = [k for r in s.ld_roh if _parsebar(r) for k in schema_knoten(json.loads(r))]
    typen = [t for k in blocks for t in schema_typen(k)]
    if "FAQPage" in typen:
        f.append(f"{rel}: FAQPage auf EN (deutsch, Rich Result abgeschafft)")
    if slug == "index":
        ws = [b for b in blocks if "WebSite" in schema_typen(b)]
        if len(ws) != 1 or ws[0].get("url") != f"{BASE_URL}/en/":
            f.append(f"{rel}: WebSite.url nicht /en/")
        else:
            tpl = (ws[0].get("potentialAction") or {}).get("target", {}).get("urlTemplate", "")
            if not str(tpl).startswith(f"{BASE_URL}/en/dashboard"):
                f.append(f"{rel}: SearchAction.urlTemplate {tpl!r} nicht auf /en/dashboard")
            if not str(ws[0].get("inLanguage", "")).startswith("en"):
                f.append(f"{rel}: WebSite.inLanguage nicht en")
    else:
        wp = [b for b in blocks if "WebPage" in schema_typen(b)]
        bc = [b for b in blocks if "BreadcrumbList" in schema_typen(b)]
        if len(wp) != 1:
            f.append(f"{rel}: {len(wp)} WebPage-Blöcke statt 1")
        elif wp[0].get("url") != kanon or not str(wp[0].get("inLanguage", "")).startswith("en"):
            f.append(f"{rel}: WebPage url={wp[0].get('url')!r} inLanguage={wp[0].get('inLanguage')!r}")
        if len(bc) != 1:
            f.append(f"{rel}: {len(bc)} BreadcrumbList-Blöcke statt 1")
        else:
            items = bc[0].get("itemListElement") or []
            if not items or items[0].get("item") != f"{BASE_URL}/en/" or items[-1].get("item") != kanon:
                f.append(f"{rel}: BreadcrumbList Anfang/Ende nicht /en/ … {kanon}")
    # robots aus der Quelle erhalten
    de = Seite()
    de.feed(de_roh)
    if "noindex" in de.robots() and "noindex" not in s.robots():
        f.append(f"{rel}: noindex der Quelle verloren")
    if "noindex" in s.robots():
        if s.hreflang:
            f.append(f"{rel}: noindex-Seite mit hreflang-Verweisen")
    else:
        de_url = f"{BASE_URL}/" if slug == "index" else f"{BASE_URL}/{slug}"
        soll = {("de", de_url), ("en", kanon), ("x-default", de_url)}
        if set(s.hreflang) != soll:
            f.append(f"{rel}: hreflang {sorted(s.hreflang)} statt {sorted(soll)}")
    # Erhalt gegen die Quelle: CSS-Link (inkl. Cache-Buster), Font-Paar, preconnect
    if slug != "index":
        # strukturell geparst: ein durch kaputtes Markup verschluckter Link fehlt hier (Codex R4)
        from shared.seo_basis import aktive_stylesheets

        def _app_css(roh):
            kopf = roh.split("</head>", 1)[0]
            return [h for h in aktive_stylesheets(kopf) if h.startswith("/landing/css/app.css")]
        de_css, en_css = _app_css(de_roh), _app_css(en_roh)
        if de_css[:1] != en_css[:1]:
            f.append(f"{rel}: CSS-Link {en_css[:1]} statt {de_css[:1]} (Cache-Buster verloren?)")
        from shared.seo_basis import google_fonts_pruefung
        de_font = google_fonts_pruefung(de_roh.split("</head>", 1)[0])[0]
        if de_font and de_font.strip() not in en_roh:
            f.append(f"{rel}: nicht-blockierendes Font-Paar der Quelle fehlt")
        for pc in PRECONNECT.findall(de_roh):
            if pc not in en_roh:
                f.append(f"{rel}: preconnect der Quelle fehlt ({pc[:60]})")
    for b in blockierende_fonts(en_roh):
        f.append(f"{rel}: {b}")
    return f


def _parsebar(roh: str) -> bool:
    try:
        json.loads(roh)
        return True
    except json.JSONDecodeError:
        return False


def _live(urls: list[str]) -> list[str]:
    import urllib.error
    import urllib.request

    class KeinRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(KeinRedirect)
    fehler = []
    for url in urls:
        try:
            with opener.open(urllib.request.Request(url, headers={"User-Agent": "sa-verify-seo"}),
                             timeout=30) as r:
                if r.status != 200:
                    fehler.append(f"LIVE {url}: HTTP {r.status}")
        except urllib.error.HTTPError as e:
            fehler.append(f"LIVE {url}: HTTP {e.code}")
        except Exception as e:  # noqa: BLE001
            fehler.append(f"LIVE {url}: {type(e).__name__} {str(e)[:60]}")
    return fehler


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--live", action="store_true", help="Sitemap-URLs zusätzlich live abrufen")
    args = ap.parse_args()
    fehler = pruefe(args.live)
    for f in fehler:
        print(f"  FEHLER {f}")
    print(f"verify_seo_html: {len(fehler)} Fehler" + (" (inkl. Live)" if args.live else ""))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
