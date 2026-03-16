import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

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
.block-container { padding-top: 5rem !important; padding-bottom: 2rem; overflow: visible; }

/* Reset Streamlit's injected paragraph/div sizes inside markdown blocks */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] div,
[data-testid="stMarkdownContainer"] span { font-size: inherit !important; }

.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.0rem !important; font-weight: 800;
    color: #f0f4ff; letter-spacing: -0.02em; margin-bottom: 0.2rem; margin-top: 1rem;
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
    font-family: 'Inter', sans-serif;
    font-size:0.78rem !important; font-weight: 700; color: #f0f4ff;
    font-variant-numeric: tabular-nums;
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
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem !important; font-weight: 700; color: #f0f4ff; line-height: 1;
    font-variant-numeric: tabular-nums;
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
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem !important; font-weight: 700;
    font-variant-numeric: tabular-nums;
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

# Get stored stock or incoming stock from sector analysis
stored_sym = st.session_state.get("fundamentals_stock")
compare_sym = st.session_state.get("compare_symbol")

# Priority: incoming > stored
if compare_sym:
    chosen_sym = compare_sym
    st.session_state["fundamentals_stock"] = compare_sym
    st.session_state["compare_symbol"] = None
elif stored_sym:
    chosen_sym = stored_sym

# Always show search bar with instruction to change
query = st.text_input(
    "search",
    placeholder="🔍  Search by symbol or company name (or leave empty to keep current)...",
    label_visibility="collapsed",
).strip()

if query:
    # User entered new search
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
        st.session_state["fundamentals_stock"] = chosen_sym

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

# ── Add to Comparison Feature ────────────────────────────────────────────────────
st.markdown('<div class="section-label">// compare mode</div>', unsafe_allow_html=True)

col_comp1, col_comp2, col_comp3 = st.columns([2, 1, 1])

with col_comp1:
    add_to_comp = st.text_input(
        "Add stock to compare",
        placeholder="Search symbol or company...",
        key="add_compare_stock",
        label_visibility="collapsed"
    ).strip()
    
    compare_sym = None
    if add_to_comp:
        mask = (
            name_df["Symbol"].str.contains(add_to_comp, case=False, na=False) |
            name_df["Company Name"].str.contains(add_to_comp, case=False, na=False)
        )
        matches = name_df[mask]
        if not matches.empty:
            opts = matches.apply(lambda r: r["Symbol"] + " – " + r["Company Name"], axis=1)
            compare_sym = st.selectbox(
                "Select stock to add",
                opts.tolist(),
                label_visibility="collapsed",
                key="select_compare"
            ).split(" – ")[0]

with col_comp2:
    if st.button("➕ Add", key="btn_add_compare"):
        if compare_sym and compare_sym != chosen_sym:
            if "comparison_stocks" not in st.session_state:
                st.session_state.comparison_stocks = []
            if compare_sym not in st.session_state.comparison_stocks:
                st.session_state.comparison_stocks.append(compare_sym)
                st.success(f"✅ Added {compare_sym}")
        elif compare_sym == chosen_sym:
            st.warning("Stock already selected")

with col_comp3:
    if st.button("🗑️ Clear All", key="btn_clear_compare"):
        st.session_state.comparison_stocks = []
        st.info("Comparison cleared")

