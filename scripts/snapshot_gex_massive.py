"""
scripts/snapshot_gex_massive.py — täglicher GEX-Snapshot aus der MASSIVE-Voll-Chain
====================================================================================
Wie `snapshot_gex.py`, aber die Options-Chain kommt aus **Massive/Polygon** (Flatrate,
EOD-Open-Interest + Greeks/IV je Kontrakt) statt aus Yahoo. Damit fällt Yahoos
`openInterest=0`-Vormittagsloch weg — die Chain ist jederzeit vollständig.

Schreibt **exakt dasselbe Schema** wie snapshot_gex.py:
  landing/data/gex_summary.json          (Live-Summary für /dealer-positioning + /skew-Vol-Trigger)
  landing/data/gex_history/<YYYY-MM-DD>.json   (dagestempeltes, schlankes Archiv — proprietäre Historie)
  landing/data/gex_profile_<T>.json      (Per-Strike/Per-Term-Profile für die Charts)

Datenquelle (alles Flatrate/unlimited über MASSIVE_API_KEY):
  • Spot     GET /v2/aggs/ticker/<SYM>/prev            (EOD-Close = passt zum EOD-OI-Snapshot)
  • Chain    GET /v3/snapshot/options/<SYM>?expiration_date.lte=<hi>&limit=250   (paginiert via next_url)
Greeks werden NICHT von Polygon übernommen, sondern intern per Black-Scholes neu gerechnet
(dieselbe Engine + `--self-test`-Beweis wie die Yahoo-Variante) — nur K/OI/IV/T/typ fließen ein.

  PYTHONUTF8=1 py -3.14 scripts/snapshot_gex_massive.py
  PYTHONUTF8=1 py -3.14 scripts/snapshot_gex_massive.py --tickers SPY,QQQ,IWM   # Teilmenge (verify)
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from shared.atomic_json import write_json_atomic
from shared.niveau_felder import feldzustand, strike_stufe  # noqa: E402
from shared.env_loader import load_env  # noqa: E402
from shared.yahoo_downloader import _fetch_yahoo  # noqa: E402
from shared.exchange_holidays import (  # noqa: E402
    letzte_session, pruefe_eod_fenster, is_trading_day, MarktOffen)
load_env()
# GEX-Engine (Black-Scholes-Greeks + Aggregation) — unverändert wiederverwendet.
from compute_gamma_exposure import (  # noqa: E402
    _exposures, _zero_gamma, _walls, _skew, _profile, _profile_by_term, _INDEX_TICKERS,
)
# Universum/Horizonte aus der Yahoo-Variante importieren → EIN Ort der Wahrheit, damit
# gex_summary.json (Frontend) und die dagestempelte Historie deckungsgleich bleiben.
from snapshot_gex import UNIVERSE, CHART_TICKERS, MAX_DAYS, PROFILE_MAX_DAYS  # noqa: E402
# Import-Einstieg: ein Schutz nur am __main__ ist ein Schutz fuer EINEN Aufrufer
# (v66.12). Wer dieses Modul importiert und die Rechnung direkt aufruft, haelt den
# geteilten Lock ab hier bis zum Prozessende.
if __name__ != "__main__":
    from shared.produktionssperre import modul_sperre
    modul_sperre("snapshot_gex_massive")


_DATA = _ROOT / "landing" / "data"

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_UA = {"User-Agent": "SeasonAlpha/1.0"}
_THROTTLE = 0.05          # s zwischen Massive-Seiten (Flatrate, kleiner Puffer)
_MAX_PAGES = 120          # Seiten-Cap (250 Kontrakte/Seite) — deckt auch die 1200d-Profil-Chains
_MIN_CONTRACTS = 20       # darunter ist der Snapshot kaputt (Fetch-Fehler), nicht bloß illiquide
_IV_LO, _IV_HI = 0.01, 5.0  # Polygon liefert für Deep-ITM/OTM Müll-IV (~0.0004) → verwerfen
_Q = 0.0                  # Dividendenrendite: bei ≤45d-Horizont für Gamma/GEX/Walls vernachlässigbar

_SNAP = "https://api.polygon.io/v3/snapshot/options/{sym}?expiration_date.lte={hi}&limit=250"

# Ergebnis des Laufs als MARKER auf stdout. Die Huelle (deploy/systemd/gex_kette.sh)
# liest ihn und entscheidet, ob compute_key_levels startet. Der Marker wird NICHT aus
# dem Exit-Code geraten: "nichts getan" und "veroeffentlicht" sind beide Exit 0, und
# ein Trockenlauf darf keinen schreibenden Folgeschritt ausloesen. Der Exit-Code hat
# trotzdem Vorrang (Exit 75 der Produktionssperre entsteht VOR main(), also ohne
# Marker) — siehe die Entscheidungstabelle in der Huelle.
_MARKER = "[ergebnis] "
ERG_VEROEFFENTLICHT = "veroeffentlicht"
ERG_UEBERSPRUNGEN = "uebersprungen"
ERG_TROCKEN = "trocken"


def _marker(ergebnis: str, warum: str = "") -> None:
    print(f"{_MARKER}{ergebnis}" + (f" ({warum})" if warum else ""), flush=True)


# Obergrenze fuer ALLE 429-Pausen dieses PROZESSES, nicht je Abruf. Gemessen am
# 21.10.2026: die Kette braucht ohne Wartezeiten 593 s (Snapshot 516 + Key Levels 77).
# Ein Budget je Abruf waere das falsche Mass — im Yahoo-Loch fragen alle 20 Ticker
# Massive, 20 x 90 s haetten die 22-Minuten-Frist der Unit gesprengt, und zwar genau
# im Rettungsfall. Ist das Budget aufgebraucht, wird nicht mehr gewartet: der Ticker
# faellt aus und die Reissleine entscheidet. Ein kontrollierter Abbruch mit
# unveraenderten Dateien ist besser als eine Frist, die mitten im Schreiben zuschlaegt.
_WARTE_BUDGET = 300.0
_gewartet_gesamt = 0.0     # Prozesszustand; `_warte_zuruecksetzen()` fuer Tests


def _retry_after(e) -> float | None:
    """`Retry-After` in Sekunden, falls der Anbieter ihn als Zahl mitschickt.
    Ein HTTP-Datum wird nicht ausgewertet — dann gilt der eigene Backoff."""
    try:
        wert = (e.headers or {}).get("Retry-After")
    except Exception:
        return None
    try:
        s = float(str(wert).strip())
    except (TypeError, ValueError):
        return None
    return s if 0 <= s <= 3600 else None


def _warte_zuruecksetzen() -> None:
    """Wartebudget des Prozesses zuruecksetzen (Waechter, Mehrfachlaeufe im Test)."""
    global _gewartet_gesamt
    _gewartet_gesamt = 0.0


def _get(url: str, key: str, tries: int = 5):
    """GET (Massive: apiKey als Query-Param, NICHT Header) mit 429-Backoff.

    `Retry-After` hat Vorrang vor dem eigenen Backoff: der Anbieter kennt die noetige
    Pause besser. Beides zusammen bleibt unter `_WARTE_BUDGET` — und das Budget gilt
    fuer den GANZEN Prozess, nicht je Abruf (siehe Kommentar an der Konstante)."""
    global _gewartet_gesamt
    full = url + ("&" if "?" in url else "?") + "apiKey=" + key
    for i in range(tries):
        time.sleep(_THROTTLE)
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(full, headers=_UA), timeout=30, context=_CTX).read())
        except urllib.error.HTTPError as e:
            if e.code != 429 or i >= tries - 1:
                raise
            pause = _retry_after(e)
            if pause is None:
                pause = 2.0 * (i + 1)
            if _gewartet_gesamt + pause > _WARTE_BUDGET:
                print(f"  [get] Wartebudget {_WARTE_BUDGET:.0f} s aufgebraucht "
                      f"({_gewartet_gesamt:.0f} s gewartet) — kein weiterer Versuch", flush=True)
                raise
            _gewartet_gesamt += pause
            time.sleep(pause)
    return None


_NY = ZoneInfo("America/New_York")


def _sessionschluss(session: date) -> datetime:
    """Regulärer Schluss der NYSE-Session als zeitzonenbewusster Zeitpunkt: 16:00 New York, an einem belegten Halbtag
    die Schlusszeit aus dem Kalender. Halbtag unbekannt → 16:00 (strenger; an einem echten Halbtag fiele der Ticker
    dann aus, statt einen ungeprüften Kurs zu nehmen)."""
    from shared.sitzungen import sitzung_info
    info = sitzung_info(session, "NYSE")
    hh, mm = 16, 0
    if info.get("halbtag") is True and info.get("schlusszeit"):
        hh, mm = (int(x) for x in str(info["schlusszeit"]).split(":")[:2])
    return datetime(session.year, session.month, session.day, hh, mm, tzinfo=_NY)


# --- Spot: zwei Quellen, benannte Ablehnungsgruende -----------------------------------
# Yahoo traegt den regulaeren Termin. Zwischen etwa 00:00 und 01:10 UTC liefert Yahoo den
# Tagesbalken der Session aber mit `close = null` (gemessen in der Nacht 16.->17.10.2026,
# Proben /root/yahoo_abend: 22:15 UTC 763.25, 00:15 und 00:45 UTC null, 02:00 UTC wieder
# 763.25) — `regularMarketTime` bleibt dabei korrekt. Genau dorthin hat der um Stunden
# verspaetete GitHub-Cron fuenf Naechte in Folge getroffen (15.-21.10.2026).
#
# Massive `/prev` deckt dieses Loch: in zwei vollstaendigen Proben-Naechten (19.->20. und
# 20.->21.10., /root/massive_abend) lieferte es ab 00:00 UTC den Balken der Session,
# davor den der Vorsession. Die beobachtete Uhrzeit ist KEIN Vertrag — verbindlich ist
# allein die Datumspruefung am Balken, die unabhaengig von der Uhr greift. Der direkte
# Tagesbalken (`/range/1/day/<session>/<session>`) bleibt bis 03:30 UTC auf 403 und ist
# deshalb keine Option.
GRUND_OK = "ok"
GRUND_KURS_FEHLT = "kurs_fehlt"                  # NUR dieser Grund oeffnet den Rueckfall
GRUND_KEIN_SCHLUSSNACHWEIS = "kein_schlussnachweis"
GRUND_KEIN_BALKEN = "kein_balken"
GRUND_MEHRERE_BALKEN = "mehrere_balken"
GRUND_KEINE_ANTWORT = "keine_antwort"
GRUND_STRUKTUR = "struktur"

_PREV = "https://api.polygon.io/v2/aggs/ticker/{sym}/prev?adjusted=false"
# Der Rueckfall gilt nur fuer belegte Aktien-/ETF-Symbole. `--tickers` nimmt beliebige
# Symbole an; ein Index (z. B. ^SPX) braucht einen eigenen Vertrag und ist hier NICHT
# zugesagt — ein ETF-Ersatz haette die falsche Strike-Basis.
_RUECKFALL_SYMBOLE = frozenset(UNIVERSE)


def _endlich(x) -> bool:
    """`math.isfinite` wandelt intern in float um und wirft bei sehr grossen
    Ganzzahlen OverflowError (nachgerechnet: `math.isfinite(10**400)` platzt).
    Eine JSON-Antwort darf so etwas enthalten, und der Vertrag lautet "None, kein
    Absturz" — also hier abfangen statt beim Aufrufer (Codex D5)."""
    try:
        return math.isfinite(x)
    except (OverflowError, TypeError, ValueError):
        return False


