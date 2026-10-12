# Daily Briefing auf systemd-Timer — Runde 4

Read-only, Arbeitsbaum (nicht committet). Runde 3: [Antwort](2026-10-12_briefing_timer_r3_antwort.md), keine Freigabe.

<task>Sind die Auflagen aus Runde 3 erfüllt, ohne neue Lücken?</task>

## Umsetzung
1. **Echter Mailadapter mit drei Ausgängen** (`shared/email_brevo.py`): neu `send_html_ergebnis()` →
   `angenommen` (2xx) / `abgelehnt` (kein Schlüssel, `ConnectTimeout`, HTTP 4xx) / `unklar` (HTTP 5xx, Lese-Timeout,
   Verbindungsabbruch, jede andere `RequestException`). `send_html()` bleibt für alle übrigen Aufrufer und ist
   `== angenommen`. Der Newsletter nutzt `send_html_ergebnis`; nur `abgelehnt` schreibt `-`, `unklar` und Ausnahmen
   bleiben `?`.
2. **Journal chronologisch** (`shared/versandsperre.py`): letzter Eintrag je Empfänger gilt, `+` gilt für immer;
   ungeklärt = letzter Eintrag `?` und nie `+`. Damit ist `? - ?` ungeklärt.
3. **Wächter** (`scripts/verify_briefing_versand.py`): neu `[Adapter]` — der echte `send_html_ergebnis` mit ersetztem
   `requests.post` (201/400/502/ReadTimeout/ConnectTimeout/ConnectionError/ohne Schlüssel, dazu `send_html` je Fall);
   `[Versand]` Folge `? - ?` (abgelehnt → zweiter Versuch angenommen, Abbruch vor `+` → dritter Lauf versendet
   nicht), unklarer Ausgang bleibt ungeklärt. Windows 73/73 (+2 nur Linux), **Linux im Container 75/75**.
   Gate-Schritt installiert `requests==2.32.3` (fehlt nach setup-python). Mutationstest **35/35** (neu: Mengen statt
   Reihenfolge, unklar als Ablehnung notiert, 5xx/Lese-Timeout als Ablehnung, `send_html` meldet unklar als Erfolg),
   Gegenproben richtig verworfen, Projektbaum unverändert.
4. `verify_produktionssperre.py`: die Versandprüfung erkennt `send_html(` und `send_html_ergebnis(`.

## Ausgabevertrag
**Urteil** (Freigabe / keine Freigabe) · **Befunde** (P1/P2, mit Datei:Zeile) · **Auflagen**. ≤ 20 Zeilen.
