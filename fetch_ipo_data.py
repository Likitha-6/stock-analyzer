"""
Automated IPO Fetcher
====================
Fetches real upcoming IPO data from:
1. NSE Website
2. BSE Website
3. IPO tracking websites
4. Web scraping from financial sites

Stores in CSV for caching and historical tracking
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

DATA_DIR = "data/ipo_data"
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

# Headers to avoid being blocked by websites
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def fetch_ipo_from_nse():
    """Fetch IPOs from NSE website"""
    try:
        print("📡 Fetching from NSE...")
        
        # NSE IPO page
        url = "https://www.nseindia.com/products/content/equities/ipos/nse_ipos.htm"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print("❌ NSE fetch failed")
            return []
        
        # Parse tables
        tables = pd.read_html(response.text)
        
        ipos = []
        for table in tables:
            if not table.empty:
                # Try to extract IPO data
                for _, row in table.iterrows():
                    try:
                        ipo_dict = {
                            "name": row.get(0) or row.get("Company") or "",
                            "opening_date": str(row.get(1) or ""),
                            "closing_date": str(row.get(2) or ""),
                            "price_band_low": row.get(3) or 0,
                            "price_band_high": row.get(4) or 0,
                            "source": "NSE"
                        }
                        if ipo_dict["name"] and ipo_dict["opening_date"]:
                            ipos.append(ipo_dict)
                    except:
                        pass
        
        if ipos:
            print(f"✅ Found {len(ipos)} IPOs from NSE")
        return ipos
    except Exception as e:
        print(f"❌ NSE error: {e}")
        return []

def fetch_ipo_from_bse():
    """Fetch IPOs from BSE website"""
    try:
        print("📡 Fetching from BSE...")
        
        url = "https://www.bseindia.com/markets/MarketWatch/MWCompanySearch.aspx?flag=ipos"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print("❌ BSE fetch failed")
            return []
        
        # Parse tables
        tables = pd.read_html(response.text)
        
        ipos = []
        for table in tables:
            if not table.empty and len(table.columns) > 2:
                for _, row in table.iterrows():
                    try:
                        ipo_dict = {
                            "name": str(row.iloc[0]) if len(row) > 0 else "",
                            "opening_date": str(row.iloc[1]) if len(row) > 1 else "",
                            "closing_date": str(row.iloc[2]) if len(row) > 2 else "",
                            "source": "BSE"
                        }
                        if ipo_dict["name"] and ipo_dict["opening_date"]:
                            ipos.append(ipo_dict)
                    except:
                        pass
        
        if ipos:
            print(f"✅ Found {len(ipos)} IPOs from BSE")
        return ipos
    except Exception as e:
        print(f"❌ BSE error: {e}")
        return []

def fetch_ipo_from_moneycontrol():
    """Fetch from Moneycontrol IPO calendar"""
    try:
        print("📡 Fetching from Moneycontrol...")
        
        url = "https://www.moneycontrol.com/ipo/"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print("❌ Moneycontrol fetch failed")
            return []
        
        # Extract using regex or parsing
        # This is a simplified version - production would need more robust parsing
        tables = pd.read_html(response.text)
        
        ipos = []
        for table in tables:
            if not table.empty:
                try:
                    for _, row in table.iterrows():
                        # Try to extract company name and dates
                        row_str = str(row)
                        if "IPO" in row_str or "opening" in row_str.lower():
                            ipo_dict = {
                                "source": "Moneycontrol"
                            }
                            # Parse row for IPO data
                            for idx, cell in enumerate(row):
                                cell_str = str(cell).strip()
                                if idx == 0 and cell_str:
                                    ipo_dict["name"] = cell_str
                                elif "date" in cell_str.lower() or re.match(r'\d{1,2}-\d{1,2}-\d{4}', cell_str):
                                    if "opening_date" not in ipo_dict:
                                        ipo_dict["opening_date"] = cell_str
                                    else:
                                        ipo_dict["closing_date"] = cell_str
                            
                            if "name" in ipo_dict and "opening_date" in ipo_dict:
                                ipos.append(ipo_dict)
                except:
                    pass
        
        if ipos:
            print(f"✅ Found {len(ipos)} IPOs from Moneycontrol")
        return ipos
    except Exception as e:
        print(f"❌ Moneycontrol error: {e}")
        return []

def fetch_ipo_from_tick():
    """Fetch from Tickertape or similar"""
    try:
        print("📡 Fetching from financial databases...")
        
        # Try multiple endpoints
        ipos = []
        
        # You can add more API endpoints here
        # Example: tickertape.in, investing.com, etc.
        
        return ipos
    except Exception as e:
        print(f"❌ Financial DB error: {e}")
        return []

def enrich_ipo_data(ipos):
    """Enrich IPO data with additional info"""
    try:
        enriched = []
        
        for ipo in ipos:
            # Try to get more data if missing
            name = ipo.get("name", "").strip()
            
            # Extract ticker if available
            if "(" in name and ")" in name:
                ipo["ticker"] = name.split("(")[-1].replace(")", "").strip()
                ipo["name"] = name.split("(")[0].strip()
            else:
                ipo["ticker"] = name[:4].upper() if name else "N/A"
            
            # Parse dates
            ipo["opening_date"] = parse_date(ipo.get("opening_date", ""))
            ipo["closing_date"] = parse_date(ipo.get("closing_date", ""))
            
            # Add default values for missing fields
            ipo.setdefault("price_band_low", "TBD")
            ipo.setdefault("price_band_high", "TBD")
            ipo.setdefault("issue_size", "TBD")
            ipo.setdefault("sector", "TBD")
            ipo.setdefault("sub_sector", "TBD")
            ipo.setdefault("book_built", False)
            ipo.setdefault("promotion", "TBD")
            ipo.setdefault("track_record", "TBD")
            ipo.setdefault("subscription", "0x")
            ipo.setdefault("listing_status", "Upcoming")
            
            # Add metadata
            ipo["fetch_date"] = datetime.now().isoformat()
            
            enriched.append(ipo)
        
        return enriched
    except Exception as e:
        print(f"Error enriching data: {e}")
        return ipos

def parse_date(date_str):
    """Parse various date formats"""
    if not date_str or date_str == "N/A":
        return None
    
    date_str = str(date_str).strip()
    
    # Try different formats
    formats = [
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d %b %Y",
        "%d %B %Y",
        "%d-%b-%Y",
        "%d.%m.%Y",
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except:
            pass
    
    return date_str

def filter_upcoming_ipos(ipos, days_ahead=30):
    """Filter only upcoming IPOs (next X days)"""
    upcoming = []
    today = datetime.now()
    cutoff_date = today + timedelta(days=days_ahead)
    
    for ipo in ipos:
        try:
            opening_date = datetime.strptime(ipo.get("opening_date", ""), "%Y-%m-%d")
            if today <= opening_date <= cutoff_date:
                upcoming.append(ipo)
        except:
            # If can't parse date, include it anyway
            upcoming.append(ipo)
    
    return upcoming

def remove_duplicates(ipos):
    """Remove duplicate IPO entries"""
    seen = set()
    unique = []
    
    for ipo in ipos:
        # Create unique key based on company name and dates
        key = (
            ipo.get("name", "").lower().strip(),
            ipo.get("opening_date", ""),
            ipo.get("closing_date", "")
        )
        
        if key not in seen:
            seen.add(key)
            unique.append(ipo)
    
    return unique

def save_ipo_data(ipos):
    """Save IPO data to CSV"""
    if not ipos:
        print("No IPOs to save")
        return False
    
    df = pd.DataFrame(ipos)
    
    # Save latest
    latest_file = f"{DATA_DIR}/upcoming_ipos.csv"
    df.to_csv(latest_file, index=False)
    print(f"✅ Saved {len(df)} IPOs to {latest_file}")
    
    # Archive
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    archive_file = f"{DATA_DIR}/ipo_archive_{date_str}.csv"
    df.to_csv(archive_file, index=False)
    print(f"✅ Archived to {archive_file}")
    
    return True

def fetch_all_ipos(days_ahead=30):
    """Fetch IPOs from all sources"""
    print(f"\n{'='*70}")
    print(f"Starting IPO Fetcher - {datetime.now()}")
    print(f"Fetching IPOs opening in next {days_ahead} days")
    print(f"{'='*70}\n")
    
    all_ipos = []
    
    # Try all sources
    all_ipos.extend(fetch_ipo_from_nse())
    all_ipos.extend(fetch_ipo_from_bse())
    all_ipos.extend(fetch_ipo_from_moneycontrol())
    all_ipos.extend(fetch_ipo_from_tick())
    
    print(f"\n📊 Total IPOs fetched: {len(all_ipos)}")
    
    # Clean and enrich
    print("🔧 Enriching data...")
    all_ipos = enrich_ipo_data(all_ipos)
    
    print("🧹 Removing duplicates...")
    all_ipos = remove_duplicates(all_ipos)
    
    print("📅 Filtering upcoming IPOs...")
    upcoming = filter_upcoming_ipos(all_ipos, days_ahead=days_ahead)
    
    print(f"✅ Found {len(upcoming)} upcoming IPOs\n")
    
    # Save
    if upcoming:
        save_ipo_data(upcoming)
    else:
        print("⚠️ No upcoming IPOs found")
    
    print(f"\n{'='*70}")
    print(f"IPO Fetcher completed at {datetime.now()}")
    print(f"{'='*70}\n")
    
    return upcoming

def load_upcoming_ipos():
    """Load cached IPO data"""
    ipo_file = f"{DATA_DIR}/upcoming_ipos.csv"
    
    if Path(ipo_file).exists():
        try:
            df = pd.read_csv(ipo_file)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading IPOs: {e}")
            return []
    
    return []

def get_ipo_for_week():
    """Get IPOs opening this week"""
    ipos = load_upcoming_ipos()
    
    if not ipos:
        return []
    
    today = datetime.now()
    week_end = today + timedelta(days=7)
    
    this_week = []
    for ipo in ipos:
        try:
            opening_date = datetime.strptime(ipo.get("opening_date", ""), "%Y-%m-%d")
            if today <= opening_date <= week_end:
                this_week.append(ipo)
        except:
            pass
    
    return sorted(this_week, key=lambda x: x.get("opening_date", ""))

if __name__ == "__main__":
    # Fetch all IPOs
    ipos = fetch_all_ipos(days_ahead=30)
    
    # Display results
    if ipos:
        df = pd.DataFrame(ipos)
        print("\n📋 Upcoming IPOs:")
        print(df[['name', 'ticker', 'opening_date', 'closing_date', 'source']])
    else:
        print("No IPOs found")