def _kurs_gueltig(c) -> bool:
    """Endliche positive Zahl, KEIN bool. `c > 0` allein reicht nicht: `True > 0` ist True
    und `float(True)` = 1.0, `inf > 0` ist ebenfalls True — beides waere ein Spot."""
    if isinstance(c, bool) or not isinstance(c, (int, float)):
        return False
    return _endlich(c) and c > 0


# Plausibler Zeitbereich 1990-01-01 .. 2100-01-01 in SEKUNDEN. Die Grenze ist nicht
# redundant zur Datumspruefung, auch wenn mein Mutationstest das zuerst nahelegte: sie
# faengt Werte, die sich gar nicht in ein Datum umrechnen LASSEN (NaN, 1e30) und die
# sonst als Ausnahme statt als benannter Grund endeten. Der Mutationstest hatte nur
# keinen Fixture-Fall dafuer — die Pruefung war nicht wirkungslos, mein Test war luecken-
# haft, und ich hatte daraus zuerst den falschen Schluss gezogen (Codex C3).
_ZEIT_MIN, _ZEIT_MAX = 631_152_000, 4_102_444_800


def _zeit_gueltig(t, faktor: int = 1) -> bool:
    """Umrechenbarer Unix-Zeitstempel. `faktor` 1000 fuer Millisekunden-Quellen."""
    if isinstance(t, bool) or not isinstance(t, (int, float)) or not _endlich(t):
        return False
    return _ZEIT_MIN <= t / faktor <= _ZEIT_MAX


