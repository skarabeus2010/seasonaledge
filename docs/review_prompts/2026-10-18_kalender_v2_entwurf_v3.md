# Kalender-Umstellung V2 — Entwurf v3 (Browserkern)

Runde 2: [Entwurf v2](2026-10-18_kalender_v2_entwurf_v2.md) · Antwort (keine Freigabe, 3 × P2; B1/B5/B6/B7
erledigt; Antworten: drei Prüfebenen reichen nach Ergänzung, ein Monat je Börse als Zusatzreferenz ja, Texte in V2
ja, aber ohne Bundle-Spannen). v3 ändert v2 nur hier. Read-only.

<task>Sind die drei Befunde aus Runde 2 erledigt? Ist v1 + v2 + v3 als Bauvorlage freigabefähig?</task>

## Zu den Befunden
**R2-1 — Auslieferungspfad des Converters.** nginx liefert `/tools/` direkt aus `seo/tools/`
(`deploy/nginx.conf:294`, `alias /app/seo/tools/`). Einbindungsvertrag, Releaseprüfung und jsdom-Proben prüfen
deshalb **`seo/tools/trading-day-converter.html` selbst** (nach `release_setzen.py`, d. h. im Zustand, den nginx
ausliefert) und zusätzlich per HTTP-Abruf `/tools/trading-day-converter` nach dem Deploy (Kennung, Skriptreihenfolge).
Kein neuer Build-Schritt; die Bundle-Referenz ist ein absoluter Pfad `/landing/js/boersenkalender.js?v=…`
Der Cache-Buster in `deploy/inject_credentials.sh:81` läuft heute nur über `landing/` — er wird auf
`seo/tools/*.html` erweitert (gleiches `sed`), sonst hinge der Converter nach einem Release an einem alten Bundle.
Alle Verweise auf `seo/output/…` aus v2 entfallen.

**R2-2 — Keine Spannen in den Texten.** Die Erklärkarten/FAQ nennen **keine** Ober- oder Untergrenzen mehr, weder alt
(1–23, 1–252, 365) noch gemessene. Neu, methodenneutral: TDOM „Nummer des Handelstags im Monat — wie viele es gibt,
hängt von Börse und Monat ab; der Rechner zeigt die Summe des gewählten Monats“, TDOY entsprechend für das Jahr,
CDOY „1 bis 365, im Schaltjahr 366“ (arithmetisch, in beiden Methoden richtig). Die Prüfung trennt
**Rechnerausgabe** (Momentaufnahme alt wörtlich / Sollwerte neu) und **freigegebene Textänderung** (Diff gegen
die Momentaufnahme genau auf die genannten Knoten beschränkt, alles andere unverändert).

**R2-3 — Statusfälle vollständig.** Geprüft werden alle Übergänge aus `KALENDER_GUELTIG` (`shared/exchange_holidays.py:474`)
mit Nachbarjahren und die konstanten Fälle, als Literal-Tabelle im Wächter (nicht aus dem Modul gelesen):

| Börse | Fälle (Jahr → Status) |
|---|---|
| NYSE | 1885 u · 1970 u · 1971 b · 2028 b · 2029 a · 2100 a |
| XETRA | 2000 u · 2001 a · 2002 b · 2026 b · 2027 a |
| LSE | 1999 u · 2000 a · 2025 a · 2026 b · 2028 b · 2029 a |
| TSE | 1999 u · 2000 a · 2001 b · 2027 b · 2028 a |
| EURONEXT, SIX, MILAN, STOCKHOLM, OSLO | 1885 u · 1999 u · 2000 a · 2100 a (kein `belegt`) |
| HKEX | 2015 u · 2016 a · 2025 a · 2026 b · 2027 u |
| KRX | 2015 u · 2016 a · 2026 a · 2027 u (kein `belegt`) |
| CRYPTO, FOREX | 1885 k · 2026 k · 2100 k |

(u = ungeprueft, a = annahme, b = belegt, k = konvention.) Header und Converter zeigen je Fall die richtige
Kennzeichnung; ein Wechsel der Tabelle im Modul ohne Wächteränderung wird rot.

## Zu Antwort 1 (Umfang der Sitzungslisten)
Die handgeschriebenen Monatslisten je Börse (v2, B4.2) legen nicht nur Offenheit fest, sondern je Tag des Monats
TDOM, Rückwärts-TDOM, `offen`, die Monatssumme sowie die Ergebnisse von `nthTradingDay(1..Summe+1)`,
`lastTradingDay(1..Summe+1)` und `nextTradingDay` ab jedem Tag; für TDOY je Liste der Wert am Monatsersten (aus dem
veröffentlichten Jahreskalender abgezählt, Quelle notiert). CRYPTO/FOREX: die Konvention ist die Referenz
(jeder Tag bzw. Mo–Fr, ausdrücklich so benannt).

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2, nur neue oder offene) · **Auflagen**. ≤ 20 Zeilen.
