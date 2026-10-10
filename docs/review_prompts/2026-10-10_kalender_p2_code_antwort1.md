# Antwort Codex — P2 Code Runde 1 (2026-10-10)

Prompt: [2026-10-10_kalender_p2_code.md](2026-10-10_kalender_p2_code.md). model: gpt-6.1-sol

**Urteil: keine Freigabe.**

Read-only geprüft. Schreiberwächter **33/33**, unabhängige Nummernreferenz **86/86**, Fehlerweitergabe **15/15** bestanden. Dateischreibende Mutationstests nicht ausgeführt; Gegenproben ausschließlich im Speicher.

**Befunde**

- **[P1] Onboarding kann bestehende Nummern auf NULL setzen.**  
  [backfill_new_ticker.py:134](/C:/dev/SeasonalEdge/scripts/backfill_new_ticker.py:134), [:147](/C:/dev/SeasonalEdge/scripts/backfill_new_ticker.py:147): Neue und bestehende Zeilen landen gemeinsam im Upsert, bestehende ohne Nummernfelder.  
  Beleg: Der echte Client erzeugt dafür `columns=…,tdom,tdoy,…` mit `resolution=merge-duplicates`. Fehlende Felder dieser Spalten werden als NULL verarbeitet ([PostgREST](https://docs.postgrest.org/en/v12/references/api/preferences.html#missing)). Damit schützt das Weglassen im einzelnen Dictionary die Altwerte nicht.  
  **Auflage:** Neue und bestehende Zeilen in getrennten Requests schreiben; Erhalt der Altwerte unter dem echten Transportvertrag prüfen.

- **[P2] Der Wächter beweist keine exakte Schreibmenge.**  
  [verify_schreiber_nummern.py:80](/C:/dev/SeasonalEdge/scripts/verify_schreiber_nummern.py:80), [:237](/C:/dev/SeasonalEdge/scripts/verify_schreiber_nummern.py:237): Er prüft vorhandene Records; die Nightly-Sollmenge entsteht aus den geschriebenen Records selbst.  
  Beleg: Eine Gegenprobe, die im Nightly ausschließlich die letzte Zeile schreibt, bleibt **33/33 grün**. Zudem überschreiten die Testdatensätze weder 500er-Chunks noch 1000er-Seiten.  
  **Auflage:** Unabhängig festgelegte vollständige Datumsmenge einschließlich Duplikaten prüfen; Pagination, mehrere Chunks und Teilfehler abdecken.

- **[P2] Abgefangene Abstürze können weiterhin als Mutationserfolg zählen.**  
  [verify_schreiber_nummern.py:52](/C:/dev/SeasonalEdge/scripts/verify_schreiber_nummern.py:52), [backfill_new_ticker.py:105](/C:/dev/SeasonalEdge/scripts/backfill_new_ticker.py:105), [verify_schreiber_nummern_mutation.py:161](/C:/dev/SeasonalEdge/scripts/verify_schreiber_nummern_mutation.py:161).  
  Beleg: `None.real` innerhalb des Onboarding-Kalender-`try` liefert einen abgefangenen `AttributeError`. Gedruckt wird lediglich `'NoneType' object has no attribute 'real'`. Der Wächter erreicht seinen Endmarker, meldet fachliche Prüfungen rot und erzeugt **keinen `[Ausnahme]`-Marker**; die Bewertung würde den passenden Befund als „gefangen“ verbuchen.  
  **Auflage:** Abgefangene Ausnahmen über ihre tatsächliche Fehlerklasse erfassen; Gegenproben auch für Onboarding, Intraday und Lückenfüller ergänzen.

**Antworten**

1. **Auflagen 1–6 sind teilweise erfüllt.**  
   Die begrenzte Reparatur, Fehlerweitergabe, K5-Zustände und Deploy-Einbindung sind umgesetzt.  
   Auflage 1 scheitert am gemischten Upsert; 5/6 bleiben wegen Mengenprüfung, Grenzfällen und Absturzerkennung offen.

2. **Ja:** Nightly überschreibt Nummern im aktuellen 7-Tage-Fenster, Intraday im heruntergeladenen Fenster – das entspricht P2.  
   Zusätzlich kann Onboarding unbeabsichtigt historische Nummern löschen; siehe P1-Befund.

3. **Nein.** Die Ausgabe enthält nicht zuverlässig die Fehlerklasse; eine Regex auf Klassennamen reicht deshalb nicht.

4. **Vor dem Commit die drei Befunde beheben und gezielt gegenprüfen.**  
   Die grünen Grundlinien allein rechtfertigen derzeit keine Freigabe.
