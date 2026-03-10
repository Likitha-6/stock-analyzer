import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from common.data import load_name_lookup
from indicators import apply_sma, apply_ema, get_pivot_lines
from indicators import detect_cross_signals,compute_rsi
from datetime import datetime
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Technical Chart", layout="wide")

# ─────────────────────────────
# Theme selector
# ─────────────────────────────
col_title, col_theme = st.columns([6, 1])
with col_title:
    st.title("Indian Stock – Technical Analysis")
with col_theme:
    dark_mode = st.checkbox("🌙 Dark Mode", value=False)

theme = "Dark" if dark_mode else "Light"

# Theme colors
bg_color = "#FFFFFF" if theme == "Light" else "#0E1117"
font_color = "#000000" if theme == "Light" else "#FFFFFF"
increasing_color = "#00B26F" if theme == "Light" else "#26de81"
decreasing_color = "#FF3C38" if theme == "Light" else "#eb3b5a"

# ─────────────────────────────
# Search bar (shared for all tabs)
# ─────────────────────────────
name_df = load_name_lookup()
symbol2name = dict(zip(name_df["Symbol"], name_df["Company Name"]))

search_query = st.text_input("Search by Symbol or Company Name").strip().lower()
chosen_sym = None

if search_query:
    mask = (
        name_df["Symbol"].str.lower().str.contains(search_query) |
        name_df["Company Name"].str.lower().str.contains(search_query)
    )
    matches = name_df[mask]

    if matches.empty:
        st.warning("No matching stock found.")
    else:
        selected = st.selectbox(
            "Select Stock",
            matches["Symbol"] + " - " + matches["Company Name"]
        )
        chosen_sym = selected.split(" - ")[0]

# ─────────────────────────────
# Tabs
# ─────────────────────────────
tab1, tab2, tab3 = st.tabs([" Chart", " Insights", " View"])

with tab1:
    # ─────────────────────────────
    # Interval dropdown
    # ─────────────────────────────
    interval_mapping = {
        "5 minutes": "5m",
        "15 minutes": "15m",
        "1 hour": "60m",
        "1 day": "1d"
    }
    label    = st.selectbox("Select Interval", list(interval_mapping.keys()), index=0)
    interval = interval_mapping[label]

    # ─────────────────────────────
    # Session-state helpers
    # ─────────────────────────────
    if "candle_days" not in st.session_state:
        st.session_state.candle_days = 1

    # Indicator selection
    all_indicators = st.multiselect("Select Indicators", ["SMA", "EMA"], default=[])

    sma_lengths, ema_lengths = [], []
    
    if "SMA" in all_indicators:
        sma_input = st.text_input("SMA lengths (comma-separated, e.g. 20,50)", value="20,50", key="sma_input")
        try:
            sma_lengths = [int(x.strip()) for x in sma_input.split(",") if x.strip().isdigit()]
        except Exception:
            sma_lengths = []

