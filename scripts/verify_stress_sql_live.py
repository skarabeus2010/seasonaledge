#!/usr/bin/env python3
"""
verify_stress_sql_live.py — schreibender Integrationstest der SQL-Funktionen der Stress-Ampel gegen die ECHTE Datenbank
(Plan docs/review_prompts/2026-10-09_stress_ampel_plan.md v5, Y2; Codex Plan-R5 Hinweis 1). Nur auf dem Server:

    docker exec seasonalpha-app python3 scripts/verify_stress_sql_live.py

Arbeitet ausschließlich mit dem Ticker `__TEST__` und entfernt dessen Zeilen am Ende IMMER (auch nach Fehlschlägen).
Prüft: zweiter Start bei laufendem Lauf → NULL; zwei gleichzeitige Starts (Barriere) → genau einer; Veröffentlichen nach
abgelaufener Lease → false; Übernahme nach Ablauf; Abbrechen eines fertigen Laufs → false, Status bleibt `fertig`;
anon darf nicht starten. Exit 0 nur, wenn alle Fälle bestehen.
"""
from __future__ import annotations

import os
import pathlib
import sys
import threading
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
T = "__TEST__"
VERWEIGERT = {"42501"}              # PostgreSQL: insufficient_privilege


def anon_pruefung(env, anon_fabrik, ticker=T):
    """None, wenn anon die Funktion NICHT ausführen darf (einzig erwarteter Ausgang); sonst Fehlertext.
    Fehlender Schlüssel, Verbindungsfehler oder ein anderer Fehlercode sind KEIN Nachweis (Codex Code-R2)."""
    url, key = env.get("SUPABASE_URL"), env.get("SUPABASE_ANON_KEY")
    if not url or not key:
        return "SUPABASE_URL/SUPABASE_ANON_KEY fehlt — Rechte nicht prüfbar"
    try:
        r = anon_fabrik(url, key).rpc("stress_lauf_starten", {"p_ticker": ticker}).execute().data
    except Exception as e:  # noqa: BLE001
        code = getattr(e, "code", None) or (e.args[0].get("code") if e.args and isinstance(e.args[0], dict) else None)
        if code in VERWEIGERT:
            return None
        return f"anon-Aufruf scheiterte ohne Rechteverweigerung ({type(e).__name__}, code {code}): {str(e)[:120]}"
    return f"anon konnte starten: {r}"


def main() -> int:
    from shared.supabase_client import get_client
    c = get_client()
    fehler = []

    def rpc(name, p, client=c):
        return client.rpc(name, p).execute().data

    def status(lid):
        r = c.table("stress_laeufe").select("status").eq("lauf_id", lid).execute().data
        return r[0]["status"] if r else None

    def aufraeumen():
        ids = [r["lauf_id"] for r in (c.table("stress_laeufe").select("lauf_id").eq("ticker", T).execute().data or [])]
        for lid in ids:
            c.table("stress_scores").delete().eq("lauf_id", lid).execute()
        c.table("stress_laeufe").delete().eq("ticker", T).execute()

    try:
        aufraeumen()
        # 1) zweiter Start bei laufendem Lauf
        a = rpc("stress_lauf_starten", {"p_ticker": T})
        b = rpc("stress_lauf_starten", {"p_ticker": T})
        if not a or b is not None:
            fehler.append(f"Sperre: erster Start {a}, zweiter {b} (soll uuid / None)")
        # 2) Veröffentlichen nach abgelaufener Lease → false; Übernahme danach erlaubt
        vergangen = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        c.table("stress_laeufe").update({"laeuft_bis": vergangen}).eq("lauf_id", a).execute()
        ok = rpc("stress_lauf_veroeffentlichen", {"p_lauf": a, "p_n": 0, "p_erstes": None, "p_letztes": None,
                                                  "p_kurse_bis": None, "p_n_kurse": 0, "p_hash": "x"})
        if ok is not False:
            fehler.append(f"Lease: Veröffentlichung nach Ablauf ergab {ok}")
        n = rpc("stress_lauf_starten", {"p_ticker": T})
        if not n or status(a) != "abgebrochen":
            fehler.append(f"Übernahme: neuer Lauf {n}, alter Status {status(a)}")
        # 3) Abbrechen eines fertigen Laufs ändert nichts
        ok = rpc("stress_lauf_veroeffentlichen", {"p_lauf": n, "p_n": 0, "p_erstes": None, "p_letztes": None,
                                                  "p_kurse_bis": None, "p_n_kurse": 0, "p_hash": "x"})
        ab = rpc("stress_lauf_abbrechen", {"p_lauf": n})
        if ok is not True or ab is not False or status(n) != "fertig":
            fehler.append(f"Unveränderlich: veröffentlicht {ok}, abbrechen {ab}, Status {status(n)}")
        # 4) zwei gleichzeitige Starts → genau einer
        sperre = threading.Barrier(2, timeout=20)
        erg = []

        def start():
            from supabase import create_client
            eigen = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
            sperre.wait()
            erg.append(eigen.rpc("stress_lauf_starten", {"p_ticker": T}).execute().data)
        th = [threading.Thread(target=start) for _ in range(2)]
        [x.start() for x in th]
        [x.join(30) for x in th]
        if sorted(e is None for e in erg) != [False, True]:
            fehler.append(f"Parallel: Ergebnisse {erg} (soll genau eine uuid)")
        # 5) anon darf keine Funktion ausführen — nur die erwartete Verweigerung zählt als bestanden
        from supabase import create_client
        a5 = anon_pruefung(os.environ, create_client)
        if a5:
            fehler.append(a5)
    except Exception as e:  # noqa: BLE001
        fehler.append(f"Ausnahme: {type(e).__name__}: {e}")
    finally:
        try:
            aufraeumen()
        except Exception as e:  # noqa: BLE001
            fehler.append(f"Aufräumen fehlgeschlagen: {e}")
    for f in fehler:
        print("FEHLER", f)
    print(f"verify_stress_sql_live: {'BESTANDEN' if not fehler else str(len(fehler)) + ' Fehler'}")
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
