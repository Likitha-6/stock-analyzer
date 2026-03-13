import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(
    page_title="Technical Analysis",
    page_icon="📈",
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

div[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem !important; font-weight: 600;
    letter-spacing: 0.04em;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">📈 Technical Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">// Candlestick chart · indicators · insights · price targets & risk management</div>', unsafe_allow_html=True)

# ── Search ────────────────────────────────────────────────────────────────────
chosen_sym = None

try:
    import csv
    stocks = []
    with open('nse_stocks_.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Symbol'):
                stocks.append(row['Symbol'])
    stocks = sorted(list(set([s for s in stocks if s])))
except:
    stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'LT', 'MARUTI', 'AXISBANK', 'NTPC']

query = st.text_input(
    "search",
    placeholder="🔍  Search by symbol or company name...",
    label_visibility="collapsed",
).strip()

if query:
    filtered_stocks = [s for s in stocks if query.upper() in s]
    if filtered_stocks:
        chosen_sym = st.selectbox('Select:', filtered_stocks, label_visibility='collapsed')
    else:
        st.error(f'No stocks found matching "{query}"')
        st.stop()
else:
    st.info('👆 Search for a stock symbol above')
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  Chart", "🔍  Insights", "🌐  Market View"])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — CHART
# ═══════════════════════════════════════════════════════════════════
with tab1:
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
        df = yf.Ticker(chosen_sym + ".NS").history(interval=interval, period=period)
        df = df.reset_index()

        if df.empty:
            st.error("No price data found for this stock.")
        else:
            st.session_state.df_stock = df
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

# ═══════════════════════════════════════════════════════════════════
# PRICE TARGETS & RISK MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

st.markdown('<div class="section-label">📈 Price Targets & Risk Management</div>', unsafe_allow_html=True)

try:
    # Get 1 day data for ATR calculation
    df_atr = yf.Ticker(chosen_sym + ".NS").history(period='1y', interval='1d')
    
    if not df_atr.empty:
        current_price = float(df_atr['Close'].iloc[-1])
        
        # Calculate ATR
        tr1 = df_atr['High'] - df_atr['Low']
        tr2 = abs(df_atr['High'] - df_atr['Close'].shift())
        tr3 = abs(df_atr['Low'] - df_atr['Close'].shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean().iloc[-1]
        
        if pd.isna(atr):
            atr = (df_atr['High'] - df_atr['Low']).iloc[-20:].mean()
        
        # Calculate targets
        stop_loss = current_price - atr
        target_1 = current_price + atr
        target_2 = current_price + (2 * atr)
        target_3 = current_price + (3 * atr)
        
        # Risk-Reward Ratios
        risk = current_price - stop_loss
        rr_1 = (target_1 - current_price) / risk if risk > 0 else 0
        rr_2 = (target_2 - current_price) / risk if risk > 0 else 0
        rr_3 = (target_3 - current_price) / risk if risk > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid #ff4d6a;border-radius:12px;padding:1.2rem;text-align:center;"><div style="font-size:0.7rem;color:#8aaac8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Stop Loss</div><div style="font-size:1.2rem;font-weight:700;color:#ff4d6a;">₹{stop_loss:,.2f}</div><div style="font-size:0.75rem;color:#ff4d6a;margin-top:0.3rem;">Risk: ₹{risk:,.2f}</div></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid #ffa500;border-radius:12px;padding:1.2rem;text-align:center;"><div style="font-size:0.7rem;color:#8aaac8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Target 1</div><div style="font-size:1.2rem;font-weight:700;color:#ffa500;">₹{target_1:,.2f}</div><div style="font-size:0.75rem;color:#ffa500;margin-top:0.3rem;">R:R {rr_1:.2f}:1</div></div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid #00c882;border-radius:12px;padding:1.2rem;text-align:center;"><div style="font-size:0.7rem;color:#8aaac8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Target 2</div><div style="font-size:1.2rem;font-weight:700;color:#00c882;">₹{target_2:,.2f}</div><div style="font-size:0.75rem;color:#00c882;margin-top:0.3rem;">R:R {rr_2:.2f}:1</div></div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid #00c882;border-radius:12px;padding:1.2rem;text-align:center;"><div style="font-size:0.7rem;color:#8aaac8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Target 3</div><div style="font-size:1.2rem;font-weight:700;color:#00c882;">₹{target_3:,.2f}</div><div style="font-size:0.75rem;color:#00c882;margin-top:0.3rem;">R:R {rr_3:.2f}:1</div></div>', unsafe_allow_html=True)
        
        # Explanation
        st.markdown(f'''
        **📊 How to Use These Targets:**
        
        - **Stop Loss (₹{stop_loss:,.2f}):** Place your stop-loss here to limit losses. Risk per trade: ₹{risk:,.2f}
        - **Target 1 (₹{target_1:,.2f}):** Conservative target with 1:1 risk-reward ratio
        - **Target 2 (₹{target_2:,.2f}):** Moderate target with 2:1 risk-reward ratio (better reward)
        - **Target 3 (₹{target_3:,.2f}):** Aggressive target with 3:1 risk-reward ratio (best case)
        
        **💡 Trading Strategy:**
        - Buy at: ₹{current_price:,.2f} (Current Price)
        - Risk: ₹{risk:,.2f} per share
        - Exit partial position at Target 1, 2, and 3
        - Recommended: Use a 1:2 or 1:3 Risk-Reward ratio
        - ATR Value (Volatility): ₹{atr:,.2f}
        ''', unsafe_allow_html=True)

except Exception as e:
    st.warning(f'Price target calculation error: {str(e)}')

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — INSIGHTS
# ═══════════════════════════════════════════════════════════════════
with tab2:
    try:
        df_i = yf.Ticker(chosen_sym + ".NS").history(period="1y", interval="1d")
        if df_i.empty or len(df_i) < 20:
            st.warning("Not enough historical data to compute insights.")
        else:
            df_i = df_i.reset_index()
            df_i["SMA_50"]  = df_i["Close"].rolling(50).mean()
            df_i["SMA_200"] = df_i["Close"].rolling(200).mean()
            df_i["EMA_20"]  = df_i["Close"].ewm(span=20, adjust=False).mean()
            
            # RSI
            delta = df_i["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df_i["RSI"] = 100 - (100 / (1 + rs))

            latest_price  = df_i["Close"].iloc[-1]
            latest_sma50  = df_i["SMA_50"].iloc[-1]
            latest_sma200 = df_i["SMA_200"].iloc[-1]
            latest_ema20  = df_i["EMA_20"].iloc[-1]
            latest_rsi    = df_i["RSI"].iloc[-1]
            high_52w      = df_i["High"].max()
            low_52w       = df_i["Low"].min()

            # ── Stat cards row ────────────────────────────────────────────
            st.markdown('<div class="section-label">// key levels</div>', unsafe_allow_html=True)
            kc1, kc2, kc3, kc4, kc5 = st.columns(5)

            def _stat(col, label, value, cls=""):
                col.markdown(
                    '<div class="stat-card">'
                    '<div class="stat-label">' + label + '</div>'
                    '<div class="stat-value ' + cls + '">' + value + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

            _stat(kc1, "Current Price", "Rs." + str(round(latest_price, 2)))
            _stat(kc2, "50-Day SMA",  "Rs." + str(round(latest_sma50,  2)) if pd.notna(latest_sma50)  else "N/A")
            _stat(kc3, "200-Day SMA", "Rs." + str(round(latest_sma200, 2)) if pd.notna(latest_sma200) else "N/A")
            _stat(kc4, "52-Week High", "Rs." + str(round(high_52w, 2)))
            _stat(kc5, "52-Week Low",  "Rs." + str(round(low_52w,  2)))

            # RSI gauge
            st.markdown('<div class="section-label">// RSI · momentum · signals</div>', unsafe_allow_html=True)
            rsi_col, sig_col = st.columns([1, 2])

            rsi_cls = "down" if latest_rsi > 70 else "up" if latest_rsi < 30 else ""
            rsi_col.markdown(
                '<div class="stat-card" style="margin-bottom:0;">'
                '<div class="stat-label">RSI (14)</div>'
                '<div class="stat-value ' + rsi_cls + '" style="font-size:2.0rem !important;">' + str(round(latest_rsi, 1)) + '</div>'
                '<div style="font-size:0.68rem !important;color:#8aaac8;margin-top:0.3rem;">'
                + ("Overbought" if latest_rsi > 70 else "Oversold" if latest_rsi < 30 else "Neutral zone") +
                '</div></div>',
                unsafe_allow_html=True
            )

            # Insight cards
            def _insight(col, icon, text, kind="blue"):
                col.markdown(
                    '<div class="insight-card ' + kind + '">'
                    '<div class="insight-icon">' + icon + '</div>'
                    '<div class="insight-text">' + text + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

            with sig_col:
                if len(df_i) >= 5 and df_i["EMA_20"].iloc[-1] > df_i["EMA_20"].iloc[-5]:
                    _insight(sig_col, "📈", "20-day EMA sloping up — short-term trend is strengthening.", "green")
                else:
                    _insight(sig_col, "📉", "20-day EMA sloping down — short-term trend may be weakening.", "yellow")

                if latest_rsi > 70:
                    _insight(sig_col, "⚠️", "RSI above 70 — stock is overbought. Momentum may slow with a possible short-term dip.", "red")
                elif latest_rsi < 30:
                    _insight(sig_col, "✅", "RSI below 30 — stock is oversold. Selling may be exhausted, potential rebound could follow.", "green")
                else:
                    _insight(sig_col, "➡️", "RSI in neutral zone (" + str(round(latest_rsi, 1)) + ") — no strong momentum signal.", "blue")

                if abs(latest_price - high_52w) < 0.03 * high_52w:
                    _insight(sig_col, "🚀", "Price is near its 52-week high — watch for resistance.", "yellow")
                elif abs(latest_price - low_52w) < 0.03 * low_52w:
                    _insight(sig_col, "🔻", "Price is near its 52-week low — potential support zone.", "yellow")

            if len(df_i["Close"]) >= 14:
                vol_pct = (df_i["Close"].tail(14).std() / latest_price) * 100
                if vol_pct > 5:
                    _insight(st, "🌊", "High volatility (" + str(round(vol_pct, 1)) + "%) — expect larger price swings.", "red")
                elif vol_pct < 2:
                    _insight(st, "😴", "Low volatility (" + str(round(vol_pct, 1)) + "%) — stable, range-bound price action.", "blue")
                else:
                    _insight(st, "⚖️", "Moderate volatility (" + str(round(vol_pct, 1)) + "%) — balanced risk/reward.", "green")

    except Exception as e:
        st.error("Error loading insights: " + str(e))

# ═══════════════════════════════════════════════════════════════════
# TAB 3 — MARKET VIEW
# ═══════════════════════════════════════════════════════════════════
with tab3:
    try:
        stock_df = yf.Ticker(chosen_sym + ".NS").history(period="6mo", interval="1d")
        nifty_df = yf.Ticker("^NSEI").history(period="6mo", interval="1d")

        if stock_df.empty or nifty_df.empty:
            st.warning("Could not load data for market view.")
        else:
            stock_df = stock_df.reset_index()
            nifty_df = nifty_df.reset_index()
            df_m = pd.merge(
                stock_df[["Date", "Close", "Volume"]],
                nifty_df[["Date", "Close"]],
                on="Date", suffixes=("", "_NIFTY")
            )
            df_m["Return"]       = df_m["Close"].pct_change()
            df_m["NIFTY_Return"] = df_m["Close_NIFTY"].pct_change()

            st.markdown('<div class="section-label">// price performance</div>', unsafe_allow_html=True)

            def _chg(n):
                try:
                    v = (df_m["Close"].iloc[-1] / df_m["Close"].iloc[-n] - 1) * 100
                    return round(v, 2)
                except Exception:
                    return None

            changes = [("1 Day", _chg(2)), ("5 Days", _chg(6)),
                       ("1 Month", _chg(22)), ("6 Months", _chg(len(df_m)))]

            perf_cols = st.columns(4)
            for pcol, (label, val) in zip(perf_cols, changes):
                if val is not None:
                    cls = "up" if val >= 0 else "down"
                    arrow = "▲" if val >= 0 else "▼"
                    pcol.markdown(
                        '<div class="stat-card">'
                        '<div class="stat-label">' + label + '</div>'
                        '<div class="stat-value ' + cls + '">' + arrow + " " + str(abs(val)) + '%</div>'
                        '</div>',
                        unsafe_allow_html=True
                    )

            st.markdown('<div class="section-label">// volume</div>', unsafe_allow_html=True)
            vc1, vc2, vc3 = st.columns(3)
            latest_vol = int(df_m["Volume"].iloc[-1])
            avg_vol    = int(df_m["Volume"].tail(21).mean())
            vol_ratio  = latest_vol / avg_vol if avg_vol > 0 else 1
            vol_cls    = "up" if vol_ratio >= 1.2 else "down" if vol_ratio < 0.8 else ""

            vc1.markdown('<div class="stat-card"><div class="stat-label">Today Volume</div><div class="stat-value">' + f"{latest_vol:,}" + '</div></div>', unsafe_allow_html=True)
            vc2.markdown('<div class="stat-card"><div class="stat-label">21-Day Avg</div><div class="stat-value">' + f"{avg_vol:,}" + '</div></div>', unsafe_allow_html=True)
            vc3.markdown('<div class="stat-card"><div class="stat-label">Vol Ratio</div><div class="stat-value ' + vol_cls + '">' + str(round(vol_ratio, 2)) + 'x</div></div>', unsafe_allow_html=True)

            st.markdown('<div class="section-label">// support · resistance · correlation</div>', unsafe_allow_html=True)
            src1, src2, src3 = st.columns(3)
            support    = round(df_m["Close"].rolling(20).min().iloc[-1], 2)
            resistance = round(df_m["Close"].rolling(20).max().iloc[-1], 2)
            corr       = round(df_m["Return"].corr(df_m["NIFTY_Return"]), 2)
            corr_cls   = "up" if corr > 0.7 else "down" if corr < 0.3 else ""

            src1.markdown('<div class="stat-card"><div class="stat-label">Support (20d)</div><div class="stat-value">Rs.' + str(support) + '</div></div>', unsafe_allow_html=True)
            src2.markdown('<div class="stat-card"><div class="stat-label">Resistance (20d)</div><div class="stat-value">Rs.' + str(resistance) + '</div></div>', unsafe_allow_html=True)
            src3.markdown('<div class="stat-card"><div class="stat-label">NIFTY Correlation</div><div class="stat-value ' + corr_cls + '">' + str(corr) + '</div></div>', unsafe_allow_html=True)

            if corr > 0.7:
                st.markdown('<div class="insight-card green"><div class="insight-icon">✅</div><div class="insight-text">Highly correlated with the broader market (NIFTY 50). Moves largely with the index.</div></div>', unsafe_allow_html=True)
            elif corr < 0.3:
                st.markdown('<div class="insight-card yellow"><div class="insight-icon">⚠️</div><div class="insight-text">Moves largely independently of the NIFTY index — stock-specific factors dominate.</div></div>', unsafe_allow_html=True)

            price_bins  = pd.cut(df_m["Close"], bins=20)
            most_traded = price_bins.value_counts().idxmax()
            st.markdown(
                '<div class="insight-card blue"><div class="insight-icon">📊</div>'
                '<div class="insight-text">Most traded price range (last 6 months): <strong>Rs.' + str(round(most_traded.left, 2)) + ' – Rs.' + str(round(most_traded.right, 2)) + '</strong></div></div>',
                unsafe_allow_html=True
            )

    except Exception as e:
        st.error("Error loading market view: " + str(e))

st.markdown('---')
st.markdown('⚠️ For educational purposes only. Always consult a financial advisor.')
