# CNN Fear & Greed Index — Nachbau fuer seasonalpha.ai?

> Recherche 2026-10-23. Internes Dokument (Dateipfade sind hier Belege, nicht Lesertext).
> Kein Produktivcode, keine Pipeline — Bestandsaufnahme, Machbarkeit, Bauvorschlag.
>
> **Kurzantwort:** Von den sieben Bestandteilen sind drei aus dem Bestand direkt rechenbar,
> zwei nur als Naeherung mit benannten Schwaechen, zwei gar nicht ohne neue Datenquelle.
> Die drei rechenbaren messen weitgehend dasselbe wie die bestehende Stress-Ampel. Die drei
> Bestandteile, die wirklich neue Information tragen (Marktbreite, Kreditrisiko,
> Optionsnachfrage), sind genau die, fuer die uns Daten oder Historie fehlen.
> **Empfehlung: nicht als „Fear-&-Greed-Nachbau" bauen.** Stattdessen zwei kleinere Vorhaben
> mit eigenem Nutzen (Marktbreite als eigene Datenreihe, Kreditrisiko-Reihe) und erst danach
> — falls ueberhaupt — eine eigene Kennzahl mit eigenem Namen und veroeffentlichter Formel.

---

## 0. Methodik dieser Recherche und ihre Grenzen

CNNs Seite liess sich nicht direkt abrufen: `edition.cnn.com/markets/fear-and-greed` und
`www.cnn.com/markets/fear-and-greed` antworten mit **HTTP 451**, der JSON-Endpunkt
`production.dataviz.cnn.io/index/fearandgreed/graphdata` mit **HTTP 418**, das Internet Archive
war aus dieser Umgebung nicht erreichbar. Ueber einen Reader-Proxy kam die Seite durch, lieferte
aber nur die **erzaehlenden Einleitungssaetze** der sieben Kacheln, keine Formeln.

Deshalb gilt fuer den ganzen Bericht eine **Herkunftskennzeichnung je Aussage**:

| Kennung | Bedeutung |
|---|---|
| **[CNN]** | In den Suchergebnissen als Zitat von CNNs eigener Seite ausgewiesen |
| **[Dritt]** | Nur aus Sekundaerquellen (Blogs, Erklaerseiten, nachgebaute Skripte) |
| **[Repo]** | Am eigenen Code oder an dokumentierten eigenen Messungen belegt |
| **[Vermutung]** | Meine Einschaetzung, nicht belegt |

Eine Einschraenkung vorweg, die den ganzen Bericht traegt: **die zentralen Zahlen, die im Netz
als „CNN-Methodik" zirkulieren — 125-Tage-Durchschnitt, 50-Tage-VIX-Durchschnitt,
Gleichgewichtung der sieben Teile, z-Standardisierung gegen die eigene Historie — habe ich in
KEINEM Fall als Zitat von CNN selbst belegen koennen.** Sie stehen durchgaengig in
Sekundaerquellen. Was CNN selbst schreibt, ist deutlich duenner.

---

## 1. Die sieben Bestandteile einzeln

### Uebersicht

| # | Bestandteil | Was CNN selbst sagt | Was Dritte ergaenzen | Nicht veroeffentlicht |
|---|---|---|---|---|
| 1 | Market Momentum | Kursniveau gegen die letzten Monate **[CNN]** | S&P 500 gegen 125-Tage-Durchschnitt **[Dritt]** | Fensterlaenge von CNN selbst; Normierung |
| 2 | Stock Price Strength | Anzahl NYSE-Titel auf 52-Wochen-Hoch gegen 52-Wochen-Tief **[CNN]** | Netto-Neuhochs als Anteil, 5-Tage-Durchschnitt **[Dritt]** | Universumsabgrenzung, Glaettung, Normierung |
| 3 | Stock Price Breadth | McClellan-Summationsindex, fallendes Volumen = Furcht; **„kuerzlich geringfuegig geaendert"** **[CNN]** | McClellan **Volume** Summation Index, NYSE Up-/Down-Volumen **[Dritt]** | Die Aenderung selbst; Oszillator-Parameter; Normierung |
| 4 | Put and Call Options | Verhaeltnis Put- zu Call-Volumen **[CNN]** | CBOE-Gesamtratio, 5-Tage-Durchschnitt **[Dritt]** | Welche CBOE-Reihe (Equity, Index, Total), Glaettung, Normierung |
| 5 | Market Volatility | VIX **[CNN]** | VIX gegen 50-Tage-Durchschnitt **[Dritt]** | Fensterlaenge, Normierung |
| 6 | Safe Haven Demand | Differenz aus Anleihe- und Aktienrendite **ueber 20 Handelstage**; steigende Nachfrage = Furcht **[CNN]** | Staatsanleihen gegen Aktien **[Dritt]** | Welches Anleiheinstrument, einfache oder log. Rendite, Normierung |
| 7 | Junk Bond Demand | Hochzinsanleihen tragen hoeheres Ausfallrisiko **[CNN]** | Renditeaufschlag High Yield gegen Investment Grade bzw. Staatsanleihen **[Dritt]** | Welche Indizes, Laufzeit, Fenster, Normierung |

### Die gemeinsame, unveroeffentlichte Mechanik

Zwei Schritte stehen zwischen den Rohdaten und der Zahl 0–100, und **beide sind nicht
veroeffentlicht**:

1. **Die Normierung je Teil.** Sekundaerquellen beschreiben sie einheitlich als „wie weit der
   aktuelle Wert von seinem eigenen Durchschnitt abweicht, relativ zur ueblichen Schwankung"
   **[Dritt]** — also eine z-aehnliche Standardisierung, auf 0–100 abgebildet. Was „eigener
   Durchschnitt" heisst (Fensterlaenge), was „uebliche Schwankung" heisst (Standardabweichung?
   Interquartilsabstand?) und wie abgeschnitten wird, sagt niemand. Unsere eigene
   Stress-Ampel loest dieselbe Aufgabe anders, naemlich als **Rang gegen bis zu 2520
   vorangegangene Sitzungen** `[Repo: shared/stress_score.py:15`, `REFERENZ_MAX = 2520]` — das
   ist nachvollziehbar, aber es ist nicht CNNs Verfahren.
