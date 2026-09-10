"""
SeasonAlpha - Berechnungen
============================
Saisonale Analyse, Pressure Chart, Indikatoren, Kriege, ToM.
"""

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
import pandas as pd
import math
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from shared.constants import (
    PRESSURE_PERIODS, US_WARS, MONTH_NAMES_DE,
    CYCLE_COLORS, DECADE_COLORS
)


# ══════════════════════════════════════════════════════════════
# SEASONAL ANALYSIS
# ══════════════════════════════════════════════════════════════

def get_presidential_cycle_year(year):
    """Bestimme die Position im Präsidentenzyklus."""
    cycle_position = (year - 2024) % 4
    if cycle_position == 0:
        return "Year 4 (Election Year)"
    elif cycle_position == 1 or cycle_position == -3:
        return "Year 1 (Post-Election)"
    elif cycle_position == 2 or cycle_position == -2:
        return "Year 2 (Midterm Election)"
    else:
        return "Year 3 (Pre-Election)"


def get_decade_digit(year):
    """Letzte Ziffer des Jahres: 2025 → 5, 1987 → 7"""
    return year % 10


def normalize_year(year_df):
    """
    Normalisiere ein Jahr auf Startwert 100.

    Konvention: Zeile 0 = 100 (Referenzpunkt), Zeile j trägt den Return VON Zeile j:
        wert_j = 100 · exp(Σ r_1..r_j)

    `log_return` ist rückwärts definiert — `LN(close / prev_close)`, siehe
    `scripts/fix_tdom_trigger_and_log_returns.sql`. Der Wert einer Zeile gehört
    also zu genau dieser Zeile.

    FRÜHER wurde stattdessen Σ r_0..r_{j-1} kumuliert. Das hatte zwei Folgen:
      * Der **Jahreswechsel-Return** (letzter Handelstag des Vorjahres → erster
        dieses Jahres) landete als Bewegung von Tag 1 auf Tag 2 IN diesem Jahr.
        Bei einem Jahresauftakt von +10 % stand Tag 2 bei 110 statt 101.
      * Der Return des **letzten** Handelstags fiel hinten weg.
    Das Frontend (`seasonal-compute.js::buildYearData`) rechnete bereits die hier
    implementierte Variante — die beiden Zwillinge lieferten damit systematisch
    verschiedene Kurven. Gegenprobe: `scripts/verify_seasonal_twins.py`.

    Fehlende/nicht-endliche Returns werden — wie im Frontend — aus den Closes
    nachgerechnet. Das ist kein Schoenreden, sondern verhindert einen weit
    groesseren Schaden: ein einzelnes NaN pflanzt sich ueber `np.exp(cumsum)`
    durch die ganze Jahreskurve fort, und `calculate_seasonal_average` mittelt
    anschliessend ueber alle Jahre — EIN kaputter Kurs machte damit den
    Saison-Durchschnitt ALLER Jahre zu NaN und den Chart leer, waehrend das
    Frontend munter weiterzeichnete. Laesst sich ein Return auch aus den Closes
    nicht rekonstruieren, wird das Jahr mit [] verworfen (build_year_data
    ueberspringt es) statt alle anderen mitzureissen.
    """
    log_returns = np.asarray(year_df["log_return"].values, dtype=float)
    if len(log_returns) == 0:
        return []

    if not np.all(np.isfinite(log_returns[1:])):
        spalte = "Close" if "Close" in year_df.columns else (
            "close" if "close" in year_df.columns else None)
        closes = (np.asarray(year_df[spalte].values, dtype=float)
                  if spalte else None)
        for j in range(1, len(log_returns)):
            if np.isfinite(log_returns[j]):
                continue
            reparierbar = (
                closes is not None
                and j < len(closes)
                and np.isfinite(closes[j]) and np.isfinite(closes[j - 1])
                and closes[j - 1] > 0 and closes[j] > 0
            )
            if reparierbar:
                log_returns[j] = math.log(closes[j] / closes[j - 1])
            else:
                return []          # nicht reparierbar -> Jahr verwerfen

    # Zeile 0 ist der Referenzpunkt (100), ab Zeile 1 kumuliert der EIGENE Return.
    steps = np.concatenate(([0.0], log_returns[1:]))
    return (100.0 * np.exp(np.cumsum(steps))).tolist()


