
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Stock News",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 3.5rem !important; padding-bottom: 2rem; }

.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.0rem !important; font-weight: 800;
    color: #f0f4ff; letter-spacing: -0.02em; margin-bottom: 0.2rem;
}
.page-sub {
    font-size: 0.78rem !important; color: #8aaac8;
    margin-bottom: 1.6rem; letter-spacing: 0.05em;
}
.section-label {
    font-size: 0.68rem !important; letter-spacing: 0.18em;
    text-transform: uppercase; color: #8aaac8;
    border-left: 3px solid #00c882; padding-left: 0.6rem;
    margin-bottom: 0.8rem; margin-top: 1.6rem;
}
.news-card {
    background: #0d1628;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    border-left: 4px solid #6ec6ff;
}

.news-title {
    font-size: 0.95rem !important; font-weight: 700;
    color: #f0f4ff; margin-bottom: 0.5rem;
    line-height: 1.4;
}
.news-source {
    font-size: 0.75rem !important; color: #8aaac8;
    text-transform: uppercase; letter-spacing: 0.05em;
}
.news-desc {
    font-size: 0.8rem !important; color: #c0d4e8;
    margin-top: 0.6rem; line-height: 1.5;
}
.news-date {
    font-size: 0.7rem !important; color: #6a88a8;
    margin-top: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">📰 Stock News</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">// Latest news · market updates · breaking stories</div>', unsafe_allow_html=True)

# ── Load stocks list ──────────────────────────────────────────────────────────
try:
    from common.sql import load_master
    master_df = load_master()
    stocks_list = sorted(master_df['Symbol'].unique().tolist())
except:
    st.error("❌ Could not load stocks from master data. Please check database connection.")
    st.stop()

# ── Stock selector ────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Select Stock</div>', unsafe_allow_html=True)

# Initialize session state for selected stock
if "news_stock" not in st.session_state:
    st.session_state.news_stock = None

# Search bar
search_query = st.text_input(
    "Search",
    placeholder="🔍 Search by symbol or company name...",
    label_visibility="collapsed"
)

selected_stock = None

if search_query:
    # Search in symbol and company name
    mask = (
        master_df["Symbol"].str.contains(search_query, case=False, na=False) |
        master_df["Company Name"].str.contains(search_query, case=False, na=False)
    )
    matches = master_df[mask]
    
    if not matches.empty:
        opts = matches.apply(lambda r: r["Symbol"] + " – " + r["Company Name"], axis=1)
        selected_option = st.selectbox(
            "Select stock",
            opts.tolist(),
            label_visibility="collapsed",
            key="news_stock_select"
        )
        if selected_option:
            selected_stock = selected_option.split(" – ")[0]
            st.session_state.news_stock = selected_stock
    else:
        st.warning("❌ No stocks found matching your search")
elif st.session_state.news_stock:
    # Use previously selected stock
    selected_stock = st.session_state.news_stock
    st.markdown(f"**Currently viewing:** {selected_stock}")
else:
    st.info("👆 Search for a stock to see news")

# ── Fetch news ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">// latest news</div>', unsafe_allow_html=True)

if not selected_stock:
    st.stop()

with st.spinner(f"🔄 Fetching latest news for {selected_stock}..."):
    try:
        ticker = yf.Ticker(f"{selected_stock}.NS")
        news = ticker.news or []
        
        if not news:
            st.warning(f"📰 No news available for {selected_stock}")
        else:
            st.markdown(f"**{len(news)} latest articles**\n")
            
            news_found = 0
            for item in news[:20]:  # Check max 20 articles
                # Safely extract all fields
                try:
                    title = item.get("title", "").strip() if item.get("title") else ""
                    if not title:
                        title = item.get("headline", "").strip() if item.get("headline") else ""
                    
                    summary = item.get("summary", "").strip() if item.get("summary") else ""
                    if not summary:
                        summary = item.get("description", "").strip() if item.get("description") else ""
                    if not summary:
                        summary = item.get("content", "").strip() if item.get("content") else ""
                    
                    publisher = item.get("publisher", "").strip() if item.get("publisher") else ""
                    if not publisher:
                        publisher = item.get("source", "").strip() if item.get("source") else ""
                    if not publisher:
                        publisher = "Unknown Source"
                    
                    link = item.get("link", "").strip() if item.get("link") else ""
                    if not link:
                        link = item.get("url", "").strip() if item.get("url") else ""
                    
                    # Get timestamp
                    timestamp = item.get("providerPublishTime")
                    if timestamp:
                        try:
                            published_date = pd.to_datetime(timestamp, unit='s').strftime("%Y-%m-%d %H:%M")
                        except:
                            published_date = "Recently"
                    else:
                        published_date = "Recently"
                    
                    # Only display if we have a title
                    if title:
                        news_found += 1
                        
                        st.markdown(
                            f'<div class="news-card">'
                            f'<div class="news-source">{publisher}</div>'
                            f'<div class="news-title">{title}</div>'
                            f'<div class="news-desc">{summary[:300]}{"..." if len(summary) > 300 else ""}</div>'
                            f'<div class="news-date">📅 {published_date}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        
                        if link:
                            st.markdown(f"[🔗 Read Full Article]({link})")
                        
                        st.markdown("")  # Spacing
                
                except Exception as e:
                    continue
            
            if news_found == 0:
                st.warning("⚠️ News data found but could not format properly")
                st.info("Sample raw data:")
                st.json(news[0] if news else {})

    except Exception as e:
        st.error(f"❌ Error fetching news: {str(e)}")
        st.info("Try searching for a different stock")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"📰 Fresh news fetched on load • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
