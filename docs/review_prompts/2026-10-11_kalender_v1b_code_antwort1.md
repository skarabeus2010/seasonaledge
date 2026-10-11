**Urteil:** Nicht freigegeben. V1b hat einen Fehlerweg mit dauerhafter Seitensperre und Lücken im Prüfvertrag.

**Befunde**

- **P1 – Wiederherstellung ohne Releasekennung:** [deploy.yml:172](/C:/dev/SeasonalEdge/.github/workflows/deploy.yml:172) setzt `landing/` zurück. Scheitert anschließend das Vorspulen, läuft nur `inject_credentials.sh`, kein `release_setzen.py`. JS trägt danach Platzhalter, vorhandene EN-/Blog-Ausgaben behalten ihre alte Kennung: Neuladen behebt diesen Mischstand nicht. Auch die erste Normalisierung liegt noch vor der Release-EXIT-Falle.
- **P2 – Fetch-Abbruchsignal verloren:** [methode.js:101](/C:/dev/SeasonalEdge/landing/js/methode.js:101) übernimmt ausschließlich `optionen.signal`. Bei `fetch(new Request(url, {signal}))` ersetzt die Hülle das Request-Signal. In-Memory bestätigt: Der Abbruch des Aufrufers erreicht den Transport nicht.
- **P2 – Cachevertrag unvollständig:** [nginx.conf:295](/C:/dev/SeasonalEdge/deploy/nginx.conf:295) liefert `/tools/` weiterhin mit `max-age=86400`, entgegen Entwurf v2. Der Wächter prüft diesen ausdrücklich geforderten HTML-Weg nicht.
- **P2 – Fehler-Exit kann grün werden:** [verify_release_sperre.py:45](/C:/dev/SeasonalEdge/scripts/verify_release_sperre.py:45) akzeptiert JSON und Endmarker ohne Prüfung von `r.returncode`. Ein nach der Ausgabe fehlgeschlagener Prozess kann damit als bestanden zählen.
- **P2 – Nachweise enger als zugesagt:** [probe_release_seite.js:130](/C:/dev/SeasonalEdge/scripts/js/probe_release_seite.js:130) lädt ausschließlich das Dashboard; Backtest-Engine und Tour fehlen. `f_fetch_phasen` prüft nur „Header erfüllt → Sperre → Body“, nicht Sperre während des Body-Lesens. ApexCharts ist ein Stub, supabase-js wird durch leeren Code ersetzt; deren Normalbetrieb wird damit nicht belegt.

**Auflagen**

- Release-Wiederherstellung ab dem ersten Eingriff in `landing/` absichern, einschließlich fehlgeschlagenem Vorspulen und erster Normalisierung.
- Request-Signal erhalten; Cacheprüfung um `/tools/` ergänzen; jeden nicht erfolgreichen Probe-Exit ablehnen.
- Die fehlenden Seiten-, Body- und Bibliothekspfade mit positiven Kontrollen prüfen. Die Setter-Lösung für spätes ApexCharts ist grundsätzlich plausibel.
- Read-only geprüft: drei bestehende Probe-Fälle und eine In-Memory-Abbruchprobe ausgeführt. Keine Dateien geschrieben, keine Mutationstests ausgeführt.
