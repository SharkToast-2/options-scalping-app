#!/usr/bin/env python3
"""
Trade Executor Module
Handles trade execution and management
"""

import json
import os
import requests
from datetime import datetime
from modules.data_fetcher import get_real_time_price

# Global variables for trade management
active_trade = False
open_trades = []
daily_pnl = 0.0
total_trades = 0
token_data = None  # Store OAuth token data

# Global variables for trade management
active_trade = False
open_trades = []
daily_pnl = 0.0
total_trades = 0

def execute_trade(contract, trade_size):
    """
    Execute a trade with Schwab OAuth
    
    Args:
        contract (str): Contract symbol
        trade_size (float): Trade size in dollars
    
    Returns:
        bool: True if trade executed successfully
    """
    global active_trade, open_trades, total_trades, token_data
    
    if active_trade:
        print("❌ Already have an active trade")
        return False
    
    # Check if we have OAuth token
    if not token_data:
        print("❌ Missing Schwab OAuth token. Please authenticate first.")
        return False
    
    try:
        # Get current price
        ticker = contract.split('_')[0]
        current_price = get_real_time_price(ticker)
        
        if current_price == 0:
            print("❌ Could not get current price")
            return False
        
        # Execute Schwab trade
        success = execute_schwab_trade(contract, trade_size)
        
        if success:
            # Create trade record
            trade = {
                'id': total_trades + 1,
                'symbol': contract,
                'entry_price': current_price,
                'current_price': current_price,
                'trade_size': trade_size,
                'entry_time': datetime.now().isoformat(),
                'status': 'open'
            }
            
            # Add to open trades
            open_trades.append(trade)
            active_trade = True
            total_trades += 1
            
            print(f"✅ Trade executed: {contract} at ${current_price:.2f}")
            print(f"   Trade size: ${trade_size}")
            
            return True
        else:
            print("❌ Schwab trade execution failed")
            return False
        
    except Exception as e:
        print(f"❌ Error executing trade: {e}")
        return False

def execute_schwab_trade(option_symbol, amount_usd):
    """
    Execute trade through Schwab API
    
    Args:
        option_symbol (str): Option symbol
        amount_usd (float): Trade amount in USD
    
    Returns:
        bool: True if trade executed successfully
    """
    global token_data
    
    if not token_data:
        print("❌ Missing Schwab token. Authenticate first.")
        return False

    account_id = os.getenv("SCHWAB_ACCOUNT_ID")  # add this to your .env
    if not account_id:
        print("❌ Missing SCHWAB_ACCOUNT_ID in environment variables")
        return False
        
    access_token = token_data.get("access_token")
    if not access_token:
        print("❌ Missing access token in token data")
        return False

    # Example logic: assume $1.50 per contract, calculate quantity
    price_per_contract = 1.50  # adjust to live data later
    quantity = int(amount_usd // (price_per_contract * 100))

    if quantity < 1:
        print("❌ Trade amount too small for minimum contract.")
        return False

    payload = {
        "orderType": "LIMIT",
        "price": str(price_per_contract),
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
                "instruction": "BUY_TO_OPEN",
                "quantity": quantity,
                "instrument": {
                    "symbol": option_symbol,
                    "assetType": "OPTION"
                }
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    url = f"https://api.schwabapi.com/v1/trading/accounts/{account_id}/orders"
    
    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 201:
            print(f"✅ Trade placed for {quantity} contracts of {option_symbol}")
            return True
        else:
            print(f"❌ Trade failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error making API request: {e}")
        return False

def close_trade(trade_id, reason="manual"):
    """
    Close a trade
    
    Args:
        trade_id (int): Trade ID to close
        reason (str): Reason for closing
    
    Returns:
        bool: True if trade closed successfully
    """
    global active_trade, open_trades, daily_pnl
    
    # Find the trade
    trade = None
    for t in open_trades:
        if t['id'] == trade_id:
            trade = t
            break
    
    if not trade:
        print(f"❌ Trade {trade_id} not found")
        return False
    
    try:
        # Get current price
        ticker = trade['symbol'].split('_')[0]
        current_price = get_real_time_price(ticker)
        
        if current_price == 0:
            print("❌ Could not get current price")
            return False
        
        # Calculate P&L
        entry_price = trade['entry_price']
        pnl = ((current_price - entry_price) / entry_price) * trade['trade_size']
        
        # Update trade
        trade['exit_price'] = current_price
        trade['exit_time'] = datetime.now().isoformat()
        trade['status'] = 'closed'
        trade['pnl'] = pnl
        trade['reason'] = reason
        
        # Update daily P&L
        daily_pnl += pnl
        
        # Remove from open trades
        open_trades = [t for t in open_trades if t['id'] != trade_id]
        
        # Update active trade status
        if not open_trades:
            active_trade = False
        
        print(f"✅ Trade closed: {trade['symbol']}")
        print(f"   Entry: ${entry_price:.2f}, Exit: ${current_price:.2f}")
        print(f"   P&L: ${pnl:.2f}")
        print(f"   Reason: {reason}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error closing trade: {e}")
        return False

def get_open_trades():
    """
    Get list of open trades
    
    Returns:
        list: List of open trades
    """
    return open_trades

def trade_active():
    """
    Check if there's an active trade
    
    Returns:
        bool: True if there's an active trade
    """
    return active_trade

def check_total_loss():
    """
    Get total daily loss
    
    Returns:
        float: Total daily P&L
    """
    return daily_pnl

def reset_daily_pnl():
    """Reset daily P&L"""
    global daily_pnl
    daily_pnl = 0.0
    print("✅ Daily P&L reset")

def get_trade_history():
    """
    Get complete trade history
    
    Returns:
        list: List of all trades (open and closed)
    """
    # In a real implementation, this would load from a database
    return open_trades

def update_trade_prices():
    """Update current prices for all open trades"""
    global open_trades
    
    for trade in open_trades:
        if trade['status'] == 'open':
            ticker = trade['symbol'].split('_')[0]
            current_price = get_real_time_price(ticker)
            if current_price > 0:
                trade['current_price'] = current_price

def set_token_data(token_info):
    """
    Set OAuth token data for Schwab API
    
    Args:
        token_info (dict): Token data from OAuth flow
    """
    global token_data
    token_data = token_info
    print("✅ OAuth token data set for Schwab API")

def get_token_data():
    """
    Get current OAuth token data
    
    Returns:
        dict: Token data or None if not authenticated
    """
    global token_data
    return token_data

def is_authenticated():
    """
    Check if Schwab OAuth is authenticated
    
    Returns:
        bool: True if authenticated
    """
    global token_data
    return token_data is not None and token_data.get("access_token") is not None 