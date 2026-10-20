"""Waechter fuer die Events-Sektion der Morgen-Mail (`events_today_tomorrow`).

Anlass: beim Pruefen aller Mail-Bestandteile am 2026-10-20 war die Sektion leer, und
das war an diesem Tag richtig (FOMC erst 28.10., kein OPEX, kein Feiertag im
Fenster). Dabei fiel aber auf, dass **VIXpiration gar keine Ereignisquelle war** —
gefiltert wurde auf `opex`/`triple_witching`, und der 21.10.2026 ist ein
VIX-Settlement. Nutzerentscheidung: aufnehmen.

Quelle ist `shared/produkttermine.py` (V1c-2, aus den Cboe-Belegen), nicht die
Tabelle `market_events`: fuer neuen Kalendercode sind die gemeinsamen Bausteine
verbindlich, und nur `produkttermine` kennt die Feiertagsregel.

Geprueft wird ohne Netz und ohne Datenbank.

REGEL ZUR KENNUNG `[Aufbau]`: nur fuer Eigenschaften der Testvorrichtung, nie fuer
Aussagen ueber den Produktivcode.
"""
from __future__ import annotations

import os
import pathlib
import sys
import traceback
from datetime import date

sys.stdout.reconfigure(encoding="utf-8")

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))


def _absturz(typ, wert, tb):
    traceback.print_exception(typ, wert, tb)
    print("[Absturz] unerwartete Ausnahme — kein Nachweis")
    sys.stdout.flush()
    os._exit(3)


sys.excepthook = _absturz

import shared.daily_report as dr          # noqa: E402
import shared.supabase_client as sc       # noqa: E402

fehler = 0
anzahl = 0


def pruefe(bed, was):
    global fehler, anzahl
    anzahl += 1
    print(("  ok   " if bed else "  FEHL ") + was)
    if not bed:
        fehler += 1


