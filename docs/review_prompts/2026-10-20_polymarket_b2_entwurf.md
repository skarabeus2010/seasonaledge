# Entwurf: Polymarket B2 zu Ende bauen (+ ein B1-Nachzug)

Stand 2026-10-20. Gebaut und gepusht ist die Hälfte von B2 (Commit `95209ec`, live mit
`7f6f35d`): der Abdeckungsvertrag `GammaAbdeckung` / `fetch_markets_mit_abdeckung` und
die Entscheidungstabelle `status_aus_markt` in `shared/polymarket_data.py`. Beides lesend
auf der laufenden DB nachgemessen.

Dieser Entwurf geht **vor** der ersten Codezeile zur Prüfung. Grund: in B1 waren drei
meiner Annahmen falsch, und sie hätten auf der Produktionsdatenbank gestanden.

---

## 0. Was heute im Code steht (nachgelesen, nicht erinnert)

| Stelle | Zustand |
|---|---|
| `shared/polymarket_data.py` | `GammaAbdeckung`, `fetch_markets_mit_abdeckung`, `status_aus_markt`, `STATUS_*`, `STATUS_BEWERTBAR`, `STATUS_SICHTBAR`. `normalize_market` gibt `"status"` zurück. |
| `scripts/polymarket_discover.py::sync_catalog_to_db` | Ruft `fetch_market_by_condition_id` **pro Markt** (N Einzelabrufe), `continue` bei Fehlschlag, schreibt `active: True` **unbedingt**, schreibt `status` **nicht** (das Feld aus `normalize_market` wird nicht übernommen), kein `status_checked_at`. |
| `scripts/polymarket_refresh.py::refresh_markets` | Holt pro Markt das ganze Market-Objekt, bewertet die Quote, schreibt `last_fetch_state`/`last_fetch_at`. Nutzt den Status **nicht** und schreibt ihn **nicht**. |
| `.github/workflows/polymarket_daily.yml` | Schritt 1 Refresh, Schritt 2 Backfill (montags). **Kein** Katalogabgleich. |
| `shared/supabase_client.py::fetch_polymarket_markets` | `active_only=True` als Standard. Verbraucher: `weekly_report` 3× mit `active_only=True`; Refresh und Backfill mit `active_only=False`. |
| `landing/js/polymarket.js::loadLatestPrices` | **Nicht** auf die RPC umgestellt: `limit = n*5`, Reduktion im Browser. |

Daraus folgt eine Korrektur an der eigenen Dokumentation: die Zeile „serverseitige
Auswahl der neuesten Zeile in BEIDEN Ladern" (CLAUDE.md, B1) ist zu stark. Umgestellt
wurde nur der Python-Lader.

---

## 1. Schreibweg des Status (`sync_catalog_to_db`)

**Regel: alle Abrufe zuerst, dann genau ein Schreibvorgang.** Heute kann der Lauf nach
dem zwölften von 26 Märkten an einem Netzfehler sterben und einen halb aktualisierten
Katalog hinterlassen.

Neuer Ablauf:

1. Alle `condition_id` aus der YAML sammeln.
2. **Ein** `fetch_markets_mit_abdeckung(cids)`.
3. Bestehende Statuszeilen lesen (`condition_id`, `status`) — nötig für Punkt 4c.
4. Aus der Abdeckung drei Mengen bilden:
   - **`markets`** → `status = status_aus_markt(raw)`, `status_checked_at = now`,
     `active = status in STATUS_SICHTBAR`, dazu die Metadaten wie heute.
   - **`fehlt_bestaetigt`** → `status = STATUS_UNERREICHBAR`, `status_checked_at = now`,
     `active = False`, **keine** Metadatenfelder (wir haben keine). Die Zeile bleibt im
     Abgleich, damit ein Wiederauftauchen den Markt zurückholt.
   - **`unklar`** → **gar nicht schreiben.** Kein Status, kein `status_checked_at`. Ein
     technischer Fehlschlag ist keine Aussage über den Markt.
5. Ein `upsert_polymarket_markets(alle_zeilen)`.

**4c — `resolved` darf nicht überschrieben werden.** `status_aus_markt` gibt per
Erkenntnisgrenze nie `resolved` zurück, würde einen in B4 belegten Markt aber zu
`closed` zurückdrehen. Regel: steht in der DB schon `resolved`, bleibt `status`
unverändert; `status_checked_at` wird erneuert (geprüft wurde ja). Das ist die
Aufrufstelle, von der der Docstring von `status_aus_markt` spricht.

