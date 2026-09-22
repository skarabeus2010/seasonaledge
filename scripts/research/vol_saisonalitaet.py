#!/usr/bin/env python3
"""
vol_saisonalitaet.py — Saisonalität der VOLATILITÄT statt der Rendite.

    py -3.14 scripts/research/vol_saisonalitaet.py --json <datei>

WARUM DAS UND NICHT NOCH EINE RENDITE-SAISONALITÄT: Die Plattform rechnet
Saisonalität an einem Dutzend Stellen — immer für Renditen. Realisierte
Volatilität wird bisher nur als TAGESFILTER benutzt (Intermarket-Signal, VRP),
nie saisonal ausgewertet. Dabei ist sie die dankbarere Grösse: Renditen sind
nahezu unprognostizierbar, Volatilität ist stark autokorreliert und hat ein
belastbares Jahresmuster. Eine saisonale Vola-Karte ist deshalb ehrlicherweise
nützlicher als die Renditekarten, die wir schon haben.

DIE VORAB FESTGELEGTE HYPOTHESE (EINE, und sie steht vor dem ersten Lauf hier
im Code):

    H1: Die realisierte Volatilität des S&P 500 ist im SEPTEMBER UND OKTOBER
        höher als im Rest des Jahres.

Das ist die verbreitete Behauptung („Crash-Monate"), sie ist gerichtet, und sie
wird an EINEM Ticker (SPY) und EINEM Monatspaar geprüft. Alles andere in diesem
Skript ist BESCHREIBUNG, keine Prüfung: die Monatsprofile der übrigen Ticker
werden ausgewiesen, damit man sie ansehen kann, aber sie tragen keine p-Werte.
Wer 366 Ticker × 12 Monate testet, stellt 4392 Fragen und findet garantiert
etwas — genau dieser Fehler hat diese Woche schon die Intermarket-Matrix
gekostet.

WARUM DER ZUFALLSTEST ZIRKULÄR VERSCHIEBT und nicht einfach Tage zieht:
Volatilität kommt in Blöcken. Eine unruhige Woche besteht aus fünf unruhigen
Tagen, nicht aus fünf unabhängigen Ziehungen. Wer die Tage mischt, zerstört
genau diese Struktur und erzeugt eine viel zu enge Nullverteilung — jeder
Monatsunterschied sähe dann signifikant aus. Die zirkuläre Verschiebung
zerstört die Kalender-Zuordnung, erhält aber das Clustering.

WARUM NICHT DIE ROLLENDE RV AUS shared/realized_vol: die misst die Vola der
zurueckliegenden 21 Handelstage. Der Septemberwert deckte damit Mitte August
bis Ende September ab, und ein Oktober-Crash landete zur Haelfte im November —
fuer eine Frage nach dem KALENDERMONAT ist das die falsche Zuordnung. Ein
erster Lauf dieses Skripts hatte genau diesen Fehler; er liess den September
als ruhigsten Monat erscheinen, weil der ruhige Spaetsommer mitgezaehlt wurde.
Gerechnet wird deshalb die annualisierte Streuung der Renditen, die dem Monat
SELBST gehoeren. Das ist nicht dieselbe Groesse wie die Live-RV und darf
deshalb auch nicht so heissen.

NORMIERT WIRD JE TICKER auf den eigenen Median: ein Wert von 1,30 im Oktober
heisst „30 % über der eigenen Normalvolatilität". Ohne das dominiert Bitcoin
jede Aggregation, weil er in absoluten Vol-Punkten um ein Vielfaches schwankt —
derselbe Fallstrick, der beim ersten Lauf der Intermarket-Matrix zugeschlagen
hat.
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import pathlib
import random
import statistics
import sys
from collections import defaultdict

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from shared.data import KursreiheFehlt, lade_closes                  # noqa: E402
from shared.realized_vol import iso_tag, log_returns                  # noqa: E402

HANDELSTAGE_JAHR = 252       # Annualisierung
MIN_TAGE_MONAT = 12          # weniger Renditen tragen keine Monatsstreuung
RUNDEN = 2000                # Zufallsverschiebungen für die Nullverteilung
MIN_JAHRE = 10               # weniger trägt kein Monatsprofil
# DIE HYPOTHESE SPRICHT VOM S&P 500 — ALSO WIRD DER S&P 500 GERECHNET.
#
# Ein erster Lauf nahm SPY. Das ist ein ETF, keine Indexreihe: die Kurse sind
# dividendenbereinigt, und die Bereinigung traegt an jedem Ex-Tag einen
# kuenstlichen Sprung in die Renditereihe. SPY schuettet QUARTALSWEISE aus —
# Maerz, Juni, September, Dezember. Fuer eine Frage nach Kalendermonaten ist
# das kein vernachlaessigbarer Rest, sondern ein Artefakt, das sich ausgerechnet
# in vier bestimmten Monaten sammelt. Von Codex gefunden.
#
# ^GSPC ist der Kursindex ohne Dividenden und damit frei davon.
HYPOTHESE_TICKER = "^GSPC"
HYPOTHESE_MONATE = (9, 10)   # September + Oktober

# START 1957, und die Grenze ist sachlich, nicht nach dem Ergebnis gewaehlt:
# in diesem Jahr wurde der Index auf 500 Werte erweitert und bekam seine
# heutige Form. Tagesdaten liegen zwar ab 1885 vor, aber vor 1900 sind es
# exakt zwoelf Werte pro Jahr (Monatsdaten), und die Qualitaet der
# Zwischenkriegsjahre aus dieser Quelle ist nicht nachpruefbar — CLAUDE.md
# warnt ausdruecklich vor Phantomen in den Alt-Daten.
HYPOTHESE_AB = "1957"

MONATSNAMEN = ["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
               "August", "September", "Oktober", "November", "Dezember"]

# Beschreibende Auswahl. Bewusst klein gehalten und nach Anlageklasse geordnet:
# die Karte soll lesbar sein, nicht vollständig.
UNIVERSUM = [
    ("SPY", "S&P 500", "Aktien breit"),
    ("QQQ", "Nasdaq 100", "Aktien breit"),
    ("DIA", "Dow Jones", "Aktien breit"),
    ("IWM", "Russell 2000", "Aktien breit"),
    ("^GDAXI", "DAX", "Aktien breit"),
    ("XLK", "Technologie", "Sektoren"),
    ("XLF", "Finanzen", "Sektoren"),
    ("XLE", "Energie", "Sektoren"),
    ("XLU", "Versorger", "Sektoren"),
    ("XLV", "Gesundheit", "Sektoren"),
    ("GLD", "Gold", "Rohstoffe"),
    ("SLV", "Silber", "Rohstoffe"),
    ("USO", "Öl", "Rohstoffe"),
    ("TLT", "Anleihen 20J+", "Zinsen"),
    ("HYG", "High Yield", "Zinsen"),
    ("BTC-USD", "Bitcoin", "Krypto"),
    ("ETH-USD", "Ether", "Krypto"),
]


# ── Bausteine ───────────────────────────────────────────────────────────────

def monatswerte(ticker: str, ab: str | None = None) -> tuple[list[str], list[float]]:
    """Annualisierte Streuung je Kalendermonat, aus dessen EIGENEN Renditen.

    Rueckgabe: (["2020-03", ...], [0.4712, ...]) in aufsteigender Reihenfolge.

    Eine Rendite gehoert zu dem Monat, in dem sie ANGEFALLEN ist: log_returns
    ist rueckwaerts definiert (ln(close/prev_close)) und gehoert damit zu
    SEINER Zeile — dieselbe Konvention wie in shared/calculations, wo eine
    Abweichung davon schon einmal den Jahreswechsel-Return ins falsche Jahr
    geschoben hat.
    """
    daten, closes = lade_closes(ticker)
    if ab:
        paare = [(d, c) for d, c in zip(daten, closes) if iso_tag(d) >= ab]
        daten = [d for d, _ in paare]
        closes = [c for _, c in paare]
    lr = log_returns(closes)
    je_monat = defaultdict(list)
    for i in range(1, len(closes)):               # lr[i-1] gehoert zu closes[i]
        r = lr[i - 1]
        if r is None or not math.isfinite(r):
            continue
        je_monat[iso_tag(daten[i])[:7]].append(r)

    # DER LAUFENDE KALENDERMONAT FLIEGT RAUS. Er ist per Definition
    # unvollstaendig, und MIN_TAGE_MONAT allein faengt das nicht: ein Lauf am
    # 22. September haette einen halben September im Median, waehrend der
    # Oktober naturgemaess ganz fehlt. Das ist eine asymmetrische Stichprobe
    # genau in den Monaten, um die es geht. Von Codex gefunden.
    from datetime import date as _d
    laufend = _d.today().isoformat()[:7]

    schluessel, werte = [], []
    for ym in sorted(je_monat):
        if ym == laufend:
            continue
        rr = je_monat[ym]
        if len(rr) < MIN_TAGE_MONAT:
            continue
        # Streuung um NULL, nicht um den Monatsmittelwert: gefragt ist die
        # Groesse der Bewegungen, nicht die Abweichung von einem Trend. Bei
        # 21 Beobachtungen wuerde ein Trendmonat sonst zu ruhig aussehen.
        var = sum(x * x for x in rr) / len(rr)
        werte.append(math.sqrt(var * HANDELSTAGE_JAHR))
        schluessel.append(ym)
    return schluessel, werte


def monatsprofil(ym: list[str], werte: list[float]) -> tuple[dict, float, int]:
    """Median-Monatsvola je Kalendermonat, normiert auf den Gesamtmedian.

    Der MEDIAN ueber die Jahre, nicht der Mittelwert: ein einzelnes Krisenjahr
    soll den Monat nicht bestimmen. Oktober 2008 ist ein Oktober von vielen.
    """
    je_monat = defaultdict(list)
    for k, w in zip(ym, werte):
        je_monat[int(k[5:7])].append(w)

    gesamt = statistics.median(werte) if werte else 0.0
    jahre = len({k[:4] for k in ym})
    if gesamt <= 0:
        return {}, gesamt, jahre

    profil = {}
    for monat in range(1, 13):
        if len(je_monat[monat]) >= MIN_JAHRE:
            profil[monat] = {
                "rel": round(statistics.median(je_monat[monat]) / gesamt, 4),
                "vola": round(statistics.median(je_monat[monat]), 4),
                "jahre": len(je_monat[monat]),
            }
    return profil, gesamt, jahre


def _monats_kennzahl(ym: list[str], werte: list[float], monate: tuple,
                     versatz: int = 0) -> float | None:
    """Verhältnis Median-Monatsvola in `monate` zum Rest des Jahres.

    `versatz` verschiebt die WERTE zirkulär gegen die MONATE. Damit bleibt die
    Blockstruktur der Volatilität erhalten — unruhige Phasen dauern mehrere
    Monate —, während die Zuordnung zum Kalender zerstört wird. Das ist die
    Nullhypothese „der Kalendermonat ist egal".

    Wer stattdessen die Monate mischen würde, zerstörte das Clustering und
    erhielte eine viel zu enge Nullverteilung: dann sähe jeder
    Monatsunterschied signifikant aus.
    """
    n = len(werte)
    if n < 60:                                    # fünf Jahre Monatswerte
        return None
    drin, draussen = [], []
    for i, k in enumerate(ym):
        w = werte[(i + versatz) % n]
        (drin if int(k[5:7]) in monate else draussen).append(w)
    if len(drin) < 10 or len(draussen) < 20:
        return None
    m_draussen = statistics.median(draussen)
    if m_draussen <= 0:
        return None
    return statistics.median(drin) / m_draussen


def pruefe_hypothese(ym: list[str], werte: list[float], monate: tuple) -> dict:
    """Der EINE Test. Einseitig, weil H1 eine Richtung behauptet (höher)."""
    ist = _monats_kennzahl(ym, werte, monate)
    if ist is None:
        return {"fehler": "zu wenige Beobachtungen"}

    rnd = random.Random(20260922)
    verteilung = []
    for _ in range(RUNDEN):
        # VIELFACHE VON ZWOELF SIND AUSGESCHLOSSEN — und das ist der Kern
        # des Tests, nicht eine Feinheit.
        #
        # Ein Versatz von 24 Monaten ordnet jeden September wieder einem
        # September zu und jeden Oktober einem Oktober. Solche Ziehungen
        # zerstoeren die Kalenderzuordnung NICHT, sie reproduzieren sie. Wer
        # sie in der Nullverteilung laesst, fuellt deren oberen Rand mit
        # Ziehungen, die den gemessenen Wert nachbauen — der p-Wert wird zu
        # gross und der Test zu konservativ.
        #
        # Ein erster Entwurf schloss nur Versaetze nahe null aus. Damit war
        # rund ein Zwoelftel der Nullverteilung wertlos. Von Codex gefunden.
        versatz = rnd.randrange(13, len(werte) - 13)
        if versatz % 12 == 0:
            continue
        v = _monats_kennzahl(ym, werte, monate, versatz=versatz)
        if v is not None:
            verteilung.append(v)

    # Einseitig MIT Plus-eins: H1 behauptet "höher", die Richtung stand vor dem
    # Lauf fest. Die Plus-eins-Korrektur ist Pflicht, sonst kann ein Verfahren
    # mit 2000 Ziehungen "p = 0,000" ausweisen, obwohl der kleinste
    # darstellbare Wert 1/2001 ist.
    groesser = sum(1 for x in verteilung if x >= ist)
    p = (groesser + 1) / (len(verteilung) + 1)

    verteilung.sort()
    return {
        "verhaeltnis": round(ist, 4),
        "p": round(p, 4),
        "null_median": round(statistics.median(verteilung), 4),
        "null_p95": round(verteilung[int(0.95 * (len(verteilung) - 1))], 4),
        "runden": len(verteilung),
        "monate": [MONATSNAMEN[m] for m in monate],
    }


# ── Lauf ────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="Ergebnis als JSON schreiben")
    ap.add_argument("--ticker", nargs="+", help="nur diese (Standard: Universum)")
    ap.add_argument("--alle", action="store_true",
                    help="das ganze Ticker-Universum statt der kuratierten Auswahl")
    a = ap.parse_args()

    if a.ticker:
        auswahl = [(t, t, "") for t in a.ticker]
    elif a.alle:
        from shared.symbols import get_all_tickers
        kuratiert = {t for t, _, _ in UNIVERSUM}
        auswahl = UNIVERSUM + [(t, t, "") for t in sorted(get_all_tickers())
                               if t not in kuratiert]
    else:
        auswahl = UNIVERSUM

    print("Saisonalität der Volatilität — Streuung der Renditen je "
          "Kalendermonat, annualisiert\n")

    profile, roh = [], {}
    for ticker, name, gruppe in auswahl:
        # Cache leeren und aufraeumen: download_data ist @st.cache_data und
        # haelt jede geladene Voll-Historie. Ueber das ganze Universum reisst
        # das den Prozess ab Ticker ~70 mit SIGKILL ab — in diesem Projekt
        # schon mehrfach als vermeintlicher Supabase-Fehler fehlgedeutet.
        if len(profile) % 10 == 9:
            try:
                from shared.yahoo_downloader import download_data as _dd
                _dd.clear()
            except Exception:
                pass
            gc.collect()
        try:
            ym, werte = monatswerte(ticker)
        except (KursreiheFehlt, Exception) as e:
            print("  %-10s ENTFÄLLT (%s)" % (ticker, str(e)[:50]))
            continue
        prof, median_rv, jahre = monatsprofil(ym, werte)
        if not prof:
            print("  %-10s ENTFÄLLT (zu kurze Historie: %d Jahre)" % (ticker, jahre))
            continue
        roh[ticker] = (ym, werte)
        profile.append({"ticker": ticker, "name": name, "gruppe": gruppe,
                        "median_rv": round(median_rv, 4), "jahre": jahre,
                        "monate": prof})
        hoch = max(prof.items(), key=lambda kv: kv[1]["rel"])
        tief = min(prof.items(), key=lambda kv: kv[1]["rel"])
        print("  %-10s %-16s Vola %5.1f%%  %d J  |  ruhigster %s (%.2f)  "
              "unruhigster %s (%.2f)"
              % (ticker, name, median_rv * 100, jahre,
                 MONATSNAMEN[tief[0]][:3], tief[1]["rel"],
                 MONATSNAMEN[hoch[0]][:3], hoch[1]["rel"]))

    if not profile:
        print("\nKeine auswertbaren Reihen.")
        return 1

    # ── Der eine vorab festgelegte Test ────────────────────────────────────
    print()
    print("=" * 76)
    print("VORAB FESTGELEGTE HYPOTHESE")
    print("  H1: Die Volatilität des S&P 500 (%s, ab %s) ist im September"
          % (HYPOTHESE_TICKER, HYPOTHESE_AB))
    print("      und Oktober höher als im Rest des Jahres.")
    print("      EIN Ticker, EIN Monatspaar, einseitig. Alles andere unten ist")
    print("      Beschreibung ohne p-Wert.")
    print("=" * 76)

    # Die Hypothesenreihe wird EIGENS geladen und nicht aus der
    # Anzeigeauswahl genommen: sie hat ihren eigenen Basiswert und ihren
    # eigenen Startzeitpunkt, und sie darf nicht davon abhaengen, welche
    # Ticker gerade in der Tabelle stehen.
    test = {}
    try:
        h_ym, h_werte = monatswerte(HYPOTHESE_TICKER, ab=HYPOTHESE_AB)
    except Exception as e:
        h_ym, h_werte = [], []
        print("  Hypothesenreihe %s nicht ladbar: %s"
              % (HYPOTHESE_TICKER, str(e)[:60]))
    if h_werte:
        test = pruefe_hypothese(h_ym, h_werte, HYPOTHESE_MONATE)
        if "fehler" in test:
            print("  %s: %s" % (HYPOTHESE_TICKER, test["fehler"]))
        else:
            print("  %s: Sep+Okt liegen bei dem %.3f-fachen des übrigen Jahres."
                  % (HYPOTHESE_TICKER, test["verhaeltnis"]))
            print("  Zufall liefert im Median %.3f, in 5 %% der Fälle %.3f oder mehr."
                  % (test["null_median"], test["null_p95"]))
            print("  p = %.4f  (%d zirkuläre Verschiebungen, einseitig, Plus-eins)"
                  % (test["p"], test["runden"]))
            print()
            print("  %s" % ("H1 gestützt." if test["p"] < 0.05 else
                            "H1 NICHT gestützt — der Unterschied liegt im "
                            "Bereich des Zufalls."))
    else:
        print("  %s nicht ladbar — Test NICHT gelaufen." % HYPOTHESE_TICKER)

    # ── Beschreibung: wo liegen die Monate quer über die Anlageklassen ─────
    print()
    print("Monatsprofil, normiert auf die eigene Normalvolatilität "
          "(1,00 = eigener Median):")
    print("  %-16s %s" % ("", " ".join("%5s" % MONATSNAMEN[m][:3]
                                       for m in range(1, 13))))
    for p in profile[:25]:
        zeile = " ".join(
            ("%5.2f" % p["monate"][m]["rel"]) if m in p["monate"] else "    ·"
            for m in range(1, 13))
        print("  %-16s %s" % (p["name"][:16], zeile))

    print()
    print("Diese Tabelle ist BESCHREIBEND. Sie trägt keine p-Werte, weil 12")
    print("Monate mal %d Reihen %d Fragen wären — da findet man immer etwas."
          % (len(profile), 12 * len(profile)))

    if a.json:
        ziel = pathlib.Path(a.json)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(json.dumps({
            "stand": max(ym[-1] for ym, _ in roh.values()),
            "methode": "Streuung der Monats-Renditen um null, annualisiert",
            "min_tage_monat": MIN_TAGE_MONAT,
            "runden": RUNDEN,
            "min_jahre": MIN_JAHRE,
            "hypothese": {
                "text": ("Die Volatilität des S&P 500 ist im September und "
                         "Oktober höher als im Rest des Jahres."),
                "ticker": HYPOTHESE_TICKER,
                "ab": HYPOTHESE_AB,
                "n_monate": len(h_werte),
                "monate": list(HYPOTHESE_MONATE),
                "einseitig": True,
                **test,
            },
            "profile": profile,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nJSON: %s" % ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
