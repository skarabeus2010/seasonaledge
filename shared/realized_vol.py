#!/usr/bin/env python3
"""
realized_vol.py — realisierte Volatilität, EINE Implementierung.

WARUM EIGENES MODUL: das VRP (Variance Risk Premium) ist IV minus realisierte
Vola. Die realisierte Seite wurde bisher nur im Live-Lauf gerechnet
(`compute_options_skew._realized_vol`), und die Historie trägt `vrp_pts`
deshalb nur in 793 von 6271 Zeilen — der Backfill schreibt es nicht. Wer das
nachrüstet, braucht dieselbe Formel für vergangene Tage. Sie ein zweites Mal
hinzuschreiben wäre genau der Fehler, der dieses Projekt schon mehrfach
getroffen hat: zwei Implementierungen derselben Mathematik driften
auseinander, und niemand merkt es, weil beide plausible Zahlen liefern.

Deshalb liegt der Kern hier, und sowohl der Live-Lauf als auch die Nachrüstung
rufen ihn auf. Auch die rollende Variante `rv_reihe` bildet die Returns mit
derselben Funktion und ruft denselben Kern — sie wiederholt nichts.

FORMEL (CBOE-Konvention):

    R_t = ln(P_t / P_{t-1})
    RV  = sqrt( 252/(N-1) · Σ(R_t − R̄)² )

Also Stichproben-Varianz (÷ N−1, nicht ÷ N) über die letzten N Log-Returns,
annualisiert mit √252. N=21 entspricht einem Monat und passt damit zur
30-Kalendertage-ATM-IV — der Horizont MUSS zusammenpassen, sonst vergleicht
das VRP zwei verschiedene Zeiträume (genau das war der Fehler in v52.0:
30 Handelstage gegen 30 Kalendertage, SPY-VRP sprang dadurch von +0,6 auf +4,2).

LÜCKEN: ein fehlender oder nicht-positiver Kurs macht den Return unbrauchbar.
Er wird als None geführt, und ein Fenster mit einem None liefert KEINE RV.
Ihn stattdessen zu überspringen würde zwei Tage zu einem Return
zusammenziehen — die Reihe enthielte dann Returns verschiedener Horizonte,
ohne dass es auffällt. Ein fehlender Wert ist ehrlicher als ein falscher.
"""
from __future__ import annotations

import math

# Handelstage im Jahr, für die Annualisierung.
HANDELSTAGE_JAHR = 252

# Standard-Fenster: 21 Handelstage = 1 Monat, passend zur 30d-IV.
RV_FENSTER = 21


def iso_tag(x) -> str:
    """Kalendertag eines Datums/Zeitstempels als ISO-String.

    Gegen den Fallstrick, der am 2026-09-18 im Live-Lauf zuschlug: die
    Kursreihe kommt mit einem DatetimeIndex, dessen Werte eine UHRZEIT tragen
    (`Timestamp('2026-09-18 13:30:00')` = NYSE-Open in UTC). Ein Vergleich
    `index <= "2026-09-18"` wird zu `<= 2026-09-18 00:00:00` und schneidet die
    Session damit WEG — die realisierte Vola lief auf einem Fenster, das einen
    Handelstag zu frueh endete, und der Frische-Waechter meldete jeden Tag eine
    veraltete Reihe, obwohl der Tag vorhanden war.
    """
    return str(x)[:10]


def log_returns(closes) -> list[float | None]:
    """Log-Returns einer Kursreihe, mit None für unbrauchbare Paare.

    Das Ergebnis ist um eins kürzer als `closes`: Element j gehört zum Kurs
    closes[j+1], weil ein Return zwei Kurse braucht.
    """
    r: list[float | None] = []
    for i in range(1, len(closes)):
        a, b = closes[i - 1], closes[i]
        try:
            a = float(a)
            b = float(b)
        except (TypeError, ValueError):
            r.append(None)
            continue
        # math.isfinite schliesst NaN UND +-inf aus. `a > 0 and a == a` allein
        # liess inf durch (inf > 0 ist wahr, inf == inf ist wahr) und erzeugte
        # dann eine NaN-Varianz statt eines fehlenden Wertes.
        if math.isfinite(a) and math.isfinite(b) and a > 0 and b > 0:
            r.append(math.log(b / a))
        else:
            r.append(None)
    return r


