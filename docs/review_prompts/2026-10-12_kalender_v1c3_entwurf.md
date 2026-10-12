# Kalender-Umstellung V1c-3 — Entwurf v1 (Halbtage, vor dem Code)

Vorgänger: V1c-1 Ereigniskatalog (live), V1c-2 Produkttermine (freigegeben, im Deploy). Vertrag B4.2: „Arten MÜSSEN
Feiertag, Ersatztag, Sonderschließung und Halbtag unterscheiden; ein Halbtag MUSS als offene Sitzung zählen."
Prüfplan P3f verlangt einen Halbtag unter den Identitätsfällen. Read-only.

<task>Ist der Entwurf als Bauvorlage für V1c-3 tragfähig? Bitte die vorgeschlagenen Belegquellen und Sollfälle prüfen
und, wo möglich, die belegten Halbtage mit Quelle nennen oder korrigieren.</task>

## Bestand
- Kein Code kennt Halbtage als Ereignis. `shared/holidays.py` (Legacy-Anzeige) führt „Black Friday (Early Close)" und
  „Christmas Eve (Early Close)" als Etiketten ohne Beleg. `markt_offen`/`letzte_session` behandeln verkürzte Tage
  bewusst wie volle (Sperre bis regulärem Schluss, dokumentierte Betriebskonvention, Codex R3 Sept.) — bleibt in V1c-3
  unverändert; eine Umstellung gehört zu V1d (Sitzungshelfer) und müsste beide Funktionen gemeinsam ändern.
- Der Katalog kennt `art = "halbtag"` bereits; `kompat()` und `schliessungen()` schließen ihn aus. Damit ändern
  Halbtage weder `get_holidays`, `is_trading_day` noch die Handelstagnummern — die eingefrorene Momentaufnahme
  (3 024 Börsen-Jahre) muss unverändert bestehen.

## Regel: nur Belege, keine Projektion
Halbtagsregeln ändern sich je Jahr (z. B. 3. Juli, wenn der 4. Juli auf einen Samstag fällt und der 3. Juli selbst
Feiertag ist), und die Börsen beschließen sie jährlich. Deshalb **keine Regelableitung**: ein Halbtag existiert nur,
wenn eine Belegreihe ihn nennt (Datum, Schlusszeit lokal, Zeitzone, Quelle, Abrufdatum). Vorschlag für den Anfang:
- **NYSE**: veröffentlichter Kalender „Holidays & Trading Hours" (aktuelle und kommende Jahre, Early Closures 13:00 ET;
  Optionen/Cboe-Abweichungen nicht modelliert) — belegen: welche Jahre dort und ggf. in archivierten Fassungen
  verfügbar sind.
- **XETRA/LSE/übrige**: zunächst keine Belege → keine Halbtagsereignisse.
Je Börse/Jahr `halbtag_status(b, j) ∈ {belegt, ungeprueft}` (belegt nur, wenn die Belegreihe das ganze Jahr deckt);
der Wächter gibt alle `ungeprueft`-Bereiche als Abdeckungslücke aus. Ein Jahr ohne belegte Halbtage ist damit nicht
„ohne Halbtage", sondern „ungeprüft".

## Modell
Halbtagsereignis wie V1c-1: `regel_id = "<B>.halbtag.<kurz>"` (z. B. `NYSE.halbtag.tag_nach_thanksgiving`),
`art = "halbtag"`, `nominal = rechtlich = wirksam`, `ersatzgrund = keiner`, Namen DE/EN, Quelle. **Neues Feld für alle
Ereignisse:** `schlusszeit` (lokal `HH:MM`, nur bei Halbtag, sonst `null`) und `zeitzone` (IANA, nur bei Halbtag).
Kennung `<B>:<regel_id>:<datum>`. `ereignisversion` ändert sich (neue Felder + Ereignisse), `kalenderversion` NICHT
(Schließungsprojektion unverändert) — beides prüft der Wächter ausdrücklich.

## Wächter (Erweiterung von `verify_boersenereignisse.py`)
Momentaufnahme unverändert; jedes Halbtagsereignis liegt auf einem offenen Tag (`is_trading_day` wahr) und erscheint
weder in `get_holidays` noch in `schliessungen`; Handelstagnummern unverändert; Sollfälle mit Quelle (vorgeschlagen,
bitte prüfen): NYSE 2025-07-03, 2025-11-28, 2025-12-24 je 13:00 ET; 2026-11-27, 2026-12-24; Juli 2026 (4. Juli
Samstag, 3. Juli Feiertag) — gibt es dort einen Halbtag?; Python = JS Objektgleichheit inkl. `schlusszeit`/`zeitzone`;
Mutationen: Halbtag als Schließung gezählt, Halbtag ohne Beleg erzeugt, `kalenderversion` ändert sich.

## Fragen
1. Ist „nur Belege, keine Regelprojektion" für Halbtage richtig, auch für künftige Jahre (die NYSE veröffentlicht
   meist drei Jahre im Voraus)?
2. Welche NYSE-Jahre sind mit welcher Quelle belegbar? Gibt es eine amtliche Historie (z. B. NYSE-Regel 7.2 bzw.
   Informationsmemos) für frühere Jahre?
3. Reicht NYSE für V1c-3, oder verlangt B4/P3f weitere Börsen (z. B. LSE 24./31.12. Schluss 12:30)?

## Ausgabevertrag
**Urteil** · **Befunde** (P1/P2) · **Antworten 1–3** (mit Quellen) · **Auflagen**. ≤ 30 Zeilen.
