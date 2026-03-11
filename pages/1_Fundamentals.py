import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

from common.sql import load_master
from common.data import load_name_lookup
from common.finance import (
    _fetch_core_metrics, get_industry_averages,
    val_with_ind_avg, interpret, human_market_cap, market_cap_label,
    get_stock_description,
)
from common.charts import _price_chart, _rev_pm_fcf_frames

st.set_page_config(
    page_title="Fundamentals",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

/* Reset Streamlit's injected paragraph/div sizes inside markdown blocks */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] div,
[data-testid="stMarkdownContainer"] span { font-size: inherit !important; }

.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.0rem !important; font-weight: 800;
    color: #f0f4ff; letter-spacing: -0.02em; margin-bottom: 0.2rem;
}
.page-sub {
    font-size: 0.78rem !important; color: #8aaac8;
    margin-bottom: 1.6rem; letter-spacing: 0.05em;
}
.section-label {
    font-size: 0.68rem !important; letter-spacing: 0.18em;
    text-transform: uppercase; color: #8aaac8;
    border-left: 3px solid #00c882; padding-left: 0.6rem;
    margin-bottom: 0.8rem; margin-top: 1.6rem;
}
.hero-card {
    background: linear-gradient(135deg, #0d1e35 0%, #0a1628 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 1.6rem 2rem;
    margin-bottom: 1.6rem; position: relative; overflow: hidden;
}
.hero-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #00c882, #6ec6ff, transparent);
}
.hero-company {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem !important; font-weight: 800;
    color: #f0f4ff; line-height: 1.1; margin-bottom: 0.3rem;
}
.hero-symbol {
    display: inline-block;
    background: rgba(0,200,130,0.12);
    border: 1px solid rgba(0,200,130,0.3);
    border-radius: 6px; padding: 0.15rem 0.6rem;
    font-size: 0.78rem !important; font-weight: 700;
    color: #00c882; letter-spacing: 0.08em; margin-right: 0.5rem;
}
.hero-tag {
    display: inline-block;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px; padding: 0.15rem 0.6rem;
    font-size: 0.68rem !important; color: #8aaac8;
    margin-right: 0.4rem; margin-top: 0.4rem;
}
.price-strip {
    display: flex; flex-wrap: wrap; gap: 0.5rem;
    align-items: center; margin-top: 0.9rem;
}
.price-chip {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px; padding: 0.35rem 0.9rem;
    display: flex; align-items: center; gap: 0.5rem;
    white-space: nowrap;
}
.price-chip-label {
    font-size: 0.68rem !important; letter-spacing: 0.1em;
    text-transform: uppercase; color: #8aaac8;
}
.price-chip-value {
    font-family: 'Syne', sans-serif;
    font-size:0.78rem !important; font-weight: 700; color: #f0f4ff;
}

