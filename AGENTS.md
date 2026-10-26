# AGENTS.md — SeasonAlpha (für Codex)

Diese Datei liest Codex automatisch. Sie ist bewusst kurz: die vollständige Projektdoku steht in
[CLAUDE.md](CLAUDE.md) (≈ 170 KB, zu groß für den Projektkontext) und in `docs/`.
**Bei jeder Aufgabe zuerst die obersten drei Versionseinträge von `CLAUDE.md` lesen** — dort steht
der aktuelle Stand, und der kann neuer sein als diese Zusammenfassung.

## Projekt

Saisonale Finanzmarkt-Analyse (`seasonalpha.ai`). Frontend = statisches HTML unter `landing/`
(nginx), Daten in Supabase, Batch-Jobs unter `scripts/`, Rechenkern unter `shared/`.
Streamlit ist seit v66.7 **abgeschaltet und gelöscht** (`/app/` → 410).

## Stand 2026-10-10 (Version 66.9)

- **v66.9 Saison-Score statt „KI-Score“:** eine Rechnung in `shared/saison_score.py` = `landing/js/saison-score.js`.
  Validierung: Rangkorrelation 0,019 → **keine Vorhersagekraft**, die Seiten sagen das. Kein Bullish/Bearish.
  `ki_score.py`, `ai_models.py` und die Tabelle `ki_scores` sind weg. Prospektive Bestätigung ab 2027-10 aus `saison_score_protokoll`.
- **v66.8 Zeitzonenfehler in den Saisonkurven behoben** (`SA.seasonal.tagNummer(iso)`, westlich von UTC lag jeder Tag um eins daneben).
  Anomalie-Radar neu: eine Rechnung `SA.decadeCompute.anomalie`, Python-Isolation-Forest gelöscht.
- **v66.7 Streamlit aus, Ampel aus allen Mails**, `regime_scores` gelöscht.
- **v66.6 Stress-Ampel** (vorher Crash-Ampel mit vertauschtem Vorzeichen): `shared/stress_score.py` = `SA.dashCompute.computeStress`,
  Tabellen `stress_laeufe`/`stress_scores`, nur vorangegangene Sitzungen als Referenz.
- **Polymarket Phase B:** B1 (Preisqualität, Migration) erledigt. **Offen:** B2 Status-Lebenszyklus (WIP-Commit 95209ec),
  B3 gemeinsame Gültigkeitsregel Seite/Newsletter, B4 Auflösung mit Beleg, `SPREAD_GRENZE` messen.
  Zwei Befunde, die veröffentlichte Aussagen zurückziehen könnten, warten auf eine Nutzerentscheidung. Plan: `docs/POLYMARKET.md`.
- **/plain-vanilla:** 1A + 1B erledigt; offen: XETRA-TDOY/TDOM-Neuberechnung (erst Trockenlauf), Phase 2/3.
- Offene Punkte insgesamt: Abschnitt `## TODO` in `CLAUDE.md`.

## Regeln für Reviews und Code

- **Das Repo ist öffentlich.** Keine Sicherheitsbefunde, Secrets, Server-Adressen oder Beschreibungen offener Lücken
  in Dateien schreiben, die committet werden.
- Reviews laufen read-only (`codex exec -s read-only`); Ablauf und Prompt-Aufbau: `docs/REVIEW_MIT_CODEX.md`.
- **Backend/Frontend-Zwillinge:** viel Mathematik existiert in Python und JS. Prüfen, ob beide dasselbe rechnen, und
  beide gegen eine dritte, unabhängig hergeleitete Referenz — Übereinstimmung zweier Zwillinge beweist nichts.
- **Fehlende Daten:** wird ein Wert `None`, oder rückt ein alter Wert an die Stelle des aktuellen? Meldet ein Fehlschlag
  sich als Fehlschlag (Exit ≠ 0), oder als grüner Lauf mit alten Zahlen?
- **Wächter und Mutationstests:** ein Test muss den Produktionspfad treffen (gleiche Argumente, gleicher Serverpfad).
  Mutationstests schreiben über `_atomar_schreiben` (deterministisch), eine Mutation ohne Anker zählt als ungültig, nicht als gefangen.
  Auch eine abgefangene Ausnahme ist kein Nachweis.
- Normalisierte Renditen (jedes Jahr startet bei 100), Handelstage nach Börsenkalender des Ticker-Suffixes, nie Kalendertage.
- Lokal Python `py -3.14`; die lokale `.env` hat keine Supabase-Zugangsdaten → Datenläufe nur auf dem Server.
  Keine DB-Writes ohne ausdrückliche Freigabe des Nutzers.
- Leser-Text: echte Umlaute, keine Selbstbeteuerungen („ehrlich“, „transparent“), keine Repo-Pfade, Fallzahl an jede Zahl.
- `de.json`/`en.json` inhaltlich geändert → `_JSON_VER` in `landing/js/i18n.js` erhöhen.
