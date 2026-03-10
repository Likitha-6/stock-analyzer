import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from common.data import load_name_lookup
from indicators import apply_ema, get_pivot_lines
from indicators import detect_cross_signals, compute_rsi, detect_crossovers
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title=“Technical Analysis”, layout=“wide”, page_icon=“📈”)

# ─────────────────────────────────────────────────────────────

# Custom CSS – cleaner UI

# ─────────────────────────────────────────────────────────────

st.markdown(”””

<style>
    /* Tighten top padding */
    .block-container { padding-top: 1rem; padding-bottom: 0.5rem; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #1c1f2e;
        border: 1px solid #2e3150;
        border-radius: 10px;
        padding: 12px 16px;
    }
    [data-testid="metric-container"] label { font-size: 0.75rem; color: #8b93b8; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.25rem; font-weight: 700; color: #e2e8f0;
    }

    /* Tab style */
    button[data-baseweb="tab"] { font-size: 0.9rem; font-weight: 600; }

    /* Search bar */
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #2e3150;
        background: #1c1f2e;
        color: #e2e8f0;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 8px;
        background: #1c1f2e;
    }

    /* Info/Success/Warning boxes */
    .stAlert { border-radius: 8px; }

    /* Sidebar width */
    section[data-testid="stSidebar"] { min-width: 280px; max-width: 320px; }

    /* Chart container */
    .chart-container { border-radius: 12px; overflow: hidden; }
</style>

“””, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────

# Cached data fetcher — avoids re-fetching on every widget change

# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ohlcv(symbol: str, interval: str, period: str) -> pd.DataFrame:
df = yf.Ticker(symbol + “.NS”).history(interval=interval, period=period)
return df.reset_index() if not df.empty else pd.DataFrame()

@st.cache_data(ttl=600, show_spinner=False)
def fetch_insights_data(symbol: str) -> pd.DataFrame:
df = yf.Ticker(symbol + “.NS”).history(interval=“1d”, period=“12mo”)
return df.reset_index() if not df.empty else pd.DataFrame()

@st.cache_data(ttl=600, show_spinner=False)
def fetch_view_data(symbol: str):
stock_df = yf.Ticker(symbol + “.NS”).history(period=“6mo”, interval=“1d”).reset_index()
nifty_df = yf.Ticker(”^NSEI”).history(period=“6mo”, interval=“1d”).reset_index()
ratings_df = yf.Ticker(symbol + “.NS”).recommendations
return stock_df, nifty_df, ratings_df

# ─────────────────────────────────────────────────────────────

# Header

# ─────────────────────────────────────────────────────────────

col_title, col_theme = st.columns([5, 1])
with col_title:
st.markdown(”## 📈 Indian Stock – Technical Analysis”)
with col_theme:
dark_mode = st.toggle(“🌙 Dark”, value=True)

theme = “Dark” if dark_mode else “Light”
bg_color        = “#0E1117” if dark_mode else “#FFFFFF”
paper_bg        = “#161b2e” if dark_mode else “#f8f9fa”
font_color      = “#e2e8f0” if dark_mode else “#1a1a2e”
grid_color      = “#1e2340” if dark_mode else “#e9ecef”
increasing_color = “#00d97e” if dark_mode else “#00B26F”
decreasing_color = “#ff4d6d” if dark_mode else “#FF3C38”

# ─────────────────────────────────────────────────────────────

# Stock Search

# ─────────────────────────────────────────────────────────────

name_df = load_name_lookup()
symbol2name = dict(zip(name_df[“Symbol”], name_df[“Company Name”]))

st.markdown(”—”)
search_query = st.text_input(“🔍 Search by Symbol or Company Name”, placeholder=“e.g. RELIANCE or Infosys”).strip().lower()
chosen_sym = None

if search_query:
mask = (
name_df[“Symbol”].str.lower().str.contains(search_query) |
name_df[“Company Name”].str.lower().str.contains(search_query)
)
matches = name_df[mask]
if matches.empty:
st.warning(“No matching stock found.”)
else:
selected = st.selectbox(
“Select Stock”,
matches[“Symbol”] + “ – “ + matches[“Company Name”],
label_visibility=“collapsed”
)
chosen_sym = selected.split(” – “)[0]

```
    # Show chosen stock badge
    st.markdown(
        f"<span style='background:#1e3a5f;color:#60a5fa;padding:4px 12px;"
        f"border-radius:20px;font-weight:600;font-size:0.85rem;'>"
        f"📌 {chosen_sym} · {symbol2name.get(chosen_sym, '')}</span>",
        unsafe_allow_html=True
    )
```

st.markdown(”—”)

# ─────────────────────────────────────────────────────────────

# Tabs

# ─────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([“📊 Chart”, “💡 Insights”, “🌐 Market View”])

# ══════════════════════════════════════════════════════════════

# TAB 1 – CHART

# ══════════════════════════════════════════════════════════════

with tab1:
# ── Controls row ──
ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 3])

