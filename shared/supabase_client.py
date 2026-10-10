"""
shared/supabase_client.py — Supabase DB-Connector für SeasonAlpha

Credentials kommen aus os.environ (SUPABASE_URL, SUPABASE_KEY).
Lokal: .env im Projekt-Root (automatisch geladen via shared/__init__.py).
Server: docker-compose env-vars.
"""
from __future__ import annotations
import os
import time

try:
    from supabase import create_client
except ImportError:
    create_client = None

_client = None


def get_client(force_new: bool = False):
    """Lazy-Init des Supabase-Clients. force_new verwirft den gecachten Client."""
    global _client
    if create_client is None:
        raise ImportError(
            "supabase-Paket nicht installiert. "
            "Installiere es mit: pip install supabase"
        )
    if force_new:
        _client = None
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL und SUPABASE_KEY müssen in .env (lokal) "
                "oder in den Docker-Env-Vars (Server) gesetzt sein."
            )
        _client = create_client(url, key)
    return _client


def _with_retry(fn, max_tries: int = 3, backoff_base: float = 1.5):
    """
    Retry-Wrapper fuer transiente Netzwerk-Fehler. Nach einem Fail wird
    der globale _client resettet, weil httpx cachet Keep-Alive-Sockets
    die nach 10+ min idle TIME_WAIT oder stale werden ("Name or service
    not known" trotz funktionierendem DNS).
    """
    try:
        from httpx import ConnectError, TimeoutException, RemoteProtocolError
        retriable = (ConnectError, TimeoutException, RemoteProtocolError)
    except ImportError:
        retriable = (Exception,)
    last_exc = None
    for attempt in range(max_tries):
        try:
            return fn()
        except retriable as e:
            last_exc = e
            global _client
            _client = None  # Force re-create beim naechsten get_client()
            if attempt < max_tries - 1:
                time.sleep(backoff_base ** (attempt + 1))
    raise last_exc


# ── Prices ──────────────────────────────────────────

def fetch_prices(ticker: str, start_date: str = None) -> list[dict]:
    """Kursdaten aus Supabase laden (paginiert, kein Row-Limit)."""
    all_data = []
    page_size = 1000
    offset = 0

    while True:
        q = get_client().table("prices").select("*").eq("ticker", ticker)
        if start_date:
            q = q.gte("date", start_date)
        q = q.order("date").range(offset, offset + page_size - 1)
        batch = q.execute().data

        if not batch:
            break

        all_data.extend(batch)
        if len(batch) < page_size:
            break  # Letzte Seite
        offset += page_size

    return all_data


def upsert_prices(records: list[dict]):
    """Kursdaten in Supabase upserten (insert or update) — je Spaltensatz eine eigene Anfrage.

    PostgREST bildet die Spaltenliste einer Anfrage aus ALLEN Schlüsseln aller Datensätze und setzt einen
    fehlenden Wert auf NULL (merge-duplicates). Ein gemischter Upsert hätte damit bestehende Werte gelöscht:
    Zeilen ohne `tdom`/`tdoy` (Onboarding schützt so den Bestand, Codex P2 R1) oder ohne `open`
    (Yahoo-NaN). Gruppiert, enthält jede Anfrage nur Spalten, die alle ihre Datensätze tragen; nicht
    gesendete Spalten bleiben in der Datenbank unverändert.
    """
    if not records:
        return
    gruppen: dict[frozenset, list[dict]] = {}
    for r in records:
        gruppen.setdefault(frozenset(r), []).append(r)
    geschrieben = 0
    for gruppe in gruppen.values():
        try:
            get_client().table("prices").upsert(
                gruppe, on_conflict="ticker,date"
            ).execute()
        except Exception as e:
            # Mehrere Gruppen sind nicht atomar: was vor dem Fehler bestätigt wurde, IST geschrieben.
            # Die Zahl geht mit, damit Aufrufer keinen geschriebenen Teil als 0 zählen (Codex P2 R2).
            raise UpsertTeilfehler(geschrieben, e) from e
        geschrieben += len(gruppe)


