#!/usr/bin/env python3
"""
verify_wahlen_blog.py — hält Blogtext, Snapshot und Rechenkern der Wahlstudie deckungsgleich.

    py -3.14 scripts/verify_wahlen_blog.py            # alle Artikel in ARTIKEL
    py -3.14 scripts/verify_wahlen_blog.py --mutationen

Geprüft wird nur der SICHTBARE Text (HTML-Kommentare entfernt). Je Artikel:
  1. Snapshot: die gespeicherten Kennzahlen ergeben sich mit dem AKTUELLEN Rechenkern neu, und der gepaarte
     Nachlauf-Abstand des Faktenblatts ist gleich aggregiere()['differenz_mittel'].
  2. JEDE Zahl mit Einheit (%, Pp, Prozentpunkt, pp, percentage point) muss ein Wert des Faktenblatts sein —
     mit Vorzeichen (sofern geschrieben), genau in der geschriebenen Rundung und mit dem Dezimaltrenner der
     Sprache. Eine erfundene, falsch gerundete oder umgedrehte Zahl fällt so an jeder Stelle auf, auch wenn
     dieselbe Aussage an anderer Stelle richtig steht (Codex-Blog R1).
  3. Pflichtaussagen stehen im Text (Werte mit Vorzeichen und Einheit).
  4. Fallzahlen „X von Y" / „X of Y" und „n = X" gehören zu den Fallzahlen des Faktenblatts.
  5. Jeder Link mit `snapshot=` zeigt auf genau diesen Snapshot; mindestens einer ist da.
  6. Jedes eingebundene Bild löst sich zu einer existierenden Datei auf; die erwarteten Bilder sind eingebunden.
--mutationen baut bekannte Fehler in DE und EN ein und verlangt jeweils Rot.
"""
from __future__ import annotations

import copy
import json
import math
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "research"))
from scripts.wahlen_snapshot import kennzahlen  # noqa: E402
from wahlen_fakten import fakten  # noqa: E402

SNAP_DIR = REPO / "landing" / "data" / "wahlen_snapshots"
BILD_DIR = REPO / "blog" / "posts" / "images"
MINUS = "−"

ARTIKEL = [
    {"datei": "blog/posts/2026-10-07_midterm-wahltag-boerse.md", "sprache": "de",
     "snapshot": "midterm-2026-10", "link": "/wahlen?snapshot=midterm-2026-10",
     "bilder": ["wahlen-midterm-2026/1_midterm_de.png", "wahlen-midterm-2026/2_live_de.png"]},
    {"datei": "blog/posts/en/2026-10-07_midterm-election-day-stock-market.md", "sprache": "en",
     "snapshot": "midterm-2026-10", "link": "/en/elections?snapshot=midterm-2026-10",
     "bilder": ["wahlen-midterm-2026/1_midterm_en.png", "wahlen-midterm-2026/2_live_en.png"]},
]

# Pflichtaussagen: Pfad im Faktenblatt + Einheit. Renditen mit 2 Nachkommastellen.
PFLICHT = [
    (("haupt", "nachlauf_mittel"), "%"), (("haupt", "nachlauf_median"), "%"),
    (("haupt", "p25_ende"), "%"), (("haupt", "p75_ende"), "%"),
    (("gepaart", "nachlauf_wahl"), "%"), (("gepaart", "nachlauf_ohne_wahl"), "%"),
    (("gepaart", "nachlauf_differenz"), "pp"),
    (("gepaart", "vorlauf_wahl"), "%"), (("gepaart", "vorlauf_ohne_wahl"), "%"),
    (("gepaart", "vorlauf_differenz"), "pp"),
    (("ab_1971", "nachlauf_mittel"), "%"), (("ab_1971", "nachlauf_median"), "%"),
    (("ab_1971", "referenz_nachlauf_mittel"), "%"), (("gepaart_ab_1971", "nachlauf_differenz"), "pp"),
    (("gepaart_ab_1971", "vorlauf_wahl"), "%"), (("gepaart_ab_1971", "vorlauf_ohne_wahl"), "%"),
    (("gepaart_ab_1971", "vorlauf_differenz"), "pp"),
    (("extreme", "bester", 1), "%"), (("extreme", "schlechtester", 1), "%"),
    (("house_wechsel", "ja", "nachlauf_mittel"), "%"), (("house_wechsel", "nein", "nachlauf_mittel"), "%"),
    (("gepaart_praesident", "nachlauf_wahl"), "%"), (("gepaart_praesident", "nachlauf_ohne_wahl"), "%"),
    (("gepaart_praesident", "nachlauf_differenz"), "pp"),
    (("gepaart_dow", "nachlauf_wahl"), "%"), (("gepaart_dow", "nachlauf_ohne_wahl"), "%"),
    (("gepaart_dow", "nachlauf_differenz"), "pp"),
    (("live", "seit_basis"), "%"), (("live", "mittel_selber_offset"), "%"),
    (("live", "p25_selber_offset"), "%"), (("live", "p75_selber_offset"), "%"),
]

