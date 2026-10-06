"""
Wahlen und Börse — Rechenkern der Ereignisstudie (Python-Referenz).

Plan: docs/review_prompts/2026-10-06_wahlen_plan.md (Codex-Freigabe nach 8 Runden),
Doku: docs/WAHLEN.md. Abschnitte 10–14 des Plans gelten vor den früheren.

Vertrag (Plan Abschnitt 3, 10, 11):
  * Anker t0 = letzter Kurs am oder vor dem Wahltermin (`anker`). Abstand Wahltag − t0
    höchstens 4 Kalendertage. Ist der Wahltag laut belegtem Kalender eine Sitzung, fehlt
    aber in den Kursen, wird die Wahl ausgeschlossen (nicht der Vortag genommen).
  * Offsets zählen Kurszeilen der jeweiligen Reihe (vor 1953 mit Samstagen bei ^GSPC,
    ohne bei ^DJI vor 1928 — dokumentiert in docs/WAHLEN.md).
  * Gültigkeit je Offset (`pfad`): ab der ersten Unstimmigkeit — fehlende erwartete Sitzung,
    Kurs an einer Nicht-Sitzung (belegter Kalender) oder Lücke > 4 Kalendertage (unbelegter
    Kalender) — sind alle weiter vom Anker entfernten Offsets in dieser Richtung ungültig.
  * Live (`live_pfad`): künftiges t0 ist eine projizierte Sitzung; vorhandene Kurse werden
    über die Zahl erwarteter Sitzungen bis t0 positioniert, die Zukunft ist None.
  * Exportiert werden Kurse, nicht Renditen; Umbasierung und Renditequotienten macht der
    Browser bzw. `fenster_rendite` hier als Referenz.
"""
from __future__ import annotations

import bisect
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Optional

REPO = Path(__file__).resolve().parent.parent
WAHLEN_JSON = REPO / "landing" / "data" / "elections.json"
AUSNAHMEN_JSON = REPO / "landing" / "data" / "election_calendar_exceptions.json"

FENSTER = 60          # gespeicherte Offsets −60…+60
MAX_ANKER_ABSTAND = 4  # Kalendertage zwischen Wahltermin und t0
MAX_LUECKE = 4         # Kalendertage zwischen zwei Kurszeilen bei unbelegtem Kalender

# Grund-Codes (Browser übersetzt sie)
G_VOR_DATENBEGINN = "vor_datenbeginn"
G_NACH_DATENENDE = "nach_datenende"
G_ZUKUNFT = "zukunft"
G_FEHLENDE_SITZUNG = "fehlende_sitzung"
G_NICHT_SITZUNG = "kurs_an_nicht_sitzung"
G_LUECKE = "ungeklaerte_luecke"


def us_wahltag(jahr: int) -> date:
    """Erster Dienstag nach dem ersten Montag im November (= Pseudotermin in Kontrolljahren)."""
    d = date(jahr, 11, 2)
    while d.weekday() != 1:
        d += timedelta(days=1)
    return d


# ── Daten laden ─────────────────────────────────────────────────────────────

def lade_wahlen() -> dict:
    return json.loads(WAHLEN_JSON.read_text(encoding="utf-8"))


def lade_kalender(calendar_id: str = "NYSE") -> Callable[[date], Optional[bool]]:
    """Sitzungsfunktion: True = erwartete Sitzung, False = keine, None = Kalender unbelegt.

    Belegt ab `calendar_documented_from` (NYSE: 1971): Regelkalender aus
    shared/nyse_holidays.py plus belegte Ausnahmen (Wahltage, Sonderschließungen).
    """
    from shared.nyse_holidays import get_nyse_holidays

    doc = json.loads(AUSNAHMEN_JSON.read_text(encoding="utf-8"))
    ab = date.fromisoformat(doc["calendar_documented_from"][calendar_id])
    zu = {date.fromisoformat(x["date"]) for x in doc["exceptions"]
          if x["calendar_id"] == calendar_id and x.get("closed")}
    cache: dict[int, set] = {}

    def ist_sitzung(d: date) -> Optional[bool]:
        if d < ab:
            return None
        if d.year not in cache:
            cache[d.year] = get_nyse_holidays(d.year, d.year)
        return d.weekday() < 5 and d not in cache[d.year] and d not in zu

    return ist_sitzung