def _als_zeit(t, faktor: int = 1) -> datetime:
    return datetime.fromtimestamp(t / faktor, tz=timezone.utc)


def _yahoo_spot(sym: str, session: date) -> tuple[float | None, str]:
    """Yahoo-Adapter. Gibt (Kurs, Grund) — bei Misserfolg ist der Grund die Begruendung.

    Quelle: Yahoo-Chart (5 Tage, Tagesbalken), Feld `close` — nicht `adjclose`. Nachweis,
    dass die Session beendet ist: `regularMarketTime` (letzter regulaerer Handel) liegt am
    oder nach dem regulaeren Schluss der Session (16:00 New York, an einem belegten
    Halbtag die Schlusszeit aus shared.sitzungen.sitzung_info). Ein Handel nur am
    Vormittag (Handelsstopp) oder eine stehengebliebene Intraday-Antwort besteht das am
    ABEND DER SESSION nicht; laeuft der Lauf erst am Folgetag, passiert `rmt` die
    Untergrenze — der gelieferte Kurs ist dann der Schluss der Zielsession, weil die
    Balkenauswahl ueber das SESSIONDATUM laeuft und nicht ueber `rmt`
    (Bestandsnachweis: verify_gex_session.py, Fall "folgetag" erwartet 700.0).

    Zeitstempel sind hier SEKUNDEN (Massive liefert Millisekunden) — die beiden Quellen
    haben verschiedene Rohschemata und deshalb getrennte Adapter."""
    d = _fetch_yahoo(sym, {"range": "5d", "interval": "1d"}, 15)
    if not d:
        return None, GRUND_KEINE_ANTWORT
    # AttributeError gehoert dazu: `chart.result = [null]` laesst res.get() auflaufen,
    # und das war in meinem ersten Entwurf nicht gefangen (Codex C3).
    try:
        res = d["chart"]["result"][0]
        ts = res.get("timestamp") or []
        closes = (res["indicators"]["quote"][0] or {}).get("close") or []
        rmt = (res.get("meta") or {}).get("regularMarketTime")
    except (KeyError, IndexError, TypeError, AttributeError):
        return None, GRUND_STRUKTUR
    if not isinstance(ts, list) or not isinstance(closes, list):
        return None, GRUND_STRUKTUR
    if len(ts) != len(closes):
        return None, GRUND_STRUKTUR
    schluss = _sessionschluss(session)
    # NaN, inf und absurd grosse Werte bestehen isinstance, lassen aber
    # fromtimestamp auflaufen — die Umrechnung wird deshalb kontrolliert abgefangen
    # und ergibt einen benannten Grund statt einer Ausnahme (Codex C3).
    if not _zeit_gueltig(rmt) or _als_zeit(rmt) < schluss:
        return None, GRUND_KEIN_SCHLUSSNACHWEIS
    treffer = []
    for t, c in zip(ts, closes):
        if not _zeit_gueltig(t):
            return None, GRUND_STRUKTUR
        if _als_zeit(t).astimezone(_NY).date() == session:
            treffer.append(c)
    if not treffer:
        return None, GRUND_KEIN_BALKEN
    if len(treffer) > 1:
        # Mehrere Tagesbalken mit demselben Sessiondatum sind eine kaputte Antwort, nicht
        # eine Auswahlfrage — welcher der Schluss ist, laesst sich nicht entscheiden.
        return None, GRUND_MEHRERE_BALKEN
    return (float(treffer[0]), GRUND_OK) if _kurs_gueltig(treffer[0]) else (None, GRUND_KURS_FEHLT)


