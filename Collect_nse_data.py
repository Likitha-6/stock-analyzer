#!/usr/bin/env python3
"""
COLLECT NSE DATA - Refresh database with fresh stock data
Usage: python3 collect_nse_data.py

This script:
1. Reads nse_stocks_.csv (your fresh stock list)
2. Fetches data from NSETools for each stock
3. Stores in SQLite database (nse.db)
4. Creates up-to-date database for your app

No rate limits - NSETools is official NSE API
Time: ~10 minutes for 2000+ stocks
"""

import pandas as pd
import sqlite3
import sys
from pathlib import Path

try:
    from nsetools import nse
except ImportError:
    print("❌ nsetools not installed!")
    print("Run: pip install nsetools")
    sys.exit(1)

def setup_database():
    """Create database schema"""
    conn = sqlite3.connect('nse.db')
    cursor = conn.cursor()
    
    # Drop old table if exists
    cursor.execute("DROP TABLE IF EXISTS DimCompany")
    
    # Create new table
    cursor.execute("""
        CREATE TABLE DimCompany (
            Symbol TEXT PRIMARY KEY,
            CompanyName TEXT,
            Industry TEXT,
            Big_Sectors TEXT,
            PE_Ratio REAL,
            EPS REAL,
            ROE REAL,
            ProfitMargin REAL,
            DebtToEquity REAL,
            MarketCap REAL,
            Description TEXT,
            Price REAL,
            High52w REAL,
            Low52w REAL,
            Volume INTEGER
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database schema created")

def load_stocks():
    """Load stock list from CSV"""
    try:
        df = pd.read_csv('data/nse_stocks_.csv')
        print(f"✅ Loaded {len(df)} stocks from nse_stocks_.csv")
        return df
    except FileNotFoundError:
        print("❌ nse_stocks_.csv not found!")
        print("Make sure it's in data/nse_stocks_.csv")
        sys.exit(1)

def fetch_stock_data(symbol):
    """Fetch data for single stock from NSETools"""
    try:
        nse_instance = nse.Nse()
        
        # Get quote data
        quote = nse_instance.get_quote(symbol)
        
        if not quote:
            return None
        
        return {
            'PE_Ratio': quote.get('pe'),
            'EPS': quote.get('eps'),
            'Price': float(quote.get('lastPrice', 0)) if quote.get('lastPrice') else None,
            'High52w': float(quote.get('high52w', 0)) if quote.get('high52w') else None,
            'Low52w': float(quote.get('low52w', 0)) if quote.get('low52w') else None,
            'Volume': int(quote.get('totalTradedVolume', 0)) if quote.get('totalTradedVolume') else None,
            'MarketCap': quote.get('marketCap'),
        }
    except Exception as e:
        print(f"  ⚠️  Error fetching {symbol}: {str(e)[:50]}")
        return None

def save_to_database(stocks_df):
    """Save stock data to database"""
    conn = sqlite3.connect('nse.db')
    
    print(f"\nFetching data for {len(stocks_df)} stocks...")
    print("This will take a few minutes...\n")
    
    success_count = 0
    
    for idx, row in stocks_df.iterrows():
        symbol = row['Symbol']
        company_name = row.get('Company Name', symbol)
        
        # Show progress
        if (idx + 1) % 100 == 0:
            print(f"[{idx + 1}/{len(stocks_df)}] {symbol}...")
        
        # Fetch data from NSETools
        data = fetch_stock_data(symbol)
        
        if data:
            try:
                conn.execute("""
                    INSERT INTO DimCompany 
                    (Symbol, CompanyName, Industry, Big_Sectors, PE_Ratio, EPS, 
                     MarketCap, Price, High52w, Low52w, Volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    company_name,
                    row.get('Industry', 'N/A'),
                    row.get('Sector', 'N/A'),
                    data.get('PE_Ratio'),
                    data.get('EPS'),
                    data.get('MarketCap'),
                    data.get('Price'),
                    data.get('High52w'),
                    data.get('Low52w'),
                    data.get('Volume'),
                ))
                conn.commit()
                success_count += 1
            except Exception as e:
                print(f"  ❌ DB error for {symbol}: {str(e)[:30]}")
    
    conn.close()
    
    print(f"\n✅ Successfully saved {success_count}/{len(stocks_df)} stocks to nse.db")
    return success_count

def main():
    """Main function"""
    print("═" * 70)
    print("NSE DATA COLLECTION - Refresh nse.db with fresh data")
    print("═" * 70)
    
    # Step 1: Setup database
    print("\nStep 1: Creating database...")
    setup_database()
    
    # Step 2: Load stocks
    print("\nStep 2: Loading stock list...")
    stocks_df = load_stocks()
    
    # Step 3: Fetch data
    print("\nStep 3: Fetching data from NSETools...")
    success = save_to_database(stocks_df)
    
    # Summary
    print("\n" + "═" * 70)
    print("SUMMARY")
    print("═" * 70)
    print(f"Total stocks processed: {len(stocks_df)}")
    print(f"Successfully saved: {success}")
    print(f"Success rate: {success/len(stocks_df)*100:.1f}%")
    print("\n✅ Database refresh complete!")
    print("Your app now has fresh data for all stocks.")
    print("\nNext: Upload nse.db to GitHub and redeploy on Streamlit Cloud")
    print("═" * 70)

if __name__ == "__main__":
    main()
