#!/usr/bin/env python3
"""Wächter: Fassade SA.holidays (landing/js/holidays.js) — Kalender V2, Bauvorlage
docs/review_prompts/2026-10-18_kalender_v2_entwurf*.md (Codex-Freigabe R3).

Vier Ebenen:
  1. alt      — die Fassade unter 'alt' ist die eingefrorene Momentaufnahme (scripts/fixtures/holidays_alt.json),
                je Zeitzone wörtlich (scripts/holidays_alt_momentaufnahme.py).
  2. Delegation — unter 'kalender_v1' liefert jede öffentliche Funktion dasselbe wie SA.boersenkalender, auf einem
                Raster (alle Börsen, jeder Tag 1990–2035) und für alle Ticker. Beweist nur die Weiterleitung.
  3. Richtigkeit — belegte Sollfälle mit Quelle (verify_kalender_sollfaelle.SOLLFAELLE) DURCH die Fassade, der
                Fehlervertrag B5 und die Zuordnungsfälle, alles wörtlich hier.
  4. Status   — alle Übergänge der Kalenderstatus-Tabelle mit Nachbarjahren als Literal (Entwurf v3, R2-3).

Aufruf:  py -3.14 scripts/verify_holidays_fassade.py     Exit 0 = alles erfüllt
"""
from __future__ import annotations

import calendar
import json
import os
import pathlib
import subprocess
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "scripts"))

from verify_kalender_sollfaelle import SOLLFAELLE  # noqa: E402

PROBE = WURZEL / "scripts" / "js" / "holidays_fassade_probe.js"
BOERSEN = ["NYSE", "XETRA", "LSE", "EURONEXT", "MILAN", "SIX", "STOCKHOLM", "OSLO", "TSE", "HKEX", "KRX",
           "CRYPTO", "FOREX"]
ZONEN = ("UTC", "America/New_York", "Pacific/Kiritimati", "Asia/Tokyo", "Europe/Berlin", "America/Adak")
F = "__fehler__"

# Fehlervertrag B5 (nur kalender_v1) und Zuordnung — (Aufruf, Soll). Soll F = KalenderFehler.
VERTRAG: list[tuple[list, object]] = [
    (["H", "isTradingDay", "2026-10-16"], F),                       # Börse fehlt (alt: NYSE)
    (["H", "isTradingDay", "2026-10-16", ""], F),
    (["H", "isTradingDay", "2026-10-16", "NONE"], F),               # 'NONE' ist keine Börse
    (["H", "isTradingDay", "2026-10-16", "MARS"], F),
    (["H", "isTradingDay", "2026-02-30", "NYSE"], F),               # ungültiges Datum
    (["H", "isTradingDay", "20261016", "NYSE"], F),
    (["H", "isTradingDay", "1884-12-31", "NYSE"], F),               # außerhalb 1885–2100
    (["H", "isTradingDay", "2101-01-03", "NYSE"], F),
    (["H", "nthTradingDay", 2026, 8, 0, "NYSE"], F),                # n < 1
    (["H", "nthTradingDay", 2026, 8, -1, "NYSE"], F),
    (["H", "nthTradingDay", 2026, 8, 1.5, "NYSE"], F),              # keine ganze Zahl
    (["H", "nthTradingDay", 2026, 13, 1, "NYSE"], F),
    (["H", "nthTradingDay", 2026, 8, 22, "NYSE"], None),            # n > Monatssumme (21) → null
    (["H", "nthTradingDay", 2026, 8, 21, "NYSE"], "2026-08-31"),
    (["H", "lastTradingDay", 2026, 8, "__undefined__", "NYSE"], "2026-08-31"),  # n fehlt → 1
    (["H", "lastTradingDay", 2026, 8, 0, "NYSE"], F),
    (["H", "nthTradingDayOfYear", 2026, 0, "NYSE"], F),
    (["H", "nthTradingDayOfYear", 2026, 1, "NYSE"], "2026-01-02"),
    (["H", "nthTradingDayOfYear", 2026, 400, "NYSE"], None),
    (["H", "nextTradingDay", 2026, 2, 30, "NYSE"], F),              # ungültiges Datum, kein Überlauf
    (["H", "nextTradingDay", "2026", 10, 16, "NYSE"], F),           # Zeichenkette statt Zahl (Codex Code R1)
    (["H", "nextTradingDay", 2026, "10", 16, "NYSE"], F),
    (["H", "nextTradingDay", 2026, 10, "16", "NYSE"], F),
    (["H", "nextTradingDay", 2026, 10, 16.5, "NYSE"], F),
    (["H", "nthTradingDay", "2026", 8, 1, "NYSE"], F),
    (["H", "lastTradingDay", 2026, "8", 1, "NYSE"], F),
    (["H", "nthTradingDayOfYear", 2026, "1", "NYSE"], F),
    (["H", "get", "2026", "NYSE"], F),
    (["H", "nextTradingDay", 2100, 12, 31, "TSE"], F),              # Kalenderende → Fehler, kein Ausgangsdatum
    (["H", "nextTradingDay", 2001, 9, 11, "NYSE"], "2001-09-17"),   # 6 geschlossene Tage am Stück
    (["H", "nextTradingDay", 2026, 5, 2, "TSE"], "2026-05-07"),     # Golden Week
    (["H", "nextTradingDay", 2026, 12, 31, "XETRA"], "2027-01-04"), # über den Jahreswechsel
    (["H", "nextTradingDay", 2026, 10, 17, "CRYPTO"], "2026-10-17"),
    (["H", "nextTradingDay", 2026, 10, 17, "FOREX"], "2026-10-19"),
    (["H", "isTradingDay", "2026-10-17", "FOREX"], False),          # Konvention Mo–Fr
    (["H", "isTradingDay", "2026-10-17", "CRYPTO"], True),          # Konvention täglich
    (["H", "isTradingDay", "2026-04-03", "FOREX"], True),           # Karfreitag offen
    (["H", "detect", ""], F),
    (["H", "detect", None], F),
    (["H", "detect", "^FOO"], F),                                   # unbekannter Index
    (["H", "detect", "FOO=F"], F),                                  # unbekannter Future
    (["H", "detect", "FOO.ZZ"], F),                                 # unbekanntes Suffix
    (["H", "detect", "11 Sektoren"], "NYSE"),                       # einfacher Name → Listingregel
    (["H", "detect", "AZN"], "NYSE"),                               # ADR
    (["H", "detect", "ASML"], "NYSE"),
    (["H", "detect", "SAP.DE"], "XETRA"),
    (["H", "detect", "ENR.F"], "XETRA"),
    (["H", "detect", "^N225"], "TSE"),
    (["H", "detect", "^HSI"], "HKEX"),
    (["H", "detect", "^KS11"], "KRX"),
    (["H", "detect", "NEL.OL"], "OSLO"),
    (["H", "detect", "BTC-USD"], "CRYPTO"),
    (["H", "detect", "EURUSD=X"], "FOREX"),
    (["H", "_NYSE_SONDER"], F),                                     # alte Regeln unter kalender_v1 gesperrt
    (["H", "_XETRA_SONDER"], F),
    (["H", "_nyse", 2026], F),
    (["H", "easter", 2026], [4, 5]),                                # Arithmetik bleibt
    (["H", "goodFriday", 2026], "2026-04-03"),
    (["H", "thanksgiving", 2026], "2026-11-26"),
]

