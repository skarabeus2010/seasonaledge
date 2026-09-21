# Intermarket / Lead-Lag — kanonische Doku

> Stand 2026-09-22. Deckt ab: die zwei veröffentlichten Einzelstudien (Krypto,
> Anleihen), die Matrix über 19 Märkte, die Seite `/intermarket`, das Signal im
> Daily Briefing und die Methodik, die für alles drei gilt.

## 1. Worum es geht

Die Frage ist immer dieselbe: **Wenn Markt A sich ungewöhnlich stark bewegt hat,
passiert danach etwas Besonderes in Markt B?** Entscheidend ist „danach" — eine
gleichzeitige Korrelation ist keine Prognose, sondern nur die Feststellung, dass
sich zwei Märkte am selben Tag bewegen. Genau daran scheitert die populäre
Lesart der Bitcoin-Aktien-Korrelation: sie ist bei Versatz null deutlich
(+0,36 bis +0,45 je nach Zeitraum) und bei Versatz eins praktisch verschwunden.

## 2. Die gemeinsame Methodik

Alle drei Untersuchungen nutzen dieselben Bausteine. Wer einen davon ändert,
ändert alle Aussagen, die darauf beruhen.

| Baustein | Umsetzung | Warum |
|---|---|---|
| Signalfenster | 10 Handelstage, kumuliert | zwei Wochen; kurz genug für ein Ereignis, lang genug gegen Tagesrauschen |
| Schwelle | 90. Perzentil der **eigenen** Bewegungsverteilung | 5 % sind bei Gold ein seltener Sprung und bei Bitcoin der Median — eine feste Prozentschwelle vergleicht Unvergleichbares |
| Messfenster | t+1 bis t+10 | ausschließlich, was **nach** dem Signal liegt |
| Mindestabstand | 41 Handelstage | disjunkte Pfade, sonst zählt dieselbe Bewegung mehrfach |
| Referenz | Basisrate des Zielmarktes | nicht gegen null lesen — jeder Markt steigt im Mittel |
| Nullverteilung | zirkuläre Zeitverschiebung, 2000 Runden | zerstört den zeitlichen Zusammenhang, erhält Volatilitäts-Clustering |
| p-Wert | zweiseitig, mit Plus-eins-Korrektur | siehe 5. Lessons |

Code: `shared/realized_vol.py` (RV an EINER Stelle), `scripts/research/btc_lead_lag.py`
(die Bausteine; die anderen Skripte importieren daraus), `scripts/research/bond_lead_lag.py`,
`scripts/research/bond_kontrollen.py`, `scripts/research/intermarket_matrix.py`,
`scripts/research/export_intermarket.py`.

## 3. Die drei Untersuchungen

### 3a. Krypto → Aktien (veröffentlicht)

Artikel: `/blog/laeuft-bitcoin-dem-aktienmarkt-voraus/` (DE),
`/en/blog/does-bitcoin-lead-the-stock-market/` (EN).
Charts: `scripts/research/render_krypto_lag_charts.py`.

**Die viel zitierte 5-%-Schwelle ist bei Bitcoin der MEDIAN aller
10-Tage-Bewegungen** — also die normalste Bewegung überhaupt, und der Effekt
dort liegt unter dem Marktdurchschnitt. Messbar wird erst etwas ab 10 %, und
belastbarer ab 20 %:

| Signal | Horizont | SPY danach | Basis | p |
|---|---|---|---|---|
| BTC ≥ 10 % | 3 Wochen | +2,06 % | +0,85 % | 0,022 |
| BTC ≥ 20 % | 3 Wochen | +2,29 % | +0,85 % | 0,027 |
| BTC ≥ 20 % | 4 Wochen | — | +1,14 % | 0,050 (Grenzfall) |
| ETH ≥ 20 % | 3 Wochen | +2,85 % | +0,85 % | 0,020 |
| ETH ≥ 20 % | 4 Wochen | +3,63 % | +1,14 % | 0,011 |

### 3b. Anleihen → Aktien (veröffentlicht, der belastbarste Befund)

Artikel: `/blog/anleihen-fruehindikator-aktienmarkt/` (DE),
`/en/blog/bonds-as-a-stock-market-indicator/` (EN).
Charts: `scripts/research/render_bond_lag_charts.py`.

Signal: TLT-Kursanstieg ab **4,1 %** über 10 Handelstage (n = 50, 2002-2026).
SPY danach: +1,80 / **+2,09** / +2,12 / +2,85 % (1-4 Wochen), p 0,001-0,005,
Trefferquote 74 % gegen 65,7 % Basis. Die Gegenrichtung zeigt **nichts**
(p 0,29-0,97).

**Der Effekt existiert nur im Stress**, und das ist der eigentliche Befund:

