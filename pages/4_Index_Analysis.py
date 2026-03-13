"""
Index Analysis Page - ULTIMATE FIXED VERSION
==============================================
All Pandas Series comparison errors eliminated
Complete error handling and validation
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import logging
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

.signal-bullish { border-left: 4px solid #00c882; }
.signal-bearish { border-left: 4px solid #ff4d6a; }
.signal-neutral { border-left: 4px solid #8aaac8; }

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
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────
# SAFE HELPER FUNCTIONS
# ────────────────────────────────────────────────────────────────────

def safe_float(value) -> float:
    """Safely convert value to float, return None if invalid."""
    try:
        if pd.isna(value):
            return None
        f = float(value)
        if np.isnan(f) or np.isinf(f):
            return None
        return f
    except:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_index_data(symbol: str, period: str = '1y') -> Optional[pd.DataFrame]:
    """Fetch index historical data."""
    try:
        data = yf.download(symbol, period=period, progress=False)
        if data is None or len(data) == 0:
            return None
        return data
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {str(e)}")
        return None


def calculate_ema(data: pd.Series, period: int = 20) -> pd.Series:
    """Calculate EMA safely."""
    try:
        if data is None or len(data) < period:
            return pd.Series(dtype=float)
        return data.ewm(span=period, adjust=False).mean()
    except:
        return pd.Series(dtype=float)


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI safely."""
    try:
        if data is None or len(data) < period:
            return pd.Series(dtype=float)
        
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        return pd.Series(dtype=float)


def get_ema_signal(data: pd.DataFrame) -> Tuple[str, float, float]:
    """Get EMA crossover signal safely."""
    try:
        if data is None or len(data) < 50:
            return ('NEUTRAL', 0, 0)
        
        ema20 = calculate_ema(data['Close'], 20)
        ema50 = calculate_ema(data['Close'], 50)
        
        if len(ema20) == 0 or len(ema50) == 0:
            return ('NEUTRAL', 0, 0)
        
        # Get last values
        last20 = ema20.dropna()
        last50 = ema50.dropna()
        
        if len(last20) == 0 or len(last50) == 0:
            return ('NEUTRAL', 0, 0)
        
        val20 = safe_float(last20.iloc[-1])
        val50 = safe_float(last50.iloc[-1])
        
        if val20 is None or val50 is None:
            return ('NEUTRAL', 0, 0)
        
        if val20 > val50:
            signal = 'BULLISH'
        elif val20 < val50:
            signal = 'BEARISH'
        else:
            signal = 'NEUTRAL'
        
        return (signal, val20, val50)
    except Exception as e:
        logger.error(f"EMA error: {e}")
        return ('NEUTRAL', 0, 0)


def get_rsi_signal(data: pd.Series) -> Tuple[str, float]:
    """Get RSI signal safely."""
    try:
        if data is None or len(data) == 0:
            return ('NEUTRAL', 50.0)
        
        rsi_clean = data.dropna()
        if len(rsi_clean) == 0:
            return ('NEUTRAL', 50.0)
        
        val = safe_float(rsi_clean.iloc[-1])
        if val is None:
            return ('NEUTRAL', 50.0)
        
        # Clamp to 0-100
        val = max(0, min(100, val))
        
        if val > 70:
            signal = 'OVERBOUGHT'
        elif val < 30:
            signal = 'OVERSOLD'
        else:
            signal = 'NEUTRAL'
        
        return (signal, val)
    except Exception as e:
        logger.error(f"RSI error: {e}")
        return ('NEUTRAL', 50.0)


def get_52week_position(data: pd.DataFrame) -> Dict:
    """Get 52-week position safely."""
    try:
        if data is None or len(data) < 50:
            return {'current': 0, 'high': 0, 'low': 0, 'position': 50}
        
        last_52w = data.tail(252)
        
        high = safe_float(last_52w['Close'].max())
        low = safe_float(last_52w['Close'].min())
        current = safe_float(data['Close'].iloc[-1])
        
        if None in [high, low, current]:
            return {'current': 0, 'high': 0, 'low': 0, 'position': 50}
        
        if high == low:
            position = 50
        else:
            position = ((current - low) / (high - low)) * 100
            position = max(0, min(100, position))
        
        return {
            'current': current,
            'high': high,
            'low': low,
            'position': position
        }
    except Exception as e:
        logger.error(f"52-week error: {e}")
        return {'current': 0, 'high': 0, 'low': 0, 'position': 50}


# ────────────────────────────────────────────────────────────────────
# PAGE
# ────────────────────────────────────────────────────────────────────

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
data = fetch_index_data(symbol)

if data is None or len(data) == 0:
    st.error(f'❌ Could not fetch data for {selected_index}. Please try another index.')
