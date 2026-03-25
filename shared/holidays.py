"""
SeasonAlpha - NYSE Feiertage
=============================
Berechnung aller NYSE-Feiertage und Feiertags-Effekt-Analyse.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime


# ── Hilfsfunktionen ──────────────────────────────────────────

def _nth_weekday(year, month, weekday, n):
    """
    Berechne den n-ten Wochentag eines Monats.
    weekday: 0=Mo, 1=Di, ..., 4=Fr
    n: 1=erster, 2=zweiter, etc.
    """
    from calendar import monthcalendar
    cal = monthcalendar(year, month)
    days = [week[weekday] for week in cal if week[weekday] != 0]
    return datetime(year, month, days[n - 1])


def _last_weekday(year, month, weekday):
    """Letzter Wochentag eines Monats."""
    from calendar import monthcalendar
    cal = monthcalendar(year, month)
    days = [week[weekday] for week in cal if week[weekday] != 0]
    return datetime(year, month, days[-1])


def _easter(year):
    """Berechne Ostersonntag nach dem Gauss-Algorithmus."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return datetime(year, month, day)


def _apply_weekend_rule(dt):
    """
    NYSE Weekend Rule:
    - Feiertag auf Samstag → Freitag geschlossen
    - Feiertag auf Sonntag → Montag geschlossen
    """
    wd = dt.weekday()
    if wd == 5:
        return dt - pd.Timedelta(days=1)
    elif wd == 6:
        return dt + pd.Timedelta(days=1)
    return dt


# ── NYSE-Feiertags-Definitionen ──────────────────────────────

HOLIDAY_DEFINITIONS = {
    "Neujahr": {
        "calc": lambda y: _apply_weekend_rule(datetime(y, 1, 1)),
        "label": "New Year's Day",
        "emoji": "🎆"
    },
    "MLK Day": {
        "calc": lambda y: _nth_weekday(y, 1, 0, 3),
        "label": "Martin Luther King Jr. Day",
        "emoji": "✊",
        "since": 1998
    },
    "Presidents Day": {
        "calc": lambda y: _nth_weekday(y, 2, 0, 3),
        "label": "Presidents' Day",
        "emoji": "🇺🇸"
    },
    "Karfreitag": {
        "calc": lambda y: _easter(y) - pd.Timedelta(days=2),
        "label": "Good Friday",
        "emoji": "✝️"
    },
    "Memorial Day": {
        "calc": lambda y: _last_weekday(y, 5, 0),
        "label": "Memorial Day",
        "emoji": "🎖️"
    },
    "Juneteenth": {
        "calc": lambda y: _apply_weekend_rule(datetime(y, 6, 19)),
        "label": "Juneteenth",
        "emoji": "✊",
        "since": 2022
    },
    "Independence Day": {
        "calc": lambda y: _apply_weekend_rule(datetime(y, 7, 4)),
        "label": "Independence Day",
        "emoji": "🎇"
    },
    "Labor Day": {
        "calc": lambda y: _nth_weekday(y, 9, 0, 1),
        "label": "Labor Day",
        "emoji": "⚒️"
    },
    "Thanksgiving": {
        "calc": lambda y: _nth_weekday(y, 11, 3, 4),
        "label": "Thanksgiving",
        "emoji": "🦃"
    },
    "Black Friday": {
        "calc": lambda y: _nth_weekday(y, 11, 3, 4) + pd.Timedelta(days=1),
        "label": "Black Friday (Early Close)",
        "emoji": "🛍️"
    },
    "Heiligabend": {
        "calc": lambda y: _apply_weekend_rule(datetime(y, 12, 24)) if datetime(y, 12, 24).weekday() < 5 else None,
        "label": "Christmas Eve (Early Close)",
        "emoji": "🎄"
    },
    "Weihnachten": {
        "calc": lambda y: _apply_weekend_rule(datetime(y, 12, 25)),
        "label": "Christmas Day",
        "emoji": "🎅"
    },
}


def get_nyse_holidays(year):
    """
    Berechne alle NYSE-Feiertage für ein gegebenes Jahr.
    
    Returns:
        list of dict: [{name, date, label, emoji}, ...]
    """
    holidays = []
    for name, defn in HOLIDAY_DEFINITIONS.items():
        since = defn.get("since", 1900)
        if year < since:
            continue
        try:
            dt = defn["calc"](year)
            if dt is None:
                continue
            holidays.append({
                "name": name,
                "date": pd.Timestamp(dt).normalize(),
                "label": defn["label"],
                "emoji": defn["emoji"]
            })
        except Exception:
            continue
    return holidays


# ── Feiertags-Effekt-Analyse ─────────────────────────────────

