# Spec: Kurschart mit Options-Niveaus auf /key-levels

> Stand 2026-10-23 · kanonisch für dieses Vorhaben · **gebaut wird auf Grundlage dieser Spec**
>
> **Codex-Abnahme nach fünf Runden: BAUGRUNDLAGE TRAGFÄHIG mit drei Auflagen** — alle drei
> eingearbeitet (Leserbeschriftung „innerhalb der Spot-Toleranz" statt „Preisbasis belegt",
> `strike_stufe` samt Herkunft und maßgeblicher Kette im Historienvertrag, Sollbestand der
> Historie = GEX-Summary statt Key-Levels-Liste).
>
> Vorgeschichte: Entwurf [v1](review_prompts/2026-10-22_key_levels_chart_entwurf.md) und
> [v2](review_prompts/2026-10-22_key_levels_chart_entwurf_v2.md), beide von Codex als
> **nicht tragfähig** beurteilt (Runde 1: sieben Befunde, Runde 2: sechs). Alle Befunde
> wurden am Code nachgeprüft und sind hier eingearbeitet; wo eine Entscheidung offen ist,
> steht sie in Abschnitt 10 und nicht im Baukörper.

## 1 Zweck

Unter der Tabelle „Key Levels je Ticker" zeigt die Seite ein **Kurschart des angewählten
Tickers** mit den Options-Niveaus als waagerechten Linien: Call Wall, Put Wall, Max Pain,
Vol-Trigger. Dazu, soweit belegt, der **Verlauf** dieser Niveaus. Die Tabelle wird
scrollbar und zeigt mehr als die heutigen 11 Ticker.

Das Chart ist eine Darstellung vorhandener Werte. Es trifft keine Aussage über Richtung,
es ist kein Signal, und es wird nichts gezeichnet, was die Daten nicht tragen.

## 2 Gemessene Lage

Alles hier Genannte ist am Code oder lesend an der Produktion gemessen, mit Datum.
Vermutungen stehen nicht in diesem Abschnitt.

### 2.1 Was ein Niveau ist

| Größe | Grundlage | Quelle |
|---|---|---|
| Call Wall, Put Wall | Netto-Dealer-Gamma **je Strike, summiert über alle Verfälle ≤ 45 Tage** | `compute_gamma_exposure.py:218`, Fenster `MAX_DAYS = 45` (`snapshot_gex.py:37`), angewandt in `snapshot_gex_massive.py:425` |
| Vol-Trigger | Nulldurchgang des Gamma-Profils, Suchbereich ±20 % um den Spot | `compute_gamma_exposure.py:190` |
| Max Pain | **ein** gewählter Verfall, aus der Optionskette | `compute_key_levels.py:217` (`mp["exp"] = ex`) |

**Eine Wall gehört deshalb zu keinem Verfall.** Jede Beschriftung, die Walls einen Verfall
zuordnet, ist falsch; `exp`/`exp_dte` in `key_levels.json` beschreiben allein Max Pain.
Die Verlaufsreihe SPY 785 → 785 → 780 → 800 → 780 (13.–21.10.) ist damit **nicht** als
Verfallsroll erklärbar — der Sprung kann aus jeder OI-Verschiebung im 45-Tage-Fenster
kommen. Eine Deutung wird nicht angeboten.

Call Wall, Put Wall und Vol-Trigger können **regulär** fehlen: existiert auf der
passenden Spot-Seite kein Gamma mit passendem Vorzeichen, ist die Wall `None` statt einer
erfundenen Marke (`compute_gamma_exposure.py:229`); findet der Suchbereich keinen
Nulldurchgang, fehlt der Vol-Trigger. Das ist ein Ergebnis, kein Fehler.

### 2.2 Preisbasis — gemessen kompatibel, Abweichung beziffert

Die Strikes beziehen sich auf **unbereinigte** Kurse; der GEX-Spot wird deshalb mit
`adjusted=false` geholt (`snapshot_gex_massive.py:287`). Unsere `prices` entstehen aus
`adjclose`-skalierten Werten (`yahoo_downloader.py:105`), jede Zeile trägt den
Adjustierungsstand ihres Schreibzeitpunkts.

Gemessen gegen eine **unabhängige Nominalpreis-Referenz**
(Massive `/v2/aggs/.../range/1/day?adjusted=false`, 139 gemeinsame Handelstage,
05.04.–22.10.2026). Ausdrücklich **nicht** dieselbe Quelle wie der Spot: `_spot` nimmt
Yahoos unbereinigten Schluss zuerst und fällt nur bei `GRUND_KURS_FEHLT` auf Massive
`/prev` zurück (`snapshot_gex_massive.py:350`) — der Range-Endpunkt ist eine dritte,
davon unabhängige Reihe.

| Ticker | Median \|Abw.\| | max \|Abw.\| | Muster |
|---|---|---|---|
| TSLA (keine Ausschüttung) | 0,0000 % | +0,0013 % | keine Stufe |
| AAPL | 0,0000 % | −0,0921 % | eine Stufe |
| SPY | 0,0000 % | −0,2570 % | Stufe am 17.06. |
| DIA | 0,0000 % | −0,2721 % | Stufe am 12.06. |
| TLT | 0,0000 % | −0,4012 % | Stufe am 28.07. |
| HYG (monatlich, ~6 % p. a.) | 0,0000 % | −0,5451 % | Stufe am 26.08. |

Dazu: der GEX-Spot ist bei allen 11 heutigen Tickern **auf den Cent** gleich dem
gespeicherten `close` derselben Session (Session 21.10., 11 von 11).