class UpsertTeilfehler(RuntimeError):
    """Ein Upsert ist gescheitert; `geschrieben` Datensätze davor sind bestätigt geschrieben."""

    def __init__(self, geschrieben: int, ursache: Exception):
        super().__init__(f"{ursache} (davor {geschrieben} Zeilen bestätigt geschrieben)")
        self.geschrieben = geschrieben


def delete_prices(ticker: str):
    """Alle Kursdaten für einen Ticker löschen."""
    get_client().table("prices").delete().eq("ticker", ticker).execute()


# ── Seasonality ─────────────────────────────────────

def fetch_seasonality(ticker: str) -> list[dict]:
    """Vorberechnete Saisonalität laden."""
    return (
        get_client()
        .table("seasonality")
        .select("*")
        .eq("ticker", ticker)
        .order("day_of_year")
        .execute()
        .data
    )


def upsert_seasonality(records: list[dict]):
    """Saisonalitätsdaten upserten."""
    if not records:
        return
    get_client().table("seasonality").upsert(
        records, on_conflict="ticker,day_of_year"
    ).execute()


# ── TDoY Stats ─────────────────────────────────────

def upsert_tdoy_stats(records: list[dict]):
    """TDoY-Statistiken in Supabase upserten (Batch)."""
    if not records:
        return
    get_client().table("tdoy_stats").upsert(
        records, on_conflict="ticker,tdoy,direction,strategy"
    ).execute()


def fetch_tdoy_stats(
    ticker: str,
    strategy: str = "open_to_close",
    direction: str = "forward",
) -> list[dict]:
    """Vorberechnete TDoY-Statistiken für einen Ticker laden."""
    return (
        get_client()
        .table("tdoy_stats")
        .select("*")
        .eq("ticker", ticker)
        .eq("strategy", strategy)
        .eq("direction", direction)
        .order("tdoy")
        .execute()
        .data
    )


# ── App Logs ────────────────────────────────────────

def insert_log(level: str, channel: str, message: str, user_email: str = None):
    """Log-Eintrag in Supabase schreiben (für Streamlit Cloud)."""
    get_client().table("app_logs").insert({
        "level": level,
        "channel": channel,
        "message": message,
        "user_email": user_email,
    }).execute()


# ── Subscribers ────────────────────────────────────

def subscribe_email(
    email: str,
    source: str = "website",
    ip_address: str = None,
    brevo_synced: bool = False,
) -> dict | None:
    """
    Neuen Subscriber anlegen oder reaktivieren.

    Falls E-Mail bereits existiert und unsubscribed war,
    wird der Status auf 'active' zurückgesetzt.

    Returns:
        dict mit Subscriber-Daten oder None bei Fehler
    """
    email = email.strip().lower()
    client = get_client()

    # Prüfen ob schon vorhanden
    existing = (
        client.table("subscribers")
        .select("*")
        .eq("email", email)
        .execute()
        .data
    )

    if existing:
        # Reaktivieren falls unsubscribed
        record = existing[0]
        if record["status"] != "active" or record["no_emails"]:
            client.table("subscribers").update({
                "status": "active",
                "no_emails": False,
                "unsubscribed_at": None,
                "brevo_synced": brevo_synced,
                "source": source,
            }).eq("email", email).execute()
        elif brevo_synced and not record["brevo_synced"]:
            client.table("subscribers").update({
                "brevo_synced": True,
            }).eq("email", email).execute()
        return record

    # Neu anlegen
    result = client.table("subscribers").insert({
        "email": email,
        "status": "active",
        "source": source,
        "no_emails": False,
        "brevo_synced": brevo_synced,
        "ip_address": ip_address,
    }).execute()

    return result.data[0] if result.data else None


def unsubscribe_email(email: str) -> bool:
    """
    Subscriber austragen — setzt status='unsubscribed' und no_emails=True.

    Returns:
        True wenn erfolgreich, False wenn E-Mail nicht gefunden
    """
    email = email.strip().lower()
    client = get_client()

    existing = (
        client.table("subscribers")
        .select("id")
        .eq("email", email)
        .execute()
        .data
    )

    if not existing:
        return False

    client.table("subscribers").update({
        "status": "unsubscribed",
        "no_emails": True,
        "unsubscribed_at": "now()",
    }).eq("email", email).execute()

    return True


