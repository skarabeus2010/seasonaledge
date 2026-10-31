#!/usr/bin/env python3
"""verify_drawdown_mutation.py — prüft verify_drawdown.py.

Baut bekannte Defekte in shared/drawdown.py, landing/js/drawdown-compute.js und landing/pages/drawdown.html
absichtlich ein und verlangt Rot AN DER BENANNTEN PRÜFUNG, mit vollständigem Lauf. Mechanik aus
verify_twins_mutation (atomares Schreiben, exklusiver Lauf, frischer Bytecode-Pfad, Wiederherstellung geprüft).
Exit des Wächters: 0 grün, 1 rot (= erkannt), 3 Absturz (= ungültig, eine Ausnahme ist kein Nachweis).
Kern-Mutationen laufen ohne jsdom (--ohne-seite), Seiten-Mutationen mit.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from scripts.verify_twins_mutation import (_atomar_schreiben, _exklusiver_lauf,  # noqa: E402
                                           _zeilenende, python_probe, LF)

_WAECHTER = _ROOT / "scripts" / "verify_drawdown.py"
P = "shared/drawdown.py"
J = "landing/js/drawdown-compute.js"
H = "landing/pages/drawdown.html"

# (Name, Datei, [(alt, neu)], Teilstring der Prüfung, die reißen muss, mit Seite?)
MUTATIONEN = [
    # ── Python-Kern ──
    ("Recovery nur bei neuem Hoch (> statt ≥)", P, [("        if idx[i] >= idx[peak] * (1 - EPS):", "        if idx[i] > idx[peak]:")], "[A] A1 zwei Episoden (Python)", False),
    ("Trough bei Gleichstand der spätere", P, [('            elif d < ep["tiefe"] - EPS:', '            elif d <= ep["tiefe"]:')], "[A] A2 Gleichstand am Trough (Python)", False),
    ("Stichtag schließt heute ein", P, [('    return _iso(SZ.vorherige(heute, boerse, einschliesslich=False))', '    return _iso(SZ.vorherige(heute, boerse, einschliesslich=True))')], "[E] Python NYSE 2026-10-30T22:00:00Z", False),
    ("Brücke ohne Konsistenzprüfung", P, [("        return abs(t - math.log(cn / cv)) <= BRUECKE_TOL\n", "        return True\n")], "[A] A7 Brücke verletzt (Python)", False),
    # NICHT „Krypto-Ausnahme entfernt“: äquivalent — CRYPTO hat Kalenderstatus `konvention` und scheitert schon an der
    # Statusprüfung; die ausdrückliche Sperre ist eine zweite Linie (Mutationstest 2026-10-31, unbemerkt = äquivalent).
    ("belegtes Jahr überbrückt", P, [('''        if boerse != "FOREX" and any(kalender_status(boerse, int(x[:4])) not in ("ungeprueft", "annahme") for x in fehl):\n            return False\n''', "")], "[A] A4 Lücke belegtes Jahr (Python)", False),
    ("fehlende Endzeilen still", P, [('            aus["ende_fehlt"] = True\n', '            pass\n')], "[A] A9 Reihenende fehlt (Python)", False),
    ("Tempo gegen das ganze Alter", P, [('        lauf_tempo = None if c is None else c - ep["p"]\n', '        lauf_tempo = None if c is None else res["laufend"]["seit_peak"]\n')], "[A] A11 Tempo = erster Übertritt (Python)", False),
    ("Greenwood ohne (n − d)", P, [('                var_sum += d / (n_risk * (n_risk - d))\n', '                var_sum += d / (n_risk * n_risk)\n')], "[A] A10 Kaplan-Meier Handfall (Greenwood, log-log) (Python)", False),
    ("KM ohne Zensierung im Risikosatz", P, [('        n_risk -= d + c\n        i += d + c\n', '        n_risk -= d\n        i += d + c\n')], "[A] A10 Kaplan-Meier Handfall (Greenwood, log-log) (Python)", False),
    ("Quantil mit Floor statt Interpolation", P, [('    return s[lo] + (s[hi] - s[lo]) * (pos - lo)\n\n\ndef _iso', '    return s[lo]\n\n\ndef _iso')], "[B] qqq Zeitraum 10 MaxDD 5: Episoden/Quartile = Referenz", False),
    ("Ulcer ohne Wurzel", P, [('            z["ulcer"] = math.sqrt(sum(x * x for x in d) / len(d))\n', '            z["ulcer"] = sum(x * x for x in d) / len(d)\n')], "[A] A12 Kalender mit Vorjahreshoch (Python)", False),
    ("Recovery ohne Toleranz", P, [("        if idx[i] >= idx[peak] * (1 - EPS):", "        if idx[i] >= idx[peak]:")], "[A] A13 Recovery trotz Rundungsrest (Python)", False),
    ("Überlappende Paare über das doppelte Fenster", P, [("                        if abs(gueltig[i] - gueltig[j]) < h)", "                        if abs(gueltig[i] - gueltig[j]) < 2 * h)")], "Forward 60 HT = Referenz", False),
    ("Periodenübergreifend ohne Toleranz", P, [('and e["tiefe"] <= -0.05 + EPS]', 'and e["tiefe"] <= -0.05]')], "[A] A14 periodenübergreifend trotz Rundungsrest (Python)", False),
    ("Forward ohne Zinseszins (Summe der log-Renditen)", P, [("            mn = min(mn, math.exp(kum) - 1)\n        return math.exp(kum) - 1, mn", "            mn = min(mn, math.exp(kum) - 1)\n        return kum, mn")], "Forward 60 HT = Referenz", False),
    ("Positivquote ohne Toleranz", P, [('"anteil_positiv": sum(1 for w in v if w[0] > EPS) / len(v),', '"anteil_positiv": sum(1 for w in v if w[0] > 0) / len(v),')], "[A] A15 Nullrendite nicht positiv (Python)", False),
    ("Positivquote mit zu grober Toleranz", P, [('"anteil_positiv": sum(1 for w in v if w[0] > EPS) / len(v),', '"anteil_positiv": sum(1 for w in v if w[0] > 1e-9) / len(v),')], "[A] A16 Kleinstrendite positiv (Python)", False),
    # ── JS-Kern (fällt im Zwillingsvergleich auf) ──
    ("JS: Recovery nur bei neuem Hoch", J, [("      if (idx[i] >= idx[peak] * (1 - EPS)) {", "      if (idx[i] > idx[peak]) {")], "[C] UTC A1 zwei Episoden: Python = JS", False),
    ("JS: periodenübergreifend ohne Toleranz", J, [("&& e.tiefe <= -0.05 + EPS;", "&& e.tiefe <= -0.05;")], "[A] A14 periodenübergreifend trotz Rundungsrest (JS UTC)", False),
    ("JS: Positivquote ohne Toleranz", J, [("anteil_positiv: v.filter(function (w) { return w[0] > EPS; })", "anteil_positiv: v.filter(function (w) { return w[0] > 0; })")], "[A] A15 Nullrendite nicht positiv (JS)", False),
    ("JS: Positivquote mit zu grober Toleranz", J, [("anteil_positiv: v.filter(function (w) { return w[0] > EPS; })", "anteil_positiv: v.filter(function (w) { return w[0] > 1e-9; })")], "[A] A16 Kleinstrendite positiv (JS)", False),
    ("JS: Toleranz an der Schwelle fehlt", J, [("  var EPS = 1e-12;\n", "  var EPS = 0;\n")], "[C] UTC A3 laufend: Python = JS", False),
    ("JS: Forward-Fenster eine Sitzung zu lang", J, [("      if (i + h > letzt) return null;\n", "      if (i + h >= letzt) return null;\n")], "[C] UTC C qqq: Python = JS", False),
    ("JS: Phantomzeilen-Rendite ignoriert", J, [("      for (var q = vRow + 1; q <= nRow; q++) { var x = z[q].log_return; if (!endlich(x)) return null; t += x; }",
                                                "      for (var q = nRow; q <= nRow; q++) { var x = z[q].log_return; if (!endlich(x)) return null; t += x; }")], "[C] UTC C gdaxi: Python = JS", False),   # echte Phantomzeilen im DAX

    ("JS: Krypto ohne Zeitzone (heute mit lokalem Datum)", J, [("    var h = K().heute(boerse, jetzt);\n    return K().vorherige(h.datum, boerse, false);",
                                                               "    var d = new Date(jetzt), h = { datum: d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0') };\n    return K().vorherige(h.datum, boerse, false);")], "[E] JS America/Los_Angeles", False),
    ("JS: Schalttag immer auf den 28.", J, [("    if (m === '02' && t === '29' && !schalt) t = '28';", "    if (m === '02' && t === '29') t = '28';")], "minusJahre mit Schalttag", False),
    # ── Seite ──
    ("Seite: überholte Antwort wird angezeigt", H, [("        if (nr !== _anfrage) return;                      // überholte Antwort (schneller Tickerwechsel)\n", "")], "[F] wechsel: Lücke erkannt", True),
    ("Seite: Fehler lässt alte Tabelle stehen", H, [("        _res = null; _ticker = ticker; ergebnisseLeeren();", "        _res = null; _ticker = ticker;")], "[F] fehler_nach_erfolg", True),
    ("Seite: Historie ab 2000 statt voll", H, [("{ felder: ['date', 'close', 'log_return'], ab: null }", "{ felder: ['date', 'close', 'log_return'], ab: '2000-01-01' }")], "[F] normal: volle Historie angefordert", True),
    ("Seite: zu kurze Historie lässt alte Ergebnisse stehen", H, [("      if (r.status === 'zu_wenig_daten') { ergebnisseLeeren();", "      if (r.status === 'zu_wenig_daten') {")], "[F] kurz_nach_erfolg", True),
    ("Seite: n = 0 zeigt „0 von 0“", H, [("      if (G.laufend_erfuellt && !G.n) {", "      if (false) {")], "[F] n0", True),
    ("Seite: Kurzantwort zeigt „0 von 0“", H, [("      } else if (!g5.n) {", "      } else if (false) {")], "[F] n0: Kurzantwort", True),
    ("Seite: Schwelle ohne Toleranz", H, [("      if (!g5.laufend_erfuellt) {", "      if (-r.d_heute < 5) {")], "[F] schwelle", True),
    ("Seite: Vorzeichen aus ungerundetem Wert", H, [("var s = nullGerundet(v, d) ? '' : v > 0 ? '+' : '−';", "var s = v > 0 ? '+' : v < 0 ? '−' : '';")], "[F] null: gerundet 0,00 % ohne Vorzeichen und nicht rot", True),
    ("Seite: Zwischenverlust immer rot", H, [("'</td><td' + negKl(e ? e.zwischenverlust_mittel : null) + '>'", "'</td><td class=\"neg\">'")], "[F] null: gerundet 0,00 % ohne Vorzeichen und nicht rot", True),
    ("Seite: Rang aus falscher Gruppe (MaxDD 10 statt Auswahl)", H, [("      var G = SA.drawdown.gruppe(r, start, wahl.m), V", "      var G = SA.drawdown.gruppe(r, start, 10), V")], "[F] normal: Kachel Rang Dauer/Tiefe = Kern", True),
]


def _anwenden(original: bytes, paare, nr: int, name: str):
    le = _zeilenende(original)
    neu = original
    for such, ersatz in paare:
        s = such.encode("utf-8").replace(LF, le)
        e = ersatz.encode("utf-8").replace(LF, le)
        if neu.count(s) != 1:
            print(f"{nr:>2}. [UNGUELTIG] {name} — Anker {neu.count(s)}x: {such[:70]!r}")
            return None
        neu = neu.replace(s, e, 1)
    return neu


def _umfang(ausgabe: str) -> int:
    m = re.findall(r"^verify_drawdown: (?:BESTANDEN|DURCHGEFALLEN) \((\d+) Prüfungen\)$", ausgabe or "", re.M)
    return int(m[-1]) if m else -1


def main() -> int:
    unbemerkt, ungueltig = [], []
    with _exklusiver_lauf():
        umfang0 = {}
        for seite in (False, True):
            arg = [] if seite else ["--ohne-seite"]
            r0 = python_probe([_WAECHTER] + arg, capture_output=True, text=True, cwd=str(_ROOT))
            if r0.returncode != 0:
                print("[FAIL] Wächter ist schon ohne Mutation rot (Exit %d, Seite=%s):\n%s" % (r0.returncode, seite, (r0.stdout or "")[-2500:]))
                return 1
            umfang0[seite] = _umfang(r0.stdout)
            print("Ausgangslauf %s: %d Prüfungen." % ("mit Seite" if seite else "ohne Seite", umfang0[seite]))

        for nr, (name, datei, paare, pruefung, seite) in enumerate(MUTATIONEN, 1):
            pfad = _ROOT / datei
            original = pfad.read_bytes()
            neu = _anwenden(original, paare, nr, name)
            if neu is None:
                ungueltig.append(name)
                continue
            arg = [] if seite else ["--ohne-seite"]
            try:
                _atomar_schreiben(pfad, neu)
                r = python_probe([_WAECHTER] + arg, capture_output=True, text=True, cwd=str(_ROOT))
            finally:
                _atomar_schreiben(pfad, original)
                assert pfad.read_bytes() == original, f"{datei} nicht wiederhergestellt"
            if r.returncode == 3:
                print(f"{nr:>2}. [Absturz]   {name} — kein Nachweis")
                ungueltig.append(name)
                continue
            if r.returncode != 1:
                print(f"{nr:>2}. [UNBEMERKT] {name} (Exit {r.returncode})")
                unbemerkt.append(name)
                continue
            if _umfang(r.stdout) < umfang0[seite]:
                print(f"{nr:>2}. [UNGUELTIG] {name} — Lauf unvollständig ({_umfang(r.stdout)} < {umfang0[seite]})")
                ungueltig.append(name)
                continue
            fehl = [z for z in (r.stdout or "").splitlines() if z.startswith("FEHL ")]
            if not any(pruefung in z for z in fehl):
                print(f"{nr:>2}. [FALSCHE PRÜFUNG] {name} — erwartet „{pruefung}“, rot: {[z[:90] for z in fehl[:3]]}")
                unbemerkt.append(name)
                continue
            print(f"{nr:>2}. [erkannt]   {name}  ->  {pruefung}")
    print()
    if unbemerkt or ungueltig:
        print(f"[FAIL] unbemerkt/falsch: {len(unbemerkt)}, ungültig: {len(ungueltig)}")
        return 1
    print(f"[OK] Alle {len(MUTATIONEN)} Mutationen an der benannten Prüfung erkannt.")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