def interpolate_to_365(days, values):
    """Interpoliere auf volle 365 Kalendertage.

    Schaltjahre: der 31.12. ist dort Tag 366 und fiel aus der 365er-Achse heraus —
    die Kurve endete am 30.12., der letzte Handelstag des Jahres fehlte in
    Jahresrendite und Dezember-Statistik. Tag 366 wird deshalb auf Slot 365
    gefaltet: der letzte Slot traegt den Jahresendwert, die Ausrichtung aller
    uebrigen Tage bleibt unveraendert.
    """
    if days and days[-1] > 365:
        days = list(days)
        values = list(values)
        # Alles jenseits von 365 auf 365 ziehen; der spaeteste Wert gewinnt.
        keep = {}
        for d, v in zip(days, values):
            keep[min(d, 365)] = v
        days = sorted(keep)
        values = [keep[d] for d in days]

    full_year = []
    
    for target_day in range(1, 366):
        if target_day in days:
            idx = days.index(target_day)
            full_year.append(values[idx])
        elif target_day < days[0]:
            full_year.append(values[0])
        elif target_day > days[-1]:
            full_year.append(values[-1])
        else:
            prev_days = [d for d in days if d < target_day]
            next_days = [d for d in days if d > target_day]
            
            if prev_days and next_days:
                prev_day = prev_days[-1]
                next_day = next_days[0]
                prev_val = values[days.index(prev_day)]
                next_val = values[days.index(next_day)]
                
                weight = (target_day - prev_day) / (next_day - prev_day)
                interpolated = prev_val + weight * (next_val - prev_val)
                full_year.append(interpolated)
            else:
                full_year.append(values[-1])
    
    return full_year


def last_actual_day(yd) -> int:
    """Letzter Tag eines Jahres mit ECHTER Beobachtung (1..365).

    Hinter diesem Tag ist `full_365` konstant fortgeschrieben — eine flache
    Linie, kein Kursverlauf. Wer daraus Renditen, Drawdowns, Perzentile oder
    Heatmap-Zellen rechnet, zaehlt erfundene Beobachtungen mit: die Volatilitaet
    sinkt, der Drawdown geht gegen null, und das laufende Jahr sieht ruhiger aus
    als es ist.

    Fuer Mittelwert/Std ueber die Jahre ist die Fortschreibung dagegen gewollt
    (sonst bricht die Durchschnittskurve am Jahresende ab) — deshalb filtert
    nicht der Erzeuger, sondern jeder Konsument, der es braucht.
    """
    tage = yd.get("days") or []
    return min(max(tage), 365) if tage else 0


def year_end_reference(year_data) -> int:
    """Wie weit reicht ein VOLLSTAENDIGES Jahr dieses Tickers ueberhaupt?

    Ein abgeschlossenes Jahr endet fast nie am Kalendertag 365: XETRA schliesst
    am 30.12., die NYSE hatte 2006/2017/2023 ihren letzten Handelstag am 29.12.
    Zwischen letztem Handelstag und Silvester ist die Fortschreibung **exakt** —
    es wurde nicht gehandelt, der Kurs hat sich nicht geaendert.

    Diese Referenz kalibriert sich aus den Daten selbst, damit `year_covers`
    ohne Boersenkalender auskommt.
    """
    werte = [last_actual_day(yd) for yd in year_data.values()]
    return max(werte) if werte else 0


def year_covers(yd, end_day: int, ref: int) -> bool:
    """Darf dieses Jahr fuer eine Periode bis `end_day` mitgezaehlt werden?

    Ja, wenn echte Beobachtungen bis zum Periodenende reichen — ODER das Jahr
    bis zu seinem eigenen Jahresende reicht (`ref`), denn dann ueberbrueckt die
    Fortschreibung nur handelsfreie Tage.

    Ein starres `>= 365` warf 7 von 26 NYSE- und 15 von 26 XETRA-Jahren weg
    (gemessen 2000-2025) — das laufende Jahr fiel korrekt raus, aber eben auch
    jedes zweite abgeschlossene XETRA-Jahr.
    """
    lad = last_actual_day(yd)
    return lad >= min(end_day, 365) or lad >= ref


