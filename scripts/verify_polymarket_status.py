"""Waechter fuer den Marktstatus-Lebenszyklus von /polymarket (Phase B2).

Entwurf in vier Runden mit Codex bis FREIGABE
(docs/review_prompts/2026-10-20_polymarket_b2_entwurf_v4.md). Geprueft wird ohne Netz
und ohne Datenbank: Gamma und Supabase sind Attrappen.

**Die Supabase-Attrappe stellt die GEMESSENE Filtersemantik nach**, nicht eine
freundlichere. Zwei Messungen vom 2026-10-20, lesend auf der laufenden Datenbank und am
echten postgrest-Client:

  * Alle 26 Katalogzeilen haben `status IS NULL`, und `.neq("status","resolved")` trifft
    davon GENAU NULL Zeilen. Ein Entwurf mit blossem `neq` haette nichts geschrieben,
    ohne zu scheitern.
  * `update().eq(...).or_(...)` baut ein PATCH mit zwei getrennten Query-Parametern
    (`condition_id=eq.…` und `or=(…)`), die PostgREST mit AND verbindet, und setzt
    `Prefer: return=representation` — die Antwort traegt also die betroffenen Zeilen.
    Darauf stuetzt sich die Preisfreigabe.

REGEL ZUR KENNUNG `[Aufbau]`: nur fuer Eigenschaften der Testvorrichtung, nie fuer
Aussagen ueber den Produktivcode.
"""
from __future__ import annotations

import os
import pathlib
import sys
import traceback
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))


def _absturz(typ, wert, tb):
    """Eine Ausnahme ist kein Nachweis — Exit 3, damit der Mutationstest sie als
    UNGUELTIG zaehlt und nicht als „erkannt"."""
    traceback.print_exception(typ, wert, tb)
    print("[Absturz] unerwartete Ausnahme — kein Nachweis")
    sys.stdout.flush()
    os._exit(3)


sys.excepthook = _absturz

import shared.polymarket_data as pd          # noqa: E402
import shared.supabase_client as sc          # noqa: E402

fehler = 0
anzahl = 0


def _json_leer(text) -> bool:
    """Trug `missing_details` einen Skip-Vermerk? Dann wurde der Pfad nicht erreicht."""
    import json as _j
    try:
        return "skip" in (_j.loads(text) or {})
    except Exception:
        return False


def pruefe(bed, was):
    global fehler, anzahl
    anzahl += 1
    print(("  ok   " if bed else "  FEHL ") + was)
    if not bed:
        fehler += 1


# ── Attrappe: Supabase ──────────────────────────────────────────────────────

class Antwort:
    def __init__(self, data):
        self.data = data


