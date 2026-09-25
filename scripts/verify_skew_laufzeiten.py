#!/usr/bin/env python3
"""verify_skew_laufzeiten.py — NE-Skew, Skew-Term, Term-Struktur, Smile pruefen.

WARUM (Messung 2026-09-24, 40 Ticker): diese vier Werte liefen ueber den
Anbieter-Picker, der den Kontrakt ueber das Anbieter-Delta waehlt (aus der IV
desselben Kontrakts). NE-Skew war obendrein gar nicht der naechste Verfall,
sondern immer der Monatsverfall mit 22 Tagen (Monatsvorzug in _skew_at).
Ausreisser |NE| > 15: 5, |Skew-Term| > 10: 3 — nach der Umstellung 0.

Die Verzweigungen stammen aus der Codex-Entwurfspruefung: Anbieter-Ausfall
bei gueltiger eigener Kette, veralteter Spot, fehlende Fluegel, lueckenhafte
ATM-Klammer, NE-Ersatz und NE ohne Ersatz, single ohne 30-Tage-Kurve, fehlende
Smile-Punkte, Term mit 0/1 Punkten, Konsistenz Kurve <-> Anzeige, und
leg_from_prices unveraendert.

Laeuft isoliert (scripts/waechter_isolation.py): Unterprozess, Schreibsperre
vor dem Cron-Import, keine .env, Nonce-Bilanz.

Aufruf: py -3.14 scripts/verify_skew_laufzeiten.py     (Exit 1 = Fehler)
"""
from __future__ import annotations
import os
import sys

os.environ["SA_OHNE_DOTENV"] = "1"
sys.dont_write_bytecode = True

import io                                      # noqa: E402
import contextlib                              # noqa: E402
import math                                    # noqa: E402
from datetime import date, datetime, timedelta  # noqa: E402
from pathlib import Path                       # noqa: E402
from zoneinfo import ZoneInfo                  # noqa: E402

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.waechter_isolation import (melde_bilanz, nonce_sichern,   # noqa: E402
                                        schreibsperre, starte_isoliert)

eh = m = bs = None                             # erst im Unterprozess, nach der Sperre
PROBEN: list[str] = []
ERWARTETE_PROBEN = ("regression", "basis", "ne_ersatz", "ne_ohne", "anbieter_fehlt",
                    "spot_veraltet", "fluegel_fehlen", "klammer_luecke", "single",
                    "smile_luecke", "ne_weggefiltert", "tick", "helfer", "render_ne", "audit")

ET = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")
SESSION = date(2026, 9, 24)
S = 100.0
# Verfaelle: echte Monatsverfaelle (3. Freitag) plus kurze Wochenverfaelle.
VERFAELLE = {1: "2026-09-25", 4: "2026-09-28", 8: "2026-10-02", 22: "2026-10-16",
             57: "2026-11-20", 85: "2026-12-18", 113: "2027-01-15", 176: "2027-03-19"}


def _zeile(ok: bool, text: str) -> int:
    print(f"  {'OK  ' if ok else 'FAIL'} {text}")
    return 0 if ok else 1


def _ns(tag: date, stunde=15, minute=30) -> int:
    return int(datetime(tag.year, tag.month, tag.day, stunde, minute, tzinfo=ET).timestamp() * 1e9)


def _sigma(K: float, T: float, schiefe: float = 0.10) -> float:
    """Smile mit Put-Skew und leichter Aufwaertsneigung der Term-Struktur."""
    mm = math.log(K / S)
    return 0.20 + 0.03 * T - schiefe * mm + 0.40 * mm * mm