def build_year_data(df, selected_years):
    """Baue normalisierte Jahreskurven für alle gewählten Jahre."""
    year_data = {}
    
    for year in selected_years:
        year_df = df[df["year"] == year].copy()
        
        if len(year_df) < 20:
            continue
        
        cumulative = normalize_year(year_df)
        if not cumulative:            # nicht reparierbare Luecke -> Jahr auslassen
            continue
        days = year_df["day_of_year"].tolist()
        full_365 = interpolate_to_365(days, cumulative)
        
        year_data[year] = {
            "days": days,
            "cumulative": cumulative,
            "full_365": full_365,
            "df": year_df
        }
    
    return year_data


def calculate_seasonal_average(year_data):
    """Berechne den saisonalen Durchschnitt über alle Jahre."""
    if not year_data:
        return [], []
    
    all_curves = [yd["full_365"] for yd in year_data.values()]
    
    avg = []
    std = []
    
    for day_idx in range(365):
        day_values = [curve[day_idx] for curve in all_curves]
        avg.append(np.mean(day_values))
        std.append(np.std(day_values))
    
    return avg, std


def count_trading_days(year_data, start_day, end_day):
    """Zähle die durchschnittliche Anzahl Handelstage im Zeitraum."""
    counts = []
    for yd in year_data.values():
        period_days = [d for d in yd["days"] if start_day <= d <= end_day]
        if period_days:
            counts.append(len(period_days))
    return int(np.mean(counts)) if counts else 0


def calculate_period_stats(year_data, start_day, end_day):
    """Berechne Statistiken für einen gewählten Zeitraum.

    Ein Jahr zählt NUR mit, wenn es bis zum Periodenende echte Beobachtungen hat.

    Warum: `full_365` ist hinter dem letzten Handelstag konstant fortgeschrieben
    (siehe interpolate_to_365). Ohne diese Prüfung ging das laufende, noch
    unfertige Jahr als abgeschlossenes in Trefferquote und Mittelwert ein — sein
    „Periodenende" war dann der fortgeschriebene letzte Kurs, also eine Rendite
    über einen Zeitraum, den es noch gar nicht gab. Im September lieferte der
    September damit eine Beobachtung mehr, als real vorlag.

    Die Prüfung über `days` ist schärfer als ein Ausschluss nur des laufenden
    Jahres (so macht es das Frontend in ki-saisonalitaet.html): sie erwischt auch
    Jahre mit abgeschnittenem Ende, etwa bei Delisting oder Datenlücken.

    ABER: ein abgeschlossenes Jahr endet fast nie am Kalendertag 365. XETRA
    schliesst am 30.12., die NYSE hatte 2006/2017/2023 ihren letzten Handelstag
    am 29.12. Zwischen letztem Handelstag und Silvester ist die Fortschreibung
    **exakt** — es wurde ja nicht gehandelt, der Kurs hat sich nicht geändert.
    Ein starres `< 365` warf deshalb 7 von 26 NYSE- und 15 von 26 XETRA-Jahren
    weg (gemessen 2000-2025). Die Referenz ist daher nicht 365, sondern wie weit
    ein vollständiges Jahr DIESES Tickers überhaupt reicht — selbstkalibrierend,
    ohne den Börsenkalender hier zu kennen.
    """
    period_returns = []

    ref = year_end_reference(year_data)

    for year, yd in year_data.items():
        if not year_covers(yd, end_day, ref):
            continue                      # Periode reicht in die Fortschreibung
        start_val = yd["full_365"][start_day - 1]
        end_val = yd["full_365"][min(end_day - 1, 364)]
        if not start_val:
            continue
        ret = (end_val - start_val) / start_val * 100
        period_returns.append(ret)

    if not period_returns:
        return {}
    
    wins = [r for r in period_returns if r > 0]
    
    return {
        "win_rate": len(wins) / len(period_returns) * 100,
        "avg_return": np.mean(period_returns),
        "median_return": np.median(period_returns),
        "max_gain": max(period_returns),
        "max_loss": min(period_returns),
        "std_dev": np.std(period_returns),
        "total_years": len(period_returns),
        "winning_years": len(wins),
        "losing_years": len(period_returns) - len(wins)
    }


