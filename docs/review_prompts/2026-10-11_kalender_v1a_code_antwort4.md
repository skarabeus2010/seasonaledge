**Urteil**

**Runde-3-Befund behoben; V1a zum Deploy freigegeben, sofern das strenge Linux-Gate besteht.** Diff und neue Sperr-/Wächterdateien geprüft, 23 Python-Dateien per AST geprüft. Nichts geschrieben, keine Wächter oder Mutationstests ausgeführt.

**Befunde**

- Keine neuen blockierenden Codebefunde.
- `modul_sperre()` hält einen eigenen Deskriptor über das äußere Blockende hinaus. Eine schreibfreie In-Memory-Probe mit unverändertem Sperrcode bestätigt die Deskriptor-Lebensdauer, die gespeicherte Kennung und das Schließen bei abgelehntem Import.
- Der neue Linux-Wächter trifft den beanstandeten Ablauf und verlangt `TimeoutError` ohne gesetzte Marke; die beiden passenden Mutationen sind verankert.
- Die vorhandenen `subprocess`-Aufrufe erben die Deskriptoren nicht. `fork` ohne `exec` würde sie erben und die Aktivierung gegebenenfalls länger aufhalten; kein solcher Produktionspfad gefunden.

**Auflagen**

- Vor dem Ausrollen muss `SA_SPERRE_STRENG=1` im Linux-Deploy-Gate bestehen.
- Die im Prompt angekündigten Linux-Wächter- und Mutationsergebnisse für diesen Stand nachreichen. Echte Linux-Locks wurden hier nicht reproduziert; die In-Memory-Probe ersetzt diesen Nachweis nicht.

