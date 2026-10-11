# Kalender-Umstellung V1a — Produktionssperre, `[ohne-deploy]`, Timer-Schutz (Code-Runde 1)

Plan: [docs/KALENDER_UMSTELLUNG.md](../KALENDER_UMSTELLUNG.md), [v4](2026-10-11_kalender_p3p4_plan_v4.md)/[v5](2026-10-11_kalender_p3p4_plan_v5.md).
Read-only, nichts schreiben, Mutationstest NICHT ausführen (er schreibt). Änderungen: `git diff` + neue Dateien.

<task>Prüfe V1a. Wird mit dem Deploy sofort wirksam (alle Pflicht-Läufe nehmen den geteilten Lock; ohne Marke
ändert sich nichts) — gibt es einen Pfad, auf dem das den Betrieb stört oder die Sperre umgeht?</task>

## Inhalt
- `shared/produktionssperre.py`: `produktion(name)` = geteilter `flock` auf `<Projekt>/logs/sperre/produktion.lock`
  (Container `/app/logs/sperre`, Host `/opt/seasonaledge/logs/sperre` — derselbe Ordner, `./logs` ist gemountet;
  beide laufen als root). Marke `AKTIVIERUNG` (Kennung) wird **unter** dem Lock geprüft; ohne passende
  `SA_AKTIVIERUNG` → `Gesperrt` = `SystemExit(75)` vor jeder Arbeit. Ohne `fcntl` (Windows) nur Markenprüfung.
  Abweichung vom Plan: Kennung über die Umgebung `SA_AKTIVIERUNG` statt Argument `--aktivierung` — gleich für alle
  Skripte, über `docker exec -e` setzbar; bitte bewerten.
- Inventar `PFLICHT` (19 Skripte) / `AUSNAHMEN` (40, je mit Grund) im Modul.
- Jedes Pflicht-Skript: `__main__`-Block in `with produktion("<name>"):` (19 Dateien, mechanisch, Syntax geprüft).
- `deploy/install_timers.sh`: bei gesetzter Marke werden die Units kopiert, die Timer aber nicht gestartet (exit 0).
- `deploy.yml`: Job-Bedingung `!contains(head_commit.message, '[ohne-deploy]')`; neuer Gate-Schritt.

## Nachweise
`scripts/verify_produktionssperre.py`: Inventar (jedes Skript mit Schreib-/Versandmuster in genau einer Liste),
Einbau per AST, Verhalten in Unterprozessen (ohne Marke Rumpf; Marke ohne/mit falscher Kennung Exit 75 ohne Rumpf;
passende Kennung läuft; gehaltener exklusiver Lock blockiert ≥ 1 s), echte Pflicht-Skripte bei Marke → Exit 75
— **abgeschottet** (Supabase auf 127.0.0.1:9, Brevo leer, alle Proxys tot, Frist 30 s), weil eine Mutation
„Sperre fehlt" sonst im Server-Container einen echten Nightly gestartet hätte; Betrieb (install_timers, deploy.yml).
Windows 29/29 (Lock UNGEPRÜFT), **Linux im Server-Container (Kopie unter /tmp, streng) 30/30**.
Mutationstest 10/10 auf Linux (u. a. Pflicht-Skript ohne Sperre, Marke nicht geprüft, jede/keine Kennung, Lock nicht
genommen, Inventarlücke, unbekannter neuer Schreiber, Timer trotz Marke, Deploy ohne Bedingung), Gegenproben verworfen.

## Fokusfragen
1. Kann ein Pflicht-Lauf die Sperre umgehen (andere Einstiege: `refresh_ticker_data` aus Nightly-Import,
   GitHub-Workflows mit `python3 -c`, `docker exec … python3 -m`)? 2. Kann der geteilte Lock einen Lauf blockieren,
   ohne dass eine Aktivierung läuft (z. B. ein verwaistes exklusives Lock)? 3. Ist Exit 75 für systemd/GitHub
   unproblematisch, oder braucht es `SuccessExitStatus`/eine `refresh_log`-Zeile (Plan v4 nannte sie)?

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 35 Zeilen.
