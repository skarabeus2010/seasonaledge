"""
submit_indexnow.py — Pingt URLs an IndexNow (Bing, Yandex, Seznam, etc.)

IndexNow ist ein offener Standard von Microsoft und Yandex fuer sofortiges
Crawling-Trigger. Google unterstuetzt es nicht direkt, aber:
- Bing indexiert binnen Minuten statt Tagen
- Yandex (4% DE-Traffic) profitiert ebenfalls
- Kostenlos, kein API-Key-Registrierung, nur ein oeffentlich erreichbares Key-File

Key-File: landing/assets/indexnow-key.txt
Key wird in der submission als `keyLocation` Parameter uebergeben, damit
IndexNow die Owner-Verification machen kann.

Usage:
  py scripts/submit_indexnow.py                    # Core URLs (landing + 21 features + blog)
  py scripts/submit_indexnow.py --all              # Alle URLs aus sitemap.xml
  py scripts/submit_indexnow.py --urls "u1,u2,u3"  # Spezifische URLs
  py scripts/submit_indexnow.py --dry-run          # Preview ohne senden

Exit Codes:
  0 = erfolgreich oder Accepted (200/202)
  1 = Error (Network, 4xx, 5xx, ...)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import urllib.request
import urllib.error

REPO = Path(__file__).resolve().parent.parent
BASE_URL = "https://seasonalpha.ai"
KEY_FILE = REPO / "landing" / "assets" / "indexnow-key.txt"
KEY_URL = f"{BASE_URL}/landing/assets/indexnow-key.txt"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/IndexNow"

# Core-URLs die bei jedem Deploy gepingt werden (hochpriorisierte Pages)
CORE_URLS = [
    f"{BASE_URL}/",
    f"{BASE_URL}/dashboard",
    f"{BASE_URL}/jahreszyklus",
    f"{BASE_URL}/monatszyklus",
    f"{BASE_URL}/dekadenzyklus",
    f"{BASE_URL}/wochentage",
    f"{BASE_URL}/monatswechsel",
    f"{BASE_URL}/mondphasen",
    f"{BASE_URL}/zentralbanken",
    f"{BASE_URL}/feiertage",
    f"{BASE_URL}/opex",
    f"{BASE_URL}/intermarket-shocks",
    f"{BASE_URL}/trifecta",
    f"{BASE_URL}/plain-vanilla",
    f"{BASE_URL}/backtest-engine",
    f"{BASE_URL}/ki-saisonalitaet",
    f"{BASE_URL}/crash-fruehwarnung",
    f"{BASE_URL}/spot-vol-beta",
    f"{BASE_URL}/tdom-analyse",
    f"{BASE_URL}/overnight",
    f"{BASE_URL}/sektor-rotation",
    f"{BASE_URL}/kriegszeiten",
    f"{BASE_URL}/blog/",
    f"{BASE_URL}/blog/education/",
    f"{BASE_URL}/blog/marktausblick/",
    f"{BASE_URL}/blog/tutorials/",
]


def load_key() -> str:
    if not KEY_FILE.exists():
        print(f"ERROR: Key file {KEY_FILE} not found", file=sys.stderr)
        sys.exit(1)
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not key or len(key) < 8:
        print(f"ERROR: Key file empty or too short", file=sys.stderr)
        sys.exit(1)
    return key


def load_all_from_sitemap() -> list[str]:
    """Liest alle URLs aus seo/output/sitemap.xml (falls vorhanden)."""
    import re
    sitemap_path = REPO / "seo" / "output" / "sitemap.xml"
    if not sitemap_path.exists():
        print(f"WARN: {sitemap_path} not found, fallback auf CORE_URLS", file=sys.stderr)
        return list(CORE_URLS)
    content = sitemap_path.read_text(encoding="utf-8")
    return re.findall(r"<loc>([^<]+)</loc>", content)


def submit(urls: list[str], key: str, *, dry_run: bool = False) -> bool:
    """Sendet URLs an IndexNow. Returns True bei Erfolg."""
    if not urls:
        print("WARN: empty URL list, nothing to submit")
        return True

    # IndexNow erlaubt max 10000 URLs pro Request
    if len(urls) > 10000:
        print(f"WARN: {len(urls)} URLs > 10000 Limit, kuerze auf 10000")
        urls = urls[:10000]

    # Deduplizieren
    urls = sorted(set(urls))

    payload = {
        "host": "seasonalpha.ai",
        "key": key,
        "keyLocation": KEY_URL,
        "urlList": urls,
    }

    print(f"IndexNow submission:")
    print(f"  Endpoint:    {INDEXNOW_ENDPOINT}")
    print(f"  Host:        seasonalpha.ai")
    print(f"  Key:         {key[:8]}... ({len(key)} chars)")
    print(f"  KeyLocation: {KEY_URL}")
    print(f"  URLs:        {len(urls)}")
    if len(urls) <= 10:
        for u in urls:
            print(f"    - {u}")
    else:
        for u in urls[:3]:
            print(f"    - {u}")
        print(f"    ... ({len(urls) - 3} more)")

    if dry_run:
        print("DRY-RUN: kein Request gesendet")
        return True

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "SeasonAlpha IndexNow Submitter / Python",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            status = response.status
            body_text = response.read().decode("utf-8", errors="replace")
            print(f"Response: HTTP {status}")
            if body_text.strip():
                print(f"Body: {body_text[:500]}")
            # 200 = Success, 202 = Accepted (verification pending)
            return status in (200, 202)
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace") if e.fp else ""
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        if body_text.strip():
            print(f"Body: {body_text[:500]}", file=sys.stderr)
        # IndexNow HTTP Status Codes:
        # 200 = OK
        # 202 = Accepted (URLs will be processed)
        # 400 = Bad request (invalid URL format)
        # 403 = Forbidden (key verification failed)
        # 422 = Unprocessable (URLs don't belong to host)
        # 429 = Too many requests
        return False
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Submit URLs to IndexNow API")
    ap.add_argument("--all", action="store_true", help="Alle URLs aus sitemap.xml submitten")
    ap.add_argument("--urls", help="Komma-separierte URL-Liste")
    ap.add_argument("--dry-run", action="store_true", help="Preview ohne Request")
    args = ap.parse_args()

    key = load_key()

    if args.urls:
        urls = [u.strip() for u in args.urls.split(",") if u.strip()]
    elif args.all:
        urls = load_all_from_sitemap()
    else:
        urls = list(CORE_URLS)

    ok = submit(urls, key, dry_run=args.dry_run)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
