# Seasonal Trading Tool - Development Skill

## Overview
This skill contains best practices, patterns, and domain knowledge for developing and maintaining the SeasonalEdge trading tool - a Streamlit-based seasonal pattern analyzer for financial instruments.

---

## Core Methodology

### Calculation Method: NORMALIZED RETURNS (Not Price Deltas)

**Critical Decision:**
We use **percentage returns normalized to 100** - NOT absolute price changes like TradingView.

**Why:**
- ✅ Comparable across different price levels (SPY $200 vs $600)
- ✅ No detrending needed (each year starts at 100)
- ✅ Intuitive for retail traders (direct % gain visible)
- ✅ Works across decades without bias

**Code Pattern:**
```python
# CORRECT - Our Method:
for year in available_years:
    cumulative = []
    cum_return = 0
    
    for i in range(len(year_df)):
        if i == 0:
            cumulative.append(100)  # Always start at 100
        else:
            daily_ret = year_df.iloc[i]["return"]
            cum_return += daily_ret * 100
            cumulative.append(100 + cum_return)
    
    year_data[year] = cumulative

# Then average normalized curves:
avg = np.mean([year_data[y][day] for y in years])
```

**AVOID:**
```python
# WRONG - TradingView Method (Price Deltas):
priceChange = close - close[lookback]  # Absolute $
seasonal += priceChange  # Needs detrending!
```

---

## Data Structure Standards

### Year Data Storage
```python
year_data_stacked = {
    2024: {
        "days": [1, 2, 3, ..., 365],      # Day of year
        "cumulative": [100, 100.5, ...],  # Normalized returns
        "df": year_df                      # Original dataframe
    },
    2023: {...},
    ...
}
```

### Interpolation for Missing Days
```python
# Always interpolate to full 365-day calendar:
for target_day in range(1, 366):
    if target_day in year_days:
        value = year_cum[year_days.index(target_day)]
    else:
        # Linear interpolation between nearest days
        prev_day = max([d for d in year_days if d < target_day])
        next_day = min([d for d in year_days if d > target_day])
        weight = (target_day - prev_day) / (next_day - prev_day)
        value = interpolate(prev_val, next_val, weight)
    
    full_year_cum.append(value)
```

---

## Feature Implementation Patterns

### 1. Smoothing (Moving Average)
```python
# Apply AFTER averaging all years:
smoothing_window = 5
avg_smooth = pd.Series(avg_cumulative).rolling(
    smoothing_window, 
    center=True,      # Symmetric
    min_periods=1     # Handle edges
).mean().tolist()
```

### 2. Confidence Bands (Standard Deviation)
```python
# Calculate per day:
std_cumulative = []
for day_idx in range(365):
    day_values = [year[day_idx] for year in normalized_years]
    std_cumulative.append(np.std(day_values))

# Bands:
upper = [avg[i] + std[i] for i in range(365)]
lower = [avg[i] - std[i] for i in range(365)]
```

### 3. Future Projection
```python
# Repeat pattern into future:
future_days = 60
future_projection = avg_cumulative[:future_days]  # First 60 days
future_x = list(range(366, 366 + future_days))

# Plot with dash:
fig.add_trace(go.Scatter(
    x=future_x,
    y=future_projection,
    line=dict(dash="dash", color="orange")
))
```

### 4. Presidential Cycle Filter
```python
def get_presidential_cycle_year(year):
    """2024 = Election, 2025 = Post-Election, etc."""
    cycle_position = (year - 2024) % 4
    
    if cycle_position == 0:
        return "Year 4 (Election Year)"
    elif cycle_position == 1 or cycle_position == -3:
        return "Year 1 (Post-Election)"
    elif cycle_position == 2 or cycle_position == -2:
        return "Year 2 (Midterm Election)"
    else:
        return "Year 3 (Pre-Election)"

# Calculate separate average for each cycle type:
for cycle_type in selected_cycles:
    matching_years = [y for y in all_years 
                      if get_cycle_year(y) == cycle_type]
    cycle_avg = average_normalized_years(matching_years)
    plot_cycle_average(cycle_avg, color=cycle_colors[cycle_type])
```

---

## Trading Days Calculation

**CRITICAL:** Count actual trading days, not calendar days.

```python
def count_trading_days(start_day, end_day):
    """Count average trading days across all years"""
    trading_days_per_year = []
    
    for year in available_years:
        year_df = year_data_stacked[year]["df"]
        period_df = year_df[
            (year_df["day_of_year"] >= start_day) & 
            (year_df["day_of_year"] <= end_day)
        ]
        if len(period_df) > 0:
            trading_days_per_year.append(len(period_df))
    
    return int(np.mean(trading_days_per_year)) if trading_days_per_year else 0
```

**Display:**
```python
period_str = f"{start} to {end} | {cal_days} Calendar Days | ~{td_days} Trading Days"
```

---

## Trading Day of Month (TDoM) System

### Concept

The **Trading Day of Month (TDoM)** counts only days the exchange is open within each calendar month. Weekends and holidays are excluded. A typical month has 20-23 trading days.

**Forward counting:** TDoM 1 = first trading day, TDoM 2 = second, etc.  
**Backward counting:** TDoM -1 = last trading day, TDoM -2 = second-to-last, etc.

**Why TDoM matters:**
- Pension fund rebalancing clusters around TDoM 1 and TDoM -1
- Options expiration effects are TDoM-based, not calendar-based
- Month-end window dressing by fund managers
- Payroll-driven inflows at specific TDoMs

### TDoM Assignment Algorithm

```python
def assign_tdom(df):
    """
    Assign forward and backward Trading Day of Month to each row.
    
    Args:
        df: DataFrame with DatetimeIndex, containing only trading days
             (weekends/holidays already excluded by yfinance)
    
    Returns:
        df with columns 'tdom' (forward) and 'tdom_reverse' (backward)
    """
    df = df.copy()
    df["year"] = df.index.year
    df["month"] = df.index.month
    
    # Forward: count from start of month
    df["tdom"] = df.groupby(["year", "month"]).cumcount() + 1
    
    # Backward: count from end of month (TDoM -1 = last day)
    # Use negative numbers: -1, -2, -3, ...
    def reverse_count(group):
        n = len(group)
        group["tdom_reverse"] = list(range(-n, 0))  # [-n, ..., -2, -1]
        return group
    
    df = df.groupby(["year", "month"], group_keys=False).apply(reverse_count)
    
    return df
```

**Example output for January 2024:**
```
Date        | Open   | Close  | tdom | tdom_reverse
2024-01-02  | 472.65 | 469.58 |  1   |  -21
2024-01-03  | 468.39 | 467.77 |  2   |  -20
...
2024-01-30  | 487.57 | 487.41 | 20   |  -2
2024-01-31  | 487.60 | 482.88 | 21   |  -1
```

### Edge Cases

**Variable month lengths:**
```python
# Months have 19-23 trading days depending on holidays.
# When averaging across years, TDoM 22 and 23 will have fewer data points.
# ALWAYS track sample size per TDoM:

tdom_counts = df.groupby("tdom").size()
# TDoM 1:  n=240 (all months have at least 19 trading days)
# TDoM 22: n=87  (only months with 22+ trading days)
# TDoM 23: n=12  (rare, only months with 23 trading days)

# Display sample size in output so user knows confidence level.
```

**Mapping forward ↔ backward:**
```python
def tdom_forward_to_reverse(tdom_forward, total_days_in_month):
    """Convert TDoM 1 → TDoM -21 (if month has 21 trading days)"""
    return tdom_forward - total_days_in_month - 1

def tdom_reverse_to_forward(tdom_reverse, total_days_in_month):
    """Convert TDoM -1 → TDoM 21 (if month has 21 trading days)"""
    return total_days_in_month + tdom_reverse + 1
```

---

## TDoM Strategy Variants

### Three Entry/Exit Modes

Each TDoM can be traded with three different holding strategies:

**Strategy A: Intraday (Open → Close)**
Buy at the open, sell at the close of the SAME day.
```python
def calc_return_open_to_close(row):
    """Intraday return for a single trading day."""
    return (row["Close"] - row["Open"]) / row["Open"]
```

**Strategy B: Overnight-inclusive (Open → Next Open)**
Buy at the open, sell at the next day's open.
```python
def calc_return_open_to_next_open(df, idx):
    """Return from this open to next trading day's open."""
    if idx + 1 >= len(df):
        return np.nan  # No next day available
    return (df.iloc[idx + 1]["Open"] - df.iloc[idx]["Open"]) / df.iloc[idx]["Open"]
```

**Strategy C: Close-to-Close (Close → Next Close)**
Buy at the close, sell at the next day's close.
```python
def calc_return_close_to_next_close(df, idx):
    """Return from this close to next trading day's close."""
    if idx + 1 >= len(df):
        return np.nan
    return (df.iloc[idx + 1]["Close"] - df.iloc[idx]["Close"]) / df.iloc[idx]["Close"]
```

### Multi-Day TDoM Ranges

Allow user to define entry and exit TDoMs, e.g., "Buy TDoM 1, sell TDoM 5":

```python
def calc_tdom_range_return(df, entry_tdom, exit_tdom, entry_price="Open", exit_price="Close"):
    """
    Calculate return for holding from entry_tdom to exit_tdom.
    
    Args:
        df: DataFrame with tdom and tdom_reverse columns
        entry_tdom: int, positive for forward (1,2,3...) or negative for backward (-1,-2,...)
        exit_tdom: int, same convention
        entry_price: "Open" or "Close" - price used to enter
        exit_price: "Open" or "Close" - price used to exit
    
    Returns:
        List of (year, month, return_pct, entry_date, exit_date) tuples
    """
    results = []
    tdom_col = "tdom" if entry_tdom > 0 else "tdom_reverse"
    exit_tdom_col = "tdom" if exit_tdom > 0 else "tdom_reverse"
    
    for (year, month), group in df.groupby(["year", "month"]):
        entry_rows = group[group[tdom_col] == entry_tdom]
        exit_rows = group[group[exit_tdom_col] == exit_tdom]
        
        if len(entry_rows) == 0 or len(exit_rows) == 0:
            continue  # Skip months where TDoM doesn't exist
        
        entry_row = entry_rows.iloc[0]
        exit_row = exit_rows.iloc[0]
        
        # Ensure exit is after entry
        if exit_row.name <= entry_row.name:
            continue
        
        p_entry = entry_row[entry_price]
        p_exit = exit_row[exit_price]
        ret = (p_exit - p_entry) / p_entry * 100
        
        results.append({
            "year": year,
            "month": month,
            "return_pct": ret,
            "entry_date": entry_row.name,
            "exit_date": exit_row.name,
            "entry_price": p_entry,
            "exit_price": p_exit,
            "holding_days": len(group.loc[entry_row.name:exit_row.name])
        })
    
    return pd.DataFrame(results)
```

### TDoM Analysis Output

**Heatmap: Average return per TDoM (all three strategies)**
```python
def build_tdom_heatmap(df, strategy="open_to_close"):
    """
    Build a heatmap showing avg return per TDoM across all months/years.
    
    Returns DataFrame with:
        Rows: TDoM (1-23 forward, or -1 to -23 backward)
        Columns: avg_return, win_rate, count, std_dev
    """
    if strategy == "open_to_close":
        df["strat_return"] = (df["Close"] - df["Open"]) / df["Open"] * 100
    elif strategy == "open_to_next_open":
        df["strat_return"] = df["Open"].shift(-1) / df["Open"] * 100 - 100
    elif strategy == "close_to_next_close":
        df["strat_return"] = df["Close"].shift(-1) / df["Close"] * 100 - 100
    
    stats = df.groupby("tdom").agg(
        avg_return=("strat_return", "mean"),
        win_rate=("strat_return", lambda x: (x > 0).mean() * 100),
        count=("strat_return", "count"),
        std_dev=("strat_return", "std"),
        median_return=("strat_return", "median"),
        max_return=("strat_return", "max"),
        min_return=("strat_return", "min")
    ).round(4)
    
    return stats
```

**TDoM Bar Chart:**
```python
# Color bars green (positive avg) or red (negative avg)
colors = ["#4CAF50" if r > 0 else "#F44336" for r in tdom_stats["avg_return"]]

fig = go.Figure(go.Bar(
    x=tdom_stats.index,
    y=tdom_stats["avg_return"],
    marker_color=colors,
    text=[f"{r:.3f}%" for r in tdom_stats["avg_return"]],
    textposition="outside"
))

fig.update_layout(
    title=f"Average Return by Trading Day of Month – {ticker}",
    xaxis_title="Trading Day of Month",
    yaxis_title="Avg Return (%)",
    template="plotly_dark"
)
```

---

## Backtesting Engine

### Architecture Overview

The backtesting engine simulates historical trades based on TDoM rules and calculates performance metrics comparable to TradingView's strategy tester.

```python
@dataclass
class BacktestConfig:
    """Configuration for a TDoM backtest."""
    # Entry/Exit
    entry_tdom: int              # e.g., 1 or -3 (positive=forward, negative=backward)
    exit_tdom: int               # e.g., 5 or -1
    entry_price: str = "Open"    # "Open" or "Close"
    exit_price: str = "Close"    # "Open" or "Close"
    direction: str = "long"      # "long" or "short"
    
    # Position Sizing
    instrument_type: str = "etf"  # "etf", "futures", "crypto"
    quantity: float = 100         # Shares (ETF/stock) or contracts (futures)
    contract_multiplier: float = 1.0  # Futures: ES=50, NQ=20, CL=1000
    tick_size: float = 0.01      # Minimum price increment
    tick_value: float = 0.01     # Dollar value per tick (for futures)
    
    # Risk Management
    stop_loss_type: str = "none"  # "none", "fixed_pct", "trailing", "atr", "breakeven"
    stop_loss_value: float = 0.0  # Percentage or ATR multiplier
    atr_period: int = 14          # For ATR-based stops
    breakeven_trigger_pct: float = 0.5  # Move stop to breakeven after X% profit
    
    # Time Stop
    use_time_stop: bool = False
    time_stop_bars: int = 5       # Max TRADING days to hold (not calendar days)
    time_stop_exit_price: str = "Close"  # Exit at "Open" or "Close" of the stop bar
    
    # Costs
    commission_per_trade: float = 0.0   # Per trade (entry OR exit)
    slippage_per_trade: float = 0.0     # Per trade in currency
    
    # Filters
    start_year: int = 2000
    end_year: int = 2026
    months_filter: list = None   # None = all months, or [1,2,3] for Jan-Mar only
    lookback_years: int = None   # None = use start/end_year, or 5/10/15/20
    presidential_cycle_filter: list = None  # None = all, or [1,3] for Post-Election + Pre-Election
    
    # Trend Filter (SMA)
    use_trend_filter: bool = False
    trend_sma_period: int = 200       # SMA period (e.g., 50, 100, 200)
    trend_condition: str = "above"    # "above" or "below" - price vs SMA
    
    # Overbought/Oversold Filter (RSI)
    use_rsi_filter: bool = False
    rsi_period: int = 14              # RSI lookback period
    rsi_threshold: float = 30.0       # Threshold value (0-100)
    rsi_condition: str = "below"      # "below" = oversold buy, "above" = overbought buy
    
    # Combined Filter Mode
    filter_combine_mode: str = "and"  # "and" = both must pass, "or" = either passes
```

