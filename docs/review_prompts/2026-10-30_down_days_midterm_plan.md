# Plan v1 — zwei Datenartikel: SPY-Down-Days und S&P 500 in der letzten Woche vor Midterms

Stand 2026-10-30. Geschrieben **vor** dem Rechenlauf: Definitionen, Kennzahlen und
Robustheitsprüfungen stehen fest, bevor Ergebnisse angesehen werden. Bitte prüfen, ob
die Definitionen tragen, wo Look-ahead, Überlappung oder Stichprobenmischung lauern, und
welche Aussage die Artikel am Ende höchstens machen dürfen.

Beide Artikel erscheinen DE+EN im Blog (`blog/posts/`), mit eigenen Charts
(matplotlib, Muster `scripts/research/render_zweig_charts.py`) und einem
Zahlenwächter im Deploy-Gate (Muster `scripts/verify_wahlen_blog.py`).

---

## Studie A — Was nach Down-Days im SPY passiert (letzte 20 Jahre)

### Daten
- `blog/daten/spy_2026-10-29.json` (eingefroren, im Repo): SPY aus der Supabase-Tabelle
  `prices`, Spalten `date, close, log_return`, 2005-01-03 … 2026-10-29. `close` ist der
  adjustierte Schluss zum Schreibzeitpunkt, `log_return` der gespeicherte (aus
  adjustierten Kursen, also inklusive Dividenden-Anpassung — Gesamtrendite-Näherung).
- Die Zeile 2026-10-30 war beim Abruf die **laufende** Sitzung (15:33 New York) und ist
  nicht enthalten. Letzte abgeschlossene Sitzung: 2026-10-29.
- Geprüft: keine Zeile an einem Nicht-Handelstag (NYSE-Kalender), echte Schließungen
  (2007-01-02 Ford, 2012-10-29/30 Sandy) sind Lücken ohne Phantomzeile. 13 Zeilen mit
  `log_return = 0` seit 2006, alle an Handelstagen (vermutlich echte Gleichstände auf
  Cent-Raster; für Down-Day-Ereignisse irrelevant, in Vorwärtssummen enthalten).

### Definitionen
- Tagesrendite `r_t = exp(lr_t) − 1`.
- Zeitraum: Ereignistage `t` mit `2006-10-30 ≤ t ≤ 2026-10-29` (20 Jahre).
- **Down-Day-Stufen:** `r_t ≤ −1 %`, `≤ −2 %`, `≤ −3 %`, `≤ −4 %` (kumulativ, d. h. ein
  −3-%-Tag zählt auch in −1 % und −2 %). Zusätzlich nur zur Häufigkeit: `r_t < 0`.
- **Vorwärtsrendite** `F_h(t) = exp(Σ_{i=1..h} lr_{t+i}) − 1`, Schluss des Ereignistags bis
  Schluss der h-ten Folgesitzung, `h ∈ {15, 30, 50}` Handelstage. Kein Einstieg zum Schluss
  eines Tages, dessen Schluss man nicht kennt — der Ereignistag ist zum Schluss bekannt.
- Nur vollständige Fenster (`t + h ≤ 2026-10-29`); unvollständige werden gezählt und
  benannt, nicht ausgewertet.
- **Basis:** alle Sitzungen desselben Zeitraums mit vollständigem Fenster (unbedingte
  Vorwärtsrendite). Überrendite = Ereignismittel − Basismittel.

### Kennzahlen je Stufe und Horizont
n, Mittel, Median, Trefferquote (`F_h > 0`), 10.-/90.-Perzentil (linear wie numpy),
schlechtester Fall, Basis-Mittel/Median/Trefferquote, Überrendite. Dazu Häufigkeit je
Kalenderjahr (Chart: Balken je Jahr, Stufe −2 %).

### Überlappung / Häufung
Down-Days häufen sich (2008, 2020, 2022) → Fenster überlappen, die effektive Fallzahl ist
viel kleiner als n. Deshalb zwei Stichproben:
1. **alle Ereignisse** (beschreibend);
2. **entzerrt** je Horizont h: ein Ereignis zählt nur, wenn seit dem letzten
   **gezählten** Ereignis derselben Stufe mindestens h Sitzungen vergangen sind
   (chronologisch, gierig) → die Vorwärtsfenster überlappen nicht.

### Test (nur auf der entzerrten Stichprobe)
Zufallsvergleich: 10 000-mal k Starttage aus der Basis ziehen, **mit derselben
Nicht-Überlappungsbedingung** (gierige Ziehung ohne Überlappung), Mittel der
Vorwärtsrendite; p zweiseitig mit Plus-eins (`(1 + #|Δ_zufall| ≥ |Δ_beob|) / (1 + 10 000)`),
Δ = Mittel − Basismittel. Mehrfachtests: 4 Stufen × 3 Horizonte = 12 — Holm über die 12.
Kein Test auf „alle Ereignisse“.

