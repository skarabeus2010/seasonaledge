"""Sitzungshelfer (V1d, Verträge B1.5–B1.6, B2.1, B5.1–B5.8) — Zwilling: `SA.boersenkalender` in
landing/js/boersenkalender.js. Entwurf mit Codex freigegeben: docs/review_prompts/2026-10-12_kalender_v1d_entwurf_v2.md.

Eine Offenheitsdefinition für alles: `exchange_holidays.is_trading_day` (Halbtage sind offene Sitzungen). Diese
Helfer ändern keine Verbraucher und nicht die Betriebsfunktionen `letzte_session`/`markt_offen`.

Verträge:
- Rechenbereich 1885-01-01 … 2100-12-31 wird hier selbst geprüft (`ValueError`); Suchen enden am Rand mit Fehler,
  keine feste Tagesgrenze.
- `einschliesslich` ist Pflicht und ein echtes `bool`; `n` eine ganze Zahl ≠ 0 (kein `bool`).
- Positionen: ungültige Angabe → Fehler; gültige, nicht vorhandene Position → `None`.
- `heute`/`zieltermin` verlangen einen Zeitpunkt MIT Zeitzone (naiv → `TypeError`); Börsenzone aus `_SCHLUSSZEIT`,
  CRYPTO/FOREX in UTC, Börse ohne Zone → `ValueError`.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from shared.exchange_holidays import (
    _SCHLUSSZEIT, NUMMERN_BIS_JAHR, NUMMERN_VON_JAHR, boerse_normalisieren, is_trading_day, kalender_status,
)

UNTEN = date(NUMMERN_VON_JAHR, 1, 1)
OBEN = date(NUMMERN_BIS_JAHR, 12, 31)
ZONEN = {b: z for b, (z, _, _) in _SCHLUSSZEIT.items()}
ZONEN.update({"CRYPTO": "UTC", "FOREX": "UTC"})
ZIELARTEN = ("heutige_sitzung_oder_naechste", "naechste_nach_heute")


def _b(boerse) -> str:
    return boerse_normalisieren(boerse)


def _datum(x) -> date:
    if isinstance(x, datetime) or not isinstance(x, (date, str)):
        raise TypeError("Datum muss date oder 'YYYY-MM-DD' sein: %r" % (x,))
    d = date.fromisoformat(x) if isinstance(x, str) else x
    if not UNTEN <= d <= OBEN:
        raise ValueError("Datum außerhalb des Rechenbereichs %s–%s: %s" % (UNTEN, OBEN, d))
    return d


def _bool(x, name):
    if type(x) is not bool:
        raise TypeError("%s muss True/False sein: %r" % (name, x))
    return x


def _ganz(x, name):
    if type(x) is not int:
        raise TypeError("%s muss eine ganze Zahl sein: %r" % (name, x))
    return x


def _schritt(d: date, richtung: int) -> date:
    n = d + timedelta(days=richtung)
    if not UNTEN <= n <= OBEN:
        raise ValueError("Keine Sitzung bis zum Rand des Rechenbereichs (%s)" % (OBEN if richtung > 0 else UNTEN))
    return n


def offen(datum, boerse) -> bool:
    return is_trading_day(_datum(datum), _b(boerse))


def sitzungen(boerse, von, bis) -> list[date]:
    """Geordnete offene Sitzungen von..bis (beide Enden eingeschlossen)."""
    b, a, e = _b(boerse), _datum(von), _datum(bis)
    if a > e:
        raise ValueError("von (%s) liegt nach bis (%s)" % (a, e))
    out, d = [], a
    while d <= e:
        if is_trading_day(d, b):
            out.append(d)
        d += timedelta(days=1)
    return out


def _suche(datum, boerse, einschliesslich, richtung) -> date:
    b, d = _b(boerse), _datum(datum)
    _bool(einschliesslich, "einschliesslich")
    if not einschliesslich:
        d = _schritt(d, richtung)
    while not is_trading_day(d, b):
        d = _schritt(d, richtung)
    return d


def naechste(datum, boerse, *, einschliesslich) -> date:
    """Erste offene Sitzung ab (einschließlich) bzw. streng nach `datum`."""
    return _suche(datum, boerse, einschliesslich, +1)


def vorherige(datum, boerse, *, einschliesslich) -> date:
    """Letzte offene Sitzung bis (einschließlich) bzw. streng vor `datum`."""
    return _suche(datum, boerse, einschliesslich, -1)


def verschiebe(sitzung, n, boerse) -> date:
    """n-te Sitzung nach (n > 0) bzw. vor (n < 0) einer offenen Sitzung — statt `tdom + offset` (B5.5)."""
    b, d = _b(boerse), _datum(sitzung)
    _ganz(n, "n")
    if n == 0:
        raise ValueError("n darf nicht 0 sein")
    if not is_trading_day(d, b):
        raise ValueError("Ausgangsdatum %s ist keine offene Sitzung" % d)
    richtung = 1 if n > 0 else -1
    for _ in range(abs(n)):
        d = _schritt(d, richtung)
        while not is_trading_day(d, b):
            d = _schritt(d, richtung)
    return d


def _monat_pruefen(j, m):
    _ganz(j, "Jahr")
    _ganz(m, "Monat")
    if not NUMMERN_VON_JAHR <= j <= NUMMERN_BIS_JAHR:
        raise ValueError("Jahr außerhalb des Rechenbereichs: %r" % j)
    if not 1 <= m <= 12:
        raise ValueError("Monat außerhalb 1–12: %r" % m)


def _monatsende(j, m) -> date:
    return (date(j + 1, 1, 1) if m == 12 else date(j, m + 1, 1)) - timedelta(days=1)


def nte_im_monat(j, m, n, boerse):
    """n-te offene Sitzung (n ≥ 1) eines Monats; None, wenn es sie nicht gibt."""
    _monat_pruefen(j, m)
    _ganz(n, "Position")
    if n < 1:
        raise ValueError("Position muss ≥ 1 sein: %r" % n)
    s = sitzungen(boerse, date(j, m, 1), _monatsende(j, m))
    return s[n - 1] if n <= len(s) else None


def nte_von_hinten_im_monat(j, m, n, boerse):
    """n-te offene Sitzung von hinten (1 = letzte) eines Monats; None, wenn es sie nicht gibt."""
    _monat_pruefen(j, m)
    _ganz(n, "Position")
    if n < 1:
        raise ValueError("Position muss ≥ 1 sein: %r" % n)
    s = sitzungen(boerse, date(j, m, 1), _monatsende(j, m))
    return s[-n] if n <= len(s) else None


def nte_im_jahr(j, n, boerse):
    """n-te offene Sitzung (n ≥ 1) eines Jahres; None, wenn es sie nicht gibt."""
    _monat_pruefen(j, 1)
    _ganz(n, "Position")
    if n < 1:
        raise ValueError("Position muss ≥ 1 sein: %r" % n)
    s = sitzungen(boerse, date(j, 1, 1), date(j, 12, 31))
    return s[n - 1] if n <= len(s) else None


def _utc_text(t: datetime) -> str:
    u = t.astimezone(timezone.utc)
    return u.strftime("%Y-%m-%dT%H:%M:%S.") + "%03dZ" % (u.microsecond // 1000)


def heute(boerse, jetzt) -> dict:
    """Börsendatum zum Zeitpunkt `jetzt` (datetime MIT tzinfo) in der Börsenzone; CRYPTO/FOREX in UTC (B1.5)."""
    b = _b(boerse)
    if not isinstance(jetzt, datetime) or jetzt.tzinfo is None or jetzt.utcoffset() is None:
        raise TypeError("jetzt muss ein datetime mit Zeitzone sein: %r" % (jetzt,))
    if b not in ZONEN:
        raise ValueError("Keine Zeitzone für Börse %s" % b)
    lokal = jetzt.astimezone(ZoneInfo(ZONEN[b]))
    d = _datum(lokal.date())
    return {"boerse": b, "datum": d.isoformat(), "zeitzone": ZONEN[b], "zeitpunkt_utc": _utc_text(jetzt)}


def zieltermin(boerse, jetzt, *, art) -> dict:
    """Zieltermin (B5.1/B5.3/B5.6): heutige Sitzung oder ihr echter Nachfolger; geschlossen → nächste offene."""
    if art not in ZIELARTEN:
        raise ValueError("unbekannte Art %r" % (art,))
    h = heute(boerse, jetzt)                 # einmal erfasst
    b, d = h["boerse"], date.fromisoformat(h["datum"])
    if is_trading_day(d, b):
        ziel = d if art == "heutige_sitzung_oder_naechste" else naechste(d, b, einschliesslich=False)
    else:
        ziel = naechste(d, b, einschliesslich=True)
    return {"boerse": b, "referenzzeitpunkt": h["zeitpunkt_utc"], "zeitzone": h["zeitzone"], "heute": h["datum"],
            "datum": ziel.isoformat(), "kalenderstatus": kalender_status(b, ziel.year), "art": art}


def sitzung_info(datum, boerse) -> dict:
    """{offen, halbtag, halbtag_status, schlusszeit, zeitzone, sitzung} — halbtag None heißt: unbekannt."""
    from shared import boersenereignisse as BE
    b, d = _b(boerse), _datum(datum)
    status = BE.halbtag_status(b, d.year)
    leer = {"offen": False, "halbtag": None, "halbtag_status": status, "schlusszeit": None, "zeitzone": None,
            "sitzung": None}
    if not is_trading_day(d, b):
        return leer
    for e in BE.ereignisse(b, d.year):
        if e.art == "halbtag" and e.wirksam == d:
            return {"offen": True, "halbtag": True, "halbtag_status": status, "schlusszeit": e.schlusszeit,
                    "zeitzone": e.zeitzone, "sitzung": e.sitzung}
    return dict(leer, offen=True, halbtag=False if status == "belegt" else None)