### Instrument-Specific Configuration

```python
INSTRUMENT_PRESETS = {
    "etf": {
        "contract_multiplier": 1.0,
        "tick_size": 0.01,
        "tick_value": 0.01,
        "default_quantity": 100,  # shares
        "commission_default": 0.0,  # Most brokers: $0 for ETFs
        "description": "Shares (1:1 price exposure)"
    },
    "stock": {
        "contract_multiplier": 1.0,
        "tick_size": 0.01,
        "tick_value": 0.01,
        "default_quantity": 100,
        "commission_default": 0.0,
        "description": "Shares (1:1 price exposure)"
    },
    "futures_es": {
        "contract_multiplier": 50.0,   # $50 per point
        "tick_size": 0.25,
        "tick_value": 12.50,            # $12.50 per tick
        "default_quantity": 1,          # contracts
        "commission_default": 2.25,     # Per contract per side
        "description": "E-mini S&P 500 ($50/point)"
    },
    "futures_nq": {
        "contract_multiplier": 20.0,
        "tick_size": 0.25,
        "tick_value": 5.0,
        "default_quantity": 1,
        "commission_default": 2.25,
        "description": "E-mini Nasdaq-100 ($20/point)"
    },
    "futures_cl": {
        "contract_multiplier": 1000.0,
        "tick_size": 0.01,
        "tick_value": 10.0,
        "default_quantity": 1,
        "commission_default": 2.25,
        "description": "Crude Oil ($1000/point)"
    },
    "futures_mes": {
        "contract_multiplier": 5.0,
        "tick_size": 0.25,
        "tick_value": 1.25,
        "default_quantity": 1,
        "commission_default": 0.62,
        "description": "Micro E-mini S&P 500 ($5/point)"
    },
    "futures_mnq": {
        "contract_multiplier": 2.0,
        "tick_size": 0.25,
        "tick_value": 0.50,
        "default_quantity": 1,
        "commission_default": 0.62,
        "description": "Micro E-mini Nasdaq-100 ($2/point)"
    },
    "crypto": {
        "contract_multiplier": 1.0,
        "tick_size": 0.01,
        "tick_value": 0.01,
        "default_quantity": 1.0,        # Units (e.g., 1 BTC, 10 ETH)
        "commission_default": 0.0,      # Varies by exchange
        "description": "Crypto spot (1:1 exposure)"
    }
}
```

### Trade Filters

**CRITICAL:** Filters are evaluated on the **entry day** — if the filter condition is not met on the day the trade would be entered, the trade is **skipped entirely** for that month.

#### Lookback Period (Rolling Window)

```python
def apply_lookback_filter(config):
    """Convert lookback_years to start_year/end_year."""
    if config.lookback_years is not None:
        current_year = datetime.now().year
        config.start_year = current_year - config.lookback_years
        config.end_year = current_year
    return config
```

#### Month Filter

```python
# Single month or multi-select:
# months_filter = None        → all months
# months_filter = [1]         → January only
# months_filter = [1, 2, 3]   → Jan + Feb + Mar
# months_filter = [10, 11, 12] → Q4 only

# Applied in backtest loop:
if config.months_filter and month not in config.months_filter:
    continue  # Skip this month
```

#### Presidential Cycle Filter

```python
def get_presidential_cycle_year_number(year):
    """
    Returns 1-4 based on presidential cycle position.
    Year 1 = Post-Election, Year 2 = Midterm, Year 3 = Pre-Election, Year 4 = Election
    """
    cycle_position = (year - 2024) % 4
    if cycle_position == 0:
        return 4  # Election Year (2024, 2028, ...)
    elif cycle_position == 1 or cycle_position == -3:
        return 1  # Post-Election (2025, 2029, ...)
    elif cycle_position == 2 or cycle_position == -2:
        return 2  # Midterm (2026, 2030, ...)
    else:
        return 3  # Pre-Election (2027, 2031, ...)

CYCLE_LABELS = {
    1: "Year 1 (Post-Election)",
    2: "Year 2 (Midterm Election)",
    3: "Year 3 (Pre-Election)",
    4: "Year 4 (Election Year)"
}

# Applied in backtest loop:
if config.presidential_cycle_filter:
    cycle_year = get_presidential_cycle_year_number(year)
    if cycle_year not in config.presidential_cycle_filter:
        continue  # Skip this year
```

#### SMA Trend Filter

```python
def calculate_sma(df, period):
    """Calculate Simple Moving Average on Close prices."""
    df["sma"] = df["Close"].rolling(window=period, min_periods=period).mean()
    return df

def check_trend_filter(df, entry_date, config):
    """
    Check if price is above/below SMA on entry day.
    
    Args:
        df: DataFrame with 'sma' column already calculated
        entry_date: DatetimeIndex of entry bar
        config: BacktestConfig
    
    Returns:
        bool: True if filter passes (trade allowed)
    """
    if not config.use_trend_filter:
        return True  # No filter = always pass
    
    row = df.loc[entry_date]
    
    if pd.isna(row["sma"]):
        return False  # Not enough data for SMA yet
    
    if config.trend_condition == "above":
        return row["Close"] > row["sma"]
    elif config.trend_condition == "below":
        return row["Close"] < row["sma"]
    
    return True
```

**Use cases:**
- `trend_condition = "above"` + Long: Classic trend-following (buy when uptrend)
- `trend_condition = "below"` + Long: Mean-reversion (buy when price is depressed)
- `trend_condition = "below"` + Short: Trend-following short (sell when downtrend)
- `trend_condition = "above"` + Short: Mean-reversion short (sell when overbought)

#### RSI Overbought/Oversold Filter

```python
def calculate_rsi(df, period=14):
    """
    Calculate RSI (Relative Strength Index) on Close prices.
    Uses standard Wilder smoothing (exponential).
    """
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    # Wilder smoothing (equivalent to EMA with alpha=1/period)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    df["rsi"] = 100 - (100 / (1 + rs))
    
    return df

def check_rsi_filter(df, entry_date, config):
    """
    Check if RSI is above/below threshold on entry day.
    
    Returns:
        bool: True if filter passes (trade allowed)
    """
    if not config.use_rsi_filter:
        return True
    
    row = df.loc[entry_date]
    
    if pd.isna(row["rsi"]):
        return False  # Not enough data for RSI yet
    
    if config.rsi_condition == "below":
        return row["rsi"] < config.rsi_threshold
    elif config.rsi_condition == "above":
        return row["rsi"] > config.rsi_threshold
    
    return True
```

**Typical setups:**
- Long entry + RSI below 30: Buy oversold dips
- Long entry + RSI below 50: Buy when not overbought
- Short entry + RSI above 70: Sell overbought peaks
- Short entry + RSI above 50: Sell when not oversold

#### Combined Filter Logic

```python
def check_all_filters(df, entry_date, config):
    """
    Evaluate all active filters on the entry day.
    
    Combines trend (SMA) and momentum (RSI) filters using AND/OR logic.
    
    Returns:
        (passes: bool, filter_details: dict)
    """
    results = {}
    
    # Trend filter
    if config.use_trend_filter:
        results["trend"] = check_trend_filter(df, entry_date, config)
    
    # RSI filter
    if config.use_rsi_filter:
        results["rsi"] = check_rsi_filter(df, entry_date, config)
    
    # No filters active → always pass
    if not results:
        return True, {"no_filters": True}
    
    # Combine
    if config.filter_combine_mode == "and":
        passes = all(results.values())
    elif config.filter_combine_mode == "or":
        passes = any(results.values())
    else:
        passes = all(results.values())
    
    return passes, results
```

**Example combinations:**
```python
# "Buy TDoM 1 only when price is above 200-SMA AND RSI is below 30"
# → Uptrend + oversold dip = high-probability mean-reversion entry
config = BacktestConfig(
    entry_tdom=1,
    exit_tdom=5,
    use_trend_filter=True,
    trend_sma_period=200,
    trend_condition="above",
    use_rsi_filter=True,
    rsi_period=14,
    rsi_threshold=30,
    rsi_condition="below",
    filter_combine_mode="and"
)

# "Buy TDoM -1 when price is below 50-SMA OR RSI below 20"
# → Aggressive dip-buying at month-end
config = BacktestConfig(
    entry_tdom=-1,
    exit_tdom=-1,  # Same day (intraday)
    use_trend_filter=True,
    trend_sma_period=50,
    trend_condition="below",
    use_rsi_filter=True,
    rsi_period=14,
    rsi_threshold=20,
    rsi_condition="below",
    filter_combine_mode="or"
)
```

#### Integrating Filters into Backtest Loop

```python
def run_backtest(df, config):
    """Extended backtest loop with filter integration."""
    
    # ── Pre-calculate indicators ──────────────────────
    config = apply_lookback_filter(config)
    
    if config.use_trend_filter:
        df = calculate_sma(df, config.trend_sma_period)
    
    if config.use_rsi_filter:
        df = calculate_rsi(df, config.rsi_period)
    
    df = assign_tdom(df)
    trades = []
    skipped_trades = []  # Track filtered-out trades for analysis
    equity = [0.0]
    
    for (year, month), group in df.groupby(["year", "month"]):
        # ── Apply basic filters ───────────────────────
        if config.months_filter and month not in config.months_filter:
            continue
        
        if year < config.start_year or year > config.end_year:
            continue
        
        if config.presidential_cycle_filter:
            cycle_year = get_presidential_cycle_year_number(year)
            if cycle_year not in config.presidential_cycle_filter:
                continue
        
        # ── Find entry day ────────────────────────────
        tdom_col = "tdom" if config.entry_tdom > 0 else "tdom_reverse"
        entry_mask = group[tdom_col] == config.entry_tdom
        if entry_mask.sum() == 0:
            continue
        
        entry_idx = group[entry_mask].index[0]
        
        # ── Apply technical filters on entry day ──────
        passes, filter_details = check_all_filters(df, entry_idx, config)
        
        if not passes:
            skipped_trades.append({
                "date": entry_idx,
                "year": year,
                "month": month,
                "reason": filter_details
            })
            continue  # Skip this trade
        
        # ── Execute trade (same as before) ────────────
        entry_price = group.loc[entry_idx, config.entry_price]
        # ... rest of trade execution logic ...
    
    return BacktestResult(
        trades=trades, 
        equity_curve=equity, 
        config=config,
        skipped_trades=skipped_trades  # Include for filter analysis
    )
```

#### Filter Analysis Output

```python
def display_filter_analysis(trades, skipped_trades, config):
    """Show how filters affected trade selection."""
    total_opportunities = len(trades) + len(skipped_trades)
    
    st.markdown(f"""
    **Filter Impact:**
    - Total trade opportunities: {total_opportunities}
    - Trades taken: {len(trades)} ({len(trades)/total_opportunities*100:.1f}%)
    - Trades filtered out: {len(skipped_trades)} ({len(skipped_trades)/total_opportunities*100:.1f}%)
    """)
    
    if skipped_trades:
        skip_df = pd.DataFrame(skipped_trades)
        
        # Show which filter blocked the most trades
        if config.use_trend_filter and config.use_rsi_filter:
            trend_blocked = sum(1 for s in skipped_trades 
                              if not s["reason"].get("trend", True))
            rsi_blocked = sum(1 for s in skipped_trades 
                            if not s["reason"].get("rsi", True))
            
            st.markdown(f"""
            - Blocked by SMA filter: {trend_blocked}
            - Blocked by RSI filter: {rsi_blocked}
            """)
```

### Stop-Loss Implementation

**CRITICAL:** Stop-losses are checked against intraday High/Low, not just Close.

```python
def check_stop_loss(trade, daily_bar, config):
    """
    Check if stop-loss was triggered during this bar.
    
    Args:
        trade: dict with 'entry_price', 'stop_price', 'direction'
        daily_bar: row with Open, High, Low, Close
        config: BacktestConfig
    
    Returns:
        (triggered: bool, exit_price: float)
    """
    if config.stop_loss_type == "none":
        return False, None
    
    stop_price = trade["stop_price"]
    
    if config.direction == "long":
        # Long: stop triggers if Low <= stop_price
        if daily_bar["Low"] <= stop_price:
            # Assume fill at stop price (or worse = low if gap down)
            exit_price = min(stop_price, daily_bar["Open"])
            # If opened below stop → gapped through, fill at open
            if daily_bar["Open"] <= stop_price:
                exit_price = daily_bar["Open"]
            return True, exit_price
    
    elif config.direction == "short":
        # Short: stop triggers if High >= stop_price
        if daily_bar["High"] >= stop_price:
            exit_price = max(stop_price, daily_bar["Open"])
            if daily_bar["Open"] >= stop_price:
                exit_price = daily_bar["Open"]
            return True, exit_price
    
    return False, None


def update_trailing_stop(trade, daily_bar, config):
    """Update trailing stop based on favorable price movement."""
    if config.stop_loss_type != "trailing":
        return trade["stop_price"]
    
    if config.direction == "long":
        highest = max(trade.get("highest_price", trade["entry_price"]), daily_bar["High"])
        trade["highest_price"] = highest
        new_stop = highest * (1 - config.stop_loss_value / 100)
        return max(trade["stop_price"], new_stop)  # Only moves up
    
    elif config.direction == "short":
        lowest = min(trade.get("lowest_price", trade["entry_price"]), daily_bar["Low"])
        trade["lowest_price"] = lowest
        new_stop = lowest * (1 + config.stop_loss_value / 100)
        return min(trade["stop_price"], new_stop)  # Only moves down


def update_breakeven_stop(trade, daily_bar, config):
    """Move stop to breakeven after reaching trigger profit."""
    if config.stop_loss_type != "breakeven":
        return trade["stop_price"]
    
    trigger_price = trade["entry_price"] * (1 + config.breakeven_trigger_pct / 100)
    
    if config.direction == "long" and daily_bar["High"] >= trigger_price:
        return max(trade["stop_price"], trade["entry_price"])  # Move to breakeven
    elif config.direction == "short" and daily_bar["Low"] <= trigger_price:
        return min(trade["stop_price"], trade["entry_price"])
    
    return trade["stop_price"]


def calculate_atr_stop(df, idx, config):
    """Calculate stop-loss based on ATR."""
    if idx < config.atr_period:
        return None  # Not enough data for ATR
    
    # ATR calculation
    lookback = df.iloc[max(0, idx - config.atr_period):idx]
    tr = pd.DataFrame({
        "hl": lookback["High"] - lookback["Low"],
        "hc": abs(lookback["High"] - lookback["Close"].shift(1)),
        "lc": abs(lookback["Low"] - lookback["Close"].shift(1))
    }).max(axis=1)
    atr = tr.mean()
    
    entry_price = df.iloc[idx][config.entry_price]
    
    if config.direction == "long":
        return entry_price - (atr * config.stop_loss_value)
    else:
        return entry_price + (atr * config.stop_loss_value)
```