ZAHL = re.compile(r"(?<![\w.,])([+\-−]?)(\d+(?:[.,]\d+)?)\s?(%|Pp\b|pp\b|Prozentpunkt|percentage point)")
KOMMENTAR = re.compile(r"<!--.*?-->", re.S)
LINK = re.compile(r"\]\(([^)\s]+)\)")
BILD = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def _hol(d, pfad):
    for k in pfad:
        d = d[k]
    return d


def sichtbar(text: str) -> str:
    return KOMMENTAR.sub("", text)


# Typisierung der Faktenblatt-Felder nach Schlüssel (Codex-Blog R2): Fallzahlen, Offsets und Indexstände sind
# keine Renditen; Abstände (Pp) und Renditen (%) werden getrennt zugelassen.
_KEINE_RENDITE = {"n", "n_tripel", "n_positiv", "n_ausgeschlossen", "n_kalender_ungeprueft", "letzter_offset",
                  "live_letzter_wert", "vorlauf_wahl_positiv"}


def _werte(d, art="pct"):
    """Alle Zahlen des Faktenblatts als (wert, art) mit art ∈ {pct, pp, quote}; Ganzzahlen sind Fallzahlen."""
    if isinstance(d, dict):
        for k, w in d.items():
            if k in _KEINE_RENDITE:
                continue
            yield from _werte(w, "quote" if k == "trefferquote" else "pp" if "differenz" in k else art)
    elif isinstance(d, list):
        for w in d:
            yield from _werte(w, art)
    elif isinstance(d, float):
        yield (d * 100 if art == "quote" else d), art


def erlaubt(f: dict) -> dict:
    """{'pct': {...}, 'pp': {...}, 'quote': {...}} — gerundete Zahlenwerte je Art (Renditen/Abstände 2 Stellen)."""
    aus = {"pct": set(), "pp": set(), "quote": set()}
    for w, art in _werte(f):
        if art == "quote":
            aus["quote"].update({round(w, 0), round(w, 1)})
        else:
            aus[art].add(round(w, 2))
    return aus


def fmt(wert: float, sprache: str, einheit: str) -> str:
    s = f"{abs(wert):.2f}"
    if sprache == "de":
        s = s.replace(".", ",")
    vz = "+" if wert > 0 else (MINUS if wert < 0 else "")
    if einheit == "%":
        return f"{vz}{s} %" if sprache == "de" else f"{vz}{s}%"
    return f"{vz}{s} " + ("Pp|Prozentpunkt" if sprache == "de" else "pp|percentage point")


def fallzahlen(f: dict) -> tuple[set, set]:
    h, g, a71 = f["haupt"], f["gepaart"], f["ab_1971"]
    paare = {(h["n_positiv"], h["n"]), (g["vorlauf_wahl_positiv"], g["n_tripel"]),
             (round(a71["trefferquote"] * a71["n"]), a71["n"]),
             (f["gepaart_ab_1971"]["vorlauf_wahl_positiv"], a71["n"])}
    ns = {h["n"], g["n_tripel"], a71["n"], f["house_wechsel"]["ja"]["n"], f["house_wechsel"]["nein"]["n"]}
    return paare, ns


def pruefe_snapshot(st: dict) -> list[str]:
    fehler = []
    neu = kennzahlen(st, st["ansicht"])
    for k, alt in st["kennzahlen"].items():
        if not _gleich(alt, neu.get(k)):
            fehler.append(f"Snapshot {st['snapshot_id']}: Kennzahl {k} gespeichert {alt}, neu gerechnet {neu.get(k)}")
    for name, w in st.get("weitere_ansichten", {}).items():
        neu = kennzahlen(st, w["ansicht"])
        for k, alt in w["kennzahlen"].items():
            if not _gleich(alt, neu.get(k)):
                fehler.append(f"Snapshot {st['snapshot_id']}/{name}: {k} gespeichert {alt}, neu {neu.get(k)}")
    f = fakten(st)
    for g, ref in (("gepaart", st["kennzahlen"]["differenz_mittel"]),
                   ("gepaart_praesident", st["weitere_ansichten"]["praesident"]["kennzahlen"]["differenz_mittel"]),
                   ("gepaart_dow", st["weitere_ansichten"]["dow"]["kennzahlen"]["differenz_mittel"])):
        if not _gleich(f[g]["nachlauf_differenz"], ref):
            fehler.append(f"Faktenblatt {g}: gepaarter Abstand {f[g]['nachlauf_differenz']} ≠ Rechenkern {ref}")
    return fehler


