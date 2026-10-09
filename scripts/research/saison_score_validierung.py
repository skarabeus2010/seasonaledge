#!/usr/bin/env python3
"""
saison_score_validierung.py — historische Walk-forward-Auswertung des Saison-Scores NACH der Methodenrevision
(Plan v2/v3, Abschnitt D5, Codex-Freigabe 2026-10-09).

Ausdrücklich KEIN Bestätigungstest: die Jahre 2010–2025 sind durch die Methodik-Berichte vom 08.10.2026 bereits
angesehen. Die prospektive Bestätigung läuft über das unveränderliche Protokoll `saison_score_protokoll` (frühestens
2027-10). Aussage danach nur: „Rangzusammenhang in der historischen Auswertung ja/nein" + Zahlen. Die Bullish/Bearish-
Etiketten kehren aufgrund dieses Laufs NICHT zurück.

Zwei Schritte:
    py -3.14 scripts/research/saison_score_validierung.py --protokoll --snapshot <pv_kurse>
        schreibt scripts/research/saison_score_validierung_protokoll.json (Codeversion = Git-Commit + SHA-256 der
        Rechenkern-Dateien, SHA-256 jeder Datenreihe, Manifest, Raster, Seed, Regeln). Verlangt saubere Kern-Dateien.
    py -3.14 scripts/research/saison_score_validierung.py --lauf
        rechnet NUR, wenn Kern und Daten exakt dem Protokoll entsprechen; schreibt ..._ergebnis.json.

Festgelegt (vor dem Lauf, hier im Code und im Protokoll):
  * Manifest: ^GSPC, ^DJI, ^GDAXI, SPY, QQQ (Snapshot) + alle Reihen in scripts/research/.cache außer SPY/QQQ.
  * Abschnitt A: jeder 5. Handelstag 2010-01-01 … 2025-12-31; Abschnitt B (getrennt): ^GSPC, ^DJI 1960 … 2009.
  * Ziel: Rendite vom Schluss am as_of bis zur letzten Kurszeile ≤ as_of + 30 KT — gleicher Vertrag wie die
    Fenster (Endpunkt ≤ T Tage vor dem Ziel, keine Lücke > T); nur ausgereifte Ziele (letzte Kurszeile ≥ as_of + 30).
  * Auswertbar: ≥ 100 Bewertungstage mit Score und Ziel in A, auf ≥ 8 Kalenderjahre verteilt, Score und Ziel nicht
    konstant. Universum einmal auf den Originaldaten bestimmt, dann fest.
  * Primär (einziger Test): Mittel der Spearman-Korrelationen je Reihe (gleich gewichtet) zwischen `score_roh` und
    Ziel, Abschnitt A. 95-%-Intervall: Block-Bootstrap über Kalenderjahre (dieselben gezogenen Jahre für alle Reihen,
    mit Zurücklegen), 2000 Ziehungen, Seed 20261009, Perzentilintervall. Ziehung mit einer undefinierten Reihe
    (< 10 Beobachtungen oder konstant) wird VERWORFEN und gezählt; > 5 % verworfen → „nicht auswertbar".
  * Sekundär, gepaart (dieselben Tage, dieselben Ziehungen): Score vs. 5 · (B1 + B2) — Differenz der Mittel.
  * Explorativ: B1–B4 einzeln, Quintile je Reihe (Mittelrang bei Gleichstand), Abschnitt B.
  * Gültigkeit je Kennzahl GETRENNT (Codex vor dem Lauf): dieselben 2000 Jahresziehungen, aber eine Ziehung wird für
    den Primärtest nur nach Score/Ziel verworfen, für den gepaarten Vergleich nach beiden Scores/Ziel, explorativ je
    Baustein — eine konstante Explorativ-Kennzahl verändert den Primärtest nicht. Verwerfungen getrennt berichtet;
    über 5 % → diese Kennzahl „nicht auswertbar" (null, nicht „nein").
  * Positivrate (Basis „immer positiv"): je Reihe k/n der Ziele > 0 auf denselben Bewertungstagen, dazu das Mittel
    der Raten über die Reihen (gleich gewichtet) und explorativ die Rate im obersten Score-Quintil je Reihe.
  * Das Protokoll hält den SHA-256 dieses Skripts fest; `--lauf` verweigert bei abweichendem Skript, Kern, Daten
    oder Parameter.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np
import pandas as pd

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from shared import saison_score as SS  # noqa: E402

PROTOKOLL = REPO / "scripts/research/saison_score_validierung_protokoll.json"
ERGEBNIS = REPO / "scripts/research/saison_score_validierung_ergebnis.json"
KERN = ["shared/saison_score.py", "landing/js/saison-score.js", "shared/calculations.py"]
SKRIPT = "scripts/research/saison_score_validierung.py"
SNAP = {"^GSPC": "_GSPC.json", "^DJI": "_DJI.json", "^GDAXI": "_GDAXI.json", "SPY": "SPY.json", "QQQ": "QQQ.json"}
CACHE = REPO / "scripts/research/.cache"
SEED = 20261009
ZIEHUNGEN = 2000
A = ("2010-01-01", "2025-12-31")
B = ("1960-01-01", "2009-12-31")
B_REIHEN = ["^GSPC", "^DJI"]
RASTER = 5
MIN_BEOB, MIN_JAHRE, MIN_BEOB_ZIEHUNG = 100, 8, 10
MAX_VERWORFEN = 0.05


PARAMETER = {"seed": SEED, "ziehungen": ZIEHUNGEN, "abschnitt_a": list(A), "abschnitt_b": list(B), "b_reihen": B_REIHEN,
             "raster": RASTER, "min_beob": MIN_BEOB, "min_jahre": MIN_JAHRE, "min_beob_ziehung": MIN_BEOB_ZIEHUNG,
             "max_verworfen": MAX_VERWORFEN, "horizont_kt": 30}


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def manifest(snap: pathlib.Path) -> dict:
    m = {t: snap / f for t, f in SNAP.items()}
    for p in sorted(CACHE.glob("*.json")):
        if p.stem not in ("SPY", "QQQ"):
            m[p.stem] = p
    return m


def lade(p: pathlib.Path):
    rows = json.loads(p.read_text())
    return [r["date"] for r in rows], [r["close"] for r in rows]


def ziel(daten, closes, ticker, as_of):
    """Rendite as_of → letzte Kurszeile ≤ as_of + 30 KT, gleicher Vertrag wie die Fenster des Scores."""
    T = SS.TOLERANZ[SS.marktklasse(ticker)]
    ds, cs = SS.bereinigen(daten, closes)
    i = ds.index(as_of)
    z = (dt.date.fromisoformat(as_of) + dt.timedelta(days=30)).isoformat()
    if ds[-1] < z:
        return None                                   # nicht ausgereift
    e = max(k for k in range(i, len(ds)) if ds[k] <= z)
    if e <= i or (dt.date.fromisoformat(z) - dt.date.fromisoformat(ds[e])).days > T:
        return None
    for k in range(i + 1, e + 1):
        if (dt.date.fromisoformat(ds[k]) - dt.date.fromisoformat(ds[k - 1])).days > T:
            return None
    return (cs[e] / cs[i] - 1) * 100


def beobachtungen(daten, closes, ticker, von, bis):
    ds, _ = SS.bereinigen(daten, closes)
    tage = [d for d in ds if von <= d <= bis][::RASTER]
    out = []
    for a in tage:
        e = SS.berechne(daten, closes, ticker, a)
        if e["status"] != "ok":
            continue
        zz = ziel(daten, closes, ticker, a)
        if zz is None:
            continue
        out.append({"as_of": a, "jahr": int(a[:4]), "score": e["score_roh"], "ohne": e["vergleich_ohne_matching"],
                    "b1": e["b1"]["wert"], "b2": e["b2"]["wert"], "b3": e["b3"]["wert"], "b4": e["b4"]["wert"],
                    "ziel": zz})
    return out


def spearman(x, y):
    x, y = pd.Series(x), pd.Series(y)
    if x.nunique() < 2 or y.nunique() < 2:
        return None
    return float(x.rank().corr(y.rank()))


def mittel_spearman(reihen, spalte):
    """Mittel der Spearman je Reihe; None, wenn EINE Reihe undefiniert ist (zu wenige Beobachtungen oder konstant)."""
    werte = []
    for obs in reihen.values():
        if len(obs) < MIN_BEOB_ZIEHUNG:
            return None
        s = spearman([o[spalte] for o in obs], [o["ziel"] for o in obs])
        if s is None:
            return None
        werte.append(s)
    return float(np.mean(werte))


def bootstrap(beob: dict, spalten, jahre):
    """Dieselben Jahresziehungen für alle Kennzahlen; Gültigkeit und Verwerfung aber JE KENNZAHL getrennt.
    Gepaart: nur Ziehungen, in denen Score UND Vergleichsscore definiert sind."""
    rnd = np.random.default_rng(SEED)
    werte = {s: [] for s in spalten}
    verworfen = {s: 0 for s in spalten}
    diffs, verworfen_paar = [], 0
    for _ in range(ZIEHUNGEN):
        gezogen = rnd.choice(jahre, size=len(jahre), replace=True)
        zaehl = pd.Series(gezogen).value_counts().to_dict()
        reihen = {t: [o for o in obs for _ in range(zaehl.get(o["jahr"], 0))] for t, obs in beob.items()}
        z = {s: mittel_spearman(reihen, s) for s in spalten}
        for s in spalten:
            if z[s] is None:
                verworfen[s] += 1
            else:
                werte[s].append(z[s])
        if z["score"] is None or z["ohne"] is None:
            verworfen_paar += 1
        else:
            diffs.append(z["score"] - z["ohne"])

    def ci(v):
        return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else None
    return ({s: ci(werte[s]) for s in spalten}, verworfen, ci(diffs), verworfen_paar)


def positivrate(obs):
    k = sum(1 for o in obs if o["ziel"] > 0)
    return {"k": k, "n": len(obs), "rate": k / len(obs) if obs else None}


def positivrate_top_quintil(obs):
    df = pd.DataFrame(obs)
    q = pd.qcut(df["score"].rank(method="average"), 5, labels=False, duplicates="drop")
    oben = df["ziel"][q == q.max()]
    return {"k": int((oben > 0).sum()), "n": int(len(oben)), "rate": float((oben > 0).mean()) if len(oben) else None}


def quintile(obs):
    df = pd.DataFrame(obs)
    q = pd.qcut(df["score"].rank(method="average"), 5, labels=False, duplicates="drop")
    return [float(df["ziel"][q == k].mean()) for k in sorted(q.unique())]


def protokoll(snap: pathlib.Path):
    st = subprocess.run(["git", "status", "--porcelain", "--"] + KERN + [SKRIPT], capture_output=True, text=True, cwd=REPO).stdout
    if st.strip():
        sys.exit(f"Kern-Dateien oder Validierungsskript nicht committet:\n{st}\nErst committen, dann das Protokoll festschreiben.")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO).stdout.strip()
    m = manifest(snap)
    p = {
        "erstellt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "bezeichnung": "historische Walk-forward-Auswertung nach Methodenrevision (kein Bestätigungstest)",
        "commit": commit, "kern_sha256": {k: sha(REPO / k) for k in KERN}, "skript_sha256": sha(REPO / SKRIPT),
        "parameter": PARAMETER,
        "methode": SS.METHODE, "snapshot": str(snap),
        "manifest": {t: {"datei": str(p.relative_to(REPO) if p.is_relative_to(REPO) else p.name), "sha256": sha(p)}
                     for t, p in m.items()},
        "abschnitt_a": A, "abschnitt_b": {"zeitraum": B, "reihen": B_REIHEN}, "raster_handelstage": RASTER,
        "auswertbar": {"min_beobachtungen": MIN_BEOB, "min_jahre": MIN_JAHRE, "nicht_konstant": True},
        "primaer": "Mittel der Spearman je Reihe (gleich gewichtet), score_roh vs. Ziel, Abschnitt A",
        "bootstrap": {"ziehungen": ZIEHUNGEN, "seed": SEED, "block": "Kalenderjahr, dieselben Jahre für alle Reihen",
                      "min_beob_je_reihe_und_ziehung": MIN_BEOB_ZIEHUNG, "max_verworfen": MAX_VERWORFEN,
                      "intervall": "Perzentil 2,5/97,5"},
        "sekundaer": "gepaart: Score vs. 5·(B1+B2), Differenz der Mittel, dieselben Tage/Ziehungen",
        "gueltigkeit": "je Kennzahl getrennt: primär nach Score/Ziel, gepaart nach beiden Scores/Ziel, explorativ je Baustein",
        "positivrate": "je Reihe k/n Ziel > 0; Mittel der Raten (gleich gewichtet); explorativ oberstes Score-Quintil",
        "explorativ": ["B1–B4 einzeln", "Quintile je Reihe (Mittelrang)", "Abschnitt B"],
        "aussage": "nur Rangzusammenhang ja/nein mit Zahlen; keine Rückkehr der Richtungsetiketten",
    }
    PROTOKOLL.write_text(json.dumps(p, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Protokoll geschrieben: {PROTOKOLL.relative_to(REPO)} (Commit {commit[:10]}, {len(m)} Reihen)")


def lauf():
    p = json.loads(PROTOKOLL.read_text(encoding="utf-8"))
    if sha(REPO / SKRIPT) != p.get("skript_sha256"):
        sys.exit("Validierungsskript weicht vom Protokoll ab — Lauf verweigert.")
    if p.get("parameter") != json.loads(json.dumps(PARAMETER)):
        sys.exit(f"Parameter weichen vom Protokoll ab — Lauf verweigert: {p.get('parameter')} ≠ {PARAMETER}")
    for k, h in p["kern_sha256"].items():
        if sha(REPO / k) != h:
            sys.exit(f"Kern {k} weicht vom Protokoll ab — Lauf verweigert.")
    snap = pathlib.Path(p["snapshot"])
    m = manifest(snap)
    if set(m) != set(p["manifest"]):
        sys.exit("Manifest weicht ab — Lauf verweigert.")
    for t, pp in m.items():
        if sha(pp) != p["manifest"][t]["sha256"]:
            sys.exit(f"Datenreihe {t} weicht vom Protokoll ab — Lauf verweigert.")

    beob, aus = {}, {}
    for t, pp in m.items():
        daten, closes = lade(pp)
        obs = beobachtungen(daten, closes, t, *A)
        jahre = {o["jahr"] for o in obs}
        if len(obs) < MIN_BEOB:
            aus[t] = f"nur {len(obs)} Beobachtungen"
        elif len(jahre) < MIN_JAHRE:
            aus[t] = f"nur {len(jahre)} Kalenderjahre"
        elif spearman([o["score"] for o in obs], [o["ziel"] for o in obs]) is None:
            aus[t] = "konstant"
        else:
            beob[t] = obs
        print(f"  {t:7} {len(obs):5} Beobachtungen{'  → ' + aus[t] if t in aus else ''}", flush=True)
    spalten = ["score", "ohne", "b1", "b2", "b3", "b4"]
    punkt = {sp: mittel_spearman(beob, sp) for sp in spalten}
    jahre_a = list(range(int(A[0][:4]), int(A[1][:4]) + 1))
    ci, verworfen, ci_diff, verworfen_paar = bootstrap(beob, spalten, jahre_a)
    ok = {sp: verworfen[sp] / ZIEHUNGEN <= MAX_VERWORFEN for sp in spalten}
    ok_paar = verworfen_paar / ZIEHUNGEN <= MAX_VERWORFEN
    rang = (None if not ok["score"] or ci["score"] is None else bool(ci["score"][0] > 0))
    je_reihe = {t: {"n": len(o), "spearman": spearman([x["score"] for x in o], [x["ziel"] for x in o]),
                    "positivrate": positivrate(o), "positivrate_oberstes_quintil": positivrate_top_quintil(o),
                    "quintile_ziel": quintile(o)} for t, o in beob.items()}
    raten = [r["positivrate"]["rate"] for r in je_reihe.values()]
    abschnitt_b = {}
    for t in B_REIHEN:
        daten, closes = lade(m[t])
        o = beobachtungen(daten, closes, t, *B)
        abschnitt_b[t] = {"n": len(o), "spearman": spearman([x["score"] for x in o], [x["ziel"] for x in o]) if o else None,
                          "positivrate": positivrate(o) if o else None}
    erg = {
        "protokoll": str(PROTOKOLL.relative_to(REPO)), "commit": p["commit"],
        "universum": sorted(beob), "ausgeschlossen": aus,
        "primaer": {"mittel_spearman": punkt["score"], "ci95": ci["score"], "verworfen": verworfen["score"],
                    "auswertbar": ok["score"], "rangzusammenhang": rang},
        "sekundaer_gepaart": {"ohne_matching": punkt["ohne"], "ci95_ohne": ci["ohne"], "verworfen_ohne": verworfen["ohne"],
                              "differenz": (punkt["score"] - punkt["ohne"]) if None not in (punkt["score"], punkt["ohne"]) else None,
                              "ci95_differenz": ci_diff, "verworfen": verworfen_paar, "auswertbar": ok_paar},
        "positivrate": {"mittel_ueber_reihen": float(np.mean(raten)) if raten else None},
        "explorativ": {"bausteine": {sp: {"mittel_spearman": punkt[sp], "ci95": ci[sp], "verworfen": verworfen[sp],
                                          "auswertbar": ok[sp]} for sp in ("b1", "b2", "b3", "b4")},
                       "je_reihe": je_reihe, "abschnitt_b": abschnitt_b},
    }
    ERGEBNIS.write_text(json.dumps(erg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pr = erg["primaer"]
    urteil = "nicht auswertbar" if pr["rangzusammenhang"] is None else ("ja" if pr["rangzusammenhang"] else "nein")
    print(f"\nPrimär: Mittel Spearman {pr['mittel_spearman']}, 95-%-Intervall {pr['ci95']}, "
          f"verworfen {pr['verworfen']}/{ZIEHUNGEN} → Rangzusammenhang: {urteil}")
    g = erg["sekundaer_gepaart"]
    print(f"Gepaart ({'auswertbar' if g['auswertbar'] else 'nicht auswertbar'}): ohne Matching {g['ohne_matching']}, "
          f"Differenz {g['differenz']}, 95-%-Intervall {g['ci95_differenz']}")
    print(f"Positivrate (Mittel über Reihen): {erg['positivrate']['mittel_ueber_reihen']}")


if __name__ == "__main__":
    if "--protokoll" in sys.argv:
        protokoll(pathlib.Path(sys.argv[sys.argv.index("--snapshot") + 1]).resolve())
    elif "--lauf" in sys.argv:
        lauf()
    else:
        sys.exit(__doc__)