### Time Stop (Trading Day Limit)

**CRITICAL:** Time stop counts TRADING days only, not calendar days. Weekends and holidays are excluded.

The time stop is independent from the TDoM exit and the price-based stop-loss. Whichever exit condition triggers first wins:
1. TDoM exit target reached → exit at target
2. Price stop-loss hit → exit at stop price
3. Time stop reached → exit at configured price (Open or Close)

```python
def check_time_stop(trade, current_bar_index, holding_bars, config):
    """
    Check if maximum holding period (in trading days) has been reached.
    
    Args:
        trade: dict with 'entry_bar_index' (position in holding_bars)
        current_bar_index: int, current position in holding_bars iteration
        holding_bars: DataFrame slice from entry onwards
        config: BacktestConfig
    
    Returns:
        (triggered: bool, exit_price: float or None)
    """
    if not config.use_time_stop:
        return False, None
    
    # current_bar_index is 0-based from entry
    # time_stop_bars=5 means: exit on the 5th trading day after entry
    if current_bar_index >= config.time_stop_bars:
        current_bar = holding_bars.iloc[current_bar_index]
        exit_price = current_bar[config.time_stop_exit_price]
        return True, exit_price
    
    return False, None
```

**Integration in backtest loop:**
```python
# Inside the holding period walk-forward:
for i, (bar_date, bar) in enumerate(holding_days.iterrows()):
    if i == 0 and config.entry_price == "Open":
        continue
    
    # 1. Check price-based stop-loss first (intraday trigger)
    if stop_price is not None:
        triggered, stop_exit_price = check_stop_loss(trade, bar, config)
        if triggered:
            trade["exit_date"] = bar_date
            trade["exit_price"] = stop_exit_price
            trade["exit_reason"] = "stop_loss"
            break
    
    # 2. Check time stop (end of bar trigger)
    time_triggered, time_exit_price = check_time_stop(trade, i, holding_days, config)
    if time_triggered:
        trade["exit_date"] = bar_date
        trade["exit_price"] = time_exit_price
        trade["exit_reason"] = "time_stop"
        trade["holding_trading_days"] = i
        break
    
    # 3. Check TDoM exit target
    if bar[exit_tdom_col] == config.exit_tdom and bar_date != entry_idx:
        trade["exit_date"] = bar_date
        trade["exit_price"] = bar[config.exit_price]
        trade["exit_reason"] = "target"
        break
```

**Use cases:**
- `time_stop_bars=1`: Day trade only — if TDoM target not reached same day, exit at close
- `time_stop_bars=3`: Maximum 3 trading days hold — limits weekend/overnight exposure
- `time_stop_bars=5`: Week-long max hold — for weekly rotation strategies
- `time_stop_bars=10`: Two-week limit — prevents trades from dragging through full month

**Combining with other stops:**
```python
# "Buy TDoM 1, target TDoM 5, but max 3 trading days, with 1% stop-loss"
config = BacktestConfig(
    entry_tdom=1,
    exit_tdom=5,
    stop_loss_type="fixed_pct",
    stop_loss_value=1.0,
    use_time_stop=True,
    time_stop_bars=3,
    time_stop_exit_price="Close"
)
# Possible exits: TDoM 5 reached (target), price drops 1% (stop_loss), 
#                 or 3 trading days pass (time_stop)
```

### Core Backtest Loop

```python
def run_backtest(df, config):
    """
    Execute the full TDoM backtest.
    
    Args:
        df: DataFrame with OHLC + tdom + tdom_reverse columns
        config: BacktestConfig
    
    Returns:
        BacktestResult with trades list, equity curve, and metrics
    """
    df = assign_tdom(df)
    trades = []
    equity = [0.0]  # Cumulative P&L in currency
    
    tdom_col = "tdom" if config.entry_tdom > 0 else "tdom_reverse"
    exit_tdom_col = "tdom" if config.exit_tdom > 0 else "tdom_reverse"
    
    for (year, month), group in df.groupby(["year", "month"]):
        # Apply month filter
        if config.months_filter and month not in config.months_filter:
            continue
        
        # Apply year filter
        if year < config.start_year or year > config.end_year:
            continue
        
        # Find entry day
        entry_mask = group[tdom_col] == config.entry_tdom
        if entry_mask.sum() == 0:
            continue
        
        entry_idx = group[entry_mask].index[0]
        entry_price = group.loc[entry_idx, config.entry_price]
        
        # Calculate initial stop-loss
        stop_price = None
        if config.stop_loss_type == "fixed_pct":
            if config.direction == "long":
                stop_price = entry_price * (1 - config.stop_loss_value / 100)
            else:
                stop_price = entry_price * (1 + config.stop_loss_value / 100)
        elif config.stop_loss_type == "atr":
            df_idx = df.index.get_loc(entry_idx)
            stop_price = calculate_atr_stop(df, df_idx, config)
        elif config.stop_loss_type in ("trailing", "breakeven"):
            if config.direction == "long":
                stop_price = entry_price * (1 - config.stop_loss_value / 100)
            else:
                stop_price = entry_price * (1 + config.stop_loss_value / 100)
        
        # Initialize trade
        trade = {
            "entry_date": entry_idx,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "highest_price": entry_price,
            "lowest_price": entry_price,
            "exit_date": None,
            "exit_price": None,
            "exit_reason": "target",  # or "stop_loss"
        }
        
        # Walk forward from entry to find exit
        stopped_out = False
        holding_days = group.loc[entry_idx:]
        
        for i, (bar_date, bar) in enumerate(holding_days.iterrows()):
            if i == 0 and config.entry_price == "Open":
                continue  # Skip entry bar for Open entries (entered at open)
            
            # Check stop-loss against intraday range
            if stop_price is not None:
                triggered, stop_exit_price = check_stop_loss(trade, bar, config)
                if triggered:
                    trade["exit_date"] = bar_date
                    trade["exit_price"] = stop_exit_price
                    trade["exit_reason"] = "stop_loss"
                    stopped_out = True
                    break
                
                # Update dynamic stops
                if config.stop_loss_type == "trailing":
                    trade["stop_price"] = update_trailing_stop(trade, bar, config)
                    stop_price = trade["stop_price"]
                elif config.stop_loss_type == "breakeven":
                    trade["stop_price"] = update_breakeven_stop(trade, bar, config)
                    stop_price = trade["stop_price"]
            
            # Check if we've reached exit TDoM
            if bar[exit_tdom_col] == config.exit_tdom and bar_date != entry_idx:
                trade["exit_date"] = bar_date
                trade["exit_price"] = bar[config.exit_price]
                trade["exit_reason"] = "target"
                break
        
        # If no exit found (month ended), exit at last bar
        if trade["exit_date"] is None:
            last_bar = holding_days.iloc[-1]
            trade["exit_date"] = holding_days.index[-1]
            trade["exit_price"] = last_bar["Close"]
            trade["exit_reason"] = "month_end"
        
        # Calculate P&L
        if config.direction == "long":
            price_diff = trade["exit_price"] - trade["entry_price"]
        else:
            price_diff = trade["entry_price"] - trade["exit_price"]
        
        gross_pnl = price_diff * config.quantity * config.contract_multiplier
        total_commission = config.commission_per_trade * 2  # Entry + exit
        total_slippage = config.slippage_per_trade * 2
        net_pnl = gross_pnl - total_commission - total_slippage
        
        trade["gross_pnl"] = gross_pnl
        trade["net_pnl"] = net_pnl
        trade["return_pct"] = (trade["exit_price"] / trade["entry_price"] - 1) * 100
        if config.direction == "short":
            trade["return_pct"] = -trade["return_pct"]
        trade["commission"] = total_commission
        trade["slippage"] = total_slippage
        
        trades.append(trade)
        equity.append(equity[-1] + net_pnl)
    
    return BacktestResult(trades=trades, equity_curve=equity, config=config)
```

---

## Performance Metrics (TradingView-Compatible)

### Metric Definitions

```python
def calculate_metrics(trades, equity_curve, config):
    """
    Calculate comprehensive performance metrics.
    Mirrors TradingView's Strategy Tester output.
    """
    if not trades:
        return {}
    
    returns = [t["net_pnl"] for t in trades]
    pct_returns = [t["return_pct"] for t in trades]
    winning = [r for r in returns if r > 0]
    losing = [r for r in returns if r < 0]
    
    # ── Core Metrics ──────────────────────────────────────
    net_profit = sum(returns)
    gross_profit = sum(winning) if winning else 0
    gross_loss = sum(losing) if losing else 0  # Negative number
    
    # ── Ratios ────────────────────────────────────────────
    profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float("inf")
    
    win_rate = len(winning) / len(returns) * 100 if returns else 0
    
    avg_win = np.mean(winning) if winning else 0
    avg_loss = np.mean(losing) if losing else 0
    payoff_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")
    
    # Expectancy: avg $ won per trade
    expectancy = np.mean(returns) if returns else 0
    
    # ── Drawdown ──────────────────────────────────────────
    equity = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity)
    drawdown = equity - running_max  # Always <= 0
    max_drawdown = abs(drawdown.min())
    
    # Drawdown duration (in trades)
    dd_duration = 0
    max_dd_duration = 0
    for i in range(1, len(equity)):
        if equity[i] < running_max[i]:
            dd_duration += 1
            max_dd_duration = max(max_dd_duration, dd_duration)
        else:
            dd_duration = 0
    
    # ── Streaks ───────────────────────────────────────────
    max_consec_wins = 0
    max_consec_losses = 0
    current_wins = 0
    current_losses = 0
    
    for r in returns:
        if r > 0:
            current_wins += 1
            current_losses = 0
            max_consec_wins = max(max_consec_wins, current_wins)
        elif r < 0:
            current_losses += 1
            current_wins = 0
            max_consec_losses = max(max_consec_losses, current_losses)
        else:
            current_wins = 0
            current_losses = 0
    
    # ── Risk-Adjusted ─────────────────────────────────────
    # Sharpe Ratio (annualized, assuming ~12 trades/year for monthly TDoM)
    trades_per_year = 12  # Approximate for monthly strategies
    if np.std(pct_returns) != 0:
        sharpe = (np.mean(pct_returns) / np.std(pct_returns)) * np.sqrt(trades_per_year)
    else:
        sharpe = 0
    
    # Sortino Ratio (only downside deviation)
    downside_returns = [r for r in pct_returns if r < 0]
    if downside_returns and np.std(downside_returns) != 0:
        sortino = (np.mean(pct_returns) / np.std(downside_returns)) * np.sqrt(trades_per_year)
    else:
        sortino = 0
    
    # Recovery Factor
    recovery_factor = net_profit / max_drawdown if max_drawdown != 0 else float("inf")
    
    # ── Return Metrics ────────────────────────────────────
    total_return_pct = np.mean(pct_returns) * len(pct_returns) if pct_returns else 0
    
    return {
        # Overview
        "total_trades": len(returns),
        "net_profit": round(net_profit, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(profit_factor, 2),
        
        # Win/Loss
        "win_rate": round(win_rate, 1),
        "winning_trades": len(winning),
        "losing_trades": len(losing),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "payoff_ratio": round(payoff_ratio, 2),
        "expectancy": round(expectancy, 2),
        "largest_win": round(max(returns), 2) if returns else 0,
        "largest_loss": round(min(returns), 2) if returns else 0,
        
        # Streaks
        "max_consecutive_wins": max_consec_wins,
        "max_consecutive_losses": max_consec_losses,
        
        # Drawdown
        "max_drawdown": round(max_drawdown, 2),
        "max_drawdown_duration": max_dd_duration,
        "recovery_factor": round(recovery_factor, 2),
        
        # Risk-Adjusted
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 2),
        
        # Returns
        "avg_return_pct": round(np.mean(pct_returns), 3) if pct_returns else 0,
        "total_return_pct": round(total_return_pct, 2),
        "total_commissions": round(sum(t["commission"] for t in trades), 2),
        "total_slippage": round(sum(t["slippage"] for t in trades), 2),
    }
```

---

## Backtest Visualization

### Equity Curve + Drawdown Chart

```python
def plot_backtest_results(trades, equity_curve, metrics):
    """
    Two-panel chart: Equity curve on top, drawdown below.
    Matches TradingView strategy tester visual style.
    """
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3],
        subplot_titles=("Equity Curve", "Drawdown")
    )
    
    # ── Equity Curve ──────────────────────────────────
    trade_dates = [t["exit_date"] for t in trades]
    equity_values = equity_curve[1:]  # Skip initial 0
    
    fig.add_trace(go.Scatter(
        x=trade_dates,
        y=equity_values,
        mode="lines",
        line=dict(color="#00CED1", width=2),
        name="Equity",
        fill="tozeroy",
        fillcolor="rgba(0,206,209,0.1)"
    ), row=1, col=1)
    
    # Mark winning/losing trades
    for trade in trades:
        color = "#4CAF50" if trade["net_pnl"] > 0 else "#F44336"
        fig.add_trace(go.Scatter(
            x=[trade["exit_date"]],
            y=[sum(t["net_pnl"] for t in trades[:trades.index(trade)+1])],
            mode="markers",
            marker=dict(size=4, color=color),
            showlegend=False,
            hovertext=f"P&L: ${trade['net_pnl']:.2f}<br>"
                      f"Return: {trade['return_pct']:.2f}%<br>"
                      f"Exit: {trade['exit_reason']}"
        ), row=1, col=1)
    
    # ── Drawdown ──────────────────────────────────────
    equity_arr = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_arr)
    drawdown = equity_arr - running_max
    
    fig.add_trace(go.Scatter(
        x=trade_dates,
        y=drawdown[1:],
        mode="lines",
        line=dict(color="#F44336", width=1),
        name="Drawdown",
        fill="tozeroy",
        fillcolor="rgba(244,67,54,0.3)"
    ), row=2, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        height=600,
        showlegend=False,
        title=f"Backtest: TDoM {config.entry_tdom} → {config.exit_tdom} | "
              f"Net: ${metrics['net_profit']:,.2f} | "
              f"Win Rate: {metrics['win_rate']}% | "
              f"Sharpe: {metrics['sharpe_ratio']}"
    )
    
    return fig
```

