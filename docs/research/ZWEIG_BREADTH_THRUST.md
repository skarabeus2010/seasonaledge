# Zweig Breadth Thrust — Recherche, Datenlage und Spezifikation

> Stand 2026-10-27 · **Entwurf v3** — Codex R1 „tragfähig mit Auflagen" (13 Befunde), R2 **„Freigabe mit Auflagen"**
> (4 Befunde), alle eingearbeitet ([R1](../review_prompts/2026-10-27_zweig_breadth_thrust_r1_antwort.md),
> [R2](../review_prompts/2026-10-27_zweig_breadth_thrust_r2_antwort.md))
> · nichts gebaut, nichts in die DB geschrieben.
> Nutzerauftrag: Recherche zum Zweig-Kaufsignal, benötigte Indikatoren und Daten, Spezifikation zur Umsetzung,
> Performance-Auswertung 10 / 30 / 60 / 90 / 120 Tage nach dem Signal.

## 0. Kurzfassung

- **Das Signal braucht eine Datenreihe, die wir nicht haben:** die tägliche Zahl steigender und fallender Titel an
  der NYSE (Advances/Declines). Aus unseren ~200 US-Titeln lässt sie sich nicht ableiten (falsches Universum).
- **1965-03-01 bis 2020-02-10 gibt es sie frei** (Archiv unicorn.us.com, eingestellt). Nach Bereinigung (38
  Phantomzeilen an Börsenschließungen, 3 fehlende Sitzungen, Nullzeilen) trifft die Probe **alle acht Termine, die
  Greg Morris für 1965–2014 nennt**, plus einen zusätzlichen (Mai 2004, bei McClellan belegt) und 2015/2019.
  Das stützt Archiv und Definition — **beweist** die Fensterregel aber nicht (Abschnitt 1).
- **2020-02-11 bis heute fehlt sie** — dort liegen die viel zitierten Signale November 2023 und April 2025.
  Günstigster Kandidat: **McClellan-Historienpaket ab 1960 für 40 USD** bzw. **Pinnacle NYSE-Breite ab 1940
  (39 USD, Updates ab 20 USD/Monat)** — Dateiaufbau und Anzeigerechte vor dem Kauf klären.
- **Das Signal reagiert stark auf jede Definitionsentscheidung** (Schwelle, Glättung, Fensterregel, Nenner).
  Die Definition wird vorab fest im Code verankert, nicht nachträglich auf schöne Ergebnisse optimiert.
- **Stichprobe klein:** 11 Signale 1965–2020 (mit 2023/2025 voraussichtlich 13), zwei überlappen ab 60 HT.
  Auswertung **beschreibend**: Einzelfälle, Basisrate, Fallzahl an jeder Zahl, keine Signifikanzbehauptung.

## 1. Definition

Verbreitete Fassung (Morris, StockCharts, McClellan). Die Zuschreibung an Zweigs Buch *Winning on Wall Street*
(1986) ist **nicht seitengenau belegt** — Arthur Hill (StockCharts, 11/2023) schreibt, der Indikator stehe dort
nicht. Wir nennen ihn nach der Literatur, ohne Buchzitat.

```
Anteil_t = A_t / (A_t + D_t)               # NYSE-Zählung, Unveränderte NICHT im Nenner
EMA_t    = EMA_{t-1} + 2/11 · (Anteil_t − EMA_{t-1})
Signal   = EMA steigt von < 0,40 auf > 0,615 innerhalb von ≤ 10 Sitzungen
```

| Frage | Festlegung | Grundlage |
|---|---|---|
| Glättung | EMA, `alpha = 2/11`, rekursiv | Morris; SMA ergibt eine andere Liste (19 Signale) |
| Nenner | A + D | Morris; A/(A+D+U) ergibt nur 3 Signale |
| Vergleich | streng `< 0,40`, `> 0,615`, auf ungerundeten Werten | Morris; 2004-05-25 liegt bei 0,617 |
| Fensterregel | jeder Tag mit EMA < 0,40 setzt den Anker `arm` neu; Signal am ersten Tag `i` mit EMA > 0,615 und `i − arm ≤ 10` (Sitzungsindex) | Morris' Wortlaut („nach einem Unterschreiten von 0,40 … sonst beginnt der Vorgang neu") stützt den Neustart; die genaue Zählung `≤ 10` ab dem letzten Unterschreiten ist **unsere dokumentierte Umsetzung**. Der Listenabgleich ist eine Validierung, kein Beweis — „ab erstem Unterschreiten" verlöre 1971, 2004, 2011 und 2019. |
| Neuarmierung | nach einem Signal erst nach einem neuen Tag < 0,40 | verhindert Doppelzählung |
| Reihenstart | Startwert `EMA = Anteil` der ersten gültigen Sitzung; gewertet erst nach **50 Sitzungen Vorlauf** | Startfehler · (9/11)^50 < 5·10⁻⁵ |
| Universum | Exchange-Zählung der NYSE (wie veröffentlicht) | Breiteres Universum (~5 000 Stammaktien) verfehlt laut thetrading.tools 2023 und 2025 um 0,003 |

