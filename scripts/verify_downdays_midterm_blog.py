#!/usr/bin/env python3
"""
verify_downdays_midterm_blog.py — hält die Blogartikel „Down-Days im SPY“ und „S&P 500 in der letzten Woche vor
der Midterm-Wahl“ (DE+EN, 2026-10-30) deckungsgleich mit ihren Faktenblättern.

    py -3.14 scripts/verify_downdays_midterm_blog.py               # Prüfung
    py -3.14 scripts/verify_downdays_midterm_blog.py --tabellen     # gibt die Soll-Tabellen aus (zum Einfügen)
    py -3.14 scripts/verify_downdays_midterm_blog.py --mutationen   # baut bekannte Fehler ein, verlangt Rot

Geprüft wird nur der SICHTBARE Text (HTML-Kommentare entfernt):
  1. Datenstand: SHA-256 des SPY-Datenstands (im Faktenblatt), Snapshot-Kennung des Midterm-Artikels.
  2. Rechenkern: shared.elections.intervall_rendite gegen unabhängige Sollfälle (Hand gerechnet).
  3. Tabellen: jede Soll-Tabelle steht WÖRTLICH im Artikel — damit hängt jede Tabellenzahl an Zeile und Spalte
     (Codex Plan R1, Befund 9: eine bloße Liste erlaubter Zahlen genügt nicht).
  4. Fließtext: JEDE Zahl mit Einheit (%, Pp, pp) ist ein Wert des Faktenblatts — mit Vorzeichen, in der
     geschriebenen Rundung (Renditen 2 Stellen, Quoten 0/1 Stelle) und mit dem Dezimaltrenner der Sprache.
  5. Pflichtsätze (Kernaussagen mit Kontext) stehen im Text; Fallzahlen „X von Y“ / „X of Y“ und „n = X“
     gehören zum Faktenblatt.
  6. Bilder lösen sich zu existierenden Dateien auf, die erwarteten sind eingebunden.
"""
from __future__ import annotations

import copy
import math
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts" / "research"))
import down_days_fakten as DD                      # noqa: E402
import midterm_letzte_woche_fakten as MW           # noqa: E402
from shared.elections import intervall_rendite     # noqa: E402

BILD_DIR = REPO / "blog" / "posts" / "images"
MINUS = "−"
KOMMENTAR = re.compile(r"<!--.*?-->", re.S)
BILD = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
ZAHL = re.compile(r"(?<![\w.,])([+\-−]?)(\d+(?:[.,]\d+)?)\s?(%|Pp\b|pp\b)")


# ------------------------------------------------------------------ Formatierung
def z(wert, sprache, stellen=2, vz=True):
    s = f"{abs(wert):.{stellen}f}"
    if sprache == "de":
        s = s.replace(".", ",")
    if vz:
        s = ("+" if wert > 0 else MINUS if wert < 0 else "") + s
    elif wert < 0:
        s = MINUS + s
    return s


def p(wert, sprache, stellen=2, vz=True):
    return z(wert, sprache, stellen, vz) + (" %" if sprache == "de" else "%")


def q(anteil, sprache, stellen=0):
    return p(100 * anteil, sprache, stellen, vz=False)


def pp(wert, sprache):
    return z(wert, sprache) + (" Pp" if sprache == "de" else " pp")


def ganz(n, sprache):
    s = f"{n:,}"
    return s.replace(",", " " if sprache == "de" else ",")


# ------------------------------------------------------------------ Soll-Tabellen
STUFEN = ("1", "2", "3", "4")


def stufe_label(s, sp):
    return f"≤ {MINUS}{s} %" if sp == "de" else f"≤ {MINUS}{s}%"


def tabellen_dd(f, sp):
    de = sp == "de"
    t = {}
    zeilen = ["| Tagesverlust | Tage | Anteil der Handelstage | Jahre mit mindestens einem Fall |" if de else
              "| Daily loss | Days | Share of trading days | Years with at least one case |", "|---|---:|---:|---:|"]
    for s in STUFEN:
        st = f["stufen"][s]
        zeilen.append(f"| {stufe_label(s, sp)} | {ganz(st['n_gesamt'], sp)} | {q(st['quote'], sp, 1)} | "
                      f"{st['jahre_mit_ereignis']} {'von 21' if de else 'of 21'} |")
    t["haeufigkeit"] = "\n".join(zeilen)

    zeilen = ["| Ausgangstag | n (50 HT) | nach 15 HT | nach 30 HT | nach 50 HT |" if de else
              "| Starting day | n (50 TD) | after 15 TD | after 30 TD | after 50 TD |", "|---|---:|---:|---:|---:|"]
    b = f["basis"]
    zeilen.append(f"| {'alle Handelstage' if de else 'all trading days'} | {ganz(b['50']['alle']['n'], sp)} | "
                  + " | ".join(p(b[h]["alle"]["mittel"], sp) for h in ("15", "30", "50")) + " |")
    for s in STUFEN:
        hh = f["stufen"][s]["h"]
        zeilen.append(f"| {stufe_label(s, sp)} | {ganz(hh['50']['alle']['n'], sp)} | "
                      + " | ".join(p(hh[h]["alle"]["mittel"], sp) for h in ("15", "30", "50")) + " |")
    t["mittel"] = "\n".join(zeilen)

    zeilen = ["| Ausgangstag | Median nach 50 HT | positiv nach 50 HT | größter Zwischenverlust bis 15 HT (Mittel) |" if de else
              "| Starting day | Median after 50 TD | Positive after 50 TD | Largest interim loss within 15 TD (mean) |",
              "|---|---:|---:|---:|"]
    zeilen.append(f"| {'alle Handelstage' if de else 'all trading days'} | {p(b['50']['alle']['median'], sp)} | "
                  f"{q(b['50']['alle']['trefferquote'], sp)} | {p(f['basis_risiko15']['mittel'], sp)} |")
    for s in STUFEN:
        st = f["stufen"][s]
        a = st["h"]["50"]["alle"]
        zeilen.append(f"| {stufe_label(s, sp)} | {p(a['median'], sp)} | {q(a['trefferquote'], sp)} | "
                      f"{p(st['risiko15']['mittel'], sp)} |")
    t["risiko"] = "\n".join(zeilen)

    hh, bb = f["stufen"]["2"]["h"]["50"], f["basis"]["50"]
    zeilen = ["| Stichprobe (−2-%-Tage, 50 HT) | n | Mittel nach −2-%-Tag | Mittel aller Tage derselben Stichprobe | Abstand |" if de else
              "| Sample (−2% days, 50 TD) | n | Mean after −2% day | Mean of all days in the same sample | Difference |",
              "|---|---:|---:|---:|---:|"]
    namen = ({"alle": "alle Fälle", "ausgeduennt": "chronologisch ausgedünnt", "ohne_krisen": "ohne Herbst 2008 bis Juni 2009 und Frühjahr 2020",
              "erste_haelfte": "30.10.2006 bis 28.10.2016", "zweite_haelfte": "31.10.2016 bis 29.10.2026"} if de else
             {"alle": "all cases", "ausgeduennt": "thinned chronologically", "ohne_krisen": "excluding autumn 2008 to June 2009 and spring 2020",
              "erste_haelfte": "2006-10-30 to 2016-10-28", "zweite_haelfte": "2016-10-31 to 2026-10-29"})
    for k in ("alle", "ausgeduennt", "ohne_krisen", "erste_haelfte", "zweite_haelfte"):
        g = hh[k]
        basis = bb["alle" if k == "ausgeduennt" else k]
        zeilen.append(f"| {namen[k]} | {ganz(g['n'], sp)} | {p(g['mittel'], sp)} | {p(basis['mittel'], sp)} | "
                      f"{pp(g['mittel'] - basis['mittel'], sp)} |")
    t["robust"] = "\n".join(zeilen)
    return t


