# YouTube- & Social-Video-Strategie — SeasonAlpha

> **Living Doc.** Stand: 2026-06-28. Faceless, bilingualer (DE+EN) Short-Video-Kanal als Authority-/
> Traffic-/Backlink-Hebel für die junge YMYL-Domain `seasonalpha.ai`.
> Rechtstexte: **[YOUTUBE_DISCLAIMER.md](YOUTUBE_DISCLAIMER.md)** (kanonisch). Voller Plan-Verlauf:
> `~/.claude/plans/tranquil-noodling-pixel.md`.

## 1. Ziel & Begründung

Domain ~3-4 Mon. alt, 0 Backlinks, 293 „gecrawlt-nicht-indexiert" → Engpass = **Off-Page-Authority +
Traffic**. Ein faceless Short-Kanal ist der stärkste ungenutzte Hebel. **Primärziel: Traffic +
Backlinks → seasonalpha.ai** (sekundär: Newsletter-Leads, Markenautorität/E-E-A-T).

## 2. Plattformen & Kanal-Struktur

- **YouTube:** getrennte DE- & EN-Kanäle (gespiegelt). **DE-Kanal „Seasonalpha (de)" (live):**
  <https://www.youtube.com/channel/UC0L04LrthJ133mzruu23Law> (Channel-ID `UC0L04LrthJ133mzruu23Law`,
  Handle `@seasonalpha.de`). EN-Kanal folgt.
- **Instagram + TikTok:** je DE/EN. **Facebook:** Auto-Cross-Post aus Instagram (nicht aktiv bespielt).
- **X/@SeasonAlph4882 + LinkedIn:** Low-Effort-Cross-Post / Phase 2.
- **POSSE:** Ein vertikales 9:16-Video wird **einmal** produziert und überall verteilt.
- **Sprach-Start:** DE-MVP zuerst (native QA), EN ~2 Wochen danach (Reichweite).
- **Bio-Link überall → `seasonalpha.ai`** (= der Traffic-/Backlink-Mechanismus).

## 3. Format & Content

**Shorts-first** (9:16, 30-50s), gelegentlich Long-Form (5-10 min). **Hybrid faceless:** echte
SeasonAlpha-Charts (reale, aktuelle Daten) + KI-Voiceover (feste DE/EN-Brand-Voice) + eingebrannte
Untertitel + Branding.

**Short-Dramaturgie:** Hook (Kernzahl, 0-2s) → Setup/Mythos → Chart-Reveal → Ursache+Grenze → CTA.

**Content-Säulen:** „Saisonalitäts-Mythos-Check" · „Diesen Monat saisonal" · „Heute an der Börse"
(TDOM-Snack) · „Ticker-Saisonalität" · „Dekaden/Zyklen" · Long-Form aus Blog-Posts.

## 4. Produktions-Pipeline (`scripts/video/`)

| Baustein | Status | Zweck |
|----------|--------|-------|
| `render_vertical_chart.py` | **fertig** | Echtdaten → animierter 9:16-Chart-Clip (+Hero-Still). Methodik = Website (`shared.calculations`). matplotlib→ffmpeg. Trägt Dauer-Disclaimer-Fußzeile. |
| `render_brand_assets.py` | **fertig** | Kanal-Avatar 800×800 + Banner 2048×1152. |
| `compose.py` | geplant | Chart-Clip + Branding + **eingebrannter Disclaimer-Einblender** + Untertitel + TTS-Voiceover → finale MP4. |
| `publish_*.py` | geplant (Phase 2) | Auto-Upload (YT Data API / IG Graph API / TikTok). |

Details + Befehle: [scripts/video/README.md](../scripts/video/README.md).

## 5. Agenten-Roster (Reuse bevorzugt — spiegelt den Blog-Flywheel)

