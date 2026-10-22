# Entwurf v2: Kurschart mit Options-Niveaus auf /key-levels (2026-10-22)

Runde 1 war **NICHT TRAGFÄHIG**, sieben Befunde. Alle sieben am Code nachgeprüft, alle
berechtigt. Diese Fassung ersetzt v1 vollständig; was sich geändert hat, steht in
Abschnitt 1 mit dem Befund, der es erzwungen hat.

## 1 Was Runde 1 widerlegt hat

### 1.1 Eine Wall gehört NICHT zu einem Verfall (Befund 1)

`_walls` summiert das Netto-Dealer-Gamma **je Strike über alle Kontrakte des Fensters**
(`compute_gamma_exposure.py:218`), und das Fenster ist `MAX_DAYS = 45`
(`snapshot_gex.py:37`, angewandt in `snapshot_gex_massive.py:425` als
`summary_c = [c for c in all_c if c["dte"] <= max_days]`). Call Wall, Put Wall und
Vol-Trigger sind damit **45-Tage-Aggregate ohne Verfallstrennung**. `exp`/`exp_dte`
entstehen ausschließlich im Max-Pain-Block (`compute_key_levels.py:217`,
`mp["exp"] = ex`) und gehören nur zu Max Pain.

Folgen, alle in dieser Fassung umgesetzt:

- Der gemeinsame `exp`-Kopf über allen vier Linien aus v1 ist **falsch** und entfällt.
  Das Feld heißt in der Historie `max_pain_exp` und beschriftet nur die Max-Pain-Linie.
- Die Verfallswechsel-Markierung für Wall-Linien entfällt. Es gibt keinen Verfall, auf
  den sich eine Wall bezieht.
- **Zurückgenommen:** meine Erklärung, der SPY-Sprung Call Wall 785 → 800 am 16.10. sei
  der Wochenroll. Die Wall-Werte belegen das nicht; der Sprung kann aus jeder
  OI-Verschiebung im 45-Tage-Fenster kommen. Die Zahlenreihe bleibt im Entwurf, die
  Deutung ist gestrichen.
- Statt des Verfalls trägt jede Zeile `gex_horizont_tage` (heute 45). Ändert sich der
  Horizont, sind ältere Zeilen nicht mehr vergleichbar — ohne das Feld wäre das
  unsichtbar.

### 1.2 Preisbasis: Mechanismus echt, Randabweichung gemessen null (Befund 2)

Der Einwand ist richtig: `prices` wird aus `adjclose`-skalierten Werten geschrieben
(`yahoo_downloader.py:105` → `nightly_refresh.py:105`), der GEX-Spot kommt ausdrücklich
unbereinigt (`snapshot_gex_massive.py:287`, `adjusted=false`), weil er die Strike-Basis
ist. Zwei Preisbasen in einem Bild sind ein echtes Problem.

**Gemessen** (Session 2026-10-21, alle 11 Ticker, lesend auf der Produktion): der
GEX-Spot ist auf den Cent gleich dem gespeicherten `close` **derselben Session** —
SPY 773,09 = 773,09, QQQ 725,20 = 725,20, META 697,52 = 697,52, 11 von 11 exakt. Das
deckt sich mit dem Befund aus v62: eine Kurszeile trägt den Adjustierungsstand ihres
Schreibzeitpunkts, die jüngste Zeile ist deshalb praktisch unbereinigt.

Die Abweichung entsteht erst **rückwärts**: eine Zeile, die vor einer seit dem
gezahlten Dividende geschrieben wurde, trägt den damaligen Stand. Die Größe ist durch
die seither gezahlten Ausschüttungen begrenzt — für SPY in v62 gemessen 1,005066 →
1,002483 → 1,000000 über zwei Ex-Tage, also rund 0,25 % je Quartal. Für HYG
(monatliche Ausschüttung, ~6 % p. a.) wären es über drei Monate rund 1,5 %.

Deshalb gilt in dieser Fassung:

- **Keine Umrechnung, keine Rekonstruktion.** Ein Verhältnis aus einem Spot/Close-Paar
  taugt nicht als Umrechnung (Befund 2 ausdrücklich), und ein Rückwärtspfad über
  `log_return` wäre ein **Total-Return**-Pfad und damit systematisch zu hoch in der
  Vergangenheit — er würde den Fehler vergrößern statt ihn zu beheben.