**Was diese Messung trägt — und was nicht.** Sie trägt: *bei diesen sechs Reihen und
diesen gemeinsamen Tagen wurden diese Abweichungen beobachtet, und sie springen nur an
Ex-Tagen.* Sie trägt **nicht**: eine allgemeine Preisgleichheit, eine Fehlerschranke für
die übrigen 157 Ticker, und keinen Schutz gegen Splits oder einen konstanten
Skalierungsfehler. Ausschüttungsfreiheit hilft dagegen nicht — ETHA steht im
vorgeschlagenen Universum und hatte 2026-09-30 einen Basiswechsel um Faktor 3. Und
`basisabweichungen()` kann einen konstanten Faktor **strukturell nicht sehen**: es prüft
`|ln(close_t/close_{t-1}) − log_return_t|`, und dieser Ausdruck ist für 110/100 und
330/300 identisch null (`basisabweichung.py:60`).

Deshalb entscheidet nicht diese Messung über die Darstellung, sondern die Regel in 2.2a.
- Verworfen: eine Rückwärtsrekonstruktion über `log_return`. Sie ist ein
  **Total-Return**-Pfad und trifft den damaligen Nominalkurs ebenfalls nicht (Codex R2,
  Befund 1 — mein Vorzeichen in v2 war falsch).
- Verworfen als Nachweis: `basisabweichungen()` allein. Es bleibt als Bruchprüfung für
  Splits nützlich, gilt aber nicht als Basisbeleg.

### 2.2a Freigaberegel der Preisbasis — je Ticker, je Session, ohne Netz

Der im Archiv gespeicherte `spot` ist der unbereinigte Schluss der Session mit
Schlussnachweis (2.2). Ein Vergleich dagegen ist ohne jeden API-Abruf zu führen und
wächst mit der Historie:

> Eine Session gilt als **spot-konsistent** für einen Ticker, wenn ein session-gestempelter
> Archiv- oder Historienwert mit `spot` **und** eine belegte Strike-Stufe vorliegen und
> `|close_db(session) − spot(session)| ≤ strike_stufe / 2`. Fehlt der Spot **oder** die
> Strike-Stufe, ist die Session **unbelegt** — nicht belegt und nicht widerlegt.

**Was das Ergebnis heißt und was nicht** (Codex R4, Befund 1): „spot-konsistent", nicht
„Nominalpreis belegt". Beide Seiten stammen aus derselben Quelle — `_yahoo_spot` liest
`indicators.quote[0].close` (`snapshot_gex_massive.py:250`), und der Downloader nimmt
`adjclose` mit **Rückfall auf genau dasselbe Rohschlussfeld** (`yahoo_downloader.py:105`),
das der Nightly nach `prices.close` schreibt (`nightly_refresh.py:110`). Liefert Yahoo für
beide Felder denselben falschen Wert, ergibt der Vergleich null und bestätigt den Fehler.
Das Restrisiko ist **benannt, nicht behoben**; begrenzt wird es durch die Referenzmessung
aus 2.2 (dritte, unabhängig erhobene Reihe) und durch 9.5, die sie wiederholt. Eine
stärkere Freigabe bräuchte einen gespeicherten unabhängigen Referenzbeleg je Session —
ein eigener Posten, kein Teil dieser Spec.

**Die Schwelle ist eine gewählte Darstellungstoleranz, keine Übertrittsgarantie**
(Codex R4, Befund 2). Meine Herleitung in Runde 3 war falsch: bei Strike-Stufe 1,00,
Strike 100,00, Spot 99,90 und DB-Schluss 100,10 liegt die Abweichung mit 0,20 unter der
halben Stufe, und der DB-Kurs liegt trotzdem **oberhalb** des Strikes, der Spot
**unterhalb** — genau die Seitenzuordnung, die `_walls` bei `K >= spot` bzw. `K <= spot`
trifft (`compute_gamma_exposure.py:229`). Beim Vol-Trigger greift die Begründung ohnehin
nicht, er ist eine interpolierte Nullstelle, kein Strike (`:199`). Die halbe Stufe bleibt
als Toleranz, weil sie an der Strike-Granularität des jeweiligen Kontrakts hängt statt an
einem runden Prozentwert — aber sie garantiert keine unveränderte Seitenlage, und die Spec
behauptet das nicht mehr. Bei SPY sind 0,5 Punkte auf 773 rund 0,065 %; die Prüfung
rechnet jedoch **in Preispunkten**, nicht als Verhältnis (die Fassung aus Runde 3 mischte
beide Einheiten).

**Gemessen** (alle 20 Ticker der 4 session-gestempelten Archivtage, 80 Vergleiche):
**79 Vergleiche exakt 0,0000 %**, größte Abweichung **0,0219 %** (DIA, 15.10.). Gegenprobe
an den Lauftagszeilen: derselbe Vergleich liefert dort bis **5,9 %** (TSLA, 04.09.), weil
das Datum nicht die Session ist. Die Prüfung trennt diese beiden Fälle also messbar — das
ist ihr belegter Nutzen. Beides sind Beobachtungen, keine Fehlerschranke für andere
Ticker und kein Beleg für Quellenunabhängigkeit.

**Die Strike-Stufe ist Pflichteingabe** (Codex R4, Befund 3). Sie steht heute in keiner
Datei: der schlanke Archivschreiber führt sie nicht (`snapshot_gex_massive.py:573`), und
aus `top_call_oi`/`top_put_oi` lässt sie sich nicht belegen — fünf Strikes der größten OI
müssen nicht benachbart sein. Deshalb liefert **B1** je Ticker und Session
`strike_stufe` (kleinster Abstand zweier benachbarter Strikes der ausgewerteten Kette)
mit Herkunft. Fehlt sie, ist die Session **unbelegt**, und für die neueste dargestellte
Session heißt das: Linien aus. Ein geratener Standardwert ist ausgeschlossen, auch bei
`close == spot`.

Wirkung auf die Darstellung (verbindlich, nicht optional):

- Ist die **neueste dargestellte** Session nicht spot-konsistent, werden **keine**
  Niveaulinien gezeichnet; die Kachel nennt den Grund.
