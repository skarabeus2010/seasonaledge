"""Vertical (9:16) chart renderer for the SeasonAlpha faceless video pipeline.

Erzeugt aus ECHTEN, AKTUELLEN Daten einen animierten 1080x1920-Chart-Clip (+ Hero-Still)
fuer Social-Shorts (YouTube/Instagram/TikTok/Facebook). Methodik IDENTISCH zur Website/Blog:
normalisierte Renditen (Start = 100) via shared.calculations -> Text<->Chart bleiben konsistent.

Engine: matplotlib -> PNG-Frames -> ffmpeg (kein Kaleido noetig). ffmpeg muss auf PATH sein.

Beispiele:
  py -3.14 scripts/video/render_vertical_chart.py --type seasonal_yearly --ticker ^GSPC --years 20
  py -3.14 scripts/video/render_vertical_chart.py --type monthly_cycle --ticker ^GDAXI --years 38 --lang en

Output: scripts/video/out/<ticker>_<type>_<lang>.mp4  (+ _still.png)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

# --- Projekt-Root auf den Pfad (damit `shared` importierbar ist) ---
_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# --- Theme (gespiegelt aus shared.constants.SE_COLORS, mit Fallback) ---
try:
    from shared.constants import SE_COLORS as _SE
except Exception:
    _SE = {}
BG = _SE.get("bg", "#080c12")
ACCENT = _SE.get("accent", "#00d4aa")
WARM = _SE.get("accent_warm", "#e8a425")
BLUE = _SE.get("accent_blue", "#4d9fff")
MUTED = _SE.get("text_muted", "#5a6e85")
NEG = "#ff5b6e"
TEXT = "#f2f5f8"

# --- Kalender-Konstanten (gespiegelt aus blog/blog_builder.py) ---
_MONTH_DOY = {
    1: (1, 31), 2: (32, 59), 3: (60, 90), 4: (91, 120),
    5: (121, 151), 6: (152, 181), 7: (182, 212), 8: (213, 243),
    9: (244, 273), 10: (274, 304), 11: (305, 334), 12: (335, 365),
}
_MONTH_STARTS = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
_MONTH_LABELS_DE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
_MONTH_LABELS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
_MONTH_FULL_DE = ["Januar", "Februar", "März", "April", "Mai", "Juni",
                  "Juli", "August", "September", "Oktober", "November", "Dezember"]
_MONTH_FULL_EN = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]

W, H, DPI = 1080, 1920, 100  # 9:16
_VIDEO_MODE = False  # True: Branding/CTA/Footer weglassen — Compose legt dort Untertitel/Disclaimer hin
_HIGHLIGHT_MONTH = None  # None = aktueller Monat; 1-12 = diesen Monat hervorheben + KPI darauf fokussieren

# Konsumenten-freundliche Anzeigenamen statt Roh-Ticker
_TICKER_NAMES = {
    "^GSPC": "S&P 500", "^GDAXI": "DAX", "^NDX": "Nasdaq 100", "^IXIC": "Nasdaq",
    "^DJI": "Dow Jones", "^STOXX50E": "Euro Stoxx 50", "^FTSE": "FTSE 100",
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "EURUSD=X": "EUR/USD",
    "SPY": "S&P 500 (SPY)", "QQQ": "Nasdaq 100 (QQQ)", "DIA": "Dow Jones (DIA)",
    "GLD": "Gold (GLD)", "USO": "Oil (USO)", "TLT": "US Treasuries (TLT)",
}


def _disp(ticker: str) -> str:
    return _TICKER_NAMES.get(ticker, ticker.replace("^", ""))


def _fmt(v: float, lang: str, plus: bool = True) -> str:
    """Prozent-String; DE mit Komma, EN mit Punkt."""
    s = (f"{v:+.1f}" if plus else f"{v:.1f}")
    if lang == "de":
        s = s.replace(".", ",")
    return s + "%"


# ----------------------------------------------------------------------------- Daten
def _load_year_data(ticker: str, years: int):
    """Laedt Echtdaten (Yahoo-Default-Basis) + baut normalisierte Jahresdaten.

    Reuse exakt der Website-Methodik: download_data/preprocess + build_year_data.
    Returns (year_data, n_years, data_date) oder (None, 0, None).
    """
    from shared.yahoo_downloader import download_data, preprocess
    from shared.calculations import build_year_data

    raw = download_data(ticker)
    if raw is None or len(raw) == 0:
        return None, 0, None
    df = preprocess(raw)

    # Datenstand (juengstes Datum) robust ermitteln
    if "Date" in df.columns:
        data_date = str(df["Date"].iloc[-1])[:10]
    else:
        try:
            data_date = str(df.index[-1])[:10]
        except Exception:
            data_date = ""

    cy = date.today().year
    selected = [y for y in sorted(df["year"].unique()) if y >= cy - years]
    if not selected:
        return None, 0, data_date
    yd = build_year_data(df, selected)
    return yd, (len(yd) if yd else 0), data_date


def _seasonal_avg(year_data):
    from shared.calculations import calculate_seasonal_average
    avg, std = calculate_seasonal_average(year_data)
    return np.asarray(avg, dtype=float), (np.asarray(std, dtype=float) if std else None)


def _monthly_avg(year_data):
    month_returns = {m: [] for m in range(1, 13)}
    for yd in year_data.values():
        f365 = yd["full_365"]
        for m in range(1, 13):
            s, e = _MONTH_DOY[m]
            sv = f365[s - 1]
            ev = f365[min(e - 1, 364)]
            if sv:
                month_returns[m].append((ev - sv) / sv * 100)
    return np.array([float(np.mean(month_returns[m])) if month_returns[m] else 0.0
                     for m in range(1, 13)])


# ----------------------------------------------------------------------------- Layout
def _new_fig():
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor(BG)
    return fig


def _chrome(fig, title, subtitle, kpi, data_date, lang):
    """Statische Rahmen-Elemente (Titel, KPI-Badge, Branding, Datenstand)."""
    fig.text(0.5, 0.945, title, color=TEXT, fontsize=30, fontweight="bold",
             ha="center", va="center")
    if subtitle:
        fig.text(0.5, 0.905, subtitle, color=MUTED, fontsize=18, ha="center", va="center")
    # KPI-Badge (zitierfaehige Kernzahl)
    if kpi:
        fig.text(0.5, 0.20, kpi, color=WARM, fontsize=40, fontweight="bold",
                 ha="center", va="center")
    if not _VIDEO_MODE:
        # Standalone-Chart: Branding + CTA + Dauer-Disclaimer-Fußzeile
        fig.text(0.5, 0.085, "seasonalpha.ai", color=ACCENT, fontsize=26, fontweight="bold",
                 ha="center", va="center")
        cta = "Interaktiv für jeden Ticker" if lang == "de" else "Interactive for every ticker"
        fig.text(0.5, 0.055, cta, color=MUTED, fontsize=16, ha="center", va="center")
        disc = ("Historische Daten · keine Anlageberatung" if lang == "de"
                else "Historical data · not investment advice")
        fig.text(0.03, 0.012, disc, color=MUTED, fontsize=11, ha="left", va="bottom")
        stamp_y, stamp_va = 0.012, "bottom"
    else:
        # Video-Mode: unten freihalten (Compose legt dort Untertitel/Disclaimer/Branding)
        stamp_y, stamp_va = 0.885, "top"
    # Datenstand-Stempel (immer)
    if data_date:
        stamp = (f"Daten: {data_date}" if lang == "de" else f"Data: {data_date}")
        fig.text(0.97, stamp_y, stamp, color=MUTED, fontsize=11, ha="right", va=stamp_va)


def _style_axes(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=15, length=0)
    ax.grid(True, color="white", alpha=0.05, linewidth=1)


# ----------------------------------------------------------------------------- Render
def _render(frames_dir: Path, draw_frame, n_frames: int, hold: int):
    """Ruft draw_frame(p in [0,1]) je Frame auf, speichert PNGs (inkl. End-Hold)."""
    idx = 0
    for i in range(n_frames):
        p = (i + 1) / n_frames
        fig = draw_frame(p)
        fig.savefig(frames_dir / f"f{idx:05d}.png", facecolor=BG)
        plt.close(fig)
        idx += 1
    # End-Hold (letztes Bild stehen lassen)
    last = frames_dir / f"f{idx - 1:05d}.png"
    for _ in range(hold):
        dst = frames_dir / f"f{idx:05d}.png"
        shutil.copyfile(last, dst)
        idx += 1
    return idx


def _ease(p):  # easeOutCubic
    return 1 - (1 - p) ** 3


def draw_seasonal(year_data, n_years, data_date, ticker, lang):
    avg, std = _seasonal_avg(year_data)
    x = np.arange(1, 366)
    labels = _MONTH_LABELS_EN if lang == "en" else _MONTH_LABELS_DE
    name = _disp(ticker)
    pct = avg[-1] - 100.0
    if lang == "en":
        title = f"{name} · Seasonal Year"
        subtitle = f"Normalized (start = 100) · {n_years} years"
        kpi = f"Ø year: {_fmt(pct, lang)}"
    else:
        title = f"{name} · Saisonaler Jahresverlauf"
        subtitle = f"Normiert (Start = 100) · {n_years} Jahre"
        kpi = f"Ø Jahr: {_fmt(pct, lang)}"
    if std is not None:
        lo = float(np.min(avg - std)); hi = float(np.max(avg + std))
    else:
        lo = float(np.min(avg)); hi = float(np.max(avg))
    pad = (hi - lo) * 0.06 + 0.3

    def frame(p):
        fig = _new_fig()
        ax = fig.add_axes([0.12, 0.30, 0.80, 0.52])
        _style_axes(ax)
        k = max(2, int(_ease(p) * 365))
        ax.axhline(100, color="white", alpha=0.18, ls="--", lw=1)
        if std is not None:
            ax.fill_between(x[:k], (avg - std)[:k], (avg + std)[:k],
                            color=BLUE, alpha=0.12, linewidth=0)
        ax.plot(x[:k], avg[:k], color=ACCENT, lw=4, solid_capstyle="round")
        ax.scatter([x[k - 1]], [avg[k - 1]], color=ACCENT, s=70, zorder=5,
                   edgecolors=BG, linewidths=2)
        ax.set_xlim(1, 365)
        ax.set_ylim(lo - pad, hi + pad)
        ax.set_xticks(_MONTH_STARTS)
        ax.set_xticklabels(labels)
        _chrome(fig, title, subtitle, kpi, data_date, lang)
        return fig

    return frame


def draw_monthly(year_data, n_years, data_date, ticker, lang):
    vals = _monthly_avg(year_data)
    labels = _MONTH_LABELS_EN if lang == "en" else _MONTH_LABELS_DE
    name = _disp(ticker)
    hl = _HIGHLIGHT_MONTH or date.today().month
    best = int(np.argmax(vals)) + 1
    full = _MONTH_FULL_EN if lang == "en" else _MONTH_FULL_DE
    if lang == "en":
        title = f"{name} · Avg Return / Month"
        subtitle = f"{n_years} years"
        kpi = (f"{full[hl - 1]}: avg {_fmt(vals[hl - 1], lang)}" if _HIGHLIGHT_MONTH
               else f"Best: {labels[best - 1]} {_fmt(vals[best - 1], lang)}")
    else:
        title = f"{name} · Ø Rendite je Monat"
        subtitle = f"{n_years} Jahre"
        kpi = (f"{full[hl - 1]}: Ø {_fmt(vals[hl - 1], lang)}" if _HIGHLIGHT_MONTH
               else f"Stärkster: {labels[best - 1]} {_fmt(vals[best - 1], lang)}")
    cols = [WARM if (i + 1) == hl else (ACCENT if v >= 0 else NEG)
            for i, v in enumerate(vals)]
    vmax = float(max(abs(vals.min()), abs(vals.max()))) * 1.35 + 0.3

    def frame(p):
        fig = _new_fig()
        ax = fig.add_axes([0.12, 0.30, 0.80, 0.52])
        _style_axes(ax)
        e = _ease(p)
        ax.axhline(0, color="white", alpha=0.25, ls=":", lw=1)
        ax.bar(range(1, 13), vals * e, color=cols, width=0.74)
        if p > 0.82:  # Werte erst am Ende einblenden
            a = min(1.0, (p - 0.82) / 0.18)
            for i, v in enumerate(vals, start=1):
                ax.annotate(_fmt(v, lang), (i, v), ha="center",
                            va="bottom" if v >= 0 else "top",
                            color=TEXT, fontsize=12, alpha=a,
                            xytext=(0, 4 if v >= 0 else -4), textcoords="offset points")
        ax.set_xlim(0.4, 12.6)
        ax.set_ylim(-vmax, vmax)
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(labels)
        _chrome(fig, title, subtitle, kpi, data_date, lang)
        return fig

    return frame


_DRAWERS = {"seasonal_yearly": draw_seasonal, "monthly_cycle": draw_monthly}


def main():
    ap = argparse.ArgumentParser(description="SeasonAlpha vertical chart video renderer")
    ap.add_argument("--type", required=True, choices=list(_DRAWERS), dest="ctype")
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--years", type=int, default=20)
    ap.add_argument("--lang", default="de", choices=["de", "en"])
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--seconds", type=float, default=5.0, help="Animationsdauer (ohne End-Hold)")
    ap.add_argument("--hold", type=float, default=1.5, help="Standzeit am Ende (s)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--video-mode", action="store_true",
                    help="Branding/Footer weglassen — Compose legt dort Untertitel/Disclaimer hin")
    ap.add_argument("--highlight-month", type=int, default=None,
                    help="Monat 1-12 hervorheben + KPI fokussieren (Default: aktueller Monat)")
    args = ap.parse_args()
    global _VIDEO_MODE, _HIGHLIGHT_MONTH
    _VIDEO_MODE = args.video_mode
    _HIGHLIGHT_MONTH = args.highlight_month

    print(f"[render] {args.ctype} {args.ticker} ({args.years}J, {args.lang}) — lade Echtdaten…")
    year_data, n_years, data_date = _load_year_data(args.ticker, args.years)
    if not year_data:
        print(f"[render] FEHLER: keine Daten für {args.ticker}")
        sys.exit(2)
    print(f"[render] {n_years} Jahre, Datenstand {data_date}")

    drawer = _DRAWERS[args.ctype](year_data, n_years, data_date, args.ticker, args.lang)

    out_dir = Path(__file__).resolve().parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_ticker = args.ticker.replace("^", "").replace("=", "").replace("/", "")
    out = Path(args.out) if args.out else out_dir / f"{safe_ticker}_{args.ctype}_{args.lang}.mp4"

    n_frames = int(args.fps * args.seconds)
    hold_frames = int(args.fps * args.hold)
    tmp = Path(tempfile.mkdtemp(prefix="savid_"))
    try:
        total = _render(tmp, drawer, n_frames, hold_frames)
        # Hero-Still = letzter Frame
        still = out.with_name(out.stem + "_still.png")
        shutil.copyfile(tmp / f"f{total - 1:05d}.png", still)
        # ffmpeg: Frames -> MP4 (yuv420p fuer Social-Kompatibilitaet)
        cmd = [
            "ffmpeg", "-y", "-framerate", str(args.fps),
            "-i", str(tmp / "f%05d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-r", str(args.fps), str(out),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("[render] ffmpeg-Fehler:\n" + r.stderr[-1500:])
            sys.exit(3)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"[render] OK -> {out}")
    print(f"[render] Still -> {still}")


if __name__ == "__main__":
    main()
