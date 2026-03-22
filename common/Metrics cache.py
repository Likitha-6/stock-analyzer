"""
Metrics Cache Module
====================
Reads pre-collected daily metrics from CSV files.
Eliminates API calls during the day - super fast!
"""

import pandas as pd
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = "data/daily_metrics"
LATEST_METRICS_FILE = os.path.join(DATA_DIR, "latest_metrics.csv")

def load_latest_metrics():
    """Load today's cached metrics"""
    try:
        if os.path.exists(LATEST_METRICS_FILE):
            df = pd.read_csv(LATEST_METRICS_FILE)
            return df
        else:
            return None
    except Exception as e:
        print(f"Error loading cached metrics: {e}")
        return None

def get_stock_metrics(symbol):
    """Get all metrics for a specific stock"""
    try:
        df = load_latest_metrics()
        if df is not None:
            stock_data = df[df['Symbol'] == symbol]
            if not stock_data.empty:
                return stock_data.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"Error getting metrics for {symbol}: {e}")
        return None

def get_all_stocks_metrics():
    """Get metrics for all stocks"""
    try:
        df = load_latest_metrics()
        if df is not None:
            return df.to_dict('records')
        return []
    except Exception as e:
        print(f"Error getting all metrics: {e}")
        return []

def get_metric_by_symbol(symbol, metric_name):
    """Get specific metric for a stock"""
    try:
        metrics = get_stock_metrics(symbol)
        if metrics and metric_name in metrics:
            return metrics[metric_name]
        return None
    except Exception as e:
        print(f"Error getting {metric_name} for {symbol}: {e}")
        return None

def get_last_update_time():
    """Get when metrics were last collected"""
    try:
        df = load_latest_metrics()
        if df is not None and 'Timestamp' in df.columns:
            return df['Timestamp'].iloc[0]
        return None
    except Exception as e:
        print(f"Error getting update time: {e}")
        return None

def get_stocks_by_metric(metric_name, ascending=False):
    """Get all stocks sorted by a metric"""
    try:
        df = load_latest_metrics()
        if df is not None and metric_name in df.columns:
            # Drop NaN values and sort
            return df.dropna(subset=[metric_name]).sort_values(
                metric_name, ascending=ascending
            ).to_dict('records')
        return []
    except Exception as e:
        print(f"Error sorting by {metric_name}: {e}")
        return []

def get_top_performers(metric_name, n=10):
    """Get top N stocks by metric"""
    stocks = get_stocks_by_metric(metric_name, ascending=False)
    return stocks[:n]

def get_bottom_performers(metric_name, n=10):
    """Get bottom N stocks by metric"""
    stocks = get_stocks_by_metric(metric_name, ascending=True)
    return stocks[:n]

def filter_stocks(criteria):
    """Filter stocks by criteria
    
    Example:
    criteria = {
        'PE_Ratio': (0, 30),  # PE between 0 and 30
        'ROE': (0.15, 1.0),   # ROE between 15% and 100%
        'Dividend_Yield': (0.02, 1.0)  # Yield between 2% and 100%
    }
    """
    try:
        df = load_latest_metrics()
        if df is None:
            return []
        
        for metric, (min_val, max_val) in criteria.items():
            if metric in df.columns:
                df = df[(df[metric] >= min_val) & (df[metric] <= max_val)]
        
        return df.to_dict('records')
    except Exception as e:
        print(f"Error filtering stocks: {e}")
        return []

def get_technical_signal(symbol):
    """Get technical trading signal for a stock"""
    try:
        metrics = get_stock_metrics(symbol)
        if not metrics:
            return None
        
        current_price = metrics.get('Current_Price')
        sma_50 = metrics.get('SMA_50')
        sma_200 = metrics.get('SMA_200')
        rsi = metrics.get('RSI_14')
        support = metrics.get('Support_Level')
        resistance = metrics.get('Resistance_Level')
        
        signal = {
            'symbol': symbol,
            'price': current_price,
            'signals': []
        }
        
        # Moving average signals
        if sma_50 and sma_200:
            if sma_50 > sma_200:
                signal['signals'].append('SMA 50 > SMA 200 (Uptrend)')
            else:
                signal['signals'].append('SMA 50 < SMA 200 (Downtrend)')
        
        # RSI signals
        if rsi:
            if rsi > 70:
                signal['signals'].append(f'RSI {rsi:.1f} (Overbought)')
            elif rsi < 30:
                signal['signals'].append(f'RSI {rsi:.1f} (Oversold)')
            else:
                signal['signals'].append(f'RSI {rsi:.1f} (Neutral)')
        
        # Support/Resistance signals
        if support and resistance and current_price:
            if current_price < support:
                signal['signals'].append(f'Price below support ({support:.2f})')
            elif current_price > resistance:
                signal['signals'].append(f'Price above resistance ({resistance:.2f})')
            else:
                signal['signals'].append(f'Price between support & resistance')
        
        return signal
    except Exception as e:
        print(f"Error getting signal for {symbol}: {e}")
        return None

def get_fundamental_quality_score(symbol):
    """Score stock quality (1-10) based on fundamentals"""
    try:
        metrics = get_stock_metrics(symbol)
        if not metrics:
            return None
        
        score = 0
        max_score = 0
        
        # PE Ratio (lower is better, but not too low)
        pe = metrics.get('PE_Ratio')
        if pe and 10 < pe < 50:
            score += 2
            max_score += 2
        elif pe:
            max_score += 2
        
        # ROE (higher is better)
        roe = metrics.get('ROE')
        if roe and roe > 0.15:
            score += 2
            max_score += 2
        elif roe:
            max_score += 2
        
        # Profit Margin (higher is better)
        pm = metrics.get('Profit_Margin')
        if pm and pm > 0.10:
            score += 2
            max_score += 2
        elif pm:
            max_score += 2
        
        # Debt to Equity (lower is better)
        de = metrics.get('Debt_to_Equity')
        if de and de < 1.0:
            score += 2
            max_score += 2
        elif de:
            max_score += 2
        
        # Dividend Yield (should have some)
        div = metrics.get('Dividend_Yield')
        if div and div > 0:
            score += 2
            max_score += 2
        elif div:
            max_score += 2
        
        quality_score = (score / max_score * 10) if max_score > 0 else 0
        return round(quality_score, 1)
    except Exception as e:
        print(f"Error calculating quality for {symbol}: {e}")
        return None

def metrics_are_fresh(hours_threshold=24):
    """Check if cached metrics are fresh (updated within X hours)"""
    try:
        last_update = get_last_update_time()
        if last_update is None:
            return False
        
        last_update_dt = pd.to_datetime(last_update)
        hours_old = (datetime.now() - last_update_dt).total_seconds() / 3600
        
        return hours_old < hours_threshold
    except Exception as e:
        print(f"Error checking freshness: {e}")
        return False