`saisonalitaet-scout` (Thema) → **`shorts-skripter`** (Skript JSON DE+EN, NEU) → `daten-auditor`
(Echtdaten-Gate) → [Render-Pipeline] → `wachstum-distributor` (Captions/Hashtags je Plattform, **inkl.
Disclaimer**) → [Publish] → `gsc-analyst` (Analytics). `blogger` = Quelle für Long-Form.

## 6. Compliance / Disclaimer (VERBINDLICH)

YMYL-Finanz-Content. Rechtstexte sind kanonisch in **[YOUTUBE_DISCLAIMER.md](YOUTUBE_DISCLAIMER.md)**.
Der Disclaimer wird in **jede Ebene** eingebacken — das ist nicht optional:

| Ebene | Was | Wer setzt es um |
|-------|-----|-----------------|
| **Kanal-About** | Kanal-Disclaimer (Teil 1) | Owner (einmalig in Kanalbeschreibung) |
| **Video-Beschreibung** | Kurzform 2a (DE/EN) oben + als YT-Studio-Standardinfo | `wachstum-distributor` liefert sie in JEDER Caption; Owner hinterlegt Standardinfo |
| **On-Screen-Einblender** | Kurzeinblender (Teil 3), 2-3s eingebrannt | `compose.py` (Pflicht-Overlay) |
| **Dauer-Fußzeile** | „Historische Daten · keine Anlageberatung" in jedem Frame | `render_vertical_chart.py` |
| **Skript-Inhalt** | KEIN Kauf-/Verkaufssignal; deskriptiv („historisch/Ø/Trefferquote") | `shorts-skripter` (harte Regel) |
| **Krypto** | Krypto-Zusatz 2c bei BTC/ETH etc. | `shorts-skripter` + `wachstum-distributor` |
| **Impressum/Datenschutz** | externe Seite, im Kanal verlinkt (§5 DDG) | Owner (= YMYL-P0 aus SEO_TODO) |

**Regeln für ALLE Skripte/Captions/SEO-Hinweise:**
- NIE „kaufen / verkaufen / wird steigen / Kursziel / garantiert / Signal" als Handlungsempfehlung.
- IMMER deskriptiv-historisch + eine Grenze/Vorsicht nennen.
- Jede Video-Caption beginnt/endet mit der **Kurzform 2a** (sprachgerecht).
- Krypto-Themen → Zusatz 2c zwingend.
- SEO-/Posting-Hinweise an den Owner enthalten den Disclaimer-Status als Checkpunkt.

## 7. Owner-Aktionen

**Setup:** Accounts (YT DE/EN, IG, TikTok, FB-Page via Meta Business Manager), Meta Business Suite,
TTS-Key (ElevenLabs/higgsfield), Bio-Links → seasonalpha.ai. Branding-Assets liegen in
`scripts/video/out/` (Avatar/Banner).
**Recht (vor Kanalstart):** Disclaimer-Texte anwaltlich prüfen lassen; **Impressum + Datenschutz** auf
`seasonalpha.ai` + im Kanal verlinken; bei Einnahmen Gewerbeanmeldung. Siehe Checkliste in
[YOUTUBE_DISCLAIMER.md](YOUTUBE_DISCLAIMER.md#teil-5--checkliste-vor-kanalstart-owner-aktionen).

## 8. Roadmap

- **Phase 1 (MVP):** `compose.py` + 3-5 Muster-Shorts DE (H2/Q4-Pilot) → Owner-Review (Look/Voice/CTA/Disclaimer).
- **Phase 2:** alle 6 Chart-Typen, Serien-Templates, Auto-Upload + Scheduling, EN-Launch, `gsc-analyst`-Feedback.
- **Phase 3:** 28×2 Blog-Posts als Long-Form-Backlog.

## 9. KPIs

Views/Watch-Time, Klicks auf den Bio-/Beschreibungs-Link (→ GA4-Referral von YT/IG/TikTok), neue
Backlinks/Brand-Searches, Newsletter-Signups mit Quelle „social". Review via `gsc-analyst`.