class FakeTabelle:
    def __init__(self, db, protokoll, name):
        self.db, self.protokoll, self.name = db, protokoll, name
        self.op = None

    # -- Aufbau der Anfrage
    def select(self, *a, **k):
        self.op = {"art": "select", "tabelle": self.name, "filter": {}}
        return self

    def update(self, payload):
        self.op = {"art": "update", "tabelle": self.name,
                   "payload": dict(payload), "filter": {}}
        return self

    def insert(self, rows):
        self.op = {"art": "insert", "tabelle": self.name,
                   "rows": [dict(rows)] if isinstance(rows, dict) else
                           [dict(r) for r in rows], "filter": {}}
        return self

    def upsert(self, rows, on_conflict=None):
        self.op = {"art": "upsert", "tabelle": self.name,
                   "rows": [dict(r) for r in rows], "on_conflict": on_conflict,
                   "filter": {}}
        return self

    def eq(self, spalte, wert):
        self.op["filter"].setdefault("eq", []).append((spalte, wert))
        return self

    def neq(self, spalte, wert):
        # Mit SQL-NULL-Semantik, und das ist hier der ganze Punkt: `status <>
        # 'resolved'` ist fuer eine NULL-Zeile nicht wahr, sondern NULL, also
        # trifft die Zeile NICHT. Ohne diese Eigenheit wuerde die Attrappe eine
        # freundlichere Welt pruefen als die echte Datenbank — am 2026-10-20
        # lesend gemessen: `.neq("status","resolved")` trifft von 26 Zeilen mit
        # `status IS NULL` genau null.
        self.op["filter"].setdefault("neq", []).append((spalte, wert))
        return self

    def or_(self, ausdruck):
        self.op["filter"]["or"] = ausdruck
        return self

    def gte(self, *a, **k):
        return self

    def lte(self, *a, **k):
        return self

    def order(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def range(self, *a, **k):
        return self

    # -- Ausfuehrung
    def _trifft(self, zeile) -> bool:
        f = self.op["filter"]
        for spalte, wert in f.get("eq", []):
            if zeile.get(spalte) != wert:
                return False
        for spalte, wert in f.get("neq", []):
            if zeile.get(spalte) is None or zeile.get(spalte) == wert:
                return False
        ausdruck = f.get("or")
        if ausdruck:
            # Nur die eine Form, die der Produktivcode baut. Alles andere waere
            # eine erfundene Semantik.
            if ausdruck == "status.is.null,status.neq.resolved":
                if not (zeile.get("status") is None
                        or zeile.get("status") != "resolved"):
                    return False
            else:
                raise AssertionError("unbekannter or_-Ausdruck: %r" % ausdruck)
        return True

    def execute(self):
        self.protokoll.append(self.op)
        if self.op["art"] == "select":
            return Antwort([dict(z) for z in self.db.get(self.name, [])])
        if self.op["art"] == "insert":
            self.db.setdefault(self.name, []).extend(self.op["rows"])
            return Antwort(self.op["rows"])
        if self.op["art"] == "upsert":
            for r in self.op["rows"]:
                bestand = self.db.setdefault(self.name, [])
                for z in bestand:
                    if z.get("condition_id") == r.get("condition_id"):
                        z.update(r)
                        break
                else:
                    bestand.append(dict(r))
            return Antwort(self.op["rows"])
        # update
        getroffen = []
        for z in self.db.get(self.name, []):
            if self._trifft(z):
                z.update(self.op["payload"])
                getroffen.append(dict(z))
        return Antwort(getroffen)


class FakeClient:
    def __init__(self, db, protokoll):
        self.db, self.protokoll = db, protokoll

    def table(self, name):
        return FakeTabelle(self.db, self.protokoll, name)


def mit_db(zeilen):
    """Setzt die Supabase-Attrappe und gibt (db, protokoll) zurueck.

    Das Protokoll ist GEMEINSAM mit den Gamma-Abrufen (siehe `gamma`): nur in
    einer Liste laesst sich „alle Abrufe vor dem ersten Schreibvorgang" wirklich
    messen. Mit zwei getrennten Listen wurden nur Anzahl und Vorhandensein
    geprueft, und ein Schreibvorgang zwischen zwei Abrufen waere durchgegangen
    (Codex, Befund W3).
    """
    db = {"polymarket_markets": [dict(z) for z in zeilen], "polymarket_prices": []}
    protokoll = []
    global LOG
    LOG = protokoll
    sc.get_client = lambda: FakeClient(db, protokoll)
    return db, protokoll


LOG: list = []


# ── Attrappe: Gamma ────────────────────────────────────────────────────────

OFFEN = {"closed": False, "acceptingOrders": True, "archived": False,
         "enableOrderBook": True}
GESCHLOSSEN = {"closed": True, "acceptingOrders": None, "archived": False,
               "enableOrderBook": None}
PAUSIERT = {"closed": False, "acceptingOrders": False, "archived": False,
            "enableOrderBook": True}


def markt(cid, felder=None, bid=0.60, ask=0.62, slug=None):
    m = {"conditionId": cid, "question": "Frage " + cid, "slug": slug or ("slug-" + cid),
         "bestBid": bid, "bestAsk": ask, "outcomes": '["Yes","No"]',
         "clobTokenIds": '["t1","t2"]', "endDateIso": "2026-12-31",
         "liquidityNum": 1000, "volumeNum": 2000}
    m.update(felder if felder is not None else OFFEN)
    return m


def gamma(antworten):
    """`antworten` ordnet jeder angefragten ID-Menge eine Antwort zu.

    Wert `None` bedeutet technischer Fehlschlag, `[]` erfolgreich und leer.
    Die Attrappe protokolliert jeden Abruf, damit die Reihenfolge Abrufe-vor-
    Schreiben pruefbar ist.
    """
    rufe = []
    verbraucht: dict = {}

    def _ein_stapel(batch):
        rufe.append(tuple(batch))
        LOG.append({"art": "gamma", "batch": tuple(batch)})
        # Mehrere Eintraege mit demselben Schluessel werden der REIHE NACH
        # verbraucht — sonst liesse sich „Stapel scheitert, Einzelnachfrage
        # antwortet anders" nicht nachstellen: meine erste Fassung nahm immer den
        # ersten Treffer, und der Testfall fuer fremde IDs in der Einzelnachfrage
        # pruefte dadurch nichts.
        passend = [w for s, w in antworten if set(s) == set(batch)]
        if passend:
            schluessel = frozenset(batch)
            i = verbraucht.get(schluessel, 0)
            verbraucht[schluessel] = i + 1
            return passend[min(i, len(passend) - 1)]
        # Standard: jede ID als offener Markt
        return [markt(c) for c in batch]

    pd._ein_stapel = _ein_stapel
    return rufe


# ════════════════════════════════════════════════════════════════════════════
print("1. Entscheidungstabelle an den gemessenen Feldkombinationen:")
faelle = [
    ("offen", OFFEN, pd.STATUS_OFFEN),
    ("geschlossen", GESCHLOSSEN, pd.STATUS_GESCHLOSSEN),
    ("pausiert", PAUSIERT, pd.STATUS_PAUSIERT),
    ("archiviert aber offen", dict(OFFEN, archived=True), pd.STATUS_UNBEKANNT),
    # Dieser Fall trennt, was der vorige nicht trennt: ohne die Archiv-Pruefung
    # wuerde er `paused` ergeben, weil `acceptingOrders is False` zuerst greift.
    # Mit dem Fall „offen aber archiviert" allein war die Mutation aequivalent —
    # der Mutationstest hat das gemeldet.
    ("pausiert und archiviert", dict(PAUSIERT, archived=True), pd.STATUS_UNBEKANNT),
    ("closed fehlt", {"acceptingOrders": True}, pd.STATUS_UNBEKANNT),
    ("closed kein Wahrheitswert", dict(OFFEN, closed="false"), pd.STATUS_UNBEKANNT),
    ("acceptingOrders null, offen", dict(OFFEN, acceptingOrders=None), pd.STATUS_UNBEKANNT),
    ("kein dict", None, pd.STATUS_UNBEKANNT),
]
for name, felder, soll in faelle:
    ist = pd.status_aus_markt(None if felder is None else dict(felder))
    pruefe(ist == soll, "%-28s -> %s" % (name, ist))
alle = [pd.status_aus_markt(dict(f)) for _, f, _ in faelle if f is not None]
pruefe(pd.STATUS_AUFGELOEST not in alle,
       "`resolved` kommt aus keiner Feldkombination heraus (Erkenntnisgrenze)")

print("")
print("2. Deduplizierung und Widerspruch im Erzeuger:")
gamma([(("A", "B"), [markt("A"), markt("A"), markt("B")])])
ab = pd.fetch_markets_mit_abdeckung(["A", "B"])
pruefe(len(ab.markets) == 2,
       "dieselbe conditionId zweimal ergibt EINEN Eintrag (%d)" % len(ab.markets))
pruefe(not ab.unklar, "gleiche Antworten sind kein Widerspruch (%r)" % (ab.unklar,))

gamma([(("A", "B"), [markt("A", OFFEN), markt("A", GESCHLOSSEN), markt("B")])])
ab = pd.fetch_markets_mit_abdeckung(["A", "B"])
pruefe([m["conditionId"] for m in ab.markets] == ["B"],
       "widerspruechliche Antworten fliegen aus `markets` (%r)"
       % [m["conditionId"] for m in ab.markets])
pruefe ("A" in ab.unklar, "und landen in `unklar` (%r)" % (sorted(ab.unklar),))

gamma([(("A",), [markt("A"), markt("FREMD")])])
ab = pd.fetch_markets_mit_abdeckung(["A"])
pruefe(ab.fremd == {"FREMD"}, "nicht angefragte IDs sind `fremd` (%r)" % (ab.fremd,))

print("")
print("3. Nach gescheitertem Stapel die drei Faelle der Einzelnachfrage:")
gamma([(("A", "B", "C"), None),
       (("A",), [markt("A")]),
       (("B",), []),
       (("C",), None)])
ab = pd.fetch_markets_mit_abdeckung(["A", "B", "C"])
pruefe([m["conditionId"] for m in ab.markets] == ["A"],
       "Einzelantwort vorhanden -> markets (%r)" % [m["conditionId"] for m in ab.markets])
pruefe(ab.fehlt_bestaetigt == {"B"},
       "erfolgreich leer -> fehlt_bestaetigt (%r)" % (ab.fehlt_bestaetigt,))
pruefe(ab.unklar == {"C"},
       "erneut gescheitert -> unklar, NICHT verschwunden (%r)" % (ab.unklar,))
pruefe(ab.vollstaendig is False,
       "die Abdeckung ist damit nicht vollstaendig")

print("")
print("4. Der Schreibhelfer schreibt genau die uebergebenen Felder:")
_, prot = mit_db([{"condition_id": "A", "status": None, "active": True}])
sc.update_polymarket_markt_zustand([
    {"condition_id": "A", "last_fetch_state": "ok", "last_fetch_at": "T"}])
ups = [o for o in prot if o["art"] == "update"]
pruefe(len(ups) == 1, "[Aufbau] genau eine Anweisung (%d)" % len(ups))
pruefe(set(ups[0]["payload"]) == {"last_fetch_state", "last_fetch_at"},
       "ohne `status` enthaelt der Payload NUR die Abruffelder (%r)"
       % sorted(ups[0]["payload"]))
pruefe("or" not in ups[0]["filter"],
       "und laeuft ohne Statusfilter (%r)" % (ups[0]["filter"],))

_, prot = mit_db([{"condition_id": "A", "status": None, "active": True}])
sc.update_polymarket_markt_zustand([
    {"condition_id": "A", "status": "open", "status_checked_at": "T", "active": True,
     "unbekanntes_feld": 1}])
ups = [o for o in prot if o["art"] == "update"]
pruefe(set(ups[0]["payload"]) == {"status", "status_checked_at", "active"},
       "ein Feld ausserhalb der Weissliste wird nicht geschrieben (%r)"
       % sorted(ups[0]["payload"]))
pruefe(ups[0]["filter"].get("or") == "status.is.null,status.neq.resolved",
       "der Statusfilter deckt auch NULL ab (%r)" % ups[0]["filter"].get("or"))

print("")
print("5. Eine Zeile mit status IS NULL wird wirklich getroffen:")
db, prot = mit_db([{"condition_id": "A", "status": None, "active": True}])
getroffen = sc.update_polymarket_markt_zustand([
    {"condition_id": "A", "status": "closed", "status_checked_at": "T", "active": False}])
zeile = db["polymarket_markets"][0]
pruefe(zeile["status"] == "closed",
       "Status gesetzt, obwohl er vorher NULL war (%r)" % zeile["status"])
pruefe(zeile["active"] is False,
       "und `active` gleich mit (%r)" % zeile["active"])
pruefe(len(getroffen["freigegeben"]) == 1
       and getroffen["freigegeben"][0]["condition_id"] == "A",
       "die Freigabe nennt den Markt (%r)" % getroffen["freigegeben"])
pruefe(getroffen["beruehrt"] == {"A"},
       "und `beruehrt` ebenso (%r)" % (getroffen["beruehrt"],))

print("")
print("6. `resolved` ueberlebt, der Pruefzeitpunkt wird trotzdem erneuert:")
db, prot = mit_db([{"condition_id": "A", "status": "resolved", "active": False,
                    "status_checked_at": "ALT", "last_fetch_state": "alt"}])
getroffen = sc.update_polymarket_markt_zustand([
    {"condition_id": "A", "status": "open", "status_checked_at": "NEU",
     "active": True, "last_fetch_state": "ok", "last_fetch_at": "NEU"}])
zeile = db["polymarket_markets"][0]
pruefe(zeile["status"] == "resolved",
       "der Status bleibt `resolved` (%r)" % zeile["status"])
pruefe(zeile["active"] is False,
       "die Sichtbarkeit bleibt unberuehrt (%r)" % zeile["active"])
pruefe(zeile["status_checked_at"] == "NEU",
       "der Pruefzeitpunkt wird erneuert (%r)" % zeile["status_checked_at"])
pruefe(zeile["last_fetch_state"] == "ok" and zeile["last_fetch_at"] == "NEU",
       "die Abruffelder gehen NICHT verloren (%r/%r)"
       % (zeile["last_fetch_state"], zeile["last_fetch_at"]))
pruefe(getroffen["freigegeben"] == [],
       "die Freigabe ist leer — fuer den Preis eine Ablehnung (%r)"
       % getroffen["freigegeben"])
pruefe(getroffen["beruehrt"] == {"A"},
       "`beruehrt` nennt die Zeile trotzdem — sie EXISTIERT, und daraus darf "
       "niemand „keine Katalogzeile\" ableiten (%r)" % (getroffen["beruehrt"],))

print("")
print("7. Fetch-only auf einer aufgeloesten Zeile:")
db, prot = mit_db([{"condition_id": "A", "status": "resolved", "active": False,
                    "status_checked_at": "ALT"}])
sc.update_polymarket_markt_zustand([
    {"condition_id": "A", "last_fetch_state": "verworfen", "last_fetch_at": "NEU"}])
zeile = db["polymarket_markets"][0]
pruefe(zeile["last_fetch_state"] == "verworfen",
       "der Abrufzustand wird geschrieben (%r)" % zeile["last_fetch_state"])
pruefe(zeile["status"] == "resolved", "der Status bleibt (%r)" % zeile["status"])
pruefe(zeile["status_checked_at"] == "ALT",
       "ein nicht uebergebener Pruefzeitpunkt wird NICHT ergaenzt (%r)"
       % zeile["status_checked_at"])

print("")
print("8. Eine fremde Katalogzeile bleibt in allen Feldern unberuehrt:")
db, prot = mit_db([{"condition_id": "A", "status": None, "active": True},
                   {"condition_id": "FREMD", "status": None, "active": True,
                    "slug": "fremd"}])
sc.update_polymarket_markt_zustand([
    {"condition_id": "A", "status": "open", "status_checked_at": "T", "active": True}])
fremd = [z for z in db["polymarket_markets"] if z["condition_id"] == "FREMD"][0]
pruefe(fremd == {"condition_id": "FREMD", "status": None, "active": True,
                 "slug": "fremd"},
       "die fremde Zeile ist unveraendert (%r)" % fremd)

print("")
print("9. Katalogabgleich: alle Abrufe VOR dem ersten Schreibvorgang:")
import scripts.polymarket_discover as disc    # noqa: E402

DATEN = {"markets": [
    {"slug": "a", "category": "fed", "condition_id": "A"},
    {"slug": "b", "category": "fed", "condition_id": "B"},
    {"slug": "c", "category": "macro", "condition_id": "C"},
]}
db, prot = mit_db([{"condition_id": c, "status": None, "active": True,
                    "slug": c.lower(), "question": "q", "category": "fed"}
                   for c in ("A", "B", "C")])
rufe = gamma([(("A", "B", "C"), [markt("A", OFFEN), markt("B", GESCHLOSSEN)]),
              (("C",), [])])
bericht = disc.sync_catalog_to_db(DATEN)

schreibend = [i for i, o in enumerate(prot) if o["art"] in ("update", "upsert")]
abrufend = [i for i, o in enumerate(prot) if o["art"] == "gamma"]
pruefe(bool(abrufend), "[Aufbau] Gamma wurde ueberhaupt gerufen (%d Abrufe)" % len(abrufend))
pruefe(bool(schreibend), "[Aufbau] es wurde geschrieben (%d Anweisungen)" % len(schreibend))
pruefe(len(rufe) == 2,
       "beide Abrufe (Stapel + Einzelnachfrage) fanden statt (%r)" % (rufe,))
# Die eigentliche Reihenfolgepruefung, im GEMEINSAMEN Protokoll: der letzte Abruf
# muss vor dem ersten Schreibvorgang liegen.
pruefe(max(abrufend) < min(schreibend),
       "der LETZTE Gamma-Abruf liegt vor dem ERSTEN Schreibvorgang (%d < %d)"
       % (max(abrufend), min(schreibend)))
pruefe(bericht["gefunden"] == 2 and bericht["fehlt_bestaetigt"] == 1
       and bericht["unklar"] == 0,
       "Bericht: gefunden 2, bestaetigt nicht vorhanden 1, ungeprueft 0 (%r)"
       % {k: bericht[k] for k in ("gefunden", "fehlt_bestaetigt", "unklar")})

upserts = [o for o in prot if o["art"] == "upsert"]
pruefe(len(upserts) == 1, "genau EIN Metadaten-Upsert (%d)" % len(upserts))
felder = set().union(*[set(r) for r in upserts[0]["rows"]]) if upserts else set()
pruefe(not ({"status", "status_checked_at", "active"} & felder),
       "der Upsert enthaelt KEINE Statusfelder (%r)" % sorted(felder))
pruefe(all(set(r) == set(upserts[0]["rows"][0]) for r in upserts[0]["rows"]),
       "alle Upsert-Zeilen haben dieselben Schluessel")

status_ups = [o for o in prot if o["art"] == "update"]
nach_cid = {}
for o in status_ups:
    cid = dict(o["filter"].get("eq", [])).get("condition_id")
    nach_cid.setdefault(cid, []).append(o)
pruefe(nach_cid.get("A") and nach_cid["A"][0]["payload"].get("status") == "open",
       "A wird `open` (%r)" % (nach_cid.get("A") and nach_cid["A"][0]["payload"]))
pruefe(nach_cid.get("B") and nach_cid["B"][0]["payload"].get("status") == "closed"
       and nach_cid["B"][0]["payload"].get("active") is False,
       "B wird `closed` mit active=False (%r)"
       % (nach_cid.get("B") and nach_cid["B"][0]["payload"]))
pruefe(nach_cid.get("C")
       and nach_cid["C"][0]["payload"].get("status") == pd.STATUS_UNERREICHBAR
       and nach_cid["C"][0]["payload"].get("active") is False,
       "C wird `unavailable` mit active=False (%r)"
       % (nach_cid.get("C") and nach_cid["C"][0]["payload"]))
pruefe(all(o["art"] != "upsert" or "C" not in [r.get("condition_id") for r in o["rows"]]
           for o in prot),
       "fuer C wird KEINE Katalogzeile angelegt")

print("")
print("10. Ungeprueft bekommt keine Anweisung — und macht den Lauf rot:")
db, prot = mit_db([{"condition_id": c, "status": None, "active": True,
                    "slug": c.lower(), "question": "q", "category": "fed"}
                   for c in ("A", "B", "C")])
gamma([(("A", "B", "C"), None), (("A",), [markt("A")]), (("B",), []), (("C",), None)])
bericht = disc.sync_catalog_to_db(DATEN)
beruehrt = set()
for o in prot:
    if o["art"] == "update":
        beruehrt.add(dict(o["filter"].get("eq", [])).get("condition_id"))
    if o["art"] == "upsert":
        beruehrt |= {r.get("condition_id") for r in o["rows"]}
pruefe(bericht["unklar"] == 1, "[Aufbau] eine ID ist ungeprueft (%r)" % bericht["unklar"])
pruefe("C" not in beruehrt,
       "die ungepruefte ID kommt in KEINER Anweisung vor (%r)" % sorted(beruehrt))

print("")
print("11. Die Erzeuger: nur ein Weg fuehrt zu einem aktuellen Preis:")
pruefe(not hasattr(pd, "market_to_price_snapshot"),
       "der irrefuehrende oeffentliche Name ist weg")
pruefe(hasattr(pd, "aktueller_snapshot"), "[Aufbau] `aktueller_snapshot` existiert")
u = pd.aktueller_snapshot(markt("A", GESCHLOSSEN))
pruefe(u["preis_freigegeben"] is False and u["snapshot"] is None,
       "ein geschlossener Markt gibt keinen aktuellen Snapshot (%r)" % u["grund"])
u = pd.aktueller_snapshot(markt("A", PAUSIERT))
pruefe(u["preis_freigegeben"] is False,
       "ein pausierter Markt auch nicht (%r)" % u["grund"])
u = pd.aktueller_snapshot(markt("A", OFFEN))
pruefe(u["preis_freigegeben"] is True and u["snapshot"] is not None,
       "ein offener Markt mit gueltiger Quote schon")
u = pd.aktueller_snapshot(markt("A", OFFEN), db_status="resolved")
pruefe(u["endstatus"] == "resolved" and u["preis_freigegeben"] is False,
       "DB `resolved` schlaegt Gamma `open` (%r)" % u["grund"])
q = pd.bewerte_quote(markt("A", GESCHLOSSEN))
pruefe(q["status"] == "ok",
       "`bewerte_quote` bleibt statusfrei und bewertet nur die Quote (%r)" % q["status"])

gamma([(("A",), [markt("A", GESCHLOSSEN)])])
pruefe(pd.fetch_current_price("A") is None,
       "`fetch_current_price` liefert fuer einen geschlossenen Markt None")
gamma([(("A",), [markt("A", OFFEN)])])
pruefe(pd.fetch_current_price("A") is not None,
       "und fuer einen offenen Markt einen Snapshot")

print("")
print("12. Refresh: Status mitgeschrieben, Preis nur bei bewertbarem Status:")
import scripts.polymarket_refresh as rf      # noqa: E402

EINTRAEGE = [{"slug": "a", "condition_id": "A", "category": "fed"}]


def refresh_mit(katalogzeile, gamma_markt, **kw):
    db, prot = mit_db([katalogzeile])
    gamma([(("A",), [gamma_markt] if gamma_markt is not None else gamma_markt)])
    zaehler, errors = rf.refresh_markets(EINTRAEGE, **kw)
    return db, prot, zaehler, errors


db, prot, z, err = refresh_mit(
    {"condition_id": "A", "status": None, "active": True}, markt("A", OFFEN))
pruefe(z["preise"] == 1, "offener Markt: eine Preiszeile (%r)" % z)
preis_ups = [o for o in prot if o["art"] == "upsert" and o["tabelle"] == "polymarket_prices"]
pruefe(len(preis_ups) == 1, "die Preiszeile wird geschrieben (%d)" % len(preis_ups))
zeile = db["polymarket_markets"][0]
pruefe(zeile["status"] == "open" and zeile["active"] is True,
       "Status und Sichtbarkeit mitgeschrieben (%r/%r)" % (zeile["status"], zeile["active"]))

db, prot, z, err = refresh_mit(
    {"condition_id": "A", "status": "open", "active": True}, markt("A", GESCHLOSSEN))
pruefe(z["preise"] == 0 and z["fachlich_uebersprungen"] == 1,
       "geschlossener Markt: keine Preiszeile, fachlich uebersprungen (%r)" % z)
pruefe(not [o for o in prot if o["art"] == "upsert"
            and o["tabelle"] == "polymarket_prices"],
       "und wirklich kein Preis-Upsert")
zeile = db["polymarket_markets"][0]
pruefe(zeile["status"] == "closed" and zeile["active"] is False,
       "open -> closed setzt active=False (%r/%r)" % (zeile["status"], zeile["active"]))

db, prot, z, err = refresh_mit(
    {"condition_id": "A", "status": "unavailable", "active": False}, markt("A", OFFEN))
zeile = db["polymarket_markets"][0]
pruefe(zeile["status"] == "open" and zeile["active"] is True,
       "unavailable -> open setzt active=True (%r/%r)" % (zeile["status"], zeile["active"]))

db, prot, z, err = refresh_mit(
    {"condition_id": "A", "status": "resolved", "active": False}, markt("A", OFFEN))
pruefe(z["preise"] == 0,
       "DB `resolved` + Gamma `open`: keine Preiszeile (%r)" % z)
pruefe(db["polymarket_markets"][0]["status"] == "resolved",
       "und der Status bleibt aufgeloest")

# Der Wettlauf, den die Rueckgabe des Schreibvorgangs abfaengt: der Katalog wurde
# gelesen, als der Markt noch offen war, und ist inzwischen aufgeloest. Der aus dem
# Katalog gelesene Status sagt also „open" und blockt den Preis NICHT — erst die
# gefilterte Statusanweisung trifft keine Zeile, und daran wird die Preiszeile
# verworfen. Ohne diesen Fall waere die Rueckgabepruefung nur eine zweite Linie,
# die nie geprueft wird (der Mutationstest hat genau das gemeldet).
db = {"polymarket_markets": [{"condition_id": "A", "status": "resolved", "active": False}],
      "polymarket_prices": []}
prot = []


class VeralteterKatalogClient(FakeClient):
    def table(self, name):
        t = FakeTabelle(self.db, self.protokoll, name)
        echt = t.execute

        def execute():
            antwort = echt()
            if (t.op or {}).get("art") == "select" and name == "polymarket_markets":
                # So, wie der Katalog aussah, als er gelesen wurde.
                return Antwort([dict(z, status="open", active=True) for z in antwort.data])
            return antwort
        t.execute = execute
        return t


sc.get_client = lambda: VeralteterKatalogClient(db, prot)
gamma([(("A",), [markt("A", OFFEN)])])
z, err = rf.refresh_markets(EINTRAEGE)
pruefe(z["preise"] == 0,
       "veralteter Katalog (`open`), Zeile inzwischen `resolved`: keine Preiszeile (%r)" % z)
pruefe(not [o for o in prot if o["art"] == "upsert"
            and o["tabelle"] == "polymarket_prices"],
       "und wirklich kein Preis-Upsert — die Rueckgabe des Schreibvorgangs entscheidet")
pruefe(db["polymarket_markets"][0]["status"] == "resolved",
       "der Status bleibt aufgeloest (%r)" % db["polymarket_markets"][0]["status"])

db, prot, z, err = refresh_mit(
    {"condition_id": "A", "status": None, "active": True}, None)
pruefe(z["technische_fehler"] == 1,
       "kein Markt von Gamma: technischer Fehler (%r)" % z)
zeile = db["polymarket_markets"][0]
pruefe("status_checked_at" not in zeile or zeile.get("status_checked_at") is None,
       "ein gescheiterter Abruf erneuert `status_checked_at` NICHT (%r)"
       % zeile.get("status_checked_at"))
pruefe(zeile.get("last_fetch_state") == "fehler",
       "der Abrufzustand wird trotzdem festgehalten (%r)" % zeile.get("last_fetch_state"))

# Bestaetigt nicht vorhanden (`unavailable` aus dem Katalogabgleich) + Gamma ohne Markt: fachlich
# uebersprungen, KEIN technischer Fehler — sonst macht jeder von Polymarket entfernte Markt den
# taeglichen Lauf dauerhaft rot (fed-hike-2026, 29.–31.10.2026). Gegenprobe oben: ohne Katalogbeleg
# (status None) bleibt es ein technischer Fehler.
# Erfolgreich und leer (Stapel UND Einzelnachfrage `[]`) = bestaetigt nicht vorhanden.
db, prot = mit_db([{"condition_id": "A", "status": "unavailable", "active": False}])
gamma([(("A",), []), (("A",), [])])
z, err = rf.refresh_markets(EINTRAEGE)
pruefe(z["technische_fehler"] == 0 and z["fachlich_uebersprungen"] == 1,
       "kein Markt, Katalog `unavailable`: fachlich uebersprungen, kein technischer Fehler (%r)" % z)
pruefe(not [o for o in prot if o["art"] == "upsert" and o["tabelle"] == "polymarket_prices"],
       "und keine Preiszeile")
pruefe(db["polymarket_markets"][0]["status"] == "unavailable",
       "der Status bleibt `unavailable` (%r)" % db["polymarket_markets"][0]["status"])
db, prot, z, err = refresh_mit(
    {"condition_id": "A", "status": "unavailable", "active": False}, markt("A", OFFEN))
pruefe(z["preise"] == 1 and z["technische_fehler"] == 0,
       "taucht der Markt wieder auf, wird er normal bewertet (%r)" % z)
# Bestaetigt fehlend, aber der Katalog fuehrt den Markt (noch) nicht als `unavailable`: technischer Fehler —
# die Ausnahme braucht BEIDE Belege (Katalogabgleich + Abruf dieses Laufs).
db, prot = mit_db([{"condition_id": "A", "status": "open", "active": True}])
gamma([(("A",), []), (("A",), [])])
z, err = rf.refresh_markets(EINTRAEGE)
pruefe(z["technische_fehler"] == 1 and z["fachlich_uebersprungen"] == 0,
       "bestaetigt fehlend ohne Katalogbeleg `unavailable`: technischer Fehler (%r)" % z)

# Technischer Fehlschlag (`None`) bei Katalog `unavailable` bleibt technisch — der Wettlauf „Markt wieder da,
# Gamma gerade nicht erreichbar" darf nicht als bestaetigte Abwesenheit durchgehen (Codex 2026-10-31, Befund 1/2).
db, prot, z, err = refresh_mit(
    {"condition_id": "A", "status": "unavailable", "active": False}, None)
pruefe(z["technische_fehler"] == 1 and z["fachlich_uebersprungen"] == 0,
       "Abruf scheitert technisch, Katalog `unavailable`: technischer Fehler (%r)" % z)

print("")
print("13. Die Exit-Regel am echten Pfad:")


def main_mit(katalog, eintraege, gamma_antworten, fehlerhaft=None):
    """Fuehrt `rf.main()` mit Attrappen aus und gibt den Exit-Code zurueck."""
    db = {"polymarket_markets": [dict(z) for z in katalog], "polymarket_prices": []}
    protokoll = []

    class Client(FakeClient):
        def table(self, name):
            t = FakeTabelle(self.db, self.protokoll, name)
            if fehlerhaft:
                echt = t.execute

                def execute():
                    if (t.op or {}).get("art") in fehlerhaft.get("arten", ()) and \
                            (t.op or {}).get("tabelle") in fehlerhaft.get("tabellen", ()):
                        raise RuntimeError("Attrappe: Schreibfehler")
                    return echt()
                t.execute = execute
            return t

    # Das GEMEINSAME Protokoll umsetzen. Ohne diese Zeile las die Pruefung „keine
    # Preiszeile nach gescheitertem Zustands-Update" ein VERALTETES Protokoll aus
    # einem frueheren Abschnitt und bestand immer — die zugehoerige Mutation blieb
    # unbemerkt, gemeldet vom Mutationstest.
    global LOG
    LOG = protokoll
    sc.get_client = lambda: Client(db, protokoll)
    gamma(gamma_antworten)
    pd.load_markets_yaml = lambda: {"markets": eintraege}
    rf.load_markets_yaml = lambda: {"markets": eintraege}
    alt = sys.argv
    sys.argv = ["polymarket_refresh.py"]
    try:
        return rf.main()
    finally:
        sys.argv = alt


KAT_A = [{"condition_id": "A", "status": None, "active": True}]
rc = main_mit(KAT_A, EINTRAEGE, [(("A",), [markt("A", OFFEN)])])
pruefe(rc == 0, "ein Preis geschrieben -> Exit 0 (%r)" % rc)

rc = main_mit(KAT_A, EINTRAEGE, [(("A",), [markt("A", GESCHLOSSEN)])])
pruefe(rc == 0,
       "0 Preise, nur fachlich uebersprungen -> Exit 0, sonst stuerbe der Backfill (%r)"
       % rc)

rc = main_mit(KAT_A, EINTRAEGE, [(("A",), None)])
pruefe(rc == 1, "ein technischer Fehler -> Exit 1 (%r)" % rc)

# Der Gegenfall aus der Codex-Abnahme: ein fachlich uebersprungener Markt darf
# technische Fehler nicht neutralisieren.
E2 = [{"slug": "a", "condition_id": "A", "category": "fed"},
      {"slug": "b", "condition_id": "B", "category": "fed"}]
KAT_AB = [{"condition_id": "A", "status": None, "active": True},
          {"condition_id": "B", "status": None, "active": True}]
rc = main_mit(KAT_AB, E2, [(("A",), [markt("A", GESCHLOSSEN)]), (("B",), None)])
pruefe(rc == 1,
       "1 fachlich uebersprungen + 1 technischer Fehler -> Exit 1 (%r)" % rc)

# Alle IDs fehlen im Katalog: kein Markt wurde bearbeitet.
rc = main_mit([], EINTRAEGE, [(("A",), [markt("A", OFFEN)])])
pruefe(rc == 1, "alle IDs fehlen im DB-Katalog -> Exit 1 (%r)" % rc)

# Beide Schreibwege getrennt: ein Ausfall darf nicht vom Erfolg des anderen
# verdeckt werden.
rc = main_mit(KAT_A, EINTRAEGE, [(("A",), [markt("A", OFFEN)])],
              fehlerhaft={"arten": ("update",), "tabellen": ("polymarket_markets",)})
pruefe(rc == 1, "Zustands-Update scheitert -> Exit 1 (%r)" % rc)

rc = main_mit(KAT_A, EINTRAEGE, [(("A",), [markt("A", OFFEN)])],
              fehlerhaft={"arten": ("upsert",), "tabellen": ("polymarket_prices",)})
pruefe(rc == 1, "Preis-Upsert scheitert -> Exit 1 (%r)" % rc)

# Der Fall, in dem AUSSCHLIESSLICH `schreiben_ok` rot macht: ein Markt ist legitim
# geschlossen (fachlich uebersprungen, also waere der Lauf sonst gruen), der andere
# offen, und sein Preis-Upsert scheitert. Ohne diesen Fall war die Mutation
# „Schreibfehler nicht in der Exit-Regel" aequivalent, weil der letzte Term den
# Lauf ohnehin rot machte — gemeldet vom Mutationstest.
rc = main_mit(KAT_AB, E2,
              [(("A",), [markt("A", GESCHLOSSEN)]), (("B",), [markt("B", OFFEN)])],
              fehlerhaft={"arten": ("upsert",), "tabellen": ("polymarket_prices",)})
pruefe(rc == 1,
       "1 fachlich uebersprungen + gescheiterter Preis-Upsert -> Exit 1; nur "
       "`schreiben_ok` traegt diesen Fall (%r)" % rc)

print("")
print("14. Der Workflow ruft den Katalogabgleich als Schritt 1:")
wf = (WURZEL / ".github" / "workflows" / "polymarket_daily.yml").read_text(encoding="utf-8")
i1 = wf.find("polymarket_discover.py --sync-db")
i2 = wf.find("polymarket_refresh.py")
i3 = wf.find("polymarket_backfill.py")
pruefe(i1 != -1, "der Katalogabgleich steht im Workflow")
pruefe(i1 != -1 and i2 != -1 and i1 < i2,
       "er steht VOR dem Snapshot (%d < %d)" % (i1, i2))
pruefe(i1 != -1 and i3 != -1 and i1 < i3, "und vor dem Backfill")
block = wf[i1 - 200:i2] if i1 > 200 else wf[:i2]
pruefe("if !" in block and "exit 1" in block,
       "ein Fehlschlag in Schritt 1 bricht ab, bevor Schritt 2 laeuft")
pruefe("set -euo pipefail" in wf,
       "errexit und pipefail stehen im Shellblock")

print("")
print("15. Der Lader wird AUSGEFUEHRT, nicht im Text gesucht:")
# Textfragmente sind hier kein Nachweis: Codex hat am Lader ein
# `return Promise.resolve({});` direkt an den Anfang gesetzt, den restlichen Text
# stehen gelassen — und der Waechter blieb gruen, obwohl der RPC nie gerufen
# wurde (Befund W2). Deshalb laeuft der echte Lader in node gegen eine
# fetch-Attrappe, und diese Probe muss ihren Endmarker erreichen.
import subprocess    # noqa: E402

LADER_PROBE = WURZEL / "scripts" / "js" / "probe_polymarket_lader.js"
r = subprocess.run(["node", str(LADER_PROBE)], capture_output=True, text=True,
                   encoding="utf-8", timeout=120, cwd=str(WURZEL))
pruefe(r.returncode == 0,
       "probe_polymarket_lader.js laeuft durch (Exit %d)" % r.returncode)
if r.returncode != 0:
    # Die Fehlerzeilen der Probe DURCHREICHEN, jede auf eigener Zeile. Sonst
    # kann keine Mutation die Pruefung benennen, die sie reisst: die Zeilen
    # steckten zusammengequetscht in einer einzigen Meldung, und der
    # Mutationstest traf sie nur zufaellig (am Lauf gemeldet).
    for zeile in (r.stdout or "").splitlines():
        if zeile.startswith("  FEHL"):
            print("  FEHL [Lader]" + zeile[6:])
pruefe("PROBE-ENDE" in (r.stdout or ""),
       "und erreicht ihren Endmarker")
anz_lader = 0
for zeile in (r.stdout or "").splitlines():
    if zeile.startswith("PROBE-ENDE"):
        anz_lader = int(zeile.split()[1])
pruefe(anz_lader >= 14,
       "mit dem erwarteten Pruefumfang (%d, erwartet mindestens 14)" % anz_lader)
# Dass `SA.supabase.get` die Antwortform NICHT prueft, ist der Grund, warum der
# Lader sie selbst pruefen muss. Das gehoert als eigener Posten festgehalten.
app_js = (WURZEL / "landing" / "js" / "app.js").read_text(encoding="utf-8")
i_get = app_js.find("  get: function(table, query) {")
block = app_js[i_get:i_get + 900] if i_get != -1 else ""
pruefe(i_get != -1, "[Aufbau] SA.supabase.get gefunden")
pruefe("r.ok" not in block,
       "SA.supabase.get prueft `r.ok` weiterhin NICHT — eigener Posten, "
       "betrifft jede Seite; genau deshalb prueft der Lader selbst")

print("")
print("16. Der Katalogabgleich endet bei `unklar` mit Exit != 0 — am echten main:")
# Abschnitt 10 ruft nur `sync_catalog_to_db`. Codex hat `abgleich_rot` auf
# `return 0` geaendert und der Waechter blieb gruen (Befund W1). Also der echte
# Einstieg mit echtem Rueckgabewert.
db, prot = mit_db([{"condition_id": c, "status": None, "active": True,
                    "slug": c.lower(), "question": "q", "category": "fed"}
                   for c in ("A", "B", "C")])
gamma([(("A", "B", "C"), None), (("A",), [markt("A")]), (("B",), []), (("C",), None)])
disc.load_markets_yaml = lambda: DATEN
alt_argv = sys.argv
sys.argv = ["polymarket_discover.py", "--sync-db"]
try:
    rc_disc = disc.main()
finally:
    sys.argv = alt_argv
pruefe(rc_disc == 1,
       "main() --sync-db mit einer ungepruefte ID gibt 1 zurueck (%r)" % rc_disc)

db, prot = mit_db([{"condition_id": c, "status": None, "active": True,
                    "slug": c.lower(), "question": "q", "category": "fed"}
                   for c in ("A", "B", "C")])
gamma([(("A", "B", "C"), [markt("A"), markt("B"), markt("C")])])
sys.argv = ["polymarket_discover.py", "--sync-db"]
try:
    rc_disc = disc.main()
finally:
    sys.argv = alt_argv
pruefe(rc_disc in (0, None),
       "ohne ungepruefte ID gibt es keinen Fehlerexit (%r)" % rc_disc)

print("")
print("17. Der Workflow-Shellblock wird AUSGEFUEHRT, mit Attrappen:")
# Codex' Auflage: der Shelltest darf nicht die Textform pruefen, sondern muss
# zeigen, dass ein Fehlschlag in Schritt 1 die Schritte 2 und 3 verhindert.
import os as _os          # noqa: E402
import shutil             # noqa: E402
import tempfile           # noqa: E402

# PyYAML ist eine echte Voraussetzung dieses Abschnitts: der Shellblock wird aus
# der Workflow-Datei GELESEN und ausgefuehrt, nicht nachgebaut. Fehlt das Paket,
# ist der Nachweis UNGEPRUEFT — und ungepruefte Nachweise gelten in diesem Projekt
# nie als bestanden. Also rot, aber mit benannter Ursache statt als Absturz: der
# erste Gate-Lauf scheiterte genau hier, und im Protokoll stand nur ein
# Traceback (dieselbe Klasse wie „Jinja2 fehlte im Gate", v66.23).
try:
    import yaml as _yaml      # noqa: E402
except ModuleNotFoundError:
    _yaml = None

if _yaml is None:
    pruefe(False, "PyYAML fehlt — der Workflow-Shellblock ist nicht pruefbar "
                  "(im Gate `python3 -m pip install PyYAML` ergaenzen)")
    skript = ""
else:
    wf_text = (WURZEL / ".github" / "workflows" / "polymarket_daily.yml").read_text(encoding="utf-8")
    wf = _yaml.safe_load(wf_text)
    skript = wf["jobs"]["refresh"]["steps"][0]["with"]["script"]
pruefe("polymarket_discover.py --sync-db" in skript,
       "[Aufbau] der Shellblock aus der YAML enthaelt den Katalogabgleich")

bash = shutil.which("bash")
if not bash or not skript:
    pruefe(False, "bash oder der Shellblock fehlt — nicht pruefbar "
                  "(bash=%r, Shellblock=%d Zeichen)" % (bool(bash), len(skript)))
else:
    def shellblock(discover_rc: int, backfill: str = ""):
        tmp = tempfile.mkdtemp(prefix="sa-wf-")
        try:
            # `docker`-Attrappe: protokolliert jeden Aufruf und gibt fuer den
            # Katalogabgleich den gewuenschten Code zurueck.
            docker = _os.path.join(tmp, "docker")
            with open(docker, "w", newline="\n", encoding="utf-8") as fh:
                fh.write("#!/bin/sh\n"
                         'echo "$@" >> "$SA_LOG"\n'
                         'case "$*" in\n'
                         "  *polymarket_discover.py*) exit %d ;;\n" % discover_rc +
                         "esac\nexit 0\n")
            _os.chmod(docker, 0o755)
            for name in ("date", "tail"):
                pass
            log = _os.path.join(tmp, "aufrufe.txt")
            skriptdatei = _os.path.join(tmp, "block.sh")
            with open(skriptdatei, "w", newline="\n", encoding="utf-8") as fh:
                fh.write(skript)
            umgebung = dict(_os.environ)
            umgebung["PATH"] = tmp + _os.pathsep + umgebung.get("PATH", "")
            umgebung["SA_LOG"] = log
            umgebung["SA_EVENT"] = "workflow_dispatch" if backfill else "schedule"
            umgebung["SA_BACKFILL"] = backfill
            p = subprocess.run([bash, skriptdatei], capture_output=True, text=True,
                               encoding="utf-8", timeout=120, env=umgebung, cwd=tmp)
            aufrufe = ""
            if _os.path.exists(log):
                with open(log, encoding="utf-8") as fh:
                    aufrufe = fh.read()
            return p.returncode, aufrufe
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    rc_ok, aufrufe_ok = shellblock(0)
    pruefe("polymarket_discover.py" in aufrufe_ok,
           "[Aufbau] Schritt 1 wird gerufen")
    pruefe("polymarket_refresh.py" in aufrufe_ok,
           "bei Erfolg laeuft Schritt 2 (%r)" % aufrufe_ok.replace("\n", " | ")[:90])

    rc_rot, aufrufe_rot = shellblock(1)
    pruefe(rc_rot != 0,
           "scheitert Schritt 1, endet der Block mit Fehler (Exit %d)" % rc_rot)
    pruefe("polymarket_refresh.py" not in aufrufe_rot,
           "und Schritt 2 laeuft NICHT (%r)" % aufrufe_rot.replace("\n", " | ")[:90])
    pruefe("polymarket_backfill.py" not in aufrufe_rot,
           "Schritt 3 ebenfalls nicht")

    # Die Abwesenheit allein beweist nichts: ein dauerhaft abgeschalteter Backfill
    # haette dieselbe Pruefung bestanden (Codex' Gegenprobe blieb 121/121 gruen).
    # Deshalb ZUERST der positive Fall — mit include_backfill=true muss Schritt 3
    # wirklich laufen.
    rc_bf, aufrufe_bf = shellblock(0, backfill="true")
    pruefe("polymarket_backfill.py" in aufrufe_bf,
           "mit include_backfill=true laeuft Schritt 3 wirklich (%r)"
           % aufrufe_bf.replace("\n", " | ")[:100])
    rc_bf2, aufrufe_bf2 = shellblock(1, backfill="true")
    pruefe("polymarket_backfill.py" not in aufrufe_bf2,
           "und bleibt bei gescheitertem Schritt 1 aus, OBWOHL er angefordert war")

print("")
print("18. Die Gegenfaelle aus der Code-Abnahme, als Regressionsfaelle:")

# B1: ein gescheitertes Zustands-Update darf KEINE Preiszeile hinterlassen. Vorher
# wurde nur Exit 1 geprueft — der Schreibvorgang selbst blieb unbemerkt, und der
# rote Exit nimmt ihn nicht zurueck.
rc = main_mit(KAT_A, EINTRAEGE, [(("A",), [markt("A", OFFEN)])],
              fehlerhaft={"arten": ("update",), "tabellen": ("polymarket_markets",)})
letzte_preise = [o for o in LOG if o["art"] == "upsert"
                 and o["tabelle"] == "polymarket_prices"]
pruefe(rc == 1, "[Aufbau] der Lauf ist rot (%r)" % rc)
pruefe(not letzte_preise,
       "nach gescheitertem Zustands-Update entsteht KEINE Preiszeile (%d Upserts)"
       % len(letzte_preise))

# B2: ein gekreuztes Buch bei OFFENEM Markt ist ein Messproblem und begruendet
# keinen Erfolg. Vorher zaehlte es als „fachlich uebersprungen" -> Exit 0.
db, prot, z, err = refresh_mit({"condition_id": "A", "status": None, "active": True},
                               markt("A", OFFEN, bid=0.80, ask=0.20))
pruefe(z["quote_unbrauchbar"] == 1 and z["fachlich_uebersprungen"] == 0,
       "gekreuztes Buch zaehlt als Quotenproblem, nicht als fachliche Auslassung (%r)"
       % {k: z[k] for k in ("quote_unbrauchbar", "fachlich_uebersprungen")})
rc = main_mit(KAT_A, EINTRAEGE, [(("A",), [markt("A", OFFEN, bid=0.80, ask=0.20)])])
pruefe(rc == 1,
       "und macht den Lauf rot — ein Messfehler ist kein Erfolg (%r)" % rc)

# B3: der Fetch-only-Zweig laeuft ohne Statusfilter und darf deshalb nur die zwei
# Abruffelder tragen. Mit `active` konnte er einen aufgeloesten Markt sichtbar machen.
db, prot = mit_db([{"condition_id": "A", "status": "resolved", "active": False,
                    "status_checked_at": "ALT"}])
try:
    sc.update_polymarket_markt_zustand([
        {"condition_id": "A", "last_fetch_state": "fehler", "active": True,
         "status_checked_at": "NEU"}])
    geworfen = None
except ValueError as e:
    geworfen = str(e)
pruefe(geworfen is not None,
       "ohne `status` wird ein Feld ausserhalb der zwei Abruffelder abgelehnt (%r)"
       % (geworfen or "nichts geworfen")[:70])
zeile = db["polymarket_markets"][0]
pruefe(zeile["active"] is False and zeile["status_checked_at"] == "ALT",
       "und der aufgeloeste Markt bleibt unsichtbar mit altem Pruefzeitpunkt (%r/%r)"
       % (zeile["active"], zeile["status_checked_at"]))

# B4: `False == 0` in Python, aber `status_aus_markt` prueft auf Identitaet. Zwei
# Antworten mit `closed=False` und `closed=0` ergeben verschiedene Status.
pruefe(pd.status_aus_markt(dict(OFFEN, closed=0)) != pd.status_aus_markt(dict(OFFEN)),
       "[Aufbau] `closed=0` und `closed=False` ergeben verschiedene Status (%s / %s)"
       % (pd.status_aus_markt(dict(OFFEN, closed=0)), pd.status_aus_markt(dict(OFFEN))))
gamma([(("A",), [markt("A", OFFEN), markt("A", dict(OFFEN, closed=0))])])
ab = pd.fetch_markets_mit_abdeckung(["A"])
pruefe("A" in ab.unklar,
       "`closed=False` gegen `closed=0` ist ein Widerspruch, kein Treffer (%r)"
       % (sorted(ab.unklar),))

# B5: eine vorhandene `resolved`-Zeile, die Gamma nicht mehr kennt, ist KEINE
# fehlende Katalogzeile — ihr Pruefzeitpunkt wurde gerade erneuert.
db, prot = mit_db([{"condition_id": "A", "status": "resolved", "active": False,
                    "slug": "a", "question": "q", "category": "fed",
                    "status_checked_at": "ALT"}])
gamma([(("A",), [])])
bericht = disc.sync_catalog_to_db({"markets": [
    {"slug": "a", "category": "fed", "condition_id": "A"}]})
pruefe(bericht["fehlt_bestaetigt"] == 1,
       "[Aufbau] Gamma kennt den Markt nicht mehr (%r)" % bericht["fehlt_bestaetigt"])
pruefe(bericht["ohne_katalogzeile"] == [],
       "die vorhandene aufgeloeste Zeile wird NICHT als fehlend gemeldet (%r)"
       % (bericht["ohne_katalogzeile"],))
pruefe(db["polymarket_markets"][0]["status_checked_at"] != "ALT",
       "ihr Pruefzeitpunkt wurde erneuert (%r)"
       % db["polymarket_markets"][0]["status_checked_at"])

# B6: `preise` zaehlt GESCHRIEBENE Zeilen. Vorher stieg der Zaehler vor dem Upsert,
# und ein gescheiterter Upsert meldete trotzdem „1/1 Snapshots".
db, prot = mit_db([{"condition_id": "A", "status": None, "active": True}])


class UpsertFehlerClient(FakeClient):
    def table(self, name):
        t = FakeTabelle(self.db, self.protokoll, name)
        echt = t.execute

        def execute():
            if (t.op or {}).get("art") == "upsert" and name == "polymarket_prices":
                raise RuntimeError("Attrappe: Preis-Upsert scheitert")
            return echt()
        t.execute = execute
        return t


sc.get_client = lambda: UpsertFehlerClient(db, prot)
gamma([(("A",), [markt("A", OFFEN)])])
z, err = rf.refresh_markets(EINTRAEGE)
pruefe(z["preise"] == 0 and z["preise_vorbereitet"] == 1,
       "ein gescheiterter Upsert meldet 0 geschriebene bei 1 vorbereiteten (%r)"
       % {k: z[k] for k in ("preise", "preise_vorbereitet")})
pruefe(z["schreiben_ok"] is False, "und `schreiben_ok` ist falsch")

# B7: fremde IDs auch im Zweig der Einzelnachfrage.
gamma([(("A",), None), (("A",), [markt("FOREIGN")])])
ab = pd.fetch_markets_mit_abdeckung(["A"])
pruefe(ab.fremd == {"FOREIGN"},
       "eine fremde ID aus der Einzelnachfrage landet in `fremd` (%r)" % (ab.fremd,))
pruefe(ab.unklar == {"A"},
       "und die angefragte bleibt `unklar` (%r)" % (ab.unklar,))

# B8 der zweiten Runde: der Ablehnungsgrund muss auf einer Stufe stehen, die die
# PRODUKTIVEN Handler ausgeben. `debug` wird vom Dateihandler (INFO) und vom
# Konsolenhandler (WARNING) verworfen — er waere protokolliert worden, ohne
# irgendwo zu erscheinen.
import logging    # noqa: E402

aufgezeichnet = []


class _Sammler(logging.Handler):
    def emit(self, satz):
        aufgezeichnet.append((satz.levelno, satz.getMessage()))


_sammler = _Sammler(level=logging.INFO)     # wie der produktive Dateihandler
pd.app_logger.addHandler(_sammler)
gamma([(("A",), [markt("A", GESCHLOSSEN)])])
try:
    ergebnis_fcp = pd.fetch_current_price("A")
finally:
    pd.app_logger.removeHandler(_sammler)
pruefe(ergebnis_fcp is None, "[Aufbau] der geschlossene Markt liefert None")
pruefe(any("kein aktueller Preis" in text for _, text in aufgezeichnet),
       "der Ablehnungsgrund erscheint auf INFO oder hoeher — `debug` haetten beide "
       "produktiven Handler verworfen (%r)" % (aufgezeichnet,))
pruefe(all(stufe >= logging.INFO for stufe, _ in aufgezeichnet) and aufgezeichnet,
       "und zwar auf einer Stufe, die der Dateihandler ausgibt (%r)"
       % [stufe for stufe, _ in aufgezeichnet])

# N1 der zweiten Code-Runde: eine BESTAETIGTE Auflösung darf den Lauf nicht rot
# machen. Vorher wurde die verworfene Preiszeile nirgends gezaehlt -> 0 Preise,
# 0 fachlich -> Exit 1, und damit fiel zusaetzlich der Backfill aus.
db = {"polymarket_markets": [{"condition_id": "A", "status": "resolved", "active": False}],
      "polymarket_prices": []}
prot = []
LOG = prot
sc.get_client = lambda: VeralteterKatalogClient(db, prot)
gamma([(("A",), [markt("A", OFFEN)])])
rf.load_markets_yaml = lambda: {"markets": EINTRAEGE}
alt_argv2 = sys.argv
sys.argv = ["polymarket_refresh.py"]
try:
    rc_aufgeloest = rf.main()
finally:
    sys.argv = alt_argv2
pruefe(rc_aufgeloest == 0,
       "veralteter Katalog + inzwischen aufgeloeste Zeile: Exit 0, denn es ist eine "
       "bestaetigte fachliche Auslassung und kein Ausfall (%r)" % rc_aufgeloest)
pruefe(not [o for o in prot if o["art"] == "upsert"
            and o["tabelle"] == "polymarket_prices"],
       "und trotzdem keine Preiszeile")

print("")
print("19. Der Logpfad wird wirklich erreicht:")
# Alle `main`-Proben liefen ohne `--near-fomc-only`, also blieb `_log_intraday`
# unerreicht: ein entferntes `or not log_ok` liess den Waechter gruen (Befund W4).


def main_intraday(katalog, eintraege, gamma_antworten, log_scheitert: bool):
    db = {"polymarket_markets": [dict(z) for z in katalog], "polymarket_prices": [],
          "refresh_log": []}
    protokoll = []

    class Client(FakeClient):
        def table(self, name):
            t = FakeTabelle(self.db, self.protokoll, name)
            echt = t.execute

            def execute():
                if log_scheitert and name == "refresh_log":
                    raise RuntimeError("Attrappe: refresh_log scheitert")
                return echt()
            t.execute = execute
            return t

    global LOG
    LOG = protokoll
    sc.get_client = lambda: Client(db, protokoll)
    gamma(gamma_antworten)
    rf.load_markets_yaml = lambda: {"markets": eintraege}
    # `is_near_fomc` wird INNERHALB von main importiert — eine Attrappe an `rf`
    # greift nicht. Meine erste Fassung tat genau das, der Lauf nahm den
    # FOMC-Ausstieg und protokollierte `tickers_success: 0`, und der Test haette
    # „Logpfad erreicht" behauptet, ohne ihn zu erreichen. Dieselbe Klasse wie
    # Befund W4, nur eine Ebene tiefer.
    import shared.fed_dates as fd
    fd.is_near_fomc = lambda: True
    alt = sys.argv
    sys.argv = ["polymarket_refresh.py", "--near-fomc-only"]
    try:
        return rf.main(), db
    finally:
        sys.argv = alt


rc, db_i = main_intraday(KAT_A, EINTRAEGE, [(("A",), [markt("A", OFFEN)])], False)
pruefe(rc == 0, "[Aufbau] der Intraday-Lauf ist gruen (%r)" % rc)
pruefe(len(db_i.get("refresh_log", [])) == 1,
       "er schreibt genau eine refresh_log-Zeile (%d)" % len(db_i.get("refresh_log", [])))
zeile = (db_i.get("refresh_log") or [{}])[0]
pruefe(zeile.get("run_type") == "polymarket_intraday"
       and zeile.get("tickers_success") == 1
       and not _json_leer(zeile.get("missing_details")),
       "mit run_type, der ECHTEN Erfolgszahl 1 und ohne Skip-Vermerk — sonst hat der "
       "Lauf den FOMC-Ausstieg genommen statt den Pfad (%r)"
       % {k: zeile.get(k) for k in ("run_type", "tickers_success", "missing_details")})

rc, _ = main_intraday(KAT_A, EINTRAEGE, [(("A",), [markt("A", OFFEN)])], True)
pruefe(rc == 1,
       "scheitert die refresh_log-Zeile, ist der Lauf rot (%r)" % rc)

print("")
print("ALLE PRUEFUNGEN BESTANDEN" if fehler == 0 else "%d FEHLER" % fehler)
print("PROBE-ENDE %d Pruefungen, %d Fehler" % (anzahl, fehler))
sys.exit(0 if fehler == 0 else 1)
