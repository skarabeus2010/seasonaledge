# -*- coding: utf-8 -*-
"""Prüft den Wächter des Briefing-Versands (scripts/verify_briefing_versand.py): baut Fehler in Versandsperre,
Newsletter, Health-Check und Betriebsdateien ein und verlangt Rot an der benannten Prüfung.

    py -3.14 scripts/verify_briefing_versand_mutation.py

Nutzt die isolierte Mechanik von scripts/verify_boersenereignisse_mutation.py (Temp-Kopie, frischer Bytecodepfad,
Projektbaum-Hash vor = nach, Gegenproben); die Kopie bekommt zusätzlich deploy/ und .github/workflows/, weil der
Wächter Timer, Unit, Installer und Workflow prüft. Ein Absturz oder eine abgefangene Ausnahme zählt nicht als gefangen.
"""
from __future__ import annotations

import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scripts import verify_boersenereignisse_mutation as M  # noqa: E402

VS = "shared/versandsperre.py"
DN = "scripts/daily_newsletter.py"
HC = "scripts/daily_health_check.py"
TI = "deploy/systemd/sa-daily-briefing.timer"
SV = "deploy/systemd/sa-daily-briefing.service"
FT = "deploy/systemd/sa-briefing-frist.timer"
EB = "shared/email_brevo.py"
IT = "deploy/install_timers.sh"
WF = ".github/workflows/daily_newsletter.yml"

_kopie_basis = M.isolierte_kopie


def _kopie(ziel):
    _kopie_basis(ziel)
    shutil.copytree(M.WURZEL / "deploy", ziel / "deploy", ignore=shutil.ignore_patterns("__pycache__"))
    (ziel / ".github").mkdir()
    shutil.copytree(M.WURZEL / ".github" / "workflows", ziel / ".github" / "workflows")
    return ziel


