#!/usr/bin/env python3
"""
compute_options_skew.py — Options-Skew, IV-Term-Structure & Vol-Metriken, daily.

Ebenen:
  1) Markt-Gauges (gratis, kein Key): ^SKEW, ^VIX, ^VVIX via yahoo_downloader.
  2) Per-Ticker via Massive/Polygon Option-Chain-Snapshot (flatrate, EIN Fetch/Ticker):
     - 25Δ-Skew (Put-IV − Call-IV) bei 30d UND 90d  → Skew + Skew-Term-Structure
     - ATM-IV-Term-Structure über mehrere Laufzeiten (Contango/Backwardation)
     - VRP = ATM-IV(30d) − realisierte Vola (aus unseren Kursen)
     - 25Δ-Butterfly = (Put25+Call25)/2 − ATM  (Smile-Krümmung)
     - Put/Call-IV-Ratio

Schreibt landing/data/options_skew.json (+ akkumuliert options_skew_history.json).

Nutzung:  py -3.14 scripts/compute_options_skew.py [--tickers AAPL SPY QQQ]
"""
from __future__ import annotations
import argparse, gc, json, math, os, ssl, sys, time, urllib.error, urllib.request
from datetime import date, timedelta
from pathlib import Path

_THROTTLE = 0.05  # s zwischen Massive-Seiten (flatrate/unlimited; kleiner Puffer)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.env_loader import load_env          # noqa: E402
load_env()
from shared.yahoo_downloader import download_data, clear_cache  # noqa: E402
from shared.options_universe import all_option_tickers, categories_for, OPTIONS_CATEGORIES  # noqa: E402
from shared.exchange_holidays import is_trading_day, letzte_session, MarktOffen, pruefe_eod_fenster   # noqa: E402
from shared.atomic_json import write_json_atomic                      # noqa: E402
from shared.realized_vol import (RV_FENSTER, kappe_auf,               # noqa: E402
                                 rv_aus_closes)
from shared.data import KursreiheFehlt, lade_closes                   # noqa: E402
from shared.black_scholes import (diagnose_start as _diagnose_start,
                                  diagnose_stop as _diagnose_stop,
                                  bs_delta, implied_vol, cm_interp as _cm_interp,  # noqa: E402
                                  CM_DAYS as _CM_DAYS, CM_DTE_MIN as _CM_DTE_MIN,
                                  CM_DTE_MAX as _CM_DTE_MAX, CM_SINGLE_TOL as _CM_SINGLE_TOL,
                                  DELTA_TOL as _DELTA_TOL, VOL_PCTL as _CM_VOL_PCTL,
                                  leg_from_prices, standardserie_filter,
                                  atm_from_prices, smile_from_prices, SMILE_DELTAS,
                                  _gefilterte_punkte,
                                  cm_leg_kandidaten as _cm_leg_kandidaten,
                                  ist_monatsverfall, _zaehl as _bs_zaehl,
                                  IV_MIN as _IV_MIN, IV_MAX as _IV_MAX)


_RANKBAR = ("cm", "cm_extrap")


def _rankbar(e: dict | None) -> bool:
    """Traegt diese History-Zeile zum Ranking bei? Muss exakt
    `landing/pages/skew.html::_isNorm` entsprechen. `noatm` und `single`
    sind NICHT rankbar, obwohl ihr cm_mode nicht None ist — genau daran
    scheiterte die erste Fassung der Ersetzungsregel (Codex-Review
    2026-09-25): eine noatm-Zeile blockierte den rankbaren Punkt."""
    return bool(e) and e.get("cm_mode") in _RANKBAR


def _last_session(d: date | None = None) -> str:
    """Letzter NYSE-Handelstag ≤ d. Das Options-Universum ist komplett US-gelistet.

    Der Cron läuft täglich um 23:00 UTC — auch samstags, sonntags und an
    Feiertagen. Mit date.today() gestempelt landeten dadurch Einträge auf Tagen
    ohne Handel in der History, die immer die Daten der letzten Session
    duplizieren. Das verfälscht jede Percentile-Berechnung (aufgeblähte
    Stichprobe mit Doppelwerten) und verstößt gegen die Grundregel, in
    Handelstagen statt Kalendertagen zu rechnen.

    EINE SESSION GILT ERST NACH DEM US-HANDELSSCHLUSS ALS ABGESCHLOSSEN.
    Der Cron steht auf 23:00 UTC, GitHub startet ihn aber regelmaessig mit
    ein bis zwei Stunden Verzug — gemessen 2026-09-18 bis 25: 00:44, 00:52,
    00:56, 00:59, 01:00, 01:20 UTC. Nach Mitternacht UTC ist `date.today()`
    schon der FOLGETAG. Ist der ein Handelstag, stempelte diese Funktion eine
    Session, die noch nicht gehandelt hatte, auf Daten vom Vortag.
    Folge am 2026-09-25: alle 161 Ticker bekamen eine Zeile mit `date`
    2026-09-25, waehrend die Kursreihe (korrekt) am 24. endete. Der
    Frische-Waechter unten verweigerte daraufhin die cm-Normierung — fuer
    JEDEN Ticker — und das Frontend hatte keinen aktuellen normierten Punkt
    mehr: **0 von 165 Tickern im Radar**, `method` faellt auf `provider`
    zurueck (genau die Methodenmischung, die v54 beseitigt hat).
    Der Waechter war richtig, der Stempel war falsch.

    Deshalb: vor 16:15 ET gehoert der laufende Kalendertag noch nicht in die
    Historie. Grenze in ET statt UTC gerechnet, damit die Sommerzeit
    (20:00 UTC im Sommer, 21:00 im Winter) nicht von Hand nachgezogen werden
    muss. Verkuerzte Handelstage (Schluss 13:00 ET) fallen bewusst unter
    dieselbe Regel: der Cron laeuft um 19:00 ET, lange danach; ein
    Ad-hoc-Lauf um 14:00 ET stempelt lieber die Vorsession als eine
    unfertige.

    Ein ausdruecklich uebergebenes `d` bleibt unangetastet — `_fix_session_dates`
    datiert damit Alt-Eintraege um und braucht reine Kalenderlogik."""
    if d is None:
        # Eine Kopie dieser Regel in jedem Cron wuerde driften (dieselbe
        # Fehlerklasse wie die beiden Black-Scholes-Kopien mit
        # verschiedenen Zinssaetzen) -> EINE Quelle in shared/.
        return letzte_session("NYSE").isoformat()
    for _ in range(10):
        if is_trading_day(d, "NYSE"):
            return d.isoformat()
        d -= timedelta(days=1)
    return d.isoformat()


def _fix_session_dates(hist: dict) -> tuple[int, int]:
    """Alt-Einträge auf ihren tatsächlichen Handelstag umdatieren (selbstheilend).

    Ein am Samstag geschriebener Eintrag enthält die Chain von Freitag — der Wert
    stimmt, nur das Label war falsch. Deshalb umdatieren statt löschen. Danach
    dedupen: die Einträge von Sonntag und Feiertag fallen als Duplikate derselben
    Session weg. Bei Kollision gewinnt der Provider-Eintrag gegen eine
    BS-Rekonstruktion (echte IV schlägt invertierte)."""
    moved = dropped = 0
    for k, arr in hist.items():
        by_date: dict = {}
        for e in arr:
            try:
                s = _last_session(date.fromisoformat(e["date"]))
            except Exception:
                by_date.setdefault(e.get("date"), e)      # unparsbar: unangetastet behalten
                continue
            if s != e["date"]:
                e["date"] = s; moved += 1
            cur = by_date.get(s)
            if cur is None:
                by_date[s] = e
            else:
                dropped += 1
                # Normiert schlaegt nicht-normiert: ein laufzeitnormierter Punkt
                # (cm/cm_extrap) traegt die Rangfolge, ein Front-Monats-Punkt
                # nicht. Frueher gewann pauschal der Live-Eintrag — der konnte
                # damit einen brauchbaren Backfill-Punkt verdraengen und die
                # Stichprobe verkleinern.
                _norm = _rankbar
                if _norm(e) and not _norm(cur):
                    by_date[s] = e
                elif _norm(e) == _norm(cur) and cur.get("reconstructed") and not e.get("reconstructed"):
                    by_date[s] = e
        hist[k] = sorted(by_date.values(), key=lambda e: e.get("date") or "")
    return moved, dropped

_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
# Massive.com (Polygon.io) Option-Chain-Snapshot — Flatrate, 1 Ticker = ganze Chain
# (Greeks/IV/OI je Kontrakt), paginiert. Ersetzt die per-Kontrakt-bepreiste marketdata-API.
_SNAP = "https://api.polygon.io/v3/snapshot/options/{sym}?expiration_date.lte={hi}&limit=250"
_MAXDTE = 190                       # nur Laufzeiten ≤190d (deckt Term-Structure + 25Δ ab)
_TERM_TARGETS = (7, 30, 60, 90, 120, 180)
_DEFAULT_TICKERS = all_option_tickers()   # thematisch gegliedertes US-Options-Universum


def _get(url: str, key: str, tries: int = 5):
    """GET (Massive: apiKey als Query-Param) mit 429-Backoff."""
    full = url + ("&" if "?" in url else "?") + "apiKey=" + key
    for i in range(tries):
        time.sleep(_THROTTLE)
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(full, headers={"User-Agent": "SeasonAlpha/1.0"}),
                timeout=30, context=_CTX).read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < tries - 1:
                time.sleep(2.0 * (i + 1))
                continue
            raise


