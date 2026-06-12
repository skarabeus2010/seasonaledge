# -*- coding: utf-8 -*-
"""
fix_i18n_html_markup.py - korrigiert mis-markiertes data-i18n in den Landing-Pages.

Problem: Etliche Elemente tragen data-i18n="KEY" (Text-Modus), obwohl der
zugehoerige Wert in en.json HTML enthaelt (<b>, <a>, ...). Die Laufzeit
(_applyDOM) UND der Pre-Render uebersetzen solche Elemente nur teilweise
(nur der letzte Textknoten) -> halb deutsch/halb englisch. Auch live sichtbar.

Fix: data-i18n="KEY" -> data-i18n-html="KEY", genau fuer die Keys, deren
en.json-Wert HTML-Tags enthaelt. en.json bleibt unveraendert (Wert ist schon
HTML). Idempotent: bereits gefixte Stellen matchen nicht mehr.

Usage:
  py scripts/fix_i18n_html_markup.py          # dry-run
  py scripts/fix_i18n_html_markup.py --write
"""
from __future__ import annotations
import re, sys, json
from pathlib import Path

REPO  = Path(__file__).resolve().parent.parent
PAGES = REPO / "landing" / "pages"
EN    = json.loads((REPO / "landing" / "i18n" / "en.json").read_text(encoding="utf-8"))

# Keys, deren EN-Wert HTML enthaelt -> data-i18n muss data-i18n-html sein
HTML_KEYS = {k for k, v in EN.items() if isinstance(v, str) and "<" in v}


def fix_file(path: Path, write: bool) -> int:
    html = path.read_text(encoding="utf-8")
    n = 0
    for key in HTML_KEYS:
        # nur exaktes data-i18n="KEY" (nicht -html/-placeholder/-title/-aria)
        pat = re.compile(r'data-i18n="' + re.escape(key) + r'"')
        html, c = pat.subn(f'data-i18n-html="{key}"', html)
        n += c
    if write and n:
        path.write_text(html, encoding="utf-8")
    return n


def main():
    write = "--write" in sys.argv
    print(f"=== fix_i18n_html_markup.py ({'WRITE' if write else 'DRY-RUN'}) | "
          f"{len(HTML_KEYS)} HTML-Keys ===")
    total = 0
    for path in sorted(PAGES.glob("*.html")):
        n = fix_file(path, write)
        if n:
            print(f"  [{'FIX' if write else 'DRY'}] {path.name}: {n} Stellen")
            total += n
    print(f"\n  Summe: {total} Stellen {'korrigiert' if write else '(dry-run)'}")
    if not write and total:
        print("  -> mit --write anwenden")


if __name__ == "__main__":
    main()
