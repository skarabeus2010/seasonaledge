# -*- coding: utf-8 -*-
"""Prüft den Wächter, nicht den Code: baut Fehler in landing/js/kurse.js ein und verlangt, dass
verify_kurse.py ROT wird — an der benannten FACHLICHEN Prüfung.

    py -3.14 scripts/verify_kurse_mutation.py

Beweisregeln wie in den übrigen Mutationstests: Endmarker `PROBE-ENDE` muss erreicht sein · jede Mutation
BENENNT die Prüfung, die sie reißen muss · eine Ausnahme gilt nie als Nachweis, auch eine eingefangene
(`[Ausnahme]`) nicht · ein Anker, der nicht genau einmal trifft, macht die Mutation ungültig ·
`UNGUELTIG_ERWARTET` prüft das Urteil dieses Tests.
"""
from __future__ import annotations

import io
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from scripts.verify_twins_mutation import (LockBelegt, _atomar_schreiben,  # noqa: E402
                                           _exklusiver_lauf)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

KU = "landing/js/kurse.js"
PROBE = "scripts/verify_kurse.py"

MUTATIONEN = [
    # Codex S1 R1: drei Mutationen, die die erste Probe NICHT fing.
    ("Sortierung aus der Abfrage entfernt",
     KU, "'&order=date.asc&limit=' + K.BLOCK", "'&limit=' + K.BLOCK",
     "[Request-Vertrag: "),
    ("count=exact wieder angefordert",
     KU, "headers: { 'apikey': SA.supabase.key, 'Authorization': 'Bearer ' + SA.supabase.key },",
     "headers: { 'apikey': SA.supabase.key, 'Authorization': 'Bearer ' + SA.supabase.key, 'Prefer': 'count=exact' },",
     "[Request-Vertrag: "),
    ("Retry-After ignoriert",
     KU, "          return nochmal(retryAfterMs(w.retryAfter));", "          return nochmal(null);",
     "[Retry-After Sekunden eingehalten]"),
    ("Retry-After als HTTP-Datum ignoriert",
     KU, "    var t = Date.parse(s);\n    if (isNaN(t)) return null;", "    var t = NaN;\n    if (isNaN(t)) return null;",
     "[Retry-After HTTP-Datum eingehalten]"),
    ("Poolplatz schon mit der Frist frei",
     KU, "      antwort.then(frei, frei);", "      antwort.then(frei, frei);\n      setTimeout(frei, K.TIMEOUT_MS);",
     "[Schlange mit Frist ("),
    ("Pool ohne Grenze",
     KU, "    while (aktiv < K.POOL && schlange.length) schlange.shift()();",
     "    while (schlange.length) schlange.shift()();",
     "[Pool höchstens 4]"),
    # Codex S1 R2: Frist schließt die Wartezeit in der Schlange ein; verspätete Antworten veröffentlichen nichts.
    ("abgelaufene Wartende bleibt in der Schlange",
     KU, "        warten.entfernen();                     // noch in der Schlange → raus, belegt nie einen Platz\n", "",
     "[abgelaufene Wartende fragt später nicht an]"),
    ("Frist startet erst mit dem Platz",
     KU, "    var frist = new Promise(function (ok, nein) {\n      zeit = setTimeout(function () {\n"
         "        warten.entfernen();                     // noch in der Schlange → raus, belegt nie einen Platz\n"
         "        if (abbruch) abbruch.abort();\n"
         "        nein(KursFehler('Zeitüberschreitung (' + ticker + ')'));\n      }, K.TIMEOUT_MS);\n    });",
     "    var frist = warten.promise.then(function () { return new Promise(function (ok, nein) {\n      zeit = setTimeout(function () {\n"
     "        warten.entfernen();\n"
     "        if (abbruch) abbruch.abort();\n"
     "        nein(KursFehler('Zeitüberschreitung (' + ticker + ')'));\n      }, K.TIMEOUT_MS);\n    }); });",
     "[Abschnitt hängt: 19b"),
    ("Frist ignoriert (verspätete Antwort wird veröffentlicht)",
     KU, "    return Promise.race([transport, frist]).then(", "    return transport.then(",
     "[verspätete Antwort veröffentlicht nichts]"),
    # Vollständigkeit
    ("Ende schon bei genau 1000 Zeilen",
     KU, "        if (z.length < K.BLOCK) return [].concat.apply([], bloecke);",
     "        if (z.length <= K.BLOCK) return [].concat.apply([], bloecke);",
     "[Sollmenge 1001]"),
    ("Netzfehler nach den Wiederholungen wird leeres Ergebnis",
     KU, "      if (versuch < K.MAX_WIEDERHOLUNGEN) return nochmal(null);\n      throw",
     "      if (versuch < K.MAX_WIEDERHOLUNGEN) return nochmal(null);\n      return [];\n      throw",
     "[JSON-Fehler dauerhaft: abgelehnt]"),
    ("500 wird ohne Wiederholung zum leeren Ergebnis",
     KU, "        throw KursFehler('prices ' + w.status + ' (' + ticker + ')');",
     "        return [];",
     "[Teilfehler lehnt ab]"),
    ("Cursor-Fortschritt nicht geprüft",
     KU, "    var vorher = nach;", "    var vorher = null;",
     "[Block abgelehnt: Cursor ohne Fortschritt]"),
    ("Blockgrenze fehlt",
     KU, "      if (++n > K.MAX_BLOECKE) return", "      if (++n > 1e9) return",
     "[zu viele Blöcke abgelehnt]"),
    ("Feldprüfung fehlt",
     KU, "        if (!Object.prototype.hasOwnProperty.call(zeile, bedarf.felder[f])) {",
     "        if (false) {",
     "[Block abgelehnt: Feld fehlt]"),
    ("Datumsprüfung lässt Zeitstempel durch",
     KU, "  var ISO = /^(\\d{4})-(\\d{2})-(\\d{2})$/;", "  var ISO = /^(\\d{4})-(\\d{2})-(\\d{2})/;",
     "[Block abgelehnt: Zeitstempel statt Datum]"),
    # Sicht
    ("Grenztag ausgeschlossen",
     KU, "      if (ab !== null && z.date < ab) continue;", "      if (ab !== null && z.date <= ab) continue;",
     "[Grenze inklusive]"),
    ("Sicht ohne Kopie",
     KU, "      var o = {};\n      for (var f = 0; f < felder.length; f++) o[felder[f]] = z[felder[f]];\n      aus.push(o);",
     "      aus.push(z);",
     "[Ergebnis ist Kopie]"),
    ("null wird zu 0",
     KU, "o[felder[f]] = z[felder[f]];", "o[felder[f]] = z[felder[f]] || 0;",
     "[null bleibt null]"),
    # Koordinator
    ("Deckung ignoriert die Felder",
     KU, "    for (var i = 0; i < felder.length; i++) if (bedarf.felder.indexOf(felder[i]) < 0) return false;\n", "",
     "[Bestand schrumpft nicht]"),
    ("Deckung ignoriert die Grenze",
     KU, "    return bedarf.ab === null || (ab !== null && ab >= bedarf.ab);", "    return true;",
     "[wartende Vereinigung]"),
    ("Vereinigung nimmt die spätere Grenze",
     KU, "(a.ab < b.ab ? a.ab : b.ab)", "(a.ab < b.ab ? b.ab : a.ab)",
     "[wartende Vereinigung zweier Grenzen]"),
    ("Bestand nicht Teil der Vereinigung (schrumpft)",
     KU, "      return starte(ticker, k, vereinige(anfrage, k.bestand ? k.bestand.bedarf : null)).promise.then(aus);",
     "      return starte(ticker, k, vereinige(anfrage, null)).promise.then(aus);",
     "[Bestand schrumpft nicht]"),
    ("laufende Ladung nicht geteilt",
     KU, "      if (k.laufend && deckt(k.laufend.bedarf, felder, ab)) return k.laufend.promise.then(aus);\n", "",
     "[geteilte Ladung]"),
    ("wartende Ladung startet nach Fehler nicht",
     KU, "    lauf.promise.then(danach, danach);", "    lauf.promise.then(danach, function () { k.laufend = null; });",
     "[Abschnitt hängt: 12 laufende Ladung scheitert"),
    ("TTL ignoriert",
     KU, "  function frisch(b) { return b && (uhr() - b.geladenUm) < K.TTL_MS; }",
     "  function frisch(b) { return !!b; }",
     "[TTL: frisch aus Bestand, abgelaufen neu]"),
    ("Fehler verlängert die Frische",
     KU, "    lauf.promise = ladeAlles(ticker, bedarf).then(function (zeilen) {",
     "    lauf.promise = ladeAlles(ticker, bedarf).catch(function (e) { if (k.bestand) k.bestand.geladenUm = uhr(); throw e; }).then(function (zeilen) {",
     "[alter Bestand bleibt ohne Frischeverlängerung]"),
    ("Generation je Ticker statt global",
     KU, "generation: ++generationen };", "generation: (k.bestand ? k.bestand.generation : 0) + 1 };",
     "[Generation über Ticker streng steigend]"),
    # Die Schutzprüfung in laden() (Bestand deckt die Anfrage) ist bei sonst korrektem Code unerreichbar —
    # ihr Entfernen ändert kein Verhalten (äquivalente Mutation) und steht deshalb nicht in der Liste. Ihre
    # Wirkung zeigt die Mutation "Vereinigung nimmt die spätere Grenze": ohne sie gäbe es eine zu kurze Reihe.
    ("LRU verdrängt laufende Koordinatoren",
     KU, "        if (t === neu || k.laufend || k.wartend) return;      // nur ruhende Koordinatoren",
     "        if (t === neu) return;",
     "[laufende nicht verdrängt]"),
    ("LRU fehlt",
     KU, "    while (namen.length > K.MAX_TICKER) {", "    while (false) {",
     "[LRU-Grenze]"),
    ("Eingabe: unbekanntes Feld erlaubt",
     KU, "      if (ERLAUBT.indexOf(f) < 0) throw KursFehler('unbekanntes Feld: ' + f);\n", "",
     "[Eingabe abgelehnt: unbekanntes Feld]"),
]

