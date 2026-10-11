# Tage nach Börsenkalender — Plan P3/P4 v2

Runde 1: [Plan](2026-10-11_kalender_p3p4_plan.md) · [Antwort](2026-10-11_kalender_p3p4_plan_antwort1.md) (nicht tragfähig).
**Matrix A, Verträge B1–B7 und Prüfplan C** = [deine Ausarbeitung](2026-10-11_kalender_p3p4_matrix_antwort1.md) —
übernommen **wörtlich und verbindlich**; dieser Plan ergänzt nur Schalter, Bauphasen und Aktivierung. Read-only.

<task>Prüfe Plan v2 (Bauphasen + Schalter + Aktivierung) zusammen mit A/B/C als Bauplan.</task>

## Grundsatz: ein Methodenschalter, gemeinsame Aktivierung
- **JS:** `SA.kalenderMethode` (`'alt'` | `'kalender_v1'`), gesetzt an EINER Stelle (`landing/js/methode.js`, vor
  allen Rechnern eingebunden). **Python:** `shared/kalender_methode.py` `METHODE` (Konstante + Umgebung für Tests).
- Jeder migrierte Verbraucher aus A verzweigt genau einmal am Schalter; beide Zweige bleiben bis zur Aktivierung
  lauffähig. Der alte Zweig wird **nicht** verändert (Bestandsschutz, die Seitenprobe vergleicht ihn wörtlich).
- Statistikleser (B6) wählen zusätzlich die aktive Generation; P3d hängt an beiden.
- **Aktivierung** = ein Commit: Schalter auf `kalender_v1` (JS + Python), aktive Statistikgeneration gesetzt,
  P3h-Texte/Bilder aktualisiert — erst nach Schreibruhe → freigegebenem P5 → vollständigem P6.
- Nach der Aktivierung: alter Zweig in einem eigenen Schritt entfernt.

## Bauphasen (jede: Code → Wächter/Proben → Mutation → Codex-Freigabe → Commit, nichts aktiv)
- **V1 Fundament:** Ereigniskatalog (B4) im Python-Kalender + Bundle (`ereignisse` mit `regel_id`, `ereignis_id`,
  Art, nominal/wirksam, DE/EN-Name); Sitzungshelfer (B1/B2) in Python **und** `boersenkalender.js` (Sitzungsfolge,
  Nachfolger/Vorgänger, n-ter/letzter im Monat/Jahr, Zieltermin B5) gegen handgeschriebene Sollfälle (C
  „Gemeinsam"); Methodenschalter; Einbindungswächter ersetzt das Isolations-Gate (C P3a).
- **V2 Browserkern:** `SA.holidays` als Fassade über den Kalender im neuen Zweig (P3a); Header P3b; Converter P3e.
- **V3 Ereignisse:** P3f (Feiertage-Seite, Dashboard-Ereignisse, OPEX/VIX nach Cboe, Kalender/ICS, Flows).
- **V4 Fenster/Renditen:** P3k + P3i + P3j je Seite mit Python-Zwilling, B2/B3 als gemeinsame Helfer.
- **V5 Engine:** P3c.
- **V6 Statistik:** Schema-Migration (SQL, **Nutzer führt aus**), Generationsproduktion P3g unter Sperre,
  Leser P3d hinter Generation + Schalter.
- **V7 Veröffentlichte Zahlen:** Snapshots + Faktenblätter je Artikel (B7), alt/neu auf identischem Eingang;
  Textänderungen vorbereitet (Branch-los: im Faktenblatt; Artikeländerung erst im Aktivierungs-Commit).
- **V8 P3l/P3m:** Methodenregister der bewusst bestandsgeschützten Pfade (Wahlen, Pinning, Saison-Score, Stress,
  Indikatoren …) mit Kennzeichnung; keine Formeländerung.
- **Aktivierung** (s. o.), danach **Aufräumen**.

## Seitenprobe neu (C)
Kalendergerechte Fixtures (Sitzungen je Börse aus handgeschriebenen Fällen + gezielte Lücken/Füllzeilen),
sechs Zeitzonen mit Offsetnachweis, Vergleich **alt-Zweig = Fixture-Stand vorher** (wörtlich) und **neu-Zweig =
unabhängige Sollwerte** je Paket; A→B→A. Die heutige Kurslader-Seitenprobe bleibt unverändert daneben.

## Fokusfragen
1. Trägt der Schalter (beide Zweige bis zur Aktivierung) — oder erzeugt er eine zweite Wahrheit, die driftet?
2. Reihenfolge V1–V8: richtig? Was kann früher aktiv werden, ohne den gemeinsamen Vertrag zu brechen (z. B.
   Converter/Engine, die keine Statistikgeneration lesen)?
3. Fehlt eine Bauphase für A-Zeilen?

## Ausgabevertrag
**Urteil** · **Antworten** · **Befunde** · **Auflagen**. ≤ 50 Zeilen.
