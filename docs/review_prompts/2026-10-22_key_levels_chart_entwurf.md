# Entwurf: Kurschart mit Options-Niveaus auf /key-levels (2026-10-22)

**Zu prüfen VOR der ersten Codezeile.** Alle Zahlen unten sind an der laufenden
Produktion gemessen (lesend), nicht geschätzt; die Messbefehle stehen jeweils dabei.

## 1 Anlass

Nutzerwunsch: unter der Tabelle „Key Levels je Ticker" ein Kurschart des **angewählten**
Tickers, mit den Niveaus als waagerechten Linien — Vol-Trigger, Max Pain, Call Wall,
Put Wall. Offene Frage des Nutzers: „ob wir auch die historischen Call- und Put-Walls
einzeichnen können, das weiß ich nicht."

Dazu zwei Nutzerentscheidungen vom 2026-10-22:

1. Die 51 Altsessions **sollen** mit eingelesen werden, mit sichtbarer Kennzeichnung.
2. Die Tabelle soll **scrollbar** werden und in Schritt 1 **30 Ticker** zeigen (heute 11),
   „die größten nach Marketcap inkl. ETFs"; die restlichen in einem späteren Schritt.

## 2 Bestand, gemessen

### 2.1 Aktuelle Niveaus

`landing/data/key_levels.json` (Session 2026-10-21, `gex_status: ok`) trägt je Ticker:
`call_wall`, `put_wall`, `max_pain`, `max_pain_non_unique`, `vol_trigger`, `spot`,
`exp`, `exp_dte`, `regime`, `net_gex_usd_bn`, `pc_oi_ratio`, `top_call_oi[5]`,
`top_put_oi[5]`, `mp_dist_pct`, `vt_dist_pct`, `cats`.

Enthalten sind **11 Ticker** (`CORE_OPTIONS` = SPY, QQQ, IWM, DIA + Mag7).
Alles, was als Linie gezeichnet werden soll, liegt also für die aktuelle Session vor —
**einschließlich des Verfalls**, auf den sich die Walls beziehen.

### 2.2 Historie der Walls — teilweise vorhanden

```
ssh … "cd /opt/seasonaledge/landing/data && ls gex_history/ | wc -l; ls gex_history_session/"
```

| Archiv | Dateien | Stempel | Felder je Ticker |
|---|---|---|---|
| `gex_history/` | 51 (2026-08-03 … 2026-10-14) | **Lauftag**, kein `session`-Feld | call_wall, put_wall, zero_gamma, spot, regime, skew, net_gex, net_vanna, net_charm |
| `gex_history_session/` | 4 (15., 16., 20., 21.10.) | `session`, `stempel_art: "session"` | dieselben |

Daraus folgt dreierlei, und jedes davon ist ein Darstellungsproblem, kein Datenproblem:

- **Max Pain fehlt in der Historie vollständig.** Es entsteht erst in
  `compute_key_levels.py` aus der Optionskette; gespeichert wird nur die aktuelle Datei.
  Rückwirkend ist es **nicht** herstellbar (die rohen Ketten werden nicht archiviert).
  Für eine Max-Pain-Historie gibt es nur den Weg nach vorn.
- **Das Datum der 51 Altsessions ist der Lauftag.** 8 dieser Dateien tragen ein
  Wochenend-Datum (an denen nicht gehandelt wurde) — das sind verschobene
  Freitags-Sessions. Im Zeitraum fehlen 11 Werktage, und zwar fast ausschließlich
  **Montage** (06.08., 26./28./31.08., 07.09., 14.09., 21.09., 28.09., 05.10., 12.10.,
  19.10.): die verspäteten GitHub-Crons liefen nach Mitternacht UTC und stempelten den
  Folgetag. Der 19.10. ist zusätzlich dauerhaft verloren (Yahoo-Abendlücke, v66.25).
- **Kein `exp` im Archiv.** Eine Wall gilt immer für genau einen Verfall. Ohne `exp`
  ist eine durchgezogene Wall-Linie über Wochen mehrdeutig. Gemessen an SPY:

  ```
  13.10. call 785  put 772   15.10. call 780  put 765
  14.10. call 785  put 772   16.10. call 800  put 760   ← Roll, keine Positionsverschiebung
  20.10. call 780  put 760   21.10. call 780  put 760
  ```

  Der Sprung auf 800 am 16.10. ist der Wochenroll. Wer das als Bewegung der
  Dealer-Positionierung liest, liest etwas, das nicht passiert ist.

### 2.3 Die Seite

