# Kalender-Umstellung V2 — Code Runde 2

Runde 1: [Vorlage](2026-10-18_kalender_v2_code_r1.md) · [Antwort](2026-10-18_kalender_v2_code_r1_antwort.md)
(keine Freigabe, 4 × P2; Bedingungen: unabhängige Monatslisten, echte jsdom-Seitenproben). Arbeitsbaum. Read-only.

<task>Sind die Befunde und Bedingungen aus Runde 1 erledigt? Ist V2 freigabefähig?</task>

## Zu den Befunden
1. **Typprüfung** (`holidays.js`, `nextTradingDay`): Jahr/Monat/Tag vor `_ds` auf ganze Zahlen geprüft
   (`K.Fehler`); Wächter: acht Typfälle für `nextTradingDay`, `nthTradingDay`, `lastTradingDay`,
   `nthTradingDayOfYear`, `get`.
2. **EN-Einbindung:** `verify_boersenkalender_js.isolation_scan` erlaubt genau die EN-Fassung jeder Manifestseite
   unter ihrer EN-Adresse (`shared.seo_basis.en_slug`) und verlangt sie, wenn `landing/en/` vorliegt;
   `verify_einbindung.py --mit-en` prüft Manifest + Reihenfolge auch auf `landing/en/`. Gegenprobe: mit den lokal
   veralteten EN-Seiten (vor V2 gebaut) wurden beide rot, nach `build_en.py --write` grün. Im Gate gibt es
   `landing/en/` noch nicht (wird auf dem Host gebaut) — dort greift der Vertrag erst beim HTTP-Nachweis nach dem Deploy.
3. **Inventar:** Muster jetzt jedes Zeichenkettenliteral `NONE|NYSE|XETRA|LSE` in beiden Anführungszeichenformen und
   jeder Zugriff auf `_NYSE_SONDER/_XETRA_SONDER`, Kommentarzeilen ausgenommen; 66 Stellen (V3 25, V4 20, V5 2,
   Aufräumen 19), darunter `strategy-compute.js:335/336`.
4. **Produktionspfad:** `scripts/js/probe_header_seiten.js` lädt die echte Seite mit allen Skripten in jsdom (feste
   Uhr, `methode.js` und Seitenkennung auf die Probemethode gestellt). Für alle 23 Header-Seiten: unter `alt`
   gleich einer eingefrorenen Momentaufnahme des Stands vor V2 (`scripts/fixtures/header_alt_seiten.json`, einmalig
   aus `git archive HEAD` erzeugt — im Gate wäre HEAD schon V2); unter `kalender_v1` gleich der Headerfunktion für den
   Ticker, den die Seite zeigt; A→B→A (SAP.DE → BTC-USD → SAP.DE) auf dashboard, tdom-analyse, monatszyklus;
   sektor-rotation muss „Kalender: <Ticker> · NYSE“ nennen. Converter als ausgelieferte Seite (`seo/tools/…`) mit
   echtem Bootstrap: alt = Momentaufnahme, kalender_v1 = Sollwerte. Statuskennzeichen je Klasse in Header und
   Converter (ungeprüft, Annahme, belegt ohne Zusatz, Konvention). Keine Seitenfehler zugelassen (jsdom-Lücke
   `canvas` per Stub).

## Zu den Bedingungen
- **Monatslisten** (`scripts/fixtures/kalender_monatslisten_2026.json`): 11 Börsen, je ein Monat 2026, abgelesen aus
  dem Kalender der Börse (Recherche durch einen Agenten ohne Blick in den Code; Quelle + Archivfassung, bei Xetra/SIX
  byte-gleiche Archiv-PDF mit SHA-256). LSE Mai 2026 nur aus Fremdquellen → `unbelegt`, so gekennzeichnet geprüft.
  Je Tag: Offenheit, TDOM vorwärts/rückwärts, TDOY = abgezählte Sitzungen vor dem Monat + Position,
  `nextTradingDay` (nach der letzten Sitzung: Nachfolger im Folgemonat), `nth/lastTradingDay` 1…Summe+1.
  Ergebnis: alle 11 gleich unserem Kalender.
- Wächter: 1835 Prüfungen, ~1½ min; Gate-Schritt hinter der Seitenprobe (braucht jsdom aus `npm ci`).
  Mutationstest jetzt 20 Mutationen (+ Kalenderticker ignoriert, Seite ohne Bundle) + 2 Gegenproben.

## Ausgabevertrag
**Urteil** · **Befunde** (nur neue/offene, P1/P2 mit Datei:Zeile) · **Auflagen**. ≤ 25 Zeilen.
