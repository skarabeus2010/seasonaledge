#!/usr/bin/env python3
"""
Wächter: shared/indicators.py rechnet dasselbe wie landing/js/indicators.js (Audit 2026-11-15 mit Codex).

Vorher drei Abweichungen: RSI Python = gleitendes einfaches Mittel, JS = Wilder; EMA Python startete beim ersten Kurs
(pandas ewm), JS mit dem SMA; Bollinger Python Stichproben-, JS Populations-Standardabweichung. Dazu JS-RSI einer
nur steigenden Reihe 99,0099 statt 100. Betroffen: Morgen-Mail (RSI/LBR-Score), Backtests, Filter der Seiten.

Geprüft:
  [Hand]     analytische Sollwerte (EMA [1,2,3,4] p2 = 3,5; Bollinger [1,2] p2 k2 oben = 2,5; RSI steigend = 100,
             flach = unbestimmt; RSI(2) [1,2,1,3,2] = 50 nach Wilder) — Python UND JS
  [Zwilling] Python = JS (echte indicators.js in node) für EMA, RSI(2/3/14), Bollinger, MACD, LBR auf fünf Reihen
             inkl. Zufallsweg 400 Tage, Toleranz 1e-9; unbestimmt (NaN/null) an denselben Stellen

Aufruf:  py -3.14 scripts/verify_indikator_zwillinge.py      Exit 0 = alles erfüllt
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WURZEL)

FEHLER: list[str] = []
ZAEHLER = {"n": 0}


def pruefe(kennung: str, bedingung: bool, text: str = "") -> None:
    ZAEHLER["n"] += 1
    if not bedingung:
        FEHLER.append(f"[{kennung}] {text}")


NODE = r"""
global.window = global; global.SA = { __release: function () {} };
require(process.argv[process.argv.length - 2]);
const I = SA.indicators, reihen = JSON.parse(process.argv[process.argv.length - 1]), aus = {};
for (const [name, c] of Object.entries(reihen)) {
  const bb = I.calcBollinger(c, 2, 2), bb20 = I.calcBollinger(c, 20, 2), m = I.calcMACD(c, 12, 26, 9), l = I.calcLBR(c, 3, 10, 16);
  aus[name] = { ema2: I.calcEMA(c, 2), ema10: I.calcEMA(c, 10), rsi2: I.calcRSI(c, 2), rsi3: I.calcRSI(c, 3),
    rsi14: I.calcRSI(c, 14), bb_o: bb.upper, bb_u: bb.lower, bb20_o: bb20.upper, macd: m.macd, macd_s: m.signal,
    lbr_f: l.fastline, lbr_s: l.slowline, macd_h: m.histogram, lbr_h: l.histogram, sma3: I.calcSMA(c, 3) };
}
console.log(JSON.stringify(aus));
"""


def _js(reihen: dict) -> dict:
    pfad = os.path.join(WURZEL, "landing", "js", "indicators.js")
    r = subprocess.run(["node", "-e", NODE, pfad, json.dumps(reihen)], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"node: {r.stderr[-400:]}")
    return json.loads(r.stdout)


def _py(reihen: dict) -> dict:
    import pandas as pd
    from shared import indicators as I
    aus = {}
    for name, c in reihen.items():
        s = pd.Series(c, dtype=float)
        bb, bb20 = I.calc_bollinger(s, 2, 2.0), I.calc_bollinger(s, 20, 2.0)
        m, l = I.calc_macd(s, 12, 26, 9), I.calc_lbr(s, 3, 10, 16)
        aus[name] = {"ema2": I.calc_ema(s, 2), "ema10": I.calc_ema(s, 10), "rsi2": I.calc_rsi(s, 2),
                     "rsi3": I.calc_rsi(s, 3), "rsi14": I.calc_rsi(s, 14), "bb_o": bb["upper"], "bb_u": bb["lower"],
                     "bb20_o": bb20["upper"], "macd": m["macd"], "macd_s": m["signal"],
                     "lbr_f": l["fastline"], "lbr_s": l["slowline"], "macd_h": m["histogram"],
                     "lbr_h": l["histogram"], "sma3": I.calc_sma(s, 3)}
        aus[name] = {k: [None if (v is None or (isinstance(v, float) and math.isnan(v))) else float(v)
                         for v in ser.tolist()] for k, ser in aus[name].items()}
    return aus


def _reihen() -> dict:
    import random
    rnd = random.Random(20261115)
    weg, x = [], 100.0
    for _ in range(400):
        x *= math.exp(rnd.gauss(0.0003, 0.012))
        weg.append(round(x, 4))
    return {
        "steigend": [1.0, 2.0, 3.0, 4.0],
        "zickzack": [1.0, 2.0, 1.0, 3.0, 2.0],
        "flach": [5.0] * 20,
        "weg": weg,
        "steigend_lang": [100.0 + i for i in range(60)],
        # Lückenvertrag (Codex 2026-11-15): Codex' Gegenbeispiel, dazu Lücken vorn, innen (mehrere) und hinten
        "codex_luecke": [1.0, 2.0, None, 1.0, 3.0, 2.0],
        "weg_luecken": [None, None] + [None if i in (37, 38, 120, 250) else v for i, v in enumerate(weg)] + [None],
    }


def block_hand(py: dict, js: dict) -> None:
    for seite, w in (("Python", py), ("JS", js)):
        e = w["steigend"]["ema2"][-1]
        pruefe(f"Hand {seite} EMA [1,2,3,4] p2 = 3,5", e is not None and abs(e - 3.5) < 1e-12, str(e))
        pruefe(f"Hand {seite} EMA vor dem Startwert unbestimmt", w["steigend"]["ema2"][0] is None,
               str(w["steigend"]["ema2"][:2]))
        o = w["steigend"]["bb_o"][1]
        pruefe(f"Hand {seite} Bollinger [1,2] oben = 2,5 (Population)", o is not None and abs(o - 2.5) < 1e-12, str(o))
        r = w["steigend"]["rsi2"][-1]
        pruefe(f"Hand {seite} RSI steigend = 100", r is not None and abs(r - 100) < 1e-12, str(r))
        r = w["steigend_lang"]["rsi14"][-1]
        pruefe(f"Hand {seite} RSI(14) steigend lang = 100", r is not None and abs(r - 100) < 1e-12, str(r))
        pruefe(f"Hand {seite} RSI flach unbestimmt", all(v is None for v in w["flach"]["rsi14"]),
               str(w["flach"]["rsi14"][14:17]))
        # Wilder RSI(2) [1,2,1,3,2]: d = +1,−1,+2,−1; Start ag=0,5 av=0,5; i=2: ag=1,25 av=0,25; i=3: ag=0,625 av=0,625
        r = w["zickzack"]["rsi2"][-1]
        pruefe(f"Hand {seite} RSI(2) Zickzack = 50 (Wilder)", r is not None and abs(r - 50) < 1e-12, str(r))
        # Lücke: gerechnet auf den gültigen Kursen [1,2,1,3,2] → wieder 50; die Lückenstelle selbst unbestimmt
        r = w["codex_luecke"]["rsi2"]
        pruefe(f"Hand {seite} RSI(2) mit Lücke = 50, Lücke unbestimmt",
               r[-1] is not None and abs(r[-1] - 50) < 1e-12 and r[2] is None, str(r))
        sm = w["codex_luecke"]["sma3"]
        pruefe(f"Hand {seite} SMA-Fenster mit Lücke unbestimmt", sm[2] is None and sm[3] is None and sm[4] is None
               and sm[5] is not None and abs(sm[5] - 2.0) < 1e-12, str(sm))
        # Histogramm = Linie − Signal (Plain Vanilla handelt auf dem LBR-Histogramm, Codex 2026-11-15)
        for nm in ("weg", "weg_luecken"):
            for lin, sig, hist in (("macd", "macd_s", "macd_h"), ("lbr_f", "lbr_s", "lbr_h")):
                bad = [i for i, (a, b, h) in enumerate(zip(w[nm][lin], w[nm][sig], w[nm][hist]))
                       if (a is None or b is None) != (h is None)
                       or (h is not None and abs(h - (a - b)) > 1e-12 * max(1.0, abs(a)))]
                pruefe(f"Hand {seite} Histogramm {hist} = Linie − Signal ({nm})", not bad, f"erste Abweichung i={bad[:1]}")
        # Lückenstellen bleiben in allen Linien unbestimmt
        for k in ("ema10", "rsi14", "macd", "lbr_f", "lbr_h"):
            pruefe(f"Hand {seite} {k} an Lückenstelle unbestimmt",
                   all(w["weg_luecken"][k][i] is None for i in (0, 1, 39, 40, 122, 252, 402)), k)


def block_zwilling(py: dict, js: dict) -> None:
    for name in py:
        for k in py[name]:
            a, b = py[name][k], js[name][k]
            if len(a) != len(b):
                pruefe(f"Zwilling {name} {k} Länge", False, f"{len(a)} gegen {len(b)}")
                continue
            abw = [i for i, (x, y) in enumerate(zip(a, b))
                   if (x is None) != (y is None) or (x is not None and abs(x - y) > 1e-9 * max(1.0, abs(x)))]
            pruefe(f"Zwilling {name} {k}", not abw,
                   f"{len(abw)} Abweichungen, erste i={abw[0]}: Python {a[abw[0]]} JS {b[abw[0]]}" if abw else "")


def main() -> int:
    try:
        reihen = _reihen()
        py, js = _py(reihen), _js(reihen)
        block_hand(py, js)
        block_zwilling(py, js)
    except Exception as e:  # eine Ausnahme ist nie ein Nachweis
        FEHLER.append(f"[Ausnahme] {type(e).__name__}: {e}")
    print(f"verify_indikator_zwillinge: {ZAEHLER['n'] - len(FEHLER)}/{ZAEHLER['n']} Prüfungen bestanden")
    for f in FEHLER[:40]:
        print("  FEHL", f)
    print(f"PROBE-ENDE {ZAEHLER['n']} Pruefungen")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
