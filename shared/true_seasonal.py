"""Williams True Seasonal — Saisonkurve ohne Zukunftswissen.

Quelle (Primär): Larry Williams, „Larry Williams Indicators“ (LNL Publishing 2020, S. 15):
  „all other seasonal studies 'run the numbers' then curve fit them to the past! The seasonal pattern they show for
  2010 includes data from 2011, 2012, 2013, etc... My 'True Seasonal' uses only data known up to the current time and
  then is pushed forward on charts for the next year.“

Rechnung (Plan v3, docs/review_prompts/2026-10-16_true_seasonal_plan_v3.md, Codex-Freigabe): Kurve für Zieljahr Y =
ungerundeter Mittelwert der normierten Jahreskurven (`build_year_data` → `full_365`) aller VOLLSTÄNDIGEN Jahre im
Kalenderfenster [Y − N, Y − 1] (N = None: alle Vorjahre). Williams' genaue Skalierung ist nicht veröffentlicht.

„Vollständig“ ist bis zur Kalender-Umstellung V4 eine benannte HEURISTIK, keine Sitzungsprüfung: vergangenes Jahr,
erste Kurszeile ≤ Tag 7, letzte ≥ Tag 362, kein Abstand zweier Kurszeilen > 14 Kalendertage. Einzelne fehlende
Sitzungen erkennt sie nicht (die Seite interpoliert sie); Jahre mit langen Schließungen (NYSE 1914) fallen vorsorglich
heraus. Geprüft gegen alle 13 Kalender des Repos 1990–2030: 0 von 533 Börsenjahren verworfen (Codex R3).

Gegenstück: landing/js/seasonal-compute.js (jahrVollstaendig, trueSeasonalJahre, mittelKurve, monatsAenderungen,
vergleich12, rueckblick). Wächter: scripts/verify_seasonal_twins.py.
"""
from __future__ import annotations

import math

JAHRESANFANG_GRENZE = 7
JAHRESENDE_VOLL = 362
LUECKE_MAX = 14
MONATSENDE_SLOT = (31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365)


def jahr_vollstaendig(yd, jahr: int, stichtag_jahr: int) -> bool:
    t = list(yd.get("days") or []) if yd else []
    if not t:
        return False
    if not int(jahr) < int(stichtag_jahr):
        return False
    if not t[0] <= JAHRESANFANG_GRENZE:
        return False
    if not min(t[-1], 365) >= JAHRESENDE_VOLL:
        return False
    for a, b in zip(t, t[1:]):
        if not 0 < b - a <= LUECKE_MAX:
            return False
    return True


def true_seasonal_mindest(fenster_n: int | None) -> int:
    return 10 if fenster_n is None else math.ceil(0.8 * fenster_n)


def true_seasonal_jahre(year_data: dict, ziel_jahr: int, fenster_n: int | None) -> list[int]:
    von = -math.inf if fenster_n is None else ziel_jahr - fenster_n
    return sorted(int(j) for j, yd in year_data.items()
                  if von <= int(j) < ziel_jahr and jahr_vollstaendig(yd, int(j), ziel_jahr))


def mittel_kurve(year_data: dict, jahre: list[int]) -> list[float] | None:
    if not jahre:
        return None
    return [sum(year_data[j]["full_365"][d] for j in jahre) / len(jahre) for d in range(365)]


def true_seasonal(year_data: dict, ziel_jahr: int, fenster_n: int | None = None,
                  min_jahre: int | None = None) -> tuple[list[float] | None, list[int]]:
    """(Kurve oder None, benutzte Jahre). Mindestmenge: min_jahre, sonst true_seasonal_mindest(fenster_n)."""
    jahre = true_seasonal_jahre(year_data, ziel_jahr, fenster_n)
    mindest = true_seasonal_mindest(fenster_n) if min_jahre is None else min_jahre
    if len(jahre) < mindest:
        return None, jahre
    return mittel_kurve(year_data, jahre), jahre


def monats_aenderungen(kurve) -> list[float] | None:
    out, vor = [], 100.0
    for e in MONATSENDE_SLOT:
        v = kurve[e - 1]
        if not (v is not None and math.isfinite(v) and v > 0 and vor > 0):
            return None
        out.append(math.log(v / vor))
        vor = v
    return out


def vergleich12(ist, modell) -> dict | None:
    a = monats_aenderungen(ist)
    b = monats_aenderungen(modell) if modell is not None else None
    if a is None or b is None:
        return None
    ma, mb = sum(x / 12 for x in a), sum(x / 12 for x in b)
    sab = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    saa = sum((x - ma) ** 2 for x in a)
    sbb = sum((y - mb) ** 2 for y in b)
    treffer = sum(1 for x, y in zip(a, b) if x != 0 and y != 0 and (x > 0) == (y > 0))
    return {"r": sab / math.sqrt(saa * sbb) if saa > 0 and sbb > 0 else None,
            "treffer": treffer, "immerPositiv": sum(1 for x in a if x > 0)}


def rueckblick(year_data: dict, stichtag_jahr: int, fenster_n: int | None) -> dict:
    alle = sorted(int(j) for j in year_data)
    unten = -math.inf if fenster_n is None else stichtag_jahr - fenster_n
    mindest = true_seasonal_mindest(fenster_n)
    zeilen = []
    for y in alle:
        if y < unten or y >= stichtag_jahr or not jahr_vollstaendig(year_data[y], y, stichtag_jahr):
            continue
        ts_jahre = true_seasonal_jahre(year_data, y, fenster_n)
        if len(ts_jahre) < mindest:
            continue
        von = -math.inf if fenster_n is None else y - fenster_n
        r_jahre = [j for j in alle if von <= j <= y]
        ist = year_data[y]["full_365"]
        zeilen.append({"jahr": y, "nTs": len(ts_jahre), "nRueck": len(r_jahre),
                       "ts": vergleich12(ist, mittel_kurve(year_data, ts_jahre)),
                       "rueck": vergleich12(ist, mittel_kurve(year_data, r_jahre))})

    def zusammen(feld):
        rs = [z[feld]["r"] for z in zeilen if z[feld] and z[feld]["r"] is not None]
        tr = [z[feld]["treffer"] for z in zeilen if z[feld]]
        return {"rMittel": sum(rs) / len(rs) if rs else None, "rPositiv": sum(1 for r in rs if r > 0),
                "nGueltig": len(rs), "trefferMittel": sum(tr) / len(tr) if tr else None}

    ip = [z["ts"]["immerPositiv"] for z in zeilen if z["ts"]]
    return {"jahre": zeilen, "ts": zusammen("ts"), "rueck": zusammen("rueck"),
            "immerPositivMittel": sum(ip) / len(ip) if ip else None, "mindest": mindest}
