"""
SeasonalEdge - Chart Builder
==============================
Erstellt den interaktiven Plotly Saisonalchart.
"""

import pandas as pd
import numpy as np
import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _candidate in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_candidate, "shared")):
            _project_dir = _candidate
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)
import plotly.graph_objects as go
from datetime import datetime

from shared.constants import (
    COLOR_SEASONAL_AVG, COLOR_INDIVIDUAL, COLOR_CONFIDENCE,
    COLOR_CURRENT_YEAR, COLOR_PRESSURE, COLOR_WAR,
    CYCLE_COLORS, DECADE_COLORS, OVERLAY_CONFIGS
)
from shared.calculations import get_presidential_cycle_year, get_decade_digit
from shared.holidays import get_nyse_holidays


def build_seasonal_chart(year_data, avg, std, ticker, smoothing_window,
                          show_individual, show_bands, show_current_year,
                          selected_range, selected_cycles=None, selected_decades=None,
                          indicator_years=None, indicator_label=None, indicator_color=None,
                          pressure_curve=None, war_years_data=None, war_label=None,
                          df=None, overlay_options=None):
    """Erstelle den interaktiven Plotly Seasonal Chart."""
    
    fig = go.Figure()
    
    # Monatslabels für X-Achse
    month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                   "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    month_starts = []
    for m in range(1, 13):
        day = datetime(2024, m, 1).timetuple().tm_yday
        month_starts.append(day)
    
    x_days = list(range(1, 366))
    
    # ── Hover-Lookup: Datum, CDOY, TDOY, TDOM für jeden der 365 Tage ──
    hover_texts = []
    current_year = datetime.now().year
    
    # Schritt 1: Bekannte Handelstage aus den echten Daten (Vergangenheit)
    tdoy_map = {}  # cdoy → tdoy
    tdom_map = {}  # cdoy → tdom
    
    if df is not None:
        cy_df = df[df["year"] == current_year].copy()
        if len(cy_df) > 0:
            cy_df = cy_df.sort_index()
            cy_df["tdoy"] = range(1, len(cy_df) + 1)
            cy_df["tdom"] = cy_df.groupby("month").cumcount() + 1
            
            for _, row in cy_df.iterrows():
                cdoy = int(row["day_of_year"])
                tdoy_map[cdoy] = int(row["tdoy"])
                tdom_map[cdoy] = int(row["tdom"])
    
    # Schritt 2: Zukünftige Handelstage projizieren (Wochenenden + Feiertage auslassen)
    # Sammle NYSE-Feiertage für das aktuelle Jahr
    holiday_dates = set()
    try:
        for hol in get_nyse_holidays(current_year):
            hd = hol["date"]
            holiday_dates.add(hd.timetuple().tm_yday)
    except Exception:
        pass
    
    # Finde den letzten bekannten TDOY und TDOM
    last_known_cdoy = max(tdoy_map.keys()) if tdoy_map else 0
    last_tdoy = tdoy_map.get(last_known_cdoy, 0)
    
    # Für TDOM: letzten bekannten Monat und TDOM merken
    last_known_month = 0
    last_tdom = 0
    if tdom_map and last_known_cdoy > 0:
        dt_last = datetime(current_year, 1, 1) + pd.Timedelta(days=last_known_cdoy - 1)
        last_known_month = dt_last.month
        last_tdom = tdom_map[last_known_cdoy]
    
    # Projiziere ab dem letzten bekannten Tag weiter
    projected_tdoy = last_tdoy
    projected_tdom = last_tdom
    projected_month = last_known_month
    
    for cdoy in range(last_known_cdoy + 1, 366):
        try:
            dt = datetime(current_year, 1, 1) + pd.Timedelta(days=cdoy - 1)
        except Exception:
            continue
        
        wd = dt.weekday()  # 0=Mo, 5=Sa, 6=So
        is_weekend = wd >= 5
        is_holiday = cdoy in holiday_dates
        
        # Monatswechsel? → TDOM zurücksetzen
        if dt.month != projected_month:
            projected_month = dt.month
            projected_tdom = 0
        
        if not is_weekend and not is_holiday:
            projected_tdoy += 1
            projected_tdom += 1
            tdoy_map[cdoy] = projected_tdoy
            tdom_map[cdoy] = projected_tdom
    
    # Schritt 3: Hover-Text bauen — Format wie im Screenshot
    for cdoy in range(1, 366):
        try:
            dt = datetime(current_year, 1, 1) + pd.Timedelta(days=cdoy - 1)
            date_str = dt.strftime("%d.%m.%Y")
        except Exception:
            date_str = f"Tag {cdoy}"
        
        tdoy_val = tdoy_map.get(cdoy, None)
        tdom_val = tdom_map.get(cdoy, None)
        
        # Für Wochenenden/Feiertage: letzten bekannten Wert mit * anzeigen
        if tdoy_val is None:
            for lookback in range(1, 6):
                prev = cdoy - lookback
                if prev in tdoy_map:
                    tdoy_val = f"{tdoy_map[prev]}*"
                    tdom_val = f"{tdom_map[prev]}*"
                    break
        
        if tdoy_val is None:
            tdoy_val = "–"
            tdom_val = "–"
        
        hover_texts.append(
            f"<b>{date_str}</b><br>"
            f"CDOY: {cdoy}<br>"
            f"TDOY: {tdoy_val}<br>"
            f"TDOM: {tdom_val}"
        )
    
    # ── Zeitraummarkierung ────────────────────────────
    if selected_range:
        fig.add_vrect(
            x0=selected_range[0], x1=selected_range[1],
            fillcolor="rgba(255,255,255,0.05)",
            line_width=0,
            annotation_text="",
        )
        fig.add_vline(x=selected_range[0], line_dash="dash", 
                      line_color="rgba(255,255,255,0.3)", line_width=1)
        fig.add_vline(x=selected_range[1], line_dash="dash",
                      line_color="rgba(255,255,255,0.3)", line_width=1)
    
    # ── Einzelne Jahre (grau, transparent) ────────────
    if show_individual:
        for year, yd in year_data.items():
            fig.add_trace(go.Scatter(
                x=x_days,
                y=yd["full_365"],
                mode="lines",
                line=dict(color=COLOR_INDIVIDUAL, width=0.8),
                name=str(year),
                showlegend=False,
                hoverinfo="skip"
            ))
    
    # ── Confidence Bands (±1 Std.Abw.) ────────────────
    if show_bands and std:
        upper = [avg[i] + std[i] for i in range(365)]
        lower = [avg[i] - std[i] for i in range(365)]
        
        fig.add_trace(go.Scatter(
            x=x_days, y=upper,
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip"
        ))
        fig.add_trace(go.Scatter(
            x=x_days, y=lower,
            mode="lines", line=dict(width=0),
            fill="tonexty",
            fillcolor=COLOR_CONFIDENCE,
            name="±1σ Band",
            showlegend=True,
            hoverinfo="skip"
        ))
    
    # ── Präsidentenzyklus-Linien ──────────────────────
    if selected_cycles:
        for cycle_type in selected_cycles:
            matching_years = [y for y in year_data.keys()
                            if get_presidential_cycle_year(y) == cycle_type]
            
            if not matching_years:
                continue
            
            cycle_curves = [year_data[y]["full_365"] for y in matching_years]
            cycle_avg = [np.mean([c[d] for c in cycle_curves]) for d in range(365)]
            
            # Glätten
            if smoothing_window > 1:
                cycle_avg = pd.Series(cycle_avg).rolling(
                    smoothing_window, center=True, min_periods=1
                ).mean().tolist()
            
            fig.add_trace(go.Scatter(
                x=x_days, y=cycle_avg,
                mode="lines",
                line=dict(color=CYCLE_COLORS[cycle_type], width=2, dash="dash"),
                name=f"{cycle_type} ({len(matching_years)}y)",
            ))
    
    # ── Dekadenzyklus-Linien ──────────────────────────
    if selected_decades:
        for digit in selected_decades:
            matching_years = [y for y in year_data.keys()
                            if get_decade_digit(y) == digit]
            
            if not matching_years:
                continue
            
            decade_curves = [year_data[y]["full_365"] for y in matching_years]
            decade_avg = [np.mean([c[d] for c in decade_curves]) for d in range(365)]
            
            # Glätten
            if smoothing_window > 1:
                decade_avg = pd.Series(decade_avg).rolling(
                    smoothing_window, center=True, min_periods=1
                ).mean().tolist()
            
            fig.add_trace(go.Scatter(
                x=x_days, y=decade_avg,
                mode="lines",
                line=dict(color=DECADE_COLORS[digit], width=2, dash="dot"),
                name=f"X{digit}er Jahre ({len(matching_years)}y)",
            ))
    
    # ── Indikator-Linie (December Low / Januar) ───────
    if indicator_years and indicator_label and indicator_color:
        indicator_matching = [y for y in year_data.keys() if y in indicator_years]
        
        if len(indicator_matching) >= 2:
            ind_curves = [year_data[y]["full_365"] for y in indicator_matching]
            ind_avg = [np.mean([c[d] for c in ind_curves]) for d in range(365)]
            
            if smoothing_window > 1:
                ind_avg = pd.Series(ind_avg).rolling(
                    smoothing_window, center=True, min_periods=1
                ).mean().tolist()
            
            fig.add_trace(go.Scatter(
                x=x_days, y=ind_avg,
                mode="lines",
                line=dict(color=indicator_color, width=2.5, dash="dashdot"),
                name=f"{indicator_label} ({len(indicator_matching)}y)",
                text=hover_texts,
                hovertemplate=f"{indicator_label}<br>%{{text}}<br>Wert: %{{y:.2f}}<extra></extra>"
            ))
    
    # ── Saisonaler Durchschnitt (Hauptlinie) ──────────
    if avg:
        avg_display = avg.copy()
        
        if smoothing_window > 1:
            avg_display = pd.Series(avg_display).rolling(
                smoothing_window, center=True, min_periods=1
            ).mean().tolist()
        
        fig.add_trace(go.Scatter(
            x=x_days, y=avg_display,
            mode="lines",
            line=dict(color=COLOR_SEASONAL_AVG, width=3.5),
            name=f"Saisonaler Ø ({len(year_data)} Jahre)",
            text=hover_texts,
            hovertemplate="%{text}<br>Wert: %{y:.2f}<extra></extra>"
        ))
    
    # ── War-Verlauf (Durchschnitt Kriegsjahre) ────────
    if war_years_data and war_label:
        war_matching = [y for y in year_data.keys() if y in war_years_data]
        
        if len(war_matching) >= 2:
            war_curves = [year_data[y]["full_365"] for y in war_matching]
            war_avg = [np.mean([c[d] for c in war_curves]) for d in range(365)]
            
            if smoothing_window > 1:
                war_avg = pd.Series(war_avg).rolling(
                    smoothing_window, center=True, min_periods=1
                ).mean().tolist()
            
            fig.add_trace(go.Scatter(
                x=x_days, y=war_avg,
                mode="lines",
                line=dict(color=COLOR_WAR, width=2.5, dash="dash"),
                name=f"{war_label} ({len(war_matching)}y)",
                text=hover_texts,
                hovertemplate=f"{war_label}<br>%{{text}}<br>Wert: %{{y:.2f}}<extra></extra>"
            ))
    
    # ── Aktuelles Jahr (hervorgehoben) ────────────────
    # Wichtig: Das aktuelle Jahr wird IMMER aus den Rohdaten gebaut,
    # auch wenn es nicht in year_data ist (z.B. weil < 20 Handelstage)
    if show_current_year:
        current_year = datetime.now().year
        if current_year in year_data:
            yd = year_data[current_year]
            today_doy = datetime.now().timetuple().tm_yday
            display_days = [d for d in yd["days"] if d <= today_doy]
            display_vals = yd["cumulative"][:len(display_days)]
            
            if display_days:
                fig.add_trace(go.Scatter(
                    x=display_days, y=display_vals,
                    mode="lines",
                    line=dict(color=COLOR_CURRENT_YEAR, width=2.5),
                    name=f"{current_year} (aktuell)",
                    text=[hover_texts[d-1] if d <= len(hover_texts) else "" for d in display_days],
                    hovertemplate=f"{current_year}<br>%{{text}}<br>Wert: %{{y:.2f}}<extra></extra>"
                ))
    
    # ── Overlay-Linien (Last Year, Last 5Y, Last 10Y) ──
    if overlay_options:
        overlay_configs = {
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
        
        current_year = datetime.now().year
        
        for opt in overlay_options:
            cfg = overlay_configs.get(opt)
            if not cfg:
                continue
            
            n = cfg["years_back"]
            
            if n == 1:
                # Last Year: einzelnes Vorjahr
                target_year = current_year - 1
                if target_year in year_data:
                    fig.add_trace(go.Scatter(
                        x=x_days, y=year_data[target_year]["full_365"],
                        mode="lines",
                        line=dict(color=cfg["color"], width=cfg["width"], dash=cfg["dash"]),
                        name=f"{target_year} (Vorjahr)",
                        text=hover_texts,
                        hovertemplate=f"{target_year}<br>%{{text}}<br>Wert: %{{y:.2f}}<extra></extra>"
                    ))
            else:
                # Last N Years: Durchschnitt
                target_years = [y for y in year_data.keys()
                               if current_year - n <= y < current_year]
                
                if len(target_years) >= 2:
                    overlay_curves = [year_data[y]["full_365"] for y in target_years]
                    overlay_avg = [np.mean([c[d] for c in overlay_curves]) for d in range(365)]
                    
                    if smoothing_window > 1:
                        overlay_avg = pd.Series(overlay_avg).rolling(
                            smoothing_window, center=True, min_periods=1
                        ).mean().tolist()
                    
                    fig.add_trace(go.Scatter(
                        x=x_days, y=overlay_avg,
                        mode="lines",
                        line=dict(color=cfg["color"], width=cfg["width"], dash=cfg["dash"]),
                        name=f"Ø Last {n}Y ({len(target_years)}y)",
                        text=hover_texts,
                        hovertemplate=f"Last {n}Y<br>%{{text}}<br>Wert: %{{y:.2f}}<extra></extra>"
                    ))
    
    # ── "Heute"-Markierung mit Info-Box ───────────────
    today = datetime.now()
    today_doy = today.timetuple().tm_yday  # Kalendertag des Jahres (CDOY)
    
    # TDOY und TDOM aus der gleichen Map wie der Hover
    tdoy = tdoy_map.get(today_doy, "–")
    tdom = tdom_map.get(today_doy, "–")
    
    # Vertikale Linie für heute
    fig.add_vline(
        x=today_doy, line_dash="solid",
        line_color="rgba(255,255,255,0.6)", line_width=1.5
    )
    
    # Info-Box als Annotation
    info_text = (
        f"<b>Heute: {today.strftime('%d.%m.%Y')}</b><br>"
        f"CDOY: {today_doy}<br>"
        f"TDOY: {tdoy}<br>"
        f"TDOM: {tdom}"
    )
    fig.add_annotation(
        x=today_doy, y=1.0, yref="paper",
        text=info_text,
        showarrow=True, arrowhead=0, arrowcolor="rgba(255,255,255,0.4)",
        ax=40, ay=-10,
        bgcolor="rgba(30,30,30,0.85)",
        bordercolor="rgba(255,255,255,0.3)",
        borderwidth=1,
        font=dict(size=10, color="#e0e0e0"),
        align="left"
    )
    
    # ── Layout ────────────────────────────────────────
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=550,
        margin=dict(t=40, r=20, b=50, l=60),
        title=dict(
            text=f"{ticker} — Saisonalität ({len(year_data)} Jahre)",
            font=dict(size=18, color="#e0e0e0")
        ),
        xaxis=dict(
            tickmode="array",
            tickvals=month_starts,
            ticktext=month_names,
            gridcolor="rgba(255,255,255,0.06)",
            range=[1, 365]
        ),
        yaxis=dict(
            title="Normalisierte Rendite (Start = 100)",
            gridcolor="rgba(255,255,255,0.06)",
            tickformat=".1f"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
        hovermode="x unified"
    )
    
    # Y-Achse dynamisch anpassen — berücksichtigt ALLE sichtbaren Traces
    all_y_values = []
    
    # Saisonaler Durchschnitt
    if avg:
        all_y_values.extend(avg)
    
    # Konfidenzband
    if show_bands and std and avg:
        all_y_values.extend([avg[i] + std[i] for i in range(365)])
        all_y_values.extend([avg[i] - std[i] for i in range(365)])
    
    # Einzelne Jahre
    if show_individual:
        for yd in year_data.values():
            all_y_values.extend(yd["full_365"])
    
    # Aktuelles Jahr
    if show_current_year:
        current_year = datetime.now().year
        if current_year in year_data:
            all_y_values.extend(year_data[current_year]["cumulative"])
    
    # Präsidentenzyklus-Linien
    if selected_cycles:
        for cycle_type in selected_cycles:
            matching = [y for y in year_data.keys()
                       if get_presidential_cycle_year(y) == cycle_type]
            if matching:
                curves = [year_data[y]["full_365"] for y in matching]
                cycle_avg = [np.mean([c[d] for c in curves]) for d in range(365)]
                all_y_values.extend(cycle_avg)
    
    # Dekadenzyklus-Linien
    if selected_decades:
        for digit in selected_decades:
            matching = [y for y in year_data.keys()
                       if get_decade_digit(y) == digit]
            if matching:
                curves = [year_data[y]["full_365"] for y in matching]
                decade_avg = [np.mean([c[d] for c in curves]) for d in range(365)]
                all_y_values.extend(decade_avg)
    
    # Indikator-Linie
    if indicator_years and indicator_label:
        ind_matching = [y for y in year_data.keys() if y in indicator_years]
        if len(ind_matching) >= 2:
            ind_curves = [year_data[y]["full_365"] for y in ind_matching]
            ind_avg = [np.mean([c[d] for c in ind_curves]) for d in range(365)]
            all_y_values.extend(ind_avg)
    
    # Overlay-Linien
    if overlay_options:
        current_year = datetime.now().year
        for opt in (overlay_options or []):
            if opt == "Last Year":
                ty = current_year - 1
                if ty in year_data:
                    all_y_values.extend(year_data[ty]["full_365"])
            elif opt == "Last 5 Years":
                tys = [y for y in year_data.keys() if current_year - 5 <= y < current_year]
                if len(tys) >= 2:
                    curves = [year_data[y]["full_365"] for y in tys]
                    all_y_values.extend([np.mean([c[d] for c in curves]) for d in range(365)])
            elif opt == "Last 10 Years":
                tys = [y for y in year_data.keys() if current_year - 10 <= y < current_year]
                if len(tys) >= 2:
                    curves = [year_data[y]["full_365"] for y in tys]
                    all_y_values.extend([np.mean([c[d] for c in curves]) for d in range(365)])
    
    if all_y_values:
        y_min = min(all_y_values) - 2
        y_max = max(all_y_values) + 2
        fig.update_yaxes(range=[y_min, y_max])
    
    return fig

