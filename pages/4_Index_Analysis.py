import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.signal import argrelextrema
from indicators import compute_rsi

st.set_page_config(
    page_title="Index Analysis",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 3.5rem !important; padding-bottom: 2rem; }

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
.stat-card {
    background: #0d1628;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 1.1rem 1.3rem;
    position: relative; overflow: hidden;
}
.stat-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #00c882, transparent);
}
.stat-label {
    font-size: 0.68rem !important; letter-spacing: 0.12em;
    text-transform: uppercase; color: #8aaac8; margin-bottom: 0.4rem;
}
.stat-value {
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem !important; font-weight: 700; color: #f0f4ff;
    font-variant-numeric: tabular-nums; line-height: 1;
}
.stat-value.up   { color: #00c882; }
.stat-value.down { color: #ff4d6a; }
.stat-sub { font-size: 0.68rem !important; color: #8aaac8; margin-top: 0.3rem; }

.insight-card {
    border-radius: 10px; padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem; display: flex;
    align-items: flex-start; gap: 0.8rem;
}
.insight-card.green  { background: rgba(0,200,130,0.08);  border: 1px solid rgba(0,200,130,0.25); }
.insight-card.red    { background: rgba(255,77,106,0.08); border: 1px solid rgba(255,77,106,0.25); }
.insight-card.yellow { background: rgba(245,166,35,0.08); border: 1px solid rgba(245,166,35,0.25); }
.insight-card.blue   { background: rgba(110,198,255,0.08);border: 1px solid rgba(110,198,255,0.25); }
.insight-icon { font-size: 1.0rem !important; line-height: 1.4; flex-shrink: 0; }
.insight-text { font-size: 0.78rem !important; color: #c0d4e8; line-height: 1.5; }
.insight-text strong { color: #f0f4ff; }

.rec-card {
    border-radius: 12px; padding: 1.3rem 1.6rem;
    margin-top: 0.4rem; text-align: center;
    border: 1px solid;
}
.rec-card.buy    { background: rgba(0,200,130,0.1);  border-color: #00c882; }
.rec-card.hold   { background: rgba(110,198,255,0.1);border-color: #6ec6ff; }
.rec-card.avoid  { background: rgba(255,77,106,0.1); border-color: #ff4d6a; }
.rec-card.watch  { background: rgba(245,166,35,0.1); border-color: #f5a623; }
.rec-label {
    font-size: 0.68rem !important; letter-spacing: 0.18em;
    text-transform: uppercase; color: #8aaac8; margin-bottom: 0.4rem;
}
.rec-value {
    font-family: 'Syne', sans-serif;
    font-size: 1.4rem !important; font-weight: 800; line-height: 1;
}
.rec-card.buy   .rec-value { color: #00c882; }
.rec-card.hold  .rec-value { color: #6ec6ff; }
.rec-card.avoid .rec-value { color: #ff4d6a; }
.rec-card.watch .rec-value { color: #f5a623; }
.rec-sub { font-size: 0.68rem !important; color: #8aaac8; margin-top: 0.5rem; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">📉 Index Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">// Select an index · read technicals · spot signals</div>', unsafe_allow_html=True)

# ── Index selector ────────────────────────────────────────────────────────────
INDEX_OPTIONS = {
    "NIFTY 50":    "^NSEI",
    "SENSEX":      "^BSESN",
    "NIFTY Bank":  "^NSEBANK",
    "NIFTY IT":    "^CNXIT",
    "NIFTY FMCG":  "^CNXFMCG",
    "NIFTY Auto":  "^CNXAUTO",
    "NIFTY Pharma":"^CNXPHARMA",
}

sel_cols = st.columns([2, 6])
selected_index = sel_cols[0].selectbox(
    "index", list(INDEX_OPTIONS.keys()),
    label_visibility="collapsed"
)
index_symbol = INDEX_OPTIONS[selected_index]

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading " + selected_index + "..."):
    df = yf.Ticker(index_symbol).history(period="2y", interval="1d").reset_index()

if df.empty:
    st.error("No data available for " + selected_index)
    st.stop()

df["Date"] = pd.to_datetime(df["Date"])
df.set_index("Date", inplace=True)

# Indicators
df["EMA_9"]  = df["Close"].ewm(span=9,  adjust=False).mean()
df["EMA_15"] = df["Close"].ewm(span=15, adjust=False).mean()
df["SMA_50"] = df["Close"].rolling(50).mean()
df["RSI"]    = compute_rsi(df)

df["Prev_1d"]   = df["Close"].shift(1)
df["Prev_30d"]  = df["Close"].shift(30)
df["Prev_250d"] = df["Close"].shift(250)

price        = float(df["Close"].iloc[-1])
day_ago      = df["Prev_1d"].iloc[-1]
month_ago    = df["Prev_30d"].iloc[-1]
year_ago     = df["Prev_250d"].iloc[-1]
latest_rsi   = float(df["RSI"].iloc[-1])
prev_rsi     = float(df["RSI"].iloc[-2]) if len(df) > 1 else latest_rsi
latest_ema9  = float(df["EMA_9"].iloc[-1])
latest_ema15 = float(df["EMA_15"].iloc[-1])
ema15_5d_ago = float(df["EMA_15"].iloc[-5])
latest_sma50 = float(df["SMA_50"].iloc[-1]) if df["SMA_50"].notna().any() else None

df.reset_index(inplace=True)

def pct(cur, prev):
    return round((cur - prev) / prev * 100, 2) if pd.notna(prev) and prev != 0 else None

day_chg   = pct(price, day_ago)
month_chg = pct(price, month_ago)
year_chg  = pct(price, year_ago)

def fmt_pct(v):
    if v is None: return "N/A"
    arrow = "▲" if v >= 0 else "▼"
    return arrow + " " + str(abs(v)) + "%"

def val_class(v):
    if v is None: return ""
    return "up" if v >= 0 else "down"

# ── Snapshot cards ────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">// snapshot</div>', unsafe_allow_html=True)
sc1, sc2, sc3, sc4, sc5 = st.columns(5)

rsi_cls = "up" if latest_rsi < 50 else "down" if latest_rsi > 65 else ""
rsi_arrow = "↑" if latest_rsi >= prev_rsi else "↓"

for col, label, val, sub, cls in [
    (sc1, "Price",      "Rs." + f"{price:,.2f}",            selected_index,        ""),
    (sc2, "1 Day",      fmt_pct(day_chg),                   "vs yesterday",         val_class(day_chg)),
    (sc3, "1 Month",    fmt_pct(month_chg),                 "vs 30 days ago",       val_class(month_chg)),
    (sc4, "1 Year",     fmt_pct(year_chg),                  "vs 250 days ago",      val_class(year_chg)),
    (sc5, "RSI (14)",   str(round(latest_rsi, 1)) + " " + rsi_arrow, "overbought>70 oversold<30", rsi_cls),
]:
    col.markdown(
        '<div class="stat-card">'
        '<div class="stat-label">' + label + '</div>'
        '<div class="stat-value ' + cls + '">' + str(val) + '</div>'
        '<div class="stat-sub">' + sub + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

# ── Combined interactive chart: candlestick + RSI subplot ────────────────────
from plotly.subplots import make_subplots

st.markdown('<div class="section-label">// candlestick · EMA 9 · EMA 15 · SMA 50 · RSI</div>', unsafe_allow_html=True)

plot_df = df.copy()

fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=[0.72, 0.28],
)

# ── Row 1: Candlestick + EMAs ─────────────────────────────────────────────────
fig.add_trace(go.Candlestick(
    x=plot_df["Date"],
    open=plot_df["Open"], high=plot_df["High"],
    low=plot_df["Low"],   close=plot_df["Close"],
    increasing_line_color="#00c882",
    decreasing_line_color="#ff4d6a",
    increasing_fillcolor="#00c882",
    decreasing_fillcolor="#ff4d6a",
    name="Price",
    hovertext=plot_df["Date"].dt.strftime("%d %b %Y"),
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=plot_df["Date"], y=plot_df["EMA_9"],
    mode="lines", name="EMA 9",
    line=dict(color="#f5a623", width=1.5),
    hovertemplate="EMA 9: %{y:,.2f}<extra></extra>",
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=plot_df["Date"], y=plot_df["EMA_15"],
    mode="lines", name="EMA 15",
    line=dict(color="#6ec6ff", width=1.5),
    hovertemplate="EMA 15: %{y:,.2f}<extra></extra>",
), row=1, col=1)

if latest_sma50:
    fig.add_trace(go.Scatter(
        x=plot_df["Date"], y=plot_df["SMA_50"],
        mode="lines", name="SMA 50",
        line=dict(color="#c084fc", width=1.2, dash="dot"),
        hovertemplate="SMA 50: %{y:,.2f}<extra></extra>",
    ), row=1, col=1)

# ── Row 2: RSI ────────────────────────────────────────────────────────────────
fig.add_trace(go.Scatter(
    x=plot_df["Date"], y=plot_df["RSI"],
    mode="lines", name="RSI",
    line=dict(color="#6ec6ff", width=1.5),
    fill="tozeroy", fillcolor="rgba(110,198,255,0.04)",
    hovertemplate="RSI: %{y:.1f}<extra></extra>",
), row=2, col=1)

# Overbought / oversold bands on RSI
fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,77,106,0.06)",
              line_width=0, row=2, col=1)
fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,200,130,0.06)",
              line_width=0, row=2, col=1)
fig.add_hline(y=70, line_color="#ff4d6a", line_dash="dash", line_width=0.8,
              annotation_text="70", annotation_font=dict(color="#ff4d6a", size=9),
              annotation_position="right", row=2, col=1)
fig.add_hline(y=30, line_color="#00c882", line_dash="dash", line_width=0.8,
              annotation_text="30", annotation_font=dict(color="#00c882", size=9),
              annotation_position="right", row=2, col=1)

# ── Layout ────────────────────────────────────────────────────────────────────
fig.update_xaxes(
    rangebreaks=[dict(bounds=["sat", "sun"])],
    showgrid=False, color="#8aaac8",
    rangeslider_visible=False,
)
fig.update_yaxes(
    showgrid=True, gridcolor="rgba(255,255,255,0.05)",
    color="#8aaac8",
)
fig.update_layout(
    paper_bgcolor="#080d1a",
    plot_bgcolor="#080d1a",
    font=dict(family="Inter", color="#c0d4e8", size=11),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="#0d1e35",
        bordercolor="rgba(255,255,255,0.15)",
        font=dict(family="Inter", color="#e8f0ff", size=11),
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.01,
        xanchor="left", x=0,
        bgcolor="rgba(8,13,26,0.0)",
        font=dict(size=11),
    ),
    dragmode="pan",
    margin=dict(l=10, r=40, t=40, b=10),
    height=620,
    yaxis2=dict(range=[0, 100]),
    xaxis_showticklabels=True,
    xaxis2_showticklabels=True,
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "scrollZoom": True,
        "displayModeBar": True,
        "modeBarButtonsToRemove": ["autoScale2d", "lasso2d", "select2d"],
        "modeBarButtonsToAdd": ["drawline", "eraseshape"],
        "toImageButtonOptions": {"format": "png", "filename": selected_index + "_chart"},
    }
)

# ── Insights ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">// technical insights</div>', unsafe_allow_html=True)

ic1, ic2 = st.columns(2)

# EMA crossover
with ic1:
    if latest_ema9 > latest_ema15:
        st.markdown(
            '<div class="insight-card green">'
            '<div class="insight-icon">✅</div>'
            '<div class="insight-text"><strong>Bullish momentum</strong> — EMA 9 is above EMA 15. Short-term trend is positive.</div>'
            '</div>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="insight-card red">'
            '<div class="insight-icon">❌</div>'
            '<div class="insight-text"><strong>Bearish momentum</strong> — EMA 9 is below EMA 15. Short-term trend is negative.</div>'
            '</div>', unsafe_allow_html=True
        )

# EMA 15 slope
with ic2:
    if latest_ema15 > ema15_5d_ago:
        st.markdown(
            '<div class="insight-card green">'
            '<div class="insight-icon">📈</div>'
            '<div class="insight-text"><strong>Trend strengthening</strong> — EMA 15 is sloping upward over the last 5 sessions.</div>'
            '</div>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="insight-card yellow">'
            '<div class="insight-icon">📉</div>'
            '<div class="insight-text"><strong>Trend weakening</strong> — EMA 15 is sloping downward over the last 5 sessions.</div>'
            '</div>', unsafe_allow_html=True
        )

ic3, ic4 = st.columns(2)

# RSI signal
with ic3:
    if latest_rsi > 70:
        st.markdown(
            '<div class="insight-card yellow">'
            '<div class="insight-icon">⚠️</div>'
            '<div class="insight-text"><strong>Overbought</strong> — RSI at ' + str(round(latest_rsi, 1)) + '. Potential short-term pullback.</div>'
            '</div>', unsafe_allow_html=True
        )
    elif latest_rsi < 30:
        st.markdown(
            '<div class="insight-card green">'
            '<div class="insight-icon">🔄</div>'
            '<div class="insight-text"><strong>Oversold</strong> — RSI at ' + str(round(latest_rsi, 1)) + '. Potential rebound opportunity.</div>'
            '</div>', unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="insight-card blue">'
            '<div class="insight-icon">⚖️</div>'
            '<div class="insight-text"><strong>Neutral RSI</strong> — at ' + str(round(latest_rsi, 1)) + '. No strong overbought or oversold signal.</div>'
            '</div>', unsafe_allow_html=True
        )

# Price vs SMA 50
with ic4:
    if latest_sma50:
        above = price > latest_sma50
        diff  = round(abs(price - latest_sma50) / latest_sma50 * 100, 2)
        cls   = "green" if above else "red"
        icon  = "🟢" if above else "🔴"
        dirn  = "above" if above else "below"
        st.markdown(
            '<div class="insight-card ' + cls + '">'
            '<div class="insight-icon">' + icon + '</div>'
            '<div class="insight-text"><strong>Price vs SMA 50</strong> — currently ' + dirn + ' the 50-day average by ' + str(diff) + '%.</div>'
            '</div>', unsafe_allow_html=True
        )

# ── Recommendation ────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">// signal</div>', unsafe_allow_html=True)

buy_signal   = latest_ema9 > latest_ema15 and latest_rsi < 50 and latest_ema15 > ema15_5d_ago
avoid_signal = latest_ema9 < latest_ema15 and latest_ema15 < ema15_5d_ago
wait_signal  = latest_ema9 > latest_ema15 and 50 <= latest_rsi <= 65

if buy_signal:
    css, label, sub = "buy",   "BUY",   "Bullish crossover with strengthening trend and RSI below 50."
elif avoid_signal:
    css, label, sub = "avoid", "AVOID", "Bearish alignment and weakening EMA trend. Stay cautious."
elif wait_signal:
    css, label, sub = "hold",  "HOLD",  "Momentum improving but no clear breakout yet. Monitor closely."
else:
    css, label, sub = "watch", "WATCH", "Mixed signals. No strong directional confirmation."

_, rec_col, _ = st.columns([2, 2, 2])
rec_col.markdown(
    '<div class="rec-card ' + css + '">'
    '<div class="rec-label">Recommendation</div>'
    '<div class="rec-value">' + label + '</div>'
    '<div class="rec-sub">' + sub + '</div>'
    '</div>',
    unsafe_allow_html=True
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:2rem 0 1rem;'>", unsafe_allow_html=True)
st.markdown(
    "<div style='font-size:0.68rem !important;color:#6a88a8;'>"
    "Data sourced from Yahoo Finance via yfinance · 2-year daily history"
    "</div>",
    unsafe_allow_html=True
)
