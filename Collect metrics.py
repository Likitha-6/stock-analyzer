"""
Daily Stock Metrics Collection
===============================
Collects fundamental and technical metrics for all stocks at 12 AM daily.
Stores data in CSV for fast retrieval without API calls during the day.

Run as scheduled task (cron/Task Scheduler) to execute daily at 12:00 AM
"""

import pandas as pd
import yfinance as yf
import os
from datetime import datetime
from pathlib import Path
import json

# Configuration
DATA_DIR = "data/daily_metrics"
ARCHIVE_DIR = "data/metrics_archive"
STOCKS_FILE = "data/stocks.csv"

# Create directories
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(ARCHIVE_DIR).mkdir(parents=True, exist_ok=True)

def load_stocks_list():
    """Load list of stocks to collect metrics for"""
    try:
        # Try to load from master database
        try:
            from common.sql import load_master
            master_df = load_master()
            return master_df['Symbol'].tolist()
        except:
            # Fallback to CSV
            df = pd.read_csv(STOCKS_FILE)
            return df['Symbol'].tolist()
    except Exception as e:
        print(f"Error loading stocks list: {e}")
        return []

def fetch_stock_metrics(symbol):
    """Fetch comprehensive metrics for a stock"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info or {}
        
        # Fetch historical data
        hist = ticker.history(period="1y")
        
        if hist.empty:
            return None
        
        # Current price
        current_price = hist["Close"].iloc[-1]
        
        # Calculate technical metrics
        sma_50 = hist["Close"].tail(50).mean()
        sma_200 = hist["Close"].tail(200).mean()
        
        # RSI calculation
        delta = hist["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not rsi.empty else None
        
        # Support and resistance
        support = hist["Low"].tail(50).min()
        resistance = hist["High"].tail(50).max()
        
        # 52-week data
        high_52w = hist["High"].max()
        low_52w = hist["Low"].min()
        
        # Fundamental metrics
        metrics = {
            "Symbol": symbol,
            "Timestamp": datetime.now().isoformat(),
            "Date": datetime.now().strftime("%Y-%m-%d"),
            
            # Price Data
            "Current_Price": current_price,
            "52W_High": high_52w,
            "52W_Low": low_52w,
            "Price_From_High": ((high_52w - current_price) / high_52w * 100),
            "Price_From_Low": ((current_price - low_52w) / low_52w * 100),
            
            # Technical Indicators
            "SMA_50": sma_50,
            "SMA_200": sma_200,
            "RSI_14": current_rsi,
            "Support_Level": support,
            "Resistance_Level": resistance,
            
            # Fundamental Metrics
            "PE_Ratio": info.get("trailingPE"),
            "EPS": info.get("trailingEps"),
            "ROE": info.get("returnOnEquity"),
            "Profit_Margin": info.get("profitMargins"),
            "Debt_to_Equity": info.get("debtToEquity"),
            "Dividend_Yield": info.get("dividendYield"),
            "Free_Cash_Flow": info.get("freeCashflow"),
            
            # Company Info
            "Market_Cap": info.get("marketCap"),
            "Company_Name": info.get("longName"),
            "Sector": info.get("sector"),
            "Industry": info.get("industry"),
        }
        
        return metrics
    except Exception as e:
        print(f"Error fetching metrics for {symbol}: {e}")
        return None

def save_daily_metrics(metrics_list):
    """Save metrics to CSV"""
    if not metrics_list:
        print("No metrics to save")
        return
    
    df = pd.DataFrame(metrics_list)
    
    # Save to current daily file
    daily_file = os.path.join(DATA_DIR, "latest_metrics.csv")
    df.to_csv(daily_file, index=False)
    print(f"✅ Saved {len(df)} stocks to {daily_file}")
    
    # Archive with date stamp
    date_str = datetime.now().strftime("%Y-%m-%d")
    archive_file = os.path.join(ARCHIVE_DIR, f"metrics_{date_str}.csv")
    df.to_csv(archive_file, index=False)
    print(f"✅ Archived to {archive_file}")

def collect_all_metrics():
    """Main function to collect metrics for all stocks"""
    print(f"\n{'='*70}")
    print(f"Starting Daily Metrics Collection - {datetime.now()}")
    print(f"{'='*70}\n")
    
    stocks = load_stocks_list()
    if not stocks:
        print("❌ No stocks found to fetch")
        return
    
    print(f"📊 Collecting metrics for {len(stocks)} stocks...\n")
    
    metrics_list = []
    success_count = 0
    fail_count = 0
    
    for idx, symbol in enumerate(stocks, 1):
        print(f"[{idx}/{len(stocks)}] {symbol}...", end=" ")
        
        metrics = fetch_stock_metrics(symbol)
        if metrics:
            metrics_list.append(metrics)
            print("✅")
            success_count += 1
        else:
            print("❌")
            fail_count += 1
    
    print(f"\n{'='*70}")
    print(f"Results: {success_count} ✅ | {fail_count} ❌")
    print(f"{'='*70}\n")
    
    save_daily_metrics(metrics_list)
    print(f"\n✅ Daily metrics collection completed at {datetime.now()}\n")

if __name__ == "__main__":
    collect_all_metrics()
