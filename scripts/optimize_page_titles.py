"""
optimize_page_titles.py — SEO-optimierte Titles + Descriptions fuer Landing-Pages.

Google kappt Titles bei ~60 Zeichen. Descriptions bei ~160.
Aktuelle Titles sind generisch ("Feature — SeasonAlpha"), liefern wenig
Keyword-Signal. Dieser Script ersetzt Title + Meta-Description durch
SEO-optimierte Varianten mit Ziel-Keywords.

Idempotent ueber MARKER-Check. Laeuft VOR upgrade_page_meta.py — der
nimmt dann die neuen Titles in die OG/Twitter/JSON-LD Tags auf.

Usage:
  py scripts/optimize_page_titles.py           # dry-run
  py scripts/optimize_page_titles.py --write   # schreibt
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGES_DIR = REPO / "landing" / "pages"

# Slug -> (neuer title, neue description)
# Ziel: title <= 60 chars, description 140-160 chars, beide mit Ziel-Keywords
PAGE_SEO = {
    "dashboard.html": {
        "title": "Ticker Dashboard &mdash; Saisonalit&auml;t auf einen Blick | SeasonAlpha",
        "description": "Alle Saisonal-Signale f&uuml;r deinen Ticker: KI-Score, Crash-Ampel, Jahreschart, TruePath, Strategien, Events. Dein Cockpit f&uuml;r datengetriebene Trading-Entscheidungen.",
    },
    "scanner.html": {
        "title": "Saisonal-Scanner &mdash; Alle Ticker nach KI-Score | SeasonAlpha",
        "description": "Saisonal-Scanner: alle Ticker nach KI-Score sortiert. Filter nach Kategorie, Signal (Bullish/Bearish/Neutral), Win-Rate. Screening f&uuml;r saisonale Trading-Chancen.",
    },
    "jahreszyklus.html": {
        "title": "Jahreszyklus &mdash; Saisonale Jahresmuster am Markt | SeasonAlpha",
        "description": "Saisonaler Jahresverlauf, Pressure Chart, Detrend, Pr&auml;sidentenzyklus, Monats- & Quartals-Performance. Erkenne wiederkehrende Muster mit bis zu 131 Jahren Daten.",
    },
    "monatszyklus.html": {
        "title": "Monatszyklus &mdash; Intra-Monat Saisonalit&auml;t | SeasonAlpha",
        "description": "TDOM-Analyse, Two-Week Performance, Wochen-Bias, Monats-Heatmap, Saisonal Match. Welche Tage im Monat statistisch besonders stark oder schwach sind.",
    },
    "dekadenzyklus.html": {
        "title": "Dekadenzyklus &mdash; 131 Jahre Dow-Jones-Muster | SeasonAlpha",
        "description": "131 Jahre Dow-Jones-Daten nach Dekaden-Kohorten aufgeschl&uuml;sselt. Jahresverlauf, Drawdown, Volatilit&auml;t & Heatmap &mdash; wie verh&auml;lt sich x0, x1, x2... im Durchschnitt?",
    },
    "wochentage.html": {
        "title": "Wochentag-Effekt &mdash; Bester B&ouml;rsentag analysiert | SeasonAlpha",
        "description": "Mo-Fr Renditen, Signifikanztest, Weekend-Effekt, Overnight vs Intraday. Welcher Wochentag historisch die st&auml;rksten Returns liefert &mdash; statistisch belegt.",
    },
    "monatswechsel.html": {
        "title": "Turn-of-the-Month Effekt &mdash; TOM Trading | SeasonAlpha",
        "description": "Die letzten 3 und ersten 3 Handelstage des Monats liefern oft die st&auml;rksten Renditen. TOM-Heatmap, Signifikanztest, Streak-Analyse, Indikator-Filter.",
    },
    "mondphasen.html": {
        "title": "Mondphasen &amp; B&ouml;rse &mdash; Voll-/Neumond-Effekt | SeasonAlpha",
        "description": "Renditen rund um Voll-, Neu- und Supermond wissenschaftlich analysiert. Mond-Heatmap, Signifikanz, Lunar-Kalender. Mythos oder messbarer Effekt?",
    },
    "zentralbanken.html": {
        "title": "Fed, EZB &amp; Notenbank-Effekt &mdash; Event-Trading | SeasonAlpha",
        "description": "Renditen rund um Fed-, EZB-, BoE- und BoJ-Sitzungen. Event-Window Analyse, Streak, Signifikanztest. Wie reagiert der Markt auf Zentralbank-Entscheidungen?",
    },
    "feiertage.html": {
        "title": "Feiertags-Effekt &mdash; Trading vor &amp; nach Holidays | SeasonAlpha",
        "description": "NYSE-, XETRA- und LSE-Feiertage analysiert: Pre-Holiday Rally, Post-Holiday Drift, Ranking, Heatmap. B&ouml;rsenspezifisch mit Exchange-aware Kalender.",
    },
    "opex.html": {
        "title": "OPEX &amp; VIXpiration &mdash; Verfallstags-Analyse | SeasonAlpha",
        "description": "Triple Witching, monatlicher OPEX, VIX-Settlement: Wie verhalten sich Kurse rund um den 3. Freitag? Heatmap, Backtest, Signifikanz und CBOE-konformer VIX-Kalender.",
    },
    "intermarket-shocks.html": {
        "title": "Intermarket Shocks &mdash; Trigger-Target-Analyse | SeasonAlpha",
        "description": "Wie reagiert SPY wenn VIX spiked? Oder Bitcoin wenn DXY f&auml;llt? Shock-Analyse mit Scatter, Regression und saisonalem Breakdown f&uuml;r jedes Ticker-Paar.",
    },
    "trifecta.html": {
        "title": "Januar Trifecta &mdash; SCR + FFD + JanB Signal | SeasonAlpha",
        "description": "Santa Claus Rally, First Five Days, January Barometer kombiniert: Die Ampel f&uuml;rs Gesamtjahr. Historische Hit-Rate, Drawdowns und Jahresrenditen nach Signal.",
    },
    "plain-vanilla.html": {
        "title": "Plain Vanilla Strategien &mdash; 24 Saisonal-Trades | SeasonAlpha",
        "description": "24 backgetestete Saisonal-Strategien: Sell in May, Santa Claus, Turn of Month, KTI, UECS. Equity-Kurven, Stats, Signifikanz, n&auml;chste Signale, Trailing Stops.",
    },
    "backtest-engine.html": {
        "title": "Backtest Engine &mdash; Event-Trading Optimierung | SeasonAlpha",
        "description": "Single Backtest, Parameter-Optimierung, Walk-Forward, Event-Relevanz. Teste Trading-Strategien rund um Feiertage, FOMC, OPEX und Mondphasen mit Stop-Loss.",
    },
    "ki-saisonalitaet.html": {
        "title": "KI-Saisonalit&auml;t &mdash; Composite Score &amp; Musterpfad | SeasonAlpha",
        "description": "KI-gest&uuml;tzte Saisonal-Prognose: Composite Score 1-10, Musterpfad aus Top-N &auml;hnlichsten Jahren, Forward-Projektion und Radar-Chart mit 4 Sub-Scores.",
    },
    "crash-fruehwarnung.html": {
        "title": "Crash-Fr&uuml;hwarnung &mdash; KI Regime-Ampel | SeasonAlpha",
        "description": "Isolation Forest Regime-Erkennung: Vol, Drawdown, Returns vs 252d-Percentile. Live Risk-Score, Traffic-Light-Ampel und historischer Backtest der Warnsignale.",
    },
    "spot-vol-beta.html": {
        "title": "Spot-Vol Beta &mdash; SPX vs VIX Regression | SeasonAlpha",
        "description": "Tagesaktuelles SPX-VIX Beta, Rolling Beta, Regime-Wendepunkte. VIX-Spikes, Complacency-Warnungen und Forward Returns 5/10/20/60 Tage.",
    },
    "tdom-analyse.html": {
        "title": "TDoM Analyse &mdash; Trading Day of Month | SeasonAlpha",
        "description": "3 TDoM-Strategien (Intraday, Overnight, Close-to-Close), Heatmap Monat &times; TDoM, Strategie-Tester mit Stop-Loss. Vorw&auml;rts- und r&uuml;ckw&auml;rts-Analyse.",
    },
    "overnight.html": {
        "title": "Overnight vs Intraday &mdash; Split-Analyse | SeasonAlpha",
        "description": "Wo verdienst du mit AAPL, GOOG, TSLA &amp; Co wirklich Geld &mdash; nachts oder tags&uuml;ber? OHLC-Split mit Signifikanztest und Indikator-Filter f&uuml;r jede Aktie.",
    },
    "sektor-rotation.html": {
        "title": "Sektor-Rotation &mdash; 23 US-Sektor-ETFs | SeasonAlpha",
        "description": "Welche US-Sektor-ETFs performen wann? 23 Select-Sector SPDRs als Heatmap, Top/Flop, Jahresverlauf und Win-Rate mit Streak-Analyse.",
    },
    "kriegszeiten.html": {
        "title": "Kriegszeiten &mdash; B&ouml;rse in Konflikten | SeasonAlpha",
        "description": "11 historische Kriege analysiert: Wie reagieren M&auml;rkte auf Konflikte? Event-Window mit Live-Overlay f&uuml;r aktuelle Krisen (Ukraine, Nahost, ...).",
    },
}

MARKER_PREFIX = "<!-- SA_META_V"  # V2, V3, V4 — irgendein Meta-Marker vorhanden


def upgrade_file(path: Path, *, write: bool) -> tuple[bool, str]:
    try:
        html = path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"read error: {e}"

    seo = PAGE_SEO.get(path.name)
    if not seo:
        return False, "not in PAGE_SEO"

    new_title = seo["title"]
    new_desc = seo["description"]

    # Check: title length (ohne HTML-Entities zaehlen)
    import html as h
    title_plain_len = len(h.unescape(new_title))
    desc_plain_len = len(h.unescape(new_desc))
    if title_plain_len > 65:
        return False, f"title too long ({title_plain_len} chars)"
    if desc_plain_len > 170:
        return False, f"description too long ({desc_plain_len} chars)"

    # <title> ersetzen
    new_html = re.sub(
        r"<title>.*?</title>",
        f"<title>{new_title}</title>",
        html,
        count=1,
        flags=re.DOTALL,
    )
    # <meta name="description"> ersetzen
    new_html = re.sub(
        r'<meta\s+name="description"\s+content="[^"]*"',
        f'<meta name="description" content="{new_desc}"',
        new_html,
        count=1,
    )

    if new_html == html:
        return False, "no change (title + description identical)"

    if write:
        path.write_text(new_html, encoding="utf-8")

    return True, f"title={title_plain_len}c, desc={desc_plain_len}c"


def main() -> None:
    write = "--write" in sys.argv
    mode = "WRITE" if write else "DRY-RUN"
    print(f"=== optimize_page_titles.py ({mode}) ===")

    changed = 0
    skipped = 0
    errors = 0

    for fname in sorted(PAGE_SEO.keys()):
        path = PAGES_DIR / fname
        if not path.exists():
            print(f"  [MISS] {fname}")
            errors += 1
            continue
        ok, reason = upgrade_file(path, write=write)
        if ok:
            print(f"  [{mode}] {fname}: {reason}")
            changed += 1
        else:
            print(f"  [SKIP] {fname}: {reason}")
            skipped += 1

    print()
    print(f"  changed: {changed}")
    print(f"  skipped: {skipped}")
    print(f"  errors:  {errors}")
    if not write and changed > 0:
        print()
        print("  -> Run with --write to apply changes.")
        print("  -> IMPORTANT: Rerun scripts/upgrade_page_meta.py after writing,")
        print("                  damit OG/Twitter/JSON-LD auch die neuen Titles aufnehmen.")


if __name__ == "__main__":
    main()
