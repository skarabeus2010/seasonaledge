**FREIGABE (Code): ja**

Keine P1-/P2-Befunde. Ein kleiner P3-Befund:

- **P3 – HTTP-Prüfung hängt an den Inhaltsprüfungen:** In [daily_health_check.py:454](/C:/dev/Seasonaledge/scripts/daily_health_check.py:454) liegt sie im selben `try`. Scheitert vorher etwa das JSON-Parsen, entfällt der HTTP-Check vollständig. Der Gesamtstatus wird trotzdem rot; der ursprüngliche 0600-Fall wird erkannt. Für unabhängige Diagnose den HTTP-Block außerhalb dieses `try` ausführen.

Zu den drei Posten:

1. **HEAD ist geeignet.** nginx öffnet bei HEAD und GET dieselbe Datei und übersetzt `EACCES` in 403. Erst anschließend entfällt bei HEAD der Body. 0600 verursacht also bei fehlendem Leserecht des nginx-Workers auch für HEAD einen 403. [nginx-Quellcode](https://github.com/nginx/nginx/blob/master/src/http/modules/ngx_http_static_module.c). Statusbewertung, Redirect-Sperre und Vorrang von Rot gegenüber Netzfehlern passen.
2. **`indent=None` ist unkritisch.** Die produktiven Aufrufer betreffen die Skew-History; JSON-Struktur, Sperre, atomarer Austausch und Rechtebehandlung bleiben erhalten. Keine zeilenabhängigen Leser gefunden.
3. **Keine funktionale Earnings-Abhängigkeit übersehen.** Download-ICS verwendet dieselben Ereignislisten; statische JSON und abonnierbarer ICS-Feed erhalten keine Earnings aus ihrem Generator. Separate Filterchips gibt es nicht. Übrig bleiben lediglich ungenutzte Earnings-Einträge in `PREMIUM_TYPES`, `CHIP_LABELS` und CSS.

**Verifikation:** JS-Syntax, `git diff --check` und ein Node-Test für Premium-Abfrage, Dividendenanzeige und ICS-Export bestanden. Die Python-Testfälle konnte ich mangels ausführbarem Python nicht starten; den gemeldeten Live-Abruf habe ich nicht wiederholt. Keine Dateien verändert.
