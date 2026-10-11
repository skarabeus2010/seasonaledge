# Kalender-Umstellung V1b — Code-Abnahme Runde 1 (Releasekennung, Seitensperre, Transportsperre)

Entwurf v6 freigegeben ([v6](2026-10-11_kalender_v1b_entwurf_v6.md) + [Antwort](2026-10-11_kalender_v1b_entwurf_v6_antwort.md);
fortgeltend v1–v5). Read-only, nichts schreiben, Mutationstest NICHT ausführen. Änderungen: `git diff` + neue Dateien.
Kanonisch: docs/KALENDER_UMSTELLUNG.md Abschnitt „Releasekennung und Seitensperre".

<task>Erfüllt der Code den freigegebenen Entwurf (V1b-1 + V1b-2)? Wo weicht er ab, wo kann eine Seite dauerhaft
gesperrt bleiben, wo prüfen die Proben eine freundlichere Welt?</task>

## Inhalt
- **Neu:** `landing/js/methode.js` (Methode, Kennung, Sperre; Hüllen fetch/Response, Storage, Einfügewege +
  innerHTML/outerHTML, ApexCharts per Setter auch bei späterer Bibliothek; Neulademarke 120 s; Prüfnaht
  `window.__saNeuladen` nur für jsdom), `shared/kalender_methode.py`, `deploy/release_setzen.py`,
  `scripts/verify_einbindung.py`, `scripts/verify_release_sperre.py`, `scripts/js/probe_release_transport.js`,
  `scripts/js/probe_release_seite.js`, `scripts/js/release_harness.js`, `scripts/verify_release_mutation.py`.
- **Geändert:** 24 eigene JS-Dateien (Prüfzeile als erste Anweisung; `boersenkalender.js` über
  `scripts/boersenkalender/api.js` + Generator), 48 HTML + 2 Blog-Templates (Bootstrap, nur Einfügungen),
  `kurse.js` (Sperrprüfung vor fetch/zwischen Blöcken/vor Wiederholung/vor Übernahme/kein Rückfall/keine wartende
  Ladung, `_abbrechenAlle`, Zähler `eigeneGesamt`), `app.js` (`SA.supabase.get/getAll`, `loadAnalytics`),
  `tour.js`/`i18n.js` (Lader prüfen `__gesperrt`), `deploy.yml` (RELEASE einmal, Normalisieren nach dem Vorspulen,
  EXIT-Falle, letzter Schritt nach allen HTML-Erzeugern, zwei Gate-Schritte), `inject_credentials.sh` (RELEASE als
  Cache-Buster), `nginx.conf` (must-revalidate für /rechtliches, /ueber-uns, /landing/*.html), 22 Harnesse
  (echte methode.js über den Helfer), Fixtures der Seitenprobe (fachfremd nachgezogen, LIESMICH).
- Abweichung vom Entwurf, bitte bewerten: ApexCharts steht auf 31 Seiten HINTER den eigenen Skripten — statt die
  Seiten umzusortieren hüllt `methode.js` über einen Setter auf `window.ApexCharts`.

## Nachweise (Windows lokal)
`verify_einbindung` 22/22 (inkl. Simulation release_setzen: Normalisieren alter Ausgaben ohne Bootstrap, Setzen,
fremde Methode → Exit 3 ohne Schreiben); `verify_release_sperre` 93/93 (Transport a–f + d2 je mit/ohne Hülle +
Kontrollen; Seite: gleich, a/b beide Richtungen, c spät während Rechnung mit über die Sperre laufendem render(),
d zweiter Versuch, e Speicherfehler, f fetch-Phasen, g Skript/Einfügung/Speicher/innerHTML/Chart/Analytics mit
bereits erfülltem Body — je mit Kontrolle); `verify_seiten_kurse` 313/313 (vorher = nachher); `verify_kurse` 125;
alle übrigen Harnesse grün (Liste im Antworttext). Mutationstest: Ergebnis folgt.

## Fokus
1. Kann eine Seite nach einem gewöhnlichen Deploy dauerhaft gesperrt bleiben (Kennungsquelle, EN-Build, Blog im
   Container, seo/tools, Cache, Teilfehler + EXIT-Falle)?
2. Hüllen in `methode.js`: Normalbetrieb ohne Sperre unverändert (Response-Hülle per `defineProperty`, `clone`,
   supabase-js, Storage-Hülle auf dem Prototyp, Setter-Hülle innerHTML, ApexCharts-Statics)?
3. Lücken im Transportvertrag (v9 Punkte 1–3), die die Proben nicht treffen.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 35 Zeilen.