def tabellen_mw(f, sp):
    de = sp == "de"
    t = {}
    zeilen = ["| | 31 Midterms 1898–2022 | 13 Midterms 1974–2022 |" if de else
              "| | 31 midterms 1898–2022 | 13 midterms 1974–2022 |", "|---|---:|---:|"]
    a, b = f["alle"], f["ab_1971"]
    def zeile(name, fa, fb):
        zeilen.append(f"| {name} | {fa} | {fb} |")
    zeile("Mittel" if de else "Mean", p(a["woche"]["mittel"], sp), p(b["woche"]["mittel"], sp))
    zeile("Median", p(a["woche"]["median"], sp), p(b["woche"]["median"], sp))
    zeile("positiv" if de else "positive",
          f"{a['woche']['n_positiv']} {'von' if de else 'of'} {a['woche']['n']}",
          f"{b['woche']['n_positiv']} {'von' if de else 'of'} {b['woche']['n']}")
    for k, name in (("bester", "beste Woche" if de else "best week"), ("schlechtester", "schlechteste Woche" if de else "worst week")):
        zeile(name, f"{p(a['woche'][k][1], sp)} ({a['woche'][k][0]})", f"{p(b['woche'][k][1], sp)} ({b['woche'][k][0]})")
    zeile("dieselben Tage ohne Wahl (Mittel)" if de else "same days without an election (mean)",
          p(a["gepaart"]["woche_ohne_wahl"], sp), p(b["gepaart"]["woche_ohne_wahl"], sp))
    zeile("Abstand Wahljahr zu ohne Wahl" if de else "difference election year vs. no election",
          pp(a["gepaart"]["woche_differenz"], sp), pp(b["gepaart"]["woche_differenz"], sp))
    t["woche"] = "\n".join(zeilen)

    namen = {"-4": "t−4", "-3": "t−3", "-2": "t−2", "-1": "t−1",
             "0": "t0 (Referenztag)" if de else "t0 (reference day)", "1": "t+1 (Tag nach der Wahl)" if de else "t+1 (day after the election)"}
    zeilen = ["| Tag | Mittel Wahljahr | positiv | Mittel ohne Wahl | Abstand |" if de else
              "| Day | Mean election year | Positive | Mean without election | Difference |", "|---|---:|---:|---:|---:|"]
    for j in ("-4", "-3", "-2", "-1", "0", "1"):
        k, d = a["tage"][j], a["gepaart"]["tage_differenz"][j]
        zeilen.append(f"| {namen[j]} | {p(k['mittel'], sp)} | {k['n_positiv']} {'von' if de else 'of'} {k['n']} | "
                      f"{p(a['gepaart']['tage_ohne_wahl'][j], sp)} | {pp(d, sp)} |")
    t["tage"] = "\n".join(zeilen)
    return t


# ------------------------------------------------------------------ Artikel
ARTIKEL = [
    {"datei": "blog/posts/2026-10-30_spy-down-days-was-danach-passiert.md", "sprache": "de", "art": "dd",
     "bilder": ["spy-down-days/1_haeufigkeit_de.png", "spy-down-days/2_pfad_de.png", "spy-down-days/3_rendite_risiko_de.png"]},
    {"datei": "blog/posts/en/2026-10-30_spy-down-days-what-happens-next.md", "sprache": "en", "art": "dd",
     "bilder": ["spy-down-days/1_haeufigkeit_en.png", "spy-down-days/2_pfad_en.png", "spy-down-days/3_rendite_risiko_en.png"]},
    {"datei": "blog/posts/2026-10-30_sp500-letzte-woche-vor-midterm-wahl.md", "sprache": "de", "art": "mw",
     "bilder": ["midterm-letzte-woche/1_wochen_de.png", "midterm-letzte-woche/2_tage_de.png"]},
    {"datei": "blog/posts/en/2026-10-30_sp500-last-week-before-midterm-election.md", "sprache": "en", "art": "mw",
     "bilder": ["midterm-letzte-woche/1_wochen_en.png", "midterm-letzte-woche/2_tage_en.png"]},
]


# Reihen, die nur Charts speisen: ihre vielen Einzelwerte dürfen keine Fließtextzahl „erlauben“ (Mutationstest:
# +4,01 % ging als Median des Pfads bei Tag 39 durch).
_NUR_CHART = {"pfad", "je_jahr_quote", "wochen_werte"}


def _floats(d, schluessel=""):
    """Alle Fließkommazahlen des Faktenblatts als (wert, art): quote (0…1), pct (Prozentwerte)."""
    if isinstance(d, dict):
        for k, w in d.items():
            if k in _NUR_CHART:
                continue
            yield from _floats(w, k)
    elif isinstance(d, list):
        for w in d:
            yield from _floats(w, schluessel)
    elif isinstance(d, float):
        yield (d, "quote") if schluessel in ("trefferquote", "quote", "down_quote") or schluessel.isdigit() and d < 1 \
            else (d, "pct")


ALLE = r"\b(alle|allen|aller|all)\b"          # nicht „vor allem“