**Sichtbare Warnung ohne Abbruch:** `fehlt_bestaetigt` ist heute nicht leer
(`fed-hike-2026`). Der Lauf meldet die Liste auf stdout und setzt die Zeilen auf
`unavailable`, läuft aber weiter und endet mit Exit 0. `unklar` dagegen ist ein
Fehlschlag des Laufs → Exit ≠ 0, denn danach ist der Katalog unvollständig
aktualisiert.

**Offene Frage an den Prüfer:** `active = status in STATUS_SICHTBAR` bedeutet, dass ein
`closed` gewordener Markt aus `weekly_report` (dreimal `active_only=True`) und aus dem
Frontend (`active=eq.true`) verschwindet, während Refresh und Backfill ihn weiter sehen
(`active_only=False`). Das halte ich für richtig — ein geschlossener Markt gehört nicht
in eine Wahrscheinlichkeitsanzeige, und das Weiterprobieren erlaubt ein
Wiederauftauchen. Ist das die Semantik, die `active` heute schon hat, oder breche ich
damit eine andere Erwartung?

---

## 2. Status im Refresh (stärker als ein Filter)

`refresh_markets` holt pro Markt bereits `fetch_market_by_condition_id(cid)` — es hat
das Rohobjekt, aus dem `status_aus_markt` liest. Statt den Status nur zu *filtern*,
**schreibt der Refresh ihn mit**, aus derselben Antwort, aus der auch der Preis kommt.
Das ist der Punkt, an dem der Status nicht veralten kann: er wird jede Stunde erneuert,
nicht einmal täglich.

Also je Markt:

- Status aus `markt` ableiten (bei Abrufzustand `fehler`: **nichts** schreiben, auch
  nicht `status_checked_at`).
- `last_fetch_state`, `last_fetch_at`, `status`, `status_checked_at` in **einer** Zeile
  an `update_polymarket_fetch_state` (das ist bewusst ein `.update().eq()`, kein Upsert,
  damit ein unbekannter Markt keine halbe Katalogzeile anlegt).
- `resolved` in der DB bleibt `resolved` — gleiche Regel wie 4c, gleiche Hilfsfunktion.
- **Preiszeile nur, wenn der gemessene Status in `STATUS_BEWERTBAR` liegt.** Ein
  geschlossener Markt liefert `outcomePrices ["0","0"]`; eine solche Zeile als frischen
  Preis zu speichern ist genau der Fehler, den B1 an anderer Stelle geschlossen hat.
  Der Fall wird gezählt und gemeldet, nicht verschluckt.

Damit ist `active` nicht die einzige Bremse, und B3 bekommt eine Statusangabe, deren
Alter aus `status_checked_at` ablesbar ist.

**Offene Frage:** soll ein `paused` Markt eine Preiszeile schreiben? Mein Vorschlag:
nein (`STATUS_BEWERTBAR` ist nur `open`), aber sichtbar bleiben (`STATUS_SICHTBAR`
enthält `paused`) — die Seite zeigt dann den letzten bekannten Preis mit Alter, statt
einen Preis zu erfinden. Gegenargument?

---

## 3. Katalogabgleich als Schritt 1 des Daily-Workflows

`polymarket_daily.yml` bekommt vor dem Snapshot:

```
echo "[polymarket-daily] Step 1/3: Katalogabgleich (Status)"
if ! docker exec seasonalpha-app python3 scripts/polymarket_discover.py --sync-db 2>&1 | tail -40; then
  echo "[polymarket-daily] FEHLER: Katalogabgleich fehlgeschlagen"
  exit 1
fi
```

Die bestehenden Schritte werden zu 2/3 und 3/3. `set -euo pipefail` steht schon da.
Wichtig und ausdrücklich zu prüfen: **ein Fehlschlag in Schritt 1 verhindert Schritt 2
und 3.** Dafür kommt eine eigene Mutation (Schritt 1 auf `exit 1` gesetzt → der
Wächter muss sehen, dass Refresh und Backfill nicht laufen).

---

## 4. B1-Nachzug: Frontend auf die RPC

`loadLatestPrices` holt `limit = conditionIds.length * 5` Zeilen nach `ts desc` und
nimmt im Browser die erste je Markt. Bei 26 Märkten sind das 130 Zeilen; ein häufig
aktualisierter Markt kann einen selten aktualisierten vollständig herausdrängen, und
ein Markt ohne Zeile im Fenster fällt heraus. Beides endet im Verbraucher als Preis 0 —
dasselbe, was der Python-Lader seit B1 nicht mehr macht.

Umstellung auf `SA.supabase.get('rpc/polymarket_latest_prices?...')`. Zu klären, und
deshalb hier gefragt statt geraten:

