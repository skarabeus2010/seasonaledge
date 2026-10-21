# Entwurf v4 — Stufe 1: GEX-Snapshot wieder pünktlich und lochfest

**Status:** Entwurf v4 nach Codex-Runde 3 (nicht tragfähig, M1–M6; N1 zu meinen Gunsten
entschieden, N4 und N7 abgenommen).

**Nutzerentscheidungen 2026-10-21:**
1. Timer **und** Spot-Regel bauen.
2. **Gestuft.** Dieser Entwurf ist **Stufe 1**. Was in Stufe 2 geht, steht in Abschnitt 6
   — nicht als Absicht, sondern als Liste mit Begründung.
3. Die am 21.10. nachgeholte Archivzeile für Session 20.10. **bleibt und wird nicht
   gekennzeichnet.** Damit entfallen Herkunftsfeld, Versionierung und
   Qualitätskennzeichen aus dem Bau. Die Folge ist benannt (Abschnitt 5) und nicht
   erneut zur Debatte gestellt.

## 1. Vorbedingung (unverändert, B1)

Die Diagnose bleibt eine Hypothese, bis das Job-Log eines roten Laufs pro Ticker
`[spot] <T>: kein Tagesbalken der Session <datum> — verworfen` zeigt, gefolgt von
`[snapshot] ABBRUCH: nur 0/20 Ticker brauchbar`.

**Durch Ausschluss verengt** (neu gegenüber v3, mit eigenen Messungen):

| Alternativerklärung aus Runde 1 | Status |
|---|---|
| `MASSIVE_API_KEY` fehlt → Exit 1 | **ausgeschlossen** — dieselbe `.env` lief am 21.10. zweimal durch |
| offener Markt → Exit 2 | **ausgeschlossen** — `pruefe_eod_fenster` gegen alle fünf Startzeiten gerechnet, jedes Mal „EOD ok" |
| Chain-HTTP-Fehler / zu wenige Kontrakte | **unwahrscheinlich** — die Chain wird paginiert geholt, 20 Ticker brauchen weit mehr als 13 s |
| Spot-Ausfall | **übrig**, und für die Nacht 16.→17.10. gemessen |

Offen bleibt allein, ob Yahoo in den anderen vier Nächten `null` lieferte oder eine
kaputte Struktur. Beides sind Spot-Ausfälle, beide behandelt die neue Regel.

## 2. Spot-Regel

### 2.1 Zwei Quellenadapter, eine gemeinsame Prüfung (N4, abgenommen)

| Adapter | prüft quellenspezifisch |
|---|---|
| Yahoo | `chart.result[0]` vorhanden · `timestamp` und `close` **gleich lang** · **genau ein** Balken mit Sessiondatum in New York · Zeitstempel in **Sekunden** |
| Massive `/prev` | **genau ein** Ergebnis · Antwortsymbol == angefragtes Symbol · `t` in **Millisekunden** im plausiblen Bereich · Balkendatum in New York == Session |

Gemeinsam geprüft wird nur der normalisierte Satz `{symbol, session, kurs}`: `kurs` ist
`int`/`float`, **kein `bool`**, endlich, > 0. Gemessen: `True > 0` ist `True` und
`float(True)` = 1.0, `inf > 0` ist `True` — beides lässt die heutige Prüfung `c > 0`
durch (`snapshot_gex_massive.py:134`). Die Verschärfung gilt für beide Quellen.

Rückfall nur für **belegte Aktien-/ETF-Symbole**; `--tickers` nimmt beliebige, ein nicht
unterstütztes ergibt kontrolliert `None`. **Keine Indexunterstützung.**
`adjusted=false` ist Pflicht — der Spot ist die Strike-Basis.

### 2.2 Das Zukunftstor entfällt (M6, andere Folgerung als Codex)

