# Tage nach Börsenkalender — Plan P3/P4 v5 (nur V9/Gate präzisiert)

Runde 4: [Plan v4](2026-10-11_kalender_p3p4_plan_v4.md) · [Antwort](2026-10-11_kalender_p3p4_plan_v4_antwort.md) (3 Befunde, 5 Auflagen).
Alles aus v4/v3 + A/B/C gilt, außer den folgenden Punkten. Read-only.

<task>Prüfe, ob V9 + Gate jetzt als Bauplan freigegeben werden können.</task>

## 1 Aktivierungspfad (Befund 1)
Die Aktivierungsmarke enthält eine Zufallskennung. Ein Lauf darf trotz Marke starten, wenn er **diese Kennung als
Argument** (`--aktivierung <kennung>`) erhält — die Markenprüfung erfolgt **unter** dem gemeinsamen Lock. Erlaubt
sind damit nur: Newsletter im Modus `--nur-rendern` (rendert vollständig in eine Datei, **kein** Versand, kein
`refresh_log`-, Abonnenten- oder Statistik-Schreiben), `build_calendar_data.py --aktivierung` (schreibt JSON/ICS in
den Release-Baum), die Abnahmeproben. Alle gewöhnlichen Starts bleiben gesperrt. Der Deploy-Schritt
`build_calendar_data` wird für den Aktivierungs-Deploy aus `inject_credentials.sh` herausgenommen und im Ablauf
explizit mit Fehlerprüfung aufgerufen (kein `|| echo`).

## 2 Kein Mischstand im Browser (Befund 2)
Die Wartungsregel sperrt im Fenster **nicht nur HTML**, sondern auch `/landing/js/`, `/landing/css/`,
`/landing/i18n/`, `/landing/components/` (503 + `Retry-After`; Fetch-Fehler statt neuem Code). Eine vor dem Fenster
begonnene Seite bricht beim Nachladen ab (sichtbarer Ladefehler), statt alte und neue Rechnung zu mischen; eine
vollständig geladene Seite lädt keine Rechenskripte nach. Offen bleiben `/landing/data/` (Cron-Ausgaben, nicht
methodenabhängig — Ausnahme `market_calendar.json`: im Fenster ebenfalls gesperrt). Regel + Marke im nginx-Container
(`/etc/nginx/wartung/AN`, gemountetes Verzeichnis) werden **vor V9** installiert und mit einem Probe-Ein/Aus geprüft
(HTTP-Codes je Pfad, Schwesterprojekt-Domain unberührt).

## 3 Rückweg in richtiger Reihenfolge (Befund 3)
Sicherung vor dem Umschalten zusätzlich: **Image per ID** (`docker image tag <id> seasonaledge-app:vor-aktivierung`,
ID im Sicherungsprotokoll). Bei Fehler:
1. Revert-Commit auf master mit `[ohne-deploy]` (der Deploy-Workflow überspringt Commits mit dieser Kennung —
   neue Bedingung, eigener kleiner Commit in V1, mit Wächter);
2. Server: `git reset --hard <Revert-Commit>` (Quellstand = alt), dann `rsync --delete` der gesicherten
   `landing/`, `blog/output/`, `seo/output/`, `docker compose up -d` mit `seasonaledge-app:vor-aktivierung`,
   Generationszeiger zurück;
3. **danach** Prüfsummenliste, Methode in `methode.js` = `LESER` im Container = Methode der aktiven Generation,
   HTTP-Stichproben je Paket; erst dann Wartung aus und Marke weg.
Probelauf von Umschalten und Rückweg einschließlich Fehlern nach jedem Teilschritt und während des DE-/EN-Builds auf
einem **Testpfad** (Kopie unter `/opt/seasonaledge-probe`, eigener Compose-Projektname, kein Zeiger, kein nginx).

## 4 Gate (Auflage 4)
Im neuen Baum bleiben mit `kalender_v1` und eigenen Sollwerten: `blockfehler` (Seite zeigt `prices 500`),
`vollfehler` (Saison-Score „nicht berechenbar", Radar mit eigener 31-J-Ladung: Basis = Sollzahl Vergleichsjahre aus
der Fixture), `ttl` (nach Ablauf + Fehler gleiches Soll), `wechsel`/`rueckwechsel`/`zeitraum` (gegen „direkt").
Nur der Vergleich gegen die alten Lader-Fixtures entfällt.

## 5 Release-Vorbedingung (Auflage 5)
Der Kandidat liegt auf Branch `aktivierung` (Deploy nur für master); erst Schritt 4 („Umschalten") bringt ihn per
Merge auf master. Alle Gates laufen vorher auf dem Branch (Workflow-Lauf ohne Deploy-Schritt). P5 separat.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 25 Zeilen.
