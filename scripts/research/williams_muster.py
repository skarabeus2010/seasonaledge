"""Ereignisstudie Williams-Kursmuster — nach dem freigegebenen Prüfplan.

Plan: docs/review_prompts/2026-10-17_williams_muster_plan_v2.md mit den Ersetzungen aus v3 (§7, §8) und v4 (§8 c),
Freigabe docs/review_prompts/2026-10-17_williams_muster_plan_v4_antwort.md. Jede Konstante unten steht dort.
Code-Review: docs/review_prompts/2026-10-17_williams_muster_code_r*.md.

Phasen (nur lesend aus der DB, Ausgaben unter logs/williams/):
  --laden         Kurse aus Supabase → Export (gz-JSON) + SHA-256. Alle weiteren Phasen lesen NUR den Export.
  --entdeckung    Entdeckungsabschnitt 2000–2023 + Hälften + explorative Werte. Die Kurszeilen werden VOR der
                  Aufbereitung auf ≤ 2023-12-29 gekürzt — aus dem Prüfzeitraum wird nichts gelesen.
  --einfrieren    schreibt Richtung d und die weitergereichten Hypothesen fest (exklusiv, nie überschreiben).
  --pruefzeitraum nur mit Einfrier-Datei, gleichem Export und unverändertem Skript.

Renditen nur aus `log_return` (Close→Close) und ln(C/Einstieg) derselben Zeile — nie O[t+1]/C[t]
(unterschiedliche Bereinigungsstände, CLAUDE.md).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
from bisect import bisect_left, bisect_right, insort
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Konstanten aus dem Plan ───────────────────────────────────────────────────────────────────────────────────────
H_MAX = 10                      # v2 §5: dieselbe Ereignismenge für alle Horizonte (t+10 im Abschnitt)
HAUPT = 5                       # konfirmatorisch nur h = 5 (v2 §6)
KOSTEN = 0.0010                 # 5 Bp je Seite, Log-Einheiten (v2 §3)
MIN_KONTROLLE = 20              # v3 §7
RV_FENSTER = 20                 # v2 §4
RV_VORGESCHICHTE = 250          # v2 §4
BLOCK = 20                      # v3 §7, Sensitivität 10/40
BLOCK_SENS = (10, 40)
B_STANDARD = 20_000
B_FEIN = 100_000
B_SENS = 5_000
ALPHA = 0.05
RELEVANZ_GERICHTET = 0.0010     # |T| ≥ 0,10 % auf 5 Sitzungen (v3 §7)
RELEVANZ_REL = 0.05             # INSIDE/BODY |T|/K ≥ 5 %
MIN_EREIGNISSE, MIN_TICKER, MIN_HAELFTE, MIN_PRUEF = 1000, 100, 300, 150   # v2 §7
AUSFALL_MAX = 0.01              # v3 §7
MIN_TICKER_ANZEIGE = 30         # v2 §5: Ticker-Einzelwerte erst ab n = 30
LADEN_AB = "1998-01-01"

ABSCHNITTE = {
    "entdeckung": ("2000-01-03", "2023-12-29"),
    "haelfte1": ("2000-01-03", "2011-12-30"),
    "haelfte2": ("2012-01-02", "2023-12-29"),
    "pruef": ("2024-01-02", "2026-09-30"),
}
ENTDECKUNG_BIS = ABSCHNITTE["entdeckung"][1]

HYPOTHESEN = [
    ("H1", "SMASH_K", "bek", +1), ("H2", "SMASH_K", "stopp", +1),
    ("H3", "SMASH_V", "bek", -1), ("H4", "SMASH_V", "stopp", -1),
    ("H5", "OUT_K", "bek", +1), ("H6", "OUT_K", "open", +1),
    ("H7", "OUT_V", "bek", -1), ("H8", "OUT_V", "open", -1),
    ("H9", "INSIDE", "abs", 0), ("H10", "BODY", "abs", 0),
]
NETTO = {"H2": "N2", "H4": "N4", "H6": "N6", "H8": "N8"}       # v4
AUSGABE = _ROOT / "logs" / "williams"


def im_universum(t: str) -> bool:
    """v2 §3: nur Aktien und ETFs — ohne Krypto, Devisen, Futures, Indizes."""
    return not (t.endswith("-USD") or t.endswith("=X") or t.endswith("=F") or t.startswith("^"))


def kuerzen(rows: list, bis: str | None) -> list:
    """Zeilen nach `bis` entfernen — vor jeder Aufbereitung (Entdeckung sieht den Prüfzeitraum nicht)."""
    return rows if bis is None else [r for r in rows if r[0] <= bis]


# ── Aufbereitung je Ticker ────────────────────────────────────────────────────────────────────────────────────────
def aufbereiten(rows: list, sitzungen: list, volumen_pflicht: bool = True) -> dict:
    """rows: [[date, o, h, l, c, v, lr], …] aufsteigend; sitzungen: Handelstage der Börse (ISO, aufsteigend)."""
    n = len(rows)
    d = [r[0] for r in rows]
    a = np.array([[np.nan if x is None else float(x) for x in r[1:7]] for r in rows], dtype=float).reshape(n, 6)
    o, h, l, c, v, lr = (a[:, k] for k in range(6))
    sidx = {s: k for k, s in enumerate(sitzungen)}
    pos = np.array([sidx.get(x, -10**9) for x in d], dtype=np.int64)

    endlich = np.isfinite(a[:, [0, 1, 2, 3, 5]]).all(axis=1)
    with np.errstate(invalid="ignore"):
        positiv = (o > 0) & (h > 0) & (l > 0) & (c > 0)
        geometrie = (h > l) & (l <= np.minimum(o, c)) & (h >= np.maximum(o, c))
        vol_ok = (v > 0) if volumen_pflicht else np.ones(n, bool)
    handelstag = pos >= 0
    kopie = np.zeros(n, bool)
    if n > 1:
        kopie[1:] = (c[1:] == c[:-1]) & ~(v[1:] > 0)
    gueltig = endlich & positiv & geometrie & vol_ok & handelstag & ~kopie
    grund = np.full(n, "", dtype=object)               # erster Grund je ungültiger Zeile (für die Diagnostik)
    # Reihenfolge = Vorrang in der Diagnostik: eine Kopie hat auch Volumen 0, soll aber als Kopie zählen
    for maske, name in ((~endlich, "nicht_endlich"), (~positiv, "nicht_positiv"), (kopie, "kopie"),
                        (~geometrie, "geometrie"), (~vol_ok, "volumen"), (~handelstag, "kein_handelstag")):
        grund[(grund == "") & maske] = name

    glied = np.zeros(n, bool)
    basisbruch = np.zeros(n, bool)
    luecke = np.zeros(n, bool)
    if n > 1:
        with np.errstate(divide="ignore", invalid="ignore"):
            diff = np.abs(np.log(c[1:] / c[:-1]) - lr[1:])
            tol = 1e-4 + 1e-4 / c[1:]
        basis = diff <= tol
        folge = pos[1:] == pos[:-1] + 1
        beide = gueltig[1:] & gueltig[:-1]
        glied[1:] = beide & folge & basis
        luecke[1:] = beide & ~folge
        basisbruch[1:] = beide & folge & ~basis

    pre = np.concatenate([[0], np.cumsum(glied.astype(np.int64))])
    fenster = np.zeros(n, bool)                        # glied[k] für k = t … t+H_MAX (deckt t−1 … t+H_MAX)
    if n > H_MAX + 1:
        t = np.arange(1, n - H_MAX)
        fenster[t] = (pre[t + H_MAX + 1] - pre[t]) == H_MAX + 1

    lr0 = np.where(np.isfinite(lr), lr, 0.0)
    P = np.concatenate([[0.0], np.cumsum(lr0)])       # P[k] = Σ lr[0..k−1]

    # Vola-Quintil (v2 §4, Code-Review R1): Std der 20 Renditen lr[t−19..t] (nur mit glied[t−19..t]); Rang gegen die
    # Vorgeschichte BIS EINSCHLIESSLICH t; mindestens 250 Vorwerte (ohne t).
    quintil = np.full(n, -1, dtype=np.int64)
    hist: list[float] = []
    for t in range(RV_FENSTER, n):
        if pre[t + 1] - pre[t - RV_FENSTER + 1] != RV_FENSTER:
            continue
        rv = float(np.std(lr[t - RV_FENSTER + 1:t + 1], ddof=1))
        genug = len(hist) >= RV_VORGESCHICHTE
        insort(hist, rv)
        if genug:
            lo, hi = bisect_left(hist, rv), bisect_right(hist, rv)
            quintil[t] = min(4, int((lo + hi) / 2.0 / len(hist) * 5))

    return {"d": d, "o": o, "h": h, "l": l, "c": c, "lr": lr, "P": P, "gueltig": gueltig, "glied": glied,
            "fenster": fenster, "quintil": quintil, "grund": grund, "basisbruch": basisbruch, "luecke": luecke,
            "n": n}


def muster_roh(r: dict) -> dict:
    """Mustergeometrie an t ohne Fensterbedingung (für die Diagnostik verworfener Kandidaten)."""
    n, o, h, l, c = r["n"], r["o"], r["h"], r["l"], r["c"]
    z = {}
    hv = np.r_[np.nan, h[:-1]] if n else h
    lv = np.r_[np.nan, l[:-1]] if n else l
    with np.errstate(invalid="ignore"):
        z["SMASH_K"] = c < lv
        z["SMASH_V"] = c > hv
        aussen = (h > hv) & (l < lv)
        z["OUT_K"] = aussen & (c < lv)
        z["OUT_V"] = aussen & (c > hv)
        z["INSIDE"] = (h < hv) & (l > lv)
    body = np.zeros(n, bool)
    for t in range(n):                                 # Produktionsregel newsletter_indicators.py (Python-round)
        if r["gueltig"][t]:
            body[t] = round(abs(o[t] - c[t]) / (h[t] - l[t]) * 100, 1) < 20
    z["BODY"] = body
    return z


def muster(r: dict) -> dict:
    """Muster je t (v2 §2) — nur an Fenster-Tagen wahr."""
    roh = r.get("_roh") or muster_roh(r)
    return {k: v & r["fenster"] for k, v in roh.items()}


def rendite(r: dict, art: str, sicht: int, hz: int) -> np.ndarray:
    """Zielgröße je t (NaN = nicht definiert / nicht ausgelöst). Nur an Fenster-Tagen."""
    n, P, o, h, l, c = r["n"], r["P"], r["o"], r["h"], r["l"], r["c"]
    y = np.full(n, np.nan)
    t = np.nonzero(r["fenster"])[0]
    if not len(t):
        return y
    bek = P[t + hz + 1] - P[t + 1]
    rest = P[t + hz + 1] - P[t + 2]                  # Σ lr[t+2..t+h]
    if art == "bek":
        y[t] = sicht * bek
    elif art == "abs":
        y[t] = np.abs(bek)
    elif art == "open":
        y[t] = sicht * (np.log(c[t + 1] / o[t + 1]) + rest)
    elif art == "stopp":
        if sicht > 0:
            ausgeloest = h[t + 1] > h[t]
            kurs = np.maximum(o[t + 1], h[t])
            wert = np.log(c[t + 1] / kurs) + rest
        else:
            ausgeloest = l[t + 1] < l[t]
            kurs = np.minimum(o[t + 1], l[t])
            wert = -(np.log(c[t + 1] / kurs) + rest)
        y[t] = np.where(ausgeloest, wert, np.nan)
    elif art == "spanne":
        hi = np.array([h[k + 1:k + hz + 1].max() for k in t])
        lo = np.array([l[k + 1:k + hz + 1].min() for k in t])
        y[t] = np.log(hi / lo)
    elif art == "setup":                              # explorativ: Stopp-Setup inkl. nicht ausgelöster (= 0)
        z = rendite(r, "stopp", sicht, hz)
        y[t] = np.where(np.isnan(z[t]), 0.0, z[t])
    else:
        raise ValueError(art)
    return y


def im_abschnitt(r: dict, abschnitt: str) -> np.ndarray:
    a, b = ABSCHNITTE[abschnitt]
    m = np.zeros(r["n"], bool)
    for k in np.nonzero(r["fenster"])[0]:
        if r["d"][k] >= a and r["d"][k + H_MAX] <= b:
            m[k] = True
    return m


# ── Einträge (kompakt) ────────────────────────────────────────────────────────────────────────────────────────────
class Zellen:
    """Zellnummern für (Ticker, Abschnitt[, Quintil]) — kompakt statt Tupel je Eintrag (Speicher, Code-Review R1)."""

    def __init__(self):
        self.id, self.ticker = {}, []

    def nr(self, schluessel) -> int:
        if schluessel not in self.id:
            self.id[schluessel] = len(self.ticker)
            self.ticker.append(schluessel[0])
        return self.id[schluessel]


def achse_fuer(sitzungen: dict, boersen: set, abschnitt: str) -> dict:
    """Gemeinsame Bootstrap-Achse: Vereinigung der SITZUNGEN aller beteiligten Börsen im Abschnitt — auch Tage ohne
    Einträge bleiben als Nullspalten erhalten (Blockstruktur, Code-Review R1)."""
    a, b = ABSCHNITTE[abschnitt]
    tage = sorted({s for bo in boersen for s in sitzungen[bo] if a <= s <= b})
    return {d: i for i, d in enumerate(tage)}


def sammeln(reihen: dict, abschnitt: str, muster_k: str, art: str, sicht: int, hz: int, mit_quintil: bool,
            zellen: Zellen, achse: dict) -> dict:
    """Arrays zelle, datum, y, ev (ev ⊂ Kontrolle: jedes gültige Ereignis ist auch Kontrolltag seiner Zelle)."""
    zs, ds, ys, es = [], [], [], []
    for tk, r in reihen.items():
        maske = r["_abschnitt"][abschnitt]
        if not maske.any():
            continue
        y = rendite(r, art, sicht, hz)
        mu = r["_muster"][muster_k]
        idx = np.nonzero(maske & np.isfinite(y))[0]
        if mit_quintil:
            idx = idx[r["quintil"][idx] >= 0]
            z = [zellen.nr((tk, abschnitt, int(q))) for q in r["quintil"][idx]]
        else:
            nr = zellen.nr((tk, abschnitt))
            z = [nr] * len(idx)
        zs.append(np.array(z, np.int32))
        ds.append(np.array([achse[r["d"][t]] for t in idx], np.int32))
        ys.append(y[idx])
        es.append(mu[idx])
    if not zs:
        return {"zelle": np.zeros(0, np.int32), "datum": np.zeros(0, np.int32), "y": np.zeros(0), "ev": np.zeros(0, bool)}
    return {"zelle": np.concatenate(zs), "datum": np.concatenate(ds), "y": np.concatenate(ys), "ev": np.concatenate(es)}


def daten_aus_tupeln(ko: list, ev: list, zellen: Zellen, achse: dict) -> dict:
    """Hilfe für Wächter: Kontrolle [(zellschlüssel, datum, y)], Ereignisse ⊂ Kontrolle."""
    evs = {(z, d) for z, d, _ in ev}
    return {"zelle": np.array([zellen.nr(z) for z, _, _ in ko], np.int32),
            "datum": np.array([achse[d] for _, d, _ in ko], np.int32),
            "y": np.array([y for _, _, y in ko], float),
            "ev": np.array([(z, d) in evs for z, d, _ in ko], bool)}


# ── Statistik ─────────────────────────────────────────────────────────────────────────────────────────────────────
def punkt(daten: dict, zellen: Zellen) -> dict:
    """T = Mittel der x_e = y_e − m_z (v3 §7); Zellen mit < 20 Kontrolltagen samt Ereignissen ausgeschlossen."""
    z, y, ev = daten["zelle"], daten["y"], daten["ev"]
    Z = len(zellen.ticker)
    cnt = np.bincount(z, minlength=Z)
    s = np.bincount(z, weights=y, minlength=Z)
    ok = cnt >= MIN_KONTROLLE
    m = np.divide(s, cnt, out=np.zeros(Z), where=cnt > 0)
    e = ev & ok[z]
    aus = {"ausgeschlossen_zellen": int((ev & ~ok[z]).sum()), "n": int(e.sum())}
    if not e.any():
        return {**aus, "T": None, "ticker": 0}
    x = y[e] - m[z[e]]
    tk = np.array(zellen.ticker, dtype=object)[z[e]]
    je = {}
    for t_, xi in zip(tk, x):
        je.setdefault(t_, []).append(xi)
    kontrolle = ok[z]
    return {**aus, "T": float(x.mean()), "K": float(m[z[e]].mean()), "ticker": len(je),
            "median_x": float(np.median(x)),
            "T_ticker_gleich": float(np.mean([np.mean(v) for v in je.values()])),
            "anteil_positiv_ereignis": float((y[e] > 0).mean()),
            "anteil_positiv_kontrolle": float((y[kontrolle] > 0).mean()) if kontrolle.any() else None,
            "ticker_einzeln": {k: {"n": len(v), "x": float(np.mean(v))} for k, v in sorted(je.items())
                               if len(v) >= MIN_TICKER_ANZEIGE}}


def netto_punkt(daten: dict) -> float | None:
    y = daten["y"][daten["ev"]]
    return float(y.mean() - KOSTEN) if len(y) else None


def ziehung(D: int, L: float, rng) -> np.ndarray:
    """Stationärer Bootstrap (Politis–Romano): Gewichte je Datum auf der gemeinsamen Achse (zyklisch)."""
    p = 1.0 / L
    idx = np.empty(D, dtype=np.int64)
    pos = 0
    while pos < D:
        s = int(rng.integers(D))
        laenge = min(int(rng.geometric(p)), D - pos)
        idx[pos:pos + laenge] = (s + np.arange(laenge)) % D
        pos += laenge
    return np.bincount(idx, minlength=D)


def _matrizen(daten: dict, Z: int, D: int):
    from scipy.sparse import csr_matrix
    z, d, y, ev = daten["zelle"], daten["datum"], daten["y"], daten["ev"]
    cnt = np.bincount(z, minlength=Z)
    ok = cnt >= MIN_KONTROLLE
    neu = np.cumsum(ok) - 1                            # gültige Zellen kompakt nummerieren
    k = ok[z]
    zz, dd, yy, ee = neu[z[k]], d[k], y[k], ev[k]
    Zk = int(ok.sum())
    S = csr_matrix((yy, (zz, dd)), shape=(Zk, D))
    N = csr_matrix((np.ones(len(yy)), (zz, dd)), shape=(Zk, D))
    EY = csr_matrix((yy[ee], (zz[ee], dd[ee])), shape=(Zk, D))
    E = csr_matrix((np.ones(int(ee.sum())), (zz[ee], dd[ee])), shape=(Zk, D))
    return S, N, EY, E


def bootstrap(alle: dict, Z: int, D: int, B: int, L: float, seed: int, netto: dict | None = None) -> dict:
    """T* je Hypothese mit denselben Ziehungen; netto: {name: daten} → N* = Mittel(R_ein) − Kosten (ohne Kontrolle)."""
    from scipy.sparse import csr_matrix
    rng = np.random.default_rng(seed)
    mats = {k: _matrizen(v, Z, D) for k, v in alle.items()}
    nmats = {}
    for k, v in (netto or {}).items():
        dd, yy = v["datum"][v["ev"]], v["y"][v["ev"]]
        r0 = np.zeros(len(yy), int)
        nmats[k] = (csr_matrix((yy, (r0, dd)), shape=(1, D)), csr_matrix((np.ones(len(yy)), (r0, dd)), shape=(1, D)))
    erg = {k: [] for k in list(mats) + list(nmats)}
    ausfall = {k: [] for k in mats}
    stapel = 500
    for start in range(0, B, stapel):
        b = min(stapel, B - start)
        W = np.stack([ziehung(D, L, rng) for _ in range(b)], axis=1).astype(float)   # D × b
        for k, (S, N, EY, E) in mats.items():
            SW, NW, EYW, EW = S @ W, N @ W, EY @ W, E @ W
            ok = NW > 0
            m = np.divide(SW, NW, out=np.zeros_like(SW), where=ok)
            zaehler = np.where(ok, EYW - m * EW, 0.0).sum(axis=0)
            nenner = np.where(ok, EW, 0.0).sum(axis=0)
            erg[k].append(np.divide(zaehler, nenner, out=np.full(b, np.nan), where=nenner > 0))
            gesamt = EW.sum(axis=0)
            ausfall[k].append(np.divide(gesamt - nenner, gesamt, out=np.zeros(b), where=gesamt > 0))
        for k, (EY1, E1) in nmats.items():
            s, n = np.asarray(EY1 @ W).ravel(), np.asarray(E1 @ W).ravel()
            erg[k].append(np.divide(s, n, out=np.full(b, np.nan), where=n > 0) - KOSTEN)
    return {k: {"T_stern": np.concatenate(v),
                "ausfall": float(np.mean(np.concatenate(ausfall[k]))) if k in ausfall else 0.0}
            for k, v in erg.items()}


def p_zweiseitig(T: float, Ts: np.ndarray) -> float:
    Ts = Ts[np.isfinite(Ts)]
    return float((1 + np.sum(np.abs(Ts - T) >= abs(T))) / (1 + len(Ts)))


def p_einseitig(T: float, Ts: np.ndarray, d: int) -> float:
    Ts = Ts[np.isfinite(Ts)]
    return float((1 + np.sum(d * (Ts - T) >= d * T)) / (1 + len(Ts)))


def intervall(Ts: np.ndarray) -> list:
    Ts = Ts[np.isfinite(Ts)]
    return [float(np.percentile(Ts, 2.5)), float(np.percentile(Ts, 97.5))]


def holm(ps: dict, alpha: float = ALPHA) -> dict:
    """Holm: {name: (verworfen, schwelle)}; None-p zählt als nicht verworfen und bleibt in der Familie."""
    m = len(ps)
    reihe = sorted(ps.items(), key=lambda kv: (1.0 if kv[1] is None else kv[1], kv[0]))
    aus, weiter = {}, True
    for i, (k, p) in enumerate(reihe):
        schwelle = alpha / (m - i)
        verworfen = weiter and p is not None and p < schwelle
        if not verworfen:
            weiter = False
        aus[k] = (verworfen, schwelle)
    return aus


def nahe_schwelle(ps: dict, hl: dict) -> bool:
    """v2 §7: liegt ein p zwischen der Hälfte und dem Doppelten seiner Holm-Schwelle → Feinziehung."""
    return any(p is not None and hl[k][1] / 2 <= p <= 2 * hl[k][1] for k, p in ps.items())


def netto_ps(nps: dict, b_erfuellt: dict) -> dict:
    """v4 §8c: ohne (b) bleibt N in der Familie, kann aber nicht verworfen werden → p = None vor Holm (sonst
    verschöbe ihr kleines p die Schwellen der anderen, Code-Review R1)."""
    return {k: (p if b_erfuellt.get(k) else None) for k, p in nps.items()}


def netto_familie(nps: dict, b_erfuellt: dict) -> dict:
    """Holm über ALLE vier N mit den bereinigten p-Werten."""
    return holm(netto_ps(nps, b_erfuellt))


def fein_noetig(ps: dict, hl: dict, nps: dict, b_erfuellt: dict) -> bool:
    """Feinziehung, wenn ein H- oder N-Test nahe an SEINER Entscheidungsschwelle liegt — für N mit derselben
    bereinigten Familie wie die Entscheidung (Code-Review R2)."""
    return nahe_schwelle(ps, hl) or nahe_schwelle(netto_ps(nps, b_erfuellt), netto_familie(nps, b_erfuellt))


def relevant(name: str, pt: dict) -> bool:
    if pt.get("T") is None:
        return False
    if name in ("H9", "H10"):
        return pt["K"] > 0 and abs(pt["T"]) / pt["K"] >= RELEVANZ_REL
    return abs(pt["T"]) >= RELEVANZ_GERICHTET


# ── Daten ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def laden(ziel: Path) -> Path:
    from shared.sitzungen import sitzungen
    from shared.supabase_client import get_client
    from shared.symbols import get_all_tickers, get_exchange_for_holidays
    c = get_client()
    tickers = sorted(t for t in get_all_tickers() if im_universum(t))
    aus = {"erzeugt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "ab": LADEN_AB,
           "universum": tickers, "ticker": {}, "sitzungen": {}}
    for t in tickers:
        boerse = get_exchange_for_holidays(t)
        if boerse not in aus["sitzungen"]:
            aus["sitzungen"][boerse] = [s.isoformat() for s in sitzungen(boerse, LADEN_AB, "2026-12-31")]
        rows, last = [], "1997-12-31"
        while True:
            for versuch in range(4):
                try:
                    d = (c.table("prices").select("date,open,high,low,close,volume,log_return").eq("ticker", t)
                         .gt("date", last).order("date").limit(1000).execute().data)
                    break
                except Exception:
                    if versuch == 3:
                        raise
                    time.sleep(2 * (versuch + 1))
            if not d:
                break
            rows += [[x["date"], x["open"], x["high"], x["low"], x["close"], x["volume"], x["log_return"]] for x in d]
            last = d[-1]["date"]
            if len(d) < 1000:
                break
        aus["ticker"][t] = {"boerse": boerse, "rows": rows}
        print(f"  {t:10} {boerse:10} {len(rows):6} Zeilen", flush=True)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(ziel, "wt", encoding="utf-8") as f:
        json.dump(aus, f, separators=(",", ":"))
    sha = hashlib.sha256(ziel.read_bytes()).hexdigest()
    ziel.with_suffix(".sha256").write_text(sha + "\n", encoding="utf-8")
    print(f"[laden] {len(tickers)} Ticker → {ziel} sha256 {sha}", flush=True)
    return ziel


def export_lesen(pfad: Path, bis: str | None, volumen_pflicht: bool = True) -> tuple[dict, dict, str, dict]:
    """Export lesen; Zeilen VOR der Aufbereitung auf ≤ `bis` kürzen (Entdeckung)."""
    roh = pfad.read_bytes()
    sha = hashlib.sha256(roh).hexdigest()
    daten = json.loads(gzip.decompress(roh).decode("utf-8"))
    reihen = {}
    for t, x in daten["ticker"].items():
        r = aufbereiten(kuerzen(x["rows"], bis), daten["sitzungen"][x["boerse"]], volumen_pflicht)
        r["boerse"] = x["boerse"]
        r["_roh"] = muster_roh(r)
        r["_muster"] = muster(r)
        r["_abschnitt"] = {a: im_abschnitt(r, a) for a in ABSCHNITTE}
        reihen[t] = r
    meta = {"universum_sha256": hashlib.sha256("\n".join(daten["universum"]).encode()).hexdigest(),
            "ticker": len(reihen), "export_erzeugt": daten["erzeugt"]}
    return reihen, meta, sha, daten["sitzungen"]


def diagnostik(reihen: dict, abschnitt: str) -> dict:
    """Ausschlüsse im Abschnitt: Zeilen je Grund und verworfene Musterkandidaten je Grund (v2 §3, Code-Review R1)."""
    a, b = ABSCHNITTE[abschnitt]
    zeilen, kand = {}, {}
    for r in reihen.values():
        im = np.array([a <= d <= b for d in r["d"]], bool)
        for g in r["grund"][im & ~r["gueltig"]]:
            zeilen[g] = zeilen.get(g, 0) + 1
        zeilen["basisbruch"] = zeilen.get("basisbruch", 0) + int((r["basisbruch"] & im).sum())
        zeilen["luecke"] = zeilen.get("luecke", 0) + int((r["luecke"] & im).sum())
        for mk, roh in r["_roh"].items():
            ziel = kand.setdefault(mk, {"gezaehlt": 0, "verworfen": {}})
            for t in np.nonzero(roh & im)[0]:
                if t + H_MAX >= r["n"] or r["d"][t + H_MAX] > b:
                    continue                           # Fenster reicht über den Abschnitt — kein Kandidat hier
                ziel["gezaehlt"] += 1
                if r["fenster"][t]:
                    continue
                spanne = range(max(t - 1, 0), min(t + H_MAX + 1, r["n"]))
                if any(not r["gueltig"][k] for k in spanne):
                    g = next(r["grund"][k] for k in spanne if not r["gueltig"][k])
                elif any(r["basisbruch"][k] for k in spanne):
                    g = "basisbruch"
                elif any(r["luecke"][k] for k in spanne):
                    g = "luecke"
                else:
                    g = "sonstig"
                ziel["verworfen"][g] = ziel["verworfen"].get(g, 0) + 1
    return {"zeilen": zeilen, "musterkandidaten": kand}


def ausloesung(reihen: dict, abschnitt: str, muster_k: str, sicht: int) -> dict:
    """Auslösequote des Stopps: Ereignisse vs. Kontrolltage (v2 §4, deskriptiv)."""
    ev_n = ev_a = ko_n = ko_a = 0
    for r in reihen.values():
        m = r["_abschnitt"][abschnitt]
        y = rendite(r, "stopp", sicht, HAUPT)
        mu = r["_muster"][muster_k] & m
        ko_n += int(m.sum())
        ko_a += int((m & np.isfinite(y)).sum())
        ev_n += int(mu.sum())
        ev_a += int((mu & np.isfinite(y)).sum())
    return {"ereignis": ev_a / ev_n if ev_n else None, "kontrolle": ko_a / ko_n if ko_n else None,
            "n_ereignis": ev_n, "n_kontrolle": ko_n}


def hypothesen_daten(reihen: dict, abschnitt: str, hz: int, zellen: Zellen, achse: dict,
                     ersatz: dict | None = None, nur: tuple | None = None) -> dict:
    alle = {}
    for name, mk, art, sicht in HYPOTHESEN:
        if nur and name not in nur:
            continue
        a = (ersatz or {}).get(name, art)
        alle[name] = sammeln(reihen, abschnitt, mk, a, sicht if sicht else 1, hz, art == "abs", zellen, achse)
    return alle


def skript_sha() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _boersen(reihen: dict) -> set:
    return {r["boerse"] for r in reihen.values()}


# ── Phasen ────────────────────────────────────────────────────────────────────────────────────────────────────────
def entdeckung(export: Path, seed: int = 20261017) -> dict:
    reihen, meta, sha, sitz = export_lesen(export, bis=ENTDECKUNG_BIS)
    erg = {"phase": "entdeckung", "export_sha256": sha, "skript_sha256": skript_sha(), **meta, "hypothesen": {}}
    achse = achse_fuer(sitz, _boersen(reihen), "entdeckung")
    zellen = Zellen()
    haupt = hypothesen_daten(reihen, "entdeckung", HAUPT, zellen, achse)
    pts = {k: punkt(v, zellen) for k, v in haupt.items()}
    netto = {NETTO[k]: haupt[k] for k in NETTO}
    Z, D = len(zellen.ticker), len(achse)

    def rechnen(B, s):
        bs = bootstrap(haupt, Z, D, B, BLOCK, s, netto=netto)
        ps = {k: (p_zweiseitig(pts[k]["T"], bs[k]["T_stern"]) if pts[k]["T"] is not None else None) for k in pts}
        return bs, ps, holm(ps)

    bs, ps, hl = rechnen(B_STANDARD, seed)
    B_verwendet = B_STANDARD
    if nahe_schwelle(ps, hl):
        bs, ps, hl = rechnen(B_FEIN, seed + 1)
        B_verwendet = B_FEIN
    sens = {L: bootstrap(haupt, Z, D, B_SENS, L, seed + L) for L in BLOCK_SENS}
    halb = {}
    for hk in ("haelfte1", "haelfte2"):                 # nacheinander, nur Punktschätzer (Speicher)
        zh = Zellen()
        ah = achse_fuer(sitz, _boersen(reihen), hk)
        halb[hk] = {k: punkt(v, zh) for k, v in hypothesen_daten(reihen, hk, HAUPT, zh, ah).items()}
    for name, mk, art, sicht in HYPOTHESEN:
        pt, a, b = pts[name], halb["haelfte1"][name], halb["haelfte2"][name]
        abdeckung = (pt["n"] >= MIN_EREIGNISSE and pt["ticker"] >= MIN_TICKER
                     and a["n"] >= MIN_HAELFTE and b["n"] >= MIN_HAELFTE)
        gleich = (pt["T"] is not None and a["T"] is not None and b["T"] is not None
                  and np.sign(a["T"]) == np.sign(b["T"]) == np.sign(pt["T"]))
        ausfall_ok = bs[name]["ausfall"] <= AUSFALL_MAX
        eintrag = {
            "muster": mk, "zielgroesse": art, "sicht": sicht, "punkt": pt,
            "p_zweiseitig": ps[name], "holm_verworfen": hl[name][0], "holm_schwelle": hl[name][1],
            "intervall_95": intervall(bs[name]["T_stern"]) if pt["T"] is not None else None,
            "bootstrap_B": B_verwendet, "ausfall_mittel": bs[name]["ausfall"],
            "p_block10": p_zweiseitig(pt["T"], sens[10][name]["T_stern"]) if pt["T"] is not None else None,
            "p_block40": p_zweiseitig(pt["T"], sens[40][name]["T_stern"]) if pt["T"] is not None else None,
            "haelfte1": {k: a.get(k) for k in ("T", "n", "ticker")},
            "haelfte2": {k: b.get(k) for k in ("T", "n", "ticker")},
            "gleiches_vorzeichen": bool(gleich), "relevant": relevant(name, pt),
            "abdeckung_ok": bool(abdeckung), "ausfall_ok": bool(ausfall_ok),
            "weiter_in_pruefzeitraum": bool(hl[name][0] and gleich and relevant(name, pt) and abdeckung and ausfall_ok),
        }
        if name in NETTO:                               # v3/v4: absolute Nettorendite in der Entdeckung berichten
            nk = NETTO[name]
            eintrag["netto_beschreibend"] = {"N": netto_punkt(haupt[name]),
                                             "intervall_95": intervall(bs[nk]["T_stern"]) if pt["n"] else None}
        if art == "stopp":
            eintrag["ausloesung"] = ausloesung(reihen, "entdeckung", mk, sicht)
        erg["hypothesen"][name] = eintrag
    del haupt, bs, sens
    # explorativ (v2 §6) — jeweils neu gesammelt und sofort verdichtet
    expl = {}
    for hz in (1, 10):
        zx = Zellen()
        expl[f"h{hz}"] = {k: _kurz(punkt(v, zx)) for k, v in hypothesen_daten(reihen, "entdeckung", hz, zx, achse).items()}
    zx = Zellen()
    expl["setup_h5"] = {k: _kurz(punkt(v, zx)) for k, v in hypothesen_daten(
        reihen, "entdeckung", HAUPT, zx, achse, {"H2": "setup", "H4": "setup"}, nur=("H2", "H4")).items()}
    zx = Zellen()
    expl["spanne_h5"] = {k: _kurz(punkt(v, zx)) for k, v in hypothesen_daten(
        reihen, "entdeckung", HAUPT, zx, achse, {"H9": "spanne", "H10": "spanne"}, nur=("H9", "H10")).items()}
    erg["diagnostik"] = diagnostik(reihen, "entdeckung")
    del reihen
    ohne_vol, _, _, _ = export_lesen(export, bis=ENTDECKUNG_BIS, volumen_pflicht=False)
    zx = Zellen()
    expl["ohne_volumenregel_h5"] = {k: _kurz(punkt(v, zx)) for k, v in hypothesen_daten(
        ohne_vol, "entdeckung", HAUPT, zx, achse).items()}
    erg["explorativ"] = expl
    return erg


def _kurz(pt: dict) -> dict:
    return {k: v for k, v in pt.items() if k != "ticker_einzeln"}


def einfrieren(entdeckung_json: Path, commit: str) -> dict:
    e = json.loads(entdeckung_json.read_text(encoding="utf-8"))
    return {"erstellt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "commit": commit,
            "export_sha256": e["export_sha256"], "skript_sha256": e["skript_sha256"],
            "universum_sha256": e["universum_sha256"],
            "richtung": {k: (int(np.sign(v["punkt"]["T"])) if v["punkt"]["T"] is not None else 0)
                         for k, v in e["hypothesen"].items()},
            "weitergereicht": [k for k, v in e["hypothesen"].items() if v["weiter_in_pruefzeitraum"]]}


def pruefzeitraum(export: Path, frost: dict, seed: int = 20261018) -> dict:
    if skript_sha() != frost["skript_sha256"]:
        raise SystemExit("Skript seit dem Einfrieren verändert — Prüfzeitraum verweigert.")
    reihen, meta, sha, sitz = export_lesen(export, bis=None)
    if sha != frost["export_sha256"]:
        raise SystemExit("Export ist nicht der eingefrorene — Prüfzeitraum verweigert.")
    achse = achse_fuer(sitz, _boersen(reihen), "pruef")
    zellen = Zellen()
    daten = hypothesen_daten(reihen, "pruef", HAUPT, zellen, achse)
    netto = {NETTO[k]: daten[k] for k in NETTO}
    pts = {k: punkt(v, zellen) for k, v in daten.items()}
    weiter = frost["weitergereicht"]
    Z, D = len(zellen.ticker), len(achse)

    def rechnen(B, s):
        bs = bootstrap(daten, Z, D, B, BLOCK, s, netto=netto)
        ps = {k: (p_einseitig(pts[k]["T"], bs[k]["T_stern"], frost["richtung"][k])
                  if pts[k]["T"] is not None and frost["richtung"][k] else None) for k in weiter}
        hl = holm(ps) if ps else {}
        nps = {nk: (p_einseitig(netto_punkt(v), bs[nk]["T_stern"], 1) if netto_punkt(v) is not None else None)
               for nk, v in netto.items()}
        return bs, ps, hl, nps

    bs, ps, hl, nps = rechnen(B_STANDARD, seed)
    # (a)/(b) vorläufig, um die N-Familie richtig zu besetzen; Feinziehung, wenn H oder N nahe an der Schwelle
    def entscheiden(bs, ps, hl, nps):
        hyp = {}
        for name, mk, art, sicht in HYPOTHESEN:
            pt, d = pts[name], frost["richtung"][name]
            abdeckung = pt["n"] >= MIN_PRUEF
            ausfall_ok = bs[name]["ausfall"] <= AUSFALL_MAX
            a = bool(name in hl and hl[name][0] and abdeckung and ausfall_ok and pt["T"] is not None
                     and np.sign(pt["T"]) == d)
            hyp[name] = {"punkt": pt, "richtung_d": d, "weitergereicht": name in weiter, "p_einseitig": ps.get(name),
                         "holm": hl.get(name), "intervall_95": intervall(bs[name]["T_stern"]) if pt["T"] is not None else None,
                         "abdeckung_ok": abdeckung, "ausfall_mittel": bs[name]["ausfall"], "ausfall_ok": ausfall_ok,
                         "a_repliziert": a, "b_richtung": bool(a and name not in ("H9", "H10") and d == 1)}
        bmap = {NETTO[h]: hyp[h]["b_richtung"] for h in NETTO}
        return hyp, netto_familie(nps, bmap), bmap

    hyp, nhl, bmap = entscheiden(bs, ps, hl, nps)
    B_verwendet = B_STANDARD
    if fein_noetig(ps, hl, nps, bmap):
        bs, ps, hl, nps = rechnen(B_FEIN, seed + 1)
        hyp, nhl, bmap = entscheiden(bs, ps, hl, nps)
        B_verwendet = B_FEIN
    erg = {"phase": "pruefzeitraum", "export_sha256": sha, "frost": frost, "bootstrap_B": B_verwendet,
           "hypothesen": hyp, "netto": {}}
    for hk, nk in NETTO.items():
        v = netto[nk]
        erg["netto"][nk] = {"N": netto_punkt(v), "n": int(v["ev"].sum()),
                            "intervall_95": intervall(bs[nk]["T_stern"]) if v["ev"].any() else None,
                            "p_einseitig": nps[nk], "holm": nhl[nk],
                            "c_wirtschaftlich": bool(hyp[hk]["b_richtung"] and nhl[nk][0])}
    erg["diagnostik"] = diagnostik(reihen, "pruef")
    return erg


def _json(x):
    if isinstance(x, np.floating):
        return float(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, tuple):
        return list(x)
    raise TypeError(type(x))


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--laden", action="store_true")
    g.add_argument("--entdeckung", action="store_true")
    g.add_argument("--einfrieren", metavar="COMMIT")
    g.add_argument("--pruefzeitraum", action="store_true")
    ap.add_argument("--export", default=str(AUSGABE / "export.json.gz"))
    a = ap.parse_args()
    export = Path(a.export)
    AUSGABE.mkdir(parents=True, exist_ok=True)
    if a.laden:
        laden(export)
        return 0
    if a.einfrieren:
        erg = einfrieren(AUSGABE / "entdeckung.json", a.einfrieren)
        # exklusiv anlegen: zwei parallele Aufrufe können sich nicht überschreiben (Code-Review R1)
        with open(AUSGABE / "einfrieren.json", "x", encoding="utf-8") as f:
            json.dump(erg, f, default=_json, ensure_ascii=False, indent=1)
        print(f"[einfrieren] → {AUSGABE / 'einfrieren.json'}", flush=True)
        return 0
    if a.entdeckung:
        erg, ziel = entdeckung(export), AUSGABE / "entdeckung.json"
    else:
        frost = json.loads((AUSGABE / "einfrieren.json").read_text(encoding="utf-8"))
        erg, ziel = pruefzeitraum(export, frost), AUSGABE / "pruefzeitraum.json"
    ziel.write_text(json.dumps(erg, default=_json, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{ziel.stem}] → {ziel}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
