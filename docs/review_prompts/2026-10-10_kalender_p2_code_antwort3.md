# Antwort Codex — P2 Code Runde 3 (2026-10-10)

Prompt: [2026-10-10_kalender_p2_code_runde3.md](2026-10-10_kalender_p2_code_runde3.md). model: gpt-6.1-sol

**Urteil: Freigabe mit Auflage.** Die Teilerfolgszählung ist korrigiert; die neue Absturzwache muss vor dem Commit enger gefasst werden.

**Befunde**

- **[P2] Beliebige verkettete Produktivabstürze werden ignoriert.** [verify_schreiber_nummern.py:75](/C:/dev/SeasonalEdge/scripts/verify_schreiber_nummern.py:75) überspringt jede Ausnahme mit bereits gesehener `__cause__`, unabhängig von Klasse und Auslöseort.
  **Reproduziert:** Im Speicher `raise UpsertTeilfehler(geschrieben, e) from e` durch `raise AttributeError("neuer Produktivfehler") from e` ersetzt.
  Ergebnis: **35/36**, `ABSTUERZE=[]`; das tatsächliche `bewerte()` verbucht diesen Absturz als **„gefangen“**.
  **Auflage:** Nur die ausdrücklich erlaubte `UpsertTeilfehler`-Umhüllung ausnehmen und eine Gegenprobe für einen unbekannten Ausnahmetyp mit Stub-Ursache ergänzen.

**Antworten**

1. **Ja, die Auflage aus Runde 2 ist erfüllt.** Onboarding zählt den bestätigten Teil desselben Chunks. Auch der Lückenfüller zählt bei einem Gruppenfehler korrekt **1/3** bestätigte Zeilen und meldet den Fehler.
2. **Ja.** Die Umhüllungsregel kann einen echten Produktivabsturz verdecken und dadurch einen ungültigen Mutationsnachweis akzeptieren.
3. **Vor dem Commit:** den genannten Wächterbefund beheben. Weitere Abnahmebefunde habe ich nicht gefunden.

Read-only geprüft: **36/36** Schreiberprüfungen, **86/86** Nummernreferenzen, **15/15** Fehlerweitergabe; **22/22** Mutationen erkannt, **6/6** vorhandene Gegenproben korrekt verworfen. Logger und Mutationen ausschließlich im Speicher; nichts geschrieben.