if "EMA" in all_indicators:
    ema_input = st.text_input("EMA lengths (comma-separated, e.g. 20,50)", value="20,50", key="ema_input")
    try:
        ema_lengths = [int(x.strip()) for x in ema_input.split(",") if x.strip().isdigit()]
    except Exception:
        ema_lengths = []
    # Choose period so the chart loads enough candles
    period = (
        "60d" if interval == "1d" else
        "5d"  if interval == "60m" else
        "2d"
    )

    # Buttons to pull older intraday candles (only if intraday)
    if interval != "1d" and chosen_sym:
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("🔁 Load older candles"):
                st.session_state.candle_days += 1
        with c2:
            if st.button("♻️ Reset to 1 Day"):
                st.session_state.candle_days = 1
        st.caption(f"Showing: **{st.session_state.candle_days} day(s)** of data")

    # ─────────────────────────────
    # Chart section
    # ─────────────────────────────
    if chosen_sym:
        try:
            df = yf.Ticker(chosen_sym + ".NS").history(interval=interval, period=period)
            df = df.reset_index()

            if df.empty:
                st.error("No data found.")
                st.session_state.df_stock = None
            else:
                st.session_state.df_stock = df
                x_col = "Datetime" if "Datetime" in df.columns else "Date"
                df["x_label"] = (
                    df[x_col].dt.strftime("%d/%m %H:%M")
                    if any(k in interval for k in ("m", "h"))
                    else df[x_col].dt.strftime("%d/%m")
                )

                # ────────────────── build candlestick figure ──────────────────
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df["x_label"],
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    increasing_line_color=increasing_color,
                    decreasing_line_color=decreasing_color,
                    name="Price"
                ))

                # ←────────────── support / resistance logic ──────────────→
                if interval == "5m":               # 1-day levels
                    last_day = df[x_col].max().date()
                    sr_df = df[df[x_col].dt.date == last_day]
                elif interval == "15m":            # 1-week levels
                    end_date   = df[x_col].max().date()
                    start_date = end_date - pd.Timedelta(days=7)
                    sr_df = df[df[x_col].dt.date >= start_date]
                else:                              # fallback: whole df
                    sr_df = df

                support    = sr_df["Low"].min()
                resistance = sr_df["High"].max()

                fig.add_hline(
                    y=support,
                    line_dash="dot",
                    line_width=1,
                    line_color="#2ecc71",
                    annotation=dict(text="Support", yanchor="bottom",
                                    font=dict(color="#2ecc71"))
                )
                fig.add_hline(
                    y=resistance,
                    line_dash="dot",
                    line_width=1,
                    line_color="#e74c3c",
                    annotation=dict(text="Resistance", yanchor="top",
                                    font=dict(color="#e74c3c"))
                )
                # ────────────────── indicator overlays (EMA) ──────────────────
                if sma_lengths:
                    df = apply_sma(df, sma_lengths)
                    for sma_len in sma_lengths:
                        col = f"SMA_{sma_len}"
                        if col in df.columns and df[col].notna().sum() > 5:
                            fig.add_trace(go.Scatter(
                                x=df["x_label"], y=df[col],
                                mode="lines",
                                line=dict(width=1.5, dash="dash"),
                                name=f"SMA ({sma_len})"
                            ))
                if ema_lengths:
                    df = apply_ema(df, ema_lengths)
                    for ema_len in ema_lengths:
                        fig.add_trace(go.Scatter(
                            x=df["x_label"],
                            y=df[f"EMA_{ema_len}"],
                            mode="lines",
                            line=dict(width=1.5, dash="solid"),
                            name=f"EMA ({ema_len})"
                        ))

                # (Your crossover-signal logic unchanged)
                from indicators import detect_crossovers
                signals = detect_crossovers(df, short_col="EMA_20", long_col="EMA_50")
                for idx in signals["buy"]:
                    fig.add_trace(go.Scatter(
                        x=[df["x_label"][idx]], y=[df["Close"][idx]],
                        mode="markers",
                        marker=dict(color='green', size=10),
                        name='Buy Signal'
                    ))
                for idx in signals["sell"]:
                    fig.add_trace(go.Scatter(
                        x=[df["x_label"][idx]], y=[df["Close"][idx]],
                        mode="markers",
                        marker=dict(color='red', size=10),
                        name='Sell Signal'
                    ))

                # ────────────────── layout tweaks ──────────────────
                total_candles = len(df)
                max_ticks     = 15
                N             = max(1, total_candles // max_ticks)
                tickvals      = df["x_label"].iloc[::N].tolist()

                fig.update_layout(
                    title=f"{chosen_sym}.NS – {label} Chart ({period})",
                    xaxis_title="Date/Time",
                    yaxis_title="Price",
                    xaxis=dict(
                        type="category",
                        tickangle=-45,
                        showgrid=False,
                        tickfont=dict(color=font_color),
                        tickmode="array",
                        tickvals=tickvals,
                        ticktext=tickvals
                    ),
                    yaxis=dict(
                        showgrid=False,
                        tickfont=dict(color="#000000" if theme == "Light" else font_color),
                        fixedrange=False
                    ),
                    plot_bgcolor=bg_color,
                    paper_bgcolor=bg_color,
                    font=dict(color=font_color),
                    legend=dict(font=dict(color=font_color)),
                    xaxis_rangeslider_visible=False,
                    dragmode="pan",
                    hovermode="x unified",
                    height=600,
                    width=900
                )

                # ───────────────────────────────
                # Render chart in Streamlit
                # ───────────────────────────────
                st.plotly_chart(
                    fig,
                    use_container_width=False,
                    config={
                        "scrollZoom": True,
                        "displayModeBar": True,
                        "modeBarButtonsToRemove": [
                            "zoom2d", "select2d", "lasso2d",
                            "zoomIn2d", "zoomOut2d"
                        ],
                        "displaylogo": False
                    }
                )

        except Exception as e:
            st.error(f"Error: {e}")


with tab2:
    if chosen_sym:
        # Always fetch enough data for SMA 200
        df_insights = yf.Ticker(chosen_sym + ".NS").history(interval="1d", period="12mo")
        if not df_insights.empty:
            df_insights = df_insights.reset_index()
            df_insights["SMA_50"] = df_insights["Close"].rolling(window=50).mean()
            df_insights["SMA_200"] = df_insights["Close"].rolling(window=200).mean()
            df_insights["EMA_20"] = df_insights["Close"].ewm(span=20, adjust=False).mean()
            high_52w = df_insights["High"].max()
            low_52w = df_insights["Low"].min()

            latest_price = df_insights["Close"].iloc[-1]
            latest_sma50 = df_insights["SMA_50"].iloc[-1]
            latest_sma200 = df_insights["SMA_200"].iloc[-1]
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Current Price", f"₹{latest_price:,.2f}")
    
            with col2:
                st.metric(
                    "50-day SMA",
                    f"₹{latest_sma50:,.2f}" if pd.notna(latest_sma50) else "Not Available"
                )
    
            with col3:
                st.metric(
                    " 200-day SMA",
                    f"₹{latest_sma200:,.2f}" if pd.notna(latest_sma200) else "Not Available"
                )
            
            if df_insights["EMA_20"].iloc[-1] > df_insights["EMA_20"].iloc[-5]:
                st.success("20-day EMA is sloping upward — short-term trend is strengthening.")
            else:
                st.warning("20-day EMA is sloping downward — short-term trend may be weakening.")

            if not df_insights["Close"].empty and len(df_insights["Close"]) >= 14:
                recent_close = df_insights["Close"].tail(14)
                volatility = recent_close.std()
                latest_price = df_insights["Close"].iloc[-1]
                vol_pct = (volatility / latest_price) * 100
            
                #st.subheader("📊 Volatility Insight")
                #st.write(f"14-day Price Std Dev: ₹{volatility:.2f} ({vol_pct:.2f}%)")
            
                if vol_pct > 5:
                    st.warning(" High volatility — expect bigger price swings.")
                elif vol_pct < 2:
                    st.info(" Low volatility — stable price action.")
                else:
                    st.success(" Moderate volatility — balanced risk/reward.")


            if abs(latest_price - high_52w) < 0.03 * high_52w:
                st.info("🚀 Price is near its 52-week high — possible resistance level.")
            elif abs(latest_price - low_52w) < 0.03 * low_52w:
                st.info("🔻 Price is near its 52-week low — potential support level.")
            df_insights["RSI"] = compute_rsi(df_insights)

            latest_rsi = df_insights["RSI"].iloc[-1]
            #st.metric("📊 RSI (14-day)", f"{latest_rsi:.2f}")
            
            if latest_rsi > 70:
                st.warning(" The stock is overbought — momentum may slow, and there could be a short-term dip or consolidation.")
            elif latest_rsi < 30:
                st.success("The stock is oversold — selling may be exhausted, and a potential rebound could follow.")
            else:
                st.info(" RSI is in neutral zone – no strong momentum signal.")
                        

            signal = detect_cross_signals(df_insights)
            if signal:
                st.info(signal)
        else:
            st.warning("Not enough data to compute insights.")



with tab3:
    st.subheader(f"Market View for {chosen_sym or 'selected stock'}")

    if chosen_sym:
        try:
            # Load stock and NIFTY50 data
            stock_df = yf.Ticker(chosen_sym + ".NS").history(period="6mo", interval="1d")
            nifty_df = yf.Ticker("^NSEI").history(period="6mo", interval="1d")  # NIFTY 50

            if not stock_df.empty and not nifty_df.empty:
                stock_df = stock_df.reset_index()
                nifty_df = nifty_df.reset_index()

                # Ensure both have the same date index
                df_merged = pd.merge(
                    stock_df[["Date", "Close", "Volume"]],
                    nifty_df[["Date", "Close"]],
                    on="Date",
                    suffixes=("", "_NIFTY")
                )

                # Compute price returns
                df_merged["Return"] = df_merged["Close"].pct_change()
                df_merged["NIFTY_Return"] = df_merged["Close_NIFTY"].pct_change()
                ticker = yf.Ticker(chosen_sym + ".NS")
                ratings_df = ticker.recommendations
                #st.write(ratings_df)

                def convert_to_month(period_label):
                    try:
                        offset = int(str(period_label).replace("m", ""))
                        month = datetime.today() + relativedelta(months=offset)
                        return month.strftime("%b")  # e.g., 'Jul', 'Jun'
                    except:
                        return str(period_label)
                
                ratings_df["Month"] = ratings_df["period"].apply(convert_to_month)
                

                # Compute Buy, Hold, Sell categories
                ratings_df["Buy"] = ratings_df["strongBuy"] + ratings_df["buy"]
                ratings_df["Sell"] = ratings_df["sell"] + ratings_df["strongSell"]
                
                # Ensure order of display (most recent first)
                ratings_df = ratings_df[::-1]
                
                # Create grouped bar chart
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=ratings_df["Month"],
                    y=ratings_df["Buy"],
                    name="✅ Buy",
                    marker_color="green"
                ))
                
                fig.add_trace(go.Bar(
                    x=ratings_df["Month"],
                    y=ratings_df["hold"],
                    name="⚪ Hold",
                    marker_color="gray"
                ))
                
                fig.add_trace(go.Bar(
                    x=ratings_df["Month"],
                    y=ratings_df["Sell"],
                    name="❌ Sell",
                    marker_color="red"
                ))
                
                fig.update_layout(
                    barmode="group",
                    title="Analyst Recommendations",
                    xaxis_title="Month",
                    yaxis_title="Number of Ratings",
                    legend_title="Rating",
                    plot_bgcolor=bg_color,
                    paper_bgcolor=bg_color,
                    font=dict(color=font_color),
                    xaxis=dict(color=font_color),
                    yaxis=dict(color=font_color),
                    height=400
                )

                
                st.plotly_chart(fig, use_container_width=True)


                #st.markdown("### 📈 Price Performance")
                change_1d = (df_merged["Close"].iloc[-1] / df_merged["Close"].iloc[-2] - 1) * 100
                change_5d = (df_merged["Close"].iloc[-1] / df_merged["Close"].iloc[-6] - 1) * 100
                change_1mo = (df_merged["Close"].iloc[-1] / df_merged["Close"].iloc[-22] - 1) * 100
                change_ytd = (df_merged["Close"].iloc[-1] / df_merged["Close"].iloc[0] - 1) * 100
                col1, col2, col3, col4 = st.columns(4)

                col1.metric("1 Day", f"{change_1d:.2f}%")
                col2.metric("5 Days", f"{change_5d:.2f}%")
                col3.metric("1 Month", f"{change_1mo:.2f}%")
                col4.metric("YTD", f"{change_ytd:.2f}%")

                

                #st.markdown("### 📊 Volume Analysis")
                latest_vol = df_merged["Volume"].iloc[-1]
                avg_vol = df_merged["Volume"].tail(21).mean()
                st.write(f"Today's Volume: `{int(latest_vol):,}` | 21-Day Avg: `{int(avg_vol):,}`")
                

                #st.markdown("### 🧱 Support & Resistance (20-day)")
                support = df_merged["Close"].rolling(window=20).min().iloc[-1]
                resistance = df_merged["Close"].rolling(window=20).max().iloc[-1]
                current_price = df_merged["Close"].iloc[-1]

                st.write(f"📉 Support(20-day): ₹{support:.2f}")
                st.write(f"📈 Resistance(20-day): ₹{resistance:.2f}")

                #st.markdown("### 🤝 Correlation with NIFTY 50")
                correlation = df_merged["Return"].corr(df_merged["NIFTY_Return"])
                st.write(f"Correlation with NIFTY 50 (last 6 months): `{correlation:.2f}`")
                if correlation > 0.7:
                    st.success("✅ Highly correlated with broader market.")
                elif correlation < 0.3:
                    st.warning("⚠️ Moves independently of the NIFTY index.")

                #st.markdown("### 📅 Earnings")
                #st.info("🗓️ Next Earnings: Not available via yFinance. Please check official filings.")

                #st.markdown("### 🧭 Most Traded Price Range")
                price_bins = pd.cut(df_merged["Close"], bins=20)
                most_traded = price_bins.value_counts().idxmax()
                st.write(f"Most traded price range in last 6 months: **{most_traded}**")

            else:
                st.warning("Could not load complete data to compute View Tab insights.")

        except Exception as e:
            st.error(f"Error while generating view insights: {e}")
    else:
        st.info("Please select a stock to view details.")
