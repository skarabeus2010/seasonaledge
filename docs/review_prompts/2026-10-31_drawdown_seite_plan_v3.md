# Bauplan v3 — `/drawdown`, Nightly-Übersicht, Morgen-Mail

Antwort v2: [2026-10-31_drawdown_seite_plan_v2_antwort.md](2026-10-31_drawdown_seite_plan_v2_antwort.md) —
FREIGABE MIT AUFLAGEN (Befunde 1–9). v3 ersetzt nur die beanstandeten Abschnitte; alles Übrige aus
[v2](2026-10-31_drawdown_seite_plan_v2.md) gilt unverändert. Verweis „[B n]“ = Befund n der v2-Antwort.

## [B 1] Letzte abgeschlossene Sitzung E — konservative Regel (Nutzerentscheidung 2026-10-31)
Der Kalender kennt reguläre Schlusszeiten nicht; ein belegter Schlusszeitvertrag gehört in die
Kalender-Umstellung (eigener Posten) und wird hier NICHT improvisiert. Bis dahin:
- **Börsen:** E = letzte offene Sitzung **strikt vor** dem heutigen Datum in der Börsenzeitzone
  (`SA.boersenkalender.heute(boerse, jetzt)` / `sitzungen.heute`, dann `vorherige(…, einschliesslich=false)`).
  Die heutige Sitzung zählt nie, auch nach Handelsschluss. Folge: bis Mitternacht Ortszeit einen Tag Verzug,
  auf der Seite benannt („ausgewertet bis zur letzten Sitzung vor heute“). Nie eine halbe Sitzung.
- **Krypto:** E = letzter vollständig abgeschlossener UTC-Kalendertag. **Forex:** letzter Werktag vor dem heutigen
  UTC-Datum (Konvention, so gekennzeichnet).
- Python (Nightly/Mail) und JS (Seite) nutzen **dieselbe** Regel über die gemeinsamen Sitzungshelfer
  (`shared/sitzungen.py` ↔ `SA.boersenkalender`); `letzte_session()` (15-min-Puffer, NYSE-Logik) wird NICHT benutzt.
- Wächter: eingefrorene Zeitpunkte (vor/nach Schluss, Sonntag, Feiertag, Sommerzeitwechsel, Krypto 23:59/00:01 UTC,
  Forex Samstag) in drei Prozesszeitzonen, beide Produktionspfade.

## [B 2, B 3] Phase 3 gesperrt; Renditebasis
- Price-Return-Formel gestrichen. Phase 3 erst nach Nachweis der Adjustierungsregel des Lieferanten (Split,
  Dividende, Sonderausschüttung) und einer unabhängigen Dividendenquelle (Emittent/Börse); Yahoo-Abgleich heißt
  „Abgleich derselben Quelle“. Datenstand bekannt: `dividend_events` 17 864 Zeilen, 272 Ticker, frühestens
  2001-04-27 (SPY ab 2001, QQQ ab 2003) — vor 2001 ohnehin kein Vergleich möglich.
- Renditebasis wird **explizit je Instrument** hinterlegt (neue Zuordnung `RENDITEBASIS` in `shared/symbols.py`,
  Werte `total_return_naeherung` | `kursindex` | `performanceindex` | `neutral`), Vorgabe `neutral`; nur belegte
  Einträge bekommen einen anderen Text (US-ETFs/Aktien mit `adjclose`, ^GDAXI = Performanceindex, ^GSPC/^NDX/^DJI =
  Kursindex). Fällt `adjclose` im Lader weg, ist das kein Nachweis — Text bleibt neutral für Unbelegtes.

## [B 4] Kaplan-Meier
- Kohorte: **alle** Episoden mit Peak im Zeitraum (Peak-Vertrag wie Rest der Seite), die die gewählte Schwelle −x %
  erstmals erreichen — abgeschlossene und die laufende; keine Auswahl nach späterer Endtiefe. Grenzüberschreitende
  Episoden (Peak vor dem Zeitraum) gesondert gelistet, nicht in der Kurve.
- Zeit = Sitzungen ab erstem Übertritt bis Recovery (Ereignis) bzw. bis E (zensiert, nur laufende Episode).
- Unbekannter Pfad: Episode mit Lücke zwischen Übertritt und Recovery → zensiert am letzten bekannten Tag vor der
  Lücke; Episoden nach der ersten Lücke fallen aus (globaler Vertrag), die Anzahl steht unter der Kurve.
- Gleichstände: Ereignisse vor Zensierungen bei gleicher Zeit (Standardkonvention), Risikosatz zählt beide.
- Median = erste Zeit mit S(t) ≤ 0,5, sonst „nicht erreicht“. Greenwood-Varianz, Intervall log(−log)-transformiert,
  beschriftet als **„punktweises 95-%-Intervall (nominell)“**, kein Band-Anspruch. „at risk“ an jedem Schritt.
