# Entwurf v2: Polymarket B2 zu Ende bauen (+ B1-Nachzug)

Runde 1 war **NICHT TRAGFÄHIG**, zehn Befunde, alle am Code nachgeprüft und alle
zutreffend. Vier betrafen Behauptungen des Entwurfs, nicht den Bestand:

* **B3** „Statusfelder einfach mitgeben" wäre ein stiller No-Op —
  `update_polymarket_fetch_state` baut den Payload aus zwei fest verdrahteten Feldern.
* **B7** „lehnt ab wie `kurse.js`" ist nicht gegeben — `SA.supabase.get` ruft `r.json()`
  ohne `r.ok`, ein PostgREST-Fehlerobjekt scheitert nur zufällig als `TypeError`, und
  `null` wird über `(rows || [])` zum leeren Erfolg.
* **B10** „stündlich erneuert" ist falsch — die Intraday-Unit läuft mit
  `--near-fomc-only` und endet außerhalb des Fensters vor jedem Marktabruf.
* **B4** `active` fehlte im Refresh, obwohl Frontend und Newsletter ausschließlich
  darauf filtern.

Die übrigen sechs sind Eigenschaften des Bestands, auf dem der Entwurf aufbauen wollte.
Die wichtigste Folge: **der Schreibweg wird anders gebaut als in v1.**

---

## 1. Kein Lesen-Ändern-Schreiben mehr — bedingte Schreibvorgänge

v1 wollte die Bestandsstatus lesen, `resolved` in Python schützen und dann schreiben.
Das hat drei Löcher (B1, B5): heterogene Upsert-Payloads gegen `NOT NULL`-Spalten, ein
Bestandsabruf, der mit dem Standard `active_only=True` gerade die aufgelösten Märkte
übersieht, und ein Zeitfenster zwischen Lesen und Schreiben.

**Neu: der Status wird nie durch einen Upsert geschrieben, sondern durch gefilterte
Aktualisierungen, deren Bedingung in der Anweisung selbst steht.**

Je Markt mit Antwort (`abdeckung.markets`), nach `status_aus_markt`:

```
# (a) Status setzen — aber niemals über einen aufgeloesten Markt.
#     `or_` ist NICHT Bequemlichkeit: `status <> 'resolved'` ist fuer eine
#     NULL-Zeile nicht wahr, sondern NULL. Gemessen am 2026-10-20 lesend auf
#     der laufenden DB: alle 26 Katalogzeilen haben `status IS NULL`, und
#     `.neq("status","resolved")` trifft davon GENAU NULL. Mein erster
#     Entwurf haette also beim ersten Lauf nichts geschrieben, ohne zu
#     scheitern — ein vollstaendiger stiller No-Op.
client.table("polymarket_markets").update({
    "status": neu, "status_checked_at": jetzt, "active": neu in STATUS_SICHTBAR,
}).eq("condition_id", cid).or_(
    "status.is.null,status.neq.%s" % STATUS_AUFGELOEST).execute()

# (b) Beim aufgeloesten Markt nur den Pruefzeitpunkt erneuern.
#     Hier ist `eq` richtig: eine NULL-Zeile soll gerade nicht getroffen werden.
client.table("polymarket_markets").update({
    "status_checked_at": jetzt,
}).eq("condition_id", cid).eq("status", STATUS_AUFGELOEST).execute()
```

Gegenprobe derselben Messung: `.or_("status.is.null,status.neq.resolved")` trifft 26 von
26. Die beiden Anweisungen bleiben disjunkt und decken zusammen jede Zeile ab — auch die
mit `status IS NULL`, und das ist der Bestand.

Damit ist der Schutz von `resolved` **eine Eigenschaft der Datenbankanweisung**, nicht
einer vorher gelesenen Kopie. Es gibt kein Fenster, in dem ein zweiter Schreiber
dazwischenkommen kann, und der Standardfilter von `fetch_polymarket_markets` spielt
keine Rolle mehr. Die beiden Anweisungen sind disjunkt (`neq` / `eq` auf dieselbe
Spalte), es wird also immer genau eine wirksam.

Für `abdeckung.fehlt_bestaetigt` dasselbe mit `status = STATUS_UNERREICHBAR`,
`active = False`. **Kein Insert** — eine YAML-ID, die in der Datenbank nie existierte,
aktualisiert null Zeilen; das wird gemeldet (es ist ein YAML-Problem, keine
Katalogzeile). Damit ist B1 erledigt, ohne heterogene Payloads zu brauchen.