### Trade Table

```python
def display_trade_table(trades):
    """Scrollable table of all trades with color-coded P&L."""
    trade_df = pd.DataFrame(trades)
    trade_df["entry_date"] = pd.to_datetime(trade_df["entry_date"]).dt.strftime("%Y-%m-%d")
    trade_df["exit_date"] = pd.to_datetime(trade_df["exit_date"]).dt.strftime("%Y-%m-%d")
    
    display_cols = [
        "entry_date", "exit_date", "entry_price", "exit_price",
        "return_pct", "net_pnl", "exit_reason"
    ]
    
    def highlight_pnl(val):
        if isinstance(val, (int, float)):
            color = "#4CAF50" if val > 0 else "#F44336" if val < 0 else "#666"
            return f"color: {color}"
        return ""
    
    styled = trade_df[display_cols].style.applymap(
        highlight_pnl, subset=["return_pct", "net_pnl"]
    )
    
    return styled
```

### Metrics Dashboard

```python
def display_metrics_dashboard(metrics):
    """Display metrics in a compact Streamlit layout."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Net Profit", f"${metrics['net_profit']:,.2f}")
        st.metric("Gross Profit", f"${metrics['gross_profit']:,.2f}")
        st.metric("Gross Loss", f"${metrics['gross_loss']:,.2f}")
        st.metric("Total Trades", metrics["total_trades"])
    
    with col2:
        st.metric("Win Rate", f"{metrics['win_rate']}%")
        st.metric("Profit Factor", metrics["profit_factor"])
        st.metric("Payoff Ratio", metrics["payoff_ratio"])
        st.metric("Expectancy", f"${metrics['expectancy']:,.2f}")
    
    with col3:
        st.metric("Sharpe Ratio", metrics["sharpe_ratio"])
        st.metric("Sortino Ratio", metrics["sortino_ratio"])
        st.metric("Recovery Factor", metrics["recovery_factor"])
        st.metric("Max Drawdown", f"${metrics['max_drawdown']:,.2f}")
    
    with col4:
        st.metric("Largest Win", f"${metrics['largest_win']:,.2f}")
        st.metric("Largest Loss", f"${metrics['largest_loss']:,.2f}")
        st.metric("Max Consec. Wins", metrics["max_consecutive_wins"])
        st.metric("Max Consec. Losses", metrics["max_consecutive_losses"])
```

---

## Streamlit UI for TDoM Tab

### Layout Pattern

```python
def render_tdom_tab():
    st.header("📅 Trading Day of Month Analysis")
    
    # ── Sidebar Controls ──────────────────────────────
    with st.sidebar:
        st.subheader("TDoM Settings")
        
        counting_mode = st.radio(
            "Counting Direction",
            ["Forward (1, 2, 3...)", "Backward (-1, -2, -3...)"],
            help="Forward counts from month start, backward from month end"
        )
        
        strategy = st.selectbox(
            "Strategy Type",
            ["Open → Close (Intraday)",
             "Open → Next Open (Overnight)",
             "Close → Next Close"],
        )
        
        st.markdown("---")
        st.subheader("📆 Period & Cycle Filters")
        
        # Lookback period
        lookback_mode = st.radio(
            "Backtest Period",
            ["Last N Years", "Custom Range"]
        )
        
        if lookback_mode == "Last N Years":
            lookback_years = st.select_slider(
                "Lookback",
                options=[5, 10, 15, 20, 25, 30],
                value=20
            )
            start_year = None
            end_year = None
        else:
            col_y1, col_y2 = st.columns(2)
            with col_y1:
                start_year = st.number_input("From", 1990, 2026, 2000)
            with col_y2:
                end_year = st.number_input("To", 1990, 2026, 2026)
            lookback_years = None
        
        # Month filter
        month_names = {
            1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
            7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
        }
        selected_months = st.multiselect(
            "Months",
            options=list(month_names.keys()),
            format_func=lambda x: month_names[x],
            default=None,
            help="Leave empty for all months"
        )
        months_filter = selected_months if selected_months else None
        
        # Presidential cycle filter
        cycle_options = {
            1: "Year 1 (Post-Election)",
            2: "Year 2 (Midterm)",
            3: "Year 3 (Pre-Election)",
            4: "Year 4 (Election)"
        }
        selected_cycles = st.multiselect(
            "Presidential Cycle",
            options=list(cycle_options.keys()),
            format_func=lambda x: cycle_options[x],
            default=None,
            help="Leave empty for all cycle years"
        )
        presidential_cycle_filter = selected_cycles if selected_cycles else None
        
        st.markdown("---")
        st.subheader("🎯 Technical Filters")
        
        # SMA Trend Filter
        use_trend = st.checkbox("SMA Trend Filter")
        
        if use_trend:
            trend_sma_period = st.select_slider(
                "SMA Period",
                options=[10, 20, 50, 100, 150, 200],
                value=200
            )
            trend_condition = st.radio(
                "Price must be",
                ["Above SMA (Uptrend)", "Below SMA (Downtrend)"],
                help="Above = trend-following, Below = mean-reversion"
            )
            trend_cond = "above" if "Above" in trend_condition else "below"
        
        # RSI Filter
        use_rsi = st.checkbox("RSI Filter")
        
        if use_rsi:
            rsi_period = st.slider("RSI Period", 2, 30, 14)
            
            col_rsi1, col_rsi2 = st.columns(2)
            with col_rsi1:
                rsi_condition = st.selectbox(
                    "RSI must be",
                    ["Below threshold", "Above threshold"]
                )
            with col_rsi2:
                rsi_threshold = st.slider("Threshold", 0, 100, 30)
            
            rsi_cond = "below" if "Below" in rsi_condition else "above"
        
        # Combine mode (only if both filters active)
        if use_trend and use_rsi:
            filter_mode = st.radio(
                "Combine Filters",
                ["AND (both must pass)", "OR (either passes)"],
                help="AND is stricter, OR takes more trades"
            )
            combine_mode = "and" if "AND" in filter_mode else "or"
        else:
            combine_mode = "and"
        
        st.markdown("---")
        st.subheader("⚙️ Backtest Settings")
        
        use_range = st.checkbox("Multi-day hold (TDoM range)")
        
        if use_range:
            entry_tdom = st.number_input("Entry TDoM", -23, 23, 1)
            exit_tdom = st.number_input("Exit TDoM", -23, 23, 5)
        else:
            selected_tdom = st.number_input("TDoM", -23, 23, 1)
        
        direction = st.radio("Direction", ["Long", "Short"])
        
        instrument = st.selectbox(
            "Instrument Type",
            list(INSTRUMENT_PRESETS.keys()),
            format_func=lambda x: INSTRUMENT_PRESETS[x]["description"]
        )
        
        quantity = st.number_input(
            "Quantity",
            1, 10000,
            INSTRUMENT_PRESETS[instrument]["default_quantity"]
        )
        
        # Stop-Loss
        stop_type = st.selectbox(
            "Stop-Loss Type",
            ["None", "Fixed %", "Trailing %", "ATR-based", "Break-Even"]
        )
        
        if stop_type != "None":
            if stop_type in ("Fixed %", "Trailing %"):
                stop_value = st.slider("Stop-Loss %", 0.1, 10.0, 1.0, 0.1)
            elif stop_type == "ATR-based":
                stop_value = st.slider("ATR Multiplier", 0.5, 5.0, 1.5, 0.1)
                atr_period = st.slider("ATR Period", 5, 30, 14)
            elif stop_type == "Break-Even":
                stop_value = st.slider("Initial Stop %", 0.1, 10.0, 1.0, 0.1)
                be_trigger = st.slider("Break-Even Trigger %", 0.1, 5.0, 0.5, 0.1)
        
        # Time Stop
        use_time_stop = st.checkbox("Time Stop (max holding period)")
        if use_time_stop:
            time_stop_bars = st.slider(
                "Max Trading Days", 1, 23, 5,
                help="Position closes after N trading days regardless of P&L"
            )
            time_stop_exit = st.radio(
                "Time Stop Exit",
                ["Close", "Open"],
                help="Exit at Close of last bar or Open of next bar"
            )
        
        # Costs
        commission = st.number_input(
            "Commission (per trade)",
            0.0, 100.0,
            INSTRUMENT_PRESETS[instrument]["commission_default"]
        )
        slippage = st.number_input("Slippage (per trade)", 0.0, 100.0, 0.0)
    
    # ── Main Content ──────────────────────────────────
    
    # Tab 1: TDoM Heatmap / Bar Chart
    # Tab 2: Backtest Results
    # Tab 3: Trade List
    # Tab 4: Filter Analysis
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 TDoM Analysis", "📈 Backtest", "📋 Trades", "🔍 Filter Impact"
    ])
    
    with tab1:
        # Show bar chart of avg return per TDoM
        # Show heatmap: months × TDoM
        pass
    
    with tab2:
        # Equity curve + drawdown
        # Metrics dashboard
        pass
    
    with tab3:
        # Scrollable trade table
        pass
    
    with tab4:
        # Filter analysis: taken vs skipped trades
        # Comparison: with filter vs without filter
        display_filter_analysis(trades, skipped_trades, config)
```

---

## Chart Layout Standards

### Color Palette
```python
# Individual years: Light gray, low opacity
individual_years = "rgba(150,150,150,0.3)"

# Seasonal average: Bright cyan, thick
seasonal_avg = "#00CED1", width=4

# Confidence bands: Cyan transparent
confidence = "rgba(0,206,209,0.2)"

# Future projection: Orange dashed
future = "#FFA500", dash="dash"

# Presidential cycles:
cycle_colors = {
    "Year 1 (Post-Election)": "#FF6B6B",
    "Year 2 (Midterm Election)": "#FFA07A",
    "Year 3 (Pre-Election)": "#4ECDC4",
    "Year 4 (Election Year)": "#45B7D1"
}

# TDoM colors:
tdom_positive = "#4CAF50"   # Green for positive avg return
tdom_negative = "#F44336"   # Red for negative avg return
equity_line = "#00CED1"     # Cyan for equity curve
drawdown_fill = "rgba(244,67,54,0.3)"  # Red transparent for drawdown
```

### Y-Axis Range
```python
# Tight range for better visibility:
fig.update_yaxes(
    range=[90, 125],  # ±10% from start
    row=1, col=1
)
```

### Month Labels on X-Axis
```python
month_starts = []
month_names = ["Jan", "Feb", "Mar", ..., "Dec"]

for month in range(1, 13):
    day = datetime(2024, month, 1).timetuple().tm_yday
    month_starts.append(day)

fig.update_xaxes(
    tickmode="array",
    tickvals=month_starts,
    ticktext=month_names
)
```

---

## Performance Metrics

### Win Rate Calculation
```python
def calculate_stats(start_day, end_day):
    period_returns = []
    
    for year in available_years:
        year_df = year_data_stacked[year]["df"]
        period_df = year_df[
            (year_df["day_of_year"] >= start_day) & 
            (year_df["day_of_year"] <= end_day)
        ]
        
        if len(period_df) > 0:
            # Cumulative return for period:
            cum_return = (1 + period_df["return"]).prod() - 1
            period_returns.append(cum_return * 100)
    
    # Metrics:
    win_rate = len([r for r in period_returns if r > 0]) / len(period_returns) * 100
    avg_return = np.mean(period_returns)
    annualized = avg_return * (252 / num_trading_days)
    
    return {
        "win_rate": win_rate,
        "avg_return": avg_return,
        "annualized": annualized,
        "max_gain": max(period_returns),
        "max_loss": min(period_returns)
    }
```

---

## Monthly Heatmap

### Calculation with Log Returns for Yearly Sum

**CRITICAL:** Use log returns to sum monthly returns correctly.

```python
# Monthly returns:
monthly_returns = {}
log_returns = []

for month in range(1, 13):
    month_df = year_df[year_df["month"] == month]
    if len(month_df) > 0:
        monthly_return = (1 + month_df["return"]).prod() - 1
        monthly_returns[month] = monthly_return * 100
        log_returns.append(np.log(1 + monthly_return))
    else:
        monthly_returns[month] = np.nan  # Not 0!

# Yearly total (correct math):
yearly_return = (np.exp(sum(log_returns)) - 1) * 100
```

### Color Coding
```python
def color_cells(val):
    if pd.isna(val):
        return 'background-color: #1a1a1a; color: #666'  # Black (no data)
    elif val > 3:
        return 'background-color: #2d5016; color: white'  # Dark green
    elif val > 0:
        return 'background-color: #5a8c3a; color: white'  # Green
    elif val > -3:
        return 'background-color: #8c3a3a; color: white'  # Red
    else:
        return 'background-color: #5c1a1a; color: white'  # Dark red
```

---

## Common Bugs & Solutions

### Bug: Seasonal line starts at 200 instead of 100
**Cause:** Averaging BEFORE normalizing each year  
**Fix:** Normalize each year to start at 100 FIRST, THEN average

```python
# WRONG:
avg = np.mean(all_raw_cumulative)  # Some start at 205!

# CORRECT:
normalized = [normalize_to_100(year) for year in years]
avg = np.mean(normalized)  # All started at 100
```

### Bug: Future projection disconnected from historical
**Cause:** Starting future projection at day 366 with different value  
**Fix:** Connect last historical point to first future point

```python
# Ensure continuity:
future_start_value = avg_cumulative[0]  # Same as Jan 1
```

### Bug: Confidence bands show as lines instead of fill
**Cause:** Missing fill='tonexty' parameter  
**Fix:**
```python
fig.add_trace(go.Scatter(y=upper, line=dict(width=0)))
fig.add_trace(go.Scatter(y=lower, fill='tonexty', fillcolor='rgba(...)'))
```

### Bug: Trading days count returns 0
**Cause:** DataFrame doesn't have "df" key in year_data_stacked  
**Fix:** Always store original dataframe:
```python
year_data_stacked[year] = {
    "days": [...],
    "cumulative": [...],
    "df": year_df  # ← Don't forget!
}
```

### Bug: TDoM -1 maps to wrong day
**Cause:** Using `range(-1, -n, -1)` instead of `range(-n, 0)`  
**Fix:** Reverse count must go from -n to -1 (not -1 to -n):
```python
# WRONG:
tdom_reverse = list(range(-1, -(n+1), -1))  # [-1, -2, ..., -n]

# CORRECT:
tdom_reverse = list(range(-n, 0))  # [-n, ..., -2, -1]
# Last element is -1 = last trading day ✓
```