def analyze_holiday_effect(df, days_before, days_after, selected_holidays, selected_years):
    """
    Feiertags-Effekt-Analyse: t0 = letzter Handelstag VOR Feiertag → 0% normiert.
    """
    window_size = days_before + 1 + days_after
    t0_idx = days_before
    all_curves = []
    
    for year in selected_years:
        holidays = get_nyse_holidays(year)
        
        for hol in holidays:
            if hol["name"] not in selected_holidays:
                continue
            
            holiday_date = hol["date"]
            
            try:
                pre_holiday = df[df.index < holiday_date]
                if len(pre_holiday) < days_before + 1:
                    continue
                
                pre_window = pre_holiday.iloc[-(days_before + 1):]
                
                post_holiday = df[df.index > holiday_date]
                if len(post_holiday) < days_after:
                    continue
                
                post_window = post_holiday.iloc[:days_after]
                
                tom_window = pd.concat([pre_window, post_window])
                
                if len(tom_window) != window_size:
                    continue
                
                log_rets = tom_window["log_return"].values
                cum_log = np.cumsum(np.insert(log_rets, 0, 0)[:-1])
                raw_curve = 100 * np.exp(cum_log)
                
                t0_value = raw_curve[t0_idx]
                curve = ((raw_curve / t0_value - 1) * 100).tolist()
                
                total_return = curve[-1] - curve[0]
                
                all_curves.append({
                    "year": year,
                    "holiday": hol["name"],
                    "holiday_label": hol["label"],
                    "holiday_emoji": hol["emoji"],
                    "curve": curve,
                    "total_return": total_return
                })
                
            except Exception:
                continue
    
    if not all_curves:
        return None
    
    avg_curve = []
    for i in range(window_size):
        day_values = [c["curve"][i] for c in all_curves]
        avg_curve.append(np.mean(day_values))
    
    labels = []
    for i in range(window_size):
        offset = i - days_before
        if offset < 0:
            labels.append(f"t{offset}")
        elif offset == 0:
            labels.append("t0")
        else:
            labels.append(f"t+{offset}")
    
    returns = [c["total_return"] for c in all_curves]
    wins = [r for r in returns if r > 0]
    
    stats = {
        "avg_return": np.mean(returns),
        "median_return": np.median(returns),
        "win_rate": len(wins) / len(returns) * 100 if returns else 0,
        "std_dev": np.std(returns),
        "max_gain": max(returns),
        "max_loss": min(returns),
        "total_windows": len(all_curves),
        "winning": len(wins),
        "losing": len(returns) - len(wins)
    }
    
    sorted_curves = sorted(all_curves, key=lambda c: c["total_return"])
    
    return {
        "avg_curve": avg_curve,
        "all_curves": all_curves,
        "labels": labels,
        "stats": stats,
        "best": sorted_curves[-1],
        "worst": sorted_curves[0]
    }


def build_holiday_chart(hol_result, ticker, days_before, days_after, selected_holidays,
                        show_individual_hol=False):
    """Erstelle den Holiday-Effekt Chart (t0 = 0%)."""
    
    fig = go.Figure()
    
    labels = hol_result["labels"]
    avg_curve = hol_result["avg_curve"]
    x_indices = list(range(len(labels)))
    
    if show_individual_hol:
        for entry in hol_result["all_curves"]:
            fig.add_trace(go.Scatter(
                x=x_indices, y=entry["curve"],
                mode="lines",
                line=dict(color="rgba(150,150,150,0.15)", width=0.7),
                showlegend=False, hoverinfo="skip"
            ))
    
    t0_idx = days_before
    fig.add_vline(
        x=t0_idx, line_dash="dash",
        line_color="rgba(255,215,0,0.5)", line_width=1.5,
        annotation_text="t0 (letzter HT vor Feiertag)",
        annotation_position="top",
        annotation_font=dict(size=10, color="#FFD700")
    )
    
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)", line_width=1)
    
    fig.add_vrect(
        x0=t0_idx, x1=t0_idx + 1,
        fillcolor="rgba(255,69,0,0.1)", line_width=0,
        annotation_text="📅 Feiertag",
        annotation_position="top",
        annotation_font=dict(size=9, color="#FF6B6B")
    )
    
    fig.add_trace(go.Scatter(
        x=x_indices, y=avg_curve,
        mode="lines+markers",
        line=dict(color="#FF6B6B", width=3),
        marker=dict(size=6, color="#FF6B6B"),
        fill="tozeroy", fillcolor="rgba(255,107,107,0.1)",
        name=f"Ø Holiday ({hol_result['stats']['total_windows']} Fenster)",
        hovertemplate="%{text}<br>%{y:+.3f}%<extra></extra>",
        text=labels
    ))
    
    if len(selected_holidays) == 1:
        hol_str = selected_holidays[0]
    elif len(selected_holidays) <= 3:
        hol_str = ", ".join(selected_holidays)
    else:
        hol_str = f"{len(selected_holidays)} Feiertage"
    
    from shared.charts import apply_se_theme
    fig = apply_se_theme(
        fig,
        title=f"{ticker} — Feiertags-Effekt (t-{days_before} bis t+{days_after}) · {hol_str}",
        height=420,
    )
    fig.update_xaxes(tickmode="array", tickvals=x_indices, ticktext=labels, title="Handelstage relativ zum Feiertag")
    fig.update_yaxes(title="Rendite relativ zu t0 (%)", tickformat="+.2f", ticksuffix="%")
    
    return fig