| Marktumfeld | SPY nach 2 Wochen | p |
|---|---|---|
| ruhige Phasen (Vola unter Median) | +0,53 % | 0,935 — also exakt die Basisrate, sprich nichts |
| unruhige Phasen | **+3,65 %** | < 0,001 |

Beide Zeithälften halten (2003-2019 +1,72 %, p 0,019; 2020-2025 +2,87 %, p 0,008).
Max-T über 64 Kombinationen: p 0,018.

⚠️ **Es ist ein Erholungsmuster, keine Vorhersage aus heiterem Himmel.** Der SPY
ist VOR dem Ereignis im Median um 1,31 % gefallen (in 62 % der Fälle negativ).
Jeder Text dazu muss das sagen — ohne diese Hälfte liest man eine Prognose, wo
eine Erholung steht.

### 3c. Die Matrix (Seite `/intermarket`)

19 Märkte, 556 auswertbare Paare, davon **470 in der Primärfamilie**.
Ergebnis: **0 bestätigte Befunde.** Das ist die Aussage der Seite.

Die vier Hürden für einen Befund:

1. **Primärfamilie** — das Paar muss zwei *verschiedene* Kategorien verbinden.
   Dass der Dow dem S&P 500 folgt, ist keine Intermarket-Hypothese, sondern
   derselbe Markt unter anderem Namen. Die Regel trennt nach **Kategorie**, nicht
   nach gemessener Korrelation; sonst wäre schon die Wahl der Familie eine Suche
   nach dem Ergebnis.
2. **Max-T-Schranke** |t| > 3,92 über die ganze Familie.
3. Gleiches Vorzeichen in **beiden Zeithälften**.
4. Mindestens **20 Ereignisse je Hälfte** (nicht insgesamt).

Hürde 4 entscheidet den konkreten Fall: die stärkste Zelle der Matrix
(**Silber abwärts → Versorger**, t = 4,09, p = 0,043) *reisst* die Max-T-Schranke
— und scheitert an 21/14 Ereignissen je Hälfte. Ohne diese Hürde stünde dort ein
Befund.

Der kohärenteste Hinweis ist der Anleihen-Cluster: TLT aufwärts gegen sechs
verschiedene Aktienziele (SPY t=3,73, QQQ 3,65, XLK 3,58, XLF 3,45, DIA 3,04,
XLU 2,99), je n=52 mit 26/26 je Hälfte, alle mit gleichem Vorzeichen in beiden
Hälften — aber unter der Schranke. Ein Zufallstreffer verteilt sich nicht so
systematisch über verwandte Ziele; und es ist genau der Zusammenhang, den 3b
mit gezielter Prüfung belegt.

**Mag 7 fällt komplett heraus** (ETF erst ab 04-2023, erreicht nirgends 20
Ereignisse). Steht so auf der Seite.

## 4. Was live ist

| Ort | Was |
|---|---|
| `/intermarket` + `/en/intermarket` | die Matrix, `landing/pages/intermarket.html` |
| `landing/data/intermarket_matrix.json` | 77 KB, **committet** (Studienergebnis, kein Cron-Output) |
| Daily Briefing | `shared/intermarket.py`, Abschnitt im `daily_report.html.j2` |
| Wächter | `scripts/verify_intermarket.py` (22 Verhaltensfälle) |

**Das Anleihen-Signal im Briefing meldet nur, wenn BEIDE Bedingungen zutreffen:**
TLT-Anstieg ≥ 4,0632 % UND realisierte SPY-Vola > 13,9 %. Ohne die zweite
Bedingung wäre es Rauschen, das wie eine Aussage aussieht (siehe 3b). Die
Schwelle ist bewusst der **exakte** Wert aus der Studie, nicht die im Artikel
angezeigte Rundung 4,1 % — die gerundete Zahl wählt eine andere Ereignismenge.

**`/intermarket` und `/intermarket-shocks` gehören zusammen** und verlinken sich
gegenseitig: der Shock-Analyser lässt jede Kombination frei wählen und rechnet
sie einzeln, *ohne* Korrektur — er kann sie gar nicht haben, wenn der Nutzer
beliebig durchklickt. Die Matrix zeigt die eine vorab festgelegte Spezifikation,
korrigiert. Dort erkunden, hier nachsehen, was standhält.

## 5. Lessons

- **Ein Test, der einen anderen Pfad nimmt als die Produktion, sagt nichts über
  die Produktion** — auch wenn er dieselbe Funktion aufruft. (Die
  Normierungsquote 43 % → 76 % war mit `bis=None` gemessen, der Live-Pfad ruft
  mit `bis=<Session>`; genau dort sass der Fehler.)
- **Eine Matrix ist ein Data-Mining-Generator.** Bei 470 Tests sind ~24
  Zufallstreffer zu erwarten. Ohne Korrektur findet man *immer* etwas.