M.isolierte_kopie = _kopie
M.WAECHTER = "verify_briefing_versand"
M.MUTATIONEN = [
    # ── Versandsperre ──
    ("abgeschlossener Versand läuft erneut", [(VS, '            if status and status.get("status") == "fertig":\n',
                                                '            if False:\n')], False, "[Versand]"),
    ("Abbruch ohne Wiederaufnahme fortgesetzt", [(VS, '            if status and status.get("status") == "laeuft" and not wiederaufnahme:\n',
                                                  '            if False:\n')], False, "[Versand]"),
    ("Bediente werden nicht übersprungen", [(VS, "        return [e for e in empfaenger if kennung(e) not in self.bedient and kennung(e) not in self.unklar]",
                                             "        return [e for e in empfaenger if kennung(e) not in self.unklar]")], False, "[Versand]"),
    ("Ungeklärte werden erneut versandt", [(VS, "        return [e for e in empfaenger if kennung(e) not in self.bedient and kennung(e) not in self.unklar]",
                                            "        return [e for e in empfaenger if kennung(e) not in self.bedient]")], False, "[Versand]"),
    ("Hash ohne Kleinschreibung", [(VS, "hashlib.sha256(email.strip().lower().encode", "hashlib.sha256(email.strip().encode")],
     False, "[Sperre]"),
    ("Datum nach UTC statt Berlin", [(VS, "        self.datum = jetzt.astimezone(ZONE).date().isoformat()",
                                      "        self.datum = jetzt.date().isoformat()")], False, "[Sperre]"),
    ("naive Zeit angenommen", [(VS, "        if jetzt.tzinfo is None:\n            raise TypeError", "        if False:\n            raise TypeError")],
     False, "[Sperre]"),
    # ── Newsletter ──
    ("Versand wird nicht notiert", [(DN, "            if versand is not None:\n                versand.notieren(email)\n", "")],
     False, "[Versand]"),
    ("offen nicht vor dem Versand markiert", [(DN, "        if versand is not None:\n            versand.beginnen(email)        # VOR dem Versand",
                                               "        if False:\n            versand.beginnen(email)        # VOR dem Versand")],
     False, "[Versand]"),
    ("Ablehnung nicht notiert", [(DN, "            if ergebnis == ABGELEHNT and versand is not None:\n                versand.abgelehnt(email)\n", "")],
     False, "[Versand]"),
    ("Journalfehler als Versandfehler geschluckt", [(DN, "            if versand is not None:\n                versand.notieren(email)\n",
                                                     "            if versand is not None:\n                try:\n                    versand.notieren(email)\n                except OSError:\n                    failed += 1\n")],
     False, "[Versand]"),
    ("Wiederaufnahme ohne Meldung der Ungeklärten", [(DN, "        if versand.unklar_beim_start:\n", "        if False:\n")], False, "[Versand]"),
    ("Abschluss wird nicht gesetzt", [(DN, "        versand.abschliessen(sent, failed)\n", "")], False, "[Versand]"),
    ("schon versandt endet rot", [(DN, '            if e.grund == "schon_versandt":\n                return 0\n', "")],
     False, "[Versand]"),
    ("Testversand als live geloggt", [(DN, '    modus = "einzel" if args.to else ("test" if args.test else "live")',
                                       '    modus = "live"')], False, "[Versand]"),
    ("Abbruch ohne Admin-Alarm", [(DN, '                    send_admin_alert(f"Daily Newsletter: {e} — nicht automatisch wiederholt.")',
                                   "                    pass")], False, "[Versand]"),
    # ── Health-Check ──
    ("Check 5c zählt Testläufe", [(HC, '        rows = [r for r in (resp.data or []) if _newsletter_modus(r) == "live"][:1]',
                                   "        rows = (resp.data or [])[:1]")], False, "[Health]"),
    ("Altzeile nicht als live", [(HC, '.get("modus", "live")', '.get("modus", "alt")')], False, "[Health]"),
    ("Frist erst ab 12 Uhr", [(HC, "    if berlin.weekday() >= 5 or berlin.hour < 10:", "    if berlin.weekday() >= 5 or berlin.hour < 12:")],
     False, "[Health]"),
    ("Frist vergleicht UTC-Datum", [(HC, '            t = _dt.fromisoformat(str(ts).replace("Z", "+00:00")).astimezone(ZoneInfo("Europe/Berlin"))',
                                     '            t = _dt.fromisoformat(str(ts).replace("Z", "+00:00"))')], False, "[Health]"),
    ("alte Ablehnung verdeckt neuen Versuch (Mengen statt Reihenfolge)",
     [(VS, "                        letzter[teil[1]] = teil[0]\n",
       "                        letzter[teil[1]] = \"-\" if letzter.get(teil[1]) == \"-\" else teil[0]\n")], False, "[Versand]"),
    ("unklarer Ausgang als Ablehnung notiert", [(DN, "            if ergebnis == ABGELEHNT and versand is not None:\n",
                                                  "            if versand is not None:\n")], False, "[Versand]"),
    ("Adapter: 5xx als Ablehnung", [(EB, "        return ABGELEHNT if isinstance(status, int) and 400 <= status < 500 else UNKLAR\n",
                                     "        return ABGELEHNT\n")], False, "[Adapter]"),
    ("Adapter: Lese-Timeout als Ablehnung", [(EB, '        print(f"[brevo] REQUEST ERROR (unklar): {e}")\n        return UNKLAR\n',
                                              '        print(f"[brevo] REQUEST ERROR (unklar): {e}")\n        return ABGELEHNT\n')],
     False, "[Adapter]"),
    ("Adapter: 3xx als Annahme", [(EB, "        if not (isinstance(resp.status_code, int) and 200 <= resp.status_code < 300):\n",
                                   "        if False:\n")], False, "[Adapter]"),
    ("Adapter: send_html meldet unklar als Erfolg", [(EB, ") == ANGENOMMEN\n", ") != ABGELEHNT\n")], False, "[Adapter]"),
    ("Frist ohne Live-Zeile wirkungslos", [(HC, '            st = "red" if frist_rot else "yellow"', '            st = "yellow"')], False, "[Health]"),
    ("Fristprüfung ohne Alarm", [(HC, '    alarm("Daily Morning Briefing: bis 10:00', '    (lambda *a: None)("Daily Morning Briefing: bis 10:00')],
     False, "[Health]"),
    ("Fristprüfung vor 10 Uhr", [(FT, "OnCalendar=Mon..Fri *-*-* 10:15:00 Europe/Berlin", "OnCalendar=Mon..Fri *-*-* 09:15:00 Europe/Berlin")],
     False, "[Betrieb]"),
    ("Installer ohne Fristprüfung", [(IT, " sa-briefing-frist.timer)", ")"), (IT, " sa-briefing-frist.service)", ")")], False, "[Betrieb]"),
    ("Frist ohne Wirkung auf den Status", [(HC, "            if frist_rot:\n                status = \"red\"\n", "            if frist_rot:\n                pass\n")],
     False, "[Health]"),
    # ── Betrieb ──
    ("Timer in UTC", [(TI, "OnCalendar=Mon..Fri *-*-* 07:30:00 Europe/Berlin", "OnCalendar=Mon..Fri *-*-* 05:30:00")], False, "[Betrieb]"),
    ("Timeout nur außen", [(SV, "seasonalpha-app timeout --kill-after=30s 15m python3", "seasonalpha-app python3")], False, "[Betrieb]"),
    ("Exit 75 als Fehler", [(SV, "SuccessExitStatus=75\n", "")], False, "[Betrieb]"),
    ("Installer ohne Briefing-Timer", [(IT, " sa-daily-briefing.timer sa-briefing-frist.timer)", " sa-briefing-frist.timer)"),
                                       (IT, " sa-daily-briefing.service sa-briefing-frist.service)", " sa-briefing-frist.service)"),
                                       (IT, "(sa-nightly, sa-daily-briefing)", "(sa-nightly)")], False, "[Betrieb]"),
    ("GitHub-Zeitplan zurück", [(WF, "  workflow_dispatch:\n", "  schedule:\n    - cron: '0 6 * * 1-5'\n  workflow_dispatch:\n")],
     False, "[Betrieb]"),
]
M.UNGUELTIG_ERWARTET = [
    ("Absturz im Health-Helfer (abgefangen)", [(HC, '    """Modus eines daily_newsletter-Eintrags aus missing_details (seit 2026-10-12); Altzeilen ohne Modus = live."""\n',
                                                 '    """Modus eines daily_newsletter-Eintrags aus missing_details (seit 2026-10-12); Altzeilen ohne Modus = live."""\n'
                                                 '    raise RuntimeError("Absturz-Gegenprobe")\n')], False),
    ("Anker existiert nicht", [(VS, "diese Zeile gibt es nicht", "egal")], False),
    ("Absturz: Versandsperre nicht importierbar", [(VS, "ZONE = ZoneInfo(", "ZONE = ZoneInfo((")], False),
]

if __name__ == "__main__":
    sys.exit(M.main())
