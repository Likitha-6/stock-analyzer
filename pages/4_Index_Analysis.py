"""
Index Analysis Page - SIMPLIFIED VERSION
=========================================
Minimal validation, maximum compatibility
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(
    page_title="Index Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
.page-title { font-family: 'Syne', sans-serif; font-size: 2.0rem; font-weight: 800; color: #f0f4ff; letter-spacing: -0.02em; margin-bottom: 0.2rem; }
.page-sub { font-size: 0.78rem; color: #8aaac8; margin-bottom: 1.6rem; letter-spacing: 0.05em; }
.section-label { font-size: 0.68rem; letter-spacing: 0.18em; text-transform: uppercase; color: #8aaac8; border-left: 3px solid #00c882; padding-left: 0.6rem; margin-bottom: 0.8rem; margin-top: 1.6rem; }
.signal-card { background: #0b1525; border: 1px solid rgba(255,255,255,0.09); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
.signal-title { font-size: 0.9rem; font-weight: 700; color: #ffffff; margin-bottom: 0.4rem; }
.signal-detail { font-size: 0.8rem; color: #8aaac8; line-height: 1.5; }
.stat-box { background: #0b1525; border: 1px solid rgba(255,255,255,0.09); border-radius: 8px; padding: 1rem; text-align: center; margin: 0.5rem 0; }
.stat-label { font-size: 0.65rem; color: #8aaac8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem; }
.stat-value { font-size: 1.3rem; font-weight: 700; color: #00c882; }
.stat-subtext { font-size: 0.7rem; color: #00c882; margin-top: 0.2rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_data(symbol):
    """Fetch data from yfinance."""
    try:
        data = yf.download(symbol, period='1y', progress=False)
        if data is not None and len(data) > 0:
            return data
    except:
        pass
    return None

def calculate_ema(series, period):
    """Calculate EMA."""
    try:
        if len(series) >= period:
            return series.ewm(span=period, adjust=False).mean()
    except:
        pass
    return None

def calculate_rsi(series, period=14):
    """Calculate RSI."""
    try:
        if len(series) >= period:
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
    except:
        pass
    return None

# PAGE
st.markdown('<h1 class="page-title">📊 Index Analysis</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-sub">Monitor major indices with technical signals and analysis.</p>', unsafe_allow_html=True)

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

selected_index = st.selectbox('Choose an index:', list(INDICES.keys()), label_visibility='collapsed')
symbol = INDICES[selected_index]

st.markdown('<div class="section-label">Loading Data...</div>', unsafe_allow_html=True)

# Fetch data
data = fetch_data(symbol)

if data is None or len(data) == 0:
    st.error(f'❌ Could not fetch data for {selected_index}. Please try another index.')
else:
    # Calculate indicators
    ema20 = calculate_ema(data['Close'], 20)
    ema50 = calculate_ema(data['Close'], 50)
    rsi = calculate_rsi(data['Close'])
    
    # Get latest values
    try:
        current_price = float(data['Close'].iloc[-1])
    except:
        current_price = None
    
    try:
        prev_price = float(data['Close'].iloc[-2]) if len(data) > 1 else current_price
        change_pct = ((current_price - prev_price) / prev_price * 100) if prev_price and prev_price != 0 else 0
    except:
        change_pct = 0
    
    # EMA Signal
    try:
        ema20_val = float(ema20.dropna().iloc[-1]) if ema20 is not None else None
        ema50_val = float(ema50.dropna().iloc[-1]) if ema50 is not None else None
        
        if ema20_val and ema50_val:
            if ema20_val > ema50_val:
                ema_signal = 'BULLISH'
                ema_color = '#00c882'
            elif ema20_val < ema50_val:
                ema_signal = 'BEARISH'
                ema_color = '#ff4d6a'
            else:
                ema_signal = 'NEUTRAL'
                ema_color = '#8aaac8'
        else:
            ema_signal = 'NEUTRAL'
            ema_color = '#8aaac8'
    except:
        ema_signal = 'NEUTRAL'
        ema_color = '#8aaac8'
    
    # RSI Signal
    try:
        rsi_val = float(rsi.dropna().iloc[-1]) if rsi is not None else None
        rsi_val = max(0, min(100, rsi_val)) if rsi_val else None
        
        if rsi_val:
            if rsi_val > 70:
                rsi_signal = 'OVERBOUGHT'
                rsi_color = '#ff4d6a'
            elif rsi_val < 30:
                rsi_signal = 'OVERSOLD'
                rsi_color = '#00c882'
            else:
                rsi_signal = 'NEUTRAL'
                rsi_color = '#8aaac8'
        else:
            rsi_signal = 'NEUTRAL'
            rsi_color = '#8aaac8'
            rsi_val = None
    except:
        rsi_signal = 'NEUTRAL'
        rsi_color = '#8aaac8'
        rsi_val = None
    
    # 52-week stats
    try:
        high_52w = float(data['Close'].tail(252).max())
        low_52w = float(data['Close'].tail(252).min())
        pos_52w = ((current_price - low_52w) / (high_52w - low_52w) * 100) if (high_52w != low_52w) else 50
        pos_52w = max(0, min(100, pos_52w))
    except:
        high_52w = None
        low_52w = None
        pos_52w = None
    
    # Chart
    st.markdown('<div class="section-label">📈 Price Chart</div>', unsafe_allow_html=True)
    
    try:
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price',
            increasing_line_color='#00c882',
            decreasing_line_color='#ff4d6a'
        ))
        
        if ema20 is not None:
            fig.add_trace(go.Scatter(x=data.index, y=ema20, name='EMA 20',
                                    line=dict(color='#00c882', width=1, dash='dot')))
        if ema50 is not None:
            fig.add_trace(go.Scatter(x=data.index, y=ema50, name='EMA 50',
                                    line=dict(color='#ffa500', width=1, dash='dot')))
        
        fig.update_layout(
            title=f'{selected_index} - Price & EMA',
            yaxis_title='Price',
            template='plotly_dark',
            hovermode='x unified',
            height=500,
            margin=dict(l=0, r=0, t=50, b=0),
            paper_bgcolor='rgba(11, 21, 37, 1)',
            plot_bgcolor='rgba(11, 21, 37, 1)',
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f'Chart error: {str(e)}')
    
    # Signals
    st.markdown('<div class="section-label">📊 Technical Signals</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'''<div class="signal-card">
            <div class="signal-title">EMA Signal</div>
            <div style="font-size:1.2rem;font-weight:700;color:{ema_color};">{ema_signal}</div>
            <div class="signal-detail">EMA 20 {'above' if ema_signal == 'BULLISH' else 'below' if ema_signal == 'BEARISH' else 'near'} EMA 50</div>
        </div>''', unsafe_allow_html=True)
    
    with col2:
        rsi_display = f'{rsi_val:.0f}' if rsi_val is not None else 'N/A'
        st.markdown(f'''<div class="signal-card">
            <div class="signal-title">RSI Status</div>
            <div style="font-size:1.2rem;font-weight:700;color:{rsi_color};">{rsi_display}</div>
            <div class="signal-detail">{rsi_signal}</div>
        </div>''', unsafe_allow_html=True)
    
    with col3:
        if pos_52w is not None:
            pos_color = '#00c882' if pos_52w > 70 else '#ff4d6a' if pos_52w < 30 else '#ffa500'
            st.markdown(f'''<div class="signal-card">
                <div class="signal-title">52-Week Position</div>
                <div style="font-size:1.2rem;font-weight:700;color:{pos_color};">{pos_52w:.1f}%</div>
                <div class="signal-detail">From low to high</div>
            </div>''', unsafe_allow_html=True)
    
    # Statistics
    st.markdown('<div class="section-label">📊 Key Statistics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if current_price:
            st.markdown(f'''<div class="stat-box">
                <div class="stat-label">Current Price</div>
                <div class="stat-value">₹{current_price:,.0f}</div>
                <div class="stat-subtext">{'↑' if change_pct >= 0 else '↓'} {abs(change_pct):.2f}%</div>
            </div>''', unsafe_allow_html=True)
    
    with col2:
        if high_52w:
            st.markdown(f'''<div class="stat-box">
                <div class="stat-label">52-Week High</div>
                <div class="stat-value">₹{high_52w:,.0f}</div>
            </div>''', unsafe_allow_html=True)
    
    with col3:
        if low_52w:
            st.markdown(f'''<div class="stat-box">
                <div class="stat-label">52-Week Low</div>
                <div class="stat-value">₹{low_52w:,.0f}</div>
            </div>''', unsafe_allow_html=True)
    
    with col4:
        try:
            avg_vol = data['Volume'].tail(20).mean()
            st.markdown(f'''<div class="stat-box">
                <div class="stat-label">Avg Volume (20d)</div>
                <div class="stat-value">{avg_vol/1e6:.1f}M</div>
            </div>''', unsafe_allow_html=True)
        except:
            pass
    
    # Alerts
    st.markdown('<div class="section-label">⚠️ Trading Alerts</div>', unsafe_allow_html=True)
    
    alerts = []
    
    if ema_signal == 'BULLISH':
        alerts.append(('Bullish', 'EMA 20 above EMA 50 - uptrend signal', '#00c882'))
    elif ema_signal == 'BEARISH':
        alerts.append(('Bearish', 'EMA 20 below EMA 50 - downtrend signal', '#ff4d6a'))
    
    if rsi_signal == 'OVERBOUGHT':
        alerts.append(('Overbought', 'RSI > 70 - consider profit booking', '#ff4d6a'))
    elif rsi_signal == 'OVERSOLD':
        alerts.append(('Oversold', 'RSI < 30 - potential buying opportunity', '#00c882'))
    
    if pos_52w is not None:
        if pos_52w > 90:
            alerts.append(('Resistance', 'Index near 52-week high - potential selling pressure', '#ff9800'))
        elif pos_52w < 10:
            alerts.append(('Support', 'Index near 52-week low - potential support level', '#00c882'))
    
    if alerts:
        for alert_type, msg, color in alerts:
            st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-left:3px solid {color};padding:1rem;border-radius:8px;margin:0.5rem 0;"><div style="font-weight:700;color:{color};">{alert_type}</div><div style="color:#8aaac8;font-size:0.9rem;">{msg}</div></div>', unsafe_allow_html=True)
    else:
        st.info('✅ No major alerts. Index showing neutral technical conditions.')
    
    # Data table
    st.markdown('<div class="section-label">📋 Recent Data</div>', unsafe_allow_html=True)
    
    try:
        display_data = data.tail(10).copy()
        display_data.index = display_data.index.strftime('%Y-%m-%d')
        st.dataframe(display_data, use_container_width=True)
    except:
        pass

st.markdown('---')
st.markdown('⚠️ **Disclaimer:** This analysis is for educational purposes only. Always consult a financial advisor before trading.')
