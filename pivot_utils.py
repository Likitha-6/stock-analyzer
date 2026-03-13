"""
common/utils.py
===============
Enhanced utilities for error handling, caching, and performance.

Functions:
- safe_yfinance_fetch() - Fetch with retry logic
- get_cached_data() - Smart caching wrapper
- log_performance() - Performance monitoring
- format_error_message() - User-friendly errors
"""

import logging
import time
import functools
from typing import Any, Callable, Optional, TypeVar, Dict
from datetime import datetime, timedelta
import streamlit as st

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────
# RETRY MECHANISM
# ────────────────────────────────────────────────────────────────────

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exception_types: tuple = (Exception,)
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay between retries
        exception_types: Tuple of exceptions to catch
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exception_types as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: "
                            f"{str(e)}. Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


# ────────────────────────────────────────────────────────────────────
# SMART CACHING
# ────────────────────────────────────────────────────────────────────

class CacheManager:
    """
    Manage caching with staleness detection.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str, max_age_seconds: int = 3600) -> Optional[Any]:
        """Get cached value if not stale."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        age = (datetime.now() - entry['timestamp']).total_seconds()
        
        if age > max_age_seconds:
            logger.debug(f"Cache entry '{key}' is stale ({age}s old)")
            del self._cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any):
        """Set cache value with timestamp."""
        self._cache[key] = {
            'value': value,
            'timestamp': datetime.now()
        }
        logger.debug(f"Cached '{key}'")
    
    def clear(self, pattern: Optional[str] = None):
        """Clear cache (optionally by pattern)."""
        if pattern is None:
            self._cache.clear()
        else:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for k in keys_to_remove:
                del self._cache[k]
            logger.debug(f"Cleared {len(keys_to_remove)} cache entries matching '{pattern}'")


_cache_manager = CacheManager()


def cached_fetch(func: Callable, cache_key: str, ttl: int = 3600, **fetch_kwargs):
    """
    Fetch with caching and staleness detection.
    
    Args:
        func: Callable that fetches data
        cache_key: Unique cache key
        ttl: Time-to-live in seconds
        **fetch_kwargs: Arguments to pass to func
    
    Returns:
        Tuple of (data, age_seconds, is_fresh)
    """
    # Check cache
    cached_value = _cache_manager.get(cache_key, max_age_seconds=ttl)
    if cached_value is not None:
        return cached_value, 0, True
    
    # Fetch new data
    try:
        data = func(**fetch_kwargs)
        _cache_manager.set(cache_key, data)
        return data, 0, True
    except Exception as e:
        logger.error(f"Fetch failed for '{cache_key}': {str(e)}")
        raise


# ────────────────────────────────────────────────────────────────────
# SAFE API WRAPPERS
# ────────────────────────────────────────────────────────────────────

@retry_with_backoff(max_retries=3, initial_delay=1.0)
def safe_yfinance_fetch(ticker: str, period: str = '1y'):
    """
    Safely fetch data from yfinance with retries.
    
    Args:
        ticker: Stock ticker (with or without .NS suffix)
        period: Period to fetch
    
    Returns:
        DataFrame or None on failure
    """
    import yfinance as yf
    
    # Ensure .NS suffix for NSE
    if not ticker.endswith('.NS') and '.' not in ticker:
        ticker = f"{ticker}.NS"
    
    data = yf.download(ticker, period=period, progress=False)
    
    if data is None or len(data) == 0:
        raise ValueError(f"No data returned for {ticker}")
    
    return data


def fetch_with_fallback(
    ticker: str,
    primary_fetch: Callable = None,
    fallback_fetch: Callable = None,
    **kwargs
) -> Optional[Any]:
    """
    Try primary fetch, fallback to secondary.
    
    Args:
        ticker: Stock ticker
        primary_fetch: Primary fetch function
        fallback_fetch: Fallback function if primary fails
        **kwargs: Additional arguments
    
    Returns:
        Data or None
    """
    if primary_fetch is None:
        primary_fetch = safe_yfinance_fetch
    
    try:
        return primary_fetch(ticker, **kwargs)
    except Exception as e:
        logger.warning(f"Primary fetch failed for {ticker}: {str(e)}")
        
        if fallback_fetch is not None:
            try:
                return fallback_fetch(ticker, **kwargs)
            except Exception as e2:
                logger.error(f"Fallback also failed: {str(e2)}")
        
        return None


# ────────────────────────────────────────────────────────────────────
# ERROR FORMATTING
# ────────────────────────────────────────────────────────────────────

def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format exception into user-friendly message.
    
    Args:
        error: Exception object
        context: Additional context
    
    Returns:
        Formatted error message
    """
    error_str = str(error).lower()
    
    if 'rate' in error_str:
        return f"📊 Data service limit reached. Please try again in a few moments."
    elif 'no data' in error_str or 'not found' in error_str:
        return f"❌ Could not find data for {context}. Please check the symbol."
    elif 'timeout' in error_str:
        return f"⏱️ Request timed out. Please try again."
    elif 'connection' in error_str:
        return f"🌐 Network error. Please check your internet connection."
    else:
        return f"⚠️ An error occurred{f' while {context}' if context else ''}. Please try again."


def log_performance(func: Callable) -> Callable:
    """
    Decorator to log function execution time.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        logger.debug(f"{func.__name__} took {duration:.2f}s")
        
        if duration > 5.0:
            logger.warning(
                f"{func.__name__} is slow ({duration:.2f}s). "
                "Consider optimizing or caching."
            )
        
        return result
    
    return wrapper


# ────────────────────────────────────────────────────────────────────
# STREAMLIT INTEGRATION
# ────────────────────────────────────────────────────────────────────

def show_data_freshness(timestamp: datetime, container=None):
    """
    Display data freshness indicator.
    
    Args:
        timestamp: When data was last updated
        container: Streamlit container (st if None)
    """
    if container is None:
        container = st
    
    age = datetime.now() - timestamp
    
    if age.total_seconds() < 300:  # Less than 5 min
        badge = '🟢 Fresh'
        color = '#00c882'
    elif age.total_seconds() < 3600:  # Less than 1 hour
        badge = '🟡 Recent'
        color = '#ffa500'
    else:
        badge = '🔴 Stale'
        color = '#ff4d6a'
    
    age_str = f"{age.seconds // 3600}h {(age.seconds % 3600) // 60}m ago"
    
    container.markdown(
        f'<div style="font-size:0.7rem;color:{color};">{badge} • {age_str}</div>',
        unsafe_allow_html=True
    )


def show_spinner_adaptive(message: str, long_operation: bool = False):
    """
    Show spinner with adaptive messaging.
    
    Args:
        message: Base message
        long_operation: True if operation likely > 2 seconds
    """
    with st.spinner(message + (' (this may take a moment)' if long_operation else '')):
        pass


# ────────────────────────────────────────────────────────────────────
# PERFORMANCE MONITORING
# ────────────────────────────────────────────────────────────────────

class PerformanceTracker:
    """Track performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
    
    def record(self, metric_name: str, value: float):
        """Record a metric value."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
    
    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {}
        
        vals = self.metrics[metric_name]
        return {
            'min': min(vals),
            'max': max(vals),
            'avg': sum(vals) / len(vals),
            'count': len(vals),
        }
    
    def log_report(self):
        """Log all metrics."""
        for metric, values in self.metrics.items():
            stats = self.get_stats(metric)
            logger.info(
                f"{metric}: {stats['count']} samples, "
                f"avg={stats['avg']:.2f}s, "
                f"min={stats['min']:.2f}s, "
                f"max={stats['max']:.2f}s"
            )


_perf_tracker = PerformanceTracker()
