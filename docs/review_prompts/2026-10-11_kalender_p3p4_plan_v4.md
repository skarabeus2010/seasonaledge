# Tage nach Börsenkalender — Plan P3/P4 v4 (nur V9 und Gate geändert)

Runde 3: [Plan v3](2026-10-11_kalender_p3p4_plan_v3.md) · [Antwort](2026-10-11_kalender_p3p4_plan_v3_antwort.md) (V9 drei Lücken).
**Nutzerentscheidung 2026-10-11: Umschaltung im Wartungsfenster** (einmalig, ~15–20 Min., ruhige Zeit). Alles
Übrige aus v3 + A/B/C gilt. Read-only.

<task>Prüfe, ob V9 + Gate jetzt als Bauplan freigegeben werden können.</task>

## Produktionssperre (gebaut in V1, wirksam ab sofort)
`shared/produktionssperre.py`: Kontextmanager `produktion(name)` auf einer `flock`-Datei im gemounteten
Daten-Verzeichnis des Hosts (überlebt Containerneustarts). Jeder Lauf, der `prices`, Statistiktabellen,
Saison-Score, Stress oder Kalender-/Newsletterausgaben schreibt **oder** versendet, hält einen geteilten Lock:
Nightly, Intraday, Onboarding, `fix_missing_days`, alle `backfill_*`, Full Scanner, Daily-/Weekly-Newsletter,
Polymarket-Snapshots, `compute_regime_scores`, `build_calendar_data` (Inventar per Wächter: jedes Skript mit einem
Schreib-/Versandaufruf muss den Kontextmanager tragen, sonst rot). Liegt die **Aktivierungsmarke**
`<daten>/AKTIVIERUNG` vor, beendet sich jeder dieser Läufe sofort mit Exit 75 und einer `refresh_log`-Zeile
„gesperrt (Aktivierung)" — auch manuelle Starts und GitHub-Notauslöser. `install_timers.sh` startet bei vorhandener
Marke keine Timer neu. V9 setzt die Marke, wartet per exklusivem `flock` (Frist 60 Min.) bis kein Lauf mehr
hält, und hält die Marke bis nach der Abnahme.

## V9 Aktivierung (Wartungsfenster)
1. **Vorbedingungen:** P5 freigegeben und abgeschlossen; P6-Generation `kalender_v1` vollständig, rückgelesen,
   unveröffentlicht; alle Bauphasen V1–V8 grün; Release-Kandidat ist ein Commit auf master **nicht** deployt
   (eigener Branch `aktivierung`, Deploy-Workflow nur für master).
2. **Fenster öffnen:** Marke setzen, auf freie Sperre warten; nginx-Wartungsmodus (eigene `location`-Regel, die
   bei vorhandener Datei `<landing>/../WARTUNG` für alle HTML-Routen eine statische Seite mit 503 + Retry-After
   liefert; Daten-JSONs und Assets bleiben erreichbar).
3. **Sicherung:** `landing/` (mit eingesetzten Zugangsdaten), `blog/output/`, `seo/output/`, Container-Image-Tag
   und aktiver Generationszeiger werden in `<daten>/aktivierung-<datum>/` gesichert (Prüfsummenliste).
4. **Umschalten** in fester Reihenfolge: Merge `aktivierung` → master mit Deploy (baut Image mit `LESER=kalender_v1`,
   statische Dateien, EN, Blog — hinter der Wartungsseite unsichtbar); dann Generationszeiger umsetzen.
5. **Abnahme** hinter der Wartungsseite (Zugriff über einen Kopf `X-Abnahme`, den nginx im Wartungsmodus
   durchlässt): Methode `methode.js` = `LESER` im Container = Methode der aktiven Generation; Seitenprobe live je
   Paket; Daily/Weekly im Trockenlauf; Faktenwächter der Artikel auf der gebauten Ausgabe.
6. **Erfolg:** Wartungsdatei entfernen, Marke entfernen, Timer starten, Health-Check.
   **Fehler in 4 oder 5:** Zeiger zurück, gesicherte Verzeichnisse per `rsync --delete` zurück, Image-Tag zurück
   (`docker compose up -d` mit dem gesicherten Tag), Prüfsummenliste vergleichen; master per Revert-Commit
   zurück (der Revert-Deploy läuft ebenfalls hinter der Wartungsseite). Erst nach bestätigter Rücksicherung Marke
   entfernen. Ein Probelauf von 2–6 einschließlich Fehlerweg erfolgt vorher gegen einen **Testpfad** auf dem Server
   (Kopie der Verzeichnisse, ohne Zeigerwechsel), Ergebnis im Plan festgehalten.

## Kurslader-Gate (Korrektur)
Bis V9: unverändert, beide Bäume mit `SA.kalenderMethode='alt'` — die alten Fixtures rechnen mit altem Code, der
neue Baum im alt-Zweig gleich. **Mit V9** endet der Vorher/Nachher-Vergleich gegen die alten Lader-Fixtures (sein
Zweck, die Transportumstellung, ist abgeschlossen; nach V9 rechnen beide Bäume nicht mehr dieselbe Kalenderrechnung).
Erhalten bleiben die transportbezogenen Prüfungen im neuen Baum (Blockfehler zeigt `prices 500`, Wechsel/Rückwechsel/
Zeitraum gegen „direkt"), dann mit `kalender_v1`.

## V7 (Korrektur)
Exakte Alt-Reproduktion nur, wo der ursprüngliche Eingang belegt ist (Down-Month: reproduziert, n/WR/PF/Sharpe/DD
identisch); sonst B7.4 (Neuberechnung auf benanntem Datenstand, so gekennzeichnet).

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 30 Zeilen.