# Show comparison stocks
if st.session_state.get("comparison_stocks"):
    st.markdown(f'**Comparing:** {chosen_sym} vs {", ".join(st.session_state.comparison_stocks)}')
    
    # ─────────────────────────────────────────────────────────────────────────
    # COMPARISON TABLE
    # ─────────────────────────────────────────────────────────────────────────
    
    st.markdown('<div class="section-label">// comparison table</div>', unsafe_allow_html=True)
    
    with st.spinner("Loading comparison data..."):
        comparison_stocks_list = [chosen_sym] + st.session_state.comparison_stocks
        comparison_results = {}
        
        for sym in comparison_stocks_list:
            try:
                if sym == chosen_sym:
                    comp_data = data
                    comp_company = company
                    comp_industry = industry
                else:
                    comp_data = _fetch_core_metrics(sym)
                    comp_db = master_df[master_df["Symbol"] == sym]
                    comp_company = comp_data.get("_company") or (comp_db.iloc[0]["Company Name"] if not comp_db.empty else sym)
                    comp_industry = comp_db.iloc[0]["Industry"] if not comp_db.empty else "N/A"
                
                comparison_results[sym] = {
                    "company": comp_company,
                    "industry": comp_industry,
                    "PE Ratio": comp_data.get("PE Ratio"),
                    "EPS": comp_data.get("EPS"),
                    "Profit Margin": comp_data.get("Profit Margin"),
                    "ROE": comp_data.get("ROE"),
                    "Debt to Equity": comp_data.get("Debt to Equity"),
                    "Dividend Yield": comp_data.get("Dividend Yield"),
                }
            except:
                pass
        
        # Display as styled table
        st.markdown('<div style="overflow-x:auto;">', unsafe_allow_html=True)
        
        metrics_compare = [
            ("PE Ratio", "PE Ratio", None, "Lower is better"),
            ("EPS", "EPS", "Rs.", "Higher is better"),
            ("Profit Margin", "Profit Margin", "%", "Higher is better"),
            ("ROE", "ROE", "%", "Higher is better"),
            ("Debt to Equity", "Debt to Equity", None, "Lower is better"),
            ("Dividend Yield", "Dividend Yield", "%", "Higher is better"),
        ]
        
        # Build HTML table
        html_table = '<table style="width:100%;border-collapse:collapse;margin:1rem 0;">'
        html_table += '<tr style="background:#0d1628;border-bottom:2px solid rgba(0,200,130,0.3);">'
        html_table += '<th style="padding:1rem;text-align:left;color:#8aaac8;font-size:0.75rem;text-transform:uppercase;font-weight:700;">Metric</th>'
        
        for sym in comparison_stocks_list:
            html_table += f'<th style="padding:1rem;text-align:center;color:#00c882;font-size:0.75rem;text-transform:uppercase;font-weight:700;">{sym}</th>'
        
        html_table += '</tr>'
        
        for metric_name, metric_key, unit, direction in metrics_compare:
            row_bg = '#0a1420'
            html_table += f'<tr style="background:{row_bg};border-bottom:1px solid rgba(255,255,255,0.05);">'
            html_table += f'<td style="padding:0.8rem;color:#c0d4e8;font-size:0.8rem;font-weight:500;">{metric_name}<br><span style="color:#6a88a8;font-size:0.7rem;">{direction}</span></td>'
            
            # Get values for this metric
            values = []
            for sym in comparison_stocks_list:
                if sym in comparison_results:
                    val = comparison_results[sym][metric_key]
                    if val is not None:
                        if unit == "Rs.":
                            display_val = f"₹{val:.2f}"
                        elif unit == "%":
                            display_val = f"{val*100:.2f}%"
                        else:
                            display_val = f"{val:.2f}"
                        values.append((sym, val, display_val))
                    else:
                        values.append((sym, None, "N/A"))
                else:
                    values.append((sym, None, "N/A"))
            
            # Determine best/worst
            numeric_vals = [(sym, v) for sym, v, _ in values if v is not None]
            if numeric_vals:
                if "Lower is better" in direction:
                    best_sym = min(numeric_vals, key=lambda x: x[1])[0]
                    worst_sym = max(numeric_vals, key=lambda x: x[1])[0]
                else:
                    best_sym = max(numeric_vals, key=lambda x: x[1])[0]
                    worst_sym = min(numeric_vals, key=lambda x: x[1])[0]
            else:
                best_sym = worst_sym = None
            
            # Add value cells
            for sym, val, display_val in values:
                if val is None or best_sym is None:
                    cell_color = "transparent"
                    text_color = "#f0f4ff"
                elif sym == best_sym:
                    cell_color = "rgba(0,200,130,0.2)"
                    text_color = "#00c882"
                elif sym == worst_sym:
                    cell_color = "rgba(255,77,106,0.2)"
                    text_color = "#ff4d6a"
                else:
                    cell_color = "transparent"
                    text_color = "#f0f4ff"
                
                html_table += f'<td style="padding:0.8rem;text-align:center;color:{text_color};font-size:0.8rem;font-weight:600;background:{cell_color};">{display_val}</td>'
            
            html_table += '</tr>'
        
        html_table += '</table>'
        
        st.markdown(html_table, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.caption("🟢 Green = Best value | 🔴 Red = Worst value")
        
        # ─────────────────────────────────────────────────────────────────────────
        # SIDE-BY-SIDE PRICE CHARTS
        # ─────────────────────────────────────────────────────────────────────────
        
        st.markdown('<div class="section-label">// price history comparison</div>', unsafe_allow_html=True)
        
        try:
            # Fetch price data for all stocks
            price_data_all = {}
            
            for sym in comparison_stocks_list:
                try:
                    hist = yf.Ticker(sym + ".NS").history("1y", auto_adjust=True)
                    if not hist.empty:
                        price_data_all[sym] = hist["Close"]
                except:
                    pass
            
            if price_data_all:
                # Create subplots for each stock
                num_stocks = len(price_data_all)
                cols_per_row = 2
                num_rows = (num_stocks + 1) // 2
                
                chart_cols = st.columns(cols_per_row)
                
                for idx, (sym, prices) in enumerate(price_data_all.items()):
                    with chart_cols[idx % cols_per_row]:
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=prices.index,
                            y=prices.values,
                            mode='lines',
                            name=sym,
                            line=dict(color='#00c882', width=2),
                            fill='tozeroy',
                            fillcolor='rgba(0,200,130,0.1)'
                        ))
                        
                        # Add min/max lines
                        min_price = prices.min()
                        max_price = prices.max()
                        
                        fig.add_hline(
                            y=min_price, 
                            line_dash="dash", 
                            line_color="#ff4d6a",
                            annotation=dict(text=f"Low: ₹{min_price:.0f}", font=dict(color="#ff4d6a", size=9))
                        )
                        fig.add_hline(
                            y=max_price,
                            line_dash="dash",
                            line_color="#00c882",
                            annotation=dict(text=f"High: ₹{max_price:.0f}", font=dict(color="#00c882", size=9))
                        )
                        
                        fig.update_layout(
                            title=f"<b>{sym}</b> - 1 Year Price",
                            paper_bgcolor="#080d1a",
                            plot_bgcolor="#080d1a",
                            font=dict(family="Inter", color="#c0d4e8", size=10),
                            xaxis=dict(
                                showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                                color="#8aaac8"
                            ),
                            yaxis=dict(
                                showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                                color="#8aaac8"
                            ),
                            margin=dict(l=10, r=10, t=40, b=30),
                            height=350,
                            showlegend=False,
                            hovermode='x'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        
        except Exception as e:
            st.warning(f"Could not load price charts: {str(e)}")
        
        # ─────────────────────────────────────────────────────────────────────────
        # OVERLAY COMPARISON CHART
        # ─────────────────────────────────────────────────────────────────────────
        
        st.markdown('<div class="section-label">// normalized performance overlay</div>', unsafe_allow_html=True)
        
        try:
            # Normalize all prices to 100 at start for easy comparison
            fig_overlay = go.Figure()
            
            colors = ["#00c882", "#6ec6ff", "#f5a623", "#ff4d6a", "#ccff90", "#80d8ff"]
            
            for idx, (sym, prices) in enumerate(price_data_all.items()):
                normalized = (prices / prices.iloc[0]) * 100
                
                fig_overlay.add_trace(go.Scatter(
                    x=normalized.index,
                    y=normalized.values,
                    mode='lines',
                    name=sym,
                    line=dict(color=colors[idx % len(colors)], width=2.5)
                ))
            
            fig_overlay.update_layout(
                title="<b>Performance Comparison</b> (Normalized to 100)",
                paper_bgcolor="#080d1a",
                plot_bgcolor="#080d1a",
                font=dict(family="Inter", color="#c0d4e8", size=11),
                xaxis=dict(
                    showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                    color="#8aaac8"
                ),
                yaxis=dict(
                    showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                    color="#8aaac8",
                    title="Performance (Base = 100)"
                ),
                legend=dict(
                    bgcolor="rgba(8,13,26,0.8)",
                    bordercolor="rgba(255,255,255,0.1)",
                    borderwidth=1
                ),
                margin=dict(l=10, r=10, t=40, b=40),
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_overlay, use_container_width=True, config={"displayModeBar": False})
        
        except Exception as e:
            st.warning(f"Could not load overlay chart: {str(e)}")

# ── Metric cards ──────────────────────────────────────────────────────────────
# Only show metric cards if NOT in comparison mode
if not st.session_state.get("comparison_stocks"):
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

# ─────────────────────────────────────────────────────────────────────────────
# COMPARE WITH OTHER STOCKS
# ─────────────────────────────────────────────────────────────────────────────


st.markdown(
    "<div style='font-size:0.68rem !important;color:#6a88a8;'>"
    "Fundamentals sourced from Yahoo Finance · DB fallback for missing values"
    "</div>",
    unsafe_allow_html=True
)

st.session_state["from_sector_nav"] = False
