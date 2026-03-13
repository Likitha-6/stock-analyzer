"""
Technical Analysis Page - FIXED VERSION
========================================
Stock analysis with candlestick and indicators
"""

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

st.set_page_config(page_title="Technical Analysis", page_icon="📈", layout="wide")

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
st.markdown('<p class="page-sub">Analyze stocks with candlesticks, moving averages, and indicators.</p>', unsafe_allow_html=True)

# Load stocks
try:
    import csv
    stocks = []
    with open('nse_stocks_.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('Symbol'):
                stocks.append(row['Symbol'])
    stocks = sorted(list(set([s for s in stocks if s])))[:100]
except:
    stocks = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICIBANK', 'SBIN', 'LT', 'MARUTI', 'AXISBANK', 'NTPC']

st.markdown('<div class="section-label">Select Stock</div>', unsafe_allow_html=True)
selected_stock = st.selectbox('Choose:', stocks, label_visibility='collapsed')

@st.cache_data(ttl=3600)
def fetch_stock(symbol):
    try:
        return yf.download(f'{symbol}.NS', period='1y', progress=False)
    except:
        return None

data = fetch_stock(selected_stock)

if data is None or len(data) == 0:
    st.error(f'Could not fetch data for {selected_stock}')
else:
    # Calculate indicators
    data['SMA20'] = data['Close'].rolling(20).mean()
    data['SMA50'] = data['Close'].rolling(50).mean()
    
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
    
    st.markdown('<div class="section-label">📊 Price Chart with Indicators</div>', unsafe_allow_html=True)
    
    # Create subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        row_heights=[0.6, 0.2, 0.2]
    )
    
    # Candlestick
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
    
    # Moving averages
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA20'], name='SMA20', line=dict(color='#FFD700', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], name='SMA50', line=dict(color='#FF6B9D', width=1)), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='#00D9FF', width=2)), row=2, col=1)
    fig.add_hline(y=70, line_dash='dash', line_color='red', row=2, col=1)
    fig.add_hline(y=30, line_dash='dash', line_color='green', row=2, col=1)
    
    # MACD
    fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], name='MACD', line=dict(color='#00D9FF', width=2)), row=3, col=1)
    fig.add_trace(go.Scatter(x=data.index, y=data['Signal'], name='Signal', line=dict(color='#FF6B9D', width=2)), row=3, col=1)
    
    fig.update_xaxes(title_text='Date', row=3, col=1)
    fig.update_yaxes(title_text='Price (₹)', row=1, col=1)
    fig.update_yaxes(title_text='RSI', row=2, col=1)
    fig.update_yaxes(title_text='MACD', row=3, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    fig.update_layout(
        title=f'{selected_stock} - Technical Analysis',
        height=800,
        template='plotly_dark',
        hovermode='x unified',
        paper_bgcolor='rgba(6,12,26,1)',
        plot_bgcolor='rgba(11,21,37,1)',
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary
    st.markdown('<div class="section-label">📊 Summary</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    current = data['Close'].iloc[-1]
    prev = data['Close'].iloc[-2]
    change = current - prev
    
    with col1:
        st.metric('Price', f'₹{current:,.2f}', f'{change:+.2f}')
    with col2:
        st.metric('SMA20', f'₹{data["SMA20"].iloc[-1]:,.2f}')
    with col3:
        st.metric('SMA50', f'₹{data["SMA50"].iloc[-1]:,.2f}')
    with col4:
        st.metric('RSI', f'{data["RSI"].iloc[-1]:.0f}')
    with col5:
        st.metric('MACD', f'{data["MACD"].iloc[-1]:.4f}')
    
    # Data table
    st.markdown('<div class="section-label">📋 Recent Data</div>', unsafe_allow_html=True)
    display = data.tail(20)[['Open', 'High', 'Low', 'Close', 'Volume', 'RSI']].copy()
    display.index = display.index.strftime('%Y-%m-%d')
    st.dataframe(display, use_container_width=True)

st.markdown('---')
st.markdown('⚠️ For educational purposes only.')
