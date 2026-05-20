"""
NSE Data Module - Get Indian stock data from NSE API (NO RATE LIMITS)
This module provides current prices and quotes from NSE without rate limiting
"""

import streamlit as st
import pandas as pd

@st.cache_data(ttl=60 * 60)  # Cache for 1 hour
def get_nse_quote(symbol):
    """
    Get current price and data from NSE API
    NO RATE LIMITS - completely free and reliable for Indian stocks
    
    Args:
        symbol: Stock symbol (e.g., 'TCS', 'INFY', 'RELIANCE')
    
    Returns:
        dict with: price, high52w, low52w, volume, or None if failed
    """
    try:
        from nse_india import NSEClient
        
        nse = NSEClient()
        quote = nse.get_quote(symbol)
        
        return {
            'price': quote.get('lastPrice'),
            'high52w': quote.get('high52w'),
            'low52w': quote.get('low52w'),
            'volume': quote.get('totalTradedVolume'),
            'pe': quote.get('pe'),
            'eps': quote.get('eps'),
            'market_cap': quote.get('marketCap'),
        }
    except Exception as e:
        print(f"⚠️  NSE API Error for {symbol}: {str(e)[:50]}")
        return None

@st.cache_data(ttl=60 * 60 * 24)  # Cache for 24 hours
def get_nse_fundamentals(symbol):
    """
    Get fundamental data from NSE
    
    Returns:
        dict with financial metrics or None if failed
    """
    try:
        from nse_india import NSEClient
        
        nse = NSEClient()
        data = nse.get_quote(symbol)
        
        return {
            'pe_ratio': data.get('pe'),
            'eps': data.get('eps'),
            'roe': data.get('roe'),
            'dividend_yield': data.get('dividendYield'),
            'market_cap': data.get('marketCap'),
        }
    except Exception as e:
        print(f"⚠️  NSE Fundamentals Error for {symbol}: {str(e)[:50]}")
        return None

def is_nse_api_available():
    """Check if NSE API is installed and available"""
    try:
        from nse_india import NSEClient
        return True
    except ImportError:
        return False
