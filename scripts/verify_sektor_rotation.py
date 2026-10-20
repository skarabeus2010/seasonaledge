"""Waechter fuer die Sektor-Rotation der Morgen-Mail (Befund des Nutzers, 2026-10-20).

Anlass: der Nutzer bemerkte, dass „die Ticker staendig wechseln". Nachgemessen waren
es drei Defekte, und keiner hat je eine Fehlerzeile erzeugt:

  1. Eine handgeschriebene Tabelle `HISTORIC_BEST` sprang ein, wenn die Rechnung
     nichts lieferte — stumm, ohne Kennzeichnung, mit erfundenen Zahlen. Die Mail
     des Nutzers zeigte Ziffer fuer Ziffer diese Tabelle.
  2. Der laufende, unfertige Monat zaehlte als voller Monat. Gemessen am 2026-10-20
     drehte das die Rangfolge der Spalte „aktueller Monat": XLK von Platz 5 (+2,10 %)
     auf Platz 2 (+2,58 %).
  3. Keine Fallzahl an den Werten, und ungleiche Fallzahlen wurden gemischt
     (XLC n=8 gegen XLK n=15 in derselben Rangliste).
  4. In der Vorlage waren Vorzeichen und Farbe fest verdrahtet: ein negativer
     Sektorwert waere als „+-0.7%" in GRUEN erschienen.
  5. `letzte_session(...)` wurde als Argument ausgewertet, bevor `muster_fuer` einen
     Ticker ausserhalb des Studienuniversums verwerfen konnte — jeder Lauf schrieb
     eine ERROR-Zeile fuer einen erwarteten Fall.

Geprueft wird ohne Netz und ohne Datenbank: die Kurshistorie ist eine Attrappe, die
Vorlage wird echt gerendert.

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


def _absturz(typ, wert, tb):
    """Eine Ausnahme ist kein Nachweis — Exit 3, damit der Mutationstest sie als
    UNGUELTIG zaehlt und nicht als „erkannt" (Beweisregel 4)."""
    traceback.print_exception(typ, wert, tb)
    print("[Absturz] unerwartete Ausnahme — kein Nachweis")
    sys.stdout.flush()
    os._exit(3)


sys.excepthook = _absturz

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

import pandas as pd  # noqa: E402

import shared.daily_report as dr  # noqa: E402

fehler = 0
anzahl = 0


def pruefe(bed, was):
    global fehler, anzahl
    anzahl += 1
    print(("  ok   " if bed else "  FEHL ") + was)
    if not bed:
        fehler += 1


# ── Vorrichtung: Monatsschlusskurse, bei denen jede Monatsrendite BEKANNT ist ──
# Je Ticker eine Reihe mit einem Schlusskurs am Monatsende. Der Kurs waechst in
# jedem Oktober um genau `okt_rendite` Prozent und in jedem anderen Monat um 0 %,
# damit der Oktober-Durchschnitt analytisch feststeht.
STICHTAG = date(2026, 10, 20)      # laufender Monat ist Oktober 2026


def reihe(erstes_jahr: int, letztes_jahr: int, okt_rendite: float) -> pd.Series:
    daten, kurs = [], 100.0
    for jahr in range(erstes_jahr, letztes_jahr + 1):
        for monat in range(1, 13):
            if jahr == STICHTAG.year and monat > STICHTAG.month:
                break
            if monat == 10:
                kurs *= (1.0 + okt_rendite / 100.0)
            tag = pd.Timestamp(year=jahr, month=monat, day=1) + pd.offsets.MonthEnd(0)
            if jahr == STICHTAG.year and monat == STICHTAG.month:
                tag = pd.Timestamp(STICHTAG)      # laufender Monat: unfertig
            daten.append((tag, kurs))
    return pd.Series([k for _, k in daten], index=pd.DatetimeIndex([d for d, _ in daten]),
                     dtype=float)


# XLK: 2011..2026, Oktober +2 % — also 15 abgeschlossene Oktober (2011..2025)
#      plus den laufenden 2026, der NICHT zaehlen darf.
# XLF: dieselbe Spanne, Oktober +3 % → muss vor XLK stehen.
# XLC: nur 2023..2026, Oktober +9 % → hoechster Mittelwert, aber n = 3 < Schwelle.
# XLU: 2011..2026, Oktober -1 % → negativer Wert, muss das Vorzeichen behalten.
FIXTURE = {
    "XLF": reihe(2011, 2026, 3.0),
    "XLK": reihe(2011, 2026, 2.0),
    "XLU": reihe(2011, 2026, -1.0),
    "XLC": reihe(2023, 2026, 9.0),
}

_echt_history = dr.fetch_daily_close_history
_fehlerzeilen: list[str] = []


class _LogAttrappe:
    def error(self, text):
        _fehlerzeilen.append(str(text))

    def warning(self, text):
        pass

    def info(self, text):
        pass

    def debug(self, text):
        pass