2. **Die Gewichtung.** Dass die sieben Teilscores **gleich** gewichtet und gemittelt werden,
   sagen mehrere Sekundaerquellen **[Dritt]**. Ich habe keine CNN-Aussage dazu gefunden.

Dazu CNNs eigener Hinweis, dass an der Breiten-Komponente „kuerzlich eine geringfuegige
Rechenaenderung" vorgenommen wurde, ohne Angabe welche **[CNN]**. Das heisst: selbst eine heute
perfekt kalibrierte Nachbildung driftet, ohne dass wir die Ursache sehen.

### Daten je Bestandteil

| # | Bestandteil | Benoetigte Daten |
|---|---|---|
| 1 | Momentum | S&P-500-Tagesschluss, >= 125 Sitzungen Vorlauf + Normierungshistorie |
| 2 | Strength | Tagesanzahl NYSE-Titel auf 52-Wochen-Hoch und -Tief (oder Titel-Einzelkurse ueber das NYSE-Universum, 52 Wochen rollierend) |
| 3 | Breadth | Tagesvolumen getrennt nach steigenden und fallenden Titeln ueber das NYSE-Universum |
| 4 | Put/Call | Taegliches Put- und Call-Volumen eines marktweiten Aggregats |
| 5 | Volatility | VIX-Tagesschluss, >= 50 Sitzungen Vorlauf + Normierungshistorie |
| 6 | Safe Haven | Aktien-**Gesamtrendite** und Staatsanleihen-**Gesamtrendite** ueber 20 Handelstage |
| 7 | Junk Bond | Renditeaufschlag High Yield gegen eine Referenzkurve (OAS oder Renditedifferenz) |

---

## 2. Abgleich mit unserem Bestand

### Was wir tatsaechlich haben — drei Korrekturen am Auftragstext

Vor dem Abgleich drei Punkte, die ich anders gemessen habe als in der Aufgabenstellung
beschrieben:

1. **`^SKEW`, `^VVIX` und `^COR1M/3M/30D` stehen NICHT in `shared/symbols.py`** und damit nicht
   in der Tabelle `prices` (Suche nach `VVIX|\^SKEW|\^COR` in `shared/symbols.py`: 0 Treffer).
   Sie werden in `scripts/compute_options_skew.py` **live bei Yahoo** geholt
   (`_index_series`, Zeile 239 ff.), und der Kommentar dort sagt ausdruecklich, diese Indizes
   stuenden „nicht vollstaendig in Supabase"; `^COR*` liefert Yahoo „ohnehin nur den letzten
   Wert", weshalb die Reihe unter `__CORR` **vorwaerts akkumuliert** wird (Zeile 1311 ff.).
   Die VIX-Familie dagegen ist onboardet: `^VIX`, `^VIX9D`, `^VIX3M`, `^VIX1D`, dazu `^VXN`
   und `^OVX` `[Repo: shared/symbols.py:171–206]`.
2. **LQD gibt es bei uns nicht.** Der Anleihenbestand in `shared/symbols.py` ist `SHY`, `IEF`,
   `HYG` (Zeilen 943–945) und `TLT` (Zeile 290). Kein LQD, also **kein
   Investment-Grade-Unternehmensanleihen-Instrument** — und damit fehlt genau das Bein, das
   CNNs Junk-Bond-Komponente in der verbreiteten Beschreibung braucht. Zusaetzlich vorhanden:
   die Renditeindizes `^IRX`, `^FVX`, `^TNX`, `^TYX` `[Repo: shared/symbols.py:224–248]`.
3. **Das Feld `pc_ratio` je Ticker in `options_skew.json` ist KEINE Put/Call-Ratio aus
   Volumen.** Es ist das Verhaeltnis der 25-Delta-IVs (`put_iv / call_iv`,
   `scripts/compute_options_skew.py:763` und `:863`, bei rankbaren Tickern aus den
   30-Tage-IVs, `:1297`). Dieselbe Verwechslung ist in `CLAUDE.md` v64 schon einmal als Befund
   notiert. Die volumenbasierte Groesse ist **marktweit** `pc_ratio.equity` / `pc_ratio.index`
   mit je `vol` und `oi` (`:1203–1210`), je Ticker gibt es `put_vol`/`call_vol`/`put_oi`/
   `call_oi` (`:675`).

Weiter belegt: das Options-Universum umfasst **rund 160 grosse US-Werte in neun Kategorien**
`[Repo: shared/options_universe.py:17–56]`; die Symboldatenbank hat **rund 354 Eintraege**
(Zaehlung der Eintraege auf oberster Ebene in `shared/symbols.py`), davon **201 in den
Kategorien US-Aktie / US-ETF / Mag7 / Tech**. Die marktweite Equity-P/C-Ratio wird **vorwaerts
akkumuliert** (`__PCR`, `:1319–1324`), mit dem ausdruecklichen Kommentar „keine freie Historie
verfuegbar"; sie existiert seit der Einfuehrung der Equity-P/C-Ratio (v52, 2026-09-08
`[Repo: CLAUDE.md]`), also **etwa sechs Wochen** — als Normierungsbasis unbrauchbar.

### Verdikt je Bestandteil

| # | Bestandteil | Verdikt | Begruendung in einem Satz |
|---|---|---|---|
| 1 | Market Momentum | **direkt baubar** | `^GSPC` liegt in `prices` mit 9264 Schluessen ab 1990 `[Repo: CLAUDE.md v66.25, eigene Messung]`; ein 125-Sitzungs-Durchschnitt und der Abstand dazu sind reine Kursrechnung. |
| 2 | Stock Price Strength | **nur Naeherung, und eine schwache** | Unser US-Bestand sind 201 heute existierende, grosskapitalisierte Titel ohne NYSE-Abgrenzung — nicht das NYSE-Universum. |
| 3 | Stock Price Breadth | **nicht baubar** | Up-/Down-Volumen ueber ein breites Universum existiert bei uns in keiner Form. |
| 4 | Put and Call Options | **nur Naeherung, Historie fehlt** | Marktweite Equity-P/C existiert, aber aus ~160 Large Caps und erst seit sechs Wochen. |
| 5 | Market Volatility | **direkt baubar** | `^VIX` ab 1990 in `prices` `[Repo: CLAUDE.md v66.25]`, 50-Sitzungs-Durchschnitt trivial. |
| 6 | Safe Haven Demand | **direkt baubar ab 2002, davor nicht** | SPY und IEF/TLT liegen als Kursreihen vor; die Treasury-ETFs starten 2002, und die Renditeindizes sind kein Ersatz. |
| 7 | Junk Bond Demand | **nur Naeherung, und sie misst etwas anderes** | HYG liegt als Kursreihe vor, ein Spread nicht; es fehlt zudem das Investment-Grade-Bein. |

