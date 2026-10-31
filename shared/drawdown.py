"""
shared/drawdown.py — Drawdown-Analyse eines Tickers (Fachkern Python; Zwilling von landing/js/drawdown-compute.js).

Plan: docs/review_prompts/2026-10-31_drawdown_seite_plan_v3.md (+ v2, Methodik 2026-10-31_drawdown_analyse_plan.md),
von Codex mit Auflagen freigegeben. Rein beschreibend: keine Prognose, kein Signifikanztest.

Verträge (Kurzfassung):
  * E = letzte offene Sitzung STRIKT VOR dem heutigen Börsendatum (konservativ; Krypto: letzter abgeschlossener
    UTC-Tag, Forex: letzter Werktag vor dem UTC-Datum). Zeilen nach E zählen nicht.
  * Achse = offene Sitzungen der Börse des Tickers von der ersten Kurszeile bis E. Sitzungsrendite = Summe der
    log_return der Zeilen nach der vorigen Sitzung bis s (Phantomzeilen an Nicht-Sitzungen exakt eingerechnet).
    Unbekannt, wenn an s keine Zeile liegt oder eine beteiligte Rendite fehlt/nicht endlich ist.
  * Ab der ersten unbekannten Rendite ist der Pfad unbekannt: nur Episoden, die vorher vollständig abgeschlossen
    sind, gelten; es wird nie neu basiert, kein laufender Drawdown, keine Ränge.
  * Episode: Peak (letzter Schluss mit DD = 0) bis Recovery (erste Sitzung mit Index ≥ Peak). Trough = erste Sitzung
    mit minimalem DD. Zeitraum = Peak im Zeitraum (Start = E minus N Kalenderjahre).
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from shared import sitzungen as SZ
from shared.exchange_holidays import kalender_status

HORIZONTE = (20, 60, 120)
# Renditebasis je Instrument (Bauplan v3, B3): nur belegte Einträge; alles andere „neutral“. Kursindizes laut
# Indexanbieter (S&P DJI, Nasdaq), DAX laut Qontigo/Deutsche Börse als Performanceindex.
RENDITEBASIS = {"^GSPC": "kursindex", "^NDX": "kursindex", "^DJI": "kursindex", "^GDAXI": "performanceindex"}
Z95 = 1.959963984540054
# Schwellenvergleiche mit Toleranz: log/exp runden in Python und JS im letzten Bit verschieden; ein Drawdown von
# genau −10 % darf nicht in einem Zwilling die Schwelle erreichen und im anderen nicht.
EPS = 1e-12


# ───────────────────────────── Hilfen ─────────────────────────────

def quantil(werte, q):
    """Lineare Interpolation wie numpy ('linear'); leere Liste → None."""
    s = sorted(werte)
    if not s:
        return None
    pos = (len(s) - 1) * q
    lo = math.floor(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def _iso(d) -> str:
    return d.isoformat() if isinstance(d, date) else str(d)[:10]


def minus_jahre(iso: str, n: int) -> str:
    d = date.fromisoformat(iso)
    try:
        return d.replace(year=d.year - n).isoformat()
    except ValueError:                       # 29.02.
        return d.replace(year=d.year - n, day=28).isoformat()


def stichtag(boerse: str, jetzt: datetime) -> str:
    """E nach der konservativen Regel (beide Produktionspfade identisch)."""
    heute = SZ.heute(boerse, jetzt)["datum"]
    return _iso(SZ.vorherige(heute, boerse, einschliesslich=False))


# ───────────────────────────── Achse ─────────────────────────────

BRUECKE_TOL = 1e-6
BRUECKE_MAX = 2


def _endlich(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def achse(zeilen, boerse: str, jetzt: datetime) -> dict:
    """zeilen: Liste von dicts {date, close, log_return} (aufsteigend, eindeutig). Ergebnis siehe Modulkopf.

    Fehlende Kurszeile an einer Kalendersitzung (Nachtrag 2 zum Bauplan v3): überbrückt (Sitzung entfällt, die
    Rendite der nächsten vorhandenen Sitzung trägt beide Tage) NUR wenn der Kalender des Jahres nicht belegt ist
    (ungeprueft/annahme; FOREX = Konvention zählt dazu, CRYPTO nie), höchstens BRUECKE_MAX Sitzungen in Folge fehlen,
    eine spätere Zeile existiert und Σ log_return (v, n] = ln(close_n/close_v) auf BRUECKE_TOL genau. Sonst echte
    Lücke. Fehlen Zeilen am Reihenende vor E: aktueller Wert unbekannt (ende_fehlt)."""
    daten = [_iso(z["date"]) for z in zeilen]
    if daten != sorted(daten) or len(set(daten)) != len(daten):
        raise ValueError("Kurszeilen nicht aufsteigend oder mit doppelten Daten")
    e = stichtag(boerse, jetzt)
    aus = {"boerse": boerse, "e": e, "datenende": daten[-1] if daten else None, "daten": [], "lr": [],
           "n_nach_e": sum(1 for d in daten if d > e), "n_phantom": 0, "erste_luecke": None, "ende_fehlt": False,
           "n_ueberbrueckt": 0, "ueberbrueckt_jahre": [], "kalender_nicht_belegt": []}
    zeilen = [z for z, d in zip(zeilen, daten) if d <= e]
    zd = [d for d in daten if d <= e]
    if not zeilen:
        return aus
    sitz = [_iso(x) for x in SZ.sitzungen(boerse, zd[0], e)]
    satz = set(sitz)
    aus["n_phantom"] = sum(1 for d in zd if d not in satz)
    zeile_an = {d: i for i, d in enumerate(zd)}
    i0 = next((k for k, x in enumerate(sitz) if x in zeile_an), None)
    if i0 is None:
        return aus
    sitz = sitz[i0:]

    def summe(v_row, n_row):
        """Σ log_return der Zeilen v_row+1 … n_row; None, wenn eine fehlt/nicht endlich ist."""
        t = 0.0
        for q in range(v_row + 1, n_row + 1):
            x = zeilen[q]["log_return"]
            if not _endlich(x):
                return None
            t += x
        return t

    def brueckenfaehig(fehl, v_row, n_row):
        if boerse == "CRYPTO" or len(fehl) > BRUECKE_MAX:
            return False
        if boerse != "FOREX" and any(kalender_status(boerse, int(x[:4])) not in ("ungeprueft", "annahme") for x in fehl):
            return False
        t = summe(v_row, n_row)
        cv, cn = zeilen[v_row].get("close"), zeilen[n_row].get("close")
        if t is None or not _endlich(cv) or not _endlich(cn) or cv <= 0 or cn <= 0:
            return False
        return abs(t - math.log(cn / cv)) <= BRUECKE_TOL

    v_row = zeile_an[sitz[0]]
    aus["daten"], aus["lr"] = [sitz[0]], [0.0]
    jahre_ue = set()
    k = 1
    while k < len(sitz):
        x = sitz[k]
        if x in zeile_an:
            n_row = zeile_an[x]
            aus["daten"].append(x)
            aus["lr"].append(summe(v_row, n_row))
            v_row = n_row
            k += 1
            continue
        fehl = []
        while k < len(sitz) and sitz[k] not in zeile_an:
            fehl.append(sitz[k])
            k += 1
        if k == len(sitz):                               # Reihenende: keine spätere Zeile
            aus["ende_fehlt"] = True
            break
        n_row = zeile_an[sitz[k]]
        if brueckenfaehig(fehl, v_row, n_row):
            aus["n_ueberbrueckt"] += len(fehl)
            jahre_ue.update(int(f_[:4]) for f_ in fehl)
            continue                                     # sitz[k] wird im nächsten Durchlauf normal verarbeitet
        for f_ in fehl:                                  # echte Lücke
            aus["daten"].append(f_)
            aus["lr"].append(None)
    unbekannt = next((q for q, v in enumerate(aus["lr"]) if v is None), None)
    if unbekannt is not None:
        aus["erste_luecke"] = aus["daten"][unbekannt]
    aus["ueberbrueckt_jahre"] = sorted(jahre_ue)
    jahre = range(int(sitz[0][:4]), int(e[:4]) + 1)
    aus["kalender_nicht_belegt"] = [j_ for j_ in jahre if kalender_status(boerse, j_) not in ("belegt", "konvention")]
    return aus


def index_und_dd(a: dict) -> dict:
    """Index (bis vor die erste Lücke), laufendes Hoch, Drawdown D_t (Anteil, negativ)."""
    lr = a["lr"]
    ende = len(lr) if a["erste_luecke"] is None else lr.index(None)      # erste unbekannte Position
    idx, hoch, dd, k, h = [], [], [], 0.0, None
    for i in range(ende):
        k += lr[i]
        x = math.exp(k)
        h = x if h is None else max(h, x)
        idx.append(x)
        hoch.append(h)
        d = x / h - 1
        dd.append(0.0 if d > -EPS else d)          # Rundungsrest beim Wiedererreichen ist kein Drawdown
    return {"idx": idx, "hoch": hoch, "dd": dd, "bekannt": ende}


# ───────────────────────────── Episoden ─────────────────────────────

def episoden(a: dict, k: dict) -> list[dict]:
    """Episoden im bekannten Pfad. r=None + offen=True: läuft bis E (nur ohne Lücke) bzw. unbestimmbar (Lücke)."""
    idx, n = k["idx"], k["bekannt"]
    aus, peak, ep = [], 0, None
    for i in range(1, n):
        if idx[i] >= idx[peak] * (1 - EPS):        # Recovery mit Toleranz (Codex Code R1, Befund 1)
            if ep is not None:
                ep["r"] = i
                aus.append(ep)
                ep = None
            peak = i
        else:
            d = idx[i] / idx[peak] - 1
            if ep is None:
                ep = {"p": peak, "t": i, "r": None, "tiefe": d}
            elif d < ep["tiefe"] - EPS:                # Gleichstand (auch numerisch) → früherer Trough
                ep["t"], ep["tiefe"] = i, d
    if ep is not None:
        ep["laufend"] = a["erste_luecke"] is None and not a["ende_fehlt"]   # sonst offen, aber nicht „laufend bis E“
        aus.append(ep)
    return aus


def erster_uebertritt(k: dict, ep: dict, schwelle: float):
    """Erste Sitzung der Episode mit DD ≤ schwelle (schwelle negativ, ungerundet), sonst None."""
    idx, h = k["idx"], k["idx"][ep["p"]]
    ende = ep["r"] if ep["r"] is not None else k["bekannt"]
    for i in range(ep["p"] + 1, ende):
        if idx[i] / h - 1 <= schwelle + EPS:
            return i
    return None


def _kt(a, i, j):
    return (date.fromisoformat(a["daten"][j]) - date.fromisoformat(a["daten"][i])).days


def beschreibe(a, k, ep, d_heute=None) -> dict:
    z = {"peak": a["daten"][ep["p"]], "trough": a["daten"][ep["t"]],
         "recovery": a["daten"][ep["r"]] if ep["r"] is not None else None,
         "max_dd": 100 * ep["tiefe"], "peak_to_trough": ep["t"] - ep["p"],
         "peak_to_trough_kt": _kt(a, ep["p"], ep["t"])}
    if ep["r"] is not None:
        z.update({"dauer": ep["r"] - ep["p"], "dauer_kt": _kt(a, ep["p"], ep["r"]),
                  "ttr": ep["r"] - ep["t"], "ttr_kt": _kt(a, ep["t"], ep["r"])})
    if d_heute is not None and d_heute < 0:
        s = erster_uebertritt(k, ep, d_heute)
        if s is not None:
            z["uebertritt"] = a["daten"][s]
            z["bis_uebertritt"] = s - ep["p"]
            if ep["r"] is not None:
                z["ab_uebertritt_bis_recovery"] = ep["r"] - s
    return z


# ───────────────────────────── Auswertung ─────────────────────────────

def analyse(zeilen, boerse: str, jetzt: datetime) -> dict:
    """Grundgerüst, das Seite und Nightly teilen: Achse, Episoden, laufender Drawdown, Kurve."""
    a = achse(zeilen, boerse, jetzt)
    if len(a["daten"]) < 2:
        return {"achse": a, "status": "zu_wenig_daten"}
    k = index_und_dd(a)
    eps = episoden(a, k)
    letzt = k["bekannt"] - 1
    aktuell = a["erste_luecke"] is None and not a["ende_fehlt"]
    lauf = eps[-1] if aktuell and eps and eps[-1]["r"] is None and eps[-1].get("laufend") else None
    d_heute = (k["idx"][letzt] / k["hoch"][letzt] - 1) if aktuell else None
    status = "luecke" if a["erste_luecke"] is not None else ("nicht_aktuell" if a["ende_fehlt"] else "ok")
    out = {"achse": a, "k": k, "eps": eps, "status": status, "d_heute": None if d_heute is None else 100 * d_heute}
    if lauf is not None:
        z = beschreibe(a, k, lauf, d_heute)
        z.update({"seit_peak": letzt - lauf["p"], "seit_peak_kt": _kt(a, lauf["p"], letzt)})
        out["laufend"] = z
    return out


def gruppe(res: dict, start: str, m: float) -> dict:
    """Abgeschlossene Episoden mit Peak ≥ start und Max Drawdown ≤ −m % (m in Prozent), Ränge des laufenden."""
    a, k = res["achse"], res["k"]
    grp = [e for e in res["eps"] if e["r"] is not None and a["daten"][e["p"]] >= start and -100 * e["tiefe"] >= m - 100 * EPS]
    dauer = [e["r"] - e["p"] for e in grp]
    n = len(grp)
    g = {"n": n, "dauer_median": quantil(dauer, .5), "dauer_q25": quantil(dauer, .25),
         "dauer_q75": quantil(dauer, .75), "dauer_max": max(dauer) if dauer else None,
         "ttr_median": quantil([e["r"] - e["t"] for e in grp], .5),
         "einzel": [beschreibe(a, k, e, None if res["d_heute"] is None else res["d_heute"] / 100) for e in grp]}
    lauf = res.get("laufend")
    g["laufend_erfuellt"] = bool(lauf) and -res["d_heute"] >= m - 100 * EPS
    if g["laufend_erfuellt"]:
        g["kuerzer_als_laufend"] = sum(1 for x in dauer if x < lauf["seit_peak"])
        g["tiefer_als_laufend"] = sum(1 for e in grp if 100 * e["tiefe"] < res["d_heute"] - 100 * EPS)
    g["dauerkurve"] = ([[0, 1.0]] + [[t, sum(1 for x in dauer if x > t) / n] for t in sorted(set(dauer))]) if n else []
    return g


def grenzueberschreitend(res: dict, start: str) -> list[dict]:
    a, k = res["achse"], res["k"]
    return [beschreibe(a, k, e) for e in res["eps"] if a["daten"][e["p"]] < start
            and (e["r"] is None or a["daten"][e["r"]] >= start) and e["tiefe"] <= -0.05 + EPS]


def zeitanteil(res: dict, start: str):
    """Anteil der Sitzungen im Zeitraum (bekannter Pfad) mit DD ≤ aktuellem DD."""
    if res["d_heute"] is None:
        return None
    a, k = res["achse"], res["k"]
    tage = [i for i in range(k["bekannt"]) if a["daten"][i] >= start]
    return {"n": len(tage), "mind": sum(1 for i in tage if 100 * k["dd"][i] <= res["d_heute"] + 100 * EPS)}


def vergleich_ab(res: dict, start: str, x: float) -> dict:
    """Frühere Episoden (Peak ≥ start, abgeschlossen), die −x % erreichten: Handelstage bis zum Übertritt und vom
    Übertritt bis zur Recovery; dazu dieselbe Größe der laufenden Episode (falls sie −x % erreicht hat)."""
    a, k = res["achse"], res["k"]
    s = -x / 100
    tempo, ab, einzel = [], [], []
    for e in res["eps"]:
        if e["r"] is None or a["daten"][e["p"]] < start:
            continue
        c = erster_uebertritt(k, e, s)
        if c is None:
            continue
        tempo.append(c - e["p"])
        ab.append(e["r"] - c)
        einzel.append({"peak": a["daten"][e["p"]], "uebertritt": a["daten"][c], "bis_uebertritt": c - e["p"],
                       "ab_uebertritt_bis_recovery": e["r"] - c})
    lauf_tempo = None
    lauf = res.get("laufend")
    if lauf is not None:
        ep = res["eps"][-1]
        c = erster_uebertritt(k, ep, s)
        lauf_tempo = None if c is None else c - ep["p"]
    return {"x": x, "n": len(ab), "einzel": einzel, "ab_median": quantil(ab, .5), "ab_q25": quantil(ab, .25),
            "ab_q75": quantil(ab, .75), "tempo_laufend": lauf_tempo,
            "langsamer_als_laufend": (sum(1 for t in tempo if t > lauf_tempo) if lauf_tempo is not None else None)}


def kaplan_meier(res: dict, start: str, x: float) -> dict:
    """KM ab erstem Übertritt von −x %: Ereignis = Recovery; zensiert = laufende Episode (bei E) bzw. Episode, die
    an der ersten Lücke noch offen war (am letzten bekannten Tag). Gleichstände: Ereignisse vor Zensierungen."""
    a, k = res["achse"], res["k"]
    s = -x / 100
    letzt = k["bekannt"] - 1
    beob = []                                         # (zeit, ereignis 1/0)
    for e in res["eps"]:
        if a["daten"][e["p"]] < start:
            continue
        c = erster_uebertritt(k, e, s)
        if c is None:
            continue
        if e["r"] is not None:
            beob.append((e["r"] - c, 1))
        else:
            beob.append((letzt - c, 0))
    beob.sort(key=lambda b: (b[0], -b[1]))
    n_risk, s_t, var_sum, kurve = len(beob), 1.0, 0.0, []
    kurve.append({"t": 0, "s": 1.0, "risiko": n_risk, "lo": None, "hi": None})
    i = 0
    median = None
    while i < len(beob):
        t = beob[i][0]
        d = sum(1 for b in beob if b[0] == t and b[1] == 1)
        c = sum(1 for b in beob if b[0] == t and b[1] == 0)
        if d:
            s_t *= (1 - d / n_risk)
            if n_risk - d > 0:
                var_sum += d / (n_risk * (n_risk - d))
            lo = hi = None
            if 0 < s_t < 1:
                se = math.sqrt(var_sum) / abs(math.log(s_t))
                ll = math.log(-math.log(s_t))
                lo, hi = math.exp(-math.exp(ll + Z95 * se)), math.exp(-math.exp(ll - Z95 * se))
            kurve.append({"t": t, "s": s_t, "risiko": n_risk, "lo": lo, "hi": hi})
            if median is None and s_t <= 0.5:
                median = t
        n_risk -= d + c
        i += d + c
    return {"x": x, "n": len(beob), "ereignisse": sum(b[1] for b in beob),
            "zensiert": [b[0] for b in beob if b[1] == 0], "kurve": kurve, "median": median}


def forward_returns(res: dict, start: str, x: float) -> dict:
    """Ereignis = erster Übertritt von −x % je Episode (Peak ≥ start). F_h ab Schluss des Übertrittstags."""
    a, k = res["achse"], res["k"]
    s, letzt, lr = -x / 100, k["bekannt"] - 1, a["lr"]
    ereig = []
    for e in res["eps"]:
        if a["daten"][e["p"]] < start:
            continue
        c = erster_uebertritt(k, e, s)
        if c is not None:
            ereig.append(c)

    def pfad(i, h):
        if i + h > letzt:
            return None
        kum, mn = 0.0, 0.0
        for j in range(i + 1, i + h + 1):
            kum += lr[j]
            mn = min(mn, math.exp(kum) - 1)
        return math.exp(kum) - 1, mn

    out = {"x": x, "h": {}}
    basis_idx = [i for i in range(k["bekannt"]) if a["daten"][i] >= start]
    for h in HORIZONTE:
        werte = [pfad(c, h) for c in ereig]
        voll = [w for w in werte if w is not None]
        bas = [w for w in (pfad(i, h) for i in basis_idx) if w is not None]
        gueltig = [c for c in ereig if c + h <= letzt]
        ueberlapp = sum(1 for i in range(len(gueltig)) for j in range(i + 1, len(gueltig))
                        if abs(gueltig[i] - gueltig[j]) < h)
        def kz(v):
            if not v:
                return None
            f = [100 * w[0] for w in v]
            return {"n": len(v), "mittel": sum(f) / len(f), "median": quantil(f, .5),
                    "anteil_positiv": sum(1 for w in v if w[0] > EPS) / len(v),
                    "zwischenverlust_mittel": sum(100 * w[1] for w in v) / len(v)}
        out["h"][str(h)] = {"ereignisse": kz(voll), "unvollstaendig": len(werte) - len(voll),
                            "basis": kz(bas), "ueberlappende_paare": ueberlapp}
    return out


def kalender(res: dict) -> list[dict]:
    """Je Kalenderjahr: tiefster Abstand zum bisherigen Hoch (Hoch seit Datenbeginn) und Ulcer Index. Jahre ab der
    ersten Lücke: unbekannt."""
    a, k = res["achse"], res["k"]
    daten, n_alle = a["daten"], len(a["daten"])
    jahre = sorted({d[:4] for d in daten})
    aus = []
    for j in jahre:
        pos = [i for i in range(n_alle) if daten[i][:4] == j]
        bekannt = all(i < k["bekannt"] for i in pos)
        z = {"jahr": int(j), "n": len(pos), "teiljahr": j == jahre[0] or j == jahre[-1],
             "tiefster": None, "ulcer": None}
        if bekannt and pos:
            d = [100 * k["dd"][i] for i in pos]
            z["tiefster"] = min(d)
            z["ulcer"] = math.sqrt(sum(x * x for x in d) / len(d))
        aus.append(z)
    return aus


def kurve(res: dict) -> list:
    a, k = res["achse"], res["k"]
    return [[a["daten"][i], 100 * k["dd"][i]] for i in range(k["bekannt"])]
