import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from common.data import load_name_lookup
from indicators import apply_ema
from indicators import detect_cross_signals, compute_rsi, detect_crossovers
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title=“Technical Analysis”, layout=“wide”, page_icon=“📈”)

st.markdown(”””<style>.block-container{padding-top:1rem}.stAlert{border-radius:8px}[data-testid=‘metric-container’]{background:#1c1f2e;border:1px solid #2e3150;border-radius:10px;padding:12px 16px}[data-testid=‘metric-container’] label{font-size:.75rem;color:#8b93b8}[data-testid=‘metric-container’] [data-testid=‘stMetricValue’]{font-size:1.25rem;font-weight:700;color:#e2e8f0}button[data-baseweb=‘tab’]{font-size:.9rem;font-weight:600}</style>”””, unsafe_allow_html=True)

@st.cache_data(ttl=300, show_spinner=False)
def fetch_ohlcv(symbol, interval, period):
df = yf.Ticker(symbol + “.NS”).history(interval=interval, period=period)
return df.reset_index() if not df.empty else pd.DataFrame()

@st.cache_data(ttl=600, show_spinner=False)
def fetch_insights_data(symbol):
df = yf.Ticker(symbol + “.NS”).history(interval=“1d”, period=“12mo”)
return df.reset_index() if not df.empty else pd.DataFrame()

@st.cache_data(ttl=600, show_spinner=False)
def fetch_view_data(symbol):
stock_df = yf.Ticker(symbol + “.NS”).history(period=“6mo”, interval=“1d”).reset_index()
nifty_df = yf.Ticker(”^NSEI”).history(period=“6mo”, interval=“1d”).reset_index()
ratings_df = yf.Ticker(symbol + “.NS”).recommendations
return stock_df, nifty_df, ratings_df

col_title, col_theme = st.columns([5, 1])
with col_title:
st.markdown(”## 📈 Indian Stock – Technical Analysis”)
with col_theme:
dark_mode = st.toggle(“🌙 Dark”, value=True)

bg_color = “#0E1117” if dark_mode else “#FFFFFF”
paper_bg = “#161b2e” if dark_mode else “#f8f9fa”
font_color = “#e2e8f0” if dark_mode else “#1a1a2e”
grid_color = “#1e2340” if dark_mode else “#e9ecef”
increasing_color = “#00d97e” if dark_mode else “#00B26F”
decreasing_color = “#ff4d6d” if dark_mode else “#FF3C38”

name_df = load_name_lookup()
symbol2name = dict(zip(name_df[“Symbol”], name_df[“Company Name”]))

st.markdown(”—”)
search_query = st.text_input(“🔍 Search by Symbol or Company Name”, placeholder=“e.g. RELIANCE or Infosys”).strip().lower()
chosen_sym = None

if search_query:
mask = name_df[“Symbol”].str.lower().str.contains(search_query) | name_df[“Company Name”].str.lower().str.contains(search_query)
matches = name_df[mask]
if matches.empty:
st.warning(“No matching stock found.”)
else:
options = (matches[“Symbol”] + “ – “ + matches[“Company Name”]).tolist()
selected = st.selectbox(“Select Stock”, options, label_visibility=“collapsed”)
chosen_sym = selected.split(” – “)[0]
company = symbol2name.get(chosen_sym, “”)
badge_html = “<span style='background:#1e3a5f;color:#60a5fa;padding:4px 12px;border-radius:20px;font-weight:600;font-size:0.85rem;'>📌 “ + chosen_sym + “ \u00b7 “ + company + “</span>”
st.markdown(badge_html, unsafe_allow_html=True)

st.markdown(”—”)
tab1, tab2, tab3 = st.tabs([“📊 Chart”, “💡 Insights”, “🌐 Market View”])

# ═══════════════════════════════════════

# TAB 1 – CHART

# ═══════════════════════════════════════

with tab1:
ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 3])
with ctrl1:
interval_mapping = {“5 min”: “5m”, “15 min”: “15m”, “1 Hour”: “60m”, “1 Day”: “1d”}
label = st.selectbox(“⏱ Interval”, list(interval_mapping.keys()), index=3)
interval = interval_mapping[label]
with ctrl2:
period_options = {
“5 min”: {“1 Day”: “1d”, “2 Days”: “2d”, “5 Days”: “5d”},
“15 min”: {“2 Days”: “2d”, “5 Days”: “5d”, “10 Days”: “10d”},
“1 Hour”: {“5 Days”: “5d”, “1 Month”: “1mo”, “3 Months”: “3mo”},
“1 Day”: {“1 Month”: “1mo”, “3 Months”: “3mo”, “6 Months”: “6mo”, “1 Year”: “1y”},
}
period_opts = period_options[label]
period_label = st.selectbox(“📅 Period”, list(period_opts.keys()))
period = period_opts[period_label]
with ctrl3:
ema_options = st.multiselect(“📐 Overlays”, [“EMA 9”, “EMA 20”, “EMA 50”, “EMA 200”, “Support/Resistance”], default=[“EMA 20”, “Support/Resistance”])

```
show_rsi = st.checkbox("Show RSI subplot", value=True)
show_volume = st.checkbox("Show Volume subplot", value=True)

if chosen_sym:
    with st.spinner("Loading chart..."):
        df = fetch_ohlcv(chosen_sym, interval, period)

    if df.empty:
        st.error("No data found for this symbol / interval.")
    else:
        x_col = "Datetime" if "Datetime" in df.columns else "Date"
        is_intraday = any(k in interval for k in ("m", "h"))
        df["x_label"] = df[x_col].dt.strftime("%d/%m %H:%M" if is_intraday else "%d %b '%y")

        ema_map = {"EMA 9": 9, "EMA 20": 20, "EMA 50": 50, "EMA 200": 200}
        ema_lengths = [ema_map[e] for e in ema_options if e in ema_map]
        if ema_lengths:
            df = apply_ema(df, ema_lengths)

        show_sr = "Support/Resistance" in ema_options
        if show_sr:
            if interval == "5m":
                sr_df = df[df[x_col].dt.date == df[x_col].max().date()]
            elif interval == "15m":
                sr_df = df[df[x_col].dt.date >= (df[x_col].max().date() - pd.Timedelta(days=7))]
            else:
                sr_df = df
            support = sr_df["Low"].min()
            resistance = sr_df["High"].max()

        n_rows = 1 + int(show_volume) + int(show_rsi)
        row_heights = [0.6] + ([0.2] if show_volume else []) + ([0.2] if show_rsi else [])
        sp_titles = [chosen_sym + ".NS \u2013 " + label + " (" + period_label + ")"] + (["Volume"] if show_volume else []) + (["RSI (14)"] if show_rsi else [])

        fig = make_subplots(rows=n_rows, cols=1, shared_xaxes=True, row_heights=row_heights, vertical_spacing=0.03, subplot_titles=sp_titles)

        fig.add_trace(go.Candlestick(x=df["x_label"], open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"], increasing_line_color=increasing_color, decreasing_line_color=decreasing_color, increasing_fillcolor=increasing_color, decreasing_fillcolor=decreasing_color, name="Price", showlegend=False), row=1, col=1)

        if show_sr:
            fig.add_hline(y=support, line_dash="dot", line_width=1.2, line_color="#2ecc71", annotation=dict(text="  S " + str(round(support, 1)), font=dict(color="#2ecc71", size=10)), row=1, col=1)
            fig.add_hline(y=resistance, line_dash="dot", line_width=1.2, line_color="#e74c3c", annotation=dict(text="  R " + str(round(resistance, 1)), font=dict(color="#e74c3c", size=10), yanchor="bottom"), row=1, col=1)

        ema_colors = {9: "#f59e0b", 20: "#3b82f6", 50: "#a78bfa", 200: "#f43f5e"}
        for ema_len in ema_lengths:
            col_name = "EMA_" + str(ema_len)
            if col_name in df.columns:
                fig.add_trace(go.Scatter(x=df["x_label"], y=df[col_name], mode="lines", line=dict(width=1.5, color=ema_colors.get(ema_len, "#ffffff")), name="EMA " + str(ema_len), opacity=0.85), row=1, col=1)

        if "EMA_20" in df.columns and "EMA_50" in df.columns:
            signals = detect_crossovers(df, short_col="EMA_20", long_col="EMA_50")
            if signals["buy"]:
                fig.add_trace(go.Scatter(x=[df["x_label"].iloc[i] for i in signals["buy"]], y=[df["Close"].iloc[i] for i in signals["buy"]], mode="markers", marker=dict(color="#00d97e", size=11, symbol="triangle-up", line=dict(color="white", width=1)), name="Buy Signal"), row=1, col=1)
            if signals["sell"]:
                fig.add_trace(go.Scatter(x=[df["x_label"].iloc[i] for i in signals["sell"]], y=[df["Close"].iloc[i] for i in signals["sell"]], mode="markers", marker=dict(color="#ff4d6d", size=11, symbol="triangle-down", line=dict(color="white", width=1)), name="Sell Signal"), row=1, col=1)

        vol_row = 2 if show_volume else None
        if show_volume:
            fig.add_trace(go.Bar(x=df["x_label"], y=df["Volume"], marker_color=[increasing_color if c >= o else decreasing_color for c, o in zip(df["Close"], df["Open"])], name="Volume", opacity=0.7, showlegend=False), row=vol_row, col=1)

        rsi_row = (2 if not show_volume else 3) if show_rsi else None
        if show_rsi:
            fig.add_trace(go.Scatter(x=df["x_label"], y=compute_rsi(df), mode="lines", line=dict(color="#a78bfa", width=1.5), name="RSI", showlegend=False), row=rsi_row, col=1)
            fig.add_hline(y=70, line_dash="dot", line_width=1, line_color="#555577", row=rsi_row, col=1)
            fig.add_hline(y=30, line_dash="dot", line_width=1, line_color="#555577", row=rsi_row, col=1)

        N = max(1, len(df) // 12)
        tickvals = df["x_label"].iloc[::N].tolist()
        ax = dict(showgrid=True, gridcolor=grid_color, gridwidth=0.5, zeroline=False, tickfont=dict(color=font_color, size=10), linecolor=grid_color)
        fig.update_layout(plot_bgcolor=bg_color, paper_bgcolor=paper_bg, font=dict(color=font_color, family="Inter, sans-serif"), legend=dict(font=dict(color=font_color, size=11), bgcolor="rgba(0,0,0,0.3)", bordercolor=grid_color, borderwidth=1, orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0), xaxis_rangeslider_visible=False, dragmode="pan", hovermode="x unified", height=500 + 150 * int(show_volume) + 150 * int(show_rsi), margin=dict(l=10, r=60, t=60, b=30))
        for i in range(1, n_rows + 1):
            fig.update_xaxes(**ax, type="category", tickangle=-40, tickmode="array", tickvals=tickvals, ticktext=tickvals, row=i, col=1)
            fig.update_yaxes(**ax, row=i, col=1)

        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True, "modeBarButtonsToRemove": ["zoom2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d"], "displaylogo": False})

        latest = df["Close"].iloc[-1]
        prev = df["Close"].iloc[-2] if len(df) > 1 else latest
        chg = latest - prev
        chg_pct = (chg / prev) * 100
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Last Price", "\u20b9{:,.2f}".format(latest), "{:+.2f} ({:+.2f}%)".format(chg, chg_pct))
        m2.metric("Period High", "\u20b9{:,.2f}".format(df["High"].max()))
        m3.metric("Period Low", "\u20b9{:,.2f}".format(df["Low"].min()))
        m4.metric("Candles", "{:,}".format(len(df)))
        m5.metric("Avg Volume", "{:,}".format(int(df["Volume"].mean())))
else:
    st.info("👆 Search and select a stock above to load the chart.")
```

# ═══════════════════════════════════════

# TAB 2 – INSIGHTS

# ═══════════════════════════════════════

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
        df_ins["SMA_50"] = df_ins["Close"].rolling(50).mean()
        df_ins["SMA_200"] = df_ins["Close"].rolling(200).mean()
        df_ins["EMA_20"] = df_ins["Close"].ewm(span=20, adjust=False).mean()
        df_ins["RSI"] = compute_rsi(df_ins)

        high_52w = df_ins["High"].max()
        low_52w = df_ins["Low"].min()
        latest_price = df_ins["Close"].iloc[-1]
        latest_sma50 = df_ins["SMA_50"].iloc[-1]
        latest_sma200 = df_ins["SMA_200"].iloc[-1]
        latest_rsi = df_ins["RSI"].iloc[-1]

        st.markdown("### 📌 Key Levels")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Current Price", "\u20b9{:,.2f}".format(latest_price))
        m2.metric("SMA 50", "\u20b9{:,.2f}".format(latest_sma50) if pd.notna(latest_sma50) else "N/A")
        m3.metric("SMA 200", "\u20b9{:,.2f}".format(latest_sma200) if pd.notna(latest_sma200) else "N/A")
        m4.metric("52W High", "\u20b9{:,.2f}".format(high_52w))
        m5.metric("52W Low", "\u20b9{:,.2f}".format(low_52w))
        st.markdown("---")

        col_rsi, col_sig = st.columns([1, 2])

        with col_rsi:
            st.markdown("### 📊 RSI (14-day)")
            rsi_clr = "#ff4d6d" if latest_rsi > 70 else ("#00d97e" if latest_rsi < 30 else "#a78bfa")
            gauge = go.Figure(go.Indicator(mode="gauge+number", value=latest_rsi, number={"font": {"color": rsi_clr, "size": 32}}, gauge={"axis": {"range": [0, 100], "tickcolor": font_color, "tickfont": {"color": font_color}}, "bar": {"color": rsi_clr}, "steps": [{"range": [0, 30], "color": "rgba(0,217,126,0.15)"}, {"range": [30, 70], "color": "rgba(167,139,250,0.1)"}, {"range": [70, 100], "color": "rgba(255,77,109,0.15)"}], "threshold": {"line": {"color": "white", "width": 2}, "thickness": 0.75, "value": latest_rsi}, "bgcolor": bg_color, "bordercolor": grid_color}))
            gauge.update_layout(paper_bgcolor=paper_bg, font=dict(color=font_color), height=220, margin=dict(l=20, r=20, t=30, b=10))
            st.plotly_chart(gauge, use_container_width=True)
            if latest_rsi > 70:
                st.warning("⚠️ Overbought — momentum may slow.")
            elif latest_rsi < 30:
                st.success("✅ Oversold — potential rebound ahead.")
            else:
                st.info("🔵 RSI neutral — no extreme signal.")

        with col_sig:
            st.markdown("### 🧠 Signal Checklist")

            def signal_card(icon, lbl, msg, kind):
                colors = {"good": "#00d97e", "bad": "#ff4d6d", "info": "#60a5fa", "neutral": "#8b93b8"}
                bgs = {"good": "rgba(0,217,126,0.1)", "bad": "rgba(255,77,109,0.1)", "info": "rgba(96,165,250,0.1)", "neutral": "rgba(139,147,184,0.1)"}
                html = "<div style='background:" + bgs[kind] + ";border-left:3px solid " + colors[kind] + ";border-radius:6px;padding:8px 12px;margin-bottom:8px;'><b style='color:" + colors[kind] + "'>" + icon + " " + lbl + "</b> \u2014 <span style='color:#c0c8e8'>" + msg + "</span></div>"
                st.markdown(html, unsafe_allow_html=True)

            if df_ins["EMA_20"].iloc[-1] > df_ins["EMA_20"].iloc[-5]:
                signal_card("📈", "EMA 20 Slope", "Trending up \u2014 short-term bullish", "good")
            else:
                signal_card("📉", "EMA 20 Slope", "Trending down \u2014 short-term weak", "bad")

            if pd.notna(latest_sma50):
                if latest_price > latest_sma50:
                    signal_card("✅", "Price vs SMA 50", "\u20b9{:.0f} above \u20b9{:.0f}".format(latest_price, latest_sma50), "good")
                else:
                    signal_card("❌", "Price vs SMA 50", "\u20b9{:.0f} below \u20b9{:.0f}".format(latest_price, latest_sma50), "bad")

            cross = detect_cross_signals(df_ins)
            if cross:
                ck = "good" if any(x in cross for x in ["Golden", "Bullish"]) else "bad"
                signal_card("🔁", "SMA Cross", cross.replace("\u2705","").replace("\u274c","").strip(), ck)

            if abs(latest_price - high_52w) < 0.03 * high_52w:
                signal_card("🚀", "52W High", "Near 52-week high \u2014 watch for resistance", "info")
            elif abs(latest_price - low_52w) < 0.03 * low_52w:
                signal_card("🔻", "52W Low", "Near 52-week low \u2014 potential support", "neutral")

            vol_pct = (df_ins["Close"].tail(14).std() / latest_price) * 100
            if vol_pct > 5:
                signal_card("⚡", "Volatility", "{:.1f}% \u2014 high, expect wide swings".format(vol_pct), "bad")
            elif vol_pct < 2:
                signal_card("😴", "Volatility", "{:.1f}% \u2014 low, stable price action".format(vol_pct), "neutral")
            else:
                signal_card("⚖️", "Volatility", "{:.1f}% \u2014 moderate, balanced risk".format(vol_pct), "good")

        st.markdown("---")
        st.markdown("### 📉 Price History (12 months)")
        mf = go.Figure()
        mf.add_trace(go.Scatter(x=df_ins["Date"], y=df_ins["Close"], mode="lines", fill="tozeroy", line=dict(color="#3b82f6", width=2), fillcolor="rgba(59,130,246,0.08)", name="Close"))
        if pd.notna(latest_sma50):
            mf.add_trace(go.Scatter(x=df_ins["Date"], y=df_ins["SMA_50"], mode="lines", line=dict(color="#f59e0b", width=1.2, dash="dot"), name="SMA 50"))
        if pd.notna(latest_sma200):
            mf.add_trace(go.Scatter(x=df_ins["Date"], y=df_ins["SMA_200"], mode="lines", line=dict(color="#f43f5e", width=1.2, dash="dot"), name="SMA 200"))
        mf.update_layout(plot_bgcolor=bg_color, paper_bgcolor=paper_bg, font=dict(color=font_color), height=260, margin=dict(l=10, r=10, t=10, b=30), hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.01, font=dict(size=11), bgcolor="rgba(0,0,0,0)"), xaxis=dict(showgrid=True, gridcolor=grid_color, tickfont=dict(color=font_color)), yaxis=dict(showgrid=True, gridcolor=grid_color, tickfont=dict(color=font_color)))
        st.plotly_chart(mf, use_container_width=True)