.metric-card {
    background: #0d1628;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 1.1rem 1.3rem;
    height: 100%; position: relative; overflow: hidden;
}
.metric-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
}
.metric-card.green::before  { background: #00c882; }
.metric-card.yellow::before { background: #f5a623; }
.metric-card.red::before    { background: #ff4d6a; }
.metric-card.grey::before   { background: rgba(255,255,255,0.15); }
.metric-name {
    font-size: 0.68rem !important; letter-spacing: 0.12em;
    text-transform: uppercase; color: #8aaac8; margin-bottom: 0.5rem;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem !important; font-weight: 700; color: #f0f4ff; line-height: 1;
}
.metric-avg  { font-size: 0.68rem !important; color: #8aaac8; margin-top: 0.3rem; }
.metric-signal { font-size:0.78rem !important; position: absolute; top: 1rem; right: 1rem; }

.signal-bar {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 0.9rem 1.4rem;
    display: flex; align-items: center; gap: 1.2rem;
    margin-bottom: 1.4rem; flex-wrap: wrap;
}
.sig-count {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem !important; font-weight: 700;
}
.sig-label { font-size: 0.68rem !important; color: #8aaac8; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">📊 Fundamentals</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">// Search a stock · analyse fundamentals · compare vs industry</div>', unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
master_df = load_master()
name_df   = load_name_lookup()

if "Description" not in master_df.columns:
    master_df = pd.merge(
        master_df, name_df[["Symbol", "Description"]],
        on="Symbol", how="left", validate="1:1",
    )

# ── Search bar ────────────────────────────────────────────────────────────────
chosen_sym = None
default_sym = st.session_state.get("compare_symbol")

if default_sym and not st.session_state.get("already_loaded_from_sector"):
    chosen_sym = default_sym
    st.session_state["already_loaded_from_sector"] = True
    st.session_state["compare_symbol"] = None
else:
    query = st.text_input(
        "🔍  Search by symbol or company name",
        placeholder="e.g. RELIANCE or Tata Consultancy...",
    ).strip()
    if query:
        mask = (
            name_df["Symbol"].str.contains(query, case=False, na=False) |
            name_df["Company Name"].str.contains(query, case=False, na=False)
        )
        matches = name_df[mask]
        if matches.empty:
            st.warning("No match found.")
        else:
            opts = matches.apply(lambda r: r["Symbol"] + " – " + r["Company Name"], axis=1)
            sel  = st.selectbox("Select company", opts.tolist(), label_visibility="collapsed")
            chosen_sym = sel.split(" – ")[0]

if not chosen_sym:
    st.stop()

# ── Fetch data ────────────────────────────────────────────────────────────────
with st.spinner("Loading..."):
    data = _fetch_core_metrics(chosen_sym)

    # Fill missing from DB
    db_row = master_df[master_df["Symbol"] == chosen_sym]
    if not db_row.empty:
        db = db_row.iloc[0]
        _db_map = {
            "ROE":            ("ROE",          1.0),
            "Profit Margin":  ("ProfitMargin", 1.0),
            "PE Ratio":       ("PE Ratio",     1.0),
            "EPS":            ("EPS",          1.0),
            "Debt to Equity": ("DebtToEquity", 1.0),
        }
        for metric, (db_col, scale) in _db_map.items():
            if data.get(metric) is None and db_col in db.index and pd.notna(db[db_col]):
                try:
                    data[metric] = float(db[db_col]) * scale
                except (ValueError, TypeError):
                    pass

    db_row_data = db_row.iloc[0] if not db_row.empty else None
    industry  = db_row_data["Industry"]  if db_row_data is not None else "N/A"
    sector    = db_row_data["Big Sectors"] if db_row_data is not None else data.get("_sector", "N/A")
    company   = data.get("_company") or (db_row_data["Company Name"] if db_row_data is not None else chosen_sym)
    ind_avg   = get_industry_averages(industry, master_df)

    # Price + ATH
    price = data.get("_price")
    try:
        hist = yf.Ticker(chosen_sym + ".NS").history("max", auto_adjust=True)
        ath  = float(hist["Close"].max()) if not hist.empty else None
    except Exception:
        ath = None
    pct_from_ath = ((price - ath) / ath * 100) if price and ath else None

# ── Hero strip ────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-card">', unsafe_allow_html=True)

left_col, right_col = st.columns([3, 2])
with left_col:
    st.markdown(
        '<div class="hero-company">' + company + '</div>'
        '<div style="margin-top:0.5rem;">'
        '<span class="hero-symbol">' + chosen_sym + '</span>'
        '<span class="hero-tag">📂 ' + str(sector) + '</span>'
        '<span class="hero-tag">🏭 ' + str(industry) + '</span>'
        '<span class="hero-tag">📊 ' + market_cap_label(data.get("_market_cap")) + '</span>'
        '</div>',
        unsafe_allow_html=True
    )
    desc = get_stock_description(chosen_sym)
    if desc and desc != "N/A":
        short = desc[:180] + "..." if len(desc) > 180 else desc
        st.markdown(
            '<div style="font-size:0.78rem !important;color:#8aaac8;margin-top:0.8rem;line-height:1.5;">' + short + '</div>',
            unsafe_allow_html=True
        )

with right_col:
    price_str = ("Rs." + str(round(price, 2))) if price else "N/A"
    ath_str   = ("Rs." + str(round(ath,   2))) if ath   else "N/A"
    if pct_from_ath is not None:
        pct_clr = "#00c882" if pct_from_ath >= 0 else "#ff4d6a"
        arrow   = "▲" if pct_from_ath >= 0 else "▼"
        pct_str = arrow + " " + str(round(abs(pct_from_ath), 1)) + "% from ATH"
    else:
        pct_clr = "#8aaac8"; pct_str = "N/A"

    st.markdown(
        '<div class="price-strip">'
        '<div class="price-chip">'
        '<span class="price-chip-label">Price</span>'
        '<span class="price-chip-value">' + price_str + '</span>'
        '</div>'
        '<div class="price-chip">'
        '<span class="price-chip-label">ATH</span>'
        '<span class="price-chip-value">' + ath_str + '</span>'
        '</div>'
        '<div class="price-chip">'
        '<span class="price-chip-label">vs ATH</span>'
        '<span class="price-chip-value" style="color:' + pct_clr + ';">' + pct_str + '</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

st.markdown('</div>', unsafe_allow_html=True)

# ── Signal summary bar ────────────────────────────────────────────────────────
METRICS = [
    ("PE Ratio",       "PE Ratio",      "pe"),
    ("EPS",            "EPS",           "eps"),
    ("Profit Margin",  "ProfitMargin",  "pm"),
    ("ROE",            "ROE",           "roe"),
    ("Debt to Equity", "DebtToEquity",  "de"),
    ("Dividend Yield", "Dividend Yield","dy"),
    ("Free Cash Flow", "Free Cash Flow","fcf"),
]

signals = [interpret(m, data.get(m), ind_avg.get(m)) for m, _, _ in METRICS]
green  = signals.count("✅")
yellow = signals.count("🟡")
red    = signals.count("🔴")

st.markdown('<div class="section-label">// signal summary</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="signal-bar">'
    '<div><div class="sig-count" style="color:#00c882;">' + str(green) + ' ✅</div><div class="sig-label">Strong</div></div>'
    '<div><div class="sig-count" style="color:#f5a623;">' + str(yellow) + ' 🟡</div><div class="sig-label">Neutral</div></div>'
    '<div><div class="sig-count" style="color:#ff4d6a;">' + str(red) + ' 🔴</div><div class="sig-label">Weak</div></div>'
    '<div style="flex:1;"></div>'
    '<div style="font-size:0.68rem !important;color:#8aaac8;">vs ' + str(industry) + ' industry average</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── Metric cards ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">// key metrics</div>', unsafe_allow_html=True)

METRIC_DISPLAY = [
    ("PE Ratio",       "PE Ratio",       None),
    ("EPS",            "EPS",            "Rs."),
    ("ROE",            "ROE",            None),
    ("Profit Margin",  "Profit Margin",  None),
    ("Debt to Equity", "Debt to Equity", None),
    ("Dividend Yield", "Dividend Yield", None),
    ("Free Cash Flow", "Free Cash Flow", None),
]

def _display_val(metric, raw):
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return "N/A", "N/A"
    if metric == "Debt to Equity":
        v = raw / 100
        return str(round(v, 2)) + "x", str(round(v, 2)) + "x"
    if metric in ("Profit Margin", "ROE"):
        v = raw * 100
        return str(round(v, 1)) + "%", str(round(v, 1)) + "%"
    if metric == "Free Cash Flow":
        v = raw / 1e7
        return "Rs." + str(round(v, 0)) + " Cr", str(round(v, 0))
    if metric == "Dividend Yield":
        v = raw * 100 if raw < 1 else raw
        return str(round(v, 2)) + "%", str(round(v, 2)) + "%"
    if metric == "EPS":
        return "Rs." + str(round(raw, 2)), str(round(raw, 2))
    return str(round(raw, 2)), str(round(raw, 2))

def _avg_val(metric, avg):
    if avg is None or (isinstance(avg, float) and np.isnan(avg)):
        return "N/A"
    if metric == "Debt to Equity":
        return str(round(avg / 100, 2)) + "x"
    if metric in ("Profit Margin", "ROE"):
        return str(round(avg * 100, 1)) + "%"
    if metric == "Free Cash Flow":
        return "Rs." + str(round(avg / 1e7, 0)) + " Cr"
    if metric == "Dividend Yield":
        v = avg * 100 if avg < 1 else avg
        return str(round(v, 2)) + "%"
    return str(round(avg, 2))

def _signal_class(sig):
    if sig == "✅": return "green"
    if sig == "🟡": return "yellow"
    if sig == "🔴": return "red"
    return "grey"

cols = st.columns(4)
for i, (metric, label, _) in enumerate(METRIC_DISPLAY):
    raw = data.get(metric)
    avg = ind_avg.get(metric)
    sig = interpret(metric, raw, avg)
    val_str, _ = _display_val(metric, raw)
    avg_str     = _avg_val(metric, avg)
    css_class   = _signal_class(sig)
    sig_icon    = sig if sig else "—"

    col = cols[i % 4]
    col.markdown(
        '<div class="metric-card ' + css_class + '">'
        '<div class="metric-signal">' + sig_icon + '</div>'
        '<div class="metric-name">' + label + '</div>'
        '<div class="metric-value">' + val_str + '</div>'
        '<div class="metric-avg">Ind avg: ' + avg_str + '</div>'
        '</div>',
        unsafe_allow_html=True
    )
    if (i + 1) % 4 == 0 and i < len(METRIC_DISPLAY) - 1:
        cols = st.columns(4)

# ── Price chart ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">// price history</div>', unsafe_allow_html=True)
period_opts = ["1mo", "3mo", "6mo", "1y", "3y", "5y", "max"]
period = st.selectbox("Period", period_opts, index=3, label_visibility="collapsed", key="price_period")
ch = _price_chart(chosen_sym, period)
if ch is not None:
    st.altair_chart(ch, use_container_width=True)
else:
    st.info("No price data available.")

# ── Financials ────────────────────────────────────────────────────────────────
rev, pm, fcf = _rev_pm_fcf_frames(chosen_sym)

has_rev = rev is not None and not rev.empty
has_pm  = pm  is not None and not pm.empty
has_fcf = fcf is not None and not fcf.empty

if has_rev or has_pm or has_fcf:
    st.markdown('<div class="section-label">// financials</div>', unsafe_allow_html=True)
    if has_rev and has_pm:
        fc1, fc2 = st.columns(2)
        with fc1:
            st.caption("Revenue (Rs. Cr)")
            st.bar_chart(rev)
        with fc2:
            st.caption("Profit Margin (%)")
            st.line_chart(pm)
    elif has_rev:
        st.caption("Revenue (Rs. Cr)"); st.bar_chart(rev)
    elif has_pm:
        st.caption("Profit Margin (%)"); st.line_chart(pm)
    if has_fcf:
        st.caption("Free Cash Flow (Rs. Cr)"); st.bar_chart(fcf)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:2rem 0 1rem;'>", unsafe_allow_html=True)
st.markdown(
    "<div style='font-size:0.68rem !important;color:#6a88a8;'>"
    "Fundamentals sourced from Yahoo Finance · DB fallback for missing values"
    "</div>",
    unsafe_allow_html=True
)

st.session_state["from_sector_nav"] = False