`landing/pages/key-levels.html` (300 Zeilen) hat den Einstiegspunkt bereits:
`tbl.querySelectorAll('tr[data-tk]')` → `selectTicker(tk)` → rendert heute das
OI-je-Strike-Balkenchart in `#kl-oi-chart`. ApexCharts 4 ist eingebunden,
`baseChart()`/`renderInto()` existieren. Das Kurschart ist eine zweite Kachel am
selben Haken.

### 2.4 Kurse

Alle 11 heutigen und alle 12 unten vorgeschlagenen Ticker stehen in `symbols.py`
(373 Ticker), die Kursreihe kommt über `SA.kurse`. **Nur Tagesdaten** — eine
Intraday-Reihe haben wir nicht.

### 2.5 Laufzeit der Kette

`journalctl -u sa-gex-snapshot.service`: 21.10. **22:15:05 → 22:25:28**, also
**10 min 23 s** für 20 GEX-Ticker + 11 Key-Levels-Ticker; der Snapshot veröffentlichte
um 22:24:08, Key Levels brauchten die restlichen 80 s (≈ 7 s/Ticker, deckt sich mit den
früher gemessenen 77 s). Containerfrist der Unit: 28 min, `TimeoutStartSec` 33 min.

## 3 Was gebaut werden soll

### 3.1 Kurschart mit Niveaus (`#kl-kurs-chart`)

- Tageskerzen des angewählten Tickers aus `SA.kurse`, **Standard 1 Monat** (≈ 21
  Sitzungen), Umschalter 1M / 3M / 6M. *Begründung gegen den Nutzerwunsch „ein paar
  Tage": fünf Tagespunkte tragen keine Achse; die Linien hingen ohne Kontext im Bild.
  Entscheidung des Nutzers steht aus, der Vorschlag ist 1M mit Umschalter.*
- Vier waagerechte Linien aus `key_levels.json`: Call Wall, Put Wall, Max Pain,
  Vol-Trigger, jede mit Wert beschriftet, dazu der Spot als Bezug.
- **Einfarbig Gold mit abgesetzten Strichmustern, kein Grün/Rot.** Eine grüne Put-Wall
  neben einer roten Call-Wall liest sich als Kauf-/Verkaufsmarke; dieselbe Regel, aus der
  auf `/skew`, `/intermarket` und `/index-effekt` die Ampelfarben entfernt wurden.
- Über dem Chart eine Zeile „Niveaus der Session <session>, Verfall <exp> (<exp_dte> T.)".
  Ein Niveau ohne Verfallsangabe wird nicht gezeichnet.
- `max_pain_non_unique: true` → Max-Pain-Linie gestrichelt und als „nicht eindeutig"
  beschriftet (das Feld existiert und wird heute nirgends ausgewertet).

### 3.2 Historische Wall-Linien

- Quelle: neue Datei `landing/data/key_levels_history.json`, geschrieben vom
  bestehenden Kettenlauf unter derselben Sperre wie `key_levels.json`, eine Zeile je
  **Ticker und Session** mit `session`, `exp`, `call_wall`, `put_wall`, `vol_trigger`,
  `max_pain`, `spot`, `quelle` (`"session"` | `"lauftag"`).
- **Einmaliger Backfill** der 51 Altsessions und der 4 Session-Dateien aus den
  GEX-Archiven, `quelle: "lauftag"` für alles vor dem 15.10., `max_pain: null`,
  `exp: null`.
- Darstellung als **Stufenlinie** (`curve: 'stepline'`) — die Walls sind
  strikequantisiert und springen am Verfallsroll; eine interpolierte Linie behauptet
  Zwischenwerte, die es nie gab.
- Fehlende Sessions bleiben `null` (Lücke im Pfad), werden **nicht** überbrückt.
- Werte mit `quelle: "lauftag"` werden sichtbar abgesetzt (geringere Deckkraft) und in
  der Legende benannt: „vor dem 15.10. ist das Datum der Lauftag, nicht die Session".
- Wo `exp` vorliegt, markiert ein senkrechter Strich den Verfallswechsel.

### 3.3 Tabelle: scrollbar, 30 Ticker

- `max-height` mit `overflow-y: auto`, Kopfzeile fixiert (wie auf `/skew` nach v66.22).
- Das Universum wächst von 11 auf 30. Die Ticker-Auswahl ist die **einzige offene
  Sachfrage**, siehe 4.1.
- Vor der Umstellung muss die Kettenlaufzeit gegen die 28-min-Frist gemessen werden:
  Hochrechnung aus 2.5 ergibt GEX 30 × 27 s ≈ 13,5 min und Key Levels 30 × 7 s ≈ 3,5 min,
  zusammen ≈ 17 min. Das passt, aber die Reserve sinkt von 18 auf 11 min — der
  Trockenlauf gehört vor den Deploy, nicht danach.
