# Tage nach Börsenkalender — P3/P4: Matrix und Verträge (Codex als Code-Assistent)

Runde 1: [Plan](2026-10-11_kalender_p3p4_plan.md) · [Antwort](2026-10-11_kalender_p3p4_plan_antwort1.md) (nicht tragfähig, 10 Befunde).
Read-only, nichts schreiben. Du arbeitest diesmal als **Mitautor**: dein Text wird die Grundlage von Plan v2.

<task>Liefere zwei Bausteine für Plan v2, beide konkret am Code belegt.</task>

## A — Vollständige Verbraucher-/Erzeugermatrix
Jede Stelle (Python, JS, Seiten, Mails, Kalender/ICS, Blog-Erzeuger, Tools), die eine Handelstag-Nummer, einen
Handelstag-Offset, einen „n-ten Handelstag", ein Ereignis aus dem Feiertagskalender oder eine Ticker→Börse-
Zuordnung verwendet. Je Zeile: Datei:Funktion · was sie liefert · heutige Quelle (Spalte a / Zeilenzählung b /
Kalender c, welcher) · Python-/JS-Zwilling · Paket (P3a… oder neu) · **bewusste Ausnahme** mit Grund (z. B. US-
Verfallstermine bleiben NYSE/Cboe). Gruppiere nach Paket.

## B — Vertragsentwürfe (je ≤ 15 Zeilen, normativ formuliert)
1. **Tagesnummer**: Definition TDOM/TDOY/rückwärts je Börse, geschlossener Tag, Krypto/Forex, Zeitzone des
   „heute", Kalenderstatus `ungeprueft` (zulässig? sichtbar?).
2. **Rendite/Fenster (V4)**: je Renditeart (close→close, open→close, close→open, open→next-open) Endpunkte über
   Kalendersitzungen; fehlender Kurs an offener Sitzung; Füllzeilen; was zählt als Beobachtung; Ausschlusszähler.
3. **Kurve**: Monats-/Jahreskurven über Kalendernummern, Lücken als Unterbrechung, nicht interpoliert.
4. **Ereignis**: stabile Ereigniskennung (Name/Art: Feiertag, Ersatztag, Sonderschließung, Halbtag), Zuordnung
   nicht über Listenposition; t0 bei geschlossener Tickerbörse; US-Verfall (OPEX, VIX nach Cboe) als US-Termin.
5. **Zieltermin** (Newsletter/Dashboard „nächste Sitzung"): tatsächliche nächste Sitzungsdaten je Börse, Monats-
   und Jahresgrenze, geschlossener Zielmarkt.
6. **Statistikgeneration**: `tdom_stats`/`tdoy_stats` mit `methode`, Schlüssel, vollständige Veröffentlichung,
   Leser wählen genau eine Generation, Cache-Fallback, Fehlerfall; Reihenfolge mit P5/P6.
7. **Veröffentlichte Zahlen**: Snapshot-Vertrag je Artikel (Eingang, Adjustierung, Abrufdatum, Stichtag,
   Parameter, Code-/Kalenderversion, Prüfsumme), alt/neu auf identischem Eingang, Kennzeichnung einer Neuberechnung.

## C — Prüfplan
Welche Proben/Wächter (Fixtures kalendergerecht, unabhängige Sollwerte, Zeitzonen, Einbindungswächter statt des
heutigen Isolations-Gates) braucht jedes Paket, und welche Mutationen müssen rot werden.

## Ausgabevertrag
Markdown, gegliedert A/B/C. Keine Bewertung des alten Plans mehr. ≤ 220 Zeilen.
