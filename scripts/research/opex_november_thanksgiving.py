#!/usr/bin/env python3
"""
opex_november_thanksgiving.py — Faktenblatt für den Blogartikel „Optionsverfall im November und die
Thanksgiving-Woche“ (2026-11-15), gerechnet aus dem eingefrorenen Datenstand blog/daten/gspc_2026-11-13.json.

    PYTHONUTF8=1 py -3.14 scripts/research/opex_november_thanksgiving.py      # schreibt + druckt das Faktenblatt

Nur lesend. Jede Zahl, die der Artikel nennt, kommt aus dem Faktenblatt
scripts/research/out/opex_november_thanksgiving_fakten.json.

Festlegungen (vor dem Lauf):
  * Reihe ^GSPC (Kursindex ohne Dividenden), Renditen aus dem gespeicherten log_return, nie aus Schlusskursen.
  * Auswertung Kalendermonate 1973-01 bis 2025-12 (börsennotierte Optionen ab 1973), 2026 nur für die Termine.
  * Verfallstag: ab 02/2015 der belegte Verfallstermin aus shared/produkttermine.py, davor die Regel
    (3. Freitag, bei NYSE-Schließung der Handelstag davor) — im Faktenblatt je Monat als „belegt“/„regel“.
  * Thanksgiving: NYSE.thanksgiving aus shared/boersenereignisse.py.
  * Verfallswoche = Handelstage der Kalenderwoche (Mo–Fr) des Verfallstags bis einschließlich Verfallstag;
    Rendite vom letzten Schluss davor bis zum Schluss des Verfallstags.
  * Woche danach = Handelstage der folgenden Kalenderwoche; Rendite vom Schluss des Verfallstags bis zum letzten
    Schluss dieser Woche. Bei 6 Tagen Abstand ist das im November die Thanksgiving-Woche.
  * Vergleich: Welch-t und Permutationstest der Mittelwertdifferenz (zweiseitig, +1-Korrektur, fester Startwert).
  * Pfad: kumulierte Rendite von Schluss t−5 (= 100) bis Schluss t+4, t = Verfallstag, in Handelstagen der Reihe.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import random
import statistics as S
import sys
from datetime import date, timedelta

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from shared.produkttermine import opex_ereignis, opex_regel, vix_ereignis, OPEX_AB   # noqa: E402
from shared.boersenereignisse import ereignisse                                     # noqa: E402
from shared.exchange_holidays import is_trading_day                                 # noqa: E402

DATEI = REPO / "blog" / "daten" / "gspc_2026-11-13.json"
SHA256 = "27b320b0ef06ea9a0d0c838ef92c8395734b87b051f7802b50a1a1878d4f9ee4"
AUS = REPO / "scripts" / "research" / "out" / "opex_november_thanksgiving_fakten.json"
PRUEFDATUM = "2026-11-15"
J0, J1 = 1973, 2025
PERM, SEED = 20000, 20261115
PFAD_VOR, PFAD_NACH = 5, 4


def lade():
    roh = DATEI.read_bytes()
    if hashlib.sha256(roh).hexdigest() != SHA256:
        raise SystemExit("Prüfsumme des eingefrorenen Datenstands weicht ab")
    d = json.loads(roh.decode("utf-8"))
    zeilen = [(date.fromisoformat(a), lr) for a, _c, lr in d["zeilen"]]
    if any(lr is None for _a, lr in zeilen):
        raise SystemExit("log_return fehlt in mindestens einer Zeile")
    return d, zeilen


def thanksgiving(j):
    t = [e.wirksam for e in ereignisse("NYSE", j) if e.regel_id == "NYSE.thanksgiving"]
    assert len(t) == 1
    return t[0]


def verfall(j, m):
    if (j, m) >= OPEX_AB:
        e = opex_ereignis(j, m, PRUEFDATUM)
        if e is not None:
            return date.fromisoformat(e["verfallstermin"]), e["listung"]
    return opex_regel(j, m)["verfallstermin"], "regel"


def pct(lr_sum):
    return (math.exp(lr_sum) - 1.0) * 100.0


def kennzahlen(werte):
    n = len(werte)
    return {"n": n, "mittel": S.fmean(werte), "median": S.median(werte),
            "positiv": sum(1 for v in werte if v > 0), "anteil_positiv": 100.0 * sum(1 for v in werte if v > 0) / n,
            "std": S.stdev(werte) if n > 1 else None}


def welch(a, b):
    ma, mb, va, vb = S.fmean(a), S.fmean(b), S.variance(a), S.variance(b)
    se = math.sqrt(va / len(a) + vb / len(b))
    return (ma - mb) / se


def welch_p(a, b):
    from scipy.stats import ttest_ind
    return float(ttest_ind(a, b, equal_var=False).pvalue)


def perm_p(a, b, seed=SEED, k=PERM):
    rng = random.Random(seed)
    beob = abs(S.fmean(a) - S.fmean(b))
    alle = list(a) + list(b)
    na = len(a)
    treffer = 0
    for _ in range(k):
        rng.shuffle(alle)
        if abs(S.fmean(alle[:na]) - S.fmean(alle[na:])) >= beob - 1e-15:
            treffer += 1
    return (treffer + 1) / (k + 1)


def vergleich(a, b, name_a, name_b):
    return {name_a: kennzahlen(a), name_b: kennzahlen(b), "differenz_mittel": S.fmean(a) - S.fmean(b),
            "differenz_median": S.median(a) - S.median(b), "t_welch": welch(a, b), "p_welch": welch_p(a, b),
            "p_perm": perm_p(a, b)}


def main():
    meta, zeilen = lade()
    daten = [a for a, _ in zeilen]
    lr = [x for _, x in zeilen]
    pos = {a: i for i, a in enumerate(daten)}

    # Phantomzeilen (Kurszeile an einer NYSE-Schließung) im Auswertungszeitraum
    phantome = [a.isoformat() for a in daten if J0 <= a.year <= J1 and not is_trading_day(a, "NYSE")]
    # fehlende Sitzungen (NYSE offen, keine Kurszeile)
    fehlend = []
    t = date(J0, 1, 1)
    vorhanden = set(daten)
    while t <= date(J1, 12, 31):
        if t.weekday() < 5 and is_trading_day(t, "NYSE") and t not in vorhanden:
            fehlend.append(t.isoformat())
        t += timedelta(days=1)

    def summe(von_excl, bis_incl):
        return sum(x for a, x in zeilen if von_excl < a <= bis_incl)

    monate = []
    for j in range(J0, J1 + 1):
        for m in range(1, 13):
            v, listung = verfall(j, m)
            if v not in pos:
                raise SystemExit("Verfallstag %s ohne Kurszeile" % v)
            mo = v - timedelta(days=v.weekday())
            vorwoche_ende = mo - timedelta(days=1)          # Sonntag davor → letzter Schluss davor
            mo_n = mo + timedelta(days=7)
            fr_n = mo_n + timedelta(days=4)
            tage_vw = sum(1 for a in daten if mo <= a <= v)
            tage_wd = sum(1 for a in daten if mo_n <= a <= fr_n)
            zwischen = sum(1 for a in daten if v < a < mo_n)
            i = pos[v]
            pfad = None
            if i - PFAD_VOR >= 0 and i + PFAD_NACH < len(daten):
                basis = 0.0
                pfad = []
                for k in range(-PFAD_VOR, PFAD_NACH + 1):
                    if k > -PFAD_VOR:
                        basis += lr[i + k]
                    pfad.append(100.0 * math.exp(basis))
            e = {"jahr": j, "monat": m, "verfall": v.isoformat(), "listung": listung,
                 "verfallswoche": pct(summe(vorwoche_ende, v)), "tage_verfallswoche": tage_vw,
                 "woche_danach": pct(summe(v, fr_n)), "tage_woche_danach": tage_wd, "zeilen_zwischen": zwischen,
                 "pfad": pfad}
            if m == 11:
                tg = thanksgiving(j)
                tmo = tg - timedelta(days=tg.weekday())
                e["thanksgiving"] = tg.isoformat()
                e["abstand_tage"] = (tg - v).days
                e["thanksgiving_woche"] = pct(summe(tmo - timedelta(days=1), tmo + timedelta(days=4)))
                e["tage_thanksgiving_woche"] = sum(1 for a in daten if tmo <= a <= tmo + timedelta(days=4))
            monate.append(e)

    nov = [e for e in monate if e["monat"] == 11]
    rest = [e for e in monate if e["monat"] != 11]
    nov6 = [e for e in nov if e["abstand_tage"] == 6]
    nov13 = [e for e in nov if e["abstand_tage"] == 13]
    assert len(nov6) + len(nov13) == len(nov)
    assert all(e["woche_danach"] == e["thanksgiving_woche"] for e in nov6)

    # alle Kalenderwochen 1973–2025 als Grundlinie (Woche = Handelstage Mo–Fr, Rendite Schluss Vorwoche → Schluss)
    wochen = {}
    for a, x in zeilen:
        if J0 <= a.year <= J1:
            k = a - timedelta(days=a.weekday())
            wochen.setdefault(k, []).append(x)
    alle_wochen = [pct(sum(v)) for v in wochen.values()]

    def proTag(liste, feld, tage):
        return [e[feld] / e[tage] for e in liste]

    fakten = {
        "datenstand": {"datei": str(DATEI.relative_to(REPO)).replace("\\", "/"), "sha256": SHA256,
                       "letzte_sitzung": meta["letzte_sitzung"], "abgerufen": meta["abgerufen"],
                       "zeitraum": "%d-01 bis %d-12" % (J0, J1), "monate": len(monate),
                       "phantomzeilen": phantome, "fehlende_sitzungen": fehlend},
        "verfall_belegt_ab": "%04d-%02d" % OPEX_AB,
        "listung_anzahl": {k: sum(1 for e in monate if e["listung"] == k) for k in ("belegt", "regel", "projektion")},
        "abstand": {"6": len(nov6), "13": len(nov13), "jahre_13": [e["jahr"] for e in nov13]},
        "A_verfallswoche_nov_gegen_rest": vergleich([e["verfallswoche"] for e in nov],
                                                    [e["verfallswoche"] for e in rest], "november", "uebrige"),
        "B_woche_danach_nov6_gegen_rest": vergleich([e["woche_danach"] for e in nov6],
                                                    [e["woche_danach"] for e in rest], "november_6", "uebrige"),
        "B_pro_tag": vergleich(proTag(nov6, "woche_danach", "tage_woche_danach"),
                               proTag(rest, "woche_danach", "tage_woche_danach"), "november_6", "uebrige"),
        "B_woche_danach_nov_alle": kennzahlen([e["woche_danach"] for e in nov]),
        "C_alle_wochen": kennzahlen(alle_wochen),
        "C_thanksgiving_woche_alle": kennzahlen([e["thanksgiving_woche"] for e in nov]),
        "C_thanksgiving_gegen_alle_wochen": vergleich([e["thanksgiving_woche"] for e in nov], alle_wochen,
                                                      "thanksgiving", "alle_wochen"),
        "E_woche_danach_rest_gegen_alle_wochen": vergleich([e["woche_danach"] for e in rest], alle_wochen,
                                                           "uebrige", "alle_wochen"),
        "D_jahre_13": [{k: e[k] for k in ("jahr", "verfall", "thanksgiving", "verfallswoche", "woche_danach",
                                           "thanksgiving_woche")} for e in nov13],
        "D_13_woche_danach": kennzahlen([e["woche_danach"] for e in nov13]),
        "D_13_thanksgiving_woche": kennzahlen([e["thanksgiving_woche"] for e in nov13]),
        "tage_woche_danach_nov6": sorted({e["tage_woche_danach"] for e in nov6}),
        "tage_woche_danach_rest": {str(k): sum(1 for e in rest if e["tage_woche_danach"] == k)
                                   for k in sorted({e["tage_woche_danach"] for e in rest})},
    }
    # Hälften
    for name, a, b in (("1973_1999", 1973, 1999), ("2000_2025", 2000, 2025)):
        n_ = [e for e in nov if a <= e["jahr"] <= b]
        n6 = [e for e in nov6 if a <= e["jahr"] <= b]
        r_ = [e for e in rest if a <= e["jahr"] <= b]
        fakten["haelfte_" + name] = {
            "A": vergleich([e["verfallswoche"] for e in n_], [e["verfallswoche"] for e in r_], "november", "uebrige"),
            "B": vergleich([e["woche_danach"] for e in n6], [e["woche_danach"] for e in r_], "november_6", "uebrige"),
        }
    # Pfad (Mittel) Nov-6 gegen übrige Monate
    def mittelpfad(liste):
        p = [e["pfad"] for e in liste if e["pfad"] is not None]
        return {"n": len(p), "pfad": [S.fmean(x[k] for x in p) for k in range(len(p[0]))]}
    fakten["pfad_offsets"] = list(range(-PFAD_VOR, PFAD_NACH + 1))
    fakten["pfad_november_6"] = mittelpfad(nov6)
    fakten["pfad_uebrige"] = mittelpfad(rest)

    # Termine 2026
    e26 = opex_ereignis(2026, 11, PRUEFDATUM)
    d26 = opex_ereignis(2026, 12, PRUEFDATUM)
    v26 = vix_ereignis(2026, 10, PRUEFDATUM)    # Kontraktmonat 2026-11? → Settlement im November prüfen
    v26b = vix_ereignis(2026, 11, PRUEFDATUM)
    halb = [e.wirksam.isoformat() for e in ereignisse("NYSE", 2026) if e.art == "halbtag"]
    fakten["termine_2026"] = {
        "opex_nov": e26["verfallstermin"], "opex_nov_listung": e26["listung"], "opex_nov_triple": e26["triple_witching"],
        "opex_dez": d26["verfallstermin"], "opex_dez_triple": d26["triple_witching"],
        "vix_kontrakt_2026_10": v26["settlement"] if v26 else None,
        "vix_kontrakt_2026_11": v26b["settlement"] if v26b else None,
        "vix_kontrakt_2026_11_listung": v26b["listung_futures"] if v26b else None,
        "thanksgiving": thanksgiving(2026).isoformat(), "abstand": (thanksgiving(2026) - date(2026, 11, 20)).days,
        "halbtage": halb,
        "naechste_13_jahre": [j for j in range(2026, 2041) if date(j, 11, 1).weekday() == 4],
        "letzte_13_jahre": [j for j in range(1973, 2026) if date(j, 11, 1).weekday() == 4],
    }
    fakten["einzeln_november"] = [{k: e[k] for k in ("jahr", "verfall", "listung", "thanksgiving", "abstand_tage",
                                                     "verfallswoche", "woche_danach", "tage_woche_danach")}
                                  for e in nov]
    AUS.parent.mkdir(parents=True, exist_ok=True)
    AUS.write_text(json.dumps(fakten, ensure_ascii=False, indent=1), encoding="utf-8")
    kurz = {k: v for k, v in fakten.items() if k not in ("einzeln_november",)}
    print(json.dumps(kurz, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
