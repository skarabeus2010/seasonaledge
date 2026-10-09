"""
shared/saison_score_betrieb.py — Betrieb des Saison-Scores (D3): aus Supabase laden, in scanner_results speichern,
im unveränderlichen saison_score_protokoll festhalten. Bewusst getrennt vom Rechenkern shared/saison_score.py, dessen
Stand für die Validierung per Hash festgeschrieben ist.
"""
from __future__ import annotations

from shared.saison_score import METHODE, berechne

def code_version() -> str:
    """Inhaltshash des Rechenkerns shared/saison_score.py — bindet das Protokoll an den Code, der wirklich lief (der Container kennt kein .git)."""
    import hashlib
    import pathlib
    import shared.saison_score as kern
    return METHODE + ":" + hashlib.sha256(pathlib.Path(kern.__file__).read_bytes()).hexdigest()[:12]


def fuer_ticker(ticker, client=None) -> dict:
    """Saison-Score aus den Supabase-Kursen (dieselbe Quelle wie die Seiten). LadeFehler wird nicht verschluckt."""
    from shared import stress_score
    daten, closes, _ = stress_score.lade_kurse(ticker, client)
    e = berechne(daten, closes, ticker)
    e["kurse_bis"] = daten[-1] if daten else None
    e["kurse_hash"] = stress_score.kurse_hash(daten, closes)
    return e


def _bausteine(e: dict) -> dict:
    return {k: e[k] for k in ("score_roh", "b1", "b2", "b3", "b4", "vergleich_ohne_matching", "konformitaet", "fenster")} | {
        "n_jahre": len(e["jahre"]),
        "musterjahre": [{"jahr": m["jahr"], "r": m["r"], "rendite": m["rendite"]} for m in e["musterjahre"]],
    }


def scanner_zeile(e: dict, ticker: str, scan_date: str) -> dict:
    """Zeile für scanner_results. win_rate = B1 in Prozent, avg_return = Ø Fensterrendite (30 KT) — NICHT mehr der
    Kalendermonat. signal ausdrücklich None (keine Richtungsetiketten); nicht berechenbar → Score None + Grund."""
    ok = e["status"] == "ok"
    return {
        "ticker": ticker, "scan_date": scan_date, "methode": METHODE, "status": e["status"],
        "grund": None if ok else (e.get("grund_code") or "unbekannt"),
        "score": e["score"] if ok else None, "signal": None,
        "win_rate": round(100 * e["b1"]["wert"], 2) if ok else None,
        "avg_return": round(e["b2"]["mittel"], 4) if ok else None,
        "deviation": None, "as_of": e.get("as_of"),
        "bausteine": _bausteine(e) if ok else None,
    }


def protokoll_zeile(e: dict, ticker: str) -> dict | None:
    """Zeile für saison_score_protokoll (unveränderlich, erster Lauf je Ticker/as_of zählt). None ohne Kurse."""
    if not e.get("as_of") or not e.get("kurse_bis"):
        return None
    ok = e["status"] == "ok"
    return {
        "methode": METHODE, "code_version": code_version(), "ticker": ticker, "as_of": e["as_of"],
        "kurse_bis": e["kurse_bis"], "kurse_hash": e["kurse_hash"], "status": e["status"],
        "grund": None if ok else e.get("grund_code"), "score": e["score"] if ok else None,
        "bausteine": _bausteine(e) if ok else None,
    }


# Felder, die bei einer Wiederholung desselben (methode, ticker, as_of) gleich sein müssen
_ABGLEICH = ("kurse_hash", "status", "score", "code_version")


def schreibe(client, scanner: list[dict], protokoll: list[dict]) -> list[str]:
    """Schreibt ZUERST das Protokoll (nur Einfügen, Konflikt → nichts), DANN die Scanner-Zeilen (Upsert je Ticker/Tag).
    Reihenfolge ist Absicht: `--resume` überspringt Ticker mit Scanner-Zeile von heute — steht sie da, ist auch das
    Protokoll geschrieben (Codex D3/D4 R1 Befund 3). Fehler werden NICHT verschluckt.

    Gibt Abweichungen zurück: weicht der gespeicherte Eintrag für (methode, ticker, as_of) vom neuen in
    `_ABGLEICH` ab (z. B. Kurskorrektur bei gleichem Stichtag), bleibt der erste Eintrag stehen und die Abweichung
    wird gemeldet (Plan v3: Abweichungslog) — Aufrufer loggen sie, ein Fehler ist es nicht."""
    abweichungen: list[str] = []
    protokoll = [p for p in protokoll if p]
    if protokoll:
        client.table("saison_score_protokoll").upsert(protokoll, on_conflict="methode,ticker,as_of",
                                                      ignore_duplicates=True).execute()
    # Abgleich NACH dem Einfügen gegen den tatsächlich gespeicherten Eintrag: so meldet auch der zweite von zwei
    # gleichzeitigen Writern seine Abweichung (Codex D3/D4 R2 Befund 2). Der eigene, neu eingefügte Eintrag ist gleich.
    for p in protokoll:
        gespeichert = (client.table("saison_score_protokoll").select(",".join(_ABGLEICH))
                       .eq("methode", p["methode"]).eq("ticker", p["ticker"]).eq("as_of", p["as_of"])
                       .limit(1).execute().data)
        if not gespeichert:
            raise RuntimeError(f"Saison-Protokoll fehlt nach dem Schreiben: {p['ticker']} {p['as_of']}")
        g = gespeichert[0]
        diff = [f"{k}: {g.get(k)!r} → {p.get(k)!r}" for k in _ABGLEICH
                if g.get(k) != p.get(k) and not (k == "score" and g.get(k) is not None and p.get(k) is not None
                                                 and abs(float(g[k]) - float(p[k])) < 1e-9)]
        if diff:
            abweichungen.append(f"{p['ticker']} {p['as_of']}: " + "; ".join(diff))
    if scanner:
        client.table("scanner_results").upsert(scanner, on_conflict="ticker,scan_date").execute()
    return abweichungen
