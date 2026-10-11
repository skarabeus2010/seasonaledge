"""US-Produkttermine: Monatsverfall (OPEX) und VIX-Abrechnung (V1c-2, Vertrag B4 8–9).

Entwurf mit Codex in 6 Runden freigegeben: docs/review_prompts/2026-10-12_kalender_v1c2_entwurf.md … _v6.md.

Regeln (nur im belegten Regelbereich, davor KEINE Ereignisse — die frühen Grenzen sind nicht belegbar):
  OPEX ab 2015-02 (SEC/OCC 34-69772, Grenztermin 01.02.2015; OCC By-Laws Art. I):
    regeltermin = 3. Freitag; verfallstermin = regeltermin, ist er kein Geschäftstag, der vorangehende Geschäftstag
    (rekursiv); formaler_verfall = verfallstermin (Samstagsverfälle liegen vor dem Bereich; grandfathered Serien
    nicht modelliert); triple_witching = Monat 3/6/9/12.
  VIX ab Kontrakt 2015-09 (CFE SR-CFE-2015-023, Regelbuch S. 170):
    referenzfreitag = 3. Freitag des Folgemonats; nominal = referenzfreitag − 30 Tage (Mittwoch);
    settlement = nominal; ist nominal ODER referenzfreitag kein Geschäftstag: der Geschäftstag unmittelbar vor
    nominal. handelsende_futures = settlement (Ende am Abrechnungsmorgen); verfall_optionen = settlement;
    handelsende_optionen = Geschäftstag vor verfall_optionen.
  Geschäftstag = Regelsitzung (RTH) der Cboe-Optionsbörse; Annahme: = NYSE-Handelstag aus dem Ereigniskatalog V1c-1.

Belege (shared/produkttermine_listung.py) und Einstufung je Feldgruppe, erst bei der Abfrage mit Pflicht-Prüfdatum:
  Monat in der Belegreihe → `belegt` (Wert der Quelle); sonst Regeltermin > pruefdatum → `projektion`;
  sonst `luecke`: Felder None, Grund `nicht_belegt`, in `abdeckung()` gemeldet. Gespeichert/gehasht werden nur
  Fakten (Regeln + Belege), nie die Einstufung — die hinge am Abfragetag.
"""
from __future__ import annotations

import functools
import hashlib
import json
from datetime import date, timedelta

from shared.produkttermine_listung import BELEGREIHEN

OPEX_AB = (2015, 2)
VIX_AB = (2015, 9)
BIS = (2100, 12)
VIX_BIS = (2100, 11)   # Dezember 2100 bräuchte den Referenzfreitag 2101 — außerhalb des Kalenderbereichs
ARTEN = ("opex", "vix")
REGELSTAND_OPEX = "OCC Art. I, Freitagsverfall ab 2015-02 (SEC 34-69772)"
REGELSTAND_VIX = "CFE SR-CFE-2015-023 (ODER-Regel, Handelsende am Settlementtag)"
TRIPLE_MONATE = (3, 6, 9, 12)
# Geschäftstag = Cboe-Regelsitzung; als NYSE-Handelstag angenommen (Codex V1c-2 R1: maschinenlesbar am Objekt)
KALENDERANNAHME = "cboe_rth_gleich_nyse"
KALENDERSTATUS = "annahme"


def _offen_nyse(d: date) -> bool:
    from shared.exchange_holidays import is_trading_day
    return is_trading_day(d, "NYSE")


def _vorher(d: date, offen) -> date:
    """Geschäftstag unmittelbar vor d (rekursiv über geschlossene Tage)."""
    d -= timedelta(days=1)
    while not offen(d):
        d -= timedelta(days=1)
    return d


def _dritter_freitag(j: int, m: int) -> date:
    d = date(j, m, 15)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def _monate(von: tuple, bis: tuple):
    j, m = von
    while (j, m) <= bis:
        yield j, m
        j, m = (j + 1, 1) if m == 12 else (j, m + 1)


def _monat_parsen(x) -> tuple:
    if not isinstance(x, str) or len(x) != 7 or x[4] != "-":
        raise ValueError("Monat nicht im Format YYYY-MM: %r" % (x,))
    j, m = int(x[:4]), int(x[5:])
    if not 1 <= m <= 12:
        raise ValueError("Monat außerhalb 1–12: %r" % (x,))
    return j, m


