# Tage nach Börsenkalender — Plan P3/P4 v6 (nur V9 präzisiert)

Runde 5: [Plan v5](2026-10-11_kalender_p3p4_plan_v5.md) · [Antwort](2026-10-11_kalender_p3p4_plan_v5_antwort.md) (4 Befunde).
Alles aus v5/v4/v3 + A/B/C gilt, außer den folgenden Punkten. Read-only.

<task>Prüfe, ob V9 jetzt als Bauplan freigegeben werden kann.</task>

## 1 Releasebindung statt nur Fenstersperre (Befund 1)
`inject_credentials.sh` setzt in **jedes** HTML `window.__SA_RELEASE='<sha>'` (neben den Zugangsdaten) und in
`landing/js/methode.js` `SA.release='<sha>'` + `SA.kalenderMethode`. Erste Zeile jedes Rechenskripts ist nicht
nötig: `methode.js` wird als **erstes** Skript eingebunden und prüft `SA.release === window.__SA_RELEASE`; bei
Abweichung (HTML älter oder jünger als die Skripte — auch eine über das Fenster pausierte Ladung) wird die Seite
**einmal** mit `?r=<zeit>` neu geladen (Schutz gegen Schleife: Marke in `sessionStorage`, beim zweiten Mal sichtbarer
Fehler „Seite veraltet — bitte neu laden" statt Rechnung). Rechenskripte prüfen zu Beginn `SA.releaseOk === true`
und rechnen sonst nicht. Wächter: jede Seite bindet `methode.js` vor jedem anderen eigenen Skript ein; Probe mit
altem HTML + neuen Skripten (und umgekehrt) → Neuladen, beim zweiten Mal Fehler, nie Rechnung.

## 2 Methodenabhängige Datenartefakte (Befund 2)
Inventar (aus A + Suche nach Schreibern unter `landing/data/`, Wächter verlangt Vollständigkeit): u. a.
`market_calendar.json/.ics`, `flows_rebalancing.json`, `index_effect_study.json`, `wahlen_study.json` (bestandsgeschützt,
trotzdem gekennzeichnet). Jedes erhält das Feld `kalender_methode`; der Leser prüft es gegen `SA.kalenderMethode` und
zeigt bei Abweichung „Daten werden aktualisiert" statt einer Rechnung. Erzeuger laufen in V9 mit `--aktivierung`
explizit (fehlerhaft = Abbruch). Nicht methodenabhängige Cron-Ausgaben (Options, Polymarket …) bleiben im Fenster
erreichbar; der Wächter kennt beide Listen.

## 3 Rückweg inkl. nginx-Einzelmounts (Befund 3)
Nach `rsync` und Image-Rückwechsel: `docker compose restart nginx` (Einzeldatei-Mounts neu auflösen; Schwesterprojekt
kurz betroffen — wie bei jedem nginx-Konfig-Deploy), danach HTTP-Prüfung von `/sitemap.xml`, `/robots.txt`,
`/llms.txt` und je einer Seite pro Paket gegen die Prüfsummen der Sicherung. Gleiches nach erfolgreicher Aktivierung.

## 4 Isolierter Probelauf (Befund 4)
`deploy/probe/docker-compose.probe.yml` (eigene Datei, nicht die Produktions-Compose): `container_name:
seasonalpha-probe-app`, Mounts ausschließlich unter `/opt/seasonaledge-probe/`, keine Ports, kein nginx; DB nur
lesend (Anon-Key), der Generationszeiger wird im Probelauf aus einer Datei gelesen (`GENERATION_ZEIGER_DATEI`) statt
aus der Tabelle; Probe-HTTP über einen eigenen `python -m http.server` auf dem Probe-Baum. Prüft Umschalten,
Rückweg und Fehler nach jedem Teilschritt, Ergebnis in `docs/KALENDER_UMSTELLUNG.md`.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 25 Zeilen.
