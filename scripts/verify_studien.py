# -*- coding: utf-8 -*-
"""Waechter fuer /studien — prueft die Seite gegen ihre eigenen Quellen.

Drei Dinge koennen hier still falsch werden, und alle drei sind mechanisch
pruefbar:

1. DE/EN-DRIFT. Die englische Fassung entsteht aus en.json. Faellt dort eine
   Zahl oder eine Bedingung weg ("nur im Stress"), liest die englische Seite
   eine staerkere Aussage als die deutsche — und verify_en meldet das nicht,
   weil es nur prueft, ob ein Schluessel FEHLT, nicht ob sein Inhalt passt.
2. ZAHLEN GEGEN QUELLE. Die Kennzahlen auf den Karten stammen aus den
   Studien-JSONs. Wird eine Studie neu gerechnet, veraltet die Karte still.
3. TOTE LINKS. Jede Karte verweist auf einen Blog-Slug oder eine Seite mit
   nginx-Route.

Aufruf: py -3.14 scripts/verify_studien.py
"""
import io
import json
import os
import re
import sys
from html import unescape as _unescape

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DE = os.path.join(WURZEL, "landing/pages/studien.html")
EN_JSON = os.path.join(WURZEL, "landing/i18n/en.json")

fehler = []
hinweise = []


def melde(ok: bool, text: str) -> None:
    print(("  ok   " if ok else "  FEHL ") + text)
    if not ok:
        fehler.append(text)


def _zahlen(s: str) -> list:
    """Alle Zahlen aus einem Textstueck, auf eine Schreibweise normiert.

    Deutsch schreibt 6,88 und 41.203, Englisch 6.88 und 41,203 — ein naiver
    Vergleich meldete sonst an jeder Zahl einen Unterschied. Beide Trenner
    fallen deshalb weg und die Ziffernfolge bleibt uebrig.
    """
    s = re.sub(r"<[^>]+>", "", s)
    # Vollstaendig dekodieren, nicht eine Handvoll Entities einzeln ersetzen:
    # `&#39;` im englischen Text wurde sonst als die Zahl 39 gelesen.
    s = _unescape(s)
    roh = re.findall(r"\d[\d.,]*", s)
    aus = []
    for r in roh:
        r = r.rstrip(".,")
        aus.append(r.replace(".", "").replace(",", ""))
    return sorted(aus)


def karten(html: str) -> dict:
    """Je Studie den deutschen Fliesstext, an den i18n-Schluesseln aufgehaengt.

    Das Muster schliesst auf dem EIGENEN Tag (\\1). Ein naives `(.*?)</` bricht
    am ersten `</b>` MITTEN im Satz ab und liefert einen Bruchteil des Textes —
    der Vergleich gegen die englische Fassung meldete dann ueberall
    Unterschiede, die keine sind.
    """
    aus = {}
    for m in re.finditer(
            r'<(h3|p|span)[^>]*data-i18n-html="st\.([a-z0-9]+)_(t|f|e|b)"[^>]*>'
            r'(.*?)</\1>', html, re.S):
        aus.setdefault(m.group(2), {})[m.group(3)] = m.group(4)
    return aus


