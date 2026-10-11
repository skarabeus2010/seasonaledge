# Kalender-Umstellung V1b — Entwurf v5 (vor dem Code)

Runde 4: [Entwurf v4](2026-10-11_kalender_v1b_entwurf_v4.md) · [Antwort](2026-10-11_kalender_v1b_entwurf_v4_antwort.md) (1 Befund).
Alles aus v4 und früher gilt, außer dem folgenden Punkt. Read-only.

<task>Ist der Befund aus Runde 4 aufgelöst? Ist der Entwurf als Bauvorlage freigegeben?</task>

## Dynamische Ressourcen synchron gesperrt (P2)
1. **Zentral, synchron:** `methode.js` hüllt die Einfügewege `Node.prototype.appendChild/insertBefore/replaceChild`
   und `Element.prototype.append/prepend/after/before/replaceWith/insertAdjacentElement/insertAdjacentHTML` sowie die
   Setter `innerHTML/outerHTML`: bei `__gesperrt` werfen sie `ReleaseFehler` **bevor** der Browser etwas einfügt
   oder parst — das gilt auch für abgehängte Elemente (ein `<img src>` in `innerHTML` eines nicht eingehängten
   `div` lädt sonst). Einzige Ausnahme: der Hinweis der Sperre über eine interne Referenz. Damit startet nach der
   Sperre keine Ressourcenanfrage über Skript-, Link-, Bild- oder Iframe-Elemente, unabhängig vom Aufrufer.
2. **Zusätzlich ausdrücklich beim Verbraucher:** `loadAnalytics()` (`app.js`) und die Skript-/CSS-Ladung in
   `tour.js` prüfen `SA.__gesperrt` unmittelbar vor dem Erzeugen/Einfügen und brechen still ab — die zentrale
   Hülle ist die Absicherung, die Verbraucherprüfung macht den Vertrag am Aufrufer sichtbar. Der Einbindungswächter
   führt die Liste der dynamischen Ressourcenlader (Suche nach `createElement('script'|'link'|'img'|'iframe')`
   in eigenen Dateien und Seiten) und verlangt die Prüfung bei jedem.
3. Der Observer aus v3 bleibt als zweite Linie (entfernt Knoten, die auf anderem Weg entstehen).

**Probe** (jsdom mit `resources: 'usable'`-gleichem Zähler über einen eigenen `ResourceLoader`, der jede
Ressourcenanfrage protokolliert, echte `app.js`/`tour.js`): Analytics-Body bereits erfüllt → Sperre → Verbraucher
läuft weiter → 0 Ressourcenanfragen, 0 Skriptausführungen, 0 neue Knoten, `ReleaseFehler` bzw. stiller Abbruch.
Dasselbe für die Tour-Ladung. **Mutationen:** Verbraucherprüfung in `loadAnalytics` entfernt **und** zentrale Hülle
aktiv → Probe bleibt grün (Hülle trägt), Wächter „Verbraucherprüfung" rot; zentrale Hülle entfernt **und**
Verbraucherprüfung aktiv → Probe grün für Analytics, rot für einen Testlader ohne Prüfung; beide entfernt →
Probe „Ressourcenanfrage nach Sperre" rot.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 15 Zeilen.
