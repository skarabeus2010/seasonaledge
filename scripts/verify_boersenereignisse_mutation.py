# -*- coding: utf-8 -*-
"""Prüft den Wächter des Ereigniskatalogs (scripts/verify_boersenereignisse.py): baut Fehler in Katalog, Projektionen,
Versionen, Generator und JS-API ein und verlangt Rot an der benannten Prüfung.

    py -3.14 scripts/verify_boersenereignisse_mutation.py

ERZWUNGEN ISOLIERT: alles geschieht in einer frischen Temp-Kopie (shared/, scripts/ ohne video/perf/research,
landing/js/). Bei Mutationen an Generator oder JS-API wird landing/js/boersenkalender.js IN DER KOPIE neu erzeugt —
sonst finge nur die Aktualitätsprüfung den Fehler, nie der Objektvergleich. Abschluss: Hash des Projektbaums vor = nach.

Beweisregeln wie in den übrigen Mutationstests: Endmarker/Summenzeile, benannte Prüfung, ein Abbruch ist kein
Nachweis, Anker genau einmal, Gegenproben.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import sys
import tempfile

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from scripts.verify_twins_mutation import _atomar_schreiben, python_probe  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BE = "shared/boersenereignisse.py"
API = "scripts/boersenkalender/api.js"
GEN = "scripts/build_boersenkalender_js.py"

# (Name, [(Datei, alt, neu), …], neu erzeugen?, erwartete Prüfung)
MUTATIONEN = [
    ("LSE: Weihnachten/Boxing Day vertauscht (gleiche Menge)", [
        (BE, "        xw, bw = date(j, 12, 27), boxing\n", "        xw, bw = boxing, date(j, 12, 27)\n")], False, "[Sollfall]"),
    ("TSE: Furikae-Sonntag fällt aus der Kompatibilitätsmenge", [
        (BE, 'NOMINAL_BLEIBT = frozenset({"TSE"})', "NOMINAL_BLEIBT = frozenset()")], False, "[Bestand]"),
    ("TSE: Regeltermin statt rechtlichem Tag in der Menge", [
        (BE, "            menge.add(e.rechtlich)\n", "            menge.add(e.nominal)\n")], False, "[Bestand]"),
    ("TSE: verlegt geht beim Furikae verloren", [
        (BE, "grund=\"furikae\", verlegt=verlegt))", "grund=\"furikae\", verlegt=False))")], False, "[Invariante]"),
    ("schliessungen enthält Wochenenden", [
        (BE, 'e.art != "halbtag" and e.wirksam.weekday() < 5})', 'e.art != "halbtag"})')], False, "[Invariante]"),
    ("schliessungen zählt doppelte Tage", [
        (BE, '    return sorted({e.wirksam for e in ereignisse(b, jahr) if e.art != "halbtag" and e.wirksam.weekday() < 5})',
         '    return sorted([e.wirksam for e in ereignisse(b, jahr) if e.art != "halbtag" and e.wirksam.weekday() < 5])')],
     False, "[Invariante]"),
    ("ereignisversion ohne Namen/Quellen", [
        (BE, '                h.update(json.dumps(e.inhalt(), sort_keys=True, ensure_ascii=False).encode("utf-8"))',
         '                h.update((e.ereignis_id + e.wirksam.isoformat()).encode("utf-8"))')], False, "[Version]"),
    ("kalenderversion über die Kompatibilitätsmenge", [
        (BE, '",".join(d.isoformat() for d in schliessungen(b, j))', '",".join(d.isoformat() for d in sorted(kompat(b, j)))')],
     False, "[Version]"),
    ("Tabellenereignis bekommt einen Namen", [
        (BE, '"unbestimmt", d, d, d, "keiner", False, "tabelle", None, None, q)',
         '"unbestimmt", d, d, d, "keiner", False, "tabelle", "Feiertag", "Holiday", q)')], False, "[Invariante]"),
    ("LSE 2002: Spring Bank und Golden Jubilee vertauscht (gleiche Menge)", [
        (BE, "verlegt_spring = {2002: date(2002, 6, 4),", "verlegt_spring = {2002: date(2002, 6, 3),"),
        (BE, "jubilaeum = {2002: (date(2002, 6, 3),", "jubilaeum = {2002: (date(2002, 6, 4),")], True, "[Sollfall]"),
    ("LSE 2012: Spring Bank und Diamond Jubilee vertauscht (gleiche Menge)", [
        (BE, "2012: date(2012, 6, 4), 2022", "2012: date(2012, 6, 5), 2022"),
        (BE, "2012: (date(2012, 6, 5),", "2012: (date(2012, 6, 4),")], True, "[Sollfall]"),
    ("ereignisversion hasht die Version mit", [
        (BE, '                h.update(json.dumps(e.inhalt(), sort_keys=True, ensure_ascii=False).encode("utf-8"))',
         '                h.update(json.dumps(e.als_dict(), sort_keys=True, ensure_ascii=False).encode("utf-8"))')],
     False, "[Invariante]"),
    ("JS: Ereignisse ohne kalenderversion", [
        (API, "quelle_stand: q[3],\n        kalenderversion: DATEN.kalenderversion\n", "quelle_stand: q[3]\n")], True, "[Zwilling]"),
    ("NYSE-Sonderschließung mit falscher Kennung", [
        (BE, 'date(2025, 1, 9): ("carter",', 'date(2025, 1, 9): ("mlk",')], False, "[Sollfall]"),
    ("Spring Bank: Regeltermin statt verlegtem Tag", [
        (BE, '                      rechtlich=verlegt_spring[j], grund="verlegung", verlegt=True))',
         '                      grund="verlegung", verlegt=True))')], False, "[Bestand]"),
    # ── Generator / JS (Kopie wird neu erzeugt) ──
    ("Generator verliert den wirksamen Tag", [(GEN, '                ab["w"] = e.wirksam.strftime("%Y%m%d")', '                pass')],
     True, "[Zwilling]"),
    ("Generator verliert den Ersatzgrund", [(GEN, '                ab["g"] = e.ersatzgrund', '                pass')], True, "[Zwilling]"),
    ("JS: Tabellenkennung nach Regel", [
        (API, "ereignis_id: herkunft === 'tabelle' ? b + ':tabelle:' + nominal : b + ':' + r[0] + ':' + nominal,",
         "ereignis_id: b + ':' + r[0] + ':' + nominal,")], True, "[Zwilling]"),
    ("JS: verlegt auch bei reinem Ersatz", [(API, "verlegt: ab.v === 1,", "verlegt: ab.v === 1 || !!ab.w,")], True, "[Zwilling]"),
    ("JS: schliessungen ohne Werktagsfilter", [
        (API, "        if (wochentag(+w.slice(0, 4), +w.slice(5, 7), +w.slice(8, 10)) < 5) menge[w] = true;",
         "        menge[w] = true;")], True, "[Zwilling]"),
    ("JS: Name englisch/deutsch vertauscht", [
        (API, "name_en: nIdx < 0 ? null : DATEN.namen[nIdx][1],", "name_en: nIdx < 0 ? null : DATEN.namen[nIdx][0],")],
     True, "[Zwilling]"),
    ("JS: Identität immer Regel", [(API, "return DATEN.identitaet[b].indexOf(j) >= 0 ? 'tabelle' : 'regel';", "return 'regel';")],
     True, "[Zwilling]"),
    ("JS: Ereignisse veränderlich", [
        (API, "      liste.push(Object.freeze({", "      liste.push(({")], True, "[Zwilling]"),
    ("API geändert, Datei nicht neu erzeugt", [(API, "verlegt: ab.v === 1,", "verlegt: ab.v === 1 || !!ab.w,")],
     False, "nicht aktuell"),
]
# Gegenproben: dürfen NICHT als gefangen gelten
UNGUELTIG_ERWARTET = [
    ("Anker existiert nicht", [(BE, "diese Zeile gibt es nicht", "egal")], False),
    ("Absturz: Katalog nicht importierbar", [(BE, "ARTEN = (", "ARTEN = ((")], False),
]

KOPIE = pathlib.Path()
WAECHTER = "verify_boersenereignisse"   # verify_produkttermine_mutation.py setzt den Namen um
ROH: dict = {}


def isolierte_kopie(ziel: pathlib.Path) -> pathlib.Path:
    shutil.copytree(WURZEL / "shared", ziel / "shared", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(WURZEL / "scripts", ziel / "scripts",
                    ignore=shutil.ignore_patterns("__pycache__", "video", "perf", "research", "node_modules"))
    (ziel / "landing").mkdir()
    shutil.copytree(WURZEL / "landing" / "js", ziel / "landing" / "js", ignore=shutil.ignore_patterns("__pycache__"))
    return ziel


def _fingerabdruck(w: pathlib.Path) -> str:
    h = hashlib.sha256()
    for teil in ("shared", "scripts", "landing/js"):
        for p in sorted((w / teil).rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts and "node_modules" not in p.parts:
                h.update(str(p.relative_to(w)).encode())
                h.update(p.read_bytes())
    return h.hexdigest()


def anker(datei, text):
    roh = ROH.setdefault(datei, (KOPIE / datei).read_bytes())
    if roh.count(b"\r\n") > roh.count(b"\n") // 2:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    return text.encode("utf-8")


def _env():
    return {**os.environ, "PYTHONUTF8": "1"}


def erzeugen():
    r = python_probe([KOPIE / GEN], capture_output=True, text=True, encoding="utf-8", env=_env(), cwd=str(KOPIE))
    return r.returncode == 0


def lauf():
    r = python_probe([KOPIE / "scripts" / (WAECHTER + ".py")], capture_output=True, text=True,
                     encoding="utf-8", env=_env(), cwd=str(KOPIE))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def auswerten(rc, aus, erwartet):
    if rc == 0:
        return "entwischt", "Wächter blieb grün"
    if WAECHTER + ":" not in aus:
        return "ungueltig", "der Wächter brach ab statt durchzulaufen"
    zeilen = [z for z in aus.splitlines() if z.startswith("FEHL")]
    if not zeilen:
        return "ungueltig", "rot ohne inhaltliche Prüfung"
    if erwartet and not any(erwartet in z for z in zeilen):
        return "ungueltig", "erwartete Prüfung %s blieb grün; rot war: %s" % (erwartet, zeilen[0][:90])
    return "gefangen", zeilen[0][:90]


def bewerte(aenderungen, neu_erzeugen, erwartet=None):
    neu = {}
    for datei, alt, ne in aenderungen:
        a = anker(datei, alt)
        basis = neu.get(datei, ROH[datei])
        n = basis.count(a)
        if n != 1:
            return "ungueltig", "Anker %dx gefunden in %s, erwartet 1x" % (n, datei)
        neu[datei] = basis.replace(a, anker(datei, ne), 1)
    js = "landing/js/boersenkalender.js"
    ROH.setdefault(js, (KOPIE / js).read_bytes())
    for d, b in neu.items():
        _atomar_schreiben(KOPIE / d, b)
    try:
        if neu_erzeugen and not erzeugen():
            return "ungueltig", "Neuerzeugung in der Kopie scheiterte"
        rc, aus = lauf()
    finally:
        for d in neu:
            _atomar_schreiben(KOPIE / d, ROH[d])
        _atomar_schreiben(KOPIE / js, ROH[js])
    return auswerten(rc, aus, erwartet)


def _main():
    rc, aus = lauf()
    if rc != 0:
        print("ABBRUCH: der Wächter ist schon ohne Mutation rot.\n%s" % aus[-1500:])
        return 1
    print("Grundlinie: Wächter ohne Mutation grün (isolierte Kopie %s)\n" % KOPIE)
    gefangen, probleme, urteil_ok = 0, [], True
    for name, aend, neu_erzeugen, erwartet in MUTATIONEN:
        ergebnis, warum = bewerte(aend, neu_erzeugen, erwartet)
        print(("  gefangen       %s" % name) if ergebnis == "gefangen" else ("  %-12s   %s  (%s)" % (ergebnis.upper(), name, warum)), flush=True)
        gefangen += ergebnis == "gefangen"
        if ergebnis != "gefangen":
            probleme.append(name)
    print("  -- Gegenprobe am Urteil dieses Tests --")
    for name, aend, neu_erzeugen in UNGUELTIG_ERWARTET:
        ergebnis, warum = bewerte(aend, neu_erzeugen)
        if ergebnis == "ungueltig":
            print("  richtig verworfen  %s  (%s)" % (name, warum))
        else:
            print("  FALSCH EINGEORDNET %s  -> %s" % (name, ergebnis))
            urteil_ok = False
    rc, _ = lauf()
    print("\n" + ("wiederhergestellt: Wächter wieder grün" if rc == 0 else "WARNUNG: nach Wiederherstellung ROT!"))
    print("%d von %d Mutationen gefangen" % (gefangen, len(MUTATIONEN)))
    for p in probleme:
        print("  " + p)
    return 0 if (gefangen == len(MUTATIONEN) and urteil_ok and rc == 0) else 1


def main():
    global KOPIE
    vorher = _fingerabdruck(WURZEL)
    temp = pathlib.Path(tempfile.mkdtemp(prefix="sa_ereignis_mut_")).resolve()
    if temp == WURZEL or WURZEL in temp.parents:
        print("ABBRUCH: Temp-Verzeichnis liegt im Projektbaum")
        return 1
    try:
        KOPIE = isolierte_kopie(temp / "baum")
        rc = _main()
    finally:
        shutil.rmtree(temp, ignore_errors=True)
    if _fingerabdruck(WURZEL) != vorher:
        print("FEHL: der Projektbaum hat sich während des Tests verändert — Isolation verletzt")
        return 1
    print("Projektbaum unverändert (Hash vor = nach)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
