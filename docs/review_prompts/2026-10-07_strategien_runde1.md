# Codex-Prompt: Review der Strategie-Seite, Runde 1

> Vorbereitet 2026-10-07, zu starten **nach** dem Abschluss der Polymarket-Arbeit.
> Gelesene Seite: `/plain-vanilla` („Plain Vanilla Strategien" in der Navigation).
> Falls stattdessen `/scanner` oder die Backtest-Engine gemeint ist: Dateiliste
> austauschen, der Aufbau des Prompts bleibt.

```
<task>
Pruefe die Strategie-Seite von SeasonAlpha (seasonalpha.ai/plain-vanilla) und ihren
Rechenkern. Die Seite zeigt regelbasierte Handelsstrategien mit Kennzahlen (Sharpe,
Trefferquote, Profit-Faktor) und Signalen fuer den aktuellen Tag.

Dateien:
  landing/pages/plain-vanilla.html        (698 Zeilen, Oberflaeche + Inline-JS)
  landing/js/strategy-compute.js          (751, SA.STRATEGIES, Signal- und Kennzahlenrechnung)
  landing/js/indicators.js                (435, Indikatorfilter)
  shared/backtest_engine.py               (727, der Python-Zwilling)
  landing/js/seasonal-compute.js          (gemeinsame Saison-Mathematik)
  landing/pages/dashboard.html            (nutzt SA.STRATEGIES ebenfalls)

Was diese Seite besonders macht, und woran du sie messen sollst: sie veroeffentlicht
Kennzahlen, auf die ein Leser Geld setzen koennte. Eine zu guenstig gerechnete
Trefferquote ist hier kein Darstellungsfehler, sondern eine falsche Aussage.

**Domaenen-Invarianten, gegen die du pruefen sollst** (nicht „schau mal drueber"):

1. **Look-ahead-Bias.** Das Projekt hat die Regel `filterMask[entryIdx-1]`, NICHT
   `[entryIdx]` — ein Filter darf nur Information vom Vortag nutzen. Gilt sie
   ueberall? Auch bei Stop-Loss, bei der Positionsgroesse, bei der Auswahl des
   Einstiegstags, und in `indicators.js`?
2. **Backend/Frontend-Zwillinge.** `strategy-compute.js` und `backtest_engine.py`
   rechnen dieselbe Sache. Rechnen sie nachweislich dasselbe? Im Options-Teil dieses
   Projekts hatten zwei Black-Scholes-Kopien verschiedene Zinssaetze, und ein
   Frontend-Rueckfall erzwang eine Symmetrie, die es nicht gibt.
3. **Quantile ohne Floor-Indexing.** Projektregel: lineare Interpolation wie numpy,
   nie `arr[Math.floor(p*n)]`.
4. **Normalisierte Renditen.** Jedes Jahr startet bei 100, taegliche Log-Renditen
   kumulieren darauf. Niemals `close - close[lookback]`. Und: `log_return` ist
   RUECKWAERTS definiert (`LN(close/prev_close)`), gehoert also zu SEINER Zeile — ein
   Off-by-one hier zeichnet plausible Kurven und ist deshalb teuer.
5. **Was passiert bei fehlenden Daten?** Wird ein Wert `None`/`null`, oder rutscht ein
   alter Wert in die Rolle des aktuellen? Zaehlt ein konstant fortgeschriebener Kurs
   (Constant-Fill) in die Kennzahlen? Das Projekt hat dafuer
   `shared/calculations.last_actual_day(yd)` und die Regel, dass der KONSUMENT filtert.
6. **Transaktionskosten, Slippage, Survivorship.** Werden sie beruecksichtigt, und
   sagt die Seite, was sie annimmt?
7. **Mehrfachtestung.** Wie viele Parameterkombinationen wurden durchprobiert, bevor
   die veroeffentlichte Zahl entstand? Steht das dabei? Eine optimierte Haltedauer
   ohne Hinweis auf die Suche ist eine zu starke Aussage.
8. **Reproduzierbarkeit.** Kann ein Leser die angezeigte Kennzahl aus den angezeigten
   Parametern nachrechnen? Weichen Seite und Newsletter voneinander ab?
9. **Signal fuer heute.** Wird der Handelstag boersenspezifisch gezaehlt
   (`SA.holidays`), oder aus der letzten DB-Zeile abgeleitet? Letzteres ist in diesem
   Projekt ein bekannter Fehler, weil die DB vor dem Intraday-Refresh veraltet ist.
10. **Sprache und Recht.** Die Seite darf keine Handlungsempfehlung aussprechen. Pruefe
    auch die Farbskala: gruen/rot ueber einer Betragsspalte liest sich als Kauf- oder
    Verkaufsempfehlung (dieser Fehler wurde auf /skew schon einmal korrigiert).

**Bereits bekannt und NICHT erneut zu melden:**
* `SPY Down-Month ToM Reversal`: die Kennzahlen (Sharpe 0,34 · Trefferquote 72 % ·
  Profit-Faktor 2,39) sind korrekt gerechnet, aber die PARAMETER (Einstieg TDOM 14,
  Haltedauer 13) wurden aus einer um einen Handelstag verschobenen Kurve abgelesen.
  Steht als offener Posten im Projekt.
* Die Turn-of-Month-Fehlerfamilie ist 2026-09-10/11 behoben (fuenf Fundstellen).
* Der `author` im Blog-Template ist `Organization` statt `Person` — bekannt.

**Absehbare Fehlalarme, bitte vorher gegenpruefen:**
* `data-i18n`-Attribute ohne sichtbaren englischen Text sind kein Defekt, solange der
  Schluessel in `landing/i18n/en.json` existiert — die EN-Seiten werden statisch
  vorgerendert.
* Cron-Ausgaben unter `landing/data/` sind gitignoriert und lokal nicht vorhanden. Eine
  fehlende JSON-Datei ist hier kein Befund.
</task>

<verification_loop>
Pruefe am Code, nicht an der Beschreibung. Wo du einen Fehler findest, nenne Datei und
Zeile und den konkreten Eingabewert, der ihn zeigt — eine Kennzahl, ein Datum, eine
Kursreihe. Wo du etwas nicht pruefen kannst, schreibe UNGEPRUEFT.

`strategy-compute.js` laesst sich in node mit einem `window`-Stub fahren; Muster dafuer
liegen in `scripts/js/twin_probe.js` und `scripts/js/probe_skew_tabelle.js`. Wenn du
eine Abweichung zwischen JS und Python behauptest, belege sie mit einem Eingabefall, in
dem sich die Zahlen unterscheiden.
</verification_loop>

<grounding_rules>
Du siehst nur den Arbeitsbaum. Ueber ausgelieferte Seiten, laufende Jobs und
Produktionsdaten behaupte nichts.

Widerlege mich, wo meine Annahmen falsch sind. In diesem Projekt hat ein ungeprueft
uebernommener Reviewer-Befund schon einmal fast das KORREKTE Frontend zerstoert — der
Reviewer nannte eine Konvention neutral, und richtig war die Seite, die geaendert
werden sollte.
</grounding_rules>

<structured_output_contract>
Teil A — Befunde, nach Stufe sortiert (hoch / mittel / niedrig), je mit Datei:Zeile,
  Eingabewert, Wirkung und der kleinsten Aenderung, die es behebt. Kennzeichne, was du
  am Code BESTAETIGT hast und was Vermutung ist.
Teil B — was du ausdruecklich als KORREKT geprueft hast. Diese Liste ist so wichtig wie
  die Befunde, damit die naechste Runde nicht dasselbe nochmal prueft.
Teil C — eine Zeile: FREIGABE: ja / nein.
</structured_output_contract>

<action_safety>
Nur lesen. Keine Datei aendern, keinen Commit, keinen Workflow ausloesen, keine
Mail senden.
</action_safety>
```

## Vorgehen fuer den Loop

Dieselbe Mechanik wie bei Polymarket, die sich dort bewaehrt hat:

1. **Entwurf vor Code.** Jede Phase geht als Entwurf zu Codex, bevor eine Zeile
   entsteht. Bei Polymarket fielen so acht Einwaende vor dem ersten Code — und in
   v65.2 hat das fuenf Runden gespart.
2. **Ein Waechter je Phase, mit Mutationstest.** Die Mechanik aus Phase D ist
   uebertragbar: Aufbaupruefungen getrennt gekennzeichnet (`[Aufbau]`), ein Endmarker,
   jede Mutation benennt die Pruefung, die sie reissen muss, eine Ausnahme gilt nie als
   Nachweis, und eine eigene Liste prueft das **Urteil des Tests selbst**.
3. **Kennzahlen nie aendern, ohne sie neu zu rechnen.** Hier besonders: die Seite
   veroeffentlicht Zahlen, die ein Leser als Entscheidungsgrundlage nimmt.
4. **Was eine veroeffentlichte Aussage zurueckzieht, ist eine Nutzerentscheidung** —
   vorbereiten, messen, fragen.