def _kette(dtes=None, schritt=None, entferne=None, provider=True, frisch=True,
           veraltet=(), schiefe=0.10) -> list:
    """Synthetische Chain im Massive-Format.

    schritt(dte) -> Strike-Abstand; entferne(dte, K, typ) -> True = weglassen;
    provider=False entfernt IV/Greeks (Anbieter-Pick unmoeglich)."""
    from shared.black_scholes import bs_price, bs_delta
    dtes = dtes or sorted(VERFAELLE)
    schritt = schritt or (lambda d: 1.0)
    lu = _ns(SESSION if frisch else SESSION - timedelta(days=14))
    out = []
    for dte in dtes:
        ex = VERFAELLE[dte]; T = dte / 365.0; st = schritt(dte)
        k = 60.0
        while k <= 140.0 + 1e-9:
            K = round(k, 4)
            sig = _sigma(K, T, schiefe)
            for typ in ("call", "put"):
                if entferne and entferne(dte, K, typ):
                    continue
                px = round(max(bs_price(S, K, T, sig, typ), 0.01), 2)
                c = {"details": {"expiration_date": ex, "contract_type": typ, "strike_price": K,
                                 "ticker": f"O:SYN{ex[2:4]}{ex[5:7]}{ex[8:10]}{typ[0].upper()}{int(K * 1000):08d}"},
                     "open_interest": 100, "day": {"close": px, "volume": 10,
                                                   "last_updated": _ns(SESSION - timedelta(days=14)) if dte in veraltet else lu}}
                if provider:
                    c["implied_volatility"] = round(sig, 4)
                    c["greeks"] = {"delta": round(bs_delta(S, K, T, sig, typ), 4)}
                out.append(c)
            k += st
    return out


def _enrich(kette, close_datum=SESSION) -> dict | None:
    m._spot = lambda sym, key: S
    m._chain = lambda sym, key, spot=None: kette
    m._realized_vol = lambda sym, n=21, bis=None: (0.18, S, close_datum.isoformat())
    with contextlib.redirect_stdout(io.StringIO()):
        return m._enrich("SYN", "probe-kein-echter-schluessel")


# 1-Tages-Verfall mit grobem Raster: 25d liegt ~0,7 % aus dem Geld, bei
# 1-$-Schritten trifft kein Strike die Toleranz — wie bei 13 echten Tickern.
GROB_1T = lambda d: 1.0
FEIN_1T = lambda d: 0.1 if d == 1 else 1.0


_NODE_PROBE = r"""
const fs = require('fs');
const src = fs.readFileSync(process.argv[1], 'utf8');
const a = src.indexOf('function renderSkewCurve(tk){');
const b = src.indexOf('// IV-Term-Structure', a);
if (a < 0 || b < 0) { console.log(JSON.stringify({fehler: 'Funktion nicht gefunden'})); process.exit(0); }
const fnSrc = src.slice(a, b);
const labels = ['10ΔP','25ΔP','40ΔP','ATM','40ΔC','25ΔC','10ΔC'];
const kurve = [0.21,0.2,0.2,0.19,0.19,0.18,0.18];
const faelle = {
  nur_ne:  {labels, iv30: null, iv_ne: kurve, dte_ne: 4, dte30: null},
  beide:   {labels, iv30: kurve, iv_ne: kurve, dte_ne: 4, dte30: 30},
  keine:   {labels, iv30: null, iv_ne: null},
};
const out = {};
for (const [name, sc] of Object.entries(faelle)) {
  let gefangen = null;
  const ctx = {document: {getElementById: () => ({innerHTML: ''})}, T: (k, d) => d,
               ACC: 'ACC', BLUE: 'BLUE', MUT: 'MUT', baseChart: () => ({}),
               renderInto: (id, opt) => { gefangen = opt; }, _curTicker: () => ({skew_curve: sc})};
  const f = new Function(...Object.keys(ctx), fnSrc + '; renderSkewCurve("X"); return null;');
  f(...Object.values(ctx));
  out[name] = gefangen ? {n: gefangen.series.length, namen: gefangen.series.map(s => s.name),
                          farben: gefangen.colors} : null;
}
console.log(JSON.stringify(out));
"""


def _pruefe_render() -> int:
    import json
    import subprocess
    r = subprocess.run(["node", "-e", _NODE_PROBE, str(_ROOT / "landing" / "pages" / "skew.html")],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)
    try:
        out = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return _zeile(False, f"node-Probe lieferte nichts Auswertbares (Exit {r.returncode}): "
                             f"{(r.stderr or r.stdout)[-200:]}")
    if "fehler" in out:
        return _zeile(False, out["fehler"])
    f = 0
    ne = out.get("nur_ne")
    f += _zeile(ne is not None and ne["n"] == 1 and ne["farben"] == ["BLUE"]
                and ne["namen"][0].startswith("Front"),
                f"nur NE-Kurve: gezeichnet, eigene Farbe — {ne}")
    b = out.get("beide")
    f += _zeile(b is not None and b["n"] == 2 and b["farben"] == ["ACC", "BLUE"], f"beide Kurven: {b}")
    f += _zeile(out.get("keine") is None, "keine Kurve: nichts gezeichnet")
    return f


