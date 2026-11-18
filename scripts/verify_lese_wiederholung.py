"""
scripts/verify_lese_wiederholung.py — Wächter: Kursladen wiederholt einen Statement-Timeout (57014)
===================================================================================================
Anlass (Nightly 14.11. und 17.11.2026, rot): `stress_score.lade_kurse` (Saison-Score, Stress-Ampel) zählt die Zeilen
mit count=exact. Für ^GSPC (~40 000 Zeilen) dauert das mit kaltem Cache 5,8 s statt 0,1 s; nach den schweren Phasen
des Nightly riss die Abfrage das Statement-Limit, ohne Wiederholung → Phase rot.

Geprüft mit einer Attrappe des Supabase-Clients (keine Datenbank, keine Wartezeit):
  1. Grundlinie: 2 500 Zeilen in drei Seiten, vollständig geladen
  2. Zählung scheitert einmal mit 57014 → zweiter Versuch, Ergebnis vollständig
  3. eine Seite scheitert zweimal mit 57014 → dritter Versuch, Ergebnis vollständig, keine Zeile doppelt
  4. dreimal 57014 hintereinander → LadeFehler (kein grüner Teilbestand), genau drei Versuche
  5. anderer Fehler (42501) → sofort LadeFehler, genau ein Versuch
  6. Mutation: lade_kurse ohne Wiederholung (`_lesen` ruft nur einmal) MUSS bei Fall 2 und 3 durchfallen

Aufruf: py -3.14 scripts/verify_lese_wiederholung.py   (Exit 0 = bestanden)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared import stress_score as ss  # noqa: E402

N = 2500
FEHLER: list[str] = []


class _APIError(Exception):
    def __init__(self, code, msg):
        super().__init__({"message": msg, "code": code})
        self.code = code


class _Antwort:
    def __init__(self, data=None, count=None):
        self.data, self.count = data, count


class _Anfrage:
    def __init__(self, c):
        self.c, self.zaehlen, self.von, self.bis = c, False, 0, 0

    def select(self, *_a, count=None):
        self.zaehlen = count == "exact"
        return self

    def eq(self, *_a):
        return self

    def order(self, *_a):
        return self

    def limit(self, *_a):
        return self

    def range(self, von, bis):
        self.von, self.bis = von, bis
        return self

    def execute(self):
        art = "zaehlen" if self.zaehlen else f"seite{self.von}"
        self.c.versuche[art] = self.c.versuche.get(art, 0) + 1
        plan = self.c.fehler.get(art, [])
        if plan:
            code = plan.pop(0)
            raise _APIError(code, "canceling statement due to statement timeout" if code == "57014" else "denied")
        if self.zaehlen:
            return _Antwort(count=N)
        return _Antwort(data=[{"date": f"{2000 + i // 365:04d}-01-01+{i}", "close": 100.0 + i}
                              for i in range(self.von, min(self.bis + 1, N))])


class _Client:
    def __init__(self, fehler=None):
        self.fehler, self.versuche = fehler or {}, {}

    def table(self, _name):
        return _Anfrage(self)


def pruefe(name, ok, detail=""):
    if not ok:
        FEHLER.append(f"{name}: {detail}")
    print(("  ok   " if ok else "  FEHL ") + name + ("" if ok else f" — {detail}"))


def _bereinigen_durchreichen(daten, closes):
    return daten, closes, 0


def lauf(fehler):
    c = _Client(fehler)
    try:
        d, cl, info = ss.lade_kurse("^GSPC", c)
        return {"ok": True, "n": info["roh"], "einzig": len(set(d)), "versuche": c.versuche}
    except ss.LadeFehler as e:
        return {"ok": False, "msg": str(e), "versuche": c.versuche}


def faelle(erwarte_wiederholung=True) -> list[str]:
    alt = list(FEHLER)
    FEHLER.clear()
    r = lauf({})
    pruefe("Grundlinie vollständig", r["ok"] and r["n"] == N and r["einzig"] == N, str(r))
    r = lauf({"zaehlen": ["57014"]})
    pruefe("Zählung 1× 57014 → wiederholt", r["ok"] and r["n"] == N and r["versuche"].get("zaehlen") == 2, str(r))
    r = lauf({"seite1000": ["57014", "57014"]})
    pruefe("Seite 2× 57014 → wiederholt, nichts doppelt",
           r["ok"] and r["n"] == N and r["einzig"] == N and r["versuche"].get("seite1000") == 3, str(r))
    if erwarte_wiederholung:
        r = lauf({"zaehlen": ["57014"] * 3})
        pruefe("3× 57014 → LadeFehler nach drei Versuchen",
               not r["ok"] and "57014" in r["msg"] and r["versuche"].get("zaehlen") == 3, str(r))
        r = lauf({"zaehlen": ["42501"]})
        pruefe("anderer Fehler → sofort LadeFehler", not r["ok"] and r["versuche"].get("zaehlen") == 1, str(r))
    gefunden = list(FEHLER)
    FEHLER[:] = alt
    return gefunden


def main() -> int:
    ss.LESE_WIEDERHOLUNG_S = (0.0, 0.0)
    ss.bereinigen = _bereinigen_durchreichen
    FEHLER.extend(faelle())

    echt = ss._lesen
    ss._lesen = lambda fn, warte=None: fn()           # Mutation: keine Wiederholung
    print("  -- Mutation: ohne Wiederholung --")
    mut = faelle(erwarte_wiederholung=False)
    ss._lesen = echt
    if len(mut) < 2:
        FEHLER.append(f"Mutation nicht gefangen ({len(mut)} von 2 Fällen rot)")
        print("  FEHL Mutation nicht gefangen")
    else:
        print(f"  ok   Mutation gefangen ({len(mut)} Fälle rot)")

    print("verify_lese_wiederholung:", "BESTANDEN" if not FEHLER else f"DURCHGEFALLEN ({len(FEHLER)})")
    return 0 if not FEHLER else 1


if __name__ == "__main__":
    sys.exit(main())