- Für die übrigen Sessions im Fenster steht die Abdeckung an der Kachel: **„a von b
  Sitzungen innerhalb der Spot-Toleranz"**. Ausdrücklich nicht „Preisbasis belegt" — der
  beidseitig gleiche Fehler würde diese Zahl erhöhen, obwohl die Basis falsch ist (Codex
  R5, Auflage 1). Sitzungen ohne Vergleich werden im Chart markiert, nicht stillschweigend
  mitgezeichnet.
- Überschreitet eine Sitzung die Schwelle, ist sie **nicht spot-konsistent**: Linien aus,
  Grund mit Datum und gemessener Abweichung. Das ist eine Aussage über die Konsistenz mit
  dem archivierten Spot, nicht über den Nominalpreis.
- Die Prüfung läuft im Browser über Werte, die ohnehin geladen werden. Kein Netzabruf,
  kein Schlüssel, keine Dividendentabelle.

### 2.3 Historie der Niveaus

| Archiv | Dateien | Stempel | Enthalten |
|---|---|---|---|
| `gex_history/` | 51 (03.08.–14.10.) | **Lauftag**, kein `session`-Feld, 8 Wochenend-Daten | call_wall, put_wall, zero_gamma, spot, regime, skew, GEX/Vanna/Charm |
| `gex_history_session/` | 4 (15., 16., 20., 21.10.) | `session`, `stempel_art: "session"` | dieselben |

- **Max Pain fehlt in beiden Archiven.** Es entsteht erst in `compute_key_levels.py` und
  wird nur in der aktuellen Datei gehalten. Rückwirkend nicht herstellbar: die rohen
  Ketten werden nicht archiviert.
- **Kein `exp`, keine Laufkennung, kein Soll-Universum, kein `generated_at`** im
  schlanken Archiv (`snapshot_gex_massive.py:573`).
- Im Zeitraum fehlen 11 Werktage, fast nur Montage: die verspäteten GitHub-Crons liefen
  nach Mitternacht UTC und stempelten den Folgetag. Der 19.10. ist dauerhaft verloren
  (Yahoo-Abendlücke). In der Altzeit waren zudem Bewertungsdatum und Verfallsausschluss
  laufzeitabhängig und der Spot zeitweise veraltet (`docs/OPTIONS.md`, Abschnitt
  Abendlücke) — Altwerte sind also auch **inhaltlich** nicht gleichartig mit
  Sessionwerten.

### 2.4 Verfügbarkeit je Ticker

Gemessen an `options_skew.json` (Session 21.10.): **alle 163 Ticker** des Options-Universums
hatten eine Optionskette — **36 ETFs, 127 US-Einzelaktien**, keiner ohne Kettenwerte.
Die Verfügbarkeit ist damit nicht die Grenze. Grenzen sind die Laufzeit (2.5) und die
Frage, ob ein Niveau auf dünner Kette noch etwas aussagt: 39 Ticker liegen unter 100 000
Kontrakten Open Interest, 19 unter 50 000 (dünnste: TRV, ARRY, HCA, TAN, MAR).

### 2.5 Laufzeit

`sa-gex-snapshot.service` am 21.10.: **22:15:05 → 22:25:28 = 10 min 23 s** für 20
GEX-Ticker plus 11 Key-Levels-Ticker; der Snapshot veröffentlichte 22:24:08, Key Levels
brauchten 80 s. Containerfrist 28 min, `TimeoutStartSec` 33 min.

Dazu zwei Posten, die eine lineare Hochrechnung verbieten: **beide** Schritte haben je
300 s 429-Wartebudget (`snapshot_gex_massive.py:101`, `compute_key_levels.py:56`), und
GEX lädt für vier Profil-Ticker `PROFILE_MAX_DAYS = 1200` statt 45 (`snapshot_gex.py:45`).

Grobe Fortschreibung, ausdrücklich als Planungsgröße: 30 Ticker ≈ 17 min, **50 Ticker
≈ 28 min** — also die Frist selbst, vor jeder Wartezeit. Mehr als 30 Ticker braucht
deshalb eine Änderung am Betrieb (Abschnitt 10.2), nicht nur eine längere Liste.

## 3 Datenvertrag `landing/data/key_levels_history.json`

**Sollbestand** (Codex R5, Auflage 3): die Historie führt **alle Ticker der GEX-Summary**
(heute 20), nicht nur die der Key-Levels-Liste (heute 11). Grund: ab Stufe C ist sie die
Vergleichsquelle der gemeinsamen Wall-Zelle, und `/skew` zeigt die Walls seiner GEX-Eingabe
(`skew.html:851`). Führte die Historie nur 11, verlören dort beim Quellenwechsel neun
Ticker ihre Klammer — eine Vertragslücke, kein eingetretener Fehler. Abnahmefall: **TLT
über den Quellenwechsel hinweg** behält seine Veränderungsangabe.

**Schlüssel einer Beobachtung** ist `(ticker, herkunft, session | archiv_datum, lauf)`.
Mehrere Läufe derselben Session können koexistieren; die Auswahl eines Lesers ist
festgelegt und nicht dem Gefühl überlassen:

1. nur Zeilen mit `lauf_vollstaendig: true`,
2. davon die mit der **jüngsten Abschlussmarke** (nicht der jüngsten Zeile),
3. bei gleicher Marke: Abbruch mit Meldung, denn dann ist der Bestand widersprüchlich.

Ein später gescheiterter Versuch verdrängt damit nie einen früher abgeschlossenen Lauf.
Eine Abschlussmarke bindet die **Artefaktversionen** ihres Laufs (Pfad plus Inhaltshash);
passt ein Artefakt nicht mehr dazu, gilt der Lauf als nicht abgeschlossen.

Eine Zeile je **Ticker und Beobachtung**. Geschrieben ausschließlich über
`shared.atomic_json.history_aktualisieren` (exklusiver flock, Lesen und Schreiben unter
derselben Sperre) — Cron und Backfill benutzen denselben Weg, einen zweiten gibt es nicht.