def vertraege(f, art, sp):
    """Kontextverträge für den Fließtext (Codex Code R1, Befund 2): jede Zahl mit Einheit muss genau einem
    Faktenblatt-Wert in der geschriebenen Form entsprechen UND im selben Satz die Bezugswörter dieses Werts tragen
    (Schwelle, Horizont, Kohorte). Eine erlaubte Zahl im falschen Zusammenhang fällt damit auf.
    Rückgabe: Liste (Zahl wie geschrieben, [Regex, …]) — alle Regexe müssen im Satz treffen."""
    if art == "dd":
        st, b = f["stufen"], f["basis"]
        s2 = st["2"]["h"]
        pos = r"positiv|positive|Trefferquote|hit rate"
        risiko = r"Zwischenverlust|interim|tiefer|deeper|unter dem Schluss|below|fell|nach unten"
        km = "!median"
        return [
            (p(s2["50"]["alle"]["mittel"], sp), ["@s:2", "@h:50", "@k:mittel", "@p:gesamt"]),
            (p(b["50"]["alle"]["mittel"], sp), ["@s:alle", "@h:50", "@k:mittel", "@p:gesamt"]),
            (q(s2["50"]["alle"]["trefferquote"], sp), ["@k:quote", "@s:2", "@h:50", "@p:gesamt"]),
            (q(b["50"]["alle"]["trefferquote"], sp), ["@k:quote", "@s:alle", "@h:50", "@p:gesamt"]),
            (p(st["2"]["risiko15"]["mittel"], sp), [risiko, "@s:2", "@h:15", "@k:mittel", "@p:gesamt"]),
            (p(f["basis_risiko15"]["mittel"], sp), [risiko, "@s:alle", "@h:15", "@k:mittel", "@p:gesamt"]),
            (p(st["4"]["risiko15"]["mittel"], sp), [risiko, "@s:4", "@h:15", "@k:mittel", "@p:gesamt"]),
            (pp(s2["50"]["alle"]["ueberrendite"], sp), ["@s:2", "@h:50", "@p:gesamt", "@k:mittel"]),
            (pp(s2["15"]["alle"]["ueberrendite"], sp), ["@s:2", "@h:15", "@p:gesamt", "@k:mittel"]),
            (p(st["3"]["h"]["15"]["alle"]["mittel"], sp), ["@s:3", "@h:15", "@k:mittel", "@p:gesamt"]),
            (p(s2["50"]["alle"]["median"], sp), ["@k:median", "@s:2", "@h:50", "@p:gesamt"]),
            (p(s2["50"]["alle"]["schlechtester"], sp), ["@k:extrem", r"schlechteste|worst", "@s:2", "@h:50", "@p:gesamt"]),
            (pp(s2["50"]["ausgeduennt"]["ueberrendite"], sp), ["@p:ausgeduennt", "@s?:2", "@h:50", "@k:mittel"]),
            (pp(s2["50"]["ohne_krisen"]["ueberrendite"], sp), ["@p:krisen", "@s?:2", "@h:50", "@k:mittel"]),
            (pp(s2["50"]["erste_haelfte"]["ueberrendite"], sp), ["@p:haelfte1", "@s?:2", "@h:50", "@k:mittel"]),
            (pp(s2["50"]["zweite_haelfte"]["ueberrendite"], sp), ["@p:haelfte2", "@s?:2", "@h:50", "@k:mittel"]),
            (q(f["down_quote"], sp, 1), [r"Minus|lower"]),
            (q(st["2"]["quote"], sp, 1), ["@s:2", "@p:gesamt"]),
        ]
    a, b = f["alle"], f["ab_1971"]
    wo = a["wahltag_offen"]
    alle31, nicht71 = r"\b31\b|1898", "!1971|1974"
    return [
        (p(a["woche"]["mittel"], sp), ["@f:woche", "@c?:alle", "@k:mittel"]),
        (p(a["woche"]["median"], sp), ["@f?:woche", "@c?:alle", "@k:median"]),
        (p(a["gepaart"]["woche_ohne_wahl"], sp), [r"ohne Wahl|without an election|Vergleichsjahre|comparison years|Nachbar|neighbo", "@c?:alle", "@k:mittel", "@f?:woche"]),
        (pp(a["gepaart"]["woche_differenz"], sp), [r"Abstand|gap|mehr als|above", "@c:alle", "@f?:woche"]),
        (p(b["woche"]["mittel"], sp), ["@c:1971", "@k:mittel", "@f?:woche"]),
        (pp(b["gepaart"]["woche_differenz"], sp), [r"Abstand|gap", "@c:1971", "@f?:woche"]),
        (p(a["woche"]["bester"][1], sp), [str(a["woche"]["bester"][0])]),
        (p(b["woche"]["schlechtester"][1], sp), [str(b["woche"]["schlechtester"][0])]),
        (p(a["gepaart"]["tage_ohne_wahl"]["-2"], sp), ["@f:t-2", "@k:mittel"]),
        (p(a["tage"]["0"]["mittel"], sp), ["@f:t0", "@c?:alle", "@k:mittel", "!geöffnet|open"]),
        (p(wo["mittel"], sp), ["@f:t0", "@c:offen", "@k:mittel"]),
        (p(a["tage"]["1"]["mittel"], sp), ["@f:t+1", "@c?:alle", "@k:mittel"]),
        (pp(f["vorlauf20"]["differenz"], sp), [r"\b20\b"]),
    ]


STUFE = {"1": r"(?<![\d,.])1(-| ?)%", "2": r"(?<![\d,.])2(-| ?)%", "3": r"(?<![\d,.])3(-| ?)%",
         "4": r"(?<![\d,.])4(-| ?)%", "alle": ALLE}
HORIZONT = {"15": r"\b15\b|drei Wochen|three weeks", "30": r"\b30\b", "50": r"\b50\b|fifty|fünfzig"}
# Kennzahl (Codex Code R5, Befund 2): ohne Kennzahlwort gilt der Mittelwert („stand er +4,00 % höher“)
KENNZAHL = {"mittel": r"\bMittel|mittler|average|\bmean", "median": r"median",
            "quote": r"positiv|positive|Trefferquote|hit rate", "quantil": r"Quantil|Perzentil|percentile|quantile",
            "extrem": r"schlechteste|beste[rn]?\b|worst|\bbest\b"}
# Teilstichprobe (Befund 1): Gesamtwerte dürfen nicht unter Ausdünnung, Krisenausschluss oder einer Hälfte stehen
STICHPROBE = {"ausgeduennt": r"ausgedünnt|überlapp|thinned|overlapping|bleiben 51|51 remain",
              "krisen": r"Krisen|crisis",
              "haelfte1": r"2006 bis 2016|2006 to 2016", "haelfte2": r"2016 bis 2026|2016 to 2026"}
# Midterm-Fenster und -Kohorte (Befund 3)
FENSTER = {"woche": r"Woche|week", "t+1": r"Wahlnacht|election night|nach der Wahl|after the election",
           "t0": r"\bt0\b|Referenz|reference|Wahltag|election day", "t-2": r"t−2"}
