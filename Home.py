# Home.py – Enhanced Dashboard
import streamlit as st
import yfinance as yf
import pandas as pd
from common.sql import load_master
from common.data import load_name_lookup

st.set_page_config(
    page_title="Indian Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }

.hero-wrapper {
    background: linear-gradient(135deg, #0a0f1e 0%, #0d1f3c 50%, #0a1628 100%);
    border: 1px solid rgba(0,200,130,0.15);
    border-radius: 16px;
    padding: 3.5rem 4rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-wrapper::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,200,130,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.22em;
    color: #00c882;
    text-transform: uppercase;
    margin-bottom: 1rem;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1.05;
    color: #f0f4ff;
    margin-bottom: 1.2rem;
    letter-spacing: -0.02em;
}
.hero-title span { color: #00c882; }
.hero-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.92rem;
    color: rgba(180,200,230,0.7);
    line-height: 1.7;
    max-width: 560px;
    font-weight: 300;
}
.pill-row { display: flex; gap: 0.6rem; flex-wrap: wrap; margin-top: 1.8rem; }
.pill {
    background: rgba(0,200,130,0.08);
    border: 1px solid rgba(0,200,130,0.2);
    border-radius: 999px;
    padding: 0.25rem 0.75rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: rgba(0,200,130,0.8);
    letter-spacing: 0.05em;
}
.stat-card {
    background: #0d1628;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.stat-card:hover { border-color: rgba(0,200,130,0.3); }
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00c882, transparent);
}
.stat-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: rgba(150,180,220,0.6);
    margin-bottom: 0.6rem;
}
.stat-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: #f0f4ff;
    line-height: 1;
    margin-bottom: 0.3rem;
}
.stat-sub { font-size: 0.7rem; color: #00c882; font-weight: 300; }
.nav-card {
    background: #0d1628;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.6rem 2rem;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
    margin-bottom: 1rem;
}
.nav-card:hover {
    border-color: rgba(0,200,130,0.35);
    background: #0f1c36;
    transform: translateY(-2px);
}
.nav-card-icon { font-size: 1.8rem; margin-bottom: 0.8rem; display: block; }
.nav-card-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #e8f0ff;
    margin-bottom: 0.4rem;
}
.nav-card-desc {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: rgba(150,180,220,0.55);
    line-height: 1.6;
    font-weight: 300;
}
.nav-card-arrow {
    position: absolute;
    bottom: 1.4rem; right: 1.6rem;
    font-size: 1rem;
    color: rgba(0,200,130,0.4);
}
.section-header {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(150,180,220,0.4);
    margin-bottom: 0.8rem;
    margin-top: 0.5rem;
}
.idx-card {
    text-align: center;
    padding: 0.9rem;
    background: #080d1a;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
}
.idx-name {
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(150,180,220,0.5);
    margin-bottom: 4px;
}
.idx-price {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #e8f0ff;
}
</style>
""", unsafe_allow_html=True)


# ── Hero ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
    <div class="hero-eyebrow">▸ NSE / BSE · Real-time Analysis</div>
    <div class="hero-title">Indian <span>Stock</span><br>Analyzer</div>
    <div class="hero-subtitle">
        Fundamental screening, technical charting, sector comparison,
        and AI-powered news sentiment — all in one place.
    </div>
    <div class="pill-row">
        <span class="pill">Streamlit</span>
        <span class="pill">yfinance</span>
        <span class="pill">FinBERT</span>
        <span class="pill">TF-IDF</span>
        <span class="pill">Plotly</span>
        <span class="pill">SQLite</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Live Market Snapshot ────────────────────────────────────────────────────
st.markdown('<div class="section-header">// live market snapshot</div>', unsafe_allow_html=True)

INDICES = {
    "NIFTY 50":   "^NSEI",
    "SENSEX":     "^BSESN",
    "NIFTY Bank": "^NSEBANK",
    "NIFTY IT":   "^CNXIT",
    "NIFTY FMCG": "^CNXFMCG",
}

cols = st.columns(len(INDICES))
for col, (name, sym) in zip(cols, INDICES.items()):
    try:
        hist = yf.Ticker(sym).history(period="2d", interval="1d")
        if len(hist) >= 2:
            price = hist["Close"].iloc[-1]
            prev  = hist["Close"].iloc[-2]
            chg   = (price - prev) / prev * 100
            arrow = "▲" if chg >= 0 else "▼"
            color = "#00c882" if chg >= 0 else "#ff4d6a"
            col.markdown(f"""
                <div class="idx-card">
                    <div class="idx-name">{name}</div>
                    <div class="idx-price">₹{price:,.0f}</div>
                    <div style="font-size:0.75rem;color:{color};margin-top:3px;">{arrow} {abs(chg):.2f}%</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            col.markdown(f'<div class="idx-card"><div class="idx-name">{name}</div><div class="idx-price">—</div></div>', unsafe_allow_html=True)
    except Exception:
        col.markdown(f'<div class="idx-card"><div class="idx-name">{name}</div><div class="idx-price">—</div></div>', unsafe_allow_html=True)


# ── Dataset Stats ───────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-header">// dataset coverage</div>', unsafe_allow_html=True)

try:
    master_df = load_master()
    name_df   = load_name_lookup()
    stats = [
        ("Total Symbols",     f"{len(master_df):,}",                   "tracked on NSE"),
        ("Unique Sectors",    str(master_df["Big Sectors"].nunique()),  "broad market sectors"),
        ("Unique Industries", str(master_df["Industry"].nunique()),     "industry categories"),
    ]
    for col, (label, value, sub) in zip(st.columns(3), stats):
        col.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{value}</div>
                <div class="stat-sub">{sub}</div>
            </div>
        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error loading dataset stats: {e}")


# ── Navigation Cards ────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
st.markdown('<div class="section-header">// explore the app</div>', unsafe_allow_html=True)

pages = [
    ("📊", "Fundamentals",       "Deep dive into any NSE stock — PE, EPS, ROE, margins, FCF, peer comparison, and historical price charts."),
    ("🏭", "Sector Analysis",    "Browse all sectors and industries. Rank companies by market cap, EPS, or ROE and flag top performers."),
    ("📉", "Technical Analysis", "Candlestick charts with EMA/SMA overlays, RSI, pivot levels, and analyst recommendation history."),
    ("🧭", "Index Analysis",     "Monitor NIFTY 50, SENSEX, and sectoral indices. EMA crossovers, RSI signals, and FinBERT news sentiment."),
]

c1, c2 = st.columns(2)
for i, (icon, title, desc) in enumerate(pages):
    col = c1 if i % 2 == 0 else c2
    col.markdown(f"""
        <div class="nav-card">
            <span class="nav-card-icon">{icon}</span>
            <div class="nav-card-title">{title}</div>
            <div class="nav-card-desc">{desc}</div>
            <span class="nav-card-arrow">→</span>
        </div>
    """, unsafe_allow_html=True)


# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:1.5rem 0;'>", unsafe_allow_html=True)
st.markdown("""
    <div style="display:flex;justify-content:space-between;align-items:center;
         font-family:'DM Mono',monospace;font-size:0.68rem;
         color:rgba(150,180,220,0.35);padding:0 0.2rem;">
        <span>Indian Stock Analyzer · NSE/BSE Data via Yahoo Finance</span>
        <span>Use the sidebar ← to navigate</span>
    </div>
""", unsafe_allow_html=True)
