#!/usr/bin/env python3
"""
verify_docs.py — hält die Dokumentation sauber und das öffentliche Repo frei von
Betriebsdetails.

    py -3.14 scripts/verify_docs.py            # alle Prüfungen
    py -3.14 scripts/verify_docs.py --json      # maschinenlesbar
    py -3.14 scripts/verify_docs.py --nur 3     # nur eine Prüfung

**Warum dieses Skript keine Suchwerte enthält.** Eine Prüfung, die die Server-Adresse
als Literal sucht, trägt sie selbst wieder ins öffentliche Repo — der Wächter wäre dann
die Lücke. Geprüft werden deshalb **Formen**: eine öffentliche IPv4, ein
Supabase-Projekt-Host, ein Versand-Key-Präfix mit Nutzlast. Das leckt nichts und ist
strenger als eine Werteliste, weil es auch eine **neue** Adresse fängt.

Drei Ergebnisse, wie in `verify_security.py`:
BESTANDEN / DURCHGEFALLEN / **UNGEPRÜFT** — und ungeprüft ist niemals bestanden.
Exit 0 alles grün, 1 mindestens ein Fehler, 2 nur Ungeprüfte übrig.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

BESTANDEN = "BESTANDEN"
DURCHGEFALLEN = "DURCHGEFALLEN"
UNGEPRUEFT = "UNGEPRÜFT"


def setze_repo(pfad: Path) -> None:
    """Richtet die Prüfungen auf einen anderen Baum — nur für den Mutationstest."""
    global REPO
    REPO = Path(pfad).resolve()


# ── Soll-Manifest ───────────────────────────────────────────────────────────

# Obergrenze für die Einstiegsdatei. Der Sinn ist nicht Schönheit: CLAUDE.md wuchs von
# Version 39 auf 66 auf 140 KB, weil jede Sitzung oben einen Absatz anhängte und
# niemand je einen entfernte. Eine Grenze erzwingt die Entscheidung „wer etwas
# hinzufügt, nimmt etwas heraus".
MAX_ZEILEN = {
    "AGENTS.md": 260,
    "CLAUDE.md": 80,
}

# Verzeichnisse, die geprüft werden. `.claude/worktrees` ist bewusst draußen —
# das sind alte Arbeitskopien, keine gültige Doku.
SUCHE_IN = ("*.md", "docs/**/*.md", ".claude/agents/*.md", ".claude/skills/**/*.md")

# Eigenes Verzeichnis plus die geplante neutrale Infrastruktur-Ebene. Alles
# andere unter /opt gehört einem anderen Projekt.
EIGENE_OPT = ("seasonaledge", "infra")


@dataclass
class Ergebnis:
    nummer: int
    titel: str
    status: str
    details: list[str] = field(default_factory=list)

    def zeile(self) -> str:
        z = {BESTANDEN: "OK  ", DURCHGEFALLEN: "FEHL", UNGEPRUEFT: "?   "}[self.status]
        return f"[{z}] {self.nummer}. {self.titel}"


def getrackte_dateien() -> list[Path] | None:
    """Nur was WIRKLICH im Repo liegt. Untrackte Dateien sind nicht veröffentlicht."""
    try:
        r = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True,
                           text=True, timeout=60)
        if r.returncode != 0:
            return None
        return [REPO / z for z in r.stdout.splitlines() if z.strip()]
    except Exception:
        return None


def lies(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(p)


def zeilennummer(s: str, pos: int) -> int:
    return s.count("\n", 0, pos) + 1


# ── Prüfung 1: keine öffentliche IPv4 in getrackten Dateien ────────────────

IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
# Beispiel- und Doku-Adressen sind erlaubt, ebenso Versionsnummern-artige Treffer.
# Version-artige Treffer sind keine Adressen. Der häufigste Fall sind
# User-Agent-Strings („Chrome/120.0.0.0") — die erfüllen die IPv4-Form, und mein
# erster Entwurf meldete vier davon als Befund.
IP_ERLAUBT_TEXT = re.compile(
    r"(?i)beispiel|example|version|Mozilla|Chrome|Safari|AppleWebKit|Gecko|"
    r"User-Agent|\bv?\d+\.\d+\.\d+\.\d+-")
# Direkt nach einem Schrägstrich steht eine Programmversion, keine Adresse.
IP_NACH_SLASH = re.compile(r"[A-Za-z]/$")


def _ist_oeffentlich(text: str) -> bool:
    try:
        a = ipaddress.ip_address(text)
    except ValueError:
        return False
    return a.is_global and not a.is_multicast


def pruefe_keine_ip() -> Ergebnis:
    """Eine öffentliche IPv4 in einem öffentlichen Repo ist eine Zieladresse.

    Private Bereiche (10/8, 172.16/12, 192.168/16), Loopback und
    Dokumentationsnetze bleiben erlaubt — die sagen niemandem etwas.
    """
    titel = "Keine öffentliche IP-Adresse in getrackten Dateien"
    dateien = getrackte_dateien()
    if dateien is None:
        return Ergebnis(1, titel, UNGEPRUEFT, ["git ls-files nicht ausführbar"])
    treffer = []
    for p in dateien:
        if p.suffix not in (".md", ".py", ".js", ".json", ".yml", ".yaml", ".sh",
                            ".conf", ".j2", ".html", ".txt", ".sql", ".ts"):
            continue
        if not p.is_file():
            continue
        s = lies(p)
        for m in IPV4.finditer(s):
            if not _ist_oeffentlich(m.group(0)):
                continue
            anfang = s.rfind("\n", 0, m.start()) + 1
            ende = s.find("\n", m.end())
            zeile = s[anfang:ende if ende > 0 else len(s)]
            if IP_ERLAUBT_TEXT.search(zeile):
                continue
            if IP_NACH_SLASH.search(s[max(0, m.start() - 12):m.start()]):
                continue
            treffer.append(f"{rel(p)}:{zeilennummer(s, m.start())}")
    if treffer:
        return Ergebnis(1, titel, DURCHGEFALLEN, sorted(set(treffer)))
    return Ergebnis(1, titel, BESTANDEN, [f"{len(dateien)} getrackte Dateien geprüft"])


# ── Prüfung 2: kein Projekt-Host und kein Key-Präfix ───────────────────────

# Formen, nicht Werte: ein Supabase-Projekt-Host ist 20 Kleinbuchstaben vor
# `.supabase.co`; ein Brevo-Key beginnt mit `xkeysib-` und trägt Nutzlast.
FORMEN = (
    (re.compile(r"\b[a-z]{18,24}\.supabase\.co"), "Supabase-Projekt-Host"),
    (re.compile(r"xkeysib-(?![<A-Z])[A-Za-z0-9]{6,}"), "Versand-Key mit Nutzlast"),
    (re.compile(r"/opt/(?!(?:" + "|".join(EIGENE_OPT) + r")\b)[a-z][a-z0-9_-]{2,}"),
     "fremdes Server-Verzeichnis"),
    # Zwischen `ssh` und `root@` stehen beliebige Tokens, nicht nur Schalter:
    # `ssh -i ~/.ssh/key root@host`. Mein erster Entwurf erlaubte dort nur
    # `-…`-Argumente und übersah deshalb genau die übliche Form — der
    # Mutationstest hat es gemeldet.
    # Platzhalter sind erlaubt, auch HTML-maskiert (`root@&lt;VPS&gt;`).
    (re.compile(r"(?i)\bssh\s+(?:[-~/\w.=:]+\s+){0,4}root@(?!<|&lt;)[\w.-]+"),
     "SSH-Zugang mit konkretem Ziel"),
)


def pruefe_formen() -> Ergebnis:
    """Projekt-Host, Key mit Nutzlast, fremde Serverpfade, konkrete SSH-Ziele.

    Platzhalter in spitzen Klammern sind ausdrücklich erlaubt — sie sind der
    gewünschte Zustand.
    """
    titel = "Keine Betriebsdetails (Projekt-Host, Key, fremde Pfade, SSH-Ziel)"
    dateien = getrackte_dateien()
    if dateien is None:
        return Ergebnis(2, titel, UNGEPRUEFT, ["git ls-files nicht ausführbar"])
    treffer = []
    for p in dateien:
        if p.suffix not in (".md", ".py", ".js", ".json", ".yml", ".yaml", ".sh",
                            ".conf", ".j2", ".html", ".txt", ".sql", ".ts"):
            continue
        if not p.is_file():
            continue
        s = lies(p)
        for rx, was in FORMEN:
            for m in rx.finditer(s):
                treffer.append(f"{rel(p)}:{zeilennummer(s, m.start())} — {was}")
    if treffer:
        return Ergebnis(2, titel, DURCHGEFALLEN, sorted(set(treffer)))
    return Ergebnis(2, titel, BESTANDEN)


# ── Prüfung 3: kein Verweis zeigt ins Leere ────────────────────────────────

LINK = re.compile(r"\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")


def pruefe_verweise() -> Ergebnis:
    """Ein gebrochener Verweis fällt nie auf — die Seite lädt, sie springt nur nicht.

    Geprüft werden nur **relative** Ziele auf Dateien im Repo. Externe URLs,
    Anker ohne Datei und absolute Pfade bleiben außen vor.
    """
    titel = "Kein Markdown-Verweis zeigt ins Leere"
    quellen = []
    for muster in ("*.md", "docs/**/*.md", ".claude/agents/*.md"):
        quellen.extend(p for p in REPO.glob(muster)
                       if p.is_file() and "worktrees" not in p.parts)
    if not quellen:
        return Ergebnis(3, titel, UNGEPRUEFT, ["keine Markdown-Dateien gefunden"])
    treffer = []
    for p in quellen:
        s = lies(p)
        for m in LINK.finditer(s):
            ziel = m.group(1)
            if re.match(r"(?i)^(https?:|mailto:|tel:|data:|/|[A-Z]:[\\/])", ziel):
                continue
            # Ein Linkziel sieht wie ein Pfad aus. Ohne diese Schranke matcht die
            # Regex Code wie `_loaders['indicator-filters'](filters)` als Link —
            # genau das meldete der erste Lauf.
            if "." not in ziel and "/" not in ziel:
                continue
            # Platzhalter in Vorlagen (`<slug>/datei.png`) sind kein Defekt.
            if "<" in ziel or ">" in ziel:
                continue
            if not (p.parent / ziel).exists():
                treffer.append(f"{rel(p)}:{zeilennummer(s, m.start())} → {ziel}")
    if treffer:
        return Ergebnis(3, titel, DURCHGEFALLEN, sorted(set(treffer)))
    return Ergebnis(3, titel, BESTANDEN, [f"{len(quellen)} Dateien geprüft"])


# ── Prüfung 4: die Einstiegsdateien bleiben unter ihrer Grenze ─────────────

def pruefe_groesse() -> Ergebnis:
    """Gegen die Inflation, die CLAUDE.md auf 140 KB gebracht hat.

    Fehlt eine Datei, ist das UNGEPRÜFT und nicht bestanden — sonst wäre die
    Prüfung grün, solange es die Datei gar nicht gibt.
    """
    titel = "Einstiegsdateien unter ihrer Zeilengrenze"
    treffer, offen = [], []
    for name, grenze in MAX_ZEILEN.items():
        p = REPO / name
        if not p.is_file():
            offen.append(f"{name} existiert nicht (Grenze {grenze})")
            continue
        n = len(lies(p).splitlines())
        if n > grenze:
            treffer.append(f"{name}: {n} Zeilen, erlaubt {grenze} — "
                           f"wer etwas hinzufügt, nimmt etwas heraus")
        else:
            offen.append(None)
    if treffer:
        return Ergebnis(4, titel, DURCHGEFALLEN, treffer)
    fehlend = [o for o in offen if o]
    if fehlend:
        return Ergebnis(4, titel, UNGEPRUEFT, fehlend)
    return Ergebnis(4, titel, BESTANDEN,
                    [f"{n}: ≤ {g} Zeilen" for n, g in MAX_ZEILEN.items()])


# ── Lauf ────────────────────────────────────────────────────────────────────

def alle_pruefungen() -> list[Ergebnis]:
    return [pruefe_keine_ip(), pruefe_formen(), pruefe_verweise(), pruefe_groesse()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--nur", type=int, action="append")
    args = ap.parse_args(argv)

    ergebnisse = alle_pruefungen()
    if args.nur:
        ergebnisse = [e for e in ergebnisse if e.nummer in args.nur]

    fehler = [e for e in ergebnisse if e.status == DURCHGEFALLEN]
    offen = [e for e in ergebnisse if e.status == UNGEPRUEFT]

    if args.json:
        print(json.dumps({"pruefungen": [e.__dict__ for e in ergebnisse],
                          "durchgefallen": len(fehler), "ungeprueft": len(offen)},
                         ensure_ascii=False, indent=2, default=str))
    else:
        print("verify_docs.py — Dokumentation und öffentliches Repo")
        print("=" * 72)
        for e in ergebnisse:
            print(e.zeile())
            for d in e.details:
                print(f"         {d}")
        print("=" * 72)
        print(f"{len(ergebnisse)} Prüfungen · {len(fehler)} durchgefallen · "
              f"{len(offen)} ungeprüft")
        if offen:
            print("\nUNGEPRÜFT ist nicht BESTANDEN:")
            for e in offen:
                print(f"  {e.nummer}. {e.titel}")

    return 1 if fehler else (2 if offen else 0)


if __name__ == "__main__":
    sys.exit(main())
