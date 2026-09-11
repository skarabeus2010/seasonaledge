#!/usr/bin/env python3
"""
verify_leg_robustheit.py — haelt die 25Δ-Leg-Auswahl gegen verdorbene Preise dicht.

WARUM ES DAS GIBT: Bis zum 2026-09-11 wurde je Kontrakt die IV aus dem Preis
invertiert und das Delta DANN aus genau dieser IV berechnet. Ein schlechter
Preis erzeugte damit beides — die falsche IV und das Delta, das den Kontrakt wie
den gesuchten Strike aussehen liess. Die Delta-Toleranz prueft gegen dieselbe
verdorbene Groesse und kann das nicht fangen.

Live gemessen an dem Tag: SPY wies eine ATM-IV von 38 % aus (realistisch ~13 %),
SPGI 43 % ueber BEIDEN Fluegeln, HON gar keine. Auf /skew standen 21 % der
Ticker mit einer 25Δ-Put-IV UNTER der ATM-IV — bei Aktien praktisch
ausgeschlossen.

Dieses Skript baut eine saubere synthetische Kette, verdirbt gezielt einzelne
Kontrakte und verlangt, dass die Auswahl stabil bleibt.

Nutzung:  PYTHONUTF8=1 py -3.14 scripts/verify_leg_robustheit.py
Exit 0 = robust, 1 = ein verdorbener Preis hat die Auswahl gekippt.
"""
from __future__ import annotations
import math
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.black_scholes import (bs_price, leg_from_prices, forward,  # noqa: E402
                                  R, DELTA_TOL)

_ausfaelle: list[str] = []


def _melde(fall: str, ok: bool, detail: str = "") -> None:
    print(f"  {fall:<56}{'OK' if ok else 'ABWEICHUNG'}")
    if not ok:
        _ausfaelle.append(fall)
        if detail:
            print(f"      {detail}")


def _kette(spot: float, dte: int, atm_vol: float, skew: float,
           schritt: float = 5.0, n: int = 24) -> list:
    """Synthetische Kette mit glattem Smile: IV(K) = atm_vol + skew*log(F/K).

    `skew > 0` heisst Puts teurer als Calls — die normale Aktien-Form.
    Die Preise sind mit genau dieser IV bepreist, also ist die Kette in sich
    konsistent und die Soll-Antwort bekannt.
    """
    T = dte / 365.0
    F = forward(spot, T)
    cands = []
    for i in range(-n, n + 1):
        K = round((round(spot / schritt) * schritt) + i * schritt, 2)
        if K <= 0:
            continue
        iv = atm_vol + skew * math.log(F / K)
        if iv <= 0.01:
            continue
        for typ in ("call", "put"):
            cands.append({"typ": typ, "K": K, "px": bs_price(spot, K, T, iv, typ)})
    return cands


def _verdirb_nahe_atm(cands: list, typ: str, faktor: float, spot: float, dte: int):
    """EINE Seite nahe ATM moderat verdrehen — das ist das ECHTE Fehlermuster.

    Eine 20-fache Ueberteuerung eines weiten Fluegels erzeugt eine IV ueber
    IV_MAX und fliegt ohnehin raus; sie testet also nichts. Der Live-Fall sah
    anders aus: SPY wies (call 0.12 + put 0.65)/2 = 0.385 als ATM-IV aus. Eine
    Seite war moderat daneben, blieb im gueltigen IV-Band und vergiftete den
    Mittelwert.
    """
    F = forward(spot, dte / 365.0)
    passend = [c for c in cands if c["typ"] == typ]
    ziel = min(passend, key=lambda c: abs(c["K"] - F))
    out, K = [], ziel["K"]
    for c in cands:
        out.append({**c, "px": c["px"] * faktor} if c is ziel else c)
    return out, K


def _verdirb(cands: list, typ: str, richtung: str, faktor: float) -> list:
    """Einen weit aus dem Geld liegenden Kontrakt kuenstlich ueberteuern —
    genau das Muster eines veralteten Prints, der nicht zum Spot passt."""
    passend = [c for c in cands if c["typ"] == typ]
    passend.sort(key=lambda c: c["K"], reverse=(richtung == "hoch"))
    ziel = passend[2]                       # drittweitester Strike dieser Seite
    out = []
    for c in cands:
        if c is ziel:
            out.append({**c, "px": c["px"] * faktor})
        else:
            out.append(c)
    return out, ziel["K"]