# Statusübergänge (Entwurf v3, R2-3) — Literal, NICHT aus shared/exchange_holidays gelesen.
STATUS: dict[str, list[tuple[int, str]]] = {
    "NYSE": [(1885, "ungeprueft"), (1970, "ungeprueft"), (1971, "belegt"), (2028, "belegt"), (2029, "annahme"),
             (2100, "annahme")],
    "XETRA": [(2000, "ungeprueft"), (2001, "annahme"), (2002, "belegt"), (2026, "belegt"), (2027, "annahme")],
    "LSE": [(1999, "ungeprueft"), (2000, "annahme"), (2025, "annahme"), (2026, "belegt"), (2028, "belegt"),
            (2029, "annahme")],
    "TSE": [(1999, "ungeprueft"), (2000, "annahme"), (2001, "belegt"), (2027, "belegt"), (2028, "annahme")],
    **{b: [(1885, "ungeprueft"), (1999, "ungeprueft"), (2000, "annahme"), (2100, "annahme")]
       for b in ("EURONEXT", "SIX", "MILAN", "STOCKHOLM", "OSLO")},
    "HKEX": [(2015, "ungeprueft"), (2016, "annahme"), (2025, "annahme"), (2026, "belegt"), (2027, "ungeprueft")],
    "KRX": [(2015, "ungeprueft"), (2016, "annahme"), (2026, "annahme"), (2027, "ungeprueft")],
    "CRYPTO": [(1885, "konvention"), (2026, "konvention"), (2100, "konvention")],
    "FOREX": [(1885, "konvention"), (2026, "konvention"), (2100, "konvention")],
}