- Text: beschreibt frühere Episoden derselben Schwelle; keine Restdauerprognose.

## [B 5] Forward Returns
- Ereignis je Episode: erster Übertritt von −x % (Sitzung s). Für h ∈ {20, 60, 120}:
  `F_h = exp(Σ lr_{s+1…s+h}) − 1`, gültig nur, wenn alle h Sitzungsrenditen bekannt sind; Recovery beendet das
  Fenster nicht. Zwischenverlust `min(0, F_1 … F_h)` (Schlusskurse, relativ zum Übertrittsschluss).
- Ereignisse ohne vollständigen Horizont getrennt gezählt; n je h.
- Basis: alle Sitzungen desselben Tickers mit Peak-unabhängigem Zeitraum = Sitzungen im gewählten Zeitraum mit
  vollständigem Fenster; Kennzahlen vorab: Mittel, Median, Anteil positiv, Zwischenverlust (Mittel), n.
- Überlappung: Anzahl Ereignispaare, deren Fenster gemeinsame Renditesitzungen haben, je h angezeigt.
- Kein Test, keine Aussage „Überrendite bestätigt“.

## [B 6] Drawdown-Kalender
- Jahreswert „**Tiefster Abstand zum bisherigen Hoch im Jahr**“ = min D_t über die Jahressitzungen, Hoch aus der
  vollständigen verfügbaren Vorgeschichte; Beschriftung „Hoch seit Datenbeginn“ (nicht „Allzeithoch“).
- Ulcer Index je Jahr = √(Mittel D_t² in %) über die Jahressitzungen, Hoch nicht jährlich zurückgesetzt.
- Jahr mit unbekanntem Pfad → beide Werte unbekannt (kein Mittel über Resttage). Erstes Jahr und laufendes Jahr
  als Teiljahr gekennzeichnet; n = ausgewertete Sitzungen je Jahr.

## [B 7] Nightly-Übersicht (Phase 2)
- Läuft nach Kursnachladen und `log_return`-Reparatur; Datei mit `erzeugt`, `methode_version`, `kalender_version`
  und je Ticker `{status: ok | unbestimmbar | fehler, grund, e_erwartet, datenende, …}`. Technischer Fehler eines
  Tickers → Eintrag `fehler`, Nightly-Phase rot (Muster `_FEHLGESCHLAGEN`); fachlich unbestimmbar ist kein Fehler.
- Nur endliche Zahlen oder `null` (`allow_nan=False`), atomar, HTTP-Prüfung im Health-Check.
- Leser (Seite, Mail) prüfen selbst: `e_erwartet` je Ticker = beim Lesen berechnetes E, sonst „veraltet“ statt
  alter Werte; ausgefallene Ticker nie mit Vorwerten gefüllt.

## [B 8] Morgen-Mail (Phase 2)
- Entscheidung: **neue Übertritte seit dem letzten erfolgreichen Briefing** (Krypto-Wochenende geht nicht verloren,
  Feiertags-Montag wiederholt nicht). Ereignisidentität = (Ticker, Peak-Datum, Schwelle, Übertrittssitzung);
  gemeldete Identitäten im Versandjournal (`logs/versand/`) neben der bestehenden Versandsperre.
- Grenze `D ≤ −10 %` bzw. `≤ −20 %` (ungerundet). Beide Schwellen am selben Tag → eine Zeile („−20 %, zuvor −10 %“).
- Snapshot-Frische zur Versandzeit geprüft; veraltet/unbekannt → Abschnitt „nicht verfügbar“ im Log, nicht
  „kein Ereignis“. Leerer Abschnitt entfällt in der Mail.

## [B 9] Zusätzliche Wächterfälle
KM: gleichzeitige Recovery/Zensierung, nur zensierte Fälle, S genau 0,5, Endsprung auf 0, Lücke. Forward: Fenster
über Recovery und Jahreswechsel, innere Lücke, Überlappungszählung. Kalender: Jahreswert mit Vorjahreshoch,
Teiljahr, Jahr mit Lücke. Nightly/Mail (Phase 2): alter Snapshot, Tickerfehler, Wiederholungsereignis,
Wochenendereignis, beide Schwellen an einem Tag. E-Regel: siehe [B 1].

## Fragen
1. Ist die konservative E-Regel so vollständig spezifiziert (beide Pfade, alle Markttypen)?
2. KM-Kohorte inkl. Lückenzensierung tragfähig?
3. Reicht die Phase-2-Leserprüfung gegen veraltete Werte?
Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT TRAGFÄHIG.
