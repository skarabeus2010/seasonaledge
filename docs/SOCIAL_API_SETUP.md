# Social-Auto-Posting — Setup (Meta Graph API: Instagram + Facebook Reels)

Automatisches Posten der fertigen Shorts auf **Instagram** & **Facebook** via `scripts/video/publish_meta.py`.
Strategie/Compliance: [YOUTUBE_STRATEGY.md](YOUTUBE_STRATEGY.md) · [YOUTUBE_DISCLAIMER.md](YOUTUBE_DISCLAIMER.md).

> Status: **Skript gebaut, wartet auf Owner-Setup** (Meta-App + Token + öffentliches Video-Hosting).
> TikTok hat eine separate, stärker gegatete Content-Posting-API → Phase 2.

## Wie das Posten funktioniert (wichtig zu verstehen)
Meta **lädt die MP4 selbst von einer öffentlichen HTTPS-URL** (kein Datei-Upload vom Skript). Das fertige
Video muss also **öffentlich erreichbar** sein — z.B. auf `seasonalpha.ai` gehostet (`out/`-MP4 auf den
Server kopieren, unter z.B. `https://seasonalpha.ai/video/<slug>_de.mp4`). Caption/Hashtags/Disclaimer
+ UTM zieht das Skript automatisch aus dem Skript-JSON.

**IG-Flow:** Container anlegen (`/{ig}/media`, REELS, video_url) → auf `FINISHED` warten → `media_publish`.
**FB-Flow:** `video_reels` start → Upload per `file_url` → finish (PUBLISHED).

## Owner-Setup (einmalig)

1. **IG-Business-Account** an die FB-Page **„SeasonAlpha"** verknüpfen (Meta Business Suite → Einstellungen →
   Instagram-Konto verbinden; IG muss „Professional/Business" sein).
2. **Meta-Developer-App** anlegen: <https://developers.facebook.com> → App (Typ „Business") →
   Produkte: **Instagram Graph API** + **Facebook Login / Pages**.
3. **Berechtigungen** (Permissions): `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`, `pages_manage_posts`, `business_management`.
4. **IDs ermitteln** (Graph API Explorer):
   - `META_PAGE_ID`: `GET /me/accounts` → die SeasonAlpha-Page.
   - `META_IG_USER_ID`: `GET /{page-id}?fields=instagram_business_account`.
5. **Long-Lived Page-Access-Token** holen: Kurzes Token (Graph Explorer) → in ein **Long-Lived User Token**
   tauschen (`/oauth/access_token?grant_type=fb_exchange_token…`) → daraus das **Page-Token** (`/me/accounts`,
   ~60 Tage gültig). Stabiler: **System-User-Token** im Business Manager (läuft nicht ab).
6. **App-Review / Advanced Access:** `instagram_content_publish` + `pages_manage_posts` brauchen für den
   Live-Betrieb App-Review. **Im Dev-Modus** können nur App-Admins/Tester posten → fürs MVP reicht das
   (du bist Admin), für Skalierung Review beantragen.
7. **Video-Hosting:** `out/<slug>_de.mp4` öffentlich bereitstellen (nginx-Pfad auf seasonalpha.ai o.ä.).

## `.env` (gitignored — NIE in getrackte Dateien!)
```
META_PAGE_ID=...
META_IG_USER_ID=...
META_PAGE_ACCESS_TOKEN=...      # Long-Lived Page- oder System-User-Token
META_GRAPH_VERSION=v21.0        # optional
```

## Nutzung
```bash
# Trockenlauf (postet nichts, zeigt nur Caption/Ziel)
py -3.14 scripts/video/publish_meta.py --script scripts/video/scripts/spy-juli.json \
   --lang de --video-url https://seasonalpha.ai/video/spy-juli_de.mp4 --ig --fb --dry-run

# Echt posten (IG + FB)
py -3.14 scripts/video/publish_meta.py --script scripts/video/scripts/spy-juli.json \
   --lang de --video-url https://seasonalpha.ai/video/spy-juli_de.mp4 --ig --fb
```

## Grenzen / Hinweise
- **IG-Limit:** 25 API-Veröffentlichungen / 24 h pro Konto.
- **Format:** 9:16, MP4 (H.264/AAC, yuv420p) — liefert unsere Pipeline bereits.
- **KI-Label:** Meta hat eigene KI-Kennzeichnung; bei KI-Stimme/-Visuals entsprechend deklarieren (analog YT).
- **Token-Ablauf** überwachen (Long-Lived ~60 Tage) — bei 190-Fehlern Token erneuern.
- Caption enthält bereits Disclaimer (Kurzform 2a, + Krypto-Zusatz 2c) + UTM (`utm_source=instagram/facebook`).
