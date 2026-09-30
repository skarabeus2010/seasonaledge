# Review-Auftrag Runde 3: SEO-Umsetzungsplan

Repo `C:\dev\Seasonaledge`. Runde 2 (`docs/review_prompts/2026-09-30_seo_review_plan_runde2.md`): FREIGABE nein, 5 Befunde.
Alle eingearbeitet in `docs/SEO_UMSETZUNGSPLAN_2026-09.md`:
1. Veröffentlichung und Indexierbarkeit getrennt (1b): „veröffentlicht" steuert den Build, „veröffentlicht UND
   indexierbar" die drei Sitemaps; `de_slug`-Prüfung gegen veröffentlichte Artikel unabhängig von `noindex`.
2. Serialisierung (1a): JSON-Unicode-Escapes für kleiner/größer/Und, danach keine zweite HTML-Maskierung;
   `upgrade_page_meta.py` dekodiert Eingaben und maskiert HTML-Text/Attribute separat; zweiter Regressionsfall `</script>`.
3. Wächter (1e): Zuordnung öffentliche URL → Artefakt inkl. `seo/output/disclaimer.html` und `seo/tools/`;
   Syntax für alle, Canonical/hreflang nach Seitentyp; Farbvorschauen und `embed.html` ausdrücklich ausgenommen.
4. Kennzahlen (1f): „22 Tools", „24 Strategien", „131 Jahre" wieder aufgenommen, mit Geltungsbereich.
5. Phase 2 nur noch Preise/Leistungsumfang/Vermarktung; Korrektur des heutigen Angebots in 1f.

Prüfe den Gesamtplan erneut. Antwort auf Deutsch, je Befund Schwere + Datei:Zeile + Änderung, am Ende genau
eine Zeile `FREIGABE: ja` oder `FREIGABE: nein`.
