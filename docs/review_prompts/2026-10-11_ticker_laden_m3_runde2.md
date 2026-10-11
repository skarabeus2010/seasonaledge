# Ticker schneller laden — Schritt 3, Runde 2

Runde 1: [Prompt](2026-10-11_ticker_laden_m3.md) · [Antwort](2026-10-11_ticker_laden_m3_antwort1.md) (keine Freigabe).
Read-only, nichts schreiben, Mutationstests NICHT ausführen.

<task>Prüfe die drei Auflagen aus Runde 1. Freigabe für den Deploy von Schritt 3?</task>

## Umsetzung
1. **Rückwechsel** (wochentage, backtest-engine): der Gleichheits-Return VOR der Kennung ist ersetzt durch die
   zweistellige Form `var _lk = SA.ladeKennung.start(ticker, <getCurrentTicker>); if (_lk === null) return;` —
   derselbe angezeigte Ticker ohne laufenden Abruf tut nichts, A → B → A entwertet B.
2. **Dashboard-Darstellung**: Zähler `_darstellung` (jedes `renderAll`, auch der Zeitraum-Regler), Overnight prüft in
   Erfolg UND Fehler `SA.ladeKennung.aktuell(_rk) && _dn === _darstellung`.
3. **Seitenprobe**: jeder verglichene Lauf (neu und Soll) muss Ruhe, keine Seitenfehler, vollständige Anzeige und
   gefüllte Charts haben (Funktion `vollstaendig`). Neue Fälle: `rueckwechsel` (A langsam → zurück zum
   Start-Ticker, Soll = „normal") auf wochentage/backtest-engine; `zeitraum` (Dashboard, 16 min später scheitern die
   ganze Historie und die 30-J-Grenze langsam; 30 → sofort 5 Jahre, Soll = „nur 5 Jahre").

## Ergebnisse
`verify_seiten_kurse.py` **313/313**. Alter Stand (berichtet): in allen neun Wechselfällen überschrieb die verspätete
Antwort die neuere Ansicht (dashboard wechsel/zeitraum, wochentage + backtest-engine wechsel/rueckwechsel, opex,
vixpiration, spot-vol-beta). Gegenproben von Hand: ohne `_dn !== _darstellung` → zeitraum ≠ zeitraum_direkt; mit dem
alten Gleichheits-Return auf wochentage → rueckwechsel ≠ normal.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 25 Zeilen.
