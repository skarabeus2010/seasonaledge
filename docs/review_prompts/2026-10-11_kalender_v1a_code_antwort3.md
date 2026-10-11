**Urteil**

**V1a noch nicht freigegeben.** Die drei Befunde aus Runde 2 sind für die direkten Einstiege behoben; eine Lücke bei verschachtelten Importen bleibt. Diff und neue Sperr-/Wächterdateien lesend geprüft, 23 Python-Dateien per AST geprüft. Nichts geschrieben, keine Wächter oder Mutationstests ausgeführt; Linux-Locks nicht selbst reproduziert.

**Befunde**

1. **Hoch — Ein äußerer Produktionsblock beendet die dauerhafte Importsperre vorzeitig.** Wird ein Pflicht-Modul innerhalb von `with produktion("abnahme:…")` importiert, übernimmt `modul_sperre()` nur den verschachtelten Kontext. Beim Verlassen des äußeren Blocks setzt dessen `finally` die Tiefe auf null und entsperrt/schließt den einzigen Lock, obwohl der Importkontext weiter im `ExitStack` liegt ([Freigabe:173](C:/dev/SeasonalEdge/shared/produktionssperre.py:173), [Importsperre:188](C:/dev/SeasonalEdge/shared/produktionssperre.py:188)). Danach kann die Aktivierung gesetzt werden; das bereits importierte `build_flows_rebalancing.main()` schreibt trotzdem seine Datei ([Schreibpfad:100](C:/dev/SeasonalEdge/scripts/build_flows_rebalancing.py:100)).
   Schreibfreie In-Memory-Probe mit unverändertem Sperr-/Buildercode und Ersatz für Dateisystem/Locks: nach Import Tiefe 2, nach Blockende Tiefe 0 und entsperrt; bei anschließend simulierter Marke erreicht `main()` einen abgefangenen Dateischreibaufruf und liefert Exit 0. Der Wächter prüft diesen Ablauf bislang nicht.

**Auflagen**

- Lock-Lebensdauer so verwalten, dass ein dauerhafter Importkontext den gemeinsamen Lock auch nach Ende seines äußeren Produktionsblocks hält.
- Den Ablauf „äußerer Block → Pflicht-Modul importieren → Block beenden → Aktivierung versuchen“ ergänzen und unter Linux nachweisen: Die Aktivierung wartet beziehungsweise läuft in die Frist; keine Marke und kein ungeschützter Dateischreibweg.

