# Entwurf v3: GEX-Snapshot läuft seit dem 15.10. ins Yahoo-Loch

**Status:** Entwurf v3 nach Codex-Runde 2 (Urteil: nicht tragfähig, N1–N7).
**Nutzerentscheidung 2026-10-21:** Timer UND Spot-Regel bauen.

Runde 2 hat B1, B2 und B7 abgenommen, B6 und B10 verschoben und fünf Befunde nicht
abgenommen. Von den sieben neuen übernehme ich sechs; **bei N1 widerspreche ich mit
Codebeleg** (Abschnitt 2.2.1). Was unverändert gilt, steht hier nicht erneut — v2
bleibt für die Messdaten die Quelle, dieser Entwurf ändert nur, was Runde 2 beanstandet
hat.

Zu B10: mein Fehler in der Nummerierung. Runde 1 hatte zehn Befunde, Abschnitt 3 von v2
nannte in den Begründungen aber nur B3 und B5. Die nachgeforderten Wächterfälle aus B10
sind in v2 eingebaut (Fälle 4–11), nur nicht als B10 gekennzeichnet. In v3 steht die
Zuordnung an jedem Fall.

## 1. Vorbedingung vor dem Bau (unverändert aus v2, B1)

Die Diagnose bleibt eine **Hypothese**, bis das Job-Log eines roten Laufs die Zeile
`[spot] <T>: kein Tagesbalken der Session <datum> — verworfen` pro Ticker zeigt, gefolgt
von `[snapshot] ABBRUCH: nur 0/20 Ticker brauchbar`. Ich habe keinen GitHub-Token; das
muss der Nutzer einmal nachsehen. Steht dort etwas anderes, ist dieser Entwurf hinfällig.

Belegt ist dagegen: der Lauf vom 17.10. startete um 00:26 UTC zwischen zwei gemessenen
`close = null`-Antworten derselben Nacht.

## 2. Spot-Regel

### 2.1 Zwei Quellenadapter statt eines Vertrags (N4 — mein Fehler)

v2 schrieb „Der Vertrag gilt für **beide** Quellen". Das ist falsch: Yahoo liefert eine
Fünftagesreihe mit parallelen `timestamp`/`close`-Arrays in **Sekunden**
(`snapshot_gex_massive.py:120,133`), Massive genau ein Aggregat in **Millisekunden**. Eine
wörtliche Umsetzung hätte gültige Yahoo-Antworten verworfen.

Richtig sind **zwei Adapter plus eine gemeinsame Prüfung eines normalisierten Satzes**:

| Adapter | prüft quellenspezifisch |
|---|---|
| Yahoo | `chart.result[0]` vorhanden · `timestamp` und `close` gleich lang · genau ein Balken, dessen Datum **in New York** == Session · Zeitstempel in Sekunden |
| Massive | genau **ein** Ergebnis · Antwortsymbol == angefragtes Symbol · `t` in Millisekunden im plausiblen Bereich · Balkendatum in New York == Session |

Gemeinsam geprüft wird danach nur noch der normalisierte Satz
`{symbol, session, kurs, schlussnachweis}`: `kurs` ist `int`/`float`, **kein `bool`**,
endlich, > 0. Gemessen: `True > 0` ist `True` und `float(True)` = 1.0, `inf > 0` ist
`True` — beides lässt die heutige Prüfung `c > 0` durch
(`snapshot_gex_massive.py:134`). Diese Verschärfung gilt für beide Quellen; sie ist eine
Qualitätsregel, kein Schema.

Der Rückfall gilt nur für **belegte Aktien-/ETF-Symbole**. Das heutige `UNIVERSE` sind 20
Aktien und ETFs, kein Index — `^SPX` steht dort nicht, `_INDEX_TICKERS`
(`compute_gamma_exposure.py:48`) ist nur eine Einordnungsmenge für den Gamma-Index
(Korrektur von Codex, am Code bestätigt). `--tickers` nimmt aber beliebige Symbole: ein
nicht unterstütztes ergibt kontrolliert `None`. **Indexunterstützung ist nicht zugesagt.**

