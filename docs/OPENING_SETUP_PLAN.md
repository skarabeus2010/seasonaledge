# Plan: Bausteine nach dem Vorbild „Opening Setup“ (SpotGamma) — Stand 2026-10-13

Status: **nur Plan, nichts gebaut.** Grundlage: Abgleich unserer Daten vom 12.10.2026 mit dem SpotGamma-Report
„Opening Setup“ vom 13.10.2026 und drei lesende Prüfungen (Zahlenabgleich, Übernahme-Katalog, Datenquellen).
SpotGamma-Inhalte werden nicht übernommen, nur Ideen und Vergleichszahlen.

## 1. Wie plausibel sind unsere Zahlen?

| Größe | Ergebnis | Vergleichbar? |
|---|---|---|
| ATM-IV (1 Monat) | alle 9 gemeinsamen Ticker innerhalb ~1 Vol-Punkt (SPY 12,3 / 12; META 44,3 / 45; MU 47,1 / 46) | ja |
| IV-Rank / -Percentile (1 J.) | meist ≤ 10 Punkte Abstand (META 57/90 gegen 64/86, NVDA 0/0 gegen 7/2) | ja |
| Skew-Rang | **systematisch anders**: SpotGamma hoch (SPY 92, XLF 96, GOOG 85), wir mittig bis tief (SPY 52, XLF 25, GOOGL 8); keine von vier Normierungen kommt heran | nein — deren Definition ist nicht offengelegt; vermutlich andere Laufzeit/Normierung, bei META/GOOGL/MSFT drücken Earnings im 30-T.-Fenster unseren Skew |
| Gamma | wir: Summe SPY+QQQ+IWM+DIA in $, Gesamtvorzeichen negativ; SpotGamma: SPX-Index, normiert, +0,44 | nein; nur SPY allein: Vorzeichen gleich (long), Spot 0,07 % über unserem Zero-Gamma |
| Erwartete Bewegung | 7-Tage-IV als Straddle ergibt für SPY ±1,03 % auf 5 Tage (SG ±1,0 %) | Definition vermutet, nicht belegt |
| Earnings-Move BAC/MS | aus der IV des ersten Verfalls nach dem Termin: ±3,3 % / ±3,8 % (SG ±3,3 / ±3,7) | Rechenweg plausibel; uns fehlen die Termine |

**Fehler in unseren Daten, die dabei auffielen:**
1. **ETHA realisierte Vola 380 % / VRP −333** seit 07.10. — Kurssprung 20,28 → 60,36 am 30.09. (Reverse-Split) wird
   aus `close` in die RV gerechnet; `log_return` ist korrekt. Live sichtbar auf /skew.
2. **IWM** Historienpunkt 17.08. mit ATM-IV 3,35 % (`cm_extrap`) — gehört zum laufenden Vorhaben Skew-Ausreißer.
3. **Datumsstempel** `gex_summary.date`/`pc_ratio.date` = Lauftag (13.10.) statt Session (12.10.).
4. **Briefing-Skew** rechnet das Perzentil über alle History-Zeilen (auch nicht normierte, ab 5 Punkten, bis
   `date.today()`), /skew nur über `cm`/`cm_extrap` ab 20 Punkten zur Session — Zwillingsbruch; dazu Grün/Rot nach
   Vorzeichen (`daily_report.html.j2:115`), /skew ist seit v64 einfarbig.
5. **Earnings im Briefing**: `fetch_event_data.py` speichert das Ende des Geschäftsquartals als „Termin“ und nur
   vergangene Quartale → der Earnings-Teil des Briefings ist leer oder falsch datiert.
6. 16 Ticker ohne normierten Punkt zur Session (korrekt aus dem Ranking, aber z. T. seit Wochen, z. B. DUK, ARRY).

## 2. Lizenzfrage — ✅ erledigt (Nutzer, 2026-10-14)

## 3. Was wir übernehmen — und was nicht

