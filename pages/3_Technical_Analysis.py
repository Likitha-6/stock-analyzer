"""
Technical Analysis Page - CLEAN VERSION
========================================
Candlestick chart + SMA/EMA + RSI + MACD
No search bar - direct stock selection
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Technical Analysis", page_icon="📈", layout="wide", initial_sidebar_state="auto")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
.page-title { font-family: 'Syne', sans-serif; font-size: 2.0rem; font-weight: 800; color: #f0f4ff; }
.page-sub { font-size: 0.78rem; color: #8aaac8; margin-bottom: 1.6rem; }
.section-label { font-size: 0.68rem; text-transform: uppercase; color: #8aaac8; border-left: 3px solid #00c882; padding-left: 0.6rem; margin-bottom: 0.8rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="page-title">📈 Technical Analysis</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-sub">Analyze stocks with candlestick charts and technical indicators.</p>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Search Stock</div>', unsafe_allow_html=True)

# Load all stocks from CSV
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

# Search bar
search_query = st.text_input('🔍 Search by stock symbol...', placeholder='e.g., RELIANCE, TCS, INFY', label_visibility='collapsed')

# Filter stocks based on search
if search_query:
    filtered_stocks = [s for s in stocks if search_query.upper() in s]
    if filtered_stocks:
        selected_stock = st.selectbox('Select from results:', filtered_stocks, label_visibility='collapsed')
    else:
        st.error(f'No stocks found matching "{search_query}"')
        st.stop()
else:
    st.info('👆 Search for a stock symbol above')
    st.stop()

@st.cache_data(ttl=3600)
def fetch_data(symbol):
    try:
        return yf.download(f'{symbol}.NS', period='1y', progress=False, interval='1d')
    except:
        return None

with st.spinner(f'Loading {selected_stock}...'):
    data = fetch_data(selected_stock)

if data is None or len(data) == 0:
    st.error(f'Could not fetch data for {selected_stock}')
    st.stop()

# Calculate indicators
data['SMA20'] = data['Close'].rolling(20).mean()
data['SMA50'] = data['Close'].rolling(50).mean()
data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()

# RSI
delta = data['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
data['RSI'] = 100 - (100 / (1 + rs))

# MACD
data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = data['EMA12'] - data['EMA26']
data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
data['MACD_Hist'] = data['MACD'] - data['Signal']

st.markdown('<div class="section-label">📊 Price Chart with Support & Resistance</div>', unsafe_allow_html=True)

try:
    import plotly.graph_objects as go
    
    # Get last 200 days of data
    chart_df = data.tail(200).copy()
    
    # Calculate support and resistance (52-week) - use float() to convert Series to scalar
    high_52w = float(data['Close'].tail(252).max())
    low_52w = float(data['Close'].tail(252).min())
    
    # Create figure
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=chart_df.index,
        y=chart_df['Close'],
        name='Close Price',
        line=dict(color='#00c882', width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 200, 130, 0.1)'
    ))
    
    # Add SMA20
    fig.add_trace(go.Scatter(
        x=chart_df.index,
        y=chart_df['SMA20'],
        name='SMA20',
        line=dict(color='#FFD700', width=1.5, dash='dash')
    ))
    
    # Add SMA50
    fig.add_trace(go.Scatter(
        x=chart_df.index,
        y=chart_df['SMA50'],
        name='SMA50',
        line=dict(color='#FF6B9D', width=1.5, dash='dash')
    ))
    
    # Add resistance line (52W High)
    fig.add_hline(
        y=high_52w,
        line_dash='dash',
        line_color='#ff4d6a',
        line_width=2,
        annotation_text=f'Resistance: ₹{high_52w:,.0f}',
        annotation_position='right'
    )
    
    # Add support line (52W Low)
    fig.add_hline(
        y=low_52w,
        line_dash='dash',
        line_color='#00c882',
        line_width=2,
        annotation_text=f'Support: ₹{low_52w:,.0f}',
        annotation_position='right'
    )
    
    # Update layout
    fig.update_layout(
        title=f'{selected_stock} - Price Chart with Support & Resistance',
        xaxis_title='Date',
        yaxis_title='Price (₹)',
        height=500,
        template='plotly_dark',
        hovermode='x unified',
        paper_bgcolor='rgba(6,12,26,1)',
        plot_bgcolor='rgba(11,21,37,1)',
        margin=dict(l=60, r=150, t=80, b=60),
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)'),
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor='rgba(11,21,37,0.8)',
            bordercolor='rgba(255,255,255,0.1)',
            borderwidth=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
except Exception as e:
    st.error(f'Chart error: {str(e)}')

st.markdown('<div class="section-label">📊 RSI (14) Indicator</div>', unsafe_allow_html=True)

try:
    rsi_data = data['RSI'].tail(200).copy()
    rsi_data.name = 'RSI'
    st.line_chart(rsi_data, height=250, use_container_width=True)
except Exception as e:
    st.error(f'RSI chart error: {str(e)}')

# ANALYSIS RECOMMENDATIONS
st.markdown('<div class="section-label">🎯 Technical Analysis & Recommendations</div>', unsafe_allow_html=True)

try:
    # Get current values
    current = float(data['Close'].iloc[-1])
    prev = float(data['Close'].iloc[-2]) if len(data) > 1 else current
    change = current - prev
    change_pct = (change / prev * 100) if prev != 0 else 0
    
    sma20 = float(data['SMA20'].iloc[-1]) if len(data['SMA20'].dropna()) > 0 else 0
    sma50 = float(data['SMA50'].iloc[-1]) if len(data['SMA50'].dropna()) > 0 else 0
    ema20 = float(data['EMA20'].iloc[-1]) if len(data['EMA20'].dropna()) > 0 else 0
    ema50 = float(data['EMA50'].iloc[-1]) if len(data['EMA50'].dropna()) > 0 else 0
    
    rsi = float(data['RSI'].iloc[-1]) if len(data['RSI'].dropna()) > 0 else 50
    macd = float(data['MACD'].iloc[-1]) if len(data['MACD'].dropna()) > 0 else 0
    signal = float(data['Signal'].iloc[-1]) if len(data['Signal'].dropna()) > 0 else 0
    
    high_52w = float(data['Close'].tail(252).max())
    low_52w = float(data['Close'].tail(252).min())
    position_52w = ((current - low_52w) / (high_52w - low_52w) * 100) if (high_52w != low_52w) else 50
    
    # Generate signals
    signals = []
    
    # 1. Moving Average Analysis
    if sma20 > sma50:
        signals.append(('Bullish', 'SMA20 > SMA50 (Uptrend)', '#00c882'))
    else:
        signals.append(('Bearish', 'SMA20 < SMA50 (Downtrend)', '#ff4d6a'))
    
    # 2. Price vs Moving Averages
    if current > ema20 > ema50:
        signals.append(('Strong Bullish', 'Price > EMA20 > EMA50', '#00c882'))
    elif current < ema20 < ema50:
        signals.append(('Strong Bearish', 'Price < EMA20 < EMA50', '#ff4d6a'))
    
    # 3. RSI Analysis
    if rsi > 70:
        signals.append(('Overbought', f'RSI {rsi:.0f} > 70 (Consider Selling)', '#ff4d6a'))
    elif rsi < 30:
        signals.append(('Oversold', f'RSI {rsi:.0f} < 30 (Consider Buying)', '#00c882'))
    elif rsi > 60:
        signals.append(('Strong Momentum', f'RSI {rsi:.0f} (Bullish)', '#00c882'))
    elif rsi < 40:
        signals.append(('Weak Momentum', f'RSI {rsi:.0f} (Bearish)', '#ff4d6a'))
    
    # 4. MACD Analysis
    if macd > signal:
        signals.append(('MACD Bullish', 'MACD > Signal Line (Momentum Up)', '#00c882'))
    else:
        signals.append(('MACD Bearish', 'MACD < Signal Line (Momentum Down)', '#ff4d6a'))
    
    # 5. Price Position
    if position_52w > 80:
        signals.append(('Near Resistance', f'Price at {position_52w:.0f}% of 52W (Selling Zone)', '#ff9800'))
    elif position_52w < 20:
        signals.append(('Near Support', f'Price at {position_52w:.0f}% of 52W (Buying Zone)', '#00c882'))
    
    # 6. Trend Analysis
    if current > sma20 > sma50 and sma20 > sma50:
        signals.append(('Uptrend', 'Price & MA are aligned upward', '#00c882'))
    elif current < sma20 < sma50:
        signals.append(('Downtrend', 'Price & MA are aligned downward', '#ff4d6a'))
    
    # Display signals
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('**📊 Signal Analysis:**')
        for signal_type, message, color in signals[:4]:
            st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-left:4px solid {color};padding:0.8rem;border-radius:6px;margin:0.5rem 0;"><div style="font-weight:700;color:{color};font-size:0.9rem;">{signal_type}</div><div style="color:#8aaac8;font-size:0.8rem;margin-top:0.3rem;">{message}</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('**⚡ Additional Signals:**')
        for signal_type, message, color in signals[4:]:
            st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-left:4px solid {color};padding:0.8rem;border-radius:6px;margin:0.5rem 0;"><div style="font-weight:700;color:{color};font-size:0.9rem;">{signal_type}</div><div style="color:#8aaac8;font-size:0.8rem;margin-top:0.3rem;">{message}</div></div>', unsafe_allow_html=True)
    
    # Overall Recommendation
    st.markdown('<div class="section-label">🎯 Overall Recommendation</div>', unsafe_allow_html=True)
    
    bullish_count = sum(1 for s in signals if s[0] in ['Bullish', 'Strong Bullish', 'MACD Bullish', 'Uptrend', 'Oversold', 'Near Support'])
    bearish_count = sum(1 for s in signals if s[0] in ['Bearish', 'Strong Bearish', 'MACD Bearish', 'Downtrend', 'Overbought', 'Near Resistance'])
    
    if bullish_count > bearish_count:
        recommendation = 'BUY'
        rec_color = '#00c882'
        rec_reason = f'{bullish_count} bullish signals vs {bearish_count} bearish signals'
    elif bearish_count > bullish_count:
        recommendation = 'SELL'
        rec_color = '#ff4d6a'
        rec_reason = f'{bearish_count} bearish signals vs {bullish_count} bullish signals'
    else:
        recommendation = 'HOLD'
        rec_color = '#ffa500'
        rec_reason = 'Mixed signals - wait for clarity'
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid {rec_color};border-radius:12px;padding:1.5rem;text-align:center;"><div style="font-size:0.75rem;color:#8aaac8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Recommendation</div><div style="font-size:2rem;font-weight:800;color:{rec_color};">{recommendation}</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid #8aaac8;border-radius:12px;padding:1.5rem;text-align:center;"><div style="font-size:0.75rem;color:#8aaac8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">Entry Point</div><div style="font-size:1.5rem;font-weight:700;color:#00c882;">₹{current:,.2f}</div><div style="font-size:0.8rem;color:#8aaac8;margin-top:0.5rem;">Current Price</div></div>', unsafe_allow_html=True)
    
    with col3:
        support = low_52w
        resistance = high_52w
        st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid #8aaac8;border-radius:12px;padding:1.5rem;text-align:center;"><div style="font-size:0.75rem;color:#8aaac8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem;">52W Range</div><div style="font-size:0.9rem;color:#00c882;margin-bottom:0.3rem;">H: ₹{resistance:,.0f}</div><div style="font-size:0.9rem;color:#ff4d6a;">L: ₹{support:,.0f}</div></div>', unsafe_allow_html=True)
    
    # ATR Calculation
    st.markdown('<div class="section-label">📈 Price Targets & Risk Management</div>', unsafe_allow_html=True)
    
    # Calculate ATR
    tr1 = data['High'] - data['Low']
    tr2 = abs(data['High'] - data['Close'].shift())
    tr3 = abs(data['Low'] - data['Close'].shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    
    if pd.isna(atr):
        atr = (data['High'] - data['Low']).iloc[-20:].mean()
    
    # Calculate targets
    stop_loss = current - atr
    target_1 = current + atr
    target_2 = current + (2 * atr)
    target_3 = current + (3 * atr)
    
    # Risk-Reward Ratios
    risk = current - stop_loss
    rr_1 = (target_1 - current) / risk if risk > 0 else 0
    rr_2 = (target_2 - current) / risk if risk > 0 else 0
    rr_3 = (target_3 - current) / risk if risk > 0 else 0
    
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
    - Buy at: ₹{current:,.2f} (Current Price)
    - Risk: ₹{risk:,.2f} per share
    - Exit partial position at Target 1, 2, and 3
    - Recommended: Use a 1:2 or 1:3 Risk-Reward ratio
    - ATR Value (Volatility): ₹{atr:,.2f}
    ''', unsafe_allow_html=True)
    
    st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-left:4px solid {rec_color};padding:1rem;border-radius:8px;margin:1rem 0;"><div style="color:#8aaac8;font-size:0.9rem;"><strong>Reason:</strong> {rec_reason}</div><div style="color:#8aaac8;font-size:0.85rem;margin-top:0.5rem;"><strong>Note:</strong> This is a technical analysis-based recommendation. Always do your own research and consult a financial advisor before trading.</div></div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f'Analysis error: {str(e)}')

st.markdown('---')
st.markdown('⚠️ For educational purposes only. Always consult a financial advisor.')