```
schema            2  (Version des Vertrags; ältere Zeilen werden nicht umgeschrieben)
ticker            "SPY"
herkunft          "kette" | "archiv"
session           "2026-10-21" | null      # null, wenn unbekannt
archiv_datum      "2026-09-12" | null      # Dateiname des Altarchivs
stempel_art       "session" | "lauftag"
lauf              "<Kennung des Kettenlaufs>" | null
lauf_vollstaendig true | false | null      # null = unbekannt (Altdaten)
gex_horizont_tage 45 | null                # null bei Altdaten: damalige Konfiguration unbelegt
call_wall         780.0 | null
put_wall          760.0 | null
vol_trigger       775.21 | null
max_pain          769.0 | null
max_pain_exp      "2026-10-22" | null
spot              773.09 | null
felder            { call_wall: <zustand>, put_wall: …, vol_trigger: …, max_pain: … }
gex_kette_vollst   true | false | null     # Kette des GEX-Laufs (Walls, Vol-Trigger)
mp_kette_vollst    true | false | null     # Kette des Key-Levels-Laufs (Max Pain, OI)
strike_stufe       1.0 | null              # maßgeblich fuer 2.2a
strike_stufe_quelle "gex_kette" | null     # woher sie stammt
```

**Maßgebliche Kette für `strike_stufe`** (Codex R5, Auflage 2): die **GEX-Kette**
`summary_c` (alle Kontrakte ≤ `gex_horizont_tage`, `snapshot_gex_massive.py:425`) — denn
die Walls, auf die sich die Toleranz bezieht, entstehen genau daraus. **Nicht** die
separat geladene Max-Pain-Kette eines einzelnen Verfalls (`compute_key_levels.py:215`);
die wäre eine andere Grundmenge und könnte eine andere Stufe ergeben.

Definition: kleinster Abstand zweier benachbarter Werte der **sortierten, auf eindeutige
Werte reduzierten** Strike-Liste dieser Kette, endlich und größer null. Ergibt sich kein
solcher Abstand (ein einziger Strike, nicht endliche Werte), ist `strike_stufe: null` →
die Session ist unbelegt (2.2a). Ein Schreib-/Lese-Rundlauf muss Stufe und Herkunft
erhalten; ohne sie kann eine vertragskonforme Zeile die Konsistenzprüfung gar nicht
erfüllen.

Zwei getrennte Felder, weil es zwei getrennte Abrufe sind: vollständiges GEX mit
unvollständiger Max-Pain-Kette ist ein realer Fall, der umgekehrte ebenso. Ein einzelnes
`kette_vollstaendig` könnte beides nicht ausdrücken (Codex R3, Befund 2).

`<zustand>` ist genau einer von:

| Zustand | Bedeutung | Gezeichnet? |
|---|---|---|
| `ok` | berechnet, Wert vorhanden | ja |
| `kein_niveau` | **regulär** berechnet, es existiert kein solches Niveau (kein Gamma passenden Vorzeichens, kein Nulldurchgang) | nein, mit Grund |
| `nicht_eindeutig` | berechnet, aber mehrdeutig (`max_pain_non_unique`) | ja, gestrichelt und benannt |
| `teilkette` | aus einer unvollständig geladenen Kette berechnet | nein, mit Grund |
| `quelle_fehlt` | GEX-Zeile bzw. Kette nicht vorhanden | nein, mit Grund |
| `nicht_erhoben` | zu dieser Beobachtung nie erhoben (Max Pain in Altdaten) | nein, mit Grund |

Je Session zusätzlich `abdeckung: {soll, ist}`.

**Begründung der Zustände** (Codex R2, Befund 3): `ok|fehlt` reicht nicht. Eine fehlende
Wall kann ein korrektes Ergebnis sein (2.1), eine vorhandene kann aus einer Teilkette
stammen — der Abruf gibt heute nach Erreichen der Seitengrenze die bisher gesammelten
Kontrakte zurück, ohne Vollständigkeitsstatus (`compute_key_levels.py:86`,
`snapshot_gex_massive.py:369`). **Pflichtänderung:** beide Abrufe geben ihren
Vollständigkeitszustand zurück, statt ihn zu verwerfen. Ohne das sind `ok` und
`teilkette` nicht unterscheidbar, und zehn weitere Statusfelder ändern daran nichts.

Ein gescheiterter Lauf schreibt **keinen Wert**, aber einen Versuchseintrag
(`felder` alle `quelle_fehlt`, `lauf_vollstaendig: false`) — sonst sind „nicht versucht",
„gescheitert" und „noch nicht archiviert" nicht unterscheidbar. Ein alter Wert wird
**nie** unter einem neuen Datum fortgeschrieben.

**Wer schreibt den Versuchseintrag** (Codex R3, Befund 5): `gex_kette.py`, und zwar
**vor** dem ersten Teilschritt, nicht danach — ein getöteter Prozess kann hinterher
nichts mehr schreiben. Der Eintrag entsteht also beim Start des Laufs mit
`lauf_vollstaendig: false` und wird erst von der Abschlussmarke auf `true` gehoben. Ein
Abbruch an jeder Stelle hinterlässt damit eine Zeile, die sagt, dass versucht wurde —
und ein Leser nimmt sie nach Regel 4 nicht. Der Abbruchtest in 9.3 prüft genau das.

## 4 Veröffentlichungsvertrag

Heute ist aus dem Code folgende Reihenfolge möglich (Codex R2, Befund 2): Lauf A schreibt
seine Summary, Lauf B überschreibt sie für dieselbe Session, und Key Levels von Lauf A
liest anschließend die Summary von B — `_load_gex` prüft nur Stempelart und Session
(`compute_key_levels.py:175`), die Kette übergibt kein konkretes Ergebnis
(`gex_kette.py:93`). Die geteilte Produktionssperre verhindert das nicht
(`produktionssperre.py:173`, `LOCK_SH`), und ein exklusiver Lock erst beim Historien-Merge
auch nicht.

Pflicht, bevor die Historie geschrieben wird:

1. **Laufgebundene Übergabe.** Der Snapshot gibt seine Kennung und den Pfad seines
   Ergebnisses aus; die Kette reicht beides an Key Levels durch (`--gex-datei`, `--lauf`).
   Key Levels liest **nicht** mehr die gemeinsame Datei nach Session, sondern genau diese
   Eingabe, und bricht ab, wenn Kennung oder Session nicht passen.
2. **Abschlussnachweis.** Der Kettenlauf veröffentlicht als letzten Schritt eine Marke
   mit seiner Kennung und der Liste der Pflichtartefakte. Erst mit dieser Marke gilt
   `lauf_vollstaendig: true`. Exit 0 genügt nicht — Key Levels fängt Kettenfehler ab und
   endet regulär mit 0 (`compute_key_levels.py:197`, `:273`).
3. **Leser wählen nur abgeschlossene Läufe.** Das Chart zeigt die letzte Session mit
   `lauf_vollstaendig: true`, mit ihrem Datum, nicht „aktuell".
4. **Serialisierung.** Zwei Kettenläufe derselben Session laufen nicht gleichzeitig: die
   Kette hält zusätzlich einen **exklusiven** Lock auf `logs/sperre/gex_kette.lock`.

## 5 Backfill der Altarchive

- Liest die 51 Alt- und 4 Sessiondateien **einmalig**, schreibt über denselben Weg wie der
  Cron, ist wiederholbar ohne anderes Ergebnis.
- Altzeilen: `herkunft: "archiv"`, `session: null`, `archiv_datum: "<Dateiname>"`,
  `stempel_art: "lauftag"`, `lauf: null`, `lauf_vollstaendig: null`,
  `gex_horizont_tage: null`, `max_pain: null` mit `nicht_erhoben`, `abdeckung` unbekannt.
  Es wird **nichts** erfunden und keine Session rekonstruiert.
- **Konfliktregel** (Codex R2, Befund 4): eine Zeile mit `herkunft: "kette"` wird von einer
  Archivzeile **nie** ersetzt oder verschlechtert. Treffen zwei Zeilen zusammen, gewinnt
  die mit mehr belegtem Inhalt; bei Widerspruch gleicher Herkunft und Kennung bricht der
  Backfill mit Meldung ab, statt zu überschreiben.
- **Die 4 session-gestempelten Archivdateien sind ein eigener Fall** (Codex R3, Befund 5):
  sie haben eine Session, aber keinen Abschlussnachweis. Sie werden mit
  `herkunft: "archiv"`, `session: "<Datum>"`, `stempel_art: "session"`,
  `lauf_vollstaendig: null` übernommen — die Regel „`session: null`" gilt nur für die
  Lauftagsdateien. Als Vergleichswert für 6.1a sind sie damit zulässig, aber
  gekennzeichnet; als „abgeschlossener Lauf" (4) gelten sie **nicht**.
- Herkunft wird mitgeschrieben: Archivdatei und Inhaltshash.

## 6 Darstellung

### 6.1 Kurschart (`#kl-kurs-chart`, unter dem OI-Profil)

- Tageskerzen des angewählten Tickers über `SA.kurse`; Standard **1 Monat**, Umschalter
  1M / 3M / 6M. Begründung: fünf Tagespunkte tragen keine Achse (eine Intraday-Reihe
  haben wir nicht), und die Dividendentreppe aus 2.2 wächst mit dem Fenster.
- Vier waagerechte Linien, **einfarbig Gold mit verschiedenen Strichmustern**, jede mit
  Wert beschriftet, dazu der Spot. Kein Grün/Rot — eine grüne Put-Wall neben einer roten
  Call-Wall liest sich als Kauf-/Verkaufsmarke (dieselbe Regel wie auf `/skew`,
  `/intermarket`, `/index-effekt`).
- Kopfzeile wörtlich: „Niveaus der Session &lt;session&gt; · Walls und Vol-Trigger aus allen
  Verfällen bis &lt;gex_horizont_tage&gt; Tagen · Max Pain für den Verfall &lt;max_pain_exp&gt; ·
  Referenzen von heute, keine damals bekannten Marken."
