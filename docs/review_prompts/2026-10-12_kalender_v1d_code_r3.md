# Kalender-Umstellung V1d — Code-Runde 3 (Sitzungshelfer)

Runde 2: [Prompt](2026-10-12_kalender_v1d_code_r2.md) · [Antwort](2026-10-12_kalender_v1d_code_r2_antwort.md)
(P2: JS-Absturz in Vierergruppen `X,X,0,E` nicht erkannt). Read-only, Arbeitsbaum.

<task>Ist der Befund aus Runde 2 aufgelöst? Ist V1d freigegeben?</task>

## Änderung
`verify_sitzungen.py`: Raster, `verschiebe` und Positionen werden an `;` **und** `,` getrennt (`re.split(r"[;,]")`);
jedes Feld `X` → `[Absturz]`. Neue Pflicht-Gegenprobe im Mutationstest: echter JS-`Error` in `suche` (nur am
2026-07-02) → muss „ungültig“ sein.

## Nachweise
`verify_sitzungen` 445/445 · Mutationstest 16/16 gefangen; vier Gegenproben richtig verworfen: Python-Absturz
(abgefangen), **JS-Absturz in der Suche (abgefangen)**, fehlender Anker, Modul nicht importierbar; Projektbaum
unverändert.

## Ausgabevertrag
**Urteil** · **Befunde** · **Auflagen**. ≤ 10 Zeilen.
