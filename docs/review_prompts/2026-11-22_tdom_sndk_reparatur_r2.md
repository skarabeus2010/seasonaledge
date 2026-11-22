# Gegenprüfung Runde 2: SNDK-Split und TDOM-Lauf nach deinen Befunden (2026-11-22)

Deine Antwort Runde 1: docs/review_prompts/2026-11-22_tdom_sndk_reparatur_antwort.md. Umgesetzt:
- SNDK (Befund 1, 8): unveränderlicher Plan (open mode x), jede Zeile wird eingestuft (alt → schreiben, neu → erledigt, sonst Abbruch ohne Schreiben), log_return/tdom/tdoy und die Zeilen ab 13.11. müssen unverändert sein, EIN Upsert für alle offenen Zeilen, Rücklesen: Planschlüsselmenge, neu-Werte, ab-Bruch unverändert, basisabweichungen über die ganze Reihe ohne Treffer.
- Befund 5: Beide Läufe laufen auf dem Host unter  (wie der Deploy-Containertausch); im Skript selbst KEIN produktion()-Lock mehr (sonst Selbstblockade). TDOM-Trockenlauf endet bei Lesefehlern/verweigerten Tickern mit 1.
- Befund 3: Regel 4-6 in scripts/verify_calendar_rules.py vergleicht jetzt gegen tdom_tdoy_fuer_ticker (ein Ticker je Börse, ohne =F/Krypto/Devisen) statt Vorzeile+1 (Diff im Arbeitsbaum: git diff scripts/verify_calendar_rules.py).
- Befund 6 (Statistiken mit cumcount) und Futures/FOREX bleiben ausdrücklich offen (P3/P6), nicht Teil dieser Reparatur.

Urteil je Teil: FREIGABE / FREIGABE MIT AUFLAGEN / KEINE FREIGABE. Knapp, nummeriert.