def _massive_spot(sym: str, key: str, session: date) -> float | None:
    """Massive-Adapter: `/v2/aggs/ticker/<SYM>/prev?adjusted=false`.

    `adjusted=false` ist Pflicht — der Spot ist die Strike-Basis, ein bereinigter Kurs
    waere falsch (gleiche Begruendung wie Yahoo `close` statt `adjclose`).

    BENANNTE GRENZE: `/prev` liefert kein `regularMarketTime`-Aequivalent. Akzeptiert wird
    ein zum abgeschlossenen Sessiontag passendes Anbieteraggregat — NICHT der Nachweis
    eines letzten Handels zur Schlusssekunde. Dass die Session vorbei ist, steht vor dem
    Abruf fest (letzte_session + pruefe_eod_fenster + Handelstagpruefung). Mehr kann die
    Quelle nicht leisten; eine Zusage ueber einen „amtlichen" Schluss gibt es hier nicht."""
    if sym not in _RUECKFALL_SYMBOLE:
        print(f"  [spot] {sym}: kein Rueckfall — Symbol nicht im belegten Universum", flush=True)
        return None
    try:
        d = _get(_PREV.format(sym=sym), key)
    except urllib.error.HTTPError as e:
        print(f"  [spot] {sym}: Massive HTTP {e.code}", flush=True)
        return None
    except Exception as e:
        print(f"  [spot] {sym}: Massive {type(e).__name__}", flush=True)
        return None
    if not isinstance(d, dict):
        return None
    ergebnisse = d.get("results")
    if not isinstance(ergebnisse, list) or len(ergebnisse) != 1:
        print(f"  [spot] {sym}: Massive nicht genau ein Aggregat", flush=True)
        return None
    bar = ergebnisse[0]
    if not isinstance(bar, dict):
        return None
    # Antwortsymbol muss das angefragte sein (Verwechslung waere ein falscher Spot).
    # MINDESTENS EIN Feld muss da sein: mein erster Entwurf uebersprang die Pruefung,
    # wenn BEIDE fehlten — eine Antwort ohne Symbol haette den ausdruecklich
    # geforderten Nachweis dann gar nicht gebraucht (Codex C2).
    symbole = [f for f in (bar.get("T"), d.get("ticker")) if f is not None]
    if not symbole:
        print(f"  [spot] {sym}: Massive-Antwort ohne Symbol — nicht zuordenbar", flush=True)
        return None
    if any(str(f).upper() != sym.upper() for f in symbole):
        print(f"  [spot] {sym}: Massive antwortet fuer {symbole}", flush=True)
        return None
    # Millisekunden (Yahoo: Sekunden). Der Bereich faengt nicht nur falsche Einheiten,
    # sondern vor allem Werte, die sich nicht in ein Datum umrechnen lassen (1e30 besteht
    # isfinite und laesst fromtimestamp auflaufen).
    t = bar.get("t")
    if not _zeit_gueltig(t, 1000):
        print(f"  [spot] {sym}: Massive-Zeitstempel unbrauchbar ({t!r})", flush=True)
        return None
    if _als_zeit(t, 1000).astimezone(_NY).date() != session:
        # Genau der Fall, aus dem /prev in v66.20 verworfen wurde: vor 00:00 UTC liefert es
        # die Vorsession. Die Datumspruefung faengt das unabhaengig von der Uhrzeit.
        print(f"  [spot] {sym}: Massive-Balken {_als_zeit(t, 1000).astimezone(_NY).date()} "
              f"ist nicht die Session {session} — verworfen", flush=True)
        return None
    c = bar.get("c")
    if not _kurs_gueltig(c):
        print(f"  [spot] {sym}: Massive-Schluss unbrauchbar", flush=True)
        return None
    print(f"  [spot] {sym}: Yahoo ohne Kurs, Massive-Aggregat der Session genommen", flush=True)
    return float(c)