```
with ctrl1:
    interval_mapping = {
        "5 min": "5m",
        "15 min": "15m",
        "1 Hour": "60m",
        "1 Day": "1d",
    }
    label    = st.selectbox("⏱ Interval", list(interval_mapping.keys()), index=3)
    interval = interval_mapping[label]

with ctrl2:
    period_mapping = {
        "5 min":  {"1 Day": "1d", "2 Days": "2d", "5 Days": "5d"},
        "15 min": {"2 Days": "2d", "5 Days": "5d", "10 Days": "10d"},
        "1 Hour": {"5 Days": "5d", "1 Month": "1mo", "3 Months": "3mo"},
        "1 Day":  {"1 Month": "1mo", "3 Months": "3mo", "6 Months": "6mo", "1 Year": "1y"},
    }
    period_opts = period_mapping[label]
    period_label = st.selectbox("📅 Period", list(period_opts.keys()))
    period = period_opts[period_label]

with ctrl3:
    ema_options = st.multiselect(
        "📐 Overlays",
        ["EMA 9", "EMA 20", "EMA 50", "EMA 200", "Support/Resistance"],
        default=["EMA 20", "Support/Resistance"]
    )

show_rsi    = st.checkbox("Show RSI subplot", value=True)
show_volume = st.checkbox("Show Volume subplot", value=True)

# ── Chart ──
if chosen_sym:
    with st.spinner(f"Loading {chosen_sym} data..."):
        df = fetch_ohlcv(chosen_sym, interval, period)

    if df.empty:
        st.error("No data found for this symbol / interval.")
    else:
        x_col = "Datetime" if "Datetime" in df.columns else "Date"
        is_intraday = any(k in interval for k in ("m", "h"))
        df["x_label"] = (
            df[x_col].dt.strftime("%d/%m %H:%M") if is_intraday
            else df[x_col].dt.strftime("%d %b '%y")
        )

        # ── EMA columns ──
        ema_map = {"EMA 9": 9, "EMA 20": 20, "EMA 50": 50, "EMA 200": 200}
        ema_lengths = [ema_map[e] for e in ema_options if e in ema_map]
        if ema_lengths:
            df = apply_ema(df, ema_lengths)

        # ── Support / Resistance ──
        show_sr = "Support/Resistance" in ema_options
        if show_sr:
            if interval == "5m":
                sr_df = df[df[x_col].dt.date == df[x_col].max().date()]
            elif interval == "15m":
                sr_df = df[df[x_col].dt.date >= (df[x_col].max().date() - pd.Timedelta(days=7))]
            else:
                sr_df = df
            support    = sr_df["Low"].min()
            resistance = sr_df["High"].max()

        # ── Build subplots ──
        n_rows   = 1 + int(show_volume) + int(show_rsi)
        row_heights = [0.6]
        if show_volume: row_heights.append(0.2)
        if show_rsi:    row_heights.append(0.2)
        subplot_titles = [f"{chosen_sym}.NS – {label} ({period_label})"]
        if show_volume: subplot_titles.append("Volume")
        if show_rsi:    subplot_titles.append("RSI (14)")

        fig = make_subplots(
            rows=n_rows, cols=1, shared_xaxes=True,
            row_heights=row_heights,
            vertical_spacing=0.03,
            subplot_titles=subplot_titles
        )

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df["x_label"],
            open=df["Open"], high=df["High"],
            low=df["Low"],   close=df["Close"],
            increasing_line_color=increasing_color,
            decreasing_line_color=decreasing_color,
            increasing_fillcolor=increasing_color,
            decreasing_fillcolor=decreasing_color,
            name="Price", showlegend=False
        ), row=1, col=1)

        # Support / Resistance lines
        if show_sr:
            fig.add_hline(y=support, line_dash="dot", line_width=1.2,
                          line_color="#2ecc71", row=1, col=1,
                          annotation=dict(text=f"  S {support:.1f}",
                                          font=dict(color="#2ecc71", size=10)))
            fig.add_hline(y=resistance, line_dash="dot", line_width=1.2,
                          line_color="#e74c3c", row=1, col=1,
                          annotation=dict(text=f"  R {resistance:.1f}",
                                          font=dict(color="#e74c3c", size=10),
                                          yanchor="bottom"))

        # EMA overlays
        ema_colors = {9: "#f59e0b", 20: "#3b82f6", 50: "#a78bfa", 200: "#f43f5e"}
        for ema_len in ema_lengths:
            col_name = f"EMA_{ema_len}"
            if col_name in df.columns:
                fig.add_trace(go.Scatter(
                    x=df["x_label"], y=df[col_name],
                    mode="lines",
                    line=dict(width=1.5, color=ema_colors.get(ema_len, "#ffffff")),
                    name=f"EMA {ema_len}", opacity=0.85
                ), row=1, col=1)

        # Crossover signals (EMA 20 vs 50)
        if "EMA_20" in df.columns and "EMA_50" in df.columns:
            signals = detect_crossovers(df, short_col="EMA_20", long_col="EMA_50")
            if signals["buy"]:
                buy_x = [df["x_label"].iloc[i] for i in signals["buy"]]
                buy_y = [df["Close"].iloc[i] for i in signals["buy"]]
                fig.add_trace(go.Scatter(
                    x=buy_x, y=buy_y, mode="markers",
                    marker=dict(color="#00d97e", size=11, symbol="triangle-up",
                                line=dict(color="white", width=1)),
                    name="Buy Signal"
                ), row=1, col=1)
            if signals["sell"]:
                sell_x = [df["x_label"].iloc[i] for i in signals["sell"]]
                sell_y = [df["Close"].iloc[i] for i in signals["sell"]]
                fig.add_trace(go.Scatter(
                    x=sell_x, y=sell_y, mode="markers",
                    marker=dict(color="#ff4d6d", size=11, symbol="triangle-down",
                                line=dict(color="white", width=1)),
                    name="Sell Signal"
                ), row=1, col=1)

        # Volume subplot
        vol_row = 2 if show_volume else None
        if show_volume:
            vol_colors = [
                increasing_color if c >= o else decreasing_color
                for c, o in zip(df["Close"], df["Open"])
            ]
            fig.add_trace(go.Bar(
                x=df["x_label"], y=df["Volume"],
                marker_color=vol_colors, name="Volume",
                opacity=0.7, showlegend=False
            ), row=vol_row, col=1)

        # RSI subplot
        rsi_row = (2 if not show_volume else 3) if show_rsi else None
        if show_rsi:
            rsi_series = compute_rsi(df)
            fig.add_trace(go.Scatter(
                x=df["x_label"], y=rsi_series,
                mode="lines", line=dict(color="#a78bfa", width=1.5),
                name="RSI", showlegend=False
            ), row=rsi_row, col=1)
            # Overbought/oversold bands
            for lvl, clr in [(70, "rgba(255,77,109,0.15)"), (30, "rgba(0,217,126,0.15)")]:
                fig.add_hline(y=lvl, line_dash="dot", line_width=1,
                              line_color="#555577", row=rsi_row, col=1)
            fig.add_hrect(y0=70, y1=100, fillcolor="rgba(255,77,109,0.05)",
                          line_width=0, row=rsi_row, col=1)
            fig.add_hrect(y0=0, y1=30, fillcolor="rgba(0,217,126,0.05)",
                          line_width=0, row=rsi_row, col=1)

        # ── Layout ──
        total_candles = len(df)
        N        = max(1, total_candles // 12)
        tickvals = df["x_label"].iloc[::N].tolist()

        common_axis = dict(
            showgrid=True, gridcolor=grid_color, gridwidth=0.5,
            zeroline=False, tickfont=dict(color=font_color, size=10),
            linecolor=grid_color
        )

        fig.update_layout(
            plot_bgcolor=bg_color,
            paper_bgcolor=paper_bg,
            font=dict(color=font_color, family="Inter, sans-serif"),
            legend=dict(
                font=dict(color=font_color, size=11),
                bgcolor="rgba(0,0,0,0.3)",
                bordercolor=grid_color,
                borderwidth=1,
                orientation="h",
                yanchor="bottom", y=1.01, xanchor="left", x=0
            ),
            xaxis_rangeslider_visible=False,
            dragmode="pan",
            hovermode="x unified",
            height=500 + 150 * int(show_volume) + 150 * int(show_rsi),
            margin=dict(l=10, r=60, t=60, b=30),
        )

        # Apply axis styles to each row
        for i in range(1, n_rows + 1):
            fig.update_xaxes(
                **common_axis,
                type="category",
                tickangle=-40,
                tickmode="array",
                tickvals=tickvals,
                ticktext=tickvals,
                row=i, col=1
            )
            fig.update_yaxes(**common_axis, row=i, col=1)

        st.plotly_chart(fig, use_container_width=True, config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["zoom2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d"],
            "displaylogo": False
        })

        # ── Quick stats strip ──
        latest = df["Close"].iloc[-1]
        prev   = df["Close"].iloc[-2] if len(df) > 1 else latest
        chg    = latest - prev
        chg_pct = (chg / prev) * 100
        hi     = df["High"].max()
        lo     = df["Low"].min()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Last Price", f"₹{latest:,.2f}", f"{chg:+.2f} ({chg_pct:+.2f}%)")
        m2.metric("Period High", f"₹{hi:,.2f}")
        m3.metric("Period Low",  f"₹{lo:,.2f}")
        m4.metric("Candles",     f"{len(df):,}")
        avg_vol = df["Volume"].mean()
        m5.metric("Avg Volume",  f"{int(avg_vol):,}")

else:
    st.info("👆 Search and select a stock above to load the chart.")
```

