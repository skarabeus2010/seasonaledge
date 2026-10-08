#!/usr/bin/env python3
"""
plain_vanilla_zwilling.py — Python-Zwilling (`shared.strategies.plain_vanilla.auswerten`) gegen einen JS-Messlauf
(`scripts/js/probe_plain_vanilla_messlauf.js`) auf demselben eingefrorenen Kurs-Snapshot.

    py -3.14 scripts/research/plain_vanilla_zwilling.py <snapshot-ordner> <messlauf.json> [--kombis max|aus,10|fixed8]
                                                        [--strategien a,b] [--json ausgabe.json]

Vergleicht je Ticker × Zeitraum|Stop × Strategie (Schnittmenge beider Registries) die Trades — Ein-/Ausstieg,
Rendite (relativ 1e-9), offen, gestoppt, fehlende Sitzungen, auffällige Abstände, Näherung — und die Tageswerte
(`taeglich.max_dd`, `taeglich.final_equity`, relativ 1e-9). Der Zeitraum wird wie auf der Seite gefiltert (ab 1. Januar
des Jahres Stichtag − Zeitraum). Exit 1, wenn eine Strategie aus `--strategien` (Standard: alle gemeinsamen)
abweicht. Ausgabe: je Strategie gleich/abweichend und das erste abweichende Merkmal.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def lade_df(datei: pathlib.Path, stichtag: str):
    import pandas as pd
    rows = [r for r in json.loads(datei.read_text(encoding="utf-8")) if r["date"] <= stichtag]
    df = pd.DataFrame({"Close": [float(r["close"]) if r["close"] is not None else float("nan") for r in rows]},
                      index=pd.DatetimeIndex([pd.Timestamp(r["date"]) for r in rows]))
    df["year"], df["month"] = df.index.year, df.index.month
    return df


def filtern(df, z: str, stichtag: str):
    if z == "max":
        return df
    import pandas as pd
    return df[df.index >= pd.Timestamp(f"{int(stichtag[:4]) - int(z)}-01-01")]


def gleich(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
    return a == b


def py_tupel(t) -> list:
    return [t["entry_date"].strftime("%Y-%m-%d"), t["exit_date"].strftime("%Y-%m-%d"), t["return_pct"],
            1 if t.get("open") else 0, 1 if t.get("stopped") else 0,
            t.get("fehlende_sitzungen", 0), t.get("auffaellige_abstaende", 0), 1 if t.get("naeherung") else 0]


def js_tupel(t) -> list:
    # Messlauf-Spalten: 0 Ein, 1 Aus, 4 Rendite, 5 offen, 6 gestoppt, 11 fehlend, 12 Abstand, 13 Näherung
    return [t[0], t[1], t[4], t[5], t[6], t[11], t[12], t[13]]


MERKMALE = ["Einstieg", "Ausstieg", "Rendite", "offen", "gestoppt", "fehlende_sitzungen", "auffaellige_abstaende",
            "naeherung"]


def vergleiche(py_r: dict, js_v: dict) -> str | None:
    pt = sorted((py_tupel(t) for t in py_r["trades"]), key=lambda x: (x[0], x[1]))
    jt = sorted((js_tupel(t) for t in js_v["trades"]), key=lambda x: (x[0], x[1]))
    if len(pt) != len(jt):
        return f"Trades {len(pt)} ≠ JS {len(jt)}"
    for a, b in zip(pt, jt):
        for i, (x, y) in enumerate(zip(a, b)):
            if not gleich(x, y):
                return f"{a[0]}→{a[1]}: {MERKMALE[i]} {x} ≠ JS {y}"
    ps, js = py_r["stats"] or {}, js_v["stats"] or {}
    pg, jg = ps.get("taeglich"), js.get("taeglich")
    if (pg is None) != (jg is None):
        return f"taeglich {pg is None and 'None' or 'Wert'} ≠ JS {jg is None and 'None' or 'Wert'}"
    if pg:
        for k in ("max_dd", "final_equity"):
            if not gleich(pg[k], jg[k]):
                return f"taeglich.{k} {pg[k]} ≠ JS {jg[k]}"
    return None


def main() -> int:
    from shared.strategies import plain_vanilla as pv
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot")
    ap.add_argument("messlauf")
    ap.add_argument("--kombis", default=None)
    ap.add_argument("--strategien", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    ordner = pathlib.Path(a.snapshot)
    ml = json.loads(pathlib.Path(a.messlauf).read_text(encoding="utf-8"))
    stichtag = ml["stichtag"]
    pflicht = set(a.strategien.split(",")) if a.strategien else None
    ergebnis, rot = {}, 0
    for tk, o in ml["ticker"].items():
        df_all = lade_df(ordner / (tk.replace("^", "_") + ".json"), stichtag)
        boerse = "XETRA" if tk in ("^GDAXI",) or tk.endswith(".DE") else "NYSE"
        for kombi, je in o["je"].items():
            if a.kombis and kombi not in a.kombis.split(","):
                continue
            z, s = kombi.split("|")
            sub = filtern(df_all, z, stichtag)
            typ, pct = ("aus", 0.0)
            if s != "aus":
                typ, pct = ("trailing", float(s[8:])) if s.startswith("trailing") else ("fixed", float(s[5:]))
            for key, js_v in je.items():
                if key not in pv.STRATEGIES or (pflicht and key not in pflicht):
                    continue
                try:
                    r = pv.auswerten(sub, key, boerse=boerse, stichtag=__import__("datetime").date.fromisoformat(stichtag),
                                     stop_pct=pct, stop_type=typ)
                    abw = vergleiche(r, js_v)
                except Exception as e:  # noqa: BLE001
                    abw = f"Ausnahme {type(e).__name__}: {e}"
                ergebnis.setdefault(key, []).append((tk, kombi, abw))
    for key, liste in sorted(ergebnis.items()):
        abw = [x for x in liste if x[2]]
        zeile = f"{'GLEICH ' if not abw else 'ABWEICH'} {key:20s} {len(liste) - len(abw)}/{len(liste)}"
        if abw:
            zeile += f"  z. B. {abw[0][0]} {abw[0][1]}: {abw[0][2]}"
            if pflicht is None or key in pflicht:
                rot += 1
        print(zeile)
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(ergebnis, ensure_ascii=False), encoding="utf-8")
    return 1 if rot else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
