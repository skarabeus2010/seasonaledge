# Review-Auftrag Runde 1: Zweig Breadth Thrust — Recherche + Spezifikation

Du prüfst einen **Entwurf** (noch kein Produktivcode). Arbeite nur lesend. Antworte auf Deutsch.

## Zu prüfen

1. `docs/research/ZWEIG_BREADTH_THRUST.md` (Recherche, Probe, Spezifikation).
2. Probeskript: `C:/Users/HEIKOS~1/AppData/Local/Temp/claude/c--dev-SeasonalEdge/328e5456-81e6-40a1-b398-8918c4c5166d/scratchpad/zbt_probe.py`
   mit Daten im selben Ordner (`unicorn/NYSE_*.csv`, `gspc.json`). Ausführen mit
   `py -3.14 zbt_probe.py <ordner>` ist erlaubt (schreibt nichts).
3. Kontext im Repo: `docs/research/FEAR_GREED_NACHBAU.md` Abschnitt 3.1 und Stufe 2 (Marktbreite, Massive-Lizenz),
   `scripts/build_index_effect.py` (Muster Ereignisstudie), `shared/intermarket.py` (Muster Mail-Signal),
   `scripts/research/williams_muster.py` (Muster vorab festgelegter Studienplan), CLAUDE.md (Projektregeln).

## Fragen

A. **Definition:** Ist die Festlegung (EMA alpha 2/11 rekursiv, A/(A+D), Fenster 10 HT ab dem LETZTEN Tag < 0,40,
   strenge Vergleiche, Neuarmierung) die in der Literatur belegte Zweig/Morris-Fassung? Ist die Fensterregel
   richtig gelesen, oder rechtfertigt nur der Abgleich mit Morris die Wahl (Zirkelschluss-Gefahr)?
B. **Probe:** Rechnet `zbt_probe.py` richtig? Insbesondere Signal-Logik (Armierung/Fenster/Neuarmierung),
   Behandlung der Nullzeilen und der fehlenden Sitzung 2019-08-20, Rendite-Horizonte in Handelstagen auf der
   ^GSPC-Achse (nicht auf der A/D-Achse), Basisrate. Stimmen die Zahlen in Abschnitt 3?
C. **Daten:** Ist die Datenlage vollständig erfasst? Gibt es eine freie oder günstige, lizenzklare Quelle für
   NYSE Advances/Declines ab 2020-02 bzw. täglich live, die fehlt? Ist der Plan „Unicorn-Backfill + Kalibrierung
   jeder Nachfolgequelle auf der Überlappung" tragfähig? Was ist mit Strukturbrüchen (Anzahl NYSE-Issues,
   ETFs/Vorzüge/geschlossene Fonds in der Zählung, Dezimalisierung 2001)?
D. **Studie:** Ist die Performance-Auswertung (5 Horizonte, Einstieg t und t+1, Basisrate, max. Rückgang,
   Zufallsvergleich mit Mindestabstand, Überlappungskennzeichen) methodisch sauber für n ≈ 11–13? Was fehlt,
   was ist überzogen? Look-ahead irgendwo?
E. **Einbau:** Ist der Ort richtig (eigene Seite, Python-only + JSON, Mail-Zeile, Health-Check, Wächter)? Was
   widerspricht Projektregeln (Kalender, `log_return`, Cron-JSON nicht committen, öffentliches Repo)?
F. Alles, was ich übersehen habe.

## Format

Befunde nummeriert, je mit Schwere (hoch/mittel/niedrig), Beleg (Datei:Zeile oder Quelle mit URL, oder
Nachrechnung) und konkretem Änderungsvorschlag. Am Ende ein Urteil: **tragfähig / tragfähig mit Auflagen /
nicht tragfähig**. Keine Wiederholung dessen, was der Entwurf selbst schon als Grenze nennt, außer du hältst es
für falsch eingeordnet.