### Bug: Stop-loss fills at wrong price on gap days
**Cause:** Assuming fill at stop price when market gaps through  
**Fix:** If Open is already past stop, fill at Open (slippage):
```python
if daily_bar["Open"] <= stop_price:  # Gapped below stop
    exit_price = daily_bar["Open"]   # Fill at open, not stop
```

### Bug: Backtest double-counts entry bar
**Cause:** Checking stop-loss on the same bar as entry  
**Fix:** Skip the entry bar in the stop-loss check loop:
```python
for i, (bar_date, bar) in enumerate(holding_days.iterrows()):
    if i == 0 and config.entry_price == "Open":
        continue  # Don't check stop on entry bar
```

---

## Streamlit Best Practices

### Caching
```python
@st.cache_data(ttl=3600)  # Cache 1 hour
def load_data(ticker, years):
    return yf.download(ticker, period=f"{years}y", ...)
```

### Session State for Presets
```python
if 'preset_range' not in st.session_state:
    st.session_state.preset_range = (274, 311)

if st.button("Fall Rally"):
    st.session_state.preset_range = (274, 334)
    # No need to rerun, slider updates automatically
```

### Compact Layout
```python
# Avoid excessive spacing:
# ❌ st.markdown("---") after every section
# ✅ Use sparingly, only for major sections

# Integrate info into headers:
st.subheader(f"Performance (Period: {start} to {end})")
# Instead of separate info box
```

---

## AI Integration Features

### Overview

The AI layer adds intelligent analysis on top of the statistical engine. It uses pattern recognition, multi-factor scoring, natural language generation, and anomaly detection to help traders make better decisions. All AI features are optional add-ons — the core tool works without them.

### Feature 1: Pattern Matcher (DTW — Dynamic Time Warping)

**Purpose:** Find historical years whose price pattern most closely resembles the current year's trajectory. This helps answer: "Which past years looked like this year so far, and what happened next?"

```python
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

def find_similar_patterns(current_pattern, historical_data, top_n=5):
    """
    Find the N most similar historical years using DTW.
    
    Args:
        current_pattern: list/array of normalized returns for current year (up to today)
        historical_data: dict {year: full_year_normalized_returns}
        top_n: number of matches to return
    
    Returns:
        List of (year, similarity_score, full_year_pattern) tuples, sorted by similarity
    """
    current_len = len(current_pattern)
    similarities = []
    
    for year, full_pattern in historical_data.items():
        # Compare only the same portion of the year (up to current day)
        comparable = full_pattern[:current_len]
        
        if len(comparable) < current_len * 0.9:
            continue  # Skip years with too little data
        
        distance, path = fastdtw(current_pattern, comparable, dist=euclidean)
        
        # Normalize score: 0 = identical, 1 = very different
        max_possible = current_len * 10  # Heuristic normalization
        similarity_score = max(0, 1 - (distance / max_possible))
        
        similarities.append({
            "year": year,
            "similarity": round(similarity_score * 100, 1),  # 0-100%
            "distance": round(distance, 2),
            "full_pattern": full_pattern,
            "rest_of_year": full_pattern[current_len:],  # What happened AFTER this point
        })
    
    return sorted(similarities, key=lambda x: x["similarity"], reverse=True)[:top_n]


def project_from_matches(matches, weights="similarity"):
    """
    Create a forward projection based on similar year matches.
    
    Args:
        matches: output from find_similar_patterns
        weights: "similarity" (weighted by match quality) or "equal"
    
    Returns:
        dict with projected_path, confidence_upper, confidence_lower
    """
    rest_patterns = [m["rest_of_year"] for m in matches if len(m["rest_of_year"]) > 0]
    
    if not rest_patterns:
        return None
    
    # Truncate to shortest remaining pattern
    min_len = min(len(p) for p in rest_patterns)
    rest_patterns = [p[:min_len] for p in rest_patterns]
    
    if weights == "similarity":
        w = np.array([m["similarity"] for m in matches[:len(rest_patterns)]])
        w = w / w.sum()  # Normalize to sum=1
        projected = np.average(rest_patterns, axis=0, weights=w)
    else:
        projected = np.mean(rest_patterns, axis=0)
    
    std = np.std(rest_patterns, axis=0)
    
    return {
        "projected": projected.tolist(),
        "upper": (projected + std).tolist(),
        "lower": (projected - std).tolist(),
        "n_matches": len(rest_patterns),
        "avg_similarity": np.mean([m["similarity"] for m in matches[:len(rest_patterns)]])
    }
```

**Visualization:**
```python
def plot_pattern_matches(current_year, matches, projection):
    """
    Plot current year + top matches + forward projection.
    Color matches by similarity (bright = close match, faded = weaker).
    """
    fig = go.Figure()
    
    # Current year (bold)
    fig.add_trace(go.Scatter(
        y=current_year,
        mode="lines",
        line=dict(color="#00CED1", width=3),
        name=f"Current Year ({datetime.now().year})"
    ))
    
    # Historical matches (with opacity based on similarity)
    match_colors = ["#FF6B6B", "#FFA07A", "#4ECDC4", "#45B7D1", "#96CEB4"]
    for i, match in enumerate(matches):
        opacity = match["similarity"] / 100
        fig.add_trace(go.Scatter(
            y=match["full_pattern"],
            mode="lines",
            line=dict(color=match_colors[i % len(match_colors)], width=1.5),
            opacity=max(0.3, opacity),
            name=f"{match['year']} ({match['similarity']}% match)"
        ))
    
    # Forward projection (dashed with confidence band)
    if projection:
        proj_x = list(range(len(current_year), len(current_year) + len(projection["projected"])))
        
        fig.add_trace(go.Scatter(
            x=proj_x, y=projection["upper"],
            mode="lines", line=dict(width=0),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=proj_x, y=projection["lower"],
            mode="lines", line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(255,165,0,0.15)",
            name="Projection Range"
        ))
        fig.add_trace(go.Scatter(
            x=proj_x, y=projection["projected"],
            mode="lines",
            line=dict(color="#FFA500", width=2, dash="dash"),
            name=f"AI Projection ({projection['n_matches']} matches)"
        ))
    
    fig.update_layout(template="plotly_dark", title="Pattern Match Analysis")
    return fig
```

### Feature 2: Multi-Factor AI Score (SeasonalEdge Score)

**Purpose:** Combine multiple signals into a single 0-100 score that indicates how favorable the current setup is for a seasonal trade. Displayed as a dashboard gauge/meter.

```python
@dataclass
class ScoreFactor:
    """Single scoring factor with weight and value."""
    name: str
    value: float        # Raw value (0-100)
    weight: float       # 0.0 to 1.0 (weights must sum to 1.0)
    description: str    # Human-readable explanation
    signal: str         # "bullish", "bearish", "neutral"


def calculate_seasonal_edge_score(date, ticker, df, config):
    """
    Calculate composite AI score from multiple factors.
    
    Args:
        date: current date
        ticker: symbol string
        df: full OHLC DataFrame
        config: scoring configuration
    
    Returns:
        (total_score: float, factors: list[ScoreFactor])
    """
    factors = []
    
    # ── Factor 1: Seasonal Pattern Strength (30%) ─────────────
    day_of_year = date.timetuple().tm_yday
    seasonal_avg = get_avg_return_for_day(day_of_year, historical_data)
    seasonal_std = get_std_for_day(day_of_year, historical_data)
    
    # Z-score of seasonal tendency
    if seasonal_std > 0:
        z_score = seasonal_avg / seasonal_std
        seasonal_score = min(100, max(0, 50 + z_score * 25))  # Map to 0-100
    else:
        seasonal_score = 50  # Neutral
    
    signal = "bullish" if seasonal_score > 60 else "bearish" if seasonal_score < 40 else "neutral"
    factors.append(ScoreFactor(
        name="Seasonality",
        value=round(seasonal_score, 1),
        weight=0.30,
        description=f"Avg return on day {day_of_year}: {seasonal_avg:.3f}% (z={z_score:.2f})",
        signal=signal
    ))
    
    # ── Factor 2: TDoM Edge (25%) ─────────────────────────────
    tdom = get_current_tdom(date, df)
    tdom_avg = get_avg_return_for_tdom(tdom, df)
    tdom_win_rate = get_win_rate_for_tdom(tdom, df)
    
    tdom_score = min(100, max(0, tdom_win_rate))  # Win rate as score
    signal = "bullish" if tdom_score > 55 else "bearish" if tdom_score < 45 else "neutral"
    factors.append(ScoreFactor(
        name="TDoM Edge",
        value=round(tdom_score, 1),
        weight=0.25,
        description=f"TDoM {tdom}: Win rate {tdom_win_rate:.1f}%, Avg {tdom_avg:.3f}%",
        signal=signal
    ))
    
    # ── Factor 3: Presidential Cycle (15%) ────────────────────
    cycle_year = get_presidential_cycle_year_number(date.year)
    cycle_label = CYCLE_LABELS[cycle_year]
    
    # Historical return by cycle phase for this day-of-year
    cycle_returns = get_cycle_returns(day_of_year, cycle_year, historical_data)
    cycle_avg = np.mean(cycle_returns) if cycle_returns else 0
    
    cycle_score = min(100, max(0, 50 + cycle_avg * 10))
    signal = "bullish" if cycle_score > 60 else "bearish" if cycle_score < 40 else "neutral"
    factors.append(ScoreFactor(
        name="Presidential Cycle",
        value=round(cycle_score, 1),
        weight=0.15,
        description=f"{cycle_label}: Avg {cycle_avg:.3f}%",
        signal=signal
    ))
    
    # ── Factor 4: Volatility Regime / VIX (15%) ──────────────
    vix_level = get_vix_level(date)  # Requires ^VIX data
    
    if vix_level is not None:
        # Low VIX = favorable for longs, high VIX = opportunity but risky
        if vix_level < 15:
            vol_score = 75  # Low vol, steady uptrend environment
        elif vix_level < 20:
            vol_score = 60  # Normal
        elif vix_level < 30:
            vol_score = 40  # Elevated, cautious
        else:
            vol_score = 20  # Fear regime
        
        signal = "bullish" if vol_score > 60 else "bearish" if vol_score < 40 else "neutral"
        factors.append(ScoreFactor(
            name="Volatility Regime",
            value=round(vol_score, 1),
            weight=0.15,
            description=f"VIX: {vix_level:.1f} ({'Low' if vix_level < 20 else 'Elevated' if vix_level < 30 else 'High'})",
            signal=signal
        ))
    else:
        # Fallback: use realized volatility
        realized_vol = df["Close"].pct_change().tail(20).std() * np.sqrt(252) * 100
        vol_score = min(100, max(0, 80 - realized_vol * 2))
        factors.append(ScoreFactor(
            name="Realized Volatility",
            value=round(vol_score, 1),
            weight=0.15,
            description=f"20-day realized vol: {realized_vol:.1f}%",
            signal="bullish" if vol_score > 60 else "bearish" if vol_score < 40 else "neutral"
        ))
    
    # ── Factor 5: Trend Alignment (15%) ──────────────────────
    sma_50 = df["Close"].rolling(50).mean().iloc[-1]
    sma_200 = df["Close"].rolling(200).mean().iloc[-1]
    current_price = df["Close"].iloc[-1]
    
    above_50 = current_price > sma_50
    above_200 = current_price > sma_200
    golden_cross = sma_50 > sma_200
    
    trend_score = 50
    if above_200: trend_score += 20
    if above_50: trend_score += 15
    if golden_cross: trend_score += 15
    trend_score = min(100, trend_score)
    
    signal = "bullish" if trend_score > 65 else "bearish" if trend_score < 35 else "neutral"
    factors.append(ScoreFactor(
        name="Trend Alignment",
        value=round(trend_score, 1),
        weight=0.15,
        description=f"{'Above' if above_200 else 'Below'} 200-SMA, "
                    f"{'Golden' if golden_cross else 'Death'} Cross",
        signal=signal
    ))
    
    # ── Composite Score ───────────────────────────────────────
    total_score = sum(f.value * f.weight for f in factors)
    
    return round(total_score, 1), factors


def get_score_interpretation(score):
    """Human-readable interpretation of the composite score."""
    if score >= 80:
        return "🟢 Strong Bullish", "Multiple factors align strongly for upside."
    elif score >= 65:
        return "🟢 Moderately Bullish", "Favorable conditions, above-average setup."
    elif score >= 50:
        return "🟡 Neutral", "Mixed signals, no clear directional edge."
    elif score >= 35:
        return "🟠 Moderately Bearish", "Caution advised, below-average conditions."
    else:
        return "🔴 Strong Bearish", "Multiple factors suggest downside risk."
```

**Dashboard Visualization:**
```python
def display_ai_score_dashboard(score, factors):
    """Display the SeasonalEdge Score as a gauge + factor breakdown."""
    
    # Main gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={"text": "SeasonalEdge Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#00CED1"},
            "steps": [
                {"range": [0, 35], "color": "rgba(244,67,54,0.3)"},
                {"range": [35, 65], "color": "rgba(255,193,7,0.3)"},
                {"range": [65, 100], "color": "rgba(76,175,80,0.3)"}
            ],
            "threshold": {
                "line": {"color": "white", "width": 2},
                "value": score
            }
        }
    ))
    fig_gauge.update_layout(template="plotly_dark", height=250)
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Interpretation
    label, desc = get_score_interpretation(score)
    st.markdown(f"### {label}")
    st.markdown(desc)
    
    # Factor breakdown
    st.markdown("#### Factor Breakdown")
    for f in factors:
        emoji = "🟢" if f.signal == "bullish" else "🔴" if f.signal == "bearish" else "🟡"
        col1, col2, col3 = st.columns([3, 1, 6])
        with col1:
            st.markdown(f"{emoji} **{f.name}**")
        with col2:
            st.markdown(f"**{f.value:.0f}** ({f.weight*100:.0f}%)")
        with col3:
            st.progress(f.value / 100)
            st.caption(f.description)
```

### Feature 3: Natural Language Commentary

**Purpose:** Generate human-readable market commentary based on current seasonal data. Answers questions like "What's the seasonal outlook for next week?" in plain language.