v3 hatte als eigene Verschärfung vorgesehen: `rmt` darf nicht in der Zukunft liegen.
M6 weist zu Recht nach, dass das den Bestandswächter reißt — und zwar schärfer als
beschrieben: `_uhr` wird nur **innerhalb** von `_gex_lauf` gestellt
(`verify_gex_session.py:83-85`), die direkten `_spot`-Prüfungen ab Zeile 231 laufen mit
der Uhr des letzten Laufs (`NACH_MITTERNACHT` = 17.10. 01:30 UTC), während das
Folgetag-Fixture `rmt` auf 17.10. 14:00 UTC setzt — 12,5 h „in der Zukunft". Die
Halbtag-Fixtures liegen im November.

Codex schlägt vor, je Test eine eigene Uhr zu stellen. **Ich ziehe die Verschärfung
stattdessen zurück.** Begründung: das Tor verhindert keinen gemessenen Fehlschlag, und es
kann auch keinen falschen Kurs verhindern — die Balkenauswahl läuft über das
**Sessiondatum** (`snapshot_gex_massive.py:135-140`), `rmt` ist nur ein zusätzliches Tor.
Ein unsinniger Anbieter-Zeitstempel würde also höchstens einen Kurs *durchlassen*, der
ohnehin der Schluss der Zielsession ist. Dafür einen grünen Bestandswächter chirurgisch
umzubauen, ist Aufwand und Risiko ohne Gegenwert — und „Zusagen nicht über den Plan
hinaus ausweiten" ist eine Lehre aus v66.13.

**Bleibt** aus M6: die Eindeutigkeit. Genau **ein** Balken mit Sessiondatum; mehrere
bedeuten eine kaputte Antwort und werden verworfen. Das ist ein Adaptervertrag, keine
Uhrfrage, und berührt den Bestandswächter nicht.

### 2.3 Wann der Rückfall öffnet

`_spot` liefert statt `None` einen benannten Grund. Nur **einer** öffnet den Rückfall:

| Grund | darf Massive ersetzen? |
|---|---|
| genau ein Balken der Session, `close` leer oder ungültig, `rmt` ≥ Sessionschluss | **ja** — das Loch |
| `rmt` fehlt oder < Sessionschluss | nein |
| kein Balken · mehrere Balken der Session · keine Antwort · Struktur kaputt | nein |

**Benannte Grenze des Massive-Nachweises** (Antwort 2 aus Runde 3, abgenommen): `/prev`
liefert kein `rmt`-Äquivalent. Akzeptiert wird ein **zum abgeschlossenen Sessiontag
passendes Anbieteraggregat** — nicht der Nachweis eines letzten Handels zur
Schlusssekunde. Dass die Session vorbei ist, steht vor dem Abruf fest
(`letzte_session` + `pruefe_eod_fenster` + Handelstagprüfung aus 3.1). Mehr kann die
Quelle nicht leisten. **Keine Zusage über einen „amtlichen" oder unkorrigierbaren
Schluss** — diese Formulierung aus v3 ziehe ich zurück, sie war durch keinen Code gedeckt.

Bei **429** gedrosselte Wiederholung mit `Retry-After`; danach `None`. Die Reissleine
(0,6 × Universum) bleibt unberührt.

## 3. Betrieb

### 3.1 Betriebsmodi — mit ausdrücklicher Reparatur (M2)

Gemessen: an Thanksgiving 2026 (Donnerstag), am 25.12. und am 03.07. feuert ein
Werktagstimer, `markt_offen` ist `False`, und `letzte_session` zeigt auf eine Session,
die in der Nacht davor schon veröffentlicht wurde.

M2 hält zu Recht fest, dass ein pauschaler „automatisch"-Standard einen **manuellen
Reparaturlauf am Feiertag** mitsperren würde — und der Notauslöser
`gex_snapshot.yml` ruft ohne Schalter auf. Also drei benannte Modi, Zuordnung je
Aufrufer:

