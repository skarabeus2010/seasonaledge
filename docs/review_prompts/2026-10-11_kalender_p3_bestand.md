# Tage nach Börsenkalender — P3 Bestandsaufnahme: welche veröffentlichten Zahlen hängen an den Tagesnummern?

Plan: [v3 Runde-2-Abschnitt](2026-10-10_xetra_tdoy_plan_v3.md) (P2–P4 hinter Methodengeneration, veröffentlichte
Zahlen vorher eingefroren nachrechnen und dem Nutzer vorlegen), [v7](2026-10-10_xetra_tdoy_plan_v7.md).
Stand: P1a/P1b/P2 live — `shared/exchange_holidays.handelstag_nummern`, `landing/js/boersenkalender.js` (isoliert),
alle Schreiber setzen `prices.tdom/tdoy` ab jetzt nach Börsenkalender (die Historie noch nicht, das ist P5).
Read-only, nichts schreiben.

<task>Bestandsaufnahme für P3/P4: Erstelle eine vollständige Liste aller VERÖFFENTLICHTEN Zahlen (Blogartikel
DE+EN unter `blog/posts`, statische Seitentexte, Newsletter-Texte, die eine konkrete Zahl nennen), deren Rechnung
von einer Handelstag-Nummer oder dem Feiertagskalender abhängt — TDOM, TDOY, Turn-of-Month, n-ter Handelstag,
OPEX/VIXpiration, Monatswechsel-Fenster, Strategien wie Monthly 10 / Down-Month-ToM-Reversal / UHTS.</task>

Je Zahl bitte:
1. **Fundstelle** (Datei:Zeile, Wortlaut kurz), DE und EN getrennt.
2. **Rechenweg**: welche Funktion erzeugt sie (Python: `tdom_analysis`, `plain_vanilla`, `cache_manager`
   tdom/tdoy_stats, …; JS: `strategy-compute.js`, `holidays.js`, `seasonal-compute.js` …), und **woher die Nummer
   kommt**: (a) DB-Spalte `prices.tdom/tdoy` (Zeilenzählung in der Historie, P5 korrigiert sie), (b) zur Laufzeit
   aus Kurszeilen gezählt, (c) aus dem Feiertagskalender (`holidays.js` / `exchange_holidays`) — und welcher Börse.
3. **Erwartete Wirkung** der Umstellung auf den Börsenkalender: keine (z. B. US-Ticker, NYSE-Kalender schon richtig
   und Zeilen = Handelstage), möglich (XETRA/LSE/TSE/HKEX/KRX, Ticker mit Kurslücken), sicher (benannte Ursache).
4. Ob es einen **eingefrorenen Snapshot** gibt (Muster Wahlen) oder die Zahl aus einem laufenden Datenstand stammt.

Dazu: welche **Seiten** (nicht Blog) zeigen solche Nummern direkt an (Header „TDOM x/y", `/tdom-analyse`,
`/monatswechsel`, `/feiertage`, `/opex`, `/vixpiration`, Dashboard), und welche Statistiktabellen
(`tdom_stats`, `tdoy_stats`) lesen sie.

## Ausgabevertrag
Tabelle(n) + kurze Liste „sicher betroffen" / „möglich" / „nicht betroffen". Keine Bewertung, ob geändert werden
soll — das entscheidet der Nutzer. ≤ 120 Zeilen.
