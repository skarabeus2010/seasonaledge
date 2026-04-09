"""
generate_og_images.py — Generiert Social-Media OG-Image + Apple-Touch-Icon + Favicon-PNG.

Schreibt nach landing/assets/images/:
  - og-image.png        1200x630 (Twitter, LinkedIn, Facebook, WhatsApp, iMessage)
  - apple-touch-icon.png  180x180 (iOS Home-Screen-Bookmark)
  - favicon-32x32.png      32x32
  - favicon-16x16.png      16x16

Design: V3 Ultra Palette — Pure Black BG, Signal Gold Accents, Neon Green/Red.
Typografie: Sora Display fuer Headline, DM Sans fuer Tagline (wenn installiert),
sonst PIL default.

Usage:
  py scripts/generate_og_images.py
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "landing" / "assets" / "images"
OUT.mkdir(parents=True, exist_ok=True)

# V3 Ultra Palette
BG          = (0, 0, 0)
GOLD        = (232, 168, 32)
GOLD_DIM    = (160, 115, 22)
TEXT        = (255, 255, 255)
DIM         = (136, 136, 136)
GREEN       = (48, 232, 120)
RED         = (255, 64, 64)

def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Versucht einen System-Font, sonst PIL default."""
    candidates = []
    if bold:
        candidates += [
            "C:/Windows/Fonts/segoeuib.ttf",  # Segoe UI Bold
            "C:/Windows/Fonts/arialbd.ttf",   # Arial Bold
        ]
    candidates += [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_og_image() -> None:
    """1200x630 — Twitter/LinkedIn/Facebook Share Card."""
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Subtile Grid-Lines im Hintergrund (wie ein Chart-Background)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=(15, 15, 15), width=1)
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=(15, 15, 15), width=1)

    # Gold-Border oben (Akzent wie im Dashboard)
    d.rectangle([0, 0, W, 4], fill=GOLD)

    # Gold-Akzent-Bar links (vertikal, wie Card-Border)
    d.rectangle([48, 80, 52, H - 80], fill=GOLD)

    # Brand: Season Alpha
    brand_font = _font(96, bold=True)
    d.text((80, 120), "Season", font=brand_font, fill=TEXT)
    # "Alpha" in Gold
    season_w = d.textlength("Season", font=brand_font)
    d.text((80 + season_w, 120), "Alpha", font=brand_font, fill=GOLD)

    # Tagline 1
    tagline_font = _font(36)
    d.text((80, 250), "Saisonale B\u00f6rsenanalyse", font=tagline_font, fill=TEXT)
    d.text((80, 298), "mit 131 Jahren Marktdaten.", font=tagline_font, fill=DIM)

    # KPI-Row unten (wie auf der Landing)
    kpi_y = 420
    kpi_gap = 280
    kpis = [
        ("131 Jahre", "Marktdaten", GOLD),
        ("15 Modelle", "KI-Saisonalit\u00e4t", GREEN),
        ("500+ Ticker", "Weltweit", TEXT),
    ]
    kpi_val_font = _font(44, bold=True)
    kpi_lbl_font = _font(20)
    for i, (val, lbl, col) in enumerate(kpis):
        x = 80 + i * kpi_gap
        d.text((x, kpi_y), val, font=kpi_val_font, fill=col)
        d.text((x, kpi_y + 60), lbl, font=kpi_lbl_font, fill=DIM)

    # URL unten rechts
    url_font = _font(22)
    url_text = "seasonalpha.ai"
    url_w = d.textlength(url_text, font=url_font)
    d.text((W - url_w - 80, H - 50), url_text, font=url_font, fill=GOLD)

    path = OUT / "og-image.png"
    img.save(path, "PNG", optimize=True)
    print(f"  [OK] {path.relative_to(REPO)} ({path.stat().st_size // 1024} KB)")


def generate_touch_icon() -> None:
    """180x180 — iOS Home-Screen-Bookmark."""
    S = 180
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)

    # Gold-Square Border (wie Card-Border)
    d.rectangle([0, 0, S - 1, S - 1], outline=GOLD, width=4)

    # Innerer Bereich: "S" in Gold (kompakt, ikonisch)
    s_font = _font(120, bold=True)
    txt = "SA"
    w = d.textlength(txt, font=s_font)
    # Text-BBox fuer vertikales Zentrieren
    bbox = d.textbbox((0, 0), txt, font=s_font)
    h = bbox[3] - bbox[1]
    x = (S - w) / 2
    y = (S - h) / 2 - bbox[1]
    d.text((x, y), txt, font=s_font, fill=GOLD)

    path = OUT / "apple-touch-icon.png"
    img.save(path, "PNG", optimize=True)
    print(f"  [OK] {path.relative_to(REPO)} ({path.stat().st_size // 1024} KB)")


def generate_favicon_png(size: int) -> None:
    """32x32 / 16x16 PNG-Favicon (Fallback fuer Browser die SVG nicht moegen)."""
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    # Einfach: Gold "S"
    font_size = int(size * 0.72)
    f = _font(font_size, bold=True)
    txt = "S"
    w = d.textlength(txt, font=f)
    bbox = d.textbbox((0, 0), txt, font=f)
    h = bbox[3] - bbox[1]
    x = (size - w) / 2
    y = (size - h) / 2 - bbox[1]
    d.text((x, y), txt, font=f, fill=GOLD)
    path = OUT / f"favicon-{size}x{size}.png"
    img.save(path, "PNG", optimize=True)
    print(f"  [OK] {path.relative_to(REPO)} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    print("Generating OG / Touch / Favicon Images ...")
    generate_og_image()
    generate_touch_icon()
    generate_favicon_png(32)
    generate_favicon_png(16)
    print("Done.")
