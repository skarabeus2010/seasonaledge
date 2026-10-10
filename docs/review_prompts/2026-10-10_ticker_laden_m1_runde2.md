# Ticker schneller laden — Migration Schritt 1, Runde 2

Runde 1: [Prompt](2026-10-10_ticker_laden_m1.md) · [Antwort](2026-10-10_ticker_laden_m1_antwort1.md) (keine Freigabe).
Read-only, nichts schreiben, Mutationstests NICHT ausführen.

<task>Prüfe, ob die drei Auflagen aus Runde 1 erfüllt sind und Schritt 1 deployt werden kann.</task>

## Auflage 1 — Fehlerkopplungen aufgelöst (`landing/js/kurse.js`, `laden`)
Regel: **eine Anfrage scheitert nur an ihrem eigenen Bedarf.** Hängt sie an einer breiteren gemeinsamen Ladung
(laufend, wartend oder neue Vereinigung mit dem Bestand) und scheitert diese, lädt `eigeneLadung` genau ihren
Bedarf einmal allein — ohne Cache, ohne den Bestand zu ändern, eigene Generation. War die gescheiterte Ladung
genau ihr Bedarf (`deckt(anfrage, b)`), kein zweiter Versuch. Für die wartende Ladung zählt der tatsächlich
gestartete Bedarf (`w.gestartet`), nicht der beim Einreihen.
- Probe Abschnitt 19d (Radar am Saison-Score, Vollladung scheitert → Radar bekommt seine 31 Jahre, Bestand
  unverändert), 19e (TTL-Ablauf, Neuladung des ganzen Bestands scheitert → 30-J-Anfrage gelingt; Anfrage mit genau
  dem gescheiterten Bedarf lehnt ab mit genau EINER Anfrage). Mutationstest jetzt 37/37 (zweimal). Mutationen „kein Rückfall" und „Rückfall auch bei
  genau dem eigenen Bedarf" sind rot.

## Auflage 2 — Seitenprobe der echten Dashboard-Seite (A4)
`scripts/js/probe_seiten_kurse.js` + `scripts/verify_seiten_kurse.py`: die echte `dashboard.html` mit ihren echten
Skripten in **jsdom 25.0.1** (fest in `scripts/perf/package-lock.json`), feste Uhr 2026-10-09 14:00 UTC, Zone
Europe/Berlin, leerer Speicher, deterministische Kurse (^GSPC ab 1960, Mo–Fr), PostgREST-Nachbau mit Range +
`count=exact` (alter Weg) und Keyset (neuer). ApexCharts als Stub, der alle übergebenen Serien aufzeichnet.
Vorher-Stand = aktueller Baum + wörtliche alte `app.js`/`decade-compute.js` (`scripts/fixtures/kurse_vorher/`, aus
`05e6310`), ohne `kurse.js` und dessen Einbindung (kein `git archive`, weil der Deploy nur 2 Commits tief klont).
Fälle **normal · vollfehler** (jede Abfrage ohne Untergrenze → 500) **· ttl** (16 min später scheitert die ganze
Historie, Zeitraum-Regler zeichnet neu). Verlangt je Lauf: Endmarker, Ruhe (Platzhalter „Wird berechnet" weg,
1,5 s ohne Kursanfrage), keine Seitenfehler, Saison-Score/Stress-Ampel/Anomalie-Radar in der Anzeige, ≥ 3 Charts
mit Serien; dann **Anzeige (Text des Inhaltsbereichs) und Chart-Serien vorher = nachher**: 36/36 grün.
Kursanfragen (nur berichtet): normal alt 36 / neu 27, vollfehler 22 / 23, ttl 50 / 42.
**Nachweis, dass sie den Befund fängt:** ohne den Rückfall zeigt sie in vollfehler und ttl genau deinen Fall —
„Basis: 30 Vergleichsjahre (1996–2025)" vorher gegen „29 (1997–2025)" nachher.
Im Deploy-Gate (`npm ci --prefix scripts/perf`, dann der Wächter).

## Auflage 3 — Commit-Umfang
Hüllenprobe, Fixtures (`kurse_alte_lader.js`, `kurse_vorher/`), Seitenprobe, `scripts/perf/package*.json` gehen
in denselben Commit.

## Fokusfragen
1. Ist die Rückfall-Regel richtig (z. B. Doppelte Last bei vielen Verbrauchern im Fehlerfall, oder eine Anfrage,
   die nach dem Rückfall eine ältere Generation als ein späterer Bestand trägt)?
2. Ist die Seitenprobe aussagekräftig genug für Schritt 1 (nur Dashboard; die übrigen 17 `fetchAllPrices`-Seiten
   ändern keinen Seitencode und hängen an der Hüllenprobe)?
3. Freigabe für den Deploy?

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 35 Zeilen.