Für `abdeckung.unklar`: **keine Anweisung.** Kein Status, kein `status_checked_at`.

Der **Upsert** bleibt, aber nur noch für Metadaten der gefundenen Märkte (`slug`,
`question`, `category`, `end_date`, Token-IDs, Liquidität, Volumen, `meta`) — gleiche
Schlüssel in jeder Zeile, wie heute. `status`, `status_checked_at` und `active` kommen
dort **nicht** mehr vor.

**Reihenfolge bleibt: alle Abrufe zuerst, dann die Schreibphase.** Ein Netzfehler beim
zwölften von 26 Märkten hinterlässt damit keinen halb aktualisierten Katalog.

## 2. Doppelte und widersprüchliche Antworten (B2)

`fetch_markets_mit_abdeckung` hängt heute jede passende Antwort an `markets`; eine
`conditionId`, die zweimal zurückkommt, steht zweimal in der Liste und damit zweimal im
Upsert — `ON CONFLICT DO UPDATE` kann dieselbe Zeile nicht zweimal treffen und bricht
den ganzen Schreibvorgang ab.

Regel im **Erzeuger**, nicht beim Aufrufer:

* Erste Antwort je `conditionId` gewinnt.
* Eine zweite Antwort wird mit der ersten verglichen, und zwar an den Feldern, die die
  Entscheidung tragen: `closed`, `acceptingOrders`, `archived`, `enableOrderBook`.
  Gleich → verworfen. **Ungleich → die ID wandert nach `unklar` und fliegt aus
  `markets`**; widersprüchliche Antworten sind keine Aussage.
* `fremd` bleibt eine Menge (dedupliziert sich selbst).

## 3. Status im Refresh — mit `active`, und die Freigabe am Endstatus (B4, B5, B6, B9)

Der Refresh hat das Rohobjekt schon. Er leitet daraus den Status ab und schreibt ihn mit
denselben zwei bedingten Anweisungen aus Abschnitt 1 — also auch `active`, sonst bleibt
ein geschlossener Markt bis zum nächsten Katalogabgleich sichtbar und ein
wiederaufgetauchter unsichtbar.

**Die Preisfreigabe entscheidet am Endstatus, nicht am gemessenen.** Den
Datenbankstatus hat der Refresh ohne Zusatzabruf: `_fetch_catalog(active_only=False)`
liefert `select("*")`, also auch `status`. Regel:

```
endstatus = STATUS_AUFGELOESt wenn db_status == resolved sonst gemessen
preis schreiben nur wenn endstatus in STATUS_BEWERTBAR
```

Damit kann ein in B4 belegter aufgelöster Markt keinen neuen „aktuellen" Preis
bekommen, auch wenn Gamma ihn als offen meldet.

**Die Sperre gehört zum Erzeuger (B6).** Heute können `fetch_current_price` und
`market_to_price_snapshot` einen Snapshot für einen geschlossenen Markt liefern; nur der
neu gefilterte Aufruf im Refresh wäre geschützt — dieselbe Fehlerklasse, für die das
Projekt schon bezahlt hat. Deshalb:

* `bewerte_quote` bleibt **reine Quotenbewertung** (40 Prüfungen hängen daran) und wird
  im Docstring ausdrücklich darauf begrenzt.
* Neu `aktueller_snapshot(raw, db_status=None) -> dict` mit
  `{status, endstatus, quote, preis_freigegeben, grund}`. Das ist der **einzige** Weg zu
  einem Snapshot, der als *aktueller Preis* gespeichert werden darf.
* `fetch_current_price` läuft über `aktueller_snapshot` und gibt für einen nicht
  freigegebenen Markt `None` mit Grund zurück.
* Der **Backfill** ist davon ausgenommen und bleibt wie er ist: historische Zeilen eines
  inzwischen geschlossenen Marktes sind richtig, und ihre Preisart ist `historie`.

**Exit-Regel (B9).** Heute ist `success == 0` ein Fehlschlag — mit der Preissperre wäre
ein Tag, an dem alle Märkte legitim geschlossen sind, ein roter Lauf, der zusätzlich den
Backfill verhindert. Neu drei getrennte Zähler: `preise`, `fachlich_uebersprungen`,
`technische_fehler`. Exit 1 nur, wenn `preise == 0 und fachlich_uebersprungen == 0 und
entries > 0` — also wenn kein einziger Markt zu *irgendeinem* Ergebnis geführt hat. Ein
Schreibfehler bleibt Exit 1 wie bisher.

