# Kalender-Umstellung V1b — Entwurf v4 (vor dem Code)

Runde 3: [Entwurf v3](2026-10-11_kalender_v1b_entwurf_v3.md) · [Antwort](2026-10-11_kalender_v1b_entwurf_v3_antwort.md) (2 Befunde).
Alles aus v3/v2/v1 gilt, außer den folgenden Punkten. Read-only.

<task>Sind die zwei Befunde aus Runde 3 aufgelöst? Ist der Entwurf als Bauvorlage freigegeben?</task>

## 1 Deploy-Fenster: Vertrag ausdrücklich begrenzt (P1)
Gewählt: **zeitweilige Sperre mit zuverlässiger Wiederherstellung**. Begründung: ein Methodenwechsel geschieht nur
in V9, und V9 sperrt HTML/JS/i18n/components samt `market_calendar.json` im Wartungsfenster per 503 (Plan v5 §2).
In einem gewöhnlichen Deploy können sich nur Stände **derselben** Methode mischen; eine Seite darf dort für das
Deploy-Fenster gesperrt sein, eine Seite ohne Bootstrap darf bis zur Normalisierung (Sekunden nach dem Vorspulen)
mit einem Skriptfehler stehen bleiben. Zugesagt wird: (a) **keine Rechnung aus gemischten Kennungen** (Sperre),
(b) **nach Deploy-Ende ist jede Seite konsistent** (Abschlussprüfung, `trap`), (c) **eine gesperrte Seite erholt
sich** (automatisches Neuladen höchstens alle 120 s, sonst Hinweis „bitte neu laden" — ein manueller Neuladeversuch
nach Deploy-Ende rechnet). `release_setzen.py` schreibt jede Datei atomar (Temp + `os.replace`).
Probe auf einer Kopie, **während** der Schritte: Zwischenstände (a) neue Skripte + Blog/EN ohne Bootstrap,
(b) halb normalisiert, (c) halb auf `<RELEASE>` gesetzt → jeweils keine Rechnung und keine dauerhafte Wirkung
(Abschnitt 2); danach Endstand → jede Seite rechnet wie vorher.

## 2 Nach der Sperre: kein Netz, nichts Sichtbares, nichts Dauerhaftes (P2)
Der Vertrag nennt beobachtbare Wirkungen statt „kein Wert":
1. **Netz:** keine neue Anfrage, laufende abgebrochen, Body-Lesen scheitert (v3 §3).
2. **Sichtbar:** kein hinzugefügter Knoten in `head`/`body` außer dem Hinweis (Observer); ein dennoch ausgeführtes
   nachgeladenes Skript scheitert an seiner ersten Anweisung.
3. **Dauerhaft:** `methode.js` hüllt `Storage.prototype.setItem/removeItem/clear`: bei `__gesperrt` → `ReleaseFehler`
   (einzige Ausnahme: die eigene Neulademarke über eine interne Referenz). Damit gelangt kein Ergebnis aus einem
   gesperrten Stand in `localStorage`/`sessionStorage` und überlebt das Neuladen nicht (betrifft u. a. `SA.cache`,
   `SA.prefs`, `kurse.js`, Watchlist). IndexedDB, Cache-API, `XMLHttpRequest`, `sendBeacon` kommen in eigenen
   Dateien nicht vor — der Einbindungswächter verlangt das weiterhin.
4. **Arbeitsspeicher** (z. B. `SA._tickerCache` nach bereits erfülltem Body) darf sich ändern: die Seite ist
   endgültig gesperrt (nicht rücksetzbar) und wird verworfen; ohne Netz, DOM und Speicher hat der Wert keine Wirkung.
Probe (iii) startet mit **bereits erfülltem** Body-Promise, sperrt, lässt den Verbraucher laufen (`app.js`
Tickerliste): beobachtet werden Netzanfragen (0), neue Knoten in `head`/`body` (0), Storage-Schreibvorgänge (0
außer der Marke), ausgeführte nachgeladene Skripte (erste Anweisung wirft). Mutationen: Storage-Hülle entfernt;
Observer nur auf `body`; Prüfzeile ohne `__gesperrt`-Vorrang → jeweils benannte Prüfung rot.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 20 Zeilen.