- **Für die 10–12 neuen Ticker gibt es keine Wall-Historie** (das GEX-Archiv kennt nur
  seine 20). Ihre historischen Linien bleiben leer, mit Grund an der Kachel.

## 4 Offene Entscheidung

### 4.1 Auswahlregel der 30 Ticker

Der Nutzer wünscht „die größten nach Marketcap inkl. ETFs". Dagegen spricht ein
Sachargument und eine Messung:

- **Marketcap haben wir nicht als Daten.** Es gibt kein Feld dafür; eine solche Liste
  wäre mein Gedächtnis, nicht unsere Messung — und bei ETFs müsste man sie ohnehin durch
  AUM ersetzen, was eine andere Größe ist.
- **Auf einer Options-Seite sagt die Marktkapitalisierung nichts über die Aussagekraft
  einer Wall.** Eine Wall ist nur dort ein Niveau, wo Open Interest liegt. Gemessen am
  Frontverfall (`options_skew.json`, 163 Ticker, Session 21.10.), Rangsumme aus Open
  Interest und Volumen, Top 30:

  ```
   1 SPY    2 QQQ    3 IWM    4 NVDA   5 AAPL   6 TSLA   7 TLT    8 AMZN
   9 IBIT  10 HYG   11 CRWV  12 NFLX  13 INTC  14 GOOGL 15 META  16 XLF
  17 GLD   18 MSFT  19 MU    20 SLV   21 SMH   22 AMD   23 XLE   24 ORCL
  25 PLTR  26 AVGO  27 SMCI  28 KRE   29 IREN  30 ETHA
  ```

  HYG liegt nach Open Interest auf Platz **4** (8,76 Mio Kontrakte, mehr als IWM),
  TLT auf Platz 2 — beide wären in einer Marketcap-Liste gar nicht dabei, und ihre Walls
  gehören zu den meistbeachteten überhaupt. Umgekehrt sind die nächsten Werte nach
  Marktkapitalisierung (LLY, JPM, V, WMT, XOM, UNH, MA, COST, BRK.B) im Optionsvolumen
  Mittelfeld.

**Vorschlag:** die heutigen 20 GEX-Ticker behalten (DIA und XLK liegen auf OI-Rang 57
bzw. 66, werden aber heute schon angezeigt — ein sichtbares Feature wird nicht ohne
Nutzerentscheidung abgeschaltet) und um die 10 liquidesten neuen ergänzen:
HYG, CRWV, NFLX, INTC, MU, AMD, ORCL, PLTR, AVGO, SMCI. Alle zehn haben Kursreihen.

## 5 Fragen an den Prüfer

1. Ist der Datenvertrag der neuen Historiendatei vollständig, oder fehlt ein Feld, ohne
   das eine Zeile in drei Monaten nicht mehr interpretierbar ist? Insbesondere: genügt
   `quelle` als Kennzeichnung, oder braucht es den Lauf-Zeitstempel dazu?
2. Der Backfill liest zwei Archive mit unterschiedlichem Schema. Welche Fälle übersehe
   ich — doppelte Daten, Wochenend-Stempel, ein Ticker, der nur in einem der beiden
   Archive vorkommt, eine Session mit 20 statt 11 Tickern?
3. Ist die Stufenlinie mit abgesetzter Deckkraft eine ausreichende Kennzeichnung für
   Werte, deren Datum der Lauftag ist, oder behauptet das Chart damit weiterhin zu viel?
   Gibt es eine Darstellung, die weniger behauptet, ohne nutzlos zu werden?
4. Die Niveaus gelten für einen Verfall, der Kurschart-Zeitraum umfasst mehrere. Reicht
   die Kopfzeile mit `exp`, oder muss die Linie räumlich auf ihren Verfallszeitraum
   begrenzt werden?
5. Trägt die Laufzeit-Hochrechnung in 3.3? Welche Messung würde sie belegen, bevor das
   Universum umgestellt wird — und was passiert, wenn die Kette doch in die
   Containerfrist läuft (heute: harter Abbruch, Session ohne Snapshot)?
6. Die Erweiterung auf 30 Ticker betrifft `snapshot_gex.UNIVERSE` **und**
   `CORE_OPTIONS`. Welche anderen Verbraucher hängen an diesen beiden Listen, und
   welche Nebenwirkung übersehe ich dort?
7. Wo würde dieses Vorhaben ohne Wächter still falsch werden — welche drei Prüfungen
   wären die wirksamsten?
