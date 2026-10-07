#!/usr/bin/env python3
"""
verify_wahlen_build.py — Wächter für den Rechenkern shared/elections.py und scripts/build_wahlen.py.

Pflichtfälle aus dem freigegebenen Plan (docs/review_prompts/2026-10-06_wahlen_plan.md):
offener / geschlossener / fehlender Wahltag, Sonntag, einzelne fehlende Sitzung, Lücke bei +45
und Datenende bei +25 (je 20/20 gegen 60/60), lange Schließung und historischer Samstag bei
unbelegtem Kalender, Kurs an einer Nicht-Sitzung, Anker zu weit, künftiges t0 (Live) und eine
handgerechnete Mini-Reihe für die Renditen. Dazu ein Durchlauf von build_wahlen.baue() mit
synthetischen Kursen auf dem echten Kalender.

    py -3.14 scripts/verify_wahlen_build.py      # Exit 0 = grün
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from shared import elections as el  # noqa: E402

N = el.FENSTER
FEHLER: list[str] = []


def soll(bedingung: bool, text: str) -> None:
    if not bedingung:
        FEHLER.append(text)


def kalender(belegt_ab: date, zu: set[date] = frozenset()):
    """Synthetischer Kalender: Mo–Fr ausser `zu`; vor belegt_ab unbelegt (None)."""
    def ist(d: date):
        if d < belegt_ab:
            return None
        return d.weekday() < 5 and d not in zu
    return ist


def reihe(von: date, bis: date, ohne: set[date] = frozenset(), mit: set[date] = frozenset(),
          samstage: bool = False, start: float = 100.0, schritt: float = 1.0):
    """Kurse an Werktagen (optional mit Samstagen); Kurs steigt je Zeile um `schritt`."""
    daten, closes, x, v = [], [], von, start
    while x <= bis:
        werktag = x.weekday() < 5 or (samstage and x.weekday() == 5)
        if (werktag and x not in ohne) or x in mit:
            daten.append(x.isoformat())
            closes.append(v)
            v += schritt
        x += timedelta(days=1)
    return daten, closes


def gueltig(p: dict, x: int, y: int) -> bool:
    return el.fenster_rendite(p, x, y) is not None


WAHL = date(2010, 11, 2)           # Dienstag
VON, BIS = date(2010, 1, 1), date(2011, 6, 30)
BELEGT = kalender(date(2000, 1, 1))


def fall_offen():
    d, c = reihe(VON, BIS)
    i, g = el.anker(d, WAHL, BELEGT)
    soll(i is not None and d[i] == "2010-11-02", f"offener Dienstag: Anker {d[i] if i is not None else g}")
    p = el.pfad(d, c, i, BELEGT)
    soll(gueltig(p, 60, 60), "offener Dienstag: 60/60 nicht vollständig")


def fall_geschlossen():
    ist = kalender(date(2000, 1, 1), {WAHL})
    d, c = reihe(VON, BIS, ohne={WAHL})
    i, g = el.anker(d, WAHL, ist)
    soll(i is not None and d[i] == "2010-11-01", f"geschlossener Dienstag: Anker {d[i] if i is not None else g}")
    soll(gueltig(el.pfad(d, c, i, ist), 20, 20), "geschlossener Dienstag: 20/20 ungültig")


def fall_wahltag_fehlt():
    d, c = reihe(VON, BIS, ohne={WAHL})          # Kalender sagt offen, Kurs fehlt
    i, g = el.anker(d, WAHL, BELEGT)
    soll(i is None and g == "kurs_am_wahltag_fehlt", f"fehlender offener Wahltag: {i}, {g} (Montag darf nicht t0 werden)")


def fall_sonntag():
    so = date(2010, 9, 26)
    d, c = reihe(VON, BIS)
    i, g = el.anker(d, so, BELEGT)
    soll(i is not None and d[i] == "2010-09-24", f"Sonntag: Anker {d[i] if i is not None else g}, erwartet Freitag")


def fall_fehlende_sitzung_plus3_und_45():
    d, c = reihe(VON, BIS)
    i0 = d.index(WAHL.isoformat())
    for off, x_y in ((3, ((2, 2), (20, 20))), (45, ((20, 20), (60, 60)))):
        weg = date.fromisoformat(d[i0 + off])
        d2, c2 = reihe(VON, BIS, ohne={weg})
        i, _ = el.anker(d2, WAHL, BELEGT)
        p = el.pfad(d2, c2, i, BELEGT)
        kurz, lang = x_y
        soll(gueltig(p, *kurz), f"Lücke bei +{off}: {kurz} sollte gültig sein")
        soll(not gueltig(p, *lang), f"Lücke bei +{off}: {lang} sollte ungültig sein")
        soll(p["grund"].get(off) == el.G_FEHLENDE_SITZUNG, f"Lücke bei +{off}: Grund {p['grund'].get(off)}")
        soll(p["c"][N + off - 1] is not None, f"Lücke bei +{off}: Offset davor fälschlich ungültig")


def fall_datenende_plus25():
    d, c = reihe(VON, BIS)
    i0 = d.index(WAHL.isoformat())
    d2, c2 = d[: i0 + 26], c[: i0 + 26]
    p = el.pfad(d2, c2, i0, BELEGT)
    soll(gueltig(p, 20, 20), "Datenende +25: 20/20 sollte gültig sein")
    soll(not gueltig(p, 60, 60), "Datenende +25: 60/60 sollte ungültig sein")
    soll(p["grund"].get(26) == el.G_NACH_DATENENDE, f"Datenende +25: Grund {p['grund'].get(26)}")


def fall_unbelegt_lange_schliessung_und_samstag():
    ist = kalender(date(1971, 1, 1))
    w = date(1914, 11, 3)
    # Samstagshandel (unbelegt): Samstage sind gültige Zeilen
    d, c = reihe(date(1914, 1, 1), date(1915, 6, 30), samstage=True)
    i, g = el.anker(d, w, ist)
    p = el.pfad(d, c, i, ist)
    soll(gueltig(p, 60, 60), "historischer Samstag: Fenster fälschlich ungültig")
    soll(p["kalender_belegt"] is False, "unbelegter Kalender nicht gekennzeichnet")
    # lange Schliessung 10 Tage bei etwa −5
    weg = {date(1914, 10, 22) + timedelta(days=k) for k in range(10)}
    d2, c2 = reihe(date(1914, 1, 1), date(1915, 6, 30), ohne=weg, samstage=True)
    i2, _ = el.anker(d2, w, ist)
    p2 = el.pfad(d2, c2, i2, ist)
    erste_ungueltig = max(o for o in p2["grund"] if o < 0)
    soll(p2["grund"][erste_ungueltig] == el.G_LUECKE, f"lange Schliessung: Grund {p2['grund'][erste_ungueltig]}")
    soll(gueltig(p2, -erste_ungueltig - 1, 5) and not gueltig(p2, -erste_ungueltig, 5),
         "lange Schliessung: Grenze der Gültigkeit falsch")


def fall_lueckengrenze_4_tage():
    """Unbelegter Kalender: Lücke von genau 4 Kalendertagen ok, 5 Tage ungültig (MAX_LUECKE = 4)."""
    ist = kalender(date(1971, 1, 1))
    w = date(1914, 11, 3)
    for weg, erwartet_ok in (({date(1914, 10, 26), date(1914, 10, 27)}, True),            # Sa→Mi = 4
                             ({date(1914, 10, 26), date(1914, 10, 27), date(1914, 10, 28)}, False)):  # Sa→Do = 5
        d, c = reihe(date(1914, 1, 1), date(1915, 6, 30), ohne=weg, samstage=True)
        i, _ = el.anker(d, w, ist)
        p = el.pfad(d, c, i, ist)
        soll(gueltig(p, 20, 0) is erwartet_ok,
             f"Lückengrenze: {len(weg)} fehlende Tage → gültig={gueltig(p, 20, 0)}, erwartet {erwartet_ok}")


def fall_kontrolljahre():
    d, c = reihe(date(2008, 6, 1), date(2012, 6, 30))
    st = el.studie_fuer_reihe({"date": "2010-11-02"}, d, c, BELEGT, date(2012, 6, 30))
    k = {x["jahr"]: x for x in st["kontrollen"]}
    soll(sorted(k) == [2009, 2011], f"Kontrolljahre {sorted(k)}, erwartet [2009, 2011]")
    soll(k.get(2009, {}).get("pseudotermin") == "2009-11-03" and k.get(2011, {}).get("pseudotermin") == "2011-11-08",
         "Pseudotermine nicht nach der US-Regel")
    soll(k.get(2011, {}).get("pfad", {}).get("t0") == "2011-11-08", "Kontrolle 2011 nicht am Pseudotermin verankert")
    st2 = el.studie_fuer_reihe({"date": "2010-11-02"}, d, c, BELEGT, date(2011, 6, 30))
    k2 = {x["jahr"]: x for x in st2["kontrollen"]}
    soll(k2[2011].get("ausgeschlossen") == el.G_ZUKUNFT, "künftiges Kontrolljahr nicht ausgeschlossen")


def fall_nicht_sitzung_vorlauf_und_grenze():
    """Codex R1: rückwärts ist die neu aufgenommene Zeile `a`; Grenze unbelegt → belegt."""
    sa = date(2010, 10, 23)  # Samstag vor der Wahl
    d, c = reihe(VON, BIS, mit={sa})
    i, _ = el.anker(d, WAHL, BELEGT)
    p = el.pfad(d, c, i, BELEGT)
    off = d.index(sa.isoformat()) - i
    soll(p["grund"].get(off) == el.G_NICHT_SITZUNG, f"Nicht-Sitzung im Vorlauf: Grund {p['grund'].get(off)}")
    soll(not gueltig(p, -off, 20) and gueltig(p, -off - 1, 20), "Nicht-Sitzung im Vorlauf: Gültigkeitsgrenze falsch")
    ist = kalender(date(1971, 1, 1))
    d2, c2 = reihe(date(1970, 6, 1), date(1971, 3, 1), ohne={date(1971, 1, 1)}, mit={date(1971, 1, 2)})
    i2 = d2.index("1970-12-31")
    p2 = el.pfad(d2, c2, i2, ist)
    soll(p2["grund"].get(1) == el.G_NICHT_SITZUNG, f"Grenze 1970→1971: Samstag 02.01.1971 als {p2['grund'].get(1)}")
    soll(p2["tage"][N + 1] == 2 and p2["tage"][N - 1] == -1, f"Datumsversatz im Pfad falsch: {p2['tage'][N - 1:N + 2]}")


def fall_belegte_lange_schliessung():
    """Belegter Kalender: eine belegte Schliessung > 4 Tage (11.–14.09.2001) ist keine Lücke."""
    zu = {date(2001, 9, 11) + timedelta(days=k) for k in range(4)}
    ist = kalender(date(1971, 1, 1), zu)
    d, c = reihe(date(2001, 1, 2), date(2002, 6, 28), ohne=zu)
    i, _ = el.anker(d, date(2001, 11, 6), ist)
    soll(gueltig(el.pfad(d, c, i, ist), 60, 20), "belegte Schliessung 2001 macht das Fenster fälschlich ungültig")


def fall_kurs_an_nicht_sitzung():
    sa = date(2010, 11, 6)  # Samstag nach der Wahl
    d, c = reihe(VON, BIS, mit={sa})
    i, _ = el.anker(d, WAHL, BELEGT)
    p = el.pfad(d, c, i, BELEGT)
    off = d.index(sa.isoformat()) - i
    soll(p["grund"].get(off) == el.G_NICHT_SITZUNG, f"Kurs an Nicht-Sitzung: Grund {p['grund'].get(off)}")
    soll(p["c"][N + off - 1] is not None, "Kurs an Nicht-Sitzung: Offset davor fälschlich ungültig")


def fall_anker_zu_weit():
    d, c = reihe(VON, date(2010, 10, 20))
    d += ["2010-12-01"]
    c += [999.0]
    i, g = el.anker(d, date(2010, 11, 30), kalender(date(2020, 1, 1)))
    soll(i is None and g == "anker_zu_weit", f"Anker zu weit: {i}, {g}")


def fall_live():
    termin = date(2026, 11, 3)
    d, c = reihe(date(2026, 1, 1), date(2026, 10, 6))  # letzter Kurs Di 06.10.
    p = el.live_pfad(d, c, termin, BELEGT, date(2026, 10, 6))
    # Sitzungen 07.10.–03.11. = 20 → letzter Kurs liegt bei Offset −20
    soll(p["c"][N - 20] == c[-1], f"Live: letzter Kurs nicht bei −20 ({p['c'][N - 20]} vs {c[-1]})")
    soll(p["c"][N - 19] is None and p["grund"].get(-19) == el.G_ZUKUNFT, "Live: −19 sollte Zukunft sein")
    soll(p["c"][N - 25] == c[-6], "Live: −25 falsch positioniert")
    soll(el.fenster_rendite(p, 20, 5) is None, "Live: Fenster mit Zukunft darf keine Rendite haben")
    soll(p["t0"] == "2026-11-03" and p["t0_projiziert"], "Live: projiziertes t0 falsch")
    # Wechsel X=5 / X=20: Basis t−X liegt in der Zukunft bzw. ist vorhanden
    soll(p["c"][N - 5] is None and p["c"][N - 20] is not None, "Live: Basis t−5 / t−20 falsch verfügbar")
    soll(p["tage"][N] == 0 and p["tage"][N - 20] == -28 and p["tage"][N + 1] == 1, f"Live: Datumsversatz {p['tage'][N - 20]}")
    # Verzögerter Kurs-Refresh (Codex R1): Session 06.10. abgeschlossen, Kurs fehlt noch
    d2, c2 = d[:-1], c[:-1]
    p2 = el.live_pfad(d2, c2, termin, BELEGT, date(2026, 10, 6))
    soll(p2["grund"].get(-20) == el.G_FEHLENDE_SITZUNG, f"Live: fehlende abgeschlossene Session als {p2['grund'].get(-20)}")
    soll(p2["c"][N - 21] == c2[-1], "Live: ältere Kurse durch fehlende Session verschoben")
    soll(p2["grund"].get(-19) == el.G_ZUKUNFT, "Live: Session nach dem Stichtag nicht als Zukunft")


def fall_mini_rendite():
    d = ["2010-10-29", "2010-11-01", "2010-11-02", "2010-11-03", "2010-11-04"]
    c = [100.0, 110.0, 99.0, 108.9, 118.8]
    i, _ = el.anker(d, WAHL, BELEGT)
    p = el.pfad(d, c, i, BELEGT, n=2)
    r = el.fenster_rendite(p, 2, 2, n=2)
    # Vorlauf 99/100−1 = −1 %, Nachlauf 118,8/99−1 = +20 %, Fenster 118,8/100−1 = +18,8 %
    ok = r and abs(r["vorlauf"] + 1) < 1e-9 and abs(r["nachlauf"] - 20) < 1e-9 and abs(r["fenster"] - 18.8) < 1e-9
    soll(bool(ok), f"Mini-Reihe: {r}")


def fall_machtwechsel_unbekannt():
    """Codex R1: unbekannte Ergebnisse dürfen weder als Wechsel noch als kein Wechsel erscheinen."""
    import build_wahlen as bw
    w = {"id": "x", "type": "president", "date": "2000-11-07", "status": "held",
         "result": {"winner": "?", "winner_party": "unknown", "prior_party": "US-R"}}
    soll(bw._meta(w)["machtwechsel"] is None, "unknown + US-R ergibt einen Machtwechsel-Wert")
    w["result"]["prior_party"] = "unknown"
    soll(bw._meta(w)["machtwechsel"] is None, "unknown + unknown ergibt 'kein Wechsel'")
    w["result"].update(winner_party="US-D", prior_party="US-R")
    soll(bw._meta(w)["machtwechsel"] is True, "bekannter Wechsel nicht erkannt")


def fall_baue_end_to_end():
    """build_wahlen.baue() mit synthetischen Kursen auf dem echten Kalender."""
    import build_wahlen as bw

    ist = el.lade_kalender("NYSE")
    from shared.nyse_holidays import get_nyse_holidays  # noqa: F401  (Kalender bereits in `ist`)
    wahltage_zu = {el.us_wahltag(y) for y in range(1896, 1969)} | {el.us_wahltag(y) for y in (1972, 1976, 1980)}

    def laden(t):
        letzte = date(2026, 10, 5)
        von = date(1896, 1, 2) if t == "^DJI" else date(1885, 1, 2)
        daten, closes, x, v = [], [], von, 50.0
        while x <= letzte:
            s = ist(x)
            offen = (x.weekday() < 5 and x not in wahltage_zu) if s is None else s
            if offen:
                daten.append(x.isoformat())
                closes.append(v)
                v *= 1.0003
            x += timedelta(days=1)
        return daten, closes

    st = bw.baue(laden=laden, letzte=date(2026, 10, 5))
    f = bw.pruefe(st)
    soll(not f, f"baue(): {f[:3]}")
    live = next(w for w in st["wahlen"] if w["id"] == "us-midterm-2026")
    soll(live["reihen"]["^GSPC"]["pfad"].get("t0_projiziert") is True, "baue(): Midterm 2026 ohne Live-Pfad")
    w72 = next(w for w in st["wahlen"] if w["id"] == "us-president-1972")
    soll(w72["reihen"]["^GSPC"]["pfad"]["t0"] == "1972-11-06", "baue(): 1972 (Wahltag geschlossen) nicht am Montag verankert")
    w00 = next(w for w in st["wahlen"] if w["id"] == "us-president-2000")
    soll(w00.get("contested") is True and w00.get("result_decided") == "2000-12-12",
         "baue(): 2000 ohne verspätetes Ergebnisdatum im Export")
    soll(st.get("kalender_belegt_ab") == "1971-01-01", "baue(): kalender_belegt_ab fehlt im Export")
    w84 = next(w for w in st["wahlen"] if w["id"] == "us-president-1984")
    soll(w84["reihen"]["^GSPC"]["pfad"]["t0"] == "1984-11-06", "baue(): 1984 nicht am Wahltag verankert")


def main() -> int:
    for f in (fall_offen, fall_geschlossen, fall_wahltag_fehlt, fall_sonntag, fall_fehlende_sitzung_plus3_und_45,
              fall_datenende_plus25, fall_unbelegt_lange_schliessung_und_samstag, fall_lueckengrenze_4_tage, fall_kontrolljahre,
              fall_nicht_sitzung_vorlauf_und_grenze, fall_belegte_lange_schliessung,
              fall_kurs_an_nicht_sitzung,
              fall_anker_zu_weit, fall_live, fall_mini_rendite, fall_machtwechsel_unbekannt, fall_baue_end_to_end):
        vorher = len(FEHLER)
        try:
            f()
        except Exception as e:  # noqa: BLE001
            FEHLER.append(f"{f.__name__}: {type(e).__name__}: {e}")
        print(("  ok    " if len(FEHLER) == vorher else "  FEHLER") + f"  {f.__name__}")
    for x in FEHLER:
        print("    " + x)
    print(f"verify_wahlen_build: {len(FEHLER)} Fehler")
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
