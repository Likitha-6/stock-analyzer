import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

st.set_page_config(
    page_title="IPO Analysis",
    page_icon="🆕",
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

.ipo-card {
    background: linear-gradient(135deg, #0d1628 0%, #0a1420 100%);
    border: 2px solid;
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
}
.ipo-good { border-color: #00c882; }
.ipo-moderate { border-color: #f5a623; }
.ipo-risky { border-color: #ff4d6a; }

.ipo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.2rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 1rem;
}
.ipo-name {
    font-size: 1.3rem;
    font-weight: 800;
    color: #f0f4ff;
}
.ipo-ticker {
    font-size: 0.8rem;
    color: #8aaac8;
    background: rgba(255,255,255,0.05);
    padding: 0.3rem 0.8rem;
    border-radius: 6px;
}
.ipo-rating {
    font-size: 1.2rem;
    font-weight: 700;
}
.ipo-good .ipo-rating { color: #00c882; }
.ipo-moderate .ipo-rating { color: #f5a623; }
.ipo-risky .ipo-rating { color: #ff4d6a; }

.ipo-details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}
.detail-item {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 0.8rem;
}
.detail-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    color: #8aaac8;
    margin-bottom: 0.3rem;
}
.detail-value {
    font-size: 1rem;
    font-weight: 700;
    color: #f0f4ff;
}

.analysis-box {
    background: rgba(255,255,255,0.02);
    border-left: 3px solid;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.8rem 0;
}
.analysis-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #8aaac8;
    margin-bottom: 0.6rem;
}
.analysis-content {
    font-size: 0.9rem;
    color: #c0d4e8;
    line-height: 1.5;
}

.pros-cons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin: 1rem 0;
}
.pros { border-left-color: #00c882; }
.cons { border-left-color: #ff4d6a; }

.pro-item, .con-item {
    font-size: 0.9rem;
    margin-bottom: 0.6rem;
    padding-left: 1rem;
}
.pro-item { color: #00c882; }
.con-item { color: #ff4d6a; }
.pro-item::before { content: "✓ "; font-weight: 700; }
.con-item::before { content: "✗ "; font-weight: 700; }

.recommendation-badge {
    display: inline-block;
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 700;
    margin-top: 1rem;
}
.badge-good { background: rgba(0,200,130,0.2); color: #00c882; }
.badge-moderate { background: rgba(245,166,35,0.2); color: #f5a623; }
.badge-risky { background: rgba(255,77,106,0.2); color: #ff4d6a; }
</style>
""", unsafe_allow_html=True)

# ── Load IPO Data ────────────────────────────────────────────────────────────
from fetch_ipo_data import get_ipo_for_week, load_upcoming_ipos

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_ipos():
    """Load upcoming IPOs for this week"""
    ipos = get_ipo_for_week()
    
    if not ipos:
        # Fallback to all upcoming if none this week
        ipos = load_upcoming_ipos()
    
    return ipos

IPO_DATA = load_ipos()

def analyze_ipo(ipo):
    """Analyze IPO and return recommendation"""
    
    score = 0
    pros = []
    cons = []
    
    # Sector analysis
    good_sectors = ["Technology", "Pharma", "Finance", "FMCG", "Healthcare"]
    if ipo["sector"] in good_sectors:
        score += 2
        pros.append(f"Strong sector: {ipo['sector']}")
    else:
        score -= 1
        cons.append(f"Moderate sector: {ipo['sector']}")
    
    # Issue size (₹300-1000 Cr is healthy)
    try:
        issue_amount = int(ipo["issue_size"].split()[1])
        if 300 <= issue_amount <= 1000:
            score += 2
            pros.append(f"Healthy issue size: ₹{issue_amount} Cr")
        elif issue_amount < 300:
            score += 1
            pros.append(f"Small cap opportunity: ₹{issue_amount} Cr")
        else:
            score -= 1
            cons.append(f"Large issue size: ₹{issue_amount} Cr")
    except:
        pass
    
    # Price band
    price_range = ipo["price_band_high"] - ipo["price_band_low"]
    price_range_pct = (price_range / ipo["price_band_low"]) * 100
    
    if price_range_pct < 25:
        score += 1
        pros.append(f"Stable price band: {price_range_pct:.1f}% range")
    else:
        score -= 1
        cons.append(f"Wide price band: {price_range_pct:.1f}% range")
    
    # Promoter track record
    if ipo["track_record"] != "New":
        track_years = int(ipo["track_record"].split()[0])
        if track_years >= 10:
            score += 3
            pros.append(f"Strong promoter track record: {ipo['track_record']}")
        elif track_years >= 5:
            score += 2
            pros.append(f"Decent track record: {ipo['track_record']}")
        else:
            score -= 1
            cons.append(f"Limited track record: {ipo['track_record']}")
    else:
        score -= 2
        cons.append("New promoter (unproven)")
    
    # Promotion type
    if ipo["promotion"] in ["Founders", "Experienced Entrepreneurs"]:
        score += 2
        pros.append(f"Experienced promoters: {ipo['promotion']}")
    elif ipo["promotion"] == "Family":
        score += 1
        pros.append(f"Family-backed: {ipo['promotion']}")
    else:
        cons.append(f"Promoter type: {ipo['promotion']}")
    
    # Book building status
    if ipo["book_built"]:
        score += 1
        pros.append("Book building completed")
    else:
        cons.append("Book building not yet completed")
    
    # Determine recommendation
    if score >= 7:
        recommendation = "GOOD TO BUY"
        rating = "✅ BUY"
        risk_level = "LOW"
    elif score >= 4:
        recommendation = "MODERATE - Wait for Opening"
        rating = "⚠️ MODERATE"
        risk_level = "MEDIUM"
    else:
        recommendation = "RISKY - Avoid or Wait"
        rating = "❌ AVOID"
        risk_level = "HIGH"
    
    return {
        "score": score,
        "recommendation": recommendation,
        "rating": rating,
        "risk_level": risk_level,
        "pros": pros,
        "cons": cons,
    }

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🆕 IPO Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">// Upcoming IPO analysis · fundamentals · risk assessment</div>', unsafe_allow_html=True)

# ── Week Range ────────────────────────────────────────────────────────────────
today = datetime.now()
week_start = today
week_end = today + timedelta(days=7)

st.markdown(f'<div class="section-label">This Week ({week_start.strftime("%b %d")} - {week_end.strftime("%b %d")})</div>', unsafe_allow_html=True)

# ── IPO Cards ─────────────────────────────────────────────────────────────────
if not IPO_DATA:
    st.info("📭 No IPOs opening this week")
else:
    for ipo in IPO_DATA:
        analysis = analyze_ipo(ipo)
        
        # Determine card class
        if "BUY" in analysis["rating"]:
            card_class = "ipo-good"
            badge_class = "badge-good"
        elif "MODERATE" in analysis["rating"]:
            card_class = "ipo-moderate"
            badge_class = "badge-moderate"
        else:
            card_class = "ipo-risky"
            badge_class = "badge-risky"
        
        # Card
        st.markdown(f'<div class="ipo-card {card_class}">', unsafe_allow_html=True)
        
        # Header
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f'<div class="ipo-name">{ipo["name"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="ipo-ticker">{ipo["ticker"]}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="ipo-rating">{analysis["rating"]}</div>', unsafe_allow_html=True)
        
        # Details grid
        st.markdown('<div class="ipo-details">', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="detail-item">
            <div class="detail-label">Opening Date</div>
            <div class="detail-value">{ipo["opening_date"]}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Closing Date</div>
            <div class="detail-value">{ipo["closing_date"]}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Price Band</div>
            <div class="detail-value">₹{ipo["price_band_low"]}-{ipo["price_band_high"]}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Issue Size</div>
            <div class="detail-value">{ipo["issue_size"]}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Sector</div>
            <div class="detail-value">{ipo["sector"]}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Risk Level</div>
            <div class="detail-value">{analysis["risk_level"]}</div>
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Analysis boxes
        st.markdown(f'<div class="analysis-box" style="border-left-color: #6ec6ff;">', unsafe_allow_html=True)
        st.markdown(f'<div class="analysis-title">📊 Company Profile</div>', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="analysis-content">
        <b>Sector:</b> {ipo["sector"]} → {ipo["sub_sector"]}<br>
        <b>Promoter:</b> {ipo["promotion"]}<br>
        <b>Track Record:</b> {ipo["track_record"]}<br>
        <b>Status:</b> {"Book Building Completed" if ipo["book_built"] else "Book Building Pending"}
        </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Pros and Cons
        st.markdown('<div class="pros-cons">', unsafe_allow_html=True)
        st.markdown('<div class="analysis-box pros">', unsafe_allow_html=True)
        st.markdown('<div class="analysis-title">✅ Positives</div>', unsafe_allow_html=True)
        for pro in analysis["pros"]:
            st.markdown(f'<div class="pro-item">{pro}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="analysis-box cons">', unsafe_allow_html=True)
        st.markdown('<div class="analysis-title">❌ Concerns</div>', unsafe_allow_html=True)
        for con in analysis["cons"]:
            st.markdown(f'<div class="con-item">{con}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Recommendation
        st.markdown(f'''
        <div class="analysis-box" style="border-left-color: #00c882;">
            <div class="analysis-title">🎯 Recommendation</div>
            <div class="analysis-content">
            <b>{analysis["recommendation"]}</b><br>
            Score: {analysis["score"]}/10
            </div>
            <span class="recommendation-badge {badge_class}">{analysis["rating"]}</span>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('---')

# ── IPO Tips ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">📋 IPO Investment Tips</div>', unsafe_allow_html=True)

tips = """
**Before Investing in an IPO:**

1. **Check Sector** - Avoid distressed sectors, prefer growth sectors
2. **Promoter Track Record** - At least 5-10 years of business experience
3. **Issue Size** - ₹300-1000 Cr is healthy range
4. **Price Band** - Should not be too wide (ideally <20% range)
5. **P/E Multiple** - Compare with listed peers in same sector
6. **Issue Subscription** - Higher subscription = better demand
7. **Listing Gains** - Don't get carried away by first-day gains
8. **Exit Plan** - Decide entry and exit before applying

**Red Flags:**

❌ Unknown or unproven promoters
❌ Small issue size (<₹100 Cr) in unproven sector
❌ Very wide price band (>30%)
❌ No clear business model
❌ Highly leveraged company
❌ Sector facing structural challenges

**Green Flags:**

✅ Experienced promoters with track record
✅ Growing market with tailwinds
✅ Strong financial fundamentals
✅ Industry leadership position
✅ Clear growth trajectory
✅ Healthy issue size
"""

st.markdown(tips)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🆕 IPO Analysis Tool • Analyzes upcoming IPOs • For educational purposes • Not financial advice")
