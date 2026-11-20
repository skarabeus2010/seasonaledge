Reading additional input from stdin...
OpenAI Codex v0.162.0
--------
workdir: C:\dev\SeasonalEdge
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a1f97b-bf4e-7f40-b6cc-ec42a4788ac9
--------
user
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
codex
Ich prüfe zuerst die drei neuesten Versionseinträge in `CLAUDE.md`, danach die Ladepfade, Fehlerbehandlung und Aufrufer. Ich bleibe vollständig read-only.
exec
"C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -Command 'Get-Content CLAUDE.md -TotalCount 240' in C:\dev\SeasonalEdge
 exited -1 in 0ms:
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
2026-11-20T15:03:26.437517Z ERROR codex_core::tools::router: error=exec_command failed: CreateProcess { message: "Rejected(\"Failed to create unified exec process: helper_unknown_error: setup refresh had errors\")" }
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Der Ladepfad bricht bei jedem Abruffehler ab und prüft anschließend die Zeilenzahl. Der vorhandene Retry schützt ihn nicht; auch die Statistik-Upserts im Nightly nutzen diesen Wrapper nicht. Beim Client-Neustart ist entscheidend: Das Zurücksetzen der globalen Variable ersetzt kein bereits übergebenes Client-Objekt.
mcp: node_repl/js started
mcp: node_repl/js (completed)
web search: 
web search: site.rfc-editor.org rfc 9113 last-stream-id GOAWAY odd stream identifiers ...
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (failed)
codex
Die `inf`-Meldung passt zu einer weiteren Lücke: TDOM/TDOY filtern mit `notna()`, wodurch Unendlich in der Stichprobe bleibt. Bei `open_to_next_open` ist der Nenner der Open desselben Tages, nicht der Schlusskurs. Ob `^MDAXI` am 15.11. tatsächlich einen Open von null lieferte, lässt sich ohne die damaligen Eingabedaten nicht belegen.
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
web search: 
web search: site.postgrest.org exact count performance large tables ...
mcp: node_repl/js started
mcp: node_repl/js (completed)
web search: 
web search: https://raw.githubusercontent.com/encode/httpcore/master/httpcore/_sync/http2.py
mcp: node_repl/js started
mcp: node_repl/js (completed)
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
Die Offline-Probe mit dem echten Lader bestätigt den fehlenden Retry: Ein Fehler bei der Zählung führt nach einer Anfrage zu `LadeFehler`; ein Fehler auf Seite 2 bricht ebenfalls sofort ab. Auch die Abweichung zwischen Zeilenzahl und Count wird abgelehnt. Ein synthetischer Null-Open erzeugt im echten Renditecode `inf`, das den `notna()`-Filter passiert.

Ich würde die Wiederholungen im Lader bündeln und den Nightly nach ausgeschöpften Versuchen weiterhin rot melden lassen.
mcp: node_repl/js started
mcp: node_repl/js (completed)
codex
## Befunde

