#!/usr/bin/env python3
"""
next_day_range.py — Was sagt der Optionsmarkt über die Spanne von morgen?

    py -3.14 scripts/research/next_day_range.py --json <datei>

DIE IDEE: Am Schluss den Straddle nehmen, der am nächsten Verfallstag liegt, und
daraus die Spanne des nächsten Tages vorhersagen. Ein Straddle kostet ungefähr,
was der Markt als mittlere absolute Bewegung erwartet — er ist also eine
Prognose, die man ablesen statt schätzen kann.

DREI DINGE MÜSSEN DAFÜR AUSEINANDERGEHALTEN WERDEN, und das ist der Grund, warum
dieses Skript zuerst etwas anderes misst als den Straddle:

  1. SPANNE IST NICHT BEWEGUNG. Ein Straddle bepreist die Endverteilung, also
     |Schlusskurs morgen − Schlusskurs heute|. Die Tagesspanne Hoch-minus-Tief
     ist systematisch GRÖSSER, weil sie den Weg misst und nicht das Ziel. Für
     eine Brownsche Bewegung ohne Drift gilt E[Spanne] = σ·√(8/π) gegen
     E|Bewegung| = σ·√(2/π) — die Spanne ist im Erwartungswert das DOPPELTE.
     Wer einen Straddlepreis direkt als Spannenprognose liest, liegt um den
     Faktor zwei daneben.

  2. DIE ÜBERNACHTLÜCKE. Ein Straddle, der über Nacht gehalten wird, deckt die
     Lücke mit ab. Die Spanne Hoch-minus-Tief einer Sitzung tut das NICHT. Beide
     Grössen werden hier gerechnet, dazu eine dritte, die zum Straddle passt:
     die Spanne einschliesslich des Vortagsschlusses.

  3. NORMALVERTEILUNG IST EINE ANNAHME. Die Faktoren √(2/π) und √(8/π) gelten
     für eine Brownsche Bewegung. Kursreihen haben dickere Enden. Deshalb werden
     die Faktoren hier nicht vorausgesetzt, sondern GEMESSEN.

WAS DIESES SKRIPT DESHALB TUT: Es misst die Umrechnung an 36 Jahren, mit dem
VIX als impliziter Erwartung — der ist die einzige implizite Vola, die wir so
weit zurück haben. Damit stehen (a) die empirischen Faktoren, die ein
Straddlepreis braucht, um eine Spannenprognose zu werden, und (b) die Messlatte,
die ein Front-Straddle schlagen muss, um besser zu sein als „VIX auf einen Tag
skaliert".

WAS ES NOCH NICHT TUT: den Front-Straddle auswerten. Dafür braucht es dessen
Preis am Schluss, und den archivieren wir nicht — die Options-Snapshots liefern
ihn täglich, aber weggeschrieben wird nur IV, Skew und VRP. Der Teil steht als
eigener Schritt aus; `--straddle-archiv` liest ihn, sobald es ihn gibt.

DIE VORAB FESTGELEGTE HYPOTHESE FÜR DEN MESSBAREN TEIL:

    H1: Die aus dem VIX abgeleitete Erwartung der absoluten Tagesbewegung ist
        systematisch ZU HOCH (dieselbe Varianzrisikoprämie, die schon beim
        30-Tage-Expected-Move einen Deckungsüberschuss von 16 Punkten erzeugte).
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

from shared.data import download_data                                # noqa: E402
from shared.realized_vol import iso_tag                              # noqa: E402

BASIS = "^GSPC"
IMPLIZIT = "^VIX"
HANDELSTAGE = 252
BOOTSTRAP = 2000

# Theoriewerte für eine Brownsche Bewegung ohne Drift, je Einheit sigma.
# Sie werden NICHT vorausgesetzt, sondern als Vergleichsmass ausgewiesen.
F_BEWEGUNG = math.sqrt(2.0 / math.pi)        # E|X|        ~ 0,7979
F_SPANNE = math.sqrt(8.0 / math.pi)          # E[max-min]  ~ 1,5958


def beobachtungen() -> list[dict]:
    """Je Handelstag t: implizite Tages-Sigma aus dem VIX, und was an t+1 kam."""
    kurs = download_data(BASIS)
    vix = download_data(IMPLIZIT)
    v = {iso_tag(i): float(r["Close"]) for i, r in vix.iterrows()
         if r["Close"] and math.isfinite(float(r["Close"]))}

    zeilen = []
    for i, r in kurs.iterrows():
        try:
            o, h, l, c = (float(r["Open"]), float(r["High"]),
                          float(r["Low"]), float(r["Close"]))
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(x) and x > 0 for x in (o, h, l, c)) or h < l:
            continue
        zeilen.append({"tag": iso_tag(i), "o": o, "h": h, "l": l, "c": c})

    out = []
    for i in range(len(zeilen) - 1):
        heute, morgen = zeilen[i], zeilen[i + 1]
        iv = v.get(heute["tag"])
        if iv is None or not (1.0 < iv < 300.0):
            continue
        sigma = (iv / 100.0) / math.sqrt(HANDELSTAGE)      # implizite Tages-Sigma
        p = heute["c"]

        # (1) was ein Straddle bepreist: Schluss zu Schluss, Luecke inklusive
        bewegung = abs(math.log(morgen["c"] / p))
        # (2) die Sitzungsspanne OHNE Luecke — das ist NICHT, was ein Straddle deckt
        spanne_intraday = (morgen["h"] - morgen["l"]) / p
        # (3) die Spanne MIT Luecke: der Straddle wird ueber Nacht gehalten, also
        #     zaehlt der Vortagsschluss als Startpunkt des Pfades mit
        hoch = max(morgen["h"], p)
        tief = min(morgen["l"], p)
        spanne_voll = (hoch - tief) / p

        out.append({"tag": heute["tag"], "sigma": sigma,
                    "bewegung": bewegung,
                    "spanne_intraday": spanne_intraday,
                    "spanne_voll": spanne_voll})
    return out


def faktor(beob: list[dict], feld: str) -> float:
    """Gemessener Faktor: Mittel(Ist) / Mittel(implizite Sigma).

    Als Verhaeltnis der MITTELWERTE, nicht als Mittel der Verhaeltnisse: an
    ruhigen Tagen ist sigma klein, und ein Quotient mit kleinem Nenner
    dominiert sonst den Durchschnitt.
    """
    s = statistics.fmean(b["sigma"] for b in beob)
    return statistics.fmean(b[feld] for b in beob) / s if s > 0 else float("nan")


def block_ci(beob: list[dict], feld: str, block: int = 21) -> tuple[float, float]:
    """Konfidenzintervall über Bloecke, weil Volatilitaet in Bloecken kommt."""
    bloecke = [beob[i:i + block] for i in range(0, len(beob), block)]
    bloecke = [b for b in bloecke if b]
    rnd = random.Random(20260922)
    werte = []
    for _ in range(BOOTSTRAP):
        zieh = [x for _ in range(len(bloecke))
                for x in bloecke[rnd.randrange(len(bloecke))]]
        werte.append(faktor(zieh, feld))
    werte.sort()
    return (werte[int(0.025 * (len(werte) - 1))],
            werte[int(0.975 * (len(werte) - 1))])


def straddle_teil(pfad: pathlib.Path | None) -> dict:
    """Der Front-Straddle-Teil — sobald ein Archiv existiert.

    Erwartetes Format: {"SPY": [{"date": "...", "spot": .., "straddle": ..,
    "dte": ..}, ...]}. `straddle` ist der Preis von Call+Put am Strike, der dem
    Spot am naechsten liegt, am naechstliegenden Verfallstag.
    """
    if pfad is None or not pfad.exists():
        return {"vorhanden": False,
                "hinweis": ("Kein Straddle-Archiv. Die taeglichen "
                            "Options-Snapshots enthalten die Preise, "
                            "weggeschrieben wird aber nur IV/Skew/VRP. "
                            "Der Archivierungsschritt fehlt noch.")}
    try:
        arch = json.loads(pfad.read_text(encoding="utf-8"))
    except Exception as e:
        return {"vorhanden": False, "hinweis": str(e)[:80]}
    n = sum(len(v) for v in arch.values() if isinstance(v, list))
    return {"vorhanden": True, "n_punkte": n, "ticker": sorted(arch),
            "hinweis": ("Auswertung folgt, sobald genug Punkte vorliegen — "
                        "bei taeglicher Archivierung braucht ein Jahr ein Jahr.")
            if n < 250 else "genug Punkte fuer eine erste Auswertung"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    ap.add_argument("--straddle-archiv")
    a = ap.parse_args()

    beob = beobachtungen()
    if len(beob) < 500:
        print("Zu wenige Beobachtungen: %d" % len(beob))
        return 1

    print("Spanne des naechsten Tages gegen implizite Erwartung")
    print("  %s gegen %s · %s bis %s · %d Tage\n"
          % (BASIS, IMPLIZIT, beob[0]["tag"], beob[-1]["tag"], len(beob)))

    felder = [
        ("bewegung", "|Schluss zu Schluss|", F_BEWEGUNG,
         "das, was ein Straddle bepreist"),
        ("spanne_intraday", "Spanne Hoch-Tief", F_SPANNE,
         "OHNE Uebernachtluecke — passt NICHT zum Straddle"),
        ("spanne_voll", "Spanne inkl. Vortagsschluss", F_SPANNE,
         "mit Luecke — das ist der Pfad, den ein Straddle ueber Nacht sieht"),
    ]

    print("  %-30s %9s %9s %9s  %s"
          % ("Groesse", "gemessen", "Theorie", "Verhaeltnis", "95-%-Intervall"))
    ergebnis = []
    for feld, name, theorie, _ in felder:
        f = faktor(beob, feld)
        lo, hi = block_ci(beob, feld)
        ergebnis.append({"feld": feld, "name": name, "gemessen": round(f, 4),
                         "theorie": round(theorie, 4),
                         "verhaeltnis": round(f / theorie, 4),
                         "ci95": [round(lo, 4), round(hi, 4)]})
        print("  %-30s %9.4f %9.4f %9.3f  %.4f bis %.4f"
              % (name, f, theorie, f / theorie, lo, hi))
    print()
    for feld, name, _, kommentar in felder:
        print("    %-30s %s" % (name, kommentar))

    # ── Die vorab festgelegte Hypothese ────────────────────────────────────
    bew = ergebnis[0]
    print()
    print("=" * 74)
    print("VORAB FESTGELEGTE HYPOTHESE")
    print("  H1: Die implizite Erwartung der absoluten Tagesbewegung ist zu hoch.")
    print("=" * 74)
    print("  Erwartet bei kalibrierter impliziter Vola: Faktor %.4f" % F_BEWEGUNG)
    print("  Gemessen: %.4f  (95-%%-Intervall %.4f bis %.4f)"
          % (bew["gemessen"], bew["ci95"][0], bew["ci95"][1]))
    ueber = bew["ci95"][1] < F_BEWEGUNG
    if ueber:
        print()
        print("  H1 GESTUETZT: die tatsaechliche Bewegung liegt um %.0f %% unter"
              % ((1 - bew["verhaeltnis"]) * 100))
        print("  der impliziten Erwartung. Wer den Straddle kauft, zahlt im")
        print("  Mittel mehr, als der naechste Tag liefert.")
    elif bew["ci95"][0] > F_BEWEGUNG:
        print()
        print("  H1 WIDERLEGT, in die andere Richtung: die Bewegung ist GROESSER")
        print("  als implizit erwartet.")
    else:
        print()
        print("  H1 nicht entschieden: das Intervall schliesst %.4f ein."
              % F_BEWEGUNG)

    # ── Die Umrechnung, die ein Straddlepreis braucht ──────────────────────
    q_voll = ergebnis[2]["gemessen"] / bew["gemessen"]
    q_intra = ergebnis[1]["gemessen"] / bew["gemessen"]
    print()
    print("DIE UMRECHNUNG, die ein Straddlepreis in eine Spannenprognose braucht:")
    print("  Straddlepreis / Spot ist die erwartete |Schluss-zu-Schluss|-Bewegung.")
    print("  Gemessen liegt die Spanne inkl. Luecke beim %.3f-fachen davon," % q_voll)
    print("  die Sitzungsspanne ohne Luecke beim %.3f-fachen." % q_intra)
    print("  Theorie fuer eine Brownsche Bewegung waere 2,000 — gemessen %.3f."
          % q_voll)
    print("  Wer den Straddlepreis unverrechnet als Spanne liest, liegt also um")
    print("  rund den Faktor %.1f daneben." % q_voll)

    # ── Straddle-Teil ─────────────────────────────────────────────────────
    st = straddle_teil(pathlib.Path(a.straddle_archiv) if a.straddle_archiv else None)
    print()
    print("-" * 74)
    print("FRONT-STRADDLE (die eigentliche Idee)")
    if st["vorhanden"]:
        print("  Archiv gefunden: %d Punkte, %d Ticker"
              % (st["n_punkte"], len(st["ticker"])))
    print("  %s" % st["hinweis"])
    print("  Messlatte: er muss besser sein als der VIX auf einen Tag skaliert,")
    print("  und das heisst konkret — Faktor naeher an %.4f als %.4f."
          % (F_BEWEGUNG, bew["gemessen"]))

    if a.json:
        ziel = pathlib.Path(a.json)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(json.dumps({
            "basis": BASIS, "implizit": IMPLIZIT,
            "von": beob[0]["tag"], "bis": beob[-1]["tag"], "n": len(beob),
            "theorie": {"bewegung": round(F_BEWEGUNG, 4),
                        "spanne": round(F_SPANNE, 4)},
            "hypothese": {
                "text": ("Die implizite Erwartung der absoluten Tagesbewegung "
                         "ist systematisch zu hoch."),
                "einseitig": True, "gestuetzt": bool(ueber),
            },
            "faktoren": ergebnis,
            "umrechnung": {
                "spanne_voll_je_bewegung": round(q_voll, 4),
                "spanne_intraday_je_bewegung": round(q_intra, 4),
                "theorie": 2.0,
            },
            "front_straddle": st,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nJSON: %s" % ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