def main() -> int:
    print("=" * 78)
    print("Robustheit der 25-Delta-Auswahl gegen verdorbene Einzelpreise")
    print("=" * 78)
    spot, dte, atm_vol, skew = 500.0, 30, 0.25, 0.08

    sauber = _kette(spot, dte, atm_vol, skew)
    basis = leg_from_prices(sauber, spot, dte)
    print(f"\nSaubere Kette: ATM-Soll {atm_vol:.4f}")
    _melde("Saubere Kette liefert eine Leg", basis is not None, "leg=None")
    if not basis:
        return 1
    print(f"  gemessen: atm {basis['iv_atm']:.4f}  call {basis['call_iv']:.4f}  "
          f"put {basis['put_iv']:.4f}  skew {(basis['put_iv']-basis['call_iv'])*100:+.2f}")
    _melde("ATM-IV trifft den Sollwert (< 0,5 Vol-Punkte)",
           abs(basis["iv_atm"] - atm_vol) < 0.005,
           f"{basis['iv_atm']:.4f} vs {atm_vol:.4f}")
    _melde("Skew hat das richtige Vorzeichen (Puts teurer)",
           basis["put_iv"] > basis["call_iv"],
           f"put {basis['put_iv']:.4f} <= call {basis['call_iv']:.4f}")

    # ── Der eigentliche Test: einzelne Preise verderben ──────────────────────
    print("\nVerdorbene Einzelpreise (veralteter Print, viel zu teuer):")
    for typ, richtung, faktor in (("call", "hoch", 6.0), ("put", "runter", 6.0),
                                  ("call", "hoch", 20.0), ("put", "runter", 20.0)):
        kaputt, K = _verdirb(sauber, typ, richtung, faktor)
        r = leg_from_prices(kaputt, spot, dte)
        name = f"{typ} K={K:.0f} auf das {faktor:.0f}-fache"
        if r is None:
            _melde(f"{name}: Leg verworfen statt verfaelscht", True)
            continue
        d_atm = abs(r["iv_atm"] - basis["iv_atm"])
        d_skew = abs((r["put_iv"] - r["call_iv"]) - (basis["put_iv"] - basis["call_iv"])) * 100
        _melde(f"{name}: ATM bleibt stabil (< 0,5 Pkt)", d_atm < 0.005,
               f"atm {r['iv_atm']:.4f} statt {basis['iv_atm']:.4f}")
        _melde(f"{name}: Skew bleibt stabil (< 1,0 Pkt)", d_skew < 1.0,
               f"skew verschoben um {d_skew:.2f} Punkte")

    # ── Das ECHTE Fehlermuster ──────────────────────────────────────────────
    # Nachgestellt aus dem Live-Fall: eine niedrige ATM-Vol (Index-artig) und EIN
    # verdorbener Preis am Geld oder einen Strike darueber. Bei hoher IV wandert
    # der Delta-0,50-Punkt nach oben — der verdorbene Kontrakt landet dort exakt
    # und gewinnt den ATM-Pick gegen den echten ATM-Strike.
    # Mit der ALTEN Methode ergab z. B. "put K=505 x5" eine ATM-IV von 0,4487
    # statt 0,1300 — dasselbe Muster wie SPY mit 0,3845 statt ~0,13.
    print("")
    print("Verdorbener Preis am Geld (das Live-Muster, Index-artig 13 % ATM-Vol):")
    for atm_soll in (0.13, 0.25):
        kette = _kette(spot, dte, atm_soll, skew)
        ref = leg_from_prices(kette, spot, dte)
        if not ref:
            _melde(f"Basis-Kette mit ATM {atm_soll:.0%}", False, "leg=None")
            continue
        F_ = forward(spot, dte / 365.0)
        fehler = 0
        for versatz in (0, 5, 10):
            K = round(F_ / 5) * 5 + versatz
            for typ in ("call", "put"):
                for fak in (1.5, 2.0, 3.0, 5.0):
                    kaputt = [({**c, "px": c["px"] * fak}
                               if (c["K"] == K and c["typ"] == typ) else c) for c in kette]
                    r = leg_from_prices(kaputt, spot, dte)
                    if r is not None and abs(r["iv_atm"] - atm_soll) >= 0.005:
                        fehler += 1
                        print(f"      {typ} K={K:.0f} x{fak}: atm {r['iv_atm']:.4f} "
                              f"statt {atm_soll:.4f}")
        _melde(f"ATM {atm_soll:.0%}: 24 verdorbene Varianten, keine kippt den Anker",
               fehler == 0, f"{fehler} Varianten haben den ATM-Anker verschoben")

    # ── Kein ATM-Anker -> unbewertbar, KEIN Rueckfall auf einen Fluegel ──────
    print("\nOhne ATM-Anker:")
    T = dte / 365.0
    F = forward(spot, T)
    weit = [c for c in sauber if abs(math.log(c["K"] / F)) > 0.20]   # nur Fluegel
    r = leg_from_prices(weit, spot, dte)
    _melde("Kette ohne Strikes am Forward wird verworfen", r is None,
           f"leg={r} — es darf KEIN Rueckfall auf einen Fluegel geben")

    leer = leg_from_prices([], spot, dte)
    _melde("Leere Kette wird verworfen", leer is None, f"leg={leer}")

    # ── Der Forward-Anker muss wirken ───────────────────────────────────────
    print("\nForward-Anker:")
    _melde("forward() liegt ueber dem Spot (r > 0)", forward(spot, T) > spot,
           f"F={forward(spot, T)} <= S={spot}")
    erwartet = spot * math.exp(R * T)
    _melde("forward() == S*exp(R*T)", abs(forward(spot, T) - erwartet) < 1e-9)

    print("\n" + "=" * 78)
    if _ausfaelle:
        print(f"[FAIL] {len(_ausfaelle)} Abweichung(en):")
        for a in _ausfaelle:
            print(f"   - {a}")
        return 1
    print("[OK] Ein verdorbener Einzelpreis kippt weder ATM noch Skew.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
