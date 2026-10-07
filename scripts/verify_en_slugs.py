#!/usr/bin/env python3
"""
verify_en_slugs.py — Regressionstest für eigene EN-Adressen (`_EN_SLUGS` in landing/js/i18n.js).

    py -3.14 scripts/verify_en_slugs.py

Prüft den echten Bestand (muss sauber sein) und fünf Kollisionsfälle (müssen rot sein), darunter
den Fall aus Codex-Runde 2: ein EN-Ziel, das wie eine andere DE-Seite heisst ('skew' -> 'wahlen').
Dazu die Python-Abbildung en_slug/en_url gegen die Erwartung.
"""
from __future__ import annotations

import pathlib
import sys
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import shared.seo_basis as sb  # noqa: E402

FAELLE = [
    ("EN-Ziel = anderer DE-Slug mit EN-Fassung", {"wahlen": "elections", "skew": "wahlen"}),
    ("EN-Ziel doppelt", {"wahlen": "elections", "skew": "elections"}),
    ("EN-Ziel = DE-Slug einer bestehenden EN-Seite", {"wahlen": "dashboard"}),
    ("EN-Ziel = DE-Seite ohne EN-Fassung", {"wahlen": "kalender"}),
    ("Eintrag ohne Seite", {"gibtsnicht": "x"}),
]


def main() -> int:
    fehler = []
    meta = sb.en_seiten_meta()
    echt = sb.pruefe_en_slugs(meta)
    if echt:
        fehler += [f"Bestand: {x}" for x in echt]
    for name, abb in FAELLE:
        with mock.patch.object(sb, "en_slugs", return_value=abb):
            if not sb.pruefe_en_slugs(meta):
                fehler.append(f"nicht erkannt: {name} {abb}")
    if sb.en_slug("wahlen") != "elections" or sb.en_slug("skew") != "skew" or sb.en_slug("index") != "index":
        fehler.append("en_slug bildet falsch ab")
    if sb.en_url("wahlen") != f"{sb.BASE_URL}/en/elections" or sb.en_url("index") != f"{sb.BASE_URL}/en/":
        fehler.append("en_url bildet falsch ab")
    for x in fehler:
        print("FEHLER", x)
    print(f"verify_en_slugs: {len(fehler)} Fehler ({len(FAELLE)} Kollisionsfälle)")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
