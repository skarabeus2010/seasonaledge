#!/usr/bin/env python3
"""
expected_move_kalibrierung.py — Taugt der Expected Move als Erwartung?

    py -3.14 scripts/research/expected_move_kalibrierung.py --json <datei>

DIE FRAGE: Wir zeigen auf `/skew` täglich einen Expected Move an, abgeleitet aus
der 30-Tage-ATM-IV. Geprüft hat nie jemand, ob diese Zahl hält, was ihr Name
verspricht. Ein 1-Sigma-Band soll unter einer kalibrierten Normalverteilung in
**68,3 %** der Fälle halten. Tut es das?

Eine Kennzahl, die wir selbst anzeigen, auf ihre Vertrauenswürdigkeit zu prüfen,
ist das Mindeste — und das Ergebnis ist in BEIDE Richtungen veröffentlichbar:
„der Expected Move ist gut kalibriert" wäre eine Aussage, „er ist systematisch
zu weit" wäre eine bessere.

WARUM DER VIX UND NICHT UNSERE EIGENE iv_atm — das ist die entscheidende
Design-Entscheidung:

    Unsere Optionshistorie reicht für SPY vom 08.09.2025 bis 18.09.2026, das
    sind 165 Punkte. Bei einem Vorwärtsfenster von 21 Handelstagen und
    täglichem Abstand bleiben daraus rund ACHT unabhängige Fenster. Acht.
    Darauf eine Kalibrierungsaussage zu stützen wäre genau die Sorte Zahl, die
    diese Woche schon die Intermarket-Matrix gekostet hat.

    Der VIX ist definitionsgemäss dieselbe Grösse — die 30-Tage-IV des S&P 500 —
    und liegt ab 1990 vor. Das sind rund 430 unabhängige Fenster statt acht.

    Unsere eigene iv_atm wird trotzdem gerechnet, aber als ZWEITES und mit
    klarer Kennzeichnung: als Gegenprobe im überlappenden Jahr. Sie beantwortet
    nicht die Kalibrierungsfrage, sondern eine andere, ebenfalls nützliche —
    ob unsere Rekonstruktion dasselbe misst wie der Marktstandard.

DIE VORAB FESTGELEGTE HYPOTHESE (eine, gerichtet):

    H1: Der aus dem VIX abgeleitete 1-Sigma-Expected-Move deckt die tatsächliche
        21-Handelstage-Bewegung des S&P 500 HÄUFIGER ab als die 68,3 %, die eine
        kalibrierte Normalverteilung verlangt.

Die Richtung steht vorab fest und ist nicht geraten: Implizite Vola liegt im
Mittel über der realisierten (Varianzrisikoprämie), ein daraus gebautes Band
sollte also zu weit sein. Genau das prüfen wir — und wenn es NICHT so ist, ist
das die interessantere Meldung.

WARUM ^GSPC UND NICHT SPY als Basiswert: Der VIX wird auf den S&P-500-INDEX
gerechnet, und der ist ein Kursindex ohne Dividenden. SPY ist dividenden-
bereinigt und hat deshalb eine systematisch andere Renditereihe. Die beiden zu
mischen hiesse, eine Vola-Erwartung gegen die Bewegung eines anderen
Instruments zu halten.

ÜBERLAPPENDE FENSTER: Der Punktschätzer nutzt jeden Handelstag, das ist die
effizienteste Verwendung der Daten. Das Konfidenzintervall darf das NICHT tun —
zwei Fenster, die einen Tag auseinanderliegen, teilen 20 von 21 Tagen. Deshalb
Block-Bootstrap über nicht überlappende Blöcke, plus eine strikt
nicht-überlappende Teilstichprobe (jeder 21. Tag) als Gegenprobe.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import statistics
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from shared.data import KursreiheFehlt, lade_closes                  # noqa: E402
from shared.realized_vol import iso_tag                              # noqa: E402

HORIZONT = 21                # Handelstage ~ 30 Kalendertage
KALENDERTAGE = 30            # Laufzeit, auf die der VIX normiert ist
SOLL_DECKUNG = 0.6827        # 1 Sigma unter Normalverteilung
BOOTSTRAP = 2000
SIGMA_STUFEN = (0.5, 1.0, 1.5, 2.0)
BASIS = "^GSPC"
IMPLIZIT = "^VIX"


def reihen(ticker: str) -> dict[str, float]:
    daten, closes = lade_closes(ticker)
    return {iso_tag(d): float(c) for d, c in zip(daten, closes)
            if c is not None and math.isfinite(float(c)) and float(c) > 0}


def beobachtungen() -> list[dict]:
    """Je Handelstag: erwartete und tatsächliche Bewegung über HORIZONT Tage."""
    kurs, vix = reihen(BASIS), reihen(IMPLIZIT)
    tage = sorted(set(kurs) & set(vix))
    out = []
    for i in range(len(tage) - HORIZONT):
        t = tage[i]
        iv = vix[t] / 100.0
        if not (0.01 < iv < 3.0):
            continue
        # Expected Move als 1-Sigma-Bewegung ueber die Restlaufzeit. Die
        # Wurzelzeit-Skalierung nimmt KALENDERTAGE/365, weil der VIX auf
        # 30 Kalendertage normiert ist — nicht Handelstage/252. Die beiden
        # Konventionen unterscheiden sich um rund 4 %, und wer sie mischt,
        # verschiebt die Deckung systematisch.
        em = iv * math.sqrt(KALENDERTAGE / 365.0)
        r = math.log(kurs[tage[i + HORIZONT]] / kurs[t])
        out.append({"tag": t, "em": em, "rendite": r, "abs": abs(r),
                    "gedeckt": abs(r) <= em, "iv": iv})
    return out


def deckung(beob: list[dict], faktor: float = 1.0) -> float:
    if not beob:
        return float("nan")
    return sum(1 for b in beob if b["abs"] <= faktor * b["em"]) / len(beob)


def block_bootstrap(beob: list[dict], faktor: float = 1.0) -> tuple[float, float]:
    """Konfidenzintervall der Deckung ueber nicht ueberlappende Bloecke.

    Blocklaenge = HORIZONT: zwei Beobachtungen, die weiter als 21 Tage
    auseinanderliegen, teilen kein einziges Renditefenster mehr. Gezogen werden
    ganze Bloecke mit Zuruecklegen, damit die Abhaengigkeit INNERHALB eines
    Blocks erhalten bleibt.
    """
    bloecke = [beob[i:i + HORIZONT] for i in range(0, len(beob), HORIZONT)]
    bloecke = [b for b in bloecke if b]
    if len(bloecke) < 20:
        return float("nan"), float("nan")
    rnd = random.Random(20260922)
    werte = []
    for _ in range(BOOTSTRAP):
        zieh = [x for _ in range(len(bloecke))
                for x in bloecke[rnd.randrange(len(bloecke))]]
        werte.append(deckung(zieh, faktor))
    werte.sort()
    return (werte[int(0.025 * (len(werte) - 1))],
            werte[int(0.975 * (len(werte) - 1))])


def eigene_iv_gegenprobe(pfad: pathlib.Path | None = None) -> dict:
    """Misst unsere rekonstruierte iv_atm dasselbe wie der VIX?

    KEINE Kalibrierungsaussage — dafuer ist die Reihe zu kurz. Die Frage ist
    eine andere: laeuft unsere eigene Rekonstruktion mit dem Marktstandard
    mit, oder driftet sie? Ein systematischer Versatz waere ein Pipeline-Fehler
    und kein Marktphaenomen.
    """
    # Die Datei ist gitignored und wird vom Cron geschrieben. Ein lokaler
    # Checkout hat deshalb entweder gar keine oder monatealte Reste — beim
    # ersten Lauf hier waren es 57 statt 165 SPY-Punkte, wovon nur 19
    # brauchbar. Wer die Gegenprobe ernst meint, uebergibt --history mit der
    # LIVE gezogenen Datei:
    #   curl -sf -o /tmp/h.json https://seasonalpha.ai/landing/data/options_skew_history.json
    pfad = pfad or (_ROOT / "landing" / "data" / "options_skew_history.json")
    if not pfad.exists():
        return {"fehler": "options_skew_history.json nicht vorhanden"}
    try:
        hist = json.loads(pfad.read_text(encoding="utf-8"))
    except Exception as e:
        return {"fehler": str(e)[:80]}
    punkte = hist.get("SPY") or []
    vix = reihen(IMPLIZIT)

    paare = []
    for p in punkte:
        t, iv = p.get("date"), p.get("iv_atm")
        # Nur laufzeitnormierte Punkte: 'single' misst den Frontmonat mit
        # wechselnder Restlaufzeit und ist mit einer 30-Tage-Groesse nicht
        # vergleichbar.
        if not t or not iv or p.get("cm_mode") not in ("cm", "cm_extrap"):
            continue
        if t in vix:
            paare.append((t, float(iv), vix[t] / 100.0))
    if len(paare) < 30:
        return {"n": len(paare), "quelle": str(pfad),
                "fehler": "zu wenige vergleichbare Punkte (lokale Datei "
                          "vermutlich veraltet — siehe --history)"}

    diff = [a - b for _, a, b in paare]
    quot = [a / b for _, a, b in paare if b > 0]

    # DER NIVEAUABSTAND IST KEIN FEHLER, sondern Konstruktion. Der VIX ist
    # keine ATM-Vola: er wird als varianzswap-aehnliche Groesse ueber den
    # GANZEN OTM-Strip gerechnet. Weil Aktien-Smiles nach unten schief sind,
    # ziehen die OTM-Puts den VIX systematisch UEBER die ATM-IV. Ein erster
    # Entwurf dieses Checks warnte bei mehr als 2 Vol-Punkten Abstand und
    # haette damit ein Lehrbuchphaenomen als Pipeline-Defekt gemeldet.
    #
    # Was wirklich interessiert: laeuft unsere Reihe MIT dem Marktstandard?
    # Das beantwortet die Korrelation der TAGESAENDERUNGEN — sie ist
    # niveau-unabhaengig. Driftet unsere Rekonstruktion, bricht sie ein;
    # ein konstanter Skew-Abstand stoert sie nicht.
    paare.sort(key=lambda x: x[0])
    d_eigen = [paare[i][1] - paare[i - 1][1] for i in range(1, len(paare))]
    d_vix = [paare[i][2] - paare[i - 1][2] for i in range(1, len(paare))]
    korr = None
    if len(d_eigen) > 10:
        try:
            korr = round(statistics.correlation(d_eigen, d_vix), 3)
        except Exception:
            korr = None

    return {
        "n": len(paare),
        "von": paare[0][0], "bis": paare[-1][0],
        "median_eigene": round(statistics.median(a for _, a, _ in paare), 4),
        "median_vix": round(statistics.median(b for _, _, b in paare), 4),
        "median_differenz_pts": round(statistics.median(diff) * 100, 3),
        "median_verhaeltnis": round(statistics.median(quot), 4),
        "korr_tagesaenderungen": korr,
        "hinweis": ("Der Niveauabstand ist erwartet: der VIX rechnet ueber den "
                    "gesamten OTM-Strip und liegt wegen der Skew-Schiefe ueber "
                    "der ATM-IV. Aussagekraeftig ist die Korrelation der "
                    "Tagesaenderungen."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--history", help="options_skew_history.json (live gezogen)")
    a = ap.parse_args()

    try:
        beob = beobachtungen()
    except (KursreiheFehlt, Exception) as e:
        print("Kursreihen fehlen: %s" % e)
        return 1
    if len(beob) < 500:
        print("Zu wenige Beobachtungen: %d" % len(beob))
        return 1

    bloecke = math.ceil(len(beob) / HORIZONT)
    print("Expected-Move-Kalibrierung: %s gegen %s" % (IMPLIZIT, BASIS))
    print("  %s bis %s · %d Handelstage · Horizont %d HT"
          % (beob[0]["tag"], beob[-1]["tag"], len(beob), HORIZONT))
    print("  ~%d nicht überlappende Fenster — das ist die Zahl, die zählt,"
          % bloecke)
    print("  nicht die %d überlappenden." % len(beob))
    print()

    ist = deckung(beob)
    lo, hi = block_bootstrap(beob)
    print("=" * 74)
    print("VORAB FESTGELEGTE HYPOTHESE")
    print("  H1: Das 1-Sigma-Band deckt HÄUFIGER als die geforderten %.1f %%."
          % (SOLL_DECKUNG * 100))
    print("=" * 74)
    print("  gemessene Deckung: %.1f %%   (95-%%-Intervall %.1f bis %.1f %%)"
          % (ist * 100, lo * 100, hi * 100))
    print("  gefordert bei kalibrierter Normalverteilung: %.1f %%"
          % (SOLL_DECKUNG * 100))
    gestuetzt = lo > SOLL_DECKUNG
    print()
    if gestuetzt:
        print("  H1 GESTÜTZT: das Band ist systematisch zu weit. Der Expected")
        print("  Move überschätzt die tatsächliche Bewegung — anders gesagt,")
        print("  Optionen sind im Mittel zu teuer (Varianzrisikoprämie).")
    elif hi < SOLL_DECKUNG:
        print("  H1 WIDERLEGT, und zwar in die andere Richtung: das Band ist zu")
        print("  ENG. Der Expected Move unterschätzt die Bewegung.")
    else:
        print("  H1 nicht entschieden: das Intervall schliesst %.1f %% ein."
              % (SOLL_DECKUNG * 100))

    # Strikt nicht überlappende Gegenprobe
    strikt = beob[::HORIZONT]
    print()
    print("  Gegenprobe ohne jede Überlappung (jeder %d. Tag, n = %d): %.1f %%"
          % (HORIZONT, len(strikt), deckung(strikt) * 100))

    # Beschreibung: die ganze Kalibrierungskurve
    print()
    print("Kalibrierungskurve — Deckung je Bandbreite:")
    print("  %-10s %10s %10s %s" % ("Band", "gemessen", "Soll", "Abweichung"))
    kurve = []
    for f in SIGMA_STUFEN:
        d = deckung(beob, f)
        # Soll unter Normalverteilung: P(|Z| <= f)
        soll = math.erf(f / math.sqrt(2))
        kurve.append({"sigma": f, "gemessen": round(d, 4), "soll": round(soll, 4)})
        print("  %-10s %9.1f %% %9.1f %% %+9.1f pp"
              % ("%.1f Sigma" % f, d * 100, soll * 100, (d - soll) * 100))

    # Gegenprobe der eigenen Pipeline
    print()
    print("-" * 74)
    print("GEGENPROBE: misst unsere eigene iv_atm dasselbe wie der VIX?")
    print("  (kurze Reihe — KEINE Kalibrierungsaussage, nur ein Pipeline-Check)")
    gp = eigene_iv_gegenprobe(pathlib.Path(a.history) if a.history else None)
    if "fehler" in gp:
        print("  entfällt: %s" % gp["fehler"])
    else:
        print("  %d gemeinsame Tage, %s bis %s" % (gp["n"], gp["von"], gp["bis"]))
        print("  Median eigene iv_atm %.1f %%  ·  Median VIX %.1f %%"
              % (gp["median_eigene"] * 100, gp["median_vix"] * 100))
        print("  Median-Differenz %+.2f Vol-Punkte  (Verhältnis %.3f)"
              % (gp["median_differenz_pts"], gp["median_verhaeltnis"]))
        print("  Der Abstand ist ERWARTET: der VIX rechnet über den ganzen")
        print("  OTM-Strip und liegt wegen der Skew-Schiefe über der ATM-IV.")
        k = gp.get("korr_tagesaenderungen")
        if k is None:
            print("  Korrelation der Tagesänderungen: nicht berechenbar.")
        else:
            print("  Korrelation der Tagesänderungen: %.3f — DAS ist der"
                  " eigentliche Check." % k)
            if k < 0.7:
                print("  ⚠ Unter 0,70: unsere Reihe läuft nicht sauber mit.")
            else:
                print("  Die Rekonstruktion läuft mit dem Marktstandard mit.")

    if a.json:
        ziel = pathlib.Path(a.json)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(json.dumps({
            "basis": BASIS, "implizit": IMPLIZIT,
            "von": beob[0]["tag"], "bis": beob[-1]["tag"],
            "n_ueberlappend": len(beob), "n_bloecke": bloecke,
            "horizont_ht": HORIZONT, "kalendertage": KALENDERTAGE,
            "soll_deckung": SOLL_DECKUNG,
            "hypothese": {
                "text": ("Das 1-Sigma-Band aus dem VIX deckt die tatsächliche "
                         "21-Handelstage-Bewegung häufiger ab als 68,3 %."),
                "einseitig": True,
                "deckung": round(ist, 4),
                "ci95": [round(lo, 4), round(hi, 4)],
                "gestuetzt": bool(gestuetzt),
            },
            "strikt_ohne_ueberlappung": {
                "n": len(strikt), "deckung": round(deckung(strikt), 4)},
            "kalibrierungskurve": kurve,
            "eigene_iv_gegenprobe": gp,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nJSON: %s" % ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