def _spot(sym: str, key: str):
    """EOD-Vortagsschluss als Spot-Proxy (Underlying im Snapshot ist oft leer)."""
    try:
        d = _get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/prev", key)
        r = d.get("results") or []
        return round(float(r[0]["c"]), 2) if r else None
    except Exception:
        return None


def _chain(sym: str, key: str, spot=None) -> list:
    """Option-Chain (≤190d) als Kontraktliste (paginiert). Bei bekanntem Spot auf
    ±30 % Moneyness gefiltert — spart viele Seiten (25Δ+ATM liegen near-the-money)."""
    hi = (date.today() + timedelta(days=_MAXDTE)).isoformat()
    url = _SNAP.format(sym=sym, hi=hi)
    if spot:
        url += f"&strike_price.gte={round(spot * 0.7, 2)}&strike_price.lte={round(spot * 1.3, 2)}"
    out, pages = [], 0
    while url and pages < 45:
        d = _get(url, key)
        if d.get("status") not in ("OK", "DELAYED") and not d.get("results"):
            break
        out += d.get("results", [])
        url = d.get("next_url")
        pages += 1
    return out




def _pick(lst, target, tol=None):
    """Kontrakt mit |delta| am nächsten an target (lst = [(delta, iv, strike, oi), …]).

    tol: maximal erlaubte Abweichung vom Ziel. Ohne Toleranz liefert min() IMMER
    einen Treffer — bei dünner Kette also z.B. einen 0,40Δ-Kontrakt, der dann still
    als „25Δ" etikettiert wird und den Ticker-übergreifenden Vergleich verfälscht.
    Mit tol wird daraus None → der Ticker fällt für den Tag sauber raus."""
    if not lst:
        return None
    best = min(lst, key=lambda x: abs(abs(x[0]) - target))
    if tol is not None and abs(abs(best[0]) - target) > tol:
        return None
    return best


def _byexp(contracts: list) -> dict:
    """Kontrakte je Verfallstag: {exp: {dte, call:[(δ,iv,K,oi)], put:[…], spot}}."""
    # Restlaufzeit gegen die SESSION, zu der die Chain gehoert — nicht gegen
    # date.today(). Nach Mitternacht UTC (Cron mit Verzug) war jede dte einen
    # Tag zu kurz, und _nearest_exp(by, 30) waehlte damit ggf. einen anderen
    # Verfall als "30 Tage". Befund Codex-Review 2026-09-25.
    today = date.fromisoformat(_last_session()); by = {}
    for c in contracts:
        g = c.get("greeks") or {}; iv = c.get("implied_volatility"); dl = g.get("delta")
        if iv is None or dl is None:
            continue
        det = c.get("details") or {}; ex = det.get("expiration_date"); typ = det.get("contract_type")
        if not ex or typ not in ("call", "put"):
            continue
        dte = (date.fromisoformat(ex) - today).days
        e = by.setdefault(ex, {"dte": dte, "call": [], "put": []})
        e[typ].append((float(dl), round(float(iv), 4), det.get("strike_price"), c.get("open_interest")))
    return by


def _index_series(sym: str, days: int = 504) -> dict:
    """Letzte ~days Handelstage: {dates:[...], vals:[...]} + letzter Wert.

    Bleibt BEWUSST bei Yahoo, obwohl _realized_vol auf Supabase umgestellt
    wurde: hier kommen Volatilitaetsindizes herein (^VIX, ^SKEW, ^VVIX,
    ^COR1M/3M/30D). Die zahlen keine Dividende, also gibt es keine
    Adjustierung, die wandern koennte — der Grund fuer die Umstellung trifft
    hier nicht zu. Ausserdem stehen diese Indizes nicht vollstaendig in
    Supabase (^COR* liefert Yahoo ohnehin nur den letzten Wert, weshalb die
    Historie vorwaerts akkumuliert wird).
    """
    try:
        df = download_data(sym, period="max")
        clear_cache()
        if df is None or len(df) == 0:
            return {}
        dts = [str(d)[:10] for d in (df["Date"] if "Date" in df.columns else df.index).tolist()][-days:]
        vals = [None if v != v else round(float(v), 2) for v in df["Close"].to_numpy()[-days:]]
        return {"dates": dts, "vals": vals, "last": vals[-1], "date": dts[-1]}
    except Exception as e:
        print(f"  [idx] {sym}: {e}")
        return {}


def _rv_ab(bis: str | None, monate: int = 8) -> str:
    """Fruehestes Datum fuer das Laden der Kursreihe.

    Ein 21-Handelstage-Fenster braucht gut einen Monat; acht Monate geben
    Luft fuer Feiertage, Handelspausen und den n+5-Puffer, ohne die ganze
    Historie zu ziehen (das waren bei 165 Tickern sonst Millionen Zeilen).
    """
    ende = date.fromisoformat(bis) if bis else date.today()
    jahr, monat = ende.year, ende.month - monate
    while monat <= 0:
        monat += 12
        jahr -= 1
    return f"{jahr:04d}-{monat:02d}-01"


def _realized_vol(sym: str, n: int = 21, bis: str | None = None):
    """Annualisierte realisierte Vola über n Handelstage (CBOE-Formel), Decimal.
    n=21 = 1 Monat (passt zur 30-Kalendertage-ATM-IV für den VRP).
    RV = sqrt( 252/(N-1) · Σ(R_t − R̄)² ), R_t = ln(P_t/P_{t-1}).

    Rückgabe: (rv, last_close, last_date). Der letzte Close dient als Spot-Fallback —
    der Massive-Endpoint liefert das Underlying nicht immer (ARM am 2026-09-08:
    Spot 0,00), und die Kursreihe ist hier ohnehin schon geladen.

    `last_date` MUSS mitkommen und vom Aufrufer gegen die Session geprüft werden.
    Ein um eine Session veralteter Spot verschiebt den Forward, damit den
    Moneyness-Anker UND über `bs_delta(spot, K, T, iv_atm, typ)` die 25Δ-Auswahl
    beider Flügel — ein einziger falscher Spot erzeugt also alle Symptome
    gleichzeitig: gekipptes Skew-Vorzeichen, `iv_atm` über beiden Flügeln, und
    Legs, die an der Delta-Toleranz scheitern. Gemessen am 2026-09-18: der aus
    den veröffentlichten IVs zurückgerechnete Spot lag bei NVDA 3,0 % und bei
    SPY 0,94 % unter dem echten Schluss; mit dem korrekten Schluss sind dieselben
    Ticker sauber."""
    # QUELLE: Supabase, ohne stillen Rueckfall auf Yahoo. `download_data`
    # liefert ADJUSTIERTE Kurse, und die Adjustierung wandert mit jeder
    # Dividende — dieselbe Abfrage ergibt an verschiedenen Tagen verschiedene
    # Reihen. Fuer eine Historie, aus der ein ticker-internes Perzentil
    # gebildet wird, ist das unbrauchbar: der heutige Punkt verschiebt sich
    # gegen die gespeicherten. Begruendung, Messung und der in Kauf genommene
    # Restfehler stehen bei shared.data.lade_closes.
    #
    # Ein Ticker ohne Reihe beendet den Lauf NICHT — er bekommt kein rv und
    # keinen Spot-Fallback, damit faellt unten die cm-Normierung aus
    # (fail-closed). Gemeldet wird es aber, sonst ist es ein stiller Ausfall.
    try:
        daten_alle, closes_alle = lade_closes(sym, ab=_rv_ab(bis),
                                              mindestens=n + 5)
    except KursreiheFehlt as e:
        print(f"  {sym:6} {e} -> kein rv, kein Spot-Fallback", flush=True)
        return None, None, None
    except Exception as e:
        print(f"  {sym:6} Kursreihe nicht ladbar ({e}) -> kein rv", flush=True)
        return None, None, None
    # ZUERST auf die Session kappen, DANN rechnen. Sonst stammt die realisierte
    # Vola aus einem Fenster, das ueber die Session hinausreicht — und bliebe
    # selbst dann falsch, wenn der Spot als veraltet verworfen wird.
    # (Der umgekehrte Fall, eine Reihe die VOR der Session endet, wird unten
    # ueber last_d erkannt und fuehrt zum Verzicht auf die cm-Normierung.)
    #
    # ACHTUNG, HIER SASS EIN FEHLER (gefunden 2026-09-19): die Kappung lief als
    # `df[df.index <= bis]` auf dem DatetimeIndex. Dessen Werte tragen eine
    # UHRZEIT (Timestamp('2026-09-18 13:30:00') = NYSE-Open in UTC), also wurde
    # der Vergleich zu `<= 2026-09-18 00:00:00` und schnitt die Session WEG.
    # Folge: die realisierte Vola lief taeglich auf einem Fenster, das einen
    # Handelstag zu frueh endete, und `last_d` war immer der Vortag — der
    # Frische-Waechter unten meldete deshalb JEDEN Tag eine veraltete Reihe,
    # obwohl der Tag vorhanden war. Gemessen am 2026-09-19: _last_session()
    # 2026-09-18, last_d 2026-09-17 bei SPY/QQQ/NVDA, VRP um 0,26-0,75 pp
    # verschoben. Jetzt wird auf Kalendertagen verglichen, nicht auf
    # Zeitstempeln (shared/realized_vol.kappe_auf).
    try:
        daten, closes = kappe_auf(daten_alle, closes_alle, bis)
    except Exception:
        return None, None, None
    if not closes:
        return None, None, None
    c = closes
    last = round(float(c[-1]), 2) if c[-1] == c[-1] else None
    last_d = daten[-1]
    # n+5 statt n+1: ein Puffer gegen Reihen, die gerade eben reichen. Bewusst
    # beibehalten, damit die Umstellung keine Zahl verschiebt. Gezaehlt wird
    # auf der GEKAPPTEN Reihe — vorher stand hier len(df), was nach der Kappung
    # dasselbe war, jetzt aber auseinanderfallen wuerde.
    if len(c) < n + 5:
        return None, last, last_d
    # Die Formel liegt in shared/realized_vol.py — dieselbe Funktion nutzt die
    # Nachruestung des VRP fuer vergangene Tage (scripts/backfill_skew_vrp.py).
    # Zwei Implementierungen derselben Mathematik driften; nachgewiesen
    # identisch zur vorherigen Fassung in scripts/verify_realized_vol.py.
    return rv_aus_closes(c, n), last, last_d


