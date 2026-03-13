"""
Index Analysis Page - FIXED VERSION
====================================
Line chart for indices with all indicators
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Index Analysis", page_icon="📊", layout="wide")

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
.stat-box { background: #0b1525; border: 1px solid rgba(255,255,255,0.09); border-radius: 8px; padding: 1rem; text-align: center; }
.stat-value { font-size: 1.3rem; font-weight: 700; color: #00c882; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="page-title">📊 Index Analysis</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-sub">Monitor major indices with technical signals.</p>', unsafe_allow_html=True)

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
        return yf.download(sym, period='1y', progress=False)
    except:
        return None

data = fetch_data(symbol)

if data is None or len(data) == 0:
    st.error(f'Could not fetch data for {selected_index}')
else:
    # Calculate EMAs
    ema20 = data['Close'].ewm(span=20, adjust=False).mean()
    ema50 = data['Close'].ewm(span=50, adjust=False).mean()
    
    # Calculate RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Values
    current = float(data['Close'].iloc[-1])
    prev = float(data['Close'].iloc[-2]) if len(data) > 1 else current
    change_pct = ((current - prev) / prev * 100) if prev != 0 else 0
    
    try:
        ema20_val = float(ema20.dropna().iloc[-1])
        ema50_val = float(ema50.dropna().iloc[-1])
        ema_signal = 'BULLISH' if ema20_val > ema50_val else 'BEARISH' if ema20_val < ema50_val else 'NEUTRAL'
        ema_color = '#00c882' if ema_signal == 'BULLISH' else '#ff4d6a' if ema_signal == 'BEARISH' else '#8aaac8'
    except:
        ema_signal = 'NEUTRAL'
        ema_color = '#8aaac8'
    
    try:
        rsi_val = float(rsi.dropna().iloc[-1])
        rsi_val = max(0, min(100, rsi_val))
        if rsi_val > 70:
            rsi_signal = 'OVERBOUGHT'
            rsi_color = '#ff4d6a'
        elif rsi_val < 30:
            rsi_signal = 'OVERSOLD'
            rsi_color = '#00c882'
        else:
            rsi_signal = 'NEUTRAL'
            rsi_color = '#8aaac8'
    except:
        rsi_signal = 'NEUTRAL'
        rsi_color = '#8aaac8'
        rsi_val = None
    
    try:
        high_52w = float(data['Close'].tail(252).max())
        low_52w = float(data['Close'].tail(252).min())
        pos_52w = ((current - low_52w) / (high_52w - low_52w) * 100) if high_52w != low_52w else 50
    except:
        high_52w = None
        low_52w = None
        pos_52w = None
    
    # CHART
    st.markdown('<div class="section-label">📈 Price Chart</div>', unsafe_allow_html=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Price', line=dict(color='#00c882', width=2), fill='tozeroy', fillcolor='rgba(0,200,130,0.1)'))
    fig.add_trace(go.Scatter(x=data.index, y=ema20, name='EMA 20', line=dict(color='#FFD700', width=1, dash='dash')))
    fig.add_trace(go.Scatter(x=data.index, y=ema50, name='EMA 50', line=dict(color='#FF6B9D', width=1, dash='dash')))
    
    fig.update_layout(title=f'{selected_index}', height=400, template='plotly_dark', hovermode='x unified', paper_bgcolor='rgba(6,12,26,1)', plot_bgcolor='rgba(11,21,37,1)', margin=dict(l=40, r=40, t=40, b=40))
    st.plotly_chart(fig, use_container_width=True)
    
    # Signals
    st.markdown('<div class="section-label">📊 Signals</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'<div class="signal-card"><div style="font-size:0.8rem;color:#8aaac8;">EMA Signal</div><div style="font-size:1.2rem;font-weight:700;color:{ema_color};">{ema_signal}</div></div>', unsafe_allow_html=True)
    with col2:
        rsi_display = f'{rsi_val:.0f}' if rsi_val else 'N/A'
        st.markdown(f'<div class="signal-card"><div style="font-size:0.8rem;color:#8aaac8;">RSI</div><div style="font-size:1.2rem;font-weight:700;color:{rsi_color};">{rsi_display}</div></div>', unsafe_allow_html=True)
    with col3:
        if pos_52w:
            pos_color = '#00c882' if pos_52w > 70 else '#ff4d6a' if pos_52w < 30 else '#ffa500'
            st.markdown(f'<div class="signal-card"><div style="font-size:0.8rem;color:#8aaac8;">52W Pos</div><div style="font-size:1.2rem;font-weight:700;color:{pos_color};">{pos_52w:.0f}%</div></div>', unsafe_allow_html=True)
    
    # Stats
    st.markdown('<div class="section-label">📊 Statistics</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="stat-box"><div style="font-size:0.65rem;color:#8aaac8;text-transform:uppercase;">Current</div><div class="stat-value">₹{current:,.0f}</div><div style="font-size:0.7rem;color:#00c882;">{"↑" if change_pct >= 0 else "↓"} {abs(change_pct):.2f}%</div></div>', unsafe_allow_html=True)
    with col2:
        if high_52w:
            st.markdown(f'<div class="stat-box"><div style="font-size:0.65rem;color:#8aaac8;text-transform:uppercase;">52W High</div><div class="stat-value">₹{high_52w:,.0f}</div></div>', unsafe_allow_html=True)
    with col3:
        if low_52w:
            st.markdown(f'<div class="stat-box"><div style="font-size:0.65rem;color:#8aaac8;text-transform:uppercase;">52W Low</div><div class="stat-value">₹{low_52w:,.0f}</div></div>', unsafe_allow_html=True)
    with col4:
        try:
            avg_vol = data['Volume'].tail(20).mean()
            st.markdown(f'<div class="stat-box"><div style="font-size:0.65rem;color:#8aaac8;text-transform:uppercase;">Avg Vol</div><div class="stat-value">{avg_vol/1e6:.1f}M</div></div>', unsafe_allow_html=True)
        except:
            pass
    
    # Data table
    st.markdown('<div class="section-label">📋 Recent Data</div>', unsafe_allow_html=True)
    display = data.tail(10).copy()
    display.index = display.index.strftime('%Y-%m-%d')
    st.dataframe(display, use_container_width=True)

st.markdown('---')
st.markdown('⚠️ For educational purposes only.')
