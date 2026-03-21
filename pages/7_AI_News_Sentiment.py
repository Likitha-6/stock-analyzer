"""
News Sentiment Analysis with Claude API
========================================
Analyzes stock news using Claude LLM to determine:
- Sentiment (Bullish/Bearish/Neutral)
- Key points
- Market impact
- Investment implications
"""

import anthropic
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Initialize Claude client
@st.cache_resource
def get_claude_client():
    return anthropic.Anthropic()

def fetch_recent_news(symbol, days=2):
    """Fetch news for last N days"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        news = ticker.news or []
        
        two_days_ago = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days)
        recent_news = []
        
        for item in news:
            try:
                content = item.get("content", {})
                pub_date = content.get("pubDate", content.get("displayTime", ""))
                
                if pub_date:
                    try:
                        article_date = pd.to_datetime(pub_date)
                        if article_date >= two_days_ago:
                            recent_news.append(item)
                    except:
                        pass
            except:
                pass
        
        return recent_news
    except Exception as e:
        st.error(f"Error fetching news: {e}")
        return []

def extract_news_text(news_items):
    """Extract text from news items"""
    news_text = []
    
    for item in news_items[:10]:  # Limit to 10 articles
        try:
            content = item.get("content", {})
            
            title = content.get("title", "")
            summary = content.get("summary", "")
            provider = content.get("provider", {}).get("displayName", "Unknown")
            pub_date = content.get("pubDate", "")
            
            if pub_date:
                try:
                    pub_date = pd.to_datetime(pub_date).strftime("%Y-%m-%d %H:%M")
                except:
                    pass
            
            news_text.append(f"[{provider}] {pub_date}\nTitle: {title}\nSummary: {summary}")
        except:
            pass
    
    return "\n\n".join(news_text)

def analyze_sentiment_with_claude(symbol, news_text):
    """Analyze news sentiment using Claude"""
    
    client = get_claude_client()
    
    prompt = f"""Analyze the following stock news for {symbol} and provide a detailed sentiment analysis.

NEWS ARTICLES:
{news_text}

Please provide analysis in the following JSON format:
{{
    "overall_sentiment": "BULLISH | BEARISH | NEUTRAL",
    "confidence": 0-100,
    "sentiment_score": -1.0 to 1.0 (where -1 is very bearish, 0 is neutral, 1 is very bullish),
    "key_points": ["point1", "point2", "point3"],
    "bullish_factors": ["factor1", "factor2"],
    "bearish_factors": ["factor1", "factor2"],
    "market_impact": "Brief explanation of potential market impact",
    "investment_implication": "What this means for investors",
    "headline": "One-line summary of sentiment"
}}

Be specific, analytical, and base your analysis only on the provided news articles."""

    with st.spinner("🤖 Analyzing sentiment with Claude..."):
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text

def parse_sentiment_response(response_text):
    """Parse Claude's response"""
    try:
        import json
        # Extract JSON from response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
    except Exception as e:
        st.error(f"Error parsing response: {e}")
    
    return None

def get_sentiment_color(sentiment):
    """Get color for sentiment"""
    if sentiment == "BULLISH":
        return "#00c882"
    elif sentiment == "BEARISH":
        return "#ff4d6a"
    else:
        return "#f5a623"

def get_sentiment_emoji(sentiment):
    """Get emoji for sentiment"""
    if sentiment == "BULLISH":
        return "📈"
    elif sentiment == "BEARISH":
        return "📉"
    else:
        return "➡️"