def get_subscriber(email: str) -> dict | None:
    """Subscriber-Daten abrufen."""
    email = email.strip().lower()
    result = (
        get_client()
        .table("subscribers")
        .select("*")
        .eq("email", email)
        .execute()
        .data
    )
    return result[0] if result else None


def get_active_subscribers() -> list[dict]:
    """Alle aktiven Subscriber laden (für Newsletter-Versand)."""
    return (
        get_client()
        .table("subscribers")
        .select("email, subscribed_at")
        .eq("status", "active")
        .eq("no_emails", False)
        .order("subscribed_at")
        .execute()
        .data
    )


def count_subscribers() -> dict:
    """Subscriber-Statistiken."""
    client = get_client()
    active = len(
        client.table("subscribers")
        .select("id", count="exact")
        .eq("status", "active")
        .eq("no_emails", False)
        .execute()
        .data
    )
    total = len(
        client.table("subscribers")
        .select("id", count="exact")
        .execute()
        .data
    )
    return {"active": active, "total": total, "unsubscribed": total - active}


# ── Market Events ──────────────────────────────────

def upsert_market_events(records: list[dict]):
    """Market Events in Supabase upserten (Feiertage, OPEX, Zentralbank)."""
    if not records:
        return
    # Supabase hat ein Limit von ~1000 Rows pro Request
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("market_events").upsert(
            batch,
            on_conflict="event_date,event_type,event_name,exchange",
        ).execute()


def fetch_market_events(
    start_date: str,
    end_date: str,
    event_types: list[str] = None,
    exchanges: list[str] = None,
) -> list[dict]:
    """Market Events aus Supabase laden."""
    q = (
        get_client()
        .table("market_events")
        .select("*")
        .gte("event_date", start_date)
        .lte("event_date", end_date)
    )
    if event_types:
        q = q.in_("event_type", event_types)
    if exchanges:
        q = q.in_("exchange", exchanges)
    return q.order("event_date").execute().data


# ── Monthly Stats ──────────────────────────────────

def upsert_monthly_stats(records: list[dict]):
    """Monatliche Statistiken upserten."""
    if not records:
        return
    get_client().table("monthly_stats").upsert(
        records, on_conflict="ticker,month,years_back"
    ).execute()


def fetch_monthly_stats(ticker: str, years_back: int = 20) -> list[dict]:
    """Monatliche Statistiken aus DB laden."""
    return (
        get_client()
        .table("monthly_stats")
        .select("*")
        .eq("ticker", ticker)
        .eq("years_back", years_back)
        .order("month")
        .execute()
        .data
    )


# ── KI Scores ─────────────────────────────────────

# ── Scanner Results ────────────────────────────────

# ── TDoM Stats ────────────────────────────────────

def upsert_tdom_stats(records: list[dict]):
    """TDoM-Statistiken upserten."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("tdom_stats").upsert(
            batch, on_conflict="ticker,tdom,direction,strategy"
        ).execute()


def fetch_tdom_stats(
    ticker: str,
    direction: str = "forward",
    strategy: str = "open_to_close",
) -> list[dict]:
    """TDoM-Statistiken aus DB laden."""
    return (
        get_client()
        .table("tdom_stats")
        .select("*")
        .eq("ticker", ticker)
        .eq("direction", direction)
        .eq("strategy", strategy)
        .order("tdom")
        .execute()
        .data
    )


# ── Spot-Vol Beta ─────────────────────────────────

def upsert_spot_vol_beta(records: list[dict]):
    """Spot-Vol Beta Daten upserten."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("spot_vol_beta").upsert(
            batch, on_conflict="event_date"
        ).execute()


# ── Historical CPI ───────────────────────────────