- **Standardisieren, nicht in Prozentpunkten vergleichen.** Ein erster Lauf
  verglich rohe Prozentpunkte — Bitcoin und Uran als Ziele setzten damit eine
  Schranke von 11 pp, an der kein ruhigerer Markt je vorbeikommt. Die Matrix
  hätte nur gemessen, welcher Markt am stärksten schwankt.
- **Eine kleinere, vorab sachlich begründete Testfamilie schlägt eine grosse mit
  Korrektur** — aber die Regel muss vor dem Blick aufs Ergebnis feststehen.
- **„20 Ereignisse" reicht nicht für eine Aussage über zwei Hälften.** 20
  insgesamt können 3 und 17 sein.
- **Den p-Wert zweiseitig rechnen und plus eins korrigieren.** Die Richtung nach
  dem Blick aufs Ergebnis zu wählen halbiert p unzulässig. (Von Codex gefunden;
  die p-Werte verdoppelten sich etwa, die Befunde hielten.)
- **Ein Vergleich über verschiedene Grundmengen ist kein Vergleich.** Erst auf
  derselben Teilmenge verglichen ergab die Neurechnung +2,90 → +3,07.
- **Lokaler Build != Server-Build.** `build_en.py` erzeugt lokal 2 JSON-LD-Blöcke
  je EN-Seite und auf dem Server 3, weil dort vorher ein Cache-Buster an die
  CSS-Referenz gehängt wird und eine Regex deshalb ins Leere greift. Wer eine
  Build-Kette lokal prüft, prüft nicht die, die ausliefert. Siehe 6.
- **Der Vorlauf gehört ins Bild.** Ein Pfad, der nur ab t=0 zeigt, macht aus
  einer Erholung eine Prognose. Der Chart `2_pfad.png` zeigt bewusst t-10 bis t+30.
- Die Kursreihen sind dividendenbereinigt und tragen an Ausschüttungstagen einen
  kleinen künstlichen Abschlag — bei monatlich ausschüttenden Anleihe-ETFs
  spürbarer als bei Gold. TLT/HYG sind ETF-**Kurse**, keine Renditen, keine
  Spreads.

## 6. Offen

- [ ] **Der Haupt-Pfad von `build_en.py` ist auf dem Server tot** (2026-09-22
  gefunden und bis zur Ursache verfolgt).

  **Symptom:** das JSON-LD ist auf allen EN-Seiten deutsch — belegt an
  `/en/intermarket`, `/en/skew`, `/en/sektor-rotation` — inklusive der `url`, die
  auf die DE-Fassung zeigt. Google liest strukturierte Daten; eine englische
  Seite mit deutschem FAQPage-Schema ist ein Mismatch.

  **Ursache:** `replace_head()` ersetzt den Head bis zum `app.css`-Link durch
  einen neu gebauten mit genau zwei JSON-LD-Blöcken (WebPage, BreadcrumbList).
  Seine Regex verlangt `href="/landing/css/app.css"` **ohne Query-String**. Im
  Deploy läuft aber `inject_credentials.sh` **vorher** und macht
  `app.css?v=<git-sha>` daraus (`.github/workflows/deploy.yml:41` vor `:47`).
  Die Regex greift nie → `replace_head` liefert `False` → **jede** EN-Seite
  fällt auf `localize_head_targeted` zurück, das den deutschen Head samt
  JSON-LD erhält und nur Titel, Description und URLs tauscht.

  **Warum es niemand gemerkt hat:** lokal gibt es keinen Cache-Buster, also
  greift die Regex dort und der lokale Build erzeugt ein *anderes* Ergebnis als
  der Server (lokal 2 JSON-LD-Blöcke, Server 3). Genau die Fehlerklasse aus
  v62: **ein Test, der einen anderen Pfad nimmt als die Produktion, sagt nichts
  über die Produktion.** `verify_en` bleibt grün, weil es sichtbaren Text prüft
  und kein JSON-LD.

  **Warum der Einzeiler falsch wäre:** die Regex zu weiten lässt `replace_head`
  auf 37 EN-Seiten greifen — und entfernt dort das FAQPage-Schema, weil der neu
  gebaute Head nur WebPage und BreadcrumbList kennt. Der richtige Fix trägt
  seitenfremde JSON-LD-Blöcke mit und übersetzt sie; und er braucht einen Test,
  der **mit** Cache-Buster baut.
- [ ] Die Matrix kontrolliert nicht für das gemeinsame Marktumfeld. Starke
  Bewegungen häufen sich in Krisen; die Einzelstudie 3b trennt das, die Matrix
  nicht. Codex hat das als systematische Verzerrung benannt.
- [ ] Dritte Quellen-Option prüfen: rohe Schlusskurse + explizite
  Dividendenevents (Tabelle `dividend_events` ist leer).
- [ ] Ob ein zweiter Horizont neben t+10 sinnvoll ist, wäre eine **neue**
  Spezifikation und bräuchte eine eigene, vorab festgelegte Familie — nicht
  nachträglich dazunehmen.