```python
def generate_seasonal_commentary(ticker, date, score, factors, matches, tdom_stats):
    """
    Generate natural language commentary combining all AI signals.
    
    Returns:
        str: Multi-paragraph commentary
    """
    day_of_year = date.timetuple().tm_yday
    cycle_year = get_presidential_cycle_year_number(date.year)
    tdom = get_current_tdom(date)
    month_name = date.strftime("%B")
    
    # Build commentary sections
    sections = []
    
    # ── Opening / Score Summary ───────────────────────
    label, desc = get_score_interpretation(score)
    sections.append(
        f"**SeasonalEdge Analysis for {ticker} — {date.strftime('%B %d, %Y')}**\n\n"
        f"The composite score is **{score}/100** ({label.split(' ', 1)[1]}). {desc}"
    )
    
    # ── Seasonal Pattern ──────────────────────────────
    seasonal_factor = next((f for f in factors if f.name == "Seasonality"), None)
    if seasonal_factor:
        if seasonal_factor.signal == "bullish":
            sections.append(
                f"Historically, this period in {month_name} has shown above-average returns. "
                f"{seasonal_factor.description}."
            )
        elif seasonal_factor.signal == "bearish":
            sections.append(
                f"Seasonal headwinds are present — this period in {month_name} has historically "
                f"been weaker than average. {seasonal_factor.description}."
            )
        else:
            sections.append(
                f"Seasonal patterns are neutral for this period. {seasonal_factor.description}."
            )
    
    # ── TDoM Context ─────────────────────────────────
    tdom_factor = next((f for f in factors if f.name == "TDoM Edge"), None)
    if tdom_factor:
        sections.append(
            f"Today is Trading Day {tdom} of the month. {tdom_factor.description}."
        )
    
    # ── Pattern Match Insight ────────────────────────
    if matches and len(matches) > 0:
        best_match = matches[0]
        match_years = ", ".join(str(m["year"]) for m in matches[:3])
        sections.append(
            f"The current price trajectory most closely resembles {match_years}. "
            f"The best match is {best_match['year']} ({best_match['similarity']}% similarity)."
        )
        
        # What happened in matching years?
        future_returns = [
            np.mean(m["rest_of_year"][:20]) - m["rest_of_year"][0] 
            for m in matches if len(m["rest_of_year"]) > 20
        ]
        if future_returns:
            avg_future = np.mean(future_returns)
            if avg_future > 0:
                sections.append(
                    f"In those similar years, the following 20 trading days saw an average "
                    f"gain of {avg_future:.1f} points on the normalized scale."
                )
            else:
                sections.append(
                    f"In those similar years, the following 20 trading days saw an average "
                    f"decline of {abs(avg_future):.1f} points on the normalized scale."
                )
    
    # ── Presidential Cycle ───────────────────────────
    cycle_factor = next((f for f in factors if f.name == "Presidential Cycle"), None)
    if cycle_factor:
        sections.append(f"Presidential cycle context: {cycle_factor.description}.")
    
    # ── Risk Caveat ──────────────────────────────────
    sections.append(
        "⚠️ *This analysis is based on historical patterns and statistical probabilities. "
        "Past performance does not guarantee future results. Always use proper risk management.*"
    )
    
    return "\n\n".join(sections)
```

### Feature 4: Anomaly Detection & Alerts

**Purpose:** Automatically flag when today's price action deviates significantly from the seasonal expectation. Helps catch regime changes early.

```python
def detect_seasonal_anomalies(current_year_data, avg_seasonal, std_seasonal, 
                               z_threshold=2.0):
    """
    Detect days where the current year deviates significantly from seasonal norms.
    
    Args:
        current_year_data: list of normalized returns for current year
        avg_seasonal: average seasonal curve (365 values)
        std_seasonal: standard deviation curve (365 values)
        z_threshold: how many standard deviations = anomaly (default 2.0)
    
    Returns:
        List of anomaly dicts with date, z_score, type
    """
    anomalies = []
    
    for i, (actual, expected, std) in enumerate(
        zip(current_year_data, avg_seasonal, std_seasonal)
    ):
        if std == 0:
            continue
        
        z_score = (actual - expected) / std
        
        if abs(z_score) >= z_threshold:
            anomalies.append({
                "day_of_year": i + 1,
                "actual": actual,
                "expected": expected,
                "z_score": round(z_score, 2),
                "type": "above_normal" if z_score > 0 else "below_normal",
                "severity": "extreme" if abs(z_score) >= 3 else "significant"
            })
    
    return anomalies


def generate_anomaly_alerts(anomalies, ticker):
    """Generate human-readable alerts for detected anomalies."""
    alerts = []
    
    # Recent anomalies (last 5 trading days)
    recent = [a for a in anomalies if a["day_of_year"] >= max(a["day_of_year"] for a in anomalies) - 5]
    
    for a in recent:
        if a["type"] == "above_normal":
            emoji = "🔥" if a["severity"] == "extreme" else "📈"
            alerts.append(
                f"{emoji} **Day {a['day_of_year']}**: {ticker} is trading {abs(a['z_score']):.1f}σ "
                f"ABOVE seasonal expectations (actual: {a['actual']:.1f}, expected: {a['expected']:.1f})"
            )
        else:
            emoji = "⚠️" if a["severity"] == "extreme" else "📉"
            alerts.append(
                f"{emoji} **Day {a['day_of_year']}**: {ticker} is trading {abs(a['z_score']):.1f}σ "
                f"BELOW seasonal expectations (actual: {a['actual']:.1f}, expected: {a['expected']:.1f})"
            )
    
    # Trend of anomalies
    if len(recent) >= 3:
        all_above = all(a["type"] == "above_normal" for a in recent)
        all_below = all(a["type"] == "below_normal" for a in recent)
        
        if all_above:
            alerts.append(
                "🚀 **Pattern Break**: Sustained outperformance vs seasonal norms. "
                "Consider this may be a trend change rather than mean-reversion opportunity."
            )
        elif all_below:
            alerts.append(
                "🛑 **Pattern Break**: Sustained underperformance vs seasonal norms. "
                "The seasonal tailwind may not materialize this year."
            )
    
    return alerts
```

### Feature 5: Smart Backtest Suggestions

**Purpose:** Analyze backtest results and suggest parameter optimizations. Not a black-box optimizer — it explains WHY certain changes might help.

```python
def analyze_backtest_and_suggest(trades, metrics, config):
    """
    Analyze completed backtest and generate actionable suggestions.
    
    Returns:
        List of suggestion dicts with title, description, new_config_changes
    """
    suggestions = []
    
    # ── Check win rate ────────────────────────────────
    if metrics["win_rate"] < 45:
        suggestions.append({
            "title": "Low Win Rate — Consider Adding Trend Filter",
            "description": (
                f"Win rate is {metrics['win_rate']}%, below the typical threshold for "
                f"profitable trading. Adding a trend filter (e.g., price above 200-SMA) "
                f"would filter out trades taken during downtrends, which likely account "
                f"for many losing trades."
            ),
            "priority": "high",
            "suggested_change": {
                "use_trend_filter": True,
                "trend_sma_period": 200,
                "trend_condition": "above"
            }
        })
    
    # ── Check profit factor ───────────────────────────
    if 0 < metrics["profit_factor"] < 1.2:
        suggestions.append({
            "title": "Low Profit Factor — Tighten Stop-Loss",
            "description": (
                f"Profit factor is {metrics['profit_factor']}, meaning gross profit "
                f"barely exceeds gross loss. A tighter stop-loss or trailing stop "
                f"could cut losing trades shorter and improve the ratio."
            ),
            "priority": "medium",
            "suggested_change": {
                "stop_loss_type": "trailing",
                "stop_loss_value": 1.5
            }
        })
    
    # ── Check max drawdown ────────────────────────────
    if metrics["max_drawdown"] > abs(metrics["net_profit"]) * 0.5:
        suggestions.append({
            "title": "Large Drawdown Relative to Profit",
            "description": (
                f"Max drawdown (${metrics['max_drawdown']:,.0f}) is more than 50% of "
                f"net profit (${metrics['net_profit']:,.0f}). Consider adding a time "
                f"stop to limit exposure, or reduce position size."
            ),
            "priority": "high",
            "suggested_change": {
                "use_time_stop": True,
                "time_stop_bars": 3
            }
        })
    
    # ── Check consecutive losses ──────────────────────
    if metrics["max_consecutive_losses"] >= 6:
        suggestions.append({
            "title": "Long Losing Streaks Detected",
            "description": (
                f"Maximum {metrics['max_consecutive_losses']} consecutive losses. "
                f"This suggests the strategy performs poorly in certain market regimes. "
                f"Consider adding an RSI filter to avoid overbought entries, or limit "
                f"to specific months with stronger seasonal patterns."
            ),
            "priority": "medium",
            "suggested_change": {
                "use_rsi_filter": True,
                "rsi_period": 14,
                "rsi_threshold": 70,
                "rsi_condition": "below"
            }
        })
    
    # ── Check if short direction might work better ────
    if metrics["win_rate"] < 50 and config.direction == "long":
        suggestions.append({
            "title": "Consider Short Direction",
            "description": (
                f"The long setup has a {metrics['win_rate']}% win rate. This TDoM may "
                f"actually have a bearish bias. Try running the backtest with direction='short' "
                f"to see if the inverse trade is more profitable."
            ),
            "priority": "low",
            "suggested_change": {
                "direction": "short"
            }
        })
    
    # ── Check for over-filtering ──────────────────────
    if hasattr(config, 'skipped_trades_count'):
        total = metrics["total_trades"] + config.skipped_trades_count
        skip_pct = config.skipped_trades_count / total * 100 if total > 0 else 0
        
        if skip_pct > 70:
            suggestions.append({
                "title": "Filters Too Restrictive",
                "description": (
                    f"Filters are blocking {skip_pct:.0f}% of trade opportunities, "
                    f"leaving only {metrics['total_trades']} trades. Results may not "
                    f"be statistically significant. Consider loosening filter thresholds "
                    f"or switching from AND to OR combination."
                ),
                "priority": "high",
                "suggested_change": {
                    "filter_combine_mode": "or"
                }
            })
    
    return sorted(suggestions, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["priority"]])
```

### AI Features Streamlit UI Tab

```python
def render_ai_tab(ticker, df, historical_data, current_year_data):
    """Render the AI Features tab in the Streamlit app."""
    
    st.header("🤖 AI Analysis")
    
    ai_tab1, ai_tab2, ai_tab3, ai_tab4 = st.tabs([
        "🎯 SeasonalEdge Score",
        "🔍 Pattern Matcher", 
        "📝 Commentary",
        "⚠️ Anomaly Alerts"
    ])
    
    with ai_tab1:
        score, factors = calculate_seasonal_edge_score(
            datetime.now(), ticker, df, config
        )
        display_ai_score_dashboard(score, factors)
    
    with ai_tab2:
        col1, col2 = st.columns([1, 3])
        with col1:
            n_matches = st.slider("Top N matches", 3, 10, 5)
        
        matches = find_similar_patterns(current_year_data, historical_data, n_matches)
        projection = project_from_matches(matches)
        
        fig = plot_pattern_matches(current_year_data, matches, projection)
        st.plotly_chart(fig, use_container_width=True)
        
        # Match table
        match_df = pd.DataFrame([{
            "Year": m["year"],
            "Similarity": f"{m['similarity']}%",
            "Distance": m["distance"]
        } for m in matches])
        st.dataframe(match_df, use_container_width=True)
    
    with ai_tab3:
        tdom_stats = build_tdom_heatmap(df)
        commentary = generate_seasonal_commentary(
            ticker, datetime.now(), score, factors, matches, tdom_stats
        )
        st.markdown(commentary)
    
    with ai_tab4:
        z_thresh = st.slider("Anomaly Threshold (σ)", 1.5, 3.0, 2.0, 0.1)
        anomalies = detect_seasonal_anomalies(
            current_year_data, avg_seasonal, std_seasonal, z_thresh
        )
        alerts = generate_anomaly_alerts(anomalies, ticker)
        
        if alerts:
            for alert in alerts:
                st.markdown(alert)
        else:
            st.success("No significant anomalies detected. "
                       "Current price action is within normal seasonal bounds.")
```

---

## Multipage Architecture (CURRENT — v4.0)

### Project Structure (Implemented)

```
Saisonalcharts/                      ← Projektordner
├── seasonal_app.py                  ← 📈 Startseite / Dashboard
├── shared/                          ← Gemeinsame Module (importiert von allen Seiten)
│   ├── __init__.py
│   ├── constants.py                 ← Farben, Labels, CYCLE_COLORS, DECADE_COLORS,
│   │                                   OVERLAY_CONFIGS, US_WARS, PRESSURE_PERIODS,
│   │                                   MONTH_NAMES_DE, DEFAULT_TICKER, DEFAULT_YEARS
│   ├── data.py                      ← download_data (yfinance + cache), preprocess
│   ├── calculations.py              ← Saisonale Analyse, Pressure, Indikatoren,
│   │                                   Krieg/Frieden, Turn-of-Month Berechnung + Chart
│   ├── holidays.py                  ← NYSE-Feiertage (12 Stück), Weekend Rule,
│   │                                   Easter-Algorithmus, Holiday-Effekt Analyse + Chart
│   ├── charts.py                    ← build_seasonal_chart (Hauptchart mit Hover,
│   │                                   Heute-Markierung, Overlays, Zyklen, etc.)
│   └── strategies/                  ← ✅ NEU (v6.0): Saisonalstrategien-Modul
│       ├── __init__.py              ← Zentraler Export aller Strategien
│       ├── definitions.py           ← 65+ Strategie-Metadaten als Python-Dicts
│       │                               (Kategorie, Asset, Zeitfenster, Stärke, Modul)
│       ├── januar_trifecta.py       ← Santa Claus Rally + First Five Days +
│       │                               January Barometer → Ampelsystem (Grün/Gelb/Orange/Rot)
│       └── kaeppel.py               ← Jay Kaeppel: Holiday System, Simple Monthly,
│                                       Known Trend Index (KTI 0–5), Election Cycle,
│                                       Decennial Cycle (Years Ending in 5)
├── pages/                           ← Streamlit Multipage (automatisch erkannt)
│   ├── 1_📊_Erweiterte_Analyse.py   ← Zyklen, Pressure, War/Peace, Indikatoren
│   ├── 2_🔄_Turn_of_the_Month.py    ← Monatswechsel-Effekt
│   ├── 3_📅_Feiertags_Effekt.py     ← Feiertags-Analyse
│   ├── 4_📅_Weekday_Analyse.py      ← Wochentag-Analyse
│   ├── 5_📆_Monthly_Performance.py  ← Monatsperformance + TDOM
│   ├── 6_🏛️_Zentralbanken.py       ← Fed/ECB/BOE/BOJ
│   ├── 7_🌕_Mondphasen.py          ← Vollmond/Neumond-Effekt
│   ├── 8_🧠_TruePath.py            ← KI-Pattern-Matching + SeasonalEdge Score
│   └── 9_🚦_Strategien.py          ← ✅ NEU (v6.0): Januar Trifecta Ampelsystem
│                                       + Strategie-Bibliothek (65+ Einträge filterbar)
├── weekday_analysis.py              ← Standalone (noch nicht integriert)
├── weekday_by_month.py              ← Standalone (noch nicht integriert)
└── US-Wars.MD.docx                  ← Quelldokument
```