- Die Niveaus sind ausdrücklich **Referenzen von heute**, nicht damals bekannte Marken.
  Die Kopfzeile sagt das wörtlich.
- `shared/basisabweichungen()` (Schwelle 5 %, dasselbe Mittel wie im Health-Check)
  läuft über das **dargestellte** Fenster. Liegt ein Basisbruch darin, werden die Linien
  **nicht** gezeichnet, und die Kachel nennt den Bruch mit Datum. Das fängt Splits und
  Reverse-Splits (ETHA ×3) ab, nicht die stetige Dividendendrift.
- Die stetige Drift wird benannt, nicht geschätzt: unter dem Chart steht, dass Kerzen
  links eines Ex-Tags auf einem früheren Stand liegen und die Abweichung mit der
  Haltedauer wächst. Eine Zahl dazu könnten wir erst nennen, wenn `dividend_events`
  gefüllt ist (offener Posten der Roadmap).
- Das ist das Hauptargument für ein **kurzes Standardfenster**.

### 1.3 Lauftage sind keine Sessions (Befund 3)

v1 wollte beides in denselben Schlüsselraum legen. Jetzt:

- Altzeilen tragen `session: null`, `archiv_datum: "<Dateiname>"`,
  `stempel_art: "lauftag"`. Es gibt **keine** Verschiebung auf eine vermutete Session.
- Altzeilen erscheinen als **einzelne Punkte** in einem eigenen Bereich, ohne
  verbindende Linie und ohne Verbindung zur Sessionreihe. Die Sessionreihe liegt auf
  einer vollständigen Börsensitzungsachse (`SA.boersenkalender`) mit sichtbaren Lücken.
- Die Legende sagt bei den Punkten „Lauftag des Archivs, Session unbekannt".
- Die Zählung aus v1 (8 Wochenend-Stempel, 11 fehlende Werktage) bleibt als **Beschreibung
  des Bestands** stehen, nicht als Rekonstruktionsbeweis. Sie begründet nur, warum nicht
  rekonstruiert wird.
- Zusätzlich aus `OPTIONS.md:979` übernommen: in der Altzeit waren Bewertungsdatum und
  Verfallsausschluss laufzeitabhängig, zeitweise war der Spot veraltet. Altpunkte sind
  deshalb auch inhaltlich nicht mit Sessionwerten gleichartig — die Kachel sagt das.

### 1.4 Die Produktionssperre ist geteilt, nicht exklusiv (Befund 4)

`produktion()` nimmt `LOCK_SH` (`produktionssperre.py:173`) — parallele Läufe dürfen
gleichzeitig eintreten; sie schützt gegen die Aktivierungsmarke, nicht gegeneinander.

- Die Historie wird **ausschließlich** über `history_aktualisieren`
  (`atomic_json.py:116`, exklusiver flock, Lesen UND Schreiben unter derselben Sperre)
  geändert — Cron und Backfill benutzen denselben Weg, es gibt keinen zweiten.
- Die Kette veröffentlicht heute in drei Schritten (Summary, Profile, Archiv, dann Key
  Levels). Jede Historienzeile trägt `veroeffentlichung` = Kennung des Kettenlaufs; eine
  Session, deren Kennung nicht zu einem abgeschlossenen Lauf gehört, wird gelesen, aber
  als unvollständig gekennzeichnet.
- Wiederholung ist idempotent: gleiche Kennung + gleicher Schlüssel ersetzt, ein
  **widersprüchlicher** Wert bei gleicher Kennung ist ein Fehler und wird gemeldet.
- Zurückgenommen: der Satz aus v1, ein Fristablauf bedeute „Session ohne Snapshot".
  Er kann auch eine Teilveröffentlichung bedeuten.

### 1.5 Fehlt, gescheitert und veraltet sind drei Dinge (Befund 5)

`snapshot_gex_massive.py:533` veröffentlicht ab **60 %** des Universums — bei 30 Tickern
genügen 18. `compute_key_levels.py:197` fängt einen Kettenfehler ab und veröffentlicht
trotzdem GEX-Zeilen; der Lauf endet regulär mit Exit 0 (`:273`). Eine Zeile kann also
Walls tragen und Max Pain nicht, ohne dass irgendetwas rot wird.

