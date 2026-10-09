"""
shared/stress_score.py — Stress-Ampel: ein transparenter Stress-Score je Handelstag (Python-Zwilling)
===================================================================================================
Plan mit Codex-Freigabe (5 Runden): docs/review_prompts/2026-10-09_stress_ampel_plan.md (v5).
JS-Zwilling: landing/js/dash-compute.js::stressReihe / computeStress — gleiche Formel, gleiche Rechenreihenfolge.

Definition (D, W1, V9):
  Eingabe: Schlusskurse aufsteigend; ungültige (nicht endlich, ≤ 0) und doppelte Datumszeilen (letzter Wert gilt)
  vorab entfernt. Die Kurszeilen sind der Kalender.
  r_i     = c_i / c_{i−1} − 1
  vol5_t  = Stichproben-Std (n−1, Zwei-Pass) von r_{t−4..t} × 100      (ab dem 6. Schluss)
  vol20_t = dasselbe über r_{t−19..t}                                    (ab dem 21. Schluss)
  dd20_t  = (c_t / max(c_{t−19..t}) − 1) × 100                           (ab dem 20. Schluss)
  S_t     = 0,3·vol5 + 0,3·vol20 + 0,4·|dd20|                            (ab dem 21. Schluss)
  score_t = 100 · (#{S_j < S_t − ε} + ½·#{|S_j − S_t| ≤ ε}) / |W_t|,  W_t = S der bis zu 2520 Sitzungen VOR t,
            ε = 1e-9; nur wenn |W_t| ≥ 756 (erster Score am 777. Schluss, volle Referenz ab dem 2541.).
  Ampel   = grün < 70 ≤ gelb < 90 ≤ rot, entschieden auf dem UNGERUNDETEN Score; ohne Score „grey".
  Anzeige = auf eine Nachkommastelle ABGESCHNITTEN (89,96 → 89,9), damit Zahl und Farbe sich nie widersprechen.
Ein heuristisches Maß aus Tagesvolatilität und kurzfristigem Kursrückgang — keine Prognose. Es nutzt nur Kurse bis zum
jeweiligen Tag, bezogen auf den aktuellen Kursdatenstand.

Datenbank (X1/Y1/Y2): Tabellen `stress_laeufe` + `stress_scores` (scripts/sql/stress_scores_schema_2026_10.sql). Jeder
Schreiblauf ist ein Vollauf mit eigener `lauf_id`; sichtbar wird nur ein Lauf, den `stress_lauf_veroeffentlichen`
(atomar, mit Lease) auf `fertig` gesetzt hat. `regime_scores` (alte Isolation-Forest-Werte) wird nicht mehr gelesen
oder geschrieben.
"""
from __future__ import annotations

import bisect
import hashlib
import math
from datetime import date

GEWICHTE = (0.3, 0.3, 0.4)
REFERENZ_MAX = 2520
REFERENZ_MIN = 756
ERSTER_SCORE_KURS = REFERENZ_MIN + 21          # 777: S entsteht am 21. Schluss, danach 756 Referenzwerte
VOLLE_REFERENZ_KURS = REFERENZ_MAX + 21        # 2541
EPS = 1e-9
# Gespeicherte Genauigkeit: die Datenbank liefert double precision über PostgREST nur auf 15 signifikante Stellen
# zurück (gemessen beim ersten Lauf 2026-10-09: 88.35978835978835 → 88.3597883597884). Score und S werden deshalb
# VOR der Farbentscheidung gerundet — so übersteht der gespeicherte Wert das Rücklesen exakt, und Farbe, Anzeige und
# Datenbank beziehen sich auf dieselbe Zahl (89,99999999999999 wäre sonst gelb, käme aber als „90" zurück).
STELLEN_SCORE = 10          # Nachkommastellen; Score ≤ 100 → höchstens 13 signifikante Stellen
SIGNIFIKANT_S = 15          # S ist nach oben offen (Codex Code-R4: 1992,336… bei einem Kurssprung) → signifikante Stellen
GRENZE_GELB = 70.0
GRENZE_ROT = 90.0
METHODE = "stress_v1"
BATCH = 500


class LadeFehler(RuntimeError):
    """Die Kursreihe ließ sich nicht laden (Netzwerk, kein Client, unvollständige Antwort) — kein Score, kein Write."""


# ══════════════════════════════════════════════════════════════
# RECHNUNG
# ══════════════════════════════════════════════════════════════

def bereinigen(daten, closes):
    """Ungültige Kurse raus, doppelte Datumszeilen → letzter Wert; sortiert. Gibt (daten, closes, n_duplikate)."""
    je_datum = {}
    dup = 0
    for d, c in zip(daten, closes):
        try:
            w = float(c)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(w) or w <= 0:
            continue
        d = str(d)[:10]
        if d in je_datum:
            dup += 1
        je_datum[d] = w
    ds = sorted(je_datum)
    return ds, [je_datum[d] for d in ds], dup