# Standard-Monatsverfall = 3. Freitag. Alias auf die gemeinsame Definition in
# shared/black_scholes.py — zwei Kopien derselben Regel driften.
_is_monthly = ist_monatsverfall


def _nearest_exp(by: dict, target_dte: int, prefer_monthly: bool = False):
    """Expiry am nächsten an target_dte.

    prefer_monthly: erst Monatsverfälle, dann Freitage, dann der Rest. Für den
    25Δ-Skew Pflicht — liquide Titel haben Mittwochs-Weeklies, die exakt auf
    30 Tage fallen können und dann gewinnen, obwohl fast niemand sie handelt.
    Deren IV ist dünn gestellt, und eine Zeitreihe, die mal Weeklies und mal
    Monatsverfälle enthält, vergleicht Ungleiches. Für die Term-Structure
    NICHT setzen — die will gerade das kurze Ende abbilden."""
    if not by:
        return None
    pool = by
    if prefer_monthly:
        pool = ([e for e in by if _is_monthly(e)]
                or [e for e in by if date.fromisoformat(e).weekday() == 4]
                or by)
    return min(pool, key=lambda e: abs(by[e]["dte"] - target_dte))


def _skew_at(by: dict, target_dte: int) -> dict | None:
    """25Δ-Skew (Put-IV − Call-IV) bei der Expiry nahe target_dte (Monatsverfall bevorzugt)."""
    ex = _nearest_exp(by, target_dte, prefer_monthly=True)
    if ex is None:
        return None
    e = by[ex]; cc = _pick(e["call"], 0.25, tol=_DELTA_TOL); pp = _pick(e["put"], 0.25, tol=_DELTA_TOL)
    if not cc or not pp:
        return None
    return {"exp": ex, "dte": e["dte"], "call_iv": cc[1], "call_strike": cc[2], "call_delta": round(cc[0], 3),
            "put_iv": pp[1], "put_strike": pp[2], "put_delta": round(pp[0], 3),
            "skew_pts": round((pp[1] - cc[1]) * 100, 2)}


def _atm_iv(e: dict, tol: float | None = _DELTA_TOL, detail: bool = False):
    """ATM-IV = Mittel der 50Δ-Call/Put-IV einer Expiry.

    tol: wie bei _pick. Ohne Toleranz liefert min() IMMER einen Treffer — in einer
    dünnen Kette also z.B. einen 0,35Δ-Kontrakt, der dann als „ATM" gilt. Weil die
    Smile-Krümmung die IV vom Geld weg anhebt, verzerrt das ATM, VRP, Expected Move
    UND beide Zeta systematisch nach oben, ohne dass die Zahl unplausibel aussieht.
    Der 25Δ-Pfad hatte diese Toleranz längst; ATM blieb versehentlich ungeschützt.

    detail=True liefert zusätzlich die tatsächlich erreichte Delta-Abweichung —
    ohne sie lässt sich im Nachhinein nicht prüfen, wie nah der Pick wirklich war."""
    cc = _pick(e["call"], 0.5, tol=tol); pp = _pick(e["put"], 0.5, tol=tol)
    if not (cc and pp):
        return (None, None) if detail else None
    iv = round((cc[1] + pp[1]) / 2, 4)
    if not detail:
        return iv
    dev = max(abs(abs(cc[0]) - 0.5), abs(abs(pp[0]) - 0.5))
    return iv, round(dev, 3)


# ── Konstante 30-Tage-Laufzeit (identisch zu backfill_skew_massive.py) ────────
# Damit der Live-Tageswert auf DERSELBEN Skala wie der Backfill landet. Ohne das
# schwankt die Reihe zwischen ~21 und ~39 Tagen (nächste Monatsexpiry), und der
# Percentile misst die Position im Verfallszyklus statt den Skew.


def _cm_leg(e: dict):
    """25Δ-Call/Put-IV + ATM-IV einer Expiry (für die CM-Interpolation)."""
    cc = _pick(e["call"], 0.25, tol=_DELTA_TOL); pp = _pick(e["put"], 0.25, tol=_DELTA_TOL)
    if not cc or not pp:
        return None
    return {"dte": e["dte"], "call_iv": cc[1], "put_iv": pp[1], "iv_atm": _atm_iv(e)}


# _cm_legs ist entfallen: die Stuetzstellen-Wahl steht jetzt als
# cm_leg_kandidaten in shared/black_scholes.py und wird von Live UND
# Backfill benutzt. Zwei Kopien derselben Auswahl sind in dieser Codebasis
# schon dreimal auseinandergelaufen.



# ── Ranking-Reihe: IV SELBST invertieren (Methodengleichheit mit dem Backfill) ─
# Die angezeigten Per-Ticker-Werte nutzen weiter die Provider-IV (genau, EOD).
# Fuer die HISTORIE zaehlt aber nicht Genauigkeit, sondern Vergleichbarkeit: die
# Reihe besteht zu >99 % aus BS-rekonstruierten Backfill-Punkten. Nimmt man fuer
# den Live-Punkt die Provider-IV, mischt man zwei Messmethoden — gemessen am
# 2026-09-09 ergab das einen Zeta-Versatz von 0,84-1,30 pts, bei NVDA so gross
# wie der gesamte Interquartilsabstand: der Live-Punkt landete im 99. Percentil,
# rein methodisch. Deshalb hier dieselbe Inversion, derselbe Volumenfilter.


# Frische-Filter fuer den Live-Pfad (Begruendung in _own_cands).
_NUR_SESSIONSKURSE = True


def _kurs_datum(day: dict) -> str | None:
    """Handelstag (US-Ostkueste), zu dem der Tagesbalken eines Kontrakts gehoert.

    `last_updated` ist ein Nanosekunden-Zeitstempel. In ET umrechnen, nicht in
    UTC: ein Balken, der um 16:15 ET (20:15 UTC) schliesst, gehoert zu DIESEM
    Tag — in UTC laege er bei Winterzeit-Schluss 21:15 ebenfalls am selben Tag,
    aber spaete Korrekturen nach Mitternacht UTC wuerden den Tag wechseln."""
    lu = day.get("last_updated")
    if not lu:
        return None
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.fromtimestamp(lu / 1e9, ZoneInfo("America/New_York")).date().isoformat()


def _own_cands(contracts: list, s30_ref: str | None = None,
               underlying: str | None = None) -> dict:
    """Snapshot-Kontrakte je Expiry als Rohpreise: {exp: {dte, cands:[…]}}.

    Bewusst OHNE Provider-IV/Greeks — nur Strike, Typ, Tagesschluss und Volumen.
    Deep-ITM/OTM-Kontrakte ohne Greeks fallen hier NICHT weg (anders als in
    _byexp), sie werden erst von der Bisektion verworfen, wenn kein Root existiert.

    s30_ref: Bezugsdatum fuer die Restlaufzeit. MUSS die Session sein, unter der
    die Zeile gestempelt wird — nicht date.today(). Ein Nachhol-Lauf nach einem
    ausgefallenen Cron (oder am Wochenende) hat sonst ein T, das bis zu drei Tage
    daneben liegt, und die daraus invertierte IV waere entsprechend verzerrt."""
    today = date.fromisoformat(s30_ref) if s30_ref else date.today()
    if underlying:
        # Angepasste Serien (Wurzel mit Ziffernsuffix, z. B. SPGI1 neben SPGI)
        # haben einen anderen Lieferumfang und passen nicht zum normalen Spot.
        contracts, weg = standardserie_filter(contracts, underlying)
        if weg:
            print(f"  {underlying}: {weg} angepasste Optionskontrakte verworfen", flush=True)
    # NUR KURSE AUS DER SESSION. `day` im Snapshot ist der Tagesbalken vom
    # LETZTEN HANDELSTAG DES KONTRAKTS — das kann Wochen her sein oder vor einem
    # Split liegen. Gegen den heutigen Spot invertiert ergibt ein solcher Kurs
    # Unsinn: BKNG (nach Split) hatte am 2026-09-24 einen Call K=168,2 fuer
    # 26,70 $ bei Spot 157,41 und 22 Tagen Restlaufzeit -> IV 200 %, und weil
    # es so viele waren, griff der Smile-Test nicht mehr (cm_skew −32,0 statt
    # +3,5). SEDG: −40,3 statt −1,4. Der Backfill hat das Problem NICHT — ein
    # historischer Tagesbalken existiert nur, wenn an DIESEM Tag gehandelt wurde.
    # Ohne den Filter rechneten Live und Backfill also verschieden.
    ref_tag = today.isoformat()
    by = {}
    veraltet = 0
    for c in contracts:
        det = c.get("details") or {}
        ex, typ, K = det.get("expiration_date"), det.get("contract_type"), det.get("strike_price")
        day = c.get("day") or {}
        if _NUR_SESSIONSKURSE and s30_ref and _kurs_datum(day) != ref_tag:
            veraltet += 1
            continue
        px, vol = day.get("close"), day.get("volume") or 0
        if not ex or typ not in ("call", "put") or not K or not px:
            continue
        e = by.setdefault(ex, {"dte": (date.fromisoformat(ex) - today).days, "cands": []})
        e["cands"].append({"typ": typ, "K": float(K), "px": float(px), "vol": float(vol)})
    if veraltet and underlying:
        print(f"  {underlying}: {veraltet} Kontraktkurse nicht aus der Session {ref_tag} verworfen",
              flush=True)
    return by