# Header unter kalender_v1 (Vertrag B1, Entwurf v2/v3): (Uhr UTC, Ticker, Kalenderticker, EN) → Sollzeile.
# Von Hand gegen die Börsenkalender geprüft (2026-10-18), nicht aus dem Code erzeugt.
HEADER: list[tuple[list, str]] = [
    (["2026-08-01T15:00:00Z", "SPY", None, False],
     "Heute: Sa 01.08.2026 · SPY · TDOM 0/21 · TWOY 31/53 · TDOY 145/251 · Q3 · MidTerm · geschlossen"),   # B1.4
    (["2026-08-03T15:00:00Z", "SPY", None, False],
     "Heute: Mo 03.08.2026 · SPY · TDOM 1/21 · TWOY 32/53 · TDOY 146/251 · Q3 · MidTerm"),
    # Berlin 05:00 am Sonntag, New York noch Samstag → Börsendatum 17.10. (nicht Browserdatum)
    (["2026-10-18T03:00:00Z", "SPY", None, False],
     "Heute: Sa 17.10.2026 · SPY · TDOM 12/22 · TWOY 42/53 · TDOY 199/251 · Q4 · MidTerm · geschlossen"),
    # 23:30 UTC = 01:30 Berlin Sonntag → XETRA-Datum 18.10.
    (["2026-10-17T23:30:00Z", "SAP.DE", None, False],
     "Heute: So 18.10.2026 · SAP.DE · TDOM 12/22 · TWOY 42/53 · TDOY 203/254 · Q4 · MidTerm · geschlossen"),
    (["2026-10-18T10:00:00Z", "BTC-USD", None, False],
     "Heute: So 18.10.2026 · BTC-USD · TDOM 18/31 · TWOY 42/53 · TDOY 291/365 · Q4 · MidTerm · "
     "Kalender: täglich (Konvention)"),
    (["2026-10-18T10:00:00Z", "EURUSD=X", None, False],
     "Heute: So 18.10.2026 · EURUSD=X · TDOM 12/22 · TWOY 42/53 · TDOY 207/261 · Q4 · MidTerm · geschlossen · "
     "Kalender: Mo–Fr ohne Feiertage (Konvention)"),
    (["2026-05-04T03:00:00Z", "^N225", None, False],                                     # Greenery Day
     "Heute: Mo 04.05.2026 · ^N225 · TDOM 1/18 · TWOY 19/53 · TDOY 80/242 · Q2 · MidTerm · geschlossen"),
    (["2026-10-16T15:00:00Z", "11 Sektoren", "XLK", False],
     "Heute: Fr 16.10.2026 · 11 Sektoren · TDOM 12/22 · TWOY 42/53 · TDOY 199/251 · Q4 · MidTerm · Kalender: XLK · NYSE"),
    (["2026-10-16T15:00:00Z", "^FOO", None, False], "Kein Börsenkalender für ^FOO"),
    (["2026-10-16T15:00:00Z", "", None, False], "Kein Börsenkalender für —"),
    (["2026-12-31T15:00:00Z", "SPY", None, False],
     "Heute: Do 31.12.2026 · SPY · TDOM 22/22 · TWOY 53/53 · TDOY 251/251 · Q4 · MidTerm"),
    (["2027-01-01T15:00:00Z", "SPY", None, False],                                         # ISO-Woche 53 von 2026
     "Heute: Fr 01.01.2027 · SPY · TDOM 0/19 · TWOY 53/53 · TDOY 0/251 · Q1 · Pre-Election · geschlossen"),
    (["2026-10-16T15:00:00Z", "^HSI", None, False],
     "Heute: Fr 16.10.2026 · ^HSI · TDOM 11/20 · TWOY 42/53 · TDOY 195/247 · Q4 · MidTerm"),
    (["2026-10-16T15:00:00Z", "ENEL.MI", None, False],
     "Heute: Fr 16.10.2026 · ENEL.MI · TDOM 12/22 · TWOY 42/53 · TDOY 203/254 · Q4 · MidTerm · Kalender: Annahme"),
    # ↑ numpy.busday_count mit den Schließtagen Borsa Italiana 2026 (1.1., 3.4., 6.4., 1.5., 24./25./31.12.)
    # 1960 ist „ungeprueft“: der Kalender hat Presidents Day am 15.02. (damals 22.02.) und schließt am Wahltag
    # 08.11.1960 nicht (belegt in election_calendar_exceptions.json) → Jahressumme 253 statt 252. Der Fall prüft
    # die Kennzeichnung; TDOM 1/23, TWOY 9/52 und TDOY 41 (43 Werktage − 2) sind unabhängig nachgerechnet.
    (["1960-03-01T15:00:00Z", "SPY", None, False],
     "Heute: Di 01.03.1960 · SPY · TDOM 1/23 · TWOY 9/52 · TDOY 41/253 · Q1 · Election · "
     "Kalender ungeprüft (exploratorisch)"),
    (["2026-08-01T15:00:00Z", "SPY", None, True],
     "Today: Sat 08/01/2026 · SPY · TDOM 0/21 · TWOY 31/53 · TDOY 145/251 · Q3 · MidTerm · closed"),
]

# Converter unter kalender_v1 (Entwurf v2 B3) — Klartext ohne Tags; Werte mit numpy.busday_count nachgerechnet.
CONVERTER: list[tuple[list, str]] = [
    (["2026-07-03", "NYSE"], "03.07.2026 Freitag · CDOY 184 · geschlossen · TDOM 2/22 · TDOY 125/251 (bisher gezählt)"),
    (["2026-08-01", "NYSE"], "01.08.2026 Samstag · CDOY 213 · geschlossen · TDOM 0/21 · TDOY 145/251 (bisher gezählt)"),
    (["2026-10-16", "XETRA"], "16.10.2026 Freitag · CDOY 289 · TDOM 12/22 (-11) · TDOY 203/254 (-52)"),
    (["2026-10-17", "FOREX"], "17.10.2026 Samstag · CDOY 290 · geschlossen · TDOM 12/22 · TDOY 207/261 (bisher gezählt)"
                              " · Kalender: Mo–Fr ohne Feiertage (Konvention)"),
    (["2026-10-17", "CRYPTO"], "17.10.2026 Samstag · CDOY 290 · TDOM 17/31 (-15) · TDOY 290/365 (-76)"
                               " · Kalender: täglich (Konvention)"),
    (["2028-02-29", "NYSE"], "29.02.2028 Dienstag · CDOY 60 · TDOM 20/20 (-1) · TDOY 40/251 (-212)"),
    (["2026-10-16", "KRX"], "16.10.2026 Freitag · CDOY 289 · TDOM 10/20 (-11) · TDOY 192/244 (-53) · Kalender: Annahme"),
    (["1960-03-01", "NYSE"], "01.03.1960 Dienstag · CDOY 61 · TDOM 1/23 (-23) · TDOY 41/253 (-213)"
                             " · Kalender dieses Jahres nicht belegt (exploratorisch)"),
    (["2026-10-16", "MARS"], "Für dieses Datum oder diese Börse lässt sich nicht rechnen."),
    (["2101-01-03", "NYSE"], "Für dieses Datum oder diese Börse lässt sich nicht rechnen."),
]