Je Zeile deshalb: `felder: {call_wall: "ok"|"fehlt_gex", put_wall: …, vol_trigger: …,
max_pain: "ok"|"fehlt_chain"|"nicht_eindeutig"|"nicht_erhoben"}`, dazu
`max_pain_non_unique` (existiert in `key_levels.json` und wird heute nirgends
ausgewertet) und je Session `abdeckung: {soll, ist}`. Ein gescheiterter Lauf schreibt
**keine** Zeile; ein alter Wert wird nie unter einem neuen Datum fortgeschrieben. Das
Chart zeigt die letzte erfolgreiche Session mit ihrem Datum, nicht „aktuell".

### 1.6 Die Laufzeitreserve war keine (Befund 6)

Beide Schritte haben je **300 s** 429-Wartebudget (`snapshot_gex_massive.py:101`,
`compute_key_levels.py:56`). Von den 11 Minuten nominaler Reserve bleibt rechnerisch
**rund eine**. Dazu lädt GEX für vier Profil-Ticker `PROFILE_MAX_DAYS = 1200` statt 45
(`snapshot_gex.py:45`) — ein einheitlicher Sekundenwert je Ticker ist keine Grundlage.

- Die Umstellung des Universums erfolgt **erst nach einer Messung beider echter
  Rechenpfade mit den tatsächlichen 30 Tickern**, mit unverändertem Profilhorizont und
  getrennt ausgewiesener Abruf- und Wartezeit.
- `gex_kette.py --no-write` genügt dafür nicht: es überspringt Key Levels
  (`gex_kette.py:36`). Gebraucht wird ein Messpfad, der frisches GEX an Key Levels
  übergibt, ohne in die Produktionsdateien zu schreiben — Vorschlag: `--messlauf` mit
  Ausgabeverzeichnis, das die Kette durchreicht.
- Bleibt die Reserve unter 5 Minuten, wird das Universum **nicht** in einem Schritt
  erweitert; dann entscheidet der Nutzer über eine zweite Unit oder einen kleineren
  Schritt.

### 1.7 Die Auswahlregel war falsch beschrieben und zieht eine zweite Seite mit (Befund 7)

`call_oi`/`put_oi` in `options_skew.json` summieren **die geladene Kette bis 190 Tage
mit Strikes im Band ±30 % um den Spot** (`compute_options_skew.py:153`, `:184`, `:652`),
nicht den Frontverfall. Die Rangfolge aus v1 bleibt als Liquiditätsmaß gültig — gleiche
Regel für alle 163 Ticker, eine Session —, aber:

- Sie heißt künftig „Open Interest und Volumen der geladenen Kette ≤190 Tage, ±30 %
  Moneyness, Session 2026-10-21", nicht „Frontverfall".
- Es ist eine **Eintagsmessung**. Vor einer Universumsumstellung wird sie über
  mindestens 10 Sessions gemittelt; eine Rangsumme eines Tages entscheidet nicht über
  ein dauerhaftes Universum. Gleichstand: kleinerer OI-Rang gewinnt.
- Aus der Liquidität wird **keine** Aussage über die Aussagekraft einer Wall abgeleitet.
  Sie begründet nur, welche Ticker überhaupt eine belastbare Kette haben.
- **`CORE_OPTIONS` steuert auch `/options-flow`** (`compute_options_flow.py:372`), und
  `UNIVERSE` speist zusätzlich `/dealer-positioning` und die GEX-Spalten auf `/skew`
  (`dealer-positioning.html:314`, `skew.html:848`) sowie die Rückfall-Symbolmenge
  (`snapshot_gex_massive.py:193`). Siehe offene Entscheidung 3.1.

## 2 Was gebaut werden soll

### 2.1 Kurschart mit den heutigen Niveaus (`#kl-kurs-chart`)

