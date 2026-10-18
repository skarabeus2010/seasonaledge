# Kalender V2 — Antwort Codex auf Code Runde 2 (2026-10-18)

**Urteil**

Noch keine Freigabe für V2. Typprüfung, EN-Einbindung und Inventar aus Runde 1 sind behoben; die ergänzten Abnahmeprüfungen erfüllen den vereinbarten Umfang noch nicht vollständig.

**Befunde**

- **P2 – Monatsüberlauf ohne exakten Sollwert:** [verify_holidays_fassade.py:366](/C:/dev/SeasonalEdge/scripts/verify_holidays_fassade.py:366) akzeptiert jedes Datum in einem späteren Monat. Für LSE ab 30.05.2026 besteht dadurch auch der geschlossene Sonntag 07.06.2026 die Prüfbedingung; korrekt ist 01.06.2026. Der geforderte unabhängige Nachfolgernachweis fehlt.
- **P2 – Monatsreferenzen unvollständig:** [verify_holidays_fassade.py:335](/C:/dev/SeasonalEdge/scripts/verify_holidays_fassade.py:335) prüft nur die vorhandenen elf Börsenlisten. Die vereinbarten Konventionsreferenzen CRYPTO 02/2028 und FOREX 12/2026 fehlen; LSE bleibt ausdrücklich ohne Börsenbeleg. Die Monatslisten-Auflage aus Runde 1 ist damit nur teilweise erfüllt.
- **P2 – Statusanzeige weiterhin nur stichprobenartig geprüft:** [verify_holidays_fassade.py:412](/C:/dev/SeasonalEdge/scripts/verify_holidays_fassade.py:412) prüft vier zusätzliche Header- und drei Converterfälle. Die 57 vereinbarten Übergangsfälle werden weiterhin nur gegen `K.status` geprüft, nicht vollständig durch beide Anzeigen. Dieser Teil des vierten R1-Befunds bleibt offen.

**Auflagen**

- Exakte, unabhängig belegte Monatsnachfolger und fehlende Monatsreferenzen ergänzen; alle 57 Statusfälle durch Header und Converter prüfen.
- Nachweis dieser Runde: **1.513 Teilprüfungen und 111 echte Seitenprüfungen bestanden**, ebenso die lesenden Einbindungsprüfungen einschließlich vorhandener EN-Seiten.
- Der unveränderte Gesamtwächter brach am gesperrten temporären Verzeichnis ab; die Seitenprüfung bestand separat mit einer ausschließlich im Prozess vorgenommenen Anpassung ohne temporäres Verzeichnis. Keine Projektdateien geändert, keine Mutationstests ausgeführt.
