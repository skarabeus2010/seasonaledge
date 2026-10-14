# Wirkungsbericht Paket A (R1b, R1d, R4, R5) — 2026-10-14

Codex: Plan v2 freigegeben für R1b/R1d/R4/R5, Code Runde 1 „nein“ (drei mittlere Befunde), Runde 2 **FREIGABE (Code): ja**
([Runde 1](2026-10-14_options_paket_a_code_antwort1.md), [Runde 2](2026-10-14_options_paket_a_code_r2_antwort.md)).
Der leichte Restbefund aus Runde 2 (Health-Check nahm `data=None` auf einer Folgeseite als Seitenende) ist ebenfalls
behoben, mit Wächterfall und Mutation.

## Realisierte Vola 21 T., Stand 2026-10-13, 163 Ticker des Options-Universums

Gemessen read-only im Container mit `scripts/research/rv_wirkung_paket_a.py` (alt = aus Schlusskursen, neu = aus
gespeichertem `log_return`).

| Ticker | alt | neu | Δ |
|---|---|---|---|
| ETHA | 380,70 % | 45,82 % | −334,88 pts |
| XLU | 17,57 % | 16,72 % | −0,86 pts |
| XLP | 13,90 % | 13,20 % | −0,70 pts |
| XLE | 22,23 % | 22,77 % | +0,55 pts |
| XOP | 29,19 % | 29,67 % | +0,48 pts |
| JPM | 17,46 % | 17,00 % | −0,45 pts |

Median |Δ| 0,00 pts; 15 Ticker > 0,1 pts, 4 > 0,5 pts. Die kleinen Abweichungen sind Ausschüttungstage im Fenster:
die gespeicherten Schlusskurse tragen am Ex-Tag den Dividendenabschlag (Adjustierungsstand des Schreibzeitpunkts,
siehe `shared.data.lade_closes`), `log_return` nicht. Die neue Rechnung ist dort die richtige.

## Weitere Wirkung
- VRP auf /skew folgt der RV: ETHA live von −333 auf normale Größenordnung. Die gespeicherte ETHA-History wird NICHT
  angefasst (R1c, Plan v3).
- Health-Check: neuer Check 7 „Kursbasis“ — erwartet gelb mit ETHA 2026-09-30 ×3,0, solange der Tag im 45-Tage-Fenster
  liegt (bis ca. 14.11.).
- Morgen-Mail: keine „Quartalszahlen“-Zeilen mehr; Dividenden unverändert (der Abbau hätte sie ohne den eigenen Fund
  still entfernt).
- /skew öffnet in Percentile; Legende auf /en/skew englisch.

## Folgeposten (aus Codex Runde 1, nicht in diesem Paket)
Renditen aus Schlusskursen weiterhin in den Mail-Kursanzeigen (`shared/daily_report.py` ~244, ~422), der monatlichen
Sektorrechnung (~1273) und im Vol-Control-Proxy (`scripts/build_volcontrol_proxy.py:74`, Yahoo) → Plan v3.
