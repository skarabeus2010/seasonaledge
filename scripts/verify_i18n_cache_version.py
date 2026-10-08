# -*- coding: utf-8 -*-
"""Prueft, dass eine inhaltliche Aenderung an den Woerterbuechern die
Cache-Kennung erhoeht.

    py -3.14 scripts/verify_i18n_cache_version.py

Hintergrund (Codex, Abnahme 2026-10-08/09): `landing/js/i18n.js` legt das
geladene Woerterbuch unter `sa-i18n-<_JSON_VER>-<lang>` im **sessionStorage** ab
und haengt dieselbe Kennung als `?v=` an den Abruf. Wird en.json oder de.json
geaendert, ohne `_JSON_VER` zu erhoehen, liest ein Besucher weiter das ALTE
Woerterbuch, solange sein Tab offen ist. (Hier stand zuerst „localStorage" und
„unbegrenzt lange" — beides falsch, richtiggestellt nach Codex' Hinweis in
Runde 4. Die Lage ist weniger dauerhaft, aber genauso unbemerkt.) Codex hat damit
reproduziert, dass eine zurueckgenommene Behauptung („already knows the outcome
months in advance") wieder erscheint, obwohl sie in der Quelle nicht mehr steht.

Das ist die teuerste Klasse in diesem Projekt: eine Korrektur, die ausgerollt
ist und den Leser nicht erreicht. Ein Text ohne neue Kennung ist nicht
veroeffentlicht.

Geprueft wird gegen den letzten Commit, nicht gegen eine gepflegte Liste —
sonst veraltet die Liste. Ohne git (oder ausserhalb eines Repos) meldet der
Waechter UNGEPRUEFT und damit NICHT bestanden.
"""
from __future__ import annotations

import io
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
I18N_JS = REPO / 'landing/js/i18n.js'
WOERTERBUECHER = ['landing/i18n/de.json', 'landing/i18n/en.json']

fehler = 0
anzahl = 0


def pruefe(b: bool, was: str) -> None:
    global fehler, anzahl
    anzahl += 1
    print(('  ok   ' if b else '  FEHL ') + was)
    if not b:
        fehler += 1


def git(*args: str) -> tuple[int, str]:
    try:
        r = subprocess.run(['git', *args], cwd=str(REPO), capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as e:
        return 97, str(e)
    return r.returncode, r.stdout


def kennung(text: str) -> str | None:
    m = re.search(r"var\s+_JSON_VER\s*=\s*'([^']+)'", text)
    return m.group(1) if m else None


def main() -> int:
    global fehler
    jetzt = io.open(I18N_JS, encoding='utf-8').read()
    ist = kennung(jetzt)
    pruefe(ist is not None,
           '_JSON_VER ist in i18n.js lesbar (%r)' % ist)
    if ist is None:
        return 1

    # Die Kennung muss auch wirklich BENUTZT werden — sonst steht sie da und
    # wirkt nicht.
    pruefe("'sa-i18n-' + _JSON_VER" in jetzt,
           'die Kennung steckt im sessionStorage-Schluessel')
    pruefe("?v=' + _JSON_VER" in jetzt,
           'die Kennung haengt am Abruf des Woerterbuchs')

    rc, _ = git('rev-parse', '--git-dir')
    if rc != 0:
        print('  FEHL [Aufbau] kein git verfuegbar — UNGEPRUEFT, und das ist')
        print('       nicht bestanden: die Aenderung laesst sich nicht sehen.')
        return 1

    # ZWEI Vergleiche, damit der Waechter in beiden Lagen etwas prueft:
    #   (a) vor dem Commit: Arbeitsbaum gegen HEAD.
    #   (b) im Deploy: der Arbeitsbaum ist sauber, also HEAD gegen HEAD~1.
    # Ohne (b) waere das Gate im Deploy immer gruen — ein Gate ohne Wirkung.
    def vergleich(neuer_stand: str | None, alter_ref: str,
                  beschreibung: str) -> tuple[bool, int]:
        """Liefert (es gab Aenderungen, Exitcode bei Abbruch)."""
        rc_, kopf = git('show', alter_ref + ':landing/js/i18n.js')
        if rc_ != 0:
            # Fehlt die Referenz, ist NICHTS geprueft — und ungeprueft ist nicht
            # bestanden. Genau hier lief der Waechter vorher gruen durch: ein
            # flacher Checkout (fetch-depth 1) hat kein HEAD~1, und der
            # Referenzausfall galt als folgenlos (Codex, Abnahme Runde 3).
            # Einzige Ausnahme: es gibt wirklich keinen Vorgaenger, weil HEAD
            # der erste Commit ist.
            # `rev-list --count HEAD` liefert im FLACHEN Klon ebenfalls 1 —
            # damit hielt die erste Fassung dieser Pruefung HEAD fuer den
            # ersten Commit und lief gruen durch. Die flache Historie muss
            # direkt erkannt werden; nachgestellt an einem `git clone
            # --depth 1`.
            rc_flach, flach = git('rev-parse', '--is-shallow-repository')
            ist_flach = rc_flach == 0 and flach.strip() == 'true'
            rc_anz, anz = git('rev-list', '--count', 'HEAD')
            erster = (not ist_flach) and rc_anz == 0 and anz.strip() == '1'
            if erster:
                print('  ok   %s existiert nicht (HEAD ist der erste Commit)'
                      % alter_ref)
                return False, 0
            print('  FEHL %s nicht lesbar — die Historie ist zu flach '
                  '(fetch-depth?). UNGEPRUEFT, und das ist nicht bestanden.'
                  % alter_ref)
            return False, 1
        alt = kennung(kopf)
        betroffen = []
        for rel in WOERTERBUECHER:
            if neuer_stand is None:
                rc2, _ = git('diff', '--quiet', alter_ref, '--', rel)
            else:
                rc2, _ = git('diff', '--quiet', alter_ref, neuer_stand, '--', rel)
            if rc2 == 97:
                print('  FEHL [Aufbau] git diff nicht ausfuehrbar — UNGEPRUEFT.')
                return False, 1
            if rc2 != 0:
                betroffen.append(rel)
        if not betroffen:
            return False, 0
        neu_k = ist if neuer_stand is None else kennung(
            git('show', neuer_stand + ':landing/js/i18n.js')[1])
        print('  %s: %s' % (beschreibung, ', '.join(betroffen)))
        pruefe(neu_k != alt,
               'die Cache-Kennung wurde erhoeht (%s %r -> %r) — sonst liest ein '
               'Besucher mit offenem Tab weiter das alte Woerterbuch'
               % (alter_ref, alt, neu_k))
        return True, 0

    gab_aenderung, abbruch = vergleich(None, 'HEAD', 'geaendert im Arbeitsbaum')
    if abbruch == 1:
        return 1
    if not gab_aenderung:
        gab2, abbruch2 = vergleich('HEAD', 'HEAD~1', 'geaendert im letzten Commit')
        if abbruch2 == 1:
            return 1
        if not gab2:
            print('  ok   kein Woerterbuch geaendert (Arbeitsbaum und letzter '
                  'Commit) — nichts zu tun')

    print()
    print('ALLE PRUEFUNGEN BESTANDEN' if fehler == 0 else '%d FEHLER' % fehler)
    print('PROBE-ENDE %d Pruefungen, %d Fehler' % (anzahl, fehler))
    return 0 if fehler == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