## sndk_split.py
```python
"""SNDK-Split 8:1 einpflegen (Nutzerfreigabe 2026-11-22, Muster SOXX v66.29; Codex R1: plan-basiert + atomar).

Split wirksam 19.11.2026 nach Handelsschluss, erster Tag neuer Basis 20.11. (OCC-Infomemo 60125, 8-K). Yahoo hat
die Historie rückwirkend angepasst; der Nightly holte nur 7 Tage neu, daher liegt der Basisbruch in der DB am
Fensterrand 13.11. (12.11. alt 937,46, 13.11. neu 110,63).

Alle SNDK-Zeilen VOR dem 13.11.2026: open/high/low/close ÷ 8, volume × 8, log_return/tdom/tdoy unverändert.

  python3 /tmp/sndk_split.py              Trockenlauf: Vorbedingungen, PLAN anlegen (nur wenn noch keiner existiert)
  python3 /tmp/sndk_split.py --schreiben  schreibt NUR nach dem Plan

Der Plan (/app/logs/reparatur/sndk_split_plan.json) ist unveränderlich: je Zeile alt + neu, dazu die Zeilen ab dem
13.11. als Vergleich. Beim Schreiben wird jede Zeile eingestuft: gleich „alt“ → schreiben, gleich „neu“ → schon
erledigt, sonst Abbruch ohne Schreiben. Geschrieben wird in EINEM Upsert (eine Anfrage = eine Transaktion), danach
Rücklesen: genau die Planschlüssel = neu, Zeilen ab 13.11. unverändert, Basisprüfung über die ganze Reihe leer.
Ausführung unter exklusiver Produktionssperre auf dem Host (flock -x … docker exec), damit kein Lauf dazwischenschreibt.
"""
import json
import math
import os
import sys
from datetime import datetime, timezone

import requests

sys.path.insert(0, "/app")
from shared.supabase_client import get_client  # noqa: E402
from shared.basisabweichung import basisabweichungen  # noqa: E402

T, SPLIT, F = "SNDK", "2026-11-13", 8   # SPLIT = erste Zeile auf neuer Basis in der DB
SCHREIB = "--schreiben" in sys.argv
PLAN = "/app/logs/reparatur/sndk_split_plan.json"
KURS = ("open", "high", "low", "close")
SPALTEN = "ticker,date,open,high,low,close,volume,log_return,tdom,tdoy"


def lade(c):
    z, ab = [], "1900-01-01"
    while True:
        r = c.table("prices").select(SPALTEN).eq("ticker", T).gt("date", ab).order("date").limit(1000).execute().data
        z += r
        if len(r) < 1000:
            return [dict(x, date=x["date"][:10]) for x in z]
        ab = r[-1]["date"]


def gleich(a, b):
    if a is None or b is None:
        return a is b
    return abs(a - b) <= 1e-9 * max(1.0, abs(b))


def ist(z, soll):
    return all(gleich(z[k], soll[k]) for k in KURS) and z["volume"] == soll["volume"]


def plan_anlegen(c):
    alle = lade(c)
    vor = [z for z in alle if z["date"] < SPLIT]
    nach = [z for z in alle if z["date"] >= SPLIT]
    letzte, erste = vor[-1], nach[0]
    erklaert = math.log(erste["close"] / (letzte["close"] / F))
    print(f"Zeilen vor dem Bruch: {len(vor)} ({vor[0]['date']}..{letzte['date']}), ab 13.11.: {len(nach)}")
    print(f"Rendite 13.11. gespeichert {erste['log_return']:.8f}, aus 12.11./8 {erklaert:.8f}")
    y = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{T}?range=1mo&interval=1d&events=split",
                     headers={"User-Agent": "Mozilla/5.0"}, timeout=20).json()["chart"]["result"][0]
    splits = [(datetime.fromtimestamp(s["date"], timezone.utc).date().isoformat(), s["numerator"] / s["denominator"])
              for s in (y.get("events") or {}).get("splits", {}).values()]
    print("Yahoo-Splits:", splits)
    gruende = []
    if erste["date"] != SPLIT:
        gruende.append(f"erste Zeile auf neuer Basis ist {erste['date']}, nicht {SPLIT}")
    if abs(erklaert - erste["log_return"]) > 1e-4:
        gruende.append("Rendite am Bruch passt nicht zu Faktor 8")
    if not any(d in ("2026-11-19", "2026-11-20") and abs(f - F) < 1e-9 for d, f in splits):
        gruende.append("Yahoo meldet keinen Split 8:1 am 19./20.11.")
    if min(z["close"] for z in vor[-60:]) < 200:
        gruende.append("Zeilen vor dem Bruch sehen schon umgerechnet aus")
    if any(z[k] is None for z in vor for k in KURS):
        gruende.append("NULL-Kurse vor dem Bruch")
    if gruende:
        print("ABBRUCH:", gruende)
        return 1
    plan = {"ticker": T, "faktor": F, "bruch": SPLIT, "angelegt": datetime.now(timezone.utc).isoformat(),
            "zeilen": [{"date": z["date"], "alt": {k: z[k] for k in KURS + ("volume",)},
                        "neu": {**{k: z[k] / F for k in KURS},
                                "volume": int(round(z["volume"] * F)) if z["volume"] is not None else None},
                        "fest": {k: z[k] for k in ("log_return", "tdom", "tdoy")}} for z in vor],
            "ab_bruch": nach}
    os.makedirs(os.path.dirname(PLAN), exist_ok=True)
    with open(PLAN, "x") as h:          # nie überschreiben
        json.dump(plan, h)
    print(f"Plan angelegt: {PLAN} ({len(plan['zeilen'])} Zeilen), Beispiel {plan['zeilen'][-1]}")
    return 0


def schreiben(c):
    with open(PLAN) as h:
        plan = json.load(h)
    jetzt = {z["date"]: z for z in lade(c)}
    todo, erledigt, unerwartet = [], 0, []
    for p in plan["zeilen"]:
        z = jetzt.get(p["date"])
        if z is None:
            unerwartet.append(f"{p['date']} fehlt")
        elif ist(z, p["alt"]):
            todo.append(p)
        elif ist(z, p["neu"]):
            erledigt += 1
        else:
            unerwartet.append(f"{p['date']} weder alt noch neu")
        if z is not None and any(z[k] != v for k, v in p["fest"].items()):
            unerwartet.append(f"{p['date']} log_return/tdom/tdoy geändert")
    for a in plan["ab_bruch"]:
        z = jetzt.get(a["date"])
        if z is None or any(z[k] != a[k] for k in KURS + ("volume", "log_return")):
            unerwartet.append(f"{a['date']} (ab Bruch) geändert")
    print(f"Plan {len(plan['zeilen'])}: zu schreiben {len(todo)}, schon neu {erledigt}, unerwartet {len(unerwartet)}")
    if unerwartet:
        print("ABBRUCH, nichts geschrieben:", unerwartet[:10])
        return 1
    if todo:
        r = c.table("prices").upsert([{"ticker": T, "date": p["date"], **p["neu"]} for p in todo],
                                     on_conflict="ticker,date").execute()
        if len(r.data or []) != len(todo):
            print(f"SCHREIBFEHLER: {len(r.data or [])} statt {len(todo)} bestätigt")
            return 1
    zurueck = lade(c)
    jz = {z["date"]: z for z in zurueck}
    abw = [p["date"] for p in plan["zeilen"] if not ist(jz[p["date"]], p["neu"])
           or any(jz[p["date"]][k] != v for k, v in p["fest"].items())]
    abw += [a["date"] for a in plan["ab_bruch"] if any(jz[a["date"]][k] != a[k] for k in KURS + ("volume", "log_return"))]
    schluessel = sorted(z["date"] for z in zurueck if z["date"] < SPLIT) == [p["date"] for p in plan["zeilen"]]
    basis = basisabweichungen(zurueck)
    print(f"Rücklesen: Abweichungen {len(abw)}, Schlüsselmenge gleich {schluessel}, "
          f"Basisprüfung {basis['geprueft']} Paare, Treffer {basis['treffer']}")
    return 0 if not abw and schluessel and not basis["treffer"] else 1


def main():
    c = get_client()
    if not SCHREIB:
        if os.path.exists(PLAN):
            print("Plan existiert schon:", PLAN)
            return 0
        return plan_anlegen(c)
    if not os.path.exists(PLAN):
        print("ABBRUCH: kein Plan — zuerst Trockenlauf")
        return 1
    return schreiben(c)


if __name__ == "__main__":
    sys.exit(main())
```

