# Ticker schneller laden — S1 Code-Runde 1: der Lader `SA.kurse`

Plan (freigegeben mit Auflagen, Runde 4): [docs/TICKER_LADEN.md](../TICKER_LADEN.md). Read-only, nichts schreiben.

<task>Prüfe `landing/js/kurse.js` gegen den Vertrag in TICKER_LADEN.md (S1) und die Probe `scripts/js/probe_kurse.js`
(62 Prüfungen, alle grün: `node scripts/js/probe_kurse.js`). Noch KEINE Seite ist migriert — das kommt erst nach
deiner Freigabe des Laders. Gesucht: Vertragsbrüche, Wettläufe, Fälle, in denen eine halbe oder falsche Reihe als
vollständig durchgeht, und Prüfungen der Probe, die einen Fehler nicht fangen KÖNNEN.</task>

## Was ich bewusst so gebaut habe (bitte gegenprüfen)
- Jede neue Ladung lädt die Vereinigung aus Anfrage **und** vorhandenem Bestand (auch abgelaufenem), damit der
  Bestand innerhalb einer Seite nie schrumpft. Kosten: ein Rückwechsel nach Ablauf lädt die größte je benötigte
  Menge neu.
- Höchstens eine wartende Ladung je Ticker; ihr Bedarf wächst mit; sie startet nach Ende der laufenden, auch wenn
  diese scheiterte.
- Generation wird erst beim Erfolg vergeben (global monoton).
- Zeitüberschreitung über `Promise.race` + `AbortController`; zählt wie ein Netzfehler (Wiederholung).
- Doppelfilter `date=gte.<ab>&date=gt.<cursor>` — PostgREST verknüpft beide mit UND (prüfe, ob das stimmt).
- `pruefeBlock` lehnt Zeilen vor der Grenze ab, verlangt `hasOwnProperty` für jedes angeforderte Feld.
- Der Pool hält einen Platz nur während des Fetch; das Warten vor einer Wiederholung belegt keinen Platz.
- `verdraengen` verdrängt nur Koordinatoren ohne laufende/wartende Ladung; sind alle beschäftigt, darf die Zahl
  vorübergehend über 12 liegen.

## Fokusfragen
1. Gibt es einen Pfad, auf dem eine Anfrage eine Sicht bekommt, die ihren Bedarf nicht deckt?
2. Kann eine wartende Ladung verloren gehen oder doppelt starten (z. B. Anfrage trifft genau beim Übergang)?
3. Sind `r.json()`-Fehler, `AbortError` nach Erfolg, oder ein Fetch, der nach der Frist doch noch antwortet,
   sauber behandelt (Pool-Zähler, keine doppelte Auflösung)?
4. Fehlt der Probe ein Fall, den der Plan verlangt?

## Ausgabevertrag
**Urteil** (Freigabe / mit Auflagen / nicht) · **Befunde** (Schwere, Anker, Fehlerfall) · **Auflagen**. ≤ 50 Zeilen.