- **Eine** Zeichenregel: gezeichnet wird genau bei Zustand `ok` und `nicht_eindeutig`
  (letzteres gestrichelt und als „nicht eindeutig" beschriftet). Jeder andere Zustand
  erscheint als Textzeile mit Grund, nicht als Linie.
- Liegt im dargestellten Fenster ein Basisbruch (`basisabweichungen()`), werden **keine**
  Linien gezeichnet und der Bruch mit Datum genannt.
- Unter dem Chart ein Satz zur Dividendentreppe mit der gemessenen Größenordnung aus 2.2.

### 6.1a Veränderung von Call Wall und Put Wall (Nutzerwunsch 2026-10-22)

Hinter dem Wert steht die Veränderung gegenüber der vorigen Session in Klammern, farbig:
**nach oben grün, nach unten rot**, `±0` in Grau. Das ist keine neue Konvention — genau
diese Darstellung läuft seit v66.23 auf `/skew` (`_wallZelle`, `skew.html:823`), und die
Richtung ist dort schon entschieden. Sie ist auch für beide Walls kohärent: ein steigender
Strike heißt, die Marke ist nach oben gewandert, bei der Put Wall die Unterstützung, bei
der Call Wall der Widerstand.

**Die Linien selbst bleiben einfarbig Gold** (6.1). Gefärbt wird die *Veränderung* — eine
vorzeichenbehaftete Differenz —, nicht das Niveau. Ein grünes Niveau wäre eine Aussage
über Richtung, eine grüne Differenz ist die Richtung der Differenz.

Pflicht dabei:

- **Gemeinsame Funktion, keine zweite Kopie.** `_wallZelle` und die Suche nach der
  Vergleichssession wandern nach `landing/js/` (Vorschlag `SA.walls.zelle(…)`,
  `SA.walls.vorherigeSession(…)`); `/skew` und `/key-levels` rufen dieselbe Funktion. Eine
  Kopie würde driften — das ist die Zwillingslehre aus Welle 1.
- **Halbe Strikes nicht wegrunden.** `_zahl` zeigt ganze Zahlen ohne und sonst eine
  Nachkommastelle, und die Farbe folgt dem **ungerundeten** Vorzeichen. Gerundet wurde
  99,5 → „100 (±0)", und der Rückgang verschwand (Codex-Befund zu v66.23). Die Regel wird
  mit der Funktion übernommen, nicht neu erfunden.
- **Vergleichsberechtigung, beide Endpunkte** (Codex R3, Befund 3): ein Vergleich entsteht
  nur, wenn **für beide** Sessions ein numerischer Wall-Wert mit Feldzustand `ok` oder
  `nicht_eindeutig` vorliegt, die Quelle session-gestempelt ist, der Lauf abgeschlossen ist
  und der Rechenhorizont (`gex_horizont_tage`) übereinstimmt. Ein Sessionstempel allein
  wertet unbekannte Qualität **nicht** zu `ok` auf: er schließt weder einen abgebrochenen
  Lauf noch einen Wert aus einer Teilkette aus. Eine farbige Differenz darf nie aus einem
  Wert entstehen, den dieselbe Spec als Linie verbietet.
- **Bestandsarchive** (`gex_history_session/`, heute 4 Dateien) tragen keinen
  Abschlussnachweis — ihre Vollständigkeit ist **unbekannt**, nicht wahr. Sie sind bis
  Stufe C die einzige Quelle; die Klammer trägt dann die Kennzeichnung „Vergleich aus dem
  Bestandsarchiv, Vollständigkeit unbelegt" (Tooltip). Ab Stufe C ist
  `key_levels_history.json` die Quelle, und die Kennzeichnung entfällt für Zeilen mit
  Abschlussmarke. Diese Übergangsregel ist eine **Nutzerentscheidung** (10.5): die
  Alternative wäre, die Klammer erst ab Stufe C zu zeigen.
- **Die direkte Vorsession kommt aus dem Börsenkalender**, nicht aus „kein Samstag,
  kein Sonntag". Die heutige Funktion auf `/skew` rechnet so (`skew.html:842`) — für
  Freitag, 27.11.2026 hält sie Donnerstag für die Vorsession, obwohl Thanksgiving fällt
  und die Vorsitzung Mittwoch der 25.11. ist (`sitzungen('NYSE', …)` nachgerechnet: der
  26.11. ist keine Sitzung). Sie setzt dort heute ein `*`, das nicht hingehört. Mit der
  Herauslösung wird das über `SA.boersenkalender` korrigiert — eine **beabsichtigte**
  Änderung an `/skew`, siehe 9.0.
- **Lauftagszeilen sind nie Vergleichswert** (2.3). Zusätzlich prüft die gemeinsame
  Funktion `stempel_art` selbst; die heutige prüft nur Session, Reihenfolge und
  `tickers` (`skew.html:840`) und würde eine als `lauftag` markierte Datei annehmen.
- **Kein Vergleich, keine Klammer.** Fehlt die Vorsession, erscheint der Wert ohne
  Klammer; ist die Vergleichssession nicht die direkte Vorsession, trägt die Klammer `*`
  und der Tooltip nennt das Datum. Neu aufgenommene Ticker haben anfangs keinen
  Vergleichswert — das ist der Normalfall, nicht ein Fehler.
- Max Pain und Vol-Trigger bekommen die Klammer vorerst **nicht**: Max Pain fehlt in der
  Historie ganz (2.3), der Vol-Trigger ist stetig und nicht strikequantisiert, seine
  Differenz bräuchte eine eigene Rundungsregel. Nach Stufe C nachrüstbar, dann mit
  derselben gemeinsamen Funktion.

### 6.2 Verlauf

- Sessionwerte auf einer vollständigen Börsensitzungsachse (`SA.boersenkalender`), als
  **Stufenlinie**, Lücken bleiben Lücken. Dabei der Satz, dass die waagerechten Abschnitte
  keine zwischenzeitlich beobachteten Werte sind.
- Altwerte als **einzelne Punkte** in eigener Fläche, ohne verbindende Linie und ohne
  Verbindung zur Sessionreihe; Tooltip und Achse zeigen das **Archivdatum**, die Legende
  sagt „Lauftag des Archivs, Session unbekannt" und nennt die inhaltlichen Unterschiede
  aus 2.3.
- Max Pain im Verlauf erst ab der ersten eigenen Session.
- Ticker ohne Archivgeschichte: leerer Verlauf **mit Grund**, keine leere Fläche.

### 6.3 Tabelle

`max-height` + `overflow-y: auto`, Kopfzeile fixiert (Muster `/skew`, v66.22). Beide
Sprachen über `data-i18n`, `_JSON_VER` erhöhen.

## 7 Ticker-Universum

Kandidaten sind alle 163 Ticker mit Kette (2.4). Für die Auswahl gilt:

- Maß ist die **Options-Liquidität**, nicht die Marktkapitalisierung: letztere haben wir
  nicht als Daten, und eine Wall ist nur dort ein Niveau, wo Open Interest liegt. Belegt
  an der Rangfolge: HYG liegt nach Open Interest auf Platz 4 (8,76 Mio Kontrakte, mehr als
  IWM), TLT auf Platz 2 — beide fehlen in jeder Marktkapitalisierungsliste.
- Das Maß ist **Open Interest und Volumen der geladenen Kette ≤ 190 Tage mit Strikes im
  Band ±30 %** (`compute_options_skew.py:153`, `:184`, `:652`) — nicht des Frontverfalls.
- Eine Eintagsmessung entscheidet kein dauerhaftes Universum. Das Verfahren ist genau
  festgelegt, weil „Mittel der Tagesränge" und „Rang der gemittelten Summen" verschiedene
  Ergebnisse liefern (Codex R3, Befund 6):
  1. gemeinsames Fenster der letzten **10 abgeschlossenen Sessions**, identisch für alle
     Ticker;
  2. je Ticker und Session `oi = call_oi + put_oi` und `vol = call_vol + put_vol`;
  3. **Mindestabdeckung 8 der 10** Sessions, sonst fällt der Ticker aus der Auswahl (nicht
     aus dem Universum) — ein Ticker mit 3 Beobachtungen ist nicht mit einem mit 10
     vergleichbar;
  4. je Größe das **arithmetische Mittel über die vorhandenen Sessions**, dann ein Rang je
     Größe, dann die Rangsumme. Nicht: Mittel der Tagesränge.
  5. Gleichstand der Rangsumme: kleinerer OI-Rang gewinnt; danach alphabetisch, damit die
     Liste reproduzierbar ist.
- Die vier Summen stehen heute nicht in der Tickerhistorie (`compute_options_skew.py:1278`)
  → sie werden dort ergänzt, dann 10 Sessions gesammelt, dann gemessen, dann umgestellt.
- Aus der Liquidität wird **keine** Aussage über die Aussagekraft einer Wall abgeleitet.

Momentaufnahme 21.10., Rangsumme OI + Volumen, Top 50 (22 ETFs, 28 Aktien; 19 der heutigen
20 GEX-Ticker enthalten, nur XLK nicht):

```
 1 SPY    2 QQQ    3 IWM    4 NVDA   5 AAPL   6 TSLA   7 TLT    8 AMZN   9 IBIT  10 HYG
11 CRWV  12 NFLX  13 INTC  14 GOOGL 15 META  16 XLF   17 GLD   18 MSFT  19 MU    20 SLV
21 SMH   22 AMD   23 XLE   24 ORCL  25 PLTR  26 AVGO  27 SMCI  28 KRE   29 IREN  30 ETHA
31 BAC   32 USO   33 UBER  34 SOXL  35 PFE   36 NBIS  37 IEF   38 GDX   39 NKE   40 XLU
41 WMT   42 XLP   43 IGV   44 BA    45 NOW   46 CSCO  47 SOXX  48 BE    49 CRWD  50 DIA
```

**Abhängigkeit, die nicht übersehen werden darf** (Codex R2, Befund 5): Key Levels rechnet
Walls nicht selbst, sondern übernimmt sie aus der gemeinsamen GEX-Summary
(`compute_key_levels.py:205`). Eine eigene Liste nur für Key Levels versorgt die neuen
Ticker also **nicht** mit Walls. Wächst dagegen `UNIVERSE`, wachsen `/dealer-positioning`
und die GEX-Spalten auf `/skew` mit (`dealer-positioning.html:314`, `skew.html:848`) sowie
die Spot-Rückfallmenge (`snapshot_gex_massive.py:193`); wächst `CORE_OPTIONS`, wächst
`/options-flow` mit (`compute_options_flow.py:372`). Jede dieser Seiten ist Teil der
Abnahme, oder das Universum wächst dort nicht.

## 8 Baufolge

Die Reihenfolge folgt Codex R3: **B vor A**. Ein Chart, das nach Feldzuständen zeichnen
soll, kann nicht vor dem Erzeuger dieser Zustände freigegeben werden — sonst müsste Stufe A
unbelegte Werte als `ok` behandeln (`key_levels.json` trägt heute keine Zustände,
`compute_key_levels.py:258`) oder die Linien unterdrücken. Beides war in v2 verdeckt.

| Stufe | Inhalt | Voraussetzung |
|---|---|---|
| **B1** | Beide Kettenabrufe geben ihren Vollständigkeitszustand zurück statt ihn zu verwerfen (`compute_key_levels.py:86`, `snapshot_gex_massive.py:369`); `key_levels.json` **und die GEX-Summary samt Archiv** tragen `felder`, `gex_kette_vollst`, `mp_kette_vollst`, `gex_horizont_tage`, `strike_stufe` | keine |
| **B2** | Laufgebundene Übergabe an Key Levels, Abschlussmarke mit Artefakthashes, exklusive Kettensperre, Leserauswahl (4) | B1 |
| **A** | Kurschart mit den heutigen Niveaus, eine Zeichenregel, Kopfzeile, Basisfreigabe (2.2a), scrollbare Tabelle (weiter 11 Ticker), Wall-Veränderung über die gemeinsame Funktion (6.1a) | B1, B2 |
| **C** | `key_levels_history.json` schreiben, Verlauf der Sessionwerte, Vergleichsquelle der Klammer wechselt (6.1a) | A |
| **D** | Backfill der Altarchive, Altpunkte als eigene Fläche | C |
| **E1** | Die vier Liquiditätssummen in die Tickerhistorie schreiben (reine Datensammlung, ändert keine Anzeige) | keine |
| **E2** | Laufzeit beider Pfade mit den tatsächlichen Zieltickern messen (`--messlauf`), 10 Sessions Liquidität auswerten | E1, B2 |
| **E3** | Universum erweitern, Betrieb anpassen | E2 **und** Entscheidungen 10.2 + 10.3 |

E war in v2 ein Zirkelschluss: die Erweiterung setzte Entscheidung 10.2 voraus, und 10.2
sollte nach der Messung aus E fallen. Jetzt sammelt E1, misst E2, und erst E3 stellt um.
E1 und E2 können parallel zu A–D laufen; sie ändern nichts Sichtbares.

Die Herauslösung der Wall-Zelle (6.1a) gehört zu A und **ändert `/skew` absichtlich**
(Kalender statt Mo–Fr, `stempel_art`-Prüfung). Das ist keine Regression, sondern die
Korrektur zweier Defekte — 9.0 prüft beides getrennt.

**`/skew` braucht die Berechtigungsfelder ebenfalls** (Codex R4, Befund 4): die Seite
liest Walls aus der GEX-Summary und die Vorwerte aus dem GEX-Archiv (`skew.html:833`,
`:848`), und beide Schreiber führen die neuen Felder heute nicht
(`snapshot_gex_massive.py:548`, `:573`). Ohne sie würden bei strenger Anwendung der
gemeinsamen Funktion auf `/skew` die Klammern verschwinden — oder ein Adapter müsste
Berechtigungen erfinden. Deshalb umfasst B1 ausdrücklich **beide** Ausgaben und den
**größeren Tickerbestand** der Summary (20, nicht 11). Die Archiv-Ausnahme 10.5 ersetzt
diesen Vertrag nicht, sie regelt nur die Zeit, bis das Archiv die Felder trägt.

## 9 Prüfplan

Je Stufe ein Wächter mit Mutationstest, alle im Gate. Die Beweisregeln des Projekts
gelten: `[Aufbau]` nur für Eigenschaften der Vorrichtung, Endmarker muss erreicht werden,
jede Mutation benennt die Prüfung, die sie reißen muss, eine Ausnahme ist kein Nachweis.

0. **Gemeinsame Wall-Zelle** (6.1a) — die herausgelöste Funktion gegen beide Seiten: halbe
   Strikes (99,5 darf nicht als „100 (±0)" erscheinen), Farbe nach ungerundetem Vorzeichen,
   fehlende Vorsession ohne Klammer, beide Endpunkte berechtigt, Lauftagszeile nie als
   Vergleich, `stempel_art` geprüft. Die direkte Vorsession wird am **Börsenkalender**
   geprüft, mit Freitag 27.11.2026 als Sollfall (Vorsitzung ist der 25.11., nicht der 26.).
   Der Erhaltungsvertrag für `/skew` ist **„keine unbeabsichtigte Regression"**, nicht
   „unverändert": Referenzzustand, Datumsformat, Übersetzung und das erneute Rendern nach
   `sa:i18n-bereit` bleiben erhalten, Kalender- und Stempelprüfung sind beabsichtigte
   Korrekturen und werden **nicht** gegen den Altstand getestet.
1. **Mehrverfallsfall durch den echten Erzeuger bis in die Seite** — eine Kette mit
   mehreren Verfällen, Max Pain auf einem anderen Verfall als dem nächsten, dazu ein Fall
   ohne Max Pain und einer mit `max_pain_non_unique`. Prüft, dass keine Wall einem Verfall
   zugeordnet wird und die Zeichenregel greift.
2. **Preis- und Zeichenpfad in jsdom mit analytischen Fällen** — Dividendenstufe, Split,
   konstanter Skalierungsfehler, fehlender `log_return`, fehlende Sitzung, veraltete
   Niveaus, vertauschte Antwortreihenfolge beim Tickerwechsel.
3. **Linux-Prozessprobe des echten Ketten- und Backfillpfads** — zwei verschachtelte
   Läufe derselben Session, Abbruch zwischen zwei Veröffentlichungsschritten,
   Backfill-Konflikt gegen eine bestehende Kettenzeile, Wiederholung. Prüft Dateiinhalt,
   Erhalt der Historie und Exit-Status.
4. **Spot-Konsistenz (2.2a)** — deterministisch und im Gate, weil sie kein Netz braucht:
   `close == spot` ist konsistent, eine Abweichung über der halben Strike-Stufe ist
   widerlegt (Linien aus), ein fehlender Spot **oder eine fehlende Strike-Stufe** ist
   unbelegt (ebenfalls Linien aus, auch bei `close == spot`). Dazu drei Gegenproben: eine
   Lauftagszeile, die als Beleg nicht zählen darf; ein einseitiger Skalierungsfehler, den
   die Prüfung findet, `basisabweichungen()` aber nicht; und der **beidseitig gleiche**
   Fehler (Spot und Close tragen denselben falschen Wert), der die Prüfung bestehen
   **muss** — der Test hält fest, dass sie ihn nicht findet, damit niemand später eine
   Garantie hineinliest.
5. **Nominalpreis-Referenz als Messlauf** (die Messung aus 2.2) — gegen Massive
   `adjusted=false`, als eigener Lauf außerhalb des Gates (braucht Netz und Schlüssel).
   Sie belegt nicht die Freigabe, sondern kontrolliert die Annahme hinter 2.2a: dass der
   archivierte `spot` wirklich ein Nominalpreis ist.
6. **Auswahlverfahren** (7) — deterministischer Test des Rangverfahrens: gleiche Rangsumme,
   ein Ticker mit 7 von 10 Sessions (muss ausfallen), ein Ticker mit fehlendem Volumen,
   und der Nachweis, dass „Mittel der Tagesränge" ein anderes Ergebnis liefert als die
   vorgeschriebene Reihenfolge.

## 10 Offene Nutzerentscheidungen

1. **Standardfenster** 1M statt „ein paar Tage" (6.1).
2. **Universumsgröße und Betrieb.** 30 Ticker passen vermutlich in die Frist, **50 nicht**
   (2.5). Für 50 gibt es drei Wege: die Kette in zwei Timer teilen (GEX, dann Key Levels
   mit laufgebundener Übergabe), die Containerfrist und `TimeoutStartSec` erhöhen, oder bei
   30 bleiben. Entscheidung erst nach der Messung aus Stufe E.
3. **Welche Seiten mitwachsen** (7): `/dealer-positioning` und `/skew` hängen an `UNIVERSE`,
   `/options-flow` an `CORE_OPTIONS`. Mitwachsen und mitprüfen, oder Key Levels einen
   eigenen GEX-Pfad geben.
4. **Dünne Ticker.** 39 der 163 liegen unter 100 000 Kontrakten Open Interest. Mindestmaß
   setzen oder alle anbieten und die Dünne an der Zeile ausweisen.
5. **Wall-Veränderung vor Stufe C** (6.1a): die Klammer ab Stufe A aus dem Bestandsarchiv
   zeigen, mit dem Hinweis „Vollständigkeit unbelegt" — oder erst ab Stufe C, dann aber
   mit Abschlussnachweis. Die erste Variante zeigt die gewünschte Veränderung früher und
   entspricht dem, was `/skew` heute schon tut; die zweite ist strenger.
