# Review-Auftrag: Anzeige = Ranking + Frische-Filter (Commit c94c63d)

## <task>

Prüfe `git diff c467516..c94c63d`. Kernänderungen in `scripts/compute_options_skew.py`:
`_anzeige_aus_ranking()` (neu, am Ende von `_enrich`), `_kurs_datum()` + `_NUR_SESSIONSKURSE`
in `_own_cands`, History-Fallback über `front_provider` in `build()`. Dazu Null-Schutz in
`landing/pages/skew.html` (Tabellen-Sortierung, Default-Auswahl) und `landing/pages/flows.html`
(Skew-Tabelle), `scripts/verify_skew_iv.py`, neuer Wächter `scripts/verify_skew_anzeige.py`,
Mutationstest `scripts/verify_session_mutation.py` (jetzt 23 Mutationen, zwei Wächter),
Wiederholung in `scripts/verify_twins_mutation._atomar_schreiben`.

**Befund, der behoben werden sollte** (gemessen 2026-09-24/25):
1. Anzeigepfad: `_byexp` + `_skew_at` wählen den 25Δ-Kontrakt über das **Anbieter-Delta**, das der
   Anbieter aus der IV desselben Kontrakts rechnet → ein falsch bepreister Kontrakt wählt sich selbst.
   RSP Put K=199 (nie gehandelt, OI 0) Delta −0,229, K=200 Delta −0,134. 33/158 Ticker > 8 pts
   Abweichung zwischen Anzeige und Ranking.
2. Ranking-Pfad: `_own_cands` nahm `day.close` ohne Zeitprüfung; im Snapshot ist `day` der Balken vom
   **letzten Handelstag des Kontrakts**. BKNG (nach Split) Call K=168,2 für 26,70 $ bei Spot 157,41.
   Backfill-Balken sind per Konstruktion frisch → Live und Backfill rechneten verschieden.

**Entscheidung des Nutzers:** Variante a — Tabelle zeigt die 30-Tage-Werte des Radars; nicht
rankbare Tage bleiben leer.

## Domänen-Invarianten

1. Angezeigte 25Δ/ATM-Werte == gerankte 30-Tage-Werte, **oder leer**. Nie ein Anbieterwert in
   diesen Feldern.
2. Rankbar heißt `cm_mode ∈ {cm, cm_extrap}` — exakt wie `skew.html::_isNorm`. `single`/`noatm` sind
   nicht rankbar.
3. Live-Ranking nutzt nur Kontraktkurse aus der Session, auf die die Zeile gestempelt wird.
4. Die History-Zeile eines nicht rankbaren Tages bleibt wie vorher (Anbieterwerte bzw. single-cm-Werte,
   `method` korrekt) — die Umstellung darf die gespeicherte Reihe nicht verändern.

## Fokusfragen

1. **`_kurs_datum`**: `last_updated` in ET umgerechnet. Gibt es Balken, deren `last_updated` legitim
   nach Mitternacht ET liegt (späte Korrekturen, OCC-Nachmeldungen) und die dadurch fälschlich als
   „nicht aus der Session" verworfen werden? Wie oft wäre das realistisch?
2. **Leere Anzeige**: `_ANZEIGE_FELDER` wird an nicht rankbaren Tagen auf `None` gesetzt. Gibt es
   Konsumenten (Frontend, `shared/daily_report.py`, `scripts/daily_health_check.py`, Newsletter,
   `landing/pages/dealer-positioning.html`, `/flows`), die dann abstürzen oder einen falschen Wert
   zeigen? Suche aktiv nach `.iv*100`, `.toFixed`, arithmetischen Vergleichen auf diesen Feldern.
3. **`contango`** wird VOR der Umstellung aus dem Anbieter-`iv_atm` berechnet und bleibt stehen.
   Ist das mit den umgestellten Feldern konsistent, oder vergleicht die Tabelle jetzt Äpfel mit Birnen?
4. **Health-Check** zählt `wterm = Ticker mit term UND iv_atm` — ändert die Umstellung seine
   Schwellen-Aussage (gelb/rot) unbemerkt?
5. **Wächter**: Fängt `verify_skew_anzeige.py` einen realistischen Rückfall, den die 23 Mutationen
   nicht abdecken? Kann er selbst echte Dateien schreiben?
6. **Frontend**: Die Sortierung `((a.skew_pts==null)-(b.skew_pts==null)) || (b.skew_pts-a.skew_pts)`
   — korrekt für alle Kombinationen?

## Werkzeug

Python: `C:/Users/HeikoSeibel/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
Die Wächter schreiben nur in Temp-Verzeichnisse → TMP/TEMP auf `.codex_tmp` im Arbeitsverzeichnis
setzen. Den Mutationstest (`verify_session_mutation.py`) NICHT ausführen, er schreibt Quelldateien.
Keine Netzzugriffe nötig.

## Bereits bestätigt (nicht erneut melden)

- Messung über 163 Ticker vor Börsenöffnung: rankbar 156 → 151, 97/149 unverändert, Ausreißer
  |Skew| > 15 von 2 auf 0.
- Session-Stempel, Handelszeit-Sperre, Schlüssel-Abbruch: in acht Runden am 2026-09-25 abgenommen.

## Erwartbare Fehlalarme

- NE-Skew, Skew-Term, Term, Smile-Kurve laufen bewusst weiter über den Anbieter-Picker (kein
  30-Tage-Gegenstück) — eigener TODO, kein Befund hier. Ein Befund wäre, wenn einer davon ein
  umgestelltes Feld mit einem nicht umgestellten mischt.
- `call_25d.strike` ist bei 30-Tage-Werten `None` (interpoliert, kein einzelner Strike) — gewollt.

## Ausgabevertrag

Befunde als `DATEI:ZEILE | SCHWERE | Was | Reproduktion | Vorschlag` (max. 15 Zeilen je Befund).
Dann `FREIGABE: ja/nein` + `BEGRÜNDUNG: <ein Satz>`. Kein Lob, keine Stilkritik.