UNGUELTIG_ERWARTET = [
    ("Anker existiert nicht", KU, "diese Zeile gibt es nicht", "egal"),
    ("Absturz statt Verhaltensänderung", KU, "  var generationen = 0;", "  var generationen = 0; null.x;"),
    # Codex S1 R3: TypeError beim Lesen eines Feldes in der Sicht — fängt Abschnitt 10b ein, darf nicht zählen
    ("eingefangener TypeError in der Sicht", KU,
     "      for (var f = 0; f < felder.length; f++) o[felder[f]] = z[felder[f]];",
     "      for (var f = 0; f < felder.length; f++) { if (felder[f] === 'open' && ab === '1901-01-01') null.x; o[felder[f]] = z[felder[f]]; }"),
    # Codex S1 R3: unbehandelte Ablehnung mit TypeError am Ende eines Abschnitts
    ("unbehandelte TypeError-Ablehnung", KU,
     "      var anfrage = { felder: felder, ab: ab };",
     "      var anfrage = { felder: felder, ab: ab };\n      Promise.reject(new TypeError('unbehandelt'));"),
    # ein eingefangener Absturz (TypeError statt KursFehler) darf nicht als gefangene Mutation zählen
    ("eingefangener Absturz im Teilfehler-Pfad", KU,
     "        throw KursFehler('prices ' + w.status + ' (' + ticker + ')');",
     "        throw new TypeError('getarnt prices ' + w.status);"),
]