KOHORTE = {"alle": r"\b31\b|1898", "1971": r"1971|1974|\b13\b", "offen": r"1970|geöffnet|\bopen\b|\b14\b"}
KATEGORIEN = {"s": STUFE, "h": HORIZONT, "k": KENNZAHL, "p": STICHPROBE, "f": FENSTER, "c": KOHORTE}


def naechster(kategorie, satz, pos):
    """Wert der Kategorie, dessen Erwähnung der Zahl an Position pos am nächsten VORANGEHT; gibt es keine, die
    nächste danach. So hängt jede Zahl an ihrer Verluststufe und ihrem Horizont, auch wenn ein Satz mehrere nennt."""
    treffer = [(m.start(), m.end(), k) for k, rx in kategorie.items() for m in re.finditer(rx, satz, re.I)]
    vor = [t for t in treffer if t[1] <= pos]
    if vor:
        return max(vor, key=lambda t: t[1])[2]
    nach = [t for t in treffer if t[0] >= pos]
    return min(nach, key=lambda t: t[0])[2] if nach else None


def _trifft(regex, satz, pos=0):
    """Ein Bezugswort muss im Satz stehen; mit führendem „!“ darf es NICHT darin stehen (Median ≠ Mittel);
    „@s:k“/„@h:k“: die nächste Verluststufe bzw. der nächste Horizont ist k."""
    if regex.startswith("@"):
        kat, wert = regex[1:].split(":")
        optional = kat.endswith("?")
        ist = naechster(KATEGORIEN[kat.rstrip("?")], satz, pos)
        if ist is None and kat.rstrip("?") == "k":
            ist = "mittel"
        if ist is None and kat.rstrip("?") == "p":
            ist = "gesamt"
        return ist == wert or (optional and ist is None)
    if regex.startswith("!"):
        return re.search(regex[1:], satz, re.I) is None
    return re.search(regex, satz, re.I) is not None


def paar_vertraege(f, art):
    """Fallzahlen „X von Y“ im Fließtext mit ihrem Bezug im selben Satz (Codex Code R2, Befund 1: „10 von 14“
    durfte nicht für den Referenztag t0 stehen)."""
    if art == "dd":
        return [((f["down_days"], f["sitzungen"]), [r"Minus|lower"]),
                ((f["stufen"]["2"]["n_gesamt"], f["sitzungen"]), [r"\b2 ?%|−2"])]
    a, b = f["alle"], f["ab_1971"]
    wo = a["wahltag_offen"]
    return [((a["woche"]["n_positiv"], a["woche"]["n"]), ["@f:woche", "@c?:alle"]),
            ((a["gepaart"]["differenz_positiv"], a["gepaart"]["n_tripel"]), [r"vorn|ahead", "@f:woche", "@c?:alle"]),
            ((b["gepaart"]["differenz_positiv"], b["gepaart"]["n_tripel"]), [r"vorn|ahead", "@c:1971"]),
            ((a["t0_am_wahltag"], a["woche"]["n"]), ["@f:t0"]),          # die 14 selbst trifft KOHORTE[offen]
            ((a["tage"]["-1"]["n_positiv"], a["tage"]["-1"]["n"]), [r"vor t0|before t0|t−1"]),
            ((a["tage"]["0"]["n_positiv"], a["tage"]["0"]["n"]), ["@f:t0", "@c?:alle", "!geöffnet|open"]),
            ((wo["n_positiv"], wo["n"]), ["@c:offen"]),
            ((a["tage"]["1"]["n_positiv"], a["tage"]["1"]["n"]), ["@f:t+1", "@c?:alle"])]


def n_vertraege(f, art):
    """„n = X“: jede Fallzahl nur zusammen mit ihrer Kohorte (Verluststufe bzw. Wahlauswahl) im Satz; eine fremde
    Verluststufe im selben Satz ist verboten."""
    if art == "dd":
        aus = []
        teil = {"ausgeduennt": "ausgeduennt", "ohne_krisen": "krisen", "erste_haelfte": "haelfte1",
                "zweite_haelfte": "haelfte2"}
        for k in "1234":
            for h, hh in f["stufen"][k]["h"].items():
                aus.append((hh["alle"]["n"], [f"@s:{k}", f"@h:{h}", "@p:gesamt"]))
                for name, p_ in teil.items():
                    if hh.get(name):
                        aus.append((hh[name]["n"], [f"@s?:{k}", f"@h:{h}", f"@p:{p_}"]))
        for h, b in f["basis"].items():
            aus.append((b["alle"]["n"], ["@s:alle", f"@h:{h}", "@p:gesamt"]))
        return aus
    a, b = f["alle"], f["ab_1971"]
    return [(a["woche"]["n"], ["@c?:alle", "!1971|1974|1970|geöffnet|open"]),
            (b["woche"]["n"], ["@c:1971"]),
            (a["wahltag_offen"]["n"], ["@c:offen"])]


ZAHLWORT = {"de": {6: "sechs", 11: "elf"}, "en": {6: "six", 11: "eleven"}}


def satz_um(text, i, j):
    """Satz, der die Stelle [i, j) enthält: Grenze ist ein Satzzeichen vor Leerraum oder ein Umbruch — außer dem
    Punkt eines Datums vor einem Monatsnamen („3. November“). Dezimalpunkte stehen nie vor Leerraum."""
    grenze = re.compile(r"[.!?](?=\s)(?!\s+(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|"
                        r"November|Dezember)\b)|\n")
    anfang = max([m.end() for m in grenze.finditer(text, 0, i)] + [0])
    m = grenze.search(text, j)
    return text[anfang: m.start() if m else len(text)], anfang


def fallzahlen(f, art):
    if art == "dd":
        ns = {f["sitzungen"], f["down_days"]}
        for s in f["stufen"].values():
            ns.add(s["n_gesamt"])
            for hh in s["h"].values():
                ns.update(g["n"] for g in hh.values() if isinstance(g, dict))
        ns.update(b["alle"]["n"] for b in f["basis"].values())
        paare = {(f["down_days"], f["sitzungen"])}
        for s in f["stufen"].values():
            a = s["h"]["50"]["alle"]
            paare.add((a["n_positiv"], a["n"]))
            paare.add((s["jahre_mit_ereignis"], 21))
            paare.add((s["n_gesamt"], f["sitzungen"]))
        return paare, ns
    paare, ns = set(), {f["vorlauf20"]["n_tripel"]}
    for t in ("alle", "ab_1971"):
        a = f[t]
        ns.update({a["woche"]["n"], a["gepaart"]["n_tripel"]})
        paare.add((a["woche"]["n_positiv"], a["woche"]["n"]))
        paare.add((a["gepaart"]["differenz_positiv"], a["gepaart"]["n_tripel"]))
        paare.update((k["n_positiv"], k["n"]) for k in a["tage"].values())
        paare.add((a["t0_am_wahltag"], a["woche"]["n"]))
        paare.add((a["wahltag_offen"]["n_positiv"], a["wahltag_offen"]["n"]))
    return paare, ns


