# Code-Review: Streamlit aus + Ampel aus den Mails (Runde 3)

Repo `C:\dev\Seasonaledge`, Arbeitsstand. Vorgeschichte: `..._runde1/2.md` + Antworten. Nur lesen.
Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Fall + Änderung; am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Korrektur zu R2 (Stress-Fehlertext über refresh_log in der Health-Mail)
Beim **Erzeuger** behoben: `scripts/nightly_refresh.py` Phase E schreibt in `regime_status["error"]` nur noch
„Stress-Lauf gescheitert (<Ausnahmeklasse>), Details im App-Log"; der Volltext (mit Score/Farbe aus dem
Rücklesevergleich) geht ausschließlich an `app_logger.error`. Der refresh_log-Eintrag heißt `STRESS: …`.
Damit kann keine Ausgabe, die refresh_log liest (Health-Check 1 u. a.), Score oder Farbe enthalten — die Regel sitzt
beim Erzeuger statt bei jedem Leser.

Wächter: `ampel_nicht_in_mails` prüft zusätzlich, dass `nightly_refresh.py` nicht `regime_status["error"] = str(e)`
setzt; neue Mutation „Stress-Fehlertext roh ins refresh_log". `verify_stress_ampel.py --snapshot` 34/34.

Eine Renderprüfung der Health-Mail mit einem Stress-Fehler halte ich danach für entbehrlich, weil der Text die
Score-Daten an keiner Stelle mehr erreicht. Wenn du das anders siehst, bitte begründen.
