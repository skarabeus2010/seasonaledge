# Neue Ticker schneller laden — Plan v4 (Runde 4): Ergänzungen zu v3

Basis: [v3](2026-10-10_ticker_laden_plan_v3.md) gilt weiter; [Antwort 3](2026-10-10_ticker_laden_plan_antwort3.md)
(6 Befunde, 5 Auflagen). v4 ändert nur die genannten Stellen. Read-only.

<task>Prüfe, ob v3 + v4 als Bauplan freigegeben werden kann.</task>

## Änderungen
**A1 S0 fair messen (Befunde 1, 5).** Kein JS-Abfang mehr. Vorher und nachher werden **identisch** gemessen: je
Variante ein lokaler nginx-Container mit der Repo-`deploy/nginx.conf` (gleiche Routen, gzip, Cache-Header),
`landing/` aus dem jeweiligen Git-Stand (vorher = Commit vor S1, nachher = Kandidat, vollständiges HTML inkl.
Inline-Code und Script-Liste), beide gegen dieselbe Live-Supabase. Ablauf je Messzelle abwechselnd A/B, gleicher
Ausgangszustand: neuer Browserkontext (kalt) bzw. definiert vorbelegter localStorage und HTTP-Cache (warm), kein
`page.route`. Kursinhalt: jede Messzelle zeichnet Zeilenzahl und sha256 der empfangenen Kurszeilen auf; nur
Zellen mit gleichem Inhalt A/B zählen (Datenstand kann sich während der Messung ändern). Ergebnis Messbericht,
kein Gate.

**A2 Generation an die Rückgabe binden (Befund 3).** `SA.kurse.laden` liefert `{zeilen, generation, abdeckungAb,
geladenUm}`; `generation` ist ein über den Seitenlebenszyklus **monoton steigender** Zähler (global, nicht je
Ticker), wird nie wiederverwendet — auch nicht nach LRU-Verdrängung. Verbraucher-Ergebniscaches verwenden
`ticker|generation|eigene Parameter` als Schlüssel. LRU verdrängt **keinen** Koordinator mit laufender oder
wartender Ladung (nur ruhende). Erreichbare Konkurrenzfälle, die die Probe abdeckt: (a) Anfrage B kommt während
laufender Ladung A mit größerem Bedarf → wartet, Vereinigung lädt danach; (b) Ladung A scheitert, wartende B
startet trotzdem und kann erfolgreich sein; (c) TTL läuft während laufender Ladung ab; (d) zwei Seitenteile
fragen gleichzeitig denselben Bedarf → ein Netzaufruf. Den Fall „vertauschte Abschlussreihenfolge“ gibt es bei
einer seriellen Ladung je Ticker nicht → gestrichen.

**A3 Embed (Befund 4).** `landing/embed.html` (eigener Lader, Z. 89) kommt in die Migration; seine
Funktionsprobe prüft 1500-Zeilen-Fixture vollständig. Der Bestandswächter gilt für ganz `landing/` einschließlich
`embed.html` und `index.html`.

**A4 Abnahme über den echten Seitenpfad (Befund 2).** Neue Probe `scripts/js/probe_seiten_kurse.js`: je migrierter
Seite (27 + Embed) wird die **echte HTML-Seite** in jsdom (fest versioniert unter `scripts/perf/`) geladen, mit
ihren echten Skripten (aus `<script src>` aufgelöst, lokale Dateien), `fetch` gestubbt mit PostgREST-Fixtures
(SPY-artig 8 482 Zeilen, BTC 4 407, CRWV kurz) — ApexCharts durch einen Stub, der die übergebenen Serien
mitschreibt. Geprüft: (1) die abgefragten URLs (Tabelle, Felder, Grenze) == die Ladeparameter vor der Migration
(aus der Bestandsaufnahme, wörtlich im Wächter); (2) die an die Charts übergebenen Serien und die sichtbaren
Kennzahlen (Element-Texte) **vor/nach identisch** — vorher-Werte werden mit dem alten Stand derselben Probe
erzeugt und als Fixture festgeschrieben; Ausnahmen nur für die drei beabsichtigten Korrekturen (Overnight-
Pagination, Fehlerprüfung, O1) mit eigenem, unabhängig hergeleitetem Soll; (3) verspäteter Erfolg/Fehler eines
alten Tickers zeichnet nicht (Abrufkennung); (4) TTL-Ablauf lädt neu; (5) DE- und EN-Seite (aus `build_en.py`)
binden `kurse.js` ein. Seiten, die jsdom nicht tragen (z. B. wegen Canvas), werden einzeln mit Begründung als
„nur Funktionsprobe im Browser“ geführt.

**A5 Cursor muss fortschreiten (Befund 6).** Jeder Block: alle Daten gültige ISO-Daten, streng aufsteigend
innerhalb des Blocks, erstes Datum > Cursor des Vorblocks; sonst Ablehnung ohne Veröffentlichung. Zusätzlich
Obergrenze der Blockzahl je Ladung (Zeilen-Obergrenze 60 000 → 61 Blöcke) gegen Endlosschleifen.

## Fokusfragen
1. Reichen A1–A5 für eine Freigabe als Bauplan? 2. A4: ist jsdom mit echten Seiten realistisch (Anzahl Seiten,
Abhängigkeiten wie ApexCharts, Supabase-Auth, `loadComponent`)? Falls nein, welche minimale Alternative prüft den
echten Ladepfad? 3. Sonst etwas?

## Ausgabevertrag
**Urteil** · **Antworten** · **Befunde** · **Auflagen**. ≤ 50 Zeilen.