## 4. Der Schreibhelfer muss die Felder wirklich führen (B3)

`update_polymarket_fetch_state` schreibt genau `last_fetch_state` und `last_fetch_at`.
Ein Aufrufer, der `status` mitgibt, würde glauben, es sei gespeichert.

Neu: **ein** Helfer `update_polymarket_markt_zustand(records)` mit einer ausdrücklichen
Weißliste (`last_fetch_state`, `last_fetch_at`, `status`, `status_checked_at`,
`active`), der **nur tatsächlich übergebene** Schlüssel in den Payload nimmt und die
beiden bedingten Anweisungen aus Abschnitt 1 ausführt. `update_polymarket_fetch_state`
bleibt als dünne Hülle, damit kein Aufrufer bricht. Der Wächter prüft den **endgültigen
`.update()`-Payload**, nicht den Aufruf — eine Attrappe des ganzen Helfers hätte genau
diesen Befund übersehen.

## 5. Katalogabgleich als Schritt 1 des Daily-Workflows

Wie in v1, mit einer Korrektur der Begründung: der Status wird **täglich** erneuert,
nicht stündlich (B10). Stündlich läuft der Refresh nur im FOMC-Fenster
(`--near-fomc-only`), außerhalb endet er vor jedem Marktabruf. Die Frische eines Status
wird deshalb an `status_checked_at` gemessen und nirgends behauptet.

