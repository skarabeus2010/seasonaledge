# Tage nach Börsenkalender — Plan P3/P4 v3

Runde 2: [Plan v2](2026-10-11_kalender_p3p4_plan_v2.md) · [Antwort](2026-10-11_kalender_p3p4_plan_v2_antwort.md) (4 Befunde, 5 Auflagen).
A/B/C aus der [Matrix](2026-10-11_kalender_p3p4_matrix_antwort1.md) bleiben verbindlich; v3 ändert nur Folgendes. Read-only.

<task>Prüfe, ob v3 die Auflagen aus Runde 2 erfüllt und als Bauplan freigegeben werden kann.</task>

## 1 Zwei Methoden statt einer
- **Lesermethode** (was Seiten/Mails anzeigen): JS `SA.kalenderMethode`, Python `kalender_methode.LESER`. Wird je
  Berechnung **einmal** gelesen und als Argument an alle Unterfunktionen gereicht (kein erneutes Lesen unterwegs).
- **Produktionsmethode** (was ein Statistiklauf erzeugt): Argument des Laufs, z. B.
  `nightly_refresh.py --statistik-methode kalender_v1`, unabhängig von `LESER`. Ein Lauf schreibt nur in eine
  **unveröffentlichte** Generation; er setzt keinen aktiven Zeiger. Leser lehnen eine Generation ab, deren Methode
  nicht `LESER` entspricht (Fehler, kein Mischen). Prüfung auf echten Pfaden: Produktion `kalender_v1` bei
  `LESER='alt'`; Leser mit unpassender Generation → Fehler.
- Der alte Zweig hält auch seine **Abhängigkeiten** unverändert (alte Helfer werden nicht umgebaut, sondern neben den
  neuen weitergeführt).

## 2 Kurslader-Gate methodenfest
`verify_seiten_kurse.py` setzt beim Laden **`SA.kalenderMethode='alt'`** in beiden Bäumen (vorher/nachher) und
prüft damit weiterhin Transport, Fehler und Wechsel. Kalenderrichtigkeit prüft ausschließlich die neue
Kalender-Seitenprobe gegen unabhängige Sollwerte. Nach der Aktivierung wird das Kurslader-Gate auf `kalender_v1`
umgestellt und vergleicht dann gleiche Methode bei unterschiedlichem Transport (alter Lader-Fixture gegen neuen).

## 3 V7 erweitert: Erzeuger umbauen
V7 umfasst neben Snapshot + Faktenblatt den **Umbau der Erzeuger** aus A, Zeilen 37–41 und 54
(`backtest_new_filters.py`, `tom_ml_filter.py`, `regime_clustering.py`, `monthly10_blogzahlen.py` +
`monthly10_charts.py`, `blog_builder._build_*_chart`, `etf_seasonal_scan.py`): Offline-Einstieg (Snapshot statt
Download/`now()`), Methodenargument (alt|kalender_v1), Faktenwächter je Artikel (Muster `verify_wahlen_blog.py`),
alt-Zweig reproduziert die veröffentlichten Zahlen exakt.

## 4 Aktivierung als eigenes Paket (V9)
1. **Vorbedingung:** Schreibruhe (Nightly/Intraday/Onboarding gesperrt über die vorhandene Sperre + Timer
   angehalten), P5 freigegeben und abgeschlossen, P6-Generation `kalender_v1` vollständig und rückgelesen.
2. **Deploy mit Methodenwechsel** in fester Reihenfolge, als eigener Workflow-Modus: (a) Python-Image mit
   `LESER='kalender_v1'` gebaut, noch nicht gestartet; (b) DB-Zeiger auf die neue Generation; (c) Container
   neu; (d) statische Dateien (`methode.js` + Seiten) + EN-Build; (e) Blog-Build mit den neuen Artikeltexten.
   Zwischen (b) und (d) lesen alte Seiten den neuen Zeiger nicht (sie lesen keine Statistiktabellen — nur Python
   tut das); Python liest ab (c) die neue Generation.
3. **Konsistenzprüfung** nach dem Deploy (Server): Methode in `methode.js` = `LESER` im Container = Methode der
   aktiven Generation; Live-Abruf je Paket (Header, Engine, Feiertage, Newsletter-Trockenlauf).
4. **Abbruch/Wiederanlauf:** schlägt ein Schritt fehl, Zeiger zurück auf die alte Generation, Container mit
   `LESER='alt'`, statische Dateien vom vorherigen Commit; Schreibruhe endet erst nach erfolgreicher Abnahme.

## 5 Zuordnung A → Bauphase
Jede A-Zeile bekommt in `docs/KALENDER_UMSTELLUNG.md` (kanonisch, neu) eine Zeile: Paket · Bauphase · Erzeuger ·
Aufrufer · Abnahmenachweis (Wächter/Probe) · Status. Bestandsgeschützte Methoden (P3l/P3m) erhalten einen
Reproduktionswächter, der auch nach dem Aufräumen läuft.

## Bauphasen (unverändert gegenüber v2, ergänzt)
V1 Fundament · V2 Browserkern · V3 Ereignisse · V4 Fenster/Renditen · V5 Engine · V6 Statistik (SQL durch Nutzer;
Produktionsmethode) · V7 Veröffentlichte Zahlen + Erzeuger · V8 Methodenregister · **V9 Aktivierung** · Aufräumen.
P5 bleibt separat freigabepflichtig.

## Ausgabevertrag
**Urteil** (Freigabe / mit Auflagen / nicht) · **Befunde** · **Auflagen**. ≤ 40 Zeilen.
