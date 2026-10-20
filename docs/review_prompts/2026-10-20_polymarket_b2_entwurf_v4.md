# Entwurf v4: Polymarket B2 — die drei verbleibenden Auflagen aus Runde 3

Delta auf v3 (`2026-10-20_polymarket_b2_entwurf_v3.md`), das unverändert gilt, soweit
hier nichts anderes steht. Runde 3: **TRAGFÄHIG MIT AUFLAGEN**, Auflagen 1 und 3 aus
Runde 2 erfüllt, drei Präzisierungen offen.

---

## Auflage 1 — Der Snapshot-Vertrag, widerspruchsfrei

N1 ist berechtigt, und der Widerspruch ist mein eigener: v3 ließ
`market_to_price_snapshot` als Quotenhülle bestehen und verlangte im selben Dokument
(Wächterpunkt 21), dass dieser Einstiegspunkt über `aktueller_snapshot` läuft. Beides
gleichzeitig geht nicht, und ein Docstring sperrt keinen Preis.

**Die Ursache ist der Name.** `market_to_price_snapshot` verspricht einen *Preis*-
Snapshot, trägt aber nur eine Aussage über die *Quote*. Solange dieser Name öffentlich
ist, wird ihn jemand für einen aktuellen Preis benutzen — genau die Fehlerklasse „die
Regel sitzt an der Aufrufstelle statt am Erzeuger". Deshalb verschwindet der Name aus
der öffentlichen Fläche, statt ihn mit zwei Verträgen zu belegen:

| Name | Rolle | Sichtbarkeit |
|---|---|---|
| `bewerte_quote(market)` | Quotenqualität: `ok` / `kein_preis` / `verworfen` samt Grund | öffentlich, **unverändert** (40 Prüfungen hängen daran) |
| `_quote_snapshot(market)` | heutiges `market_to_price_snapshot`, reine Hülle über `bewerte_quote(...)["snapshot"]` | **privat** |
| `aktueller_snapshot(raw, db_status=None)` | der EINZIGE Weg zu einem Snapshot, der als aktueller Preis gespeichert werden darf; prüft Status **und** Quote | öffentlich, neu |
| `fetch_current_price(cid)` | ruft `aktueller_snapshot`; nicht freigegeben → `None` + Grund | öffentlich, unverändert in der Signatur |

Damit ist Wächterpunkt 21 erfüllbar: geprüft wird, dass **kein öffentlicher Name außer
`aktueller_snapshot`** einen Snapshot liefert, der als aktueller Preis durchgeht, und
dass `fetch_current_price` sowie der echte Refresh-Pfad darüber laufen.

**Eine Nebenwirkung, die ich benenne, statt sie zu übersehen:**
`scripts/verify_polymarket_preisqualitaet.py` importiert heute
`market_to_price_snapshot` und prüft damit unter anderem, dass ein gekreuztes Buch
`None` ergibt. Dieser Wächter wird auf `bewerte_quote(...)["snapshot"]` umgestellt —
eine Umbenennung, keine inhaltliche Änderung: seine 40 Prüfungen behalten ihre
Bedeutung, weil sie Aussagen über die **Quote** sind und nie über den Status. Das steht
hier, weil eine stille Anpassung eines bestehenden Wächters genau das ist, wovor die
Projektregeln warnen.

Codex' Vorschlag war, `market_to_price_snapshot` über den statusprüfenden Erzeuger zu
führen. Das wäre die Alternative; ich halte das Privatmachen für besser, weil es den
irreführenden Namen **beseitigt** statt ihn zu reparieren, und weil ein statusprüfender
`market_to_price_snapshot` mit Rohdaten ohne Statusfelder für jede gültige Quote `None`
liefern würde — die bestehenden Positivfälle des Quotenwächters wären dann nicht mehr
prüfbar. Wenn du die andere Variante für richtiger hältst, sag es; ich baue nicht beide.

## Auflage 2 — Katalogauslassungen begründen keinen Erfolg