def upsert_historical_cpi(records: list[dict]):
    """CPI-Jahresdaten upserten (year, cpi, source)."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("historical_cpi").upsert(
            batch, on_conflict="year"
        ).execute()


def fetch_historical_cpi() -> list[dict]:
    """CPI-Jahresdaten aus DB laden."""
    return (
        get_client()
        .table("historical_cpi")
        .select("*")
        .order("year")
        .execute()
        .data
    )


# ── Tickers (Stammdaten) ─────────────────────────

def upsert_tickers(records: list[dict]):
    """Ticker-Stammdaten upserten (aus shared/symbols.py)."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("tickers").upsert(
            batch, on_conflict="ticker"
        ).execute()


def search_tickers_db(query: str, limit: int = 10) -> list[dict]:
    """Ticker-Suche via Supabase RPC (fuer zukuenftige API-Nutzung)."""
    return (
        get_client()
        .rpc("search_tickers", {"q": query, "lim": limit})
        .execute()
        .data
    )


def fetch_spot_vol_beta(
    start_date: str = None,
    end_date: str = None,
) -> list[dict]:
    """Spot-Vol Beta aus DB laden."""
    q = get_client().table("spot_vol_beta").select("*")
    if start_date:
        q = q.gte("event_date", start_date)
    if end_date:
        q = q.lte("event_date", end_date)
    return q.order("event_date").execute().data


# ── Polymarket ────────────────────────────────────