def pflicht(f, art, sp):
    """Kernaussagen mit Kontext: (Beschreibung, Regex) — Zahl und Bezug stehen im selben Satz."""
    de = sp == "de"
    if art == "dd":
        a2 = f["stufen"]["2"]["h"]
        b = f["basis"]
        j08, j17 = f["stufen"]["2"]["je_jahr"].get("2008", 0), f["stufen"]["2"]["je_jahr"].get("2017", 0)
        return [
            ("Trefferquote nicht höher", r"nicht höher, sondern leicht niedriger" if de else r"not higher but slightly lower"),
            ("2008 gezählt", (rf"2008 brachte allein {j08} Tage" if de else rf"2008 alone brought {j08} days")),
            ("2008 FAQ", (rf"2008 gab es {j08} solcher Tage" if de else rf"2008 had {j08} such days")),
            ("2017 keiner", (r"2017 keinen" if de else r"2017 none") if j17 == 0 else r"$^"),
            ("−2-%-Tage gezählt", re.escape(ganz(f["stufen"]["2"]["n_gesamt"], sp)) + (r" Handelstage" if de else r" trading days")),
            ("Mittel 50 HT nach −2 % mit Basis", re.escape(p(a2["50"]["alle"]["mittel"], sp)) + r"[^.\n]*" + re.escape(p(b["50"]["alle"]["mittel"], sp))),
            ("Trefferquote 50 HT nach −2 % mit Basis", re.escape(q(a2["50"]["alle"]["trefferquote"], sp)) + r"[^.\n]*" + re.escape(q(b["50"]["alle"]["trefferquote"], sp))),
            ("Zwischenverlust −2 % mit Basis", re.escape(p(f["stufen"]["2"]["risiko15"]["mittel"], sp)) + r"[^.\n]*" + re.escape(p(f["basis_risiko15"]["mittel"], sp))),
            ("ausgedünnt 50 HT Abstand", re.escape(pp(a2["50"]["ausgeduennt"]["ueberrendite"], sp))),
        ]
    a, b = f["alle"], f["ab_1971"]
    return [
        ("Woche Mittel und positiv", re.escape(p(a["woche"]["mittel"], sp)) + r"[^.\n]*" + re.escape(f"{a['woche']['n_positiv']} {'von' if de else 'of'} {a['woche']['n']}")),
        ("gepaart Woche", re.escape(p(a["gepaart"]["woche_wahl"], sp)) + r"[^.\n]*" + re.escape(p(a["gepaart"]["woche_ohne_wahl"], sp)) + r"[^.\n]*" + re.escape(pp(a["gepaart"]["woche_differenz"], sp))),
        ("seit 1971 Abstand", re.escape(pp(b["gepaart"]["woche_differenz"], sp))),
        ("Bezug ±20-Artikel", re.escape(pp(f["vorlauf20"]["differenz"], sp))),
        ("negative Wochen", rf"{'in' if de else 'in'} {ZAHLWORT[sp][a['woche']['n'] - a['woche']['n_positiv']]} "
                            + (r"Wahljahren" if de else r"election years")),
        ("deutlich nur", (r"deutlich nur " if de else r"clearly so only in ") + str(a["woche"]["schlechtester"][0])),
        ("echte Wahltage", re.escape(p(a["wahltag_offen"]["mittel"], sp)) + r"[^\n]*?"
                           + re.escape(f"{a['wahltag_offen']['n_positiv']} {'von' if de else 'of'} {a['wahltag_offen']['n']}")),
    ]


def sichtbar(text):
    return KOMMENTAR.sub("", text)


def pruefe_artikel(a, text, f, bild_dir=BILD_DIR):
    fehler, t, sp, art = [], sichtbar(text), a["sprache"], a["art"]
    ort0 = a["datei"]
    tab = tabellen_dd(f, sp) if art == "dd" else tabellen_mw(f, sp)
    for name, soll in tab.items():
        if soll not in t:
            fehler.append(f"{ort0}: Soll-Tabelle „{name}“ steht nicht wörtlich im Text")
    ohne_tab = t
    for soll in tab.values():
        ohne_tab = ohne_tab.replace(soll, "")
    vt = vertraege(f, art, sp)
    falsch_trenner = "." if sp == "de" else ","
    for m in ZAHL.finditer(ohne_tab):
        vz, zahl, einheit = m.groups()
        ort = f"{ort0}: „{ohne_tab[max(0, m.start() - 40):m.end()].strip()}“"
        if falsch_trenner in zahl:
            fehler.append(f"{ort}: Dezimaltrenner passt nicht zur Sprache")
            continue
        stellen = len(re.split(r"[.,]", zahl)[1]) if re.search(r"[.,]", zahl) else 0
        if einheit == "%" and stellen == 0 and zahl in ("1", "2", "3", "4") and vz != "+":
            continue                                       # Schwellen „2 %“ / „−2 %“
        vz = MINUS if vz == "-" else vz
        geschrieben = vz + zahl + ((" %" if sp == "de" else "%") if einheit == "%" else (" Pp" if sp == "de" else " pp"))
        satz, off = satz_um(ohne_tab, m.start(), m.end())
        kandidaten = [kw for wert, kw in vt if wert == geschrieben]
        if not kandidaten:
            fehler.append(f"{ort}: Zahl ist kein Faktenblatt-Wert des Fließtexts (Wert/Vorzeichen/Rundung/Einheit)")
        elif not any(all(_trifft(r, satz, m.start() - off) for r in kw) for kw in kandidaten):
            fehler.append(f"{ort}: Zahl steht ohne ihren Bezug im Satz (erwartet: {kandidaten})")
    for name, rx in pflicht(f, art, sp):
        if not re.search(rx, ohne_tab):
            fehler.append(f"{ort0}: Pflichtaussage „{name}“ fehlt im Fließtext")
    paare, ns = fallzahlen(f, art)
    pv = paar_vertraege(f, art)
    for m in re.finditer(r"\b(\d[\d\u202f,]*) (?:von|of) (\d[\d\u202f,]*\d|\d)\b", ohne_tab):
        paar = (int(re.sub(r"[\u202f,]", "", m.group(1))), int(re.sub(r"[\u202f,]", "", m.group(2))))
        satz, off = satz_um(ohne_tab, m.start(), m.end())
        kand = [kw for pr, kw in pv if pr == paar]
        if not kand:
            fehler.append(f"{ort0}: Fallzahl „{m.group(0)}“ passt nicht zum Faktenblatt")
        elif not any(all(_trifft(r, satz, m.start() - off) for r in kw) for kw in kand):
            fehler.append(f"{ort0}: Fallzahl „{m.group(0)}“ steht ohne ihren Bezug im Satz")
    # „n = X“ gehört zur Kohorte des Satzes (Codex Code R3, Befund 2: „Median … (n = 42) … +5,77 %“ mischte die
    # −4-%-Kohorte mit einem Wert der −2-%-Kohorte)
    nv = n_vertraege(f, art)
    for m in re.finditer(r"\bn = (\d[\d\u202f ,]*\d|\d)\b", ohne_tab):
        x = int(re.sub(r"[\u202f ,]", "", m.group(1)))
        satz, off = satz_um(ohne_tab, m.start(), m.end())
        kand = [kw for n_, kw in nv if n_ == x]
        if not kand:
            fehler.append(f"{ort0}: Fallzahl n = {m.group(1)} passt nicht zum Faktenblatt")
        elif not any(all(_trifft(r, satz, m.start() - off) for r in kw) for kw in kand):
            fehler.append(f"{ort0}: Fallzahl n = {m.group(1)} steht neben einer fremden Kohorte")
    bilder = BILD.findall(t)
    for bd in bilder:
        if not (bild_dir / bd).is_file():
            fehler.append(f"{ort0}: Bild {bd} existiert nicht")
    for bd in a["bilder"]:
        if bd not in bilder:
            fehler.append(f"{ort0}: Bild {bd} nicht eingebunden")
    return fehler