else:
    # Calculate everything safely
    rsi_series = calculate_rsi(data['Close'])
    ema_signal, ema20_val, ema50_val = get_ema_signal(data)
    rsi_signal, rsi_val = get_rsi_signal(rsi_series)
    position_52w = get_52week_position(data)
    
    # Check if we have valid data
    if position_52w['high'] == 0:
        st.warning('⚠️ Insufficient data. Please try another index.')
    else:
        st.markdown('<div class="section-label">📈 Price Chart</div>', unsafe_allow_html=True)
        
        try:
            # Build chart
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
            
            # Add EMAs
            ema20 = calculate_ema(data['Close'], 20)
            ema50 = calculate_ema(data['Close'], 50)
            
            fig.add_trace(go.Scatter(x=data.index, y=ema20, name='EMA 20', 
                                    line=dict(color='#00c882', width=1, dash='dot')))
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
            st.error(f'⚠️ Error rendering chart: {str(e)}')
        
        # Signal cards
        st.markdown('<div class="section-label">📊 Technical Signals</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            color = '#00c882' if ema_signal == 'BULLISH' else '#ff4d6a' if ema_signal == 'BEARISH' else '#8aaac8'
            st.markdown(f'''<div class="signal-card">
                <div class="signal-title">EMA Signal</div>
                <div style="font-size:1.2rem;font-weight:700;color:{color};">{ema_signal}</div>
                <div class="signal-detail">EMA 20 {'above' if ema_signal == 'BULLISH' else 'below' if ema_signal == 'BEARISH' else 'near'} EMA 50</div>
            </div>''', unsafe_allow_html=True)
        
        with col2:
            color = '#ff4d6a' if rsi_signal == 'OVERBOUGHT' else '#00c882' if rsi_signal == 'OVERSOLD' else '#8aaac8'
            st.markdown(f'''<div class="signal-card">
                <div class="signal-title">RSI Status</div>
                <div style="font-size:1.2rem;font-weight:700;color:{color};">{rsi_val:.0f}</div>
                <div class="signal-detail">{rsi_signal}</div>
            </div>''', unsafe_allow_html=True)
        
        with col3:
            pos = position_52w['position']
            color = '#00c882' if pos > 70 else '#ff4d6a' if pos < 30 else '#ffa500'
            st.markdown(f'''<div class="signal-card">
                <div class="signal-title">52-Week Position</div>
                <div style="font-size:1.2rem;font-weight:700;color:{color};">{pos:.1f}%</div>
                <div class="signal-detail">From low to high</div>
            </div>''', unsafe_allow_html=True)
        
        # Statistics
        st.markdown('<div class="section-label">📊 Key Statistics</div>', unsafe_allow_html=True)
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        current = safe_float(data['Close'].iloc[-1]) or 0
        prev = safe_float(data['Close'].iloc[-2]) if len(data) > 1 else current
        change_pct = ((current - prev) / prev * 100) if prev != 0 else 0
        
        with stat_col1:
            st.markdown(f'''<div class="stat-box">
                <div class="stat-label">Current Price</div>
                <div class="stat-value">₹{current:,.0f}</div>
                <div class="stat-subtext">{'↑' if change_pct >= 0 else '↓'} {abs(change_pct):.2f}%</div>
            </div>''', unsafe_allow_html=True)
        
        with stat_col2:
            st.markdown(f'''<div class="stat-box">
                <div class="stat-label">52-Week High</div>
                <div class="stat-value">₹{position_52w['high']:,.0f}</div>
            </div>''', unsafe_allow_html=True)
        
        with stat_col3:
            st.markdown(f'''<div class="stat-box">
                <div class="stat-label">52-Week Low</div>
                <div class="stat-value">₹{position_52w['low']:,.0f}</div>
            </div>''', unsafe_allow_html=True)
        
        with stat_col4:
            avg_vol = data['Volume'].tail(20).mean() if len(data) >= 20 else 0
            st.markdown(f'''<div class="stat-box">
                <div class="stat-label">Avg Volume (20d)</div>
                <div class="stat-value">{avg_vol/1e6:.1f}M</div>
            </div>''', unsafe_allow_html=True)
        
        # Alerts
        st.markdown('<div class="section-label">⚠️ Alerts</div>', unsafe_allow_html=True)
        
        alerts = []
        if ema_signal == 'BULLISH':
            alerts.append(('Bullish', 'EMA 20 above EMA 50 - uptrend', '#00c882'))
        elif ema_signal == 'BEARISH':
            alerts.append(('Bearish', 'EMA 20 below EMA 50 - downtrend', '#ff4d6a'))
        
        if rsi_signal == 'OVERBOUGHT':
            alerts.append(('Overbought', 'RSI > 70 - consider profit booking', '#ff4d6a'))
        elif rsi_signal == 'OVERSOLD':
            alerts.append(('Oversold', 'RSI < 30 - potential buying', '#00c882'))
        
        if position_52w['position'] > 90:
            alerts.append(('High', 'Near 52-week high', '#ff9800'))
        elif position_52w['position'] < 10:
            alerts.append(('Low', 'Near 52-week low', '#00c882'))
        
        if alerts:
            for alert_type, msg, color in alerts:
                st.markdown(f'<div style="background:rgba(255,255,255,0.05);border-left:3px solid {color};padding:1rem;border-radius:8px;margin:0.5rem 0;"><div style="font-weight:700;color:{color};">{alert_type}</div><div style="color:#8aaac8;font-size:0.9rem;">{msg}</div></div>', unsafe_allow_html=True)
        else:
            st.info('✅ No alerts. Neutral conditions.')
        
        # Data table
        st.markdown('<div class="section-label">📋 Recent Data</div>', unsafe_allow_html=True)
        
        try:
            display_data = data.tail(10).copy()
            display_data.index = display_data.index.strftime('%Y-%m-%d')
            st.dataframe(display_data, use_container_width=True)
        except:
            st.info('Could not display data table.')

st.markdown('---')
st.markdown('⚠️ **Educational purposes only.** Consult a financial advisor before trading.')