def _leg_own(e: dict, spot: float, vol_pctl: float = _CM_VOL_PCTL):
    """25Δ-Call/Put- + ATM-IV EINER Expiry aus Rohpreisen.

    Die Rechnung selbst steht in shared/black_scholes.leg_from_prices und ist
    damit BUCHSTAEBLICH dieselbe Funktion, die der Backfill aufruft — nicht mehr
    zwei Spiegel, die auseinanderlaufen koennen. `vol_pctl` bleibt als Parameter
    erhalten, steht aber auf 0: der Volumenfilter war das falsche Kriterium
    (Begruendung in shared/black_scholes.py bei VOL_PCTL).
    """
    cands = e.get("cands") or []
    if vol_pctl > 0 and cands:
        vols = sorted(c["vol"] for c in cands)
        cutoff = vols[min(len(vols) - 1, int(len(vols) * vol_pctl))]
        cands = [c for c in cands if not cutoff or c["vol"] >= cutoff]
    return leg_from_prices(cands, spot, e["dte"])


def _skew_cm(by: dict, leg_fn=None) -> dict | None:
    """Konstant-30-Tage 25Δ-Skew + ATM-IV — gleiche Methodik wie
    backfill_skew_massive.py, damit Live und Backfill eine Reihe bilden.

    leg_fn: Stuetzstellen-Quelle. Default = Provider-IV (_cm_leg); fuer die
    Ranking-Historie wird _leg_own uebergeben (eigene BS-Inversion).

    PROBIERT EINE RANGLISTE, statt bei der ersten gescheiterten Leg aufzugeben.
    Vorher wurde EIN Paar gewaehlt; scheiterte davon eine Stuetzstelle an
    leg_from_prices, blieb nur eine uebrig und der Tag wurde als `single`
    gestempelt — was im Frontend nicht fuer das Ranking zaehlt. Gemessen am
    2026-09-15/16: die duenne 65-Tage-Stuetzstelle fiel durch, und damit fiel
    die Normierungsquote von 77-100 % auf 38-56 %.
    Die Rangliste kommt aus shared/black_scholes.cm_leg_kandidaten; ein
    Fehlschlag kostet jetzt nur die naechste Gruppe, nicht den Tag.
    """
    if not by:
        return None
    leg_fn = leg_fn or (lambda e: _cm_leg(by[e]))
    gruppen = _cm_leg_kandidaten({e: by[e]["dte"] for e in by})
    if not gruppen:
        return None

    _cache: dict = {}
    def _leg(e):
        # Gruppen ueberlappen sich; leg_fn invertiert ~100 IVs je Expiry.
        if e not in _cache:
            _cache[e] = leg_fn(e)
        return _cache[e]

    # Runde 1: die erste Gruppe, die ZWEI brauchbare Stuetzstellen liefert.
    for g in gruppen:
        exps = g["exps"]
        if len(exps) != 2:
            continue
        a, b = _leg(exps[0]), _leg(exps[1])
        if not a or not b:
            _diag_zaehl("gruppe_leg_fehlt")
            continue
        lo_d, hi_d = min(a["dte"], b["dte"]), max(a["dte"], b["dte"])
        if not (lo_d <= _CM_DAYS <= hi_d) and min(abs(lo_d - _CM_DAYS),
                                                  abs(hi_d - _CM_DAYS)) > 15:
            _diag_zaehl("gruppe_zu_weit_von_30d")
            continue
        call_iv = _cm_interp(a["call_iv"], a["dte"], b["call_iv"], b["dte"])
        put_iv = _cm_interp(a["put_iv"], a["dte"], b["put_iv"], b["dte"])
        iv_atm = (_cm_interp(a["iv_atm"], a["dte"], b["iv_atm"], b["dte"])
                  if (a["iv_atm"] and b["iv_atm"]) else None)
        if call_iv is None or put_iv is None:
            _diag_zaehl("gruppe_interp_fehlgeschlagen")
            continue
        mode = "cm" if lo_d <= _CM_DAYS <= hi_d else "cm_extrap"
        return _cm_out(mode, _CM_DAYS, call_iv, put_iv, iv_atm, g, exps, by)

    # Runde 2: nur noch ein Einzelpunkt, und nur nahe genug an der Ziellaufzeit.
    for g in gruppen:
        for e in g["exps"]:
            a = _leg(e)
            if not a:
                continue
            if abs(a["dte"] - _CM_DAYS) > _CM_SINGLE_TOL:
                _diag_zaehl("einzel_ausserhalb_toleranz")
                continue
            if a["call_iv"] is None or a["put_iv"] is None:
                continue
            return _cm_out("single", a["dte"], a["call_iv"], a["put_iv"], a["iv_atm"],
                           g, [e], by)
    _diag_zaehl("cm_None_keine_gruppe_brauchbar")
    return None


def _diag_zaehl(grund: str) -> None:
    """Zaehlt nur, wenn die Diagnose laeuft (shared.black_scholes.diagnose_start)."""
    _bs_zaehl(grund)


def _cm_out(mode: str, dte: int, call_iv: float, put_iv: float,
            iv_atm: float | None, gruppe: dict | None = None,
            exps: list | None = None, by: dict | None = None) -> dict:
    """Ergebniszeile. Zeta-Felder nur MIT ATM-Anker — ohne den faellt das
    Frontend auf die Naeherung (call_iv-put_iv)/2 zurueck, die
    put_zeta = -call_zeta erzwingt und den Quadranten auf seine Antidiagonale
    kollabieren laesst."""
    out = {"cm_mode": mode, "cm_dte": dte,
           "cm_call_iv": round(call_iv, 4), "cm_put_iv": round(put_iv, 4),
           "cm_skew_pts": round((put_iv - call_iv) * 100, 2)}
    if iv_atm:
        out["cm_iv_atm"] = round(iv_atm, 4)
        out["cm_call_zeta_pts"] = round((call_iv - iv_atm) * 100, 2)
        out["cm_put_zeta_pts"] = round((put_iv - iv_atm) * 100, 2)
        out["cm_bfly_pts"] = round(((put_iv + call_iv) / 2 - iv_atm) * 100, 2)
    # HERKUNFT mitschreiben. Derselbe Ticker kann heute aus dem Monatsverfall und
    # morgen aus einem Wochenverfall kommen — im Ergebnis sieht das gleich aus.
    # Ohne diese Felder ist ein Percentile-Sprung spaeter nicht erklaerbar.
    if gruppe:
        out["cm_pool"] = gruppe.get("pool")
        out["cm_art"] = gruppe.get("art")
        out["cm_rang"] = gruppe.get("rang")
    if exps:
        out["cm_exps"] = list(exps)
        if by:
            out["cm_exp_dte"] = [by[e]["dte"] for e in exps if e in by]
    return out

