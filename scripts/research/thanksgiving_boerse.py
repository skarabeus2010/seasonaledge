#!/usr/bin/env python3
"""
thanksgiving_boerse.py — Faktenblatt und Charts für den Blogartikel „Thanksgiving und Börse“
(DE thanksgiving-boerse-black-friday, EN thanksgiving-stock-market-black-friday, erscheint 2026-11-20).

    py -3.14 scripts/research/thanksgiving_boerse.py            # Faktenblatt + Charts
    py -3.14 scripts/research/thanksgiving_boerse.py --pruefen  # jede Zahl in DE+EN gegen das Faktenblatt

Daten: eingefrorener Snapshot scripts/research/out/thanksgiving_snapshot_2026-11-13.json (Supabase `prices`,
^GSPC ab 1941, ^GDAXI ab 2001, Schluss 2026-11-13, nur lesend exportiert). Renditen aus der gespeicherten
Spalte `log_return` (bezieht sich auf die vorige gespeicherte Zeile).

Definitionen (Thanksgiving T = 4. Donnerstag im November, Regel ab 1942, Termin aus shared/boersenereignisse):
  Mittwoch  = Sitzungsrendite am Mittwoch vor T (T−1)
  Freitag   = Sitzungsrendite am Freitag nach T (T+1), Vorzeile = Mittwoch
  Montag    = Sitzungsrendite am Montag nach T (T+4); bis 1952 kann die Vorzeile ein Samstag sein
  Woche     = letzter Schluss <= Freitag vor der Woche (T−6) bis letzter Schluss <= Freitag nach T (T+1)
Eine Tagesrendite zählt nur, wenn zwischen Vorzeile und Tag kein Werktag liegt, der laut Börsenkalender eine
Sitzung hätte sein müssen (eine fehlende Kurszeile ist kein Schließungsbeleg -> Fall raus, gezählt).
Vergleich: gleicher Wochentag ohne Thanksgiving-Woche (alle Monate bzw. nur November), alle übrigen Wochen.
p-Wert: Welch-t-Test zweiseitig, zusätzlich Permutationstest (20 000 Ziehungen, Plus-eins, zweiseitig).
DAX: ^GDAXI an Thanksgiving-Donnerstag 2002–2025 gegen alle übrigen Donnerstage 2002–2025, Rendite und
Tagesspanne (Hoch − Tief) / Vortagesschluss.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import random
import re
import statistics as S
import sys
from datetime import date, timedelta

HIER = pathlib.Path(__file__).resolve().parent
REPO = HIER.parent.parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(REPO))

from shared.boersenereignisse import ereignisse, kompat, halbtag_status  # noqa: E402
from shared.exchange_holidays import kalender_status  # noqa: E402

SNAPSHOT = HIER / "out" / "thanksgiving_snapshot_2026-11-13.json"
SHA256 = "bb1b8aaf0662cd83f83fe8c818fb2e0fe82581469a6aaddf72db581ce4f8ca68"
FAKTEN = HIER / "out" / "thanksgiving_fakten.json"
BILDER = REPO / "blog" / "posts" / "images" / "thanksgiving-boerse"
POSTS = [REPO / "blog" / "posts" / "2026-11-20_thanksgiving-boerse-black-friday.md",
         REPO / "blog" / "posts" / "en" / "2026-11-20_thanksgiving-stock-market-black-friday.md"]
JAHRE = range(1942, 2026)
SPLIT = 1987
PERM_N, SEED = 20000, 20261120


def lade():
    roh = SNAPSHOT.read_bytes()
    if hashlib.sha256(roh).hexdigest() != SHA256:
        raise SystemExit("Snapshot verändert (Prüfsumme)")
    return json.loads(roh)


def thanksgiving(j: int) -> date:
    t = [e.wirksam for e in ereignisse("NYSE", j) if e.regel_id == "NYSE.thanksgiving"]
    if len(t) != 1:
        raise SystemExit(f"{j}: kein eindeutiger Thanksgiving-Termin im Katalog")
    return t[0]


class Reihe:
    def __init__(self, zeilen, boerse):
        self.d = [date.fromisoformat(z[0]) for z in zeilen]
        self.o, self.h, self.l, self.c, self.v, self.r = ([z[k] for z in zeilen] for k in range(1, 7))
        self.idx = {d: i for i, d in enumerate(self.d)}
        self.boerse = boerse
        self._zu = {}

    def zu(self, j):
        if j not in self._zu:
            self._zu[j] = kompat(self.boerse, j)
        return self._zu[j]

    def lueckenlos(self, i):
        """Vorzeile ist die vorige Sitzung: kein Werktag dazwischen, der keine bekannte Schließung ist."""
        if i == 0:
            return False
        a, b = self.d[i - 1], self.d[i]
        x = a + timedelta(days=1)
        while x < b:
            if x.weekday() < 5 and x not in self.zu(x.year):
                return False
            x += timedelta(days=1)
        return True

    def tag(self, d):
        """Tagesrendite (einfach, %) oder 'fehlt'/'luecke'."""
        i = self.idx.get(d)
        if i is None:
            return "fehlt"
        if not self.lueckenlos(i):
            return "luecke"
        return 100 * math.expm1(self.r[i])

    def letzte_bis(self, d):
        lo, hi = 0, len(self.d) - 1
        if self.d[0] > d:
            return None
        while lo < hi:
            m = (lo + hi + 1) // 2
            if self.d[m] <= d:
                lo = m
            else:
                hi = m - 1
        return lo

    def fenster(self, von, bis):
        """Rendite (%) letzter Schluss <= von -> letzter Schluss <= bis, aus log_return (teleskopiert)."""
        a, b = self.letzte_bis(von), self.letzte_bis(bis)
        if a is None or b is None or b < a:
            return None
        return 100 * math.expm1(sum(self.r[a + 1:b + 1]))      # b == a: keine Sitzung dazwischen -> 0

    def fenster_close(self, von, bis):
        a, b = self.letzte_bis(von), self.letzte_bis(bis)
        return 100 * (self.c[b] / self.c[a] - 1)


def kz(w):
    w = [x for x in w if isinstance(x, float)]
    return {"n": len(w), "mittel": S.mean(w), "median": S.median(w),
            "n_positiv": sum(x > 0 for x in w), "anteil_positiv": sum(x > 0 for x in w) / len(w),
            "std": S.stdev(w)}


def welch(a, b):
    from scipy import stats
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)


def perm(a, b, seed=SEED):
    rnd = random.Random(seed)
    pool = list(a) + list(b)
    n = len(a)
    beob = abs(S.mean(a) - S.mean(b))
    tot = sum(pool)
    treffer = 0
    for _ in range(PERM_N):
        zug = rnd.sample(pool, n)
        sa = sum(zug)
        d = abs(sa / n - (tot - sa) / (len(pool) - n))
        treffer += d >= beob - 1e-12
    return (treffer + 1) / (PERM_N + 1)


def vergleich(ereignis, basis):
    e, b = [x for x in ereignis if isinstance(x, float)], [x for x in basis if isinstance(x, float)]
    return {"ereignis": kz(e), "basis": kz(b), "differenz": S.mean(e) - S.mean(b),
            "p_welch": welch(e, b), "p_perm": perm(e, b)}


def sp500(g: Reihe):
    tg = {j: thanksgiving(j) for j in JAHRE}
    tg_wochen = {t - timedelta(days=3) for t in tg.values()}              # Montag der Woche
    wed, fri, mon, woche, ausfall = {}, {}, {}, {}, []
    for j, t in tg.items():
        for name, ziel, d in (("mittwoch", wed, t - timedelta(days=1)), ("freitag", fri, t + timedelta(days=1)),
                              ("montag", mon, t + timedelta(days=4))):
            v = g.tag(d)
            if isinstance(v, str):
                ausfall.append([j, name, v])
            else:
                ziel[j] = v
        woche[j] = g.fenster(t - timedelta(days=6), t + timedelta(days=1))
        if t in g.idx:
            raise SystemExit(f"Kurszeile am Thanksgiving {t}")

    # Basis: gleiche Wochentage außerhalb der Thanksgiving-Woche (und ohne den Montag danach)
    nach = {t + timedelta(days=4) for t in tg.values()}
    basis = {k: {"alle": [], "nov": []} for k in ("mittwoch", "freitag", "montag")}
    wt = {2: "mittwoch", 4: "freitag", 0: "montag"}
    for i, d in enumerate(g.d):
        if not (1942 <= d.year <= 2025) or d.weekday() not in wt:
            continue
        mo = d - timedelta(days=d.weekday())
        if mo in tg_wochen or d in nach or not g.lueckenlos(i):
            continue
        v = 100 * math.expm1(g.r[i])
        k = wt[d.weekday()]
        basis[k]["alle"].append(v)
        if d.month == 11:
            basis[k]["nov"].append(v)
    wb = {"alle": [], "nov": []}
    f = date(1942, 1, 9)
    while f <= date(2025, 12, 31):
        if f - timedelta(days=4) not in tg_wochen:
            v = g.fenster(f - timedelta(days=7), f)
            if v is not None:
                wb["alle"].append(v)
                if f.month == 11:
                    wb["nov"].append(v)
        f += timedelta(days=7)

    # Teleskop-Kontrolle: Summe log_return == Kursverhältnis (Basiswechsel würde hier auffallen)
    abw = max(abs(woche[j] - g.fenster_close(tg[j] - timedelta(days=6), tg[j] + timedelta(days=1))) for j in JAHRE)

    def teil(jj):
        return {
            "mittwoch": vergleich([wed[j] for j in jj if j in wed], basis["mittwoch"]["alle"]),
            "freitag": vergleich([fri[j] for j in jj if j in fri], basis["freitag"]["alle"]),
            "montag": vergleich([mon[j] for j in jj if j in mon], basis["montag"]["alle"]),
            "woche": vergleich([woche[j] for j in jj], wb["alle"]),
        }

    def teil_basis(lo, hi):
        """Vergleich nur gegen Basistage desselben Zeitraums."""
        out = {}
        for k, ser in (("mittwoch", wed), ("freitag", fri), ("montag", mon)):
            bb = [100 * math.expm1(g.r[i]) for i, d in enumerate(g.d)
                  if lo <= d.year <= hi and d.weekday() == {"mittwoch": 2, "freitag": 4, "montag": 0}[k]
                  and (d - timedelta(days=d.weekday())) not in tg_wochen and d not in nach and g.lueckenlos(i)]
            out[k] = vergleich([ser[j] for j in range(lo, hi + 1) if j in ser], bb)
        ff, wb2 = date(1942, 1, 9), []
        while ff <= date(2025, 12, 31):
            if lo <= ff.year <= hi and ff - timedelta(days=4) not in tg_wochen:
                v = g.fenster(ff - timedelta(days=7), ff)
                if v is not None:
                    wb2.append(v)
            ff += timedelta(days=7)
        out["woche"] = vergleich([woche[j] for j in range(lo, hi + 1)], wb2)
        return out

    alle = list(JAHRE)
    def extrem(ser):
        jj = [j for j in alle if j in ser]
        a, b = max(jj, key=ser.get), min(jj, key=ser.get)
        return {"bester": [a, ser[a]], "schlechtester": [b, ser[b]]}
    res = {
        "extrem": {"mittwoch": extrem(wed), "freitag": extrem(fri), "montag": extrem(mon), "woche": extrem(woche)},
        "nyse_kalender_belegt_ab": min(j for j in alle if kalender_status("NYSE", j) == "belegt"),
        "jahre": [1942, 2025], "n_jahre": len(alle), "ausfaelle": ausfall, "teleskop_max_abw_pp": abw,
        "gesamt": teil(alle),
        "nov_basis": {
            "mittwoch": vergleich(list(wed.values()), basis["mittwoch"]["nov"]),
            "freitag": vergleich(list(fri.values()), basis["freitag"]["nov"]),
            "montag": vergleich(list(mon.values()), basis["montag"]["nov"]),
            "woche": vergleich(list(woche.values()), wb["nov"]),
        },
        "frueh": teil_basis(1942, SPLIT), "spaet": teil_basis(SPLIT + 1, 2025),
    }
    # Mittwoch + Freitag zusammen (Almanac-Zählweise), ab 1942 und ab 1952
    mf = {j: 100 * math.expm1(math.log1p(wed[j] / 100) + math.log1p(fri[j] / 100)) for j in alle if j in wed and j in fri}
    res["mi_fr"] = {"ab1942": kz(list(mf.values())), "ab1952": kz([v for j, v in mf.items() if j >= 1952]),
                    "ab1988": kz([v for j, v in mf.items() if j >= 1988])}
    # Halbtag-Freitage (belegt 2013–2025)
    ht = [j for j in alle if halbtag_status("NYSE", j) == "belegt"]
    res["halbtag_belegt"] = [min(ht), max(ht)]
    res["freitag_halbtag_jahre"] = kz([fri[j] for j in ht if j in fri])
    # letzte zehn Jahre
    res["zehn"] = {str(j): {"datum": tg[j].isoformat(), "mittwoch": wed.get(j), "freitag": fri.get(j),
                            "montag": mon.get(j), "woche": woche[j]} for j in range(2016, 2026)}
    res["zehn_kz"] = {k: kz([res["zehn"][str(j)][k] for j in range(2016, 2026)])
                      for k in ("mittwoch", "freitag", "montag", "woche")}
    # Pfad Freitag vor der Woche (0) -> Mo, Di, Mi, Fr, Mo danach
    def pfad(jj):
        punkte = [-3, -2, -1, 1, 4]
        out = [[] for _ in punkte]
        for j in jj:
            t = tg[j]
            for k, o in enumerate(punkte):
                out[k].append(g.fenster(t - timedelta(days=6), t + timedelta(days=o)))
        return [0.0] + [S.mean(x) for x in out]
    res["pfad"] = {"frueh": pfad(range(1942, SPLIT + 1)), "spaet": pfad(range(SPLIT + 1, 2026)),
                   "alle": pfad(alle)}
    return res


def dax(x: Reihe):
    tg = {j: thanksgiving(j) for j in range(2002, 2026)}
    status = {j: kalender_status("XETRA", j) for j in tg}
    tgset = set(tg.values())
    def spanne(i):
        return 100 * (x.h[i] - x.l[i]) / x.c[i - 1]
    er, es, br, bs, fehlt = [], [], [], [], []
    for i, d in enumerate(x.d):
        if not (2002 <= d.year <= 2025) or d.weekday() != 3:
            continue
        if not x.lueckenlos(i):
            if d in tgset:
                fehlt.append(d.isoformat())
            continue
        r, s = 100 * math.expm1(x.r[i]), spanne(i)
        if d in tgset:
            er.append(r); es.append(s)
        else:
            br.append(r); bs.append(s)
    for t in tgset:
        if t not in x.idx:
            fehlt.append(t.isoformat())
    # Spanne relativ zum Mittel der Donnerstage desselben Jahres
    rel = []
    for j, t in tg.items():
        i = x.idx.get(t)
        if i is None:
            continue
        jb = [spanne(k) for k, d in enumerate(x.d) if d.year == j and d.weekday() == 3 and d != t and x.lueckenlos(k)]
        rel.append(spanne(i) / S.mean(jb))
    return {"jahre": [2002, 2025], "xetra_status": sorted(set(status.values())), "fehlt": fehlt,
            "rendite": vergleich(er, br), "spanne": vergleich(es, bs),
            "spanne_rel_jahr": kz(rel), "n_kleiner_als_jahresmittel": sum(v < 1 for v in rel),
            "werte_tg": {t.isoformat(): [100 * math.expm1(x.r[x.idx[t]]), spanne(x.idx[t])] for t in sorted(tgset)}}


def fakten():
    s = lade()
    g = Reihe(s["reihen"]["^GSPC"], "NYSE")
    x = Reihe(s["reihen"]["^GDAXI"], "XETRA")
    t26 = thanksgiving(2026)
    ht26 = [e for e in ereignisse("NYSE", 2026) if e.art == "halbtag" and e.nominal == t26 + timedelta(days=1)]
    f = {"stand": s["stand"], "snapshot_sha256": SHA256, "thanksgiving_2026": t26.isoformat(),
         "halbtag_2026": [ht26[0].nominal.isoformat(), ht26[0].schlusszeit, ht26[0].zeitzone] if ht26 else None,
         "xetra_offen_2026": t26 not in kompat("XETRA", 2026),
         "sp500": sp500(g), "dax": dax(x)}
    FAKTEN.write_text(json.dumps(f, indent=1, ensure_ascii=False), encoding="utf-8")
    return f


# ------------------------------------------------------------------ Charts
def charts(f):
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["text.parse_math"] = False
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    from render_zweig_charts import _achse, _fuss, _speichern, _zahl, GOLD, DIM, HELL, GITTER, BLAU, FLAECHE

    sp, dx = f["sp500"], f["dax"]
    T = {
        "de": {"p_t": "S&P 500 in der Thanksgiving-Woche: mittlerer Verlauf",
               "p_u": "Kumulierte Rendite ab Schluss am Freitag vor der Woche, Mittel je Zeitraum (Kursindex)",
               "kat": ["Fr davor", "Mo", "Di", "Mi", "Fr\n(nach Thanksgiving)", "Mo danach"],
               "l1": "1942–1987 (n = %d)", "l2": "1988–2025 (n = %d)",
               "fuss": "^GSPC Kursindex, Datenstand 13.11.2026 · Donnerstag = Thanksgiving, Börse geschlossen",
               "d_t": "DAX an Thanksgiving gegen gewöhnliche Donnerstage (2002–2025)",
               "d_u": "Mittelwerte; Spanne = (Tageshoch − Tagestief) / Vortagesschluss",
               "dk": ["Tagesrendite", "Tagesspanne"], "dl1": "Thanksgiving-Donnerstag (n = %d)",
               "dl2": "übrige Donnerstage (n = %s)",
               "fuss_d": "^GDAXI, Datenstand 13.11.2026 · Xetra handelt an Thanksgiving, die Wall Street nicht"},
        "en": {"p_t": "S&P 500 in Thanksgiving week: average path",
               "p_u": "Cumulative return from the close on the Friday before the week, mean per period (price index)",
               "kat": ["Fri before", "Mon", "Tue", "Wed", "Fri\n(after Thanksgiving)", "Mon after"],
               "l1": "1942–1987 (n = %d)", "l2": "1988–2025 (n = %d)",
               "fuss": "^GSPC price index, data as of 2026-11-13 · Thursday = Thanksgiving, market closed",
               "d_t": "DAX on Thanksgiving versus ordinary Thursdays (2002–2025)",
               "d_u": "Means; range = (daily high − daily low) / prior close",
               "dk": ["Daily return", "Daily range"], "dl1": "Thanksgiving Thursday (n = %d)",
               "dl2": "other Thursdays (n = %s)",
               "fuss_d": "^GDAXI, data as of 2026-11-13 · Xetra trades on Thanksgiving, Wall Street does not"},
    }
    pz = lambda lang, nk, vz: FuncFormatter(lambda v, _: _zahl(v, ("%+." if vz else "%.") + f"{nk}f", lang)
                                             + (" %" if lang == "de" else "%"))
    nf, ns = sp["frueh"]["woche"]["ereignis"]["n"], sp["spaet"]["woche"]["ereignis"]["n"]
    for lang in ("de", "en"):
        t = T[lang]
        fig, ax = plt.subplots(figsize=(11.4, 5.4))
        _achse(ax, t["p_t"], t["p_u"])
        xs = list(range(6))
        for key, farbe, lab, n in (("frueh", BLAU, t["l1"], nf), ("spaet", GOLD, t["l2"], ns)):
            y = sp["pfad"][key]
            ax.plot(xs, y, color=farbe, linewidth=2.2, marker="o", label=lab % n)
            for i in (3, 4, 5):
                ax.annotate(_zahl(y[i], "%+.2f", lang) + (" %" if lang == "de" else "%"), (i, y[i]),
                            xytext=(0, 9) if key == "spaet" else ((34, -16) if i == 4 else (0, -15)),
                            textcoords="offset points",
                            color=farbe, fontsize=9, ha="center")
        ax.axvspan(3.35, 3.65, color=DIM, alpha=0.15)
        ax.axhline(0, color=DIM, linewidth=0.8)
        ax.set_xticks(xs, t["kat"])
        ax.yaxis.set_major_formatter(pz(lang, 1, True))
        ax.legend(loc="upper left", facecolor=FLAECHE, edgecolor=GITTER, labelcolor=HELL, fontsize=9)
        _fuss(fig, t["fuss"])
        _speichern(fig, BILDER / f"1_pfad_{lang}.png")

        fig, axs = plt.subplots(1, 2, figsize=(11.4, 5.0))
        for k, (ax, key) in enumerate(zip(axs, ("rendite", "spanne"))):
            _achse(ax, t["d_t"] if k == 0 else "", t["d_u"] if k == 0 else "")
            e, b = dx[key]["ereignis"]["mittel"], dx[key]["basis"]["mittel"]
            ax.bar([0, 1], [e, b], color=[GOLD, BLAU], width=0.55)
            for i, v in enumerate((e, b)):
                ax.text(i, v + (0.02 if v >= 0 else -0.02), _zahl(v, "%+.2f" if key == "rendite" else "%.2f", lang)
                        + (" %" if lang == "de" else "%"), color=HELL, fontsize=10, ha="center",
                        va="bottom" if v >= 0 else "top")
            nb = f"{dx[key]['basis']['n']:,}".replace(",", " " if lang == "de" else ",")
            ax.set_xticks([0, 1], [t["dl1"] % dx[key]["ereignis"]["n"], t["dl2"] % nb], fontsize=8.5)
            ax.set_xlabel(t["dk"][k], color=DIM, fontsize=10)
            ax.axhline(0, color=DIM, linewidth=0.8)
            ax.yaxis.set_major_formatter(pz(lang, 2, key == "rendite"))
            if key == "spanne":
                from matplotlib.ticker import MultipleLocator
                ax.yaxis.set_major_locator(MultipleLocator(0.25))
            if key == "rendite":
                lo = min(e, b, 0)
                ax.set_ylim(lo - 0.08, max(e, b, 0) + 0.08)
            else:
                ax.set_ylim(0, max(e, b) * 1.18)
        _fuss(fig, t["fuss_d"])
        _speichern(fig, BILDER / f"2_dax_{lang}.png")


# ------------------------------------------------------------------ Zahlenprüfung
def pruefen(f):
    """Jede Dezimalzahl (mit Komma oder Punkt) im Lesertext muss als gerundeter Faktenwert vorkommen."""
    werte = set()
    ganz = set()
    def sammle(o):
        if isinstance(o, dict):
            for v in o.values():
                sammle(v)
        elif isinstance(o, list):
            for v in o:
                sammle(v)
        elif isinstance(o, int) and not isinstance(o, bool):
            ganz.add(o)
        elif isinstance(o, float):
            for nk in (1, 2, 3, 4):
                for v in (o, 100 * o, abs(o), abs(100 * o)):
                    werte.add(f"{v:.{nk}f}")
    sammle(f)
    rot = 0
    for p in POSTS:
        txt = p.read_text(encoding="utf-8")
        txt = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
        txt = re.sub(r"^---.*?^---", "", txt, count=1, flags=re.S | re.M)
        txt = re.sub(r"(?<!\d)\d{1,2}\.\d{1,2}\.(\d{4})?", "DATUM", txt)        # Datumsangaben 26.11.
        for m in re.finditer(r"(?<![\w.,])[−+-]?(\d+[.,]\d+)", txt):
            z = m.group(1).replace(",", ".")
            if re.fullmatch(r"\d{1,3}[.,]\d{3}", m.group(1)) and int(re.sub(r"\D", "", z)) in ganz:
                continue                                                   # Tausender, z. B. 4 177 / 4,177
            if z not in werte:
                zeile = txt[:m.start()].count("\n") + 1
                print(f"  {p.name}:{zeile}: {m.group(0)} nicht im Faktenblatt")
                rot += 1
    print("Zahlenprüfung:", "OK" if not rot else f"{rot} offen")
    return rot



def _fmt(v, nk, lang, vz=True, pct=True):
    t = (("%+." if vz else "%.") + str(nk) + "f") % v
    t = t.replace("-", "−")
    if lang == "de":
        t = t.replace(".", ",")
    return t + ((" %" if lang == "de" else "%") if pct else "")


def kernzahlen(f):
    """Gezielte Prüfung: jede Kernaussage muss in beiden Sprachen formatiert im Text stehen."""
    sp, dx = f["sp500"], f["dax"]
    g, fr, la, nov = sp["gesamt"], sp["frueh"], sp["spaet"], sp["nov_basis"]

    def E(v, k):
        return v[k]["ereignis"]

    def B(v, k):
        return v[k]["basis"]

    out = []
    for k in ("mittwoch", "freitag", "montag", "woche"):
        out += [(E(g, k)["mittel"], 2, True, True), (E(g, k)["median"], 2, True, True),
                (B(g, k)["mittel"], 2, True, True), (100 * E(g, k)["anteil_positiv"], 1, False, True),
                (100 * B(g, k)["anteil_positiv"], 1, False, True)]
    out += [(g["woche"]["differenz"], 2, False, False), (nov["woche"]["differenz"], 2, False, False),
            (g["woche"]["p_welch"], 2, False, False), (nov["woche"]["p_welch"], 2, False, False),
            (g["mittwoch"]["p_welch"], 2, False, False), (g["freitag"]["p_welch"], 3, False, False),
            (g["montag"]["p_welch"], 2, False, False), (nov["montag"]["p_welch"], 2, False, False),
            (nov["montag"]["p_perm"], 3, False, False), (B(nov, "montag")["mittel"], 2, True, True)]
    for teil in (fr, la):
        out += [(E(teil, "woche")["mittel"], 2, True, True), (B(teil, "woche")["mittel"], 2, True, True),
                (teil["woche"]["p_welch"], 2, False, False), (E(teil, "freitag")["mittel"], 2, True, True),
                (B(teil, "freitag")["mittel"], 2, True, True), (teil["mittwoch"]["p_welch"], 2, False, False)]
    out += [(fr["freitag"]["p_welch"], 3, False, False), (la["freitag"]["p_welch"], 2, False, False)]
    for key in ("frueh", "spaet"):
        y = sp["pfad"][key]
        out += [(y[1], 2, True, True), (y[4], 2, True, True), (y[5], 2, True, True)]
    out.append((sp["pfad"]["spaet"][3], 2, True, True))
    h = sp["freitag_halbtag_jahre"]
    out += [(h["mittel"], 2, True, True), (h["median"], 2, True, True),
            (100 * sp["mi_fr"]["ab1952"]["anteil_positiv"], 1, False, True),
            (sp["mi_fr"]["ab1952"]["mittel"], 2, True, True), (sp["mi_fr"]["ab1988"]["mittel"], 2, True, True),
            (sp["extrem"]["montag"]["schlechtester"][1], 2, True, True),
            (sp["extrem"]["woche"]["bester"][1], 2, True, True),
            (sp["extrem"]["woche"]["schlechtester"][1], 2, True, True)]
    for k in ("mittwoch", "freitag", "montag", "woche"):
        out.append((sp["zehn_kz"][k]["mittel"], 2, True, True))
        for j in range(2016, 2026):
            out.append((sp["zehn"][str(j)][k], 2, True, True))
    for k in ("rendite", "spanne"):
        vz = k == "rendite"
        out += [(E(dx, k)["mittel"], 2, vz, True), (E(dx, k)["median"], 2, vz, True),
                (B(dx, k)["mittel"], 2, vz, True), (B(dx, k)["median"], 2, vz, True)]
    out += [(dx["rendite"]["p_welch"], 2, False, False), (dx["spanne"]["p_welch"], 3, False, False),
            (dx["spanne"]["p_perm"], 3, False, False)]

    roh = {}
    for lang, sep in (("de", " "), ("en", ",")):
        r = [_fmt(v, nk, lang, vz, pct) for v, nk, vz, pct in out]
        for n in (B(g, "mittwoch")["n"], B(g, "freitag")["n"], B(g, "montag")["n"], B(dx, "rendite")["n"]):
            r.append(f"{n:,}".replace(",", sep))
        von = "von" if lang == "de" else "of"
        r += [f"{E(g, 'woche')['n_positiv']} " + ("der 84" if lang == "de" else "of the 84"),
              f"{sp['mi_fr']['ab1952']['n_positiv']} {von} 74", f"{sp['mi_fr']['ab1988']['n_positiv']} {von} 38",
              f"{dx['n_kleiner_als_jahresmittel']} {von} 24",
              f"{E(dx, 'rendite')['n_positiv']} " + ("von 24" if lang == "de" else "times out of 24"),
              f"{round(100 * dx['spanne_rel_jahr']['median'])}" + (" %" if lang == "de" else "%"),
              f"{h['n_positiv']} " + ("Mal positiv" if lang == "de" else "times")]
        roh[lang] = r
    return roh


def pruefen_kern(f):
    rot = 0
    roh = kernzahlen(f)
    for p, lang in zip(POSTS, ("de", "en")):
        txt = p.read_text(encoding="utf-8")
        for s in roh[lang]:
            if s not in txt:
                print(f"  {p.name}: Kernzahl fehlt: {s!r}")
                rot += 1
    print("Kernzahlen:", "OK" if not rot else f"{rot} fehlen", f"({len(roh['de'])} je Sprache)")
    return rot


if __name__ == "__main__":
    f = fakten()
    if "--pruefen" in sys.argv:
        sys.exit(1 if (pruefen(f) + pruefen_kern(f)) else 0)
    charts(f)
    sp = f["sp500"]
    for k in ("mittwoch", "freitag", "montag", "woche"):
        for teil in ("gesamt", "frueh", "spaet", "nov_basis"):
            v = sp[teil][k]
            e, b = v["ereignis"], v["basis"]
            print(f"{k:8s} {teil:9s} n={e['n']:3d} m={e['mittel']:+.3f} med={e['median']:+.3f} "
                  f"pos={e['anteil_positiv']:.3f} | basis n={b['n']} m={b['mittel']:+.3f} pos={b['anteil_positiv']:.3f}"
                  f" | p={v['p_welch']:.4f} perm={v['p_perm']:.4f}")
    print("ausfaelle", sp["ausfaelle"], "teleskop", sp["teleskop_max_abw_pp"])
    print("mi_fr", {k: (v["n"], v["n_positiv"], round(v["mittel"], 3)) for k, v in sp["mi_fr"].items()})
    print("halbtag", sp["halbtag_belegt"], sp["freitag_halbtag_jahre"])
    print("zehn", json.dumps(sp["zehn"], indent=0))
    print("zehn_kz", {k: (round(v["mittel"], 3), v["n_positiv"]) for k, v in sp["zehn_kz"].items()})
    print("pfad", sp["pfad"])
    d = f["dax"]
    print("dax", d["fehlt"], d["xetra_status"])
    for k in ("rendite", "spanne"):
        v = d[k]
        print(k, v["ereignis"]["n"], round(v["ereignis"]["mittel"], 3), round(v["ereignis"]["median"], 3),
              round(v["ereignis"]["anteil_positiv"], 3), "|", v["basis"]["n"], round(v["basis"]["mittel"], 3),
              round(v["basis"]["median"], 3), round(v["basis"]["anteil_positiv"], 3), "p", round(v["p_welch"], 4),
              round(v["p_perm"], 4))
    print("spanne rel", d["spanne_rel_jahr"], d["n_kleiner_als_jahresmittel"])
    print("2026", f["thanksgiving_2026"], f["halbtag_2026"], f["xetra_offen_2026"])
