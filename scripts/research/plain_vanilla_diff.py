#!/usr/bin/env python3
"""
plain_vanilla_diff.py — Differenz zweier Messläufe von scripts/js/probe_plain_vanilla_messlauf.js.

    py -3.14 scripts/research/plain_vanilla_diff.py <vorher.json> <nachher.json> [--befund N] [--details 3]

Vergleicht je Ticker × Zeitraum|Stop × Strategie die Trades (Tupel) und die Kennzahlen. Bricht ab, wenn die beiden
Läufe nicht auf demselben Kurs-Snapshot beruhen. Ausgabe: geänderte Strategien mit Anzahl hinzugekommener/entfallener
Trades und Kennzahlen vorher → nachher; mit --details die ersten N geänderten Trades.
"""
from __future__ import annotations

import argparse
import json
import sys

KENNZ = ("win_rate", "avg_return", "profit_factor", "sharpe", "max_drawdown", "total_return")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("vorher")
    ap.add_argument("nachher")
    ap.add_argument("--befund", default="")
    ap.add_argument("--details", type=int, default=0)
    a = ap.parse_args()
    v, n = (json.load(open(p, encoding="utf-8")) for p in (a.vorher, a.nachher))
    if v["kurs_hash"] != n["kurs_hash"] or v["stichtag"] != n["stichtag"]:
        sys.exit(f"verschiedene Snapshots: {v['kurs_hash']}/{v['stichtag']} gegen {n['kurs_hash']}/{n['stichtag']}")
    if not n.get("gueltig", True):
        print("WARNUNG: Nachher-Lauf ungültig:", n.get("fehler", [])[:3])
    geaendert = 0
    for tk in sorted(n["ticker"]):
        for kombi in sorted(n["ticker"][tk]["je"]):
            alt_je = v["ticker"].get(tk, {}).get("je", {}).get(kombi, {})
            for st, neu in n["ticker"][tk]["je"][kombi].items():
                alt = alt_je.get(st)
                if alt is None:
                    print(f"{tk:7s} {kombi:14s} {st:20s} NEU in diesem Lauf")
                    geaendert += 1
                    continue
                # nur die Felder vergleichen, die beide Läufe haben (das Tupel wächst mit dem Messformat)
                breite = min([len(t) for t in alt["trades"] + neu["trades"]] or [0])
                ta = [tuple(map(str, t[:breite])) for t in alt["trades"]]
                tn = [tuple(map(str, t[:breite])) for t in neu["trades"]]
                if ta == tn and alt["stats"] == neu["stats"]:
                    continue
                geaendert += 1
                sa, sn = alt["stats"] or {}, neu["stats"] or {}
                weg, dazu = set(ta) - set(tn), set(tn) - set(ta)
                kz = ", ".join(f"{k} {sa.get(k)}→{sn.get(k)}" for k in KENNZ if sa.get(k) != sn.get(k))
                print(f"{tk:7s} {kombi:14s} {st:20s} n {alt['n']}→{neu['n']} offen {alt['offen']}→{neu['offen']} "
                      f"(−{len(weg)} +{len(dazu)}) {kz}")
                for t in sorted(weg)[:a.details]:
                    print("        −", t)
                for t in sorted(dazu)[:a.details]:
                    print("        +", t)
    print(f"{a.befund + ': ' if a.befund else ''}{geaendert} geänderte Kombinationen")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
