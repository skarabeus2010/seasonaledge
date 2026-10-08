#!/usr/bin/env python3
"""
plain_vanilla_kurse.py — lädt Kursreihen genau so, wie die Seite /plain-vanilla sie lädt (öffentliche REST-Abfrage
mit dem Schlüssel, der in der ausgelieferten Seite steht), für den Messlauf scripts/js/probe_plain_vanilla_messlauf.js.

    py -3.14 scripts/research/plain_vanilla_kurse.py --ziel <ordner> [^DJI ^GSPC SPY QQQ ^GDAXI]

Schreibt <ordner>/<ticker>.json (Liste {date, close, log_return, tdom, tdoy}) und <ordner>/snapshot.json mit Stichtag
(--stichtag, Standard: letzter gemeinsamer Kurstag), Hash und Quelle. `pruefe_snapshot(ordner)` rechnet den Hash neu;
der Messlauf bricht bei Abweichung ab. Hashverfahren: sha256 über (Dateiname, NUL, Bytes) aller Kursdateien, sortiert. Die Kursdateien gehören NICHT ins
Repo (Datenbestand, wird bei jedem Lauf neu geholt). Kein Schlüssel im Code: URL und Schlüssel werden zur Laufzeit
aus der Live-Seite gelesen.
"""
from __future__ import annotations

import argparse
import hashlib
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


def snapshot_hash(ordner: pathlib.Path) -> str:
    h = hashlib.sha256()
    # nach Dateiname in Zeichencode-Reihenfolge — wie JS Array.sort(); WindowsPath sortiert sonst ohne Groß/klein
    for f in sorted(ordner.glob("*.json"), key=lambda q: q.name):
        if f.name != "snapshot.json":
            h.update(f.name.encode() + b"\0" + f.read_bytes())
    return h.hexdigest()[:16]


def pruefe_snapshot(ordner) -> dict:
    ordner = pathlib.Path(ordner)
    meta = json.loads((ordner / "snapshot.json").read_text(encoding="utf-8"))
    ist = snapshot_hash(ordner)
    if ist != meta["hash"]:
        raise SystemExit(f"Kurs-Snapshot verändert: Hash {ist} ≠ {meta['hash']}")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ziel", required=True)
    ap.add_argument("--stichtag", default=None)
    ap.add_argument("--pruefen", action="store_true", help="nur Hash des vorhandenen Snapshots prüfen")
    ap.add_argument("ticker", nargs="*", default=STANDARD)
    a = ap.parse_args()
    ziel = pathlib.Path(a.ziel)
    if a.pruefen:
        print("Snapshot unverändert:", pruefe_snapshot(ziel))
        return 0
    if (ziel / "snapshot.json").exists():
        raise SystemExit(f"{ziel} enthält schon einen Snapshot — eingefroren, neuen Ordner wählen")
    ziel.mkdir(parents=True, exist_ok=True)
    letzte = []
    url, key = _zugang()
    for t in a.ticker:
        z = lade(t, url, key)
        (ziel / f"{t.replace('^', '_')}.json").write_text(json.dumps(z), encoding="utf-8")
        letzte.append(z[-1]["date"] if z else "0000-00-00")
        print(f"{t}: {len(z)} Zeilen, {z[0]['date'] if z else '-'} … {z[-1]['date'] if z else '-'}")
    stichtag = a.stichtag or min(letzte)
    (ziel / "snapshot.json").write_text(json.dumps({
        "stichtag": stichtag, "hash": snapshot_hash(ziel), "ticker": a.ticker,
        "quelle": f"{SEITE} → öffentliche prices-Abfrage", "verfahren": "sha256(name\0bytes), sortiert, 16 Zeichen"},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("Snapshot:", stichtag, snapshot_hash(ziel))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
