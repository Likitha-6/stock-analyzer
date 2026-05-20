"""
common.finance - Financial data helpers for Indian Stock Analyzer
"""

from __future__ import annotations
from typing import Optional
import numpy as np
import pandas as pd
import streamlit as st

@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _fetch_core_metrics(symbol: str) -> dict:
    """Fetch metrics from local database"""
    try:
        from .sql import load_master
        
        master_df = load_master()
        stock = master_df[master_df["Symbol"] == symbol]
        
        if stock.empty:
            return {}
        
        row = stock.iloc[0]
        
        # Get price from database
        price = None
        try:
            price = float(row.get("Price"))
        except:
            price = None
        
        return {
            "PE Ratio": row.get("PE Ratio"),
            "EPS": row.get("EPS"),
            "Profit Margin": row.get("ProfitMargin"),
            "ROE": row.get("ROE"),
            "Debt to Equity": row.get("DebtToEquity"),
            "Dividend Yield": None,
            "Free Cash Flow": None,
            "_company": row.get("CompanyName"),
            "_sector": row.get("Big_Sectors"),
            "_market_cap": row.get("MarketCap"),
            "_price": price,
        }
    except Exception as e:
        return {}

@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def get_industry_averages(industry, master_df, max_peers=None):
    """Get median metrics for industry peers"""
    peer_syms = (
        master_df.loc[master_df["Industry"] == industry, "Symbol"]
        .head(max_peers).tolist()
    )
    
    metric_keys = ["PE Ratio", "EPS", "Profit Margin", "ROE", "Debt to Equity", "Dividend Yield", "Free Cash Flow"]
    buckets = {m: [] for m in metric_keys}

    for sym in peer_syms:
        try:
            result = _fetch_core_metrics(sym)
            if not result:
                continue
            
            for m, v in result.items():
                if m.startswith("_"):
                    continue
                if v is not None and isinstance(v, (int, float)) and np.isfinite(v):
                    buckets[m].append(float(v))
        except Exception:
            continue

    return {m: (None if not vals else round(float(np.median(vals)), 2)) for m, vals in buckets.items()}

def get_stock_description(symbol: str) -> str:
    """Get company description from database"""
    try:
        from .sql import load_master
        master_df = load_master()
        stock = master_df[master_df["Symbol"] == symbol]
        
        if stock.empty:
            return "No description available."
        
        desc = stock.iloc[0].get("Description")
        if desc and desc != "N/A" and desc:
            return str(desc)
        
        return "No description available."
    except Exception:
        return "Description could not be fetched."

def market_cap_label(mc):
    """Classify stock by market cap"""
    if mc is None:
        return "N/A"
    if mc >= 2_000_000_000_000:
        return "Mega Cap"
    if mc >= 200_000_000_000:
        return "Large Cap"
    if mc >= 50_000_000_000:
        return "Mid Cap"
    if mc >= 5_000_000_000:
        return "Small Cap"
    return "Micro Cap"

def human_market_cap(mc: Optional[float]) -> str:
    """Pretty-print market cap"""
    if mc is None:
        return "N/A"
    if mc >= 1e12:
        return f"{mc / 1e12:.2f} T"
    if mc >= 1e9:
        return f"{mc / 1e9:.2f} B"
    if mc >= 1e6:
        return f"{mc / 1e6:.2f} M"
    return f"{mc:.0f}"

def val_with_ind_avg(metric: str, raw_val: Optional[float], ind_avg: Optional[float]) -> str:
    """Format metric with industry average"""
    if raw_val is None:
        return "N/A"

    if metric == "Debt to Equity":
        raw_val /= 100
        ind_avg = ind_avg / 100 if ind_avg is not None else None
    elif metric == "Free Cash Flow":
        raw_val /= 1e7
        ind_avg = ind_avg / 1e7 if ind_avg is not None else None
    elif metric in ("Profit Margin", "ROE"):
        raw_val *= 100
        ind_avg = ind_avg * 100 if ind_avg is not None else None

    base = f"{raw_val:.2f}"
    avg = f"{ind_avg:.2f}" if ind_avg is not None else "N/A"
    return f"{base} (Ind Avg: {avg})"

def interpret(metric: str, value: Optional[float], ind_avg: Optional[float]) -> str:
    """Return signal: ✅/🟡/🔴"""
    if (
        value is None
        or ind_avg is None
        or not isinstance(value, (int, float))
        or not isinstance(ind_avg, (int, float))
        or not np.isfinite(value)
        or not np.isfinite(ind_avg)
    ):
        return ""

    if metric == "Free Cash Flow":
        value /= 1e7
        ind_avg /= 1e7
    elif metric in ("Profit Margin", "ROE"):
        value *= 100
        ind_avg *= 100
    elif metric == "Debt to Equity":
        value /= 100
        ind_avg /= 100

    if ind_avg == 0:
        return ""

    delta_pct = (value - ind_avg) / abs(ind_avg) * 100
    lower_is_better = metric in ("Debt to Equity", "PE Ratio")

    if lower_is_better:
        if delta_pct <= 0:
            return "✅"
        if delta_pct >= 10:
            return "🔴"
        return "🟡"
    else:
        if delta_pct >= 0:
            return "✅"
        if delta_pct <= -10:
            return "🔴"
        return "🟡"
