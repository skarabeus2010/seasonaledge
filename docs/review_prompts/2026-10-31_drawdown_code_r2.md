# Code-Prüfung R2 — Drawdown-Analyse Phase 1 (`/drawdown`)

Grundlage: R1 [2026-10-31_drawdown_code_r1.md](2026-10-31_drawdown_code_r1.md), Antwort
[..._r1_antwort.md](2026-10-31_drawdown_code_r1_antwort.md) (NICHT FREIGABEFÄHIG, acht Befunde).

Umgesetzt, bitte je Befund abnehmen:

1. **Rundungsreste:** `EPS` jetzt auch bei der Recovery (`idx[i] >= idx[peak] * (1 - EPS)`), beim Trough-Gleichstand
   (`d < tiefe - EPS`) und beim Drawdown (`d > -EPS → 0`), in beiden Kernen. Handfall A13
   `100 → 102 → 74 → 102 → 74 → 102 → 103`: zwei abgeschlossene Episoden je 2 HT, keine laufende.
2. **Zu kurze Historie nach Erfolg:** `ergebnisseLeeren()` (Tabellen, Kacheln, Kurzantwort, Hinweis, Charts) bei
   `zu_wenig_daten` und im Fehlerpfad. Seitenfall `kurz_nach_erfolg` (QQQ, dann eine Kurszeile).
3. **Forward unabhängig:** `referenz_forward` im Wächter (eigene Episodenbildung, erster Übertritt je Episode,
   Zinseszins, Zwischenverlust `min(0, …)`, Basis über denselben Zeitraum, unvollständige Ereignisse, überlappende
   Paare) gegen Python für vier Reihen × Zeiträume × Horizonte 20/60/120. Mutation „Forward ohne Zinseszins“.
4. **Kohorten:** n = 0 → „nicht bestimmbar“ (`dd.k_rang_leer`), n < 5 → Einzelwerte (`dd.k_ab_einzel`). Seitenfälle
   `n0` (`100 → 90 → 85 → 80`) und `n1` (`100 → 80 → 100 → 80`).
5. **Schalttag JS:** 29.02. fällt nur bei Nicht-Schaltjahr im Ziel auf den 28. Prüfung in Python und JS (drei
   Zeitzonen): 2024-02-29 −20/−1/−4, 2000-02-29 −100 (1900 kein Schaltjahr).
6. **Kurzantwort-Schwelle:** „kleiner Rücksetzer“ über `!g5.laufend_erfuellt` (Kernregel mit EPS). Seitenfall
   `schwelle` (`100 → 102 → 96,9 → 96,9`).
7. **Methodik:** `dd.m_daten` DE/EN auf die instrumentbezogene, belegte Basis eingeschränkt.
8. **Forward-Basis-n:** eigene Spalte „Basis n“, `(+k)` als Spalte „ohne vollen Horizont“ ausgewiesen; Seitenprüfung
   auf Basis-n (DE/EN-Zahlformat).

Dazu: der Wächter baut die EN-Seite jetzt **immer** neu (lokal lag eine veraltete Fassung, gitignored).

Stand: `verify_drawdown.py` BESTANDEN (229 Prüfungen, mit Seite), Mutationstest `verify_drawdown_mutation.py`
**27/27 an der benannten Prüfung** (neu: Recovery ohne Toleranz, Forward ohne Zinseszins, überlappende Paare über das
doppelte Fenster, JS-Schalttag, Seite zu kurze Historie / n = 0 / Schwelle ohne Toleranz; zwei veraltete Seitenanker
— Fehlerpfad und zu kurze Historie — auf den Aufruf von `ergebnisseLeeren()` nachgezogen).

Fragen: Sind die acht Befunde behoben? Hält EPS die Zwillinge auch an anderen Rundungsfällen deckungsgleich (z. B.
neuer Peak innerhalb EPS über dem alten — zählt er als neuer Peak?), und verschiebt EPS irgendwo eine fachliche Zahl?
Welche falsche Anzeige käme noch durch? Schluss: FREIGABE, FREIGABE MIT AUFLAGEN oder NICHT FREIGABEFÄHIG.