def upsert_polymarket_markets(records: list[dict]):
    """Polymarket-Markt-Metadata upserten (Katalog)."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("polymarket_markets").upsert(
            batch, on_conflict="condition_id"
        ).execute()


def fetch_polymarket_markets(
    category: str | None = None,
    active_only: bool = True,
) -> list[dict]:
    """Polymarket-Markt-Katalog laden."""
    q = get_client().table("polymarket_markets").select("*")
    if category:
        q = q.eq("category", category)
    if active_only:
        q = q.eq("active", True)
    return q.order("category").execute().data


def upsert_polymarket_prices(records: list[dict]):
    """Polymarket-Preis-Snapshots upserten (Zeitreihe)."""
    if not records:
        return
    batch_size = 500
    client = get_client()
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("polymarket_prices").upsert(
            batch, on_conflict="condition_id,ts"
        ).execute()


def update_polymarket_fetch_state(records: list[dict]):
    """Haelt je Markt fest, wie der letzte Preisabruf ausging.

    Erwartet dicts mit condition_id, last_fetch_state, last_fetch_at.

    Warum das gebraucht wird: ein gescheiterter oder verworfener Abruf muss den
    zuletzt gespeicherten Preis ENTWERTEN koennen. Ohne diesen Zustand bleibt
    eine noch junge Preiszeile bewertbar, obwohl der letzte Abruf ein
    gekreuztes Buch gesehen hat — ein reiner Zeitvergleich merkt das nicht.

    Bewusst ein UPDATE je Markt und kein Upsert: ein Upsert auf
    `condition_id` wuerde bei einem unbekannten Markt eine halbe Katalogzeile
    ANLEGEN (ohne slug, question, category — alle NOT NULL), und das schlaegt
    entweder fehl oder erzeugt Datenmuell. Der Katalog wird vom
    Discovery-Lauf gepflegt, nicht hier.
    """
    if not records:
        return
    client = get_client()
    for r in records:
        cid = r.get("condition_id")
        if not cid:
            continue
        client.table("polymarket_markets").update({
            "last_fetch_state": r.get("last_fetch_state"),
            "last_fetch_at": r.get("last_fetch_at"),
        }).eq("condition_id", cid).execute()


def fetch_polymarket_latest_prices(condition_ids: list[str] | None = None) -> list[dict]:
    """Neueste Preiszeile je Markt — serverseitig bestimmt.

    Ruft die Datenbankfunktion `polymarket_latest_prices` aus der Migration
    scripts/sql/polymarket_schema_2026_10.sql.

    Die vorherige Fassung hatte denselben Fehler wie das Frontend: sie holte
    die letzten 7 Tage mit `limit(5000)` und suchte in Python den neuesten
    Eintrag je Markt. Zwei Folgen, beide gemessen von Codex: ein haeufig
    aktualisierter Markt konnte einen selten aktualisierten vollstaendig aus
    der Antwort draengen, und ein Markt ohne Zeile in den letzten sieben Tagen
    fiel grundsaetzlich heraus. Beides endete im Verbraucher als Preis 0.

    KEIN stiller Rueckfall auf den alten Weg, wenn die Funktion fehlt: ein
    Rueckfall haette den Fehler weitergetragen, und das Projekt hat fuer
    stille Rueckfaelle schon bezahlt. Stattdessen eine Meldung, die sagt, was
    zu tun ist.
    """
    client = get_client()
    try:
        antwort = client.rpc(
            "polymarket_latest_prices",
            {"p_condition_ids": list(condition_ids) if condition_ids else None},
        ).execute()
    except Exception as e:
        raise RuntimeError(
            "polymarket_latest_prices ist nicht aufrufbar. Wurde "
            "scripts/sql/polymarket_schema_2026_10.sql im Supabase-SQL-Editor "
            "ausgefuehrt? Falls ja und der Fehler bleibt: PostgREST haelt das "
            "Schema im Speicher — `NOTIFY pgrst, 'reload schema';` nachziehen. "
            f"Urspruenglicher Fehler: {e}"
        ) from e
    return antwort.data or []


def fetch_polymarket_price_history(
    condition_id: str,
    limit: int = 1000,
) -> list[dict]:
    """Preis-Zeitreihe fuer einen Markt (aufsteigend sortiert)."""
    return (
        get_client()
        .table("polymarket_prices")
        .select("*")
        .eq("condition_id", condition_id)
        .order("ts")
        .limit(limit)
        .execute()
        .data
    )


# ── Polymarket Resolved (fuer Brier-Score) ────────

def upsert_polymarket_resolved_markets(records: list[dict]):
    """Resolved-Markt-Metadata upserten (Katalog historischer Aufloesungen).
    Retry bei httpx-ConnectError — Scraper haelt Supabase-Connection lange idle."""
    if not records:
        return
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        def do_upsert(_b=batch):
            client = get_client()
            return client.table("polymarket_resolved_markets").upsert(
                _b, on_conflict="condition_id"
            ).execute()
        _with_retry(do_upsert)


def upsert_polymarket_resolved_prices(records: list[dict]):
    """Resolved-Preis-Zeitreihe upserten (CLOB prices-history Snapshots).
    Retry bei httpx-ConnectError — siehe upsert_polymarket_resolved_markets."""
    if not records:
        return
    batch_size = 1000
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        def do_upsert(_b=batch):
            client = get_client()
            return client.table("polymarket_resolved_prices").upsert(
                _b, on_conflict="condition_id,ts"
            ).execute()
        _with_retry(do_upsert)


def fetch_polymarket_resolved_markets(
    category: str | None = None,
) -> list[dict]:
    """Resolved-Markt-Katalog laden (fuer Precompute/Analyse)."""
    q = get_client().table("polymarket_resolved_markets").select("*")
    if category:
        q = q.eq("category", category)
    return q.order("resolution_date", desc=True).execute().data or []


def fetch_scanner_results(scan_date: str = None, methode: str = "saison_v1") -> list[dict]:
    """Scanner-Ergebnisse der Methode `methode` (Saison-Score) — jüngstes Datum DIESER Methode, wenn keins angegeben.
    Alte KI-Score-Zeilen (methode NULL) werden nie gelesen. Nicht berechenbare Ticker (score NULL) kommen ans Ende."""
    client = get_client()
    if not scan_date:
        latest = (client.table("scanner_results").select("scan_date").eq("methode", methode)
                  .order("scan_date", desc=True).limit(1).execute().data)
        if not latest:
            return []
        scan_date = latest[0]["scan_date"]
    zeilen, offset = [], 0
    while True:
        teil = (client.table("scanner_results").select("*").eq("methode", methode).eq("scan_date", scan_date)
                .order("score", desc=True, nullsfirst=False).range(offset, offset + 999).execute().data) or []
        zeilen += teil
        if len(teil) < 1000:
            return zeilen
        offset += 1000
