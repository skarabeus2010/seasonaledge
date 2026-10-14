# Code-Review Paket B2, Runde 2

Deine Antwort Runde 1: `docs/review_prompts/2026-10-14_options_b2_code_antwort1.md` (nein, vier Befunde). Prompt R1:
`…_b2_code.md`. Code uncommittet im Arbeitsbaum. Python wie dort. Read-only, Deutsch, **FREIGABE (Code): ja/nein**.

## Umsetzung
1. **Key Levels zeigte den Lauftag.** `landing/pages/key-levels.html`: `KL_DATE = d.session || d.generated` (Altbestand
   ohne Session: Lauftag wie bisher).
2. **Zukünftige/ungültige Sessiondaten wurden grün.** `daily_health_check._gex_bewertung`: Datum nach der erwarteten
   Session → rot („Datum nach der erwarteten Session“), Datum kein NYSE-Handelstag → rot. Fälle: 20.10. gegen 19.10.,
   Samstag 17.10., Feiertag 03.07. → rot; 02.07. gegen 06.07. → gelb (eine Session).
3. **Alte Profile unter neuem Datum.** `landing/pages/dealer-positioning.html::ensure`: ein Profil wird nur übernommen,
   wenn `(profil.session||profil.date) === (summary.session||summary.date)`; sonst `null` → die Seite zeigt „Kein
   Profil“. (Profile tragen seit B2 `session`; alte Profile tragen `date` = Lauftag des Laufs, der auch die alte Summary
   schrieb — dort bleibt die Anzeige wie bisher.)
4. **Herkunft unsichtbar.** `compare_flashalpha_gex.py`: Ausgabe „Stand … (EOD, Session)“ bzw. „(EOD, Lauftag-Archiv —
   Datum ist der Lauftag, nicht die Session)“.
5. Workflow-Kommentar in `gex_snapshot.yml` nachgezogen.

Wächter: `verify_gex_session.py` um die Health-Fälle und eine Seitenprobe ergänzt — `scripts/js/probe_options_session.js`
führt das inline-JS beider Seiten aus der Datei aus (DOM-Attrappe wie `probe_skew_tabelle.js`): kopierter Level-Text
trägt die Session; Profil der Vorsession wird nicht gezeigt, Profil derselben Session schon. Fehlt node → rot.
Mutationstest jetzt **25/25** (neu: IV-Surface-Horizont ab Lauftag — fehlte, wie du bemerkt hast —, Key-Levels-Seite
Lauftag, Dealer-Seite ohne Session-Abgleich, Health Datum nach Erwartung, Health Nicht-Handelstag).

Zum Spot um 22:15 UTC: der Tagesbalken der Session ist nicht garantiert sofort verfügbar; fehlt er, fällt der Ticker
aus, unter 60 % bricht der Lauf ohne Schreiben ab und der Workflow wird rot — das ist der gewollte sichtbare Fehler.
Der erste echte Lauf wird nach dem Deploy beobachtet (Health am Folgemorgen + Archivdatei).

## Nachweise
`verify_gex_session.py` grün (auch ohne streamlit, mit scipy wie im Gate), Mutation 25/25; `verify_seiten_kurse` 313,
`verify_einbindung` 24, `verify_release_sperre` 128, `verify_seo_html` 0, `verify_en` FAIL 0; die übrigen aus R1
unverändert grün.
