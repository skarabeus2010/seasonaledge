# Ticker schneller laden — Migration Schritt 2: lokale Lader, Dashboard-Overnight, Embed + Lader-Änderung VORLADEN

Plan [docs/TICKER_LADEN.md](../TICKER_LADEN.md). Schritt 1 live (`a19f3f0`, [Freigabe](2026-10-10_ticker_laden_m1_antwort2.md)).
Read-only, nichts schreiben, Mutationstests NICHT ausführen. Änderungen: `git diff` (Arbeitsbaum).

<task>Prüfe Schritt 2 auf Rückgabe- und Anzeigeänderungen je Seite, die nicht beabsichtigt sind, und die
Lader-Änderung VORLADEN. Freigabe für den Deploy?</task>

## Seiten
Zehn lokale Lader (Offset + `count=exact`, nacheinander, **ohne HTTP-/Array-Prüfung** — ein Fehlerkörper wurde als
„Zeile" angehängt) sind ersetzt durch `SA.kurse.zeilen(ticker, {felder, ab: SA.kurse.abAusFilter(filter)})` mit
denselben Feldern und Grenzen: jahreszyklus, ki-saisonalitaet, risikozyklus (date,close,log_return), opex,
vixpiration, spot-vol-beta (date,close), overnight, tdom-analyse (date,open,close,tdom,tdoy), wochentage,
backtest-engine (date,open,close); dazu `embed.html` (eigener Lader, bindet jetzt `kurse.js` ein) und
Dashboard-Overnight (vorher EIN Abruf **ohne Pagination** = nur die ersten 1000 Zeilen, ohne Fehlerprüfung).
`abAusFilter`: `''`/`undefined` → `null`, `&date=gte.YYYY-MM-DD` → Datum, sonst Durchreichen → Ablehnung in `laden`.
Alle Aufrufstellen haben einen `catch`; fünf Seiten ohne Abrufkennung (wochentage, backtest-engine, opex,
vixpiration, spot-vol-beta) bekommen sie in einem eigenen Schritt danach.

## Lader-Änderung VORLADEN (`kurse.js`)
Gemessen in der Seitenprobe: nach Schritt 2 brauchte das Dashboard **44** Anfragen (alt 36, Schritt 1: 27), weil
Overnight `open` braucht und die gemeinsame Ladung es nicht hatte → zweite Vollladung. Jetzt holt jede gemeinsame
Ladung (`starte`) mindestens `VORLADEN = date, open, close, log_return, tdom, tdoy`; die Sicht bleibt exakt der
angeforderte Feldsatz. Kosten ~12 % Bytes. Dashboard danach **26** Anfragen. Folge für den Rückfall (M1 R1): er
greift jetzt nur, wenn die gescheiterte Ladung einen **größeren Zeitraum** hatte (`b.ab` früher bzw. `null`
gegen Datum), nicht bei bloß zusätzlichen Spalten. Eigene Ladung (`eigeneLadung`) bleibt exakt der Bedarf.

## Nachweise
- `verify_kurse.py`: Lader 122 Prüfungen (neu 19f: Overnight-Felder aus dem Bestand ohne Anfrage; Testfälle, die
  einen Feldunterschied brauchen, auf `high` umgestellt; kaputte Blöcke tragen jetzt alle VORLADEN-Felder, sonst
  scheiterten sie schon an der Feldprüfung), Hüllen 65/65. Mutationstest **38/38**, fünf Gegenproben verworfen.
- `verify_seiten_kurse.py` (Gate): **205/205**. Je Seite die echte HTML + Skripte in jsdom, Vorher = Fixtures
  `scripts/fixtures/kurse_vorher/` (jetzt auch die elf Seiten + `embed.html` wörtlich aus HEAD).
  - `normal`: Anzeige + Chart-Serien vorher = nachher auf allen zwölf.
  - Dashboard: Soll ist der **alte Code auf vollständigen Daten** (Nachbau `--ohne-obergrenze` liefert die
    unpaginierte Overnight-Abfrage ungekürzt) — Anzeige gleich; Gegenbeweis: der alte Stand MIT Kürzung weicht ab.
  - `blockfehler` (ab Block 2 scheitert jede Ladung): Soll = Seite zeigt `prices 500`; alt nur berichtet (zeigte
    ihn außer dem Dashboard nirgends — er rechnete mit dem Fehlerkörper als Zeile).
  - Ruhe-Kriterium: keine offene Anfrage 1,5 s UND kein laufender Koordinator (der Lader wartet zwischen
    Wiederholungen ohne offene Anfrage — vorher meldete die Probe dort zu früh „fertig").
  - Kursanfragen normal alt/neu: Dashboard 36/26, alle übrigen gleich (12/12, 13/13 …).

## Fokusfragen
1. Ist VORLADEN als Vertragsänderung vertretbar (z. B. Seiten, die nur `date,close` brauchen, laden jetzt mehr)?
   Reicht die neue Rückfallregel (nur bei größerem Zeitraum)?
2. Gibt es eine Seite, deren Anzeige sich ungewollt ändert, die die Probe nicht sieht (z. B. Text, der erst
   nach Interaktion erscheint)?
3. Freigabe?

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 40 Zeilen.
