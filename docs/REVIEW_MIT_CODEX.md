# Review-Schleife: Claude baut, Codex nimmt ab

> Betriebsanleitung für den direkten Codex-Kanal. Entstanden am 2026-09-11 beim
> Abschluss der Kern-Methodik-Prüfung (vier Runden, 25 Befunde) — die Hälfte der
> verlorenen Zeit ging auf Aufsetzfehler, nicht auf Inhalte. Die stehen hier,
> damit sie sich nicht wiederholen.

## Warum zwei Modelle

Ein Modell, das seinen eigenen Code prüft, findet zuverlässig die Fehler, die es
beim Schreiben schon bedacht hat. Die teuren Fehler dieser Codebasis fand jeweils
**das andere** Modell:

- Der Turn-of-Month-Versatz steckte in **beiden** Zwillingen identisch — ein
  Selbstvergleich hätte ihn nie gefunden.
- Zwei der Korrekturen **überschossen** und warfen jedes zweite abgeschlossene
  XETRA-Jahr weg. Das fiel erst dem externen Blick auf.
- Der Wächter zertifizierte zeitweise eine **Fiktion** (einen handgeschriebenen
  Nachbau statt des echten JS). Auch das kam von außen.

Umgekehrt gilt: **Befunde des Prüfers werden gegengeprüft, nicht umgesetzt.** In
Runde 1 nannte der Reviewer eine Konvention neutral „einigt euch"; tatsächlich war
eine Seite eindeutig falsch, und ungeprüftes Umsetzen hätte das *korrekte* Frontend
zerstört.

## Der Aufruf

```bash
codex exec -s read-only "<Prompt>"
```

`-s read-only` = Codex darf lesen und Kommandos ausführen, aber nichts schreiben.
Das ist die richtige Voreinstellung für eine Abnahme.

### Fünf Fallen, alle am 2026-09-11 durchlebt

| Falle | Symptom | Abhilfe |
|---|---|---|
| **`nohup … &`** | Lauf wird abgeschnitten, kein Schlussurteil — die Tool-Shell endet und nimmt den Prozess mit | Im **Vordergrund** starten; das Werkzeug lagert selbst aus, wenn es lange dauert |
| **Veraltete CLI** | `The 'gpt-5.6-luna' model requires a newer version of Codex` | `npm install -g @openai/codex@latest` |
| **`py -3.14` unsichtbar** | Codex sieht nur Python 3.9, das an `X \| None` scheitert | Absoluten Pfad mitgeben: `C:/Users/<user>/AppData/Local/Python/pythoncore-3.14-64/python.exe` |
| **Langläufer** | Abbruch beim Warten; der Mutationstest startet den Wächter 16× | Selbst ausführen, Codex die **Ausgabe** prüfen lassen — samt der Frage, ob das Ergebnis auch ohne echtes Greifen entstehen könnte |
| **Falscher Sandbox-Modus** | Der Mutationstest **schreibt** Dateien, unter `read-only` unmöglich | `--sandbox workspace-write`, vorher `git status --porcelain --untracked-files=no \| md5sum` merken und danach vergleichen |

Ein Reviewer, der nichts ausführen kann, lehnt korrekterweise ab. **Vier der fünf
„KEINE FREIGABE" waren Werkzeugfehler, kein inhaltliches Urteil.** Vor jeder
Interpretation prüfen, ob überhaupt etwas lief.

## Prompt-Aufbau

Was sich bewährt hat — knapp, blockweise, mit Ankern:

1. **`<task>`** — Datei- und Zeilenanker, `git`-Range, was schon gilt.
2. **Domänen-Invarianten** statt „prüf mal": die Regeln, gegen die geprüft wird.
3. **Fokusfragen** — konkrete Wenn-dann-Fragen, keine offenen Einladungen.
4. **Bereits bestätigt** — gegen Doppelmeldungen.
5. **Erwartbare Fehlalarme** — bewusste Entscheidungen vorab benennen, sonst
   kommen sie als Befund zurück.
6. **Ausgabevertrag** — feste Abschnitte, feste Zeilenzahl.

Für eine **Abnahme** zusätzlich: den Reviewer seine eigene Freigabe-Bedingung
nennen lassen und sie ihm dann vorrechnen. Er hatte sich eine einzige Zahl
ausbedungen (XETRA-2023 aus Rohkursen) — das war ein besserer Prüfstein als jede
Testsuite.

## Beweise vorlegen

- **Gleiche Genauigkeit für Eingang und Ergebnis.** Gerundete Eingangskurse neben
  einem präzisen Ergebnis erzeugten einen Scheinwiderspruch von 0,0026 pp; der
  Reviewer rechnete korrekt aus dem Gezeigten nach.
- **Testfall mit genau einer Bewegung**, wenn eine kumulierende Reihe geprüft wird.
- **Mutationstest statt Behauptung.** `scripts/verify_twins_mutation.py` baut jeden
  bekannten Fehler wieder ein und verlangt Rot. Ohne diesen Schritt ist „der Test
  besteht" eine Aussage über den Test, nicht über den Code.

## Ablauf einer Runde

1. Prompt schreiben, `codex exec` im Vordergrund.
2. **Jeden Befund am Code gegenprüfen** — mit eigenem Testfall, nicht durch Lesen.
3. Echte Befunde fixen, je einen Testfall dazu.
4. Widerlegte Befunde als erwartbaren Fehlalarm in den nächsten Prompt aufnehmen.
5. Mutationstest: wird der neue Testfall auch rot?
6. Committen, Lessons in die Fach-Doku.
7. Nächste Runde auf dem neuen Stand.

Abbruch, wenn eine Runde nur noch Fehlalarme liefert oder die Befunde kleiner
werden als der Aufwand, sie zu prüfen.

## Kosten

Eine Fokusfrage mit echter Nachrechnung lag bei ~30k Tokens, eine volle Abnahme
mit sechs Fragen bei mehreren hunderttausend. Große Läufe deshalb in Einzelfragen
zerlegen: billiger, und jede Antwort ist sofort prüfbar statt am Ende als Block.

## Was nicht funktioniert

Das Codex-**Plugin** in Claude Code (`codex:codex-rescue`, `/review`,
`/adversarial-review`) scheitert am Modell — sein Companion-Script spricht ein
älteres Protokoll, auch nach dem CLI-Upgrade. Der direkte `codex exec` kann alles,
was gebraucht wird, und der Prompt bleibt unter eigener Kontrolle.
