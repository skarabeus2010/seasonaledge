# Video-Plan & Pipeline-Konventionen

Strategie: [docs/YOUTUBE_STRATEGY.md](../../docs/YOUTUBE_STRATEGY.md) · Disclaimer (kanonisch):
[docs/YOUTUBE_DISCLAIMER.md](../../docs/YOUTUBE_DISCLAIMER.md)

## Leitprinzip (wichtig)

**Keine „Excel-Histogramme".** Monatsbalken (`monthly_cycle`) kann jeder in Excel bauen — damit
verkaufen wir uns unter Wert. Wir führen mit den **distinctiven SeasonAlpha-Funktionen**, die man
nicht trivial nachbaut:
- `seasonal_yearly` — normierter Jahresverlauf mit **±1σ-Band** (+ „we are here"-Marker)
- `tom_effect` — **Turn-of-Month / TDOM** (stärkste Börsentage rund um den Monatswechsel)
- `holiday_window` — **Feiertags-Effekte** (holiday-aware Kalender, z.B. Vor-4.-Juli-Drift)
- `decade_cycle` — **Dekadenzyklus**; dazu Anomalie-/Regime-/Sektor-Rotation (`shared/`)
**Underlyings mischen** (nicht nur DAX): SPY, QQQ, DIA, ^GSPC, BTC-USD … Eine klare Zielgruppe
(Retail-Trader, die Muster suchen). Kein Doppel-Content. **Formel:** bekannter Anker + gekippter Mythos.

## Output-Struktur (seit Umbau)

`scripts/video/catalog.json` = Register (Laufnummer ↔ Slug). Pro Video:
```
out/<NNN>_<slug>/
  <slug>_de.mp4            ← fertiges Short
  <slug>_de_still.png      ← Hero-Still
  <slug>_de_seo.md         ← fertiges Posting-Kit (Titel/Beschreibung/Pinned/TikTok/FB + YouTube-Tags/Keywords)
```
`compose.py` vergibt die Nummer, schreibt die SEO-/Metatag-Datei automatisch (`--seo-only` = nur SEO).
**Disclaimer:** On-Screen = **Standard-Variante** (Teil 3) aus `disclaimer_overlay`; Caption = Kurzform 2a
(+ Krypto-Zusatz 2c bei Coins); KI-Inhalt beim Upload deklarieren.

## Bestehend
- **001 · dax-juli** — DAX Juli (monthly_cycle, Juli gold) — *timely, postbar*. (Balken = Ausnahme, schon produziert.)
- **002 · dax-q4** — DAX Q4 (monthly_cycle) — für Okt/Nov.

## 5 neue Videos (distinctive)

| Nr | Slug | Thema / Mythos-Flip | Underlying | Chart (distinctive) | Timely | Renderer-Status |
|----|------|---------------------|-----------|---------------------|--------|-----------------|
| 003 | turn-of-month-spy | „Die stärksten Börsentage des Monats? Fast immer dieselben." (Monatswechsel-Effekt) | **SPY** | `tom_effect` | ✅ Jun→Jul jetzt | **bauen** |
| 004 | july4-dow | „Vor dem 4. Juli steigt die US-Börse fast immer." (Vor-Feiertags-Drift) | **DIA/^DJI** | `holiday_window` (NEU, `shared/holidays` NYSE) | ✅ 4. Juli | **bauen** |
| 005 | btc-uptober | „Bitcoins bester Monat? Der Oktober — ‚Uptober' Ø +15 %." | **BTC-USD** | `seasonal_yearly` | evergreen (Krypto) | ✅ vorhanden — *Skript fertig* |
| 006 | qqq-typical-year | „Das typische Nasdaq-Jahr — und wo wir gerade stehen." | **QQQ** | `seasonal_yearly` + „we are here"-Marker | ✅ (wir sind hier) | Marker **bauen** |
| 007 | decade-cycle-sp | „Manche Jahre im Jahrzehnt sind systematisch stärker." (Dekadenzyklus) | **^GSPC** | `decade_cycle` | evergreen | **bauen** |

## Nächste Schritte
1. **Renderer erweitern:** `tom_effect`, `decade_cycle`, `holiday_window` (Reuse `shared/tdom_analysis`,
   `shared/holidays`, `blog/blog_builder.py`-Logik) + „we are here"-Marker in `seasonal_yearly`.
2. Skripte 003/004/006/007 via `shorts-skripter`-Agent (Anker+Mythos, echte Zahlen, Compliance, keywords).
3. `compose.py` rendern → `out/<NNN>_<slug>/` mit SEO-Datei. Owner postet (UTM + KI-Label).
4. Nach 15–20 Shorts: auf der **Website** auswerten (GA4/UTM) → Gewinner-Muster verdoppeln.
