"""
SeasonalEdge - Konstanten & Konfiguration
==========================================
Farben, Labels, Presets und statische Daten.
"""

# ── Defaults ─────────────────────────────────────────────────
DEFAULT_TICKER = "AAPL"
DEFAULT_YEARS = 20

# ── Farben ───────────────────────────────────────────────────
COLOR_SEASONAL_AVG = "#00CED1"
COLOR_INDIVIDUAL = "rgba(150,150,150,0.25)"
COLOR_CONFIDENCE = "rgba(0,206,209,0.15)"
COLOR_CURRENT_YEAR = "#FFD700"
COLOR_PRESSURE = "#FF69B4"
COLOR_WAR = "#FF4500"

CYCLE_COLORS = {
    "Year 1 (Post-Election)": "#FF6B6B",
    "Year 2 (Midterm Election)": "#FFA07A",
    "Year 3 (Pre-Election)": "#4ECDC4",
    "Year 4 (Election Year)": "#45B7D1"
}

DECADE_COLORS = {
    0: "#FF6B6B", 1: "#FF8E72", 2: "#FFA07A", 3: "#FFD93D",
    4: "#6BCB77", 5: "#4ECDC4", 6: "#45B7D1", 7: "#4682C8",
    8: "#9664B4", 9: "#C875C4"
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