# ══════════════════════════════════════════════════════════════
# PRESSURE CHART
# ══════════════════════════════════════════════════════════════

def calculate_pressure_curve(df, smoothing_window=5):
    """
    Pressure Chart: Addition der Ø-Tagesrenditen verschiedener Lookback-Perioden.
    """
    current_year = datetime.now().year
    all_years = sorted(df["year"].unique())
    max_years_available = current_year - min(all_years)
    
    available_periods = [p for p in PRESSURE_PERIODS if p <= max_years_available]
    
    if not available_periods:
        return None, 0, []
    
    period_daily_avgs = {}
    
    for period in available_periods:
        cutoff_year = current_year - period
        period_years = [y for y in all_years if y >= cutoff_year and y < current_year]
        
        if len(period_years) < 2:
            continue
        
        year_daily_returns = []
        for year in period_years:
            year_df = df[df["year"] == year].copy()
            if len(year_df) < 20:
                continue
            
            days = year_df["day_of_year"].tolist()
            log_rets = year_df["log_return"].values.tolist()
            
            full_rets = []
            for target_day in range(1, 366):
                if target_day in days:
                    idx = days.index(target_day)
                    full_rets.append(log_rets[idx])
                else:
                    full_rets.append(0.0)
            
            year_daily_returns.append(full_rets)
        
        if not year_daily_returns:
            continue
        
        avg_daily = [np.mean([yr[d] for yr in year_daily_returns]) * 100
                     for d in range(365)]
        period_daily_avgs[period] = avg_daily
    
    if not period_daily_avgs:
        return None, max_years_available, []
    
    summed_daily = [0.0] * 365
    for period, avg_daily in period_daily_avgs.items():
        for d in range(365):
            summed_daily[d] += avg_daily[d]
    
    pressure_curve = np.cumsum(summed_daily).tolist()
    
    if smoothing_window > 1:
        pressure_curve = pd.Series(pressure_curve).rolling(
            smoothing_window, center=True, min_periods=1
        ).mean().tolist()
    
    return pressure_curve, max_years_available, list(period_daily_avgs.keys())


# ══════════════════════════════════════════════════════════════
# SAISONALE INDIKATOREN
# ══════════════════════════════════════════════════════════════

def classify_december_low(df):
    """December Low Indikator: Dez-Tief des Vorjahres im Q1 unterschritten?"""
    years = sorted(df["year"].unique())
    classification = {}
    
    for year in years:
        prev_year = year - 1
        dec_prev = df[(df["year"] == prev_year) & (df["month"] == 12)]
        if len(dec_prev) == 0:
            continue
        
        dec_low = dec_prev["Low"].min() if "Low" in df.columns else dec_prev["Close"].min()
        
        q1 = df[(df["year"] == year) & (df["month"].isin([1, 2, 3]))]
        if len(q1) == 0:
            continue
        
        q1_low = q1["Low"].min() if "Low" in df.columns else q1["Close"].min()
        classification[year] = q1_low >= dec_low
    
    return classification


def classify_january_first5(df):
    """Januar Indikator: Erste 5 Handelstage positiv oder negativ?"""
    years = sorted(df["year"].unique())
    classification = {}
    
    for year in years:
        prev_year = year - 1
        prev_year_data = df[df["year"] == prev_year]
        if len(prev_year_data) == 0:
            continue
        
        last_close_prev = prev_year_data["Close"].iloc[-1]
        
        jan_data = df[(df["year"] == year) & (df["month"] == 1)]
        if len(jan_data) < 5:
            continue
        
        close_day5 = jan_data["Close"].iloc[4]
        classification[year] = close_day5 > last_close_prev
    
    return classification


# ══════════════════════════════════════════════════════════════
# KRIEG / FRIEDEN
# ══════════════════════════════════════════════════════════════

def get_war_years():
    """Alle Jahre in denen die USA in mindestens einem Krieg waren."""
    war_years = set()
    for war in US_WARS:
        for y in range(war["start"], war["end"] + 1):
            war_years.add(y)
    return war_years