def _std(werte):
    """Stichproben-Std, Zwei-Pass, einfache Summen in fester Reihenfolge (wie JS)."""
    n = len(werte)
    m = 0.0
    for x in werte:
        m += x
    m = m / n
    q = 0.0
    for x in werte:
        q += (x - m) * (x - m)
    return math.sqrt(q / (n - 1))


def ampel(score):
    if score is None:
        return "grey"
    if score >= GRENZE_ROT:
        return "red"
    if score >= GRENZE_GELB:
        return "yellow"
    return "green"


def anzeige(score):
    """Auf eine Nachkommastelle abgeschnitten; None bleibt None."""
    return None if score is None else math.floor(score * 10) / 10


def stress_reihe(daten, closes, bereinigt=False):
    """Eine Zeile je Kurs (nach Bereinigung): date, close, vol5, vol10, vol20, dd20, s, score, ampel, referenz_n,
    ret1d, ret5d, ret20d. Komponenten None, solange ihr Fenster nicht gefüllt ist."""
    if not bereinigt:
        daten, closes, _ = bereinigen(daten, closes)
    n = len(closes)
    r = [None] + [(closes[i] / closes[i - 1] - 1) * 100 for i in range(1, n)]
    out = []
    fenster = []          # sortierte S der Referenz
    s_folge = []          # S in Zeitfolge (Index = Kurs-Index, None vor dem 21. Schluss)
    for i in range(n):
        vol5 = _std(r[i - 4:i + 1]) if i >= 5 else None
        vol10 = _std(r[i - 9:i + 1]) if i >= 10 else None
        vol20 = _std(r[i - 19:i + 1]) if i >= 20 else None
        dd20 = None
        if i >= 19:
            hoch = closes[i - 19]
            for k in range(i - 18, i + 1):
                if closes[k] > hoch:
                    hoch = closes[k]
            dd20 = (closes[i] / hoch - 1) * 100
        s = None          # ungerundet für den Rang
        if vol5 is not None and vol20 is not None and dd20 is not None:
            s = GEWICHTE[0] * vol5 + GEWICHTE[1] * vol20 + GEWICHTE[2] * abs(dd20)
        score = None
        ref_n = len(fenster)
        if s is not None and ref_n >= REFERENZ_MIN:
            kleiner = bisect.bisect_left(fenster, s - EPS)
            bis_gleich = bisect.bisect_right(fenster, s + EPS)
            score = round(100.0 * (kleiner + 0.5 * (bis_gleich - kleiner)) / ref_n, STELLEN_SCORE)
        out.append({
            "date": daten[i], "close": closes[i], "vol5": vol5, "vol10": vol10, "vol20": vol20, "dd20": dd20,
            "s": None if s is None else float(f"{s:.{SIGNIFIKANT_S}g}"), "score": score, "ampel": ampel(score), "referenz_n": ref_n if s is not None else 0,
            "ret1d": r[i] if i >= 1 else None,
            "ret5d": (closes[i] / closes[i - 5] - 1) * 100 if i >= 5 else None,
            "ret20d": (closes[i] / closes[i - 20] - 1) * 100 if i >= 20 else None,
        })
        # S_t erst NACH dem Rang in die Referenz (Referenz endet bei t−1)
        # Für t+1 gilt W = S_{t−2519..t}: S_t hinein, S_{t−2520} heraus (S existiert ab Kurs 21 lückenlos)
        s_folge.append(s)
        if s is not None:
            bisect.insort(fenster, s)
            alt_i = i - REFERENZ_MAX
            if alt_i >= 0 and s_folge[alt_i] is not None:
                fenster.pop(bisect.bisect_left(fenster, s_folge[alt_i]))
    return out


def stress_aktuell(daten, closes):
    """Letzte Zeile von stress_reihe plus Status: ok | zu_kurz | leer."""
    reihe = stress_reihe(daten, closes)
    if not reihe:
        return {"status": "leer", "n_kurse": 0, "score": None, "ampel": "grey"}
    z = dict(reihe[-1])
    z["n_kurse"] = len(reihe)
    z["status"] = "ok" if z["score"] is not None else "zu_kurz"
    return z


def kurse_hash(daten, closes):
    h = hashlib.sha256()
    for d, c in zip(daten, closes):
        h.update(f"{d}|{c!r}\n".encode())
    return h.hexdigest()


# ══════════════════════════════════════════════════════════════
# LADEN (X2)
# ══════════════════════════════════════════════════════════════

