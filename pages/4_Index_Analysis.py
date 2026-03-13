"""
Index Analysis Page - ROBUST VERSION
====================================
Handles all data edge cases and validation issues
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
.signal-bullish { border-left: 4px solid #00c882; }
.signal-bearish { border-left: 4px solid #ff4d6a; }
.signal-neutral { border-left: 4px solid #8aaac8; }
.signal-title { font-size: 0.9rem; font-weight: 700; color: #ffffff; margin-bottom: 0.4rem; }
.signal-detail { font-size: 0.8rem; color: #8aaac8; line-height: 1.5; }
.stat-box { background: #0b1525; border: 1px solid rgba(255,255,255,0.09); border-radius: 8px; padding: 1rem; text-align: center; margin: 0.5rem 0; }
.stat-label { font-size: 0.65rem; color: #8aaac8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem; }
.stat-value { font-size: 1.3rem; font-weight: 700; color: #00c882; }
.stat-subtext { font-size: 0.7rem; color: #00c882; margin-top: 0.2rem; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ────────────────────────────────────────────────────────────────────

def safe_to_float(value):
    """Safely convert to float."""
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
    """Fetch index data with extensive validation."""
    try:
        data = yf.download(symbol, period=period, progress=False, interval='1d')
        
        # Check if data is valid
        if data is None:
            return None
        if isinstance(data, pd.Series):
            data = data.to_frame()
        if len(data) == 0:
            return None
        
        # Validate required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in data.columns for col in required):
            return None
        
        # Check for valid close prices
        valid_closes = data['Close'].dropna()
        if len(valid_closes) < 50:
            return None
        
        return data
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {str(e)}")
        return None


def calculate_ema(data: pd.Series, period: int = 20) -> pd.Series:
    """Calculate EMA."""
    try:
        if data is None or len(data) < period:
            return pd.Series([np.nan] * len(data)) if data is not None else pd.Series()
        result = data.ewm(span=period, adjust=False).mean()
        return result
    except:
        return pd.Series([np.nan] * len(data)) if data is not None else pd.Series()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI."""
    try:
        if data is None or len(data) < period:
            return pd.Series([np.nan] * len(data)) if data is not None else pd.Series()
        
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except:
        return pd.Series([np.nan] * len(data)) if data is not None else pd.Series()


def get_last_value(series: pd.Series) -> Optional[float]:
    """Get last valid value from series."""
    try:
        if series is None or len(series) == 0:
            return None
        clean = series.dropna()
        if len(clean) == 0:
            return None
        return safe_to_float(clean.iloc[-1])
    except:
        return None


def get_ema_signal(data: pd.DataFrame) -> Tuple[str, Optional[float], Optional[float]]:
    """Get EMA crossover signal."""
    try:
        if data is None or len(data) < 50:
            return ('NEUTRAL', None, None)
        
        ema20 = calculate_ema(data['Close'], 20)
        ema50 = calculate_ema(data['Close'], 50)
        
        val20 = get_last_value(ema20)
        val50 = get_last_value(ema50)
        
        if val20 is None or val50 is None:
            return ('NEUTRAL', val20, val50)
        
        if val20 > val50:
            return ('BULLISH', val20, val50)
        elif val20 < val50:
            return ('BEARISH', val20, val50)
        else:
            return ('NEUTRAL', val20, val50)
    except Exception as e:
        logger.error(f"EMA error: {e}")
        return ('NEUTRAL', None, None)


def get_rsi_signal(data: pd.Series) -> Tuple[str, Optional[float]]:
    """Get RSI signal."""
    try:
        if data is None or len(data) == 0:
            return ('NEUTRAL', None)
        
        val = get_last_value(data)
        if val is None:
            return ('NEUTRAL', None)
        
        # Clamp to 0-100
        val = max(0.0, min(100.0, val))
        
        if val > 70:
            return ('OVERBOUGHT', val)
        elif val < 30:
            return ('OVERSOLD', val)
        else:
            return ('NEUTRAL', val)
    except Exception as e:
        logger.error(f"RSI error: {e}")
        return ('NEUTRAL', None)