# ── Kern ────────────────────────────────────────────────────────────────────

def _d(s: str) -> date:
    return date.fromisoformat(s[:10])


def _fehlende_sitzung(a: date, b: date, ist_sitzung) -> Optional[date]:
    """Erste erwartete Sitzung strikt zwischen a und b (beide belegt), sonst None."""
    x = a + timedelta(days=1)
    while x < b:
        if ist_sitzung(x):
            return x
        x += timedelta(days=1)
    return None


def _schritt_ok(a: date, b: date, ist_sitzung) -> Optional[str]:
    """Prüft den Übergang zwischen zwei benachbarten Kurszeilen a < b. None = ok, sonst Grund.

    Beide Endpunkte werden geprüft (Codex R1: rückwärts ist `a` die neu aufgenommene Zeile),
    fehlende belegte Sitzungen auch über die Abdeckungsgrenze hinweg, die Lückenregel nur dort,
    wo mindestens ein Endpunkt unbelegt ist.
    """
    sa, sb = ist_sitzung(a), ist_sitzung(b)
    if sa is False or sb is False:
        return G_NICHT_SITZUNG
    if _fehlende_sitzung(a, b, ist_sitzung):
        return G_FEHLENDE_SITZUNG
    if (sa is None or sb is None) and (b - a).days > MAX_LUECKE:
        return G_LUECKE
    return None


def anker(daten: list[str], termin: date, ist_sitzung) -> tuple[Optional[int], Optional[str]]:
    """Index des Referenzschlusses t0 oder (None, Grund)."""
    i = bisect.bisect_right(daten, termin.isoformat()) - 1
    if i < 0:
        return None, G_VOR_DATENBEGINN
    t0 = _d(daten[i])
    if (termin - t0).days > MAX_ANKER_ABSTAND:
        return None, "anker_zu_weit"
    # Belegter Kalender: zwischen t0 und Wahltag (einschliesslich) darf keine erwartete Sitzung fehlen.
    if ist_sitzung(termin) is not None:
        x = t0 + timedelta(days=1)
        while x <= termin:
            if ist_sitzung(x):
                return None, "kurs_am_wahltag_fehlt"
            x += timedelta(days=1)
        if ist_sitzung(t0) is False:
            return None, G_NICHT_SITZUNG
    return i, None


def pfad(daten: list[str], closes: list[float], i0: int, ist_sitzung, n: int = FENSTER) -> dict:
    """Kurse −n…+n um den Anker i0, mit Gültigkeit je Offset."""
    c: list[Optional[float]] = [None] * (2 * n + 1)
    tage: list[Optional[int]] = [None] * (2 * n + 1)   # Kalendertage relativ zu t0 (Datum je Offset)
    grund: dict[int, str] = {}
    t0 = _d(daten[i0])
    c[n], tage[n] = closes[i0], 0
    for richtung in (-1, 1):
        kaputt: Optional[str] = None
        for k in range(1, n + 1):
            j = i0 + richtung * k
            off = richtung * k
            if j < 0:
                grund[off] = G_VOR_DATENBEGINN
                continue
            if j >= len(daten):
                grund[off] = G_NACH_DATENENDE
                continue
            tage[n + off] = (_d(daten[j]) - t0).days
            if kaputt is None:
                a, b = (j, j + 1) if richtung < 0 else (j - 1, j)
                kaputt = _schritt_ok(_d(daten[a]), _d(daten[b]), ist_sitzung)
            if kaputt:
                grund[off] = kaputt
                continue
            c[n + off] = closes[j]
    return {"t0": daten[i0], "c": c, "tage": tage, "grund": grund,
            "kalender_belegt": ist_sitzung(_d(daten[max(0, i0 - n)])) is not None}


