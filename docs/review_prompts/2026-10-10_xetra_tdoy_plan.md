# XETRA: TDOY/TDOM nach der Kalenderkorrektur — Entwurf zur Prüfung (Runde 1)

<task>
Nach Phase 1B von /plain-vanilla (Commit 1652383, deployt, auf dem Server geprüft) ist der XETRA-Kalender
in `shared/exchange_holidays.py` korrigiert: 24./31.12. ab 2001 geschlossen, dazu `XETRA_SONDER` (15 Tage).
Offen laut Plan V5 (`docs/review_prompts/2026-10-08_plain_vanilla_1b_plan.md`, Zeile 32 ff.): die
gespeicherten `prices.tdom`/`prices.tdoy` der 45 XETRA-Ticker neu rechnen — zuerst Trockenlauf, Schreiben
nur bei passendem Muster, sonst Rückmeldung an den Nutzer.

Ich habe lesend gemessen (vier Sonden, alle ohne Schreibzugriff, im Container mit dem deployten Code;
Quelltexte unter `C:\Users\HEIKOS~1\AppData\Local\Temp\claude\c--dev-SeasonalEdge\1daef494-b45f-4a2e-bd62-04336446f466\scratchpad\xetra\`
— `sonde.py`, `sonde2.py`, `sonde3.py`, `sonde4.py`, `alter_kalender.py` = `git show 1652383^:shared/exchange_holidays.py`).
**Das Muster passt nicht.** Bitte den Entwurf unten prüfen, BEVOR Code oder ein Schreibvorgang entsteht.
Du kannst nicht auf die Datenbank zugreifen; die Zahlen unten stammen aus meinen Läufen.
</task>

## Messung (Server, 2026-10-10, 45 XETRA-Ticker laut `get_exchange_for_holidays`)

Drei Werte je Zeile: S = gespeichert, N = Kalenderzählung ab 1.1. mit neuem Kalender, A = dieselbe Zählung
mit altem Kalender. Klassen: `ok` (S = N), `korrektur` (S = A ≠ N), `zaehlweise` (S ≠ N und S ≠ A).

```
korrektur|2001-2025                     9658     korrektur|vor2001          1464
korrektur|2001-2025|geschlossener_tag    552     korrektur|vor2001|geschl.    72
ok        (alle Zeiträume)            234464
zaehlweise|2001-2025                   13384     zaehlweise|vor2001         9321
zaehlweise|2001-2025|geschlossener_tag    21     zaehlweise|vor2001|geschl.   51
zaehlweise|2026                          123     leer|2001-2025|geschl.        3
```
Musterprüfung der Klasse `korrektur` (jede Zeile liegt in einem Jahr mit Differenztag alt/neu, Datum ≥ erster
Differenztag; TDOM nur verschieden, wenn im selben Monat ein Differenztag ≤ Datum): **0 Verstöße.**

`zaehlweise` hat (mindestens) drei Ursachen, an Beispielen belegt:
1. **Zeilenzählung statt Kalenderzählung** aus älteren Schreibwegen. `^GDAXI` beginnt 1959-09-28 mit S=(1,1),
   N=(20,189); 6435 Zeilen vor 2001. `scripts/backfill_new_ticker.py::compute_tdoy_tdom` (vom Onboarding
   genutzt) zählt entlang der Datumsliste ab der ersten Zeile, nicht ab 1.1.; eine Datenlücke verschiebt alles
   Folgende. Betrifft auch `^MDAXI`, `^SDAXI`, `^TECDAX` (721/895/1390 Zeilen ab 2001).
2. **Die 240 Zeilen je DAX-Aktie 2001–2025** liegen in 2011, 2012, 2013 (je ~60, ab 3./4.10.) und 2018. Beispiel
   SAP.DE 2011-10-04: S=(1,194), N=A=(2,195). Die Daten haben an 2011-10-03 keine Zeile.
3. **Live-Schreibwege zählen „Vorzeile + 1“**: `scripts/intraday_refresh.py:134-171` (letzte DB-Zeile vor dem
   Download + Kalenderschritte nur über die heruntergeladenen Tage, Ausnahme wird verschluckt) und
   `shared/data.py:189-220` (letzter TDOY im df + 1). Belegt: SAP.DE 2026-09-07 und 2026-09-08 tragen beide
   (5,174); N für 09-08 ist (6,175). 3 Zeilen je Ticker in 2026, an allen 41 Aktien gleich.

Zeilen an Tagen, die der neue Kalender schließt (`geschlossener_tag`): bei SAP.DE durchweg `volume=0`,
`close` = Vorschlusskurs (Füllzeilen der Quelle), auch an Karfreitag/1.5./25.12., die beide Kalender schließen.
Der Kalender ordnet ihnen den Wert des Vortags zu (doppelter TDOY).

### Kalender gegen Aktiendaten (Sonde 4)
Für jeden Werktag 2001-01-01 bis 2026-10-09: Anteil der 41 XETRA-Einzelaktien (ohne Indizes, nur Aktien,
deren Historie den Tag umspannt) mit einer Zeile mit Volumen > 0.
- Kalender **geschlossen**, aber ≥ 50 % mit Volumen: **0 Tage.**
- Kalender **offen**, aber < 50 % mit Volumen: 20 Tage. 17 davon 2001/2002/2006 mit 7–13 von 27–31 Aktien
  (Teilbelegung, sieht nach Quellenlücken aus). Die drei übrigen sind eindeutig:
  **2011-10-03 (1/35), 2012-10-03 (0/35), 2013-10-03 (1/36)** — `^GDAXI` hat an allen drei eine Zeile.
  Zum Vergleich Pfingstmontag 2011/2012/2013: 37–38 Zeilen mit Volumen.
  3.10.2010/2015 fallen auf das Wochenende, 2014 und 2016–2019 sind im neuen Kalender geschlossen.

Mein Verdacht: **Xetra war am 3.10.2011, 2012 und 2013 geschlossen**, und `XETRA_SONDER` fehlen diese drei
Tage. Die Quellenrecherche aus 1B (`docs/review_prompts/2026-10-08_plain_vanilla_1b_plan_antwort1.md`) hat
2014/2016–2019 belegt; wurde 2011–2013 geprüft, oder hat die `^GDAXI`-Zeile den Tag als offen erscheinen
lassen? Damit wäre auch 2018 erklärt: S=(3,194) am 2018-10-04 gegen N=(3,193) — dort steht der umgekehrte Fall,
den ich noch nicht verstanden habe.

## Entwurf

**E1 — Kalender zuerst.** Wenn sich der 3.10.2011–2013 als Schließung belegen lässt (zwei unabhängige Quellen
wie in 1B), in `XETRA_SONDER` und `landing/js/holidays.js::_XETRA_SONDER` aufnehmen, Zwillingstest
`scripts/verify_kalender_zwilling.py` erweitern. Erst danach irgendetwas neu rechnen — sonst schreibe ich die
nächste falsche Zählung in die DB.

**E2 — Eine Rechenfunktion.** `shared/exchange_holidays.py` bekommt `tdom_tdoy(d, exchange) -> (tdom, tdoy)`
(Kalenderzählung ab 1.1., gecacht je Jahr/Börse; für einen geschlossenen Tag der Wert des letzten Handelstags
davor, wie heute in `backfill_tdoy`). `backfill_tdoy.compute_tdoy_tdom`, `backfill_new_ticker.compute_tdoy_tdom`,
`intraday_refresh` und `shared/data.py` rufen sie; die „Vorzeile + 1“-Logik und die zweite Zeilenzählung
verschwinden. Ohne E2 driftet jeder Backfill mit dem nächsten Intraday-Lauf wieder auseinander.

**E3 — Trockenlauf als Skript** `scripts/xetra_tdoy_trockenlauf.py`, lesend: Klassen wie oben je Ticker/Jahr,
Musterprüfung der Klasse `korrektur`, Anzahl Zeilen, die ein Schreiben ändern würde, getrennt TDOM/TDOY.
Ausgabe als JSON-Bericht + Exit ≠ 0 bei Musterverstoß.

**E4 — Schreiben (erst nach Nutzerfreigabe).** Nur Zeilen mit S ≠ N, nur die Spalten `tdom`/`tdoy`, per
`update().eq(ticker).eq(date)` (nicht das bestehende `upsert` mit mitgelesenem `close` — das kann einen
`close`, den der Nightly zwischen Lesen und Schreiben aktualisiert, mit dem alten Wert überschreiben).
Außerhalb der Cron-Fenster. Danach Rücklesen und Vergleich gegen N, Exit ≠ 0 bei jeder Abweichung.

**E5 — Umfang.** Vorschlag: alle XETRA-Zeilen ab 2001 (Korrektur + Zählweise + Live-Drift), weil N die
dokumentierte Wahrheit ist („TDOY-Ground-Truth = reiner Börsenkalender ab 1.1.“, CLAUDE.md). **Vor 2001
nicht** — für den Parketthandel vor Xetra (1959–2000) ist der Kalender nicht belegt, die 9321 Zeilen bleiben,
und das wird dokumentiert. Fragen dazu unten.

**E6 — Andere Börsen.** Die Ursachen 1 und 3 sind nicht XETRA-spezifisch. Vorschlag: denselben Trockenlauf
danach für alle Börsen laufen lassen, aber erst nach E2 und getrennt entscheiden.

## Fokusfragen

1. Lässt sich die Schließung am 3.10.2011, 2012, 2013 belegen (Quellen)? Und was erklärt 2018-10-04 S=(3,194)
   gegen N=(3,193) — ist eine der beiden 2018-Schließungen (21.5., 3.10.) zweifelhaft?
2. Sind die 17 Teilbelegungs-Tage 2001/2002/2006 harmlos (Quellenlücke) oder können darunter Schließungen sein
   (z. B. 2001-10-03 mit 9/29, 2002-05-28)? Welche zusätzliche Prüfung wäre trennscharf?
3. Wer liest `prices.tdoy`/`tdom` tatsächlich (Frontend, `tdom_stats`/`tdoy_stats`, Newsletter, Backtests)?
   Bleibt die Aussage aus dem Plan wahr, dass `tdom_stats`/`tdoy_stats` keinen Recompute brauchen?
   (`shared/yahoo_downloader.py:268` übernimmt die DB-Spalte, sonst `cumcount` — wer nutzt das?)
4. E2: Welcher Wert für eine Zeile an einem geschlossenen Tag (Füllzeile)? Vortag (heute), `NULL`, oder die
   Zeile gar nicht anfassen? Was erwarten die Leser?
5. E4: Ist `update()` je Zeile bei ~25.000 Zeilen vertretbar, oder Stapel per RPC/SQL? Reicht der
   Rücklesevergleich als Nachweis?
6. E5: Ist „ab 2001“ die richtige Grenze, oder sollte auch die Zählweise vor 2001 auf die Kalenderzählung
   (ab 1.1., gleicher Kalender wie heute vor 2001) — die Zählung ab der ersten Zeile ist ja in jedem Fall falsch,
   unabhängig von der Kalendergüte?
7. Was übersehe ich? Insbesondere: Gibt es weitere Schreibwege für `tdom`/`tdoy` (DB-Trigger, SQL-Skripte unter
   `scripts/sql/`, `fix_missing_days.py`)?

## Bereits bestätigt (nicht erneut melden)
- Der Server läuft mit dem 1B-Kalender (Commit 9b0e3ef, `is_trading_day(2008-12-24,'XETRA')` = False).
- Die Klasse `korrektur` hat 0 Musterverstöße.
- `backfill_tdoy.py` meldet fehlgeschlagene Batches mit Exit 1.

## Erwartbare Fehlalarme
- Die Sonden liegen bewusst außerhalb des Repos (Wegwerf-Messung); E3 wird das Skript im Repo.
- Kein Schreiben in diesem Schritt — der Nutzer gibt den Schreibvorgang frei.

## Ausgabevertrag
Abschnitte: **Urteil** (tragfähig / tragfähig mit Auflagen / nicht tragfähig, ein Satz) · **Antworten auf
die Fokusfragen** (je 2–6 Zeilen, mit Quelle bzw. Datei:Zeile) · **Weitere Befunde** (nummeriert, je mit
Beleg) · **Auflagen vor dem Code** (Liste). Höchstens 120 Zeilen.
