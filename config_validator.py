#!/usr/bin/env python3
"""
Secure Configuration Validator
Validates all security settings and configurations
"""

import os
import json
import re
from pathlib import Path
from cryptography.fernet import Fernet

class ConfigValidator:
    def __init__(self):
        self.project_root = Path.cwd()
        self.config_dir = self.project_root / "config"
        self.secure_config_file = self.config_dir / "secure_config.json"
        self.encryption_key_file = self.config_dir / ".secret_key"
        self.env_file = self.project_root / ".env"
        
    def validate_all(self):
        """Run all validation checks"""
        print("🔍 Secure Configuration Validation")
        print("=" * 50)
        
        results = {
            "encryption": self.validate_encryption(),
            "api_keys": self.validate_api_keys(),
            "file_permissions": self.validate_file_permissions(),
            "environment": self.validate_environment(),
            "git_security": self.validate_git_security(),
            "dependencies": self.validate_dependencies()
        }
        
        self.print_results(results)
        return results
    
    def validate_encryption(self):
        """Validate encryption setup"""
        checks = {
            "key_exists": False,
            "key_permissions": False,
            "config_exists": False,
            "config_permissions": False,
            "config_encrypted": False
        }
        
        # Check encryption key
        if self.encryption_key_file.exists():
            checks["key_exists"] = True
            try:
                stat = self.encryption_key_file.stat()
                checks["key_permissions"] = (stat.st_mode & 0o777) == 0o600
            except Exception:
                pass
        
        # Check secure config
        if self.secure_config_file.exists():
            checks["config_exists"] = True
            try:
                stat = self.secure_config_file.stat()
                checks["config_permissions"] = (stat.st_mode & 0o777) == 0o600
                
                # Check if config is encrypted
                with open(self.secure_config_file, 'r') as f:
                    config = json.load(f)
                checks["config_encrypted"] = config.get("metadata", {}).get("encrypted", False)
            except Exception:
                pass
        
        return checks
    
    def validate_api_keys(self):
        """Validate API key configuration"""
        checks = {
            "env_file_exists": False,
            "env_permissions": False,
            "client_id_set": False,
            "client_secret_set": False,
            "keys_valid_format": False
        }
        
        # Check .env file
        if self.env_file.exists():
            checks["env_file_exists"] = True
            try:
                stat = self.env_file.stat()
                checks["env_permissions"] = (stat.st_mode & 0o777) == 0o600
                
                # Check API keys
                with open(self.env_file, 'r') as f:
                    content = f.read()
                
                checks["client_id_set"] = "SCHWAB_CLIENT_ID=" in content
                checks["client_secret_set"] = "SCHWAB_CLIENT_SECRET=" in content
                
                # Validate key format
                client_id_match = re.search(r'SCHWAB_CLIENT_ID=([A-Za-z0-9]+)', content)
                if client_id_match:
                    client_id = client_id_match.group(1)
                    checks["keys_valid_format"] = len(client_id) >= 20
                    
            except Exception:
                pass
        
        return checks
    
    def validate_file_permissions(self):
        """Validate file permissions"""
        checks = {
            "config_dir_secure": False,
            "logs_dir_secure": False,
            "no_world_writable": True
        }
        
        # Check config directory
        try:
            stat = self.config_dir.stat()
            checks["config_dir_secure"] = (stat.st_mode & 0o777) <= 0o750
        except Exception:
            pass
        
        # Check logs directory
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            try:
                stat = logs_dir.stat()
                checks["logs_dir_secure"] = (stat.st_mode & 0o777) <= 0o750
            except Exception:
                pass
        
        # Check for world-writable files
        sensitive_files = [".env", "config/secure_config.json", "config/.secret_key"]
        for file_path in sensitive_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    stat = full_path.stat()
                    if (stat.st_mode & 0o002) != 0:  # World writable
                        checks["no_world_writable"] = False
                except Exception:
                    pass
        
        return checks
    
    def validate_environment(self):
        """Validate environment settings"""
        checks = {
            "debug_disabled": True,
            "log_level_secure": True,
            "no_sensitive_env_vars": True
        }
        
        # Check debug mode
        if os.getenv("DEBUG", "False").lower() == "true":
            checks["debug_disabled"] = False
        
        # Check log level
        log_level = os.getenv("LOG_LEVEL", "INFO")
        if log_level.upper() == "DEBUG":
            checks["log_level_secure"] = False
        
        # Check for sensitive environment variables
        sensitive_vars = ["PASSWORD", "SECRET", "KEY", "TOKEN"]
        for var in os.environ:
            if any(sensitive in var.upper() for sensitive in sensitive_vars):
                if not var.startswith("SCHWAB_"):  # Allow Schwab-specific vars
                    checks["no_sensitive_env_vars"] = False
        
        return checks
    
    def validate_git_security(self):
        """Validate Git security"""
        checks = {
            "gitignore_updated": False,
            "no_sensitive_committed": True,
            "git_repo_exists": False
        }
        
        # Check if Git repository exists
        git_dir = self.project_root / ".git"
        checks["git_repo_exists"] = git_dir.exists()
        
        if checks["git_repo_exists"]:
            # Check .gitignore
            gitignore_file = self.project_root / ".gitignore"
            if gitignore_file.exists():
                with open(gitignore_file, 'r') as f:
                    content = f.read()
                checks["gitignore_updated"] = all(pattern in content for pattern in [
                    ".env", "secure_config.json", ".secret_key"
                ])
            
            # Check for sensitive files in Git
            import subprocess
            try:
                result = subprocess.run(
                    ["git", "ls-files"],
                    capture_output=True, text=True, cwd=self.project_root
                )
                if result.returncode == 0:
                    files = result.stdout.strip().split('\n')
                    sensitive_patterns = [".env", ".key", "secret", "credential"]
                    for file_path in files:
                        if any(pattern in file_path for pattern in sensitive_patterns):
                            checks["no_sensitive_committed"] = False
                            break
            except Exception:
                pass
        
        return checks
    
    def validate_dependencies(self):
        """Validate dependencies"""
        checks = {
            "requirements_exists": False,
            "no_vulnerable_packages": True,
            "cryptography_installed": False
        }
        
        # Check requirements.txt
        requirements_file = self.project_root / "requirements.txt"
        checks["requirements_exists"] = requirements_file.exists()
        
        if checks["requirements_exists"]:
            with open(requirements_file, 'r') as f:
                content = f.read()
            
            # Check for vulnerable packages
            vulnerable_packages = [
                "cryptography<3.4",
                "requests<2.25.0",
                "urllib3<1.26.0"
            ]
            
            for vuln_pkg in vulnerable_packages:
                if vuln_pkg in content:
                    checks["no_vulnerable_packages"] = False
            
            # Check for cryptography
            checks["cryptography_installed"] = "cryptography" in content
        
        return checks
    
    def print_results(self, results):
        """Print validation results"""
        print("\n📊 Validation Results:")
        print("=" * 30)
        
        total_checks = 0
        passed_checks = 0
        
        for category, checks in results.items():
            print(f"\n🔍 {category.replace('_', ' ').title()}:")
            for check, status in checks.items():
                total_checks += 1
                if status:
                    passed_checks += 1
                icon = "✅" if status else "❌"
                print(f"  {icon} {check.replace('_', ' ').title()}")
        
        # Calculate score
        score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        print(f"\n📈 Overall Score: {score:.1f}%")
        
        if score >= 90:
            print("🎉 Excellent security configuration!")
        elif score >= 75:
            print("✅ Good security configuration")
        elif score >= 50:
            print("⚠️ Security improvements needed")
        else:
            print("❌ Critical security issues found")
        
        # Save detailed report
        report = {
            "timestamp": str(Path().cwd()),
            "score": score,
            "results": results
        }
        
        report_file = self.project_root / "logs" / "config_validation_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

def main():
    """Main function"""
    validator = ConfigValidator()
    results = validator.validate_all()
    
    # Exit with error code if score is too low
    score = results.get("score", 0)
    if score < 50:
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main() 