- Tageskerzen des angewählten Tickers über `SA.kurse`, **Standard 1 Monat**, Umschalter
  1M / 3M / 6M. Begründung jetzt zweifach: fünf Tagespunkte tragen keine Achse (gegen
  den ursprünglichen Wunsch „ein paar Tage"), und die Dividendendrift der gespeicherten
  Kurse wächst mit dem Fenster (1.2).
- Vier waagerechte Linien aus `key_levels.json`, einfarbig Gold mit unterschiedlichen
  Strichmustern, **kein Grün/Rot**, jede mit Wert beschriftet, dazu der Spot.
- Kopfzeile wörtlich: „Niveaus der Session <session> — Walls und Vol-Trigger aus allen
  Verfällen bis <gex_horizont_tage> Tagen, Max Pain für den Verfall <max_pain_exp>.
  Referenzen von heute, keine damals bekannten Marken."
- `max_pain_non_unique: true` → gestrichelt und als „nicht eindeutig" beschriftet.
- Ein Niveau mit Feldstatus ≠ `ok` wird nicht gezeichnet; die Kachel nennt den Grund.
- Basisbruch im Fenster (1.2) → keine Linien, Grund mit Datum.

### 2.2 Verlauf der Niveaus

- Neue Datei `landing/data/key_levels_history.json`, geschrieben vom Kettenlauf über
  `history_aktualisieren`. Je Ticker und Session: `session`, `stempel_art`,
  `archiv_datum`, `veroeffentlichung`, `gex_horizont_tage`, `call_wall`, `put_wall`,
  `vol_trigger`, `max_pain`, `max_pain_exp`, `max_pain_non_unique`, `spot`, `felder`,
  `schema` (Version), je Session zusätzlich `abdeckung: {soll, ist}`.
- Einmaliger Backfill der 51 Alt- und 4 Session-Dateien; Altzeilen wie in 1.3.
- Sessionwerte als **Stufenlinie** mit der ausdrücklichen Angabe, dass die waagerechten
  Abschnitte keine zwischenzeitlich beobachteten Werte sind. Lücken bleiben Lücken.
- Max Pain erscheint im Verlauf erst ab der ersten eigenen Session (im GEX-Archiv nicht
  vorhanden, rückwirkend nicht herstellbar).
- Für Ticker ohne Archivgeschichte (alle neu aufgenommenen) bleibt der Verlauf leer, mit
  Grund.

### 2.3 Tabelle scrollbar, Universum 30

- `max-height` + `overflow-y: auto`, Kopfzeile fixiert (Muster `/skew` v66.22).
- Erweiterung erst nach der Messung aus 1.6 und der Entscheidung aus 3.1.

## 3 Offene Entscheidungen des Nutzers

1. **Universum.** (a) `CORE_OPTIONS` auf 30 erweitern — dann wächst `/options-flow`
   mit, mit mehr Abrufen und mehr Daten, und braucht eigene Prüfung. (b) Eine eigene
   Liste `KEY_LEVEL_TICKER` für Key Levels, `CORE_OPTIONS` unberührt — `/options-flow`
   bleibt bei 11, zwei Listen sind zu pflegen. Vorschlag: (b), weil die Erweiterung
   sonst eine Seite ändert, über die niemand gesprochen hat.
2. **Auswahlregel.** Nutzerwunsch war Marktkapitalisierung; wir haben sie nicht als
   Daten. Vorschlag: gemittelte Liquidität über 10 Sessions (1.7), die heutigen 20
   behalten, um die 10 liquidesten neuen ergänzen.
3. **Standardfenster** 1M statt „ein paar Tage" (2.1).

## 4 Fragen an den Prüfer

1. Hält der Datenvertrag in 2.2 jetzt — oder fehlt ein Feld, ohne das eine Zeile in drei
   Monaten nicht interpretierbar ist? Insbesondere: genügt `veroeffentlichung` als
   Kennung einer vollständigen Veröffentlichung, wenn die Kette in drei Schritten
   schreibt und dazwischen abbrechen kann?
2. Ist die Behandlung der Preisbasis in 1.2 tragfähig — gemessen gleiche Basis am
   rechten Rand, benannte wachsende Drift nach links, Bruchprüfung über
   `basisabweichungen()` —, oder darf ein Niveau über älteren Kerzen überhaupt nicht
   erscheinen?
3. Trägt die Trennung in 1.3 (Altpunkte ohne Linie, eigene Fläche, `session: null`), oder
   behauptet schon die gemeinsame Zeitachse zu viel?
4. Was übersieht der Backfill noch, nachdem Lauftag und Session getrennte Schlüssel
   haben?
5. Ist `--messlauf` (1.6) der richtige Weg für einen vollständigen Trockenlauf, oder gibt
   es im Bestand schon einen Pfad, der frisches GEX ohne Produktionswrites an Key Levels
   übergibt?
6. Welche Nebenwirkung hat Variante (b) aus 3.1 — eine zweite Tickerliste neben
   `CORE_OPTIONS` —, die ich nicht sehe?
7. Welche drei Prüfungen wären jetzt die wirksamsten, und welche davon lässt sich
   überhaupt deterministisch bauen?