def rv_aus_returns(returns, n: int = RV_FENSTER) -> float | None:
    """Annualisierte realisierte Vola aus den LETZTEN n Log-Returns.

    None, wenn weniger als n Returns vorliegen oder das Fenster eine Lücke
    enthält. Bewusst kein Rechnen auf einem kürzeren Fenster: eine RV aus
    8 Tagen neben einer aus 21 in derselben Reihe ist nicht vergleichbar, und
    ein Perzentil daraus wäre Unsinn.
    """
    if n < 2 or returns is None or len(returns) < n:
        return None
    seg = list(returns[-n:])
    if any(x is None for x in seg):
        return None
    m = sum(seg) / n
    var = sum((x - m) ** 2 for x in seg) / (n - 1)      # Stichproben-Varianz
    return round(math.sqrt(var) * math.sqrt(HANDELSTAGE_JAHR), 4)


def rv_aus_closes(closes, n: int = RV_FENSTER) -> float | None:
    """Annualisierte realisierte Vola über die letzten n Handelstage.

    Braucht n+1 Kurse für n Returns.
    """
    if closes is None or len(closes) < n + 1:
        return None
    return rv_aus_returns(log_returns(closes), n)


def rv_reihe(daten, closes, n: int = RV_FENSTER) -> dict:
    """Rollende RV je Handelstag: {datum: rv}.

    Für die Nachrüstung vergangener Tage. Der Wert zu einem Datum benutzt die
    n Returns BIS EINSCHLIESSLICH dieses Tages — dieselbe Blickrichtung wie im
    Live-Lauf, wo die RV der Session gegen die IV derselben Session gestellt
    wird. Tage ohne volles, lückenfreies Fenster fehlen im Ergebnis.

    `daten` und `closes` müssen gleich lang und aufsteigend sortiert sein.
    """
    if daten is None or closes is None or len(daten) != len(closes):
        raise ValueError("daten und closes muessen gleich lang sein")
    # Streng aufsteigend und eindeutig — sonst landet ein Wert still am
    # falschen Tag: das Ergebnis ist ein dict nach ISO-Tag, doppelte Tage
    # ueberschreiben sich, und eine unsortierte Reihe rechnet das Fenster
    # ueber die falschen Nachbarn.
    tage = [iso_tag(x) for x in daten]
    for i in range(1, len(tage)):
        if tage[i] <= tage[i - 1]:
            raise ValueError(
                "daten muessen streng aufsteigend und eindeutig sein "
                "(%s nach %s an Position %d)" % (tage[i], tage[i - 1], i))
    returns = log_returns(closes)                    # dieselbe Funktion wie oben
    out = {}
    # returns[j] gehoert zu closes[j+1]; der Tag closes[i] hat die Returns
    # returns[0..i-1] hinter sich. Genau dieses Praefix geben wir dem Kern,
    # der daraus die letzten n nimmt — identisch zum Live-Pfad.
    for i in range(1, len(closes)):
        rv = rv_aus_returns(returns[:i], n)
        if rv is not None:
            out[tage[i]] = rv
    return out


def kappe_auf(daten, closes, bis: str | None):
    """Reihe auf den Kalendertag `bis` einschliesslich kuerzen.

    Vergleicht ISO-Tage, nicht Zeitstempel — siehe iso_tag(). `bis=None`
    laesst die Reihe unveraendert.
    """
    if daten is None or closes is None or len(daten) != len(closes):
        raise ValueError("daten und closes muessen gleich lang sein")
    d = [iso_tag(x) for x in daten]
    if not bis:
        return d, list(closes)
    behalten = [i for i, x in enumerate(d) if x <= bis]
    return [d[i] for i in behalten], [closes[i] for i in behalten]