### Die Naeherungen im Einzelnen — wie gut, und woran messbar

**Nr. 2, Stock Price Strength.** Naeherung: Anteil unserer US-Titel, die am Tag ein
52-Wochen-Hoch bzw. -Tief erreichen, als Netto-Groesse. Drei systematische Abweichungen,
alle in dieselbe Richtung:

- **Survivorship.** `symbols.py` enthaelt die heute existierenden Titel. Die Insolvenzen und
  Delistings der Vergangenheit fehlen — also fehlen genau die Titel, die in Krisen die
  52-Wochen-Tiefs liefern. Die Naeherung untertreibt Furcht **systematisch**, und zwar am
  stärksten dann, wenn der Indikator etwas sagen soll.
- **Grosskapitalisierungs-Schlagseite.** Die NYSE-Zaehlung umfasst mehrere Tausend Titel
  inklusive Nebenwerte; unsere 201 sind fast ausschliesslich Standardwerte. Breite ist aber
  gerade die Frage, ob die Nebenwerte mitlaufen.
- **Falsches Universum.** Viele unserer US-Titel sind Nasdaq-gelistet, einige sind ETFs. CNNs
  Zaehlung ist NYSE.

Messbar waere die Qualitaet nur gegen eine echte NYSE-Reihe (Korrelation der Niveaus und der
Tagesaenderungen, dazu der Vergleich in den 5 % der Tage mit den schwaechsten Kursen — dort
entscheidet sich, ob die Naeherung in der Krise noch traegt). Eine solche Reihe haben wir nicht;
um die Naeherung zu pruefen, braeuchte man also genau die Quelle, die die Naeherung ersetzen
soll. **[Vermutung]** Das ist der Punkt, an dem ich die Naeherung fuer nicht verantwortbar
halte: eine Zahl, deren Fehler man nicht messen kann und deren Fehlerrichtung man kennt.

**Nr. 4, Put and Call Options.** Naeherung: `pc_ratio.equity.vol`. Zwei getrennte Probleme.
Das Universum (~160 Large Caps statt des gesamten US-Optionsmarkts) ist eine
Niveauverschiebung, die moeglicherweise stabil ist — dann waere sie durch die Normierung gegen
die eigene Historie weitgehend neutralisiert **[Vermutung]**. Das harte Problem ist die
**Historie**: CNN normiert gegen Jahre, wir haben sechs Wochen. Die Stress-Ampel verlangt aus
genau diesem Grund mindestens 756 Referenzwerte, bevor sie ueberhaupt einen Score ausgibt
`[Repo: shared/stress_score.py:36]`. Nach derselben Regel waere dieser Bestandteil **vor etwa
2029** nicht bewertbar. Eine gekaufte Historie der CBOE-Ratio wuerde das loesen; die freie
CBOE-Reihe ist weggefallen `[Repo: CLAUDE.md v52]`.

**Nr. 7, Junk Bond Demand.** Naeherung: Verhaeltnis oder Renditedifferenz HYG gegen IEF.
Drei Abweichungen:

- **Es ist kein Spread.** Ein ETF-Kursverhaeltnis misst Risikoappetit, nicht den
  Renditeaufschlag. Die beiden laufen zusammen, sind aber nicht dasselbe — HYG traegt
  Fondsstruktur, Duration und Liquiditaetspraemie. Der Kommentar in `shared/symbols.py:220–223`
  formuliert denselben Vorbehalt bereits fuer TLT gegen die Renditeindizes: „TLT ist allerdings
  nicht ihr Spiegelbild, sondern ein ETF mit Duration, Kupons und eigener Fondsstruktur".
- **Ausschuettungen fehlen.** Unsere Kursreihen sind Kursreihen; HYG schuettet deutlich mehr aus
  als IEF. Ein Verhaeltnis aus beiden driftet deshalb ueber Jahre nach unten, ohne dass sich das
  Kreditrisiko aendert. Eine Gesamtrenditereihe braeuchte `dividend_events` — die Tabelle
  enthaelt derzeit nur Vergangenheit und ist als offener Posten notiert `[Repo: CLAUDE.md]`.
- **Das Investment-Grade-Bein fehlt** (kein LQD), also ist die verbreitete CNN-Beschreibung
  „High Yield gegen Investment Grade" ohne neue Reihe gar nicht nachbildbar.

Messbar waere die Qualitaet gegen den ICE-BofA-HY-OAS (FRED-Kennung `BAMLH0A0HYM2`) — aber
dessen Lizenz verbietet die Veroeffentlichung (siehe Abschnitt 3). Eine **einmalige, nicht
veroeffentlichte** Messung (Rangkorrelation ueber 2008–2026, dazu getrennt die Stressphasen)
waere der saubere Weg, bevor irgendetwas gebaut wird.

**Nr. 6, Safe Haven Demand** ist direkt baubar, hat aber eine benannte Grenze: der
Aktien-minus-Anleihen-Vergleich braucht **Gesamtrenditen**. Ueber 20 Handelstage ist der
Ausschuettungseffekt klein (grob 0,3 Prozentpunkte bei IEF, groessenordnungsmaessig), aber er
ist einseitig. Fuer die Zeit vor 2002 gibt es kein Anleiheinstrument; die Renditeindizes
`^TNX` etc. sind Renditen, keine Anleiherenditen — eine Renditeaenderung ist keine
Wertentwicklung, und `shared/symbols.py:218–220` haelt ausdruecklich fest, dass diese Reihen
„vorzugsweise in Basispunkten" als **Aenderung** zu lesen sind. Eine Umrechnung ueber eine
Duration-Approximation waere moeglich, waere aber eine zusaetzliche Modellannahme.

---

## 3. Datenquellen fuer die Luecken

### 3.1 Marktbreite — der einzige Weg, bei dem wir die Reihe besitzen