def _spot(sym: str, key: str, session: date) -> float | None:
    """Unbereinigter Schlusskurs des Underlyings an der Session (Strike-Basis).

    Yahoo zuerst (kostenlos, kein Rate-Limit). Der Rueckfall auf Massive oeffnet NUR bei
    GRUND_KURS_FEHLT: Balken der Session vorhanden, Schluss nachgewiesen, nur der Kurs
    fehlt. Jeder andere Grund bleibt eine Ablehnung — ein gleichdatierter Massive-Balken
    beweist die Tageszuordnung, aber nicht den Schlussnachweis, und darf ihn deshalb nicht
    aushebeln."""
    kurs, grund = _yahoo_spot(sym, session)
    if grund == GRUND_OK:
        return kurs
    if grund == GRUND_KURS_FEHLT:
        print(f"  [spot] {sym}: Tagesbalken der Session {session} ohne Kurs "
              f"(Schluss nachgewiesen) — Rueckfall", flush=True)
        return _massive_spot(sym, key, session)
    print(f"  [spot] {sym}: verworfen ({grund})", flush=True)
    return None


def _fetch_chain(sym: str, hi_days: int, key: str, session: date) -> tuple[list, bool]:
    """Volle Option-Chain (≤hi_days ab der Session), paginiert via next_url.

    Zurueck kommt (Kontrakte, vollstaendig). Vollstaendig ist der Abruf NUR, wenn er am
    Ende der Paginierung stand (`next_url` leer). Reisst das Seiten-Cap oder antwortet
    eine Seite unbrauchbar, ist die Kette abgeschnitten — vorher verwarf die Funktion
    diesen Zustand und gab in beiden Faellen dieselbe Liste zurueck, womit ein aus einer
    halben Kette gerechnetes Niveau nicht von einem vollstaendigen zu unterscheiden war
    (Spec B1)."""
    hi = (session + timedelta(days=hi_days)).isoformat()
    url = _SNAP.format(sym=sym, hi=hi)
    out, pages, vollstaendig = [], 0, True
    while url and pages < _MAX_PAGES:
        d = _get(url, key)
        if not d or (d.get("status") not in ("OK", "DELAYED") and not d.get("results")):
            vollstaendig = False
            break
        out += d.get("results", [])
        url = d.get("next_url")
        pages += 1
    if url:                      # Seiten-Cap gerissen, es gaebe noch eine Seite
        vollstaendig = False
    return out, vollstaendig


