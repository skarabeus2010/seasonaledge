# Entwurf v3: Polymarket B2 — die fünf Auflagen aus Runde 2

v3 ist ein **Delta auf v2** (`2026-10-20_polymarket_b2_entwurf_v2.md`), das unverändert
gilt, soweit hier nichts anderes steht. Runde 2 hat B1, B2, B4, B7, B8, B10 als erledigt
abgenommen und fünf Auflagen gestellt. Jede wird hier beantwortet.

Zwei Befunde aus Runde 2 waren Widersprüche in meinem eigenen Entwurf, nicht im
Bestand, und das sage ich vorweg, weil sie die Form der Antworten bestimmen:

* **N3** — meine Wächterliste verlangte `neq(status, resolved)`, obwohl zwei Abschnitte
  vorher gemessen stand, dass genau das bei `status IS NULL` ein No-Op ist. Ein Wächter,
  der die ausgeschlossene Variante festschreibt, hätte die Regression zementiert.
* **N2 / Frage 3** — der Gegenfall *0 Preise, 1 fachlich übersprungen, 25 technische
  Abruffehler* wäre nach meiner Formel grün geworden. Ein einziger legitim geschlossener
  Markt hätte einen Totalausfall verdeckt.

---

## Auflage 1 — Preisfreigabe gegen zwischenzeitliche Auflösung

Codex hat recht: zwischen Kataloglesen und Preis-Upsert liegt ein Fenster, und meine
Formulierung „es gibt kein Zwischenfenster" war über den gesicherten Teil hinaus.

**Was den Fall heute eng macht, und was ihn ganz schließt:**

1. **Die Entscheidung kommt nicht mehr aus einem vorher gelesenen Status, sondern aus
   der Antwort des Schreibvorgangs.** Die bedingte Statusanweisung aus v2 Abschnitt 1
   liefert mit `returning=representation` die betroffene Zeile zurück. Kommt **keine**
   Zeile zurück, war die Zeile `resolved` (oder existiert nicht) — und dann wird keine
   Preiszeile geschrieben. Kommt eine zurück, ist ihr `status` der von der Datenbank
   serialisierte Endstatus, nicht eine Kopie von vorher. Die Reihenfolge ist also:
   Status schreiben → Antwort lesen → nur dann Preis schreiben.
2. Damit bleibt ein Restfenster zwischen diesen zwei Anweisungen. Es wird **benannt,
   nicht wegerklärt**: ein Auflösungsschreiber, der genau dazwischen schreibt, kann
   einen letzten aktuellen Preis nicht verhindern.
3. **Dieses Restfenster ist heute leer, und das ist prüfbar:** es gibt keinen
   Auflösungsschreiber. `status_aus_markt` gibt per Erkenntnisgrenze nie `resolved`
   zurück, und kein anderer Pfad setzt die Spalte. Gemessen am 2026-10-20 lesend auf der
   laufenden DB: alle 26 Katalogzeilen haben `status IS NULL`.
4. Deshalb wird die Absicherung **Vorbedingung für B4**, nicht für B2: wer den ersten
   Auflösungsschreiber baut, muss Statusprüfung und Preiseinfügung gemeinsam absichern
   (eine Datenbankfunktion, die beides in einer Anweisung tut, ist der naheliegende
   Weg). Der Posten steht in B4, nicht als Fußnote.