### Import Pattern (CRITICAL — sys.path Fix)

Streamlit's `exec()` findet `shared/` nicht automatisch. JEDE Datei braucht diesen Header:

```python
# In seasonal_app.py (Hauptordner):
import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _candidate in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_candidate, "shared")):
            _project_dir = _candidate
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

# In pages/*.py (eine Ebene tiefer → parent.parent):
import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
# ... gleicher Fallback-Code ...
```

### Page Responsibilities

| Seite | Datei | Features |
|-------|-------|----------|
| **Dashboard** | `seasonal_app.py` | Saisonalchart, Heute-Markierung, Overlay (Last Year/5Y/10Y), Zeitraum-Presets |
| **Erweiterte Analyse** | `pages/1_📊_...py` | + Zyklen, Dekade, Pressure, War/Peace, Dec-Low/Jan-First5 Indikatoren |
| **Turn of Month** | `pages/2_🔄_...py` | ToM-Chart (t0=0%), Slider t-y/t+x, Best/Worst, Detail pro Monat |
| **Feiertags-Effekt** | `pages/3_📅_...py` | 12+ NYSE-Feiertage + Chinese NY, Columbus Day, Jom Kippur |
| **Weekday-Analyse** | `pages/4_📅_...py` | 4 Rendite-Modi (C→C, C→O, O→C, O→C+1), SMA/RSI Filter, Heatmap |
| **Monthly Performance** | `pages/5_📆_...py` | Intra-Monat TDOM-Chart, Wochen-Balken, 12-Monats-Übersicht, Two-Week (1st/2nd), Detrend, Presidential Cycle Filter |
| **Zentralbanken** | `pages/6_🏛️_...py` | Fed/ECB/BOE/BOJ + Rate Hikes/Cuts + Minutes, kombinierbar, Nächste Termine |
| **Mondphasen** | `pages/7_🌕_...py` | Vollmond/Neumond-Effekt, 334+ Events seit 1990, Nächste Termine |
| **TruePath** | `pages/8_🧠_...py` | KI-Pattern-Matching (Korrelation/Euklidisch), gewichtete Prognose, 60-Tage-Projektion, SeasonalEdge Score (5 Faktoren, 0-100) |
| **Strategien** | `pages/9_🚦_...py` | ✅ NEU: Januar Trifecta Ampelsystem (SCR + FFD + JanB), Historische Trefferquote, Kaeppel-Jahresübersicht, Strategie-Bibliothek (65+ filterbar) |

### Adding New Pages

```python
# Neue Seite: pages/4_📈_Weekday_Analyse.py
import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
# ... Fallback ...
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import streamlit as st
from shared.data import download_data, preprocess
from shared.constants import DEFAULT_TICKER, DEFAULT_YEARS

st.set_page_config(page_title="SeasonalEdge - Weekday", page_icon="📈", layout="wide")

def main():
    # Sidebar + Logik + Ausgabe
    pass

if __name__ == "__main__":
    main()
```

### Module Contents

**shared/constants.py:**
- `DEFAULT_TICKER`, `DEFAULT_YEARS`
- `COLOR_*` (alle Farbkonstanten)
- `CYCLE_COLORS`, `DECADE_COLORS`, `DECADE_LABELS`
- `OVERLAY_CONFIGS` (Last Year, Last 5Y, Last 10Y)
- `MONTH_NAMES_DE`
- `PRESSURE_PERIODS`
- `US_WARS` (Liste aller US-Kriege)

**shared/data.py:**
- `download_data(ticker, period="max")` — yfinance + st.cache_data
- `preprocess(df)` — Spalten: return, log_return, day_of_year, year, month

**shared/fed_dates.py:**
- `FOMC_MEETING_DATES` — 224 Termine (2000–2026) als Tupel-Liste
- `get_fomc_dates()` → list of datetime
- `get_fomc_dates_for_years(start, end)` → filtered list

**shared/central_banks.py:**
- `FED_RATE_CHANGES` — 71 Einträge (Hikes + Cuts seit 2000, mit bps + Rate)
- `get_fed_rate_changes(type)` → list of {date, bps, rate}
- `FED_MINUTES_DATES` — 39 Release-Daten
- `ECB_MEETING_DATES` — 96 Termine (2015–2026)
- `BOE_MEETING_DATES` — 58 Termine (2020–2026)
- `BOJ_MEETING_DATES` — 40 Termine (2022–2026)
- `EXTRA_HOLIDAYS` — Chinese New Year, Columbus Day, Jom Kippur
- `get_full_moon_dates(start, end)` → Vollmond-Daten (Meeus-Algorithmus)
- `get_new_moon_dates(start, end)` → Neumond-Daten
- `CENTRAL_BANK_REGISTRY` — Registry aller Event-Quellen

**shared/data.py:**
- `download_data(ticker, period="max")` — yfinance + st.cache_data
- `preprocess(df)` — Spalten: return, log_return, day_of_year, year, month

**shared/calculations.py:**
- `get_presidential_cycle_year(year)` → String
- `get_decade_digit(year)` → int
- `normalize_year(year_df)` → Liste kumulativer Werte (Start=100)
- `interpolate_to_365(days, values)` → 365 Werte
- `build_year_data(df, selected_years)` → dict {year: {days, cumulative, full_365, df}}
- `calculate_seasonal_average(year_data)` → (avg, std)
- `count_trading_days(year_data, start, end)` → int
- `calculate_period_stats(year_data, start, end)` → dict mit win_rate, avg, median, etc.
- `calculate_pressure_curve(df, smoothing)` → (curve, max_years, periods)
- `classify_december_low(df)` → {year: bool}
- `classify_january_first5(df)` → {year: bool}
- `get_war_years()` → set
- `get_peace_years(all_years)` → list
- `analyze_turn_of_month(df, before, after, months, years)` → dict (t0=0% normiert)
- `build_tom_chart(result, ticker, ...)` → plotly Figure

**shared/holidays.py:**
- `HOLIDAY_DEFINITIONS` — 12 NYSE-Feiertage mit calc-Funktion, label, emoji, since
- `get_nyse_holidays(year)` → list of {name, date, label, emoji}
- `analyze_holiday_effect(df, before, after, holidays, years)` → dict (t0=0% normiert)
- `build_holiday_chart(result, ticker, ...)` → plotly Figure
- Interne: `_nth_weekday()`, `_last_weekday()`, `_easter()`, `_apply_weekend_rule()`

**shared/charts.py:**
- `build_seasonal_chart(year_data, avg, std, ticker, ...)` → plotly Figure
  - Parameter: smoothing, show_individual, show_bands, show_current_year,
    selected_range, selected_cycles, selected_decades, indicator_years/label/color,
    pressure_curve, war_years_data/label, df, overlay_options
  - Enthält: Hover-Lookup (CDOY/TDOY/TDOM mit Zukunfts-Projektion),
    Heute-Markierung, Overlay-Linien, dynamische Y-Achse

**shared/strategies/ (✅ NEU — v6.0):**

`shared/strategies/__init__.py`:
- Zentraler Export: `STRATEGIES`, `get_strategies_by_category`, `get_strategies_by_strength`
- Modul-Imports: `januar_trifecta`, `kaeppel`
- Import-Pattern in Pages: `from shared.strategies import januar_trifecta, kaeppel, STRATEGIES`

`shared/strategies/definitions.py`:
- `STRATEGIES` — Liste aller 65+ Strategien als Python-Dicts
  - Felder: name, kategorie, asset, zeitfenster, logik, staerke, quelle, modul, tags
- `KATEGORIEN` — Liste aller Kategorien
- `STAERKEN` — geordnete Stärke-Stufen (gering → hoch)
- `get_strategies_by_category(kategorie)` → gefilterte Liste
- `get_strategies_by_strength(min_staerke)` → gefilterte Liste
- `get_strategies_by_tag(tag)` → gefilterte Liste
- `get_strategies_with_module()` → nur implementierte Strategien

`shared/strategies/januar_trifecta.py`:
- `calculate_trifecta(df, year)` → dict mit signal, farbe, emoji, interpretation, bedingungen
- `check_santa_claus_rally(df, year)` → letzte 5 Dez + erste 2 Jan Handelstage
- `check_first_five_days(df, year)` → erste 5 Jan Handelstage
- `check_january_barometer(df, year)` → gesamter Januar vs. letzter Dez-Close
- `get_ampel_signal(count)` → "Grün" | "Gelb" | "Orange" | "Rot"
- `calculate_trifecta_history(df, start_year, end_year)` → historische DataFrame-Tabelle
- `AMPEL_FARBEN`, `AMPEL_EMOJI` — Farbkonstanten

`shared/strategies/kaeppel.py`:
- `get_holiday_windows(trading_days, holidays, ...)` → 6-Tage-Fenster rund um Feiertage
- `backtest_holiday_system(df, holidays_by_year)` → DataFrame mit Signalen + kumulierten Returns
- `is_kaeppel_long_month(month)` → bool (Nov/Dez/Apr/Jul)
- `get_monthly_seasonal_signal(date)` → aktuelles Long/Flat-Signal
- `backtest_simple_monthly(df)` → Strategie vs. Buy&Hold DataFrame
- `calculate_kti_score(date, df, holidays_by_year, election_year)` → KTI Score 0–5 + Signal
- `get_election_cycle_year(year, last_election_year)` → Zyklus-Jahr 1–4 + Signal
- `check_decennial_5_effect(year)` → Years-Ending-in-5 Check
- `get_kaeppel_year_summary(year)` → Jahres-Übersicht aller Kaeppel-Signale
- `KTI_FARBEN`, `KAEPPEL_LONG_MONATE` — Konstanten

### NYSE Holiday System

12 Feiertage implementiert, alle mit Weekend Rule:

| Feiertag | Regel | Seit |
|----------|-------|------|
| Neujahr | 1. Jan + Weekend Rule | — |
| MLK Day | 3. Montag Jan | 1998 |
| Presidents Day | 3. Montag Feb | — |
| Karfreitag | Ostersonntag - 2 (Gauss) | — |
| Memorial Day | Letzter Montag Mai | — |
| Juneteenth | 19. Jun + Weekend Rule | 2022 |
| Independence Day | 4. Jul + Weekend Rule | — |
| Labor Day | 1. Montag Sep | — |
| Thanksgiving | 4. Donnerstag Nov | — |
| Black Friday | Tag nach Thanksgiving (Early Close) | — |
| Heiligabend | 24. Dez wenn Wochentag (Early Close) | — |
| Weihnachten | 25. Dez + Weekend Rule | — |

### Turn-of-Month & Holiday Normalization

Both use **t0 = 0%** normalization:
```python
# t0 is anchor point (last trading day before event)
raw_curve = 100 * np.exp(cum_log)  # absolute normalized
t0_value = raw_curve[t0_idx]
curve = ((raw_curve / t0_value - 1) * 100).tolist()
# → t0 = 0.00%, values show % change relative to t0
```

### Hover System (Hauptchart)

Shows for each day: Datum, CDOY, TDOY, TDOM.
- Past days: from actual trading data
- Future days: projected (weekends + NYSE holidays excluded)
- Weekends/holidays: show last known value with `*` marker
  │     ├── backtest/stop_loss.py → Stop checks per bar
  │     ├── backtest/position.py  → P&L calculation
  │     └── backtest/metrics.py   → Performance stats
  │
  ├── ai/pattern_matcher.py → Similar years + projection
  ├── ai/scoring.py         → Composite AI score
  ├── ai/commentary.py      → Natural language output
  ├── ai/anomaly.py         → Deviation alerts
  ├── ai/suggestions.py     → Backtest optimization hints
  │
  └── ui/tab_*.py           → Visualization (Plotly charts, tables)
```

### Design Principles

**1. Each module has ONE job:**
- `data/downloader.py` ONLY downloads data. It doesn't calculate returns.
- `indicators/oscillators.py` ONLY calculates oscillator values. It doesn't decide trades.
- `backtest/engine.py` ONLY executes the backtest loop. Metrics are in `metrics.py`.

**2. Modules communicate via DataFrames:**
```python
# data/downloader.py returns:
df  # DatetimeIndex, columns: Open, High, Low, Close, Volume

# data/preprocess.py adds:
df["return"] = df["Close"].pct_change()
df["day_of_year"] = df.index.dayofyear
df["year"] = df.index.year
df["month"] = df.index.month

# analysis/tdom.py adds:
df["tdom"] = ...       # Forward TDoM
df["tdom_reverse"] = ...  # Backward TDoM

# indicators/moving_averages.py adds:
df["sma_200"] = ...

# indicators/oscillators.py adds:
df["rsi_14"] = ...
```

**3. Adding new features = adding new files:**
```python
# Want to add Stochastic oscillator?
# 1. Create indicators/stochastic.py with calculate_stochastic(df, k_period, d_period)
# 2. Add "stochastic" option to indicators/filters.py
# 3. Add UI controls in ui/sidebar.py
# Done — nothing else changes.

# Want to add a new stop-loss type (e.g., Chandelier Exit)?
# 1. Add calculate_chandelier_stop() to backtest/stop_loss.py
# 2. Add "chandelier" to BacktestConfig.stop_loss_type options
# 3. Add UI control in sidebar
# Done — engine.py already calls check_stop_loss() generically.
```

**4. UI modules never contain business logic:**
```python
# ui/tab_tdom.py:
# ✅ CORRECT:
from analysis.tdom import build_tdom_heatmap
stats = build_tdom_heatmap(df, strategy)
fig = create_tdom_bar_chart(stats)  # from ui/charts.py
st.plotly_chart(fig)

# ❌ WRONG:
# Don't calculate TDoM stats inside the UI tab file
df["strat_return"] = (df["Close"] - df["Open"]) / df["Open"] * 100  # NO!
```

---

## Deployment Checklist

### Pre-Deploy
- [ ] Change default password in auth section
- [ ] Test all features locally
- [ ] requirements.txt includes all packages
- [ ] No absolute file paths in code
- [ ] Remove debug prints/comments

### Files Needed
```
seasonal_app.py                    ← Startseite / Dashboard
shared/
  __init__.py
  constants.py                     ← Farben, Labels, US_WARS
  data.py                          ← download_data, preprocess
  calculations.py                  ← Saisonale Analyse, Pressure, Indikatoren, ToM
  holidays.py                      ← NYSE-Feiertage (12) + Analyse
  charts.py                        ← Hauptchart-Builder (Saisonalchart)
  fed_dates.py                     ← FOMC Meeting Dates (224 Termine)
  central_banks.py                 ← ECB/BOE/BOJ + Fed Rates/Minutes + Mond + Extra-Feiertage