DATEIEN = (KU,)
ROH: dict = {}


def anker(datei: str, text: str) -> bytes:
    roh = ROH[datei]
    if roh.count(b"\r\n") > roh.count(b"\n") // 2:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    return text.encode("utf-8")


def lauf() -> tuple[int, str]:
    r = subprocess.run([sys.executable, PROBE], capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONUTF8": "1"}, timeout=600)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def bewerte(datei, alt, neu, erwartet=None):
    a = anker(datei, alt)
    n = ROH[datei].count(a)
    if n != 1:
        return "ungueltig", f"Anker {n}x gefunden, erwartet 1x"
    _atomar_schreiben(pathlib.Path(datei), ROH[datei].replace(a, anker(datei, neu), 1))
    try:
        rc_, aus = lauf()
    finally:
        _atomar_schreiben(pathlib.Path(datei), ROH[datei])
    if rc_ == 0:
        return "entwischt", "Probe blieb grün"
    if "PROBE-ENDE" not in aus:
        return "ungueltig", "die Probe brach ab statt durchzulaufen"
    zeilen = [z for z in aus.splitlines() if "FEHL " in z]
    if any("[Ausnahme]" in z for z in zeilen):
        return "ungueltig", "Produktivcode warf"
    if not zeilen:
        return "ungueltig", "rot ohne inhaltliche Prüfung"
    if erwartet and not any(erwartet in z for z in zeilen):
        return "ungueltig", f"erwartete Prüfung {erwartet} blieb grün; rot war: {zeilen[0].strip()[:60]}"
    return "gefangen", zeilen[0].strip()[:70]


def _main() -> int:
    rc, ausgabe = lauf()
    if rc != 0:
        print("ABBRUCH: die Probe ist schon ohne Mutation rot.")
        print(ausgabe[-1500:])
        return 1
    m = re.search(r"PROBE-ENDE (\d+) Pruefungen", ausgabe)
    if not m:
        print("ABBRUCH: die Probe meldet keinen Endmarker.")
        return 1
    print(f"Grundlinie: Probe ohne Mutation grün, {m.group(1)} Prüfungen\n")

    gefangen, probleme, urteil_ok = 0, [], True
    try:
        for name, datei, alt, neu, erwartet in MUTATIONEN:
            art, warum = bewerte(datei, alt, neu, erwartet)
            if art == "gefangen":
                print(f"  gefangen       {name}")
                gefangen += 1
            else:
                print(f"  {art.upper():12s}   {name}  ({warum})")
                probleme.append(f"{name} [{art}: {warum}]")
        print("  -- Gegenprobe am Urteil dieses Tests --")
        for name, datei, alt, neu in UNGUELTIG_ERWARTET:
            art, warum = bewerte(datei, alt, neu)
            if art == "ungueltig":
                print(f"  richtig verworfen  {name}  ({warum})")
            else:
                print(f"  FALSCH EINGEORDNET {name}  -> {art}")
                probleme.append(f"{name} [als {art} verbucht]")
                urteil_ok = False
    finally:
        for d, b in ROH.items():
            _atomar_schreiben(pathlib.Path(d), b)
    for d, b in ROH.items():
        assert io.open(d, "rb").read() == b, "WIEDERHERSTELLUNG FEHLGESCHLAGEN: " + d
    rc_nach, _ = lauf()
    print()
    print("wiederhergestellt: Probe läuft wieder grün" if rc_nach == 0
          else "WARNUNG: Probe nach der Wiederherstellung ROT!")
    print(f"{gefangen} von {len(MUTATIONEN)} Mutationen gefangen")
    for p in probleme:
        print("  " + p)
    return 0 if (gefangen == len(MUTATIONEN) and urteil_ok and rc_nach == 0) else 1


def main() -> int:
    try:
        with _exklusiver_lauf():
            ROH.update({d: io.open(d, "rb").read() for d in DATEIEN})
            return _main()
    except LockBelegt as e:
        print(f"ABBRUCH: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
