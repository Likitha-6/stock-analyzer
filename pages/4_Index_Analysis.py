"""
Index Analysis Page - FIXED VERSION
====================================
Features:
- Live index charts (NIFTY 50, SENSEX, sector indices)
- EMA crossover signals
- RSI overbought/oversold detection
- 52-week high/low positioning
- Trading alerts
- Comprehensive error handling
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Index Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

# ────────────────────────────────────────────────────────────────────
# STYLING
# ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.0rem;
    font-weight: 800;
    color: #f0f4ff;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}

.page-sub {
    font-size: 0.78rem;
    color: #8aaac8;
    margin-bottom: 1.6rem;
    letter-spacing: 0.05em;
}

.section-label {
    font-size: 0.68rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #8aaac8;
    border-left: 3px solid #00c882;
    padding-left: 0.6rem;
    margin-bottom: 0.8rem;
    margin-top: 1.6rem;
}

.signal-card {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.signal-bullish {
    border-left: 4px solid #00c882;
}

.signal-bearish {
    border-left: 4px solid #ff4d6a;
}

.signal-neutral {
    border-left: 4px solid #8aaac8;
}

.signal-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.4rem;
}

.signal-detail {
    font-size: 0.8rem;
    color: #8aaac8;
    line-height: 1.5;
}

.stat-box {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    margin: 0.5rem 0;
}

.stat-label {
    font-size: 0.65rem;
    color: #8aaac8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
}

.stat-value {
    font-size: 1.3rem;
    font-weight: 700;
    color: #00c882;
}

.stat-subtext {
    font-size: 0.7rem;
    color: #00c882;
    margin-top: 0.2rem;
}

.alert-box {
    background: rgba(0, 200, 130, 0.1);
    border: 1px solid rgba(0, 200, 130, 0.3);
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}

.alert-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #00c882;
    margin-bottom: 0.4rem;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_index_data(symbol: str, period: str = '1y') -> Optional[pd.DataFrame]:
    """Fetch index historical data with error handling."""
    try:
        data = yf.download(symbol, period=period, progress=False)
        if data is None or len(data) == 0:
            logger.warning(f"No data returned for {symbol}")
            return None
        return data
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {str(e)}")
        return None


def calculate_ema(data: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Exponential Moving Average."""
    try:
        if data is None or len(data) == 0:
            return pd.Series([np.nan] * len(data)) if data is not None else pd.Series()
        return data.ewm(span=period, adjust=False).mean()
    except Exception as e:
        logger.error(f"Error calculating EMA: {str(e)}")
        return pd.Series([np.nan] * len(data))


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index with error handling."""
    try:
        if data is None or len(data) < period:
            return pd.Series([np.nan] * len(data)) if data is not None else pd.Series()
        
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Handle division by zero
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except Exception as e:
        logger.error(f"Error calculating RSI: {str(e)}")
        return pd.Series([np.nan] * len(data))


def detect_ema_crossover(data: pd.DataFrame, fast: int = 20, slow: int = 50) -> str:
    """
    Detect EMA crossover signals with error handling.
    Returns: 'BULLISH' (fast > slow), 'BEARISH' (fast < slow), or 'NEUTRAL'
    """
    try:
        if data is None or len(data) < 2:
            return 'NEUTRAL'
        
        data_copy = data.copy()
        data_copy['EMA_FAST'] = calculate_ema(data_copy['Close'], fast)
        data_copy['EMA_SLOW'] = calculate_ema(data_copy['Close'], slow)
        
        # Get last valid values, skip NaN
        ema_fast_clean = data_copy['EMA_FAST'].dropna()
        ema_slow_clean = data_copy['EMA_SLOW'].dropna()
        
        if len(ema_fast_clean) < 2 or len(ema_slow_clean) < 2:
            return 'NEUTRAL'
        
        last_fast = float(ema_fast_clean.iloc[-1])
        last_slow = float(ema_slow_clean.iloc[-1])
        prev_fast = float(ema_fast_clean.iloc[-2])
        prev_slow = float(ema_slow_clean.iloc[-2])
        
        # Crossover detection
        if prev_fast <= prev_slow and last_fast > last_slow:
            return 'BULLISH'
        elif prev_fast >= prev_slow and last_fast < last_slow:
            return 'BEARISH'
        elif last_fast > last_slow:
            return 'BULLISH'
        elif last_fast < last_slow:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    except Exception as e:
        logger.error(f"Error detecting EMA crossover: {str(e)}")
        return 'NEUTRAL'


def detect_rsi_signals(rsi: pd.Series) -> Tuple[str, float]:
    """
    Detect RSI overbought/oversold signals with comprehensive error handling.
    Returns: (signal, rsi_value)
    """
    try:
        # Handle None or empty series
        if rsi is None or len(rsi) == 0:
            return ('NEUTRAL', 50.0)
        
        # Get last valid RSI value, skip NaN
        rsi_clean = rsi.dropna()
        if len(rsi_clean) == 0:
            return ('NEUTRAL', 50.0)
        
        # Convert to Python float to avoid Pandas ambiguity errors
        last_rsi = float(rsi_clean.iloc[-1])
        
        # Validate RSI is in valid range (0-100)
        if not isinstance(last_rsi, (int, float)) or np.isnan(last_rsi):
            return ('NEUTRAL', 50.0)
        
        # Clamp to 0-100 range just in case
        last_rsi = max(0.0, min(100.0, last_rsi))
        
        # Determine signal
        if last_rsi > 70:
            return ('OVERBOUGHT', last_rsi)
        elif last_rsi < 30:
            return ('OVERSOLD', last_rsi)
        else:
            return ('NEUTRAL', last_rsi)
    except Exception as e:
        logger.error(f"Error detecting RSI signals: {str(e)}")
        return ('NEUTRAL', 50.0)


def calculate_52week_position(data: pd.DataFrame) -> Dict[str, float]:
    """Calculate 52-week high/low positioning with error handling."""
    try:
        if data is None or len(data) < 50:
            return {
                'current': 0.0,
                'high_52w': 0.0,
                'low_52w': 0.0,
                'position': 50.0
            }
        
        last_52weeks = data.tail(252)  # ~252 trading days in a year
        
        high_52w = float(last_52weeks['Close'].max())
        low_52w = float(last_52weeks['Close'].min())
        current = float(data['Close'].iloc[-1])
        
        # Safely calculate position
        if high_52w == low_52w:
            position = 50.0
        else:
            position = ((current - low_52w) / (high_52w - low_52w)) * 100
            position = max(0.0, min(100.0, position))  # Clamp to 0-100
        
        return {
            'current': current,
            'high_52w': high_52w,
            'low_52w': low_52w,
            'position': position
        }
    except Exception as e:
        logger.error(f"Error calculating 52-week position: {str(e)}")
        return {
            'current': 0.0,
            'high_52w': 0.0,
            'low_52w': 0.0,
            'position': 50.0
        }


# ────────────────────────────────────────────────────────────────────
# PAGE CONTENT
# ────────────────────────────────────────────────────────────────────

st.markdown('<h1 class="page-title">📊 Index Analysis</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-sub">Monitor major indices with technical signals, momentum indicators, and analysis.</p>', unsafe_allow_html=True)

# Index Selection
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

selected_index = st.selectbox(
    'Choose an index:',
    list(INDICES.keys()),
    label_visibility='collapsed'
)

symbol = INDICES[selected_index]

# Fetch data
st.markdown('<div class="section-label">Loading Chart Data...</div>', unsafe_allow_html=True)
data = fetch_index_data(symbol)

if data is None or len(data) == 0:
    st.error(f'❌ Could not fetch data for {selected_index}. Please try another index or check your internet connection.')
else:
    # ────────────────────────────────────────────────────────────────────
    # TECHNICAL ANALYSIS
    # ────────────────────────────────────────────────────────────────────
    
    st.markdown('<div class="section-label">📈 Technical Analysis</div>', unsafe_allow_html=True)
    
    try:
        # Calculate indicators
        data_calc = data.copy()
        rsi_val = calculate_rsi(data_calc['Close'])
        ema_signal = detect_ema_crossover(data_calc)
        rsi_signal, rsi_number = detect_rsi_signals(rsi_val)
        position_52w = calculate_52week_position(data_calc)
        
        # Verify we have valid data
        if position_52w['high_52w'] == 0:
            st.warning('⚠️ Insufficient data available. Please try another index.')
        else:
            # Create candlestick chart with EMAs
            try:
                fig = go.Figure()
                
                # Candlestick
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
                
                # EMA lines
                ema20 = calculate_ema(data['Close'], 20)
                ema50 = calculate_ema(data['Close'], 50)
                
                fig.add_trace(go.Scatter(
                    x=ema20.index,
                    y=ema20.values,
                    name='EMA 20',
                    line=dict(color='#00c882', width=1, dash='dot')
                ))
                
                fig.add_trace(go.Scatter(
                    x=ema50.index,
                    y=ema50.values,
                    name='EMA 50',
                    line=dict(color='#ffa500', width=1, dash='dot')
                ))
                
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
                st.error(f'⚠️ Error rendering chart: {str(e)}')
                logger.error(f"Chart rendering error: {str(e)}")
            
            # Signal Cards
            sig_col1, sig_col2, sig_col3 = st.columns(3)
            
            # EMA Signal
            with sig_col1:
                signal_class = 'signal-bullish' if ema_signal == 'BULLISH' else 'signal-bearish' if ema_signal == 'BEARISH' else 'signal-neutral'
                signal_color = '#00c882' if ema_signal == 'BULLISH' else '#ff4d6a' if ema_signal == 'BEARISH' else '#8aaac8'
                st.markdown(f'''<div class="signal-card {signal_class}">
                    <div class="signal-title">EMA Crossover</div>
                    <div style="font-size:1.2rem;font-weight:700;color:{signal_color};margin:0.5rem 0;">{ema_signal}</div>
                    <div class="signal-detail">EMA 20 {'above' if ema_signal == 'BULLISH' else 'below' if ema_signal == 'BEARISH' else 'near'} EMA 50</div>
                </div>''', unsafe_allow_html=True)
            
            # RSI Signal
            with sig_col2:
                rsi_color = '#ff4d6a' if rsi_signal == 'OVERBOUGHT' else '#00c882' if rsi_signal == 'OVERSOLD' else '#8aaac8'
                signal_class = 'signal-bearish' if rsi_signal == 'OVERBOUGHT' else 'signal-bullish' if rsi_signal == 'OVERSOLD' else 'signal-neutral'
                st.markdown(f'''<div class="signal-card {signal_class}">
                    <div class="signal-title">RSI Status</div>
                    <div style="font-size:1.2rem;font-weight:700;color:{rsi_color};margin:0.5rem 0;">{rsi_number:.0f}</div>
                    <div class="signal-detail">{rsi_signal}</div>
                </div>''', unsafe_allow_html=True)
            
            # 52-Week Position
            with sig_col3:
                pos = position_52w['position']
                pos_color = '#00c882' if pos > 70 else '#ff4d6a' if pos < 30 else '#ffa500'
                st.markdown(f'''<div class="signal-card">
                    <div class="signal-title">52-Week Position</div>
                    <div style="font-size:1.2rem;font-weight:700;color:{pos_color};margin:0.5rem 0;">{pos:.1f}%</div>
                    <div class="signal-detail">From low to high</div>
                </div>''', unsafe_allow_html=True)
            
            # ────────────────────────────────────────────────────────────────────
            # KEY STATISTICS
            # ────────────────────────────────────────────────────────────────────
            
            st.markdown('<div class="section-label">📊 Key Statistics</div>', unsafe_allow_html=True)
            
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
            change_pct = ((current_price - prev_price) / prev_price * 100) if prev_price != 0 else 0
            
            with stat_col1:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">Current Price</div>
                    <div class="stat-value">₹{current_price:,.0f}</div>
                    <div class="stat-subtext">{'↑' if change_pct >= 0 else '↓'} {abs(change_pct):.2f}%</div>
                </div>''', unsafe_allow_html=True)
            
            with stat_col2:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">52-Week High</div>
                    <div class="stat-value">₹{position_52w['high_52w']:,.0f}</div>
                </div>''', unsafe_allow_html=True)
            
            with stat_col3:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">52-Week Low</div>
                    <div class="stat-value">₹{position_52w['low_52w']:,.0f}</div>
                </div>''', unsafe_allow_html=True)
            
            with stat_col4:
                avg_volume = data['Volume'].tail(20).mean()
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">Avg Volume (20d)</div>
                    <div class="stat-value">{avg_volume/1e6:.1f}M</div>
                </div>''', unsafe_allow_html=True)
            
            # ────────────────────────────────────────────────────────────────────
            # ALERTS
            # ────────────────────────────────────────────────────────────────────
            
            st.markdown('<div class="section-label">⚠️ Trading Alerts</div>', unsafe_allow_html=True)
            
            alerts = []
            
            if ema_signal == 'BULLISH':
                alerts.append(('Bullish', f'EMA 20 is above EMA 50 - uptrend signal', '#00c882'))
            elif ema_signal == 'BEARISH':
                alerts.append(('Bearish', f'EMA 20 is below EMA 50 - downtrend signal', '#ff4d6a'))
            
            if rsi_signal == 'OVERBOUGHT':
                alerts.append(('Overbought', f'RSI is above 70 - consider profit booking', '#ff4d6a'))
            elif rsi_signal == 'OVERSOLD':
                alerts.append(('Oversold', f'RSI is below 30 - potential buying opportunity', '#00c882'))
            
            if position_52w['position'] > 90:
                alerts.append(('Resistance', 'Index near 52-week high - potential selling pressure', '#ff9800'))
            elif position_52w['position'] < 10:
                alerts.append(('Support', 'Index near 52-week low - potential support level', '#00c882'))
            
            if len(alerts) == 0:
                st.info('✅ No major alerts. Index showing neutral technical conditions.')
            else:
                for alert_type, message, color in alerts:
                    st.markdown(f'''<div style="background: rgba(255,255,255,0.05); border-left: 3px solid {color}; padding: 1rem; border-radius: 8px; margin: 0.5rem 0;">
                        <div style="font-weight: 700; color: {color}; margin-bottom: 0.3rem;">{alert_type}</div>
                        <div style="color: #8aaac8; font-size: 0.9rem;">{message}</div>
                    </div>''', unsafe_allow_html=True)
            
            # ────────────────────────────────────────────────────────────────────
            # DATA TABLE
            # ────────────────────────────────────────────────────────────────────
            
            st.markdown('<div class="section-label">📋 Recent Data</div>', unsafe_allow_html=True)
            
            try:
                display_data = data.tail(10).copy()
                display_data.index = display_data.index.strftime('%Y-%m-%d')
                display_data = display_data.round(2)
                
                st.dataframe(
                    display_data,
                    use_container_width=True,
                    column_config={
                        'Open': st.column_config.NumberColumn('Open', format='₹ %.0f'),
                        'High': st.column_config.NumberColumn('High', format='₹ %.0f'),
                        'Low': st.column_config.NumberColumn('Low', format='₹ %.0f'),
                        'Close': st.column_config.NumberColumn('Close', format='₹ %.0f'),
                        'Volume': st.column_config.NumberColumn('Volume', format='%d'),
                    }
                )
            except Exception as e:
                st.error(f'⚠️ Error displaying data table: {str(e)}')
                logger.error(f"Data table error: {str(e)}")
    
    except Exception as e:
        st.error(f'⚠️ Error calculating technical indicators: {str(e)}')
        logger.error(f"Technical analysis error: {str(e)}")

# ────────────────────────────────────────────────────────────────────
# DISCLAIMER
# ────────────────────────────────────────────────────────────────────

st.markdown('''
---
⚠️ **Disclaimer:** This analysis is for educational purposes only. Technical indicators are tools to aid decision-making, not guarantees of future price movement. Always conduct your own research and consult a financial advisor before making investment decisions.
''')