def _enrich(sym: str, key: str) -> dict | None:
    """Voll-Metrik-Objekt aus EINEM Massive-Chain-Snapshot."""
    spot = _spot(sym, key)
    try:
        contracts = _chain(sym, key, spot)
    except Exception as e:
        print(f"  [massive] {sym}: {str(e)[:80]}")
        return None
    by = _byexp(contracts)
    s30 = _skew_at(by, 30)
    # Der Anbieter-Pick ist seit 2026-09-25 nur noch Diagnose (front_provider).
    # Frueher beendete ein fehlender Pick den GANZEN Ticker, bevor die eigene
    # Rechnung ueberhaupt lief (Codex-Entwurfspruefung) — TAN, DUK, NXE, ARRY
    # fielen so jeden Tag aus. Jetzt entscheidet die eigene Rechnung.
    if not s30:
        print(f"  [massive] {sym}: kein Anbieter-25Δ@30 (n={len(contracts)}) — nur eigene Rechnung",
              flush=True)
    # Put/Call-Volumen + OI (für markt­weite Equity-P/C-Ratio; near-the-money aus ±30%-Chain)
    pv = cv = poi = coi = 0
    for c in contracts:
        typ = (c.get("details") or {}).get("contract_type")
        vol = (c.get("day") or {}).get("volume") or 0
        oi = c.get("open_interest") or 0
        if typ == "put":
            pv += vol; poi += oi
        elif typ == "call":
            cv += vol; coi += oi
    # Kursreihe auf die Session kappen: Spot UND realisierte Vola muessen aus
    # demselben Zeitraum stammen wie die Optionspreise.
    rv1m, last_close, close_datum = _realized_vol(sym, 21, bis=_last_session())
    if not spot:                                    # Fallback 1: Underlying aus dem Snapshot
        for c in contracts:
            p = (c.get("underlying_asset") or {}).get("price")
            if p:
                spot = round(float(p), 2); break
    if not spot:                                    # Fallback 2: letzter Close aus eigener Kursreihe
        spot = last_close
        if spot:
            print(f"  [spot] {sym}: Massive ohne Underlying → letzter Close {spot}", flush=True)
    r = {"ticker": sym, "cats": categories_for(sym), "underlying": spot,
         "put_vol": pv, "call_vol": cv, "put_oi": poi, "call_oi": coi, "rv_1m": rv1m}
    anbieter = _anbieter_werte(by, s30, rv1m, spot)
    r.update(anbieter)
    # EINMAL vollstaendig sichern, bevor irgendetwas ueberschrieben wird.
    # _anzeige_aus_ranking und _laufzeiten_eigen ergaenzen nur noch.
    r["front_provider"] = dict(anbieter)
    # Spot fuer die Inversion: der Schluss aus UNSERER Kursreihe — dieselbe Quelle,
    # die auch der Backfill nutzt (_closes). Ohne ihn wird NICHT normiert: Massives
    # /prev liefert je nach Laufzeitpunkt den Vortag, und ein damit falsch
    # skalierter Punkt bekaeme trotzdem ein cm_mode und landete in der Rangfolge.
    # Lieber kein Punkt als ein falsch skalierter.
    # SPOT UND OPTIONSPREISE MUESSEN AUS DERSELBEN SESSION KOMMEN.
    # Der Kommentar darueber versprach das ("lieber kein Punkt als ein falsch
    # skalierter"), geprueft wurde aber nur, DASS es einen Schluss gibt — nicht,
    # von WANN. Ist die Kursreihe eine Session alt, verschiebt der falsche Spot
    # den Forward und damit sowohl den Moneyness-Anker als auch die 25Δ-Auswahl
    # beider Fluegel. Ein einziger falscher Spot erzeugt so ALLE Symptome:
    # gekipptes Skew-Vorzeichen, iv_atm ueber beiden Fluegeln, gescheiterte Legs.
    # Gemessen am 2026-09-18 an vier Blue Chips; mit dem korrekten Schluss waren
    # dieselben Ticker sauber.
    _sess = _last_session()
    # FAIL-CLOSED: ein unbekanntes Datum ist kein gueltiges Datum. Ohne diese
    # Klammer wuerde ein fehlendes close_datum die Pruefung durchfallen lassen
    # und mit einem Spot unbekannter Herkunft normieren.
    if last_close and close_datum != _sess:
        print(f"  {sym:6} Kursreihe endet {close_datum}, Session ist {_sess} "
              f"-> KEINE cm-Normierung (Spot passt nicht zu den Optionspreisen)",
              flush=True)
        last_close = None
    by_own = None
    if last_close:
        # Restlaufzeit gegen die SESSION rechnen, unter der die Zeile gestempelt
        # wird — sonst liegt T bei einem Nachhol-Lauf um bis zu drei Tage daneben.
        by_own = _own_cands(contracts, s30_ref=_sess, underlying=sym)
        cm = _skew_cm(by_own, leg_fn=lambda e: _leg_own(by_own[e], last_close))
        # cm-Zeilen ohne iv_atm haetten kein Zeta — das Frontend wuerde auf die
        # (call_iv-put_iv)/2-Naeherung zurueckfallen, die put_zeta = -call_zeta
        # erzwingt und den Quadranten auf seine Antidiagonale kollabieren laesst.
        # Solche Tage gehoeren nicht in die Rangfolge.
        if cm and cm.get("cm_iv_atm"):
            r.update(cm)
    if not s30 and not r.get("cm_mode"):
        # Weder Anbieter noch eigene Rechnung: kein brauchbarer Wert — wie bisher
        # als Ausfall melden statt eine leere Zeile zu schreiben.
        print(f"  [massive] {sym}: weder Anbieter- noch eigene 30-Tage-Messung", flush=True)
        return None
    _anzeige_aus_ranking(r)
    _laufzeiten_eigen(r, by_own, last_close)
    return r


def _anbieter_werte(by: dict, s30: dict | None, rv1m, spot) -> dict:
    """Die bisherige Rechnung ueber den Anbieter-Picker — nur noch Diagnose.

    Woertlich aus _enrich uebernommen (2026-09-25), damit `front_provider` exakt
    die Werte enthaelt, die bis dahin angezeigt wurden. Kein angezeigtes oder
    gespeichertes Feld stammt mehr hieraus, ausser als History-Fallback an
    Tagen ohne jede 30-Tage-Normierung. `s30` darf fehlen."""
    out: dict = {}
    s90 = _skew_at(by, 90)
    term, seen = [], set()
    for tgt in _TERM_TARGETS:
        ex = _nearest_exp(by, tgt)
        if ex is None or ex in seen:
            continue
        atm = _atm_iv(by[ex])
        if atm:
            term.append({"dte": by[ex]["dte"], "iv": atm}); seen.add(ex)
    term.sort(key=lambda t: t["dte"])
    if s30:
        iv_atm, atm_dev = _atm_iv(by[s30["exp"]], detail=True)
        put_iv, call_iv = s30["put_iv"], s30["call_iv"]
        out.update({
            "dte": s30["dte"],
            "call_25d": {"strike": s30["call_strike"], "iv": call_iv, "delta": s30["call_delta"]},
            "put_25d": {"strike": s30["put_strike"], "iv": put_iv, "delta": s30["put_delta"]},
            "skew_25d": round(put_iv - call_iv, 4), "skew_pts": s30["skew_pts"],
            "call_zeta_pts": round((call_iv - iv_atm) * 100, 2) if iv_atm else None,
            "put_zeta_pts":  round((put_iv  - iv_atm) * 100, 2) if iv_atm else None,
            "iv_atm": iv_atm, "atm_delta_dev": atm_dev,
            "vrp_pts": round((iv_atm - rv1m) * 100, 2) if (iv_atm and rv1m) else None,
            "bfly_pts": round(((put_iv + call_iv) / 2 - iv_atm) * 100, 2) if iv_atm else None,
            "pc_ratio": round(put_iv / call_iv, 3) if call_iv else None,
            "skew_back_pts": s90["skew_pts"] if s90 else None,
            "skew_term_pts": round(s90["skew_pts"] - s30["skew_pts"], 2) if s90 else None,
        })
    else:
        iv_atm = None
        for k in ("dte", "call_25d", "put_25d", "skew_25d", "skew_pts", "call_zeta_pts",
                  "put_zeta_pts", "iv_atm", "atm_delta_dev", "vrp_pts", "bfly_pts",
                  "pc_ratio", "skew_term_pts"):
            out[k] = None
        out["skew_back_pts"] = s90["skew_pts"] if s90 else None
    out["term"] = term
    if term and iv_atm:
        out["contango"] = bool(term[0]["iv"] < iv_atm)
        out["term_slope_pts"] = round((term[-1]["iv"] - term[0]["iv"]) * 100, 2)
    else:
        out["contango"] = None; out["term_slope_pts"] = None
    emd = s30["dte"] if s30 else None
    if iv_atm and emd:
        out["em_pct"] = round(iv_atm * math.sqrt(emd / 365.0) * 100, 2)
        out["em_abs"] = round(spot * iv_atm * math.sqrt(emd / 365.0), 2) if spot else None
        out["em_dte"] = emd
    else:
        out["em_pct"] = out["em_abs"] = out["em_dte"] = None
    sne = _skew_at(by, 1)
    out["skew_ne_pts"] = sne["skew_pts"] if sne else None
    out["skew_ne_dte"] = sne["dte"] if sne else None
    def _curve(ex_target):
        ex = _nearest_exp(by, ex_target)
        if ex is None:
            return None
        e = by[ex]; kurve = []
        for dl in (0.10, 0.25, 0.40):
            pk = _pick(e["put"], dl); kurve.append(pk[1] if pk else None)
        kurve.append(_atm_iv(e))
        for dl in (0.40, 0.25, 0.10):
            c = _pick(e["call"], dl); kurve.append(c[1] if c else None)
        return kurve
    out["skew_curve"] = {
        "labels": ["10ΔP", "25ΔP", "40ΔP", "ATM", "40ΔC", "25ΔC", "10ΔC"],
        "iv30": _curve(30), "iv_ne": _curve(1),
        "dte30": s30["dte"] if s30 else None, "dte_ne": (sne["dte"] if sne else None),
    }
    return out


# Felder, die bisher den Front-Monat mit Anbieter-IV zeigten und jetzt die
# 30-Tage-Werte des Radars tragen.
_ANZEIGE_FELDER = ("dte", "call_25d", "put_25d", "skew_25d", "skew_pts",
                   "call_zeta_pts", "put_zeta_pts", "iv_atm", "atm_delta_dev",
                   "vrp_pts", "bfly_pts", "pc_ratio", "em_pct", "em_abs", "em_dte")