def mit_fixture(daten):
    dr.fetch_daily_close_history = lambda tickers, lookback_days=5500: dict(daten)


print("Der laufende Monat zaehlt nicht mit, und jede Zahl traegt ihre Fallzahl:")
mit_fixture(FIXTURE)
m = dr._sector_monthly_avg_returns(heute=STICHTAG)

pruefe(set(m) == set(FIXTURE),
       "[Aufbau] alle vier Attrappen-Ticker kommen durch: %s" % sorted(m))
pruefe(10 in m.get("XLK", {}),
       "[Aufbau] fuer XLK gibt es einen Oktober-Wert")

xlk = m["XLK"][10]
pruefe(xlk["n"] == 15,
       "XLK: 15 abgeschlossene Oktober, der laufende 2026 zaehlt NICHT (n=%s)" % xlk["n"])
pruefe(abs(xlk["avg"] - 2.0) < 1e-9,
       "XLK: Mittelwert ist die analytisch bekannten 2,00 %% (%.6f)" % xlk["avg"])
pruefe(m["XLU"][10]["avg"] < 0,
       "XLU: der negative Monat bleibt negativ (%.2f)" % m["XLU"][10]["avg"])
pruefe(m["XLC"][10]["n"] == 3,
       "[Aufbau] XLC hat nur 3 abgeschlossene Oktober (n=%s)" % m["XLC"][10]["n"])

# Gegenprobe: mit dem laufenden Monat waere n = 16 und der Mittelwert anders.
m_mit = dr._sector_monthly_avg_returns(heute=date(2026, 11, 1))
pruefe(m_mit["XLK"][10]["n"] == 16,
       "[Aufbau] ausserhalb des Oktobers zaehlt der Oktober 2026 mit (n=%s)"
       % m_mit["XLK"][10]["n"])

print("")
print("Die Rangfolge kommt aus den Daten, und die Mindest-Fallzahl greift:")
sig = dr.sector_rotation_signal(target_date=STICHTAG)
tickers = [r["ticker"] for r in sig["current_top"]]
pruefe(sig["berechenbar"] is True, "berechenbar ist True, wenn Werte da sind")
pruefe(tickers and tickers[0] == "XLF",
       "der hoechste zulaessige Mittelwert fuehrt: %s" % tickers)
pruefe("XLC" not in tickers,
       "XLC fuehrt NICHT, obwohl sein Mittelwert der hoechste ist — n=3 unter der "
       "Schwelle %d (%s)" % (dr.SEKTOR_MIN_JAHRE, tickers))
pruefe(all("n" in r for r in sig["current_top"]),
       "jede Zeile traegt ihre Fallzahl")
pruefe([r["avg_return_pct"] for r in sig["current_top"]]
       == sorted((r["avg_return_pct"] for r in sig["current_top"]), reverse=True),
       "absteigend sortiert")
pruefe(sig.get("min_jahre") == dr.SEKTOR_MIN_JAHRE,
       "die Schwelle wird mitgegeben (%s)" % sig.get("min_jahre"))

print("")
print("Ohne Kurshistorie wird nichts erfunden — und es steht im Log:")
_fehlerzeilen.clear()
_echt_log = dr.error_logger
dr.error_logger = _LogAttrappe()
mit_fixture({})
leer = dr._sector_monthly_avg_returns(heute=STICHTAG)
sig_leer = dr.sector_rotation_signal(target_date=STICHTAG)
dr.error_logger = _echt_log

pruefe(leer == {}, "ohne Historie kommt ein leeres Ergebnis (%r)" % (leer,))
pruefe(sig_leer["berechenbar"] is False,
       "berechenbar ist False (%r)" % sig_leer["berechenbar"])
pruefe(sig_leer["current_top"] == [] and sig_leer["next_top"] == [],
       "keine Ersatzwerte: beide Listen sind leer")
pruefe(any("Sektor-Rotation" in z for z in _fehlerzeilen),
       "der stumme Zweig schreibt jetzt eine Logzeile (%d Zeilen)" % len(_fehlerzeilen))

print("")
print("Die erfundene Tabelle ist aus dem Code verschwunden:")
# Nicht nach dem NAMEN suchen: der steht jetzt im erklaerenden Kommentar, und ein
# Wortfund waere ein Fehlalarm — meine erste Fassung dieser Pruefung ist genau
# darauf hereingefallen. Gesucht wird die FORM der Tabelle: ein Monatsschluessel,
# der auf eine Liste von (Ticker, Zahl)-Paaren zeigt.
import re  # noqa: E402

quelle = (WURZEL / "shared" / "daily_report.py").read_text(encoding="utf-8")
tabellenzeilen = re.findall(r'^\s*\d{1,2}\s*:\s*\[\s*\(\s*["\']X[A-Z]{1,3}["\']\s*,',
                            quelle, re.MULTILINE)
pruefe(not tabellenzeilen,
       "keine Monatstabelle mit festen Sektorwerten mehr im Quelltext (%d Zeilen)"
       % len(tabellenzeilen))