- Die Funktion nimmt `p_condition_ids TEXT[] DEFAULT NULL`. Über `GET` auf
  `rpc/<name>` müssen Argumente als Query-Parameter kommen. Für ein `text[]` ist die
  Schreibweise `p_condition_ids={a,b,c}` (geschweifte Klammern, URL-kodiert). Ist das
  der Weg, oder ruft man die Funktion ohne Argument (`NULL` → alle Märkte) und
  filtert dahinter? Der Katalog hat 26 Einträge; ein Aufruf ohne Argument wäre
  einfacher und robuster, kostet aber alle Märkte statt der angefragten.
- `GRANT EXECUTE` steht für `anon` in der Migration, und ein `curl` mit Anon-Key gab
  in der Abnahme 200. Fehlt etwas, das nur bei `GET` statt `POST` auffällt?
- Rückfall: **keiner.** Scheitert der Aufruf, lehnt der Lader ab, wie `kurse.js` es
  tut. Ein stiller Rückfall hätte den Fehler weitergetragen.

---

## 5. Wächter und Mutationen

Ein Wächter `scripts/verify_polymarket_status.py`, im Deploy-Gate, mit Attrappen für
Gamma und Supabase (kein Netz, keine DB). Geprüft wird:

1. Die Entscheidungstabelle an den **gemessenen** Feldkombinationen (offen, geschlossen,
   pausiert, archiviert-aber-offen, `closed` fehlt, `closed` kein Wahrheitswert,
   `acceptingOrders` null) — und dass `resolved` nie herauskommt.
2. Der Schreibweg: alle Abrufe vor dem ersten Schreiben (die Attrappe zählt die
   Reihenfolge), genau **ein** Upsert, `unklar` kommt in **keiner** geschriebenen Zeile
   vor, `fehlt_bestaetigt` wird `unavailable` mit `active=False`.
3. `resolved` in der DB überlebt einen Lauf, der `closed` messen würde, und
   `status_checked_at` wird dabei trotzdem erneuert.
4. Ein gescheiterter **zweiter** Stapel macht den ganzen Lauf zu `unklar` für dessen IDs
   und führt nicht zu `unavailable`.
5. Fremde und doppelte IDs in der Antwort.
6. Der Refresh schreibt bei Abrufzustand `fehler` **kein** `status_checked_at`.
7. Der Refresh schreibt **keine** Preiszeile für einen nicht bewertbaren Status, aber
   die Statuszeile.
8. Wiederauftauchen: ein Markt, der einen Lauf `unavailable` war, wird im nächsten Lauf
   wieder `open` mit `active=True`.
9. Der Workflow: Schritt 1 vorhanden, und ein Fehlschlag dort verhindert 2 und 3
   (Textprüfung auf die `if ! … exit 1`-Form plus eine Mutation, die sie entfernt).

Je Prüfung eine Mutation, die sie reißen **muss**, mit `UNGUELTIG_ERWARTET` für die,
die das Urteil des Tests selbst prüfen. Beweisregeln wie gehabt: `[Aufbau]` nur für die
Vorrichtung, `PROBE-ENDE` muss erreicht werden, eine Ausnahme ist nie ein Nachweis —
auch eine gefangene nicht.

---

## 6. Was dieser Entwurf ausdrücklich NICHT macht

- **Kein** `resolved` setzen. Das ist B4 und braucht einen Beleg, der nicht `endDate`
  ist.
- **Keine** Schemaänderung. Die Spalten `status`, `status_checked_at`,
  `last_fetch_state`, `last_fetch_at` stehen seit der Migration vom 2026-10-09.
- **Keine** Verbraucheränderung an Seite oder Newsletter über Punkt 4 hinaus. Die
  gemeinsame Gültigkeitsregel ist B3.
- **Kein** Deploy, kein Workflow-Dispatch, keine DB-Schreibzugriffe aus dieser Sitzung.

## 7. Konkrete Bitte

Bitte vor allem gegen diese vier Punkte prüfen:

1. Ist der Dreischritt „alle Abrufe → Status lesen → ein Upsert" an einer Stelle
   angreifbar, an der ich ihn für dicht halte?
2. Bricht `active = status in STATUS_SICHTBAR` eine bestehende Erwartung?
3. Ist der `GET`-Aufruf der Postgres-Funktion mit `text[]`-Argument so möglich, wie in
   Punkt 4 beschrieben — und wenn nicht, was ist der Weg?
4. Fehlt in der Wächterliste ein Fall, dessen Ausfall niemandem auffiele?
