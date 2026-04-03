"""
scripts/generate_landing_chart.py — Generiert chart-data.json fuer Landing Page
================================================================================
Erzeugt vorberechnete Jahreskurven (DJI, 130+ Jahre) als statisches JSON.
Die Landing Page laedt dieses JSON und rendert den interaktiven Split-Slider.

Aufruf: py scripts/generate_landing_chart.py
        py -m scripts.generate_landing_chart
"""

import sys
import os
import pathlib
import json

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import numpy as np
import pandas as pd
from datetime import datetime
from shared.yahoo_downloader import download_data, preprocess


def generate(ticker="^DJI", output_path=None):
    """Generiert chart-data.json mit normalisierten Jahreskurven."""
    if output_path is None:
        output_path = os.path.join(_project_dir, "landing", "chart-data.json")

    print(f"Lade {ticker} ...")
    raw_df = download_data(ticker, period="max")
    if raw_df is None or raw_df.empty:
        print("FEHLER: Keine Daten!")
        return

    df = preprocess(raw_df)
    print(f"  {len(df)} Zeilen, {df['year'].nunique()} Jahre "
          f"({df['year'].min()}-{df['year'].max()})")

    # Normalisierte Jahreskurven berechnen
    target_days = 252
    current_year = datetime.now().year
    years_data = {}
    all_curves = []

    for year in sorted(df["year"].unique()):
        ydf = df[df["year"] == year].sort_index()
        if len(ydf) < 20:
            continue

        # Kumulative Log-Returns (startet bei 0%)
        log_rets = ydf["log_return"].values
        cum = np.cumsum(log_rets)
        curve = (np.exp(cum) - 1) * 100  # In Prozent

        # Aktuelles Jahr: NICHT padden (nur echte Daten)
        if year == current_year:
            curve_list = [round(float(v), 2) for v in curve]
            years_data[str(year)] = curve_list
            continue

        # Historische Jahre: auf target_days interpolieren
        if len(curve) < target_days:
            padded = np.full(target_days, curve[-1])
            padded[:len(curve)] = curve
            curve = padded
        elif len(curve) > target_days:
            indices = np.linspace(0, len(curve) - 1, target_days).astype(int)
            curve = curve[indices]

        curve_list = [round(float(v), 2) for v in curve]
        years_data[str(year)] = curve_list
        all_curves.append(curve)

    # Durchschnitt berechnen
    if all_curves:
        avg = np.mean(all_curves, axis=0)
        avg_list = [round(float(v), 2) for v in avg]
    else:
        avg_list = [0.0] * target_days

    result = {
        "ticker": ticker,
        "n_years": len(years_data),
        "trading_days": target_days,
        "average": avg_list,
        "years": years_data,
        "current_year": current_year,
    }

    # JSON schreiben
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, separators=(",", ":"))

    size_kb = os.path.getsize(output_path) / 1024
    print(f"  Geschrieben: {output_path} ({size_kb:.0f} KB, {len(years_data)} Jahre)")


if __name__ == "__main__":
    generate()
