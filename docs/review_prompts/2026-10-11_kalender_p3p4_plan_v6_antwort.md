**Urteil**

**V9 noch nicht als Bauplan freigegeben.** Zwei Lücken bleiben. Ausschließlich gelesen und eine Vertragsprobe im Speicher ausgeführt; nichts geschrieben. Keine Server-Probeläufe.

**Befunde**

1. **Hoch — Die Releaseprüfung bindet weitere Skripte nicht an den geprüften Stand.** Altes HTML und alte `methode.js` setzen vor dem Fenster `releaseOk=true`. Ein danach geladenes neues Rechenskript prüft nur dieses weiterhin wahre Flag und rechnet. Die Vertragsprobe bestätigt den Ablauf; der Vergleich in [v6:11](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v6.md:11) erkennt ihn nicht. Überschreibbare Asset-URLs ermöglichen ihn weiterhin.

2. **Mittel — Der Rückweg erfasst den nun releaseinjizierten Converter nicht.** „Jedes HTML“ erhält eine Releasekennung ([v6:9](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v6.md:9)); der Converter liegt jedoch unter `seo/tools/`. Die Rücksicherung umfasst nur `landing/`, `blog/output/` und `seo/output/` ([v5:31](/C:/dev/SeasonalEdge/docs/review_prompts/2026-10-11_kalender_p3p4_plan_v5.md:31)). `git reset` stellt den Quellstand her, nicht dessen injizierte Releasekennung; der Revert-Deploy bleibt ausgeschaltet.

**Auflagen**

- Jedes Rechenskript vor seiner Ausführung gegen seine **eigene** Releasekennung prüfen oder unveränderliche Release-Assets verwenden. Zusätzlich „HTML + Methode alt, weiteres Skript neu“ und den umgekehrten Fall über das gesamte Fenster prüfen; jeweils keine Rechnung.
- Alle durch Releaseinjection veränderten Ausgaben sichern und wiederherstellen, ausdrücklich auch `seo/tools/`. Den Converter nach Rücksicherung per HTTP gegen Sicherungsprüfsumme und alte Releasekennung prüfen.