| Modus | Aufrufer | Handelstagprüfung | schreibt |
|---|---|---|---|
| `automatisch` (Standard) | `sa-gex-snapshot.service` | **ja** — kein Handelstag → „übersprungen", **ohne Abruf** | ja |
| `--reparatur` | `workflow_dispatch`, Mensch | nein | ja |
| `--no-write` | Prüfung, Wächter | nein | nein |

Der Notauslöser bekommt `--reparatur` ausdrücklich mitgegeben, sonst wäre er am Feiertag
wertlos. Die Handelstagprüfung rechnet **in New York**: die Testfälle um 01:30 UTC
(`verify_gex_session.py:71`) liegen dort noch am Freitag und dürfen nicht reißen.

**Teilmengenläufe** (`--tickers`) schreiben heute dieselben Produktionsdateien und
bewerten die Mindestabdeckung relativ zur Teilmenge (M2). Stufe 1 ändert daran nichts,
**und genau deshalb darf Stufe 1 keine Vollständigkeitsprüfung einführen** — sie würde
einen Dreiticker-Lauf als fertige Tagesveröffentlichung lesen. Die
Vollständigkeitsprüfung gehört mit der Laufsperre in Stufe 2 (Abschnitt 6).

### 3.2 Die Kette — fünf Ergebnisse, nicht vier (M3)

v3 hatte vier Zustände und ordnete den **erfolgreichen Trockenlauf** keinem zu. `--no-write`
gibt heute 0 zurück (`snapshot_gex_massive.py:303-305`). Würde die Hülle 0 als
„veröffentlicht" lesen, startete ein Trockenlauf die **schreibenden** Key Levels. Das
ist derselbe Fehler, den ich in v3 bei „übersprungen" schon einmal gemacht hatte —
zweimal zu wenige Zustände in zwei Entwürfen hintereinander.

| Snapshot-Ergebnis | Key Levels | Exit der Kette |
|---|---|---|
| **veröffentlicht** | laufen | 0 |
| **übersprungen** (kein Handelstag) | laufen **nicht** | 0 |
| **trocken** (`--no-write`) | laufen **nicht** | 0 |
| **unterdrückt** (Produktionssperre) | laufen **nicht** | 75 |
| **fehlgeschlagen** | laufen **nicht** | ≠ 0, ≠ 75 |

Das Ergebnis wird **nicht** aus dem Exit-Code geraten: der Snapshot schreibt es als
Marker-Zeile auf stdout, die Hülle liest sie, und ein **fehlendes** Ergebnis gilt als
„fehlgeschlagen". `SuccessExitStatus=75` sitzt am **äußeren** Rand der Hülle, nicht an
einem einzelnen Schritt.

### 3.3 systemd-Timer

`sa-gex-snapshot.timer` / `.service` nach dem Muster `sa-intraday`:
`OnCalendar=Mon..Fri 22:15 UTC`, `AccuracySec=1min`, `Persistent=false`,
`ExecStartPre=warte_auf_app.sh`, Timeout **im Container**. Eine Hülle, ein `ExecStart`.
`gex_snapshot.yml` behält nur `workflow_dispatch`, startet dieselbe Unit mit
`--reparatur` und bekommt **keinen** `schedule` — sonst läuft es doppelt.
`deploy/install_timers.sh`: Unit in `SERVICES`/`TIMERS`.

### 3.4 Produktionssperre (B7, abgenommen)

`modul_sperre("<name>")` auf Modulebene, `with produktion("<name>")` im `__main__`,
Entfernen aus `AUSNAHMEN` — Muster `nightly_refresh.py:18,580`. Für **beide** Programme.
Die bestehenden GEX-Wächter importieren diese Module; ihre Sperrverzeichnisse bleiben
isoliert.

Nebenwirkung, die zählt: damit **wartet der Deploy** auf einen laufenden Snapshot. Das
ist der Grund, warum der nicht atomare Schreibweg in Stufe 1 bleiben darf (Abschnitt 6).