# ══════════════════════════════════════════════════════════════

# TAB 2 – INSIGHTS

# ══════════════════════════════════════════════════════════════

with tab2:
if not chosen_sym:
st.info(“👆 Select a stock to view insights.”)
else:
with st.spinner(“Computing insights…”):
df_ins = fetch_insights_data(chosen_sym)

```
    if df_ins.empty:
        st.warning("Not enough data.")
    else:
        df_ins["SMA_50"]  = df_ins["Close"].rolling(50).mean()
        df_ins["SMA_200"] = df_ins["Close"].rolling(200).mean()
        df_ins["EMA_20"]  = df_ins["Close"].ewm(span=20, adjust=False).mean()
        df_ins["RSI"]     = compute_rsi(df_ins)

        high_52w    = df_ins["High"].max()
        low_52w     = df_ins["Low"].min()
        latest_price = df_ins["Close"].iloc[-1]
        latest_sma50 = df_ins["SMA_50"].iloc[-1]
        latest_sma200 = df_ins["SMA_200"].iloc[-1]
        latest_rsi   = df_ins["RSI"].iloc[-1]
        latest_ema20 = df_ins["EMA_20"].iloc[-1]

        # ── Key Metrics ──
        st.markdown("### 📌 Key Levels")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Current Price", f"₹{latest_price:,.2f}")
        m2.metric("SMA 50",  f"₹{latest_sma50:,.2f}"  if pd.notna(latest_sma50)  else "N/A")
        m3.metric("SMA 200", f"₹{latest_sma200:,.2f}" if pd.notna(latest_sma200) else "N/A")
        m4.metric("52W High", f"₹{high_52w:,.2f}")
        m5.metric("52W Low",  f"₹{low_52w:,.2f}")

        st.markdown("---")

        # ── RSI Gauge ──
        col_rsi, col_signals = st.columns([1, 2])
        with col_rsi:
            st.markdown("### 📊 RSI (14-day)")
            rsi_color = "#ff4d6d" if latest_rsi > 70 else ("#00d97e" if latest_rsi < 30 else "#a78bfa")
            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=latest_rsi,
                number={"font": {"color": rsi_color, "size": 32}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": font_color,
                             "tickfont": {"color": font_color}},
                    "bar":  {"color": rsi_color},
                    "steps": [
                        {"range": [0, 30],   "color": "rgba(0,217,126,0.15)"},
                        {"range": [30, 70],  "color": "rgba(167,139,250,0.1)"},
                        {"range": [70, 100], "color": "rgba(255,77,109,0.15)"},
                    ],
                    "threshold": {"line": {"color": "white", "width": 2},
                                  "thickness": 0.75, "value": latest_rsi},
                    "bgcolor": bg_color,
                    "bordercolor": grid_color,
                }
            ))
            gauge.update_layout(
                paper_bgcolor=paper_bg, font=dict(color=font_color),
                height=220, margin=dict(l=20, r=20, t=30, b=10)
            )
            st.plotly_chart(gauge, use_container_width=True)

            if latest_rsi > 70:
                st.warning("⚠️ Overbought — momentum may slow.")
            elif latest_rsi < 30:
                st.success("✅ Oversold — potential rebound ahead.")
            else:
                st.info("🔵 RSI neutral — no extreme signal.")

        with col_signals:
            st.markdown("### 🧠 Signal Checklist")

            def signal_row(icon, label, msg, kind="info"):
                colors = {"good": "#00d97e", "bad": "#ff4d6d", "info": "#60a5fa", "neutral": "#8b93b8"}
                bg     = {"good": "rgba(0,217,126,0.1)", "bad": "rgba(255,77,109,0.1)",
                          "info": "rgba(96,165,250,0.1)", "neutral": "rgba(139,147,184,0.1)"}
                st.markdown(
                    f"<div style='background:{bg[kind]};border-left:3px solid {colors[kind]};"
                    f"border-radius:6px;padding:8px 12px;margin-bottom:8px;'>"
                    f"<b style='color:{colors[kind]}'>{icon} {label}</b> — "
                    f"<span style='color:#c0c8e8'>{msg}</span></div>",
                    unsafe_allow_html=True
                )

            # EMA slope
            if df_ins["EMA_20"].iloc[-1] > df_ins["EMA_20"].iloc[-5]:
                signal_row("📈", "EMA 20 Slope", "Trending up — short-term bullish", "good")
            else:
                signal_row("📉", "EMA 20 Slope", "Trending down — short-term weak", "bad")

            # Price vs SMA 50
            if pd.notna(latest_sma50):
                if latest_price > latest_sma50:
                    signal_row("✅", "Price vs SMA 50", f"₹{latest_price:.0f} above ₹{latest_sma50:.0f}", "good")
                else:
                    signal_row("❌", "Price vs SMA 50", f"₹{latest_price:.0f} below ₹{latest_sma50:.0f}", "bad")

            # Golden / death cross
            cross_signal = detect_cross_signals(df_ins)
            if cross_signal:
                kind = "good" if "Golden" in cross_signal or "Bullish" in cross_signal else "bad"
                signal_row("🔁", "SMA Cross", cross_signal.replace("✅","").replace("❌","").strip(), kind)

            # 52-week proximity
            if abs(latest_price - high_52w) < 0.03 * high_52w:
                signal_row("🚀", "52W High", "Near 52-week high — watch for resistance", "info")
            elif abs(latest_price - low_52w) < 0.03 * low_52w:
                signal_row("🔻", "52W Low", "Near 52-week low — potential support", "neutral")

            # Volatility
            recent_close = df_ins["Close"].tail(14)
            vol_pct = (recent_close.std() / latest_price) * 100
            if vol_pct > 5:
                signal_row("⚡", "Volatility", f"{vol_pct:.1f}% — high, expect wide swings", "bad")
            elif vol_pct < 2:
                signal_row("😴", "Volatility", f"{vol_pct:.1f}% — low, stable price action", "neutral")
            else:
                signal_row("⚖️", "Volatility", f"{vol_pct:.1f}% — moderate, balanced risk", "good")

        st.markdown("---")

        # ── Price history mini-chart ──
        st.markdown("### 📉 Price History (12 months)")
        mini_fig = go.Figure()
        mini_fig.add_trace(go.Scatter(
            x=df_ins["Date"], y=df_ins["Close"],
            mode="lines", fill="tozeroy",
            line=dict(color="#3b82f6", width=2),
            fillcolor="rgba(59,130,246,0.08)",
            name="Close"
        ))
        if pd.notna(latest_sma50):
            mini_fig.add_trace(go.Scatter(
                x=df_ins["Date"], y=df_ins["SMA_50"],
                mode="lines", line=dict(color="#f59e0b", width=1.2, dash="dot"), name="SMA 50"
            ))
        if pd.notna(latest_sma200):
            mini_fig.add_trace(go.Scatter(
                x=df_ins["Date"], y=df_ins["SMA_200"],
                mode="lines", line=dict(color="#f43f5e", width=1.2, dash="dot"), name="SMA 200"
            ))
        mini_fig.update_layout(
            plot_bgcolor=bg_color, paper_bgcolor=paper_bg,
            font=dict(color=font_color),
            height=260, margin=dict(l=10, r=10, t=10, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.01,
                        font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
            hovermode="x unified",
            xaxis=dict(showgrid=True, gridcolor=grid_color, tickfont=dict(color=font_color)),
            yaxis=dict(showgrid=True, gridcolor=grid_color, tickfont=dict(color=font_color)),
        )
        st.plotly_chart(mini_fig, use_container_width=True)
```