Der Wächter prüft den **echten Shellblock** mit Attrappen (Codex' Auflage), nicht seine
Textform: Schritt 1 mit Exit 1 muss Schritt 2 und 3 verhindern.

## 6. B1-Nachzug: Frontend auf die Postgres-Funktion

`loadLatestPrices` holt `limit = n*5` Zeilen und reduziert im Browser — ein häufig
aktualisierter Markt kann einen selten aktualisierten herausdrängen.

**Der Fehlervertrag wird gebaut, nicht behauptet (B7).** `SA.supabase.get` prüft weder
`r.ok` noch die Antwortform; das global zu ändern berührt 30 Seiten und ist eine eigene
Entscheidung (eigener Posten, siehe Abschnitt 8). Für diesen Lader gilt:

* Antwort muss ein Array sein, sonst **Ablehnung**. `Array.isArray(rows)` ist die
  Prüfung, die ein PostgREST-Fehlerobjekt und `null` gleichermaßen fängt.
* **Kein Rückfall** auf die Tabellenabfrage. Scheitert die Funktion, zeigt die Seite
  ihren Ladefehler.
* Aufruf: `SA.supabase.get('rpc/polymarket_latest_prices', 'p_condition_ids=' +
  encodeURIComponent('{' + ids.join(',') + '}'))`.

**Die Array-Schreibweise ist eine unverifizierte Schnittstellenannahme** (Codex'
Antwort 3). Sie wird **vor** dem Bauen gemessen, lesend, mit dem Anon-Key über HTTP:
zwei bekannte IDs, eine unbekannte ID, `{}`. Erwartet: genau die Teilmenge, je Markt die
neueste Zeile, keine fremden Zeilen. Fällt die Messung anders aus, wird der Aufruf ohne
Argument gebaut (laut SQL zulässig) und die Teilmenge im Browser gefiltert — dann aber
mit ausdrücklichem Vermerk, dass die Antwortgröße mit dem Bestand wächst.

## 7. Wächter und Mutationen

`scripts/verify_polymarket_status.py`, im Deploy-Gate, Attrappen für Gamma und Supabase,
kein Netz, keine DB. Geprüft wird:

1. Entscheidungstabelle an den gemessenen Feldkombinationen; `resolved` kommt nie heraus.
2. Schreibweg: alle Abrufe vor der ersten Anweisung (die Attrappe protokolliert die
   Reihenfolge), Metadaten-Upsert **ohne** Statusfelder, Statusanweisungen **mit**
   `neq(status, resolved)` bzw. `eq(status, resolved)`.
3. Der endgültige `.update()`-Payload enthält genau die übergebenen Felder — und `status`
   fehlt dort, wenn der Aufrufer ihn nicht übergibt (B3-Regressionsfall).
4. `resolved` überlebt einen Lauf, der `closed` messen würde, und `status_checked_at`
   wird dabei trotzdem erneuert (zweite Anweisung).
5. `fehlt_bestaetigt` → `unavailable` + `active=False`, **kein Insert**; eine ID ohne
   Katalogzeile wird gemeldet.
6. `unklar` kommt in **keiner** Anweisung vor.
7. Doppelte Antwort gleichen Inhalts → ein Eintrag; doppelte Antwort **anderen** Inhalts
   → `unklar`, nicht in `markets` (B2).
8. Nach gescheitertem Stapel **drei** Fälle (B8): Einzelantwort vorhanden → `markets`;
   erfolgreich leer → `fehlt_bestaetigt`; erneut gescheitert → `unklar`.
9. Fremde IDs landen in `fremd` und in keiner Anweisung.
10. Refresh: Abrufzustand `fehler` → **kein** `status_checked_at`.
11. Refresh: nicht bewertbarer Endstatus → **keine** Preiszeile, aber Statuszeile.
12. Refresh: `open → closed` setzt `active=False`, `unavailable → open` setzt
    `active=True` (B4, beide Übergänge).
13. Refresh: DB `resolved` + Gamma `open` → **keine** Preiszeile (B5).
14. Erzeuger: `fetch_current_price` liefert für einen geschlossenen Markt `None` mit
    Grund; `bewerte_quote` bleibt statusfrei (B6).
15. Exit-Regel: Lauf mit 0 Preisen und >0 fachlichen Auslassungen → Exit 0; Lauf mit 0
    und 0 → Exit 1 (B9).
16. Lader: Fehlerobjekt, `null` und Netzfehler führen zur Ablehnung, und **kein**
    Ersatzabruf auf `polymarket_prices` erfolgt (B7) — geprüft an der echten Laderkette.
17. Workflow: echter Shellblock mit Attrappen, Schritt 1 Exit 1 verhindert 2 und 3.

Je Prüfung eine Mutation, die sie reißen **muss**, plus `UNGUELTIG_ERWARTET`.
Beweisregeln: `[Aufbau]` nur für die Vorrichtung, `PROBE-ENDE` muss erreicht werden,
eine Ausnahme ist nie ein Nachweis — auch eine gefangene nicht.

## 8. Eigene Posten, bewusst nicht hier

* **`SA.supabase.get` prüft `r.ok` nicht.** Betrifft jede Seite, nicht nur
  `/polymarket`. Eigener Posten mit eigener Messung — eine globale Änderung am
  Transportweg gehört nicht in ein Polymarket-Paket.
* `resolved` setzen = B4, braucht einen Beleg, der nicht `endDate` ist.
* Gemeinsame Gültigkeitsregel für Seite und Newsletter = B3 der Phase.
* Keine Schemaänderung; die vier Spalten stehen seit dem 2026-10-09.

## 9. Konkrete Bitte

1. Ist der bedingte Schreibweg aus Abschnitt 1 wirklich ohne Lesen-Ändern-Schreiben —
   oder bleibt ein Fall, in dem `resolved` doch überschrieben wird?
2. Beide Fragen zum Filter sind inzwischen **gemessen**, lesend auf der laufenden DB
   (2026-10-20), weil eine falsche Übersetzung hier den ganzen Katalog überschreiben
   würde:

   | Auswahl | Zeilen |
   |---|---|
   | `eq(cid)` | 1 |
   | `eq(cid)` + `or_("status.is.null,status.neq.resolved")` | **1** |
   | `or_(…)` allein | 26 |
   | `eq(cid)` + `eq("status","resolved")` | 0 |

   `eq` und `or_` werden also mit AND verbunden (`cid AND (null OR neq)`), nicht als
   `(cid AND null) OR neq` — die geplante Anweisung trifft genau eine Zeile. Die
   Gegenanweisung trifft im Bestand erwartungsgemäß keine, weil `status` noch NULL ist.

   Bleibt trotzdem etwas offen, das ich nicht messen konnte: gilt dieselbe Verbindung
   auch bei `UPDATE` und nicht nur bei `SELECT`? Ich habe bewusst nur gelesen.
3. Ist die Exit-Regel aus Abschnitt 3 vollständig, oder gibt es einen Lauf, der damit
   grün wird und es nicht sein darf?
4. Fehlt in der Wächterliste ein Fall, dessen Ausfall niemandem auffiele?