# ── Attrappen: keine Datenbank, keine Feiertage, keine Notenbanken ─────────
class LeerTabelle:
    def select(self, *a, **k):
        return self

    def gte(self, *a, **k):
        return self

    def lte(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def in_(self, *a, **k):
        return self

    def order(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def range(self, *a, **k):
        return self

    def execute(self):
        class A:
            data = []
        return A()


class LeerClient:
    def table(self, name):
        return LeerTabelle()


sc.get_client = lambda: LeerClient()
dr.fetch_market_events = lambda *a, **k: []


def ereignisse(stichtag: date, tage: int = 5):
    """`events_today_tomorrow` mit festem Stichtag, damit das Ergebnis nicht vom
    Kalender des Prueflaufs abhaengt — ein Test, dessen Ergebnis vom Datum
    abhaengt, ist kein Test."""
    import shared.daily_report as _dr
    alt_today = _dr.datetime
    # `events_today_tomorrow` liest `datetime.now(timezone.utc).date()` fuer
    # `today_utc` und bekommt `target_date` uebergeben. Der Stichtag wird deshalb
    # ueber eine Huelle um `datetime` gesetzt.
    from datetime import datetime as _echt, timezone as _tz

    class _Dt(_echt):
        @classmethod
        def now(cls, tz=None):
            return _echt(stichtag.year, stichtag.month, stichtag.day, 12, 0,
                         tzinfo=tz or _tz.utc)

    _dr.datetime = _Dt
    try:
        return _dr.events_today_tomorrow(target_date=stichtag, lookahead_days=tage)
    finally:
        _dr.datetime = alt_today


print("Der 21.10.2026 ist ein VIX-Settlement und erscheint in der Mail:")
# Nachgerechnet aus dem Katalog, nicht angenommen: Referenzfreitag 2026-11-20
# minus 30 Tage = 2026-10-21, Einstufung `belegt`.
from shared.produkttermine import produkttermine   # noqa: E402

kat = produkttermine("2026-10", "2026-10", "vix", pruefdatum=date(2026, 10, 20))
pruefe(len(kat) == 1 and kat[0]["settlement"] == "2026-10-21",
       "[Aufbau] der Katalog nennt den 21.10.2026 (%r)"
       % (kat and kat[0].get("settlement")))
pruefe(kat and kat[0]["listung_futures"] == "belegt",
       "[Aufbau] und zwar als belegt, nicht als Projektion (%r)"
       % (kat and kat[0].get("listung_futures")))

ev = ereignisse(date(2026, 10, 20))
vix = [e for e in ev if e.get("type") == "VIXPIRATION"]
pruefe(len(vix) == 1,
       "am 20.10. steht genau ein VIX-Settlement im Fenster (%d von %d Ereignissen)"
       % (len(vix), len(ev)))
pruefe(vix and vix[0]["date"] == "2026-10-21",
       "mit dem richtigen Datum (%r)" % (vix and vix[0].get("date")))
pruefe(vix and "2026-10" in (vix[0].get("name") or ""),
       "und dem Kontraktmonat im Namen (%r)" % (vix and vix[0].get("name")))

print("")
print("Die Feiertagsregel wird mitgenommen, nicht der nominale Termin:")
# Kontraktmonat 2026-05: nominal 2026-05-20, Settlement 2026-05-19 — der Mittwoch
# oder der Referenzfreitag war geschlossen. Der Fall trennt `settlement` von
# `nominal`; im Oktober 2026 sind beide gleich und wuerden nichts beweisen.
mai = produkttermine("2026-05", "2026-05", "vix", pruefdatum=date(2026, 5, 18))
pruefe(mai and mai[0]["nominal"] == "2026-05-20"
       and mai[0]["settlement"] == "2026-05-19",
       "[Aufbau] der Katalog verschiebt hier um einen Tag (%r -> %r)"
       % (mai and mai[0].get("nominal"), mai and mai[0].get("settlement")))
ev_mai = ereignisse(date(2026, 5, 18))
vix_mai = [e for e in ev_mai if e.get("type") == "VIXPIRATION"]
pruefe(len(vix_mai) == 1 and vix_mai[0]["date"] == "2026-05-19",
       "die Mail nennt den 19.05., nicht den nominalen 20.05. (%r)"
       % (vix_mai and vix_mai[0].get("date")))

print("")
print("Ausserhalb des Fensters erscheint es nicht:")
ev2 = ereignisse(date(2026, 10, 1))
pruefe(not [e for e in ev2 if e.get("type") == "VIXPIRATION"],
       "am 1.10. liegt der 21.10. nicht im 5-Tage-Fenster (%d Ereignisse)" % len(ev2))
ev3 = ereignisse(date(2026, 10, 22))
pruefe(not [e for e in ev3 if e.get("type") == "VIXPIRATION"],
       "am 22.10. ist er vorbei")

print("")
print("Die Erkenntnisgrenze des Katalogs wird nicht ueberschritten:")
ev4 = ereignisse(date(2014, 6, 16))      # Juni 2014: VIX-Settlement am 18.06.
pruefe(not [e for e in ev4 if e.get("type") == "VIXPIRATION"],
       "vor Kontraktmonat 2015-09 liefert der Katalog nichts, und die Mail "
       "erfindet nichts (%d Ereignisse)" % len(ev4))

print("")
print("Ein Fehlschlag der VIX-Quelle nimmt die uebrigen Ereignisse nicht mit:")
import shared.produkttermine as pt       # noqa: E402

_echt_pt = pt.produkttermine


def _kaputt(*a, **k):
    raise RuntimeError("Attrappe: Katalog nicht lesbar")


pt.produkttermine = _kaputt
fehlerzeilen = []
_echt_log = dr.error_logger


class _Log:
    def error(self, text, *a):
        fehlerzeilen.append(str(text))

    def warning(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass

    def debug(self, *a, **k):
        pass


dr.error_logger = _Log()
try:
    ev5 = ereignisse(date(2026, 10, 20))
finally:
    pt.produkttermine = _echt_pt
    dr.error_logger = _echt_log

pruefe(not [e for e in ev5 if e.get("type") == "VIXPIRATION"],
       "ohne Katalog kein VIX-Ereignis (%d Ereignisse)" % len(ev5))
pruefe(any("VIXpiration" in z for z in fehlerzeilen),
       "aber eine Logzeile — der Ausfall ist nicht stumm (%d Zeilen)"
       % len(fehlerzeilen))
pruefe(isinstance(ev5, list),
       "und die Funktion liefert weiter eine Liste, statt die Sektion zu reissen")

print("")
print("Die Quelle ist der Katalog, nicht die Tabelle market_events:")
quelle = (WURZEL / "shared" / "daily_report.py").read_text(encoding="utf-8")
i_vix = quelle.find("# VIXpiration")
abschnitt = quelle[i_vix:i_vix + 1600] if i_vix != -1 else ""
pruefe(i_vix != -1, "[Aufbau] der Abschnitt ist gefunden")
pruefe("from shared.produkttermine import" in abschnitt,
       "er importiert shared.produkttermine")
pruefe("pruefdatum=" in abschnitt,
       "und uebergibt das Pflicht-Pruefdatum")
# KEINE Wortsuche nach „market_events": das Wort steht im erklaerenden Kommentar
# des Abschnitts selbst, die Pruefung koennte also nie bestehen. Dieselbe Falle wie
# bei der Sektor-Rotation am selben Tag. Dass die Quelle der Katalog ist, ist oben
# an der WIRKUNG geprueft (ohne Katalog kein Ereignis). Hier bleibt, was fuer die
# Vorlage zaehlt: der Typ ist eigenstaendig und nicht als OPEX getarnt.
pruefe(vix and vix[0].get("type") == "VIXPIRATION",
       "der Ereignistyp ist eigenstaendig, nicht OPEX (%r)"
       % (vix and vix[0].get("type")))
pruefe(vix and vix[0].get("impact") in ("low", "medium", "high"),
       "und traegt eine gueltige Einstufung (%r)" % (vix and vix[0].get("impact")))

print("")
print("ALLE PRUEFUNGEN BESTANDEN" if fehler == 0 else "%d FEHLER" % fehler)
print("PROBE-ENDE %d Pruefungen, %d Fehler" % (anzahl, fehler))
sys.exit(0 if fehler == 0 else 1)
