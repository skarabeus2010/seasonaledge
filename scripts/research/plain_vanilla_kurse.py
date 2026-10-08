#!/usr/bin/env python3
"""
plain_vanilla_kurse.py — lädt Kursreihen genau so, wie die Seite /plain-vanilla sie lädt (öffentliche REST-Abfrage
mit dem Schlüssel, der in der ausgelieferten Seite steht), für den Messlauf scripts/js/probe_plain_vanilla_messlauf.js.

    py -3.14 scripts/research/plain_vanilla_kurse.py --ziel <ordner> [^DJI ^GSPC SPY QQQ ^GDAXI]

Schreibt <ordner>/<ticker>.json (Liste {date, close, log_return, tdom, tdoy}). Die Kursdateien gehören NICHT ins
Repo (Datenbestand, wird bei jedem Lauf neu geholt). Kein Schlüssel im Code: URL und Schlüssel werden zur Laufzeit
aus der Live-Seite gelesen.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

SEITE = "https://seasonalpha.ai/plain-vanilla"
STANDARD = ["^DJI", "^GSPC", "SPY", "QQQ", "^GDAXI"]


def _zugang() -> tuple[str, str]:
    html = urllib.request.urlopen(urllib.request.Request(SEITE, headers={"User-Agent": "sa-messlauf"}), timeout=30).read().decode()
    url = re.search(r"__SA_SB_URL='([^']+)'", html).group(1)
    key = re.search(r"__SA_SB_KEY='([^']+)'", html).group(1)
    return url, key


def lade(ticker: str, url: str, key: str) -> list[dict]:
    zeilen, offset = [], 0
    while True:
        q = (f"ticker=eq.{urllib.parse.quote(ticker)}&select=date,close,log_return,tdom,tdoy&order=date"
             f"&date=gte.1895-01-01&limit=1000&offset={offset}")
        req = urllib.request.Request(f"{url}/rest/v1/prices?{q}",
                                     headers={"apikey": key, "Authorization": f"Bearer {key}"})
        for versuch in range(4):
            try:
                teil = json.loads(urllib.request.urlopen(req, timeout=60).read())
                break
            except Exception:
                if versuch == 3:
                    raise
                time.sleep(1 + versuch)
        zeilen += teil
        if len(teil) < 1000:
            return zeilen
        offset += 1000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ziel", required=True)
    ap.add_argument("ticker", nargs="*", default=STANDARD)
    a = ap.parse_args()
    ziel = pathlib.Path(a.ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    url, key = _zugang()
    for t in a.ticker:
        z = lade(t, url, key)
        (ziel / f"{t.replace('^', '_')}.json").write_text(json.dumps(z), encoding="utf-8")
        print(f"{t}: {len(z)} Zeilen, {z[0]['date'] if z else '-'} … {z[-1]['date'] if z else '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
