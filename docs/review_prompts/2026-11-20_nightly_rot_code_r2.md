# Code-Review Runde 2: Reparatur Nightly rot — Codex, read-only

Deine Runde 1: docs/review_prompts/2026-11-20_nightly_rot_code_antwort.md (NICHT FREIGABEFÄHIG, drei Befunde).
Ändere NICHTS. Antworte auf Deutsch: je Befund erledigt/nicht erledigt mit Datei:Zeile, neue Befunde, Urteil.

Umgesetzt:
1. Strategietreffen: (2027,11,17) aus shared/fed_dates.py FOMC_MEETING_DATES und landing/js/fomc-dates.js entfernt,
   neue Konstante FOMC_STRATEGIE_TREFFEN; scripts/verify_calendar_rules.py Regel 9.2 meldet eine Überschneidung.
2. Wächter scripts/verify_db_wiederholung.py: Fälle 13a–f (ReadTimeout, ReadError, __cause__, __context__,
   Nicht-vorübergehend, Ladestufe im Log) und 14a/b (echter Aufruf saison_score_betrieb.fuer_ticker mit
   client_factory: Erholung von GOAWAY; dauerhaftes GOAWAY → LadeFehler beim Aufrufer). Deine Mutation „nur direkte
   RemoteProtocolError" macht jetzt 13a/13b/13c rot; `beschreibe=str` macht 13f rot; `_kette` ohne Ursachen 13c/13d.
3. shared/db_wiederholung.py beschreibe() hängt e.__notes__ an (Ladestufe count / seite nach …).

Zur Aggregation im Nightly (dein Hinweis „nicht bis zur Fehleraggregation geprüft"): der LadeFehler aus fuer_ticker
landet in scripts/nightly_refresh.py im bestehenden except → saison_fehler → _FEHLGESCHLAGEN → Exit 1; diesen Pfad
prüft verify_nightly_phasen.py bereits mit Stubs. Reicht das, oder ist ein echter Fehler mit Exit-Code nötig?
