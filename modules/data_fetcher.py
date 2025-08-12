#!/usr/bin/env python3
"""
Optimized Data Fetcher Module
Fetches minute-level market data for options scalping with enhanced performance
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings
import asyncio
import aiohttp
from functools import lru_cache
import logging

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    """Structured market data"""
    ticker: str
    price: float
    volume: int
    timestamp: datetime
    change: float
    change_pct: float
    high: float
    low: float
    open_price: float

class OptimizedDataFetcher:
    """Optimized data fetcher with caching and enhanced performance"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 60  # 1 minute cache
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0
        self.session = None
        self.lock = threading.Lock()
        
        # Performance metrics
        self.metrics = {
            'requests_made': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'avg_response_time': 0
        }
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _get_cache_key(self, ticker: str, period: str, interval: str) -> str:
        """Generate cache key"""
        return f"{ticker}_{period}_{interval}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        
        cache_time = cache_entry.get('timestamp', 0)
        current_time = time.time()
        return (current_time - cache_time) < self.cache_ttl
    
    def get_minute_data(self, ticker: str, period: str = "1d", interval: str = "1m") -> pd.DataFrame:
        """
        Get optimized minute-level data with caching
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period (default: "1d")
            interval (str): Data interval (default: "1m")
        
        Returns:
            pd.DataFrame: Minute-level OHLCV data
        """
        cache_key = self._get_cache_key(ticker, period, interval)
        
        # Check cache first
        with self.lock:
            if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
                self.metrics['cache_hits'] += 1
                logger.info(f"📊 Cache hit for {ticker}")
                return self.cache[cache_key]['data']
        
        self.metrics['cache_misses'] += 1
        start_time = time.time()
        
        try:
            self._rate_limit()
            
            # Get ticker object
            stock = yf.Ticker(ticker)
            
            # Get minute data with error handling
            data = stock.history(period=period, interval=interval, prepost=False)
            
            if data.empty:
                logger.warning(f"❌ No data available for {ticker}")
                return pd.DataFrame()
            
            # Clean and validate data
            data = self._clean_data(data)
            
            # Add calculated columns
            data = self._add_calculated_columns(data)
            
            # Cache the result
            with self.lock:
                self.cache[cache_key] = {
                    'data': data,
                    'timestamp': time.time()
                }
            
            # Update metrics
            response_time = time.time() - start_time
            self.metrics['requests_made'] += 1
            self.metrics['avg_response_time'] = (
                (self.metrics['avg_response_time'] * (self.metrics['requests_made'] - 1) + response_time) 
                / self.metrics['requests_made']
            )
            
            logger.info(f"✅ Fetched {len(data)} minutes of data for {ticker} in {response_time:.2f}s")
            return data
            
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"❌ Error fetching data for {ticker}: {e}")
            return pd.DataFrame()
    
    def get_real_time_price(self, ticker: str) -> float:
        """
        Get optimized real-time price with caching
        
        Args:
            ticker (str): Stock ticker symbol
        
        Returns:
            float: Current price
        """
        cache_key = f"{ticker}_realtime"
        
        # Check cache first
        with self.lock:
            if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
                self.metrics['cache_hits'] += 1
                return self.cache[cache_key]['price']
        
        self.metrics['cache_misses'] += 1
        
        try:
            self._rate_limit()
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            price = info.get('regularMarketPrice', 0)
            
            if price and price > 0:
                # Cache the result
                with self.lock:
                    self.cache[cache_key] = {
                        'price': price,
                        'timestamp': time.time()
                    }
                
                self.metrics['requests_made'] += 1
                return price
            else:
                logger.warning(f"❌ Invalid price for {ticker}: {price}")
                return 0
                
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"❌ Error getting real-time price for {ticker}: {e}")
            return 0
    
    def get_market_data_batch(self, tickers: List[str], period: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Get optimized market data for multiple tickers
        
        Args:
            tickers (list): List of ticker symbols
            period (str): Time period
        
        Returns:
            dict: Dictionary with ticker as key and data as value
        """
        data_dict = {}
        
        # Use threading for parallel requests
        threads = []
        results = {}
        
        def fetch_ticker_data(ticker):
            try:
                data = self.get_minute_data(ticker, period)
                if not data.empty:
                    results[ticker] = data
            except Exception as e:
                logger.error(f"❌ Error fetching {ticker}: {e}")
        
        # Create threads for parallel fetching
        for ticker in tickers:
            thread = threading.Thread(target=fetch_ticker_data, args=(ticker,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return results
    
    def get_comprehensive_data(self, ticker: str) -> MarketData:
        """
        Get comprehensive market data for a ticker
        
        Args:
            ticker (str): Stock ticker symbol
        
        Returns:
            MarketData: Comprehensive market data
        """
        try:
            # Get real-time price
            current_price = self.get_real_time_price(ticker)
            
            if current_price == 0:
                return None
            
            # Get historical data for additional info
            hist_data = self.get_minute_data(ticker, period="1d")
            
            if hist_data.empty:
                return MarketData(
                    ticker=ticker,
                    price=current_price,
                    volume=0,
                    timestamp=datetime.now(),
                    change=0,
                    change_pct=0,
                    high=current_price,
                    low=current_price,
                    open_price=current_price
                )
            
            # Calculate additional metrics
            prev_close = hist_data['Close'].iloc[-2] if len(hist_data) > 1 else current_price
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close > 0 else 0
            
            return MarketData(
                ticker=ticker,
                price=current_price,
                volume=hist_data['Volume'].iloc[-1] if not hist_data.empty else 0,
                timestamp=datetime.now(),
                change=change,
                change_pct=change_pct,
                high=hist_data['High'].max() if not hist_data.empty else current_price,
                low=hist_data['Low'].min() if not hist_data.empty else current_price,
                open_price=hist_data['Open'].iloc[0] if not hist_data.empty else current_price
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting comprehensive data for {ticker}: {e}")
            return None
    
    def _clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate market data"""
        if data.empty:
            return data
        
        # Remove rows with NaN values
        data = data.dropna()
        
        # Ensure all required columns exist
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in data.columns:
                data[col] = 0
        
        # Remove outliers (prices that are too far from the mean)
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in data.columns:
                mean_price = data[col].mean()
                std_price = data[col].std()
                
                # Remove prices that are more than 5 standard deviations from mean
                data = data[abs(data[col] - mean_price) <= 5 * std_price]
        
        # Ensure volume is positive
        if 'Volume' in data.columns:
            data = data[data['Volume'] >= 0]
        
        return data
    
    def _add_calculated_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add calculated columns to the data"""
        if data.empty:
            return data
        
        # Add timestamp column
        data['timestamp'] = data.index
        
        # Add price change columns
        data['price_change'] = data['Close'].diff()
        data['price_change_pct'] = data['Close'].pct_change() * 100
        
        # Add volume change
        data['volume_change'] = data['Volume'].diff()
        data['volume_change_pct'] = data['Volume'].pct_change() * 100
        
        # Add volatility (True Range)
        data['true_range'] = np.maximum(
            data['High'] - data['Low'],
            np.maximum(
                abs(data['High'] - data['Close'].shift(1)),
                abs(data['Low'] - data['Close'].shift(1))
            )
        )
        
        # Add price position within day's range
        data['price_position'] = (data['Close'] - data['Low']) / (data['High'] - data['Low'])
        
        return data
    
    def get_market_status(self) -> Dict:
        """Get current market status"""
        try:
            now = datetime.now()
            
            # Check if it's a weekday (Monday = 0, Sunday = 6)
            is_weekday = now.weekday() < 5
            
            if not is_weekday:
                # Weekend - market is closed
                return {
                    'is_open': False,
                    'current_time': now,
                    'market_open': None,
                    'market_close': None,
                    'time_to_open': 0,
                    'time_to_close': 0
                }
            
            # US Market hours: 9:30 AM - 4:00 PM ET
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            
            # Check if market is currently open
            is_open = market_open <= now <= market_close
            
            if is_open:
                # Market is open
                time_to_close = (market_close - now).total_seconds()
                return {
                    'is_open': True,
                    'current_time': now,
                    'market_open': market_open,
                    'market_close': market_close,
                    'time_to_open': 0,
                    'time_to_close': time_to_close
                }
            else:
                # Market is closed - calculate time to next open
                if now < market_open:
                    # Before market opens today
                    time_to_open = (market_open - now).total_seconds()
                else:
                    # After market closes - next open is tomorrow
                    tomorrow = now + timedelta(days=1)
                    next_open = tomorrow.replace(hour=9, minute=30, second=0, microsecond=0)
                    time_to_open = (next_open - now).total_seconds()
                
                return {
                    'is_open': False,
                    'current_time': now,
                    'market_open': market_open,
                    'market_close': market_close,
                    'time_to_open': time_to_open,
                    'time_to_close': 0
                }
            
        except Exception as e:
            logger.error(f"❌ Error getting market status: {e}")
            return {'is_open': False, 'current_time': datetime.now()}
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        return {
            'requests_made': self.metrics['requests_made'],
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'cache_hit_rate': self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses']) if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0 else 0,
            'errors': self.metrics['errors'],
            'avg_response_time': self.metrics['avg_response_time'],
            'cache_size': len(self.cache)
        }
    
    def clear_cache(self):
        """Clear the cache"""
        with self.lock:
            self.cache.clear()
        logger.info("🗑️ Cache cleared")
    
    def optimize_cache(self, max_size: int = 1000):
        """Optimize cache by removing oldest entries"""
        with self.lock:
            if len(self.cache) > max_size:
                # Remove oldest entries
                sorted_cache = sorted(self.cache.items(), key=lambda x: x[1]['timestamp'])
                entries_to_remove = len(self.cache) - max_size
                
                for i in range(entries_to_remove):
                    del self.cache[sorted_cache[i][0]]
                
                logger.info(f"🗑️ Removed {entries_to_remove} old cache entries")

# Global instance for backward compatibility
data_fetcher = OptimizedDataFetcher()

def get_minute_data(ticker, period="1d"):
    """Backward compatibility function"""
    return data_fetcher.get_minute_data(ticker, period)

def get_real_time_price(ticker):
    """Backward compatibility function"""
    return data_fetcher.get_real_time_price(ticker)

def get_market_data_batch(tickers, period="1d"):
    """Backward compatibility function"""
    return data_fetcher.get_market_data_batch(tickers, period) 