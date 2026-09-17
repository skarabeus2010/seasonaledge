#!/usr/bin/env python3
"""
monthly10_blogzahlen.py — belastbare Zahlen fuer den Blogpost "Monthly 10".

Bildet die PRODUKTIVE Logik nach (landing/js/strategy-compute.js::calc_monthly_10
und scripts/research/etf_seasonal_scan.py::S_monthly_10), damit die Blog-Zahlen
mit dem uebereinstimmen, was die Backtest-Seite zeigt:

  * aktive Handelstage im Monat: TDOM 1-4, 9-12 und die letzten beiden
  * daraus zusammenhaengende Bloecke; je Block EIN Trade
  * Einstieg zum SCHLUSS des ersten Blocktages, Ausstieg zum Schluss des letzten
    (_makeTrade nutzt rows[entryIdx].close) -> der erste Blocktag selbst traegt
    keine Rendite bei
  * ausserhalb der Bloecke: Kasse, 0 % (keine Verzinsung unterstellt)

Basis: Adjusted Close (Dividenden enthalten). Bei einer Strategie, die nur die
halbe Zeit investiert ist, waere ein reiner Kursindex ein unfairer Vergleich zu
Buy & Hold — der Vergleich muss Dividenden auf BEIDEN Seiten enthalten.

Nutzung: PYTHONUTF8=1 py -3.14 scripts/research/monthly10_blogzahlen.py
"""
from __future__ import annotations
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from shared.yahoo_downloader import download_data, clear_cache   # noqa: E402

TICKER = "SPY"
JAHR_VON, JAHR_BIS = 1994, 2025      # volle Kalenderjahre; SPY startet 1993-01-29


def lade(ticker: str):
    df = download_data(ticker, period="max")
    clear_cache()
    spalte = df["Date"] if "Date" in df.columns else df.index
    daten = [str(x)[:10] for x in spalte.tolist()]
    kurse = [float(v) for v in df["Close"].to_numpy()]
    return [(d, k) for d, k in zip(daten, kurse)
            if k == k and k > 0 and JAHR_VON <= int(d[:4]) <= JAHR_BIS]


def bloecke(rows):
    """(start_idx, end_idx, block_typ) je Monat — identisch zur Produktivlogik."""
    nach_monat = defaultdict(list)
    for i, (d, _) in enumerate(rows):
        nach_monat[(int(d[:4]), int(d[5:7]))].append(i)
    out = []
    for (y, m), idx in sorted(nach_monat.items()):
        if len(idx) < 10:
            continue                       # continue, nicht return (siehe JS-Fix)
        n = len(idx)
        aktiv = {t for t in list(range(1, 5)) + list(range(9, 13)) + [n, n - 1]
                 if 1 <= t <= n}
        srt = sorted(aktiv)
        bs = prev = srt[0]
        for k in range(1, len(srt)):
            if srt[k] != prev + 1:
                out.append((idx[bs - 1], idx[prev - 1], _typ(bs)))
                bs = srt[k]
            prev = srt[k]
        out.append((idx[bs - 1], idx[prev - 1], _typ(bs)))
    return out


def _typ(start_tdom: int) -> str:
    if start_tdom <= 4:
        return "Monatsanfang (TDOM 1-4)"
    if start_tdom <= 12:
        return "Monatsmitte (TDOM 9-12)"
    return "Monatsende (letzte 2)"


def kennzahlen(equity, n_jahre):
    gesamt = equity[-1] / equity[0] - 1
    cagr = (equity[-1] / equity[0]) ** (1 / n_jahre) - 1
    spitze, maxdd = equity[0], 0.0
    for v in equity:
        spitze = max(spitze, v)
        maxdd = min(maxdd, v / spitze - 1)
    return gesamt, cagr, maxdd


