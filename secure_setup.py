#!/usr/bin/env python3
"""
Secure Setup Script for Options Scalping Bot
Secures GitHub data and handles Schwab API key input with encryption
"""

import os
import sys
import json
import getpass
import base64
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import re
import shutil

class SecureSetup:
    def __init__(self):
        self.project_root = Path.cwd()
        self.config_dir = self.project_root / "config"
        self.logs_dir = self.project_root / "logs"
        self.secure_config_file = self.config_dir / "secure_config.json"
        self.encryption_key_file = self.config_dir / ".secret_key"
        self.env_file = self.project_root / ".env"
        
        # Create necessary directories
        self.config_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Initialize encryption
        self.cipher_suite = self._initialize_encryption()
        
    def _initialize_encryption(self):
        """Initialize or load encryption key"""
        if self.encryption_key_file.exists():
            # Load existing key
            with open(self.encryption_key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.encryption_key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self.encryption_key_file, 0o600)
            print(f"🔑 Generated new encryption key: {self.encryption_key_file}")
        
        return Fernet(key)
    
    def encrypt_value(self, value):
        """Encrypt a string value"""
        if not value:
            return ""
        return self.cipher_suite.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value):
        """Decrypt a string value"""
        if not encrypted_value:
            return ""
        try:
            return self.cipher_suite.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return ""
    
    def validate_api_key(self, api_key):
        """Validate API key format"""
        if not api_key:
            return False
        
        # Check length and format
        if len(api_key) < 20:
            return False
        
        # Check for common patterns
        if re.match(r'^[A-Za-z0-9_-]+$', api_key):
            return True
        
        return False
    
    def secure_github_data(self):
        """Secure GitHub repository data"""
        print("\n🔒 Securing GitHub Data")
        print("=" * 40)
        
        # Check for existing .git directory
        git_dir = self.project_root / ".git"
        if not git_dir.exists():
            print("❌ No Git repository found. Please initialize Git first:")
            print("   git init")
            print("   git add .")
            print("   git commit -m 'Initial commit'")
            return False
        
        # Update .gitignore
        self._update_gitignore()
        
        # Check for sensitive files
        sensitive_files = [
            ".env",
            "config/.env",
            "config/secure_config.json",
            "config/.secret_key",
            "*.key",
            "*.pem",
            "secrets.json",
            "credentials.json",
            "api_keys.txt"
        ]
        
        print("\n🔍 Checking for sensitive files...")
        found_sensitive = []
        
        for pattern in sensitive_files:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    found_sensitive.append(str(file_path))
                    print(f"⚠️  Found sensitive file: {file_path}")
        
        if found_sensitive:
            print(f"\n⚠️  Found {len(found_sensitive)} sensitive files!")
            response = input("Do you want to remove these from Git history? (y/n): ").lower()
            
            if response == 'y':
                self._remove_from_git_history(found_sensitive)
        
        # Check current Git status
        print("\n📊 Current Git Status:")
        os.system("git status --porcelain")
        
        return True
    
    def _update_gitignore(self):
        """Update .gitignore with security patterns"""
        gitignore_file = self.project_root / ".gitignore"
        
        security_patterns = [
            "# Security and sensitive files",
            ".env",
            ".env.local",
            ".env.production",
            ".env.staging",
            "config/.env",
            "config/secure_config.json",
            "config/.secret_key",
            "*.key",
            "*.pem",
            "*.p12",
            "*.pfx",
            "secrets.json",
            "credentials.json",
            "api_keys.txt",
            "schwab_tokens.json",
            "oauth_tokens.json",
            "*.token",
            "",
            "# Logs and data",
            "logs/",
            "*.log",
            "trading_log.json",
            "signal_log.json",
            "error_log.json",
            "performance_metrics_*.json",
            "stock_data.db",
            "*.sqlite",
            "*.sqlite3",
            "",
            "# Cache and temporary files",
            ".cache/",
            "*.cache",
            "*.tmp",
            "*.temp",
            "",
            "# IDE and editor files",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            "*~"
        ]
        
        if gitignore_file.exists():
            # Read existing content
            with open(gitignore_file, 'r') as f:
                existing_content = f.read()
            
            # Add new patterns if they don't exist
            new_patterns = []
            for pattern in security_patterns:
                if pattern not in existing_content:
                    new_patterns.append(pattern)
            
            if new_patterns:
                with open(gitignore_file, 'a') as f:
                    f.write('\n'.join(new_patterns))
                print(f"✅ Updated .gitignore with {len(new_patterns)} new security patterns")
        else:
            # Create new .gitignore
            with open(gitignore_file, 'w') as f:
                f.write('\n'.join(security_patterns))
            print("✅ Created new .gitignore with security patterns")
    
    def _remove_from_git_history(self, files):
        """Remove sensitive files from Git history"""
        print("\n🗑️  Removing sensitive files from Git history...")
        
        for file_path in files:
            try:
                # Remove from Git tracking
                os.system(f"git rm --cached {file_path}")
                print(f"✅ Removed {file_path} from Git tracking")
            except Exception as e:
                print(f"❌ Error removing {file_path}: {e}")
        
        # Commit the changes
        try:
            os.system('git add .gitignore')
            os.system('git commit -m "Remove sensitive files and update .gitignore"')
            print("✅ Committed security changes")
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
    
    def input_schwab_keys(self):
        """Securely input Schwab API keys"""
        print("\n🔑 Schwab API Key Setup")
        print("=" * 40)
        
        print("📋 Required Schwab API Keys:")
        print("1. Client ID (from Schwab Developer Portal)")
        print("2. Client Secret (from Schwab Developer Portal)")
        print("3. Market Data Key (if separate)")
        print("4. Market Data Secret (if separate)")
        print("5. Trading Key (if separate)")
        print("6. Trading Secret (if separate)")
        
        print("\n💡 How to get Schwab API keys:")
        print("1. Go to https://developer.schwab.com")
        print("2. Create a new application")
        print("3. Set callback URL to: http://localhost:8501/callback")
        print("4. Request scopes: trading, market_data, account_read")
        print("5. Copy the generated keys")
        
        # Get API keys from user
        api_keys = {}
        
        key_prompts = [
            ("SCHWAB_CLIENT_ID", "Schwab Client ID"),
            ("SCHWAB_CLIENT_SECRET", "Schwab Client Secret"),
            ("SCHWAB_MARKET_DATA_KEY", "Schwab Market Data Key (optional)"),
            ("SCHWAB_MARKET_DATA_SECRET", "Schwab Market Data Secret (optional)"),
            ("SCHWAB_TRADING_KEY", "Schwab Trading Key (optional)"),
            ("SCHWAB_TRADING_SECRET", "Schwab Trading Secret (optional)")
        ]
        
        for key_name, prompt in key_prompts:
            while True:
                if "SECRET" in key_name:
                    value = getpass.getpass(f"{prompt}: ")
                else:
                    value = input(f"{prompt}: ").strip()
                
                if not value:
                    if "optional" in prompt.lower():
                        break
                    else:
                        print("❌ This field is required!")
                        continue
                
                # Validate API key format
                if self.validate_api_key(value):
                    api_keys[key_name] = value
                    break
                else:
                    print("❌ Invalid API key format. Please check your key.")
                    retry = input("Try again? (y/n): ").lower()
                    if retry != 'y':
                        break
        
        # Save encrypted keys
        if api_keys:
            self._save_encrypted_keys(api_keys)
            self._create_env_file(api_keys)
            return True
        
        return False
    
    def _save_encrypted_keys(self, api_keys):
        """Save API keys in encrypted format"""
        encrypted_config = {
            "api_keys": {},
            "metadata": {
                "created": str(Path().cwd()),
                "encrypted": True,
                "version": "1.0"
            }
        }
        
        for key_name, value in api_keys.items():
            encrypted_config["api_keys"][key_name] = self.encrypt_value(value)
        
        # Save encrypted config
        with open(self.secure_config_file, 'w') as f:
            json.dump(encrypted_config, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(self.secure_config_file, 0o600)
        
        print(f"✅ Saved encrypted API keys to {self.secure_config_file}")
    
    def _create_env_file(self, api_keys):
        """Create .env file with API keys"""
        env_content = [
            "# Schwab API Configuration",
            "# This file contains your API keys - DO NOT COMMIT TO GIT",
            ""
        ]
        
        for key_name, value in api_keys.items():
            env_content.append(f"{key_name}={value}")
        
        env_content.extend([
            "",
            "# Application Settings",
            "DEBUG=False",
            "LOG_LEVEL=INFO",
            "STREAMLIT_SERVER_PORT=8501",
            "STREAMLIT_SERVER_ADDRESS=localhost"
        ])
        
        with open(self.env_file, 'w') as f:
            f.write('\n'.join(env_content))
        
        # Set restrictive permissions
        os.chmod(self.env_file, 0o600)
        
        print(f"✅ Created .env file with API keys")
    
    def validate_setup(self):
        """Validate the secure setup"""
        print("\n🔍 Security Validation")
        print("=" * 40)
        
        validation_results = {
            "encryption_key_exists": self.encryption_key_file.exists(),
            "encryption_key_secure": False,
            "secure_config_exists": self.secure_config_file.exists(),
            "secure_config_secure": False,
            "env_file_exists": self.env_file.exists(),
            "env_file_secure": False,
            "gitignore_updated": False,
            "sensitive_files_ignored": False
        }
        
        # Check file permissions
        if validation_results["encryption_key_exists"]:
            stat = os.stat(self.encryption_key_file)
            validation_results["encryption_key_secure"] = (stat.st_mode & 0o777) == 0o600
        
        if validation_results["secure_config_exists"]:
            stat = os.stat(self.secure_config_file)
            validation_results["secure_config_secure"] = (stat.st_mode & 0o777) == 0o600
        
        if validation_results["env_file_exists"]:
            stat = os.stat(self.env_file)
            validation_results["env_file_secure"] = (stat.st_mode & 0o777) == 0o600
        
        # Check .gitignore
        gitignore_file = self.project_root / ".gitignore"
        if gitignore_file.exists():
            with open(gitignore_file, 'r') as f:
                content = f.read()
                validation_results["gitignore_updated"] = ".env" in content
                validation_results["sensitive_files_ignored"] = "secure_config.json" in content
        
        # Display results
        for check, status in validation_results.items():
            icon = "✅" if status else "❌"
            print(f"{icon} {check.replace('_', ' ').title()}")
        
        # Security score
        score = sum(validation_results.values()) / len(validation_results) * 100
        print(f"\n📊 Security Score: {score:.1f}%")
        
        if score >= 80:
            print("🎉 Excellent security setup!")
        elif score >= 60:
            print("⚠️  Good security setup, but room for improvement")
        else:
            print("❌ Security setup needs attention")
        
        return validation_results
    
    def run_setup(self):
        """Run the complete secure setup"""
        print("🔒 Options Scalping Bot - Secure Setup")
        print("=" * 50)
        print("This script will help you:")
        print("1. Secure your GitHub repository data")
        print("2. Input and encrypt Schwab API keys")
        print("3. Validate security settings")
        print("=" * 50)
        
        # Step 1: Secure GitHub data
        if not self.secure_github_data():
            print("❌ Failed to secure GitHub data")
            return False
        
        # Step 2: Input Schwab keys
        if not self.input_schwab_keys():
            print("❌ Failed to input Schwab keys")
            return False
        
        # Step 3: Validate setup
        validation_results = self.validate_setup()
        
        # Step 4: Final recommendations
        print("\n💡 Security Recommendations:")
        print("1. ✅ Never commit .env or secure_config.json to Git")
        print("2. ✅ Use environment variables in production")
        print("3. ✅ Regularly rotate your API keys")
        print("4. ✅ Enable 2FA on your Schwab account")
        print("5. ✅ Monitor API usage regularly")
        print("6. ✅ Use a dedicated trading account with limited funds")
        
        print("\n🚀 Setup Complete!")
        print("You can now run your bot with:")
        print("   streamlit run app.py")
        
        return True

def main():
    """Main function"""
    try:
        setup = SecureSetup()
        setup.run_setup()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 