### 2.2 Wann der Rückfall öffnet

#### 2.2.1 Widerspruch zu N1

N1 sagt, `_spot` prüfe nur die Untergrenze `rmt >= schluss`, weshalb ein Handel am
Folgetag den Nachweis bestehe, und schlägt vor, **den Folgetag-Sollwert des Wächters zu
ändern**. Dem widerspreche ich; der Beleg steht im Bestandswächter selbst.

`verify_gex_session.py:160-172` baut für `art == "folgetag"` Balken für S **und** S+1
(Schlusskurse 700.0 und 999.0) und setzt `rmt` auf S+1 10:00 New York. Erwartet wird in
Zeile 232 der Wert **700.0** — der Balken der **Zielsession**, nicht der spätere. Genau
das ist richtig und der häufigste Betriebsfall: mein Nachholauf am 21.10. 06:43 UTC für
die Session 20.10. ist er, und jeder um Stunden verspätete Cron ebenso. Würde man den
Sollwert ändern, bräche der Normalfall.

Die Auswahl erfolgt auch nicht über `rmt`, sondern über die Schleife
`snapshot_gex_massive.py:135-140`, die den Balken **mit dem Datum der Session** nimmt.
`rmt` ist ein zusätzliches Tor, keine Auswahl.

**Was an N1 bleibt** — und das übernehme ich: der Kommentar
(`snapshot_gex_massive.py:104-107`) verspricht mehr, als die Prüfung leistet. Er sagt,
ein Handel nur am Vormittag (Handelsstopp) bestehe den Nachweis nicht. Das gilt am Abend
der Session; am Folgetag passiert `rmt` die Untergrenze und ein abgebrochener Handelstag
würde angenommen. Richtig ist: der Schlusskurs einer abgebrochenen Session **ist** ihr
amtlicher Schluss, die Annahme ist also sachlich nicht falsch — der Kommentar ist zu
stark. **Ich ändere den Kommentar, nicht das Verhalten**, und ergänze zwei Tore, die
nichts Gültiges verwerfen: `rmt` darf nicht in der **Zukunft** liegen, und der
Sessionbalken muss eindeutig sein.

Zur Prüfung gestellt: ist das die richtige Auflösung, oder sieht Codex einen Fall, in dem
die Annahme am Folgetag einen **falschen** Kurs ergibt (nicht nur einen, den der
Kommentar ausschließen wollte)?

#### 2.2.2 Die Ablehnungsgründe

`_spot` liefert statt `None` einen benannten Grund. Nur **einer** öffnet den Rückfall:

| Grund | darf Massive ersetzen? |
|---|---|
| Balken der Session da, `close` leer oder ungültig, `rmt` ≥ Schluss und nicht in der Zukunft | **ja** — das Loch |
| `rmt` fehlt oder < Sessionschluss | nein |
| kein Balken der Session · mehrere Balken der Session · keine Antwort · Struktur kaputt | nein |

Für Massive gibt es **keinen `rmt`-Nachweis** — `/prev` liefert nur das Aggregat. Der
Nachweis ist dort ein anderer und muss benannt werden, statt den Yahoo-Nachweis
vorzutäuschen: das Aggregat ist der **abgeschlossene Tagesbalken** der Session, und dass
die Session vorbei ist, steht schon vor dem Abruf fest (`letzte_session` plus
`pruefe_eod_fenster` plus die Handelstagprüfung aus 3.1). Mehr kann die Quelle nicht
liefern; wer mehr verlangt, kann sie nicht benutzen. **Das ist die benannte Grenze des
Rückfalls.**

Bei **429** gedrosselte Wiederholung mit `Retry-After`. `adjusted=false` ist Pflicht.

## 3. Betrieb

### 3.1 Handelstagprüfung — im Erzeuger, mit Betriebsmodus (N3, Antwort 3)