Synthetische, datierte Beispiele für die Fensterregel (Tag 10 ja, Tag 11 nein, erneutes Unterschreiten im Fenster
verlängert, zweites Überschreiten ohne neue Armierung zählt nicht) werden im Wächter festgeschrieben und dann
eingefroren. **Definitionskennung `zbt_v1`**; jede Änderung einer Zeile oben ist eine neue Kennung.

Die Signalzahlen der Literatur („18 seit dem Zweiten Weltkrieg", „19 von 19") reichen vor 1965 zurück und nennen
ihre Definition nicht. **Unsere Zahl gilt für `zbt_v1` und unseren Datenbereich und steht nie neben einer
fremden Zählung.**

## 2. Datenlage

### 2.1 Bestand

| Bedarf | Bestand | Bemerkung |
|---|---|---|
| Zielreihe | `^GSPC` in Supabase mit `log_return`, tief genug | Kursindex ohne Dividenden — so ausweisen |
| weitere Ziele (optional) | `SPY`, `RSP`, `IWM`, `QQQ`, `^NDX`, `^RUT`, `^DJI` (ab 1992) | Zusatzspalten mit eigener Fallzahl |
| NYSE-Kalender | `shared/sitzungen.py`, `shared/boersenereignisse.py` | **vor 1971 `ungeprueft`** (Abschnitt 2.4) |
| Advances/Declines NYSE | **nicht vorhanden** | — |

### 2.2 Quellen (geprüft 2026-10-27)

| Quelle | Bereich | Kosten | Bewertung |
|---|---|---|---|
| **unicorn.us.com/advdec** (`NYSE_advn/decln/unchn`, dazu Volumen, Neuhochs/-tiefs) | 1965-03-01 – 2020-02-10 | frei | Backfill-Quelle. Eingestellt, Zertifikat abgelaufen → einmal sichern + SHA-256. Defekte siehe 2.3. Lizenz ungenannt. |
| **McClellan Financial** Historienpaket | ab 1960 | 40 USD einmalig | tägliche NYSE-A/D; dokumentiert vorläufige vs. finale Zahlen. Spaltenaufbau vor dem Kauf bestätigen. |
| **Pinnacle Data** NYSE-Breitengruppe | A/D ab 1940 | 39 USD, Updates ab 20 USD/Monat | von Unicorn als Nachfolger genannt; Angebot beim Anbieter bestätigen |
| Barchart `$ADVN`/`$DECN` | ab 1980 | Download kostenpflichtig | Lückenfüller möglich |
| Norgate | — | Abo | bietet auch **selbst berechnete** Breite aus historischen Bestandteilen → nicht automatisch die Exchange-Zählung |
| Yahoo `C:ISSU` | nur aktueller Stand | frei | **keine Historie** (eine Zeile, Zeitstempel 0) |
| WSJ Markets Diary | täglich, ohne Historie | frei lesbar | nur Vorwärtssammlung; AGB ungeprüft |
| Massive Grouped Daily (eigene Zählung) | ab 2003-09-10 | Schlüssel vorhanden | eigenes Universum, nicht die NYSE-Zählung; Lizenzfrage offen (FEAR_GREED_NACHBAU.md 3.1) |

**Eine freie Quelle mit belegtem Recht zur öffentlichen Anzeige abgeleiteter Werte gibt es nicht** — Lesbarkeit
oder Kaufzugang ist kein Nachweis. Für jede Bezugsquelle die Anzeigerechte schriftlich klären.

### 2.3 Archivbefunde Unicorn (Probe)

