#!/usr/bin/env python3
"""
Test script for Yahoo Finance fallback functionality
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data.data_fetcher import DataFetcher
from signals.technical_indicators import TechnicalIndicators
from config.settings import TARGET_SYMBOLS

def test_yfinance_fallback():
    """Test Yahoo Finance fallback functionality"""
    print("🚀 Testing Yahoo Finance Fallback System")
    print("=" * 50)
    
    # Initialize data fetcher (should default to yfinance)
    print("📊 Initializing Data Fetcher...")
    data_fetcher = DataFetcher(use_schwab=False, use_alpaca=False)
    
    # Check data source
    data_source = data_fetcher.get_data_source()
    data_source_info = data_fetcher.get_data_source_info()
    
    print(f"✅ Data Source: {data_source_info['name']}")
    print(f"📋 Description: {data_source_info['description']}")
    print(f"🔧 Status: {data_source_info['status']}")
    print(f"⚠️  Limitations: {data_source_info['limitations']}")
    print()
    
    # Test stock data fetching
    print("📈 Testing Stock Data Fetching...")
    test_symbols = TARGET_SYMBOLS[:3]  # Test first 3 symbols
    
    for symbol in test_symbols:
        print(f"\n🔍 Testing {symbol}...")
        
        try:
            # Get stock data
            data = data_fetcher.get_stock_data(symbol, "1m", "1d")
            
            if data is not None and not data.empty:
                print(f"  ✅ Data retrieved: {len(data)} bars")
                print(f"  📊 Latest price: ${data['Close'].iloc[-1]:.2f}")
                print(f"  📈 Volume: {data['Volume'].iloc[-1]:,}")
                print(f"  🕒 Latest timestamp: {data.index[-1]}")
            else:
                print(f"  ❌ No data retrieved for {symbol}")
                
        except Exception as e:
            print(f"  ❌ Error fetching data for {symbol}: {e}")
    
    # Test real-time quotes
    print(f"\n💹 Testing Real-time Quotes...")
    
    for symbol in test_symbols:
        try:
            quote = data_fetcher.get_real_time_quote(symbol)
            
            if quote:
                print(f"  ✅ {symbol}: ${quote['price']:.2f} ({quote['change_percent']:+.2f}%)")
                print(f"     Volume: {quote['volume']:,} | Market Cap: ${quote['market_cap']:,.0f}")
            else:
                print(f"  ❌ No quote data for {symbol}")
                
        except Exception as e:
            print(f"  ❌ Error fetching quote for {symbol}: {e}")
    
    # Test technical indicators
    print(f"\n📊 Testing Technical Indicators...")
    
    try:
        indicators = TechnicalIndicators()
        
        # Get data for one symbol
        symbol = test_symbols[0]
        data = data_fetcher.get_stock_data(symbol, "1m", "1d")
        
        if data is not None and not data.empty:
            print(f"  🔍 Calculating indicators for {symbol}...")
            
            # Calculate all indicators
            all_indicators = indicators.calculate_all_indicators(data)
            
            if all_indicators:
                print(f"  ✅ Indicators calculated successfully")
                print(f"  📈 RSI: {all_indicators.get('rsi', pd.Series()).iloc[-1] if 'rsi' in all_indicators and not all_indicators['rsi'].empty else 'N/A'}")
                print(f"  📊 MACD: {'Available' if 'macd' in all_indicators else 'N/A'}")
                print(f"  📉 VWAP: {'Available' if 'vwap' in all_indicators else 'N/A'}")
            else:
                print(f"  ❌ No indicators calculated")
        else:
            print(f"  ❌ No data available for indicator calculation")
            
    except Exception as e:
        print(f"  ❌ Error calculating indicators: {e}")
    
    # Test stock ranking
    print(f"\n🏆 Testing Stock Ranking...")
    
    try:
        stock_data = {}
        indicators_data = {}
        current_prices = {}
        
        for symbol in test_symbols:
            data = data_fetcher.get_stock_data(symbol, "1m", "1d")
            if data is not None and not data.empty:
                stock_data[symbol] = data
                current_prices[symbol] = data['Close'].iloc[-1]
                
                # Calculate indicators
                indicators_calc = indicators.calculate_all_indicators(data)
                indicators_data[symbol] = indicators_calc
        
        if stock_data and indicators_data and current_prices:
            # Rank stocks
            rankings = indicators.rank_stocks_for_scalping(stock_data, indicators_data, current_prices)
            
            if rankings:
                print(f"  ✅ Successfully ranked {len(rankings)} stocks")
                for i, ranking in enumerate(rankings):
                    print(f"    #{i+1} {ranking['symbol']}: {ranking['overall_score']:.1f}/100 - {ranking['recommendation']}")
            else:
                print(f"  ❌ No rankings generated")
        else:
            print(f"  ❌ Insufficient data for ranking")
            
    except Exception as e:
        print(f"  ❌ Error in stock ranking: {e}")
    
    print(f"\n🎉 Yahoo Finance Fallback Test Completed!")
    print(f"📊 Data Source: {data_source_info['name']}")
    print(f"✅ Status: {data_source_info['status']}")

if __name__ == "__main__":
    test_yfinance_fallback() 