# Main App
st.set_page_config(
    page_title="AI News Sentiment",
    page_icon="🤖",
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
.sentiment-card {
    background: #0d1628;
    border: 2px solid;
    border-radius: 16px;
    padding: 2rem;
    margin: 1rem 0;
}
.sentiment-bullish { border-color: #00c882; }
.sentiment-bearish { border-color: #ff4d6a; }
.sentiment-neutral { border-color: #f5a623; }

.sentiment-label {
    font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}
.sentiment-headline {
    font-size: 1.4rem; font-weight: 700;
    color: #f0f4ff; margin-bottom: 1rem;
}
.sentiment-score {
    font-size: 2rem; font-weight: 800;
    margin-bottom: 1rem;
}
.sentiment-bars {
    display: flex; gap: 1rem; margin: 1rem 0;
}
.bar-item {
    flex: 1;
}
.bar-label {
    font-size: 0.7rem; color: #8aaac8; margin-bottom: 0.3rem;
}
.bar {
    height: 24px; border-radius: 4px;
    background: rgba(255,255,255,0.1);
}
.bullish-bar { background: rgba(0,200,130,0.3); }
.bearish-bar { background: rgba(255,77,106,0.3); }
.neutral-bar { background: rgba(245,166,35,0.3); }

.factors-box {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}
.factors-title {
    font-size: 0.8rem; font-weight: 700;
    text-transform: uppercase; color: #8aaac8;
    margin-bottom: 0.8rem;
}
.factor-item {
    font-size: 0.85rem; color: #c0d4e8;
    margin-bottom: 0.5rem;
    padding-left: 1rem;
}
.bullish-factor::before { content: "✅ "; color: #00c882; }
.bearish-factor::before { content: "❌ "; color: #ff4d6a; }

.impact-box {
    background: rgba(255,255,255,0.03);
    border-left: 3px solid #6ec6ff;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
}
.impact-title {
    font-size: 0.75rem; text-transform: uppercase;
    color: #8aaac8; margin-bottom: 0.5rem;
}
.impact-text {
    font-size: 0.9rem; color: #c0d4e8; line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🤖 AI News Sentiment Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">// Claude-powered sentiment analysis · bullish/bearish signals · market impact</div>', unsafe_allow_html=True)

# ── Load stocks ───────────────────────────────────────────────────────────────
try:
    from common.sql import load_master
    master_df = load_master()
    stocks_list = sorted(master_df['Symbol'].unique().tolist())
except:
    st.error("❌ Could not load stocks from master data")
    st.stop()

# ── Stock selector ────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Select Stock</div>', unsafe_allow_html=True)

# Initialize session state
if "sentiment_stock" not in st.session_state:
    st.session_state.sentiment_stock = None

search_query = st.text_input(
    "Search",
    placeholder="🔍 Search by symbol or company name...",
    label_visibility="collapsed"
)

selected_stock = None

if search_query:
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
            key="sentiment_stock_select"
        )
        if selected_option:
            selected_stock = selected_option.split(" – ")[0]
            st.session_state.sentiment_stock = selected_stock
    else:
        st.warning("❌ No stocks found matching your search")
elif st.session_state.sentiment_stock:
    selected_stock = st.session_state.sentiment_stock
    st.markdown(f"**Currently analyzing:** {selected_stock}")
else:
    st.info("👆 Search for a stock to analyze news sentiment")

# ── Analyze sentiment ─────────────────────────────────────────────────────────
if selected_stock:
    st.markdown('<div class="section-label">// sentiment analysis</div>', unsafe_allow_html=True)
    
    if st.button("🔍 Analyze News Sentiment", use_container_width=True):
        # Fetch news
        news_items = fetch_recent_news(selected_stock, days=2)
        
        if not news_items:
            st.warning(f"📰 No news found for {selected_stock} in last 2 days")
        else:
            st.success(f"✅ Found {len(news_items)} articles")
            
            # Extract news text
            news_text = extract_news_text(news_items)
            
            # Analyze with Claude
            response = analyze_sentiment_with_claude(selected_stock, news_text)
            
            # Parse response
            sentiment_data = parse_sentiment_response(response)
            
            if sentiment_data:
                sentiment = sentiment_data.get("overall_sentiment", "NEUTRAL")
                confidence = sentiment_data.get("confidence", 0)
                score = sentiment_data.get("sentiment_score", 0)
                headline = sentiment_data.get("headline", "")
                key_points = sentiment_data.get("key_points", [])
                bullish = sentiment_data.get("bullish_factors", [])
                bearish = sentiment_data.get("bearish_factors", [])
                impact = sentiment_data.get("market_impact", "")
                implication = sentiment_data.get("investment_implication", "")
                
                # Display sentiment card
                color = get_sentiment_color(sentiment)
                emoji = get_sentiment_emoji(sentiment)
                
                st.markdown(f'<div class="sentiment-card sentiment-{sentiment.lower()}">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f'<div class="sentiment-label" style="color:{color};">{emoji} {sentiment}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="sentiment-headline">{headline}</div>', unsafe_allow_html=True)
                    st.markdown(f'**Score:** {score:.2f} (-1 Bearish → 0 Neutral → 1 Bullish)', unsafe_allow_html=True)
                
                with col2:
                    st.metric("Confidence", f"{confidence}%")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Key points
                st.markdown('<div class="section-label">Key Points</div>', unsafe_allow_html=True)
                for point in key_points:
                    st.markdown(f"• {point}")
                
                # Factors
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="factors-box">', unsafe_allow_html=True)
                    st.markdown('<div class="factors-title">📈 Bullish Factors</div>', unsafe_allow_html=True)
                    if bullish:
                        for factor in bullish:
                            st.markdown(f'<div class="factor-item bullish-factor">{factor}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("No bullish factors identified")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown('<div class="factors-box">', unsafe_allow_html=True)
                    st.markdown('<div class="factors-title">📉 Bearish Factors</div>', unsafe_allow_html=True)
                    if bearish:
                        for factor in bearish:
                            st.markdown(f'<div class="factor-item bearish-factor">{factor}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown("No bearish factors identified")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Market impact
                st.markdown('<div class="impact-box">', unsafe_allow_html=True)
                st.markdown('<div class="impact-title">💡 Market Impact</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="impact-text">{impact}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Investment implication
                st.markdown('<div class="impact-box">', unsafe_allow_html=True)
                st.markdown('<div class="impact-title">🎯 Investment Implication</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="impact-text">{implication}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("Could not parse sentiment analysis")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🤖 Powered by Claude AI • Analyzes last 2 days of news • For informational purposes only")