def _anzeige_aus_ranking(r: dict) -> None:
    """Tabelle, /flows-Panel und Morning Briefing zeigen dieselben Zahlen wie der Radar.

    WARUM (Befund 2026-09-25, Entscheidung Variante a): der Anzeigepfad pickte
    den 25Δ-Kontrakt ueber das DELTA DES ANBIETERS, und der rechnet es aus der IV
    desselben Kontrakts. Ein falsch bepreister Kontrakt (nie gehandelt, zum
    Mindestkurs, veraltet) bekam dadurch eine zu hohe IV UND ein zu grosses Delta
    und rutschte genau in das 25Δ-Fenster. Gemessen: bei 33 von 158 Tickern wich
    der angezeigte Skew um > 8 pts vom gerankten ab — RSP +24,1 statt +3,8 (Put
    K=199 nie gehandelt, Delta −0,229, waehrend K=200 nur −0,134 hatte), SO −61
    statt +1,2 (Call zu 0,10 $ bei 15 % aus dem Geld, Delta 0,253). Der
    Ranking-Pfad hat diesen Fehler seit v61 nicht mehr (ATM-Referenz, dann alle
    Deltas aus dieser EINEN IV; Paritaets- und Smile-Pruefung).

    Deshalb EINE Rechnung: die angezeigten 25Δ/ATM-Felder kommen aus der
    30-Tage-Normierung. Ist der Tag nicht rankbar, bleiben sie LEER — lieber
    keine Zahl als die alte, nachweislich unzuverlaessige. Die Anbieterwerte
    bleiben unter `front_provider` erhalten (Diagnose, History-Fallback).
    NICHT umgestellt, weil ohne 30-Tage-Gegenstueck: NE-Skew, Skew-Term,
    Term-Struktur, Smile-Kurve — die rechnen weiter mit dem Anbieter-Picker.
    """
    # Nur ERGAENZEN: _enrich sichert die Anbieterwerte schon vollstaendig
    # (inkl. NE/Term/Smile). Ein Ueberschreiben haette diese Sicherung
    # geloescht (Codex-Entwurfspruefung 2026-09-25).
    fp = r.setdefault("front_provider", {})
    for k in _ANZEIGE_FELDER:
        fp.setdefault(k, r.get(k))
    if not _rankbar(r):
        for k in _ANZEIGE_FELDER:
            r[k] = None
        return
    call_iv, put_iv, iv_atm = r["cm_call_iv"], r["cm_put_iv"], r.get("cm_iv_atm")
    dte = r.get("cm_dte") or _CM_DAYS
    rv = r.get("rv_1m")
    spot = r.get("underlying")
    r.update({
        "dte": dte,
        "call_25d": {"strike": None, "iv": round(call_iv, 4), "delta": 0.25},
        "put_25d": {"strike": None, "iv": round(put_iv, 4), "delta": -0.25},
        "skew_25d": round(put_iv - call_iv, 4),
        "skew_pts": r.get("cm_skew_pts"),
        "call_zeta_pts": r.get("cm_call_zeta_pts"),
        "put_zeta_pts": r.get("cm_put_zeta_pts"),
        "iv_atm": iv_atm,
        "atm_delta_dev": None,          # 30-Tage-Wert ist interpoliert, kein einzelner Pick
        "vrp_pts": round((iv_atm - rv) * 100, 2) if (iv_atm and rv) else None,
        "bfly_pts": r.get("cm_bfly_pts"),
        "pc_ratio": round(put_iv / call_iv, 3) if call_iv else None,
        "em_pct": round(iv_atm * math.sqrt(dte / 365.0) * 100, 2) if iv_atm else None,
        "em_abs": round(spot * iv_atm * math.sqrt(dte / 365.0), 2) if (iv_atm and spot) else None,
        "em_dte": dte if iv_atm else None,
    })


# 90-Tage-Konstante fuer Skew-Term: Stuetzstellen-Fenster und Ziel.
_BACK_DAYS = 90
_BACK_MIN, _BACK_MAX = 45, 150
_NE_MAX_DTE = 10          # NE-Ersatz nur bis zu diesem Verfall
_KONTANGO_KURZ_MAX = 14   # Contango: kurzer Punkt hoechstens so lang
_SMILE_LABELS = ["10ΔP", "25ΔP", "40ΔP", "ATM", "40ΔC", "25ΔC", "10ΔC"]


def _laufzeiten_eigen(r: dict, by_own: dict | None, spot_ref) -> None:
    """NE-Skew, 90-Tage-Skew/Skew-Term, Term-Struktur und Smile-Kurve aus der
    EIGENEN Rechnung (Session-Kurse, Referenz-Delta, Paritaets-/Smile-Filter).

    WARUM (Messung 2026-09-24, 40 Ticker, Anbieter-Picker gegen eigene Leg):
    NE-Skew nahm IMMER den Monatsverfall mit 22 Tagen (`_skew_at(by, 1)`
    bevorzugt Monate — der naechste Monatsverfall zu "1 Tag" ist der
    Front-Monat), 14 von 38 mit umgekehrtem Vorzeichen; 90-Tage-Skew 7 von 31
    mit Vorzeichenwechsel; Term-ATM am kurzen Ende systematisch zu hoch
    (XLF 7 Tage: 20,3 % statt 14,5 %).

    Festlegungen aus der Codex-Entwurfspruefung:
    - NE = strikt der naechste Verfall mit dte >= 1 (SpotGamma-Definition,
      0DTE ausgeschlossen: T -> 0). Scheitert er, bleibt NE leer — keine
      stille Ersatzsuche.
    - Skew-Term = 90-CM minus 30-CM. Die 90 Tage werden wie die 30 Tage
      interpoliert (Call und Put getrennt, linear in totaler Varianz), nur mit
      echter Klammer, ohne Extrapolation. Vorzeichen 90 minus 30.
    - Term: je Ziel der naechste Verfall OHNE Monatsvorzug, ATM ohne
      Fluegelzwang (atm_from_prices, mit strenger Klammerpruefung).
      Contango nur mit einem Punkt UNTER 30 Tagen, Gleichstand = unbestimmt.
      Steigung nur mit >= 2 Laufzeiten, mit tatsaechlichen Endpunkten.
    - Smile 30 Tage: 25d- und ATM-Punkte = die angezeigten Werte, 10d/40d je
      Punkt zwischen denselben cm_exps interpoliert. Nur fuer cm/cm_extrap;
      `modus30` weist aus, welches von beiden.
    Ohne gueltigen Session-Schluss (`spot_ref`) bleiben ALLE Felder leer — kein
    Rueckfall auf den Anbieter und kein anderer Spot.
    """
    r.update({"skew_ne_pts": None, "skew_ne_dte": None, "skew_ne_ersatz": None,
              "skew_back_pts": None, "skew_back_dte": None, "skew_term_pts": None,
              "term": [], "contango": None, "term_slope_pts": None,
              "term_slope_von": None, "term_slope_bis": None,
              "skew_curve": {"labels": list(_SMILE_LABELS), "iv30": None, "iv_ne": None,
                             "dte30": None, "modus30": None, "dte_ne": None}})
    if not by_own or not spot_ref:
        return

    punkte_cache: dict = {}
    def _punkte(ex):
        if ex not in punkte_cache:
            e = by_own[ex]
            punkte_cache[ex] = _gefilterte_punkte(e.get("cands") or [], spot_ref, e["dte"])
        return punkte_cache[ex]

    leg_cache: dict = {}
    def _leg(ex):
        if ex not in leg_cache:
            leg_cache[ex] = _leg_own(by_own[ex], spot_ref)
        return leg_cache[ex]

    def _smile(ex):
        g = _punkte(ex)
        if g is None:
            return None
        return smile_from_prices(None, spot_ref, by_own[ex]["dte"], _punkte=g)

    laufend = sorted((e for e in by_own if by_own[e]["dte"] >= 1), key=lambda e: by_own[e]["dte"])
    if not laufend:
        return

    # ── NE-Skew: naechster Verfall, sonst naechster AUSWERTBARER (gekennzeichnet)
    # Gemessen am 2026-09-24: bei 13 von 40 Tickern scheiterte der 1-Tages-
    # Verfall an der Delta-Toleranz — kurz vor Verfall ist die Delta-Kurve so
    # steil, dass zwischen zwei Strikes kein Kontrakt nahe 25d liegt. Die Kurse
    # waren frisch; das ist Strike-Struktur, keine Datenqualitaet. Codex
    # (Entwurfspruefung): strikt = leer, Ersatz zulaessig, wenn Laufzeit und
    # Ersatz sichtbar sind. Grenze 10 Tage, damit "NE" nah bleibt.
    def _skew_von(leg):
        if leg and leg.get("put_iv") is not None and leg.get("call_iv") is not None:
            return round((leg["put_iv"] - leg["call_iv"]) * 100, 2)
        return None
    ne, leg_ne = laufend[0], _leg(laufend[0])
    r["skew_ne_ersatz"] = False
    if _skew_von(leg_ne) is None:
        for e in laufend[1:]:
            if by_own[e]["dte"] > _NE_MAX_DTE:
                break
            if _skew_von(_leg(e)) is not None:
                ne, leg_ne = e, _leg(e)
                r["skew_ne_ersatz"] = True
                break
    r["skew_ne_dte"] = by_own[ne]["dte"]
    r["skew_ne_pts"] = _skew_von(leg_ne)

    # ── 90-Tage-Konstante und Skew-Term ──────────────────────────────────────
    def _bevorzugt(e):
        # Monate vor Freitagen vor Rest — wie _nearest_exp(prefer_monthly=True)
        return 0 if _is_monthly(e) else (1 if date.fromisoformat(e).weekday() == 4 else 2)
    fenster = [e for e in laufend if _BACK_MIN <= by_own[e]["dte"] <= _BACK_MAX]
    unten = oben = None
    for rang in (0, 1, 2):
        pool = [e for e in fenster if _bevorzugt(e) <= rang]
        kand_u = sorted((e for e in pool if by_own[e]["dte"] <= _BACK_DAYS),
                        key=lambda e: -by_own[e]["dte"])
        kand_o = sorted((e for e in pool if by_own[e]["dte"] > _BACK_DAYS),
                        key=lambda e: by_own[e]["dte"])
        unten = next((e for e in kand_u if _leg(e)), None)
        oben = next((e for e in kand_o if _leg(e)), None)
        if unten and oben:
            break
    if unten and oben:
        lu, lo = _leg(unten), _leg(oben)
        c90 = _cm_interp(lu["call_iv"], lu["dte"], lo["call_iv"], lo["dte"], t_target=_BACK_DAYS)
        p90 = _cm_interp(lu["put_iv"], lu["dte"], lo["put_iv"], lo["dte"], t_target=_BACK_DAYS)
        if c90 is not None and p90 is not None:
            r["skew_back_pts"] = round((p90 - c90) * 100, 2)
            r["skew_back_dte"] = _BACK_DAYS
            if _rankbar(r) and r.get("skew_pts") is not None:
                r["skew_term_pts"] = round(r["skew_back_pts"] - r["skew_pts"], 2)

    # ── Term-Struktur ─────────────────────────────────────────────────────────
    term, gesehen = [], set()
    for ziel in _TERM_TARGETS:
        ex = min(laufend, key=lambda e: abs(by_own[e]["dte"] - ziel))
        if ex in gesehen:
            continue
        gesehen.add(ex)
        g = _punkte(ex)
        atm = atm_from_prices(None, spot_ref, by_own[ex]["dte"], _punkte=g) if g else None
        if atm:
            term.append({"dte": by_own[ex]["dte"], "iv": atm})
    term.sort(key=lambda t: t["dte"])
    r["term"] = term
    iv30 = r.get("iv_atm") if _rankbar(r) else None
    # "Kurz" heisst hier: hoechstens _KONTANGO_KURZ_MAX Tage. Mit "< 30" haette
    # XLF am 2026-09-24 (7-Tage-Punkt wegen zu weitem Anker verworfen) den
    # 29-Tage-Punkt gegen den 30-Tage-Wert verglichen — formal kuerzer,
    # fachlich derselbe Punkt.
    kurz = [t for t in term if t["dte"] <= _KONTANGO_KURZ_MAX]
    if kurz and iv30:
        if kurz[0]["iv"] < iv30:
            r["contango"] = True
        elif kurz[0]["iv"] > iv30:
            r["contango"] = False
    if len({t["dte"] for t in term}) >= 2:
        r["term_slope_pts"] = round((term[-1]["iv"] - term[0]["iv"]) * 100, 2)
        r["term_slope_von"], r["term_slope_bis"] = term[0]["dte"], term[-1]["dte"]

    # ── Smile-Kurven ──────────────────────────────────────────────────────────
    def _kurve(sm, ersetze=None):
        if not sm:
            return None
        pts = [sm["put"].get(0.10), sm["put"].get(0.25), sm["put"].get(0.40), sm["iv_atm"],
               sm["call"].get(0.40), sm["call"].get(0.25), sm["call"].get(0.10)]
        for i, v in (ersetze or {}).items():
            if v is not None:
                pts[i] = v
        return pts if any(v is not None for v in pts) else None

    sc = r["skew_curve"]
    # NE: 25d-Punkte und ATM aus derselben Leg wie skew_ne_pts, damit Kurve
    # und Tabellenwert zusammenpassen.
    ersatz_ne = ({1: leg_ne.get("put_iv"), 3: leg_ne.get("iv_atm"), 5: leg_ne.get("call_iv")}
                 if leg_ne else None)
    sc["iv_ne"] = _kurve(_smile(ne), ersatz_ne)
    sc["dte_ne"] = by_own[ne]["dte"] if sc["iv_ne"] else None

    # 30 Tage: nur fuer rankbare Tage, auf denselben Stuetzstellen wie die Anzeige.
    exps = r.get("cm_exps") or []
    if _rankbar(r) and len(exps) == 2 and all(e in by_own for e in exps):
        s1, s2 = _smile(exps[0]), _smile(exps[1])
        t1, t2 = by_own[exps[0]]["dte"], by_own[exps[1]]["dte"]
        def _ip(seite, dl):
            if not s1 or not s2:
                return None
            return _cm_interp(s1[seite].get(dl), t1, s2[seite].get(dl), t2)
        sc["iv30"] = [_ip("put", 0.10), r.get("cm_put_iv"), _ip("put", 0.40), r.get("cm_iv_atm"),
                      _ip("call", 0.40), r.get("cm_call_iv"), _ip("call", 0.10)]
        sc["dte30"] = _CM_DAYS
        sc["modus30"] = r.get("cm_mode")


