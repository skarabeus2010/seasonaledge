#!/usr/bin/env python3
"""
verify_en_serverpfad.py — baut die EN-Seiten so, wie es der Server tut, und prüft sie.

Hintergrund (2026-09-30): auf dem Server läuft deploy/inject_credentials.sh VOR
landing/build_en.py und hängt `?v=<sha>` an alle CSS/JS-Links. Die Kopf-Regex in
build_en.replace_head verlangte den CSS-Link ohne Query — lokal griff sie, auf dem
Server nie. Folge: alle EN-Seiten trugen deutsches JSON-LD mit DE-URLs (GSC: 18
EN-Seiten als „Duplikat"). Kein lokaler Test konnte das sehen, weil lokal der
Cache-Buster fehlt. Dieser Test stellt den Serverpfad nach.

    py -3.14 scripts/verify_en_serverpfad.py                 # aktueller build_en.py
    py -3.14 scripts/verify_en_serverpfad.py --code <datei>  # anderer Stand (muss rot sein)
    py -3.14 scripts/verify_en_serverpfad.py --mutationen    # zusätzlich Mutationen am Ergebnis + Quellfälle

Exit 0 = grün.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
from verify_seo_html import pruefe_en_kopf  # noqa: E402
from shared.seo_basis import en_seiten_meta  # noqa: E402

CACHE_BUST = re.compile(r"(/landing/(css|js)/[a-zA-Z0-9_./-]+\.(css|js))(\?v=[a-zA-Z0-9]+)?")


def baue(code: Path, ziel: Path) -> dict[str, str]:
    """Kopie von landing/ mit Cache-Buster wie inject_credentials.sh, dann build_page für alle Seiten.
    Rückgabe {slug: Fehlertext} für Seiten, deren Build abbricht."""
    ign = shutil.ignore_patterns("data", "assets", "vendor", "en")
    shutil.copytree(REPO / "landing", ziel / "landing", ignore=ign)
    for html_datei in (ziel / "landing").rglob("*.html"):
        t = html_datei.read_text(encoding="utf-8")
        html_datei.write_text(CACHE_BUST.sub(lambda m: m.group(1) + "?v=test", t), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("build_en_test", code)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    lz = ziel / "landing"
    mod.LANDING, mod.PAGES, mod.OUT = lz, lz / "pages", lz / "en"
    # Pfade, die ältere Stände aus dem eigenen Dateiort ableiten (Datei liegt ggf. im Temp)
    mod.I18N, mod.I18N_JS, mod.REPO = lz / "i18n", lz / "js" / "i18n.js", REPO
    abbrueche = {}
    en = mod.load_en()
    for slug, (titel, desc) in en_seiten_meta().items():
        try:
            mod.build_page(slug, titel, desc, en, True)
        except Exception as e:  # noqa: BLE001
            abbrueche[slug] = f"{type(e).__name__}: {e}"
    return abbrueche


def pruefe(ziel: Path) -> list[str]:
    fehler = []
    for slug in en_seiten_meta():
        from shared.seo_basis import en_slug
        en = ziel / "landing" / "en" / f"{en_slug(slug)}.html"
        de = ziel / "landing" / ("index.html" if slug == "index" else f"pages/{slug}.html")
        if not en.exists():
            fehler.append(f"{slug}: EN-Seite nicht gebaut")
            continue
        fehler += pruefe_en_kopf(slug, en.read_text(encoding="utf-8"), de.read_text(encoding="utf-8"))
    return fehler


def _sub(pfad: Path, muster: str, neu: str, flags=0):
    t = pfad.read_text(encoding="utf-8")
    t2, n = re.subn(muster, neu, t, count=1, flags=flags)
    if n != 1 or t2 == t:
        raise SystemExit(f"Mutation ohne Wirkung: {pfad.name} {muster[:50]}")
    pfad.write_text(t2, encoding="utf-8")


MUTATIONEN = {
    "Cache-Buster entfernt": lambda e: _sub(e / "scanner.html", r'app\.css\?v=test"', 'app.css"'),
    "Font-Paar entfernt": lambda e: _sub(e / "scanner.html", r'<link\s+href="https://fonts[^>]*media="print"[^>]*>\s*<noscript>.*?</noscript>', "", re.S),
    "blockierende Fonts": lambda e: _sub(e / "skew.html", r"</head>", '<link href="https://fonts.googleapis.com/css2?family=X" rel="stylesheet"></head>'),
    "WebPage gelöscht": lambda e: _sub(e / "scanner.html", r'<script type="application/ld\+json">\{"@context":"https://schema.org","@type":"WebPage".*?</script>', "", re.S),
    "WebPage.url DE": lambda e: _sub(e / "dashboard.html", r'"url":"https://seasonalpha\.ai/en/dashboard"', '"url":"https://seasonalpha.ai/dashboard"'),
    "noindex verloren": lambda e: _sub(e / "profile.html", r'<meta name="robots" content="[^"]*"', '<meta name="robots" content="index, follow"'),
    "hreflang fehlt": lambda e: _sub(e / "opex.html", r'\s*<link rel="alternate" hreflang="en"[^>]*>', ""),
    "urlTemplate DE": lambda e: _sub(e / "index.html", r'"urlTemplate":"https://seasonalpha\.ai/en/dashboard', '"urlTemplate":"https://seasonalpha.ai/dashboard'),
    # Codex R1: unvollständige Font-Einbindung und Schema-Knoten in @graph
    "Font ohne onload": lambda e: _sub(e / "scanner.html", r'\s+onload="[^"]*"', ""),
    "Font ohne noscript": lambda e: _sub(e / "scanner.html", r"<noscript><link href=\"https://fonts[^<]*</noscript>", ""),
    "FAQPage in @graph": lambda e: _sub(e / "opex.html", r"</head>", '<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"FAQPage","mainEntity":[]}]}</script></head>'),
    # Codex R2: Fallback ohne wirksamen Stylesheet-Link
    "noscript-Link ohne rel": lambda e: _sub(e / "scanner.html", r'(<noscript><link href="https://fonts[^"]*") rel="stylesheet"', r"\g<1>"),
    # Codex R4: abgeschnittenes End-Tag verschluckt den folgenden app.css-Link
    "app.css verschluckt": lambda e: _sub(e / "scanner.html", r"</noscript>(\s*<link rel=\"stylesheet\" href=\"/landing/css/app)", r"</noscript\g<1>"),
    "zweites WebPage in @graph": lambda e: _sub(e / "opex.html", r"</head>", '<script type="application/ld+json">{"@graph":[{"@type":"WebPage","url":"https://seasonalpha.ai/opex"}]}</script></head>'),
}


def _quelle(pfad: Path, muster: str, neu: str):
    t = pfad.read_text(encoding="utf-8")
    t2, n = re.subn(muster, neu, t, count=1)
    if n != 1 or t2 == t:
        raise SystemExit(f"Quellfall ohne Wirkung: {pfad.name} {muster[:50]}")
    pfad.write_text(t2, encoding="utf-8")


# Fälle an der DE-QUELLE: (Name, Mutation, Build muss scheitern?)
QUELLFAELLE = [
    ("rel vor href (gültig)", lambda p: _quelle(p, r'<link href="(https://fonts[^"]*)" rel="stylesheet" media="print"',
                                                  r'<link rel="stylesheet" href="\g<1>" media="print"'), False),
    ("rel ohne Anführungszeichen (gültig)", lambda p: _quelle(p, r'(<link href="https://fonts[^"]*") rel="stylesheet" media="print"',
                                                                r"\g<1> rel=stylesheet media=print"), False),
    # Codex R4: gültiges End-Tag mit Leerzeichen darf den folgenden app.css-Link nicht verschlucken
    ("</noscript > (gültig)", lambda p: _quelle(p, r"</noscript>", "</noscript >"), False),
    ("Quelle noscript-Link ohne rel", lambda p: _quelle(p, r'(<noscript><link href="https://fonts[^"]*") rel="stylesheet"', r"\g<1>"), True),
    # Codex R3: auskommentierter bzw. deaktivierter Fallback-Link ist unwirksam
    ("Quelle noscript-Link auskommentiert", lambda p: _quelle(p, r'<noscript>(<link href="https://fonts[^>]*>)</noscript>',
                                                               r"<noscript><!-- \g<1> --></noscript>"), True),
    ("Quelle noscript-Link disabled", lambda p: _quelle(p, r'(<noscript><link href="https://fonts[^"]*" rel="stylesheet")',
                                                         r"\g<1> disabled"), True),
    ("Quelle ohne onload", lambda p: _quelle(p, r'(fonts[^>]*media="print")\s+onload="[^"]*"', r"\g<1>"), True),
    ("Quelle ohne noscript", lambda p: _quelle(p, r"<noscript><link href=\"https://fonts[^<]*</noscript>", ""), True),
    ("Quelle blockierend", lambda p: _quelle(p, r'(fonts[^>]*rel="stylesheet")\s+media="print"\s+onload="[^"]*"', r"\g<1>"), True),
]


def quellfaelle(code: Path) -> int:
    """Build-Verhalten gegen veränderte DE-Quellen (scanner): gültig → baut und prüft grün, kaputt → HeadFehler."""
    falsch = 0
    for name, mut, soll_scheitern in QUELLFAELLE:
        with tempfile.TemporaryDirectory(prefix="sa-en-quelle-") as t:
            ziel = Path(t)
            shutil.copytree(REPO / "landing", ziel / "landing",
                            ignore=shutil.ignore_patterns("data", "assets", "vendor", "en"))
            mut(ziel / "landing" / "pages" / "scanner.html")
            for html_datei in (ziel / "landing").rglob("*.html"):
                tx = html_datei.read_text(encoding="utf-8")
                html_datei.write_text(CACHE_BUST.sub(lambda m: m.group(1) + "?v=test", tx), encoding="utf-8")
            spec = importlib.util.spec_from_file_location("build_en_q", code)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            lz = ziel / "landing"
            mod.LANDING, mod.PAGES, mod.OUT = lz, lz / "pages", lz / "en"
            mod.I18N, mod.I18N_JS, mod.REPO = lz / "i18n", lz / "js" / "i18n.js", REPO
            titel, desc = en_seiten_meta()["scanner"]
            try:
                mod.build_page("scanner", titel, desc, mod.load_en(), True)
                gescheitert = False
                n = len(pruefe_en_kopf("scanner", (lz / "en" / "scanner.html").read_text(encoding="utf-8"),
                                       (lz / "pages" / "scanner.html").read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                gescheitert, n = True, 0
            ok = gescheitert if soll_scheitern else (not gescheitert and n == 0)
            print(f"  {'ok      ' if ok else 'FALSCH  '}  {name} (Build {'abgebrochen' if gescheitert else f'gebaut, {n} Fehler'})")
            falsch += 0 if ok else 1
    return falsch


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", default=str(REPO / "landing" / "build_en.py"))
    ap.add_argument("--mutationen", action="store_true")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="sa-en-server-") as t:
        ziel = Path(t)
        abbrueche = baue(Path(a.code), ziel)
        fehler = [f"Build-Abbruch {s}: {m}" for s, m in abbrueche.items()] + pruefe(ziel)
        for f in fehler[:25]:
            print("  FEHLER " + f)
        print(f"verify_en_serverpfad: {len(fehler)} Fehler ({Path(a.code).name}, Cache-Buster ?v=test)")
        if not a.mutationen or fehler:
            return 1 if fehler else 0
        verfehlt = 0
        for name, mut in MUTATIONEN.items():
            kopie = Path(t) / "mut"
            shutil.copytree(ziel / "landing", kopie / "landing")
            mut(kopie / "landing" / "en")
            n = len(pruefe(kopie))
            print(f"  {'gefangen ' if n else 'VERFEHLT'}  {name} ({n} Fehler)")
            verfehlt += 0 if n else 1
            shutil.rmtree(kopie)
        print(f"{len(MUTATIONEN) - verfehlt}/{len(MUTATIONEN)} Mutationen gefangen")
        falsch = quellfaelle(Path(a.code))
        print(f"{len(QUELLFAELLE) - falsch}/{len(QUELLFAELLE)} Quellfälle richtig")
        return 1 if verfehlt or falsch else 0


if __name__ == "__main__":
    sys.exit(main())