## tdom_2025_lauf.py
```python
"""TDOM/TDOY ab 2025-01-01 nach Börsenkalender, alle Ticker außer Futures (=F), Krypto und Devisen — Nutzerfreigabe 2026-11-22.

  python3 /tmp/tdom_2025_lauf.py              Trockenlauf: Bericht + Sicherungsdatei (alt/neu je Zeile)
  python3 /tmp/tdom_2025_lauf.py --schreiben  schreibt über backfill_tdoy.schreiben (nur tdom/tdoy, je Zeile bestätigt),
                                              danach Rücklesen: 0 Abweichungen Pflicht
Grenzen je Ticker wie backfill_tdoy.grenzen_pruefen (kein ungeprüftes Kalenderjahr, ≤ 500 Zeilen).
Exit ≠ 0 bei Lesefehlern oder verweigerten Tickern, auch im Trockenlauf.
"""
import json
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/scripts")
from shared.supabase_client import get_client  # noqa: E402
from shared.symbols import SYMBOLS, get_exchange_for_holidays  # noqa: E402
import backfill_tdoy as bt  # noqa: E402

VON, BIS = "2025-01-01", "2026-12-31"
SCHREIB = "--schreiben" in sys.argv


def main():
    c = get_client()
    plan, verweigert, fehler = {}, {}, []
    for t in sorted(SYMBOLS):
        if t.endswith("=F") or get_exchange_for_holidays(t) in ("CRYPTO", "FOREX"):
            continue
        try:
            abw = bt.abweichungen(t, bt.lade(c, t, VON, BIS))
        except Exception as e:
            fehler.append(f"{t}: {type(e).__name__}: {str(e)[:120]}")
            continue
        if not abw:
            continue
        g = bt.grenzen_pruefen(t, VON, BIS, abw, 500)
        (verweigert if g else plan)[t] = g if g else abw
    n = sum(len(v) for v in plan.values())
    print(f"Ticker mit Änderungen: {len(plan)} · Zeilen: {n} · verweigert: {len(verweigert)} · Lesefehler: {len(fehler)}")
    for t, abw in sorted(plan.items(), key=lambda x: -len(x[1])):
        print(f"  {t:10s} {len(abw):4d}  erste {abw[0]['date']} {abw[0]['alt']}→{abw[0]['neu']}  letzte {abw[-1]['date']} {abw[-1]['alt']}→{abw[-1]['neu']}")
    for t, g in verweigert.items():
        print(f"  VERWEIGERT {t}: {g}")
    for f in fehler:
        print("  LESEFEHLER", f)
    stempel = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    pfad = f"/app/logs/reparatur/tdom_tdoy_2025_vorher_{stempel}.json"
    import os
    os.makedirs("/app/logs/reparatur", exist_ok=True)
    with open(pfad, "w") as h:
        json.dump({"von": VON, "bis": BIS, "plan": plan, "verweigert": verweigert}, h)
    print("Sicherung/Plan:", pfad)
    if fehler or verweigert:
        print("ABBRUCH: Lesefehler oder verweigerte Ticker — nichts geschrieben")
        return 1
    if not SCHREIB:
        return 0
    sfehler = []
    for t, abw in plan.items():
        sfehler += [f"{t} {x}" for x in bt.schreiben(c, t, abw)]
    print(f"Geschrieben: {n} Zeilen, Schreibfehler: {len(sfehler)}")
    for f in sfehler[:20]:
        print("  SCHREIBFEHLER", f)
    rest = {t: len(bt.abweichungen(t, bt.lade(c, t, VON, BIS))) for t in plan}
    offen = {t: k for t, k in rest.items() if k}
    print(f"Rücklesen: {len(plan)} Ticker, verbleibende Abweichungen: {sum(offen.values())} {offen if offen else ''}")
    return 1 if sfehler or offen else 0


if __name__ == "__main__":
    # Ausführung unter EXKLUSIVER Produktionssperre auf dem Host (flock -x … docker exec, Codex R1 Befund 5);
    # schreibend idempotent: Sollwerte kommen aus dem Kalender, ein Neustart schreibt nur noch Abweichungen.
    sys.exit(main())
```
