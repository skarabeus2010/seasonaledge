# Nightly rot an 10 von 15 Abenden — Diagnose und Reparaturvorschlag (Codex, read-only)

Du bist Reviewer. Ändere NICHTS, schreibe keine Dateien. Antworte auf Deutsch.

## Beobachtung (journalctl -u sa-nightly.service, Server, 05.–19.11.2026)

Exit 1 an 05., 06., 07., 08., 09., 11., 12., 13., 14., 15., 17., 19.11. Gescheiterte Phasen:

- 05.11. Saison-Score `^GDAXI: Abruf fehlgeschlagen: {'code': '57014' statement timeout}` + Ticker-Refresh `^SDAXI: monthly_stats <ConnectionTerminated error_code:0, last_stream_id:19999>`
- 06.11. Saison-Score `RTX` 57014
- 07.11. Saison-Score `^GSPC` 57014
- 08.11. Saison-Score `EWZ: <ConnectionTerminated error_code:0, last_stream_id:19999>`
- 09.11. Saison-Score 2 Fehler, z. B. `^GSPC` 57014
- 11./12.11. Supabase-Projekt pausiert (bekannt, NXDOMAIN) — nicht Teil dieser Frage
- 13.11. Saison-Score 7 Fehler 57014 (Rechenstufe Nano, bekannt)
- 14.11. `^GSPC` 57014
- 15.11. Ticker-Refresh 6 Fehler `^MDAXI: tdom_stats open_to_next_open Out of range float values are not JSON compliant: inf`
- 17.11. `^GSPC` 57014
- 19.11. `UEC: <ConnectionTerminated error_code:0, last_stream_id:19999>`

Jeder andere Ticker (rund 370) läuft durch. Der Fehler trifft meist die LÄNGSTEN Reihen (^GSPC ab 1927, ^GDAXI, RTX).

## Code

- `scripts/nightly_refresh.py` Zeilen ~60–180 (Ticker-Schleife; `_get_client()` = `shared.supabase_client.get_client`, ein Client für den ganzen Lauf)
- `shared/saison_score_betrieb.py::fuer_ticker` → `shared/stress_score.py::lade_kurse` (Zeile ~177): `count="exact"` auf `prices` + Offset-Paginierung `.order("date").range(offset, offset+999)`, KEINE Wiederholung; jede Ausnahme → `LadeFehler`.
- `shared/supabase_client.py::_with_retry` (Zeile ~115) existiert, wird nur bei Upserts benutzt; fängt `ConnectError, TimeoutException, RemoteProtocolError` und setzt den globalen Client zurück.
- `shared/cache_manager.py` (tdom_stats/tdoy_stats, `schreibfehler_werfen`).

## Meine Hypothesen (bitte prüfen, nicht übernehmen)

1. `last_stream_id:19999` = der HTTP/2-Server beendet die Verbindung nach 10 000 Anfragen (GOAWAY). Der Nightly nutzt EINEN Client über ~370 Ticker × viele Abfragen; wer die 10 000. Anfrage trifft, scheitert. Kein Retry → rot. Nicht tickerabhängig, nur Zählerstand.
2. 57014 trifft vor allem `count="exact"` und tiefe Offsets (`OFFSET 25000` auf ^GSPC) — Offset-Kosten wachsen linear; Keyset (`date > letztes`) wäre konstant. Gelegentlich, je nach Last.
3. `inf` am 15.11.: Division durch einen Schlusskurs 0 oder einen Open von 0 bei ^MDAXI in tdom_stats — ein Datenfehler, kein Netzfehler; trat seither nicht wieder auf?

## Fragen

1. Stimmen die Hypothesen? Belege aus dem Code (Datei:Zeile). Was übersehe ich?
2. Reparaturvorschlag mit minimalem Eingriff. Bedingungen:
   - Ein Ladefehler darf NIE als gültiger Score enden (unvollständige Reihe → Fehler, wie heute).
   - Wiederholung nur bei vorübergehenden Fehlern (57014, ConnectionTerminated/RemoteProtocolError, Timeout, Verbindungsfehler), nicht bei Rechte-/Schemafehlern.
   - Nach ConnectionTerminated einen NEUEN Client verwenden — der Nightly reicht `_get_client()` herein; wie stellt man sicher, dass der Wiederholversuch nicht denselben toten Client benutzt?
   - Die Vollständigkeitsprüfung `len(zeilen) == count` soll bleiben (oder gleichwertig).
3. Soll der Retry in `lade_kurse` sitzen (Erzeuger) oder im Nightly (Aufrufer)? Wer ruft `lade_kurse` sonst noch?
4. Gibt es weitere Vollhistorie-Lader mit demselben Muster (count=exact + Offset, kein Retry), die dieselbe Reparatur brauchen? Liste.
5. Ist es richtig, dass EIN gescheiterter Ticker von 370 den ganzen Nightly rot macht? Oder sollte ein Ticker nach N Versuchen gelb melden? (Beachte: v66.29 hat absichtlich jeden Fehler rot gemacht, weil vorher Fehler als Erfolg galten.)
6. Wie testet man das so, dass der Test fehlschlägt, wenn der Retry fehlt (Wächter-Idee, Attrappe mit erster Antwort 57014 / ConnectionTerminated)?

Antworte mit: Befunde (nummeriert, mit Datei:Zeile), Reparaturvorschlag, Testvorschlag.
