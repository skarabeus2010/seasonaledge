"""Eingefrorene Momentaufnahme der OPEX-/VIX-Termine — Bestandsschutz fuer V3.

    py -3.14 scripts/opex_momentaufnahme.py --schreiben   # einmalig aus dem Stand VOR dem Umbau
    py -3.14 scripts/opex_momentaufnahme.py --pruefen     # Waechter: aktueller Stand = Momentaufnahme

docs/KALENDER_UMSTELLUNG.md verlangt sie ausdruecklich vor dem V3-Umbau. Der Entwurf
(docs/review_prompts/2026-10-20_kalender_v3_entwurf_v2.md, Codex-Freigabe nach 3 Runden)
praezisiert, was „alle Rueckgabefelder" heisst — der erste Entwurf hatte das zu eng:

  * **Alle** Felder, nicht nur `date`. `get_all_opex_dates` liefert `month_name`,
    `is_triple`, `type`, `adjusted`, `holiday_note`; `populate_opex` zusaetzlich
    `event_name`, `subtype`, `meta`. Eine Datumspruefung schuetzt diese Felder nicht —
    die heutige Verschiebungsnotiz lautet pauschal „Good Friday", und genau so etwas
    soll sichtbar werden, wenn es sich aendert.
  * **Alle 2 592 Monate** 1885-01 bis 2100-12, ausdruecklich auch die, die im Browser
    nach der Umstellung wegfallen (Nutzerentscheidung: Historie vor OPEX 2015-02 bzw.
    VIX 2015-09 weglassen). Ein Wegfall im Browser ist kein Grund, die
    Python-Bestandsausgabe nicht einzufrieren — die Leser bleiben bis P3 unveraendert.

Die Datei ist eine **Pruefsummenliste plus Stichproben**, keine zweite Kalenderquelle.
Pruefsummen halten den Umfang klein; die Stichproben machen eine Abweichung lesbar,
statt nur „Hash ungleich" zu melden.

Die JS-Seite friert scripts/js/opex_momentaufnahme_probe.js ein (eigene Datei, eigener
Aufruf) — sonst waere Python eingefroren und JS umgebaut.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

ZIEL = WURZEL / "scripts" / "fixtures" / "opex_vor_v3.json"

# Rechenbereich. 1885 ist der Beginn des Kalenderbereichs (shared/sitzungen.py), 2100 das
# Ende — 2 592 Monate. Dass davon nur ein Teil im Browser sichtbar bleibt, aendert den
# Bestandsschutz nicht.
VON_JAHR, BIS_JAHR = 1885, 2100

# Monate, die nach der Nutzerentscheidung vom 2026-10-12 im Browser WEGFALLEN. Sie werden
# gekennzeichnet, nicht ausgelassen: so steht schwarz auf weiss, was die Entscheidung
# kostet, und der V3-Waechter kann es pruefen statt es zu behaupten.
OPEX_AB = (2015, 2)
VIX_AB = (2015, 9)


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _fest(wert):
    """JSON-fester Wert: `date` und `set` kommen in den Rueckgaben vor."""
    if hasattr(wert, "isoformat"):
        return wert.isoformat()
    if isinstance(wert, (set, frozenset)):
        return sorted(_fest(x) for x in wert)
    if isinstance(wert, dict):
        return {k: _fest(v) for k, v in sorted(wert.items())}
    if isinstance(wert, (list, tuple)):
        return [_fest(x) for x in wert]
    return wert


def aufnahme() -> dict:
    from shared.market_calendar import populate_opex
    from shared.nyse_holidays import get_all_opex_dates, get_opex_date

    # (a) get_opex_date je Monat — das nackte Datum
    zeilen = []
    for j in range(VON_JAHR, BIS_JAHR + 1):
        for m in range(1, 13):
            try:
                d = get_opex_date(j, m)
                zeilen.append("%04d-%02d=%s" % (j, m, d.isoformat()))
            except Exception as e:                      # Rand des Rechenbereichs
                zeilen.append("%04d-%02d=FEHLER:%s" % (j, m, type(e).__name__))
    opex_date_hash = h("\n".join(zeilen))

    # (b) get_all_opex_dates je Jahr — ALLE Felder
    jahre = {}
    for j in range(VON_JAHR, BIS_JAHR + 1):
        try:
            eintraege = get_all_opex_dates(j, j)
            text = json.dumps(_fest(eintraege), sort_keys=True, separators=(",", ":"))
        except Exception as e:
            text = "FEHLER:%s" % type(e).__name__
        jahre[str(j)] = h(text)
    alle_hash = h(json.dumps(jahre, sort_keys=True, separators=(",", ":")))

    # (c) populate_opex je Jahr — die DB-Zeilen inkl. subtype und meta
    pop = {}
    for j in range(VON_JAHR, BIS_JAHR + 1):
        try:
            text = json.dumps(_fest(populate_opex(j)), sort_keys=True, separators=(",", ":"))
        except Exception as e:
            text = "FEHLER:%s" % type(e).__name__
        pop[str(j)] = h(text)
    pop_hash = h(json.dumps(pop, sort_keys=True, separators=(",", ":")))

    # (d) Stichproben im Volltext — damit eine Abweichung LESBAR ist und nicht nur
    #     „Hash ungleich". Ausgewaehlt sind die Faelle, die der Entwurf benennt:
    #     Verschiebung durch Karfreitag, Triple-Witching, Jahresraender, die
    #     Startgrenzen der Nutzerentscheidung und ein Monat jenseits davon.
    stichproben = {}
    for j, m in ((2015, 2), (2015, 9), (2026, 3), (2026, 4), (2026, 5), (2026, 6),
                 (2026, 12), (2027, 1), (1885, 1), (2100, 12), (2024, 3), (2019, 4)):
        schluessel = "%04d-%02d" % (j, m)
        try:
            eintrag = [e for e in get_all_opex_dates(j, j) if e["month"] == m]
            stichproben[schluessel] = _fest(eintrag[0] if eintrag else None)
        except Exception as e:
            stichproben[schluessel] = "FEHLER:%s" % type(e).__name__

    return {
        "bereich": {"von": "%04d-01" % VON_JAHR, "bis": "%04d-12" % BIS_JAHR,
                    "monate": (BIS_JAHR - VON_JAHR + 1) * 12},
        "entfaellt_mit_v3": {"opex_ab": "%04d-%02d" % OPEX_AB, "vix_ab": "%04d-%02d" % VIX_AB},
        "get_opex_date": opex_date_hash,
        "get_all_opex_dates_je_jahr": jahre,
        "get_all_opex_dates": alle_hash,
        "populate_opex_je_jahr": pop,
        "populate_opex": pop_hash,
        "stichproben": stichproben,
    }


def _vergleiche(soll: dict, ist: dict) -> list[str]:
    abweichungen = []
    for feld in ("bereich", "entfaellt_mit_v3", "get_opex_date", "get_all_opex_dates",
                 "populate_opex"):
        if soll.get(feld) != ist.get(feld):
            abweichungen.append("%s: Momentaufnahme %r, jetzt %r"
                                % (feld, soll.get(feld), ist.get(feld)))
    for feld in ("get_all_opex_dates_je_jahr", "populate_opex_je_jahr"):
        s, i = soll.get(feld) or {}, ist.get(feld) or {}
        jahre = sorted(set(s) | set(i))
        anders = [j for j in jahre if s.get(j) != i.get(j)]
        if anders:
            abweichungen.append("%s: %d Jahr(e) anders, zuerst %s"
                                % (feld, len(anders), ", ".join(anders[:8])))
    s, i = soll.get("stichproben") or {}, ist.get("stichproben") or {}
    for k in sorted(set(s) | set(i)):
        if s.get(k) != i.get(k):
            abweichungen.append("Stichprobe %s: Momentaufnahme %r, jetzt %r"
                                % (k, s.get(k), i.get(k)))
    return abweichungen


def main() -> int:
    schreiben = "--schreiben" in sys.argv
    pruefen = "--pruefen" in sys.argv
    if schreiben == pruefen:
        print(__doc__)
        return 2

    daten = aufnahme()
    if schreiben:
        if ZIEL.exists() and "--ueberschreiben" not in sys.argv:
            print("[FEHLER] %s existiert schon. Eine Momentaufnahme wird nicht "
                  "versehentlich neu geschrieben — sonst friert sie den UMGEBAUTEN "
                  "Stand ein und schuetzt nichts. Mit --ueberschreiben erzwingen."
                  % ZIEL.name)
            return 1
        ZIEL.write_text(json.dumps(daten, sort_keys=True, indent=0,
                                   separators=(",", ":")) + "\n", encoding="utf-8")
        print("[OK] %s geschrieben: %d Monate, %d Stichproben"
              % (ZIEL.name, daten["bereich"]["monate"], len(daten["stichproben"])))
        return 0

    if not ZIEL.exists():
        print("[FEHLER] %s fehlt — erst --schreiben (vor dem Umbau!)" % ZIEL.name)
        return 1
    soll = json.loads(ZIEL.read_text(encoding="utf-8"))
    abw = _vergleiche(soll, daten)
    if abw:
        print("[FEHLER] %d Abweichung(en) zur Momentaufnahme:" % len(abw))
        for a in abw[:20]:
            print("  " + a)
        return 1
    print("[OK] OPEX-Momentaufnahme unveraendert: %d Monate, %d Stichproben"
          % (soll["bereich"]["monate"], len(soll["stichproben"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