pages/
  1_📊_Erweiterte_Analyse.py
  2_🔄_Turn_of_the_Month.py
  3_📅_Feiertags_Effekt.py
  4_📅_Weekday_Analyse.py
  5_📆_Monthly_Performance.py
  6_🏛️_Zentralbanken.py
  7_🌕_Mondphasen.py
  8_🧠_TruePath.py
requirements.txt                   ← Dependencies
```

### Dependencies (requirements.txt)
```
streamlit
yfinance
pandas
numpy
plotly
scipy
```

### Streamlit Cloud Settings
```
Python version: 3.11
Advanced:
  - Increase memory if needed (Settings → Resources)
  - Add secrets for API keys (Settings → Secrets)
```

---

## Future Enhancements Roadmap

### Phase 1 (Complete)
- [x] Basic seasonal charts
- [x] Presidential cycle filter
- [x] Monthly heatmap
- [x] Smoothing & confidence bands
- [x] Future projection

### Phase 2 (Complete)
- [x] TDoM analysis (forward + backward counting)
- [x] Three strategy variants (O→C, O→O, C→C)
- [x] Multi-day TDoM ranges
- [x] Backtesting engine with stop-losses (fixed, trailing, ATR, break-even, time)
- [x] TradingView-compatible metrics
- [x] Trade filters (month, presidential cycle, lookback, SMA, RSI, AND/OR)

### Phase 3 (Complete — AI Features)
- [x] Pattern matcher (DTW) with weighted projection
- [x] Multi-factor SeasonalEdge Score (5 factors, 0-100)
- [x] Natural language commentary generation
- [x] Anomaly detection & alerts (z-score based)
- [x] Smart backtest suggestions

### Phase 4 (Complete — Multipage & New Features)
- [x] **Multipage-Architektur** (Streamlit pages/ Ordner)
- [x] **Dashboard** (clean Startseite mit Saisonalchart)
- [x] **Erweiterte Analyse** (Zyklen, Pressure, War, Indikatoren)
- [x] **Turn-of-the-Month Effekt** (t-y/t+x Slider, t0=0% Normierung, Detailtabellen)
- [x] **Feiertags-Effekt** (12 NYSE-Feiertage, Weekend Rule, Early Closings)
- [x] **Heute-Markierung** im Saisonalchart (CDOY, TDOY, TDOM)
- [x] **Hover-System** mit Datum/CDOY/TDOY/TDOM (inkl. Zukunfts-Projektion)
- [x] **Overlay-Linien** (Last Year, Last 5 Years, Last 10 Years)
- [x] **Dekadenzyklus** (X0er bis X9er Jahre)
- [x] **Pressure Chart** als sekundäre Y-Achse
- [x] **Krieg/Frieden-Overlay** (US-Kriegsjahre vs. Friedensjahre)
- [x] **shared/ Module** (constants, data, calculations, holidays, charts)

### Phase 5 (Complete — Erweiterte Pages & KI)
- [x] **Weekday-Analyse** (4 Rendite-Modi, SMA/RSI Filter, Heatmap Monat×Wochentag)
- [x] **Monthly Performance** (Intra-Monat TDOM-Chart, Wochen, Two-Week 1st/2nd, Detrend-Indikator, Presidential Cycle Filter)
- [x] **Zentralbank-Page** (Fed/ECB/BOE/BOJ kombinierbar, Rate Hikes/Cuts, Minutes, nächste Termine)
- [x] **Mondphasen-Page** (Vollmond/Neumond-Effekt, 334+ Events, Meeus-Algorithmus)
- [x] **TruePath** (KI-Pattern-Matching: Korrelation + Euklidisch, gewichtete Prognose, 60T Projektion)
- [x] **SeasonalEdge Score** (5-Faktor Ensemble: Saisonalität, TruePath, Zyklus, Konsistenz, Position)
- [x] **Zentralbank-Daten** (Fed 224 Meetings, 71 Rate Changes, ECB 96, BOE 58, BOJ 40, Minutes 39)
- [x] **Zusatz-Feiertage** (Chinese New Year, Columbus Day, Jom Kippur)
- [x] **Mond-Daten** (Vollmond + Neumond 1990–2030, ~668 Events)

### Phase 6 (In Progress)
- [x] **shared/strategies/ Modul** (65+ Strategien-Datenbank, Januar Trifecta, Kaeppel)
- [x] **Strategien-Page** `9_🚦_Strategien.py` (Trifecta Ampel, Bibliothek filterbar)
- [ ] **OPEX / Verfallstage** als eigene Seite
- [ ] **TDOM-Strategie** Backtesting
- [ ] **Outlier Management** (Winsorize 3σ, Exclude Years Widget)
- [ ] **Anomaly Detection Page** (z-Score Alerts, Pattern Break Warnings)
- [ ] VIX regime integration
- [ ] Sentiment integration (Fear & Greed Index)

### Phase 7 (Advanced)
- [ ] Portfolio optimizer (multi-ticker seasonal allocation)
- [ ] Walk-forward optimization (in-sample / out-of-sample)
- [ ] Monte Carlo simulation for drawdown estimation
- [ ] Export to TradingView Pine Script

### Phase 7 (Premium / SaaS)
- [ ] Custom domain
- [ ] Payment integration (Stripe)
- [ ] User accounts & saved configs
- [ ] Mobile-optimized layout
- [ ] API access (REST endpoints)
- [ ] Real-time alerts via email/Telegram

---

## Domain Knowledge: Trading Concepts

### Seasonality Types
1. **Calendar Effects**: January Effect, Sell in May
2. **Event-Driven**: OPEX, Earnings Season, Fed Meetings
3. **Political**: Presidential Cycle, Election Years
4. **Economic**: Tax Season, Pension Rebalancing

### Key Periods (SPY)
- **January Rally**: Days 2-31 (Post-tax selling)
- **Sell in May**: Days 121-151 (Weak summer)
- **Fall Rally**: Days 274-334 (Q4 strength)
- **Santa Rally**: Days 335-365 (Year-end optimism)

### Presidential Cycle Pattern
- **Year 1**: Post-election uncertainty (weakest)
- **Year 2**: Midterm election volatility
- **Year 3**: Pre-election stimulus (strongest)
- **Year 4**: Election year (mixed, volatile)

### TDoM Edge Patterns (SPY Historical)
- **TDoM 1**: Tends positive (new month inflows, pension buying)
- **TDoM -1**: Tends positive (window dressing, month-end rebalancing)
- **TDoM -2 to -1**: "Turn of the Month" effect (strongest 2-day window)
- **TDoM 2-3**: Often mean-reverts after TDoM 1 strength
- **TDoM ~10-12**: Mid-month weakness common (options-related flows)
- **TDoM ~15**: Options expiration week effects (3rd Friday proximity)

---

## Performance Optimization

### For Large Datasets
```python
# Use vectorization over loops:
# ❌ Slow:
for i in range(len(df)):
    result.append(df.iloc[i]['close'] - df.iloc[i-1]['close'])

# ✅ Fast:
result = df['close'].diff()

# Cache expensive calculations:
@st.cache_data
def normalize_years(years_data):
    # Expensive calculation here
    return normalized_data
```

### Chart Rendering
```python
# Limit individual years shown:
recent_years = available_years[-10:]  # Last 10 only

# Use plotly efficiently:
# Show presidential cycles only if selected
if selected_cycles:
    # Plot cycle averages
```

### Backtest Performance
```python
# Cache backtest results:
@st.cache_data
def cached_backtest(ticker, config_hash):
    """Cache keyed on ticker + config hash to avoid rerunning."""
    return run_backtest(df, config)

# Vectorize where possible:
# Instead of row-by-row stop checks, pre-compute cumulative highs/lows
df["cum_high"] = df.groupby(["year", "month"])["High"].cummax()
df["cum_low"] = df.groupby(["year", "month"])["Low"].cummin()
```

---

## Testing Patterns

### Manual Test Checklist
- [ ] Test with different tickers (SPY, QQQ, IWM)
- [ ] Test with different year ranges (5, 10, 20)
- [ ] Test each date selection mode
- [ ] Test all preset buttons
- [ ] Test presidential cycle filters
- [ ] Test on mobile (responsive?)
- [ ] Test password protection

### TDoM-Specific Tests
- [ ] TDoM 1 forward matches first trading day of each month
- [ ] TDoM -1 backward matches last trading day of each month
- [ ] Months with 19, 20, 21, 22, 23 trading days handled correctly
- [ ] All three strategy variants produce different results
- [ ] Multi-day range (TDoM 1 → 5) calculates correct holding period
- [ ] Stop-loss triggers correctly on gap days
- [ ] Trailing stop only moves in favorable direction
- [ ] Break-even stop activates at correct threshold
- [ ] ATR stop adapts to volatility
- [ ] Commission and slippage deducted correctly
- [ ] Short trades calculate P&L with inverted direction
- [ ] Futures contract multiplier applied correctly
- [ ] Crypto data includes weekends (7-day trading)

### Filter-Specific Tests
- [ ] Month filter: selecting Jan only → trades only in January
- [ ] Month filter: multi-select (Jan+Feb+Mar) → trades only in Q1
- [ ] Month filter: empty/None → all months included
- [ ] Presidential cycle: Year 3 only → only pre-election years
- [ ] Presidential cycle: multiple selection works (Year 1 + Year 3)
- [ ] Lookback "Last 10 years" correctly sets start_year
- [ ] SMA filter: "above 200 SMA" blocks trades when price is below
- [ ] SMA filter: first ~200 bars skipped (not enough data for SMA)
- [ ] SMA filter: "below" mode works for mean-reversion setups
- [ ] RSI filter: "below 30" only takes trades when RSI < 30
- [ ] RSI filter: "above 70" only takes trades when RSI > 70
- [ ] RSI: first ~14 bars skipped (not enough data)
- [ ] Combined AND: both SMA + RSI must pass to take trade
- [ ] Combined OR: either SMA or RSI passing allows trade
- [ ] Filter analysis tab shows correct taken/skipped count
- [ ] Filters with strict settings reduce trade count significantly
- [ ] No filters → same result as previous version (backward compatibility)

### Edge Cases
- [ ] Invalid ticker symbol
- [ ] No data for selected period
- [ ] Single year available only
- [ ] Leap years (Feb 29)
- [ ] Year-end transitions
- [ ] TDoM 23 with very few data points (display warning)
- [ ] Stop-loss triggered on entry bar (should not happen)
- [ ] Month has fewer trading days than requested TDoM
- [ ] Crypto: weekends are trading days (different TDoM count)
- [ ] Time stop fires before TDoM exit (time stop wins)
- [ ] Time stop fires same bar as price stop (price stop takes priority)
- [ ] Time stop with bars=1 acts as forced intraday exit

### AI Feature Tests
- [ ] DTW pattern matcher returns different results for different years
- [ ] Similarity scores are 0-100 range, sorted descending
- [ ] Projection from matches produces valid forward curve
- [ ] SeasonalEdge Score is 0-100 and factors sum weights = 1.0
- [ ] Score interpretation labels match score ranges
- [ ] Commentary generates readable text without errors
- [ ] Anomaly detector triggers on 2σ+ deviations
- [ ] Anomaly detector does NOT trigger on normal days
- [ ] Smart suggestions change based on backtest results
- [ ] VIX data fallback (realized vol) works when ^VIX unavailable

---

## Code Style Guidelines

### Naming Conventions
```python
# Variables: snake_case
start_day, end_day, avg_cumulative

# Functions: snake_case with verbs
def calculate_stats(...):
def get_presidential_cycle(...):
def assign_tdom(...):
def run_backtest(...):

# Constants: UPPER_CASE
SMOOTHING_WINDOW = 5
DEFAULT_TICKER = "SPY"
INSTRUMENT_PRESETS = {...}

# Classes: PascalCase
class SeasonalPattern:
class BacktestConfig:
class BacktestResult:
```

### Comments
```python
# ── Section Headers ────────────────────────────────────────
# Use this style for major sections

# Inline comments for clarity:
cum_return += daily_ret * 100  # Scale to percentage

# Docstrings for functions:
def count_trading_days(start, end):
    """
    Count average trading days across all available years.
    
    Args:
        start (int): Start day of year (1-365)
        end (int): End day of year (1-365)
    
    Returns:
        int: Average number of trading days in period
    """
```

---

## Resources & References

### Key Libraries
- **yfinance**: Market data retrieval
- **pandas**: Data manipulation
- **plotly**: Interactive charts
- **streamlit**: Web framework
- **numpy**: Numerical operations
- **scikit-learn**: ML algorithms (for AI features)
- **fastdtw**: Dynamic Time Warping for pattern matching
- **scipy**: Distance metrics for DTW

### External Resources
- Seasonax.com: Pattern visualization inspiration
- TradingView: Pine Script methodology (avoid their method!)
- StockCharts.com: Seasonal screener concepts

### Internal Documentation
- `DEPLOYMENT_GUIDE.md`: Streamlit Cloud deployment
- `requirements.txt`: Python dependencies
- `README.md`: Project overview

---

## Contact & Updates

**Skill Maintainer:** Claude + Heiko  
**Last Updated:** 2026-03-10  
**Version:** 6.0  

**Changelog:**
- v6.0: shared/strategies/ Untermodul (definitions.py mit 65+ Strategien, januar_trifecta.py Ampelsystem, kaeppel.py KTI+Holiday+Election+Decennial), neue Page 9_🚦_Strategien.py
- v5.0: Weekday-Analyse (4 Modi + Filter), Monthly Performance (Detrend, Two-Week, Presidential Filter), Zentralbanken-Page (Fed/ECB/BOE/BOJ), Mondphasen-Page, TruePath (KI-Pattern-Matching + SeasonalEdge Score), Datentabellen (Fed Rates, Minutes, ECB, BOE, BOJ, Mond, Extra-Feiertage)
- v4.0: Multipage-Architektur, Turn-of-Month, Feiertags-Effekt, Hover-System, Overlays, sys.path Fix
- v3.0: AI features (DTW, scoring, commentary, anomaly detection, smart suggestions)
- v2.0: TDoM system, backtesting engine, stop-loss variants
- v1.0: Initial skill with seasonal charts, presidential cycle, heatmap

**Known Plotly Issue:** Neuere Plotly-Versionen akzeptieren `titlefont` NICHT als direkte Property. IMMER verwenden: `title=dict(text="...", font=dict(...))` statt `title="...", titlefont=dict(...)`. Betrifft yaxis, yaxis2, colorbar.

**Update this skill when:**
- New major features added
- Bugs discovered and fixed
- Methodology changes
- Performance patterns identified
