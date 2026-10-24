# Entwurf zur Diskussion: Stressindikatoren und Markttiefs

> Stand 2026-10-24 · **Diskussionsgrundlage, kein Bauplan.** Zwei Codex-Runden gelaufen,
> beide mit dem Urteil „nicht tragfähig". Die Abschnitte 3 bis 6 sind die ERSTE Fassung;
> was daran widerlegt ist, steht in Abschnitt 8. **Wer eine Zahl braucht, liest
> Abschnitt 8.**
>
> Vier eigene Fehler, alle gemessen und korrigiert:
> 1. **^SKEW und ^VVIX sind verfügbar** (SKEW 9 196 Zeilen ab 1990-01-02, VVIX 4 974 ab
>    2007-01-03). Abschnitt 2 behauptete das Gegenteil, weil ich nur `shared/symbols.py`
>    durchsucht habe — der Options-Cron holt sie direkt bei Yahoo mit `period="max"` und
>    schneidet erst für das Chart auf 504 Tage.
> 2. **Der Haupteinwand in Abschnitt 4 ist logisch falsch.** Eine Vorwärtsrendite steht
>    ebenfalls erst später fest; entscheidend ist, dass das SIGNAL nur Vergangenheit
>    nutzt. Und sie allein verfehlt die Frage: 100 → 80 → 110 ergibt +10 %, obwohl der
>    Einstieg 20 % über dem späteren Tief lag.
> 3. **Die Familie sind 324 Hypothesen, nicht 12** (12 Indikatoren × 3 Schwellen ×
>    3 Horizonte × 3 Ziele). Bei 324 Holm-Tests liegt die erste Schranke bei p ≤ 0,000154;
>    unser Bootstrap mit 2 000 Runden erreicht bestenfalls 1/2001 = 0,0005. Kein erster
>    Test könnte bestehen, unabhängig von den Daten.
> 4. **Die erste Messung zählte den Signaltag mit** (Fenster t..t+x statt t+1..t+x) und hat
>    damit etwa die Hälfte des Effekts als Erkennung statt als Vorhersage gezählt.

## 1 Was der Nutzer will

Eine Art Backtest: **welche Stressindikatoren in welcher Kombination kurz- und
mittelfristige Markttiefs bei SPY, QQQ oder DIA anzeigen.** Genannte Kandidaten: VIX,
VVIX, SKEW (mit Nachdruck), Anleihekurse (HYG, Investment Grade, TLT), Marktbreite
(notfalls herunterladen), 52-Wochen-Hoch/Tief, Dollar-Index, Öl — und die Frage, ob es
weitere gibt.

## 2 Bestand, gemessen (2026-10-23)

| Gruppe | vorhanden (mit Beginn) | fehlt |
|---|---|---|
| Volatilität | `^VIX` 1990-01-02 · **`^SKEW` 1990-01-02** · `^VXN` 2001-01-23 · `^VIX3M` 2006-07-17 · **`^VVIX` 2007-01-03** · `^OVX` 2007-05-10 · `^VIX9D`, `^VIX1D` (kurz) | — |
| Anleihen / Kredit | `TLT` 2002-07-30 · `IEF` 2002-07-31 · `SHY` · `HYG` 2007-04-12 · `^TNX`, `^TYX`, `^FVX`, `^IRX` | **`LQD`** (Investment Grade), `JNK`, `AGG`, `TIP` |
| Dollar | `EURUSD=X` 1980-01-02 · `USDJPY=X` | **`DX-Y.NYB`**, `UUP`, `DX=F` |
| Öl / Rohstoff | `CL=F` 2000-08-23 · `USO` · `XLE` · `GLD` 2004-11-18 · `SLV`, `GC=F` | `BNO`, `DBC` |
| Ziele | `SPY` 1993-01-29 · `QQQ` 1999-03-10 · `DIA` 1998-01-20 · `IWM`, `^GSPC` 1980 | — |
| Breite | nur Proxys (`RSP` 2003-05-01, `MAGS`, Sektor-ETFs) | echte A/D, Hoch/Tief-Zählung, Up/Down-Volumen |

**Korrigiert am 2026-10-24:** VVIX und SKEW stehen nicht im Ticker-Universum, sind aber
mit voller Historie verfügbar und werden auf `/skew` längst angezeigt —
`_index_series` (`scripts/compute_options_skew.py:239`) holt sie mit `period="max"` und
schneidet erst danach auf 504 Tage. „Nicht onboardet" ist nicht „nicht verfügbar"; dieser
Fehlschluss ist mir an einem Tag zweimal passiert.