def _proben() -> int:
    fehler = 0

    # ── leg_from_prices bit-genau unveraendert (eingefrorene Referenz) ─────────
    print("leg_from_prices unveraendert (eingefrorene Referenzwerte)\n" + "-" * 68)
    kette = _kette()
    with contextlib.redirect_stdout(io.StringIO()):
        by = m._own_cands(kette, s30_ref=SESSION.isoformat(), underlying="SYN")
    ist = {e: bs.leg_from_prices(by[e]["cands"], S, by[e]["dte"]) for e in sorted(by)}
    fehler += _zeile(ist == REFERENZ_LEG, f"{len(ist)} Expiries identisch mit der Referenz"
                     + ("" if ist == REFERENZ_LEG else f" — IST {ist}"))
    PROBEN.append("regression")

    # ── Basis: alles vorhanden, NE am 1-Tages-Verfall messbar ─────────────────
    print("\nBasis (feines Raster am 1-Tages-Verfall)\n" + "-" * 68)
    r = _enrich(_kette(schritt=FEIN_1T))
    fehler += _zeile(r is not None and m._rankbar(r), f"rankbar: cm_mode={r and r.get('cm_mode')}")
    # Kein Vorzeichen-Test: bei 1 Tag hat der synthetische Smile nur ~0,14 pts
    # Put-Skew, und ein 25d-Kontrakt kostet ~8 Cent — die Rundung auf 1 Cent
    # dominiert das Vorzeichen. Geprueft wird: gemessen, am richtigen Verfall,
    # plausibel klein.
    fehler += _zeile(r["skew_ne_unsicherheit_pts"] is not None,
                     f"Tick-Unsicherheit ausgewiesen: ±{r['skew_ne_unsicherheit_pts']} pts")
    fehler += _zeile(r["skew_ne_dte"] == 1 and r["skew_ne_ersatz"] is False
                     and r["skew_ne_pts"] is not None and abs(r["skew_ne_pts"]) < 3,
                     f"NE am 1-Tages-Verfall: {r['skew_ne_pts']} (dte {r['skew_ne_dte']}, Ersatz {r['skew_ne_ersatz']})")
    fehler += _zeile(r["skew_back_dte"] == 90 and (r["skew_back_pts"] or 0) > 0,
                     f"90-Tage-Skew interpoliert: {r['skew_back_pts']}")
    fehler += _zeile(r["skew_term_pts"] == round(r["skew_back_pts"] - r["skew_pts"], 2),
                     f"Skew-Term = 90 minus 30: {r['skew_term_pts']}")
    dtes = [t["dte"] for t in r["term"]]
    fehler += _zeile(len(dtes) >= 5 and dtes == sorted(dtes), f"Term-Struktur: {dtes}")
    fehler += _zeile(r["contango"] is True, f"Contango (Term steigt): {r['contango']}")
    fehler += _zeile(r["term_slope_von"] == dtes[0] and r["term_slope_bis"] == dtes[-1],
                     f"Steigung mit echten Endpunkten: {r['term_slope_von']}->{r['term_slope_bis']}")
    sc = r["skew_curve"]
    fehler += _zeile(sc["iv30"] is not None and sc["iv30"][1] == r["cm_put_iv"]
                     and sc["iv30"][3] == r["cm_iv_atm"] and sc["iv30"][5] == r["cm_call_iv"],
                     "Smile 30: 25d- und ATM-Punkte = angezeigte Werte")
    fehler += _zeile(sc["modus30"] == r["cm_mode"] and sc["dte30"] == 30, f"Smile 30 modus={sc['modus30']}")
    fehler += _zeile(sc["iv_ne"] is not None and sc["dte_ne"] == 1, f"Smile NE vorhanden (dte {sc['dte_ne']})")
    fp = r.get("front_provider") or {}
    fehler += _zeile(all(k in fp for k in ("skew_ne_pts", "term", "skew_curve", "skew_pts")),
                     "front_provider haelt alte NE/Term/Smile/30-Tage-Werte")
    PROBEN.append("basis")

    # ── NE-Ersatz: 1-Tages-Verfall scheitert, 4-Tages-Verfall springt ein ─────
    print("\nNE-Ersatz (grobes Raster am 1-Tages-Verfall)\n" + "-" * 68)
    r = _enrich(_kette(schritt=GROB_1T))
    fehler += _zeile(r["skew_ne_dte"] == 4 and r["skew_ne_ersatz"] is True and r["skew_ne_pts"] is not None,
                     f"NE = naechster auswertbarer: dte {r['skew_ne_dte']}, Ersatz {r['skew_ne_ersatz']}")
    fehler += _zeile(r["skew_curve"]["dte_ne"] == 4, "Smile NE auf demselben Ersatzverfall")
    PROBEN.append("ne_ersatz")

    # ── NE ohne Ersatz: naechster auswertbarer liegt ueber 10 Tagen ───────────
    print("\nNE ohne Ersatz (kein auswertbarer Verfall bis 10 Tage)\n" + "-" * 68)
    r = _enrich(_kette(dtes=[1, 22, 57, 85, 113, 176], schritt=GROB_1T))
    fehler += _zeile(r["skew_ne_pts"] is None and r["skew_ne_dte"] == 1 and r["skew_ne_ersatz"] is False,
                     f"NE leer statt 22-Tage-Wert: {r['skew_ne_pts']} (dte {r['skew_ne_dte']})")
    PROBEN.append("ne_ohne")

    # ── Anbieter fehlt, eigene Kette gueltig ───────────────────────────────────
    print("\nAnbieter-Pick fehlt (keine IV/Greeks), eigene Kette gueltig\n" + "-" * 68)
    r = _enrich(_kette(schritt=FEIN_1T, provider=False))
    fehler += _zeile(r is not None, "Ticker NICHT verworfen")
    if r:
        fehler += _zeile(m._rankbar(r) and r["skew_pts"] == r["cm_skew_pts"],
                         f"Anzeige aus eigener Rechnung: {r['skew_pts']}")
        fehler += _zeile((r.get("front_provider") or {}).get("skew_pts") is None,
                         "front_provider ohne Anbieter-25d-Wert")
        fehler += _zeile(r["skew_ne_pts"] is not None and len(r["term"]) >= 5,
                         "NE und Term trotzdem berechnet")
    PROBEN.append("anbieter_fehlt")

    # ── Veralteter Spot: Kursreihe endet vor der Session ───────────────────────
    print("\nKursreihe endet vor der Session (kein Session-Schluss)\n" + "-" * 68)
    r = _enrich(_kette(schritt=FEIN_1T), close_datum=SESSION - timedelta(days=1))
    fehler += _zeile(r is not None and not m._rankbar(r), "nicht rankbar, Anbieterzeile bleibt")
    leer = (r["skew_ne_pts"] is None and r["term"] == [] and r["skew_back_pts"] is None
            and r["skew_curve"]["iv30"] is None and r["skew_curve"]["iv_ne"] is None
            and r["contango"] is None)
    fehler += _zeile(leer, "NE/90/Term/Smile/Contango leer — kein Rueckfall auf den Anbieter")
    PROBEN.append("spot_veraltet")

    # ── Fluegel fehlen: 57-Tage-Verfall nur nahe am Geld ──────────────────────
    print("\nFluegel fehlen am 57-Tage-Verfall\n" + "-" * 68)
    weg = lambda d, K, typ: d == 57 and abs(math.log(K / S)) > 0.03
    kette = _kette(schritt=FEIN_1T, entferne=weg)
    with contextlib.redirect_stdout(io.StringIO()):
        by = m._own_cands(kette, s30_ref=SESSION.isoformat(), underlying="SYN")
    e57 = by[VERFAELLE[57]]
    fehler += _zeile(bs.leg_from_prices(e57["cands"], S, 57) is None, "leg_from_prices scheitert (Fluegel)")
    r = _enrich(kette)
    fehler += _zeile(57 in [t["dte"] for t in r["term"]], "Term-Punkt 57 Tage trotzdem da (ATM ohne Fluegelzwang)")
    PROBEN.append("fluegel_fehlen")

    # ── Lueckenhafte ATM-Klammer am 8-Tages-Verfall ───────────────────────────
    print("\nATM-Klammer zu weit am 8-Tages-Verfall\n" + "-" * 68)
    luecke = lambda d, K, typ: d == 8 and abs(math.log(K / S)) < 0.04
    r = _enrich(_kette(schritt=FEIN_1T, entferne=luecke))
    fehler += _zeile(8 not in [t["dte"] for t in r["term"]], "8-Tage-Punkt verworfen (Anker > 0,5 sigma)")
    fehler += _zeile(r["contango"] is None or any(t["dte"] <= 14 for t in r["term"]),
                     f"Contango nur mit Punkt <= 14 Tage: {r['contango']}, Term {[t['dte'] for t in r['term']]}")
    PROBEN.append("klammer_luecke")

    # ── single: nur eine Stuetzstelle nahe 30 Tagen ───────────────────────────
    print("\nsingle (eine Stuetzstelle) -> keine 30-Tage-Kurve\n" + "-" * 68)
    r = _enrich(_kette(dtes=[22, 113, 176]))
    fehler += _zeile(r is not None and r.get("cm_mode") == "single", f"cm_mode={r and r.get('cm_mode')}")
    fehler += _zeile(r["skew_curve"]["iv30"] is None and r["skew_curve"]["modus30"] is None,
                     "keine 30-Tage-Kurve bei single")
    fehler += _zeile(r["skew_term_pts"] is None, "kein Skew-Term ohne rankbaren 30-Tage-Wert")
    fehler += _zeile(r["term_slope_von"] is not None, "Term-Steigung trotzdem (unabhaengig vom 30-Tage-Wert)")
    PROBEN.append("single")

    # ── Smile-Luecke: keine Kontrakte im 10d-Bereich ──────────────────────────
    print("\nSmile ohne 10d-Kontrakte an den 30-Tage-Stuetzstellen\n" + "-" * 68)
    # 10d liegt bei ~1,28 sigma*sqrt(T): 22 T. ~6,3 %, 57 T. ~10 % aus dem Geld;
    # 25d bei ~0,67 sigma*sqrt(T): 3,3 % bzw. 5,3 %. Schnitt dazwischen.
    ohne10 = lambda d, K, typ: ((d == 22 and abs(math.log(K / S)) > 0.045)
                                or (d == 57 and abs(math.log(K / S)) > 0.07))
    r = _enrich(_kette(schritt=FEIN_1T, entferne=ohne10))
    iv30 = r["skew_curve"]["iv30"]
    fehler += _zeile(iv30 is not None and iv30[0] is None and iv30[6] is None and iv30[1] is not None,
                     f"10d-Punkte leer, 25d vorhanden: {iv30}")
    PROBEN.append("smile_luecke")

    # ── NE-Verfaelle durch den Frische-Filter komplett weggefiltert (Codex R1, HOCH)
    print("\nNE-Verfaelle komplett veraltet\n" + "-" * 68)
    r = _enrich(_kette(schritt=FEIN_1T, veraltet={1}))
    fehler += _zeile(r["skew_ne_dte"] == 4 and r["skew_ne_ersatz"] is True,
                     f"1 T. veraltet -> 4 T. als ERSATZ: dte {r['skew_ne_dte']}, Ersatz {r['skew_ne_ersatz']}")
    r = _enrich(_kette(schritt=FEIN_1T, veraltet={1, 4, 8}))
    fehler += _zeile(r["skew_ne_pts"] is None and r["skew_ne_dte"] == 1 and r["skew_ne_ersatz"] is False,
                     f"1/4/8 T. veraltet -> NE leer statt 22 T. als regulaer: "
                     f"{r['skew_ne_pts']} (dte {r['skew_ne_dte']}, Ersatz {r['skew_ne_ersatz']})")
    PROBEN.append("ne_weggefiltert")

    # ── Tick-Rauschen: Richtung unbestimmt vs. richtungsfest (Codex R1)
    print("\nTick-Rauschen am 1-Tages-Verfall\n" + "-" * 68)
    r = _enrich(_kette(schritt=FEIN_1T))
    u, sk = r["skew_ne_unsicherheit_pts"], r["skew_ne_pts"]
    fehler += _zeile(r["skew_ne_richtung_unsicher"] is (u is not None and sk is not None and u >= abs(sk)),
                     f"flacher Skew {sk} bei ±{u}: Richtung unsicher = {r['skew_ne_richtung_unsicher']}")
    fehler += _zeile(r["skew_ne_richtung_unsicher"] is True,
                     "der bekannte Fall (+0,14 wahr, -0,09 gerundet) ist als unsicher markiert")
    r = _enrich(_kette(schritt=FEIN_1T, schiefe=2.0))
    fehler += _zeile(r["skew_ne_richtung_unsicher"] is False and (r["skew_ne_pts"] or 0) > 0,
                     f"steiler Put-Skew {r['skew_ne_pts']} bei ±{r['skew_ne_unsicherheit_pts']}: "
                     f"richtungsfest und positiv")
    PROBEN.append("tick")

    # ── Contango und Steigung direkt (Gleichstand, 0/1 Punkte)
    print("\nContango/Steigung: Randfaelle\n" + "-" * 68)
    for name, term, iv30, soll in [
        ("Gleichstand", [{"dte": 8, "iv": 0.20}], 0.20, None),
        ("kein Punkt <= 14 T.", [{"dte": 22, "iv": 0.18}], 0.20, None),
        ("kurz billiger", [{"dte": 8, "iv": 0.18}], 0.20, True),
        ("kurz teurer", [{"dte": 8, "iv": 0.22}], 0.20, False),
        ("ohne 30-Tage-Wert", [{"dte": 8, "iv": 0.18}], None, None),
    ]:
        ist = m._kontango(term, iv30)
        fehler += _zeile(ist is soll, f"Contango {name}: {ist}")
    for name, term, soll in [("0 Punkte", [], (None, None, None)),
                             ("1 Punkt", [{"dte": 8, "iv": 0.2}], (None, None, None)),
                             ("2 Punkte", [{"dte": 8, "iv": 0.2}, {"dte": 57, "iv": 0.25}], (5.0, 8, 57))]:
        ist = m._steigung(term)
        fehler += _zeile(ist == soll, f"Steigung {name}: {ist}")
    PROBEN.append("helfer")

    # ── Frontend: NE-Kurve allein wird gezeichnet (echte Funktion aus skew.html in node)
    print("\nFrontend renderSkewCurve (in node ausgefuehrt)\n" + "-" * 68)
    fehler += _pruefe_render()
    PROBEN.append("render_ne")
    return fehler


