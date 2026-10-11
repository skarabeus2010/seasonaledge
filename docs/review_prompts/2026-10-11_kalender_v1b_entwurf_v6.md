# Kalender-Umstellung V1b — Entwurf v6 (vor dem Code)

Runde 5: [Entwurf v5](2026-10-11_kalender_v1b_entwurf_v5.md) · [Antwort](2026-10-11_kalender_v1b_entwurf_v5_antwort.md) (2 Befunde).
Alles aus v5 und früher gilt, außer dem folgenden Punkt. Read-only.

<task>Ist der Entwurf mit der präzisierten Netz-Zusage als Bauvorlage freigegeben?</task>

## Netz-Zusage präzisiert: Datenanfragen, nicht jede Ressource
Die Zusage „keine Netzanfrage" hatte ich in Entwurf v2 über den Plan hinaus ausgeweitet. Plan v8 §2.3 verlangt:
`SA.kurse.laden`/`SA.supabase.get` lehnen ab, „`fetch` auf `/landing/` wird nicht mehr angestoßen"; v9: „keine
weitere Netzanfrage" **im Kurslader und `SA.supabase.get/getAll`**. Zweck der Sperre ist, dass ein gesperrter Stand
**kein Ergebnis** erzeugt, zeigt oder dauerhaft ablegt — nicht, dass er keinerlei Bytes lädt.

Vertrag v6 (ersetzt v4 §2.1 und v5 §1 in diesem Punkt):
1. **Datenanfragen:** keine neue `fetch`-Anfrage (Hülle, gilt für `kurse.js`, `SA.supabase.*`, supabase-js, jeden
   direkten Abruf), laufende abgebrochen, Body-Lesen scheitert. `XMLHttpRequest`, `sendBeacon`, `EventSource`,
   `WebSocket` kommen in eigenen Dateien nicht vor — der Einbindungswächter verlangt das (Suche über eigene
   JS-Dateien und Inline-Skripte der Seiten); käme einer dazu, gehört er in die Hülle.
2. **Ressourcen** (Bild, Stylesheet, Schrift, Skript über Element/Attribut) sind **nicht** Teil der Netz-Zusage.
   Begründung je Art: ein nach der Sperre geladenes **Skript** scheitert an seiner ersten Anweisung (eigene Dateien)
   bzw. ist Fremdcode ohne Zugriff auf Ergebnisse (Analytics, Tour-Bibliothek von CDN); **Bilder/Stylesheets/Schriften**
   tragen keine Daten in die Rechnung und werden nicht sichtbar (Dokument ersetzt, Observer). Die synchronen
   Einfügehüllen aus v5 §1 bleiben, aber als Mittel gegen **Skriptausführung und Sichtbarkeit**, nicht als
   Netz-Zusage; `loadAnalytics`/`tour.js` prüfen weiterhin selbst (v5 §2).
3. **Proben mit positiver Kontrolle je geprüfter Art:** (a) `fetch` — ungesperrt zählt der Stub die Anfrage,
   gesperrt bleibt sie aus, Hülle entfernt → benannte Prüfung rot; (b) Body-Lesen — dasselbe Muster;
   (c) Skriptausführung nach Sperre — ein nachgeladenes eigenes Skript (jsdom `runScripts`) setzt ungesperrt einen
   Marker, gesperrt nicht; Prüfzeile ohne `__gesperrt`-Vorrang → rot; (d) Sichtbarkeit — ungesperrt erscheint der
   Knoten, gesperrt nicht. Keine Bildprobe, weil Bilder nicht zur Zusage gehören.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