- **38 Phantomzeilen** mit positiven Zählungen an Tagen ohne NYSE-Sitzung (u. a. Thanksgiving 2008, Trauertag
  2018-12-05, 2002-07-04) — nicht nur die 6 Nullzeilen.
- **3 fehlende offene Sitzungen:** 1999-11-26, 2002-06-20, 2019-08-20.
- Nullzeilen: 2016-12-26 und 2019-08-20 (je A+D=0), 2020-02-11..14 (Ende).
- **Strukturbruch-Diagnostik:** Median A+D+U je Jahr 1 381 (1965) → 3 354,5 (2000); Unveränderten-Anteil
  14,11 % (2000) → 6,41 % (2001) → 5,40 % (2002) — vereinbar mit der Dezimalisierung 2001 (GAO-05-535), Ursache
  nicht bewiesen. Gesamtzahl und Unveränderten-Anteil werden als Qualitätsmerkmal gespeichert; Ergebnisse vor/nach
  2001 beschreibend gegenübergestellt, **keine epochenweise Schwellenanpassung**.

### 2.4 Kalender vor 1971

Der NYSE-Kalender ist vor 1971 `ungeprueft` (`shared/exchange_holidays.py`, Warnhinweis
`shared/nyse_holidays.py`). Codex fand neun Tage, die er verwirft, obwohl Unicorn und Yahoo Werte haben (z. B.
1966-02-21), und umgekehrt zahlreiche Schließungen 1968 (Papierkrise), die er als offen führt. **Entscheidung:**
Stufe 1 wertet **ab 1971** aus; 1965–1970 dient nur als EMA-Vorlauf, dessen Achse aus dem Schnitt
„Unicorn-Zeile UND `^GSPC`-Kurszeile" gebildet und als Konvention benannt wird. Fehlende Daten und fehlende
Kalenderregeln sind getrennte Fehlerklassen. Kein Signal fällt dadurch weg (erstes Signal 1971-12-03).

### 2.5 Entscheidung: Lücke 2020-02-11 bis heute und Live

| Weg | Vorteil | Haken |
|---|---|---|
| **A — Bezugsquelle mit NYSE-Exchange-Zählung** (McClellan, Pinnacle) | dieselbe Größe wie die Literatur; Lücke + Live; günstig | Anzeigerechte; Lieferweg täglich |
| **B — eigene Zählung aus Massive** | eigene Reihe | anderes Universum; darf nicht „Zweig Breadth Thrust" heißen; Lizenz offen |
| **C — nur Archiv bis 2020-02** | sofort, kostenlos | ohne 2023/2025, kein aktueller Stand |

**Empfehlung:** C als Stufe 1 (Studie), A als Stufe 2, B höchstens als Gegenprobe.

