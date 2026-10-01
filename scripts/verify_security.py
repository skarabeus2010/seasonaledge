#!/usr/bin/env python3
"""
verify_security.py — prüft maschinell die Sicherheits-Invarianten von SeasonAlpha.

    py -3.14 scripts/verify_security.py            # nur Code und Konfiguration
    py -3.14 scripts/verify_security.py --live     # zusätzlich Live-Belege (Netz nötig)
    py -3.14 scripts/verify_security.py --json     # maschinenlesbar

**Die Befundliste steht NICHT in diesem Repo** — es ist öffentlich. Dieses Skript
prüft nur Regeln; was aktuell offen ist, steht im lokalen Sicherheitsbericht.

Drei Ergebnisse je Prüfung, und der dritte ist der wichtige:

  BESTANDEN     — die Invariante wurde geprüft und gilt
  DURCHGEFALLEN — sie wurde geprüft und gilt nicht
  UNGEPRÜFT     — konnte nicht gemessen werden

**UNGEPRÜFT ist niemals BESTANDEN.** Eine Prüfung, die nicht messen konnte, darf nicht
grün aussehen — das ist die Regel, an der Sicherheitswächter üblicherweise scheitern.
Exit 1 bei mindestens einem DURCHGEFALLEN, Exit 2 wenn nur UNGEPRÜFTE übrig sind und
keine Fehler, Exit 0 nur wenn alles Geprüfte grün und nichts Kritisches ungeprüft ist.

Die Ausgabe nennt **nie** einen Schlüssel, eine Adresse oder eine vollständige
Nutzerzeile. Treffer werden als Fundort gemeldet, nicht als Wert.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def setze_repo(pfad: Path) -> None:
    """Richtet die Prüfungen auf einen anderen Baum.

    Nur für den Mutationstest: der arbeitet auf einer **Kopie** und fasst keine
    Produktionsdatei an. Eine Mutation in den Arbeitsbaum zu schreiben und
    zurückzunehmen ist unter Windows schon einmal schiefgegangen (gesperrte Datei,
    mutierte Produktionsdatei blieb liegen) — deshalb gar nicht erst.
    """
    global REPO
    REPO = Path(pfad).resolve()


BESTANDEN = "BESTANDEN"
DURCHGEFALLEN = "DURCHGEFALLEN"
UNGEPRUEFT = "UNGEPRÜFT"


# ── Soll-Manifest ───────────────────────────────────────────────────────────
# Absichtlich hier und nicht in einer losen Datei: wer eine Invariante lockert,
# tut es in einem Commit, der im Review sichtbar ist.

# Tabellen, die bewusst mit dem öffentlichen Anon-Key lesbar sein dürfen.
# ⚠️ Eine Tabelle wird nach ihren SPALTEN und ihren ERZEUGERN klassifiziert, nicht
# nach ihrem Namen. Eine Protokolltabelle gehört hier nur hinein, wenn nachgewiesen
# ist, dass kein Job Personendaten hineinschreibt — siehe Prüfung 7.
OEFFENTLICHE_TABELLEN = {
    "prices", "monthly_stats", "scanner_results", "regime_scores",
    "tdom_stats", "tdoy_stats", "tickers", "historical_cpi",
    "spot_vol_beta", "market_events", "seasonality", "ki_scores",
    "central_bank_dates", "dividend_events", "earnings_events",
    "polymarket_markets", "polymarket_prices",
    "polymarket_resolved_markets", "polymarket_resolved_prices",
}

# Tabellen, die niemals eine Zeile an `anon` geben dürfen.
PRIVATE_TABELLEN = {
    "subscribers", "daily_subscribers", "user_watchlists",
    "user_subscriptions", "refresh_log",
}

# Spaltennamen, die auf Personenbezug hindeuten.
PERSONENBEZUG = ("email", "e_mail", "mail_adresse", "recipient", "empfaenger")


@dataclass
class Ergebnis:
    nummer: int
    titel: str
    status: str
    details: list[str] = field(default_factory=list)
    kritisch: bool = True

    def zeile(self) -> str:
        zeichen = {BESTANDEN: "OK  ", DURCHGEFALLEN: "FEHL", UNGEPRUEFT: "?   "}[self.status]
        return f"[{zeichen}] {self.nummer}. {self.titel}"


# ── Hilfsfunktionen ─────────────────────────────────────────────────────────

def sql_ohne_kommentare(s: str) -> str:
    """Entfernt SQL-Kommentare, ohne die Zeilenstruktur zu zerstören.

    Ohne das meldet jede Prüfung Rauschen: `fix_subscribers_rls_policy.sql` zitiert
    die fehlerhafte Policy in einem `--`-Kommentar, um sie zu erklären. Ein Prüfer,
    der das als Fund meldet, verliert sein Vertrauen beim ersten Lauf.

    Zeilen werden durch gleich viele Leerzeichen ersetzt, damit Zeilennummern in
    Meldungen weiter stimmen.
    """
    # /* ... */ zuerst, Zeilenumbrüche darin erhalten
    def block(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))

    s = re.sub(r"/\*.*?\*/", block, s, flags=re.S)
    # -- bis Zeilenende, aber nicht innerhalb eines String-Literals
    zeilen = []
    for z in s.split("\n"):
        aus = []
        in_str = False
        i = 0
        while i < len(z):
            c = z[i]
            if c == "'":
                in_str = not in_str
                aus.append(c)
            elif not in_str and z.startswith("--", i):
                break
            else:
                aus.append(c)
            i += 1
        zeilen.append("".join(aus))
    return "\n".join(zeilen)


def zeilennummer(s: str, pos: int) -> int:
    return s.count("\n", 0, pos) + 1


def sql_dateien() -> list[Path]:
    return sorted(p for p in (REPO / "scripts").glob("*.sql") if p.is_file())


def workflow_dateien() -> list[Path]:
    d = REPO / ".github" / "workflows"
    return sorted(d.glob("*.yml")) if d.is_dir() else []


def lies(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(p)


# ── Prüfung 1: keine Policy ohne TO ─────────────────────────────────────────

POLICY_RE = re.compile(
    r"CREATE\s+POLICY\s+\"?(?P<name>[^\"\s]+)\"?\s+ON\s+(?P<tabelle>[\w.\"]+)"
    r"(?P<rest>(?:.(?!CREATE\s+POLICY)){0,400})",
    re.S | re.I,
)


def pruefe_policy_to() -> Ergebnis:
    """Eine Policy ohne TO-Klausel gilt in PostgreSQL für PUBLIC — also auch für anon.

    Notwendig, nicht hinreichend: `TO public` und `TO anon` erfüllen die Form und sind
    genauso offen. Prüfung 2 nimmt sich das vor.
    """
    treffer = []
    for p in sql_dateien():
        s = sql_ohne_kommentare(lies(p))
        for m in POLICY_RE.finditer(s):
            if not re.search(r"\bTO\s+\w", m.group("rest"), re.I):
                treffer.append(
                    f"{rel(p)}:{zeilennummer(s, m.start())} — Policy "
                    f"\"{m.group('name')}\" auf {m.group('tabelle')} ohne TO-Klausel"
                )
    if treffer:
        return Ergebnis(1, "Keine CREATE POLICY ohne TO-Klausel", DURCHGEFALLEN, treffer)
    return Ergebnis(1, "Keine CREATE POLICY ohne TO-Klausel", BESTANDEN,
                    [f"{len(sql_dateien())} SQL-Dateien geprüft, Kommentare ausgenommen"])


# ── Prüfung 2: keine weite Policy für anon/public ───────────────────────────

def pruefe_policy_rollen() -> Ergebnis:
    """`TO public` oder `TO anon` mit FOR ALL / ohne Einschränkung ist dasselbe Loch
    in anderer Schreibweise. Lesende Policies auf öffentlichen Tabellen sind erlaubt.
    """
    treffer = []
    for p in sql_dateien():
        s = sql_ohne_kommentare(lies(p))
        for m in POLICY_RE.finditer(s):
            rest = m.group("rest")
            rollen = re.search(r"\bTO\s+([\w\s,]+?)(?:\n|USING|WITH|FOR|;)", rest, re.I)
            if not rollen:
                continue
            namen = {r.strip().lower() for r in rollen.group(1).split(",")}
            if not (namen & {"anon", "public", "authenticated"}):
                continue
            cmd = re.search(r"\bFOR\s+(ALL|SELECT|INSERT|UPDATE|DELETE)", rest, re.I)
            operation = cmd.group(1).upper() if cmd else "ALL"
            tabelle = m.group("tabelle").strip('"').split(".")[-1]
            if operation == "SELECT" and tabelle in OEFFENTLICHE_TABELLEN:
                continue  # bewusst öffentlich lesbar
            # Eigentümerbindung: `USING (auth.uid() = user_id)` schränkt die Zeilen auf
            # den angemeldeten Nutzer ein — das ist der KORREKTE Bauplan für eine
            # nutzerbezogene Tabelle und kein Befund. Ohne diese Ausnahme meldet der
            # Wächter jede richtig gebaute Policy, und dann wird er ignoriert.
            if namen <= {"authenticated"} and re.search(r"auth\.uid\(\)", rest, re.I):
                continue
            if operation == "INSERT" and "anon" in namen:
                treffer.append(
                    f"{rel(p)}:{zeilennummer(s, m.start())} — anon darf INSERT auf "
                    f"{tabelle} (nur zulässig, wenn ein Bestätigungsschritt davorsteht)"
                )
                continue
            treffer.append(
                f"{rel(p)}:{zeilennummer(s, m.start())} — {operation} für "
                f"{'/'.join(sorted(namen))} auf {tabelle}"
            )
    titel = "Keine weite Policy für anon/public/authenticated"
    if treffer:
        return Ergebnis(2, titel, DURCHGEFALLEN, treffer)
    return Ergebnis(2, titel, BESTANDEN)


# ── Prüfung 3: kein fest eingebautes Secret als Rückfall ────────────────────

SECRET_RUECKFALL = re.compile(
    r"""(?ix)
    (?P<name>[A-Z_]*(?:SECRET|TOKEN|PASSWORD|PASSWD|APIKEY|API_KEY)[A-Z_]*)
    \s*=\s*
    (?P<wert>["'][^"'\n]{6,}["'])
    """,
)
# Diese Namen sind Platzhalter oder Feldnamen, keine Geheimnisse.
SECRET_ERLAUBT = re.compile(r"(?i)(getenv|environ|os\.environ|input\(|%%|<|\{\{|xxx|changeme|example)")


def pruefe_secret_rueckfall() -> Ergebnis:
    """Ein Geheimnis mit Default-Wert im Code ist in einem öffentlichen Repo
    veröffentlicht — und der Default greift still, wenn die Umgebungsvariable fehlt.
    Gemeldet wird der Fundort, **nie** der Wert.
    """
    treffer = []
    for unter in ("shared", "scripts", "supabase"):
        basis = REPO / unter
        if not basis.is_dir():
            continue
        for p in sorted(basis.rglob("*")):
            if p.suffix not in (".py", ".ts", ".js", ".sql", ".sh") or not p.is_file():
                continue
            s = lies(p)
            quelle = sql_ohne_kommentare(s) if p.suffix == ".sql" else s
            for m in SECRET_RUECKFALL.finditer(quelle):
                umfeld = quelle[max(0, m.start() - 120):m.end() + 40]
                if SECRET_ERLAUBT.search(umfeld):
                    continue
                treffer.append(
                    f"{rel(p)}:{zeilennummer(quelle, m.start())} — "
                    f"{m.group('name')} hat einen fest eingebauten Wert "
                    f"({len(m.group('wert')) - 2} Zeichen, nicht ausgegeben)"
                )
    titel = "Kein fest eingebautes Geheimnis als Rückfall"
    if treffer:
        return Ergebnis(3, titel, DURCHGEFALLEN, treffer)
    return Ergebnis(3, titel, BESTANDEN)


# ── Prüfung 4: Workflow-Eingaben nicht in Shellquelltext ────────────────────

AUSDRUCK_RE = re.compile(r"\$\{\{\s*(?P<ausdruck>[^}]+?)\s*\}\}")
UNSICHERE_QUELLE = re.compile(
    r"(?i)github\.event\.(inputs|issue|comment|pull_request|head_commit)"
    r"|github\.head_ref|inputs\."
)


def pruefe_workflow_injection() -> Ergebnis:
    """Ein `${{ github.event.inputs.x }}` im Rumpf von `run:` oder `script:` wird vor
    der Shell eingesetzt — der Wert ist dann Quelltext, nicht Daten. Diese Skripte
    laufen hier per SSH als root. Der sichere Weg ist `env:` plus `"$VAR"`.
    """
    treffer = []
    for p in workflow_dateien():
        s = lies(p)
        # Rumpf von run:/script: grob abgrenzen (YAML-Blockskalar, Einrückung)
        for block in re.finditer(r"^(?P<i>\s*)(run|script):\s*[|>][-+]?\s*\n"
                                 r"(?P<rumpf>(?:(?:\s*\n)|(?:\1\s+.*\n))+)",
                                 s, re.M):
            for m in AUSDRUCK_RE.finditer(block.group("rumpf")):
                if UNSICHERE_QUELLE.search(m.group("ausdruck")):
                    zeile = zeilennummer(s, block.start("rumpf")) + \
                        block.group("rumpf").count("\n", 0, m.start())
                    treffer.append(
                        f"{rel(p)}:{zeile} — {m.group('ausdruck')} steht im "
                        f"Shellrumpf (gehört über env: und \"$VAR\")"
                    )
    titel = "Keine Workflow-Eingabe direkt im Shellrumpf"
    treffer = sorted(set(treffer))
    if treffer:
        return Ergebnis(4, titel, DURCHGEFALLEN, treffer)
    return Ergebnis(4, titel, BESTANDEN,
                    [f"{len(workflow_dateien())} Workflows geprüft"])


# ── Prüfung 5: TLS-Verifikation nirgends abgeschaltet ───────────────────────

TLS_AUS = (
    (re.compile(r"verify\s*=\s*False"), "requests mit verify=False"),
    (re.compile(r"_create_unverified_context"), "ssl._create_unverified_context"),
    (re.compile(r"CERT_NONE"), "ssl.CERT_NONE"),
    (re.compile(r"check_hostname\s*=\s*False"), "check_hostname=False"),
    (re.compile(r"NODE_TLS_REJECT_UNAUTHORIZED"), "NODE_TLS_REJECT_UNAUTHORIZED"),
    (re.compile(r"curl\s+[^\n|]*(?:-k|--insecure)\b"), "curl --insecure"),
)


def pruefe_tls() -> Ergebnis:
    """Ein Importer ohne Zertifikatsprüfung macht jeden im Netzwerkpfad zum Autor
    seiner Daten. Fließen die Daten anschließend in eine Seite, ist das ein
    geschlossener Pfad bis in den Browser des Besuchers.
    """
    treffer = []
    for unter in ("scripts", "shared", "deploy", "blog", "seo"):
        basis = REPO / unter
        if not basis.is_dir():
            continue
        for p in sorted(basis.rglob("*")):
            if p.suffix not in (".py", ".js", ".ts", ".sh", ".yml") or not p.is_file():
                continue
            s = lies(p)
            for rx, was in TLS_AUS:
                for m in rx.finditer(s):
                    z = zeilennummer(s, m.start())
                    # Kommentarzeilen überspringen
                    anfang = s.rfind("\n", 0, m.start()) + 1
                    if s[anfang:m.start()].strip().startswith(("#", "//", "--")):
                        continue
                    treffer.append(f"{rel(p)}:{z} — {was}")
    titel = "TLS-Verifikation nirgends abgeschaltet"
    treffer = sorted(set(treffer))
    if treffer:
        return Ergebnis(5, titel, DURCHGEFALLEN, treffer)
    return Ergebnis(5, titel, BESTANDEN)


# ── Prüfung 6: Edge Functions leiten Identität nicht aus dem Body ──────────

def pruefe_edge_identitaet() -> Ergebnis:
    """Eine `user_id` aus dem Request-Body ist keine Identität. Wird damit unter der
    Service-Rolle gesucht, kann jeder Aufrufer fremde Daten adressieren.

    Erwartet: der Handler prüft ein JWT (`auth.getUser`, `getClaims`, `verify`) ODER
    er liest keine Identität aus dem Body.
    """
    basis = REPO / "supabase" / "functions"
    if not basis.is_dir():
        return Ergebnis(6, "Edge Functions leiten Identität aus verifiziertem JWT ab",
                        UNGEPRUEFT, ["supabase/functions/ nicht vorhanden"])
    treffer = []
    geprueft = 0
    for p in sorted(basis.rglob("index.ts")):
        geprueft += 1
        s = lies(p)
        aus_body = re.search(
            r"(?:const|let|var)\s*\{[^}]*\buser_id\b[^}]*\}\s*=\s*await\s+req\.json", s)
        if not aus_body:
            continue
        prueft_jwt = re.search(
            r"auth\.getUser|getClaims|jwtVerify|verifyJWT|Authorization", s)
        if prueft_jwt:
            continue
        dienst = "SUPABASE_SERVICE_ROLE_KEY" in s
        treffer.append(
            f"{rel(p)}:{zeilennummer(s, aus_body.start())} — user_id aus dem Body, "
            f"keine JWT-Prüfung erkennbar" + (" (Client mit Service-Rolle)" if dienst else "")
        )
    titel = "Edge Functions leiten Identität aus verifiziertem JWT ab"
    if not geprueft:
        return Ergebnis(6, titel, UNGEPRUEFT, ["keine index.ts gefunden"])
    if treffer:
        return Ergebnis(6, titel, DURCHGEFALLEN, treffer)
    return Ergebnis(6, titel, BESTANDEN, [f"{geprueft} Functions geprüft"])


# ── Prüfung 7: keine Personendaten in öffentliche Tabellen ─────────────────

def pruefe_personendaten_in_oeffentlichen_tabellen() -> Ergebnis:
    """Die Freigabeliste oben ist eine Behauptung über SPALTEN, nicht über Namen.
    Diese Prüfung sucht Code, der eine Adresse in eine als öffentlich geführte
    Tabelle schreibt — der Weg, auf dem eine Betriebstabelle zur Datenpanne wird.
    """
    treffer = []
    basis = REPO / "scripts"
    tabellen = "|".join(sorted(OEFFENTLICHE_TABELLEN))
    for p in sorted(basis.rglob("*.py")):
        s = lies(p)
        for m in re.finditer(rf"table\(\s*[\"']({tabellen})[\"']", s):
            tabelle = m.group(1)
            # Umfeld des Aufrufs nach Personenbezug absuchen
            umfeld = s[m.start():m.start() + 1200]
            for feld in PERSONENBEZUG:
                if re.search(rf"\b{feld}\b", umfeld, re.I):
                    treffer.append(
                        f"{rel(p)}:{zeilennummer(s, m.start())} — schreibt nach "
                        f"{tabelle}, im Umfeld steht ein Feld „{feld}\""
                    )
                    break
    titel = "Keine Personendaten in als öffentlich geführte Tabellen"
    if treffer:
        return Ergebnis(7, titel, DURCHGEFALLEN, sorted(set(treffer)))
    return Ergebnis(7, titel, BESTANDEN,
                    [f"{len(OEFFENTLICHE_TABELLEN)} freigegebene Tabellen geprüft"])


# ── Prüfung 8: nginx-Header fallen in keiner location weg ──────────────────

SCHUTZHEADER = ("X-Frame-Options", "X-Content-Type-Options")


def pruefe_nginx_header() -> Ergebnis:
    """`add_header` erbt NICHT in eine location, die einen eigenen Satz deklariert.
    Eine location, die nur ein `Cache-Control` setzt, verliert damit still alle
    Schutzheader des Servers.

    `/embed` ist ausgenommen: dort ist das Einbetten der Zweck.
    """
    p = REPO / "deploy" / "nginx.conf"
    titel = "Keine nginx-location verliert die Schutzheader"
    if not p.is_file():
        return Ergebnis(8, titel, UNGEPRUEFT, ["deploy/nginx.conf nicht vorhanden"], kritisch=False)
    s = lies(p)
    treffer = []
    for m in re.finditer(r"^\s*location\s+(?P<muster>[^{]+?)\s*\{", s, re.M):
        muster = m.group("muster").strip()
        # Rumpf dieser location bis zur passenden schließenden Klammer (einfach, aber ausreichend)
        tiefe = 0
        i = s.index("{", m.start())
        ende = i
        for j in range(i, len(s)):
            if s[j] == "{":
                tiefe += 1
            elif s[j] == "}":
                tiefe -= 1
                if tiefe == 0:
                    ende = j
                    break
        rumpf = s[i:ende]
        if "add_header" not in rumpf:
            continue  # erbt den Server-Satz, in Ordnung
        if "embed" in muster:
            continue
        fehlend = [h for h in SCHUTZHEADER if h.lower() not in rumpf.lower()]
        if fehlend:
            treffer.append(
                f"{rel(p)}:{zeilennummer(s, m.start())} — location {muster} "
                f"setzt eigene add_header, ohne {', '.join(fehlend)}"
            )
    if treffer:
        return Ergebnis(8, titel, DURCHGEFALLEN, treffer)
    return Ergebnis(8, titel, BESTANDEN)


# ── Prüfung 9: Frontend-Key wird auf seine Rolle geprüft ───────────────────

def pruefe_key_rolle() -> Ergebnis:
    """Der Anon-Key im HTML ist Absicht. Ein versehentlich dort eingesetzter
    `service_role`-Key wäre eine Veröffentlichung mit Schreibrechten. Das Skript,
    das ihn einsetzt, muss die Rolle prüfen und bei Abweichung abbrechen.
    """
    p = REPO / "deploy" / "inject_credentials.sh"
    titel = "inject_credentials.sh prüft die Rolle des Frontend-Keys"
    if not p.is_file():
        return Ergebnis(9, titel, UNGEPRUEFT, ["deploy/inject_credentials.sh fehlt"])
    s = lies(p)
    # ⚠️ Nicht „irgendwo im Skript steht role" prüfen. Der erste Entwurf dieser
    # Prüfung tat genau das und meldete deshalb BESTANDEN, obwohl ein Rollen-Decode
    # in einem Zweig liegen kann, der für den tatsächlich verwendeten Schlüssel nie
    # durchlaufen wird. **Ein falsches BESTANDEN ist schlimmer als ein Fehlalarm.**
    #
    # Die Frage ist deshalb: wird die Rolle DES TATSÄCHLICH VERWENDETEN Schlüssels
    # geprüft — nicht, ob das Wort irgendwo vorkommt.
    zuweisung = re.search(r"^(?P<var>[A-Z_]+)=\"?\$\{(?P<quelle>[A-Z_]+)[:\-}]", s, re.M)
    if not zuweisung:
        return Ergebnis(9, titel, UNGEPRUEFT,
                        [f"{rel(p)} — Zuweisung des Frontend-Keys nicht erkannt"])
    var = zuweisung.group("var")
    # Ein Rollen-Decode, der sich auf genau diese Variable bezieht
    geprueft = re.search(rf"ROLE=[^\n]*\${{?{var}\b", s) or \
        re.search(rf"\${{?{var}}}?[^\n]*\|\s*[^\n]*role", s, re.I)
    if geprueft:
        return Ergebnis(9, titel, BESTANDEN,
                        [f"Rolle von ${var} wird dekodiert und geprüft"])
    # Gibt es einen Decode auf einer ANDEREN Variable? Dann ist es der Fallback-Zweig.
    anderer = re.search(r"ROLE=[^\n]*\$\{?([A-Z_]+)", s)
    hinweis = (f"; der vorhandene Rollen-Decode bezieht sich auf "
               f"${anderer.group(1)}, nicht auf ${var}" if anderer else "")
    return Ergebnis(
        9, titel, DURCHGEFALLEN,
        [f"{rel(p)} — die Rolle von ${var} wird nicht geprüft{hinweis}. Ein "
         f"service_role-Key dort würde in die ausgelieferte HTML geschrieben"])


# ── Prüfung 10 (nur --live): private Tabellen geben anon keine Zeile ───────

def pruefe_live_rls(aktiv: bool) -> Ergebnis:
    """Der einzige Beleg, der zählt: was ein Besucher tatsächlich bekommt.

    **Nur GET.** Und: „null Zeilen" ist kein Nachweis — eine leere Tabelle sieht
    genauso aus. Erwartet wird deshalb ein Fehlercode (401/403) oder ein
    PostgREST-Fehler, nicht eine leere Liste.
    """
    titel = "Private Tabellen geben anon keine Zeile (live)"
    if not aktiv:
        return Ergebnis(10, titel, UNGEPRUEFT, ["ohne --live nicht gemessen"])
    try:
        import urllib.error
        import urllib.request
    except Exception as e:  # pragma: no cover
        return Ergebnis(10, titel, UNGEPRUEFT, [f"kein urllib: {e}"])

    start = REPO / "landing" / "index.html"
    if not start.is_file():
        return Ergebnis(10, titel, UNGEPRUEFT, ["landing/index.html fehlt"])
    quelle = lies(start)
    url = re.search(r"__SA_SB_URL\s*=\s*'([^']+)'", quelle)
    key = re.search(r"__SA_SB_KEY\s*=\s*'([^']+)'", quelle)
    if not url or not key or url.group(1).startswith("%%"):
        return Ergebnis(10, titel, UNGEPRUEFT,
                        ["Platzhalter statt Zugangsdaten — nur nach "
                         "inject_credentials.sh oder gegen die Live-Seite messbar"])

    basis, schluessel = url.group(1).rstrip("/"), key.group(1)
    offen, ungeprueft = [], []
    for tabelle in sorted(PRIVATE_TABELLEN):
        ziel = f"{basis}/rest/v1/{tabelle}?select=*&limit=1"
        req = urllib.request.Request(
            ziel, headers={"apikey": schluessel,
                           "Authorization": f"Bearer {schluessel}"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                roh = r.read(4000).decode("utf-8", "replace")
                code = r.status
        except urllib.error.HTTPError as e:
            code, roh = e.code, ""
        except Exception as e:
            ungeprueft.append(f"{tabelle}: nicht erreichbar ({type(e).__name__})")
            continue
        if code in (401, 403):
            continue  # erwartet
        if code == 404:
            ungeprueft.append(f"{tabelle}: 404 — Tabelle existiert so nicht")
            continue
        if code == 200:
            # Zeilenzahl, nie Inhalt
            try:
                anzahl = len(json.loads(roh))
            except Exception:
                anzahl = -1
            if anzahl > 0:
                offen.append(f"{tabelle}: HTTP 200 mit {anzahl} Zeile(n) — offen")
            else:
                ungeprueft.append(
                    f"{tabelle}: HTTP 200, aber leer — kein Nachweis "
                    f"(leere Tabelle und offene Rechte sehen gleich aus)")
        else:
            ungeprueft.append(f"{tabelle}: unerwartet HTTP {code}")
    if offen:
        return Ergebnis(10, titel, DURCHGEFALLEN, offen + ungeprueft)
    if ungeprueft:
        return Ergebnis(10, titel, UNGEPRUEFT, ungeprueft)
    return Ergebnis(10, titel, BESTANDEN,
                    [f"{len(PRIVATE_TABELLEN)} private Tabellen: 401/403"])


# ── Lauf ────────────────────────────────────────────────────────────────────

def alle_pruefungen(live: bool) -> list[Ergebnis]:
    return [
        pruefe_policy_to(),
        pruefe_policy_rollen(),
        pruefe_secret_rueckfall(),
        pruefe_workflow_injection(),
        pruefe_tls(),
        pruefe_edge_identitaet(),
        pruefe_personendaten_in_oeffentlichen_tabellen(),
        pruefe_nginx_header(),
        pruefe_key_rolle(),
        pruefe_live_rls(live),
    ]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true",
                    help="zusätzlich Live-Belege holen (nur GET)")
    ap.add_argument("--json", action="store_true", help="maschinenlesbare Ausgabe")
    ap.add_argument("--nur", type=int, action="append",
                    help="nur diese Prüfungsnummer(n) ausführen")
    args = ap.parse_args(argv)

    ergebnisse = alle_pruefungen(args.live)
    if args.nur:
        ergebnisse = [e for e in ergebnisse if e.nummer in args.nur]

    fehler = [e for e in ergebnisse if e.status == DURCHGEFALLEN]
    offen = [e for e in ergebnisse if e.status == UNGEPRUEFT and e.kritisch]

    if args.json:
        print(json.dumps(
            {"pruefungen": [{"nummer": e.nummer, "titel": e.titel,
                             "status": e.status, "details": e.details}
                            for e in ergebnisse],
             "durchgefallen": len(fehler), "ungeprueft": len(offen)},
            ensure_ascii=False, indent=2))
    else:
        print("verify_security.py — Sicherheits-Invarianten")
        print("=" * 72)
        for e in ergebnisse:
            print(e.zeile())
            for d in e.details:
                print(f"         {d}")
        print("=" * 72)
        print(f"{len(ergebnisse)} Prüfungen · {len(fehler)} durchgefallen · "
              f"{len(offen)} ungeprüft")
        if offen:
            print("\nUNGEPRÜFT ist nicht BESTANDEN — diese Invarianten sind offen:")
            for e in offen:
                print(f"  {e.nummer}. {e.titel}")

    if fehler:
        return 1
    if offen:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
