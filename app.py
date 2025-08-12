#!/usr/bin/env python3
"""
Options Scalping Bot - Main Application (Simple Version)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
import threading
import asyncio
from typing import Dict, List, Optional, Tuple
import json
import os
from dotenv import load_dotenv

# Import optimized modules
from modules.data_fetcher import data_fetcher, get_minute_data, get_real_time_price
from modules.indicators import indicators_calculator, calc_indicators
from modules.signal_engine import signal_engine, check_signals, should_buy, should_sell
from modules.trade_executor import execute_trade, check_total_loss, get_open_trades, trade_active
from modules.risk_manager import check_exit_conditions
from modules.logger import log_trade, get_trade_history
from modules.schwab_auth import SchwabAuth

# Load environment variables
load_dotenv(".env")

# Page configuration
st.set_page_config(
    page_title="🚀 Optimized Options Scalping Bot",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-metric {
        border-left-color: #28a745;
    }
    .warning-metric {
        border-left-color: #ffc107;
    }
    .danger-metric {
        border-left-color: #dc3545;
    }
    .stAlert {
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

class OptimizedScalpingBot:
    """Optimized options scalping bot with enhanced features"""
    
    def __init__(self):
        self.trade_history = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_drawdown': 0.0
        }
        self.session_state = st.session_state
        
        # Initialize session state
        if 'bot_running' not in self.session_state:
            self.session_state.bot_running = False
        if 'trade_history' not in self.session_state:
            self.session_state.trade_history = []
        if 'performance_data' not in self.session_state:
            self.session_state.performance_data = []
    
    def run(self):
        """Main application runner"""
        # Header
        st.markdown('<h1 class="main-header">🚀 Optimized Options Scalping Bot</h1>', unsafe_allow_html=True)
        
        # Sidebar configuration
        self.setup_sidebar()
        
        # Show OAuth interface (always visible)
        st.markdown("---")
        st.subheader("🔐 Schwab OAuth Authentication")
        self.show_simple_oauth_interface()
        
        st.markdown("---")
        
        # Main content
        if self.session_state.bot_running:
            self.run_trading_session()
        else:
            self.show_dashboard()
    
    def setup_sidebar(self):
        """Setup sidebar configuration"""
        st.sidebar.header("⚙️ Bot Configuration")
        
        # Trading parameters
        st.sidebar.subheader("📊 Trading Parameters")
        TICKER = st.sidebar.text_input("Stock Ticker", value="META", help="Enter the stock ticker to trade")
        TRADE_SIZE = st.sidebar.slider("Max Price Per Trade ($)", min_value=100, max_value=2000, value=500, step=50)
        DAILY_LIMIT = st.sidebar.slider("Max Daily Loss ($)", min_value=100, max_value=2000, value=500, step=50)
        PROFIT_TARGET = st.sidebar.slider("Profit % Target", min_value=1, max_value=15, value=3, step=1)
        STOP_LOSS = st.sidebar.slider("Stop Loss %", min_value=1, max_value=10, value=3, step=1)
        
        # Advanced parameters
        st.sidebar.subheader("🔧 Advanced Settings")
        MIN_SIGNAL_STRENGTH = st.sidebar.slider("Min Signal Strength", min_value=40, max_value=90, value=60, step=5)
        MAX_TRADE_DURATION = st.sidebar.slider("Max Trade Duration (min)", min_value=1, max_value=10, value=3, step=1)
        ENABLE_TRAILING_STOP = st.sidebar.checkbox("Enable Trailing Stop", value=True)
        TRAILING_STOP_PCT = st.sidebar.slider("Trailing Stop %", min_value=1, max_value=5, value=2, step=1) if ENABLE_TRAILING_STOP else 2
        
        # Risk management
        st.sidebar.subheader("🛡️ Risk Management")
        MAX_CONCURRENT_TRADES = st.sidebar.slider("Max Concurrent Trades", min_value=1, max_value=5, value=1, step=1)
        ENABLE_CORRELATION_CHECK = st.sidebar.checkbox("Enable Correlation Check", value=True)
        MIN_VOLUME_RATIO = st.sidebar.slider("Min Volume Ratio", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
        
        # Performance monitoring
        st.sidebar.subheader("📈 Performance")
        if st.sidebar.button("📊 View Performance Metrics"):
            self.show_performance_metrics()
        
        if st.sidebar.button("🗑️ Clear Trade History"):
            self.clear_trade_history()
        
        # Schwab Authentication
        st.sidebar.subheader("🔐 Schwab Authentication")
        self.show_simple_oauth_sidebar()
        
        # Bot control
        st.sidebar.subheader("🎮 Bot Control")
        running = st.sidebar.toggle("🚀 Start Bot", key="bot_toggle")
        
        if running:
            self.session_state.bot_running = True
            st.sidebar.success("✅ Bot is running")
        else:
            self.session_state.bot_running = False
            st.sidebar.info("⏸️ Bot is paused")
        
        # Store configuration
        self.config = {
            'TICKER': TICKER,
            'TRADE_SIZE': TRADE_SIZE,
            'DAILY_LIMIT': DAILY_LIMIT,
            'PROFIT_TARGET': PROFIT_TARGET,
            'STOP_LOSS': STOP_LOSS,
            'MIN_SIGNAL_STRENGTH': MIN_SIGNAL_STRENGTH,
            'MAX_TRADE_DURATION': MAX_TRADE_DURATION,
            'ENABLE_TRAILING_STOP': ENABLE_TRAILING_STOP,
            'TRAILING_STOP_PCT': TRAILING_STOP_PCT,
            'MAX_CONCURRENT_TRADES': MAX_CONCURRENT_TRADES,
            'ENABLE_CORRELATION_CHECK': ENABLE_CORRELATION_CHECK,
            'MIN_VOLUME_RATIO': MIN_VOLUME_RATIO
        }
    
    def run_trading_session(self):
        """Run the trading session"""
        # Status indicators
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            self.show_market_status()
        
        with col2:
            self.show_bot_status()
        
        with col3:
            self.show_current_trades()
        
        with col4:
            self.show_daily_pnl()
        
        # Main trading area
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔐 OAuth Setup", "📈 Live Trading", "📊 Technical Analysis", "📋 Trade History", "🎯 Performance"])
        
        with tab1:
            self.show_oauth_setup()
        
        with tab2:
            self.show_live_trading()
        
        with tab3:
            self.show_technical_analysis()
        
        with tab4:
            self.show_trade_history()
        
        with tab5:
            self.show_performance_analysis()
    
    def show_dashboard(self):
        """Show the main dashboard when bot is not running"""
        st.info("🎯 Welcome to the Optimized Options Scalping Bot! Configure your settings in the sidebar and start trading.")
        
        # Market overview
        st.subheader("📊 Market Overview")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            self.show_market_status()
        
        with col2:
            self.show_data_fetcher_metrics()
        
        with col3:
            self.show_signal_engine_metrics()
        
        # Quick analysis
        if st.button("🔍 Quick Market Analysis"):
            self.perform_quick_analysis()
    
    def show_market_status(self):
        """Display market status"""
        market_status = data_fetcher.get_market_status()
        
        if market_status['is_open']:
            st.metric("Market Status", "🟢 OPEN", delta=f"Closes in {market_status['time_to_close']/3600:.1f}h")
        else:
            st.metric("Market Status", "🔴 CLOSED", delta=f"Opens in {market_status['time_to_open']/3600:.1f}h")
    
    def show_bot_status(self):
        """Display bot status"""
        if self.session_state.bot_running:
            st.metric("Bot Status", "🟢 RUNNING", delta="Active")
        else:
            st.metric("Bot Status", "🔴 STOPPED", delta="Inactive")
    
    def show_current_trades(self):
        """Display current trades"""
        open_trades = get_open_trades()
        st.metric("Open Trades", len(open_trades), delta="Active positions")
    
    def show_daily_pnl(self):
        """Display daily P&L"""
        daily_pnl = check_total_loss()
        color = "normal"
        if daily_pnl > 0:
            color = "inverse"
        elif daily_pnl < -self.config['DAILY_LIMIT'] * 0.8:
            color = "off"
        
        st.metric("Daily P&L", f"${daily_pnl:.2f}", delta_color=color)
    
    def show_data_fetcher_metrics(self):
        """Display data fetcher performance metrics"""
        metrics = data_fetcher.get_performance_metrics()
        
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Cache Hit Rate", f"{metrics['cache_hit_rate']:.1%}")
        st.metric("Avg Response Time", f"{metrics['avg_response_time']:.2f}s")
        st.metric("Total Requests", metrics['requests_made'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    def show_signal_engine_metrics(self):
        """Display signal engine performance metrics"""
        metrics = signal_engine.performance_metrics
        
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Signals", metrics['total_signals'])
        st.metric("Success Rate", f"{metrics['successful_signals']/max(metrics['total_signals'], 1)*100:.1f}%")
        st.metric("False Positives", metrics['false_positives'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    def show_live_trading(self):
        """Show live trading interface"""
        # Real-time data
        ticker = self.config['TICKER']
        
        # Get current data
        df = get_minute_data(ticker)
        if df.empty:
            st.error(f"❌ No data available for {ticker}")
            return
        
        # Calculate indicators
        indicators = calc_indicators(df)
        signals = check_signals(indicators)
        
        # Display current price and signals
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_price = indicators.get('current_price', 0)
            st.metric("Current Price", f"${current_price:.2f}")
        
        with col2:
            signal_strength = signal_engine.get_signal_strength(indicators)
            st.metric("Signal Strength", f"{signal_strength}/100")
        
        with col3:
            positive_signals = sum(signals.values())
            st.metric("Positive Signals", f"{positive_signals}/{len(signals)}")
        
        # Signal breakdown
        st.subheader("📊 Signal Analysis")
        signal_cols = st.columns(len(signals))
        
        for i, (signal_name, signal_value) in enumerate(signals.items()):
            with signal_cols[i]:
                color = "🟢" if signal_value else "🔴"
                st.metric(signal_name.replace('_', ' ').title(), color, delta="Active" if signal_value else "Inactive")
        
        # Trading decision
        st.subheader("🎯 Trading Decision")
        
        should_buy_signal = should_buy(indicators, self.config['MIN_SIGNAL_STRENGTH'])
        buy_confidence = signal_engine.get_signal_confidence(indicators)
        
        if should_buy_signal and not trade_active():
            st.success(f"✅ BUY SIGNAL - Confidence: {buy_confidence:.1%}")
            
            if st.button("🚀 Execute Trade"):
                self.execute_trade(ticker, indicators)
        elif trade_active():
            st.warning("⚠️ Trade already active")
        else:
            st.info("⏳ Waiting for buy signal...")
        
        # Live chart
        self.plot_live_chart(df, indicators)
    
    def show_technical_analysis(self):
        """Show technical analysis"""
        ticker = self.config['TICKER']
        df = get_minute_data(ticker)
        
        if df.empty:
            st.error(f"❌ No data available for {ticker}")
            return
        
        indicators = calc_indicators(df)
        
        # Technical indicators display
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Price Indicators")
            st.metric("RSI", f"{indicators.get('rsi', 0):.1f}")
            st.metric("MACD", f"{indicators.get('macd', 0):.4f}")
            st.metric("Volume Ratio", f"{indicators.get('volume_ratio', 0):.2f}")
            st.metric("ATR", f"{indicators.get('atr', 0):.4f}")
        
        with col2:
            st.subheader("📊 Trend Indicators")
            st.metric("SMA 20", f"${indicators.get('sma_20', 0):.2f}")
            st.metric("SMA 50", f"${indicators.get('sma_50', 0):.2f}")
            st.metric("VWAP", f"${indicators.get('vwap', 0):.2f}")
            st.metric("BB Width", f"{indicators.get('bb_width', 0):.4f}")
        
        # Advanced indicators
        st.subheader("🔬 Advanced Indicators")
        adv_col1, adv_col2, adv_col3 = st.columns(3)
        
        with adv_col1:
            st.metric("Williams %R", f"{indicators.get('williams_r', 0):.1f}")
            st.metric("CCI", f"{indicators.get('cci', 0):.1f}")
        
        with adv_col2:
            st.metric("MFI", f"{indicators.get('mfi', 0):.1f}")
            st.metric("ADX", f"{indicators.get('adx', 0):.1f}")
        
        with adv_col3:
            st.metric("Stoch RSI K", f"{indicators.get('stoch_rsi_k', 0):.1f}")
            st.metric("Stoch RSI D", f"{indicators.get('stoch_rsi_d', 0):.1f}")
        
        # Pattern detection
        st.subheader("🎯 Pattern Detection")
        pattern_col1, pattern_col2, pattern_col3 = st.columns(3)
        
        with pattern_col1:
            st.metric("Doji", "✅" if indicators.get('doji', False) else "❌")
            st.metric("Hammer", "✅" if indicators.get('hammer', False) else "❌")
        
        with pattern_col2:
            st.metric("Engulfing", "✅" if indicators.get('engulfing', False) else "❌")
            st.metric("RSI Divergence", indicators.get('rsi_divergence', 'none').title())
        
        with pattern_col3:
            volume_profile = indicators.get('volume_profile', {})
            st.metric("Volume Heavy", "✅" if volume_profile.get('volume_heavy', False) else "❌")
            st.metric("Volume Light", "✅" if volume_profile.get('volume_light', False) else "❌")
    
    def show_trade_history(self):
        """Show trade history"""
        try:
            trades = get_trade_history(50)
            
            if not trades:
                st.info("📋 No trades recorded yet")
                return
            
            # Convert to DataFrame for better display
            df_trades = pd.DataFrame(trades)
            
            # Display trade summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Trades", len(trades))
            
            with col2:
                # Filter trades with valid P&L data
                trades_with_pnl = [t for t in trades if t.get('pnl') is not None]
                winning_trades = len([t for t in trades_with_pnl if t.get('pnl', 0) > 0])
                st.metric("Winning Trades", winning_trades)
            
            with col3:
                total_pnl = sum([t.get('pnl', 0) or 0 for t in trades])
                st.metric("Total P&L", f"${total_pnl:.2f}")
            
            with col4:
                win_rate = winning_trades / len(trades_with_pnl) * 100 if trades_with_pnl else 0
                st.metric("Win Rate", f"{win_rate:.1f}%")
            
            # Trade table
            st.subheader("📋 Recent Trades")
            if not df_trades.empty:
                # Format the DataFrame for display
                display_df = df_trades.copy()
                if 'timestamp' in display_df.columns:
                    display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                if 'pnl' in display_df.columns:
                    display_df['pnl'] = display_df['pnl'].apply(lambda x: f"${x:.2f}" if pd.notna(x) and x is not None else "N/A")
                
                st.dataframe(display_df, use_container_width=True)
                
        except Exception as e:
            st.error(f"❌ Error displaying trade history: {e}")
            st.info("📋 Trade history display error - this is normal for new installations")
    
    def show_performance_analysis(self):
        """Show performance analysis"""
        try:
            trades = get_trade_history(100)
            
            if not trades:
                st.info("📊 No performance data available yet")
                return
            
            # Calculate performance metrics
            self.calculate_performance_metrics(trades)
            
            # Performance overview
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total P&L", f"${self.performance_metrics['total_pnl']:.2f}")
            
            with col2:
                st.metric("Win Rate", f"{self.performance_metrics['win_rate']:.1f}%")
            
            with col3:
                st.metric("Avg Win", f"${self.performance_metrics['avg_win']:.2f}")
            
            with col4:
                st.metric("Avg Loss", f"${self.performance_metrics['avg_loss']:.2f}")
            
            # Performance charts
            self.plot_performance_charts(trades)
            
        except Exception as e:
            st.error(f"❌ Error displaying performance analysis: {e}")
            st.info("📊 Performance analysis error - this is normal for new installations")
    
    def calculate_performance_metrics(self, trades):
        """Calculate performance metrics"""
        if not trades:
            return
        
        # Filter trades with valid P&L data
        trades_with_pnl = [t for t in trades if t.get('pnl') is not None]
        winning_trades = [t for t in trades_with_pnl if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades_with_pnl if t.get('pnl', 0) < 0]
        
        self.performance_metrics['total_trades'] = len(trades)
        self.performance_metrics['winning_trades'] = len(winning_trades)
        self.performance_metrics['losing_trades'] = len(losing_trades)
        self.performance_metrics['total_pnl'] = sum([t.get('pnl', 0) or 0 for t in trades])
        self.performance_metrics['win_rate'] = len(winning_trades) / len(trades_with_pnl) * 100 if trades_with_pnl else 0
        self.performance_metrics['avg_win'] = sum([t.get('pnl', 0) for t in winning_trades]) / len(winning_trades) if winning_trades else 0
        self.performance_metrics['avg_loss'] = sum([t.get('pnl', 0) for t in losing_trades]) / len(losing_trades) if losing_trades else 0
    
    def plot_performance_charts(self, trades):
        """Plot performance charts"""
        if not trades:
            return
        
        df_trades = pd.DataFrame(trades)
        df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'])
        df_trades = df_trades.sort_values('timestamp')
        
        # Cumulative P&L chart
        fig1 = go.Figure()
        df_trades['cumulative_pnl'] = df_trades['pnl'].cumsum()
        fig1.add_trace(go.Scatter(x=df_trades['timestamp'], y=df_trades['cumulative_pnl'], 
                                 mode='lines+markers', name='Cumulative P&L'))
        fig1.update_layout(title="Cumulative P&L Over Time", xaxis_title="Time", yaxis_title="P&L ($)")
        st.plotly_chart(fig1, use_container_width=True)
        
        # P&L distribution
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=df_trades['pnl'], nbinsx=20, name='P&L Distribution'))
        fig2.update_layout(title="P&L Distribution", xaxis_title="P&L ($)", yaxis_title="Frequency")
        st.plotly_chart(fig2, use_container_width=True)
    
    def plot_live_chart(self, df, indicators):
        """Plot live trading chart"""
        if df.empty:
            return
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Price & Bollinger Bands', 'Volume', 'RSI'),
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # Price chart with Bollinger Bands
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Price', line=dict(color='blue')), row=1, col=1)
        
        if 'bb_upper' in indicators and 'bb_lower' in indicators:
            fig.add_trace(go.Scatter(x=df.index, y=[indicators['bb_upper']] * len(df), 
                                   mode='lines', name='BB Upper', line=dict(color='red', dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=[indicators['bb_lower']] * len(df), 
                                   mode='lines', name='BB Lower', line=dict(color='red', dash='dash')), row=1, col=1)
        
        # Volume chart
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='lightblue'), row=2, col=1)
        
        # RSI chart
        rsi_values = [indicators.get('rsi', 50)] * len(df)
        fig.add_trace(go.Scatter(x=df.index, y=rsi_values, mode='lines', name='RSI', line=dict(color='purple')), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        fig.update_layout(height=600, showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    
    def execute_trade(self, ticker, indicators):
        """Execute a trade"""
        try:
            contract = f"{ticker}_OPTION_CALL"
            success = execute_trade(contract, self.config['TRADE_SIZE'])
            
            if success:
                current_price = indicators.get('current_price', 0)
                log_trade(ticker, contract, "BUY", current_price, self.config['TRADE_SIZE'])
                
                # Add to trade history
                trade_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'ticker': ticker,
                    'action': 'BUY',
                    'price': current_price,
                    'size': self.config['TRADE_SIZE']
                }
                self.session_state.trade_history.append(trade_entry)
                
                st.success(f"✅ Trade executed: {ticker} at ${current_price:.2f}")
            else:
                st.error("❌ Trade execution failed")
                
        except Exception as e:
            st.error(f"❌ Error executing trade: {e}")
    
    def perform_quick_analysis(self):
        """Perform quick market analysis"""
        ticker = self.config['TICKER']
        
        with st.spinner("🔍 Analyzing market..."):
            # Get data
            df = get_minute_data(ticker)
            if df.empty:
                st.error(f"❌ No data available for {ticker}")
                return
            
            # Calculate indicators
            indicators = calc_indicators(df)
            signals = check_signals(indicators)
            
            # Display analysis
            st.subheader(f"📊 Quick Analysis for {ticker}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Current Price", f"${indicators.get('current_price', 0):.2f}")
                st.metric("RSI", f"{indicators.get('rsi', 0):.1f}")
                st.metric("MACD", f"{indicators.get('macd', 0):.4f}")
                st.metric("Volume Ratio", f"{indicators.get('volume_ratio', 0):.2f}")
            
            with col2:
                signal_strength = signal_engine.get_signal_strength(indicators)
                st.metric("Signal Strength", f"{signal_strength}/100")
                
                positive_signals = sum(signals.values())
                st.metric("Positive Signals", f"{positive_signals}/{len(signals)}")
                
                confidence = signal_engine.get_signal_confidence(indicators)
                st.metric("Confidence", f"{confidence:.1%}")
            
            # Recommendation
            if should_buy(indicators, self.config['MIN_SIGNAL_STRENGTH']):
                st.success("🎯 RECOMMENDATION: BUY - Strong signals detected")
            else:
                st.info("⏳ RECOMMENDATION: WAIT - Insufficient signals")
    
    def clear_trade_history(self):
        """Clear trade history"""
        self.session_state.trade_history = []
        st.success("🗑️ Trade history cleared")
    
    def show_oauth_setup(self):
        """Show OAuth setup interface"""
        st.subheader("🔐 Schwab OAuth Authentication")
        self.show_simple_oauth_interface()
    
    def show_simple_oauth_interface(self):
        """Show simple OAuth interface as fallback"""
        st.info("📋 Schwab Authentication Required")
        
        st.markdown("""
        ### 🔗 Step 1: Get Authorization URL
        Click the link below to open the Schwab authorization page:
        """)
        
        # Generate authorization URL with your actual client ID
        client_id = os.getenv("SCHWAB_CLIENT_ID")
        if not client_id:
            st.error("❌ SCHWAB_CLIENT_ID not found in environment variables")
            return
        redirect_uri = "https://options-scalping-app-ydqxfd2qjfueqznzvxq9ts.streamlit.app/callback"
        
        auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?response_type=code&client_id={client_id}&scope=trading%20market_data%20account_read&redirect_uri={redirect_uri}&state=options_scalper"
        
        st.code(auth_url, language="text")
        
        # Clickable link
        st.markdown(f"[🌐 **Click here to open Schwab Authorization Page**]({auth_url})")
        
        st.markdown("""
        ### 📝 Step 2: Complete Authorization
        1. **Sign in** to your Schwab account
        2. **Authorize** the application
        3. **Copy the entire URL** you're redirected to
        """)
        
        # Input for authorization code
        st.markdown("### 📋 Step 3: Paste Authorization URL")
        
        auth_url_input = st.text_input(
            "Paste the complete URL you were redirected to:",
            placeholder="https://options-scalping-app-ydqxfd2qjfueqznzvxq9ts.streamlit.app/callback?code=...",
            help="Copy the entire URL from your browser after authorization"
        )
        
        if auth_url_input:
            if st.button("🔐 Complete Authentication", type="primary"):
                success = self.process_oauth_callback(auth_url_input)
                if success:
                    st.success("✅ Authentication completed successfully!")
                    st.rerun()
                else:
                    st.error("❌ Authentication failed. Please check the URL and try again.")
    
    def show_simple_oauth_sidebar(self):
        """Show simple OAuth interface in sidebar"""
        st.sidebar.info("📋 Schwab Auth Required - Cloud Updated")
        
        # Generate authorization URL
        client_id = os.getenv("SCHWAB_CLIENT_ID")
        if not client_id:
            st.sidebar.error("❌ SCHWAB_CLIENT_ID not found")
            return
        redirect_uri = "https://options-scalping-app-ydqxfd2qjfueqznzvxq9ts.streamlit.app/callback"
        
        auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?response_type=code&client_id={client_id}&scope=trading%20market_data%20account_read&redirect_uri={redirect_uri}&state=options_scalper"
        
        st.sidebar.markdown(f"[🌐 **Open Schwab Auth**]({auth_url})")
        
        auth_url_input = st.sidebar.text_input(
            "Paste redirect URL:",
            placeholder="https://...",
            help="Paste the URL after authorization"
        )
        
        if auth_url_input:
            if st.sidebar.button("🔐 Authenticate"):
                success = self.process_oauth_callback(auth_url_input)
                if success:
                    st.sidebar.success("✅ Authentication successful!")
                else:
                    st.sidebar.error("❌ Authentication failed!")
    
    def process_oauth_callback(self, redirect_url):
        """
        Process OAuth callback URL and exchange code for token
        
        Args:
            redirect_url (str): The redirect URL from Schwab
            
        Returns:
            bool: True if authentication successful
        """
        try:
            # Extract authorization code from URL
            if 'code=' not in redirect_url:
                st.error("❌ No authorization code found in URL")
                return False
            
            # Parse the URL to get the authorization code
            code_start = redirect_url.find('code=') + 5
            code_end = redirect_url.find('&', code_start)
            if code_end == -1:
                code_end = len(redirect_url)
            
            auth_code = redirect_url[code_start:code_end]
            
            # Exchange code for token
            token_data = self.exchange_code_for_token(auth_code)
            
            if token_data:
                # Store token data in trade executor
                from modules.trade_executor import set_token_data
                set_token_data(token_data)
                
                # Store in session state
                st.session_state.schwab_authenticated = True
                st.session_state.token_data = token_data
                
                return True
            else:
                return False
                
        except Exception as e:
            st.error(f"❌ Error processing OAuth callback: {e}")
            return False
    
    def exchange_code_for_token(self, auth_code):
        """
        Exchange authorization code for access token
        
        Args:
            auth_code (str): Authorization code from OAuth flow
            
        Returns:
            dict: Token data or None if failed
        """
        try:
            import requests
            
            # Schwab OAuth token endpoint
            token_url = "https://api.schwabapi.com/v1/oauth/token"
            
            # Your OAuth credentials
            client_id = os.getenv("SCHWAB_CLIENT_ID")
            client_secret = os.getenv("SCHWAB_CLIENT_SECRET")
            if not client_id or not client_secret:
                print("❌ Missing OAuth credentials in environment variables")
                return None
            redirect_uri = "https://options-scalping-app-ydqxfd2qjfueqznzvxq9ts.streamlit.app/callback"
            
            # Token request payload
            payload = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': redirect_uri,
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            # Make token request
            response = requests.post(token_url, data=payload)
            
            if response.status_code == 200:
                token_data = response.json()
                print("✅ OAuth token exchange successful")
                return token_data
            else:
                print(f"❌ Token exchange failed: {response.status_code}")
                print(response.text)
                return None
                
        except Exception as e:
            print(f"❌ Error exchanging code for token: {e}")
            return None
    
    def show_performance_metrics(self):
        """Show detailed performance metrics"""
        st.subheader("📈 Detailed Performance Metrics")
        
        # Data fetcher metrics
        st.write("**Data Fetcher Performance:**")
        df_metrics = data_fetcher.get_performance_metrics()
        st.json(df_metrics)
        
        # Signal engine metrics
        st.write("**Signal Engine Performance:**")
        se_metrics = signal_engine.performance_metrics
        st.json(se_metrics)

# Initialize and run the bot
if __name__ == "__main__":
    bot = OptimizedScalpingBot()
    bot.run() 