def pruefe_kern():
    """intervall_rendite gegen Hand gerechnete Sollfälle (Pfad mit n = 3: Offsets −3 … +3)."""
    fehler = []
    pf = {"c": [100.0, 110.0, 99.0, 108.9, None, 120.0, 132.0]}
    faelle = [((-3, 0), 8.9), ((-3, -1), -1.0), ((-1, 0), 10.0), ((-2, -1), -10.0),
              ((0, 1), None), ((-3, 1), None), ((2, 3), 10.0), ((-4, 0), None), ((0, 4), None), ((0, 0), None)]
    for (a, b), soll in faelle:
        ist = intervall_rendite(pf, a, b, n=3)
        if (soll is None) != (ist is None) or (soll is not None and not math.isclose(ist, soll, abs_tol=1e-9)):
            fehler.append(f"intervall_rendite({a}, {b}) = {ist}, Soll {soll}")
    return fehler


def fakten_je_art():
    return {"dd": DD.fakten(DD.lade()), "mw": MW.fakten(MW.lade())}


def pruefe(artikel=ARTIKEL):
    fehler = pruefe_kern()
    fj = fakten_je_art()
    if fj["mw"]["snapshot"] != "midterm-2026-10":
        fehler.append("Midterm-Faktenblatt rechnet nicht auf dem Snapshot midterm-2026-10")
    for a in artikel:
        pfad = REPO / a["datei"]
        if not pfad.exists():
            fehler.append(f"{a['datei']}: Datei fehlt")
            continue
        fehler += pruefe_artikel(a, pfad.read_text(encoding="utf-8"), fj[a["art"]])
    return fehler


def _einmal(text, alt, neu):
    assert alt in text, alt
    return text.replace(alt, neu, 1)


