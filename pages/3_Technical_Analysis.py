"""
Technical Analysis Page - COMPLETE WORKING VERSION
====================================================
Price chart with support/resistance, RSI, recommendations
No external dependencies on indicators.py or complex imports
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

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
st.markdown('<p class="page-sub">Analyze stocks with price charts, support/resistance, and technical indicators.</p>', unsafe_allow_html=True)

st.markdown('<div class="section-label">Search Stock</div>', unsafe_allow_html=True)

# Load stocks from CSV
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

# Filter stocks
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

# Fetch data
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

# ═══════════════════════════════════════════════════════════════
# PRICE CHART WITH SUPPORT & RESISTANCE
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-label">📊 Price Chart with Support & Resistance</div>', unsafe_allow_html=True)

try:
    # Get last 200 days
    chart_df = data.tail(200).copy()
    
    # Support and resistance
    high_52w = float(data['Close'].tail(252).max())
    low_52w = float(data['Close'].tail(252).min())
    current_price = float(data['Close'].iloc[-1])
    
    # Create chart
    fig = go.Figure()
    
    # Price line
    fig.add_trace(go.Scatter(
        x=chart_df.index,
        y=chart_df['Close'],
        name='Close Price',
        mode='lines',
        line=dict(color='#00c882', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(0, 200, 130, 0.1)'
    ))
    
    # Resistance
    fig.add_hline(y=high_52w, line_dash='dash', line_color='#ff4d6a', line_width=2,
                  annotation_text=f'R: ₹{high_52w:,.0f}', annotation_position='right')
    
    # Support
    fig.add_hline(y=low_52w, line_dash='dash', line_color='#00c882', line_width=2,
                  annotation_text=f'S: ₹{low_52w:,.0f}', annotation_position='right')
    
    # Current price
    fig.add_hline(y=current_price, line_dash='solid', line_color='#00D9FF', line_width=1,
                  annotation_text=f'C: ₹{current_price:,.0f}', annotation_position='right')
    
    fig.update_layout(
        title=f'{selected_stock} - Price with Support & Resistance',
        xaxis_title='Date', yaxis_title='Price (₹)',
        height=450, template='plotly_dark', hovermode='x unified',
        paper_bgcolor='rgba(6,12,26,1)', plot_bgcolor='rgba(11,21,37,1)',
        margin=dict(l=60, r=180, t=60, b=40),
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)', autorange=True),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(11,21,37,0.9)', bordercolor='rgba(255,255,255,0.1)', borderwidth=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
except Exception as e:
    st.error(f'Chart error: {str(e)}')

# ═══════════════════════════════════════════════════════════════
# RSI CHART
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-label">📊 RSI (14) Indicator</div>', unsafe_allow_html=True)

try:
    rsi_data = data['RSI'].tail(200)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=rsi_data.index, y=rsi_data.values, name='RSI', line=dict(color='#00D9FF', width=2)))
    fig.add_hline(y=70, line_dash='dash', line_color='#ff4d6a', line_width=1)
    fig.add_hline(y=30, line_dash='dash', line_color='#00c882', line_width=1)
    
    fig.update_layout(
        title='RSI(14) - Momentum Indicator', xaxis_title='Date', yaxis_title='RSI',
        height=300, template='plotly_dark', hovermode='x unified',
        paper_bgcolor='rgba(6,12,26,1)', plot_bgcolor='rgba(11,21,37,1)',
        margin=dict(l=60, r=60, t=40, b=40),
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='rgba(255,255,255,0.1)', range=[0, 100])
    )
    
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f'RSI chart error: {str(e)}')

# ═══════════════════════════════════════════════════════════════
# TECHNICAL ANALYSIS & RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="section-label">🎯 Technical Analysis & Recommendations</div>', unsafe_allow_html=True)

try:
    current = float(data['Close'].iloc[-1])
    prev = float(data['Close'].iloc[-2]) if len(data) > 1 else current
    change = current - prev
    
    sma20 = float(data['SMA20'].iloc[-1]) if len(data['SMA20'].dropna()) > 0 else 0
    sma50 = float(data['SMA50'].iloc[-1]) if len(data['SMA50'].dropna()) > 0 else 0
    ema20 = float(data['EMA20'].iloc[-1]) if len(data['EMA20'].dropna()) > 0 else 0
    ema50 = float(data['EMA50'].iloc[-1]) if len(data['EMA50'].dropna()) > 0 else 0
    rsi = float(data['RSI'].iloc[-1]) if len(data['RSI'].dropna()) > 0 else 50
    
    high_52w = float(data['Close'].tail(252).max())
    low_52w = float(data['Close'].tail(252).min())
    
    # Signals
    signals = []
    
    if sma20 > sma50:
        signals.append(('Bullish', 'SMA20 > SMA50 (Uptrend)', '#00c882'))
    else:
        signals.append(('Bearish', 'SMA20 < SMA50 (Downtrend)', '#ff4d6a'))
    
    if current > ema20 > ema50:
        signals.append(('Strong Bullish', 'Price > EMA20 > EMA50', '#00c882'))
    elif current < ema20 < ema50:
        signals.append(('Strong Bearish', 'Price < EMA20 < EMA50', '#ff4d6a'))
    
    if rsi > 70:
        signals.append(('Overbought', f'RSI {rsi:.0f} > 70', '#ff4d6a'))
    elif rsi < 30:
        signals.append(('Oversold', f'RSI {rsi:.0f} < 30', '#00c882'))
    elif rsi > 60:
        signals.append(('Strong Momentum', f'RSI {rsi:.0f} (Bullish)', '#00c882'))
    elif rsi < 40:
        signals.append(('Weak Momentum', f'RSI {rsi:.0f} (Bearish)', '#ff4d6a'))
    
    # Display signals
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('**📊 Signal Analysis:**')
        for signal_type, message, color in signals[:2]:
            st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-left:4px solid {color};padding:0.8rem;border-radius:6px;margin:0.5rem 0;"><div style="font-weight:700;color:{color};">{signal_type}</div><div style="color:#8aaac8;font-size:0.85rem;margin-top:0.2rem;">{message}</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('**⚡ More Signals:**')
        for signal_type, message, color in signals[2:]:
            st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-left:4px solid {color};padding:0.8rem;border-radius:6px;margin:0.5rem 0;"><div style="font-weight:700;color:{color};">{signal_type}</div><div style="color:#8aaac8;font-size:0.85rem;margin-top:0.2rem;">{message}</div></div>', unsafe_allow_html=True)
    
    # Recommendation
    bullish_count = sum(1 for s in signals if s[0] in ['Bullish', 'Strong Bullish', 'Oversold', 'Strong Momentum'])
    bearish_count = sum(1 for s in signals if s[0] in ['Bearish', 'Strong Bearish', 'Overbought', 'Weak Momentum'])
    
    if bullish_count > bearish_count:
        rec = 'BUY'; rec_color = '#00c882'; rec_reason = f'{bullish_count} bullish vs {bearish_count} bearish'
    elif bearish_count > bullish_count:
        rec = 'SELL'; rec_color = '#ff4d6a'; rec_reason = f'{bearish_count} bearish vs {bullish_count} bullish'
    else:
        rec = 'HOLD'; rec_color = '#ffa500'; rec_reason = 'Mixed signals'
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid {rec_color};border-radius:12px;padding:1.5rem;text-align:center;"><div style="font-size:0.75rem;color:#8aaac8;text-transform:uppercase;margin-bottom:0.5rem;">Recommendation</div><div style="font-size:2rem;font-weight:800;color:{rec_color};">{rec}</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid #8aaac8;border-radius:12px;padding:1.5rem;text-align:center;"><div style="font-size:0.75rem;color:#8aaac8;text-transform:uppercase;margin-bottom:0.5rem;">Entry</div><div style="font-size:1.5rem;font-weight:700;color:#00c882;">₹{current:,.2f}</div></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'<div style="background:rgba(255,255,255,0.08);border:2px solid #8aaac8;border-radius:12px;padding:1.5rem;text-align:center;"><div style="font-size:0.75rem;color:#8aaac8;text-transform:uppercase;margin-bottom:0.5rem;">52W Range</div><div style="font-size:0.9rem;color:#00c882;margin-bottom:0.3rem;">H: ₹{high_52w:,.0f}</div><div style="font-size:0.9rem;color:#ff4d6a;">L: ₹{low_52w:,.0f}</div></div>', unsafe_allow_html=True)
    
    st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-left:4px solid {rec_color};padding:1rem;border-radius:8px;margin:1rem 0;"><div style="color:#8aaac8;"><strong>Reason:</strong> {rec_reason}</div></div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f'Analysis error: {str(e)}')

st.markdown('---')
st.markdown('⚠️ For educational purposes only. Always consult a financial advisor.')
