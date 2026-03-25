"""
SeasonAlpha - Konstanten & Konfiguration
==========================================
Farben, Labels, Presets und statische Daten.
"""

# ── Defaults ─────────────────────────────────────────────────
DEFAULT_TICKER = "AAPL"
DEFAULT_YEARS = 20

# ── SeasonAlpha Theme Palette (Highcharts dark-unica inspired) ──
SE_COLORS = {
    # Backgrounds
    "bg":            "#080c12",
    "surface":       "#0f1923",
    "surface_alt":   "#131d2a",
    "panel_border":  "#1c2a3e",

    # Grid & Axes
    "grid":          "rgba(255,255,255,0.04)",
    "grid_major":    "rgba(255,255,255,0.07)",
    "axis_line":     "rgba(255,255,255,0.12)",
    "zero_line":     "rgba(77,159,255,0.25)",

    # Text
    "text_primary":  "#c8d6e5",
    "text_muted":    "#5a6e85",
    "text_dim":      "#3a4a5e",

    # Accents
    "accent":        "#00d4aa",
    "accent_warm":   "#e8a425",
    "accent_blue":   "#4d9fff",
    "accent2":       "#ff6b35",

    # Semantic
    "positive":      "#00d4aa",
    "negative":      "#ff4757",
    "neutral":       "rgba(160,180,210,0.35)",

    # Traces
    "current_year":  "rgba(232,164,37,0.92)",
    "individual":    "rgba(160,180,210,0.18)",
    "confidence":    "rgba(0,212,170,0.08)",
    "avg_line":      "#00d4aa",

    # Watermark
    "watermark":     "rgba(255,255,255,0.03)",
}

# ── Standard-Heatmap Colorscale (Ampelsystem) ──────────────────────
# Leuchtend, hoher Kontrast, symmetrisch um 0
SE_HEATMAP_COLORSCALE = [
    [0.0,  "#cc0000"],     # Starkes Rot (extrem negativ)
    [0.25, "#ff4757"],     # SE negative (leicht negativ)
    [0.5,  "#0f1923"],     # SE surface (neutral/null)
    [0.75, "#00d4aa"],     # SE positive (leicht positiv)
    [1.0,  "#00ff99"],     # Leuchtend Gruen (extrem positiv)
]

SE_HEATMAP_TEXT_COLOR = "#FFFFFF"

# ── Farben (Backward-Kompatibilität) ────────────────────────
COLOR_SEASONAL_AVG = SE_COLORS["avg_line"]
COLOR_INDIVIDUAL = SE_COLORS["individual"]
COLOR_CONFIDENCE = SE_COLORS["confidence"]
COLOR_CURRENT_YEAR = SE_COLORS["current_year"]
COLOR_PRESSURE = "#e056a0"
COLOR_WAR = "#e8553a"

CYCLE_COLORS = {
    "Year 1 (Post-Election)": "#e8553a",
    "Year 2 (Midterm Election)": "#e8a425",
    "Year 3 (Pre-Election)": "#00d4aa",
    "Year 4 (Election Year)": "#4d9fff"
}

DECADE_COLORS = {
    0: "#e8553a", 1: "#e87d3a", 2: "#e8a425", 3: "#d4c44a",
    4: "#6bcb77", 5: "#00d4aa", 6: "#4d9fff", 7: "#5b7fc7",
    8: "#8b6bb5", 9: "#c06bb5"
}

DECADE_LABELS = {
    0: "X0er (1900, 1910, ...2020)", 1: "X1er (1901, 1911, ...2021)",
    2: "X2er (1902, 1912, ...2022)", 3: "X3er (1903, 1913, ...2023)",
    4: "X4er (1904, 1914, ...2024)", 5: "X5er (1905, 1915, ...2025)",
    6: "X6er (1906, 1916, ...2026)", 7: "X7er (1907, 1917, ...2027)",
    8: "X8er (1908, 1918, ...2028)", 9: "X9er (1909, 1919, ...2029)"
}

OVERLAY_CONFIGS = {
    "Last Year": {
        "years_back": 1,
        "color": "#FF9800",
        "dash": "solid",
        "width": 2
    },
    "Last 5 Years": {
        "years_back": 5,
        "color": "#9C27B0",
        "dash": "dash",
        "width": 2
    },
    "Last 10 Years": {
        "years_back": 10,
        "color": "#2196F3",
        "dash": "dot",
        "width": 2
    }
}

# ── Monatsnamen ──────────────────────────────────────────────
MONTH_NAMES_DE = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                  "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

# ── Pressure-Perioden ────────────────────────────────────────
PRESSURE_PERIODS = [10, 20, 30, 40, 60, 80]

# ── US-Kriege mit US-Beteiligung ─────────────────────────────
US_WARS = [
    {"name": "Spanisch-Amerikanischer Krieg", "start": 1898, "end": 1898},
    {"name": "Philippinisch-Amerikanischer Krieg", "start": 1899, "end": 1902},
    {"name": "Erster Weltkrieg (US)", "start": 1917, "end": 1918},
    {"name": "Zweiter Weltkrieg (US)", "start": 1941, "end": 1945},
    {"name": "Koreakrieg", "start": 1950, "end": 1953},
    {"name": "Vietnamkrieg", "start": 1965, "end": 1975},
    {"name": "Golfkrieg", "start": 1990, "end": 1991},
    {"name": "Krieg in Afghanistan", "start": 2001, "end": 2021},
    {"name": "Irakkrieg", "start": 2003, "end": 2011},
]