def get_52week_stats(data: pd.DataFrame) -> Dict:
    """Get 52-week stats."""
    try:
        if data is None or len(data) < 50:
            return {
                'current': None,
                'high': None,
                'low': None,
                'position': None
            }
        
        last_52w = data.tail(252)
        
        current = safe_to_float(data['Close'].iloc[-1])
        high = safe_to_float(last_52w['Close'].max())
        low = safe_to_float(last_52w['Close'].min())
        
        if any(x is None for x in [current, high, low]):
            return {
                'current': current,
                'high': high,
                'low': low,
                'position': None
            }
        
        if high == low:
            position = 50.0
        else:
            position = ((current - low) / (high - low)) * 100
            position = max(0.0, min(100.0, position))
        
        return {
            'current': current,
            'high': high,
            'low': low,
            'position': position
        }
    except Exception as e:
        logger.error(f"52-week error: {e}")
        return {
            'current': None,
            'high': None,
            'low': None,
            'position': None
        }


# ────────────────────────────────────────────────────────────────────
# PAGE CONTENT
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

if data is None or len(data) < 50:
    st.error(f'❌ Could not fetch sufficient data for {selected_index}. Please try another index.')
else:
    # Calculate all indicators
    rsi_series = calculate_rsi(data['Close'])
    ema_signal, ema20_val, ema50_val = get_ema_signal(data)
    rsi_signal, rsi_val = get_rsi_signal(rsi_series)
    stats_52w = get_52week_stats(data)
    
    # Validate we have some data
    has_valid_data = any([
        ema_signal != 'NEUTRAL',
        rsi_val is not None,
        stats_52w['position'] is not None
    ])
    
    if not has_valid_data:
        st.warning('⚠️ Could not calculate technical indicators. Please try another index.')
    else:
        # Price chart
        st.markdown('<div class="section-label">📈 Price Chart</div>', unsafe_allow_html=True)
        
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
            
            # EMAs
            ema20 = calculate_ema(data['Close'], 20)
            ema50 = calculate_ema(data['Close'], 50)
            
            fig.add_trace(go.Scatter(
                x=data.index, y=ema20, name='EMA 20',
                line=dict(color='#00c882', width=1, dash='dot')
            ))
            fig.add_trace(go.Scatter(
                x=data.index, y=ema50, name='EMA 50',
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
            st.error(f'Chart error: {str(e)}')
        
        # Signals
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
            rsi_display = f'{rsi_val:.0f}' if rsi_val is not None else 'N/A'
            color = '#ff4d6a' if rsi_signal == 'OVERBOUGHT' else '#00c882' if rsi_signal == 'OVERSOLD' else '#8aaac8'
            st.markdown(f'''<div class="signal-card">
                <div class="signal-title">RSI Status</div>
                <div style="font-size:1.2rem;font-weight:700;color:{color};">{rsi_display}</div>
                <div class="signal-detail">{rsi_signal}</div>
            </div>''', unsafe_allow_html=True)
        
        with col3:
            if stats_52w['position'] is not None:
                pos = stats_52w['position']
                color = '#00c882' if pos > 70 else '#ff4d6a' if pos < 30 else '#ffa500'
                st.markdown(f'''<div class="signal-card">
                    <div class="signal-title">52-Week Position</div>
                    <div style="font-size:1.2rem;font-weight:700;color:{color};">{pos:.1f}%</div>
                    <div class="signal-detail">From low to high</div>
                </div>''', unsafe_allow_html=True)
            else:
                st.markdown(f'''<div class="signal-card signal-neutral">
                    <div class="signal-title">52-Week Position</div>
                    <div style="font-size:1.2rem;font-weight:700;color:#8aaac8;">N/A</div>
                </div>''', unsafe_allow_html=True)
        
        # Statistics
        st.markdown('<div class="section-label">📊 Key Statistics</div>', unsafe_allow_html=True)
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        current = safe_to_float(data['Close'].iloc[-1])
        prev = safe_to_float(data['Close'].iloc[-2]) if len(data) > 1 else None
        
        change_pct = 0
        if current is not None and prev is not None and prev != 0:
            change_pct = ((current - prev) / prev * 100)
        
        with stat_col1:
            if current is not None:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">Current Price</div>
                    <div class="stat-value">₹{current:,.0f}</div>
                    <div class="stat-subtext">{'↑' if change_pct >= 0 else '↓'} {abs(change_pct):.2f}%</div>
                </div>''', unsafe_allow_html=True)
            else:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">Current Price</div>
                    <div class="stat-value">N/A</div>
                </div>''', unsafe_allow_html=True)
        
        with stat_col2:
            if stats_52w['high'] is not None:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">52-Week High</div>
                    <div class="stat-value">₹{stats_52w['high']:,.0f}</div>
                </div>''', unsafe_allow_html=True)
            else:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">52-Week High</div>
                    <div class="stat-value">N/A</div>
                </div>''', unsafe_allow_html=True)
        
        with stat_col3:
            if stats_52w['low'] is not None:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">52-Week Low</div>
                    <div class="stat-value">₹{stats_52w['low']:,.0f}</div>
                </div>''', unsafe_allow_html=True)
            else:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">52-Week Low</div>
                    <div class="stat-value">N/A</div>
                </div>''', unsafe_allow_html=True)
        
        with stat_col4:
            try:
                avg_vol = data['Volume'].tail(20).mean()
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">Avg Volume (20d)</div>
                    <div class="stat-value">{avg_vol/1e6:.1f}M</div>
                </div>''', unsafe_allow_html=True)
            except:
                st.markdown(f'''<div class="stat-box">
                    <div class="stat-label">Avg Volume (20d)</div>
                    <div class="stat-value">N/A</div>
                </div>''', unsafe_allow_html=True)
        
        # Alerts
        st.markdown('<div class="section-label">⚠️ Trading Alerts</div>', unsafe_allow_html=True)
        
        alerts = []
        
        if ema_signal == 'BULLISH':
            alerts.append(('Bullish', 'EMA 20 above EMA 50 - uptrend', '#00c882'))
        elif ema_signal == 'BEARISH':
            alerts.append(('Bearish', 'EMA 20 below EMA 50 - downtrend', '#ff4d6a'))
        
        if rsi_signal == 'OVERBOUGHT':
            alerts.append(('Overbought', 'RSI > 70 - consider profit booking', '#ff4d6a'))
        elif rsi_signal == 'OVERSOLD':
            alerts.append(('Oversold', 'RSI < 30 - potential buying', '#00c882'))
        
        if stats_52w['position'] is not None:
            if stats_52w['position'] > 90:
                alerts.append(('High', 'Near 52-week high', '#ff9800'))
            elif stats_52w['position'] < 10:
                alerts.append(('Low', 'Near 52-week low', '#00c882'))
        
        if alerts:
            for alert_type, msg, color in alerts:
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.05);border-left:3px solid {color};padding:1rem;border-radius:8px;margin:0.5rem 0;">'
                    f'<div style="font-weight:700;color:{color};">{alert_type}</div>'
                    f'<div style="color:#8aaac8;font-size:0.9rem;">{msg}</div></div>',
                    unsafe_allow_html=True
                )
        else:
            st.info('✅ No major alerts. Market in neutral conditions.')
        
        # Data table
        st.markdown('<div class="section-label">📋 Recent Data</div>', unsafe_allow_html=True)
        
        try:
            display_data = data.tail(10).copy()
            display_data.index = display_data.index.strftime('%Y-%m-%d')
            st.dataframe(display_data, use_container_width=True)
        except:
            pass

st.markdown('---')
st.markdown('⚠️ **Educational purposes only.** Always consult a financial advisor before trading.')
