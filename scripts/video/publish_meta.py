"""Auto-Posting für Instagram- & Facebook-Reels via Meta Graph API.

Postet einen fertigen 9:16-Short (öffentlich erreichbare MP4-URL) als Reel auf Instagram und/oder
Facebook. Caption/Hashtags kommen aus dem Skript-JSON (UTM je Plattform automatisch gesetzt).

⚠️ Setup nötig (s. docs/SOCIAL_API_SETUP.md): Meta-App + IG-Business-Account an FB-Page,
Long-Lived Page-Access-Token mit instagram_content_publish / pages_manage_posts. Die MP4 muss
**öffentlich per HTTPS** erreichbar sein (Meta lädt sie selbst) — z.B. unter seasonalpha.ai gehostet.

.env (gitignored):
  META_PAGE_ID=...
  META_IG_USER_ID=...
  META_PAGE_ACCESS_TOKEN=...        # Long-Lived Page Token
  META_GRAPH_VERSION=v21.0          # optional

  py -3.14 scripts/video/publish_meta.py --script scripts/video/scripts/spy-juli.json \
        --lang de --video-url https://seasonalpha.ai/video/spy-juli_de.mp4 --ig --fb
  (--dry-run = nichts posten, nur anzeigen)
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent))
from scripts.video import tts  # noqa: E402  (nur für load_env)


def _env(key, default=None, required=False):
    tts.load_env()
    v = os.environ.get(key, default)
    if required and not v:
        sys.exit(f"[publish] FEHLER: {key} fehlt in .env (s. docs/SOCIAL_API_SETUP.md)")
    return v


def _api():
    ver = _env("META_GRAPH_VERSION", "v21.0")
    return f"https://graph.facebook.com/{ver}"


def _caption(spec, lang, platform):
    cap = spec[lang]["caption"]
    return cap.replace("utm_source=youtube", f"utm_source={platform}")


# ----------------------------------------------------------------- Instagram Reel
def publish_instagram(video_url, caption, dry=False):
    if dry:
        print(f"[IG dry-run] Reel\n  video={video_url}\n  caption={caption[:120]}…")
        return None
    ig = _env("META_IG_USER_ID", required=True)
    tok = _env("META_PAGE_ACCESS_TOKEN", required=True)
    api = _api()
    # 1) Container anlegen
    r = requests.post(f"{api}/{ig}/media", data={
        "media_type": "REELS", "video_url": video_url, "caption": caption,
        "share_to_feed": "true", "access_token": tok}, timeout=60)
    if r.status_code != 200:
        sys.exit(f"[IG] Container-Fehler {r.status_code}: {r.text[:300]}")
    cid = r.json()["id"]
    # 2) Auf FINISHED warten (Meta lädt + verarbeitet das Video)
    for _ in range(40):
        s = requests.get(f"{api}/{cid}", params={"fields": "status_code,status",
                                                 "access_token": tok}, timeout=30).json()
        sc = s.get("status_code")
        print(f"[IG] Container {cid}: {sc}")
        if sc == "FINISHED":
            break
        if sc == "ERROR":
            sys.exit(f"[IG] Verarbeitungs-Fehler: {s.get('status')}")
        time.sleep(6)
    else:
        sys.exit("[IG] Timeout beim Verarbeiten des Reels.")
    # 3) Veröffentlichen
    r = requests.post(f"{api}/{ig}/media_publish",
                      data={"creation_id": cid, "access_token": tok}, timeout=60)
    if r.status_code != 200:
        sys.exit(f"[IG] Publish-Fehler {r.status_code}: {r.text[:300]}")
    mid = r.json().get("id")
    print(f"[IG] ✓ veröffentlicht — media_id {mid}")
    return mid


# ----------------------------------------------------------------- Facebook Reel
def publish_facebook(video_url, description, dry=False):
    if dry:
        print(f"[FB dry-run] Reel\n  video={video_url}\n  desc={description[:120]}…")
        return None
    page = _env("META_PAGE_ID", required=True)
    tok = _env("META_PAGE_ACCESS_TOKEN", required=True)
    api = _api()
    # 1) Upload-Session starten
    r = requests.post(f"{api}/{page}/video_reels",
                      data={"upload_phase": "start", "access_token": tok}, timeout=60)
    if r.status_code != 200:
        sys.exit(f"[FB] Start-Fehler {r.status_code}: {r.text[:300]}")
    vid = r.json()["video_id"]
    # 2) Video per file_url hochladen (Meta holt die MP4)
    up = requests.post(f"https://rupload.facebook.com/video-upload/{_env('META_GRAPH_VERSION','v21.0')}/{vid}",
                       headers={"Authorization": f"OAuth {tok}", "file_url": video_url}, timeout=120)
    if up.status_code != 200 or not up.json().get("success", True):
        sys.exit(f"[FB] Upload-Fehler {up.status_code}: {up.text[:300]}")
    # 3) Veröffentlichen
    r = requests.post(f"{api}/{page}/video_reels", data={
        "upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
        "description": description, "access_token": tok}, timeout=60)
    if r.status_code != 200:
        sys.exit(f"[FB] Finish-Fehler {r.status_code}: {r.text[:300]}")
    print(f"[FB] ✓ veröffentlicht — video_id {vid}")
    return vid


def main():
    ap = argparse.ArgumentParser(description="Meta (IG/FB) Reel-Publisher")
    ap.add_argument("--script", required=True, help="Skript-JSON (für Caption/Hashtags)")
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    ap.add_argument("--video-url", required=True, help="ÖFFENTLICHE HTTPS-URL der fertigen MP4")
    ap.add_argument("--ig", action="store_true", help="auf Instagram posten")
    ap.add_argument("--fb", action="store_true", help="auf Facebook posten")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    spec = json.loads(Path(a.script).read_text(encoding="utf-8"))
    if not (a.ig or a.fb):
        sys.exit("[publish] Mind. eine Plattform wählen: --ig und/oder --fb")
    if a.ig:
        publish_instagram(a.video_url, _caption(spec, a.lang, "instagram"), a.dry_run)
    if a.fb:
        publish_facebook(a.video_url, _caption(spec, a.lang, "facebook"), a.dry_run)
    print("[publish] fertig.")


if __name__ == "__main__":
    main()
