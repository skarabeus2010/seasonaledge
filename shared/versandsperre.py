"""Versandsperre für den Live-Versand des Daily Morning Briefings (Codex-Prüfung der Timer-Umstellung 2026-10-12,
docs/review_prompts/2026-10-12_briefing_timer.md).

Ein Live-Versand je Berliner Datum:
- ein zweiter, GLEICHZEITIGER Live-Lauf scheitert sofort an einer exklusiven Dateisperre (`parallel`);
- ist der Versand des Tages abgeschlossen, endet ein weiterer Lauf ohne Versand (`schon_versandt`, Exit 0 im Aufrufer —
  ein doppelt ausgelöster Timer oder Notauslöser schadet nicht);
- wurde ein Versand abgebrochen (Deploy, Absturz, Kill), wird NICHT blind wiederholt (`abgebrochen`): nur mit
  ausdrücklicher Wiederaufnahme, und dann ohne die schon bedienten Empfänger.
Empfänger stehen nur als Hash (SHA-256 der kleingeschriebenen Adresse, 16 Hex) in `logs/versand/` — keine Adressen.
Test-, Einzel- und Trockenläufe nutzen die Sperre nicht.

Journal in zwei Stufen (Codex R2): VOR dem Versand `? <hash>` (offen), danach `+ <hash>` (angenommen) oder
`- <hash>` (eindeutig nicht versandt). Endet der Lauf zwischen Annahme und Eintrag, bleibt der Empfänger `?` =
ungeklärt; eine Wiederaufnahme überspringt ihn (lieber eine Mail zu wenig als eine doppelt) und meldet ihn. Ein
Schreibfehler im Journal ist KEIN Versandfehler — die Ausnahme läuft durch und beendet den Lauf.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    import fcntl
except ImportError:   # Windows (lokale Entwicklung): keine Sperre; der Wächter prüft die Logik unter Linux UND die Abfolge
    fcntl = None

ZONE = ZoneInfo("Europe/Berlin")
ZEICHEN = {"?": "offen", "+": "angenommen", "-": "nicht_versandt"}


class VersandGesperrt(Exception):
    """Live-Versand darf nicht starten. `grund` ∈ {parallel, schon_versandt, abgebrochen}."""

    def __init__(self, grund: str, text: str):
        super().__init__(text)
        self.grund = grund


def verzeichnis() -> pathlib.Path:
    """`<Projekt>/logs/versand` — im Container /app/logs/versand (gemountet), auf dem Host /opt/seasonaledge/logs/…"""
    return pathlib.Path(os.environ.get("SA_VERSAND_VERZ") or
                        pathlib.Path(__file__).resolve().parent.parent / "logs" / "versand")


def kennung(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()[:16]


def _atomar(pfad: pathlib.Path, daten: dict) -> None:
    tmp = pfad.with_suffix(pfad.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(daten, fh, ensure_ascii=False)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, pfad)


class Versand:
    """Kontext eines Live-Versands. `uebrige(empfaenger)` filtert angenommene und ungeklärte; je Empfänger
    `beginnen()` VOR dem Versand, danach `notieren()` (angenommen) oder `abgelehnt()` (eindeutig nicht versandt);
    `abschliessen(...)` setzt den Status `fertig`."""

    def __init__(self, name: str, *, wiederaufnahme: bool = False, jetzt: datetime | None = None):
        if type(wiederaufnahme) is not bool:
            raise TypeError("wiederaufnahme muss True/False sein")
        jetzt = jetzt or datetime.now(ZONE)
        if jetzt.tzinfo is None:
            raise TypeError("jetzt braucht eine Zeitzone")
        self.datum = jetzt.astimezone(ZONE).date().isoformat()
        verz = verzeichnis()
        verz.mkdir(parents=True, exist_ok=True)
        stamm = verz / ("%s_%s" % (name, self.datum))
        self._status = stamm.with_suffix(".json")
        self._gesendet = stamm.with_suffix(".gesendet")
        self._lockfd = os.open(stamm.with_suffix(".lock"), os.O_RDWR | os.O_CREAT, 0o644)
        try:
            if fcntl is not None:
                try:
                    fcntl.flock(self._lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise VersandGesperrt("parallel", "Ein Live-Versand für %s läuft bereits" % self.datum)
            status = json.loads(self._status.read_text(encoding="utf-8")) if self._status.exists() else None
            if status and status.get("status") == "fertig":
                raise VersandGesperrt("schon_versandt", "Live-Versand für %s ist bereits abgeschlossen" % self.datum)
            if status and status.get("status") == "laeuft" and not wiederaufnahme:
                raise VersandGesperrt("abgebrochen", "Live-Versand für %s wurde abgebrochen — Wiederaufnahme nur "
                                                     "ausdrücklich (--wiederaufnahme)" % self.datum)
            # Chronologisch auswerten (Codex R3): der LETZTE Eintrag je Empfänger gilt — eine alte Ablehnung darf
            # einen späteren, ungeklärten Versuch nicht verdecken (`? - ?` = ungeklärt). Ein `+` gilt für immer.
            letzter: dict[str, str] = {}
            self.bedient = set()
            if self._gesendet.exists():
                for zeile in self._gesendet.read_text(encoding="utf-8").splitlines():
                    teil = zeile.split()
                    if len(teil) == 2 and teil[0] in ZEICHEN:
                        letzter[teil[1]] = teil[0]
                        if teil[0] == "+":
                            self.bedient.add(teil[1])
            # ungeklärt: letzter Eintrag "offen" und nie angenommen
            self.unklar = {k for k, z in letzter.items() if z == "?" and k not in self.bedient}
            self.unklar_beim_start = len(self.unklar)
            _atomar(self._status, {"status": "laeuft", "datum": self.datum,
                                   "wiederaufnahme": bool(status), "begonnen": datetime.now(ZONE).isoformat()})
            self._fh = open(self._gesendet, "a", encoding="utf-8")
        except BaseException:
            os.close(self._lockfd)
            raise

    def uebrige(self, empfaenger: list[str]) -> list[str]:
        """Empfänger ohne die angenommenen UND ohne die ungeklärten (die bekommen keine zweite Mail)."""
        return [e for e in empfaenger if kennung(e) not in self.bedient and kennung(e) not in self.unklar]

    def _eintrag(self, zeichen: str, email: str) -> str:
        k = kennung(email)
        self._fh.write("%s %s\n" % (zeichen, k))
        self._fh.flush()
        os.fsync(self._fh.fileno())
        return k

    def beginnen(self, email: str) -> None:
        """VOR dem Versand: Empfänger als offen markieren (dauerhaft auf Platte)."""
        self.unklar.add(self._eintrag("?", email))

    def notieren(self, email: str) -> None:
        """Nach der Annahme durch den Mailanbieter."""
        k = self._eintrag("+", email)
        self.bedient.add(k)
        self.unklar.discard(k)

    def abgelehnt(self, email: str) -> None:
        """Eindeutig NICHT versandt (Anbieter lehnt ab, Mail ließ sich nicht bauen) — darf erneut versucht werden."""
        self.unklar.discard(self._eintrag("-", email))

    def abschliessen(self, gesendet: int, fehlgeschlagen: int) -> None:
        _atomar(self._status, {"status": "fertig", "datum": self.datum, "gesendet": gesendet,
                               "fehlgeschlagen": fehlgeschlagen, "bedient_gesamt": len(self.bedient),
                               "ungeklaert": len(self.unklar), "fertig": datetime.now(ZONE).isoformat()})

    def schliessen(self) -> None:
        try:
            self._fh.close()
        finally:
            os.close(self._lockfd)
