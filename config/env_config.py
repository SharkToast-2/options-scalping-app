#!/usr/bin/env python3
"""
Environment Configuration for Options Scalper
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Schwab API Configuration
SCHWAB_CLIENT_ID = os.getenv('SCHWAB_CLIENT_ID')
SCHWAB_CLIENT_SECRET = os.getenv('SCHWAB_CLIENT_SECRET')
SCHWAB_REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI', 'http://localhost:8501/callback')

# Schwab Trading API
SCHWAB_TRADING_KEY = os.getenv('SCHWAB_TRADING_KEY')
SCHWAB_TRADING_SECRET = os.getenv('SCHWAB_TRADING_SECRET')

# Schwab Market Data API
SCHWAB_MARKET_DATA_KEY = os.getenv('SCHWAB_MARKET_DATA_KEY')
SCHWAB_MARKET_DATA_SECRET = os.getenv('SCHWAB_MARKET_DATA_SECRET')

# Other API Keys
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY', '')

# Schwab URLs
SCHWAB_AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
SCHWAB_CLIENT_LOGIN = "https://client.schwab.com/Areas/Access/Login"
SCHWAB_ACCOUNT_SUMMARY = "https://client.schwab.com/app/accounts/positions/#/"

def get_schwab_auth_url():
    """Generate Schwab authorization URL"""
    params = {
        'response_type': 'code',
        'client_id': SCHWAB_CLIENT_ID,
        'scope': 'readonly',
        'redirect_uri': SCHWAB_REDIRECT_URI
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"{SCHWAB_AUTH_URL}?{query_string}"

def get_config():
    """Get complete configuration dictionary"""
    return {
        'schwab_client_id': SCHWAB_CLIENT_ID,
        'schwab_client_secret': SCHWAB_CLIENT_SECRET,
        'schwab_redirect_uri': SCHWAB_REDIRECT_URI,
        'schwab_trading_key': SCHWAB_TRADING_KEY,
        'schwab_trading_secret': SCHWAB_TRADING_SECRET,
        'schwab_market_data_key': SCHWAB_MARKET_DATA_KEY,
        'schwab_market_data_secret': SCHWAB_MARKET_DATA_SECRET,
        'polygon_api_key': POLYGON_API_KEY,
        'schwab_auth_url': get_schwab_auth_url(),
        'schwab_token_url': SCHWAB_TOKEN_URL,
        'schwab_client_login': SCHWAB_CLIENT_LOGIN,
        'schwab_account_summary': SCHWAB_ACCOUNT_SUMMARY
    } 