def _map(raw: list, session: date) -> list:
    """Polygon-Kontrakte → internes Engine-Format {type,K,oi,iv,T,exp,dte}.
    Verwirft Kontrakte ohne OI/IV und die Deep-ITM/OTM-Müll-IVs (~0).

    Bewertungsdatum ist die SESSION, nicht der Lauftag: DTE/T und die Laufzeitauswahl hängen sonst vom GitHub-Verzug
    ab. Kontrakte mit Verfall ≤ Session sind am Sessionschluss verfallen und fliegen raus — vorher blieben sie bei
    einem Lauf vor Mitternacht UTC mit T = 1e-6 drin (Gamma maximal) und fehlten danach (Plan v4 B2)."""
    out = []
    for c in raw:
        det = c.get("details") or {}
        typ = det.get("contract_type"); K = det.get("strike_price"); ex = det.get("expiration_date")
        oi = c.get("open_interest") or 0
        iv = c.get("implied_volatility") or 0.0
        if typ not in ("call", "put") or not K or not ex or not oi:
            continue
        if not (_IV_LO <= iv <= _IV_HI):
            continue
        dte = (date.fromisoformat(ex) - session).days
        if dte <= 0:
            continue
        out.append({"type": typ, "K": float(K), "oi": int(oi), "iv": float(iv),
                    "T": max(dte / 365.0, 1e-6), "exp": ex, "dte": dte})
    return out


