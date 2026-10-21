# Entwurf v2: GEX-Snapshot läuft seit dem 15.10. ins Yahoo-Loch

**Status:** Entwurf v2 nach Codex-Runde 1 (Urteil: Freigabe mit Auflagen, zehn Befunde).
**Nutzerentscheidung 2026-10-21:** beides bauen — systemd-Timer UND Spot-Regel.

Acht der zehn Befunde habe ich am Code bestätigt, zwei sind Korrekturen meiner zu
starken Aussagen (B1, B2) und eine korrigiert mich sachlich (B4: `^SPX` steht nicht im
`UNIVERSE`, `_INDEX_TICKERS` ist nur eine Einordnungsmenge). Alle sind eingearbeitet.

## 1. Der Befund — als Hypothese mit benannter Beweislücke (B1, B2)

`GEX Snapshot (Dealer Positioning)` ist seit dem 15.10.2026 fünf Nächte rot.

### 1.1 Was gemessen ist

Yahoo-Proben `/root/yahoo_abend/`, **Nacht 16.→17.10.**, Session 2026-10-16, SPY:

| Abruf (UTC) | `regularMarketTime` | letzter `close` |
|---|---|---|
| 16.10. 22:15 | 16:00 EDT | 763.25 |
| 17.10. 00:15 | 16:00 EDT | **`null`** |
| 17.10. 00:45 | 16:00 EDT | **`null`** |
| 17.10. 02:00 | 16:00 EDT | 763.25 |

`regularMarketTime` bleibt korrekt — der Frische-Nachweis besteht, es fehlt allein der
Kurs. **Zwischen 00:45 und 02:00 gibt es keine Messung**; das Ende des Lochs ist nicht
gemessen.

### 1.2 Was daraus folgt — und was nicht

Der Lauf vom **17.10. startete um 00:26 UTC**, also zwischen zwei gemessenen `null`-
Antworten derselben Nacht. Für diese eine Nacht ist die Ursache damit eng eingekreist.

Für die übrigen vier Nächte ist es eine **starke Hypothese**, nicht mehr: ich habe die
Fehlerausgaben der Läufe nicht gelesen (kein Token für die GitHub-Job-Logs). Codex hat
zu Recht beanstandet, dass Laufzeit und Exit-Code mehrere Erklärungen zulassen — `main`
bricht auch ohne `MASSIVE_API_KEY` (Exit 1), bei offenem Markt (Exit 2) und bei zu
wenigen Kontrakten ab, und die Workflow-Zeile bildet jeden Fehlschlag auf Exit 1 ab.

**Die Hypothese ist in einem Klick prüfbar:** im Job-Log muss pro Ticker die Zeile
`[spot] <T>: kein Tagesbalken der Session <datum> — verworfen` stehen, gefolgt von
`[snapshot] ABBRUCH: nur 0/20 Ticker brauchbar`. Steht dort etwas anderes, ist die
Diagnose falsch und dieser Entwurf hinfällig. **Vor dem Bauen zu prüfen.**

Nebenbefund, der die Diagnose heute unnötig schwer macht: `_spot` gibt für „Balken da,
`close` leer" und „kein Balken der Session" **dieselbe** Meldung aus
(`snapshot_gex_massive.py:137`). Die beiden Fälle sind fachlich verschieden und müssen
unterscheidbar protokolliert werden.

### 1.3 Korrelation (Beobachtung, kein Beweis)

| Start (UTC) | Ergebnis |
|---|---|
| 13.10. 03:01 · 14.10. 01:11 | grün |
| 15.10. 00:30 · 16.10. 00:21 · 17.10. 00:26 · 20.10. 01:04 · 21.10. 00:35 | rot |

Jeder rote Lauf startete zwischen 00:21 und 01:04, jeder grüne außerhalb. Der Cron steht
auf 22:15 UTC und wäre richtig; GitHub startet ihn 2–5 h verspätet.

**Zurückgezogen gegenüber v1:** „das Loch reicht mindestens bis 01:10". Der Fehlschlag um
01:04 beweist keinen fehlenden Yahoo-Kurs, nur einen Fehlschlag.

### 1.4 Datenschaden

- Fehlende Sessions: **19.10. und 20.10.** — zwei Handelssitzungen, nicht vier Tage
  (Korrektur von Codex; 17./18.10. waren Wochenende).
- Die Session **19.10. ist verloren**: ein Chain-Snapshot lässt sich nicht nachträglich
  abrufen.
- **Session 20.10. am 21.10. 06:43 UTC nachgeholt** (20/20 Ticker, Archivzeile
  geschrieben). ⚠️ Diese Zeile ist **nicht gleichwertig** zu den übrigen: Strikes und DTE
  stehen zur Session 20.10., die IV stammt aber aus dem Abruf am 21.10. morgens. Ob die
  Zeile in der proprietären Historie bleibt, ist eine **Nutzerentscheidung** —
  `MAX_DAYS` ist bewusst konstant, damit jeder Tag denselben Ausschnitt misst, und diese
  Zeile bricht die Vergleichbarkeit an anderer Stelle.