**Übernehmen (beschreibend, ohne Signal):**
- **IV-Dashboard der aktivsten Namen** (ATM-IV, Rank/Percentile, Tagesänderung) — alle Daten da.
- **Block „Vola-Lage“**: VIX, VIX9D, VIX3M (Cboe-CSV/FRED, kostenlos), VIX gegen realisierte SPX-Vola,
  ±1σ-Niveaus für 1 und 5 Tage **mit gemessener historischer Deckung** (n, Intervall), Gamma-Vorzeichen als
  gekennzeichneter Kontext.
- **Earnings-Vorschau**: impliziter Move (erster Verfall nach dem Termin) gegen 8–12 vergangene Reaktionen, alle
  Einzelwerte sichtbar; braucht zuerst eine Terminquelle mit Uhrzeit (vor Börsenbeginn/nach Schluss).
- **Extremlisten** (flachster/steilster Skew, höchstes/niedrigstes IV/RV) — erst nach dem Skew-Ausreißer-Vorhaben.
- **SPX-Gamma über `I:SPX`** — technisch evtl. mit dem jetzigen Abo möglich (ein Testabruf).

**Nicht übernehmen:**
- Sentiment-Score 0–100 mit „erwarteter Rendite 20 T.“ (Gewichte gesetzt, P/C-Historie ~1 Jahr, unvalidiert —
  dieselbe Klasse wie der alte KI-Score).
- Marktthese/Netto-Prämie und Tabelle großer Geschäfte mit Kauf/Verkauf: ohne Quotes (ab Massive Advanced $199) ist die Seite eines Geschäfts nicht messbar; „eröffnend“ nur über Cboe Open-Close (~$2 000/Monat).
- Bull/Bear/Short-Vol-Etiketten (Handelsempfehlungen), BS-„Gewinnwahrscheinlichkeit“ (risikoneutral, keine
  Trefferquote), Ruhig/Normal/Wild aus Gamma (Archiv erst seit 08/2026), „erhöht/im Rahmen“ mit n = 3.
- Kostenlos machbar wäre eine beschreibende Liste „ungewöhnliche Aktivität“ (Volumen/OI + ΔOI am Folgetag, ohne
  Richtung) — später.

## 4. Reihenfolge (jede Stufe mit Codex: Plan → Code → Wächter)
0. ~~Lizenz klären~~ — ✅ erledigt (Nutzer, 2026-10-14).
1. **Bestand reparieren** (S): ETHA-RV aus `log_return` statt `close`; Datumsstempel = Session; Briefing-Skew auf die
   Regel von /skew (eine Rechnung im Cron, Seite und Mail lesen sie) und einfarbig; Earnings-Zeilen im Briefing bis
   zur neuen Quelle ausblenden.
2. **IV-Dashboard** (S–M): Rang/Percentile rechnet der Cron einmal in Python, Briefing + /skew lesen.
3. **Vola-Lage** (M): Datenquellen VIX9D/VIX3M, ±σ-Deckung vorher nach Protokoll messen.
4. **Earnings-Vorschau** (L): Terminquelle prüfen (Yahoo `calendarEvents` / Nasdaq-Kalender, beide inoffiziell;
   Massive-Benzinga Preis offen), `earnings_events` füllen, Reaktion als Residual (nicht Open/Close-Mischung).
5. **Studie** (M–L, nur wenn gewünscht): sagen VIX/RV, VIX3M/VIX, VIX9D-Spitzen etwas über 20-T.-Rendite/-Vola des
   S&P? Vorab festgeschriebenes Protokoll; ein Nullbefund wird veröffentlicht.
6. Nach dem Skew-Ausreißer-Vorhaben: Extremlisten; optional SPX-Gamma.

## 5. Offene Nutzerentscheidungen
- ~~Lizenzklärung mit Massive~~ — ✅ erledigt (2026-10-14).
- Ob Stufe 1 sofort angegangen wird (ETHA-Fehler ist live).
- Welche der Stufen 2–5 überhaupt gewünscht sind.
- Wie der Skew-Rang mit SpotGamma auseinanderliegt, ist eine Definitionsfrage — unsere Rechnung bleibt, bis das
  Skew-Ausreißer-Vorhaben abgeschlossen ist.