```

# ═══════════════════════════════════════

# TAB 3 – MARKET VIEW

# ═══════════════════════════════════════

with tab3:
if not chosen_sym:
st.info(“👆 Select a stock to view the market perspective.”)
else:
with st.spinner(“Loading market data…”):
try:
stock_df, nifty_df, ratings_df = fetch_view_data(chosen_sym)
except Exception as ex:
st.error(“Error: “ + str(ex))
stock_df = pd.DataFrame()
nifty_df = pd.DataFrame()
ratings_df = None

```
    if stock_df.empty or nifty_df.empty:
        st.warning("Could not load market data.")
    else:
        df_m = pd.merge(stock_df[["Date", "Close", "Volume"]], nifty_df[["Date", "Close"]], on="Date", suffixes=("", "_NIFTY"))
        df_m["Return"] = df_m["Close"].pct_change()
        df_m["NIFTY_Return"] = df_m["Close_NIFTY"].pct_change()

        st.markdown("### 📈 Performance")

        def safe_ret(n):
            return (df_m["Close"].iloc[-1] / df_m["Close"].iloc[-n] - 1) * 100 if len(df_m) > n else 0.0

        p1, p2, p3, p4 = st.columns(4)
        p1.metric("1 Day", "{:+.2f}%".format(safe_ret(2)))
        p2.metric("5 Days", "{:+.2f}%".format(safe_ret(6)))
        p3.metric("1 Month", "{:+.2f}%".format(safe_ret(22)))
        p4.metric("YTD", "{:+.2f}%".format(safe_ret(len(df_m))))
        st.markdown("---")

        cl, cr = st.columns([3, 2])

        with cl:
            if ratings_df is not None and not ratings_df.empty:
                st.markdown("### 🧑\u200d💼 Analyst Recommendations")

                def to_month(pl):
                    try:
                        return (datetime.today() + relativedelta(months=int(str(pl).replace("m", "")))).strftime("%b '%y")
                    except Exception:
                        return str(pl)

                rd = ratings_df.copy()
                rd["Month"] = rd["period"].apply(to_month)
                rd["Buy"] = rd["strongBuy"] + rd["buy"]
                rd["Sell"] = rd["sell"] + rd["strongSell"]
                rd = rd[::-1]
                fr = go.Figure()
                fr.add_trace(go.Bar(x=rd["Month"], y=rd["Buy"], name="Buy", marker_color="#00d97e"))
                fr.add_trace(go.Bar(x=rd["Month"], y=rd["hold"], name="Hold", marker_color="#6b7280"))
                fr.add_trace(go.Bar(x=rd["Month"], y=rd["Sell"], name="Sell", marker_color="#ff4d6d"))
                fr.update_layout(barmode="group", plot_bgcolor=bg_color, paper_bgcolor=paper_bg, font=dict(color=font_color), height=300, margin=dict(l=10, r=10, t=30, b=30), legend=dict(orientation="h", yanchor="bottom", y=1.01, font=dict(size=11), bgcolor="rgba(0,0,0,0)"), xaxis=dict(tickfont=dict(color=font_color), showgrid=False), yaxis=dict(tickfont=dict(color=font_color), showgrid=True, gridcolor=grid_color))
                st.plotly_chart(fr, use_container_width=True)

            st.markdown("### 🆚 vs NIFTY 50")
            fv = go.Figure()
            fv.add_trace(go.Scatter(x=df_m["Date"], y=(df_m["Close"] / df_m["Close"].iloc[0]) * 100, mode="lines", line=dict(color="#3b82f6", width=2), name=chosen_sym))
            fv.add_trace(go.Scatter(x=df_m["Date"], y=(df_m["Close_NIFTY"] / df_m["Close_NIFTY"].iloc[0]) * 100, mode="lines", line=dict(color="#f59e0b", width=2, dash="dot"), name="NIFTY 50"))
            fv.update_layout(plot_bgcolor=bg_color, paper_bgcolor=paper_bg, font=dict(color=font_color), height=250, margin=dict(l=10, r=10, t=20, b=30), hovermode="x unified", yaxis_title="Indexed (base=100)", legend=dict(orientation="h", yanchor="bottom", y=1.01, font=dict(size=11), bgcolor="rgba(0,0,0,0)"), xaxis=dict(tickfont=dict(color=font_color), showgrid=True, gridcolor=grid_color), yaxis=dict(tickfont=dict(color=font_color), showgrid=True, gridcolor=grid_color))
            st.plotly_chart(fv, use_container_width=True)

        with cr:
            st.markdown("### 🔎 Market Snapshot")

            def info_card(lbl, val, sub, color):
                sub_html = "<div style='color:#6b7280;font-size:0.78rem'>" + sub + "</div>" if sub else ""
                html = "<div style='background:rgba(30,35,64,0.6);border:1px solid #2e3150;border-radius:10px;padding:12px 16px;margin-bottom:10px;'><div style='color:#8b93b8;font-size:0.75rem'>" + lbl + "</div><div style='color:" + color + ";font-size:1.2rem;font-weight:700'>" + val + "</div>" + sub_html + "</div>"
                st.markdown(html, unsafe_allow_html=True)

            lv = int(df_m["Volume"].iloc[-1])
            av = int(df_m["Volume"].tail(21).mean())
            vr = lv / av if av else 1.0
            s20 = df_m["Close"].rolling(20).min().iloc[-1]
            r20 = df_m["Close"].rolling(20).max().iloc[-1]
            corr = df_m["Return"].corr(df_m["NIFTY_Return"])
            cc = "#00d97e" if corr > 0.7 else ("#f59e0b" if corr > 0.3 else "#ff4d6d")
            cl_txt = "High" if corr > 0.7 else ("Moderate" if corr > 0.3 else "Low")
            mt = str(pd.cut(df_m["Close"], bins=20).value_counts().idxmax())

            info_card("Today's Volume", "{:,}".format(lv), "21-Day Avg: {:,} \u00b7 Ratio: {:.2f}x".format(av, vr), "#00d97e" if vr > 1.5 else "#60a5fa")
            info_card("20-Day Support", "\u20b9{:.2f}".format(s20), "", "#00d97e")
            info_card("20-Day Resistance", "\u20b9{:.2f}".format(r20), "", "#ff4d6d")
            info_card("NIFTY Correlation (6mo)", "{:.2f}  ({})".format(corr, cl_txt), "Moves with market" if corr > 0.7 else "Independent mover", cc)
            info_card("Most Traded Range (6mo)", mt, "", "#a78bfa")
```
