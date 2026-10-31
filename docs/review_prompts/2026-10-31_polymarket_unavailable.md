# Polymarket Daily seit (mindestens) 29.10. rot — „bestätigt nicht vorhanden“ im Snapshot

Befund (Trockenlauf `polymarket_refresh.py --dry-run` auf dem Server, 31.10.): 25/26 Snapshots ok,
`fed-hike-2026: Abruf fehler (kein_markt)` → `technische_fehler = 1` → Exit-Regel (B2, vier Zähler) rot.
Der Katalogabgleich (`polymarket_discover.py --sync-db`) belegt denselben Markt als `fehlt_bestaetigt` und setzt
`status = 'unavailable'` — dort ausdrücklich KEIN Fehler. Der Snapshot kannte diesen Fall nicht.

Änderung (`scripts/polymarket_refresh.py`): Gamma liefert keinen Markt UND Katalogstatus ist `unavailable` →
`fachlich_uebersprungen`, kein technischer Fehler. Abgefragt wird weiter (taucht der Markt wieder auf, wird er
normal bewertet). Ohne Katalogbeleg bleibt „kein Markt“ ein technischer Fehler.
Wächter `scripts/verify_polymarket_status.py`: zwei neue Fälle (unavailable + kein Markt; unavailable + Markt
wieder da). Mutationstest `verify_polymarket_status_mutation.py`: zwei neue Mutationen (Ausnahme entfernt;
Ausnahme ohne Katalogbeleg), 39/39 an der benannten Prüfung.

Fragen: Ist die Regel richtig abgegrenzt (z. B. Wettlauf: Katalog sagt `unavailable`, Markt existiert wieder, Gamma
antwortet aber gerade mit Netzfehler — bleibt technisch)? Reicht `last_fetch_state = 'fehler'` in diesem Fall, oder
soll ein eigener Zustand gesetzt werden? Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT FREIGABEFÄHIG.
