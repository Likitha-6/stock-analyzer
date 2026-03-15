import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Index Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 3.5rem !important; padding-bottom: 2rem; overflow: visible; }

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
.ctrl-bar {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 1.2rem 1.6rem;
    margin-bottom: 1.4rem;
}
.stat-card {
    background: #0d1628;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px; padding: 1rem 1.2rem;
    position: relative; overflow: hidden;
    text-align: center;
}
.stat-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #00c882, transparent);
}
.stat-label {
    font-size: 0.68rem !important; letter-spacing: 0.12em;
    text-transform: uppercase; color: #8aaac8; margin-bottom: 0.3rem;
}
.stat-value {
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem !important; font-weight: 700;
    color: #f0f4ff; font-variant-numeric: tabular-nums;
}
.stat-value.up   { color: #00c882; }
.stat-value.down { color: #ff4d6a; }

.insight-card {
    background: #0d1628;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px; padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    display: flex; align-items: flex-start; gap: 0.8rem;
}
.insight-icon { font-size: 1.1rem !important; flex-shrink: 0; margin-top: 0.1rem; }
.insight-text { font-size: 0.78rem !important; color: #c0d4e8; line-height: 1.5; }
.insight-card.green { border-left: 3px solid #00c882; }
.insight-card.yellow { border-left: 3px solid #f5a623; }
.insight-card.red { border-left: 3px solid #ff4d6a; }
.insight-card.blue { border-left: 3px solid #6ec6ff; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">📊 Index Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">// NIFTY 50 · SENSEX · Sector indices · trends · insights</div>', unsafe_allow_html=True)

# ── Index Selector ────────────────────────────────────────────────────────────
index_mapping = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "NIFTY Bank": "^NSEBANK",
    "NIFTY IT": "^CNXIT",
    "NIFTY Pharma": "^CNXPHARMA",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY Auto": "^CNXAUTO",
    "NIFTY Metal": "^CNXMETAL",
}

st.markdown('<div class="section-label">Select Index</div>', unsafe_allow_html=True)
chosen_index_name = st.selectbox("Index", list(index_mapping.keys()), index=0, label_visibility="visible")
chosen_symbol = index_mapping[chosen_index_name]

# ─────────────────────────────────────────────────────────────────────────────
# CANDLESTICK CHART WITH CONTROLS (SAME AS TECHNICAL ANALYSIS)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="ctrl-bar">', unsafe_allow_html=True)
cc1, cc2, cc3 = st.columns([2, 2, 3])

interval_mapping = {"5 min": "5m", "15 min": "15m", "1 hour": "60m", "1 day": "1d"}
label    = cc1.selectbox("Interval", list(interval_mapping.keys()), index=3, label_visibility="visible")
interval = interval_mapping[label]

all_indicators = cc2.multiselect("Indicators", ["SMA", "EMA"], default=["SMA"])

sma_lengths, ema_lengths = [], []
if "SMA" in all_indicators:
    raw = cc3.text_input("SMA periods (e.g. 20,50)", value="20,50", key="sma_input")
    sma_lengths = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
if "EMA" in all_indicators:
    raw = cc3.text_input("EMA periods (e.g. 20,50)", value="20,50", key="ema_input")
    ema_lengths = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]

st.markdown('</div>', unsafe_allow_html=True)

period = "60d" if interval == "1d" else "5d" if interval == "60m" else "2d"

if interval != "1d":
    if "candle_days" not in st.session_state:
        st.session_state.candle_days = 1
    bc1, bc2 = st.columns([1, 1])
    if bc1.button("🔁 Load older candles"):
        st.session_state.candle_days += 1
    if bc2.button("♻️ Reset to 1 day"):
        st.session_state.candle_days = 1
    st.caption("Showing " + str(st.session_state.candle_days) + " day(s) of data")

try:
    df = yf.Ticker(chosen_symbol).history(interval=interval, period=period)
    df = df.reset_index()

    if df.empty:
        st.error("No price data found for this index.")
    else:
        x_col  = "Datetime" if "Datetime" in df.columns else "Date"
        is_intraday = any(k in interval for k in ("m", "h"))
        df["x_label"] = (
            df[x_col].dt.strftime("%d/%m %H:%M") if is_intraday
            else df[x_col].dt.strftime("%d/%m/%y")
        )

        fig = go.Figure()

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df["x_label"],
            open=df["Open"], high=df["High"],
            low=df["Low"],   close=df["Close"],
            increasing_line_color="#00c882",
            decreasing_line_color="#ff4d6a",
            name="Price"
        ))

        # Support / Resistance
        x_col_name = "Datetime" if "Datetime" in df.columns else "Date"
        if interval == "5m":
            sr_df = df[df[x_col_name].dt.date == df[x_col_name].max().date()]
        elif interval == "15m":
            end_d = df[x_col_name].max().date()
            sr_df = df[df[x_col_name].dt.date >= end_d - pd.Timedelta(days=7)]
        else:
            sr_df = df
        support    = sr_df["Low"].min()
        resistance = sr_df["High"].max()

        fig.add_hline(y=support, line_dash="dot", line_width=1.2, line_color="#00c882",
                      annotation=dict(text="Support", font=dict(color="#00c882", size=11), yanchor="bottom"))
        fig.add_hline(y=resistance, line_dash="dot", line_width=1.2, line_color="#ff4d6a",
                      annotation=dict(text="Resistance", font=dict(color="#ff4d6a", size=11), yanchor="top"))

        # SMA overlays
        if sma_lengths:
            for idx_s, sma_len in enumerate(sma_lengths):
                sma_vals = df["Close"].rolling(sma_len).mean()
                colors_sma = ["#f5a623", "#6ec6ff", "#b388ff", "#ff80ab"]
                if sma_vals.notna().sum() > 5:
                    fig.add_trace(go.Scatter(
                        x=df["x_label"], y=sma_vals, mode="lines",
                        line=dict(width=1.5, color=colors_sma[idx_s % len(colors_sma)]),
                        name="SMA " + str(sma_len)
                    ))

        # EMA overlays
        if ema_lengths:
            for idx_e, ema_len in enumerate(ema_lengths):
                ema_vals = df["Close"].ewm(span=ema_len, adjust=False).mean()
                colors_ema = ["#ff80ab", "#80d8ff", "#ccff90", "#ffd180"]
                if ema_vals.notna().sum() > 5:
                    fig.add_trace(go.Scatter(
                        x=df["x_label"], y=ema_vals, mode="lines",
                        line=dict(width=1.5, dash="dash", color=colors_ema[idx_e % len(colors_ema)]),
                        name="EMA " + str(ema_len)
                    ))

        fig.update_layout(
            paper_bgcolor="#080d1a",
            plot_bgcolor="#080d1a",
            font=dict(family="Inter", color="#c0d4e8", size=11),
            xaxis=dict(
                showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                color="#8aaac8", rangeslider_visible=False,
                tickfont=dict(size=10),
            ),
            yaxis=dict(
                showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                color="#8aaac8", side="right",
            ),
            legend=dict(
                bgcolor="rgba(8,13,26,0.8)",
                bordercolor="rgba(255,255,255,0.1)",
                borderwidth=1, font=dict(size=10),
            ),
            margin=dict(l=10, r=60, t=20, b=40),
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

except Exception as e:
    st.error("Error loading chart: " + str(e))

# ─────────────────────────────────────────────────────────────────────────────
# KEY INSIGHTS (SAME AS TECHNICAL ANALYSIS)
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="section-label">📊 Key Insights</div>', unsafe_allow_html=True)

try:
    df_i = yf.Ticker(chosen_symbol).history(period="1y", interval="1d")
    if df_i.empty or len(df_i) < 20:
        st.warning("Not enough historical data for insights.")
    else:
        df_i = df_i.reset_index()
        df_i["SMA_20"]  = df_i["Close"].rolling(20).mean()
        df_i["SMA_50"]  = df_i["Close"].rolling(50).mean()
        df_i["SMA_200"] = df_i["Close"].rolling(200).mean()
        df_i["EMA_20"]  = df_i["Close"].ewm(span=20, adjust=False).mean()
        df_i["EMA_50"]  = df_i["Close"].ewm(span=50, adjust=False).mean()
        
        # RSI
        delta = df_i["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df_i["RSI"] = 100 - (100 / (1 + rs))

        current_price = float(df_i["Close"].iloc[-1])
        latest_sma20  = df_i["SMA_20"].iloc[-1]
        latest_sma50  = df_i["SMA_50"].iloc[-1]
        latest_sma200 = df_i["SMA_200"].iloc[-1]
        latest_ema20  = df_i["EMA_20"].iloc[-1]
        latest_ema50  = df_i["EMA_50"].iloc[-1]
        latest_rsi    = df_i["RSI"].iloc[-1]
        high_52w      = df_i["High"].max()
        low_52w       = df_i["Low"].min()
        high_20d      = df_i["High"].tail(20).max()
        low_20d       = df_i["Low"].tail(20).min()
        vol_pct       = (df_i["Close"].tail(14).std() / current_price) * 100
        
        # Volume metrics
        today_volume = float(df_i["Volume"].iloc[-1])
        avg_volume = float(df_i["Volume"].tail(20).mean())
        volume_ratio = today_volume / avg_volume if avg_volume > 0 else 1
        
        # Recent momentum (5-day change)
        price_5d_ago = float(df_i["Close"].iloc[-5]) if len(df_i) >= 5 else current_price
        momentum_5d = ((current_price - price_5d_ago) / price_5d_ago) * 100
        
        # Price position in 52W range
        price_range_pct = ((current_price - low_52w) / (high_52w - low_52w)) * 100 if high_52w != low_52w else 50

        # Display key stats
        st.markdown('<div class="section-label">// Key Levels</div>', unsafe_allow_html=True)
        kc1, kc2, kc3, kc4, kc5 = st.columns(5)

        def _stat(col, label, value, cls=""):
            col.markdown(
                '<div class="stat-card">'
                '<div class="stat-label">' + label + '</div>'
                '<div class="stat-value ' + cls + '">' + value + '</div>'
                '</div>',
                unsafe_allow_html=True
            )

        _stat(kc1, "Current", f"{current_price:,.0f}")
        _stat(kc2, "SMA 50", f"{latest_sma50:,.0f}" if pd.notna(latest_sma50) else "N/A")
        _stat(kc3, "RSI (14)", f"{latest_rsi:.1f}" if pd.notna(latest_rsi) else "N/A")
        _stat(kc4, "52W High", f"{high_52w:,.0f}")
        _stat(kc5, "52W Low", f"{low_52w:,.0f}")

        # Insight cards
        def _insight(icon, text, kind="blue"):
            st.markdown(
                f'<div class="insight-card {kind}"><div class="insight-icon">{icon}</div><div class="insight-text">{text}</div></div>',
                unsafe_allow_html=True
            )

        # 1. MOVING AVERAGE CROSSOVER STATUS
        st.markdown('<div class="section-label">// Moving Averages</div>', unsafe_allow_html=True)
        
        sma_status = ""
        sma_color = "blue"
        if pd.notna(latest_sma20) and pd.notna(latest_sma50) and pd.notna(latest_sma200):
            if latest_sma20 > latest_sma50 > latest_sma200:
                sma_status = "✅ SMA 20 > 50 > 200 — STRONG BULLISH setup. Uptrend intact."
                sma_color = "green"
            elif latest_sma20 < latest_sma50 < latest_sma200:
                sma_status = "⚠️ SMA 20 < 50 < 200 — STRONG BEARISH setup. Downtrend intact."
                sma_color = "red"
            elif current_price > latest_sma50 > latest_sma200:
                sma_status = "📈 Index > SMA 50 > 200 — Uptrend with good structure."
                sma_color = "green"
            elif current_price < latest_sma50 < latest_sma200:
                sma_status = "📉 Index < SMA 50 < 200 — Downtrend confirmed."
                sma_color = "red"
            elif latest_sma20 > latest_sma50:
                sma_status = "📈 SMA 20 > 50 — Short-term uptrend signal."
                sma_color = "green"
            else:
                sma_status = "📉 SMA 20 < 50 — Short-term downtrend signal."
                sma_color = "red"
        
        if sma_status:
            _insight("⚙️", sma_status, sma_color)

        # 2. EMA 20 vs EMA 50 TREND
        if pd.notna(latest_ema20) and pd.notna(latest_ema50):
            if latest_ema20 > latest_ema50:
                _insight("⚡", f"EMA 20 > EMA 50 — Short-term momentum strengthening.", "green")
            else:
                _insight("⚡", f"EMA 20 < EMA 50 — Short-term momentum weakening.", "red")

        # 3. RSI INSIGHT
        st.markdown('<div class="section-label">// Momentum & Signals</div>', unsafe_allow_html=True)
        if pd.notna(latest_rsi):
            if latest_rsi > 70:
                _insight("⚠️", f"RSI {latest_rsi:.1f} > 70 — OVERBOUGHT. Risk of pullback.", "red")
            elif latest_rsi < 30:
                _insight("✅", f"RSI {latest_rsi:.1f} < 30 — OVERSOLD. Bounce potential.", "green")
            elif latest_rsi > 60:
                _insight("📈", f"RSI {latest_rsi:.1f} (60-70) — Strong momentum, uptrend.", "green")
            elif latest_rsi < 40:
                _insight("📉", f"RSI {latest_rsi:.1f} (30-40) — Weak momentum, downtrend.", "red")
            else:
                _insight("➡️", f"RSI {latest_rsi:.1f} (40-60) — Neutral. No extreme signal.", "blue")

        # 4. VOLUME ANALYSIS
        if volume_ratio > 1.5:
            _insight("📊", f"Volume {volume_ratio:.2f}x average — STRONG conviction. Trend likely continues.", "green")
        elif volume_ratio > 1.2:
            _insight("📊", f"Volume {volume_ratio:.2f}x average — Above average. Trend has strength.", "green")
        elif volume_ratio < 0.7:
            _insight("📊", f"Volume {volume_ratio:.2f}x average — Weak. Move may reverse.", "yellow")
        else:
            _insight("📊", f"Volume {volume_ratio:.2f}x average — Normal. Mixed signals.", "blue")

        # 5. RECENT MOMENTUM (5-day)
        st.markdown('<div class="section-label">// Trend Strength</div>', unsafe_allow_html=True)
        if momentum_5d > 5:
            _insight("🚀", f"Last 5 days: +{momentum_5d:.2f}% — Strong upside momentum.", "green")
        elif momentum_5d > 0:
            _insight("📈", f"Last 5 days: +{momentum_5d:.2f}% — Mild upside momentum.", "green")
        elif momentum_5d < -5:
            _insight("📉", f"Last 5 days: {momentum_5d:.2f}% — Strong downside momentum.", "red")
        else:
            _insight("📉", f"Last 5 days: {momentum_5d:.2f}% — Mild downside momentum.", "red")

        # 6. PRICE POSITION IN 52W RANGE
        if price_range_pct > 80:
            _insight("🔴", f"Index at {price_range_pct:.0f}% of 52W range — Near TOP. Caution on further rallies.", "yellow")
        elif price_range_pct > 60:
            _insight("📈", f"Index at {price_range_pct:.0f}% of 52W range — In upper zone. Strong positioning.", "green")
        elif price_range_pct < 20:
            _insight("🟢", f"Index at {price_range_pct:.0f}% of 52W range — Near BOTTOM. Support zone.", "yellow")
        elif price_range_pct < 40:
            _insight("📉", f"Index at {price_range_pct:.0f}% of 52W range — In lower zone. Caution.", "red")
        else:
            _insight("⚖️", f"Index at {price_range_pct:.0f}% of 52W range — Mid-range. Balanced.", "blue")

        # 7. SUPPORT/RESISTANCE PROXIMITY
        dist_to_support = ((current_price - low_20d) / current_price) * 100
        dist_to_resistance = ((high_20d - current_price) / current_price) * 100
        
        if dist_to_support < 3:
            _insight("🔽", f"Only {dist_to_support:.2f}% above 20-day support at {low_20d:,.0f} — STRONG support zone.", "green")
        elif dist_to_resistance < 3:
            _insight("🔼", f"Only {dist_to_resistance:.2f}% below 20-day resistance at {high_20d:,.0f} — STRONG resistance zone.", "red")

        # 8. BREAKOUT/BREAKDOWN DETECTION
        st.markdown('<div class="section-label">// Breakout Analysis</div>', unsafe_allow_html=True)
        if current_price >= high_20d * 0.98:  # Within 2% of 20-day high
            _insight("🚀", f"Index near 20-day HIGH ({high_20d:,.0f}) — BREAKOUT possible above {high_20d:,.0f}.", "green")
        elif current_price <= low_20d * 1.02:  # Within 2% of 20-day low
            _insight("⬇️", f"Index near 20-day LOW ({low_20d:,.0f}) — BREAKDOWN possible below {low_20d:,.0f}.", "red")

        # 9. CONSOLIDATION DETECTION
        range_20d = high_20d - low_20d
        avg_range = df_i["High"].tail(20).sub(df_i["Low"].tail(20)).mean()
        if range_20d < avg_range * 0.6:
            _insight("🟫", f"20-day range is {(range_20d/avg_range)*100:.0f}% of normal — CONSOLIDATION. Breakout coming.", "blue")

        # 10. RSI DIVERGENCE SIGNAL
        if len(df_i) >= 10:
            recent_rsi = df_i["RSI"].tail(10)
            recent_close = df_i["Close"].tail(10)
            
            if len(recent_rsi) >= 5:
                # Bearish divergence: price higher but RSI lower
                if recent_close.iloc[-1] > recent_close.iloc[-5] and recent_rsi.iloc[-1] < recent_rsi.iloc[-5]:
                    _insight("⚠️", f"BEARISH DIVERGENCE — Index rising but RSI falling. Weakness ahead.", "red")
                # Bullish divergence: price lower but RSI higher
                elif recent_close.iloc[-1] < recent_close.iloc[-5] and recent_rsi.iloc[-1] > recent_rsi.iloc[-5]:
                    _insight("✅", f"BULLISH DIVERGENCE — Index falling but RSI rising. Bounce likely.", "green")

        # 11. VOLATILITY INSIGHT
        st.markdown('<div class="section-label">// Volatility & Risk</div>', unsafe_allow_html=True)
        if vol_pct > 5:
            _insight("🌊", f"High volatility ({vol_pct:.1f}%) — Expect large price swings. Higher risk/reward.", "red")
        elif vol_pct < 2:
            _insight("😴", f"Low volatility ({vol_pct:.1f}%) — Stable. Range-bound. Potential breakout brewing.", "blue")
        else:
            _insight("⚖️", f"Moderate volatility ({vol_pct:.1f}%) — Balanced risk/reward environment.", "green")

        # 12. 200-DAY LONG-TERM TREND
        st.markdown('<div class="section-label">// Long-term Trend</div>', unsafe_allow_html=True)
        if pd.notna(latest_sma200):
            if current_price > latest_sma200:
                pct_above_200 = ((current_price - latest_sma200) / latest_sma200) * 100
                _insight("💪", f"Index {pct_above_200:.2f}% ABOVE 200-day SMA — Long-term UPTREND intact. Strong foundation.", "green")
            else:
                pct_below_200 = ((latest_sma200 - current_price) / latest_sma200) * 100
                _insight("⚠️", f"Index {pct_below_200:.2f}% BELOW 200-day SMA — Long-term DOWNTREND. Caution.", "red")

except Exception as e:
    st.error(f"Error loading insights: {str(e)}")

st.markdown('---')
st.markdown('⚠️ For educational purposes only. Always consult a financial advisor.')