def analyze_massive(sym: str, key: str, max_days: int,
                    profile_days: int | None = None, session: date | None = None) -> dict | None:
    """GEX-Objekt im EXAKTEN analyze()-Schema (compute_gamma_exposure), aber aus Massive-Daten.
    profile_days>None → fetch bis dorthin + hänge Per-Strike/Per-Term-Profil an."""
    horizon = profile_days or max_days
    if session is None:
        raise ValueError("analyze_massive: session (Bewertungsdatum) fehlt")
    spot = _spot(sym, key, session)
    if not spot:
        return None
    try:
        raw, kette_vollstaendig = _fetch_chain(sym, horizon, key, session)
    except Exception as e:
        print(f"  [massive] {sym} Chain: {str(e)[:80]}", flush=True)
        return None
    all_c = _map(raw, session)
    summary_c = [c for c in all_c if c["dte"] <= max_days]
    if len(summary_c) < _MIN_CONTRACTS:
        print(f"  [SKIP] {sym}: nur {len(summary_c)} brauchbare Kontrakte ≤{max_days}d "
              f"(von {len(raw)} roh) — Snapshot unbrauchbar.", flush=True)
        return None
    gex, vex, cex = _exposures(spot, summary_c, _Q)
    cw, pw, ag = _walls(spot, summary_c, _Q)
    n_exp = len({c["exp"] for c in summary_c})
    zg = _zero_gamma(spot, summary_c, _Q)
    stufe = strike_stufe(c["K"] for c in summary_c)
    obj = {
        "ticker": sym, "session": session.isoformat(), "spot": round(spot, 2), "div_yield": round(_Q, 4),
        "net_gex_usd_bn": round(gex / 1e9, 3),
        "net_vanna_usd_mn": round(vex / 1e6, 2),
        "net_charm_usd_mn_per_day": round(cex / 1e6, 2),
        "regime": "long_gamma" if gex > 0 else "short_gamma",
        "vol_regime": "vola-reduzierend" if gex > 0 else "vola-forcierend",
        "zero_gamma": zg,
        "call_wall": cw, "put_wall": pw, "abs_gamma": ag,
        # B1: Ladezustand, Rechenhorizont und Strike-Stufe sind Teil der Zeile. Ohne sie
        # kann die Seite weder Feldzustaende ableiten noch die Preispruefung aus Spec 2.2a
        # fuehren, und die Historie waere von Anfang an mehrdeutig.
        "gex_kette_vollst": kette_vollstaendig,
        "gex_horizont_tage": max_days,
        "strike_stufe": stufe,
        "strike_stufe_quelle": "gex_kette" if stufe is not None else None,
        "felder": {
            "call_wall": feldzustand(cw, kette_vollstaendig),
            "put_wall": feldzustand(pw, kette_vollstaendig),
            "vol_trigger": feldzustand(zg, kette_vollstaendig),
        },
        "skew": _skew(spot, summary_c),
        "n_contracts": len(summary_c), "n_expiries": n_exp,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "US-EOD-Optionskette (OI+IV je Kontrakt) · naive Dealer-Vorzeichen "
                "(long Calls/short Puts) = Heuristik, keine echten Dealer-Bücher · "
                "Greeks Black-Scholes (q=0 bei ≤45d vernachlässigbar)",
    }
    if profile_days:
        obj["profile"] = {"by_strike": _profile(spot, all_c, _Q),
                          "by_term": _profile_by_term(spot, all_c, _Q)}
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", help="Komma-Liste statt Voll-Universum (Verify/Teilmenge)")
    ap.add_argument("--no-write", action="store_true", help="nur rechnen + drucken, nichts schreiben")
    ap.add_argument("--reparatur", action="store_true",
                    help="ausdruecklicher Reparaturlauf: ohne Handelstagpruefung (fuer einen "
                         "Nachholauf an einem Boersenfeiertag). Der Notausloeser im Workflow "
                         "nutzt ihn; der Timer NICHT.")
    a = ap.parse_args()

    key = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
    if not key:
        print("[snapshot] ABBRUCH: MASSIVE_API_KEY fehlt (.env).", flush=True)
        return 1
    # Session EINMAL bestimmen: Stempel UND Bewertungsdatum. Schreibläufe in der Handelszeit brechen VOR dem ersten
    # Abruf ab (der Snapshot wäre ein Intraday-Stand mit dem Datum der Vorsession).
    session = letzte_session("NYSE")
    if not a.no_write:
        try:
            pruefe_eod_fenster("snapshot_gex_massive")
        except MarktOffen as e:
            print(f"[snapshot] ABBRUCH: {e}", flush=True)
            return 2
    # Handelstagpruefung — nur im AUTOMATISCHEN Modus (Timer). Ohne sie feuert ein
    # Werktagstimer auch an Boersenfeiertagen: `markt_offen` ist dann False (der EOD-Test
    # laesst also durch) und `letzte_session` zeigt auf eine Session, die in der Nacht
    # davor schon veroeffentlicht wurde — der Lauf wuerde sie mit einen Tag spaeter
    # abgerufenen Daten UEBERSCHREIBEN. Gemessen: Thanksgiving 2026 (Do 26.11.) ->
    # letzte_session 25.11.; 25.12. -> 24.12.; 03.07. -> 02.07.
    # `--reparatur` und `--no-write` sind davon ausgenommen, sonst waere ein Nachholauf
    # am Feiertag gesperrt (der Notausloeser im Workflow braucht genau das).
    # Gerechnet wird in NEW YORK: ein Lauf um 01:30 UTC liegt dort noch am Vortag.
    if not a.no_write and not a.reparatur:
        # Uhr ueber exchange_holidays._uhr, NICHT datetime.now: die Funktion existiert
        # ausdruecklich, damit Waechter die Uhr festsetzen koennen (ihr eigener Docstring
        # sagt das). Mein erster Entwurf nahm datetime.now(_NY) — damit haette der
        # Waechter den Feiertagsfall nie pruefen koennen, und ein Test, dessen Ergebnis
        # vom Kalender des Testtags abhaengt, ist kein Test.
        from shared.exchange_holidays import _uhr
        heute_ny = _uhr(_NY).date()
        if not is_trading_day(heute_ny, "NYSE"):
            print(f"[snapshot] {heute_ny} ist kein NYSE-Handelstag — kein Abruf, nichts "
                  f"geschrieben. Die letzte Session ({session}) ist bereits veroeffentlicht; "
                  f"ein Nachholauf braucht --reparatur.", flush=True)
            _marker(ERG_UEBERSPRUNGEN, f"kein Handelstag {heute_ny}")
            return 0

    universe = ([t.strip().upper() for t in a.tickers.split(",") if t.strip()]
                if a.tickers else list(UNIVERSE))
    chart_set = set(CHART_TICKERS)

    results, charts, failed = [], {}, []
    for tk in universe:
        try:
            profile_days = PROFILE_MAX_DAYS if tk in chart_set else None
            o = analyze_massive(tk, key, MAX_DAYS, profile_days=profile_days, session=session)
        except Exception as e:
            o = None
            print(f"  [WARN] {tk}: {type(e).__name__}: {e}", flush=True)
        if not o:
            failed.append(tk)
            gc.collect()
            continue
        prof = o.pop("profile", None)
        results.append(o)
        flip = o["zero_gamma"]
        pos = f"Spot {o['spot']} {'ÜBER' if (flip and o['spot'] >= flip) else 'UNTER'} Flip {flip}"
        print(f"  [{tk:5}] GEX {o['net_gex_usd_bn']:+.3f}  {o['regime']:<12} {pos}  "
              f"CallW {o['call_wall']} PutW {o['put_wall']}  n={o['n_contracts']}", flush=True)
        if tk in chart_set:
            charts[tk] = prof
            if prof:
                print(f"          Profil {PROFILE_MAX_DAYS}d: {len(prof.get('by_term', []))} Verfälle, "
                      f"{len(prof.get('by_strike', []))} Strikes", flush=True)
        gc.collect()

    # Reissleine (identisch zur Yahoo-Variante): lieber gar nichts schreiben als die guten
    # bestehenden JSONs mit einem halben Lauf überbügeln.
    if len(results) < 0.6 * len(universe):
        print(f"[snapshot] ABBRUCH: nur {len(results)}/{len(universe)} Ticker brauchbar "
              f"(Fehlschläge: {failed}). Bestehende JSONs bleiben unverändert.", flush=True)
        return 1

    idx = [o for o in results if o["ticker"] in _INDEX_TICKERS]
    gamma_index = None
    if idx:
        val = round(sum(o["net_gex_usd_bn"] for o in idx), 3)
        gamma_index = {"value_usd_bn_per_pct": val,
                       "vol_regime": "vola-reduzierend" if val > 0 else "vola-forcierend",
                       "components": [o["ticker"] for o in idx]}

    stamp = session.isoformat()
    meta = {"date": stamp, "session": stamp, "bewertung": stamp, "stempel_art": "session"}
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **meta, "gamma_index": gamma_index, "tickers": results, "failed": failed,
        "note": "Naive Dealer-Heuristik (long Calls/short Puts), US-EOD-Optionskette, "
                "kein Handelssignal — Referenzen, keine Barrieren.",
    }
    print(f"\n[gamma-index] {gamma_index['value_usd_bn_per_pct'] if gamma_index else '—'} Mrd $/1 % "
          f"({gamma_index['vol_regime'] if gamma_index else '—'})", flush=True)

    if a.no_write:
        print("[snapshot] --no-write: nichts geschrieben.", flush=True)
        _marker(ERG_TROCKEN)
        return 0

    _DATA.mkdir(parents=True, exist_ok=True)
    write_json_atomic(_DATA / "gex_summary.json", summary, indent=2)
    for tk, prof in charts.items():
        write_json_atomic(_DATA / f"gex_profile_{tk.replace('^', '')}.json",
                          {"ticker": tk, **meta, "max_days": PROFILE_MAX_DAYS,
                           "profile": prof}, indent=None)

    # Archiv je SESSION in eigenem Ordner. Der alte Ordner gex_history/ trägt Lauftage (oft eine Session zu spät,
    # belegt 2026-10-14) und bekommt nichts mehr; keine Migration (die Zuordnung ist ohne generated_at nicht ableitbar).
    hist = _DATA / "gex_history_session"
    hist.mkdir(exist_ok=True)
    slim = {**meta, "gamma_index": gamma_index,
            "tickers": [{k: o[k] for k in ("ticker", "spot", "net_gex_usd_bn", "net_vanna_usd_mn",
                                           "net_charm_usd_mn_per_day", "regime", "zero_gamma",
                                           "call_wall", "put_wall", "skew",
                                           # B1: ohne diese vier ist eine Archivzeile als
                                           # Vergleichswert nicht berechtigt (Spec 6.1a).
                                           "gex_kette_vollst", "gex_horizont_tage",
                                           "strike_stufe", "felder")} for o in results]}
    write_json_atomic(hist / f"{stamp}.json", slim, indent=None)

    print(f"[snapshot] {len(results)} ok / {len(failed)} fail · Gamma-Index "
          f"{gamma_index['value_usd_bn_per_pct'] if gamma_index else '—'} · Archiv {stamp}.json", flush=True)
    _marker(ERG_VEROEFFENTLICHT, f"Session {stamp}")
    return 0


if __name__ == "__main__":
    from shared.produktionssperre import produktion
    with produktion("snapshot_gex_massive"):
        sys.exit(main())