# Eingefroren am 2026-09-25 aus der abgenommenen Fassung von leg_from_prices
# (dieselbe, die auf 574 echten Expiries bit-genau gegen die alte gepr. wurde).
# Aendert sich hier etwas, aendert sich die Rechnung von Live UND Backfill.
REFERENZ_LEG: dict = {'2026-09-25': None, '2026-09-28': {'dte': 4, 'call_iv': 0.1986247960567474, 'put_iv': 0.20009849142432212, 'iv_atm': 0.2}, '2026-10-02': {'dte': 8, 'call_iv': 0.19883787840008732, 'put_iv': 0.20272938782572747, 'iv_atm': 0.2006}, '2026-10-16': {'dte': 22, 'call_iv': 0.19825525465011595, 'put_iv': 0.20533048250079156, 'iv_atm': 0.2014}, '2026-11-20': {'dte': 57, 'call_iv': 0.19943510499596595, 'put_iv': 0.2093246588736773, 'iv_atm': 0.2039}, '2026-12-18': {'dte': 85, 'call_iv': 0.20151243433058263, 'put_iv': 0.21318159829676153, 'iv_atm': 0.206}, '2027-01-15': {'dte': 113, 'call_iv': 0.20345759300887584, 'put_iv': 0.21690577102899555, 'iv_atm': 0.208}, '2027-03-19': {'dte': 176, 'call_iv': 0.20827042280435565, 'put_iv': 0.2223272265806794, 'iv_atm': 0.2126}}


