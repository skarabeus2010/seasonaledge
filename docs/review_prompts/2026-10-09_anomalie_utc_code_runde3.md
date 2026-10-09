# Code-Review: Schritt U + Teil C — Runde 3

Repo `C:\dev\Seasonaledge`, Arbeitsstand (A/B sind inzwischen als 7efb02c committet und deployt). Vorgeschichte:
`..._code_runde1/2.md` + Antworten. Nur lesen. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Fall + Änderung;
am Ende genau eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.

## Korrektur zu R2 (Rang-Balken im Dashboard ohne CSS)
`anomalieHtml()` bindet sein CSS jetzt selbst ein (`if (typeof document !== 'undefined' && document.head)
this._ensureAnomalyCss();`) — die Darstellung bringt ihre Styles mit, egal welcher Aufrufer rendert (Dashboard-Karte,
Seitenabschnitt). `renderAnomalyInto` ruft es zusätzlich (idempotent über die Element-ID).

Wächter: `probe_anomalie_radar.js` hat einen minimalen DOM-Stub, der eingebundene `<style>`-IDs zählt;
`verify_anomalie_radar.py` verlangt `css == ["sa-anomaly-css"]` (genau einmal, trotz vieler Renderaufrufe) —
Prüfung `css_von_der_darstellung`, Mutation „CSS nur über renderAnomalyInto" (entfernt die Zeile in anomalieHtml).

## Belege
`verify_anomalie_radar.py --snapshot` **33/33**. Mutationstest läuft.