**Massive (vormals Polygon.io), Tagesuebersicht aller US-Aktien.**
Endpunkt `GET /v2/aggs/grouped/locale/us/market/stocks/{date}` liefert **alle US-Aktien eines
Handelstags in einem einzigen Aufruf**, je Titel `T, o, h, l, c, v, vw, n, t`, optional
`include_otc`. Historie zurueck bis **2003-09-10**. Enthalten in **allen** Stocks-Plaenen;
Historientiefe nach Plan: Basic 2 Jahre, Starter 5, Developer 10, Advanced/Business alles.
Basic ist Tagesschluss, Starter/Developer 15 Minuten verzoegert
([Massive-Doku](https://massive.com/docs/rest/stocks/aggregates/daily-market-summary)).

Das ist technisch genau das richtige Werkzeug: **ein Aufruf pro Tag**, und daraus lassen sich
**alle** fehlenden Breiten-Groessen selbst rechnen — Advance/Decline, Up-/Down-Volumen, daraus
McClellan-Oszillator und -Summation, und mit 52 Wochen Vorlauf auch die Hoch-/Tief-Zaehlung.
Ein Rueckbau von zwei Jahren sind rund 500 Aufrufe; bei der am Projekt gemessenen Drosselung
(„Aktien-Aggregate eng rate-limitiert, 429 ab ~6 Abrufen/min" `[Repo: CLAUDE.md v66.22]`, was
zu Polygons freier Stufe mit 5 Aufrufen/Minute passt **[Vermutung]**) waeren das etwa
100 Minuten. Wir haben den Schluessel schon (`MASSIVE_API_KEY`, genutzt in
`scripts/snapshot_gex_massive.py`).

Zwei Vorbehalte, bevor das als „geloest" gilt:

- **Universumsabgrenzung.** Die Tagesuebersicht enthaelt ETFs, Vorzuege, Zertifikate. Fuer eine
  NYSE-aehnliche Zaehlung braucht es einen Filter ueber den Referenz-Endpunkt (Titelart
  Stammaktie, Primaerboerse) — ein eigener Datenbestand mit eigener Pflege. Ohne diesen Filter
  zaehlen ETFs mit, und bei Hoch-/Tief-Zaehlungen verzerrt das stark **[Vermutung]**.
- **Adjustierung.** 52-Wochen-Extrema haengen davon ab, ob die Reihe split- und
  dividendenadjustiert ist. Der Parameter `adjusted` schaltet nur Splits; bei `adjusted=true`
  wandert die Historie bei jedem Split. Dieselbe Fehlerklasse ist am Projekt bereits belegt
  (Yahoo rechnet die Historie bei jeder Dividende nach unten `[Repo: CLAUDE.md v62]`).

**Lizenz — das eigentliche Hindernis.** Massives eigene Wissensdatenbank sagt: wenn ausser
einem selbst noch jemand die Daten sieht, ist es Weiterverbreitung; „Charts oder Tabellen, die
aus den Daten gebaut sind, zu veroeffentlichen" faellt darunter, und dafuer braucht es eine
kommerzielle Lizenz (Business-Plan oder Vertrag ueber den Vertrieb). Abgeleitete Werte werden
ausdruecklich **nicht** pauschal freigestellt: „ein aus den Daten berechnetes Signal kann
Weiterverbreitung sein oder nicht, je nachdem wie viel es vom zugrundeliegenden Kurs
offenlegt" — Einzelfallgespraech
([Massive KB](https://massive.com/knowledge-base/article/how-can-i-redistribute-massives-market-data)).
Die Market Data Terms in der Fassung vom 2024-10-09 begrenzen die Nutzung auf persoenliche,
nicht-geschaeftliche Zwecke und verbieten oeffentliche Darstellung ohne schriftliche Zustimmung
([PDF](https://massive.com/terms/market_data_terms.pdf),
[Terms-Seite](https://massive.com/legal/market-data-terms-of-service)).

⚠️ **Das ist kein Problem der Marktbreite allein.** `/skew`, `/key-levels`,
`/dealer-positioning` und `/options-flow` zeigen heute oeffentlich Groessen, die aus
Massive-Optionsdaten gerechnet sind. Ob unser Abonnement das deckt, kann ich von hier nicht
feststellen — **ich weiss nicht, welchen Plan wir haben** und welche Zusagen beim Abschluss
galten. Das ist eine offene Frage mit Prioritaet, unabhaengig von diesem Vorhaben, und sie
sollte schriftlich geklaert werden, bevor eine weitere oeffentliche Darstellung auf derselben
Quelle aufsetzt.

**Fertige Breiten-Reihen als Alternative** — alle mit Haken:

| Quelle | Abdeckung / Historie | Kosten | Lizenz fuer kommerzielle Anzeige |
|---|---|---|---|
| [Barchart](https://www.barchart.com/stocks/quotes/$ADRN/price-history/historical) (`$ADRN`, `$AVRN`, `$NSHR`) | NYSE-Breite, frei bis 2 Jahre zurueck | Download/API kostenpflichtig (OnDemand) | ungeklaert, Anzeige vermutlich lizenzpflichtig **[Vermutung]** |
| [StockCharts](https://stockcharts.com/freecharts/historical/marketbreadth.html) | A/D-Linie und Neuhochs/Neutiefs ab 1965 als **Charts** | Charts frei | kein belegter Datendownload; Anzeige fremder Charts keine Option |
| [McClellan (mcoscillator.com)](https://www.mcoscillator.com/market_breadth_data/) | Tageswerte sichtbar, Historie fuer A/D, Volumen, Neuhochs/Neutiefs | Historie kostenpflichtig | kommerzielle Anzeige nicht geklaert |
| [unicorn.us.com/advdec](http://unicorn.us.com/advdec/) | freie CSV mit A/D-Volumen | frei | Stand der gefundenen Momentaufnahme 2020, offenbar eingestellt — nicht tragfaehig |
| Yahoo `C:ISSU` / `C:ISSQ` | A/D/unveraendert NYSE bzw. Nasdaq | frei | in den Suchergebnissen **ohne Datenzeilen** — unbestaetigt, ob die Seiten liefern |

**Fazit Marktbreite:** Es gibt keine freie, lizenzgeklaerte Fertigreihe. Der einzige Weg, bei
dem wir eine eigene, selbst gerechnete und damit auch selbst erklaerbare Reihe besitzen, ist
die Tagesuebersicht aus Massive — und der haengt an der Lizenzfrage.

### 3.2 Junk-Bond-Spread — FRED ist konkret geprueft, und die Antwort ist nein

Das technische Muster steht bereits im Projekt: `shared/cpi_data.py:81–106` ruft
`https://api.stlouisfed.org/fred/series/observations` mit `series_id`, `api_key` aus
`FRED_API_KEY`, `file_type=json`. Eine Tagesreihe anzubinden waere ein Abend Arbeit.

Die Lizenz steht dem entgegen:

- **`BAMLH0A0HYM2`** (ICE BofA US High Yield Index Option-Adjusted Spread), taeglich, Prozent,
  Wert 3,27 am 2026-10-21. Die Seite sagt: „Data in this graph are copyrighted", und die
  Serienhinweise: „Reproduction of this data in any form is prohibited except with the prior
  written permission of ICE Data Indices"; die Tagesschlusswerte sind „provided for your
  internal use only and you are not authorized or permitted to publish, distribute" sie an
  Dritte ohne vorherige schriftliche Zustimmung
  ([FRED](https://fred.stlouisfed.org/series/BAMLH0A0HYM2)).
  Zwei weitere Punkte: ICE kann als **Drittbegünstigter** der FRED-Nutzungsbedingungen direkt
  gegen den Nutzer vorgehen, und der Zugang endet, wenn der Vertrag zwischen FRED und ICE
  endet. Dazu ein praktischer Befund: **„Starting in April 2026, this series will only include
  3 years of observations"** — die lange Historie, die ein Normierungsfenster ueberhaupt erst
  moeglich macht, verschwindet also.
- **`BAA10Y`** (Moody's Baa gegen 10-jaehrige Treasury) ist bei FRED als „Copyrighted:
  Citation Required" gekennzeichnet; der Moody's-Hinweis untersagt Vervielfaeltigung und
  Weiterverbreitung ohne schriftliche Zustimmung
  ([FRED](https://fred.stlouisfed.org/series/baa10y)). Also dasselbe Problem mit anderem
  Rechteinhaber.
- **Das Treasury-Bein ist unproblematisch** — FRED bezieht die Treasury-Daten fuer
  Zinsdifferenzen seit dem 2019-06-21 direkt vom US-Finanzministerium. Nur hilft das nicht:
  das geschuetzte Bein ist das Unternehmensanleihen-Bein.
- **FRED-API-Bedingungen** gelten zusaetzlich und sind kein Freibrief: keine Rechte ausser den
  ausdruecklich genannten, Urheber- und Markenhinweise duerfen nicht entfernt werden, und die
  Anwendung muss sichtbar tragen, dass sie die FRED-API nutzt und von der St. Louis Fed nicht
  bestaetigt oder zertifiziert ist
  ([Terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html)).

**Fazit Kreditrisiko:** Ein echter OAS ist ohne schriftliche ICE-Erlaubnis fuer eine
kommerzielle oeffentliche Seite nicht nutzbar. Bleiben zwei Wege: eine **eigene** Reihe aus
ETF-Gesamtrenditen (dann darf sie nicht „Spread" heissen), oder eine Lizenzanfrage. Die
ETF-Variante braucht `dividend_events` — ein Posten, der ohnehin offen ist.

Nebenbei, weil es die Lizenzlage sinnvoll abrundet: **FRED ist nicht pauschal
problematisch.** Urheberrechtlich geschuetzt sind einzelne Reihen von Drittanbietern (ICE,
Moody's). Reihen aus US-Behoerdenquellen sind es in der Regel nicht. Die Pruefung ist also
**je Reihe** zu machen, nicht „FRED ja/nein".

### 3.3 Put/Call-Historie

Die freie CBOE-Ratio ist weggefallen `[Repo: CLAUDE.md v52]`, deshalb die
Vorwaertsakkumulation. Wer die Historie will, muss sie kaufen (CBOE DataShop oder ein
Datenhaendler) **[Vermutung zur Bezugsquelle]**, oder sie sich aus den eigenen Optionsdaten
selbst bauen — was auf dieselbe Massive-Lizenzfrage hinauslaeuft und zudem nur das eigene
Universum abdeckt.

---

## 4. Sollten wir das ueberhaupt?

### 4.1 Ein Nachbau ohne Gewichte ist unsere Kennzahl mit fremdem Namen

Ja, und zwar aus vier Gruenden, die nicht am Handwerk haengen, sondern an der Pruefbarkeit:

1. **Die entscheidenden Parameter sind nicht veroeffentlicht.** Nicht nur die Gewichte — auch
   die Normierungsvorschrift, also der Schritt, der aus einer Kursgroesse eine 0-bis-100-Zahl
   macht. Zwei verschiedene Normierungen auf denselben Rohdaten ergeben verschiedene Zahlen bei
   identischer Beschreibung.
2. **Was im Netz als Methodik gilt, ist nicht CNNs Aussage.** 125 Tage, 50-Tage-VIX,
   Gleichgewichtung: durchgaengig Sekundaerquellen (Abschnitt 0). Ein Nachbau waere also die
   Rekonstruktion einer Rekonstruktion.
3. **Die Zielgroesse bewegt sich.** CNN sagt selbst, die Breiten-Komponente sei „kuerzlich
   geringfuegig geaendert" worden, ohne zu sagen wie **[CNN]**. Eine Nachbildung, die heute
   passt, kann morgen abweichen, ohne dass wir die Ursache sehen oder benennen koennen.
4. **Es gibt keinen Weg, „richtig" zu belegen.** Weil keine Referenzrechnung veroeffentlicht
   ist, koennen wir nur die **Aehnlichkeit** zu CNNs veroeffentlichter Zahl messen. Und da
   fuehren beide Ergebnisse in eine Sackgasse: **ist die Korrelation hoch, ist unsere Zahl ein
   Duplikat ohne eigenen Beitrag; ist sie niedrig, traegt sie einen Namen, der ihr nicht
   zusteht.** Ein Zwischenergebnis gibt es nicht, das etwas rechtfertigt.

Dazu die Namensfrage: „Fear & Greed Index" ist CNNs Produktname. Eine eigene Rechnung unter
fremdem Namen auszuweisen ist dieselbe Fehlerklasse, die dieses Projekt schon einmal korrigiert
hat — Anbieterwerte, die als eigene Zahl erschienen, und eine Kennzahl, die „KI-Score" hiess
und nach der Validierung in „Saison-Score" umbenannt wurde, weil der Name mehr behauptete als
die Rechnung hielt `[Repo: CLAUDE.md v65.1, v66.9]`.

**Einschaetzung:** Ein „Nachbau" unter CNNs Namen ist nicht belastbar. Was belastbar waere:
eine **eigene** Kennzahl mit eigenem Namen, veroeffentlichter Formel, veroeffentlichten
Gewichten und einer Validierung — und der Hinweis, dass CNN etwas Aehnliches rechnet, als
Einordnung im Text, nicht als Etikett auf der Zahl.

### 4.2 Ueberlappung mit der Stress-Ampel

Die Stress-Ampel ist
`S = 0,3·vol5 + 0,3·vol20 + 0,4·|dd20|`, als Rang gegen bis zu 2520 vorangegangene Sitzungen
`[Repo: shared/stress_score.py:10–17]`. Also: kurzfristige Schwankung, mittelfristige
Schwankung, Abstand zum 20-Tage-Hoch.

Nun die sieben Bestandteile daneben:

| Bestandteil | Verhaeltnis zur Stress-Ampel |
|---|---|
| Market Volatility (VIX) | **starke Ueberlappung.** Implizite gegen realisierte Vola — am Projekt selbst gemessen eng verkoppelt: Spot-Vol-Beta ab 1990 **−4,44**, Standardabweichungsverhaeltnis 6,3 `[Repo: CLAUDE.md v66.25]`. Es ist nicht derselbe Wert, aber es ist dieselbe Dimension. |
| Market Momentum (Abstand zum 125-Tage-Durchschnitt) | **Ueberlappung.** `dd20` ist der Abstand zum 20-Tage-Hoch — anderes Fenster, gleiche Idee „wie weit unter dem letzten guten Stand". |
| Safe Haven Demand (20 Tage Aktien minus Anleihen) | **Ueberlappung in genau den Phasen, auf die es ankommt.** In Stressphasen dominiert das Aktienbein, und das ist naeherungsweise die 20-Tage-Aktienrendite — also wieder `dd20`-nah. |
| Stock Price Strength | **neu** (Breite) |
| Stock Price Breadth | **neu** (Breite) |
| Junk Bond Demand | **neu** (Kreditrisiko) |
| Put and Call Options | **neu** (Nachfrage nach Absicherung) |

Das ist das Kernergebnis dieses Berichts: **Drei der sieben Bestandteile sind aus dem Bestand
rechenbar, und genau diese drei messen Varianten dessen, was die Stress-Ampel schon messt. Die
vier, die wirklich neue Information tragen, sind drei nicht baubare und eine ohne Historie.**
Ein „Nachbau aus dem Bestand" waere damit nicht nur unvollstaendig, sondern unvollstaendig an
der informativen Stelle.

**Widerspruch?** Formal nein — beide waeren 0-bis-100-Raenge auf ueberlappenden Eingaengen und
duerften sich grob gleichsinnig bewegen **[Vermutung, nicht gemessen]**. Praktisch gibt es
aber ein Darstellungsproblem: die beiden Skalen laufen **gegenlaeufig** (hoher Stress-Score =
Belastung; hoher Fear-&-Greed-Wert = Gier, also niedrige Belastung). Zwei invertierte
0-bis-100-Skalen auf derselben Seite sind eine Fehlerquelle, und dieses Projekt hat die
Vorzeichenfehlerklasse zweimal erlebt: die alte Crash-Ampel war invertiert (Lehman und Corona
standen auf 0) `[Repo: CLAUDE.md v66.6]`, und die Radar-Quadranten waren seitenweise
vertauscht `[Repo: CLAUDE.md v66.20]`.

**Welche ist besser, und woran entscheidet man das?** Das laesst sich nicht aus den Formeln
ablesen, sondern nur messen — mit einem **vor** dem Lauf festgeschriebenen Protokoll, wie bei
der Williams-Studie `[Repo: CLAUDE.md v66.23]`:

1. Ereignis vorab definieren (etwa: Rueckgang >= 10 % binnen 20 Sitzungen, wie bei der
   Stress-Ampel-Messung schon benutzt).
2. Beide Kennzahlen als Rang gegen die eigene Vorhistorie, kein Look-ahead.
3. Trennschaerfe als Kennzahl (Trefferquote gegen Basisrate, oder AUC), mit Fallzahl.
4. Entdeckungs- und Pruefzeitraum getrennt, Pruefzeitraum **einmal**.
5. Dazu die Rangkorrelation beider Kennzahlen — liegt sie hoch, ist die Frage „welche ist
   besser" ohnehin weniger wichtig als „brauchen wir zwei".

Die Stress-Ampel hat so eine Messung ansatzweise: nach roten Tagen folgte in 13–17 % der Faelle
ein Rueckgang >= 10 % binnen 20 Sitzungen, Basisrate 4–5 %, nach gruenen Tagen 2–3 %
`[Repo: CLAUDE.md v66.6]` — beschreibend, nicht prospektiv bestaetigt. Ein Nachbau haette am
Anfang gar keine. **Einschaetzung:** Die ehrliche Reihenfolge ist, zuerst die vorhandene
Kennzahl prospektiv zu pruefen, statt eine zweite mit demselben Informationsgehalt daneben zu
stellen.

### 4.3 Einschaetzung in einem Absatz

Der Nachbau unter CNNs Namen ist nicht empfehlenswert: die Parameter sind nicht
veroeffentlicht, die Zielgroesse bewegt sich, und keine Messung kann „richtig" belegen. Der
Nachbau **aus dem Bestand** ist zusaetzlich inhaltlich unattraktiv, weil er genau die
Bestandteile weglassen muesste, die ueber die Stress-Ampel hinausgehen. Was dagegen einen
eigenstaendigen Nutzen hat — unabhaengig davon, ob daraus jemals ein Index wird — sind die
beiden fehlenden **Datenreihen**: Marktbreite und Kreditrisiko. Marktbreite fehlt dem Projekt
spuerbar (Scanner, Regime, Blog, Intermarket-Matrix haben derzeit kein Breitenmass).
Kreditrisiko wuerde den kohaerentesten Hinweis der Intermarket-Matrix direkt adressieren, wo
TLT gegen sechs Aktienziele gleichzeitig auffaellt `[Repo: docs/INTERMARKET.md, CLAUDE.md v63]`.

---

## 5. Bauvorschlag in Stufen

Kein Code, keine Pipeline. Reihenfolge so, dass jede Stufe allein einen Nutzen hat und die
naechste blockieren kann.

### Stufe 0 — Messen, nicht bauen (ohne neue Quelle, ohne Seite)

Eine Studie mit **vorab festgeschriebenem Protokoll**, Ergebnis vor dem ersten
Produktivgedanken:

- Die drei baubaren Bestandteile rechnen (Momentum, Volatilitaet, Safe Haven) — nur lesend,
  Export mit Pruefsumme, Muster der Williams-Studie.
- Rangkorrelation jedes Teils **mit der Stress-Ampel** messen. Liegt sie durchgaengig hoch,
  endet das Vorhaben hier, und das ist ein Ergebnis.
- Optional und mit klarem Vorbehalt: Vergleich gegen CNNs veroeffentlichte Reihe. CNNs
  JSON-Endpunkt liefert je Bestandteil eine Zeitreihe und waere das praezisere Messinstrument
  — aber er ist **undokumentiert** (eine Go-Bibliothek haelt ausdruecklich fest, dass CNN keine
  dokumentierte oeffentliche Schnittstelle anbietet), lizenzrechtlich ungeklaert und war aus
  dieser Umgebung nicht erreichbar (HTTP 418). Deshalb: **als Einmal-Messung vertretbar, nicht
  speichern, nicht veroeffentlichen, nicht in eine Pipeline** — eine Produktivquelle, die man
  nicht lizenziert hat und die ohne Ankuendigung verschwinden kann, ist keine Quelle.
- **Grenze dieser Stufe:** Sie kann die beiden Naeherungen (Breite, Kredit) nicht bewerten, weil
  dafuer genau die fehlenden Quellen noetig sind.

### Stufe 1 — Drei Teilreihen, kein Index (ohne neue Quelle)

Falls Stufe 0 eine ausreichend geringe Ueberlappung zeigt: die drei Teile als **eigene
Reihen** fuehren, jede mit eigener Bedeutung, **ohne Zusammenfassung zu einer Zahl**.

- Momentum: `^GSPC` gegen 125-Sitzungs-Durchschnitt, ab 1990.
- Volatilitaet: `^VIX` gegen 50-Sitzungs-Durchschnitt, ab 1990.
- Safe Haven: 20-Handelstage-Differenz SPY minus IEF, **ab 2002** — und die Grenze steht an der
  Reihe, nicht im Kleingedruckten.
- Normierung: exakt die Mechanik der Stress-Ampel (Rang gegen bis zu 2520 vorangegangene
  Sitzungen, Mindestreferenz, keine Zukunft), damit beide Kennzahlen dieselbe Skala und
  dieselbe Leseart haben.
- **Grenzen, die mitgeschrieben werden:** drei Teile sind kein Index; die drei korrelieren
  untereinander (Stufe 0 liefert die Zahl); Safe Haven beginnt 2002; Gesamtrendite ist durch
  Kursrendite ersetzt.

### Stufe 2 — Marktbreite als eigene Datenreihe (neue Quelle, Lizenz zuerst)

**Vorbedingung, nicht Nebenbedingung:** die Lizenzfrage zu Massive ist schriftlich geklaert —
und zwar fuer die bestehenden Options-Seiten mit. Ohne das kein Bau.

Dann, in dieser Reihenfolge:

1. Universum definieren und als eigenen Bestand fuehren (Titelart, Primaerboerse, Stand je
   Datum — ein Universum, das sich aendert, ist selbst eine Datenreihe).
2. Rueckbau der Tagesuebersichten, Tiefe nach Plan (2 / 5 / 10 Jahre / alles ab 2003-09-10).
3. Daraus rechnen: A/D-Linie, Up-/Down-Volumen, McClellan-Oszillator und -Summation,
   52-Wochen-Hoch/Tief-Zaehlung.
4. Eigene Tabellen, eigener Waechter mit unabhaengiger Referenz, eingefrorene Momentaufnahme
   vor jedem Umbau — das Muster, das im Projekt steht.
5. **Grenzen, die an jede Zahl gehoeren:** frueheste Beobachtung 2003, also kein 2000er-Crash
   und kein 2008 mit vollem Vorlauf fuer eine 2520-Sitzungs-Referenz vor etwa 2013; unser
   McClellan ist **nicht** der NYSE-McClellan, weil das Universum ein anderes ist — er darf
   deshalb nicht unter dem etablierten Namen stehen; Splits und Adjustierung beeinflussen die
   52-Wochen-Extrema und muessen in der Definition festgelegt werden, nicht im Code
   entschieden.

### Stufe 3 — Kreditrisiko-Reihe

Zwei Wege, einander ausschliessend:

- **(a) Eigene Reihe aus ETF-Gesamtrenditen** (HYG gegen IEF, mit Ausschuettungen). Braucht
  `dividend_events` — ohnehin offen. Ergebnis ist ein **Risikoappetit-Mass, kein Spread**, und
  darf nicht „Spread" heissen. Ueberpruefbar gegen den ICE-OAS in einer einmaligen, nicht
  veroeffentlichten Messung; faellt die Rangkorrelation schwach aus, ist die Reihe als Ersatz
  ungeeignet und das waere ein Abbruchkriterium.
- **(b) Lizenzanfrage bei ICE Data Indices** fuer die Veroeffentlichung des HY-OAS. Dann waere
  es die etablierte Groesse — mit dem Vorbehalt, dass die FRED-Fassung ab April 2026 nur noch
  drei Jahre Beobachtungen traegt, die Normierungshistorie also anderswo herkommen muesste.

Das fehlende Investment-Grade-Bein (kein LQD) waere in beiden Faellen ein eigener, kleiner
Posten: ein zusaetzlicher Ticker im Bestand.

### Stufe 4 — Eine eigene Kennzahl, falls Stufe 0–3 sie rechtfertigen

Nur mit ausdruecklicher Entscheidung, und dann mit sechs Bedingungen:

1. **Eigener Name**, kein Verweis auf CNN im Namen. CNN gehoert in den erklaerenden Text.
2. **Veroeffentlichte Formel und veroeffentlichte Gewichte** — der ganze Grund, warum der
   Nachbau nicht geht, darf nicht bei uns wiederkehren.
3. **Eine Rechnung**, Python und Browser als nachweisbare Zwillinge gegen eine dritte,
   unabhaengig hergeleitete Referenz.
4. **Validierung mit vorab festgelegtem Ereignis**, Entdeckungs- und Pruefzeitraum getrennt, mit
   Fallzahl an jeder Zahl — und das Ergebnis steht auf der Seite, auch wenn es „keine
   Trennschaerfe" lautet.
5. **Keine Farbe, die eine Richtung behauptet.** Eine Skala, eine Leserichtung. Entweder
   dieselbe Richtung wie die Stress-Ampel, oder sichtbar getrennt dargestellt — nicht zwei
   gegenlaeufige 0-bis-100-Zahlen nebeneinander.
6. **Teilbestandteile einzeln sichtbar**, mit Angabe, welche fehlen und warum. Eine
   Zusammenfassung, die eine Luecke verdeckt, ist schlechter als keine.

---

## 6. Offene Punkte und Nutzerentscheidungen

- **Lizenzstatus bei Massive klaeren** — welchen Plan haben wir, und deckt er die oeffentliche
  Darstellung der bestehenden Options-Seiten? Hat Vorrang vor allem in diesem Bericht und ist
  von diesem Vorhaben unabhaengig.
- **Entscheidung: ueberhaupt?** Meine Einschaetzung steht in 4.3 — nicht als Nachbau. Die
  Entscheidung liegt nicht bei mir.
- **Falls ja: Stufe 0 zuerst**, mit Protokoll vor dem Lauf, und das Recht, nach Stufe 0 zu
  beenden.
- **LQD in den Bestand aufnehmen?** Kleine Aenderung, macht die Investment-Grade-Seite
  ueberhaupt erst messbar.
- **`dividend_events`** blockiert jede ETF-Gesamtrenditerechnung und steht schon offen.
- **Korrektur am Auftragstext festhalten:** `^SKEW`, `^VVIX`, `^COR*` sind **nicht** onboardet
  (nur Live-Abruf bei Yahoo, `^COR*` nur letzter Wert); LQD fehlt; `pc_ratio` je Ticker ist ein
  IV-Verhaeltnis, keine Volumen-Put/Call-Ratio.
- **Nicht gemessen** (und als Vermutung gekennzeichnet): die tatsaechliche Korrelation zwischen
  Stress-Ampel und den drei baubaren Bestandteilen. Das ist genau der Inhalt von Stufe 0 — und
  es waere unsauber, die Entscheidung auf eine Zahl zu stuetzen, die noch niemand gerechnet hat.

---

## Quellen

CNN und Methodik-Beschreibungen:
[CNN Fear and Greed Index](https://www.cnn.com/markets/fear-and-greed) (HTTP 451 direkt, Prosa ueber Reader-Proxy) ·
[referently.com](https://referently.com/the-cnn-fear-greed-index-how-to-read-it-what-it-measures-and-where-it-fails/) ·
[investingnews.com](https://investingnews.com/what-is-cnn-fear-greed-index/) ·
[finmasters.com](https://finmasters.com/fear-and-greed-index/) ·
[supertype.ai](https://supertype.ai/notes/fear-greed-index-part1) ·
[tradeintelligent.substack.com](https://tradeintelligent.substack.com/p/how-does-cnns-fear-and-greed-index) ·
[cheddarflow.com](https://www.cheddarflow.com/blog/uncovering-the-cnn-fear-and-greed-index-what-it-is-and-how-to-use-it/) ·
[TradingView-Nachbau](https://www.tradingview.com/script/OYMlN4a2-CNN-Fear-and-Greed-Index-JD-modified-from-minusminus/) ·
[DidierRLopes/fear-greed-index](https://github.com/DidierRLopes/fear-greed-index) ·
[wildsurfer/cnn-fear-and-greed-parse](https://pkg.go.dev/github.com/wildsurfer/cnn-fear-and-greed-parse/v2)

Datenquellen und Lizenzen:
[Massive: Daily Market Summary](https://massive.com/docs/rest/stocks/aggregates/daily-market-summary) ·
[Massive: Weiterverbreitung](https://massive.com/knowledge-base/article/how-can-i-redistribute-massives-market-data) ·
[Massive: Market Data Terms (PDF, 2024-10-09)](https://massive.com/terms/market_data_terms.pdf) ·
[Massive: Market Data Terms of Service](https://massive.com/legal/market-data-terms-of-service) ·
[FRED BAMLH0A0HYM2](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) ·
[FRED BAA10Y](https://fred.stlouisfed.org/series/baa10y) ·
[FRED API Terms of Use](https://fred.stlouisfed.org/docs/api/terms_of_use.html) ·
[Barchart $ADRN](https://www.barchart.com/stocks/quotes/$ADRN/price-history/historical) ·
[StockCharts Market Breadth](https://stockcharts.com/freecharts/historical/marketbreadth.html) ·
[McClellan Market Breadth Data](https://www.mcoscillator.com/market_breadth_data/) ·
[unicorn.us.com/advdec](http://unicorn.us.com/advdec/) ·
[AAII: Market Breadth Data](https://www.aaii.com/journal/article/gauging-market-trends-market-breadth-data)

Eigener Bestand (Repo, Stand 2026-10-23):
`shared/symbols.py` (Symboldatenbank, Zinsreihen Z. 218–248, Anleihen Z. 943–945) ·
`shared/options_universe.py` (Options-Universum, Z. 17–56) ·
`shared/stress_score.py` (Stress-Ampel, Z. 10–17, 34–39) ·
`shared/cpi_data.py` (FRED-Anbindungsmuster, Z. 81–106) ·
`scripts/compute_options_skew.py` (`_index_series` Z. 239, P/C Z. 1203–1210, `__PCR` Z. 1319) ·
`scripts/snapshot_gex_massive.py` (Massive-Endpunkte) ·
`CLAUDE.md` (Messungen v52, v62, v63, v65.1, v66.6, v66.9, v66.20, v66.22, v66.23, v66.25) ·
`docs/OPTIONS.md`, `docs/INTERMARKET.md`