class SchluesselFehlt(RuntimeError):
    """Ein Schreiblauf ohne MASSIVE_API_KEY.

    Frueher lief der Cron dann weiter und schrieb eine Datei OHNE Ticker —
    mit Exit 0. Beim Skew-Cron hiesse das: leerer Radar, gruener Job. Egal ob
    der Schluessel durch eine kaputte .env, einen falschen Container-Start
    oder den Pruefschalter SA_OHNE_DOTENV fehlt — ein Fehlschlag muss sich
    als Fehlschlag melden (Codex-Review 2026-09-25, R6)."""


def build(tickers: list[str], write: bool = True) -> dict:
    if write:
        # EOD-Job: waehrend der US-Handelszeit waere der Snapshot intraday,
        # gestempelt wuerde die Vorsession (Codex-Review 2026-09-25, R2).
        pruefe_eod_fenster("compute_options_skew")
    tok = os.environ.get("MASSIVE_API_KEY") or os.environ.get("POLYGON_API_KEY", "")
    if write and not tok:
        raise SchluesselFehlt("compute_options_skew: MASSIVE_API_KEY fehlt — ohne ihn entstuende eine "
                              "Ausgabe ohne Ticker. Nichts geschrieben.")
    skew_s = _index_series("^SKEW"); vix_s = _index_series("^VIX"); vvix_s = _index_series("^VVIX")
    indices = {}
    for name, s in [("SKEW", skew_s), ("VIX", vix_s), ("VVIX", vvix_s)]:
        if s:
            indices[name] = {"last": s["last"], "date": s["date"]}
            print(f"  idx {name:5} {s['last']} ({s['date']})")
    # CBOE Implied-Correlation-Indizes (gratis via Yahoo; oft nur letzter Wert) → KPI + Forward-History
    corr = {}
    for name, sym in [("COR1M", "^COR1M"), ("COR3M", "^COR3M"), ("COR30D", "^COR30D")]:
        s = _index_series(sym, days=504)
        if s and s.get("last") is not None:
            corr[name] = {"last": s["last"], "date": s["date"]}
            print(f"  cor {name:6} {s['last']} ({s['date']})")
    series = []
    if skew_s:
        vixmap = dict(zip(vix_s.get("dates", []), vix_s.get("vals", [])))
        for dt_, sk in zip(skew_s["dates"], skew_s["vals"]):
            series.append({"date": dt_, "skew": sk, "vix": vixmap.get(dt_)})

    per = []
    # Ausfaelle als ERGEBNIS festhalten, nicht nur als fehlende Zeile. Ohne das
    # verschwindet ein Ticker still aus options_skew.json: der Lauf meldet Erfolg,
    # der Health-Check prueft nur eine globale Mindestzahl, und dass ein bestimmter
    # Titel seit Wochen nie im Radar auftaucht, faellt niemandem auf.
    failed: list[dict] = []
    partial: list[dict] = []   # Zeile vorhanden, aber ATM-abhaengige Felder fehlen
    diag: dict = {}
    if not tok:
        print("  [massive] MASSIVE_API_KEY fehlt — überspringe Per-Ticker-Metriken.")
    else:
        # Verwerfungsgruende mitzaehlen. Die Zaehler in shared/black_scholes.py
        # waren bis hierher toter Code — ohne diesen Aufruf bleibt `_diag` None
        # und jedes `_zaehl` ist wirkungslos. Genau deshalb wurde am
        # 2026-09-15..18 zwei Tage lang OPEX verdaechtigt, waehrend die Ursache
        # ein veralteter Spot war: man sah nur das Ergebnis, nie den Grund.
        _diagnose_start()
        for t in tickers:
            try:
                r = _enrich(t, tok)
            except Exception as e:
                failed.append({"ticker": t, "reason": f"{type(e).__name__}: {str(e)[:80]}"})
                print(f"  {t:6} FEHLER {type(e).__name__}: {str(e)[:80]}", flush=True)
                continue
            if r:
                per.append(r)
                ct = "contango" if r.get("contango") else ("backwardation" if r.get("contango") is False else "?")
                # `or 0` machte aus einem fehlenden ATM ein "0.0%" — das liest sich wie
                # ein echter Messwert. Fehlend muss als fehlend erkennbar sein.
                _atm = f"{r['iv_atm']*100:.1f}%" if r.get("iv_atm") else "—"
                _sk = f"{r['skew_pts']:+.2f}" if r.get("skew_pts") is not None else "—"
                print(f"  {t:6} skew {_sk} · ATM {_atm} · "
                      f"VRP {r.get('vrp_pts')} · bfly {r.get('bfly_pts')} · P/C {r.get('pc_ratio')} · term {ct}", flush=True)
                if not r.get("iv_atm"):
                    # Teil-Ausfall: Zeile existiert, aber Zeta/Butterfly/VRP fehlen,
                    # weil der 50Δ-Pick ausserhalb der Toleranz lag.
                    # Seit die Anzeige aus der 30-Tage-Normierung kommt, heisst ein
                    # fehlendes iv_atm: dieser Tag ist nicht rankbar.
                    partial.append({"ticker": t, "reason": "keine 30-Tage-Normierung "
                                    f"(cm_mode={r.get('cm_mode')}) — Anzeige leer"})
            else:
                failed.append({"ticker": t, "reason": "kein 25Δ/ATM-Pick in Toleranz"})
        diag = _diagnose_stop()
        if diag:
            ges = sum(diag.values())
            print(f"  [diagnose] {ges} Verwerfungen ueber {len(tickers)} Ticker:", flush=True)
            for grund, n in sorted(diag.items(), key=lambda x: -x[1]):
                print(f"    {n:6}  {grund}", flush=True)

    # Marktweite Put/Call-Ratio (Equity = ohne Broad-Index-ETFs, Index = Broad-Index) — volumen- + OI-basiert
    def _pc(sel):
        pv = sum(t["put_vol"] for t in per if sel(t)); cv = sum(t["call_vol"] for t in per if sel(t))
        poi = sum(t["put_oi"] for t in per if sel(t)); coi = sum(t["call_oi"] for t in per if sel(t))
        return {"vol": round(pv / cv, 3) if cv else None, "oi": round(poi / coi, 3) if coi else None}
    _is_idx = lambda t: "Broad-Index" in (t.get("cats") or [])
    pc_ratio = {"equity": _pc(lambda t: not _is_idx(t)), "index": _pc(_is_idx), "date": date.today().isoformat()}
    if per:
        print(f"  P/C equity vol {pc_ratio['equity']['vol']} oi {pc_ratio['equity']['oi']} · index vol {pc_ratio['index']['vol']}", flush=True)

    out = {
        "generated": date.today().isoformat(),      # Laufzeitpunkt (Freshness-Checks)
        "session": _last_session(),                  # Handelstag, zu dem die Daten gehören
        "source": "CBOE ^SKEW/^VIX/^VVIX/^COR (Yahoo) + US-Option-Chain-Snapshot (25Δ-Skew, ATM-Term-Structure, VRP, Equity-P/C)",
        "indices": indices, "correlation": corr, "pc_ratio": pc_ratio, "series": series,
        "categories": list(OPTIONS_CATEGORIES.keys()), "tickers": per,
        # Abdeckung explizit ausweisen — sonst laesst sich aus der Datei nicht
        # ablesen, ob 163 Ticker angefragt und 12 still gescheitert sind.
        "coverage": {"requested": len(tickers), "returned": len(per),
                     "failed": failed, "partial": partial},
    }
    if write:
        p = _ROOT / "landing/data/options_skew.json"
        write_json_atomic(p, out)
        print(f"\n[OK] {len(per)}/{len(tickers)} Ticker + {len(indices)} Indizes → {p}")
        if failed:
            from collections import Counter
            _c = Counter(f["reason"].split(":")[0] for f in failed)
            print(f"[coverage] {len(failed)} ohne Wert: "
                  + " · ".join(f"{k} ({n})" for k, n in _c.most_common()), flush=True)
            print("           " + ", ".join(f["ticker"] for f in failed[:20])
                  + (" …" if len(failed) > 20 else ""), flush=True)
        if partial:
            print(f"[coverage] {len(partial)} nur teilweise (kein ATM → Zeta/Bfly/VRP fehlen): "
                  + ", ".join(f["ticker"] for f in partial[:20])
                  + (" …" if len(partial) > 20 else ""), flush=True)
        # Skalare Metriken vorwärts in History akkumulieren
        hp = _ROOT / "landing/data/options_skew_history.json"
        hist = {}
        if hp.exists():
            try: hist = json.loads(hp.read_text(encoding="utf-8"))
            except Exception: hist = {}
        # Handelstag stempeln, NICHT den Laufzeitpunkt: der Cron läuft täglich um
        # 23:00 UTC, auch samstags/sonntags/feiertags — dann gehört die Chain zur
        # letzten Session. Der Dedup unten sorgt dafür, dass die Wiederholungen
        # am Wochenende keine Doppeleinträge erzeugen.
        today = out["session"]
        mv, dp = _fix_session_dates(hist)
        if mv or dp:
            print(f"[history] {mv} Einträge auf ihre Session umdatiert, {dp} Duplikate entfernt")
        for t in per:
            arr = hist.setdefault(t["ticker"], [])
            # „Erste Zeile gewinnt" war zu streng: eine bereits vorhandene,
            # NICHT normierte Zeile sperrte die Session dauerhaft fuer den
            # normierten Punkt. Genau das machte den Vorfall 2026-09-25
            # unheilbar — die falsch gestempelten Provider-Zeilen haetten auch
            # den echten Lauf der Folgenacht blockiert, der Radar waere leer
            # geblieben, ohne dass irgendetwas fehlschlaegt.
            # Deshalb: rankbar ersetzt nicht-rankbar, sonst bleibt es beim
            # Bestand (kein Ueberschreiben gleichwertiger Zeilen). "Rankbar"
            # heisst cm/cm_extrap — NICHT "cm_mode ist gesetzt" (noatm/single).
            vorhanden = next((e for e in arr if e.get("date") == today), None)
            neu_norm = _rankbar(t)
            alt_norm = _rankbar(vorhanden)
            if vorhanden is not None and neu_norm and not alt_norm:
                arr.remove(vorhanden)
                print(f"  {t['ticker']:6} nicht normierte Zeile fuer {today} durch "
                      f"normierte ersetzt", flush=True)
                vorhanden = None
            if vorhanden is None:
                # Skew/IV auf konstante 30 Tage normiert speichern (gleiche Skala wie
                # der Backfill) → percentile-fähige Reihe. Felder tragen cm_mode; das
                # Frontend verwirft 'single'. Fällt die CM-Normierung aus (nur ein
                # Verfall zu weit weg), wird der reale Front-Monat gespeichert (kein
                # cm_mode) — für den Tag nicht normiert, aber kein Datenverlust.
                cm_ok = t.get("cm_mode") is not None
                # Nicht normierte Tage: wie bisher die Anbieterwerte des Front-Monats
                # (nicht rankbar, aber kein Datenverlust). Seit der Anzeige-Umstellung
                # sind die Top-Level-Felder an solchen Tagen leer — deshalb aus
                # front_provider lesen, sonst TypeError auf put_25d = None.
                fp = t.get("front_provider") or t
                arr.append({"date": today,
                            # Messmethode mitschreiben. Die cm_*-Felder stammen aus
                            # _leg_own, also aus UNSERER BS-Inversion — nicht aus der
                            # Provider-IV. Ohne Markierung hielt verify() diese Zeilen
                            # fuer Provider-Referenzen und verglich damit zwei
                            # Rekonstruktionen miteinander (siehe verify-Docstring).
                            "method": "own_bs" if t.get("cm_mode") else "provider",
                            "cm_mode": t.get("cm_mode"),
                            "dte": t.get("cm_dte") if cm_ok else fp.get("dte"),
                            "skew_pts": t.get("cm_skew_pts") if cm_ok else fp["skew_pts"],
                            "put_iv": t.get("cm_put_iv") if cm_ok else (fp.get("put_25d") or {}).get("iv"),
                            "call_iv": t.get("cm_call_iv") if cm_ok else (fp.get("call_25d") or {}).get("iv"),
                            "iv_atm": t.get("cm_iv_atm") if cm_ok else fp.get("iv_atm"),
                            # VRP/PC aus den CM-Werten ableiten, wenn vorhanden:
                            # sonst stuenden in EINER Zeile normierte IVs neben
                            # Front-Monats-Kennzahlen — intern inkonsistent.
                            "vrp_pts": (round((t["cm_iv_atm"] - t["rv_1m"]) * 100, 2)
                                        if (cm_ok and t.get("cm_iv_atm") and t.get("rv_1m"))
                                        else fp.get("vrp_pts")),
                            "pc_ratio": (round(t["cm_put_iv"] / t["cm_call_iv"], 3)
                                         if (cm_ok and t.get("cm_call_iv")) else fp.get("pc_ratio")),
                            "bfly_pts": t.get("cm_bfly_pts") if cm_ok else fp.get("bfly_pts"),
                            "call_zeta_pts": t.get("cm_call_zeta_pts") if cm_ok else fp.get("call_zeta_pts"),
                            "put_zeta_pts":  t.get("cm_put_zeta_pts") if cm_ok else fp.get("put_zeta_pts")})
            hist[t["ticker"]] = arr[-750:]
        # CBOE-Correlation vorwärts akkumulieren (Yahoo liefert oft nur letzten Wert)
        if corr:
            carr = hist.setdefault("__CORR", [])
            if not any(e.get("date") == today for e in carr):
                carr.append({"date": today, "COR1M": (corr.get("COR1M") or {}).get("last"),
                             "COR3M": (corr.get("COR3M") or {}).get("last"),
                             "COR30D": (corr.get("COR30D") or {}).get("last")})
            hist["__CORR"] = carr[-750:]
        # Equity-P/C-Ratio vorwärts akkumulieren (keine freie Historie verfügbar)
        if per:
            parr = hist.setdefault("__PCR", [])
            if not any(e.get("date") == today for e in parr):
                parr.append({"date": today,
                             "eq_vol": pc_ratio["equity"]["vol"], "eq_oi": pc_ratio["equity"]["oi"],
                             "idx_vol": pc_ratio["index"]["vol"]})
            hist["__PCR"] = parr[-750:]
        write_json_atomic(hp, hist)
        print(f"[history] {sum(len(v) for v in hist.values())} Punkte über {len(hist)} Ticker → {hp.name}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=_DEFAULT_TICKERS)
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    try:
        build(a.tickers, not a.no_write)
    except MarktOffen as e:
        print(f"ABBRUCH: {e}", flush=True)
        return 2
    except SchluesselFehlt as e:
        print(f"ABBRUCH: {e}", flush=True)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