# Und die Wirkung, nicht nur die Form: ohne Historie kommt nichts heraus. Das ist
# oben schon geprueft (berechenbar is False, beide Listen leer) — hier nur noch,
# dass kein Zweig des Codes feste Sektorwerte zurueckgibt.
pruefe(not re.search(r'avg_return_pct["\']?\s*:\s*-?\d', quelle),
       "kein Rueckgabewert setzt avg_return_pct auf eine feste Zahl")

print("")
print("Die Vorlage zeigt Vorzeichen, Farbe und Fallzahl richtig:")
import jinja2  # noqa: E402

vorlage_pfad = WURZEL / "scripts" / "templates" / "daily_report.html.j2"
umgebung = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(vorlage_pfad.parent)),
    autoescape=jinja2.select_autoescape(["html"]),
)
tpl = umgebung.get_template(vorlage_pfad.name)

RAHMEN = dict(report_date="2026-10-20", report_time="2026-10-20 05:30 UTC",
              target_display="Di 20. Okt 2026", target_tdom=14, status_line="x",
              core_list=[], etfs=[], stocks=[], watchlist=[], events=[],
              strategies=[], intermarket=[], unsubscribe_url="#", dashboard_url="#")


def rendere(rotation):
    return tpl.render(**dict(RAHMEN, rotation=rotation))


html_neg = rendere({
    "current_month": 10, "next_month": 11, "berechenbar": True,
    "min_jahre": dr.SEKTOR_MIN_JAHRE,
    "current_top": [{"ticker": "XLU", "name": "Utilities", "avg_return_pct": -0.7, "n": 11}],
    "next_top": [{"ticker": "XLF", "name": "Financials", "avg_return_pct": 4.6, "n": 15}],
    "legend": [{"ticker": "XLU", "name": "Utilities"}],
})
pruefe("-0.7%" in html_neg,
       "ein negativer Wert erscheint als -0.7%%, nicht als +-0.7%%")
pruefe("+-0.7" not in html_neg and "+-" not in html_neg,
       "kein fest verdrahtetes Plus vor einem negativen Wert")
pruefe("#ff5c5c" in html_neg,
       "der negative Wert ist rot, nicht gruen")
pruefe("+4.6%" in html_neg,
       "ein positiver Wert behaelt sein Plus")
pruefe("(11)" in html_neg and "(15)" in html_neg,
       "die Fallzahl steht in der gerenderten Mail")

html_leer = rendere({
    "current_month": 10, "next_month": 11, "berechenbar": False,
    "min_jahre": dr.SEKTOR_MIN_JAHRE,
    "current_top": [], "next_top": [],
    "legend": [{"ticker": "XLU", "name": "Utilities"}],
})
pruefe("Sektor-Rotation" in html_leer,
       "die Sektion verschwindet nicht, wenn nichts berechenbar ist")
pruefe("nicht berechenbar" in html_leer,
       "sie sagt stattdessen, dass es heute nicht berechenbar ist")
pruefe("XLK" not in html_leer,
       "und nennt dabei keinen einzigen Sektor-Wert")

print("")
print("Ein Ticker ausserhalb des Studienuniversums erzeugt keine Fehlerzeile:")
# FOREX hat keine Schlusszeit; `letzte_session` wirft dafuer. Entscheidend ist,
# dass `im_universum` VORHER greift und der Aufruf gar nicht zustande kommt.
import shared.kursmuster as km  # noqa: E402
import shared.exchange_holidays as eh  # noqa: E402

pruefe(km.im_universum("EURUSD=X") is False,
       "[Aufbau] EURUSD=X liegt nicht im Studienuniversum")
pruefe(km.im_universum("SPY") is True,
       "[Aufbau] SPY liegt darin")

aufrufe: list[str] = []
_echt_letzte = eh.letzte_session


def _letzte_attrappe(boerse):
    aufrufe.append(str(boerse))
    if str(boerse).upper() in ("FOREX", "CRYPTO"):
        raise ValueError("Keine Schlusszeit fuer %s hinterlegt" % boerse)
    return date(2026, 10, 19)


zeilen_quelle = (WURZEL / "shared" / "daily_report.py").read_text(encoding="utf-8")
i_guard = zeilen_quelle.find("if im_universum(ticker)")
i_call = zeilen_quelle.find("letzte_session(get_exchange_for_holidays(ticker))")
pruefe(i_guard != -1,
       "der Universums-Schutz steht im Code")
pruefe(i_guard != -1 and i_call != -1 and i_guard < i_call,
       "er steht VOR dem Aufruf von letzte_session (Positionen %d / %d)" % (i_guard, i_call))

print("")
print("ALLE PRUEFUNGEN BESTANDEN" if fehler == 0 else "%d FEHLER" % fehler)
print("PROBE-ENDE %d Pruefungen, %d Fehler" % (anzahl, fehler))
sys.exit(0 if fehler == 0 else 1)
