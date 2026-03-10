import streamlit as st
import yfinance as yf
import pandas as pd
import threading, subprocess
from datetime import date
from common.sql import load_master
from common.data import load_name_lookup

st.set_page_config(
    page_title="Indian Stock Analyzer",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown('\n<style>\n@import url(\'https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;0,700;0,800&display=swap\');\n\n*, html, body, [class*="css"] { font-family: \'Inter\', sans-serif !important; }\n#MainMenu, footer, header { visibility: hidden; }\n.block-container { padding-top: 1.5rem; padding-bottom: 3rem; }\n\n/* ---- Hero ---- */\n.hero {\n    background: linear-gradient(135deg, #060c1a 0%, #0b1a35 55%, #060e1f 100%);\n    border: 1px solid rgba(0,200,130,0.22);\n    border-radius: 18px;\n    padding: 3.5rem 3.5rem 3rem;\n    margin-bottom: 2rem;\n    position: relative; overflow: hidden;\n}\n.hero::before {\n    content: \'\';\n    position: absolute; top: -100px; right: -80px;\n    width: 450px; height: 450px;\n    background: radial-gradient(circle, rgba(0,200,130,0.09) 0%, transparent 65%);\n    pointer-events: none;\n}\n.hero-tag {\n    font-size: 0.72rem; font-weight: 600;\n    color: #00c882; letter-spacing: 0.18em;\n    text-transform: uppercase; margin-bottom: 1.1rem;\n}\n.hero-title {\n    font-size: 2.8rem; font-weight: 800;\n    color: #ffffff; line-height: 1.1;\n    letter-spacing: -0.03em; margin-bottom: 1rem;\n}\n.hero-title .green { color: #00c882; }\n.hero-sub {\n    font-size: 0.95rem; font-weight: 400;\n    color: #a0b8d0; line-height: 1.75;\n    max-width: 500px; margin-bottom: 1.8rem;\n}\n.pill-row { display: flex; gap: 0.5rem; flex-wrap: wrap; }\n.pill {\n    background: rgba(0,200,130,0.1);\n    border: 1px solid rgba(0,200,130,0.28);\n    border-radius: 6px; padding: 0.28rem 0.75rem;\n    font-size: 0.68rem; font-weight: 600;\n    color: #00c882; letter-spacing: 0.05em;\n    text-transform: uppercase;\n}\n\n/* ---- Section label ---- */\n.sec-label {\n    font-size: 0.68rem; font-weight: 700;\n    letter-spacing: 0.16em; text-transform: uppercase;\n    color: #ffffff;\n    border-left: 3px solid #00c882;\n    padding-left: 0.65rem;\n    margin-bottom: 1rem; margin-top: 0.5rem;\n}\n\n/* ---- Index cards ---- */\n.idx-card {\n    background: #0b1525;\n    border: 1px solid rgba(255,255,255,0.09);\n    border-radius: 12px; padding: 1.1rem 0.9rem;\n    text-align: center; transition: border-color 0.2s;\n}\n.idx-card:hover { border-color: rgba(0,200,130,0.35); }\n.idx-name {\n    font-size: 0.63rem; font-weight: 600;\n    letter-spacing: 0.1em; text-transform: uppercase;\n    color: #8aaac8; margin-bottom: 0.45rem;\n}\n.idx-price {\n    font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-bottom: 0.25rem;\n}\n.idx-up   { font-size: 0.8rem; font-weight: 600; color: #00c882; }\n.idx-down { font-size: 0.8rem; font-weight: 600; color: #ff4d6a; }\n\n/* ---- Stat cards ---- */\n.stat-card {\n    background: #0b1525;\n    border: 1px solid rgba(255,255,255,0.09);\n    border-radius: 12px; padding: 1.6rem 1.8rem;\n    position: relative; overflow: hidden; transition: border-color 0.2s;\n}\n.stat-card:hover { border-color: rgba(0,200,130,0.35); }\n.stat-card::before {\n    content: \'\'; position: absolute;\n    top: 0; left: 0; right: 0; height: 3px;\n    background: linear-gradient(90deg, #00c882, transparent);\n}\n.stat-label {\n    font-size: 0.68rem; font-weight: 600;\n    letter-spacing: 0.12em; text-transform: uppercase;\n    color: #8aaac8; margin-bottom: 0.6rem;\n}\n.stat-num {\n    font-size: 2.2rem; font-weight: 800;\n    color: #ffffff; line-height: 1; margin-bottom: 0.4rem;\n}\n.stat-hint { font-size: 0.8rem; font-weight: 500; color: #00c882; }\n\n/* ---- Feature grid ---- */\n.feat-card {\n    background: #0b1525;\n    border: 1px solid rgba(255,255,255,0.09);\n    border-radius: 12px; padding: 1.4rem 1.5rem;\n    height: 100%; transition: all 0.2s;\n}\n.feat-card:hover { border-color: rgba(0,200,130,0.35); background: #0e1c38; }\n.feat-num {\n    font-size: 0.62rem; font-weight: 700;\n    color: #00c882; letter-spacing: 0.12em;\n    margin-bottom: 0.6rem;\n}\n.feat-title {\n    font-size: 0.95rem; font-weight: 700;\n    color: #ffffff; margin-bottom: 0.5rem;\n}\n.feat-desc {\n    font-size: 0.82rem; font-weight: 400;\n    color: #8aaac8; line-height: 1.6;\n}\n\n/* ---- Nav cards ---- */\n.nav-card {\n    background: #0b1525;\n    border: 1px solid rgba(255,255,255,0.09);\n    border-radius: 12px; padding: 1.6rem 1.8rem;\n    margin-bottom: 1rem; position: relative; transition: all 0.2s;\n}\n.nav-card:hover { border-color: rgba(0,200,130,0.4); background: #0e1c38; transform: translateY(-2px); }\n.nav-title { font-size: 1rem; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem; }\n.nav-desc  { font-size: 0.83rem; font-weight: 400; color: #8aaac8; line-height: 1.6; }\n.nav-arrow { position: absolute; top: 1.5rem; right: 1.5rem; color: #00c882; font-size: 1rem; }\n\n/* ---- Buttons ---- */\ndiv[data-testid="stButton"] > button {\n    background: transparent;\n    border: 1px solid rgba(0,200,130,0.35);\n    border-radius: 8px; color: #00c882;\n    font-size: 0.75rem; font-weight: 600;\n    letter-spacing: 0.05em;\n    padding: 0.45rem 1rem; margin-top: 0.7rem;\n    transition: all 0.2s; width: 100%;\n}\ndiv[data-testid="stButton"] > button:hover {\n    background: rgba(0,200,130,0.13);\n    border-color: #00c882;\n}\n\n/* ---- Mover pill ---- */\n.mover {\n    background: #0b1525;\n    border: 1px solid rgba(255,255,255,0.09);\n    border-radius: 10px; padding: 0.8rem 1rem;\n    display: flex; justify-content: space-between; align-items: center;\n    margin-bottom: 0.5rem;\n}\n.mover-sym  { font-size: 0.82rem; font-weight: 700; color: #ffffff; }\n.mover-name { font-size: 0.7rem;  font-weight: 400; color: #8aaac8; margin-top: 1px; }\n.mover-up   { font-size: 0.82rem; font-weight: 700; color: #00c882; }\n.mover-dn   { font-size: 0.82rem; font-weight: 700; color: #ff4d6a; }\n\n/* ---- Footer ---- */\n.footer {\n    font-size: 0.68rem; font-weight: 400;\n    color: #3a5070;\n    display: flex; justify-content: space-between;\n}\n</style>\n', unsafe_allow_html=True)

if st.session_state.get('last_avg_refresh') != str(date.today()):
    def _refresh():
        try:
            subprocess.run(["python", "refresh_averages.py"], capture_output=True)
        except Exception:
            pass
    threading.Thread(target=_refresh, daemon=True).start()
    st.session_state['last_avg_refresh'] = str(date.today())

st.markdown('<div class="hero"><div class="hero-tag">&#9658;&nbsp; NSE / BSE &nbsp;&middot;&nbsp; Fundamental + Technical + Sentiment</div><div class="hero-title">Indian <span class="green">Stock</span> Analyzer</div><div class="hero-sub">Screen thousands of NSE stocks by fundamentals, chart technicals with EMA &amp; RSI, compare entire sectors, and read AI-powered news sentiment &mdash; all in one place.</div><div class="pill-row"><span class="pill">yfinance</span><span class="pill">FinBERT</span><span class="pill">TF-IDF</span><span class="pill">Plotly</span><span class="pill">SQLite</span><span class="pill">Streamlit</span></div></div>', unsafe_allow_html=True)

st.markdown('<div class="sec-label">Live Market</div>', unsafe_allow_html=True)
INDICES = {'NIFTY 50': '^NSEI', 'SENSEX': '^BSESN', 'NIFTY Bank': '^NSEBANK', 'NIFTY IT': '^CNXIT', 'NIFTY FMCG': '^CNXFMCG'}
icols = st.columns(5)
for ic, (lbl, sym) in zip(icols, INDICES.items()):
    try:
        hist = yf.Ticker(sym).history(period='2d', interval='1d')
        if len(hist) >= 2:
            price = hist['Close'].iloc[-1]
            prev  = hist['Close'].iloc[-2]
            chg   = (price - prev) / prev * 100
            arrow = '&#9650;' if chg >= 0 else '&#9660;'
            cls   = 'idx-up' if chg >= 0 else 'idx-down'
            ic.markdown('<div class="idx-card"><div class="idx-name">' + lbl + '</div><div class="idx-price">Rs.' + '{:,.0f}'.format(price) + '</div><div class="' + cls + '">' + arrow + ' ' + '{:.2f}'.format(abs(chg)) + '%</div></div>', unsafe_allow_html=True)
        else:
            ic.markdown('<div class="idx-card"><div class="idx-name">' + lbl + '</div><div class="idx-price">--</div></div>', unsafe_allow_html=True)
    except Exception:
        ic.markdown('<div class="idx-card"><div class="idx-name">' + lbl + '</div><div class="idx-price">--</div></div>', unsafe_allow_html=True)

st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="sec-label">Dataset Coverage</div>', unsafe_allow_html=True)
try:
    master_df = load_master()
    name_df   = load_name_lookup()
    s1, s2, s3 = st.columns(3)
    for sc, lbl, val, hint in [
        (s1, 'Total Symbols',     str(len(master_df)),                       'companies tracked on NSE'),
        (s2, 'Unique Sectors',    str(master_df['Big Sectors'].nunique()),   'broad market sectors'),
        (s3, 'Unique Industries', str(master_df['Industry'].nunique()),      'industry categories'),
    ]:
        sc.markdown('<div class="stat-card"><div class="stat-label">' + lbl + '</div><div class="stat-num">' + val + '</div><div class="stat-hint">' + hint + '</div></div>', unsafe_allow_html=True)
except Exception as e:
    st.error('Error loading stats: ' + str(e))

st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="sec-label">What You Can Do</div>', unsafe_allow_html=True)

FEATS = [
    ('01', 'Fundamental Screening',   'Analyse PE, EPS, ROE, profit margins, debt ratios, free cash flow and market cap for any NSE stock. Compare with industry averages instantly.'),
    ('02', 'Peer Comparison',          'Select any stock and automatically surface its closest industry peers. Side-by-side financial ratios reveal who leads the pack.'),
    ('03', 'Technical Charting',       'Full candlestick charts with customisable EMA and SMA lengths, RSI momentum, Camarilla and Standard pivot levels.'),
    ('04', 'Sector Rankings',          'Browse every sector and industry. Rank all companies by MCap, EPS, or ROE and highlight top performers with a green-signal scoring system.'),
    ('05', 'Index Pulse',              'Live NIFTY 50 and sectoral index charts. EMA crossover alerts, RSI overbought/oversold flags, and 52-week positioning.'),
    ('06', 'News Sentiment (AI)',      'FinBERT NLP model reads recent headlines and assigns bullish, neutral, or bearish sentiment scores to any stock or index in real time.'),
]

f1, f2, f3 = st.columns(3)
fcols = [f1, f2, f3]
for i, (num, title, desc) in enumerate(FEATS):
    fcols[i % 3].markdown('<div class="feat-card"><div class="feat-num">' + num + '</div><div class="feat-title">' + title + '</div><div class="feat-desc">' + desc + '</div></div>', unsafe_allow_html=True)
    if i < len(FEATS) - 1 and (i + 1) % 3 == 0:
        pass

st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="sec-label">Go To</div>', unsafe_allow_html=True)

PAGES = [
    ('Fundamentals',       'PE ratio, EPS, ROE, margins, FCF, peer comparison and price history for any NSE stock.',               'pages/1_Fundamentals.py'),
    ('Sector Analysis',    'Browse all sectors. Rank companies by MCap, EPS, or ROE. Flag top performers with signal scoring.',      'pages/2_Sector_Analysis.py'),
    ('Technical Analysis', 'Candlestick + EMA/SMA overlays, RSI, pivot levels, and analyst recommendation tracker.',                'pages/3_Technical_Analysis.py'),
    ('Index Analysis',     'NIFTY 50, SENSEX and sectoral indices with EMA crossovers, RSI signals, and FinBERT sentiment.',         'pages/4_Index_Analysis.py'),
]

nc1, nc2 = st.columns(2)
for i, (title, desc, path) in enumerate(PAGES):
    nc = nc1 if i % 2 == 0 else nc2
    nc.markdown('<div class="nav-card"><div class="nav-arrow">&#8594;</div><div class="nav-title">' + title + '</div><div class="nav-desc">' + desc + '</div></div>', unsafe_allow_html=True)
    if nc.button('Open ' + title, key='nav_' + str(i)):
        st.switch_page(path)

st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="sec-label">Top Movers Today</div>', unsafe_allow_html=True)
MOVERS = ['RELIANCE.NS','TCS.NS','INFY.NS','HDFCBANK.NS','ICICIBANK.NS','WIPRO.NS','BAJFINANCE.NS','SBIN.NS','HINDUNILVR.NS','ADANIENT.NS']
MOVER_NAMES = {'RELIANCE.NS':'Reliance','TCS.NS':'TCS','INFY.NS':'Infosys','HDFCBANK.NS':'HDFC Bank','ICICIBANK.NS':'ICICI Bank','WIPRO.NS':'Wipro','BAJFINANCE.NS':'Bajaj Finance','SBIN.NS':'SBI','HINDUNILVR.NS':'HUL','ADANIENT.NS':'Adani Ent.'}
mover_data = []
for sym in MOVERS:
    try:
        h = yf.Ticker(sym).history(period='2d', interval='1d')
        if len(h) >= 2:
            p = h['Close'].iloc[-1]
            c = (p - h['Close'].iloc[-2]) / h['Close'].iloc[-2] * 100
            mover_data.append((sym.replace('.NS',''), MOVER_NAMES.get(sym, sym), p, c))
    except Exception:
        pass
if mover_data:
    mover_data.sort(key=lambda x: abs(x[3]), reverse=True)
    gainers = [m for m in mover_data if m[3] >= 0][:3]
    losers  = [m for m in mover_data if m[3] <  0][:3]
    mc1, mc2 = st.columns(2)
    mc1.markdown('<div style="font-size:0.75rem;font-weight:700;color:#00c882;margin-bottom:0.5rem;">Top Gainers</div>', unsafe_allow_html=True)
    for sym, name, price, chg in gainers:
        mc1.markdown('<div class="mover"><div><div class="mover-sym">' + sym + '</div><div class="mover-name">' + name + '</div></div><div class="mover-up">+' + '{:.2f}'.format(chg) + '%</div></div>', unsafe_allow_html=True)
    mc2.markdown('<div style="font-size:0.75rem;font-weight:700;color:#ff4d6a;margin-bottom:0.5rem;">Top Losers</div>', unsafe_allow_html=True)
    for sym, name, price, chg in losers:
        mc2.markdown('<div class="mover"><div><div class="mover-sym">' + sym + '</div><div class="mover-name">' + name + '</div></div><div class="mover-dn">' + '{:.2f}'.format(chg) + '%</div></div>', unsafe_allow_html=True)
else:
    st.info('Market data unavailable right now.')

st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:2.5rem 0 1rem;'>", unsafe_allow_html=True)
st.markdown('<div class="footer"><span>Indian Stock Analyzer &nbsp;&middot;&nbsp; Data via Yahoo Finance</span><span>Use the sidebar to navigate</span></div>', unsafe_allow_html=True)