def live_pfad(daten: list[str], closes: list[float], termin: date, ist_sitzung,
              stichtag: date, n: int = FENSTER) -> dict:
    """Pfad für einen künftigen Termin. t0 = projizierte Sitzung (letzte erwartete ≤ Termin).

    Offsets zählen hier ERWARTETE Sitzungen des belegten Kalenders, nicht Kurszeilen: so verschiebt
    eine fehlende Zeile die übrigen nicht. Sitzungen ≤ `stichtag` (letzte abgeschlossene Session)
    ohne Kurs sind `fehlende_sitzung`, nur Sitzungen danach `zukunft` (Codex R1).
    """
    def schritt(x: date, r: int) -> date:
        x += timedelta(days=r)
        while True:
            s_ = ist_sitzung(x)
            if s_ is None:
                raise ValueError("Live-Pfad braucht einen belegten Kalender")
            if s_:
                return x
            x += timedelta(days=r)

    t0 = termin if ist_sitzung(termin) else schritt(termin, -1)
    kurs = {d: c for d, c in zip(daten, closes)}
    c: list[Optional[float]] = [None] * (2 * n + 1)
    tage: list[Optional[int]] = [None] * (2 * n + 1)
    grund: dict[int, str] = {}
    for richtung in (-1, 1):
        x = t0
        for k in range(0 if richtung < 0 else 1, n + 1):
            if k:
                x = schritt(x, richtung)
            off = richtung * k
            tage[n + off] = (x - t0).days
            if x > stichtag:
                grund[off] = G_ZUKUNFT
            elif x.isoformat() in kurs:
                c[n + off] = kurs[x.isoformat()]
            else:
                grund[off] = G_FEHLENDE_SITZUNG
    lo, hi = (t0 + timedelta(days=tage[0])).isoformat(), min(stichtag, t0).isoformat()
    fremd = [d for d in daten if lo <= d <= hi and ist_sitzung(_d(d)) is False]
    return {"t0": t0.isoformat(), "t0_projiziert": True, "stichtag": stichtag.isoformat(),
            "letzter_kurs": daten[-1] if daten else None, "c": c, "tage": tage, "grund": grund,
            "kurse_an_nicht_sitzungen": fremd, "kalender_belegt": True}


def fenster_rendite(p: dict, x: int, y: int, n: int = FENSTER) -> Optional[dict]:
    """Referenz für den Browser: Renditen in Prozent, None wenn das Fenster nicht vollständig gültig ist."""
    werte = p["c"][n - x: n + y + 1]
    if len(werte) != x + y + 1 or any(v is None for v in werte):
        return None
    pm, p0, pp = werte[0], werte[x], werte[-1]
    return {"vorlauf": 100 * (p0 / pm - 1), "nachlauf": 100 * (pp / p0 - 1), "fenster": 100 * (pp / pm - 1)}


def kontrolljahre(jahr: int) -> list[int]:
    """US-Referenz: die beiden angrenzenden ungeraden Jahre (keine reguläre Bundeswahl)."""
    return [jahr - 1, jahr + 1]


def studie_fuer_reihe(wahl: dict, daten: list[str], closes: list[float], ist_sitzung,
                      heute_letzte_session: date) -> dict:
    """Pfad + Kontrollpfade einer US-Wahl für eine Kursreihe."""
    termin = date.fromisoformat(wahl["date"])
    aus: dict = {}
    if termin > heute_letzte_session:
        try:
            aus["pfad"] = live_pfad(daten, closes, termin, ist_sitzung, heute_letzte_session)
        except ValueError as e:
            aus["ausgeschlossen"] = str(e)
    else:
        i0, g = anker(daten, termin, ist_sitzung)
        if i0 is None:
            aus["ausgeschlossen"] = g
        else:
            aus["pfad"] = pfad(daten, closes, i0, ist_sitzung)
    kontrollen = []
    for kj in kontrolljahre(termin.year):
        pt = us_wahltag(kj)
        eintrag = {"jahr": kj, "pseudotermin": pt.isoformat()}
        if pt > heute_letzte_session:
            eintrag["ausgeschlossen"] = G_ZUKUNFT
        else:
            i0, g = anker(daten, pt, ist_sitzung)
            if i0 is None:
                eintrag["ausgeschlossen"] = g
            else:
                eintrag["pfad"] = pfad(daten, closes, i0, ist_sitzung)
        kontrollen.append(eintrag)
    aus["kontrollen"] = kontrollen
    return aus
