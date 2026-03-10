import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from common.sql import load_master
from common.data import load_name_lookup
from common.finance import get_industry_averages, human_market_cap

st.set_page_config(
page_title=“Sector Analysis”,
page_icon=“🏭”,
layout=“wide”,
initial_sidebar_state=“expanded”
)

# ── CSS ─────────────────────────────────────────────────────────────────────

st.markdown(”””

<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: #f0f4ff;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}
.page-sub {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: rgba(150,180,220,0.5);
    margin-bottom: 1.8rem;
    letter-spacing: 0.05em;
}
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(150,180,220,0.4);
    margin-bottom: 0.7rem;
    margin-top: 1.5rem;
}
.stat-card {
    background: #0d1628;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00c882, transparent);
}
.stat-label {
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: rgba(150,180,220,0.5);
    margin-bottom: 0.4rem;
}
.stat-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #f0f4ff;
    line-height: 1;
    margin-bottom: 0.2rem;
}
.stat-sub { font-size: 0.68rem; color: #00c882; }

.sector-pill {
    display: inline-block;
    background: rgba(0,200,130,0.08);
    border: 1px solid rgba(0,200,130,0.2);
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    font-size: 0.72rem;
    color: rgba(0,200,130,0.85);
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
}
.qualify-badge {
    background: rgba(0,200,130,0.12);
    border: 1px solid rgba(0,200,130,0.3);
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.qualify-name {
    font-family: 'Syne', sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: #e8f0ff;
}
.qualify-sym {
    font-size: 0.7rem;
    color: rgba(150,180,220,0.5);
    margin-top: 2px;
}
.qualify-score {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #00c882;
}
div[data-testid="stButton"] > button {
    background: transparent;
    border: 1px solid rgba(0,200,130,0.25);
    border-radius: 8px;
    color: #00c882;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.06em;
    padding: 0.3rem 0.8rem;
    transition: all 0.2s;
    width: 100%;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(0,200,130,0.1);
    border-color: rgba(0,200,130,0.6);
}
</style>

“””, unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────

st.markdown(’<div class="page-title">🏭 Sector & Industry Analysis</div>’, unsafe_allow_html=True)
st.markdown(’<div class="page-sub">// Browse sectors · rank companies · spot top performers</div>’, unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────────────────

master_df = load_master()
name_df   = load_name_lookup()

# Merge — master_df has fundamentals, name_df has Company Name

merged_df = pd.merge(master_df, name_df[[“Symbol”, “Company Name”]], on=“Symbol”, how=“left”)

# Column names from load_master() SQL query

COLS = {
“PE”:     “PE Ratio”,
“EPS”:    “EPS”,
“ROE”:    “ROE”,
“PM”:     “ProfitMargin”,
“DE”:     “DebtToEquity”,
“MCAP”:   “MarketCap”,
}

# Coerce numerics

for col in COLS.values():
if col in merged_df.columns:
merged_df[col] = pd.to_numeric(merged_df[col], errors=“coerce”)

# Normalise D/E (stored as e.g. 120 meaning 1.20)

if “DebtToEquity” in merged_df.columns:
merged_df[“DebtToEquity”] = merged_df[“DebtToEquity”] / 100

# Normalise ROE and ProfitMargin to % (stored as 0.18 → 18)

for col in (“ROE”, “ProfitMargin”):
if col in merged_df.columns:
mask = merged_df[col].notna() & (merged_df[col].abs() <= 2)
merged_df.loc[mask, col] = merged_df.loc[mask, col] * 100

# ── Sidebar filters ──────────────────────────────────────────────────────────

st.sidebar.markdown(”### 🔍 Filters”)

sectors = sorted(merged_df[“Big Sectors”].dropna().unique())
sec_sel = st.sidebar.selectbox(“Sector”, sectors)

industries = sorted(merged_df[merged_df[“Big Sectors”] == sec_sel][“Industry”].dropna().unique())
ind_sel = st.sidebar.selectbox(“Industry”, industries)

rank_by   = st.sidebar.selectbox(“Rank companies by”, [“Market Cap”, “EPS”, “ROE”, “PE Ratio”, “Profit Margin”])
show_all  = st.sidebar.checkbox(“Show all companies”, value=False)

st.sidebar.markdown(”—”)
st.sidebar.markdown(”**🎯 Top Performer Criteria**”)
interp_threshold = st.sidebar.selectbox(“Min green signals”, [“5 / 5”, “4 / 5”, “3 / 5”, “2 / 5”], index=1)
interp_cutoff    = {“5 / 5”: 5, “4 / 5”: 4, “3 / 5”: 3, “2 / 5”: 2}[interp_threshold]

# ── Sector summary strip ─────────────────────────────────────────────────────

sector_df = merged_df[merged_df[“Big Sectors”] == sec_sel]
ind_count = sector_df[“Industry”].nunique()
co_count  = len(sector_df)
total_cap = sector_df[“MarketCap”].sum()

st.markdown(’<div class="section-label">// sector overview</div>’, unsafe_allow_html=True)
sc1, sc2, sc3, sc4 = st.columns(4)
for col, label, value, sub in [
(sc1, “Sector”,           sec_sel,                          “selected”),
(sc2, “Industries”,       str(ind_count),                   “in this sector”),
(sc3, “Companies”,        str(co_count),                    “listed”),
(sc4, “Total Market Cap”, human_market_cap(total_cap) if total_cap > 0 else “N/A”, “combined”),
]:
col.markdown(f”””
<div class="stat-card">
<div class="stat-label">{label}</div>
<div class="stat-value" style="font-size:1.3rem;">{value}</div>
<div class="stat-sub">{sub}</div>
</div>
“””, unsafe_allow_html=True)

# ── Industry scope ───────────────────────────────────────────────────────────

scoped_df = merged_df[merged_df[“Industry”] == ind_sel].copy()

st.markdown(’<div class="section-label">// industry averages</div>’, unsafe_allow_html=True)
st.markdown(f”””
<div style="margin-bottom:0.8rem;">
<span class="sector-pill">📍 {ind_sel}</span>
<span class="sector-pill">🏢 {len(scoped_df)} companies</span>
</div>
“””, unsafe_allow_html=True)

# ── Industry averages — from DB (fast) ──────────────────────────────────────

avg_vals = get_industry_averages(ind_sel, master_df)

def _safe(val, scale=1.0, fmt=”.2f”):
“”“Safely format a possibly-None value.”””
if val is None or (isinstance(val, float) and np.isnan(val)):
return “N/A”
return format(val * scale, fmt)

def _safe_mcap(val):
if val is None or (isinstance(val, float) and np.isnan(val)):
return “N/A”
return human_market_cap(val)

avg_pe  = avg_vals.get(“PE Ratio”)
avg_eps = avg_vals.get(“EPS”)
avg_roe = avg_vals.get(“ROE”)
avg_pm  = avg_vals.get(“Profit Margin”)
avg_de  = avg_vals.get(“Debt to Equity”)

# avg ROE and PM from DB are already in decimal form (e.g. 0.18)

# normalise to % for display

avg_roe_pct = (avg_roe * 100) if avg_roe is not None else None
avg_pm_pct  = (avg_pm * 100)  if avg_pm  is not None else None

# avg D/E from DB — normalise if stored as ratio×100

if avg_de is not None and avg_de > 5:
avg_de = avg_de / 100

a1, a2, a3, a4, a5 = st.columns(5)
for col, label, value in [
(a1, “Avg PE Ratio”,     _safe(avg_pe)),
(a2, “Avg EPS”,          _safe(avg_eps)),
(a3, “Avg ROE”,          “N/A” if avg_roe_pct is None else f”{avg_roe_pct:.1f}%”),
(a4, “Avg Profit Margin”,“N/A” if avg_pm_pct  is None else f”{avg_pm_pct:.1f}%”),
(a5, “Avg D/E”,          _safe(avg_de)),
]:
col.markdown(f”””
<div class="stat-card">
<div class="stat-label">{label}</div>
<div class="stat-value" style="font-size:1.4rem;">{value}</div>
</div>
“””, unsafe_allow_html=True)

# ── Rank & score companies ───────────────────────────────────────────────────

sort_col_map = {
“Market Cap”:    “MarketCap”,
“EPS”:           “EPS”,
“ROE”:           “ROE”,
“PE Ratio”:      “PE Ratio”,
“Profit Margin”: “ProfitMargin”,
}
sort_col = sort_col_map[rank_by]
if sort_col in scoped_df.columns:
ascending = rank_by == “PE Ratio”   # lower PE is better
scoped_df = scoped_df.sort_values(by=sort_col, ascending=ascending, na_position=“last”)

sel_df = scoped_df if show_all else scoped_df.head(10)

# ── Scoring helpers ──────────────────────────────────────────────────────────

def _score_hi(v, a):
if v is None or a is None or pd.isna(v) or pd.isna(a): return “❓”
return “✅” if v >= a else “🟡” if v >= a * 0.8 else “🔴”

def _score_lo(v, a):
if v is None or a is None or pd.isna(v) or pd.isna(a): return “❓”
return “✅” if v <= a else “🟡” if v <= a * 1.1 else “🔴”

def _score_de(v, a):
if v is None or a is None or pd.isna(v) or pd.isna(a): return “❓”
return “✅” if v <= a else “🟡” if v <= 1.5 else “🔴”

def fmt_cap(val):
if val is None or pd.isna(val): return “N/A”
if val >= 1e12: return f”₹{val/1e12:.2f}T”
if val >= 1e9:  return f”₹{val/1e9:.2f}B”
if val >= 1e6:  return f”₹{val/1e6:.2f}M”
return f”₹{val:.0f}”

# ── Build rows ───────────────────────────────────────────────────────────────

rows, qualified = [], []
name_lookup = dict(zip(name_df[“Symbol”], name_df[“Company Name”]))

for _, row in sel_df.iterrows():
sym    = row[“Symbol”]
pe_val = row.get(“PE Ratio”)
eps_val= row.get(“EPS”)
roe_val= row.get(“ROE”)       # already % after normalisation above
pm_val = row.get(“ProfitMargin”) # already % after normalisation above
de_val = row.get(“DebtToEquity”) # already ratio after normalisation above

```
icons = {
    "PE":  _score_lo(pe_val,  avg_pe),
    "EPS": _score_hi(eps_val, avg_eps),
    "ROE": _score_hi(roe_val, avg_roe_pct),
    "PM":  _score_hi(pm_val,  avg_pm_pct),
    "D/E": _score_de(de_val,  avg_de),
}
green_count = sum(v == "✅" for v in icons.values())
score_str   = " | ".join(f"{k} {v}" for k, v in icons.items())

r = {
    "Symbol":      sym,
    "Company":     name_lookup.get(sym, ""),
    "PE":          round(pe_val,  2) if pe_val  is not None and pd.notna(pe_val)  else None,
    "EPS":         round(eps_val, 2) if eps_val is not None and pd.notna(eps_val) else None,
    "ROE %":       round(roe_val, 2) if roe_val is not None and pd.notna(roe_val) else None,
    "Margin %":    round(pm_val,  2) if pm_val  is not None and pd.notna(pm_val)  else None,
    "D/E":         round(de_val,  2) if de_val  is not None and pd.notna(de_val)  else None,
    "MCap":        fmt_cap(row.get("MarketCap")),
    "Signals":     score_str,
    "✅ Count":    green_count,
}
rows.append(r)
if green_count >= interp_cutoff:
    qualified.append({**r, "_sym": sym})
```

# ── Market Cap bar chart ─────────────────────────────────────────────────────

st.markdown(’<div class="section-label">// market cap distribution — top 10</div>’, unsafe_allow_html=True)

chart_df = scoped_df.head(10).copy()
chart_df[“Company Name”] = chart_df[“Symbol”].map(name_lookup).fillna(chart_df[“Symbol”])
chart_df = chart_df.dropna(subset=[“MarketCap”])

if not chart_df.empty:
chart_df = chart_df.sort_values(“MarketCap”, ascending=True)
fig_cap = go.Figure(go.Bar(
x=chart_df[“MarketCap”] / 1e9,
y=chart_df[“Company Name”],
orientation=“h”,
marker=dict(
color=chart_df[“MarketCap”],
colorscale=[[0, “#0d3d2a”], [1, “#00c882”]],
showscale=False,
),
hovertemplate=”<b>%{y}</b><br>₹%{x:.2f}B<extra></extra>”,
))
fig_cap.update_layout(
paper_bgcolor=”#080d1a”,
plot_bgcolor=”#080d1a”,
font=dict(family=“DM Mono”, color=“rgba(180,200,230,0.7)”, size=11),
xaxis=dict(showgrid=False, title=“Market Cap (₹B)”, color=“rgba(150,180,220,0.5)”),
yaxis=dict(showgrid=False, color=“rgba(180,200,230,0.8)”),
margin=dict(l=10, r=20, t=10, b=30),
height=320,
)
st.plotly_chart(fig_cap, use_container_width=True, config={“displayModeBar”: False})
else:
st.info(“No market cap data available for this industry.”)

# ── ROE vs PE scatter ────────────────────────────────────────────────────────

scatter_df = scoped_df.dropna(subset=[“PE Ratio”, “ROE”]).head(20).copy()
scatter_df[“Company Name”] = scatter_df[“Symbol”].map(name_lookup).fillna(scatter_df[“Symbol”])

if len(scatter_df) >= 3:
st.markdown(’<div class="section-label">// ROE vs PE — value vs quality</div>’, unsafe_allow_html=True)
fig_sc = go.Figure(go.Scatter(
x=scatter_df[“PE Ratio”],
y=scatter_df[“ROE”],
mode=“markers+text”,
text=scatter_df[“Symbol”],
textposition=“top center”,
textfont=dict(size=9, color=“rgba(180,200,230,0.6)”),
marker=dict(
size=10,
color=scatter_df[“ROE”],
colorscale=[[0, “#0d3d2a”], [1, “#00c882”]],
showscale=False,
line=dict(width=1, color=“rgba(0,200,130,0.3)”),
),
hovertemplate=”<b>%{text}</b><br>PE: %{x:.1f}<br>ROE: %{y:.1f}%<extra></extra>”,
))
if avg_pe is not None:
fig_sc.add_vline(x=avg_pe, line_dash=“dot”, line_color=“rgba(0,200,130,0.3)”,
annotation_text=“Avg PE”, annotation_font_color=“rgba(0,200,130,0.5)”)
if avg_roe_pct is not None:
fig_sc.add_hline(y=avg_roe_pct, line_dash=“dot”, line_color=“rgba(0,200,130,0.3)”,
annotation_text=“Avg ROE”, annotation_font_color=“rgba(0,200,130,0.5)”)
fig_sc.update_layout(
paper_bgcolor=”#080d1a”, plot_bgcolor=”#080d1a”,
font=dict(family=“DM Mono”, color=“rgba(180,200,230,0.7)”, size=11),
xaxis=dict(showgrid=False, title=“PE Ratio”, color=“rgba(150,180,220,0.5)”, zeroline=False),
yaxis=dict(showgrid=False, title=“ROE %”,    color=“rgba(150,180,220,0.5)”, zeroline=False),
margin=dict(l=10, r=20, t=10, b=30),
height=320,
)
st.plotly_chart(fig_sc, use_container_width=True, config={“displayModeBar”: False})

# ── Company table ─────────────────────────────────────────────────────────────

st.markdown(’<div class="section-label">// company rankings</div>’, unsafe_allow_html=True)
header_lbl = f”All {len(scoped_df)} companies” if show_all else f”Top 10 by {rank_by}”
st.caption(header_lbl)

display_df = pd.DataFrame(rows).drop(columns=[”_sym”], errors=“ignore”)
display_df.index = range(1, len(display_df) + 1)
st.dataframe(
display_df,
use_container_width=True,
column_config={
“✅ Count”: st.column_config.ProgressColumn(
“Score”, min_value=0, max_value=5, format=”%d / 5”
),
“MCap”: st.column_config.TextColumn(“Market Cap”),
}
)

# ── Top performers ────────────────────────────────────────────────────────────

st.markdown(’<div class="section-label">// top performers</div>’, unsafe_allow_html=True)

if qualified:
# Sort by score descending
qualified_sorted = sorted(qualified, key=lambda x: x[“✅ Count”], reverse=True)

```
q_cols = st.columns(3)
for i, q in enumerate(qualified_sorted):
    col = q_cols[i % 3]
    sym   = q["_sym"]
    name  = q["Company"] or sym
    score = q["✅ Count"]
    mcap  = q["MCap"]
    col.markdown(f"""
        <div class="qualify-badge">
            <div>
                <div class="qualify-name">{name}</div>
                <div class="qualify-sym">{sym} · {mcap}</div>
            </div>
            <div class="qualify-score">{score}/5</div>
        </div>
    """, unsafe_allow_html=True)
    if col.button(f"View {sym}", key=f"goto_{sym}_{i}"):
        st.session_state["compare_symbol"] = sym
        st.session_state["already_loaded_from_sector"] = False
        st.switch_page("pages/1_Fundamentals.py")
```

else:
st.info(f”No company meets {interp_threshold} green signals in this industry. Try lowering the threshold in the sidebar.”)

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown(”<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:2rem 0 1rem;'>”, unsafe_allow_html=True)
st.markdown(”””
<div style="font-family:'DM Mono',monospace;font-size:0.65rem;color:rgba(150,180,220,0.3);">
Fundamentals sourced from Yahoo Finance via yfinance · Industry averages from cached DB
</div>
“””, unsafe_allow_html=True)
