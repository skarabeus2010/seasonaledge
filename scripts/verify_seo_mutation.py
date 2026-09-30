#!/usr/bin/env python3
"""
verify_seo_mutation.py — prüft den WÄCHTER verify_seo_html.py, nicht die Seite.

Baut jede bekannte Fehlerklasse in einer isolierten Kopie des Repos wieder ein und
verlangt, dass der Wächter rot wird. Die Grundkopie ohne Mutation muss grün sein.
Produktive Dateien werden nicht verändert (Lesson v65.1: eine mutierte
Produktionsdatei blieb einmal im Arbeitsbaum liegen).

Voraussetzung: gebaute Artefakte (blog/output, landing/en, seo/output/sitemap.xml).

    py -3.14 scripts/verify_seo_mutation.py
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PWERT_DE = "blog/output/p-wert-erklaert/index.html"
PWERT_EN = "blog/output/en/p-value-explained/index.html"


def kopiere(ziel: Path) -> None:
    """Minimale Repo-Kopie: alles, was Wächter und Sitemap-Builder lesen."""
    ign = shutil.ignore_patterns("__pycache__", "*.pyc", "images", "social", "youtube",
                                 "data", "vendor", "assets")
    for teil in ("shared", "seo", "landing", "blog/posts", "blog/templates"):
        shutil.copytree(REPO / teil, ziel / teil, ignore=ign)
    (ziel / "scripts").mkdir()
    shutil.copy2(REPO / "scripts" / "verify_seo_html.py", ziel / "scripts")
    for f in (REPO / "blog" / "output").rglob("*"):
        if f.is_file() and (f.name == "index.html" or f.suffix == ".xml"):
            if {"images", "social", "youtube"} & set(f.relative_to(REPO).parts):
                continue
            dst = ziel / f.relative_to(REPO)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)


def waechter(wurzel: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(wurzel / "scripts" / "verify_seo_html.py")],
                       cwd=str(wurzel), capture_output=True, text=True, encoding="utf-8",
                       env={**__import__("os").environ, "PYTHONUTF8": "1", "SA_OHNE_DOTENV": "1",
                            "SA_GIT_WURZEL": str(REPO)})
    return r.returncode, (r.stdout + r.stderr)


def ersetze(pfad: Path, alt: str, neu: str) -> None:
    t = pfad.read_text(encoding="utf-8")
    if alt not in t:
        raise SystemExit(f"Mutationsanker fehlt in {pfad}: {alt[:60]!r}")
    pfad.write_text(t.replace(alt, neu, 1), encoding="utf-8")


def ersetze_re(pfad: Path, muster: str, neu, flags=0) -> None:
    t = pfad.read_text(encoding="utf-8")
    t2, n = re.subn(muster, neu, t, count=1, flags=flags)
    if n != 1:
        raise SystemExit(f"Mutationsmuster trifft nicht in {pfad}: {muster[:60]!r}")
    if t2 == t:
        # Eine Mutation, die nichts aendert, prueft nichts (erster Lauf: die
        # Doppelmaskierung traf eine Beschreibung ohne maskierbare Zeichen).
        raise SystemExit(f"Mutation ohne Wirkung in {pfad}: {muster[:60]!r}")
    pfad.write_text(t2, encoding="utf-8")


# ── Mutationen: jede baut eine Fehlerklasse wieder ein, die real vorkam ──────

def m_unmaskierte_description(w: Path):
    """Der Live-Fehler vom 30.09.: Beschreibung roh ins Attribut (DE)."""
    p = w / PWERT_DE
    ersetze_re(p, r'<meta name="description" content="([^"]*)">',
               lambda m: f'<meta name="description" content="{html.unescape(m.group(1))}">')


def m_jsonld_texteinsetzung(w: Path):
    """BlogPosting per Texteinsetzung gebaut (altes Template) — EN."""
    p = w / PWERT_EN
    desc = 'p = 0.127 is not "no effect", p = 0.0050 is not "tradable".'
    ersetze_re(p, r'<script type="application/ld\+json">\{"@context":"https://schema.org","@type":"BlogPosting".*?</script>',
               lambda m: '<script type="application/ld+json">{"@type": "BlogPosting", "description": "'
                         + desc + '"}</script>', re.S)


def m_script_ende_im_jsonld(w: Path):
    """JSON ohne Script-Kontext-Schutz: ein </script> im Text beendet den Block."""
    p = w / PWERT_DE
    roh = json.dumps({"@context": "https://schema.org", "@type": "BlogPosting",
                      "headline": "x", "description": "a </script><b> b"}, ensure_ascii=False)
    ersetze_re(p, r'<script type="application/ld\+json">\{"@context":"https://schema.org","@type":"BlogPosting".*?</script>',
               lambda m: f'<script type="application/ld+json">{roh}</script>', re.S)


def m_doppelt_maskiert(w: Path):
    """Doppelte Maskierung (&amp;amp;): syntaktisch gültig, inhaltlich falsch."""
    p = w / PWERT_DE   # enthaelt Anfuehrungszeichen -> doppelte Maskierung aendert den Wert
    ersetze_re(p, r'<meta property="og:description" content="([^"]*)">',
               lambda m: f'<meta property="og:description" content="{html.escape(m.group(1))}">')


def m_kategorie_canonical(w: Path):
    """Kategorie kanonisch auf die Blog-Startseite (Zustand vor dem Fix)."""
    ersetze(w / "blog/output/education/index.html",
            '<link rel="canonical" href="https://seasonalpha.ai/blog/education/">',
            '<link rel="canonical" href="https://seasonalpha.ai/blog/">')


def m_hreflang_ins_leere(w: Path):
    """DE-Seite verweist auf eine EN-Fassung, die es nicht gibt."""
    ersetze(w / "landing/pages/crash-fruehwarnung.html",
            '<link rel="alternate" hreflang="de" href="https://seasonalpha.ai/crash-fruehwarnung">',
            '<link rel="alternate" hreflang="de" href="https://seasonalpha.ai/crash-fruehwarnung">\n'
            '  <link rel="alternate" hreflang="en" href="https://seasonalpha.ai/en/crash-fruehwarnung">')


def m_gebaute_seite_fehlt(w: Path):
    """Ein Artikel steht in der Sitemap, wurde aber nicht gebaut."""
    (w / PWERT_EN).unlink()


def m_noindex_in_sitemap(w: Path):
    """Seite wird noindex, die geschriebene Sitemap führt sie weiter."""
    ersetze_re(w / "landing/pages/skew.html", r'<meta name="robots" content="[^"]*">',
               '<meta name="robots" content="noindex, follow">')


def m_sitemap_fehlt(w: Path):
    (w / "seo/output/sitemap.xml").unlink()


def m_en_beschreibung(w: Path):
    """EN-Seite trägt eine andere Beschreibung als _EN_PAGE_META."""
    ersetze_re(w / "landing/en/skew.html", r'<meta name="description" content="[^"]*">',
               '<meta name="description" content="Veraltete Beschreibung">')


def m_robots_passt_nicht(w: Path):
    """noindex-Artikel wird mit index ausgeliefert."""
    ersetze(w / "blog/output/willkommen-bei-seasonalpha.ai/index.html",
            '<meta name="robots" content="noindex, follow">',
            '<meta name="robots" content="index, follow">')


def m_kennzahl_veraltet(w: Path):
    """Veraltete Universums-Zahl zurück auf der Startseite (270+ statt 350+)."""
    ersetze(w / "landing/index.html", "350+ Ticker", "270+ Ticker")


def m_strategien_falsch(w: Path):
    """Falsche Strategie-Zahl (24 statt 22) in der EN-Übersetzung."""
    ersetze(w / "landing/i18n/en.json", "walk-forward for 22 strategies", "walk-forward for 24 strategies")


def m_sitemap_leer(w: Path):
    """Leeres urlset (Codex R1: bestand vorher die Prüfung)."""
    (w / "seo/output/sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>' + chr(10)
        + '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>' + chr(10),
        encoding="utf-8")


def m_sitemap_falsche_wurzel(w: Path):
    (w / "seo/output/sitemap.xml").write_text("<kaputt/>", encoding="utf-8")


def m_sitemap_ohne_lastmod(w: Path):
    ersetze_re(w / "seo/output/sitemap.xml", r"\s*<lastmod>[^<]*</lastmod>", "")


def m_sitemap_ohne_hreflang(w: Path):
    ersetze_re(w / "seo/output/sitemap.xml", r'\s*<xhtml:link rel="alternate" hreflang="en"[^>]*/>', "")


def m_disclaimer_fehlt(w: Path):
    """Pflichtseite ausserhalb der Sitemap fehlt (Codex R1: wurde ausgefiltert)."""
    (w / "seo/output/disclaimer.html").unlink()


def m_noindex_artikel_fehlt(w: Path):
    (w / "blog/output/en/welcome-to-seasonalpha/index.html").unlink()


def m_en_doppelt_maskiert(w: Path):
    """Doppelmaskierung auf einer EN-Seite (Codex R1: vom zusätzlichen unescape verdeckt)."""
    ersetze_re(w / "landing/en/index.html", r'<meta name="description" content="([^"]*)">',
               lambda m: f'<meta name="description" content="{html.escape(m.group(1))}">')


def m_historie_ohne_bis_zu(w: Path):
    ersetze(w / "landing/js/i18n.js", "with up to 131 Years of Data", "with 131 Years of Data")


def m_noindex_de_seite_fehlt(w: Path):
    """noindex-Seite aus der Navigation fehlt (Codex R2: blieb unbemerkt)."""
    (w / "landing/pages/kalender.html").unlink()


def m_profil_fehlt(w: Path):
    (w / "landing/pages/profile.html").unlink()


def m_titel_falsch(w: Path):
    ersetze_re(w / PWERT_DE, r"<title>[^<]*</title>", "<title>Falscher Titel | SeasonAlpha Blog</title>")


def m_og_titel_falsch(w: Path):
    ersetze_re(w / PWERT_EN, r'<meta property="og:title" content="[^"]*">',
               '<meta property="og:title" content="Falscher Titel">')


def m_date_modified_falsch(w: Path):
    ersetze_re(w / PWERT_DE, r'"dateModified":"[^"]*"', '"dateModified":"2031-01-01T08:00:00+02:00"')


def m_modified_time_falsch(w: Path):
    ersetze_re(w / PWERT_EN, r'<meta property="article:modified_time" content="[^"]*">',
               '<meta property="article:modified_time" content="2031-01-01T08:00:00+02:00">')


def m_hreflang_auf_noindex(w: Path):
    """Indexierbare Seite verweist per hreflang auf einen noindex-Artikel."""
    ersetze_re(w / PWERT_DE, r'<link rel="alternate" hreflang="en" href="[^"]*">',
               '<link rel="alternate" hreflang="en" href="https://seasonalpha.ai/en/blog/welcome-to-seasonalpha/">')


def pruefe_hreflang_regel() -> bool:
    """blog_hreflang_ziele: ein einseitig noindex gesetztes Paar darf kein Ziel sein."""
    import shared.seo_basis as sb
    with tempfile.TemporaryDirectory() as t:
        de, en = Path(t) / "de", Path(t) / "de" / "en"
        en.mkdir(parents=True)
        def post(ordner, slug, extra=""):
            (ordner / f"{slug}.md").write_text(
                f"---{chr(10)}title: T{chr(10)}slug: {slug}{chr(10)}date: 2026-09-01{chr(10)}"
                f"status: published{chr(10)}{extra}---{chr(10)}text{chr(10)}", encoding="utf-8")
        post(de, "a"); post(en, "a-en", f"de_slug: a{chr(10)}")                         # beide indexierbar
        post(de, "b"); post(en, "b-en", f"de_slug: b{chr(10)}noindex: true{chr(10)}")    # nur EN noindex
        post(de, "c", f"noindex: true{chr(10)}"); post(en, "c-en", f"de_slug: c{chr(10)}")  # nur DE noindex
        alt = sb.BLOG_POSTS_DE, sb.BLOG_POSTS_EN
        sb.BLOG_POSTS_DE, sb.BLOG_POSTS_EN = de, en
        try:
            de_zu_en, en_zu_de = sb.blog_hreflang_ziele()
        finally:
            sb.BLOG_POSTS_DE, sb.BLOG_POSTS_EN = alt
    ok = de_zu_en == {"a": "a-en", "c": "c-en"} and en_zu_de == {"a-en": "a", "b-en": "b"}
    print(f"  {'gefangen ' if ok else 'VERFEHLT'}  hreflang-Regel (einseitig noindex)  {de_zu_en} {en_zu_de}")
    return ok


MUTATIONEN = [m_noindex_de_seite_fehlt, m_profil_fehlt, m_titel_falsch, m_og_titel_falsch,
              m_date_modified_falsch, m_modified_time_falsch, m_hreflang_auf_noindex, m_sitemap_leer, m_sitemap_falsche_wurzel, m_sitemap_ohne_lastmod,
              m_sitemap_ohne_hreflang, m_disclaimer_fehlt, m_noindex_artikel_fehlt,
              m_en_doppelt_maskiert, m_historie_ohne_bis_zu, m_kennzahl_veraltet, m_strategien_falsch, m_unmaskierte_description, m_jsonld_texteinsetzung, m_script_ende_im_jsonld,
              m_doppelt_maskiert, m_kategorie_canonical, m_hreflang_ins_leere,
              m_gebaute_seite_fehlt, m_noindex_in_sitemap, m_sitemap_fehlt,
              m_en_beschreibung, m_robots_passt_nicht]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sa-seo-mut-") as tmp:
        basis = Path(tmp) / "basis"
        kopiere(basis)
        rc, out = waechter(basis)
        if rc != 0:
            print("GRUNDKOPIE NICHT GRÜN — Test nicht aussagekräftig:\n" + out[-2000:])
            return 2
        print("Grundkopie: grün")
        verfehlt = []
        for m in MUTATIONEN:
            w = Path(tmp) / m.__name__
            shutil.copytree(basis, w)
            m(w)
            rc, out = waechter(w)
            gefangen = rc != 0
            zeile = next((l.strip() for l in out.splitlines() if "FEHLER" in l), "")
            print(f"  {'gefangen ' if gefangen else 'VERFEHLT'}  {m.__name__:28} {zeile[:110]}")
            if not gefangen:
                verfehlt.append(m.__name__)
            shutil.rmtree(w, ignore_errors=True)
        print(f"{len(MUTATIONEN) - len(verfehlt)}/{len(MUTATIONEN)} Mutationen gefangen")
        sys.path.insert(0, str(REPO))
        regel_ok = pruefe_hreflang_regel()
        return 1 if verfehlt or not regel_ok else 0


if __name__ == "__main__":
    sys.exit(main())