def _datum(x) -> date:
    if isinstance(x, date):
        return x
    if isinstance(x, str):
        return date.fromisoformat(x)
    raise TypeError("pruefdatum muss ein Datum oder 'YYYY-MM-DD' sein: %r" % (x,))


# ── Fakten (ohne Prüfdatum) ──────────────────────────────────────────────────────────────────────────────────
def opex_regel(j: int, m: int, offen=_offen_nyse) -> dict:
    regel = _dritter_freitag(j, m)
    verfall = regel if offen(regel) else _vorher(regel, offen)
    return {"regeltermin": regel, "verfallstermin": verfall}


def vix_regel(j: int, m: int, offen=_offen_nyse) -> dict:
    fj, fm = (j + 1, 1) if m == 12 else (j, m + 1)
    ref = _dritter_freitag(fj, fm)
    nominal = ref - timedelta(days=30)
    settlement = nominal if (offen(nominal) and offen(ref)) else _vorher(nominal, offen)
    return {"referenzfreitag": ref, "nominal": nominal, "settlement": settlement,
            "handelsende_optionen": _vorher(settlement, offen)}


def _einstufen(monat: str, reihe: str, regelwert: date, pruefdatum: date, belege) -> tuple:
    """→ (wert, listung, grund). belegt: Wert der Quelle; projektion: Regelwert; luecke: None."""
    beleg = belege[reihe]["monate"].get(monat)
    if beleg is not None:
        return date.fromisoformat(beleg), "belegt", None
    if regelwert > pruefdatum:
        return regelwert, "projektion", None
    return None, "luecke", "nicht_belegt"


def _quelle(listung: str, reihe: str):
    """Herkunft einer Feldgruppe: die Belegreihe, die Regel (Projektion) oder None (Lücke)."""
    return reihe if listung == "belegt" else ("regel" if listung == "projektion" else None)


def _iso(d):
    return None if d is None else d.isoformat()


def _kv() -> str:
    from shared.boersenereignisse import _kalenderversion_gesamt
    return _kalenderversion_gesamt()


def opex_ereignis(j: int, m: int, pruefdatum, offen=_offen_nyse, belege=None):
    """Ereignis-Dict oder None (Monat vor OPEX_AB oder Lücke)."""
    if (j, m) < OPEX_AB:
        return None
    belege = BELEGREIHEN if belege is None else belege
    monat = "%04d-%02d" % (j, m)
    r = opex_regel(j, m, offen)
    verfall, listung, grund = _einstufen(monat, "SPX_STANDARD", r["verfallstermin"], _datum(pruefdatum), belege)
    if listung == "luecke":
        return None
    return {
        "ereignis_id": "US_OPT:opex.monat:" + monat, "produkt": "US_OPT", "art": "opex", "verfallsmonat": monat,
        "regeltermin": _iso(r["regeltermin"]), "verfallstermin": _iso(verfall), "formaler_verfall": _iso(verfall),
        "ersatzgrund": "keiner" if verfall == r["regeltermin"] else "feiertag",
        "triple_witching": m in TRIPLE_MONATE, "listung": listung, "grund": grund,
        "regel_abweichung": verfall != r["verfallstermin"],
        "regelstand": REGELSTAND_OPEX, "quelle": _quelle(listung, "SPX_STANDARD"),
        "kalenderannahme": KALENDERANNAHME, "kalenderstatus": KALENDERSTATUS,
        "kalenderversion": _kv(),
    }


def vix_ereignis(j: int, m: int, pruefdatum, offen=_offen_nyse, belege=None):
    """Ereignis-Dict oder None (Kontrakt vor VIX_AB oder beide Feldgruppen Lücke)."""
    if (j, m) < VIX_AB:
        return None
    belege = BELEGREIHEN if belege is None else belege
    monat = "%04d-%02d" % (j, m)
    p = _datum(pruefdatum)
    r = vix_regel(j, m, offen)
    sett, l_vx, g_vx = _einstufen(monat, "VX", r["settlement"], p, belege)
    v_opt, l_opt, g_opt = _einstufen(monat, "VIX_OPT", r["settlement"], p, belege)
    if l_vx == "luecke" and l_opt == "luecke":
        return None
    he_opt = None if v_opt is None else _vorher(v_opt, offen)
    return {
        "ereignis_id": "US_VIX:vix.settlement:" + monat, "produkt": "US_VIX", "art": "vix", "kontraktmonat": monat,
        "referenzfreitag": _iso(r["referenzfreitag"]), "nominal": _iso(r["nominal"]),
        "ersatzgrund": "keiner" if r["settlement"] == r["nominal"] else "feiertag",
        "settlement": _iso(sett), "handelsende_futures": _iso(sett), "listung_futures": l_vx, "grund_futures": g_vx,
        "verfall_optionen": _iso(v_opt), "handelsende_optionen": _iso(he_opt), "listung_optionen": l_opt,
        "grund_optionen": g_opt, "quelle_futures": _quelle(l_vx, "VX"), "quelle_optionen": _quelle(l_opt, "VIX_OPT"),
        "kalenderannahme": KALENDERANNAHME, "kalenderstatus": KALENDERSTATUS,
        "regel_abweichung": (sett is not None and sett != r["settlement"])
                            or (v_opt is not None and v_opt != r["settlement"]),
        "regelstand": REGELSTAND_VIX, "kalenderversion": _kv(),
    }