ergebnis = {"ok": 0, "fehl": []}


def pruefe(name: str, bedingung: bool, info: str = "") -> None:
    if bedingung:
        ergebnis["ok"] += 1
    else:
        ergebnis["fehl"].append(name)
        print(f"FEHL [{name}] {info}")


def probe(eingabe: dict, zone: str = "UTC") -> dict:
    p = subprocess.run(["node", str(PROBE), str(WURZEL)], input=json.dumps(eingabe), capture_output=True,
                       text=True, encoding="utf-8", env=dict(os.environ, TZ=zone), timeout=900)
    if p.returncode != 0:
        raise RuntimeError(f"Probe ({zone}) Exit {p.returncode}: {p.stderr[-600:]}")
    return json.loads(p.stdout)


def wert(e: dict):
    return F if "e" in e else e["w"]


SEITEN_UHR = "2026-08-01T15:00:00Z"
WECHSEL_SEITEN = ("dashboard", "tdom-analyse", "monatszyklus")
WECHSEL_FOLGE = ["SAP.DE", "BTC-USD", "SAP.DE"]


def seiten_pruefen() -> None:
    import io
    import re
    import tarfile
    import tempfile
    from concurrent.futures import ThreadPoolExecutor
    if not (WURZEL / "scripts" / "perf" / "node_modules" / "jsdom").exists():
        pruefe("Seiten: jsdom vorhanden (scripts/perf, npm ci)", False, "UNGEPRÜFT — ungeprüft ist nicht bestanden")
        return
    probe_js = WURZEL / "scripts" / "js" / "probe_header_seiten.js"
    seiten = sorted(p.stem for p in (WURZEL / "landing" / "pages").glob("*.html")
                    if "renderTradingDayHeader(" in p.read_text(encoding="utf-8"))
    pruefe("Seiten: 23 Header-Seiten gefunden", len(seiten) == 23, seiten)
    ref_datei = WURZEL / "scripts" / "fixtures" / "header_alt_seiten.json"
    schreiben = "--seiten-momentaufnahme" in sys.argv
    if schreiben and ref_datei.exists():
        pruefe("Seiten-Momentaufnahme nur einmal erzeugen", False, "existiert bereits")
        return
    with tempfile.TemporaryDirectory(prefix="sa_v2_head_") as tmp:
        alt_wurzel = pathlib.Path(tmp)
        if schreiben:   # einmalig aus dem Stand VOR V2 (HEAD muss vor der Fassade liegen)
            roh = subprocess.run(["git", "archive", "HEAD", "landing", "seo/tools"], cwd=WURZEL, capture_output=True).stdout
            tarfile.open(fileobj=io.BytesIO(roh)).extractall(tmp, filter="data")
            (alt_wurzel / "landing" / "data").mkdir(parents=True, exist_ok=True)
            for f in (WURZEL / "landing" / "data").glob("tickers.json"):
                (alt_wurzel / "landing" / "data" / f.name).write_bytes(f.read_bytes())

        def lauf(wurzel, seite, methode, folge=()):
            p = subprocess.run(["node", str(probe_js), str(wurzel), seite, methode, SEITEN_UHR, ",".join(folge)],
                               capture_output=True, text=True, encoding="utf-8", timeout=300, env=dict(os.environ, TZ="UTC"))
            try:
                return json.loads(p.stdout)
            except json.JSONDecodeError:
                return {"absturz": (p.stderr or p.stdout)[-300:]}
        alt_quelle = alt_wurzel if schreiben else WURZEL   # beim Prüfen ersetzt die Fixture diesen Teil (s. u.)
        auftraege = [(alt_quelle, s, "alt", ()) for s in seiten] + [(WURZEL, s, "alt", ()) for s in seiten] + \
                    [(WURZEL, s, "kalender_v1", WECHSEL_FOLGE if s in WECHSEL_SEITEN else ()) for s in seiten]
        konv_folge = [f"{d}|{b}" for (d, b), _ in CONVERTER[:6]]
        auftraege += [(alt_quelle, "converter", "alt", ["2026-07-02", "2026-12-24"]),
                      (WURZEL, "converter", "alt", ["2026-07-02", "2026-12-24"]),
                      (WURZEL, "converter", "kalender_v1", konv_folge)]
        with ThreadPoolExecutor(max_workers=8) as ex:
            erg = list(ex.map(lambda a: lauf(*a), auftraege))
    n = len(seiten)
    alt_head, alt_wt, v1 = erg[:n], erg[n:2 * n], erg[2 * n:3 * n]
    k_alt_head, k_alt_wt, k_v1 = erg[3 * n:]
    if schreiben:
        ref = {"schema": 1, "uhr": SEITEN_UHR, "quelle": "git archive HEAD (Stand vor Kalender V2)",
               "seiten": {s: alt_head[i].get("header") for i, s in enumerate(seiten)},
               "converter": k_alt_head.get("header")}
        ref_datei.write_text(json.dumps(ref, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("geschrieben:", ref_datei.relative_to(WURZEL))
    ref = json.loads(ref_datei.read_text(encoding="utf-8"))
    pruefe("Seiten: Momentaufnahme deckt alle Header-Seiten", sorted(ref["seiten"]) == seiten,
           sorted(set(ref["seiten"]) ^ set(seiten)))
    alt_head = [{"header": ref["seiten"].get(s)} for s in seiten]
    k_alt_head = {"header": ref["converter"]}
    # erwartete v1-Header: Headerfunktion mit dem Ticker, den die Seite unter alt anzeigt (2. Feld)
    faelle, wo = [], []
    for i, s in enumerate(seiten):
        h_alt = (alt_head[i].get("header") or [None])[0] or ""
        ticker = h_alt.split(" · ")[1] if " · " in h_alt else ""
        h_v1 = (v1[i].get("header") or [""])[0] or ""
        kt = re.search(r"Kalender: (\S+) · ", h_v1)
        faelle.append([SEITEN_UHR, ticker, kt.group(1) if kt else None, False]); wo.append((i, 0))
        if s in WECHSEL_SEITEN:
            for j, t in enumerate(WECHSEL_FOLGE, 1):
                faelle.append([SEITEN_UHR, t, None, False]); wo.append((i, j))
    p = subprocess.run(["node", str(WURZEL / "scripts" / "js" / "header_v1_probe.js"), str(WURZEL)],
                       input=json.dumps(faelle), capture_output=True, text=True, encoding="utf-8", timeout=300)
    soll_v1 = json.loads(p.stdout) if p.returncode == 0 else [None] * len(faelle)
    # Seiten, die den Header erst nach einer Nutzeraktion füllen (intermarket-shocks): leer bleibt leer
    for k, (i, j) in enumerate(wo):
        if j == 0 and not ((alt_head[i].get("header") or [""])[0] or ""):
            soll_v1[k] = ""
    for i, s in enumerate(seiten):
        for name, r in (("alt", alt_wt[i]), ("kalender_v1", v1[i])):
            pruefe(f"Seite {s} ({name}) lädt ohne Seitenfehler", "absturz" not in r and not r.get("fehler"),
                   (r.get("absturz") or (r.get("fehler") or [""])[0])[:200])
        pruefe(f"Seite {s}: Header unter alt = Momentaufnahme vor V2", alt_wt[i].get("header") == alt_head[i].get("header"),
               f"\n      HEAD {alt_head[i].get('header')}\n      neu  {alt_wt[i].get('header')}")
    for (i, j), soll in zip(wo, soll_v1):
        ist = (v1[i].get("header") or [None] * 4)[j] if len(v1[i].get("header") or []) > j else None
        pruefe(f"Seite {seiten[i]}: Header kalender_v1 [{j}]", ist == soll and soll is not None,
               f"\n      ist  {ist}\n      soll {soll}")
    i_sek = seiten.index("sektor-rotation") if "sektor-rotation" in seiten else None
    pruefe("Seite sektor-rotation: Header nennt den Kalenderticker (Korb)", i_sek is not None and
           re.search(r"Kalender: [A-Z^]+ · NYSE$", (v1[i_sek].get("header") or [""])[0] or "") is not None,
           (v1[i_sek].get("header") if i_sek is not None else None))
    pruefe("Converter-Seite: alt = Momentaufnahme vor V2", k_alt_wt.get("header") == k_alt_head.get("header"),
           f"{k_alt_head.get('header')} / {k_alt_wt.get('header')}")
    klar = lambda x: re.sub(r"<[^>]+>", "", (x or "").replace(' <span class="sep">·</span> ', " · "))
    kv = (k_v1.get("header") or [])[1:]
    for (fall, soll), ist in zip(CONVERTER[:6], kv + [None] * (6 - len(kv))):
        pruefe(f"Converter-Seite kalender_v1 {fall}", klar(ist) == soll, f"\n      ist  {klar(ist)}\n      soll {soll}")


def main() -> int:
    # 1. alt
    p = subprocess.run([sys.executable, str(WURZEL / "scripts" / "holidays_alt_momentaufnahme.py"), "--pruefen"],
                       capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
    pruefe("alt = Momentaufnahme", p.returncode == 0, (p.stdout + p.stderr).strip().splitlines()[-1:])

    # 2. Delegation (Raster) — einmal UTC
    ticker = sorted(x["t"] for x in json.loads((WURZEL / "landing/data/tickers.json").read_text(encoding="utf-8")))
    r = probe({"raster": {"von": 1990, "bis": 2035, "boersen": BOERSEN, "ticker": ticker}})["raster"]
    pruefe("Delegation Fassade = Bundle", r["abweichungen"] == 0 and r["vergleiche"] > 500_000,
           f"{r['abweichungen']} von {r['vergleiche']}: {r['beispiele']}")

    # 3. Sollfälle + Vertrag, unter allen Zonen identisch
    aufrufe = [["H", "isTradingDay", d, b] for (b, d, _s, _q, _a) in SOLLFAELLE]
    aufrufe += [v[0] for v in VERTRAG]
    aufrufe += [["K", "status", b, j] for b, fs in STATUS.items() for (j, _s) in fs]
    je_zone = {z: [wert(e) for e in probe({"aufrufe": aufrufe}, z)["ergebnisse"]] for z in ZONEN}
    basis = je_zone["UTC"]
    for z in ZONEN[1:]:
        pruefe(f"Zeitzone {z} = UTC", je_zone[z] == basis,
               [aufrufe[i] for i, (a, b) in enumerate(zip(basis, je_zone[z])) if a != b][:5])
    i = 0
    for (b, d, soll, quelle, anlass) in SOLLFAELLE:
        pruefe(f"Sollfall {b} {d} ({quelle}: {anlass})", basis[i] is soll, f"ist {basis[i]}, soll {soll}")
        i += 1
    for (aufruf, soll) in VERTRAG:
        pruefe(f"Vertrag {aufruf}", basis[i] == soll, f"ist {basis[i]!r}, soll {soll!r}")
        i += 1
    for b, fs in STATUS.items():
        for (j, soll) in fs:
            pruefe(f"Status {b} {j}", basis[i] == soll, f"ist {basis[i]!r}, soll {soll!r}")
            i += 1

    # 3b. Unabhängige Monatslisten aus den veröffentlichten Börsenkalendern (scripts/fixtures/kalender_monatslisten_2026.json)
    ml = json.loads((WURZEL / "scripts" / "fixtures" / "kalender_monatslisten_2026.json").read_text(encoding="utf-8"))["boersen"]
    anfr, erw = [], []
    for b, r in ml.items():
        y, m = map(int, r["monat"].split("-"))
        letzter = calendar.monthrange(y, m)[1]   # schaltjahrgerecht (29.02.2028, Codex Code R3)
        offen = r["offen"]
        summe = len(offen)
        marke = f"{b} {r['monat']}{'' if r['status'] == 'belegt' else ' (' + r['status'] + ')'}"
        for t in range(1, letzter + 1):
            ds = f"{y}-{m:02d}-{t:02d}"
            vor = sum(1 for x in offen if x <= ds)          # Sitzungen bis einschließlich ds im Monat
            ist_offen = ds in offen
            anfr.append(["H", "isTradingDay", ds, b]); erw.append((f"Monatsliste {marke} {ds} offen", ist_offen))
            anfr.append(["K", "nummern", [ds], b])
            erw.append((f"Monatsliste {marke} {ds} Nummern", [{
                "tdom": vor, "tdoy": r["sitzungen_vor_monat"] + vor,
                "tdom_rev": -(summe - vor + 1) if ist_offen else None,
                "tdoy_rev": "__egal__", "offen": ist_offen}]))
            nachfolger = next((x for x in offen if x >= ds), None)
            if nachfolger is None:   # nach der letzten Sitzung: belegter erster Tag des Folgemonats (Codex Code R2)
                fm = r.get("erste_sitzung_folgemonat") or {}
                nachfolger = fm.get("datum") or "__unbelegt__"
                if fm.get("status") not in ("belegt", "konvention"):
                    marke_t = marke + " (Folgemonat unbelegt)"
                else:
                    marke_t = marke
            else:
                marke_t = marke
            anfr.append(["H", "nextTradingDay", y, m, t, b])
            erw.append((f"Monatsliste {marke_t} {ds} nextTradingDay", nachfolger))
        # Monatsübergang immer prüfen (Codex Code R4): auch wenn der Monat mit einer offenen Sitzung endet
        fm = r.get("erste_sitzung_folgemonat") or {}
        if fm.get("datum") and fm.get("status") in ("belegt", "konvention"):
            y2, m2 = (y + 1, 1) if m == 12 else (y, m + 1)
            anfr.append(["H", "nextTradingDay", y2, m2, 1, b])
            erw.append((f"Monatsliste {marke} Übergang: nextTradingDay ab {y2}-{m2:02d}-01", fm["datum"]))
            anfr.append(["K", "naechste", f"{y}-{m:02d}-{letzter:02d}", b, False])
            erw.append((f"Monatsliste {marke} Übergang: streng nach dem Monatsletzten", fm["datum"]))
        else:
            pruefe(f"Monatsliste {marke}: Nachfolger belegt", False, "UNGEPRÜFT — kein belegter Folgemonat")
        for k in range(1, summe + 2):
            anfr.append(["H", "nthTradingDay", y, m, k, b])
            erw.append((f"Monatsliste {marke} nthTradingDay {k}", offen[k - 1] if k <= summe else None))
            anfr.append(["H", "lastTradingDay", y, m, k, b])
            erw.append((f"Monatsliste {marke} lastTradingDay {k}", offen[-k] if k <= summe else None))
    ml_ist = [wert(e) for e in probe({"aufrufe": anfr})["ergebnisse"]]
    folgemonat_ok = 0
    for (name, soll), ist, a in zip(erw, ml_ist, anfr):
        if soll == "__unbelegt__":
            # Folgemonat ohne Börsenquelle (Mailand 2027): nur „liegt im Folgemonat“ prüfbar — so benannt
            ok = isinstance(ist, str) and ist[:7] > f"{a[2]}-{a[3]:02d}"
            pruefe(name + " (nur Folgemonat geprüft)", ok, f"ist {ist!r}")
            folgemonat_ok += ok
            continue
        if isinstance(soll, list) and soll and soll[0].get("tdoy_rev") == "__egal__" and isinstance(ist, list) and ist:
            ist = [dict(ist[0], tdoy_rev="__egal__")]       # Jahressumme ist nicht Teil der Monatsliste
        pruefe(name, ist == soll, f"ist {ist!r}, soll {soll!r}")

    # 4b. Header unter kalender_v1, alle Zonen gleich
    hprobe = WURZEL / "scripts" / "js" / "header_v1_probe.js"
    hz = {}
    for z in ZONEN:
        p = subprocess.run(["node", str(hprobe), str(WURZEL)], input=json.dumps([f for f, _ in HEADER]),
                           capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, TZ=z), timeout=300)
        hz[z] = json.loads(p.stdout) if p.returncode == 0 else ["Probe-Exit %d: %s" % (p.returncode, p.stderr[-200:])]
    for z in ZONEN[1:]:
        pruefe(f"Header Zeitzone {z} = UTC", hz[z] == hz["UTC"])
    for (fall, soll), ist in zip(HEADER, hz["UTC"]):
        pruefe(f"Header {fall[1] or '(leer)'} {fall[0]}{' EN' if fall[3] else ''}", ist == soll,
               f"\n      ist  {ist}\n      soll {soll}")

    # 4c. Converter (ausgelieferte Datei seo/tools/…): alt = Momentaufnahme je Zone, kalender_v1 = Sollwerte
    import hashlib
    import re as _re
    cprobe = WURZEL / "scripts" / "js" / "converter_probe.js"

    def conv(methode: str, faelle: list, zone: str):
        p = subprocess.run(["node", str(cprobe), str(WURZEL), methode], input=json.dumps(faelle), capture_output=True,
                           text=True, encoding="utf-8", env=dict(os.environ, TZ=zone), timeout=600)
        return json.loads(p.stdout) if p.returncode == 0 else None

    calt = json.loads((WURZEL / "scripts" / "fixtures" / "converter_alt.json").read_text(encoding="utf-8"))
    for z, soll in calt["zonen"].items():
        ist = conv("alt", [[t, None] for t in calt["tage"]], z)
        ist = [hashlib.sha256(x.encode("utf-8")).hexdigest()[:12] for x in ist] if ist is not None else None
        pruefe(f"Converter alt = Momentaufnahme ({z})", ist == soll,
               "Probe gescheitert" if ist is None else f"{sum(a != b for a, b in zip(ist, soll))} Tage verschieden")
    klar = lambda s: _re.sub(r"<[^>]+>", "", s.replace(' <span class="sep">&middot;</span> ', " · "))
    cz = {z: conv("kalender_v1", [f for f, _ in CONVERTER], z) for z in ZONEN}
    for z in ZONEN[1:]:
        pruefe(f"Converter Zeitzone {z} = UTC", cz[z] == cz["UTC"] and cz[z] is not None)
    for (fall, soll), ist in zip(CONVERTER, cz["UTC"] or [None] * len(CONVERTER)):
        pruefe(f"Converter {fall}", ist is not None and klar(ist) == soll,
               f"\n      ist  {klar(ist) if ist else ist}\n      soll {soll}")

    # 4e. ALLE Statusfälle (STATUS) durch Header und Converter (Codex Code R2): genau das erwartete Kennzeichen
    REF_TICKER = {"NYSE": "SPY", "XETRA": "SAP.DE", "LSE": "BA.L", "TSE": "^N225", "EURONEXT": "AI.PA",
                  "SIX": "NESN.SW", "MILAN": "ENEL.MI", "STOCKHOLM": "VOLV-A.ST", "OSLO": "NEL.OL", "HKEX": "^HSI",
                  "KRX": "^KS11", "CRYPTO": "BTC-USD", "FOREX": "EURUSD=X"}
    H_TEXT = {"annahme": "Kalender: Annahme", "ungeprueft": "Kalender ungeprüft (exploratorisch)"}
    C_TEXT = {"annahme": "Kalender: Annahme", "ungeprueft": "Kalender dieses Jahres nicht belegt (exploratorisch)"}
    KONV = {"CRYPTO": "Kalender: täglich (Konvention)", "FOREX": "Kalender: Mo–Fr ohne Feiertage (Konvention)"}
    alle_h = set(H_TEXT.values()) | set(KONV.values())
    alle_c = set(C_TEXT.values()) | set(KONV.values())
    sf = [(b, j, st) for b, fs in STATUS.items() for (j, st) in fs]
    hf = [[f"{j}-03-02T15:00:00Z", REF_TICKER[b], None, False] for b, j, _ in sf]
    p = subprocess.run(["node", str(hprobe), str(WURZEL)], input=json.dumps(hf), capture_output=True, text=True,
                       encoding="utf-8", timeout=300)
    hs = json.loads(p.stdout) if p.returncode == 0 else [None] * len(sf)
    cs = conv("kalender_v1", [[f"{j}-03-02", b] for b, j, _ in sf], "UTC") or [None] * len(sf)
    for (b, j, st), h, c in zip(sf, hs, cs):
        soll_h = KONV.get(b) or H_TEXT.get(st)          # None = belegt: kein Kennzeichen
        soll_c = KONV.get(b) or C_TEXT.get(st)
        h_teile = set((h or "").split(" · "))
        c_teile = set(klar(c or "").split(" · "))
        pruefe(f"Status im Header {b} {j} ({st})", isinstance(h, str) and h.startswith("Heute:") and
               (h_teile & alle_h) == ({soll_h} if soll_h else set()), f"ist {h!r}")
        pruefe(f"Status im Converter {b} {j} ({st})", isinstance(c, str) and "CDOY" in c and
               (c_teile & alle_c) == ({soll_c} if soll_c else set()), f"ist {klar(c or '')!r}")

    # 4d. Statuskennzeichen in Header und Converter je Statusklasse (Codex Code R1, Befund 4)
    hstatus = [(["2027-03-01T15:00:00Z", "^HSI", None, False], "Kalender ungeprüft (exploratorisch)"),
               (["2000-03-01T15:00:00Z", "^N225", None, False], "Kalender: Annahme"),
               (["2026-10-16T15:00:00Z", "^HSI", None, False], "MidTerm"),          # HKEX 2026 belegt: kein Zusatz
               (["2026-10-16T15:00:00Z", "SAP.DE", None, False], "MidTerm")]        # XETRA 2026 belegt
    p = subprocess.run(["node", str(hprobe), str(WURZEL)], input=json.dumps([f for f, _ in hstatus]),
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    for (fall, ende), ist in zip(hstatus, json.loads(p.stdout) if p.returncode == 0 else [None] * len(hstatus)):
        pruefe(f"Header-Status {fall[1]} {fall[0][:4]}", isinstance(ist, str) and ist.endswith(ende), f"ist {ist!r}")
    cstatus = [(["2027-03-01", "HKEX"], "Kalender dieses Jahres nicht belegt (exploratorisch)"),
               (["2000-03-01", "TSE"], "Kalender: Annahme"),
               (["2026-10-16", "HKEX"], "TDOY 195/247 (-53)")]                     # belegt: kein Zusatz
    cist = conv("kalender_v1", [f for f, _ in cstatus], "UTC") or [None] * len(cstatus)
    for (fall, ende), ist in zip(cstatus, cist):
        pruefe(f"Converter-Status {fall}", isinstance(ist, str) and klar(ist).endswith(ende), f"ist {ist and klar(ist)!r}")

    # 6. Echte Seiten in jsdom: Header auf allen Header-Seiten (alt = Stand HEAD, kalender_v1 = Headerfunktion),
    #    Tickerwechsel A→B→A, Converter mit echtem Bootstrap (methode.js + Bundle).
    seiten_pruefen()

    # 5. Inventar der Stellen mit altem Börsenalphabet (Entwurf v2, B1)
    import re
    inv = json.loads((WURZEL / "scripts" / "fixtures" / "kalender_v2_inventar.json").read_text(encoding="utf-8"))
    muster = re.compile(inv["muster"])
    dateien = sorted((WURZEL / "landing" / "js").glob("*.js")) + sorted((WURZEL / "landing" / "pages").glob("*.html"))
    treffer = []
    for p in dateien:
        if p.name == "boersenkalender.js":
            continue
        rel = p.relative_to(WURZEL).as_posix()
        for nr, zeile in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if muster.search(zeile) and not re.match(inv["kommentarzeilen"], zeile):
                treffer.append((rel, nr, zeile))
    neu = [f"{d}:{n} {z.strip()[:90]}" for (d, n, z) in treffer
           if not any(e["datei"] == d and e["text"] in z for e in inv["stellen"])]
    verwaist = [f"{e['datei']}: {e['text'][:60]}" for e in inv["stellen"]
                if not any(d == e["datei"] and e["text"] in z for (d, _n, z) in treffer)]
    pruefe("Inventar: keine neue Stelle mit altem Börsenalphabet", not neu, neu[:5])
    pruefe("Inventar: kein verwaister Eintrag", not verwaist, verwaist[:5])
    phasen: dict[str, int] = {}
    for e in inv["stellen"]:
        phasen[e["phase"]] = phasen.get(e["phase"], 0) + 1
    print("  offen bis zur Phase:", ", ".join(f"{k} {v}" for k, v in sorted(phasen.items())))

    n_ok, fehl = ergebnis["ok"], ergebnis["fehl"]
    print(f"verify_holidays_fassade: {n_ok}/{n_ok + len(fehl)} Prüfungen bestanden")
    return 1 if fehl else 0


if __name__ == "__main__":
    sys.exit(main())