### 1.5 Was Massive im Loch liefert

Proben `/root/massive_abend/`, **Nächte 19.→20. und 20.→21.10.**, SPY — beide identisch:

| Abruf (UTC) | Tagesbalken der Session | `/prev` → Balkendatum |
|---|---|---|
| 20:00 – 23:30 | 403 | 200, **Vorsession** |
| 00:00 – 01:00 | 403 | 200, **Session** |
| 01:30 | 403 | **429** |
| 02:00 – 03:30 | 403 | 200, Session |
| ab 04:00 | **200** | 200, Session |

**Zurückgezogen gegenüber v1:** „kippt punktgenau um 00:00 UTC" und „es gibt keinen
Zeitpunkt, an dem beide ausfallen". Beides ist aus zwei Nächten nicht ableitbar, und das
429 um 01:30 ist selbst ein Gegenbeispiel zur zweiten Aussage. Die Uhrzeit bleibt
**datierte Beobachtung im Kommentar**, nie Vertrag. Verbindlich ist allein die Prüfung
der Antwort.

Belegt bleibt: `/prev` liefert vor 00:00 UTC die Vorsession — genau der Grund, aus dem es
in v66.20 verworfen wurde. Die Datumsprüfung fängt das unabhängig von der Uhrzeit.

## 2. Was gebaut wird

### 2.1 Teil A — systemd-Timer

`sa-gex-snapshot.timer` / `.service` nach dem Muster `sa-intraday`:

- `OnCalendar=Mon..Fri 22:15 UTC`, `AccuracySec=1min`, `Persistent=false`.
- `ExecStartPre=warte_auf_app.sh`.
- `gex_snapshot.yml` behält nur `workflow_dispatch` und startet dieselbe Unit — kein
  Zeitplan, sonst läuft es doppelt.
- `deploy/install_timers.sh`: Unit in `SERVICES`/`TIMERS`.

**Neu nach B5 — Handelstagprüfung.** Gemessen (`markt_offen`/`letzte_session`):

| Termin | Wochentag | `markt_offen` | `letzte_session` |
|---|---|---|---|
| 26.11.2026 22:15 (Thanksgiving) | Do | False | **2026-11-25** |
| 25.12.2026 22:15 | Fr | False | **2026-12-24** |
| 03.07.2026 22:15 | Fr | False | **2026-07-02** |

Ein Werktagstimer feuert an diesen Tagen, `pruefe_eod_fenster` lässt durch (Markt ist zu)
und `letzte_session` zeigt auf eine Session, die in der Nacht davor **schon archiviert
wurde**. Der Lauf würde `gex_history_session/<session>.json` mit einen Tag später
abgerufenen Daten überschreiben — stille Verfälschung der eigenen Historie. Zwei Sperren:

1. Der automatische Lauf prüft, ob **das heutige New Yorker Datum ein Handelstag** ist,
   und endet sonst ohne Abruf mit einer Meldung und Exit 0 (geplantes Nichtstun, kein
   Fehler).
2. Unabhängig davon: existiert für die gestempelte Session **bereits** eine Archivdatei,
   wird sie nicht ersetzt. Ein bewusster Wiederholungslauf braucht einen eigenen
   Schalter (`--wiederholen`), der im Dateinamen oder in einem Feld nachweist, dass die
   Zeile nachgeholt wurde. Das deckt auch den Fall aus 1.4 ab.

### 2.2 Teil B — Spot-Regel

`_spot` bekommt eine zweite Quelle. **Entscheidend ist die Unterscheidung der
Ablehnungsgründe (B3)** — mein Entwurf v1 hatte sie nicht:

`_spot` gibt heute aus **zwei fachlich verschiedenen** Gründen `None`:

| Grund | Bedeutung | darf Massive ersetzen? |
|---|---|---|
| `close` fehlt, `regularMarketTime` ≥ Sessionschluss | das Loch — die Session ist nachweislich beendet, nur der Kurs fehlt | **ja** |
| `regularMarketTime` < Sessionschluss | kein Nachweis, dass bis zum Schluss gehandelt wurde (Handelsstopp, stehengebliebene Antwort) | **nein** |
| kein Balken der Session | unklar | **nein** ohne eigenen Nachweis |

Ein gleichdatierter Massive-Balken beweist die Tageszuordnung, **nicht** Handel bis zum
Schluss. Der Rückfall darf den Schlussnachweis also nicht aushebeln. Umsetzung: `_spot`
liefert statt `None` einen benannten Grund, und nur der Grund „Kurs fehlt bei
vorhandenem Schlussnachweis" öffnet den Rückfall.