def _gleich(a, b) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        return a is not None and b is not None and math.isclose(a, b, rel_tol=0, abs_tol=1e-9)
    return a == b


def pruefe_artikel(a: dict, text: str, f: dict, bild_dir=BILD_DIR) -> list[str]:
    fehler, t, sp = [], sichtbar(text), a["sprache"]
    erl = erlaubt(f)
    falsch_trenner = "." if sp == "de" else ","
    for m in ZAHL.finditer(t):
        vz, zahl, einheit = m.groups()
        ort = f"{a['datei']}: „{t[max(0, m.start() - 30):m.end()].strip()}“"
        if falsch_trenner in zahl:
            fehler.append(f"{ort}: Dezimaltrenner passt nicht zur Sprache")
            continue
        stellen = len(re.split(r"[.,]", zahl)[1]) if re.search(r"[.,]", zahl) else 0
        wert = float(zahl.replace(",", "."))
        if wert == 0 and not vz:
            continue                                   # „t0 = 0 %“
        if einheit == "%" and not vz and stellen <= 1 and wert in erl["quote"]:
            continue                                   # Quote, z. B. „64,5 %“ oder „40 %“
        if stellen != 2:
            fehler.append(f"{ort}: Rendite nicht auf 2 Stellen")
            continue
        # Ohne Vorzeichen gilt die Zahl als positiv — ein fehlendes Minus ist ein Fehler (Codex-Blog R2).
        signiert = -wert if vz in ("-", MINUS) else wert
        art = "pct" if einheit == "%" else "pp"
        if round(signiert, 2) not in erl[art]:
            fehler.append(f"{ort}: Zahl ist kein {art}-Wert des Faktenblatts (Vorzeichen/Rundung/Art)")
    for pfad, einheit in PFLICHT:
        muster = fmt(_hol(f, pfad), sp, einheit)
        if einheit == "%":
            ok = muster in t
        else:
            zahl, einh = muster.split(" ", 1)
            ok = re.search(re.escape(zahl) + r"\s?(" + einh + ")", t) is not None
        if not ok:
            fehler.append(f"{a['datei']}: Pflichtaussage {'/'.join(map(str, pfad))} = {muster} fehlt")
    paare, ns = fallzahlen(f)
    for x, y in re.findall(r"\b(\d+) (?:von|of) (\d+)\b", t):
        if (int(x), int(y)) not in paare:
            fehler.append(f"{a['datei']}: Fallzahl „{x} von {y}“ passt nicht zum Faktenblatt")
    for x in re.findall(r"\bn = (\d+)\b", t):
        if int(x) not in ns:
            fehler.append(f"{a['datei']}: Fallzahl n = {x} passt nicht zum Faktenblatt")
    if (f["haupt"]["n_positiv"], f["haupt"]["n"]) not in {(int(x), int(y)) for x, y in re.findall(r"\b(\d+) (?:von|of) (\d+)\b", t)}:
        fehler.append(f"{a['datei']}: Fallzahl {f['haupt']['n_positiv']} von {f['haupt']['n']} fehlt")
    ziele = LINK.findall(t)
    snap = [z for z in ziele if "snapshot=" in z]
    if a["link"] not in snap:
        fehler.append(f"{a['datei']}: Snapshot-Link {a['link']} fehlt")
    for z in snap:
        if z != a["link"]:
            fehler.append(f"{a['datei']}: Snapshot-Link zeigt auf {z}")
    bilder = BILD.findall(t)
    for b in bilder:
        if not (bild_dir / b).is_file():
            fehler.append(f"{a['datei']}: Bild {b} existiert nicht")
    for b in a["bilder"]:
        if b not in bilder:
            fehler.append(f"{a['datei']}: Bild {b} nicht eingebunden")
    return fehler


def pruefe(artikel=ARTIKEL) -> list[str]:
    fehler, cache = [], {}
    for a in artikel:
        p = REPO / a["datei"]
        if not p.exists():
            fehler.append(f"{a['datei']}: Datei fehlt")
            continue
        sid = a["snapshot"]
        if sid not in cache:
            sp = SNAP_DIR / f"{sid}.json"
            if not sp.exists():
                fehler.append(f"Snapshot {sid} fehlt")
                continue
            st = json.loads(sp.read_text(encoding="utf-8"))
            fehler += pruefe_snapshot(st)
            cache[sid] = fakten(st)
        fehler += pruefe_artikel(a, p.read_text(encoding="utf-8"), cache[sid])
    return fehler


def _einmal(text, alt, neu):
    assert alt in text, alt
    return text.replace(alt, neu, 1)