N2 ist berechtigt. In v3 wären 26 fehlende Katalogeinträge als „fachlich übersprungen"
durchgegangen und hätten einen Lauf ohne einen einzigen bearbeiteten Markt grün gemacht
— während der Bestand denselben Fall über `success == 0` rot beendet
(`scripts/polymarket_refresh.py:237`).

**Vier Zähler statt drei**, und nur einer begründet Erfolg:

| Zähler | wann | begründet Erfolg |
|---|---|---|
| `preise` | Preiszeile geschrieben | ja |
| `fachlich_uebersprungen` | Markt **erreicht**, Status gemessen, Status nicht bewertbar (geschlossen, pausiert, unbekannt) | ja |
| `katalog_fehlt` | `condition_id` nicht im DB-Katalog — der Markt wurde nie abgefragt | **nein** |
| `technische_fehler` | Abruf gescheitert, Ausnahme, kein Markt | nein, erzwingt Rot |

```
rot, wenn
    technische_fehler > 0
 or not schreiben_ok                 # Zustands-UPDATE oder Preis-Upsert gescheitert
 or not log_ok                       # refresh_log-Zeile gescheitert (bestehende Regel)
 or (preise == 0 and fachlich_uebersprungen == 0 and entries > 0)
gruen sonst
```

Der Unterschied zu v3 steckt allein in der Zuordnung: `katalog_fehlt` zählt nicht als
fachliche Auslassung. Damit wird der Fall „alle 26 fehlen im Katalog" rot (preise 0,
fachlich 0, entries 26) — wie heute —, und „ein Markt geschlossen, 25 technische
Fehler" bleibt rot über den ersten Term. `katalog_fehlt` wird weiter gemeldet und bleibt
**kein** technischer Fehler, sonst wäre jeder Lauf vor dem ersten Katalogabgleich rot.

## Auflage 3 — Die drei Gegenproben, am echten Pfad

Verbindlich in die Wächterliste, und ausdrücklich **gegen `refresh_markets`/`main`**,
nicht gegen eine nachgebaute Exit-Formel — eine Prüfung, die nur die Formel nachrechnet,
kann bestehen, ohne dass der geprüfte Code läuft:

25. **Direkter Aufruf des alten Erzeugers:** geschlossener Markt mit ansonsten gültiger
    Quote ergibt über keinen öffentlichen Namen einen aktuellen Snapshot. Mutation:
    `_quote_snapshot` wieder öffentlich machen und im Refresh verwenden.
26. **Alle angefragten IDs fehlen im DB-Katalog** → `main` endet mit Exit ≠ 0.
27. **Zustands-UPDATE scheitert** bei bereits vorhandenen Erfolgen → Exit ≠ 0;
28. **Preis-Upsert scheitert** bei bereits vorhandenen Erfolgen → Exit ≠ 0.

Zu 27/28 getrennt, weil es zwei Schreibwege sind und ein gemeinsamer Zähler den Ausfall
des einen durch den Erfolg des anderen verdecken könnte.

## Zur Betriebsannahme aus Runde 3, Antwort 1

Codex hält fest, dass „niemand außerhalb des Repositorys löst den Live-Status auf" eine
Betriebsannahme bleibt und die 26-NULL-Messung keine Abwesenheit konkurrierender
Schreiber beweist. Das übernehme ich wörtlich als Annahme, nicht als Nachweis. Prüfbar
wäre sie durch eine Inventarisierung der produktiven Schreibwege auf
`polymarket_markets` — das ist eine eigene, lesende Aufgabe und **Vorbedingung von B4**,
zusammen mit der transaktionalen Preisfreigabe. Für B2 wird eine transaktionale
Preisfreigabe ausdrücklich **nicht** zugesagt.

## Bitte für Runde 4

1. Ist das Privatmachen von `market_to_price_snapshot` die richtige Auflösung des
   Widerspruchs — oder soll es die statusprüfende Variante sein, mit der dann
   begründeten Anpassung der Positivfälle im Quotenwächter?
2. Macht die Vier-Zähler-Regel noch einen Lauf grün, der es nicht sein darf?
3. Fehlt in der Liste 1–28 ein Fall, dessen Ausfall niemandem auffiele?
