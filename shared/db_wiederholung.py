"""
shared/db_wiederholung.py — Wiederholung vorübergehender Supabase-Fehler (eine Regel für Lader und Schreiber).

Anlass (2026-11-20, Codex-Diagnose docs/review_prompts/2026-11-20_nightly_rot_diagnose_antwort.md): der Nightly war an
10 von 15 Abenden rot, jedes Mal an EINEM Ticker von rund 370 —
  * `57014 statement timeout` beim Laden langer Kursreihen (^GSPC, ^GDAXI, RTX), je nach Last;
  * `<ConnectionTerminated error_code:0, last_stream_id:19999>`: HTTP/2-GOAWAY nach 10 000 Streams auf EINER Verbindung.
    Der Nightly benutzt einen Client für den ganzen Lauf; wer die 10 000. Anfrage trifft, scheitert. Ein zweiter Versuch
    auf DEMSELBEN Client trifft dieselbe tote Verbindung — deshalb verlangt die Wiederholung nach einem Transportfehler
    einen neuen Client.

Wiederholt werden NUR diese Klassen. Rechte-, Schema- und Datenfehler (42501, PGRST…, ValueError, „Out of range float")
gehen sofort weiter — sie werden durch Wiederholen nicht besser, und ein Retry darf keinen echten Fehler verdecken.
"""
from __future__ import annotations

import random
import time

VORUEBERGEHENDE_PG_CODES = frozenset({"57014"})   # canceling statement due to statement timeout


def _pg_code(e) -> str | None:
    """Postgres-/PostgREST-Code einer postgrest.APIError (Attribut `code` oder dict im ersten Argument)."""
    code = getattr(e, "code", None)
    if code is None and e.args and isinstance(e.args[0], dict):
        code = e.args[0].get("code")
    return str(code) if code is not None else None


def _kette(e):
    """Die Ausnahme und ihre Ursachen (__cause__/__context__), ohne Schleifen."""
    gesehen = set()
    while e is not None and id(e) not in gesehen:
        gesehen.add(id(e))
        yield e
        e = e.__cause__ or e.__context__


def transportfehler(e) -> bool:
    """Verbindung kaputt (GOAWAY, Abbruch, Timeout) → Wiederholung nur mit NEUEM Client sinnvoll."""
    try:
        import httpx
        klassen = (httpx.RemoteProtocolError, httpx.TimeoutException, httpx.NetworkError)
    except ImportError:          # ohne httpx gibt es keinen Transportfehler dieser Art
        return False
    return any(isinstance(x, klassen) for x in _kette(e))


def voruebergehend(e) -> bool:
    """Lohnt ein zweiter Versuch? 57014 oder Transportfehler — sonst nein."""
    if transportfehler(e):
        return True
    return any(_pg_code(x) in VORUEBERGEHENDE_PG_CODES for x in _kette(e))


def beschreibe(e) -> str:
    """Kurzform fürs Log: Klasse + Code, damit sich 57014 und GOAWAY künftig trennen lassen."""
    code = _pg_code(e)
    notizen = " | ".join(getattr(e, "__notes__", None) or [])   # z. B. „stress_score.lade_kurse T: count"
    return f"{type(e).__name__}{f' {code}' if code else ''}: {str(e)[:160]}{f' [{notizen}]' if notizen else ''}"


VERSUCHE = 3


def warte(versuch: int) -> None:
    """Kurzer Backoff mit Streuung: 2 s, 5 s (+ bis zu 1 s)."""
    time.sleep((2, 5, 10)[min(versuch, 2)] + random.random())


def mit_wiederholung(aufgabe, *, was: str, log=None, versuche: int | None = None, schlafen=None):
    """Führt `aufgabe(neuer_client: bool)` aus und wiederholt bei vorübergehenden Fehlern.

    `neuer_client` ist True, wenn der vorige Versuch an einem Transportfehler scheiterte — die Aufgabe muss sich dann
    einen frischen Client holen (`get_client(force_new=True)`), nicht den alten weiterbenutzen. Nach dem letzten
    Versuch wird die ursprüngliche Ausnahme weitergereicht (kein Ersatzwert, kein Teilergebnis)."""
    versuche = versuche or VERSUCHE
    schlafen = schlafen or warte          # zur Laufzeit aufgelöst — Tests ersetzen `warte` am Modul
    neu = False
    for v in range(versuche):
        try:
            return aufgabe(neu)
        except Exception as e:  # noqa: BLE001 — Klassifikation unten, alles andere geht weiter
            if not voruebergehend(e) or v == versuche - 1:
                raise
            neu = transportfehler(e)
            if log:
                log(f"{was}: Versuch {v + 1}/{versuche} gescheitert ({beschreibe(e)}) — "
                    f"wiederhole{' mit neuem Client' if neu else ''}")
            schlafen(v)
