"""
Technical Analysis Page - IMPROVED VERSION
===========================================
Enhanced charts and technical indicators
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Technical Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
.page-title { font-family: 'Syne', sans-serif; font-size: 2.0rem; font-weight: 800; color: #f0f4ff; letter-spacing: -0.02em; margin-bottom: 0.2rem; }
.page-sub { font-size: 0.78rem; color: #8aaac8; margin-bottom: 1.6rem; letter-spacing: 0.05em; }
.section-label { font-size: 0.68rem; letter-spacing: 0.18em; text-transform: uppercase; color: #8aaac8; border-left: 3px solid #00c882; padding-left: 0.6rem; margin-bottom: 0.8rem; margin-top: 1.6rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">📈 Technical Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Analyze stock prices with candlestick charts, moving averages, and technical indicators</div>', unsafe_allow_html=True)

# Load stock list
try:
    import csv
    stocks = []
    with open('nse_stocks_.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stocks.append(row.get('Symbol', ''))
    stocks = sorted([s for s in stocks if s])
except:
    stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'LT', 'MARUTI', 'AXISBANK', 'NTPC']

st.markdown('<div class="section-label">Select Stock</div>', unsafe_allow_html=True)
selected_stock = st.selectbox('Choose a stock:', stocks, label_visibility='collapsed')

# Fetch data
@st.cache_data(ttl=3600)
def fetch_stock_data(symbol):
    try:
        data = yf.download(f'{symbol}.NS', period='1y', progress=False)
        return data
    except:
        return None

data = fetch_stock_data(selected_stock)

if data is None or len(data) == 0:
    st.error(f'❌ Could not fetch data for {selected_stock}. Please try another stock.')
else:
    # Calculate indicators
    data['SMA20'] = data['Close'].rolling(window=20).mean()
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['EMA20'] = data['Close'].ewm(span=20, adjust=False).mean()
    data['EMA50'] = data['Close'].ewm(span=50, adjust=False).mean()
    
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Hist'] = data['MACD'] - data['Signal']
    
    st.markdown('<div class="section-label">📊 Price Chart</div>', unsafe_allow_html=True)
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=('Price & Moving Averages', 'RSI (14)', 'MACD')
    )
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='OHLC',
        increasing_line_color='#00c882',
        decreasing_line_color='#ff4d6a'
    ), row=1, col=1)
    
    # SMA20 and SMA50
    fig.add_trace(go.Scatter(
        x=data.index, y=data['SMA20'],
        name='SMA20',
        line=dict(color='#FFD700', width=1),
        hovertemplate='<b>SMA20</b><br>₹%{y:,.2f}<extra></extra>'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=data.index, y=data['SMA50'],
        name='SMA50',
        line=dict(color='#FF6B9D', width=1),
        hovertemplate='<b>SMA50</b><br>₹%{y:,.2f}<extra></extra>'
    ), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(
        x=data.index, y=data['RSI'],
        name='RSI(14)',
        line=dict(color='#00D9FF', width=2),
        hovertemplate='<b>RSI</b><br>%{y:.2f}<extra></extra>'
    ), row=2, col=1)
    
    # RSI levels
    fig.add_hline(y=70, line_dash='dash', line_color='red', row=2, col=1)
    fig.add_hline(y=30, line_dash='dash', line_color='green', row=2, col=1)
    
    # MACD
    fig.add_trace(go.Scatter(
        x=data.index, y=data['MACD'],
        name='MACD',
        line=dict(color='#00D9FF', width=2),
        hovertemplate='<b>MACD</b><br>%{y:.4f}<extra></extra>'
    ), row=3, col=1)
    
    fig.add_trace(go.Scatter(
        x=data.index, y=data['Signal'],
        name='Signal',
        line=dict(color='#FF6B9D', width=2),
        hovertemplate='<b>Signal</b><br>%{y:.4f}<extra></extra>'
    ), row=3, col=1)
    
    fig.update_layout(
        title=f'<b>{selected_stock}</b> - Technical Analysis',
        yaxis_title='Price (₹)',
        template='plotly_dark',
        hovermode='x unified',
        height=800,
        margin=dict(l=50, r=50, t=80, b=50),
        paper_bgcolor='rgba(6, 12, 26, 1)',
        plot_bgcolor='rgba(11, 21, 37, 1)',
        xaxis3_title='Date',
        yaxis_title='Price (₹)',
        yaxis2_title='RSI',
        yaxis3_title='MACD'
    )
    
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
    
    # Summary statistics
    st.markdown('<div class="section-label">📊 Summary Statistics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    current_price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2]
    change = current_price - prev_price
    change_pct = (change / prev_price * 100) if prev_price != 0 else 0
    
    with col1:
        st.metric('Current Price', f'₹{current_price:,.2f}', f'{change:+.2f} ({change_pct:+.2f}%)')
    
    with col2:
        st.metric('52W High', f'₹{data["Close"].tail(252).max():,.2f}')
    
    with col3:
        st.metric('52W Low', f'₹{data["Close"].tail(252).min():,.2f}')
    
    with col4:
        st.metric('SMA20', f'₹{data["SMA20"].iloc[-1]:,.2f}')
    
    with col5:
        rsi_val = data['RSI'].iloc[-1]
        st.metric('RSI(14)', f'{rsi_val:.2f}')
    
    # Technical signals
    st.markdown('<div class="section-label">📈 Technical Signals</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sma_signal = 'BULLISH' if data['SMA20'].iloc[-1] > data['SMA50'].iloc[-1] else 'BEARISH'
        st.metric('SMA Crossover', sma_signal)
    
    with col2:
        if data['RSI'].iloc[-1] > 70:
            rsi_signal = 'OVERBOUGHT'
        elif data['RSI'].iloc[-1] < 30:
            rsi_signal = 'OVERSOLD'
        else:
            rsi_signal = 'NEUTRAL'
        st.metric('RSI Status', rsi_signal)
    
    with col3:
        if data['MACD'].iloc[-1] > data['Signal'].iloc[-1]:
            macd_signal = 'BULLISH'
        else:
            macd_signal = 'BEARISH'
        st.metric('MACD Signal', macd_signal)
    
    # Recent data
    st.markdown('<div class="section-label">📋 Recent Data (Last 20 Days)</div>', unsafe_allow_html=True)
    
    display_data = data.tail(20)[['Open', 'High', 'Low', 'Close', 'Volume', 'RSI']].copy()
    display_data.index = display_data.index.strftime('%Y-%m-%d')
    st.dataframe(display_data, use_container_width=True)

st.markdown('---')
st.markdown('⚠️ **Disclaimer:** This analysis is for educational purposes only. Always conduct your own research before trading.')