def main() -> None:
    html = io.open(DE, encoding="utf-8").read()
    en = json.loads(io.open(EN_JSON, encoding="utf-8").read())
    k = karten(html)

    print("Karten:")
    melde(len(k) == 11, "%d Studien-Karten gefunden (erwartet 11)" % len(k))
    melde(all(set(v) == {"t", "f", "e", "b"} for v in k.values()),
          "jede Karte hat Titel, Frage, Ergebnis und Datenbasis")

    print("DE/EN — dieselben Zahlen in beiden Sprachen:")
    for name in sorted(k):
        for feld in ("e", "b"):
            key = "st.%s_%s" % (name, feld)
            if key not in en:
                melde(False, "%s fehlt in en.json" % key)
                continue
            a, b = _zahlen(k[name][feld]), _zahlen(en[key])
            melde(a == b, "%-22s %s" % (
                key, "gleich (%d Zahlen)" % len(a) if a == b
                else "UNTERSCHIED  de=%s  en=%s" % (a, b)))

    print("DE/EN — Bedingungen, die eine Aussage einschraenken:")
    # Ein weggefallenes "nur" macht aus einer bedingten Aussage eine
    # allgemeine. Genau das ist der Fehler, der beim Uebersetzen passiert.
    bedingt = {"bonds": ("Nur im Stress", "Only under stress"),
               "btc": ("nicht", "Not at"),
               "monthly10": ("Nicht im Ertrag", "Not in return")}
    for name, (d, e) in bedingt.items():
        melde(d in k[name]["e"] and e in en["st.%s_e" % name],
              "%-12s Einschraenkung in beiden Sprachen vorhanden" % name)

    print("Zahlen gegen die Studien-Quellen:")
    dat = os.path.join(WURZEL, "landing/data")
    try:
        v = json.loads(io.open(os.path.join(dat, "vol_saisonalitaet.json"),
                               encoding="utf-8").read())["hypothese"]
        z = _zahlen(k["volsaison"]["e"]) + _zahlen(k["volsaison"]["b"])
        melde(str(round(v["verhaeltnis"], 3)).replace(".", "") in z,
              "Vola-Saisonalitaet: Verhaeltnis %.3f steht auf der Karte" % v["verhaeltnis"])
        melde(str(round(v["p"], 3)).replace(".", "") in z,
              "Vola-Saisonalitaet: p %.3f steht auf der Karte" % v["p"])
        melde(str(v["n_monate"]) in z,
              "Vola-Saisonalitaet: %d Monate stehen auf der Karte" % v["n_monate"])
    except (OSError, KeyError) as e:
        hinweise.append("vol_saisonalitaet.json nicht pruefbar: %s" % e)

    try:
        m = json.loads(io.open(os.path.join(dat, "intermarket_matrix.json"),
                               encoding="utf-8").read())
        z = _zahlen(k["matrix"]["e"]) + _zahlen(k["matrix"]["b"])
        for feld, lbl in [("n_primaer", "Primaerfamilie"), ("n_zellen", "Zellen")]:
            melde(str(m[feld]) in z, "Matrix: %s %d steht auf der Karte" % (lbl, m[feld]))
        melde(str(len(m["maerkte"])) in z,
              "Matrix: %d Maerkte stehen auf der Karte" % len(m["maerkte"]))
        # Die Karte sagt "keine einzige" — das muss die Datei bestaetigen.
        melde(m["n_befunde"] == 0,
              "Matrix: n_befunde == 0, die Karte darf 'keine einzige' sagen")
    except (OSError, KeyError) as e:
        hinweise.append("intermarket_matrix.json nicht pruefbar: %s" % e)

    try:
        i = json.loads(io.open(os.path.join(dat, "index_effect_study.json"),
                               encoding="utf-8").read())
        z = _zahlen(k["index"]["e"]) + _zahlen(k["index"]["b"])
        melde(str(i["n_events"]) in z,
              "Index-Effekt: %d Ereignisse stehen auf der Karte" % i["n_events"])
        t20 = round(i["avg_path"][i["offsets"].index(20)] - 100, 1)
        melde(str(t20).replace(".", "") in z,
              "Index-Effekt: T+20 = %.1f %% steht auf der Karte" % t20)
    except (OSError, KeyError, ValueError) as e:
        hinweise.append("index_effect_study.json nicht pruefbar: %s" % e)

    print("Links:")
    ziele = sorted(set(re.findall(r'href="(/[^"]+)"', html)))
    routen = io.open(os.path.join(WURZEL, "deploy/nginx.conf"),
                     encoding="utf-8").read()
    for u in ziele:
        if u.startswith("/landing/"):
            continue                    # Stylesheet und Favicons, keine Seitenroute
        if u.startswith("/blog/") or u.startswith("/en/blog/"):
            slug = u.strip("/").split("/")[-1]
            ordner = "blog/posts/en" if u.startswith("/en/") else "blog/posts"
            treffer = [f for f in os.listdir(os.path.join(WURZEL, ordner))
                       if f.endswith(".md")
                       and re.search(r"^slug:\s*%s\s*$" % re.escape(slug),
                                     io.open(os.path.join(WURZEL, ordner, f),
                                             encoding="utf-8").read(), re.M)]
            melde(len(treffer) == 1, "%-56s %s" % (
                u, "%s" % treffer[0] if len(treffer) == 1 else "KEIN Post mit slug %s" % slug))
        elif u.startswith("/en/"):
            p = os.path.join(WURZEL, "landing/pages", u[4:] + ".html")
            melde(os.path.exists(p), "%-56s DE-Vorlage vorhanden" % u)
        else:
            melde(("location = %s {" % u) in routen,
                  "%-56s nginx-Route vorhanden" % u)

    print("Links auf der ENGLISCHEN Fassung:")
    # rewrite_body_links ueberspringt /blog/, ein Blog-Link bleibt auf der
    # EN-Seite also deutsch. Das ist hinnehmbar, solange das Etikett es ansagt —
    # ein englischer Leser darf nicht ueber "Read it" auf einem deutschen
    # Artikel landen. Geprueft wird die GEBAUTE Seite, nicht die Vorlage.
    p_en = os.path.join(WURZEL, "landing/en/studien.html")
    if not os.path.exists(p_en):
        hinweise.append("landing/en/studien.html fehlt — erst build_en.py --write")
    else:
        enh = io.open(p_en, encoding="utf-8").read()
        anker = re.findall(r'href="([^"]+)"[^>]*data-i18n="(st\.read[a-z_]*)"', enh)
        melde(len(anker) == 11, "%d Links (erwartet 11, einer je Karte)" % len(anker))
        falsch = [u for u, key in anker
                  if u.startswith("/blog/") and key != "st.read_deonly"]
        melde(not falsch,
              "kein deutscher Artikel hinter einem neutralen Etikett"
              + ("" if not falsch else ": " + ", ".join(falsch)))
        tot = [u for u, _ in anker if u.startswith("/en/blog/")
               and not os.path.exists(os.path.join(
                   WURZEL, "blog/posts/en"))]
        melde(not tot, "alle /en/blog/-Ziele haben einen EN-Ordner")
        melde(en.get("st.read_deonly", "").endswith("(German)"),
              "das Etikett fuer deutsche Ziele nennt die Sprache")

    print("")
    for h in hinweise:
        print("  HINWEIS " + h)
    print("STUDIEN: %s" % ("ALLE PRUEFUNGEN BESTANDEN" if not fehler
                           else "%d FEHLER" % len(fehler)))
    sys.exit(1 if fehler else 0)


if __name__ == "__main__":
    main()