### Robustheit
- ohne die beiden Krisenblöcke 2008-09-01 … 2009-06-30 und 2020-02-15 … 2020-06-30;
- Hälften 2006-10-30 … 2016-10-28 und 2016-10-31 … 2026-10-29;
- Pfad 0 … 50 Sitzungen (Mittel und Median) für −2 % gegen die Basis;
- größter Zwischenverlust in den 15 Folgesitzungen (Minimum des Pfads), damit die
  Gegenseite sichtbar ist.

### Erwartbare Störgröße (wird im Text benannt, nicht wegdefiniert)
Down-Days fallen in Phasen hoher Volatilität; höhere Folgerenditen dort sind zum Teil
Risikoprämie und gehen mit größeren Zwischenverlusten einher. Ein Mittel über wenige
Krisen wird von 2008/2020 dominiert. Kein Handelssignal.

---

## Studie B — S&P 500 in der letzten Woche vor US-Midterms

### Daten
Eingefrorener Snapshot `landing/data/wahlen_snapshots/midterm-2026-10.json` (Kurse bis
06.10.2026, Code-SHA `d6d4999`) — derselbe Stand wie im Artikel
`midterm-wahltag-boerse`. Pfade ±60 Sitzungen um jede Wahl, Gültigkeit je Offset
(`grund`), Vergleichsjahre (benachbarte ungerade Jahre, Pseudotermin = erster Dienstag
nach dem ersten Montag im November). Rechnung über `shared/elections.py`
(`fenster_rendite`, `aggregiere`) — keine eigene Kopie.

### Definitionen
- t0 wie im bestehenden Artikel: letzter Schluss am oder vor dem Wahltag (bis 1968 und
  1972/76/80 war die NYSE am Wahltag geschlossen → t0 = Vortag).
- **Letzte Woche:** `t−5 → t0` (fünf Sitzungsrenditen t−4 … t0). Daneben `t−5 → t−1`
  (ohne Wahltag) und die einzelne Sitzungsrendite je Offset t−5 … t+1 („Tag für Tag“,
  t+1 = Tag nach der Wahl als Kontext).
- Stichproben: alle gültigen Midterms 1898–2022 (31, 1914 fehlt) und **seit 1971**
  (Kalender belegt, Wahltag ab 1984 geöffnet — Unterschied t0 benennen).
- Vergleich mit Jahren ohne Wahl **nur gepaart** auf den Tripeln, in denen beide
  Vergleichsjahre gültig sind; Differenz = Wahl − Mittel der beiden Vergleichsjahre.
  Mittel auf verschiedenen Stichproben werden nie ohne Fallzahl nebeneinandergestellt
  (Lehre aus dem Midterm-Artikel).
- Kennzahlen: n, Mittel, Median, Trefferquote, beste/schlechteste Woche mit Jahr.

### Kein p-Wert
Wie im bestehenden Artikel: rund 30 überlappungsfreie Fälle, viele Fenster und Offsets
wären denkbar → beschreibend, Fallzahl an jeder Zahl. Frage an Codex: ist ein
Vorzeichentest auf der gepaarten Differenz vertretbar, oder lädt er zum Data-Mining ein,
weil das 5-Tage-Fenster aus einer Familie möglicher Fenster gewählt wurde?

### Abgrenzung
Der bestehende Artikel behandelt ±20 Sitzungen und nennt einen Vorlauf von +2,33 Pp
(gepaart). Der neue Artikel zeigt nur die letzte Woche Tag für Tag und verlinkt dorthin;
er darf dem bestehenden nicht widersprechen. 2026 ist im Snapshot nicht enthalten — der
Artikel verweist für den laufenden Stand auf `/wahlen`.

### Einschränkungen (im Text)
Rückgerechnete Reihe vor 1957; Samstagshandel bis 1952 (fünf Sitzungen < eine
Kalenderwoche); Wahltag bis 1968 geschlossen.

---

## Fragen an den Reviewer
1. Trägt die Entzerrung (gierig, Abstand ≥ h) — oder verzerrt die gierige Auswahl die
   Stichprobe Richtung des ersten Tages einer Häufung (der danach meist weiter fällt)?
   Wäre „letzter Tag einer Häufung“ oder „ein zufälliger Tag je Häufung“ besser?
2. Ist der Zufallsvergleich mit derselben Nicht-Überlappungsbedingung korrekt, oder
   braucht es einen Blockansatz, der die Volatilitätshäufung der Basis nachbildet?
3. Adjustierte Kurse (Dividende) gegen „Kursrendite“ — reicht die Kennzeichnung?
4. Studie B: Fenster t−5 → t0 oder t−5 → t−1 als Hauptzahl?
5. Was fehlt, was ist zu stark formuliert?