**Quellenqualifikation (statt „Signale müssen gleich sein"):** Herkunft (Exchange-Zählung oder eigene Rechnung),
Universum, final oder vorläufig, Tagesabweichungen zu Unicorn auf der Überlappung (Verteilung von ΔA, ΔD und
ΔAnteil, Ausreißertage einzeln erklärt). Abweichende Signaltermine werden **einzeln erklärt**, nicht durch
Schwellen- oder Quellenwahl passend gemacht. 2023-11 und 2025-04 sind Prüfpunkte, keine Sollwerte — fehlt
eines, kann das an vorläufigen Zahlen, Korrekturen oder Konventionen liegen. Quellenwechsel mit
überlappendem Vorlauf (≥ 50 Sitzungen) und versionierter Übergangsregel.

## 3. Probe (nur lesend, 2026-10-27, bereinigte Achse)

Skript im Scratchpad (`zbt_probe.py` + `zbt_probe2.py`; Unicorn-CSV und `^GSPC` direkt von Yahoo **nur für die
Probe**). Achse = Unicorn-Zeilen ohne Nullzeilen und ohne Phantomzeilen (Abgleich mit `^GSPC`-Kurstagen).
Horizonte in Handelstagen der `^GSPC`-Achse, Rendite Schluss→Schluss.

**Signale `zbt_v1` und `^GSPC`-Kursrendite (%), Einstieg Schluss Signaltag t:**

| Signal | EMA | 10 HT | 30 HT | 60 HT | 90 HT | 120 HT |
|---|---|---|---|---|---|---|
| 1971-12-03 | 0,620 | +3,3 | +6,8 | +9,8 | +13,5 | +13,7 |
| 1974-10-10 | 0,625 | +0,6 | −2,3 | +1,8 | +16,7 | +16,8 |
| 1975-01-03 ¹ | 0,622 | +0,4 | +15,3 | +16,9 | +29,5 | +33,8 |
| 1982-08-20 | 0,636 | +8,5 | +7,5 | +21,2 | +25,0 | +28,3 |
| 1984-08-03 | 0,646 | +1,1 | +4,0 | +1,5 | +0,4 | +8,8 |
| 2004-05-25 | 0,617 | +1,6 | −0,0 | −1,3 | +2,0 | +6,4 |
| 2009-03-18 | 0,642 | +2,1 | +9,9 | +19,1 | +23,6 | +29,1 |
| 2011-10-14 | 0,621 | +4,9 | −2,6 | +5,5 | +11,5 | +12,9 |
| 2013-10-18 | 0,619 | +1,0 | +3,2 | +6,0 | +6,6 | +4,1 |
| 2015-10-08 | 0,644 | +1,9 | +3,4 | +0,2 | −4,7 | +2,9 |
| 2019-01-07 | 0,626 | +3,3 | +9,2 | +12,7 | +12,8 | +15,4 |

¹ 58 Sitzungen nach 1974-10-10 — Fenster überlappen ab 60 HT.

| Horizont | n | Mittel | Median | positiv | Minimum | Basisrate Mittel (positiv) | Einstieg t+1: Mittel / Median / positiv |
|---|---|---|---|---|---|---|---|
| 10 HT | 11 | +2,62 % | +1,94 % | 11/11 | +0,4 | +0,31 % (58 %) | +2,66 / +2,50 / 10/11 |
| 30 HT | 11 | +4,94 % | +4,02 % | 8/11 | −2,6 | +0,91 % (61 %) | +4,77 / +3,69 / 8/11 |
| 60 HT | 11 | +8,48 % | +5,95 % | 10/11 | −1,3 | +1,80 % (64 %) | +7,75 / +7,88 / 8/11 |
| 90 HT | 11 | +12,45 % | +12,81 % | 10/11 | −4,7 | +2,72 % (65 %) | +12,07 / +13,88 / 10/11 |
| 120 HT | 11 | +15,65 % | +13,65 % | 11/11 | +2,9 | +3,69 % (68 %) | +15,51 / +13,69 / 11/11 |

Basisrate: Starttage 1965-03 bis 2020-02-10 (Endpunkte bis 2020-07-31), noch nicht auf die Auswertung ab 1971
angeglichen — die Studie rechnet sie auf denselben Starttagen und mit denselben Gültigkeitsregeln wie die
Ereignisse.

**Sensitivität (bereinigt, Signalanzahl 1965–2020):**

| Variante | Signale | Bemerkung |
|---|---|---|
| `zbt_v1` (0,40 / 0,615, EMA, Fenster ab letztem Unterschreiten) | **11** | |
| obere Schwelle 0,61 | 13 | zusätzlich 1974-06, 2014-08 (2011/2015 um 1–2 Tage früher) |
| obere Schwelle 0,62 | 8 | ohne 1971, 2004, 2013 |
| untere Schwelle 0,39 | 7 | |
| untere Schwelle 0,41 | 14 | zusätzlich 1970-08, **2008-02-01**, 2011-08 |
| SMA statt EMA | 19 | u. a. 1973-09 (−8,7 % nach 60 HT), 1990-05 (−12,2 % nach 90 HT), 1981-10 |
| Fenster ab erstem Unterschreiten | 7 | ohne 1971, 2004, 2011, 2019 |
| Unveränderte im Nenner | 3 | |

Beschränkt auf den Auswertungsbeginn 1971 werden aus 14 → 13 (0,41) und 19 → 18 (SMA), weil je ein Signal von
1970 entfällt. Zwölf-Monats-Aussage: bei Einstieg t sind nach 252 Sitzungen alle elf Renditen positiv — als
eigener Horizont nur mit dokumentierter Konvention.

Lesart: die „100 % Trefferquote nach 12 Monaten" ist eine Eigenschaft genau dieser Definition auf genau dieser
Stichprobe; benachbarte Varianten holen Fälle wie 2008-02 herein. Das gehört auf die Seite. (Die erste Fassung
nannte hier 2008-11 als Beispiel — das war ein Phantomzeilen-Artefakt und ist gestrichen.)

**Eine fehlende Sitzung wirkt in der EMA lange nach** (Codex): nach zehn Folgetagen ist die mögliche Spannweite
noch `2/11 · (9/11)^10 = 0,0244`; für 2019-09-11 liegt die EMA je nach unbekanntem Anteil des 2019-08-20 zwischen
0,6142 und 0,6232 — über beide Seiten der Schwelle (kein Signal nur, weil die Armierung fehlte).

## 4. Spezifikation

### 4.1 Daten (Stufe 1)

- **Tabelle `marktbreite`** (SQL unter `scripts/sql/`, Ausführung durch den Nutzer): `datum date, boerse text,
  advances int, declines int, unchanged int, adv_volume bigint null, dec_volume bigint null, quelle text,
  quelle_stand text, final boolean null, geladen_am timestamptz`, Schlüssel `(boerse, datum, quelle)`. Quellen
  nebeneinander, nie überschreiben; die Auswahl je Datum ist eine **versionierte Regel im Leser**.
- **Backfill** `scripts/backfill_marktbreite_unicorn.py`: Nullzeilen verwerfen, Phantomzeilen gegen den Kalender
  (ab 1971) bzw. gegen `^GSPC`-Kurstage (1965–1970, benannte Konvention) verwerfen, fehlende Sitzungen als Lücke
  inventarisieren — alles im Bericht mit Datum. Trockenlauf zuerst, Schreiben nur mit Freigabe.
- **Eingabeartefakt:** die Unicorn-Dateien liegen als Momentaufnahme mit SHA-256-Manifest so, dass der Wächter
  sie **lokal und im Gate** findet. Lizenz ungeklärt → Entscheidung des Nutzers: Dateien ins Repo oder ein aus
  ihnen abgeleiteter, minimaler Prüfdatensatz (Datum, A, D) — fehlt das Artefakt, ist der Wächter **rot**, nie
  „übersprungen".

### 4.2 Lückenregel (ersetzt „10 Tage unbestimmt")

Eine fehlende Sitzung wird **nicht** zusammengerückt. Regel `zbt_v1`: nach einer Lücke wird die EMA **neu
initialisiert** (Startwert = Anteil der ersten Sitzung danach) und der Zustand für **50 Sitzungen gesperrt**
(`unbestimmt`, Grund `luecke`). Das ist eine dokumentierte Konvention; Alternative wäre die belegte Schließung der
Lücke aus einer zweiten Quelle (dann Quellenregel). Wirkung auf die drei bekannten Lücken: keine gesperrte Phase
enthält einen Signalkandidaten — **im Wächter nachzuweisen**, nicht angenommen.

### 4.3 Rechenkern `shared/breadth_thrust.py` (nur Python)

- `anteil`, `ema_reihe(achse, vorlauf=50, luecken)`, `signale(ema, …)` → Ereignisse mit `datum, ema,
  arm_datum, tage_seit_arm, definition`.
- **Zwei getrennte Zustände** (Codex R2):
  - *Erkennung* (bestimmt Signale): `gesperrt(grund, erste_freie_sitzung) | unarmiert | armiert(arm_datum)`.
    Während der Sperre (Vorlauf am Reihenanfang oder nach Lücke) wird **weder armiert noch ausgelöst**; die erste
    freie Sitzung ist Sitzung 51 nach dem Neustart und kann selbst armieren. Ein Signal setzt die Erkennung auf
    `unarmiert`; fällt die EMA danach (auch am Folgetag) unter 0,40, ist sie sofort wieder `armiert`.
  - *Anzeige* (Seite/Mail): `unbestimmt(grund)` > `ausgeloest(datum)` > `armiert(rest_tage, ema, abstand_bis_hi)`
    > `unarmiert`. `ausgeloest` wird am Signaltag und den 5 folgenden Sitzungen angezeigt (6 Sitzungen); eine
    in dieser Zeit entstandene neue Armierung bleibt in der Erkennung erhalten und wird nach Ablauf angezeigt.
  - Datierte Grenzfälle (Sperrende, Armierung am Folgetag des Signals, Signal am letzten Anzeigetag eines
    früheren Signals) im Wächter.
- Vertragskonstanten `LO, HI, FENSTER, ALPHA, VORLAUF, DEFINITION = "zbt_v1"`.
- **Kein JS-Zwilling** — Seite und Mail lesen dasselbe vorberechnete JSON.

### 4.4 Studie `scripts/build_breadth_thrust.py` → `landing/data/breadth_thrust_study.json` (in `.gitignore`)

- `^GSPC` aus Supabase (`shared.data.lade_kurse`, **`log_return`**), auf die geprüfte NYSE-Sitzungsachse gelegt;
  fehlende Kurszeilen rücken **nicht** zusammen (Fenster dann `unbrauchbar`).
- **Rendite:** `R(t, h) = expm1(Σ lr[t+1 … t+h])`, h ∈ {10, 30, 60, 90, 120} **Handelstage**.
  Einstieg t (Schluss des Signaltags, Konvention der Literatur, erst nach Schluss bekannt) und **t+1 mit demselben
  Haltehorizont** (`R(t+1, h)`). Da historische Veröffentlichungszeiten der Breitenzahlen fehlen, ist die Studie
  als **Auswertung finaler Daten** gekennzeichnet.
- **Rückgänge** (je Einstieg): `tiefster Schluss gegenüber Einstieg` = min über k∈[0,h] von `R(t,k)` (Einstieg
  eingeschlossen) und `maximaler Drawdown aus Tagesschlüssen` im Horizont. Kein Intraday.
- **Gültigkeit je Fenster** (Codex R2): benötigt werden `log_return` für t+1 … t+h (Rendite) und für die
  Rückgänge zusätzlich jede Zwischensumme. Eine Sitzung gilt nur, wenn die Kurszeile existiert **und**
  `log_return` endlich ist (`shared/data.py` liefert auch Zeilen mit `log_return = None`). Hauptklasse mit
  fester Priorität: `unbrauchbar` (interne Lücke oder ungültiger Wert innerhalb des bereits verfügbaren Teils)
  vor `unreif` (Horizont reicht über den Datenstand) vor `vollstaendig`; alle zutreffenden Gründe zusätzlich
  als Liste. Ereignisse und Basisrate verwenden **dieselbe** Regel.
- **Aggregat:** n, Mittel, Median, positiv, Min, Max je Horizont und Einstieg; **Basisrate** auf denselben
  Starttagen (Auswertungszeitraum, gleiche Gültigkeitsregeln) und Differenz; **Auslassen je eines Ereignisses**
  (Spannweite von Mittel und Median); Vergleich vor/nach 2001; Pfad −20 … +120 HT normiert auf 100.
- **Kein Zufallsvergleich in Stufe 1** (Codex: das Nullmodell wäre mit Mindestabstand allein nicht definiert).
  Kommt er später, dann mit festgelegter Kandidatenmenge, Ziehen ohne Zurücklegen, Abstandsregel, Startwert,
  Gleichstandsregel, als „Rang unter Nullmodell X", explorativ.
- Ausgabe atomar (`shared.atomic_json`, Rechte für nginx lesbar), Exit ≠ 0 bei jedem Fehler.

### 4.5 Oberfläche

- **Seite `/breadth-thrust`** (DE+EN, `_EN_PAGE_META`, `data-i18n`, statischer Text + FAQ), Nav „Events"
  neben „Intermarket-Matrix", Aufbau nach `/index-effekt`:
  1. Statuszeile — Stufe 1: „Datenstand bis 10.02.2020"; Stufe 2: EMA mit Sitzungsdatum, Zustand, Quelle,
     veraltet-Kennzeichen.
  2. EMA-Verlauf mit 0,40/0,615 und markierten Signalen.
  3. Signaltabelle (fünf Horizonte, t und t+1 umschaltbar, Rückgänge), Basisrate als letzte Zeile, n überall.
  4. Durchschnittspfad mit Basisrate.
  5. „Grenzen": Stichprobe, Sensitivitätstabelle, Kursindex ohne Dividenden, finale Daten, kein Signal.
- **Daily Briefing** (Stufe 2): Zeile nur bei `armiert`/`ausgeloest`, Text mit Fallzahl, liest dasselbe JSON.
- **Health-Check** (Stufe 2): ausgewählte Quelle, letzte gültige Sitzung gegen letzte abgeschlossene
  NYSE-Sitzung, final/vorläufig, Berechnungs- und JSON-Stand **gemeinsam**.

### 4.6 Wächter `scripts/verify_breadth_thrust.py` (ins Gate)

1. Eingabeartefakt vorhanden + Prüfsumme (fehlt → rot).
2. Kurze analytische EMA-Fälle inkl. früher Werte (fängt `adjust=True`, das auf dem Archiv dieselben Signale
   liefert).
3. Datierte Zustandspfade für die Fensterregel (Tag 10/11, Neustart im Fenster, Neuarmierung, Gleichheit an den
   Schwellen, Lücke mit Neuinitialisierung und Sperre).
4. Archiv: Bereinigungsbericht (38 Phantome, 3 Lücken, Nullzeilen) und Signalliste `zbt_v1` als eingefrorene
   Momentaufnahme; Morris-Termine als **Validierung** mitgeprüft.
5. Studie gegen numpy-Nachrechnung aus `log_return`, Basisrate auf denselben Starttagen.
6. Produktionsweg: Rohdaten → Quellenwahl → Kern → JSON → Seitenrender (jsdom) / Mailzeile.
7. Mutationstest am Produktionspfad (Schwelle, Fenster, Nenner, `adjust`, Lückenregel, Einstieg, Horizont in
   Kalendertagen) — jede Mutation reißt eine benannte Prüfung.

### 4.7 Stufe 2

Quelle A beschaffen → Qualifikation nach 2.5 auf 1971–2020 → Lücke 2020-02-11 bis heute → Nightly-Phase für die
Tageszeile (nach Bekanntgabe der finalen Zahlen; vorläufige Zahlen gekennzeichnet) → Live-Status, Mail,
Health-Check.

## 5. Offene Entscheidungen (Nutzer)

1. Horizonte in **Handelstagen** (Vorschlag, 120 HT ≈ 6 Monate) oder Kalendertagen?
2. Quelle für 2020-02 bis heute und Live: McClellan/Pinnacle (Vorschlag) oder vorerst nur Archiv?
3. Unicorn-Dateien ins öffentliche Repo oder nur ein minimaler Prüfdatensatz + Prüfsumme?
4. Eigene Seite `/breadth-thrust` oder Abschnitt einer künftigen Marktbreite-Seite (A/D-Linie, McClellan aus
   derselben Tabelle — FEAR_GREED_NACHBAU.md Stufe 2)?

## Quellen

- [McClellan: Zweig Breadth Thrust Signal](https://www.mcoscillator.com/learning_center/weekly_chart/zweig_breadth_thrust_signal/) · [Breitendaten](https://www.mcoscillator.com/market_breadth_data/) · [Historienpaket](https://www.mcoscillator.com/subscriptions/signup/historical-data/)
- [Greg Morris: Advance-Decline Ratio Indicators (Kap. 5, CGMBI)](https://articles.stockcharts.com/article/articles-dancing-2015-01-advance-decline-ratio-indicators-chapter-5--cgmbi/)
- [Arthur Hill: The Zweig Breadth Thrust triggers (11/2023)](https://articles.stockcharts.com/article/articles-arthurhill-2023-11-the-zweig-breadth-thrust-trigg-609/) · [ZBT dominates the headlines (04/2025)](https://stockcharts.com/articles/arthurhill/2025/04/zweig-breadth-thrust-dominates-460.html)
- [Carson Group: Houston, we have a Zweig Breadth Thrust (25.04.2025)](https://www.carsongroup.com/insights/blog/houston-we-have-a-zweig-breadth-thrust-and-four-more-bullish-developments/)
- [SentimenTrader: About that near-miss Zweig Breadth Thrust](https://sentimentrader.com/blog/about-that-near-miss-zweig-breadth-thrust)
- [thetrading.tools: Zweig Breadth Thrust](https://www.thetrading.tools/manuals/zweig-breadth-thrust)
- [unicorn.us.com/advdec](http://unicorn.us.com/advdec/) · [Pinnacle Data](https://pinnacledata2.com/idx.html) · [Norgate FAQ](https://norgatedata.com/data-package-faq.php) · [Barchart $ADRN](https://www.barchart.com/stocks/quotes/$ADRN/price-history/historical)
- [GAO-05-535 (Dezimalisierung)](https://www.gao.gov/products/gao-05-535)