def mutationen() -> int:
    st = json.loads((SNAP_DIR / f"{ARTIKEL[0]['snapshot']}.json").read_text(encoding="utf-8"))
    f = fakten(st)
    faelle = []
    s1 = copy.deepcopy(st); s1["kennzahlen"]["nachlauf_mittel"] += 0.01
    faelle.append(("Snapshot-Kennzahl verfälscht", pruefe_snapshot(s1)))
    s2 = copy.deepcopy(st); s2["weitere_ansichten"]["live"]["kennzahlen"]["n"] += 1
    faelle.append(("weitere Ansicht verfälscht", pruefe_snapshot(s2)))
    s3 = copy.deepcopy(st)
    for w in s3["wahlen"]:
        if w["id"] == "us-midterm-1974":
            c, n = w["reihen"]["^GSPC"]["pfad"]["c"], s3["fenster"]
            # nur der Nachlauf t0+1 … t0+20 wird verschoben — sonst bleiben alle Renditen gleich
            w["reihen"]["^GSPC"]["pfad"]["c"] = [v * 1.01 if v is not None and n < i <= n + 20 else v
                                               for i, v in enumerate(c)]
    faelle.append(("Kursreihe im Snapshot verfälscht", pruefe_snapshot(s3) + pruefe_artikel(ARTIKEL[0], (REPO / ARTIKEL[0]["datei"]).read_text(encoding="utf-8"), fakten(s3))))
    for a in ARTIKEL:
        text = (REPO / a["datei"]).read_text(encoding="utf-8")
        de = a["sprache"] == "de"
        if pruefe_artikel(a, text, f):
            print(f"Grundzustand {a['datei']} nicht grün — Mutationen sinnlos")
            return 1
        z = lambda s: s if de else s.replace(",", ".")              # noqa: E731
        p = lambda s: (s + " %") if de else (s + "%")                # noqa: E731
        L = a["sprache"].upper()
        faelle += [
            (f"{L}: alle +0,56 → −0,56", pruefe_artikel(a, text.replace(z("+0,56"), z("−0,56")), f)),
            (f"{L}: Einleitung falsch, FAQ richtig", pruefe_artikel(a, _einmal(text, p(z("+0,56")), p(z("+0,57"))), f)),
            (f"{L}: drei Stellen", pruefe_artikel(a, _einmal(text, p(z("+0,56")), p(z("+0,569"))), f)),
            (f"{L}: House-Wert falsch", pruefe_artikel(a, text.replace(z("−1,02"), z("−1,12")), f)),
            (f"{L}: Dow falsch gerundet", pruefe_artikel(a, text.replace(z("+0,85"), z("+0,84")), f)),
            (f"{L}: falscher Dezimaltrenner", pruefe_artikel(a, text.replace(z("+0,72"), "+0,72" if not de else "+0.72"), f)),
            (f"{L}: Fallzahl falsch", pruefe_artikel(a, text.replace("20 von 31" if de else "20 of 31", "21 von 31" if de else "21 of 31"), f)),
            (f"{L}: Pflichtaussage nur noch im Kommentar", pruefe_artikel(a, text.replace(z("+2,33"), z("+2,34")) + "\n<!-- " + z("+2,33") + " -->", f)),
            (f"{L}: sichtbare Snapshot-Links falsch, Kommentar richtig", pruefe_artikel(a, text.replace(a["link"], a["link"].replace("midterm-2026-10", "midterm-2026-09")) + f"\n<!-- {a['link']} -->", f)),
            (f"{L}: Bildordner falsch", pruefe_artikel(a, text.replace("](wahlen-midterm-2026/", "](does-not-exist/"), f)),
            (f"{L}: Bild nicht eingebunden", pruefe_artikel(a, text.replace("1_midterm_", "x_midterm_"), f)),
            (f"{L}: Minus fehlt an einer Stelle", pruefe_artikel(a, _einmal(text, z("−1,02"), z("1,02")), f)),
            (f"{L}: Fallzahl als Rendite", pruefe_artikel(a, _einmal(text, p(z("+0,56")), p(z("+31,00"))), f)),
            (f"{L}: Rendite als Abstand", pruefe_artikel(a, _einmal(text, z("+0,33"), z("+0,72")), f)),
        ]
    verfehlt = [n for n, fe in faelle if not fe]
    for n, fe in faelle:
        print(f"  {'gefangen' if fe else 'VERFEHLT'}: {n}")
    print(f"{len(faelle) - len(verfehlt)}/{len(faelle)} Mutationen gefangen")
    return 1 if verfehlt else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Windows-Konsole (cp1252)
    if "--mutationen" in sys.argv:
        sys.exit(mutationen())
    fe = pruefe()
    for x in fe:
        print("FEHLER", x)
    print(f"verify_wahlen_blog: {len(fe)} Fehler")
    sys.exit(1 if fe else 0)