Ablauf:

1. **Yahoo** wie heute (Schlussnachweis + Balkendatum). Kurs gültig → fertig.
2. Nur bei Grund „Kurs fehlt, Schluss nachgewiesen": **Massive
   `/v2/aggs/ticker/<SYM>/prev?adjusted=false`**. `adjusted=false` ist Pflicht — der Spot
   ist die Strike-Basis.
3. **Antwortvertrag (B4)**, jede Bedingung muss halten: Symbol der Antwort == angefragtes
   Symbol · genau ein Ergebnis · `t` als Millisekunden-Zeitstempel im plausiblen Bereich ·
   Balkendatum **in New York** == Session · `c` ist `int`/`float`, **kein `bool`**,
   endlich und > 0. Gemessen: `True > 0` ist `True` und `float(True)` = 1.0, `inf > 0`
   ist `True` — beides lässt die heutige Prüfung `c > 0` durch. Der Vertrag gilt für
   **beide** Quellen, nicht nur für die neue.
4. Rückfall nur für **belegte Aktien-/ETF-Symbole**. Das heutige `UNIVERSE` sind 20
   Aktien und ETFs, kein Index — aber `--tickers` nimmt beliebige Symbole. Ein nicht
   unterstütztes Symbol ergibt kontrolliert `None`, kein Ersatzwert und kein Absturz.
   Indexunterstützung braucht einen eigenen Vertrag; sie ist hier **nicht** zugesagt.
5. Bei **429** gedrosselte Wiederholung, `Retry-After` beachten. Fällt auch das aus →
   `None`. Die Reissleine bleibt unberührt.

### 2.3 Teil C — Zeitbudget (B6)

Mein „8–12 min" war geraten. **Gemessen am 21.10.:** der volle Snapshot allein brauchte
~7 min (06:36 → 06:43, 20/20 Ticker); `compute_key_levels` kommt dazu. Vor dem Bauen
wird beides einmal zusammen gemessen, und daraus wird **ein gemeinsames Budget**
abgeleitet, das Abrufe, Wiederholungen und beide Schritte deckt. Das äußere
`TimeoutStartSec` muss zusätzlich `warte_auf_app.sh` (bis zu 2 min) und den
Kill-Nachlauf abdecken. Dauer-429 für alle 20 Ticker wird mit gestellter Uhr geprüft,
nicht geschätzt.

### 2.4 Teil D — Produktionssperre (B7, B8)

`PFLICHT` ist sachlich richtig: beide Programme bestimmen die Session über den
Börsenkalender, die Begründung „keine Kalendermethode" trägt seit B2 nicht mehr. Aber
ein Listenwechsel allein macht das Gate rot. Erforderlich ist das volle Muster, wie
`nightly_refresh.py:18,580` es zeigt:

- `modul_sperre("<name>")` auf Modulebene unter `if __name__ != "__main__"`,
- `with produktion("<name>")` im `__main__`-Block,
- Entfernen aus `AUSNAHMEN`.

Dazu die bestehenden GEX-Wächter prüfen, die diese Module importieren — ihre
Sperrverzeichnisse müssen isoliert bleiben.

**B8 — der Service braucht einen ausführbaren Vertrag, keine zwei `ExecStart`-Zeilen:**
mit zwei Zeilen und `SuccessExitStatus=75` würde ein *unterdrückter* Snapshot als
Erfolg gelten und Key Levels trotzdem starten; außerdem gäbe ein getrennter zweiter
Prozess die Sperre zwischen den Schritten frei, sodass ein Deploy dazwischen den
Container tauschen kann. Also **eine** Hülle mit ausdrücklicher Statusweitergabe:

| Snapshot | Kette |
|---|---|
| 0 | Key Levels laufen |
| 75 (Sperre) | ganze Kette endet 75, Key Levels laufen **nicht** |
| alles andere | sofortiger Fehler, Key Levels laufen **nicht** |

Die Sperre wird über beide Schritte gehalten. Der Wächter muss den **tatsächlichen
Hüllenpfad ausführen**, nicht nach Textmustern suchen — `verify_produktionssperre.py`
erkennt heute nur direkte Skriptaufrufe.

## 3. Wächter

`scripts/verify_gex_spot.py` im Deploy-Gate, mit Mutationstest, gegen die **echten
Probe-Antworten** als Fixture (nicht nachgebaut). Fälle, einschließlich der von Codex
nachgeforderten:

1. Yahoo gültig → Kurs, **kein** Massive-Abruf (Aufrufe werden gezählt).
2. Yahoo `close = null`, Schluss nachgewiesen (Fixture 17.10. 00:15) → Massive-Kurs.
3. Massive-Balken der **Vorsession** (Fixture 19.10. 23:00) → verworfen. Das ist der
   v66.20-Fehler.