Die Zusage in v2 Abschnitt 1 („kein Fenster, immer genau eine Anweisung wirksam") wird
auf das zurückgenommen, was sie trägt: **der Schutz von `resolved` gegen Überschreiben**
ist eine Eigenschaft der Anweisung. Über die Reihenfolge zweier Anweisungen sagt sie
nichts.

## Auflage 2 — Ein Erzeuger für aktuelle Snapshots, alle drei Wege daran

Verbindlich, und mit dem Bestand abgeglichen:

| Funktion | heute | nach dem Bau |
|---|---|---|
| `bewerte_quote(market)` | reine Quotenbewertung, 40 Prüfungen hängen daran | **unverändert**, Docstring begrenzt sie ausdrücklich auf die Quote |
| `market_to_price_snapshot(market)` | dünne Hülle, gibt `bewerte_quote(...)["snapshot"]` | wird **nicht mehr öffentlich** für aktuelle Preise genutzt; bleibt als Quotenhülle, Docstring sagt „kein aktueller Preis" |
| `fetch_current_price(cid)` | ruft `market_to_price_snapshot` | läuft über `aktueller_snapshot`, gibt bei nicht freigegebenem Status `None` + Grund |
| `scripts/polymarket_refresh.py` | ruft `bewerte_quote` direkt | ruft **`aktueller_snapshot`**, nicht mehr `bewerte_quote` |
| `scripts/polymarket_backfill.py` | `history_to_records` | **ausgenommen und begründet**: historische Zeilen eines inzwischen geschlossenen Marktes sind richtig, Preisart `historie` |

`aktueller_snapshot(raw, db_status=None) -> dict` mit
`{status, endstatus, quote, preis_freigegeben, grund}`. Der Wächter prüft **alle drei**
Einstiegspunkte, nicht nur den neuen.

## Auflage 3 — Helfervertrag je Zweig, vollständig

`update_polymarket_markt_zustand(records)`. Jeder Datensatz nennt `condition_id` und
beliebige Felder aus der Weißliste `{last_fetch_state, last_fetch_at, status,
status_checked_at, active}`. **Nur übergebene Schlüssel werden geschrieben** — kein
Feld wird ergänzt, keines mit `None` überschrieben, wenn der Aufrufer es nicht nennt.

Daraus folgen drei Zweige, und N1 war berechtigt: mein v2-Text verlor die Abruffelder
auf `resolved`.

| Fall | Anweisung | Payload |
|---|---|---|
| Status setzen, Markt nicht aufgelöst | `eq(cid)` + `or_(status.is.null,status.neq.resolved)` | alle übergebenen Felder, also auch `last_fetch_state`/`last_fetch_at` |
| Markt ist aufgelöst | `eq(cid)` + `eq(status,resolved)` | **nur** `last_fetch_state`, `last_fetch_at`, `status_checked_at`, soweit übergeben — `status` und `active` bleiben unberührt |
| nur Abrufzustand, kein Status (Abruf gescheitert) | `eq(cid)` ohne Statusfilter | nur `last_fetch_state`, `last_fetch_at`; **kein** `status_checked_at`, denn geprüft wurde nichts |

Der dritte Zweig ist der heutige `update_polymarket_fetch_state`; der Name bleibt als
dünne Hülle, damit kein Aufrufer bricht.

Der Wächter prüft den **endgültigen `.update()`-Payload** je Zweig, nicht den Aufruf.
Eine Attrappe des ganzen Helfers hätte B3 übersehen — genau das ist passiert.

## Auflage 4 — Exit-Regel mit technischen Fehlern und Schreibfehlern

Die Formel aus v2 ist ersetzt. Drei Zähler, und die Entscheidung hängt an jedem:

```
rot, wenn
    technische_fehler > 0                     # ein Abruf ist gescheitert
 or not schreiben_ok                          # Preis- oder Zustands-Schreibvorgang gescheitert
 or not log_ok                                # refresh_log-Zeile gescheitert (bestehende Regel)
 or (preise == 0 and fachlich_uebersprungen == 0 and entries > 0)
gruen sonst
```

Damit gilt: fachliches Überspringen allein ist **grün** (ein Tag, an dem alle Märkte
legitim geschlossen sind, darf den Backfill nicht verhindern), aber es **neutralisiert
nichts**. Der Gegenfall aus Runde 2 (0 Preise, 1 übersprungen, 25 technische Fehler)
wird rot, weil `technische_fehler > 0` allein genügt. Die bestehende Regel
`success == 0 or not log_ok` bleibt in beiden Teilen enthalten.

Anmerkung zur bisherigen Toleranz: `scripts/polymarket_refresh.py` zählt heute einen
Markt, der nicht im DB-Katalog steht, als `errors`-Eintrag, aber nicht als Grund zum
Scheitern („Dauerzustand und kein Ausfall"). Dieser Fall bleibt **fachlich**, nicht
technisch — sonst wäre der Lauf vor dem ersten Katalogabgleich immer rot. Er wird
getrennt gezählt und gemeldet.

## Auflage 5 — Wächterliste korrigiert und ergänzt

Punkt 2 der Liste aus v2 wird berichtigt: geprüft wird der **vollständige** Filter
`cid AND (status IS NULL OR status <> 'resolved')`, und zwar mit einer Vorrichtung, die
eine `status IS NULL`-Zeile enthält — denn das ist der Bestand. Dazu die Mutation
„NULL-Zweig entfernen" (`or_` → bloßes `neq`), die scheitern **muss**.

Neu in der Liste, aus Codex' Antwort 4:

18. **NULL-Bestand:** Status und `active` werden an einer Zeile mit `status IS NULL`
    tatsächlich aktualisiert. Mutation: `or_` → `neq`.
19. **Fremde Katalogzeile:** beide Anweisungen lassen eine nicht angefragte Zeile in
    **allen** Feldern unverändert.
20. **Auflösung nach dem Kataloglesen:** die Statusanweisung gibt keine Zeile zurück →
    es entsteht keine Preiszeile (Auflage 1, Punkt 1).
21. **Alle drei Snapshot-Wege** (`fetch_current_price`, `market_to_price_snapshot`, der
    echte Refresh-Pfad) laufen über `aktueller_snapshot`.
22. **Fetch-only auf `resolved`:** Abrufzustand und Abrufzeit ändern sich, `status` und
    ein **nicht** übergebener `status_checked_at` bleiben erhalten.
23. **Gemischter Lauf:** fachliches Überspringen **und** technische Fehler → rot; dazu
    ein gescheiterter `refresh_log`-Eintrag → rot.
24. **Discovery-Fehler bis zum Prozess-Exit:** nicht ein Shellblock mit vorgegebenem
    Exit 1, sondern ein echter `--sync-db`-Lauf mit `unklar`, dessen Exit ≠ 0 den
    Workflow erreicht. Der Shelltest allein beweist nur das Verhalten **nach** einem
    Fehlerexit, nicht dessen Erzeugung.

Zur UPDATE-Übersetzung (Runde 2, Frage 2): die SELECT-Messung beweist sie nicht, und ich
habe bewusst nur gelesen. Prüfbar **ohne** Datenbank ist, was der echte Client auf die
Leitung legen würde: die Anfrage wird vor dem Versand abgefangen und auf Methode,
Filter und Payload geprüft. Das ist eine Prüfung am echten Client, keine Attrappe mit
eigener Filtersemantik. Die Wirkung an echten Zeilen bleibt eine Messung, die eine
ausdrückliche Freigabe braucht, und steht als Abnahmeschritt **vor** dem ersten
Schreiben.

## Was unverändert bleibt

Alles aus v2, was Runde 2 abgenommen hat: der Dreischritt mit einem Metadaten-Upsert
ohne Statusfelder, Deduplizierung und Widerspruchsregel im Erzeuger, `active` im
Refresh, der Array-Fehlervertrag des Laders samt noch zu messender Argumentform, die
drei Fälle nach einem gescheiterten Stapel, die Korrektur der Behauptung zur
stündlichen Erneuerung.

## Bitte für Runde 3

1. Trägt Auflage 1 in dieser Form — Entscheidung aus der Antwort des Schreibvorgangs,
   benanntes Restfenster, Absicherung als Vorbedingung von B4?
2. Ist der Helfervertrag mit drei Zweigen vollständig, oder fehlt ein vierter Fall?
3. Macht die Exit-Regel noch einen Lauf grün, der es nicht sein darf?
4. Fehlt in der Wächterliste (1–24) ein Fall, dessen Ausfall niemandem auffiele?