def lade_kurse(ticker, client=None):
    """Alle Kurszeilen aus Supabase `prices` (wie shared.data.lade_closes, aber mit Rohzeilen und unabhängiger
    Zählung). Gibt (daten, closes, info) bereinigt zurück; info = {roh, quell_n, duplikate, ungueltig}.
    Eine kurze oder leere Reihe ist KEIN Fehler; LadeFehler nur bei echtem Abrufproblem oder Unvollständigkeit."""
    if client is None:
        from shared.supabase_client import get_client
        client = get_client()
    if client is None:
        raise LadeFehler(f"{ticker}: kein Supabase-Client")
    try:
        quell_n = client.table("prices").select("date", count="exact").eq("ticker", ticker).limit(1).execute().count
        zeilen, offset = [], 0
        while True:
            teil = (client.table("prices").select("date,close").eq("ticker", ticker)
                    .order("date").range(offset, offset + 999).execute().data) or []
            zeilen += teil
            if len(teil) < 1000:
                break
            offset += 1000
    except LadeFehler:
        raise
    except Exception as e:  # noqa: BLE001 — jeder Abruffehler ist ein Ladefehler, nie ein grüner Wert
        raise LadeFehler(f"{ticker}: Abruf fehlgeschlagen: {e}") from e
    if quell_n is None or len(zeilen) != quell_n:
        raise LadeFehler(f"{ticker}: {len(zeilen)} Zeilen geladen, Zählung {quell_n} — unvollständig")
    daten, closes, dup = bereinigen([z.get("date") for z in zeilen], [z.get("close") for z in zeilen])
    return daten, closes, {"roh": len(zeilen), "quell_n": quell_n, "duplikate": dup,
                           "ungueltig": len(zeilen) - len(closes) - dup}


def stress_fuer_ticker(ticker, client=None, aktuell_bis=None, max_sitzungen_alt=5, boerse="NYSE"):
    """Für Berichte: aktueller Stress eines Tickers mit Status ok | veraltet | zu_kurz | leer | fehlt."""
    try:
        daten, closes, _ = lade_kurse(ticker, client)
    except LadeFehler as e:
        return {"status": "fehlt", "fehler": str(e), "score": None, "ampel": "grey"}
    z = stress_aktuell(daten, closes)
    if z["status"] == "ok" and daten:
        if aktuell_bis is None:
            from shared.exchange_holidays import letzte_session
            aktuell_bis = letzte_session(boerse)
        if _sitzungen_zwischen(date.fromisoformat(daten[-1]), aktuell_bis, boerse) > max_sitzungen_alt:
            z["status"] = "veraltet"
    return z


def _sitzungen_zwischen(von, bis, boerse):
    from datetime import timedelta
    from shared.exchange_holidays import is_trading_day
    n, d = 0, von
    while d < bis:
        d += timedelta(days=1)
        if is_trading_day(d, boerse):
            n += 1
    return n


# ══════════════════════════════════════════════════════════════
# DATENBANK (X1/Y1/Y2)
# ══════════════════════════════════════════════════════════════

def _zeile_db(ticker, lauf_id, z):
    return {"lauf_id": lauf_id, "ticker": ticker, "date": z["date"], "score": z["score"], "ampel": z["ampel"],
            "s": z["s"], "vol5": z["vol5"], "vol10": z["vol10"], "vol20": z["vol20"], "dd20": z["dd20"],
            "ret1d": z["ret1d"], "ret5d": z["ret5d"], "ret20d": z["ret20d"], "referenz_n": z["referenz_n"]}


def sollmenge(daten, closes):
    """Die exakt zu schreibenden Zeilen: alle Kurse ab dem 777. bereinigten Schluss (W2)."""
    reihe = stress_reihe(daten, closes, bereinigt=True)
    soll = [z for z in reihe if z["score"] is not None]
    erwartet = max(0, len(closes) - (ERSTER_SCORE_KURS - 1))
    if len(soll) != erwartet or [z["date"] for z in soll] != daten[ERSTER_SCORE_KURS - 1:]:
        raise RuntimeError(f"Sollmenge {len(soll)} Zeilen, erwartet {erwartet} ab Kurs Nr. {ERSTER_SCORE_KURS}")
    return soll


def _rpc(client, name, params):
    return client.rpc(name, params).execute().data