4. **Yahoo-Handel vor Schluss PLUS gleichdatierter Massive-Balken → verworfen.** Der
   Schlussnachweis darf nicht umgangen werden (B3). Dieser Fall entscheidet den Entwurf.
5. Massive leer · 403 · Timeout · kaputte Struktur · falsches Symbol · `c` als `bool` ·
   `inf` · Zeitstempel in Sekunden statt Millisekunden → je `None`, kein Absturz.
6. 429 → Wiederholung, dann Erfolg; Dauer-429 → `None`. Mit gestellter Uhr, damit der
   Test nicht wartet.
7. **Sommer- und Winterzeit:** Fixtures beiderseits des 01.11.2026, nicht nur Oktober —
   drei Prozesszeitzonen mit Oktober-Daten beweisen die Winterzeit nicht.
8. **Echter Halbtag** mit unabhängig festgelegter Schlusszeit aus `sitzung_info`.
9. **Feiertag 22:15 UTC mit vorhandenem Archiv:** kein Abruf, keine erneute
   Veröffentlichung (B5).
10. **Echter `main`-Pfad bei 11/20 und 12/20** brauchbaren Tickern: unter der Grenze
    bleibt **jede** Ausgabedatei unverändert (Hash vor/nach).
11. **Service-Ablauf** bei Snapshot-Exit 0, 1, 2, 75 und Timeout: Key Levels laufen
    ausschließlich bei 0.
12. `adjusted=false` steht in der angefragten URL.
13. Unit-Vertrag: `OnCalendar` gültig (`systemd-analyze`), Timeout im Container, Unit in
    `install_timers.sh`, `gex_snapshot.yml` ohne `schedule`.

Mutationen müssen den **Produktionspfad** treffen; ein fehlender Anker oder ein Absturz
zählt nicht als gefangener fachlicher Fehler, sondern als ungültig.

## 4. Was NICHT gebaut wird

- **Keine Rekonstruktion der Session 19.10.** Der OI/IV-Stand existiert nicht mehr.
- **Keine Änderung an der Reissleine.** Sie hat korrekt gearbeitet.
- **Keine Zeitgrenze als Umschaltkriterium.** Nur validierte Antworten entscheiden.
- **Keine Indexunterstützung** im Rückfall.
- **B9 wird hier nicht behoben** (siehe unten) — eigener Posten, bewusst getrennt.

## 5. B9 — eigener Posten, nicht Teil dieses Baus

Codex hat belegt, dass die drei Seiten mit altem Stand **weiterrechnen**, statt zu
melden: `dealer-positioning.html:224,234,314` (Fragilitätsanteil, Spot-Abstände),
`skew.html:844,857,860` (Abstand zum Vol-Trigger, „am Flip"),
`key-levels.html:197,277` (`KL_DATE` wird gesetzt, die in `render` gelesene `asof` aber
nicht angezeigt). Datenstand wird genannt, Veraltung nicht.

**Das ist der eigentliche Grund, warum fünf rote Nächte nicht aufgefallen sind** — die
Seiten sahen gesund aus. Der Health-Check prüft die Session bereits und wird ab zwei
fehlenden Sessions rot (`daily_health_check.py:431,448,903`), hat also funktioniert; die
Meldung kam dann auch. Aber die Seite ist das, was ein Leser sieht.

Es gehört in einen eigenen Bau, weil es drei Seiten in DE und EN betrifft, eigene
`data-i18n`-Schlüssel braucht und die Frage aufwirft, was eine Seite bei veralteten
Daten zeigen soll (Vorschlag: aktuelle Zustandsaussagen unterdrücken, Stand als
historisch kennzeichnen). **Nutzerentscheidung.**

## 6. Offene Fragen an Runde 2

1. Reicht die Unterscheidung in 2.2 (drei Ablehnungsgründe, nur einer öffnet den
   Rückfall), oder gibt es einen vierten Weg, auf dem ein Kurs ohne Schlussnachweis
   durchkommt?
2. Ist „existiert die Archivdatei schon, wird sie nicht ersetzt" (2.1) die richtige
   Sperre, oder verhindert sie einen legitimen Reparaturlauf zu stark? Der Schalter
   `--wiederholen` soll das lösen — genügt das, und muss die nachgeholte Zeile sich
   selbst als nachgeholt ausweisen?
3. Soll der Handelstag-Test im Skript sitzen (gilt dann für jeden Aufrufer) oder in der
   Unit (gilt nur für den Timer)? Die Projektregel sagt „Schutz zum Erzeuger" — dann ins
   Skript, aber ein manueller Reparaturlauf am Feiertag wäre damit auch gesperrt.
4. Übersehe ich beim Zeitbudget einen Schritt, der im Timer-Pfad zusätzlich Zeit kostet?
