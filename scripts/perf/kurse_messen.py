"""S0 Messbasis (Transport): wie lange dauert das Laden einer Kursreihe aus Supabase je Ladeweg?

Plan: docs/TICKER_LADEN.md (S0). Nur lesend, öffentlicher Anon-Key aus der Live-Seite.

Varianten (dieselben Abfragen, die der Browser stellt):
  F  heute SA.fetchAllPrices   Offset-Blöcke per Range, je Block Prefer: count=exact, nacheinander
  V  heute ladeVollHistorie    Keyset date=gt.<letztes>, limit=1000, ohne Zählung, nacheinander
  K  neuer Lader SA.kurse      wie V (Keyset), Ende = Block < 1000, mit Prüfung streng aufsteigender Daten

Je Ticker und Variante N gültige Läufe, Varianten abwechselnd (gleiche Netzlage), Median und p95 der Dauer,
Anfragen, übertragene und dekodierte Bytes, Zeilen. Ein Fehlerkörper oder eine abweichende Zeilenzahl macht
den Lauf ungültig; er wird gezählt, nicht gemittelt.

Aufruf: py -3.14 scripts/perf/kurse_messen.py [--laeufe 10] [--json ausgabe.json] [TICKER ...]
"""
import argparse
import gzip
import json
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request

FELDER = "date,close,log_return,tdom,tdoy"
STANDARD = ["SPY", "^GDAXI", "^DJI", "SAP.DE", "BTC-USD", "CRWV"]


def zugang():
    seite = urllib.request.urlopen("https://seasonalpha.ai/dashboard", timeout=30).read().decode()
    url = re.search(r"__SA_SB_URL='([^']*)'", seite).group(1)
    key = re.search(r"__SA_SB_KEY='([^']*)'", seite).group(1)
    if "%%" in url or "%%" in key:
        raise SystemExit("Zugangsdaten auf der Live-Seite nicht ersetzt")
    return url, key


class Lauf:
    def __init__(self):
        self.anfragen = 0
        self.bytes_netz = 0
        self.bytes_roh = 0


def abruf(url, key, query, lauf, extra=None):
    h = {"apikey": key, "Authorization": "Bearer " + key, "Accept-Encoding": "gzip"}
    h.update(extra or {})
    req = urllib.request.Request(url + "/rest/v1/prices?" + query, headers=h)
    with urllib.request.urlopen(req, timeout=60) as r:
        netz = r.read()
        roh = gzip.decompress(netz) if r.headers.get("Content-Encoding") == "gzip" else netz
        cr = r.headers.get("Content-Range")
    lauf.anfragen += 1
    lauf.bytes_netz += len(netz)
    lauf.bytes_roh += len(roh)
    daten = json.loads(roh)
    if not isinstance(daten, list):
        raise ValueError("kein Array")
    return daten, cr


def variante_f(url, key, ticker, lauf):
    alle, off = [], 0
    basis = f"ticker=eq.{urllib.parse.quote(ticker)}&select={FELDER}&order=date"
    while True:
        z, cr = abruf(url, key, basis, lauf, {"Range": f"{off}-{off + 999}", "Prefer": "count=exact"})
        alle += z
        gesamt = int(cr.split("/")[1]) if cr and cr.split("/")[1] != "*" else None
        if gesamt is not None and len(alle) < gesamt:
            off = len(alle)
            continue
        return alle


def variante_keyset(url, key, ticker, lauf, pruefen=False):
    alle, nach = [], None
    basis = f"ticker=eq.{urllib.parse.quote(ticker)}&select={FELDER}&order=date.asc&limit=1000"
    while True:
        z, _ = abruf(url, key, basis + (f"&date=gt.{nach}" if nach else ""), lauf)
        if pruefen and z:
            if nach is not None and not z[0]["date"] > nach:
                raise ValueError("Cursor schreitet nicht fort")
            if any(not z[i]["date"] < z[i + 1]["date"] for i in range(len(z) - 1)):
                raise ValueError("nicht streng aufsteigend")
        alle += z
        if len(z) < 1000:
            return alle
        nach = z[-1]["date"]


VARIANTEN = {
    "F": variante_f,
    "V": lambda u, k, t, l: variante_keyset(u, k, t, l),
    "K": lambda u, k, t, l: variante_keyset(u, k, t, l, pruefen=True),
}


def p95(werte):
    w = sorted(werte)
    if len(w) == 1:
        return w[0]
    pos = 0.95 * (len(w) - 1)
    lo = int(pos)
    return w[lo] + (w[min(lo + 1, len(w) - 1)] - w[lo]) * (pos - lo)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker", nargs="*", default=STANDARD)
    ap.add_argument("--laeufe", type=int, default=10)
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    url, key = zugang()
    ergebnis = {}
    for ticker in a.ticker:
        soll = len(variante_keyset(url, key, ticker, Lauf(), pruefen=True))
        mess = {v: [] for v in VARIANTEN}
        ungueltig = {v: 0 for v in VARIANTEN}
        versuche = 0
        while min(len(m) for m in mess.values()) < a.laeufe and versuche < a.laeufe * 3:
            versuche += 1
            for v, fn in VARIANTEN.items():
                if len(mess[v]) >= a.laeufe:
                    continue
                lauf = Lauf()
                t = time.perf_counter()
                try:
                    zeilen = fn(url, key, ticker, lauf)
                except Exception:
                    ungueltig[v] += 1
                    continue
                dauer = time.perf_counter() - t
                if len(zeilen) != soll:
                    ungueltig[v] += 1
                    continue
                mess[v].append((dauer, lauf.anfragen, lauf.bytes_netz, lauf.bytes_roh))
        ergebnis[ticker] = {"zeilen": soll, "varianten": {}}
        for v, m in mess.items():
            if not m:
                ergebnis[ticker]["varianten"][v] = {"gueltig": 0, "ungueltig": ungueltig[v]}
                continue
            d = [x[0] for x in m]
            ergebnis[ticker]["varianten"][v] = {
                "gueltig": len(m), "ungueltig": ungueltig[v],
                "median_s": round(statistics.median(d), 3), "p95_s": round(p95(d), 3),
                "anfragen": m[0][1], "bytes_netz": m[0][2], "bytes_roh": m[0][3]}
        z = ergebnis[ticker]
        for v, e in z["varianten"].items():
            if e["gueltig"]:
                sys.stdout.write(f"{ticker:8s} {v}  {z['zeilen']:6d} Zeilen  {e['anfragen']:3d} Anfr.  "
                                 f"Median {e['median_s']:6.2f}s  p95 {e['p95_s']:6.2f}s  "
                                 f"netz {e['bytes_netz'] / 1024:7.0f} KB  roh {e['bytes_roh'] / 1024:7.0f} KB  "
                                 f"gültig {e['gueltig']}  ungültig {e['ungueltig']}\n")
            else:
                sys.stdout.write(f"{ticker:8s} {v}  KEIN gültiger Lauf (ungültig {e['ungueltig']})\n")
        sys.stdout.flush()
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"stand_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "laeufe": a.laeufe, "ticker": ergebnis}, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