**Wirklich nur ein Einzelwert** sind die Korrelationsindizes: `^COR1M` liefert eine Zeile,
der Cron akkumuliert vorwärts (`__CORR`) und hat am 2026-10-22 **30 Beobachtungen ab
2026-09-04**. Für eine Studie auf Markttiefs sind das null Ereignisse.

**52-Wochen-Hoch/Tief gibt es nicht als Feld**, ist aber je Ticker aus `prices`
rechenbar. Über unser Universum aggregiert wäre es eine Breitenkennzahl — mit
Survivorship-Verzerrung, deren Richtung bekannt ist: heute gelistete Titel haben
Krisen überlebt, die Zählung untertreibt Furcht gerade am Tief.

## 3 Die Zahl, an der alles hängt: wie viele Tiefs gibt es?

Gemessen (Schlusskurse, lokales Minimum über ±k Sitzungen, zusätzlich mit
Rückgangsschwelle vom 252-Tage-Hoch):

| Ziel | Zeitraum | Sitzungen | ±5 lokal / ≥5 % / ≥10 % | ±20 lokal / ≥5 % / ≥10 % | ±60 lokal / ≥5 % / ≥10 % |
|---|---|---|---|---|---|
| SPY | ab 1993 | 8491 | 520 / 222 / 124 | 135 / 82 / 40 | 38 / 37 / 20 |
| SPY | ab 2007 | 4922 | 302 / 132 / 77 | 75 / 46 / 23 | 21 / 20 / 12 |
| QQQ | ab 2007 | 4922 | 288 / 150 / 87 | 68 / 60 / 36 | 27 / 26 / 21 |
| DIA | ab 2007 | 4922 | 295 / 129 / 62 | 75 / 48 / 22 | 26 / 23 / 12 |

**Der gemeinsame Zeitraum aller Kandidaten beginnt am 2007-05-10** — die Bindung ist
`^OVX`, davor `HYG` (2007-04-12). Das sind 4895 Sitzungen, und darin:

* mittelfristige Tiefs (±20, Rückgang ≥ 5 %): **46**
* ernste Tiefs (±20, ≥ 10 %): **23**
* große Tiefs (±60, ≥ 10 %): **12**

**Das ist das Kernproblem des Vorhabens, und ich will es vor jeder Methodik benannt
haben:** bei 12 bis 46 Ereignissen lässt sich keine Kombination aus zehn Indikatoren
prüfen. Allein die Paare aus zehn Indikatoren sind 45, die Dreier 120; mit
Schwellenwahl je Indikator vervielfacht sich das. Die Intermarket-Matrix hat bei 470
Tests **null** bestätigte Befunde geliefert — und die hatte mehr Ereignisse je Zelle.

Wer Öl-Vola und Kredit weglässt, kommt auf 1993 zurück (82 mittelfristige Tiefs) oder
mit VIX allein auf 1990. Die Tiefe der Historie und die Breite des Indikatorensatzes
sind also direkt gegeneinander zu tauschen, und diese Entscheidung gehört vor den ersten
Lauf.

## 4 Was „Markttief anzeigen" überhaupt heißt — mein Haupteinwand

Ein Tief nach ±k Sitzungen ist eine **rückblickende Beschriftung**: man weiß erst k
Sitzungen später, dass es eines war. Eine Studie „zeigt Indikator X Tiefs an?" misst
damit etwas, das niemand handeln kann, und sie ist anfällig für genau die Verwechslung,
die das Projekt bei der Crash-Ampel schon getroffen hat (dort war das Vorzeichen
vertauscht und fiel monatelang nicht auf).