# ══════════════════════════════════════════════════════════════

# TAB 3 – MARKET VIEW

# ══════════════════════════════════════════════════════════════

with tab3:
if not chosen_sym:
st.info(“👆 Select a stock to view the market perspective.”)
else:
with st.spinner(“Loading market data…”):
try:
stock_df, nifty_df, ratings_df = fetch_view_data(chosen_sym)
except Exception as e:
st.error(f”Error: {e}”)
stock_df, nifty_df, ratings_df = pd.DataFrame(), pd.DataFrame(), None

```
    if stock_df.empty or nifty_df.empty:
        st.warning("Could not load market data.")
    else:
        df_merged = pd.merge(
            stock_df[["Date", "Close", "Volume"]],
            nifty_df[["Date", "Close"]],
            on="Date", suffixes=("", "_NIFTY")
        )
        df_merged["Return"]       = df_merged["Close"].pct_change()
        df_merged["NIFTY_Return"] = df_merged["Close_NIFTY"].pct_change()

        # ── Performance Metrics ──
        st.markdown("### 📈 Performance")
        safe = lambda n: (df_merged["Close"].iloc[-1] / df_merged["Close"].iloc[-n] - 1) * 100 if len(df_merged) > n else 0
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("1 Day",   f"{safe(2):+.2f}%")
        p2.metric("5 Days",  f"{safe(6):+.2f}%")
        p3.metric("1 Month", f"{safe(22):+.2f}%")
        p4.metric("YTD",     f"{safe(len(df_merged)):+.2f}%")

        st.markdown("---")

        col_left, col_right = st.columns([3, 2])

        with col_left:
            # ── Analyst Ratings Chart ──
            if ratings_df is not None and not ratings_df.empty:
                st.markdown("### 🧑‍💼 Analyst Recommendations")

                def convert_to_month(period_label):
                    try:
                        offset = int(str(period_label).replace("m", ""))
                        month  = datetime.today() + relativedelta(months=offset)
                        return month.strftime("%b '%y")
                    except:
                        return str(period_label)

                ratings_df["Month"] = ratings_df["period"].apply(convert_to_month)
                ratings_df["Buy"]   = ratings_df["strongBuy"] + ratings_df["buy"]
                ratings_df["Sell"]  = ratings_df["sell"] + ratings_df["strongSell"]
                ratings_df = ratings_df[::-1]

                fig_rat = go.Figure()
                fig_rat.add_trace(go.Bar(x=ratings_df["Month"], y=ratings_df["Buy"],
                                        name="Buy", marker_color="#00d97e"))
                fig_rat.add_trace(go.Bar(x=ratings_df["Month"], y=ratings_df["hold"],
                                        name="Hold", marker_color="#6b7280"))
                fig_rat.add_trace(go.Bar(x=ratings_df["Month"], y=ratings_df["Sell"],
                                        name="Sell", marker_color="#ff4d6d"))
                fig_rat.update_layout(
                    barmode="group",
                    plot_bgcolor=bg_color, paper_bgcolor=paper_bg,
                    font=dict(color=font_color),
                    height=300,
                    margin=dict(l=10, r=10, t=30, b=30),
                    legend=dict(orientation="h", yanchor="bottom", y=1.01,
                                font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
                    xaxis=dict(tickfont=dict(color=font_color), showgrid=False),
                    yaxis=dict(tickfont=dict(color=font_color), showgrid=True,
                               gridcolor=grid_color),
                )
                st.plotly_chart(fig_rat, use_container_width=True)

            # ── Relative Perf vs NIFTY ──
            st.markdown("### 🆚 vs NIFTY 50")
            norm_stock = (df_merged["Close"] / df_merged["Close"].iloc[0]) * 100
            norm_nifty = (df_merged["Close_NIFTY"] / df_merged["Close_NIFTY"].iloc[0]) * 100

            fig_rel = go.Figure()
            fig_rel.add_trace(go.Scatter(
                x=df_merged["Date"], y=norm_stock,
                mode="lines", line=dict(color="#3b82f6", width=2),
                name=chosen_sym
            ))
            fig_rel.add_trace(go.Scatter(
                x=df_merged["Date"], y=norm_nifty,
                mode="lines", line=dict(color="#f59e0b", width=2, dash="dot"),
                name="NIFTY 50"
            ))
            fig_rel.update_layout(
                plot_bgcolor=bg_color, paper_bgcolor=paper_bg,
                font=dict(color=font_color),
                height=250,
                margin=dict(l=10, r=10, t=20, b=30),
                hovermode="x unified",
                yaxis_title="Indexed (base=100)",
                legend=dict(orientation="h", yanchor="bottom", y=1.01,
                            font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(tickfont=dict(color=font_color), showgrid=True, gridcolor=grid_color),
                yaxis=dict(tickfont=dict(color=font_color), showgrid=True, gridcolor=grid_color),
            )
            st.plotly_chart(fig_rel, use_container_width=True)

        with col_right:
            st.markdown("### 🔎 Market Snapshot")

            # Volume
            latest_vol = int(df_merged["Volume"].iloc[-1])
            avg_vol    = int(df_merged["Volume"].tail(21).mean())
            vol_ratio  = latest_vol / avg_vol if avg_vol else 1

            def info_card(label, value, sub=None, color="#60a5fa"):
                st.markdown(
                    f"<div style='background:rgba(30,35,64,0.6);border:1px solid #2e3150;"
                    f"border-radius:10px;padding:12px 16px;margin-bottom:10px;'>"
                    f"<div style='color:#8b93b8;font-size:0.75rem'>{label}</div>"
                    f"<div style='color:{color};font-size:1.2rem;font-weight:700'>{value}</div>"
                    + (f"<div style='color:#6b7280;font-size:0.78rem'>{sub}</div>" if sub else "")
                    + "</div>",
                    unsafe_allow_html=True
                )

            info_card("Today's Volume", f"{latest_vol:,}",
                      f"21-Day Avg: {avg_vol:,} · Ratio: {vol_ratio:.2f}x",
                      color="#00d97e" if vol_ratio > 1.5 else "#60a5fa")

            support_20    = df_merged["Close"].rolling(20).min().iloc[-1]
            resistance_20 = df_merged["Close"].rolling(20).max().iloc[-1]
            info_card("20-Day Support",    f"₹{support_20:.2f}", color="#00d97e")
            info_card("20-Day Resistance", f"₹{resistance_20:.2f}", color="#ff4d6d")

            correlation = df_merged["Return"].corr(df_merged["NIFTY_Return"])
            corr_color  = "#00d97e" if correlation > 0.7 else ("#f59e0b" if correlation > 0.3 else "#ff4d6d")
            corr_label  = "High" if correlation > 0.7 else ("Moderate" if correlation > 0.3 else "Low")
            info_card("NIFTY Correlation (6mo)",
                      f"{correlation:.2f}  ({corr_label})",
                      "Moves with broad market" if correlation > 0.7 else "Independent mover",
                      color=corr_color)

            price_bins   = pd.cut(df_merged["Close"], bins=20)
            most_traded  = price_bins.value_counts().idxmax()
            info_card("Most Traded Range (6mo)", str(most_traded), color="#a78bfa")
```