def _isoliert(tmp: str) -> int:
    global eh, m, bs
    verstoesse = schreibsperre(Path(tmp).resolve())
    import shared.exchange_holidays as _eh
    import scripts.compute_options_skew as _m
    import shared.black_scholes as _bs
    eh, m, bs = _eh, _m, _bs
    eh._uhr = lambda tz: datetime(2026, 9, 24, 23, 0, tzinfo=UTC).astimezone(tz)
    fehler = _proben()
    print("\nSchreibzugriffe ausserhalb des Temp-Verzeichnisses (Audit-Hook)\n" + "-" * 68)
    fehler += _zeile(not verstoesse, f"{len(verstoesse)} gefunden")
    for v in verstoesse[:10]:
        print(f"       {v}")
    PROBEN.append("audit")
    return fehler


def pruefe() -> int:
    fehler = starte_isoliert(Path(__file__), ERWARTETE_PROBEN, "sa_laufzeitprobe_")
    print("\n" + ("ERGEBNIS: PASS" if fehler == 0 else f"ERGEBNIS: {fehler} FAIL"))
    return 1 if fehler else 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--isoliert":
        nonce = nonce_sichern()
        n = _isoliert(sys.argv[2])
        melde_bilanz(nonce, n, PROBEN)
        sys.exit(1 if n else 0)
    sys.exit(pruefe())
