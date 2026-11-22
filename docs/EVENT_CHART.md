# Event-Chart (`/event-chart`, `/en/event-chart`)

Seit 2026-11-22. Kerzenchart eines Basiswerts mit Marktterminen als senkrechte Linien. Darunter, wie ein Indikator,
der durchschnittliche Kursverlauf rund um eine gewählte Terminart.

## Dateien

| Datei | Rolle |
|---|---|
| `landing/pages/event-chart.html` | Seite: Laden, Darstellung, Steuerung |
| `landing/js/event-chart-compute.js` | Rechenkern `SA.eventChart` (`achse`, `idxAb`, `quantil`, `durchschnitt`) |
| `landing/data/event_termine.json` | Terminliste, **committet** (kein Cron-Ausgang) |
| `scripts/build_event_termine.py` | Erzeuger der Terminliste (`--pruefen` vergleicht nur) |
| `scripts/verify_event_chart.py` + `scripts/js/probe_event_chart.js` | Wächter im Deploy-Gate (`--mutation`) |

Eingetragen in `deploy/nginx.conf` (`location = /event-chart`), Nav und Footer (Events, nach VIXpiration),
`_EN_PAGE_META` in `landing/js/i18n.js`, `landing/i18n/en.json` (`ec.*`, `nav.event_chart`) und
`scripts/fixtures/einbindung_manifest.json` (lädt `boersenkalender.js`).

## Termine

| Code | Termin | Quelle | Bereich |
|---|---|---|---|
| FOMC | Fed-Zinsentscheid | `shared/fed_dates.FOMC_MEETING_DATES` ohne Strategietreffen | 2000–2027 |
| FOMCX | außerplanmäßige Fed-Sitzung mit Zinsbeschluss | Liste im Erzeuger | 2001–2020 |
| EZB | EZB-Zinsentscheid | `shared/central_banks.ECB_MEETING_DATES` | **ab 2015** |
| MIN | Fed-Protokoll | `PROTOKOLLE_ALT` (federalreserve.gov, 2000–2021) + `FED_MINUTES_DATES`; künftige = Sitzung + 21 Tage, nächster NYSE-Handelstag | 2000–2027 |
| JOBS | US-Arbeitsmarktbericht | BLS-Regel im Erzeuger, Shutdown-Ausnahmen 2013/2025 | 2000–2027 |
| OPEX / TW | Optionsverfall / Großer Verfall | bis 2019 `produkttermine.opex_regel`, ab 2020 Cboe-Katalog | 2000–2027 |
| Q | Quartalsende-Verfall | letzter NYSE-Handelstag im Quartal (`shared/sitzungen.py`) | 2000–2027 |
| VIX | VIX-Verfall | Cboe-Katalog ab Kontrakt 2015-09 | 2015–2027 |

Das Prüfdatum des Erzeugers ist fest (`PRUEFDATUM`), damit der Gate-Vergleich reproduzierbar ist. Neue Fed- oder
EZB-Termine: Quellmodul ändern, `py -3.14 scripts/build_event_termine.py`, JSON committen. Der Wächter wird rot,
wenn das JSON nicht zum Erzeuger passt.

**Nicht enthalten:** EZB-Termine vor 2015, außerplanmäßige EZB-Sitzungen (z. B. 18.03.2020), Eurex-Verfall,
andere Notenbanken (BoE, BoJ, SNB).

## Rechnung

- **Achse:** Handelstage des Basiswerts (Kurszeilen ab 1999), dahinter Werktage bis zum letzten Termin, damit
  künftige Termine sichtbar sind.
- **Termin an einem Tag ohne Kurs** (Feiertag der Heimatbörse) → nächster Handelstag.
- **Durchschnittsverlauf:** Anker = Schluss am Termintag. Pfad `S[a+k] / S[a] · 100` für `k = −vor … +nach`. Es zählen
  nur Termine mit vollständigem Fenster, und zwei Termine auf demselben Anker zählen einmal. Mittel, Median und
  25/75-%-Quantile (linear wie numpy). Unter 5 Terminen wird kein Verlauf gezeigt.
- **Vergleich:** derselbe Pfad für jeden Handelstag ab dem Startdatum. Das Startdatum ist letzter Kurstag minus N
  Jahre, „seit 2000“ = 2000-01-01. Für EZB wird es auf 2015-01-01 angehoben, damit Termine und Vergleich dieselben
  Jahre abdecken.
- **EZB-Automatik:** Die EZB wird eingeschaltet, wenn `SA.boersenkalender.boerse(ticker)` XETRA, EURONEXT oder MILAN
  liefert (= `shared/central_banks.EXCHANGE_TO_CENTRAL_BANK` → ECB). Für alle anderen Basiswerte lässt sie sich
  zuschalten.
- **Darstellung:** Über 600 Handelstagen im Ausschnitt wird eine Linie statt Kerzen gezeichnet. Zoom und Verschieben
  zeichnen den Chart neu, damit y-Bereich und Terminlinien zum sichtbaren Teil passen. Es gibt keine Wertebeschriftung
  an den Punkten.

Beschreibend, ohne Signifikanztest. So steht es auf der Seite.

## Herkunft

Entstanden als Artifact-Entwurf (Versionen 1–7, 2026-11-20 bis 22). Die Nutzerwünsche aus den Versionen sind
übernommen: Durchschnittsverlauf direkt unter dem Chart, Achsen dynamisch, keine Werte an den Linien, EZB für
europäische Titel. Gemessen im Entwurf (echte Kurse): DAX um EZB-Entscheide seit 2015, 94 Termine, nach 20 Tagen
+0,85 % gegen +0,77 % an normalen Tagen, 50 von 94 positiv. Das ist kaum ein Unterschied.

## Offen

- EZB-Termine 2000–2014 aus der amtlichen EZB-Liste ergänzen (`ECB_MEETING_DATES` sagt „seit 2000“, enthält aber erst
  2015). Dabei prüfen, was `/zentralbanken` daraus macht.
- Außerplanmäßige EZB-Sitzungen als eigene Art.
- Eurex-Verfall für europäische Titel (eigene Regeln, nicht der US-Verfall).
- BoE für LSE, BoJ für TSE, SNB für SIX nach demselben Muster wie EZB.