### 3.5 Zeitbudget (N7, abgenommen als Vertrag)

Gemessen am 21.10.: Snapshot allein ~7 min (06:36 → 06:43, 20/20 Ticker). **Bevor eine
Zahl in die Unit kommt, wird die Kette einmal zusammen gemessen.** Das Budget beginnt
**vor** Sperrerwerb und Imports und deckt: Wartezeit auf die Produktionssperre (ihr
`flock` hat selbst keine Frist, `produktionssperre.py:177`), `warte_auf_app.sh`, beide
Yahoo-Hosts (`yahoo_downloader.py:81`), die paginierten Chains **beider** Programme
(`compute_key_levels.py:60` holt eine zweite), Wiederholungen und Kill-Nachlauf. Das
äußere `TimeoutStartSec` liegt darüber. Dauer-429 für alle 20 Ticker wird mit
**gestellter Uhr** geprüft.

## 4. Wächter (Stufe 1)

`scripts/verify_gex_spot.py` im Gate, mit Mutationstest, Fixtures aus den **echten**
Probe-Antworten.

| # | Fall | aus |
|---|---|---|
| 1 | Yahoo gültig → Kurs, **kein** Massive-Abruf (Aufrufe gezählt) | B3 |
| 2 | Yahoo `close = null`, `rmt` ≥ Schluss (Fixture 17.10. 00:15) → Massive-Kurs | B3 |
| 3 | Massive-Balken der **Vorsession** (Fixture 19.10. 23:00) → verworfen | v66.20 |
| 4 | `rmt` < Sessionschluss **plus** gleichdatierter Massive-Balken → verworfen | B3 |
| 5 | **mehrere** Balken mit Sessiondatum → verworfen, bei beiden Quellen | M6 |
| 6 | Massive leer · 403 · Timeout · Struktur kaputt · falsches Symbol · `c` als `bool` · `inf` · Sekunden statt Millisekunden → je `None`, kein Absturz | B4, N4 |
| 7 | Yahoo-Adapter: `timestamp` und `close` **verschieden lang** → verworfen | N4 |
| 8 | 429 → Wiederholung, dann Erfolg; Dauer-429 → `None`; **gestellte Uhr**, der Test wartet nicht | N7 |
| 9 | Fixtures **beiderseits des 01.11.2026** (Sommer-/Winterzeit) | B10 |
| 10 | **Echter Halbtag**, Schlusszeit unabhängig aus `sitzung_info` festgelegt | B10 |
| 11 | Feiertag, Modus `automatisch` → „übersprungen", **kein Abruf**, keine Datei, Key Levels laufen nicht | B5, N3 |
| 12 | Feiertag, Modus `--reparatur` → läuft und schreibt | M2 |
| 13 | `--no-write` am Feiertag und am Handelstag → erlaubt, schreibt nichts, Key Levels laufen **nicht** | M3 |
| 14 | Hülle bei jedem der fünf Ergebnisse: Key Levels laufen **nur** bei „veröffentlicht"; fehlender Marker ⇒ „fehlgeschlagen" | M3 |
| 15 | `main` bei 11/20 und 12/20 brauchbaren Tickern: unter der Grenze **jede** Ausgabedatei unverändert (Hash vor/nach) | B10 |
| 16 | `adjusted=false` in der URL; Unit-Vertrag (`systemd-analyze`, Timeout im Container, in `install_timers.sh`, `gex_snapshot.yml` ohne `schedule`, Notauslöser mit `--reparatur`) | B5, B8 |
| 17 | Bestandswächter `verify_gex_session.py` bleibt **unverändert grün** | M6 |

Die Hülle wird **ausgeführt**, nicht als Textmuster gesucht
(`verify_produktionssperre.py:423` erkennt nur direkte Skriptnamen). Mutationen treffen
den Produktionspfad; fehlender Anker oder Absturz zählt als **ungültig**, nicht als
gefangen.

