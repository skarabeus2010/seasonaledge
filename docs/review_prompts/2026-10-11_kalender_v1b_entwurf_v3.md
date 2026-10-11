# Kalender-Umstellung V1b — Entwurf v3 (vor dem Code)

Runde 2: [Entwurf v2](2026-10-11_kalender_v1b_entwurf_v2.md) · [Antwort](2026-10-11_kalender_v1b_entwurf_v2_antwort.md) (4 Befunde).
Alles aus v2/v1 gilt, außer den folgenden Punkten. Read-only.

<task>Sind die vier Befunde aus Runde 2 im Entwurf aufgelöst? Ist er als Bauvorlage freigegeben?</task>

## 1 Auslieferbar zu jedem Zeitpunkt des Deploys (P1 erster Rollout)
`deploy/release_setzen.py <wert>` **normalisiert** statt nur zu ersetzen: in jeder HTML unter `landing/`
(inkl. `en/`), `blog/output/`, `seo/tools/`, die ein eigenes Skript (`/landing/js/…`) einbindet, wird ein fehlender
Bootstrap **eingefügt** (Inline `window.__SA_RELEASE=…;window.__SA_METHODE=…` + `methode.js` unmittelbar vor dem
ersten eigenen Skript) und jede Kennung auf `<wert>` gesetzt. Aufrufe im Deploy:
1. **Direkt nach dem Vorspulen** (neue JS-Dateien tragen den Platzhalter): `release_setzen.py '%%RELEASE%%'` —
   alte Blog-/EN-Ausgaben (mit oder ohne Bootstrap) passen damit sofort zu den frisch gezogenen Skripten; keine
   Seite ist im Deploy-Fenster gesperrt oder ohne Bootstrap.
2. **Als letzter Schritt** (und im `trap` bei Fehler): `release_setzen.py <RELEASE>` über alle Bäume + Abschlussprüfung.
**Grenze:** Normalisieren ist nur ohne Methodenwechsel erlaubt. Das HTML trägt `window.__SA_METHODE`; das Skript
vergleicht es mit `SA.kalenderMethode` aus `methode.js` und **verweigert** (Exit ≠ 0, nichts geschrieben), wenn eine
Ausgabe eine andere Methode trägt. V9 nutzt ausschließlich seinen eigenen Ablauf (Sicherung/Rückweg v5–v7).
Probe auf einer Kopie: Blog-/EN-Ausgaben **ohne** Bootstrap + neue Skripte; Fehler nach Schritt 1, nach der
Injection und nach dem EN-Build → jeweils alle Seiten auslieferbar (jsdom: keine Sperre, Rechnung wie vorher).

## 2 Charts: Vertrag über das Dokument, nicht über die Fortsetzung (P1)
Vertrag: **nach der Sperre enthält das Dokument kein Chart-Element mit Serien**, auch wenn ein vorher gestartetes
`render()`/Update später abschließt. Mittel: `replaceChildren` entkoppelt jedes Chart-Ziel vom Dokument (eine
Fortsetzung zeichnet in ein abgehängtes Element); der `MutationObserver` (jetzt auf `document.documentElement`,
Teilbaum, also auch `head`) entfernt jeden nach der Sperre eingefügten Knoten außer dem Hinweis. Probe: Chart-Stub
mit verzögertem `render()` (Abschluss nach der Sperre, schreibt Serien-Elemente in sein Ziel) → danach weder im
`body` noch irgendwo im Dokument ein Serienelement; Sperre besteht fort (`__gesperrt`, Hinweis sichtbar).

## 3 Fetch: Header, Body und Übernahme getrennt gesperrt (P2)
Die `fetch`-Hülle gibt eine **gehüllte Response** zurück: `json()/text()/arrayBuffer()/blob()/formData()` prüfen
`__gesperrt` vor dem Lesen **und** nach dem Auflösen (dann `ReleaseFehler` statt Wert); der `AbortController` bleibt
registriert, bis der Body gelesen oder verworfen ist. Ein vor der Sperre erfülltes Header-Promise liefert so keinen
Body mehr. Nachgeladene Skripte (`app.js` hängt nach `r.text()` Elemente an `head`): der Observer entfernt sie;
führt ein Skript dennoch aus, scheitert es an seiner ersten Anweisung (`__gesperrt` hat Vorrang). Probe: Sperre
(i) zwischen Headern und `text()`, (ii) während `text()`, (iii) nach `text()` vor der Übernahme → kein Wert, kein
Knoten in `head`/`body`.

## 4 Neulademarke wird nie durch `load` gelöscht (P2)
Die Marke `sa-release-neuladen` (Zeitstempel) wird **nur** durch Ablauf ungültig (120 s), nie durch ein Ereignis.
Höchstens ein automatisches Neuladen je 120 s, unabhängig davon, wann die Abweichung auftritt. Probe: dreimal
Abweichung **nach** `load` innerhalb von 120 s → genau ein automatisches Neuladen, danach Hinweis.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 25 Zeilen.
