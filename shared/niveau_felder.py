"""Feldzustände und Strike-Stufe für die Options-Niveaus (Spec B1).

Ein Niveau — Call Wall, Put Wall, Vol-Trigger, Max Pain — kann aus drei verschiedenen
Gründen fehlen, und die Darstellung muss sie unterscheiden können:

* es gibt **regulär** keines (kein Gamma mit passendem Vorzeichen auf der richtigen
  Spot-Seite, kein Nulldurchgang im Suchbereich) — das ist ein Ergebnis, kein Fehler
  (`shared`-fremd nachzulesen in `compute_gamma_exposure._walls`),
* die Kette war **unvollständig** geladen, also ist der Wert nicht beurteilbar,
* die **Quelle fehlt** ganz (kein GEX-Lauf dieser Session, kein Kettenabruf).

Vorher gab es nur „Wert da" oder „Wert weg". Damit sah eine korrekt fehlende Put Wall
genauso aus wie ein gescheiterter Abruf, und ein aus einer halben Kette gerechneter Wert
sah vollständig aus. Siehe docs/KEY_LEVELS_CHART.md, Abschnitte 3 und 6.1.

Die Strike-Stufe wird hier mitberechnet, weil sie dieselbe Herkunft hat (die ausgewertete
Kette) und die Spec sie als Pflichteingabe der Preisprüfung führt (Abschnitt 2.2a).
"""
from __future__ import annotations

import math

# Zustände eines einzelnen Niveaus. Reihenfolge = Rangfolge der Aussagekraft.
Z_OK = "ok"                        # berechnet, Wert vorhanden
Z_KEIN_NIVEAU = "kein_niveau"      # regulär berechnet, es existiert kein solches Niveau
Z_NICHT_EINDEUTIG = "nicht_eindeutig"   # berechnet, aber mehrdeutig (Max Pain)
Z_TEILKETTE = "teilkette"          # aus unvollständig geladener Kette
Z_QUELLE_FEHLT = "quelle_fehlt"    # Kette/GEX-Zeile nicht vorhanden
Z_NICHT_ERHOBEN = "nicht_erhoben"  # zu dieser Beobachtung nie erhoben (Altdaten)

ZUSTAENDE = (Z_OK, Z_KEIN_NIVEAU, Z_NICHT_EINDEUTIG, Z_TEILKETTE, Z_QUELLE_FEHLT,
             Z_NICHT_ERHOBEN)

# Nur diese beiden Zustände werden gezeichnet (Spec 6.1, EINE Zeichenregel).
ZEICHENBAR = (Z_OK, Z_NICHT_EINDEUTIG)


def feldzustand(wert, kette_vollstaendig, *, quelle_da: bool = True,
                mehrdeutig: bool = False) -> str:
    """Zustand eines Niveaus.

    `kette_vollstaendig` ist dreiwertig: True (Kette ganz geladen), False (abgebrochen),
    None (unbekannt — etwa eine Altzeile). None wird wie False behandelt, weil ein
    unbekannter Ladezustand einen Wert nicht beurteilbar macht; die Unterscheidung
    zwischen „abgebrochen" und „unbekannt" steht in der Zeile selbst, nicht im Zustand.

    Die Reihenfolge der Prüfungen ist Teil des Vertrags: fehlende Quelle schlägt alles,
    danach die unvollständige Kette (ein fehlender Wert aus einer halben Kette ist NICHT
    als reguläres Fehlen zu lesen), dann erst Wert und Mehrdeutigkeit.
    """
    if not quelle_da:
        return Z_QUELLE_FEHLT
    if not kette_vollstaendig:
        return Z_TEILKETTE
    if wert is None:
        return Z_KEIN_NIVEAU
    if mehrdeutig:
        return Z_NICHT_EINDEUTIG
    return Z_OK


def zeichenbar(zustand: str) -> bool:
    """Darf dieses Niveau gezeichnet werden? Eine Regel, an einer Stelle."""
    return zustand in ZEICHENBAR


def strike_stufe(strikes) -> float | None:
    """Kleinster Abstand zweier benachbarter Strikes der ausgewerteten Kette.

    Maßgeblich ist die GEX-Kette (alle Kontrakte im Horizont), nicht die separat geladene
    Max-Pain-Kette eines einzelnen Verfalls — die Walls, auf die sich die Toleranz in
    Spec 2.2a bezieht, entstehen aus der GEX-Kette, und eine andere Grundmenge ergäbe
    eine andere Stufe.

    Rückgabe None, wenn sich kein endlicher positiver Abstand ergibt (ein einziger Strike,
    nicht endliche Werte, leere Liste). None heißt in der Spec: Session unbelegt, Linien
    aus — ausdrücklich KEIN geratener Standardwert.
    """
    sauber = set()
    for k in strikes or ():
        try:
            f = float(k)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f):
            sauber.add(f)
    if len(sauber) < 2:
        return None
    sortiert = sorted(sauber)
    # Rundung auf 6 Stellen, weil Strikes als Gleitkommazahlen aus JSON kommen und ein
    # Abstand von 0,5 dort als 0,4999999999999996 auftreten kann.
    abstaende = [round(b - a, 6) for a, b in zip(sortiert, sortiert[1:])]
    positiv = [d for d in abstaende if d > 0]
    return min(positiv) if positiv else None