def mutationen():
    fj = fakten_je_art()
    faelle = []
    import shared.elections as el
    orig = el.intervall_rendite
    global intervall_rendite
    intervall_rendite = lambda pf, a, b, n=60: orig(pf, a, b + 1, n) if a < 0 else orig(pf, a, b, n)  # noqa: E731
    faelle.append(("Kern: Intervall um eine Sitzung verlängert", pruefe_kern()))
    intervall_rendite = orig
    import tempfile
    for name, modul, quelle in (("SPY-Datenstand", DD, DD.DATEI), ("Midterm-Snapshot", MW, MW.SNAPSHOT)):
        roh = quelle.read_bytes()
        # Inhalt ändern, Kennung (snapshot_id / Dateiname) unverändert lassen
        veraendert = roh.replace(b'"2022-11-08"', b'"2022-11-09"', 1) if b'"2022-11-08"' in roh else roh.replace(b"]]", b"],[\"2026-10-29\",1,0]]", 1)
        with tempfile.TemporaryDirectory() as tmp:
            ziel = pathlib.Path(tmp) / quelle.name
            ziel.write_bytes(veraendert)
            try:
                modul.lade(ziel)
                faelle.append((f"{name}: Inhalt verändert, Kennung gleich", []))
            except SystemExit as e:
                faelle.append((f"{name}: Inhalt verändert, Kennung gleich", [str(e)]))
    for a in ARTIKEL:
        text = (REPO / a["datei"]).read_text(encoding="utf-8")
        f = fj[a["art"]]
        if pruefe_artikel(a, text, f):
            print(f"Grundzustand {a['datei']} nicht grün — Mutationen sinnlos")
            return 1
        sp, L = a["sprache"], a["sprache"].upper() + "/" + a["art"]
        if a["art"] == "dd":
            f2 = copy.deepcopy(f); f2["stufen"]["2"]["h"]["50"]["alle"]["mittel"] += 0.01
            m50 = p(f["stufen"]["2"]["h"]["50"]["alle"]["mittel"], sp)
            r2 = p(f["stufen"]["2"]["risiko15"]["mittel"], sp)
            faelle += [
                (f"{L}: Faktenblatt verschoben (Tabelle/Text alt)", pruefe_artikel(a, text, f2)),
                (f"{L}: Kernzahl im Fließtext falsch gerundet", pruefe_artikel(a, _einmal(text, m50 + " ", z(f["stufen"]["2"]["h"]["50"]["alle"]["mittel"] + 0.01, sp) + (" % " if sp == "de" else "% ")), f)),
                (f"{L}: Minus beim Zwischenverlust fehlt", pruefe_artikel(a, _einmal(text, r2, r2.replace(MINUS, "")), f)),
                (f"{L}: Tabellenzelle vertauscht", pruefe_artikel(a, text.replace(tabellen_dd(f, sp)["mittel"], tabellen_dd(f, sp)["mittel"].replace(m50, p(f["basis"]["50"]["alle"]["mittel"], sp))), f)),
                (f"{L}: Bild fehlt", pruefe_artikel(a, text.replace("2_pfad_", "x_pfad_"), f)),
                # Gegenproben aus Codex Code R1, Befund 2 (blieben mit der reinen Werteliste grün)
                (f"{L}: Basisquote als −2-%-Quote", pruefe_artikel(a, text + ("\n\nNach −2-%-Tagen beträgt die Trefferquote nach 50 HT 73 %.\n" if sp == "de" else "\n\nAfter −2% days the hit rate after 50 TD is 73%.\n"), f)),
                (f"{L}: Jahreszahl 2008 falsch", pruefe_artikel(a, _einmal(text, "2008 gab es 39 solcher" if sp == "de" else "2008 had 39 such", "2008 gab es 211 solcher" if sp == "de" else "2008 had 211 such"), f)),
                (f"{L}: Aussage umgedreht", pruefe_artikel(a, _einmal(text, "nicht höher, sondern leicht niedriger" if sp == "de" else "not higher but slightly lower", "höher" if sp == "de" else "higher"), f)),
                (f"{L}: Trefferquote auf 15 HT umgeschrieben", pruefe_artikel(a, _einmal(text, "Positiv nach 50 Handelstagen" if sp == "de" else "After 50 trading days **69%**", "Positiv nach 15 Handelstagen" if sp == "de" else "After 15 trading days **69%**"), f)),
                (f"{L}: Median auf 15 HT umgeschrieben", pruefe_artikel(a, _einmal(text, "Der Median nach 50 Handelstagen" if sp == "de" else "The median after 50 trading days", "Der Median nach 15 Handelstagen" if sp == "de" else "The median after 15 trading days"), f)),
                # Gegenproben aus Codex Code R3
                (f"{L}: Quote der −4-%-Kohorte zugeschrieben", pruefe_artikel(a, text + ("\n\nNach −4-%-Tagen waren nach 50 HT 69 % positiv.\n" if sp == "de" else "\n\nAfter −4% days 69% were positive after 50 TD.\n"), f)),
                (f"{L}: Basismittel mit 15 HT", pruefe_artikel(a, text + ("\n\nÜber alle Tage betrug die mittlere Rendite nach 15 HT +2,34 %.\n" if sp == "de" else "\n\nAcross all days the mean return after 15 TD was +2.34%.\n"), f)),
                (f"{L}: Zwischenverlust der −1-%-Kohorte", pruefe_artikel(a, text + ("\n\nNach −1-%-Tagen betrug der mittlere Zwischenverlust bis 15 HT −4,78 %.\n" if sp == "de" else "\n\nAfter −1% days the mean interim loss within 15 TD was −4.78%.\n"), f)),
                (f"{L}: fremde Fallzahl am Median", pruefe_artikel(a, _einmal(text, "mit +5,77 %" if sp == "de" else "for −2% days, +5.77%", "(n = 42) mit +5,77 %" if sp == "de" else "for −2% days (n = 42), +5.77%"), f)),
                # Gegenproben aus Codex Code R4
                (f"{L}: Zwischenverlust als Median", pruefe_artikel(a, _einmal(text, "im Mittel bis zu **−4,78 %**" if sp == "de" else "fell on average to as low as **−4.78%**", "im Median bis zu **−4,78 %**" if sp == "de" else "fell in the median to as low as **−4.78%**"), f)),
                (f"{L}: Zwischenverlust als Rendite", pruefe_artikel(a, text + ("\n\nNach −2-%-Tagen betrug die mittlere Rendite nach 15 Handelstagen −4,78 %.\n" if sp == "de" else "\n\nAfter −2% days the mean return after 15 trading days was −4.78%.\n"), f)),
                (f"{L}: schlechtester Fall mit 15 HT", pruefe_artikel(a, _einmal(text, "endete 50 Handelstage später bei −29,71 %" if sp == "de" else "ended 50 trading days later at −29.71%", "endete 15 Handelstage später bei −29,71 %" if sp == "de" else "ended 15 trading days later at −29.71%"), f)),
                (f"{L}: Ausdünnung mit 15 HT", pruefe_artikel(a, text + ("\n\nChronologisch ausgedünnt betrug der Abstand nach −2-%-Tagen nach 15 Handelstagen +0,34 Pp.\n" if sp == "de" else "\n\nThinned chronologically, the gap after −2% days after 15 trading days was +0.34 pp.\n"), f)),
                (f"{L}: Basis-n des falschen Horizonts", pruefe_artikel(a, text + ("\n\nÜber alle Handelstage betrug die Rendite nach 50 Handelstagen +2,34 % (n = 5\u202f016).\n" if sp == "de" else "\n\nAcross all trading days the return after 50 trading days was +2.34% (n = 5,016).\n"), f)),
                # Gegenproben aus Codex Code R5
                (f"{L}: Gesamtmittel als ausgedünnter Wert", pruefe_artikel(a, text + ("\n\nNach −2-%-Tagen beträgt die chronologisch ausgedünnte mittlere Rendite nach 50 Handelstagen +4,00 %.\n" if sp == "de" else "\n\nAfter −2% days the chronologically thinned mean return after 50 trading days is +4.00%.\n"), f)),
                (f"{L}: Ausdünnung der −4-%-Kohorte", pruefe_artikel(a, text + ("\n\nNach −4-%-Tagen beträgt der chronologisch ausgedünnte Abstand nach 50 Handelstagen +0,34 Pp.\n" if sp == "de" else "\n\nAfter −4% days the chronologically thinned gap after 50 trading days is +0.34 pp.\n"), f)),
                (f"{L}: Mittel als Quantil", pruefe_artikel(a, text + ("\n\nNach −2-%-Tagen betrug das 10-Prozent-Quantil des Zwischenverlusts bis 15 Handelstage −4,78 %.\n" if sp == "de" else "\n\nAfter −2% days the 10th percentile of the interim loss within 15 trading days was −4.78%.\n"), f)),
                (f"{L}: Mittel als Trefferquote", pruefe_artikel(a, text + ("\n\nNach −2-%-Tagen betrug die Trefferquote nach 50 Handelstagen +4,00 %.\n" if sp == "de" else "\n\nAfter −2% days the hit rate after 50 trading days was +4.00%.\n"), f)),
                # Gegenproben aus Codex Code R6
                (f"{L}: Abstand der Mittel als Abstand der Mediane", pruefe_artikel(a, _einmal(text, "betrug der Abstand nach 50 Handelstagen +1,66 Pp" if sp == "de" else "the gap after 50 trading days was +1.66 pp", "betrug der Abstand der Mediane nach 50 Handelstagen +1,66 Pp" if sp == "de" else "the gap in medians after 50 trading days was +1.66 pp"), f)),
                (f"{L}: Gesamt-n an ausgedünntem Wert", pruefe_artikel(a, text + ("\n\nNach −2-%-Tagen beträgt der chronologisch ausgedünnte Abstand nach 50 Handelstagen +0,34 Pp (n = 211).\n" if sp == "de" else "\n\nAfter −2% days the chronologically thinned gap after 50 trading days is +0.34 pp (n = 211).\n"), f)),
                (f"{L}: Pp-Werte vertauscht", pruefe_artikel(a, _einmal(text, pp(f["stufen"]["2"]["h"]["50"]["ausgeduennt"]["ueberrendite"], sp), pp(f["stufen"]["2"]["h"]["50"]["alle"]["ueberrendite"], sp)), f)),
            ]
        else:
            f2 = copy.deepcopy(f); f2["alle"]["woche"]["mittel"] += 0.01
            w = p(f["alle"]["woche"]["mittel"], sp)
            d = pp(f["alle"]["gepaart"]["woche_differenz"], sp)
            np_ = f"{f['alle']['woche']['n_positiv']} {'von' if sp == 'de' else 'of'} {f['alle']['woche']['n']}"
            faelle += [
                (f"{L}: Faktenblatt verschoben (Tabelle/Text alt)", pruefe_artikel(a, text, f2)),
                (f"{L}: Wochenmittel als Abstand", pruefe_artikel(a, _einmal(text, d, pp(f["alle"]["woche"]["mittel"], sp)), f)),
                (f"{L}: Fallzahl falsch", pruefe_artikel(a, text.replace(np_, np_.replace(str(f["alle"]["woche"]["n_positiv"]), str(f["alle"]["woche"]["n_positiv"] + 1), 1)), f)),
                (f"{L}: Tageszeile vertauscht", pruefe_artikel(a, text.replace(tabellen_mw(f, sp)["tage"], tabellen_mw(f, sp)["tage"].replace("t−4", "t−9", 1)), f)),
                (f"{L}: Kernzahl nur noch im Kommentar", pruefe_artikel(a, text.replace(w, "X") + f"\n<!-- {w} -->", f)),
                (f"{L}: falsches Jahr bei „deutlich nur“", pruefe_artikel(a, _einmal(text, "deutlich nur 1930" if sp == "de" else "clearly so only in 1930", "deutlich nur 1946" if sp == "de" else "clearly so only in 1946"), f)),
                (f"{L}: Wochenmittel als Wahltagsrendite", pruefe_artikel(a, text + ("\n\nAm Wahltag lag die mittlere Rendite bei +1,47 %.\n" if sp == "de" else "\n\nOn election day the mean return was +1.47%.\n"), f)),
                (f"{L}: Referenztag mit Wahltagskohorte", pruefe_artikel(a, _einmal(text, "t0 selbst in 23 von 31" if sp == "de" else "t0 itself in 23 of 31", "t0 selbst in 10 von 14" if sp == "de" else "t0 itself in 10 of 14"), f)),
                (f"{L}: Mittel als Median ausgegeben", pruefe_artikel(a, text + ("\n\nAm geöffneten Wahltag lag der Median bei +0,44 %.\n" if sp == "de" else "\n\nOn open election days the median was +0.44%.\n"), f)),
                (f"{L}: Nachwahltag als Median", pruefe_artikel(a, _einmal(text, "stieg der S&P 500 im Mittel um +0,20 %" if sp == "de" else "the S&P 500 rose by +0.20% on average", "stieg der S&P 500 im Median um +0,20 %" if sp == "de" else "the S&P 500 rose by a median +0.20%"), f)),
                (f"{L}: falsche Fallzahl an geöffneten Wahltagen", pruefe_artikel(a, _einmal(text, "im Mittel um +0,44 %" if sp == "de" else "rose by +0.44% on average", "im Mittel um +0,44 % (n = 31)" if sp == "de" else "rose by +0.44% on average (n = 31)"), f)),
                (f"{L}: Nachwahltag der falschen Kohorte", pruefe_artikel(a, text + ("\n\nSeit 1971 stieg der S&P 500 am ersten Handelstag nach der Wahlnacht im Mittel um +0,20 % (n = 13).\n" if sp == "de" else "\n\nSince 1971 the S&P 500 rose by +0.20% on average on the first trading day after election night (n = 13).\n"), f)),
                (f"{L}: Wochenmittel als Nachwahltag", pruefe_artikel(a, text + ("\n\nÜber alle 31 Midterms betrug die mittlere Rendite nach der Wahlnacht +1,47 %.\n" if sp == "de" else "\n\nAcross all 31 midterms the mean return after election night was +1.47%.\n"), f)),
                (f"{L}: Wochenmittel 1971 als Nachwahltag", pruefe_artikel(a, _einmal(text, "Für die Wahlen seit 1971 fällt das Mittel mit +1,79 %" if sp == "de" else "For the elections since 1971 the mean is somewhat higher at +1.79%", "Für die Wahlen seit 1971 fällt am ersten Handelstag nach der Wahlnacht das Mittel mit +1,79 %" if sp == "de" else "For the elections since 1971 the mean on the first trading day after election night is somewhat higher at +1.79%"), f)),
                (f"{L}: Wochenfallzahl an t0", pruefe_artikel(a, _einmal(text, "t0 selbst in 23 von 31" if sp == "de" else "t0 itself in 23 of 31", "t0 selbst in 25 von 31" if sp == "de" else "t0 itself in 25 of 31"), f)),
                (f"{L}: Gesamtmittel der 1971er-Kohorte zugeschrieben", pruefe_artikel(a, text + ("\n\nSeit 1971 lag die letzte Midterm-Woche im Mittel bei +1,47 %.\n" if sp == "de" else "\n\nSince 1971 the last midterm week averaged +1.47%.\n"), f)),
                (f"{L}: Abstände 1898/1971 vertauscht", pruefe_artikel(a, _einmal(text, d, pp(f["ab_1971"]["gepaart"]["woche_differenz"], sp)), f)),
            ]
    verfehlt = [n for n, fe in faelle if not fe]
    for n, fe in faelle:
        print(f"  {'gefangen' if fe else 'VERFEHLT'}: {n}")
    print(f"{len(faelle) - len(verfehlt)}/{len(faelle)} Mutationen gefangen")
    return 1 if verfehlt else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--tabellen" in sys.argv:
        fj = fakten_je_art()
        for sp in ("de", "en"):
            for art, fn in (("dd", tabellen_dd), ("mw", tabellen_mw)):
                for name, tab in fn(fj[art], sp).items():
                    print(f"\n### {sp}/{art}/{name}\n{tab}")
        sys.exit(0)
    if "--mutationen" in sys.argv:
        sys.exit(mutationen())
    fe = pruefe()
    for x in fe:
        print("FEHLER", x)
    print(f"verify_downdays_midterm_blog: {len(fe)} Fehler")
    sys.exit(1 if fe else 0)
