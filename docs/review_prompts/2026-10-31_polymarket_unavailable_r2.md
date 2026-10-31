# Polymarket „bestätigt nicht vorhanden“ — R2

Antwort R1: [2026-10-31_polymarket_unavailable_antwort.md](2026-10-31_polymarket_unavailable_antwort.md) — NICHT
FREIGABEFÄHIG (Einzelabruf verlor fehlt_bestaetigt/unklar; Wächter prüfte ausgerechnet den Fehlerfall `None`).

Umsetzung:
1. `scripts/polymarket_refresh.py` ruft jetzt `fetch_markets_mit_abdeckung([cid])` statt des Einzelhelfers;
   `bestaetigt_fehlend = cid in abdeckung.fehlt_bestaetigt`; Grund `kein_markt` nur dann, sonst `abruf_unklar`;
   im Ausnahmezweig `bestaetigt_fehlend = False`. Ausnahme nur bei `bestaetigt_fehlend` UND Katalog `unavailable`.
2. Wächter: `unavailable + []` (Stapel und Einzelnachfrage leer) → fachlich übersprungen; `unavailable + None` →
   technischer Fehler; `open + []` (bestätigt fehlend ohne Katalogbeleg) → technischer Fehler; Markt wieder da →
   normal bewertet.
3. Mutationen: Ausnahme entfernt; Ausnahme ohne Katalogbeleg (`and True`); technischer Fehlschlag gilt als
   bestätigt fehlend (Bedingung `bestaetigt_fehlend` entfernt). 40/40 an der benannten Prüfung.
Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT FREIGABEFÄHIG.
