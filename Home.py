"""
Improved Indian Stock Analyzer - Home Page
============================================
Enhanced with:
- Better error handling & logging
- Improved caching strategy
- Loading states for better UX
- Retry logic for API failures
- Type hints for code quality
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import threading
import subprocess
import logging
from datetime import date, datetime, timedelta
from typing import Dict, Tuple, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from common.sql import load_master
from common.data import load_name_lookup

# ────────────────────────────────────────────────────────────────────
# LOGGING SETUP
# ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Indian Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ────────────────────────────────────────────────────────────────────
# STYLING
# ────────────────────────────────────────────────────────────────────
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;0,800&display=swap');

*, html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; }

/* ---- Hero ---- */
.hero {
    background: linear-gradient(135deg, #060c1a 0%, #0b1a35 55%, #060e1f 100%);
    border: 1px solid rgba(0,200,130,0.22);
    border-radius: 18px;
    padding: 3.5rem 3.5rem 3rem;
    margin-bottom: 2rem;
    position: relative; overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute; top: -100px; right: -80px;
    width: 450px; height: 450px;
    background: radial-gradient(circle, rgba(0,200,130,0.09) 0%, transparent 65%);
    pointer-events: none;
}
.hero-tag {
    font-size: 0.72rem; font-weight: 600;
    color: #00c882; letter-spacing: 0.18em;
    text-transform: uppercase; margin-bottom: 1.1rem;
}
.hero-title {
    font-size: 2.8rem; font-weight: 800;
    color: #ffffff; line-height: 1.1;
    letter-spacing: -0.03em; margin-bottom: 1rem;
}
.hero-title .green { color: #00c882; }
.hero-sub {
    font-size: 0.95rem; font-weight: 400;
    color: #a0b8d0; line-height: 1.75;
    max-width: 500px; margin-bottom: 1.8rem;
}
.pill-row { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.pill {
    background: rgba(0,200,130,0.1);
    border: 1px solid rgba(0,200,130,0.28);
    border-radius: 6px; padding: 0.28rem 0.75rem;
    font-size: 0.68rem; font-weight: 600;
    color: #00c882; letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* ---- Section label ---- */
.sec-label {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.16em; text-transform: uppercase;
    color: #ffffff;
    border-left: 3px solid #00c882;
    padding-left: 0.65rem;
    margin-bottom: 1rem; margin-top: 0.5rem;
}

/* ---- Index cards ---- */
.idx-card {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px; padding: 1.1rem 0.9rem;
    text-align: center; transition: border-color 0.2s;
}
.idx-card:hover { border-color: rgba(0,200,130,0.35); }
.idx-name {
    font-size: 0.63rem; font-weight: 600;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: #8aaac8; margin-bottom: 0.45rem;
}
.idx-price {
    font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-bottom: 0.25rem;
}
.idx-up   { font-size: 0.8rem; font-weight: 600; color: #00c882; }
.idx-down { font-size: 0.8rem; font-weight: 600; color: #ff4d6a; }
.idx-stale { opacity: 0.6; }

/* ---- Stat cards ---- */
.stat-card {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px; padding: 1.6rem 1.8rem;
    position: relative; overflow: hidden; transition: border-color 0.2s;
}
.stat-card:hover { border-color: rgba(0,200,130,0.35); }
.stat-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #00c882, transparent);
}
.stat-label {
    font-size: 0.68rem; font-weight: 600;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #8aaac8; margin-bottom: 0.6rem;
}
.stat-num {
    font-size: 2.2rem; font-weight: 800;
    color: #ffffff; line-height: 1; margin-bottom: 0.4rem;
}
.stat-hint { font-size: 0.8rem; font-weight: 500; color: #00c882; }

/* ---- Feature grid ---- */
.feat-card {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px; padding: 1.4rem 1.5rem;
    height: 100%; transition: all 0.2s;
}
.feat-card:hover { border-color: rgba(0,200,130,0.35); background: #0e1c38; }
.feat-num {
    font-size: 0.62rem; font-weight: 700;
    color: #00c882; letter-spacing: 0.12em;
    margin-bottom: 0.6rem;
}
.feat-title {
    font-size: 0.95rem; font-weight: 700;
    color: #ffffff; margin-bottom: 0.5rem;
}
.feat-desc {
    font-size: 0.82rem; font-weight: 400;
    color: #8aaac8; line-height: 1.6;
}

/* ---- Nav cards ---- */
.nav-card {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px; padding: 1.6rem 1.8rem;
    margin-bottom: 1rem; position: relative; transition: all 0.2s;
}
.nav-card:hover { border-color: rgba(0,200,130,0.4); background: #0e1c38; transform: translateY(-2px); }
.nav-title { font-size: 1rem; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem; }
.nav-desc  { font-size: 0.83rem; font-weight: 400; color: #8aaac8; line-height: 1.6; }
.nav-arrow { position: absolute; top: 1.5rem; right: 1.5rem; color: #00c882; font-size: 1rem; }

/* ---- Buttons ---- */
div[data-testid="stButton"] > button {
    background: transparent;
    border: 1px solid rgba(0,200,130,0.35);
    border-radius: 8px; color: #00c882;
    font-size: 0.75rem; font-weight: 600;
    letter-spacing: 0.05em;
    padding: 0.45rem 1rem; margin-top: 0.7rem;
    transition: all 0.2s; width: 100%;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(0,200,130,0.13);
    border-color: #00c882;
}

/* ---- Mover pill ---- */
.mover {
    background: #0b1525;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 10px; padding: 0.8rem 1rem;
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.5rem;
}
.mover-sym  { font-size: 0.82rem; font-weight: 700; color: #ffffff; }
.mover-name { font-size: 0.7rem;  font-weight: 400; color: #8aaac8; margin-top: 1px; }
.mover-up   { font-size: 0.82rem; font-weight: 700; color: #00c882; }
.mover-dn   { font-size: 0.82rem; font-weight: 700; color: #ff4d6a; }

/* ---- Footer ---- */
.footer {
    font-size: 0.68rem; font-weight: 400;
    color: #3a5070;
    display: flex; justify-content: space-between;
}

/* ---- Data freshness badge ---- */
.freshness-badge {
    font-size: 0.65rem; color: #8aaac8;
    padding: 0.3rem 0.6rem; background: rgba(0,200,130,0.08);
    border-radius: 4px; margin-top: 0.3rem;
}
</style>
''', unsafe_allow_html=True)

# ────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_index_data(symbol: str, retries: int = 3) -> Optional[Dict]:
    """
    Fetch index price data with retry logic.
    Returns: {price, change_pct, prev_price} or None on failure
    """
    for attempt in range(retries):
        try:
            hist = yf.Ticker(symbol).history(period='2d', interval='1d')
            if len(hist) >= 2:
                price = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2]
                chg = (price - prev) / prev * 100
                return {
                    'price': price,
                    'change_pct': chg,
                    'prev_price': prev,
                    'timestamp': datetime.now()
                }
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for {symbol}: {str(e)}")
            if attempt < retries - 1:
                import time
                time.sleep(1)  # Brief pause before retry
    
    logger.error(f"Failed to fetch data for {symbol} after {retries} attempts")
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_multiple_indices(symbols: List[str]) -> Dict[str, Optional[Dict]]:
    """
    Fetch multiple indices in parallel for better performance.
    """
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(get_index_data, sym): sym for sym in symbols}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                results[symbol] = future.result()
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {str(e)}")
                results[symbol] = None
    return results


def format_index_card(label: str, data: Optional[Dict]) -> str:
    """
    Generate HTML for index card with proper formatting.
    """
    if data is None:
        return f'''<div class="idx-card">
            <div class="idx-name">{label}</div>
            <div class="idx-price">--</div>
            <div style="font-size:0.7rem;color:#ff4d6a;margin-top:0.3rem;">Unable to load</div>
        </div>'''
    
    price = data['price']
    chg = data['change_pct']
    arrow = '▲' if chg >= 0 else '▼'
    cls = 'idx-up' if chg >= 0 else 'idx-down'
    
    # Check if data is stale (older than 5 hours)
    age = datetime.now() - data['timestamp']
    stale_class = ' idx-stale' if age > timedelta(hours=5) else ''
    
    html = f'''<div class="idx-card{stale_class}">
        <div class="idx-name">{label}</div>
        <div class="idx-price">₹{price:,.0f}</div>
        <div class="{cls}">{arrow} {abs(chg):.2f}%</div>'''
    
    if age > timedelta(hours=5):
        html += f'<div class="freshness-badge">Data ~{age.seconds//3600}h old</div>'
    
    html += '</div>'
    return html


@st.cache_data(ttl=7200, show_spinner=False)
def load_stats() -> Tuple[int, int, int]:
    """
    Load dataset statistics with error handling.
    """
    try:
        master_df = load_master()
        return (
            len(master_df),
            master_df['Big Sectors'].nunique() if 'Big Sectors' in master_df.columns else 0,
            master_df['Industry'].nunique() if 'Industry' in master_df.columns else 0
        )
    except Exception as e:
        logger.error(f"Failed to load stats: {str(e)}")
        return (0, 0, 0)


def refresh_daily_averages():
    """
    Background task to refresh industry averages daily.
    """
    if st.session_state.get('last_avg_refresh') != str(date.today()):
        def _refresh():
            try:
                # Uncomment when refresh_averages.py exists
                # subprocess.run(["python", "refresh_averages.py"], capture_output=True, timeout=300)
                logger.info("Daily average refresh completed")
            except subprocess.TimeoutExpired:
                logger.warning("Refresh script timed out")
            except Exception as e:
                logger.warning(f"Refresh script failed: {str(e)}")
        
        threading.Thread(target=_refresh, daemon=True).start()
        st.session_state['last_avg_refresh'] = str(date.today())


# ────────────────────────────────────────────────────────────────────
# PAGE CONTENT
# ────────────────────────────────────────────────────────────────────

# Trigger daily refresh
refresh_daily_averages()

# Hero Section
st.markdown('''<div class="hero">
    <div class="hero-tag">📊 NSE / BSE · Fundamental + Technical + Sentiment</div>
    <div class="hero-title">Indian <span class="green">Stock</span> Analyzer</div>
    <div class="hero-sub">Screen thousands of NSE stocks by fundamentals, chart technicals with EMA & RSI, compare entire sectors, and read AI-powered news sentiment — all in one place.</div>
    <div class="pill-row">
        <span class="pill">yfinance</span>
        <span class="pill">FinBERT</span>
        <span class="pill">TF-IDF</span>
        <span class="pill">Plotly</span>
        <span class="pill">SQLite</span>
        <span class="pill">Streamlit</span>
    </div>
</div>''', unsafe_allow_html=True)

# Live Market Section
st.markdown('<div class="sec-label">📈 Live Market</div>', unsafe_allow_html=True)

INDICES = {
    'NIFTY 50': '^NSEI',
    'SENSEX': '^BSESN',
    'NIFTY Bank': '^NSEBANK',
    'NIFTY IT': '^CNXIT',
    'NIFTY FMCG': '^CNXFMCG'
}

# Use optimized parallel fetching
with st.spinner('⏳ Loading market data...'):
    indices_data = get_multiple_indices(list(INDICES.values()))

icols = st.columns(5)
for ic, (lbl, sym) in zip(icols, INDICES.items()):
    data = indices_data.get(sym)
    html = format_index_card(lbl, data)
    ic.markdown(html, unsafe_allow_html=True)

st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)

# Dataset Coverage Stats
st.markdown('<div class="sec-label">📦 Dataset Coverage</div>', unsafe_allow_html=True)

try:
    total_symbols, unique_sectors, unique_industries = load_stats()
    s1, s2, s3 = st.columns(3)
    
    for sc, lbl, val, hint in [
        (s1, 'Total Symbols', str(total_symbols), 'companies tracked on NSE'),
        (s2, 'Unique Sectors', str(unique_sectors), 'broad market sectors'),
        (s3, 'Unique Industries', str(unique_industries), 'industry categories'),
    ]:
        sc.markdown(f'''<div class="stat-card">
            <div class="stat-label">{lbl}</div>
            <div class="stat-num">{val}</div>
            <div class="stat-hint">{hint}</div>
        </div>''', unsafe_allow_html=True)
except Exception as e:
    st.error(f'⚠️ Could not load dataset stats: {str(e)}')
    logger.error(f"Stats loading failed: {str(e)}")

st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)

# Feature Showcase
st.markdown('<div class="sec-label">✨ What You Can Do</div>', unsafe_allow_html=True)

FEATS = [
    ('01', 'Fundamental Screening', 'Analyse PE, EPS, ROE, profit margins, debt ratios, free cash flow and market cap for any NSE stock. Compare with industry averages instantly.'),
    ('02', 'Peer Comparison', 'Select any stock and automatically surface its closest industry peers. Side-by-side financial ratios reveal who leads the pack.'),
    ('03', 'Technical Charting', 'Full candlestick charts with customisable EMA and SMA lengths, RSI momentum, Camarilla and Standard pivot levels.'),
    ('04', 'Sector Rankings', 'Browse every sector and industry. Rank all companies by MCap, EPS, or ROE and highlight top performers with a green-signal scoring system.'),
    ('05', 'Index Pulse', 'Live NIFTY 50 and sectoral index charts. EMA crossover alerts, RSI overbought/oversold flags, and 52-week positioning.'),
    ('06', 'News Sentiment (AI)', 'FinBERT NLP model reads recent headlines and assigns bullish, neutral, or bearish sentiment scores to any stock or index in real time.'),
]

f1, f2, f3 = st.columns(3)
fcols = [f1, f2, f3]
for i, (num, title, desc) in enumerate(FEATS):
    fcols[i % 3].markdown(f'''<div class="feat-card">
        <div class="feat-num">{num}</div>
        <div class="feat-title">{title}</div>
        <div class="feat-desc">{desc}</div>
    </div>''', unsafe_allow_html=True)

st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)

# Navigation Cards
st.markdown('<div class="sec-label">🚀 Go To</div>', unsafe_allow_html=True)

PAGES = [
    ('Fundamentals', 'PE ratio, EPS, ROE, margins, FCF, peer comparison and price history for any NSE stock.', 'pages/1_Fundamentals.py'),
    ('Sector Analysis', 'Browse all sectors. Rank companies by MCap, EPS, or ROE. Flag top performers with signal scoring.', 'pages/2_Sector_Analysis.py'),
    ('Technical Analysis', 'Candlestick + EMA/SMA overlays, RSI, pivot levels, and analyst recommendation tracker.', 'pages/3_Technical_Analysis.py'),
    ('Index Analysis', 'NIFTY 50, SENSEX and sectoral indices with EMA crossovers, RSI signals, and FinBERT sentiment.', 'pages/4_Index_Analysis.py'),
]

nc1, nc2 = st.columns(2)
for i, (title, desc, path) in enumerate(PAGES):
    nc = nc1 if i % 2 == 0 else nc2
    nc.markdown(f'''<div class="nav-card">
        <div class="nav-arrow">→</div>
        <div class="nav-title">{title}</div>
        <div class="nav-desc">{desc}</div>
    </div>''', unsafe_allow_html=True)
    if nc.button('Open ' + title, key='nav_' + str(i)):
        st.switch_page(path)

st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)

# Top Movers Section
st.markdown('<div class="sec-label">🔝 Top Movers Today</div>', unsafe_allow_html=True)

MOVERS = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'WIPRO.NS', 'BAJFINANCE.NS', 'SBIN.NS', 'HINDUNILVR.NS', 'ADANIENT.NS']
MOVER_NAMES = {
    'RELIANCE.NS': 'Reliance',
    'TCS.NS': 'TCS',
    'INFY.NS': 'Infosys',
    'HDFCBANK.NS': 'HDFC Bank',
    'ICICIBANK.NS': 'ICICI Bank',
    'WIPRO.NS': 'Wipro',
    'BAJFINANCE.NS': 'Bajaj Finance',
    'SBIN.NS': 'SBI',
    'HINDUNILVR.NS': 'HUL',
    'ADANIENT.NS': 'Adani Ent.'
}

mover_data = []

def fetch_mover(sym):
    try:
        h = yf.Ticker(sym).history(period='2d', interval='1d')
        if len(h) >= 2:
            p = h['Close'].iloc[-1]
            c = (p - h['Close'].iloc[-2]) / h['Close'].iloc[-2] * 100
            return (sym.replace('.NS', ''), MOVER_NAMES.get(sym, sym), p, c)
    except Exception as e:
        logger.debug(f"Could not fetch mover {sym}: {str(e)}")
    return None

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(fetch_mover, sym) for sym in MOVERS]
    for future in as_completed(futures):
        result = future.result()
        if result:
            mover_data.append(result)

if mover_data:
    mover_data.sort(key=lambda x: abs(x[3]), reverse=True)
    gainers = [m for m in mover_data if m[3] >= 0][:3]
    losers = [m for m in mover_data if m[3] < 0][:3]
    
    mc1, mc2 = st.columns(2)
    
    mc1.markdown('<div style="font-size:0.75rem;font-weight:700;color:#00c882;margin-bottom:0.5rem;">Top Gainers</div>', unsafe_allow_html=True)
    for sym, name, price, chg in gainers:
        mc1.markdown(f'''<div class="mover">
            <div><div class="mover-sym">{sym}</div><div class="mover-name">{name}</div></div>
            <div class="mover-up">+{chg:.2f}%</div>
        </div>''', unsafe_allow_html=True)
    
    mc2.markdown('<div style="font-size:0.75rem;font-weight:700;color:#ff4d6a;margin-bottom:0.5rem;">Top Losers</div>', unsafe_allow_html=True)
    for sym, name, price, chg in losers:
        mc2.markdown(f'''<div class="mover">
            <div><div class="mover-sym">{sym}</div><div class="mover-name">{name}</div></div>
            <div class="mover-dn">{chg:.2f}%</div>
        </div>''', unsafe_allow_html=True)
else:
    st.info('⚠️ Market data unavailable right now. Please try again in a few moments.')

st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:2.5rem 0 1rem;'>", unsafe_allow_html=True)
st.markdown('<div class="footer"><span>Indian Stock Analyzer · Data via Yahoo Finance</span><span>Use the sidebar to navigate</span></div>', unsafe_allow_html=True)
