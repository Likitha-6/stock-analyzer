# File: common/scoring.py

```python
import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------


def normalize_score(value, min_val, max_val):
    """
    Normalize any metric into 0–100 score.
    """

    if pd.isna(value):
        return 0

    value = max(min(value, max_val), min_val)

    return ((value - min_val) / (max_val - min_val)) * 100


# --------------------------------------------------
# Revenue Growth Score
# --------------------------------------------------


def revenue_growth_score(revenue_growth):
    return normalize_score(revenue_growth, -10, 40)


# --------------------------------------------------
# EPS Growth Score
# --------------------------------------------------


def eps_growth_score(eps_growth):
    return normalize_score(eps_growth, -10, 50)


# --------------------------------------------------
# ROE Score
# --------------------------------------------------


def roe_score(roe):
    return normalize_score(roe, 0, 30)


# --------------------------------------------------
# Debt Score
# Lower debt = better
# --------------------------------------------------


def debt_score(debt_equity):

    if pd.isna(debt_equity):
        return 50

    if debt_equity <= 0:
        return 100

    score = 100 - normalize_score(debt_equity, 0, 2)

    return max(score, 0)


# --------------------------------------------------
# RSI Score
# Sweet spot = 55–75
# --------------------------------------------------


def rsi_score(rsi):

    if pd.isna(rsi):
        return 0

    if 55 <= rsi <= 75:
        return 100

    if rsi < 55:
        return normalize_score(rsi, 20, 55)

    return 100 - normalize_score(rsi, 75, 90)


# --------------------------------------------------
# PE Valuation Score
# Lower PE compared to industry is better
# --------------------------------------------------


def valuation_score(stock_pe, industry_pe):

    if pd.isna(stock_pe) or pd.isna(industry_pe):
        return 50

    diff = industry_pe - stock_pe

    return normalize_score(diff, -30, 30)


# --------------------------------------------------
# Volume Expansion Score
# --------------------------------------------------


def volume_score(current_volume, avg_volume):

    if avg_volume == 0 or pd.isna(avg_volume):
        return 0

    ratio = current_volume / avg_volume

    return normalize_score(ratio, 0.5, 3)


# --------------------------------------------------
# Relative Strength Score
# --------------------------------------------------


def relative_strength_score(stock_return, nifty_return):

    rs = stock_return - nifty_return

    return normalize_score(rs, -20, 40)


# --------------------------------------------------
# Calculate RSI from price data
# --------------------------------------------------


def calculate_rsi(symbol):

    try:
        ticker = yf.Ticker(symbol)

        hist = ticker.history(period="6mo")

        if hist.empty:
            return np.nan

        rsi = RSIIndicator(close=hist["Close"], window=14).rsi()

        return round(rsi.iloc[-1], 2)

    except Exception:
        return np.nan


# --------------------------------------------------
# Master Stock Score
# --------------------------------------------------


def calculate_stock_score(row, nifty_return=0):

    revenue_score = revenue_growth_score(
        row.get("Revenue Growth", 0)
    )

    eps_score = eps_growth_score(
        row.get("EPS Growth", 0)
    )

    roe_val = row.get("ROE", 0)
    roe_sc = roe_score(roe_val)

    debt_sc = debt_score(
        row.get("Debt To Equity", 0)
    )

    rsi_sc = rsi_score(
        row.get("RSI", 50)
    )

    val_sc = valuation_score(
        row.get("PE Ratio", 0),
        row.get("Industry PE", 0)
    )

    vol_sc = volume_score(
        row.get("Current Volume", 0),
        row.get("Average Volume", 1)
    )

    rs_sc = relative_strength_score(
        row.get("3M Return", 0),
        nifty_return
    )

    # --------------------------------------------
    # Final Weighted Score
    # --------------------------------------------

    final_score = (
        revenue_score * 0.20 +
        eps_score * 0.20 +
        roe_sc * 0.15 +
        debt_sc * 0.10 +
        rsi_sc * 0.10 +
        val_sc * 0.10 +
        vol_sc * 0.05 +
        rs_sc * 0.10
    )

    return round(final_score, 2)


# --------------------------------------------------
# Rank Entire Market
# --------------------------------------------------


def rank_market(df, nifty_return=0):

    df = df.copy()

    df["Stock Score"] = df.apply(
        lambda row: calculate_stock_score(
            row,
            nifty_return=nifty_return
        ),
        axis=1
    )

    df = df.sort_values(
        by="Stock Score",
        ascending=False
    )

    return df
```

---

# STEP 1 — Install Dependency

Add to `requirements.txt`

```text
ta
```

---

# STEP 2 — Example Usage

Inside:

`pages/5_Market_Opportunities.py`

```python
from common.scoring import rank_market

ranked_df = rank_market(df)

st.dataframe(
    ranked_df[[
        "Symbol",
        "Stock Score",
        "ROE",
        "PE Ratio",
        "RSI"
    ]].head(25)
)
```

---

# STEP 3 — Recommended Next Improvements

After this works:

1. Add sector strength score
2. Add breakout detection
3. Add watchlist generation
4. Add relative strength ranking
5. Add market breadth

---

# IMPORTANT NOTE

Your column names may differ.

You should align these fields with your actual dataframe columns:

```python
"Revenue Growth"
"EPS Growth"
"ROE"
"Debt To Equity"
"PE Ratio"
"Industry PE"
"Current Volume"
"Average Volume"
"3M Return"
```

We can map those next directly from your existing data structure.
