# Entwurf: GEX-Snapshot läuft seit dem 15.10. jede Nacht ins Yahoo-Loch

**Status:** Entwurf, geht VOR dem Code zur Prüfung.
**Nutzerentscheidung 2026-10-21:** beides bauen — systemd-Timer UND Spot-Regel.

## 1. Der Befund, mit Messdaten

`GEX Snapshot (Dealer Positioning)` ist seit dem 15.10.2026 **fünf Nächte rot**. Kein
Code-Defekt: die in v66.22 diagnostizierte Abendlücke, jetzt belegt.

### 1.1 Yahoo nullt den Tagesbalken für etwa eine Stunde

Proben `/root/yahoo_abend/` (Nacht 16.→17.10., Session 2026-10-16, SPY):

| Abruf (UTC) | `regularMarketTime` | letzter `close` |
|---|---|---|
| 16.10. 20:30 | 1792180800 (16:00 EDT) | 763.23 (noch vorläufig) |
| 16.10. 22:15 | 1792180800 | **763.25** |
| 17.10. 00:15 | 1792180800 | **`null`** |
| 17.10. 00:45 | 1792180800 | **`null`** |
| 17.10. 02:00 | 1792180800 | 763.25 |
| 17.10. 04:30 | 1792180800 | 763.25 |

`regularMarketTime` bleibt korrekt — der Frische-Nachweis in `_spot` besteht also. Es
fehlt allein der Kurs.

### 1.2 Die Wirkung im Code

`scripts/snapshot_gex_massive.py:189` ruft `_spot` VOR der Chain. Fehlt der Kurs, gibt
`_spot` `None` und `analyze_massive` bricht ab, bevor ein einziger Kontrakt geholt wird.
Alle 20 Ticker fallen aus, die Reissleine (`len(results) < 0.6 * len(universe)`) greift,
Exit 1. Das erklärt die Laufzeit von **13 Sekunden** (20 Ticker × ein Yahoo-Abruf).

### 1.3 Die Korrelation ist vollständig

| Start (UTC) | Ergebnis |
|---|---|
| 13.10. 03:01 | grün |
| 14.10. 01:11 | grün |
| 15.10. 00:30 | rot |
| 16.10. 00:21 | rot |
| 17.10. 00:26 | rot |
| 20.10. 01:04 | rot |
| 21.10. 00:35 | rot |

Jeder rote Lauf startete im Loch, jeder grüne davor oder danach. Der Fehlschlag um
**01:04** verlängert das gemessene Loch über 00:45 hinaus auf mindestens 01:10 — die
Yahoo-Proben haben zwischen 00:45 und 02:00 keine Stütze.

Der Cron steht auf **22:15 UTC** und wäre richtig. GitHub startet ihn 2–5 h verspätet
(gemessen 02:06 bis 04:46) und trifft damit seit dem 15.10. jede Nacht das Loch.

### 1.4 Datenschaden

- `gex_summary.json` und `key_levels.json`: Stand **17.10. 08:08** (manueller Lauf).
- `landing/data/gex_history_session/`: nur `2026-10-15` und `2026-10-16`.
- Fehlende Sessions **19.10.** und **20.10.** Die vom 19.10. ist **verloren** — ein
  Chain-Snapshot lässt sich nicht nachträglich abrufen (Massive liefert Historie nur als
  Preise, nicht als OI/IV-Stand).
- Betroffene Seiten: `/dealer-positioning`, `/key-levels`, Vol-Trigger auf `/skew`.

### 1.5 Was Massive im Loch liefert

Proben `/root/massive_abend/`, zwei vollständige Nächte (19.→20. und 20.→21.10.), SPY:

| Abruf (UTC) | `/range/1/day/<session>/<session>` | `/prev` → Balkendatum |
|---|---|---|
| 20:00 – 23:30 | 403 | 200, aber **Vorsession** |
| **00:00 – 01:00** | 403 | 200, **Session** ✅ |
| 01:30 | 403 | **429** |
| 02:00 – 03:30 | 403 | 200, Session |
| ab 04:00 | **200** | 200, Session |

Beide Nächte identisch. Drei Ablesungen:

1. `/prev` kippt **punktgenau um 00:00 UTC** auf die Session. Das war der Grund, aus dem
   es in v66.20 verworfen wurde („liefert die Session DAVOR") — die Aussage stimmt, aber
   nur **vor** 00:00 UTC.
2. Der direkte Tagesbalken bleibt bis 03:30 UTC auf 403 und öffnet ab 04:00 UTC
   (= 0 Uhr New York) — wie dokumentiert.
3. **Die Quellen sind komplementär:** Yahoo trägt bis 00:00 UTC, Massive `/prev` ab
   00:00 UTC. Es gibt keinen Zeitpunkt, an dem beide ausfallen.
4. Ein **429** trat in beiden Nächten im Slot 01:30 auf. Aktien-Aggregate sind bei
   Massive eng rate-limitiert (Probe-Kommentar: „429 schon ab dem 6. Abruf in Folge",
   die Probe arbeitet deshalb mit 15 s Abstand). Eine Wiederholung ist Pflicht.

## 2. Was gebaut wird

### 2.1 Teil A — systemd-Timer (behebt die Ursache)

`sa-gex-snapshot.timer` / `.service` nach dem Muster von `sa-intraday`:

- `OnCalendar=Mon..Fri 22:15 UTC`, `AccuracySec=1min`, `Persistent=false`
  (ein verpasster Snapshot hilft nicht nachträglich — der Chain-Stand ist dann anders).
- `ExecStartPre=warte_auf_app.sh` (Container kann nach einem Deploy neu entstehen).
- Timeout **im Container**: `docker exec … timeout --kill-after=30s 15m python3 -u …`,
  `TimeoutStartSec=18min`. Der volle Lauf braucht gemessen ~8–12 min.
- Der Service führt **beide** Schritte in der Reihenfolge des Workflows aus und bricht
  nach einem gescheiterten Snapshot ab, statt `compute_key_levels` auf veralteter
  `gex_summary.json` rechnen zu lassen — dieselbe Regel wie heute in der YAML.
- `gex_snapshot.yml` behält nur `workflow_dispatch` und startet dieselbe Unit
  (`systemctl start sa-gex-snapshot.service`) — Notauslöser, kein Zeitplan, sonst
  läuft es doppelt.
- `deploy/install_timers.sh`: Unit in `SERVICES`/`TIMERS` aufnehmen.

### 2.2 Teil B — Spot-Regel (das Netz)

`_spot` bekommt eine zweite Quelle. Die Reihenfolge ist bewusst Yahoo zuerst:

1. **Yahoo** wie heute, inklusive `regularMarketTime` ≥ Sessionschluss und Balkendatum
   == Session. Liefert ein gültiger Balken einen Kurs > 0 → fertig. Kostenlos, kein
   Rate-Limit, trägt den regulären 22:15-Termin.
2. Nur wenn Yahoo keinen Kurs hat: **Massive `/v2/aggs/ticker/<SYM>/prev?adjusted=false`**.
   Angenommen wird der Balken **nur**, wenn sein Zeitstempel in New York auf die Session
   fällt. Damit prüft sich die Quelle selbst, und der Fall „Vorsession vor 00:00 UTC"
   kann nicht durchkommen — genau der Fehler, den v66.20 gefunden hat.
3. Bei **429** gedrosselte Wiederholung (Vorschlag: bis zu 3 Versuche, 20 s Abstand,
   `Retry-After` beachten, wenn der Kopf kommt).
4. Fällt auch das aus → `None` wie heute. Die Reissleine bleibt unberührt.

`adjusted=false` ist Pflicht: der Spot ist die Strike-Basis, ein bereinigter Kurs wäre
falsch (dieselbe Begründung wie beim Yahoo-`close` statt `adjclose`).

**Benannte Grenze:** fällt Yahoo für ALLE 20 Ticker aus, kostet der Rückfall bei 20 s
Abstand ~7 min zusätzlich. Das passt in 15 min, ist aber der Grund, warum Massive
zweite und nicht erste Quelle ist.

### 2.3 Teil C — Einordnung in die Produktionssperre (zur Prüfung)

`snapshot_gex_massive.py` und `compute_key_levels.py` stehen heute in `AUSNAHMEN`
(„Options"). Zwei Gründe, das zu überdenken:

- Seit B2 (v66.20) lesen beide den **Börsenkalender** (`letzte_session`, `sitzung_info`
  für Halbtage). Die Begründung „keine Kalendermethode" trägt nicht mehr.
- Als Ausnahme hält der Lauf den geteilten `flock` nicht, also **wartet der Deploy nicht
  auf ihn**. Mit dem Timer um 22:15 UTC trifft das einen abendlichen Push: der
  Container-Austausch würde einen laufenden Snapshot per SIGKILL beenden (dieselbe
  Klasse wie der Brier-Ausfall in v66.11).

Vorschlag: beide nach `PFLICHT`, Unit mit `SuccessExitStatus=75`. Zur Prüfung gestellt,
weil es die Sperrmenge ändert und `verify_produktionssperre.py` Vollständigkeit verlangt.

## 3. Wächter

`scripts/verify_gex_spot.py`, im Deploy-Gate, mit Mutationstest. Geprüft wird gegen
**die echten Probe-Antworten** (als Fixture eingefroren, nicht nachgebaut):

1. Yahoo mit gültigem Balken → Kurs, **kein** Massive-Abruf (zählt die Aufrufe).
2. Yahoo `close = null` (Fixture 17.10. 00:15) → Massive `/prev` mit Session-Balken →
   dessen Kurs.
3. Massive `/prev` mit **Vorsessions**-Balken (Fixture 19.10. 23:00) → verworfen,
   Ergebnis `None`. Das ist der v66.20-Fehler; er darf nicht wiederkehren.
4. Yahoo `regularMarketTime` vor dem Sessionschluss → verworfen, auch wenn ein Kurs da
   ist.
5. Halbtag: Sessionschluss aus dem Kalender statt 16:00 (`sitzung_info`).
6. 429 → Wiederholung, dann Erfolg; dauerhaft 429 → `None`, kein Absturz.
7. `adjusted=false` steht in der angefragten URL.
8. Zeitzone: die Prüfungen laufen unter drei Zonen (UTC, Europe/Berlin,
   America/New_York) — die Balkendatum-Prüfung rechnet in New York.
9. Unit-Vertrag: `OnCalendar` gültig, Timeout im Container, Abbruch vor
   `compute_key_levels`, Unit in `install_timers.sh` gelistet, `gex_snapshot.yml` ohne
   `schedule`.

## 4. Was NICHT gebaut wird

- **Keine Rekonstruktion der Session 19.10.** Der OI/IV-Stand existiert nicht mehr; eine
  Zeile aus Preisen zu bauen wäre eine Erfindung.
- **Keine Änderung an der Reissleine** (0,6 × Universum). Sie hat korrekt gearbeitet —
  sie hat verhindert, dass ein halber Lauf die guten JSONs überbügelt.
- **Keine Änderung an `regularMarketTime`** als Nachweis. Die Probe zeigt, dass er
  verlässlich ist; das Problem lag nie dort.

## 5. Fragen an die Prüfung

1. Ist die Reihenfolge Yahoo→Massive richtig, oder sollte ab einer bestimmten Uhrzeit
   direkt Massive gefragt werden? Letzteres wäre schneller, würde aber eine Zeitgrenze
   festschreiben, die ich nur an zwei Nächten gemessen habe.
2. Reichen zwei Nächte als Beleg für „`/prev` kippt um 00:00 UTC"? Die Grenze ist eine
   UTC-Tagesgrenze, also plausibel strukturell — aber ich habe sie nicht bewiesen,
   sondern beobachtet. Soll die Datumsprüfung die einzige Zusage bleiben (sie ist
   unabhängig von der Uhrzeit) und die Uhrzeit nur Kommentar?
3. Teil C: `PFLICHT` statt `AUSNAHMEN` — richtig, oder zu weit?
4. Übersehe ich einen Verbraucher, der auf `gex_summary.json` mit Tagesstempel statt
   Session rechnet und durch die vier fehlenden Tage still falsch liegt?