def vollauf(ticker, client=None, protokoll=print):
    """Ein vollständiger, geprüfter Schreiblauf (Y1). Rückgabe {status, lauf_id, n_scores, ...}; wirft bei Fehlern.
    Ablauf: laden → Sollmenge → Lauf starten (Sperre) → schreiben → zurücklesen → veröffentlichen → aufräumen."""
    if client is None:
        from shared.supabase_client import get_client
        client = get_client()
    # Sperre VOR dem Laden: ein Lauf, der alte Kurse geladen hat, darf nicht nach einem neueren veröffentlichen
    # (Codex Code-R1 Befund 1). Laden und Rechnen liegen im abgesicherten Pfad → bei Fehlern `abgebrochen`.
    lauf_id = _rpc(client, "stress_lauf_starten", {"p_ticker": ticker})
    if not lauf_id:
        raise RuntimeError(f"{ticker}: ein anderer Lauf ist aktiv (Sperre) — nichts geschrieben")
    try:
        daten, closes, info = lade_kurse(ticker, client)
        protokoll(f"[stress] {ticker}: {info['roh']} Rohzeilen (Zählung {info['quell_n']}), {len(closes)} bereinigt, "
                  f"{info['duplikate']} Duplikate, {info['ungueltig']} ungültig")
        soll = sollmenge(daten, closes)
        zeilen = [_zeile_db(ticker, lauf_id, z) for z in soll]
        for i in range(0, len(zeilen), BATCH):
            client.table("stress_scores").insert(zeilen[i:i + BATCH]).execute()
        rueck = lese_lauf(client, lauf_id)
        _vergleiche(soll, rueck)
        ok = _rpc(client, "stress_lauf_veroeffentlichen", {
            "p_lauf": lauf_id, "p_n": len(soll), "p_erstes": soll[0]["date"] if soll else None,
            "p_letztes": soll[-1]["date"] if soll else None, "p_kurse_bis": daten[-1] if daten else None,
            "p_n_kurse": len(closes), "p_hash": kurse_hash(daten, closes)})
        if not ok:
            raise RuntimeError(f"{ticker}: Veröffentlichung abgelehnt (Lauf verdrängt oder Lease abgelaufen)")
    except Exception:
        try:
            _rpc(client, "stress_lauf_abbrechen", {"p_lauf": lauf_id})
        except Exception as e2:  # noqa: BLE001
            protokoll(f"[stress] {ticker}: Abbrechen fehlgeschlagen: {e2}")
        raise
    entfernt = aufraeumen(client, ticker)
    protokoll(f"[stress] {ticker}: Lauf {lauf_id} veröffentlicht, {len(soll)} Scores, {entfernt} alte Läufe entfernt")
    return {"status": "fertig", "lauf_id": lauf_id, "n_scores": len(soll),
            "letztes_datum": soll[-1]["date"] if soll else None}


def lese_lauf(client, lauf_id):
    zeilen, offset = [], 0
    while True:
        teil = (client.table("stress_scores").select("date,score,s,ampel").eq("lauf_id", lauf_id)
                .order("date").range(offset, offset + 999).execute().data) or []
        zeilen += teil
        if len(teil) < 1000:
            break
        offset += 1000
    return zeilen


def _vergleiche(soll, rueck):
    if [z["date"] for z in soll] != [str(z["date"])[:10] for z in rueck]:
        raise RuntimeError(f"Rücklesen: Datumsmenge abweichend ({len(rueck)} statt {len(soll)} Zeilen)")
    for a, b in zip(soll, rueck):
        if b["ampel"] != a["ampel"] or float(b["score"]) != a["score"] or float(b["s"]) != a["s"]:
            raise RuntimeError(f"Rücklesen: {a['date']} abweichend ({b} statt score {a['score']}, s {a['s']})")


def aufraeumen(client, ticker, behalten=2):
    """Löscht abgebrochene und ältere fertige Läufe samt Zeilen (nie `laeuft`, nie die zwei jüngsten fertigen).
    Metadaten paginiert und stabil sortiert gelesen (Codex Code-R1 Befund 3); erst Zeilen, dann der Laufeintrag."""
    laeufe, offset = [], 0
    while True:
        teil = (client.table("stress_laeufe").select("lauf_id,status,fertig_am,gestartet_am").eq("ticker", ticker)
                .order("lauf_id").range(offset, offset + 999).execute().data) or []
        laeufe += teil
        if len(teil) < 1000:
            break
        offset += 1000
    fertig = sorted((l for l in laeufe if l["status"] == "fertig"), key=lambda l: l["fertig_am"] or "", reverse=True)
    weg = [l["lauf_id"] for l in laeufe if l["status"] == "abgebrochen"] + [l["lauf_id"] for l in fertig[behalten:]]
    for lid in weg:
        client.table("stress_scores").delete().eq("lauf_id", lid).execute()
        client.table("stress_laeufe").delete().eq("lauf_id", lid).neq("status", "laeuft").execute()
    return len(weg)


def letzter_fertiger_lauf(client, ticker):
    r = (client.table("stress_laeufe").select("lauf_id,letztes_datum,kurse_bis,n_scores,fertig_am")
         .eq("ticker", ticker).eq("status", "fertig").order("fertig_am", desc=True).limit(1).execute().data) or []
    return r[0] if r else None
