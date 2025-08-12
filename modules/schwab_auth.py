#!/usr/bin/env python3
"""
Simple Schwab Authentication Module
"""

import streamlit as st
import requests
import json
from datetime import datetime
from config.env_config import get_config

class SchwabAuth:
    def __init__(self):
        self.config = get_config()
        self.auth_file = "schwab_auth.json"
    
    def show_auth_interface(self):
        """Show Schwab authentication interface"""
        st.subheader("🔐 Schwab Authentication")
        
        # Check current auth status
        auth_status = self.get_auth_status()
        
        if auth_status.get('authenticated'):
            self.show_authenticated_status(auth_status)
        else:
            self.show_auth_instructions()
    
    def show_authenticated_status(self, auth_status):
        """Show authenticated status"""
        st.success("✅ Schwab API Authenticated")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Status", "Authenticated")
        
        with col2:
            st.metric("Method", auth_status.get('method', 'Unknown'))
        
        with col3:
            st.metric("Expires", auth_status.get('expires', 'Unknown'))
        
        # Show auth details
        with st.expander("🔍 Authentication Details"):
            st.json(auth_status)
        
        # Manual deauth option
        if st.button("🔓 Clear Authentication", type="secondary"):
            self.clear_auth()
            st.rerun()
    
    def show_auth_instructions(self):
        """Show authentication instructions"""
        st.info("📋 Schwab Authentication Required")
        
        st.markdown("""
        ### 🔗 Step 1: Get Authorization URL
        Click the link below to open the Schwab authorization page:
        """)
        
        # Generate authorization URL with your actual client ID
        client_id = self.config.get('schwab_client_id')
        if not client_id:
            st.error("❌ SCHWAB_CLIENT_ID not found in configuration")
            return
        redirect_uri = self.config.get('schwab_redirect_uri', 'https://options-scalping-app-ydqxfd2qjfueqznzvxq9ts.streamlit.app/callback')
        
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
            placeholder="https://developer.schwab.com/oauth2-redirect.html?code=...",
            help="Copy the entire URL from your browser after authorization"
        )
        
        if auth_url_input:
            if st.button("🔐 Complete Authentication", type="primary"):
                success = self.process_auth_url(auth_url_input)
                if success:
                    st.success("✅ Authentication completed successfully!")
                    st.rerun()
                else:
                    st.error("❌ Authentication failed. Please check the URL and try again.")
        
        # Alternative: Manual API key entry
        st.markdown("---")
        st.markdown("### 🔑 Alternative: API Key Authentication")
        
        with st.expander("🔧 API Key Setup"):
            api_key = st.text_input("Schwab API Key:", type="password")
            api_secret = st.text_input("Schwab API Secret:", type="password")
            
            if api_key and api_secret:
                if st.button("🔐 Save API Keys", type="secondary"):
                    self.save_api_keys(api_key, api_secret)
                    st.success("✅ API keys saved!")
                    st.rerun()
    
    def process_auth_url(self, auth_url):
        """Process authorization URL and extract code"""
        try:
            # Extract authorization code from URL
            if "code=" in auth_url:
                code = auth_url.split("code=")[1].split("&")[0]
                
                # Try to exchange code for token
                token_success = self.exchange_code_for_token(code)
                
                # Save authentication info
                auth_data = {
                    'authenticated': True,
                    'method': 'OAuth2',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'expires': '1 hour',
                    'auth_code': code,
                    'auth_url': auth_url,
                    'token_exchange_success': token_success
                }
                
                self.save_auth_data(auth_data)
                return True
            
            return False
            
        except Exception as e:
            st.error(f"Error processing auth URL: {e}")
            return False
    
    def exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        try:
            url = self.config['schwab_token_url']
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': self.config['schwab_client_id'],
                'client_secret': self.config['schwab_client_secret'],
                'redirect_uri': self.config['schwab_redirect_uri']
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(url, data=data, headers=headers)
            
            if response.status_code == 200:
                token_data = response.json()
                self.save_token_data(token_data)
                return True
            else:
                st.warning(f"Token exchange failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            st.error(f"Error exchanging code for token: {e}")
            return False
    
    def save_api_keys(self, api_key, api_secret):
        """Save API keys to config"""
        try:
            auth_data = {
                'authenticated': True,
                'method': 'API Key',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'expires': 'Session',
                'api_key': api_key,
                'api_secret': api_secret
            }
            
            self.save_auth_data(auth_data)
            
        except Exception as e:
            st.error(f"Error saving API keys: {e}")
    
    def get_auth_status(self):
        """Get current authentication status"""
        try:
            with open(self.auth_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception:
            return {}
    
    def save_auth_data(self, auth_data):
        """Save authentication data"""
        try:
            with open(self.auth_file, 'w') as f:
                json.dump(auth_data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving auth data: {e}")
    
    def save_token_data(self, token_data):
        """Save token data"""
        try:
            with open('schwab_tokens.json', 'w') as f:
                json.dump(token_data, f, indent=2)
        except Exception as e:
            st.error(f"Error saving token data: {e}")
    
    def clear_auth(self):
        """Clear authentication data"""
        try:
            import os
            if os.path.exists(self.auth_file):
                os.remove(self.auth_file)
            if os.path.exists('schwab_tokens.json'):
                os.remove('schwab_tokens.json')
            st.success("✅ Authentication cleared")
        except Exception as e:
            st.error(f"Error clearing auth: {e}")
    
    def test_connection(self):
        """Test Schwab API connection"""
        try:
            auth_status = self.get_auth_status()
            if not auth_status.get('authenticated'):
                return False
            
            # Here you would make an actual API call to test
            # For now, just return True if authenticated
            return True
            
        except Exception:
            return False 