Gemessen (v2 Abschnitt 2.1): an Thanksgiving 2026 (Donnerstag), am 25.12. und am 03.07.
feuert ein Werktagstimer, `markt_offen` ist `False` und `letzte_session` zeigt auf eine
Session, die schon archiviert ist.

Die Prüfung gehört ins Skript (Projektregel „Schutz zum Erzeuger"), aber eine pauschale
Prüfung würde laut Codex auch den Workflow-Aufruf, direkte `--tickers`-Läufe und den
importierten `gm.main`-Testpfad (`verify_gex_session.py:189`) mitsperren. Also ein
expliziter Modus:

| Modus | Handelstagprüfung | Schreibt |
|---|---|---|
| automatisch (Timer, Standard) | **ja** — kein Handelstag → Ende **ohne Abruf** | ja |
| `--no-write` | nein | nein |
| `--wiederholen` (Reparatur) | nein | ja, nach Regel 4 |

⚠️ Und der Grund, warum N3 ein echter Fehler meines Entwurfs war: v2 schrieb für den
Feiertagslauf „Exit 0" und in der Kettentabelle „0 → Key Levels laufen". Das ist ein
Widerspruch — Key Levels hätten am Feiertag trotzdem einen zweiten Abruf gestartet und
veröffentlicht. **Drei Zustände, nicht zwei** (dieselbe Klasse wie v66.18
„angenommen/abgelehnt/unklar", und ich habe sie wieder zu zwei gemacht):

| Snapshot | Kette |
|---|---|
| **veröffentlicht** | Key Levels laufen |
| **übersprungen** (kein Handelstag, Veröffentlichung existiert schon) | Kette endet erfolgreich, Key Levels laufen **nicht** |
| **unterdrückt** (Produktionssperre, 75) | ganze Kette endet 75 |
| **fehlgeschlagen** | sofortiger Fehler |

Die 01:30-UTC-Testfälle in `verify_gex_session.py:71` liegen in New York noch am Freitag
— eine versehentliche UTC-Datumsprüfung würde sie reißen. Die Prüfung rechnet in
New York.

### 3.2 Laufsperre über den ganzen Veröffentlichungsweg (N2)

v2 hatte „existiert die Archivdatei, wird sie nicht ersetzt". Das ist zu schwach, und
zwar belegbar: `main` schreibt `gex_summary.json` (Zeile 307) und die Profile (309–313)
**vor** dem Archiv (324). Ein zweiter Lauf hätte die Live-Dateien geändert und das Archiv
stehen lassen — zwei Stände, gleicher Stempel. Zwei gleichzeitige Erstläufe hätten
beide „kein Archiv" gesehen.

Also eine **exklusive GEX-Laufsperre** für alle Einstiege, gehalten bis zum Ende der
Kette. Darunter: existiert eine **vollständige** Veröffentlichung für die Session und
läuft kein Reparaturmodus, endet der Lauf **vor dem ersten Abruf und vor jedem
Schreibvorgang** als „übersprungen".

Nebenbefund, selbst gefunden, zur Entscheidung: `main` schreibt mit `write_text`, also
**nicht atomar** — obwohl `shared/atomic_json.py` genau dafür existiert (v56.0). Wird die
Kette jetzt deploy-geschützt, ist ein SIGKILL mitten im Schreiben unwahrscheinlicher,
aber nicht unmöglich. Soll der Schreibweg auf `atomic_json` umgestellt werden? Dann gilt
die 403-Falle aus v60.2 (Rechte der Zieldatei) und eine HTTP-Prüfung ist Pflicht.

### 3.3 Nachgeholte Zeilen ausweisen (N5)

Ein Boolean genügt nicht. Regel:

1. Eine vorhandene Sessiondatei wird **nie** ersetzt.
2. Eine Nachholung wird **separat versioniert** und trägt: Abrufzeit, Zielsession, Grund,
   und ob sie aus eingefrorenen Rohdaten repariert oder **live nachgefragt** wurde.
3. Welche Version die Live-Ausgabe und welche den historischen Vergleich speist, wird
   ausdrücklich geregelt. `skew.html:835` lädt heute nur `<session>.json` und übernimmt
   die Walls ohne Qualitätskennzeichen — der Leser muss also mitgenommen werden (3.4).
4. Ein **Key-Levels-Reparaturlauf** nach erfolgreichem Snapshot braucht einen eigenen
   Wiederaufnahmeweg, der die Chain **nicht erneut abruft**.

⚠️ **Das betrifft eine Zeile, die heute schon da ist.** Die am 21.10. 06:43 UTC
geschriebene Zeile für Session 20.10. ist genau so eine Nachholung: Strikes und DTE zur
Session, IV aus dem Abruf am Folgetag. Sie steht derzeit **unmarkiert** zwischen den
regulären Zeilen. **Nutzerentscheidung:** als Nachholung kennzeichnen (sobald das Feld
existiert), oder entfernen und die Lücke stehen lassen.

### 3.4 Mindestkennzeichnung auf den Seiten (N6 — angenommen)

v2 hatte B9 vollständig verschoben. Codex hält dagegen, und das überzeugt mich: wenn der
Bau eine Qualitätsunterscheidung einführt, die auf der Seite nicht sichtbar ist, war sie
wirkungslos. `dealer-positioning.html:219` sagt „Dealer sind netto long Gamma",
`skew.html:869` markiert „am Flip", `key-levels.html:279` liest das Datum und zeigt es an
dieser Stelle nicht.

In diesen Bau gehört deshalb **das Minimum**: sichtbare Session samt Qualitätskennzeichen
in DE und EN, und bei Veraltung oder Nachholung werden Aussagen über den **aktuellen
Zustand** unterdrückt oder ausdrücklich historisch formuliert. Layout und Bedienung
bleiben außen vor.

### 3.5 Zeitbudget (B6, N7)

Gemessen am 21.10.: Snapshot allein ~7 min (06:36 → 06:43, 20/20 Ticker), Key Levels
danach 11 Ticker. Beides wird einmal **zusammen** gemessen, bevor eine Zahl in die Unit
kommt. Das Budget beginnt **vor** Sperrerwerb und Imports und deckt: Wartezeit auf die
Produktionssperre (deren `flock` hat selbst keine Frist, `produktionssperre.py:177`),
`warte_auf_app.sh`, beide Yahoo-Hosts (`yahoo_downloader.py:81`), die paginierten Chains
**beider** Programme (`compute_key_levels.py:60` holt eine zweite), Wiederholungen,
Veröffentlichung und Kill-Nachlauf. Das äußere `TimeoutStartSec` liegt darüber, die
Fristen des manuellen Workflows werden angeglichen. Dauer-429 für alle 20 Ticker wird
mit **gestellter Uhr** geprüft, nicht geschätzt.

### 3.6 Produktionssperre (B7 — abgenommen)

`modul_sperre("<name>")` auf Modulebene, `with produktion("<name>")` im `__main__`,
Entfernen aus `AUSNAHMEN` — Muster `nightly_refresh.py:18,580`. Gilt für beide
Programme. Die bestehenden GEX-Wächter importieren diese Module; ihre
Sperrverzeichnisse bleiben isoliert.

## 4. Wächter

`scripts/verify_gex_spot.py` im Gate, mit Mutationstest, Fixtures aus den **echten**
Probe-Antworten. Jeder Fall nennt den Befund, aus dem er kommt.

| # | Fall | aus |
|---|---|---|
| 1 | Yahoo gültig → Kurs, **kein** Massive-Abruf (Aufrufe gezählt) | B3 |
| 2 | Yahoo `close = null`, Schluss nachgewiesen (17.10. 00:15) → Massive-Kurs | B3 |
| 3 | Massive-Balken der **Vorsession** (19.10. 23:00) → verworfen | v66.20 |
| 4 | `rmt` < Sessionschluss **plus** gleichdatierter Massive-Balken → verworfen | B3 |
| 5 | `rmt` in der **Zukunft** → verworfen | N1 |
| 6 | **mehrere** Balken mit Sessiondatum → verworfen | N1 |
| 7 | `folgetag`: Balken S und S+1, `rmt` von S+1 → Kurs von **S** (700.0) | N1-Gegenbeleg |
| 8 | Massive leer · 403 · Timeout · Struktur kaputt · falsches Symbol · `c` als `bool` · `inf` · Sekunden statt Millisekunden → je `None` | B4, N4 |
| 9 | Yahoo-Adapter: `timestamp`/`close` **verschieden lang** → verworfen | N4 |
| 10 | 429 → Wiederholung, dann Erfolg; Dauer-429 → `None`, mit gestellter Uhr | B6, N7 |
| 11 | Fixtures **beiderseits des 01.11.2026** (Sommer-/Winterzeit) | B10 |
| 12 | **Echter Halbtag**, Schlusszeit unabhängig aus `sitzung_info` festgelegt | B10 |
| 13 | Feiertag, Archiv vorhanden → **kein Abruf**, keine Veröffentlichung, Key Levels laufen nicht | B5, N3 |
| 14 | **Zweiter Lauf derselben Session an einem normalen Handelstag**, sequenziell **und** konkurrierend → Hash von Summary, **allen** Profilen, Archiv, Key Levels unverändert | N2 |
| 15 | `main` bei 11/20 und 12/20 brauchbaren Tickern: unter der Grenze **jede** Ausgabedatei unverändert (Hash vor/nach) | B10 |
| 16 | Service-Hülle bei Snapshot 0 / „übersprungen" / 75 / Fehler / Timeout: Key Levels laufen **nur** bei „veröffentlicht" | N3 |
| 17 | `--no-write` am Feiertag: erlaubt, schreibt nichts | Antwort 3 |
| 18 | `adjusted=false` in der URL; Unit-Vertrag (`systemd-analyze`, Timeout im Container, in `install_timers.sh`, `gex_snapshot.yml` ohne `schedule`) | B5, B8 |
| 19 | Seite: veralteter/nachgeholter Stand → Kennzeichen sichtbar, Zustandsaussage unterdrückt, DE **und** EN | N6 |

Mutationen treffen den **Produktionspfad**; fehlender Anker oder Absturz zählt als
ungültig, nicht als gefangen. Der Hüllenpfad wird **ausgeführt**, nicht als Textmuster
gesucht (`verify_produktionssperre.py:423` erkennt nur direkte Skriptnamen).

## 5. Was NICHT gebaut wird

- Keine Rekonstruktion der Session 19.10. — der OI/IV-Stand existiert nicht mehr.
- Keine Änderung an der Reissleine.
- Keine Zeitgrenze als Umschaltkriterium; nur validierte Antworten entscheiden.
- Keine Indexunterstützung im Rückfall.
- Kein Seiten-Umbau über 3.4 hinaus.
- **Keine Änderung des Folgetag-Verhaltens** (Abschnitt 2.2.1).

## 6. Fragen an Runde 3

1. Trägt mein Widerspruch zu N1? Konkret: gibt es einen Fall, in dem die Annahme am
   Folgetag einen **falschen** Kurs ergibt — nicht nur einen, den der heutige Kommentar
   ausschließen wollte?
2. Ist die benannte Grenze des Massive-Nachweises (2.2.2, letzter Absatz) tragfähig, oder
   folgt daraus, dass der Rückfall gar nicht gebaut werden darf?
3. Deckt die Laufsperre in 3.2 den Weg vollständig, wenn `--no-write` sie nicht nimmt?
4. `atomic_json` für den Schreibweg (3.2, Nebenbefund): jetzt oder eigener Posten?
5. Reicht die Mindestkennzeichnung in 3.4, um N6 zu schließen?