def produkttermine(von: str, bis: str, art: str, *, pruefdatum, offen=_offen_nyse, belege=None) -> list[dict]:
    """Ereignisse eines Produkts für die Monate von..bis (YYYY-MM). `pruefdatum` ist Pflicht (kein Standardwert)."""
    if art not in ARTEN:
        raise ValueError("unbekannte Art %r" % (art,))
    a, b = _monat_parsen(von), _monat_parsen(bis)
    grenze = BIS if art == "opex" else VIX_BIS
    if b > grenze:
        raise ValueError("Monat nach dem Rechenbereich %04d-%02d" % grenze)
    f = opex_ereignis if art == "opex" else vix_ereignis
    out = []
    for j, m in _monate(a, b):
        e = f(j, m, pruefdatum, offen, belege)
        if e is not None:
            out.append(e)
    return out


def abdeckung(*, pruefdatum, offen=_offen_nyse, belege=None) -> dict:
    """Abdeckungslücken je Feldgruppe (Monat im Regelbereich, nicht belegt, Termin ≤ pruefdatum) + Grenzen."""
    belege = BELEGREIHEN if belege is None else belege
    p = _datum(pruefdatum)
    luecken = {"SPX_STANDARD": [], "VX": [], "VIX_OPT": []}
    for j, m in _monate(OPEX_AB, BIS):
        monat = "%04d-%02d" % (j, m)
        if _einstufen(monat, "SPX_STANDARD", opex_regel(j, m, offen)["verfallstermin"], p, belege)[1] == "luecke":
            luecken["SPX_STANDARD"].append(monat)
    for j, m in _monate(VIX_AB, VIX_BIS):
        monat = "%04d-%02d" % (j, m)
        s = vix_regel(j, m, offen)["settlement"]
        for reihe in ("VX", "VIX_OPT"):
            if _einstufen(monat, reihe, s, p, belege)[1] == "luecke":
                luecken[reihe].append(monat)
    return {"pruefdatum": p.isoformat(), "nicht_modelliert": {"opex_vor": "%04d-%02d" % OPEX_AB,
                                                              "vix_vor": "%04d-%02d" % VIX_AB},
            "luecken": luecken,
            "datenstand": {k: v["datenstand"] for k, v in belege.items()}}


@functools.lru_cache(maxsize=None)
def produktversion() -> str:
    """SHA-256 über die Fakten: Regeltermine aller Monate + Belegreihen (ohne Einstufung, ohne Prüfdatum)."""
    regel = {}
    for j, m in _monate(OPEX_AB, BIS):
        r = opex_regel(j, m)
        regel["opex:%04d-%02d" % (j, m)] = [r["regeltermin"].isoformat(), r["verfallstermin"].isoformat(),
                                            m in TRIPLE_MONATE]
    for j, m in _monate(VIX_AB, VIX_BIS):
        r = vix_regel(j, m)
        regel["vix:%04d-%02d" % (j, m)] = [r[k].isoformat() for k in ("referenzfreitag", "nominal", "settlement",
                                                                      "handelsende_optionen")]
    # alle Produktregeln: Termine je Monat, Grenzen, Triple-Monate, Kalenderannahme, Regelstände, Belege
    kanon = json.dumps({"regel": regel, "belege": BELEGREIHEN, "regelstand": [REGELSTAND_OPEX, REGELSTAND_VIX],
                        "grenzen": [OPEX_AB, VIX_AB, BIS, VIX_BIS], "triple": TRIPLE_MONATE,
                        "kalender": [KALENDERANNAHME, KALENDERSTATUS]},
                       sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(kanon.encode("utf-8")).hexdigest()