def main() -> int:
    rows = lade(TICKER)
    print(f"{TICKER}  {rows[0][0]} .. {rows[-1][0]}   {len(rows)} Handelstage\n")

    bl = bloecke(rows)
    aktiv_tage = set()
    for a, b, _ in bl:
        aktiv_tage.update(range(a + 1, b + 1))    # Einstieg zum Schluss von a

    # Tagesrenditen
    ret = [0.0] + [rows[i][1] / rows[i - 1][1] - 1 for i in range(1, len(rows))]

    eq_s, eq_bh = [1.0], [1.0]
    for i in range(1, len(rows)):
        eq_s.append(eq_s[-1] * (1 + (ret[i] if i in aktiv_tage else 0.0)))
        eq_bh.append(eq_bh[-1] * (1 + ret[i]))

    n_jahre = (JAHR_BIS - JAHR_VON + 1)
    gs, cs, dds = kennzahlen(eq_s, n_jahre)
    gb, cb, ddb = kennzahlen(eq_bh, n_jahre)
    quote = 100.0 * len(aktiv_tage) / (len(rows) - 1)

    import statistics as st
    vs = st.pstdev([ret[i] if i in aktiv_tage else 0.0 for i in range(1, len(rows))]) * (252 ** 0.5)
    vb = st.pstdev(ret[1:]) * (252 ** 0.5)

    print(f"{'':<22}{'Monthly 10':>14}{'Buy & Hold':>14}")
    print("-" * 50)
    print(f"{'Gesamtrendite':<22}{gs*100:>13.0f}%{gb*100:>13.0f}%")
    print(f"{'CAGR':<22}{cs*100:>13.2f}%{cb*100:>13.2f}%")
    print(f"{'Vola p.a.':<22}{vs*100:>13.2f}%{vb*100:>13.2f}%")
    print(f"{'Rendite/Vola':<22}{cs/vs:>14.2f}{cb/vb:>14.2f}")
    print(f"{'Max. Drawdown':<22}{dds*100:>13.1f}%{ddb*100:>13.1f}%")
    print(f"{'Zeit im Markt':<22}{quote:>13.1f}%{100.0:>13.1f}%")
    print(f"{'Endwert aus 10.000':<22}{10000*eq_s[-1]:>13,.0f}{10000*eq_bh[-1]:>13,.0f}")

    # Was tragen die AUSGESCHLOSSENEN Tage bei? Das ist die eigentliche Frage.
    eq_rest = [1.0]
    for i in range(1, len(rows)):
        eq_rest.append(eq_rest[-1] * (1 + (0.0 if i in aktiv_tage else ret[i])))
    gr, cr, ddr = kennzahlen(eq_rest, n_jahre)
    print(f"\nRest-Tage (die ausgelassenen {100-quote:.0f} %): "
          f"Gesamt {gr*100:.0f}%  CAGR {cr*100:.2f}%  MaxDD {ddr*100:.1f}%")

    # Beitrag je Block
    print(f"\n{'Block':<26}{'Trades':>8}{'Treffer':>9}{'Ø Rendite':>11}{'Summe':>10}")
    print("-" * 64)
    for typ in ("Monatsanfang (TDOM 1-4)", "Monatsmitte (TDOM 9-12)", "Monatsende (letzte 2)"):
        rr = [rows[b][1] / rows[a][1] - 1 for a, b, t in bl if t == typ]
        if not rr:
            continue
        kum = 1.0
        for r in rr:
            kum *= (1 + r)
        print(f"{typ:<26}{len(rr):>8}{100*sum(1 for r in rr if r>0)/len(rr):>8.0f}%"
              f"{100*st.mean(rr):>10.3f}%{(kum-1)*100:>9.0f}%")

    # Jahresvergleich fuer den Chart
    print(f"\n{'Jahr':<6}{'Monthly 10':>12}{'Buy & Hold':>12}")
    jahre = sorted({int(d[:4]) for d, _ in rows})
    js_gewinn = 0
    for y in jahre:
        idx = [i for i, (d, _) in enumerate(rows) if int(d[:4]) == y and i > 0]
        s = b = 1.0
        for i in idx:
            s *= (1 + (ret[i] if i in aktiv_tage else 0.0)); b *= (1 + ret[i])
        if (s - 1) > (b - 1):
            js_gewinn += 1
        print(f"{y:<6}{(s-1)*100:>11.1f}%{(b-1)*100:>11.1f}%")
    print(f"\nMonthly 10 schlug Buy & Hold in {js_gewinn} von {len(jahre)} Jahren "
          f"({100*js_gewinn/len(jahre):.0f} %)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
