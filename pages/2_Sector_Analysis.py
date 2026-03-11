import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from common.sql import load_master
from common.data import load_name_lookup
from common.finance import get_industry_averages, human_market_cap

st.set_page_config(
    page_title="Sector Analysis",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="auto"
)

# -- CSS ---------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
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
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    color: #8aaac8;
    margin-bottom: 1.8rem;
    letter-spacing: 0.05em;
}
.section-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #8aaac8;
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
    color: #8aaac8;
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
    color: #8aaac8;
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
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    color: #8aaac8;
    font-family: 'Inter', sans-serif;
    font-size: 0.62rem;
    font-weight: 500;
    letter-spacing: 0.03em;
    padding: 0.2rem 0.4rem;
    transition: all 0.15s;
    width: 100%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-height: 0 !important;
    line-height: 1.3;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(0,200,130,0.08);
    border-color: rgba(0,200,130,0.4);
    color: #00c882;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: rgba(0,200,130,0.12);
    border-color: #00c882;
    color: #00c882;
    font-weight: 700;
}
.filter-bar {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.8rem;
}
.filter-title {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #8aaac8;
    margin-bottom: 0.7rem;
}
.spill {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 0.3rem;
}
.spill-pill {
    display: inline-block;
    background: #0d1e35;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 0.35rem 0.9rem;
    font-size: 0.73rem;
    font-weight: 500;
    color: #c0d4e8;
    cursor: pointer;
    transition: all 0.15s;
    white-space: nowrap;
}
.spill-pill:hover {
    border-color: rgba(0,200,130,0.5);
    color: #00c882;
}
.spill-pill.active {
    background: rgba(0,200,130,0.15);
    border-color: #00c882;
    color: #00c882;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# -- Header ------------------------------------------------------------------
st.markdown('<div class="page-title">🏭 Sector &amp; Industry Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">// Browse sectors · rank companies · spot top performers</div>', unsafe_allow_html=True)

# -- Load data ---------------------------------------------------------------
master_df = load_master()
name_df   = load_name_lookup()

merged_df = pd.merge(master_df, name_df[["Symbol", "Company Name"]], on="Symbol", how="left")

COLS = {
    "PE":   "PE Ratio",
    "EPS":  "EPS",
    "ROE":  "ROE",
    "PM":   "ProfitMargin",
    "DE":   "DebtToEquity",
    "MCAP": "MarketCap",
}

for col in COLS.values():
    if col in merged_df.columns:
        merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")

if "DebtToEquity" in merged_df.columns:
    merged_df["DebtToEquity"] = merged_df["DebtToEquity"] / 100

for col in ("ROE", "ProfitMargin"):
    if col in merged_df.columns:
        mask = merged_df[col].notna() & (merged_df[col].abs() <= 2)
        merged_df.loc[mask, col] = merged_df.loc[mask, col] * 100

# -- Inline filter bar -------------------------------------------------------
sectors    = sorted(merged_df["Big Sectors"].dropna().unique())
industries_all = sorted(merged_df["Industry"].dropna().unique())

# Sector selection state
if "sec_sel" not in st.session_state or st.session_state["sec_sel"] not in sectors:
    st.session_state["sec_sel"] = sectors[0]
if "ind_sel" not in st.session_state:
    st.session_state["ind_sel"] = None

st.markdown('<div class="filter-bar">', unsafe_allow_html=True)

# ── Row 1: Sector selector ───────────────────────────────────────────────────
st.markdown('<div class="filter-title">Sector</div>', unsafe_allow_html=True)
sec_sel = st.selectbox(
    "sector",
    sectors,
    index=sectors.index(st.session_state["sec_sel"]) if st.session_state["sec_sel"] in sectors else 0,
    label_visibility="collapsed",
    key="sec_selectbox"
)
if sec_sel != st.session_state["sec_sel"]:
    st.session_state["sec_sel"] = sec_sel
    st.session_state["ind_sel"] = None
    st.rerun()

# ── Row 2: Industry selector ──────────────────────────────────────────────────
industries = sorted(merged_df[merged_df["Big Sectors"] == sec_sel]["Industry"].dropna().unique())
if st.session_state["ind_sel"] not in industries:
    st.session_state["ind_sel"] = industries[0]

st.markdown("<div style='margin-top:0.6rem;'></div>", unsafe_allow_html=True)
st.markdown('<div class="filter-title">Industry</div>', unsafe_allow_html=True)

# Render as evenly spaced pill buttons using st.columns with equal weights
IND_PER_ROW = 5
for row_start in range(0, len(industries), IND_PER_ROW):
    row_inds = industries[row_start:row_start + IND_PER_ROW]
    # Pad to IND_PER_ROW so spacing is always consistent
    padded = row_inds + [""] * (IND_PER_ROW - len(row_inds))
    ind_cols = st.columns(IND_PER_ROW)
    for j, ind in enumerate(padded):
        if ind == "":
            continue
        active = ind == st.session_state["ind_sel"]
        if ind_cols[j].button(
            ind, key="ind_" + ind,
            type="primary" if active else "secondary",
            use_container_width=True
        ):
            st.session_state["ind_sel"] = ind
            st.rerun()

ind_sel = st.session_state["ind_sel"]

# ── No extra filters ────────────────────────────────────────────────────────
rank_by       = "ROE"       # default sort for company scoring
show_all      = False
interp_cutoff = 3           # show companies with 3+ green signals

st.markdown('</div>', unsafe_allow_html=True)

# -- Sector summary strip ----------------------------------------------------
sector_df = merged_df[merged_df["Big Sectors"] == sec_sel]
ind_count = sector_df["Industry"].nunique()
co_count  = len(sector_df)
total_cap = sector_df["MarketCap"].sum()

st.markdown('<div class="section-label">// sector overview</div>', unsafe_allow_html=True)
sc1, sc2, sc3, sc4 = st.columns(4)
for col, label, value, sub in [
    (sc1, "Sector",           sec_sel,                                              "selected"),
    (sc2, "Industries",       str(ind_count),                                       "in this sector"),
    (sc3, "Companies",        str(co_count),                                        "listed"),
    (sc4, "Total Market Cap", human_market_cap(total_cap) if total_cap > 0 else "N/A", "combined"),
]:
    col.markdown(
        '<div class="stat-card">'
        '<div class="stat-label">' + label + '</div>'
        '<div class="stat-value" style="font-size:1.3rem;">' + value + '</div>'
        '<div class="stat-sub">' + sub + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

# -- Industry scope ----------------------------------------------------------
scoped_df = merged_df[merged_df["Industry"] == ind_sel].copy()

st.markdown('<div class="section-label">// industry averages</div>', unsafe_allow_html=True)
st.markdown(
    '<div style="margin-bottom:0.8rem;">'
    '<span class="sector-pill">📍 ' + ind_sel + '</span>'
    '<span class="sector-pill">🏢 ' + str(len(scoped_df)) + ' companies</span>'
    '</div>',
    unsafe_allow_html=True
)

# -- Industry averages from DB (fast) ----------------------------------------
avg_vals = get_industry_averages(ind_sel, master_df)

def _safe(val, scale=1.0, fmt=".2f"):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    return format(val * scale, fmt)

def _safe_mcap(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    return human_market_cap(val)

avg_pe  = avg_vals.get("PE Ratio")
avg_eps = avg_vals.get("EPS")
avg_roe = avg_vals.get("ROE")
avg_pm  = avg_vals.get("Profit Margin")
avg_de  = avg_vals.get("Debt to Equity")

avg_roe_pct = (avg_roe * 100) if avg_roe is not None else None
avg_pm_pct  = (avg_pm  * 100) if avg_pm  is not None else None

if avg_de is not None and avg_de > 5:
    avg_de = avg_de / 100

a1, a2, a3, a4, a5 = st.columns(5)
for col, label, value in [
    (a1, "Avg PE Ratio",      _safe(avg_pe)),
    (a2, "Avg EPS",           _safe(avg_eps)),
    (a3, "Avg ROE",           "N/A" if avg_roe_pct is None else str(round(avg_roe_pct, 1)) + "%"),
    (a4, "Avg Profit Margin", "N/A" if avg_pm_pct  is None else str(round(avg_pm_pct,  1)) + "%"),
    (a5, "Avg D/E",           _safe(avg_de)),
]:
    col.markdown(
        '<div class="stat-card">'
        '<div class="stat-label">' + label + '</div>'
        '<div class="stat-value" style="font-size:1.4rem;">' + value + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

# -- Rank & score companies --------------------------------------------------
sort_col_map = {
    "EPS":           "EPS",
    "ROE":           "ROE",
    "PE Ratio":      "PE Ratio",
    "Profit Margin": "ProfitMargin",
}
sort_col = sort_col_map[rank_by]
if sort_col in scoped_df.columns:
    ascending = rank_by == "PE Ratio"
    scoped_df = scoped_df.sort_values(by=sort_col, ascending=ascending, na_position="last")

sel_df = scoped_df if show_all else scoped_df.head(10)

# -- Scoring helpers ---------------------------------------------------------
def _score_hi(v, a):
    if v is None or a is None or pd.isna(v) or pd.isna(a): return "❓"
    return "✅" if v >= a else "🟡" if v >= a * 0.8 else "🔴"

def _score_lo(v, a):
    if v is None or a is None or pd.isna(v) or pd.isna(a): return "❓"
    return "✅" if v <= a else "🟡" if v <= a * 1.1 else "🔴"

def _score_de(v, a):
    if v is None or a is None or pd.isna(v) or pd.isna(a): return "❓"
    return "✅" if v <= a else "🟡" if v <= 1.5 else "🔴"

def fmt_cap(val):
    if val is None or pd.isna(val): return "N/A"
    if val >= 1e12: return "Rs." + str(round(val / 1e12, 2)) + "T"
    if val >= 1e9:  return "Rs." + str(round(val / 1e9,  2)) + "B"
    if val >= 1e6:  return "Rs." + str(round(val / 1e6,  2)) + "M"
    return "Rs." + str(round(val, 0))

# -- Build rows --------------------------------------------------------------
rows, qualified = [], []
name_lookup = dict(zip(name_df["Symbol"], name_df["Company Name"]))

for _, row in sel_df.iterrows():
    sym     = row["Symbol"]
    pe_val  = row.get("PE Ratio")
    eps_val = row.get("EPS")
    roe_val = row.get("ROE")
    pm_val  = row.get("ProfitMargin")
    de_val  = row.get("DebtToEquity")

    icons = {
        "PE":  _score_lo(pe_val,  avg_pe),
        "EPS": _score_hi(eps_val, avg_eps),
        "ROE": _score_hi(roe_val, avg_roe_pct),
        "PM":  _score_hi(pm_val,  avg_pm_pct),
        "D/E": _score_de(de_val,  avg_de),
    }
    green_count = sum(v == "✅" for v in icons.values())
    score_str   = " | ".join(k + " " + v for k, v in icons.items())

    r = {
        "Symbol":    sym,
        "Company":   name_lookup.get(sym, ""),
        "PE":        round(pe_val,  2) if pe_val  is not None and pd.notna(pe_val)  else None,
        "EPS":       round(eps_val, 2) if eps_val is not None and pd.notna(eps_val) else None,
        "ROE %":     round(roe_val, 2) if roe_val is not None and pd.notna(roe_val) else None,
        "Margin %":  round(pm_val,  2) if pm_val  is not None and pd.notna(pm_val)  else None,
        "D/E":       round(de_val,  2) if de_val  is not None and pd.notna(de_val)  else None,
        "MCap":      fmt_cap(row.get("MarketCap")),
        "Signals":   score_str,
        "Score":     green_count,
    }
    rows.append(r)
    if green_count >= interp_cutoff:
        qualified.append({**r, "_sym": sym})

# -- Market Cap bar chart ----------------------------------------------------
st.markdown('<div class="section-label">// market cap distribution - top 10</div>', unsafe_allow_html=True)

chart_df = scoped_df.head(10).copy()
chart_df["Company Name"] = chart_df["Symbol"].map(name_lookup).fillna(chart_df["Symbol"])
chart_df = chart_df.dropna(subset=["MarketCap"])

if not chart_df.empty:
    chart_df = chart_df.sort_values("MarketCap", ascending=True)
    fig_cap = go.Figure(go.Bar(
        x=chart_df["MarketCap"] / 1e9,
        y=chart_df["Company Name"],
        orientation="h",
        marker=dict(
            color=chart_df["MarketCap"],
            colorscale=[[0, "#0d3d2a"], [1, "#00c882"]],
            showscale=False,
        ),
        hovertemplate="<b>%{y}</b><br>Rs.%{x:.2f}B<extra></extra>",
    ))
    fig_cap.update_layout(
        paper_bgcolor="#080d1a",
        plot_bgcolor="#080d1a",
        font=dict(family="Inter", color="#c0d4e8", size=11),
        xaxis=dict(showgrid=False, title="Market Cap (Rs.B)", color="#8aaac8"),
        yaxis=dict(showgrid=False, color="#c0d4e8"),
        margin=dict(l=10, r=20, t=10, b=30),
        height=320,
    )
    st.plotly_chart(fig_cap, use_container_width=True, config={"displayModeBar": False})
else:
    st.info("No market cap data available for this industry.")

# -- ROE vs PE scatter -------------------------------------------------------
scatter_df = scoped_df.dropna(subset=["PE Ratio", "ROE"]).head(20).copy()
scatter_df["Company Name"] = scatter_df["Symbol"].map(name_lookup).fillna(scatter_df["Symbol"])

if len(scatter_df) >= 3:
    st.markdown('<div class="section-label">// ROE vs PE - quality vs valuation</div>', unsafe_allow_html=True)

    # Colour each dot by quadrant relative to averages
    def _dot_color(pe, roe):
        if avg_pe is None or avg_roe_pct is None:
            return "#8aaac8"
        low_pe  = pe  <= avg_pe
        high_roe = roe >= avg_roe_pct
        if low_pe and high_roe:   return "#00c882"   # ideal: cheap + profitable
        if low_pe and not high_roe: return "#f5a623"  # cheap but low quality
        if not low_pe and high_roe: return "#6ec6ff"  # quality but expensive
        return "#ff4d6a"                               # expensive + low quality

    dot_colors = [_dot_color(r["PE Ratio"], r["ROE"]) for _, r in scatter_df.iterrows()]

    # Shared avg thresholds for both dots and quadrant breakdown
    _q_avg_pe  = avg_pe      if avg_pe      is not None else float(scatter_df["PE Ratio"].median())
    _q_avg_roe = avg_roe_pct if avg_roe_pct is not None else float(scatter_df["ROE"].median())

    fig_sc = go.Figure()

    # Quadrant shading (only when averages are available)
    if avg_pe is not None and avg_roe_pct is not None:
        x_min = scatter_df["PE Ratio"].min() * 0.85
        x_max = scatter_df["PE Ratio"].max() * 1.15
        y_min = scatter_df["ROE"].min() * 0.85
        y_max = scatter_df["ROE"].max() * 1.15

        quadrants = [
            (x_min, avg_pe,  avg_roe_pct, y_max, "rgba(0,200,130,0.04)",  "Cheap + Quality"),
            (avg_pe, x_max,  avg_roe_pct, y_max, "rgba(100,180,255,0.04)", "Expensive + Quality"),
            (x_min, avg_pe,  y_min, avg_roe_pct, "rgba(245,166,35,0.04)",  "Cheap + Low ROE"),
            (avg_pe, x_max,  y_min, avg_roe_pct, "rgba(255,77,106,0.04)",  "Expensive + Low ROE"),
        ]
        for x0, x1, y0, y1, fill, _ in quadrants:
            fig_sc.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                             fillcolor=fill, line_width=0, layer="below")

        # Quadrant corner labels
        label_cfg = [
            (x_min * 1.01, y_max * 0.97, "Cheap + Quality",     "#00c882",  "top left"),
            (x_max * 0.99, y_max * 0.97, "Expensive + Quality", "#6ec6ff",  "top right"),
            (x_min * 1.01, y_min * 1.03, "Cheap + Low ROE",     "#f5a623",  "bottom left"),
            (x_max * 0.99, y_min * 1.03, "Expensive + Low ROE", "#ff4d6a",  "bottom right"),
        ]
        for lx, ly, ltxt, lclr, anchor in label_cfg:
            xanchor = "left" if "left" in anchor else "right"
            yanchor = "top"  if "top"  in anchor else "bottom"
            fig_sc.add_annotation(x=lx, y=ly, text=ltxt, showarrow=False,
                                  font=dict(size=9, color=lclr, family="Inter"),
                                  xanchor=xanchor, yanchor=yanchor, opacity=0.7)

    # Avg lines — solid, clearly labelled
    if avg_pe is not None:
        fig_sc.add_vline(x=avg_pe, line_dash="dash", line_color="#00c882", line_width=1.5,
                         annotation_text="Avg PE " + str(round(avg_pe, 1)),
                         annotation_font=dict(color="#00c882", size=11, family="Inter"),
                         annotation_position="top right")
    if avg_roe_pct is not None:
        fig_sc.add_hline(y=avg_roe_pct, line_dash="dash", line_color="#00c882", line_width=1.5,
                         annotation_text="Avg ROE " + str(round(avg_roe_pct, 1)) + "%",
                         annotation_font=dict(color="#00c882", size=11, family="Inter"),
                         annotation_position="top right")

    # Scatter dots — NO inline text (avoids overlap), full info on hover
    fig_sc.add_trace(go.Scatter(
        x=scatter_df["PE Ratio"],
        y=scatter_df["ROE"],
        mode="markers",
        text=scatter_df["Symbol"],
        customdata=scatter_df[["Company Name"]].values,
        marker=dict(
            size=14,
            color=dot_colors,
            line=dict(width=1.5, color="rgba(255,255,255,0.2)"),
        ),
        hovertemplate=(
            "<b>%{text}</b>  %{customdata[0]}<br>"
            "PE Ratio: %{x:.1f}  |  ROE: %{y:.1f}%<br>"
            "<extra></extra>"
        ),
        name="",
    ))

    fig_sc.update_layout(
        paper_bgcolor="#080d1a",
        plot_bgcolor="#080d1a",
        font=dict(family="Inter", color="#c0d4e8", size=11),
        xaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            title=dict(text="PE Ratio  (lower = cheaper)", font=dict(color="#8aaac8", size=11)),
            color="#8aaac8", zeroline=False,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            title=dict(text="ROE %  (higher = more profitable)", font=dict(color="#8aaac8", size=11)),
            color="#8aaac8", zeroline=False,
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=40),
        height=420,
    )
    st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

    # -- Quadrant breakdown: company names per category ------------------
    # Build per-quadrant lists
    q_groups = {
        "Cheap + Quality":      {"color": "#00c882", "bg": "rgba(0,200,130,0.08)",  "border": "#00c882", "companies": []},
        "Expensive + Quality":  {"color": "#6ec6ff", "bg": "rgba(100,180,255,0.08)","border": "#6ec6ff", "companies": []},
        "Cheap + Low ROE":      {"color": "#f5a623", "bg": "rgba(245,166,35,0.08)", "border": "#f5a623", "companies": []},
        "Expensive + Low ROE":  {"color": "#ff4d6a", "bg": "rgba(255,77,106,0.08)", "border": "#ff4d6a", "companies": []},
    }
    # Use avg from DB, fallback to median of scatter_df itself
    for _, r in scatter_df.iterrows():
        pe   = r["PE Ratio"]
        roe  = r["ROE"]
        sym  = r["Symbol"]
        name = r["Company Name"]
        # skip if either value is null
        if pd.isna(pe) or pd.isna(roe):
            continue
        low_pe   = float(pe)  <= _q_avg_pe
        high_roe = float(roe) >= _q_avg_roe
        if   low_pe and     high_roe: q_groups["Cheap + Quality"]["companies"].append((sym, name, round(float(pe),1), round(float(roe),1)))
        elif not low_pe and high_roe: q_groups["Expensive + Quality"]["companies"].append((sym, name, round(float(pe),1), round(float(roe),1)))
        elif low_pe and not high_roe: q_groups["Cheap + Low ROE"]["companies"].append((sym, name, round(float(pe),1), round(float(roe),1)))
        else:                         q_groups["Expensive + Low ROE"]["companies"].append((sym, name, round(float(pe),1), round(float(roe),1)))

    st.markdown(
        "<div style='margin-top:1rem;margin-bottom:0.6rem;font-size:0.68rem;font-weight:700;"
        "letter-spacing:0.14em;text-transform:uppercase;color:#8aaac8;"
        "border-left:3px solid #00c882;padding-left:0.6rem;'>"
        "Company Breakdown by Quadrant</div>",
        unsafe_allow_html=True
    )
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    for qcol, (qname, qdata) in zip([q_col1, q_col2, q_col3, q_col4], q_groups.items()):
        companies = qdata["companies"]
        clr    = qdata["color"]
        bg     = qdata["bg"]
        border = qdata["border"]
        # Header badge
        qcol.markdown(
            '<div style="background:' + bg + ';border:1px solid ' + border +
            ';border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:0.6rem;">'
            '<div style="font-size:0.68rem;font-weight:700;color:' + clr + ';letter-spacing:0.06em;">' + qname + '</div>'
            '<div style="font-size:0.72rem;color:#8aaac8;margin-top:2px;">' + str(len(companies)) + ' companies</div>'
            '</div>',
            unsafe_allow_html=True
        )
        if companies:
            for sym, name, pe, roe in companies:
                disp_name = name if name and name != sym else sym
                qcol.markdown(
                    '<div style="padding:0.45rem 0.6rem;border-left:2px solid ' + clr +
                    ';margin-bottom:0.35rem;background:#0b1525;border-radius:0 6px 6px 0;">'
                    '<div style="font-size:0.75rem;font-weight:600;color:#e8f0ff;">' + sym + '</div>'
                    '<div style="font-size:0.68rem;color:#8aaac8;margin-top:1px;">' + disp_name + '</div>'
                    '<div style="font-size:0.65rem;color:' + clr + ';margin-top:2px;">PE ' + str(round(pe,1)) + '  ROE ' + str(round(roe,1)) + '%</div>'
                    '</div>',
                    unsafe_allow_html=True
                )
        else:
            qcol.markdown('<div style="font-size:0.72rem;color:#4a6080;padding:0.4rem;">None in this quadrant</div>', unsafe_allow_html=True)

# -- Top performers ----------------------------------------------------------
st.markdown('<div class="section-label">// top performers</div>', unsafe_allow_html=True)

if qualified:
    qualified_sorted = sorted(qualified, key=lambda x: x["Score"], reverse=True)

    q_cols = st.columns(3)
    for i, q in enumerate(qualified_sorted):
        col   = q_cols[i % 3]
        sym   = q["_sym"]
        name  = q["Company"] or sym
        score = q["Score"]
        mcap  = q["MCap"]
        col.markdown(
            '<div class="qualify-badge">'
            '<div>'
            '<div class="qualify-name">' + name + '</div>'
            '<div class="qualify-sym">' + sym + ' · ' + mcap + '</div>'
            '</div>'
            '<div class="qualify-score">' + str(score) + '/5</div>'
            '</div>',
            unsafe_allow_html=True
        )
        if col.button("View " + sym, key="goto_" + sym + "_" + str(i)):
            st.session_state["compare_symbol"] = sym
            st.session_state["already_loaded_from_sector"] = False
            st.switch_page("pages/1_Fundamentals.py")
else:
    st.info("No company meets 3 / 5 green signals in this industry. Try a different industry.")

# -- Footer ------------------------------------------------------------------
st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:2rem 0 1rem;'>", unsafe_allow_html=True)
st.markdown("""
    <div style="font-family:'DM Mono',monospace;font-size:0.65rem;color: #6a88a8;">
        Fundamentals sourced from Yahoo Finance via yfinance · Industry averages from cached DB
    </div>
""", unsafe_allow_html=True)