def get_peace_years(all_years):
    """Alle Jahre in denen die USA NICHT im Krieg waren."""
    war_years = get_war_years()
    return [y for y in all_years if y not in war_years]


# ══════════════════════════════════════════════════════════════
# TURN OF THE MONTH (ToM) ANALYSE
# ══════════════════════════════════════════════════════════════

def analyze_turn_of_month(df, days_before, days_after, selected_months, selected_years):
    """
    Turn-of-the-Month: t0 = letzter Handelstag des Monats → 0% normiert.
    """
    window_size = days_before + 1 + days_after
    t0_idx = days_before
    all_curves = []
    
    for year in selected_years:
        for month in selected_months:
            try:
                month_data = df[(df["year"] == year) & (df["month"] == month)].copy()
                
                if len(month_data) < days_before + 1:
                    continue
                
                pre_window = month_data.iloc[-(days_before + 1):]
                
                next_month = month + 1 if month < 12 else 1
                next_year = year if month < 12 else year + 1
                
                next_month_data = df[(df["year"] == next_year) & (df["month"] == next_month)].copy()
                
                if len(next_month_data) < days_after:
                    continue
                
                post_window = next_month_data.iloc[:days_after]
                
                tom_window = pd.concat([pre_window, post_window])
                
                if len(tom_window) != window_size:
                    continue
                
                log_rets = tom_window["log_return"].values
                # Ohne Verschiebung kumulieren: log_rets[j] ist der Return VON
                # Zeile j (LN(close/prev_close)). Die frueher genutzte Variante
                # cumsum(insert(log_rets,0,0)[:-1]) ordnete jeden Tagesschritt der
                # FOLGENDEN Zeile zu — im Chart erschien die Bewegung damit einen
                # Handelstag zu spaet (t+1 zeigte, was an t+2 stand). Nachweis:
                # ein isolierter +5%-Tag lag eine Position daneben.
                cum_log = np.cumsum(log_rets)
                raw_curve = 100 * np.exp(cum_log)
                
                t0_value = raw_curve[t0_idx]
                curve = ((raw_curve / t0_value - 1) * 100).tolist()
                
                total_return = curve[-1] - curve[0]
                
                all_curves.append({
                    "year": year,
                    "month": month,
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


def build_tom_chart(tom_result, ticker, days_before, days_after, selected_months,
                    show_individual_tom=False):
    """Erstelle den Turn-of-the-Month Chart (t0 = 0%)."""
    
    fig = go.Figure()
    
    labels = tom_result["labels"]
    avg_curve = tom_result["avg_curve"]
    x_indices = list(range(len(labels)))
    
    if show_individual_tom:
        for entry in tom_result["all_curves"]:
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
        annotation_text="t0 (letzter HT)",
        annotation_position="top",
        annotation_font=dict(size=10, color="#FFD700")
    )
    
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)", line_width=1)
    
    fig.add_trace(go.Scatter(
        x=x_indices, y=avg_curve,
        mode="lines+markers",
        line=dict(color="#00CED1", width=3),
        marker=dict(size=6, color="#00CED1"),
        fill="tozeroy", fillcolor="rgba(0,206,209,0.1)",
        name=f"Ø ToM ({tom_result['stats']['total_windows']} Fenster)",
        hovertemplate="%{text}<br>%{y:+.3f}%<extra></extra>",
        text=labels
    ))
    
    if len(selected_months) <= 3:
        month_str = ", ".join([MONTH_NAMES_DE[m - 1] for m in selected_months])
    elif len(selected_months) == 12:
        month_str = "Alle Monate"
    else:
        month_str = f"{len(selected_months)} Monate"
    
    from shared.charts import apply_se_theme
    fig = apply_se_theme(
        fig,
        title=f"{ticker} — Turn of the Month (t-{days_before} bis t+{days_after}) · {month_str}",
        height=420,
    )
    fig.update_xaxes(tickmode="array", tickvals=x_indices, ticktext=labels, title="Handelstage relativ zum Monatswechsel")
    fig.update_yaxes(title="Rendite relativ zu t0 (%)", tickformat="+.2f", ticksuffix="%")
    
    return fig