## 5. Folge der Nutzerentscheidung zur Nachholzeile

Entschieden: die Zeile bleibt, ohne Kennzeichen. Damit gilt:

- Es gibt **kein** Herkunftsfeld, also auch keine Auswahlregel für historische
  Vergleiche (M5 entfällt mit der Entscheidung, nicht durch ein Argument).
- **Konkrete Folge, benannt statt verschwiegen:** `skew.html:818-839` (`ladeVorher`) lädt
  die Vorsession und zeigt die Veränderung der Call-/Put-Wall. Sobald für den 21.10. eine
  reguläre Zeile existiert, wird sie gegen die Zeile vom 20.10. verglichen, deren OI und
  IV aus dem Abruf am Folgetagmorgen stammen. Ein Teil der angezeigten Wall-Veränderung
  ist dann Abrufzeitpunkt, nicht Marktbewegung. Einmalig, genau ein Tagespaar.
- Dasselbe gilt für `compare_flashalpha_gex.py:129-143`, das Qualitätsmetadaten des
  Gesamtobjekts ohnehin nicht überträgt.

## 6. Stufe 2 — bewusst nicht in diesem Bau

Mit Begründung, damit nichts als „vergessen" durchgeht:

1. **Exklusive GEX-Laufsperre über den ganzen Veröffentlichungsweg** (N2). `main` schreibt
   Summary (307) und Profile (309–313) **vor** dem Archiv (324); ein zweiter Lauf ändert
   die Live-Dateien und lässt das Archiv stehen. Stufe 1 macht das nicht schlimmer, die
   Handelstagprüfung nimmt den häufigsten Auslöser weg.
2. **Veröffentlichungszustand und Wiederaufnahme** (M4). Was gilt, wenn der Snapshot
   erfolgreich war und Key Levels scheiterten, ist offen — beide Lesarten sind schlecht.
   Braucht eine Versionskennung und Leser, die zusammengehörige Versionen erkennen.
3. **Atomares Schreiben** (`shared/atomic_json.py`, v56.0; Codex: „jetzt"). Ich setze es
   in Stufe 2, weil Stufe 1 den Schreibweg **nicht anfasst** und mit 3.4 den Deploy zum
   Warten bringt — damit sinkt die Abbruchgefahr, statt zu steigen. Dazu gehört die
   403-Falle aus v60.2 (Dateirechte) und eine HTTP-Prüfung.
4. **Veraltung auf den Seiten melden** (N6). `dealer-positioning.html:219` sagt „Dealer
   sind netto long Gamma", `skew.html:869` markiert „am Flip", `key-levels.html:279` liest
   das Datum und zeigt es dort nicht. **Das ist der Grund, warum fünf rote Nächte nicht
   auffielen** — die Seiten sahen gesund aus. Der Health-Check hat korrekt gegriffen
   (`daily_health_check.py:431,448,903`). Drei Seiten in DE und EN, eigene
   `data-i18n`-Schlüssel, und die Frage, was eine Seite bei veralteten Daten zeigen soll.
   **Nutzerentscheidung offen.**

## 7. Fragen an Runde 4

1. Trägt mein Rückzug des Zukunftstors (2.2), oder verliere ich damit einen Schutz, den
   ich nicht sehe?
2. Ist der Marker-Mechanismus in 3.2 (stdout-Zeile, fehlender Marker ⇒ fehlgeschlagen)
   dicht, oder gibt es einen Weg, auf dem ein Trockenlauf oder ein Feiertagslauf doch
   Key Levels startet?
3. Ist die Zuordnung der Aufrufer zu den drei Modi (3.1) vollständig? Welcher bestehende
   Aufrufer fiele noch in den falschen Modus?
4. Ist der Schnitt zwischen Stufe 1 und Stufe 2 (Abschnitt 6) tragfähig — oder macht
   Stufe 1 ohne einen der vier Punkte etwas **schlimmer** als heute?