1. **Hypothese 1 ist sehr plausibel; die feste Grenze von 10 000 Anfragen ist noch nicht bewiesen.**  
   Der Nightly ruft zwar wiederholt `_get_client()` auf, erhält aber den gecachten Singleton: [nightly_refresh.py:143](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:143), [supabase_client.py:20](C:/dev/SeasonalEdge/shared/supabase_client.py:20).

   HTTP/2 verwendet für Client-Streams ungerade IDs; `19999` entspricht bei fortlaufender Vergabe dem 10 000. Stream. `error_code:0` passt zu einem GOAWAY ohne Protokollfehler. `last_stream_id` bezeichnet allerdings den höchsten möglicherweise bearbeiteten Stream, nicht zwingend die gerade gescheiterte Anfrage. Das spricht für ein Verbindungslimit, belegt aber weder den auslösenden Proxy noch dessen Konfiguration. Der Zähler gilt **je Verbindung**, nicht je Supabase-Client oder Gesamtlauf. [HTTP/2-Spezifikation](https://www.rfc-editor.org/rfc/rfc9113.html)

   Der angezeigte `ConnectionTerminated` ist normalerweise die Darstellung eines HTTP/2-Ereignisses innerhalb eines `RemoteProtocolError`. Die konkrete Exception-Klasse sollte künftig mitgeloggt werden. [httpcore-Implementierung](https://raw.githubusercontent.com/encode/httpcore/master/httpcore/_sync/http2.py)

2. **Hypothese 2 beschreibt reale Kosten, lokalisiert aber den konkreten Timeout noch nicht.**  
   [stress_score.py:187](C:/dev/SeasonalEdge/shared/stress_score.py:187) führt **einmal pro Ticker** eine exakte Zählung aus; danach folgen Offset-Seiten ohne erneuten Count, ab [stress_score.py:190](C:/dev/SeasonalEdge/shared/stress_score.py:190). `limit(1)` begrenzt dabei den Datenkörper, ersetzt die vollständige Zählung aber nicht. Exakte Counts können teuer sein. [PostgREST-Dokumentation](https://docs.postgrest.org/en/v10/api.html#exact-count)

   Tiefe Offsets verursachen zusätzliche Arbeit, weil PostgreSQL übersprungene Zeilen trotzdem berechnen muss. Keyset beseitigt diese wiederholte Überspringarbeit; „konstant“ ist die Laufzeit deswegen nicht garantiert und setzt einen passenden Zugriffspfad voraus. [PostgreSQL-Dokumentation](https://www.postgresql.org/docs/18/queries-limit.html)

   **Aus dem heutigen Fehlertext lässt sich Count gegen Seite 26 nicht unterscheiden.** Alle Abruffehler werden identisch verpackt: [stress_score.py:198](C:/dev/SeasonalEdge/shared/stress_score.py:198). Last, Planerstatistiken und Rechenstufe bleiben zusätzliche Ursachen; die drei neuesten `CLAUDE.md`-Einträge dokumentieren diese bereits für den November-Ausfall.

3. **Hypothese 3 passt zum Code, mit einer Präzisierung: Bei `open_to_next_open` ist der Nenner der aktuelle Open.**  
   Die Rechnung lautet `(nächster Open − aktueller Open) / aktueller Open`: [tdom_analysis.py:73](C:/dev/SeasonalEdge/shared/tdom_analysis.py:73). TDOM und TDOY entfernen anschließend nur `NaN`; `inf` bleibt enthalten: [tdom_analysis.py:113](C:/dev/SeasonalEdge/shared/tdom_analysis.py:113), [tdoy_analysis.py:83](C:/dev/SeasonalEdge/shared/tdoy_analysis.py:83).

   Die Serialisierung übernimmt Mittelwert und Median ungeprüft; die Standardabweichung wird nur auf `isnan`, nicht auf Endlichkeit geprüft: [cache_manager.py:176](C:/dev/SeasonalEdge/shared/cache_manager.py:176), [cache_manager.py:237](C:/dev/SeasonalEdge/shared/cache_manager.py:237).

   Eine Offline-Probe des echten Renditecodes mit Open `[100, 0, 110]` ergibt `[-100, inf, NaN]`; `inf` überlebt den Filter. **Der Mechanismus ist bestätigt, der damalige MDAX-Eingabefehler nicht.** Die Statistik stammt hier aus dem Yahoo-DataFrame, nicht aus dem Supabase-Vollhistorielader: [nightly_refresh.py:77](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:77), [nightly_refresh.py:158](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:158).

   „Seither nicht wieder aufgetreten“ gilt nur für die vorgelegten Meldungen. Zudem wurden TDOM/TDOY-Schreibfehler vor v66.29 verschluckt; der 15.11. kann auch der erste **sichtbare** Vorfall gewesen sein.

4. **Der bestehende Retry hilft diesen Nightly-Pfaden nicht.**  
   `_with_retry` erfasst weder PostgREST-Code `57014` noch sämtliche Netzwerkfehler: [supabase_client.py:123](C:/dev/SeasonalEdge/shared/supabase_client.py:123). Seine einzigen gefundenen Produktionsverwendungen sind zwei Polymarket-Upserts: [supabase_client.py:819](C:/dev/SeasonalEdge/shared/supabase_client.py:819), [supabase_client.py:835](C:/dev/SeasonalEdge/shared/supabase_client.py:835).

   Insbesondere schreiben Monthly- und TDOM-Stats direkt ohne diesen Wrapper: [supabase_client.py:453](C:/dev/SeasonalEdge/shared/supabase_client.py:453), [supabase_client.py:483](C:/dev/SeasonalEdge/shared/supabase_client.py:483). **Ein Retry ausschließlich im Kurslader behebt deshalb nicht alle beobachteten Rotläufe.**

   Der Import-Fallback `retriable = (Exception,)` wäre für die geforderte selektive Wiederholung ungeeignet: [supabase_client.py:125](C:/dev/SeasonalEdge/shared/supabase_client.py:125).

5. **Der heutige Ladefehler-Vertrag ist richtig; Retry gehört unter diesen Vertrag.**  
   Abruffehler werden zu `LadeFehler`, eine abweichende Zeilenzahl ebenfalls: [stress_score.py:198](C:/dev/SeasonalEdge/shared/stress_score.py:198), [stress_score.py:200](C:/dev/SeasonalEdge/shared/stress_score.py:200). Erst nach erfolgreichem Laden berechnet `fuer_ticker` den Score: [saison_score_betrieb.py:21](C:/dev/SeasonalEdge/shared/saison_score_betrieb.py:21).

   Weitere Aufrufer von **diesem** `stress_score.lade_kurse`:

   | Aufrufer | Stelle |
   |---|---|
   | Saison-Score, damit auch Nightly und Vollscanner | [saison_score_betrieb.py:21](C:/dev/SeasonalEdge/shared/saison_score_betrieb.py:21), [full_scanner_run.py:69](C:/dev/SeasonalEdge/scripts/full_scanner_run.py:69) |
   | Stress-Vollauf | [stress_score.py:270](C:/dev/SeasonalEdge/shared/stress_score.py:270) |
   | Stress-Trockenlauf | [compute_regime_scores.py:47](C:/dev/SeasonalEdge/scripts/compute_regime_scores.py:47) |
   | Health-Nachrechnung für SPY | [daily_health_check.py:858](C:/dev/SeasonalEdge/scripts/daily_health_check.py:858) |
   | `stress_fuer_ticker` | [stress_score.py:210](C:/dev/SeasonalEdge/shared/stress_score.py:210); außerhalb der Definition nur Testaufrufe gefunden |

   `shared.data.lade_kurse` ist eine andere Funktion.

6. **Weitere Lader sind betroffen, allerdings überwiegend ohne `count="exact"`.**

   | Lader | Aktuelles Muster |
   |---|---|
   | [supabase_client.py:142](C:/dev/SeasonalEdge/shared/supabase_client.py:142) `fetch_prices` | Vollhistorie, Offset, kein Retry, kein Count |
   | [data.py:174](C:/dev/SeasonalEdge/shared/data.py:174) `lade_closes` | Vollhistorie oder Zeitraum, Offset, kein Retry/Count |
   | [data.py:233](C:/dev/SeasonalEdge/shared/data.py:233) `lade_kurse` | Vollhistorie oder Zeitraum, Offset, kein Retry/Count; prüft `None` und Datumsordnung |
   | [backfill_new_ticker.py:44](C:/dev/SeasonalEdge/scripts/backfill_new_ticker.py:44) `vorhandene_daten` | Gesamte Datumsmenge, Offset, kein Retry/Count |
   | [backfill_tdoy.py:50](C:/dev/SeasonalEdge/scripts/backfill_tdoy.py:50) `lade` | Optional begrenzte Historie, Offset, kein Retry/Count |
   | [fix_missing_days.py:56](C:/dev/SeasonalEdge/scripts/fix_missing_days.py:56) `get_db_dates` | Datumsbereich, Offset, kein Retry/Count |
   | [kurse_messen.py:63](C:/dev/SeasonalEdge/scripts/perf/kurse_messen.py:63) `variante_f` | Tatsächlich Count + Offset ohne Retry; bewusst alte Benchmark-Variante |

   Unter den geprüften Python-Produktionsladern fand ich **keinen zweiten vollständigen Doppelgänger** mit Count + Offset. Die ersten drei sind die vorrangigen weiteren Reparaturstellen. Bei einigen schwächeren Ladern wird `data=None` als Seitenende behandelt; das sollte ebenfalls kein erfolgreicher Teilbestand werden.

   Verwandte Offset-Pfade gibt es außerdem beim Stress-Rücklesen und bei der begrenzten Newsletter-Historie: [stress_score.py:297](C:/dev/SeasonalEdge/shared/stress_score.py:297), [daily_report.py:330](C:/dev/SeasonalEdge/shared/daily_report.py:330). Der aktuelle Browser-Kurslader verwendet bereits Keyset und Retry: [kurse.js:17](C:/dev/SeasonalEdge/landing/js/kurse.js:17).

7. **Nach ausgeschöpften Versuchen weiterhin rot ist hier richtig.**  
   Der Nightly arbeitet die übrigen Ticker weiter ab und sammelt endgültige Fehler: [nightly_refresh.py:149](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:149), [nightly_refresh.py:173](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:173). Erst am Ende folgt Exit 1: [nightly_refresh.py:613](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:613).

   Ein behobener Zwischenfehler kann als Warnung erscheinen. Ein endgültig fehlender Score bleibt dagegen ein unvollständiger Lauf — auch bei 369 erfolgreichen Tickern. Eine gelbe Gesamteinstufung wäre eine bewusste Änderung des Betriebsvertrags und sollte nicht Bestandteil dieser Reparatur sein.

## Reparaturvorschlag

**Retry im Lader, Fehleraggregation im Nightly.** Nicht den gesamten Ticker einschließlich Downloads und Writes wiederholen.

1. **Eine kleine gemeinsame Fehlerklassifikation verwenden.** Wiederholbar sind:
   - strukturierter PostgREST-Code `57014`;
   - `httpx.RemoteProtocolError`;
   - `httpx.TimeoutException`;
   - passende `httpx.NetworkError`-Unterklassen für Verbindungs-, Lese- und Schreibabbrüche.

   Rechte-/Schemafehler, ungültige JSON-Zahlen und unbekannte Exceptions sofort weiterreichen. Keine allgemeine Textsuche nach „timeout“ oder „ConnectionTerminated“; gegebenenfalls die erhaltene Ursachenkette prüfen.

2. **Im Kurslader höchstens drei vollständige Ladeversuche mit kurzem Backoff und Jitter.**  
   Jeder Versuch beginnt mit neuer Zählung, leerer Zeilenliste und zurückgesetztem Cursor. Erst nach vollständigem Erfolg bereinigen und zurückgeben. Nach dem letzten Fehler `LadeFehler` mit `raise … from e`; niemals Teilreihe, alten Score oder Ersatzwert zurückgeben.

3. **Client-Erneuerung ausdrücklich modellieren.**  
   Vorschlag: optionaler `client_factory`-Parameter, bis `lade_kurse` durchgereicht. Die Factory unterstützt wie `get_client` das Argument `force_new`.

   Für den Nightly beispielsweise:

   ```python
   _saison.fuer_ticker(ticker, client_factory=_get_client)
   ```

   Nach einem Transportabbruch muss der Lader lokal wirklich zuweisen:

   ```python
   client = client_factory(force_new=True)
   ```

   **Nur `_client = None` reicht nicht:** Der Parameter `client` zeigt weiterhin auf das alte Objekt. Bei `57014` allein ist kein Client-Wechsel erforderlich.

   Explizit injizierte Test-/Sonderclients ohne Factory dürfen nicht still durch einen Produktionsclient ersetzt werden. Dort muss der fehlende Erneuerungsweg klar scheitern. Alle Produktionsaufrufer entsprechend umstellen.

   Auch nachgelagerte lokale Referenzen beachten: `vollauf` benutzt nach dem Laden denselben vorher gespeicherten Client für Writes und RPCs. Dieser Pfad muss nach einer Erneuerung ebenfalls den aktuellen Client beziehen: [stress_score.py:275](C:/dev/SeasonalEdge/shared/stress_score.py:275).

4. **Offset durch Keyset ersetzen, exakten Count behalten.**  
   Erste Seite aufsteigend mit `limit(1000)`, danach zusätzlich `.gt("date", letztes_datum)`. Strikt aufsteigende, eindeutige Daten und Cursor-Fortschritt prüfen; am Ende weiterhin `len(zeilen) == quell_n`.

   Voraussetzung ist eine eindeutige Datumsordnung je Ticker und ein passender Index, serverseitig lesend zu prüfen. Count und Seiten sind weiterhin getrennte Datenbank-Snapshots: Die Prüfung ist keine Transaktionsgarantie bei parallelen Historienänderungen. Deshalb mindestens die zusätzliche Datumsprüfung aufnehmen.

5. **Die beobachteten Statistik-Upserts separat absichern.**  
   Dieselbe selektive Retry-Hilfe auf einzelne idempotente Upsert-Anfragen anwenden. Jeder Wiederholversuch baut seine Anfrage mit einem neu bezogenen Client auf. Nicht eine schon gebaute Query oder einen geschlossenen Client in der Closure festhalten.

6. **TDOM/TDOY vor der Aggregation reparieren.**  
   Erst die Folgepreise mittels `shift` bestimmen, dann Renditen nur für endliche, positive Ein- und Ausstiegspreise zulassen. Ungültige Zeilen vorher zu löschen würde zwei weiter auseinanderliegende Sitzungen verbinden. Anschließend Mittelwert, Median, Gewinnquote und Fallzahl auf derselben gültigen Stichprobe berechnen. `inf` keinesfalls zu null machen.

   Zusätzlich den fertigen Payload auf Endlichkeit prüfen und bei Verstoß einen Datenfehler melden.

Für die Diagnose pro Fehlversuch **Ticker, Stufe `count/page`, Cursor beziehungsweise Offset, Versuch, Exception-Klasse, Fehlercode und Dauer** protokollieren. Damit lässt sich erstmals feststellen, welcher Teil die 57014 auslöst.

## Testvorschlag

Die folgenden Tests müssen die **echten Produktionsfunktionen** mit einer zustandsbehafteten Supabase-Attrappe ausführen:

| Fall | Erforderliche Aussage |
|---|---|
| Erste Count-Anfrage wirft echte `APIError` mit Code `57014`, danach Erfolg | Vollständige Reihe kommt zurück; Retry fehlt → Test rot |
| Seite 2 wirft einmal `57014` | Keine Teilreihe und keine doppelten Zeilen; vollständiger Neustart nachweisbar |
| Client A wirft `RemoteProtocolError` mit GOAWAY-Darstellung | A bleibt dauerhaft defekt; nur Client B kann liefern; Factory wurde mit `force_new=True` aufgerufen |
| Timeout/Netzwerkabbruch | Begrenzte Wiederholung, danach Erfolg oder `LadeFehler` |
| `42501`, Schemafehler, `ValueError` | Genau ein Versuch, keine Erneuerung |
| Transienter Fehler in allen Versuchen | Exakt N Versuche, danach `LadeFehler`; weder Berechnung noch Score-Write |
| Count fehlt, ist zu groß oder zu klein | Kein gültiges Ergebnis; Count 0 mit leerer Reihe bleibt zulässig |
| 1000/1001/2000 Zeilen, doppelte oder rückläufige Datumsgrenze | Korrektes Seitenende; ungültiger Cursor wird abgelehnt |
| Null-/NaN-/Inf-Open sowie ungültiger Folgepreis | Keine unendlichen Renditen; Fallzahl und Gewinnquote stimmen mit Handreferenz überein |
| Nightly über echten `_get_client()`-Einstieg | Erholter Fehler erzeugt keinen endgültigen Phasenfehler; ausgeschöpfter Fehler erzeugt Exit 1 |

Die vorhandenen Wächter prüfen bereits Ladeabbruch und falschen Count, aber keine erfolgreiche Erholung: [verify_stress_ampel.py:496](C:/dev/SeasonalEdge/scripts/verify_stress_ampel.py:496).

**Entscheidende Mutationen:** Retry auf einen Versuch reduzieren, Client-Neuzuweisung entfernen, Count-Prüfung entfernen, Cursorprüfung entfernen, Endlichkeitsfilter entfernen. Jede Mutation muss den vorgesehenen Test rot machen. Für spätere dateibasierte Mutationstests gelten `_atomar_schreiben`, eindeutiger Anker und grüne Grundlinie; ein fehlender Anker zählt als ungültig.

Read-only ausgeführt wurden die beschriebenen Speicherproben am echten Kurslader und Renditecode. Keine Dateien geändert und keine Datenbank angesprochen.
tokens used
114.484
## Befunde

1. **Hypothese 1 ist sehr plausibel; die feste Grenze von 10 000 Anfragen ist noch nicht bewiesen.**  
   Der Nightly ruft zwar wiederholt `_get_client()` auf, erhält aber den gecachten Singleton: [nightly_refresh.py:143](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:143), [supabase_client.py:20](C:/dev/SeasonalEdge/shared/supabase_client.py:20).

   HTTP/2 verwendet für Client-Streams ungerade IDs; `19999` entspricht bei fortlaufender Vergabe dem 10 000. Stream. `error_code:0` passt zu einem GOAWAY ohne Protokollfehler. `last_stream_id` bezeichnet allerdings den höchsten möglicherweise bearbeiteten Stream, nicht zwingend die gerade gescheiterte Anfrage. Das spricht für ein Verbindungslimit, belegt aber weder den auslösenden Proxy noch dessen Konfiguration. Der Zähler gilt **je Verbindung**, nicht je Supabase-Client oder Gesamtlauf. [HTTP/2-Spezifikation](https://www.rfc-editor.org/rfc/rfc9113.html)

   Der angezeigte `ConnectionTerminated` ist normalerweise die Darstellung eines HTTP/2-Ereignisses innerhalb eines `RemoteProtocolError`. Die konkrete Exception-Klasse sollte künftig mitgeloggt werden. [httpcore-Implementierung](https://raw.githubusercontent.com/encode/httpcore/master/httpcore/_sync/http2.py)

2. **Hypothese 2 beschreibt reale Kosten, lokalisiert aber den konkreten Timeout noch nicht.**  
   [stress_score.py:187](C:/dev/SeasonalEdge/shared/stress_score.py:187) führt **einmal pro Ticker** eine exakte Zählung aus; danach folgen Offset-Seiten ohne erneuten Count, ab [stress_score.py:190](C:/dev/SeasonalEdge/shared/stress_score.py:190). `limit(1)` begrenzt dabei den Datenkörper, ersetzt die vollständige Zählung aber nicht. Exakte Counts können teuer sein. [PostgREST-Dokumentation](https://docs.postgrest.org/en/v10/api.html#exact-count)

   Tiefe Offsets verursachen zusätzliche Arbeit, weil PostgreSQL übersprungene Zeilen trotzdem berechnen muss. Keyset beseitigt diese wiederholte Überspringarbeit; „konstant“ ist die Laufzeit deswegen nicht garantiert und setzt einen passenden Zugriffspfad voraus. [PostgreSQL-Dokumentation](https://www.postgresql.org/docs/18/queries-limit.html)

   **Aus dem heutigen Fehlertext lässt sich Count gegen Seite 26 nicht unterscheiden.** Alle Abruffehler werden identisch verpackt: [stress_score.py:198](C:/dev/SeasonalEdge/shared/stress_score.py:198). Last, Planerstatistiken und Rechenstufe bleiben zusätzliche Ursachen; die drei neuesten `CLAUDE.md`-Einträge dokumentieren diese bereits für den November-Ausfall.

3. **Hypothese 3 passt zum Code, mit einer Präzisierung: Bei `open_to_next_open` ist der Nenner der aktuelle Open.**  
   Die Rechnung lautet `(nächster Open − aktueller Open) / aktueller Open`: [tdom_analysis.py:73](C:/dev/SeasonalEdge/shared/tdom_analysis.py:73). TDOM und TDOY entfernen anschließend nur `NaN`; `inf` bleibt enthalten: [tdom_analysis.py:113](C:/dev/SeasonalEdge/shared/tdom_analysis.py:113), [tdoy_analysis.py:83](C:/dev/SeasonalEdge/shared/tdoy_analysis.py:83).

   Die Serialisierung übernimmt Mittelwert und Median ungeprüft; die Standardabweichung wird nur auf `isnan`, nicht auf Endlichkeit geprüft: [cache_manager.py:176](C:/dev/SeasonalEdge/shared/cache_manager.py:176), [cache_manager.py:237](C:/dev/SeasonalEdge/shared/cache_manager.py:237).

   Eine Offline-Probe des echten Renditecodes mit Open `[100, 0, 110]` ergibt `[-100, inf, NaN]`; `inf` überlebt den Filter. **Der Mechanismus ist bestätigt, der damalige MDAX-Eingabefehler nicht.** Die Statistik stammt hier aus dem Yahoo-DataFrame, nicht aus dem Supabase-Vollhistorielader: [nightly_refresh.py:77](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:77), [nightly_refresh.py:158](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:158).

   „Seither nicht wieder aufgetreten“ gilt nur für die vorgelegten Meldungen. Zudem wurden TDOM/TDOY-Schreibfehler vor v66.29 verschluckt; der 15.11. kann auch der erste **sichtbare** Vorfall gewesen sein.

4. **Der bestehende Retry hilft diesen Nightly-Pfaden nicht.**  
   `_with_retry` erfasst weder PostgREST-Code `57014` noch sämtliche Netzwerkfehler: [supabase_client.py:123](C:/dev/SeasonalEdge/shared/supabase_client.py:123). Seine einzigen gefundenen Produktionsverwendungen sind zwei Polymarket-Upserts: [supabase_client.py:819](C:/dev/SeasonalEdge/shared/supabase_client.py:819), [supabase_client.py:835](C:/dev/SeasonalEdge/shared/supabase_client.py:835).

   Insbesondere schreiben Monthly- und TDOM-Stats direkt ohne diesen Wrapper: [supabase_client.py:453](C:/dev/SeasonalEdge/shared/supabase_client.py:453), [supabase_client.py:483](C:/dev/SeasonalEdge/shared/supabase_client.py:483). **Ein Retry ausschließlich im Kurslader behebt deshalb nicht alle beobachteten Rotläufe.**

   Der Import-Fallback `retriable = (Exception,)` wäre für die geforderte selektive Wiederholung ungeeignet: [supabase_client.py:125](C:/dev/SeasonalEdge/shared/supabase_client.py:125).

5. **Der heutige Ladefehler-Vertrag ist richtig; Retry gehört unter diesen Vertrag.**  
   Abruffehler werden zu `LadeFehler`, eine abweichende Zeilenzahl ebenfalls: [stress_score.py:198](C:/dev/SeasonalEdge/shared/stress_score.py:198), [stress_score.py:200](C:/dev/SeasonalEdge/shared/stress_score.py:200). Erst nach erfolgreichem Laden berechnet `fuer_ticker` den Score: [saison_score_betrieb.py:21](C:/dev/SeasonalEdge/shared/saison_score_betrieb.py:21).

   Weitere Aufrufer von **diesem** `stress_score.lade_kurse`:

   | Aufrufer | Stelle |
   |---|---|
   | Saison-Score, damit auch Nightly und Vollscanner | [saison_score_betrieb.py:21](C:/dev/SeasonalEdge/shared/saison_score_betrieb.py:21), [full_scanner_run.py:69](C:/dev/SeasonalEdge/scripts/full_scanner_run.py:69) |
   | Stress-Vollauf | [stress_score.py:270](C:/dev/SeasonalEdge/shared/stress_score.py:270) |
   | Stress-Trockenlauf | [compute_regime_scores.py:47](C:/dev/SeasonalEdge/scripts/compute_regime_scores.py:47) |
   | Health-Nachrechnung für SPY | [daily_health_check.py:858](C:/dev/SeasonalEdge/scripts/daily_health_check.py:858) |
   | `stress_fuer_ticker` | [stress_score.py:210](C:/dev/SeasonalEdge/shared/stress_score.py:210); außerhalb der Definition nur Testaufrufe gefunden |

   `shared.data.lade_kurse` ist eine andere Funktion.

6. **Weitere Lader sind betroffen, allerdings überwiegend ohne `count="exact"`.**

   | Lader | Aktuelles Muster |
   |---|---|
   | [supabase_client.py:142](C:/dev/SeasonalEdge/shared/supabase_client.py:142) `fetch_prices` | Vollhistorie, Offset, kein Retry, kein Count |
   | [data.py:174](C:/dev/SeasonalEdge/shared/data.py:174) `lade_closes` | Vollhistorie oder Zeitraum, Offset, kein Retry/Count |
   | [data.py:233](C:/dev/SeasonalEdge/shared/data.py:233) `lade_kurse` | Vollhistorie oder Zeitraum, Offset, kein Retry/Count; prüft `None` und Datumsordnung |
   | [backfill_new_ticker.py:44](C:/dev/SeasonalEdge/scripts/backfill_new_ticker.py:44) `vorhandene_daten` | Gesamte Datumsmenge, Offset, kein Retry/Count |
   | [backfill_tdoy.py:50](C:/dev/SeasonalEdge/scripts/backfill_tdoy.py:50) `lade` | Optional begrenzte Historie, Offset, kein Retry/Count |
   | [fix_missing_days.py:56](C:/dev/SeasonalEdge/scripts/fix_missing_days.py:56) `get_db_dates` | Datumsbereich, Offset, kein Retry/Count |
   | [kurse_messen.py:63](C:/dev/SeasonalEdge/scripts/perf/kurse_messen.py:63) `variante_f` | Tatsächlich Count + Offset ohne Retry; bewusst alte Benchmark-Variante |

   Unter den geprüften Python-Produktionsladern fand ich **keinen zweiten vollständigen Doppelgänger** mit Count + Offset. Die ersten drei sind die vorrangigen weiteren Reparaturstellen. Bei einigen schwächeren Ladern wird `data=None` als Seitenende behandelt; das sollte ebenfalls kein erfolgreicher Teilbestand werden.

   Verwandte Offset-Pfade gibt es außerdem beim Stress-Rücklesen und bei der begrenzten Newsletter-Historie: [stress_score.py:297](C:/dev/SeasonalEdge/shared/stress_score.py:297), [daily_report.py:330](C:/dev/SeasonalEdge/shared/daily_report.py:330). Der aktuelle Browser-Kurslader verwendet bereits Keyset und Retry: [kurse.js:17](C:/dev/SeasonalEdge/landing/js/kurse.js:17).

7. **Nach ausgeschöpften Versuchen weiterhin rot ist hier richtig.**  
   Der Nightly arbeitet die übrigen Ticker weiter ab und sammelt endgültige Fehler: [nightly_refresh.py:149](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:149), [nightly_refresh.py:173](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:173). Erst am Ende folgt Exit 1: [nightly_refresh.py:613](C:/dev/SeasonalEdge/scripts/nightly_refresh.py:613).

   Ein behobener Zwischenfehler kann als Warnung erscheinen. Ein endgültig fehlender Score bleibt dagegen ein unvollständiger Lauf — auch bei 369 erfolgreichen Tickern. Eine gelbe Gesamteinstufung wäre eine bewusste Änderung des Betriebsvertrags und sollte nicht Bestandteil dieser Reparatur sein.

## Reparaturvorschlag

**Retry im Lader, Fehleraggregation im Nightly.** Nicht den gesamten Ticker einschließlich Downloads und Writes wiederholen.

1. **Eine kleine gemeinsame Fehlerklassifikation verwenden.** Wiederholbar sind:
   - strukturierter PostgREST-Code `57014`;
   - `httpx.RemoteProtocolError`;
   - `httpx.TimeoutException`;
   - passende `httpx.NetworkError`-Unterklassen für Verbindungs-, Lese- und Schreibabbrüche.

   Rechte-/Schemafehler, ungültige JSON-Zahlen und unbekannte Exceptions sofort weiterreichen. Keine allgemeine Textsuche nach „timeout“ oder „ConnectionTerminated“; gegebenenfalls die erhaltene Ursachenkette prüfen.

2. **Im Kurslader höchstens drei vollständige Ladeversuche mit kurzem Backoff und Jitter.**  
   Jeder Versuch beginnt mit neuer Zählung, leerer Zeilenliste und zurückgesetztem Cursor. Erst nach vollständigem Erfolg bereinigen und zurückgeben. Nach dem letzten Fehler `LadeFehler` mit `raise … from e`; niemals Teilreihe, alten Score oder Ersatzwert zurückgeben.

3. **Client-Erneuerung ausdrücklich modellieren.**  
   Vorschlag: optionaler `client_factory`-Parameter, bis `lade_kurse` durchgereicht. Die Factory unterstützt wie `get_client` das Argument `force_new`.

   Für den Nightly beispielsweise:

   ```python
   _saison.fuer_ticker(ticker, client_factory=_get_client)
   ```

   Nach einem Transportabbruch muss der Lader lokal wirklich zuweisen:

   ```python
   client = client_factory(force_new=True)
   ```

   **Nur `_client = None` reicht nicht:** Der Parameter `client` zeigt weiterhin auf das alte Objekt. Bei `57014` allein ist kein Client-Wechsel erforderlich.

   Explizit injizierte Test-/Sonderclients ohne Factory dürfen nicht still durch einen Produktionsclient ersetzt werden. Dort muss der fehlende Erneuerungsweg klar scheitern. Alle Produktionsaufrufer entsprechend umstellen.

   Auch nachgelagerte lokale Referenzen beachten: `vollauf` benutzt nach dem Laden denselben vorher gespeicherten Client für Writes und RPCs. Dieser Pfad muss nach einer Erneuerung ebenfalls den aktuellen Client beziehen: [stress_score.py:275](C:/dev/SeasonalEdge/shared/stress_score.py:275).

4. **Offset durch Keyset ersetzen, exakten Count behalten.**  
   Erste Seite aufsteigend mit `limit(1000)`, danach zusätzlich `.gt("date", letztes_datum)`. Strikt aufsteigende, eindeutige Daten und Cursor-Fortschritt prüfen; am Ende weiterhin `len(zeilen) == quell_n`.

   Voraussetzung ist eine eindeutige Datumsordnung je Ticker und ein passender Index, serverseitig lesend zu prüfen. Count und Seiten sind weiterhin getrennte Datenbank-Snapshots: Die Prüfung ist keine Transaktionsgarantie bei parallelen Historienänderungen. Deshalb mindestens die zusätzliche Datumsprüfung aufnehmen.

5. **Die beobachteten Statistik-Upserts separat absichern.**  
   Dieselbe selektive Retry-Hilfe auf einzelne idempotente Upsert-Anfragen anwenden. Jeder Wiederholversuch baut seine Anfrage mit einem neu bezogenen Client auf. Nicht eine schon gebaute Query oder einen geschlossenen Client in der Closure festhalten.

6. **TDOM/TDOY vor der Aggregation reparieren.**  
   Erst die Folgepreise mittels `shift` bestimmen, dann Renditen nur für endliche, positive Ein- und Ausstiegspreise zulassen. Ungültige Zeilen vorher zu löschen würde zwei weiter auseinanderliegende Sitzungen verbinden. Anschließend Mittelwert, Median, Gewinnquote und Fallzahl auf derselben gültigen Stichprobe berechnen. `inf` keinesfalls zu null machen.

   Zusätzlich den fertigen Payload auf Endlichkeit prüfen und bei Verstoß einen Datenfehler melden.

Für die Diagnose pro Fehlversuch **Ticker, Stufe `count/page`, Cursor beziehungsweise Offset, Versuch, Exception-Klasse, Fehlercode und Dauer** protokollieren. Damit lässt sich erstmals feststellen, welcher Teil die 57014 auslöst.

## Testvorschlag

Die folgenden Tests müssen die **echten Produktionsfunktionen** mit einer zustandsbehafteten Supabase-Attrappe ausführen:

| Fall | Erforderliche Aussage |
|---|---|
| Erste Count-Anfrage wirft echte `APIError` mit Code `57014`, danach Erfolg | Vollständige Reihe kommt zurück; Retry fehlt → Test rot |
| Seite 2 wirft einmal `57014` | Keine Teilreihe und keine doppelten Zeilen; vollständiger Neustart nachweisbar |
| Client A wirft `RemoteProtocolError` mit GOAWAY-Darstellung | A bleibt dauerhaft defekt; nur Client B kann liefern; Factory wurde mit `force_new=True` aufgerufen |
| Timeout/Netzwerkabbruch | Begrenzte Wiederholung, danach Erfolg oder `LadeFehler` |
| `42501`, Schemafehler, `ValueError` | Genau ein Versuch, keine Erneuerung |
| Transienter Fehler in allen Versuchen | Exakt N Versuche, danach `LadeFehler`; weder Berechnung noch Score-Write |
| Count fehlt, ist zu groß oder zu klein | Kein gültiges Ergebnis; Count 0 mit leerer Reihe bleibt zulässig |
| 1000/1001/2000 Zeilen, doppelte oder rückläufige Datumsgrenze | Korrektes Seitenende; ungültiger Cursor wird abgelehnt |
| Null-/NaN-/Inf-Open sowie ungültiger Folgepreis | Keine unendlichen Renditen; Fallzahl und Gewinnquote stimmen mit Handreferenz überein |
| Nightly über echten `_get_client()`-Einstieg | Erholter Fehler erzeugt keinen endgültigen Phasenfehler; ausgeschöpfter Fehler erzeugt Exit 1 |

Die vorhandenen Wächter prüfen bereits Ladeabbruch und falschen Count, aber keine erfolgreiche Erholung: [verify_stress_ampel.py:496](C:/dev/SeasonalEdge/scripts/verify_stress_ampel.py:496).

**Entscheidende Mutationen:** Retry auf einen Versuch reduzieren, Client-Neuzuweisung entfernen, Count-Prüfung entfernen, Cursorprüfung entfernen, Endlichkeitsfilter entfernen. Jede Mutation muss den vorgesehenen Test rot machen. Für spätere dateibasierte Mutationstests gelten `_atomar_schreiben`, eindeutiger Anker und grüne Grundlinie; ein fehlender Anker zählt als ungültig.

Read-only ausgeführt wurden die beschriebenen Speicherproben am echten Kurslader und Renditecode. Keine Dateien geändert und keine Datenbank angesprochen.
