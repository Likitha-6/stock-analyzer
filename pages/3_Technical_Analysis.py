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

st.markdown('<div class="section-label">📊 Candlestick Chart with Indicators</div>', unsafe_allow_html=True)

try:
    # Create subplots: 3 rows, 1 column
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        row_heights=[0.55, 0.225, 0.225],
        subplot_titles=('Price & Moving Averages', 'RSI (14)', 'MACD')
    )
    
    # Row 1: Candlestick
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price',
        increasing_line_color='#00c882',
        increasing_fillcolor='#00c882',
        decreasing_line_color='#ff4d6a',
        decreasing_fillcolor='#ff4d6a'
    ), row=1, col=1)
    
    # Row 1: SMA20
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['SMA20'],
        name='SMA20',
        line=dict(color='#FFD700', width=1.5, dash='dash'),
        mode='lines'
    ), row=1, col=1)
    
    # Row 1: SMA50
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['SMA50'],
        name='SMA50',
        line=dict(color='#FF6B9D', width=1.5, dash='dash'),
        mode='lines'
    ), row=1, col=1)
    
    # Row 2: RSI
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['RSI'],
        name='RSI(14)',
        line=dict(color='#00D9FF', width=2),
        mode='lines'
    ), row=2, col=1)
    
    # RSI levels
    fig.add_hline(y=70, line_dash='dash', line_color='rgba(255,77,106,0.5)', row=2, col=1)
    fig.add_hline(y=30, line_dash='dash', line_color='rgba(0,200,130,0.5)', row=2, col=1)
    
    # Row 3: MACD
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['MACD'],
        name='MACD',
        line=dict(color='#00D9FF', width=2),
        mode='lines'
    ), row=3, col=1)
    
    # Row 3: Signal Line
    fig.add_trace(go.Scatter(
        x=data.index,
        y=data['Signal'],
        name='Signal',
        line=dict(color='#FF6B9D', width=2),
        mode='lines'
    ), row=3, col=1)
    
    fig.update_xaxes(title_text='Date', row=3, col=1)
    fig.update_yaxes(title_text='Price (₹)', row=1, col=1)
    fig.update_yaxes(title_text='RSI', row=2, col=1)
    fig.update_yaxes(title_text='MACD', row=3, col=1)
    
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    fig.update_layout(
        title=f'<b>{selected_stock}</b> - Technical Analysis',
        height=900,
        template='plotly_dark',
        hovermode='x unified',
        paper_bgcolor='rgba(6,12,26,1)',
        plot_bgcolor='rgba(11,21,37,1)',
        margin=dict(l=60, r=60, t=80, b=60),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f'Chart error: {str(e)}')

# SUMMARY
st.markdown('<div class="section-label">📊 Summary Metrics</div>', unsafe_allow_html=True)

try:
    current_price = float(data['Close'].iloc[-1])
    prev_price = float(data['Close'].iloc[-2]) if len(data) > 1 else current_price
    change = current_price - prev_price
    change_pct = (change / prev_price * 100) if prev_price != 0 else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric('Current Price', f'₹{current_price:,.2f}', f'{change:+.2f} ({change_pct:+.2f}%)')
    
    with col2:
        high_52w = data['Close'].tail(252).max()
        st.metric('52W High', f'₹{high_52w:,.2f}')
    
    with col3:
        low_52w = data['Close'].tail(252).min()
        st.metric('52W Low', f'₹{low_52w:,.2f}')
    
    with col4:
        sma20 = data['SMA20'].iloc[-1]
        st.metric('SMA20', f'₹{sma20:,.2f}')
    
    with col5:
        rsi = data['RSI'].iloc[-1]
        st.metric('RSI(14)', f'{rsi:.2f}')
except Exception as e:
    st.warning(f'Summary metrics error: {str(e)}')

# RECENT DATA
st.markdown('<div class="section-label">📋 Recent Data (Last 20 Days)</div>', unsafe_allow_html=True)

try:
    display_data = data[['Open', 'High', 'Low', 'Close', 'Volume', 'SMA20', 'SMA50', 'RSI', 'MACD']].tail(20).copy()
    display_data.index = display_data.index.strftime('%Y-%m-%d')
    display_data = display_data.round(2)
    st.dataframe(display_data, use_container_width=True)
except Exception as e:
    st.warning(f'Data table error: {str(e)}')

st.markdown('---')
st.markdown('⚠️ For educational purposes only. Always consult a financial advisor.')