Mein Vorschlag, der daraus folgt: **die Zielgröße ist die Vorwärtsrendite, nicht die
Tiefmarkierung.** Also: wenn der Indikator heute einen Zustand zeigt, wie fällt die
Rendite über 5, 20 und 60 Sitzungen aus, gegen die Basisrate desselben Zeitraums? Die
Tiefbeschriftung läuft als **beschreibende** zweite Spalte mit („wie oft lag ein lokales
Tief innerhalb von ±5 Sitzungen nach dem Signal"), ohne p-Wert und ohne Behauptung.

Daran hängt auch die Erholungsfalle: der Anleihen-Befund aus `docs/INTERMARKET.md` war
ein **Erholungsmuster**, kein Blick in die Zukunft — der SPY war vor dem Ereignis im
Median 1,31 % gefallen. Jede Signalkennzahl, die auf Stress reagiert, hat diese
Eigenschaft. Der Vorlauf gehört deshalb ins Bild und in die Tabelle.

## 5 Indikatoren mit Rechenvorschrift (Vorschlag)

Alle als **Rang gegen die eigene Vergangenheit** (expandierendes Perzentil, kein
Look-ahead), Mechanik wie `shared/stress_score.py`: Rang gegen bis zu 2520
vorangegangene Sitzungen, Mindestreferenz, Mittelrang bei Gleichstand.

1. **VIX-Niveau** — Perzentil.
2. **VIX-Term** — `^VIX / ^VIX3M`; Backwardation ist der eigentliche Stressanzeiger.
3. **VIX-Schock** — Veränderung über 5 Sitzungen in Punkten und relativ.
4. **VVIX** (nach Onboarding) — Vola der Vola; Perzentil.
5. **SKEW** (nach Onboarding) — Perzentil; Vorbehalt: SKEW ist bei Cboe
   konstruktionsbedingt träge und steigt oft VOR ruhigen Phasen.
6. **Kreditspanne als Kursverhältnis** — `HYG / IEF`, Veränderung über 20 Sitzungen.
   Ausdrücklich **kein** Spread (wir haben keine Renditen) und darf nicht so heißen.
7. **Fluchtbewegung** — `TLT`-Rendite minus `SPY`-Rendite über 20 Sitzungen.
8. **Dollar** — `EURUSD=X` invertiert, 20-Sitzungs-Änderung, als Behelf bis ein echter
   Dollar-Index onboardet ist.
9. **Öl** — `CL=F` 20-Sitzungs-Änderung und `^OVX`-Perzentil.
10. **Breite (Proxy)** — `RSP / SPY` über 20 Sitzungen (gleichgewichtet gegen
    kapitalgewichtet) und Anteil unserer Ticker unter ihrem 200-Tage-Durchschnitt.
    **Mit benannter Survivorship-Verzerrung.**
11. **Eigener Stress-Score** als Vergleichsmaßstab — nicht als Kandidat, sondern als
    Messlatte: ein neuer Indikator muss ihn schlagen, sonst ist er überflüssig.

Weitere, die der Nutzer nicht genannt hat und die ich für prüfenswert halte:
**Gold/SPY** (Fluchtbewegung ohne Zinskomponente), **XLU/SPY** (defensive Rotation),
**SMH/SPY** (Risikoappetit), **Korrelation der Sektoren untereinander** (steigt im
Stress), **Anteil der Ticker mit 20-Tage-Tief** (Breitenvariante ohne 52-Wochen-Fenster).
Nicht prüfenswert halte ich alles, was dieselbe Größe in anderem Fenster wiederholt —
davon haben wir schon genug.

## 6 Studienprotokoll (Vorschlag, bevor eine Zeile Code entsteht)

In der Form, die sich bei der Williams-Studie bewährt hat:

* **Familie vorab festlegen.** Mein Vorschlag: höchstens **12 Einzelindikatoren** und
  **keine automatische Kombinationssuche**. Kombinationen nur dort, wo es eine Begründung
  VOR dem Blick auf die Daten gibt (etwa „Vola hoch UND Breite schwach").
* **Schwellen nicht optimieren.** Je Indikator genau drei vorab gesetzte Perzentile
  (80/90/95 bzw. 20/10/5), keine Feinsuche.
* **Entdeckung 2007–2019, Prüfung 2020–2026**, der Prüfzeitraum wird **einmal** gelesen.
* **Holm-Korrektur** über die Familie, Fallzahl an jeder Zahl.
* **Vorlauf ausweisen** (Abschnitt 4).
* **Abbruchkriterien vorab:** weniger als 20 Ereignisse je Zelle → nicht ausgewertet;
  Vorzeichenwechsel zwischen den Zeitraumhälften → verworfen; kein Indikator schlägt den
  bestehenden Stress-Score → das Ergebnis lautet „nichts Neues" und wird so
  veröffentlicht.

## 7 Fragen an den Prüfer

1. **Trägt Abschnitt 4?** Ist die Vorwärtsrendite die richtige Zielgröße, oder verliert
   man damit genau das, was der Nutzer sehen will („hier war das Tief")? Gibt es eine
   Formulierung, die beides leistet, ohne eine rückblickende Beschriftung in eine
   Prognose zu verwandeln?
2. **Reicht die Fallzahl überhaupt?** Bei 46 mittelfristigen Tiefs im gemeinsamen
   Zeitraum: ist eine Studie mit 12 Indikatoren und drei Schwellen schon zu groß? Welche
   Obergrenze würdest du setzen, und woran leitest du sie ab?
3. **Historie gegen Breite:** 1990 mit VIX allein, 2002 mit Anleihen, 2007 mit allem.
   Was ist die bessere Wahl, und sollte man beide rechnen und als getrennte Studien
   ausweisen?
4. **Die Breiten-Proxys** (`RSP/SPY`, Anteil unter dem 200-Tage-Durchschnitt aus unserem
   Universum): tragen sie, oder ist die Survivorship-Verzerrung so groß, dass sie am Tief
   — also genau dort, wo es zählt — in die falsche Richtung zeigen? Wie würdest du das
   messen, ohne die echte Reihe zu haben?
5. **SKEW:** der Nutzer nennt ihn mit Nachdruck. Was ist über seine Eignung als
   Stressanzeiger belegt, und was ist Folklore? Wenn er träge ist und vor ruhigen Phasen
   steigt — wie prüft man das, statt es zu behaupten?
6. **Was fehlt in Abschnitt 5?** Welcher Indikator mit belegbarer Eignung ist nicht
   dabei, und welcher der genannten würde dir zuerst herausfallen?
7. **Der Vergleich mit dem Stress-Score** als Abbruchkriterium: ist das die richtige
   Messlatte, oder müsste die Messlatte etwas Einfacheres sein (etwa „VIX-Perzentil
   allein")?


## 8 Stand nach zwei Codex-Runden und der korrigierten Messung (2026-10-24)

Fenster **t+1..t+x** (ohne den Signaltag), strikte Extrema über ±10, Basisrate derselben
Tagesmenge, Rang über 252 Sitzungen, Einstieg Schluss t+1. Deskriptiv, ganze Stichprobe,
keine Korrektur, keine Teilung — und mit **Vorbefassung**: diese Zahlen sind vor jedem
Einfrieren gesehen worden.

### 8.1 Was die Korrektur überlebt

| Regel | Eintritte SPY/QQQ/DIA | Tief in 10 Sitzungen (Pp über Basis) | Rendite 20 T. (Pp) |
|---|---|---|---|
| VIX-Rang ≥ 90 | 240 / 167 / 173 | +19 / +17 / +24 | +0,41 / +0,33 / +0,41 |
| RSI ≤ 30 | 169 / 144 / 160 | +19 / +19 / +24 | +0,70 / +0,18 / +0,72 |
| VIX ≥ 90 **und** RSI ≤ 30 | 104 / 70 / 83 | +20 / +18 / +29 | +0,88 / **−0,89** / +1,50 |
| RSI-Tempo 5 T. ≤ 5. Perzentil | 212 / 172 / 177 | +15 / −0 / +13 | +0,38 / −0,43 / −0,08 |
| RSI 70 → 30 binnen 10 T. | 26 / 19 / 33 | +13 / +23 / +35 | −0,20 / −3,24 / +1,10 |
| SKEW-Rang ≥ 90 | 380 / 300 / 319 | **−6 / −5 / −7** | −0,68 / −0,78 / −0,59 |
| VIX ≤ 10 | 336 / 291 / 297 | Hoch in 10: +2 / +3 / +3 | −0,32 / −0,14 / −0,40 |
| RSI ≥ 70 | 367 / 303 / 298 | Hoch in 10: +2 / −1 / +7 | −0,29 / −0,10 / −0,26 |

Basisrate SPY: Tief in 10 Sitzungen 29,5 %, Hoch 26,7 %.

### 8.2 Vier Schlüsse

1. **VIX- und RSI-Extreme markieren Tiefs messbar häufiger**, gleichgerichtet über alle
   drei ETFs, mit 83 bis 240 Episoden.
2. **Eine Renditekante gibt es nicht** — und die Kombination wechselt zwischen den
   Zielmärkten das Vorzeichen, nach unseren eigenen Abbruchkriterien ein Verwerfungsgrund.
3. **SKEW ist kein Tiefanzeiger** (unter der Basisrate), als Hochanzeiger schwach, und als
   UND-Filter verschlechtert er VIX.
4. **Die Hochseite trägt nicht.** Teststärke bei Kontrollrate 30 %: +10 Pp braucht 336
   Episoden, +5 Pp braucht 1 310. Gemessen sind +2 bis +8 Pp. Prospektiv ergeben 368
   RSI-Eintritte in 33 Jahren etwa 55 in fünf Jahren — 3 % Teststärke bei +5 Pp, 12 % bei
   +10 Pp.

### 8.3 Die Tiefseite trägt nur retrospektiv

Für +20 Pp braucht es 90 Episoden; historisch sind 240 bzw. 169 vorhanden. **Prospektiv**
sind es rund 36 bzw. 25 in fünf Jahren — 34 % bzw. 22 % Teststärke selbst bei +20 Pp. Eine
Vorwärtsbestätigung dauert Jahrzehnte.

### 8.4 Offene Nutzerentscheidung

1. **Beschreibend veröffentlichen** mit offengelegter Vorbefassung (Empfehlung).
2. **Jetzt einfrieren und prospektiv prüfen**, mit der Erwartung, lange unentschieden zu
   bleiben.
3. **Beenden**, die Messung bleibt als Notiz.

Nicht empfohlen: die 324 Hypothesen rechnen und das Ergebnis als Befund ausgeben.
