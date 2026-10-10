#!/usr/bin/env python3
"""
Wächter: landing/js/boersenkalender.js (SA.boersenkalender) — Plan v6, Weg A (isoliert).

node führt die ECHTE erzeugte Datei aus (scripts/js/probe_boersenkalender.js), je Zeitzone ein eigener Prozess.
  [Aktuell]     Datei == Neuerzeugung aus Python (Erzeuger im Speicher, nichts geschrieben).
  [Python]      istHandelstag + nummern (alle fünf Felder) == Python für 13 Börsen × jeden Tag 1885–2100.
  [NumPy]       dieselben Nummern == unabhängige Zählung mit numpy.busday_count (Feiertage aus der Erzeugung).
  [Zeitzone]    dieselben Ergebnisse unter sechs Zonen (Offsets nachgewiesen), u. a. Pacific/Apia.
  [API]         Monats-/Jahres-/Nächster-Tag-Termine, schliessungen, status gegen Python-Referenzen.
  [Ticker]      boerse() == Python für alle SYMBOLS-Ticker, Regel- und Fehlerfälle.
  [Validierung] Fehlerfälle werfen, Alias NASDAQ, Typprüfung.
  [Sollfall]    die belegten Sollfälle aus verify_kalender_sollfaelle.py, in JS.
  [Isolation]   keine Seite unter landing/ referenziert die Datei (bis zur gemeinsamen Umschaltung).

Aufruf:  py -3.14 scripts/verify_boersenkalender_js.py      Exit 0 = alles erfüllt (braucht node + numpy)
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import date, timedelta

import numpy as np

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

from shared.exchange_holidays import (  # noqa: E402
    _EXCHANGE_FUNCTIONS, NUMMERN_BIS_JAHR, NUMMERN_VON_JAHR, get_holidays, handelstag_nummern,
    is_trading_day, kalender_status,
)
from shared.symbols import SYMBOLS, get_exchange_for_holidays  # noqa: E402
from scripts.build_boersenkalender_js import ZIEL, erzeugen  # noqa: E402
from scripts.verify_kalender_sollfaelle import SOLLFAELLE  # noqa: E402

PROBE = os.path.join(WURZEL, "scripts", "js", "probe_boersenkalender.js")
BOERSEN = sorted(b for b in _EXCHANGE_FUNCTIONS if b != "NASDAQ")
# Zone → erwartete getTimezoneOffset() für 15.01.2026 und 15.07.2026 (Minuten, Vorzeichen wie JS).
ZONEN = {"UTC": [0, 0], "Europe/Berlin": [-60, -120], "America/New_York": [300, 240],
         "Pacific/Apia": [-780, -780], "Pacific/Kiritimati": [-840, -840], "America/Adak": [600, 540]}

FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung: str, bedingung: bool, text: str = "") -> None:
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append(f"[{kennung}] {text}")


def alle_tage() -> list[str]:
    d, ende, out = date(NUMMERN_VON_JAHR, 1, 1), date(NUMMERN_BIS_JAHR, 12, 31), []
    while d <= ende:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def zeile(n) -> str:
    def f(x):
        return "null" if x is None else str(x)
    return f"{1 if n.offen else 0}:{n.tdom}:{n.tdoy}:{f(n.tdom_rev)}:{f(n.tdoy_rev)}"


def numpy_zeilen(tage: list[str], boerse: str) -> str:
    maske = "1111111" if boerse == "CRYPTO" else "1111100"
    fei = np.array(sorted(get_holidays(boerse, NUMMERN_VON_JAHR, NUMMERN_BIS_JAHR)), dtype="datetime64[D]")
    d = np.array(tage, dtype="datetime64[D]")
    kw = dict(weekmask=maske, holidays=fei)
    j0 = d.astype("datetime64[Y]").astype("datetime64[D]")
    j1 = (d.astype("datetime64[Y]") + 1).astype("datetime64[D]")
    m0 = d.astype("datetime64[M]").astype("datetime64[D]")
    m1 = (d.astype("datetime64[M]") + 1).astype("datetime64[D]")
    o = np.is_busday(d, **kw)
    tdoy, tdom = np.busday_count(j0, d + 1, **kw), np.busday_count(m0, d + 1, **kw)
    ry, rm = -np.busday_count(d, j1, **kw), -np.busday_count(d, m1, **kw)
    return ",".join(f"{1 if o[i] else 0}:{tdom[i]}:{tdoy[i]}:{rm[i] if o[i] else 'null'}:{ry[i] if o[i] else 'null'}"
                    for i in range(len(tage)))


def probe(zone: str, auftrag: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        pfad = os.path.join(tmp, "auftrag.json")
        with open(pfad, "w", encoding="utf-8") as fh:
            json.dump(auftrag, fh)
        # Liste statt Shell: keine Pfadumdeutung durch Git Bash, TZ setzt die Probe selbst.
        r = subprocess.run(["node", PROBE, zone, pfad], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"node-Probe {zone}: {r.stderr[-400:]}")
    return json.loads(r.stdout)


def h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def main() -> int:
    tage = alle_tage()
    try:
        with open(ZIEL, "rb") as fh:
            pruefe("Aktuell", fh.read() == erzeugen(), "Datei weicht von der Neuerzeugung ab")
    except Exception as e:
        FEHLER.append(f"[Ausnahme] Aktuell: {type(e).__name__}: {e}")

    # Referenzen aus Python
    soll_py = {b: ",".join(zeile(n) for n in handelstag_nummern(tage, b)) for b in BOERSEN}
    soll_ist = {b: "".join("1" if is_trading_day(date.fromisoformat(t), b) else "0" for t in tage) for b in BOERSEN}

    # API-Aufrufe mit Python-Referenz
    jahre = [1885, 1900, 1950, 1972, 1999, 2000, 2001, 2012, 2018, 2019, 2020, 2021, 2024, 2026, 2100]
    aufrufe, soll_aufrufe = [], []
    for b in BOERSEN:
        for j in jahre:
            alle = [date(j, 1, 1) + timedelta(days=i) for i in range((date(j + 1, 1, 1) - date(j, 1, 1)).days)]
            num = dict(zip(alle, handelstag_nummern(alle, b)))
            offen_tage = [d for d in alle if num[d].offen]
            for m in (1, 2, 5, 10, 12):
                im_monat = [d for d in offen_tage if d.month == m]
                for n in (1, 2, len(im_monat), len(im_monat) + 1):
                    aufrufe.append(["nterHandelstag", j, m, n, b])
                    soll_aufrufe.append(im_monat[n - 1].isoformat() if 1 <= n <= len(im_monat) else None)
                for n in (1, 2, len(im_monat) + 1):
                    aufrufe.append(["letzterHandelstag", j, m, n, b])
                    soll_aufrufe.append(im_monat[-n].isoformat() if 1 <= n <= len(im_monat) else None)
            for n in (1, 100, len(offen_tage), len(offen_tage) + 1):
                aufrufe.append(["nterHandelstagImJahr", j, n, b])
                soll_aufrufe.append(offen_tage[n - 1].isoformat() if 1 <= n <= len(offen_tage) else None)
            aufrufe.append(["schliessungen", j, b])
            soll_aufrufe.append([d.isoformat() for d in sorted(get_holidays(b, j, j))])
            aufrufe.append(["status", b, j])
            soll_aufrufe.append(kalender_status(b, j))
    # nächster Handelstag: jeder Tag mehrerer Kettenjahre (inkl. TSE Golden Week 2019, Jahreswechsel)
    for b in BOERSEN:
        for j in (2019, 2020, 2099):
            for i in range(0, 366, 1):
                d0 = date(j, 1, 1) + timedelta(days=i)
                if d0.year != j:
                    continue
                d = d0
                while not is_trading_day(d, b):
                    d += timedelta(days=1)
                aufrufe.append(["naechsterHandelstag", d0.isoformat(), b])
                soll_aufrufe.append(d.isoformat())
    # Datenende (Codex P1b R1): letzte zwölf Tage des Rechenbereichs; ohne offenen Tag bis 2100-12-31 → Fehler.
    ende = date(NUMMERN_BIS_JAHR, 12, 31)
    for b in BOERSEN:
        for k in range(12):
            d0 = ende - timedelta(days=k)
            d = d0
            while d <= ende and not is_trading_day(d, b):
                d += timedelta(days=1)
            aufrufe.append(["naechsterHandelstag", d0.isoformat(), b])
            soll_aufrufe.append(d.isoformat() if d <= ende else "FEHLER")
    # Status: JEDES Jahr knapp außerhalb und innerhalb des Rechenbereichs, alle Intervallgrenzen eingeschlossen.
    for b in BOERSEN:
        for j in range(NUMMERN_VON_JAHR - 5, NUMMERN_BIS_JAHR + 6):
            aufrufe.append(["status", b, j])
            soll_aufrufe.append(kalender_status(b, j))
    # Ticker
    regel = ["AAPL", "aapl", " spy ", "SAP", "sap.de", "NEU.F", "NEU.BR", "NEU.LS", "air.pa", "NEU.T", "NEU.HK",
             "NEU-USDT", "neu=x", "^gdaxi", "GC=F", "^XYZ", "NEU=F", "NEU.XX", "", "   ", ".F"]
    for t in list(SYMBOLS) + regel:
        aufrufe.append(["boerse", t])
        try:
            soll_aufrufe.append(get_exchange_for_holidays(t))
        except ValueError:
            soll_aufrufe.append("FEHLER")
    # Validierung: alle müssen werfen
    werfen = [["istHandelstag", "2026-01-02", "FOO"], ["istHandelstag", "2026-01-02", ""],
              ["istHandelstag", "2026-01-02", None], ["istHandelstag", "20260102", "NYSE"],
              ["istHandelstag", "2026-W01-5", "NYSE"], ["istHandelstag", "2026-02-30", "NYSE"],
              ["istHandelstag", "2026-13-01", "NYSE"], ["istHandelstag", "1884-12-31", "NYSE"],
              ["istHandelstag", "2101-01-03", "NYSE"], ["istHandelstag", 20260102, "NYSE"],
              ["istHandelstag", "2026-10-10", "FOO"],   # Samstag: Börse vor dem Wochenende prüfen
              ["nummern", [], "FOO"], ["nummern", "2026-01-02", "NYSE"],
              ["nterHandelstag", 2026, 1, 0, "NYSE"], ["nterHandelstag", 2026, 1, 1.5, "NYSE"],
              ["nterHandelstag", 2026, 13, 1, "NYSE"], ["nterHandelstag", 1884, 1, 1, "NYSE"],
              ["letzterHandelstag", 2026, 1, 0, "NYSE"], ["nterHandelstagImJahr", 2026, 0, "NYSE"],
              ["naechsterHandelstag", "2026-02-30", "NYSE"], ["schliessungen", 2101, "NYSE"], ["status", "FOO", 2026]]
    for c in werfen:
        aufrufe.append(c)
        soll_aufrufe.append("FEHLER")
    aufrufe.append(["istHandelstag", "2025-01-09", "nasdaq"]); soll_aufrufe.append(False)
    aufrufe.append(["istHandelstag", "2026-10-10", "CRYPTO"]); soll_aufrufe.append(True)
    aufrufe.append(["istHandelstag", "2026-10-10", "FOREX"]); soll_aufrufe.append(False)
    # Sollfälle
    for b, iso, soll, quelle, anlass in SOLLFAELLE:
        aufrufe.append(["istHandelstag", iso, b])
        soll_aufrufe.append(soll)

    auftrag_voll = {"tage": {"art": "tage", "boersen": BOERSEN, "daten": tage},
                    "aufrufe": {"art": "aufrufe", "aufrufe": aufrufe}}
    ergebnisse = {}
    for zone, offs in ZONEN.items():
        try:
            r = probe(zone, auftrag_voll)
        except Exception as e:
            FEHLER.append(f"[Ausnahme] Zeitzone {zone}: {type(e).__name__}: {e}")
            continue
        pruefe(f"Zeitzone {zone} wirkt", r["offsets"] == offs, f"Offsets {r['offsets']} statt {offs} — Zone nicht gesetzt?")
        ergebnisse[zone] = r

    if "UTC" in ergebnisse:
        r = ergebnisse["UTC"]["ergebnisse"]
        for b in BOERSEN:
            pruefe(f"Python istHandelstag {b}", r["tage"][b + "|ist"] == soll_ist[b], "weicht ab")
            ist = r["tage"][b]
            if ist != soll_py[b]:
                a, s = ist.split(","), soll_py[b].split(",")
                i = next(k for k in range(len(s)) if a[k] != s[k])
                pruefe(f"Python nummern {b}", False, f"erster Unterschied {tage[i]}: JS {a[i]} / Python {s[i]}")
            else:
                pruefe(f"Python nummern {b}", True)
            pruefe(f"NumPy nummern {b}", ist == numpy_zeilen(tage, b), "unabhängige Zählung weicht ab")
        ist_auf = r["aufrufe"]
        # Abstürze in JEDER Zone kennzeichnen, nicht nur in UTC — die anderen Zonen werden unten nur per
        # Hash verglichen, und ein Absturz nur unter Pacific/Apia zählte sonst als Nachweis (Codex P1b R3).
        for zone, rz in ergebnisse.items():
            if zone == "UTC":
                continue
            for c, x in zip(aufrufe, rz["ergebnisse"]["aufrufe"]):
                if "fehler" in x and x.get("art") != "api":
                    FEHLER.append(f"[Ausnahme] API {zone} {c}: {x['fehler'][:100]}")
        abw = []
        for c, soll, x in zip(aufrufe, soll_aufrufe, ist_auf):
            got = "FEHLER" if "fehler" in x else x["ok"]
            if got == "FEHLER" and x.get("art") != "api":
                # Jeder ABSTURZ (keine KalenderFehler-Instanz) ist ein [Ausnahme]-Befund — auch dort, wo
                # ein Fehler erwartet war. Damit zählt eine Mutation, die nur abstürzt, nie als „gefangen“
                # (Codex P1b R1/R2: das frühere Meldungspräfix ließ sich unterlaufen). Ein gewollter
                # KalenderFehler an falscher Stelle bleibt ein fachlicher Befund (falsches Ergebnis).
                FEHLER.append(f"[Ausnahme] API {c}: {x['fehler'][:120]}")
            elif got != soll:
                abw.append(f"{c}: JS {got!r} / soll {soll!r}")
        pruefe("API Termine/Ticker/Validierung/Sollfälle", not abw and len(ist_auf) == len(aufrufe),
               f"{len(abw)} Abweichungen, z. B. {abw[:3]}")
        # Einzelne benannte Prüfungen, damit Mutationen eine eindeutige Kennung treffen
        def get(c):
            i = aufrufe.index(c)
            x = ist_auf[i]
            return "FEHLER" if "fehler" in x else x["ok"]
        pruefe("API naechsterHandelstag TSE Golden Week", get(["naechsterHandelstag", "2019-04-27", "TSE"]) == "2019-05-07")
        pruefe("API naechsterHandelstag ab einschließlich", get(["naechsterHandelstag", "2019-05-07", "TSE"]) == "2019-05-07")
        pruefe("Validierung leere Liste prüft Börse", get(["nummern", [], "FOO"]) == "FEHLER")
        pruefe("Ticker unbekannter Index wirft", get(["boerse", "^XYZ"]) == "FEHLER")
        pruefe("Status NYSE 1960 ungeprueft", get(["status", "NYSE", 1960]) == "ungeprueft")
        pruefe("Status NYSE 2028 belegt, 2029 Annahme",
               get(["status", "NYSE", 2028]) == "belegt" and get(["status", "NYSE", 2029]) == "annahme")
        pruefe("API naechsterHandelstag Datenende wirft", get(["naechsterHandelstag", "2100-12-31", "TSE"]) == "FEHLER")
        h_utc = {k: h(v) for k, v in r["tage"].items()}
        h_auf = h(json.dumps(ist_auf, sort_keys=True))
        for zone, rz in ergebnisse.items():
            if zone == "UTC":
                continue
            gleich = {k: h(v) for k, v in rz["ergebnisse"]["tage"].items()} == h_utc and \
                h(json.dumps(rz["ergebnisse"]["aufrufe"], sort_keys=True)) == h_auf
            pruefe(f"Zeitzone {zone} gleich UTC", gleich, "Ergebnis hängt von der Zeitzone ab")

    treffer, lesefehler = isolation_scan()
    pruefe("Isolation keine Seite nutzt das Bundle", not treffer, f"referenziert in {treffer[:5]}")
    pruefe("Isolation alle Dateien lesbar", not lesefehler, f"{lesefehler[:5]}")
    # Gegenprobe am Prüfer selbst: ein nicht listbares Verzeichnis muss als Lesefehler auffallen
    # (Codex P1b R2: os.walk ohne onerror überging es still, beide Prüfungen blieben grün).
    def kaputter_walk(pfad, onerror=None):
        if onerror:
            onerror(PermissionError(13, "Stub: kein Zugriff", pfad))
        return iter(())
    _, lf_stub = isolation_scan(walk=kaputter_walk)
    pruefe("Isolation meldet Traversierungsfehler", bool(lf_stub), "ein unlesbares Verzeichnis bleibt unbemerkt")

    print(f"verify_boersenkalender_js: {ZAEHLER['n'] - len(FEHLER)}/{ZAEHLER['n']} Prüfungen bestanden")
    for f in FEHLER:
        print("  FEHL", f)
    print(f"PROBE-ENDE {ZAEHLER['n']} Pruefungen")
    return 1 if FEHLER else 0


def isolation_scan(walk=os.walk) -> tuple[list[str], list[str]]:
    """Keine Seite und kein Seiten-Generator bindet das Bundle ein — auch nicht build_en.py oder die
    Deploy-Skripte, die Köpfe erzeugen (Codex P1b R1). Lese- UND Traversierungsfehler sind Befunde."""
    treffer, lesefehler = [], []

    def beim_listen(e):
        lesefehler.append(f"{getattr(e, 'filename', '?')}: {type(e).__name__}")
    for start in ("landing", "deploy", "blog", "seo"):
        for wurzel, _, dateien in walk(os.path.join(WURZEL, start), onerror=beim_listen):
            if os.sep + "output" in wurzel or os.sep + "data" in wurzel:
                continue   # erzeugte Ausgaben und Cron-Daten — der Generator wird geprüft
            for f in dateien:
                p = os.path.join(wurzel, f)
                if os.path.abspath(p) == os.path.abspath(ZIEL) or not f.endswith(
                        (".html", ".htm", ".js", ".json", ".py", ".sh", ".conf", ".j2", ".css")):
                    continue
                try:
                    with open(p, encoding="utf-8", errors="strict") as fh:
                        if "boersenkalender" in fh.read():
                            treffer.append(os.path.relpath(p, WURZEL))
                except (OSError, UnicodeDecodeError) as e:
                    lesefehler.append(f"{os.path.relpath(p, WURZEL)}: {type(e).__name__}")
    return treffer, lesefehler


if __name__ == "__main__":
    sys.exit(main())
