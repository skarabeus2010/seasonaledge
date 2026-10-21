# Entwurf v5 — Baufassung Stufe 1

**Status:** Codex-Freigabe nach Runde 4 mit zwei Auflagen. Dies ist die **Baufassung**:
sie ändert gegenüber [v4](2026-10-21_gex_abendluecke_entwurf_v4.md) nur, was die Auflagen
verlangen. Alles Übrige gilt wie dort.

Abnahme Runde 4: M2 und M6 abgenommen, M3 nicht (→ Auflage 1), K1 und K2 neu.

## Auflage 1 — Prozessstatus und Marker gemeinsam auswerten (K1)

v4 hatte „fehlender Marker ⇒ fehlgeschlagen". Das ist falsch, und zwar belegbar:
`Gesperrt` erbt von `SystemExit` (`produktionssperre.py:71-75`) und wird in `_sperren`
(`:137-149`) beim **Eintritt** in `produktion()` geworfen — also bevor `main()` läuft und
bevor ein Marker gedruckt werden kann. Die Sperre schreibt ihren Nachweis auf stderr,
keinen Ergebnismarker. Eine geplante Unterdrückung wäre damit rot geworden.

Die Hülle entscheidet aus **Exit-Code und Marker gemeinsam**, und der Exit-Code hat
Vorrang:

| Exit | Marker | Ergebnis | Key Levels |
|---|---|---|---|
| 75 | beliebig, auch keiner | **unterdrückt** | nein |
| 0 | genau ein `veröffentlicht` | **veröffentlicht** | **ja** |
| 0 | genau ein `übersprungen` oder `trocken` | wie der Marker | nein |
| 0 | keiner, mehrere oder unbekannter | **fehlgeschlagen** | nein |
| sonst | beliebig, auch `veröffentlicht` | **fehlgeschlagen** | nein |

Die letzte Zeile ist die zweite Hälfte der Auflage: ein `veröffentlicht`-Marker **und
danach** ein Fehlerexit darf Key Levels nicht starten. Der Marker wird aus der Ausgabe
**dieses** Aufrufs gelesen, nicht aus einer Datei.

## Auflage 2 — Atomares Schreiben gehört in Stufe 1 (K2)

v4 hatte es nach Stufe 2 verschoben, mit dem Argument, Stufe 1 fasse den Schreibweg
nicht an. Das Argument trägt nicht, und K2 zeigt warum: Stufe 1 **führt einen neuen
Kill-Pfad ein**. Der heutige Workflow setzt `command_timeout: 18m` auf die ssh-action,
die beendet nur den Docker-Client; die neue Unit setzt `timeout` **im Container** (das ist
genau das dokumentierte Muster, `sa-intraday.service:15-19`). Diese Frist kann mitten in
einem `write_text()` ablaufen. Die Produktionssperre schützt davor **nicht** — sie hält
den Deploy auf, nicht die eigene Uhr.

Also in Stufe 1: die Zieldateien von `snapshot_gex_massive.py` (Summary, Profile, Archiv)
und `compute_key_levels.py` über `shared/atomic_json.write_json_atomic` veröffentlichen.
Das verlangt **keine** Versionierung und **keine** Wiederaufnahme — die bleiben Stufe 2.

Zwei Dinge gehören dazu, beide aus der eigenen Geschichte:
- die **403-Falle** aus v60.2: `mkstemp` legt mit 0600 an, `os.replace` überträgt das;
  `write_json_atomic` übernimmt deshalb die Rechte der Zieldatei
  (`atomic_json.py:43-63`). Nach dem Deploy **HTTP prüfen**, nicht nur den Dateiinhalt.
- ein **deterministischer Abbruchtest**: Frist läuft während des
  Veröffentlichungszugriffs ab → die vorhandenen Dateien bleiben vollständig lesbar.

Was Stufe 1 ausdrücklich **nicht** löst und was K2 auch nicht verlangt: ein Abbruch
**zwischen** zwei Dateien hinterlässt weiter einen gemischten Stand (Summary neu, Archiv
alt). Das ist Stufe-2-Punkt 2 (Veröffentlichungszustand und Wiederaufnahme).

## Korrektur meiner eigenen Begründung (M6)

Mein Rückzug des Zukunftstors bleibt — gegenüber dem heutigen Code geht kein Schutz
verloren, das hat Codex bestätigt. **Meine Begründung dafür war aber falsch.** Ich hatte
geschrieben, ein unsinniges `rmt` könne höchstens einen Kurs durchlassen, der ohnehin der
Sessionschluss ist. Das stimmt nicht: die Tagesbalken tragen 09:30 New York als
Zeitstempel (`verify_gex_session.py:166-173`), ein Sessiondatum beweist also **keinen
fertigen Schluss** — `rmt` ist das einzige Schlusskriterium
(`snapshot_gex_massive.py:103-108`). Ein falsches Zukunfts-`rmt` könnte einen
stehengebliebenen Intraday-Balken passieren lassen. Richtig bleibt nur: dieses Tor
existiert heute nicht, sein Nichtbau verschlechtert nichts, und es ist kein
Stufe-1-Thema. Festgehalten, weil eine richtige Entscheidung mit falscher Begründung
beim nächsten Mal zur falschen Entscheidung führt.

## Zusätzliche Wächterfälle

Zu den 17 aus v4, Abschnitt 4:

| # | Fall | aus |
|---|---|---|
| 18 | **echter Sperreintritt** → Exit 75 **ohne** Marker → „unterdrückt", Key Levels laufen nicht | K1 |
| 19 | Marker `veröffentlicht` **und danach** Fehlerexit → Key Levels laufen **nicht** | K1 |
| 20 | Exit 0 mit **mehreren** oder unbekanntem Marker → „fehlgeschlagen" | K1 |
| 21 | **Fristablauf im Veröffentlichungszugriff** → vorhandene Dateien bleiben vollständig lesbar und gültiges JSON | K2 |
| 22 | Rechte der Zieldatei bleiben nach atomarem Austausch erhalten (0644, nicht 0600) | v60.2 |
| 23 | direkter Aufruf von `compute_key_levels.py` ohne Hülle: eigener Modus gilt selbständig | Antwort 2 |

Fall 21 ist der einzige, der die neue Auflage 2 prüfen kann; der Dauer-429-Test und die
Hash-Prüfung unterhalb der Abdeckungsgrenze treffen ihn nicht.
