#!/usr/bin/env python3
"""
plain_vanilla_bericht.py — Differenzbericht zweier Messläufe als Markdown-Tabelle je Ticker × Zeitraum|Stop.

    py -3.14 scripts/research/plain_vanilla_bericht.py <alt.json> <neu.json> [--kombis 10|aus,max|aus] [--ticker ^DJI,SPY]

Zeigt je Strategie Trades (davon offen), Trefferquote, Ø Rendite, Profit-Faktor, Sharpe, Max-DD (abgeschlossene Trades)
alt → neu; unveränderte Strategien werden als „=" zusammengefasst.
"""
from __future__ import annotations

import argparse
import json
import sys

FELDER = [("win_rate", "Treffer %"), ("avg_return", "Ø %"), ("profit_factor", "PF"), ("sharpe", "Sharpe"),
          ("max_drawdown", "DD %")]


def fmt(v):
    if v is None:
        return "—"
    return f"{v:g}" if isinstance(v, (int, float)) else str(v)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("alt")
    ap.add_argument("neu")
    ap.add_argument("--kombis", default="10|aus")
    ap.add_argument("--ticker", default="^DJI,SPY")
    a = ap.parse_args()
    alt, neu = (json.load(open(p, encoding="utf-8")) for p in (a.alt, a.neu))
    if alt["kurs_hash"] != neu["kurs_hash"]:
        sys.exit("verschiedene Kurs-Snapshots")
    print(f"Kurs-Snapshot {neu['kurs_hash']}, Stichtag {neu['stichtag']}; Module alt {alt['modul_hash']} → neu {neu['modul_hash']}\n")
    for tk in a.ticker.split(","):
        for k in a.kombis.split(","):
            ja, jn = alt["ticker"][tk]["je"][k], neu["ticker"][tk]["je"][k]
            print(f"### {tk} — {k.replace('|', ', Stop ')}\n")
            print("| Strategie | Trades (offen) | " + " | ".join(n for _, n in FELDER) + " |")
            print("|---|---|" + "---|" * len(FELDER))
            gleich = []
            for st in jn:
                o, n = ja.get(st) or {}, jn[st]
                so, sn = o.get("stats") or {}, n.get("stats") or {}
                if o.get("n") == n["n"] and o.get("offen") == n["offen"] and all(so.get(f) == sn.get(f) for f, _ in FELDER):
                    gleich.append(st)
                    continue
                zellen = [f"{o.get('n')} ({o.get('offen')}) → {n['n']} ({n['offen']})"]
                for f, _ in FELDER:
                    zellen.append(fmt(so.get(f)) if so.get(f) == sn.get(f) else f"{fmt(so.get(f))} → **{fmt(sn.get(f))}**")
                print(f"| {st} | " + " | ".join(zellen) + " |")
            print(f"\nUnverändert: {', '.join(gleich) or '—'}\n")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
