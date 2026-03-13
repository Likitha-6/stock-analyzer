"""
Index Analysis - OHLC BAR CHART VERSION
========================================
Uses OHLC bars instead of candlesticks - more reliable
All indicators: SMA20/50, EMA20/50, RSI, MACD
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Index Analysis", page_icon="📊", layout="wide", initial_sidebar_state="auto")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
.page-title { font-family: 'Syne', sans-serif; font-size: 2.0rem; font-weight: 800; color: #f0f4ff; }
.page-sub { font-size: 0.78rem; color: #8aaac8; margin-bottom: 1.6rem; }
.section-label { font-size: 0.68rem; text-transform: uppercase; color: #8aaac8; border-left: 3px solid #00c882; padding-left: 0.6rem; margin-bottom: 0.8rem; }
.signal-card { background: #0b1525; border: 1px solid rgba(255,255,255,0.09); border-radius: 12px; padding: 1.5rem; }
.signal-title { font-size: 0.9rem; font-weight: 700; color: #ffffff; margin-bottom: 0.4rem; }
.signal-detail { font-size: 0.8rem; color: #8aaac8; }
.stat-box { background: #0b1525; border: 1px solid rgba(255,255,255,0.09); border-radius: 8px; padding: 1rem; text-align: center; }
.stat-label { font-size: 0.65rem; color: #8aaac8; text-transform: uppercase; margin-bottom: 0.3rem; }
.stat-value { font-size: 1.3rem; font-weight: 700; color: #00c882; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="page-title">📊 Index Analysis</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-sub">Monitor indices with OHLC bars, moving averages, RSI, MACD.</p>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Select Index</div>', unsafe_allow_html=True)

INDICES = {
    'NIFTY 50': '^NSEI',
    'SENSEX': '^BSESN',
    'NIFTY Bank': '^NSEBANK',
    'NIFTY IT': '^CNXIT',
    'NIFTY Pharma': '^CNXPHARMA',
    'NIFTY FMCG': '^CNXFMCG',
    'NIFTY Auto': '^CNXAUTO',
    'NIFTY Metal': '^CNXMETAL',
}

selected_index = st.selectbox('Choose:', list(INDICES.keys()), label_visibility='collapsed')
symbol = INDICES[selected_index]

@st.cache_data(ttl=3600)
def fetch_data(sym):
    try:
        return yf.download(sym, period='1y', progress=False, interval='1d')
    except:
        return None

with st.spinner(f'Loading {selected_index}...'):
    data = fetch_data(symbol)

if data is None or len(data) == 0:
    st.error(f'Could not fetch data for {selected_index}')
    st.stop()

# Calculate indicators
data['SMA20'] = data['Close'].rolling(20).mean()
data['SMA50'] = data['Close'].rolling(50).mean()
data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()

delta = data['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
rs = gain / loss
data['RSI'] = 100 - (100 / (1 + rs))

data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = data['EMA12'] - data['EMA26']
data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()

# Get values
current = float(data['Close'].iloc[-1])
prev = float(data['Close'].iloc[-2]) if len(data) > 1 else current
change_pct = ((current - prev) / prev * 100) if prev != 0 else 0

ema20_val = float(data['EMA20'].dropna().iloc[-1]) if len(data['EMA20'].dropna()) > 0 else 0
ema50_val = float(data['EMA50'].dropna().iloc[-1]) if len(data['EMA50'].dropna()) > 0 else 0
ema_signal = 'BULLISH' if ema20_val > ema50_val else 'BEARISH' if ema20_val < ema50_val else 'NEUTRAL'
ema_color = '#00c882' if ema_signal == 'BULLISH' else '#ff4d6a' if ema_signal == 'BEARISH' else '#8aaac8'

rsi_val = float(data['RSI'].dropna().iloc[-1]) if len(data['RSI'].dropna()) > 0 else None
if rsi_val: rsi_val = max(0, min(100, rsi_val))
rsi_signal = 'OVERBOUGHT' if (rsi_val and rsi_val > 70) else 'OVERSOLD' if (rsi_val and rsi_val < 30) else 'NEUTRAL'
rsi_color = '#ff4d6a' if rsi_signal == 'OVERBOUGHT' else '#00c882' if rsi_signal == 'OVERSOLD' else '#8aaac8'

macd_val = float(data['MACD'].dropna().iloc[-1]) if len(data['MACD'].dropna()) > 0 else 0
signal_val = float(data['Signal'].dropna().iloc[-1]) if len(data['Signal'].dropna()) > 0 else 0
macd_signal = 'BULLISH' if macd_val > signal_val else 'BEARISH'
macd_color = '#00c882' if macd_signal == 'BULLISH' else '#ff4d6a'

high_52w = float(data['Close'].tail(252).max())
low_52w = float(data['Close'].tail(252).min())
pos_52w = ((current - low_52w) / (high_52w - low_52w) * 100) if (high_52w != low_52w) else 50

# CHART - OHLC BAR CHART
st.markdown('<div class="section-label">📈 Price Chart (OHLC Bars with Moving Averages)</div>', unsafe_allow_html=True)

try:
    fig = go.Figure()
    
    # OHLC Bars
    fig.add_trace(go.Ohlc(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='OHLC',
        increasing_line_color='#00c882',
        decreasing_line_color='#ff4d6a'
    ))
    
    # Moving averages
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA20'], name='SMA20', line=dict(color='#FFD700', width=1.5, dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='SMA50', line=dict(color='#FF6B9D', width=1.5, dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA20'], name='EMA20', line=dict(color='#00D9FF', width=1, dash='dot')))
    fig.add_trace(go.Scatter(x=data.index, y=data['EMA50'], name='EMA50', line=dict(color='#FF1493', width=1, dash='dot')))
    
    fig.update_layout(
        title=f'{selected_index} - OHLC Chart with Moving Averages',
        height=500,
        template='plotly_dark',
        hovermode='x unified',
        paper_bgcolor='rgba(6,12,26,1)',
        plot_bgcolor='rgba(11,21,37,1)',
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f'Chart error: {str(e)}')

# SIGNALS
st.markdown('<div class="section-label">📊 Technical Signals</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f'<div class="signal-card"><div class="signal-title">EMA Signal</div><div style="font-size:1.2rem;font-weight:700;color:{ema_color};">{ema_signal}</div><div class="signal-detail">EMA20 vs EMA50</div></div>', unsafe_allow_html=True)

with col2:
    rsi_display = f'{rsi_val:.0f}' if rsi_val else 'N/A'
    st.markdown(f'<div class="signal-card"><div class="signal-title">RSI (14)</div><div style="font-size:1.2rem;font-weight:700;color:{rsi_color};">{rsi_display}</div><div class="signal-detail">{rsi_signal}</div></div>', unsafe_allow_html=True)

with col3:
    st.markdown(f'<div class="signal-card"><div class="signal-title">MACD</div><div style="font-size:1.2rem;font-weight:700;color:{macd_color};">{macd_signal}</div><div class="signal-detail">MACD vs Signal</div></div>', unsafe_allow_html=True)

with col4:
    pos_color = '#00c882' if pos_52w > 70 else '#ff4d6a' if pos_52w < 30 else '#ffa500'
    st.markdown(f'<div class="signal-card"><div class="signal-title">52-Week Position</div><div style="font-size:1.2rem;font-weight:700;color:{pos_color};">{pos_52w:.0f}%</div></div>', unsafe_allow_html=True)

# STATISTICS
st.markdown('<div class="section-label">📊 Key Statistics</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f'<div class="stat-box"><div class="stat-label">Current Price</div><div class="stat-value">₹{current:,.0f}</div><div style="font-size:0.7rem;color:#00c882;">{"↑" if change_pct >= 0 else "↓"} {abs(change_pct):.2f}%</div></div>', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div class="stat-box"><div class="stat-label">52-Week High</div><div class="stat-value">₹{high_52w:,.0f}</div></div>', unsafe_allow_html=True)

with col3:
    st.markdown(f'<div class="stat-box"><div class="stat-label">52-Week Low</div><div class="stat-value">₹{low_52w:,.0f}</div></div>', unsafe_allow_html=True)

with col4:
    try:
        avg_vol = data['Volume'].tail(20).mean()
        st.markdown(f'<div class="stat-box"><div class="stat-label">Avg Volume (20d)</div><div class="stat-value">{avg_vol/1e6:.1f}M</div></div>', unsafe_allow_html=True)
    except:
        pass

# ALERTS
st.markdown('<div class="section-label">⚠️ Trading Alerts</div>', unsafe_allow_html=True)

alerts = []
if ema_signal == 'BULLISH':
    alerts.append(('Bullish', 'EMA20 above EMA50', '#00c882'))
elif ema_signal == 'BEARISH':
    alerts.append(('Bearish', 'EMA20 below EMA50', '#ff4d6a'))
if rsi_signal == 'OVERBOUGHT':
    alerts.append(('Overbought', 'RSI > 70', '#ff4d6a'))
elif rsi_signal == 'OVERSOLD':
    alerts.append(('Oversold', 'RSI < 30', '#00c882'))
if macd_signal == 'BULLISH':
    alerts.append(('MACD Bullish', 'MACD > Signal', '#00c882'))
if pos_52w > 90:
    alerts.append(('Resistance', 'Near 52W high', '#ff9800'))
elif pos_52w < 10:
    alerts.append(('Support', 'Near 52W low', '#00c882'))

if alerts:
    for t, m, c in alerts:
        st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-left:3px solid {c};padding:1rem;border-radius:8px;margin:0.5rem 0;"><div style="font-weight:700;color:{c};">{t}</div><div style="color:#8aaac8;">{m}</div></div>', unsafe_allow_html=True)
else:
    st.info('✅ No alerts')

# DATA TABLE
st.markdown('<div class="section-label">📋 Recent Data</div>', unsafe_allow_html=True)

display = data[['Open', 'High', 'Low', 'Close', 'Volume', 'SMA20', 'SMA50', 'RSI', 'MACD']].tail(20).copy()
display.index = display.index.strftime('%Y-%m-%d')
st.dataframe(display, use_container_width=True)

st.markdown('---')
st.markdown('⚠️ For educational purposes.')
