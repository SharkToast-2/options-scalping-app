#!/usr/bin/env python3
"""
Test script to check app issues
"""

import os
from dotenv import load_dotenv
from modules.data_fetcher import data_fetcher

# Load environment variables
load_dotenv(".env")

print("=== Environment Variables Test ===")
print(f"SCHWAB_CLIENT_ID: {os.getenv('SCHWAB_CLIENT_ID', 'NOT FOUND')[:10]}..." if os.getenv('SCHWAB_CLIENT_ID') else "NOT FOUND")
print(f"SCHWAB_CLIENT_SECRET: {'FOUND' if os.getenv('SCHWAB_CLIENT_SECRET') else 'NOT FOUND'}")

print("\n=== Market Status Test ===")
try:
    market_status = data_fetcher.get_market_status()
    print(f"Market Status: {market_status}")
    print(f"Is Open: {market_status['is_open']}")
    print(f"Time to Close: {market_status['time_to_close']/3600:.1f} hours")
    print(f"Time to Open: {market_status['time_to_open']/3600:.1f} hours")
except Exception as e:
    print(f"Error getting market status: {e}")

print("\n=== Data Fetcher Test ===")
try:
    metrics = data_fetcher.get_performance_metrics()
    print(f"Performance Metrics: {metrics}")
except Exception as e:
    print(f"Error getting performance metrics: {e}")
