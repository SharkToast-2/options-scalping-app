#!/usr/bin/env python3
"""
Security Audit Script for Options Scalping Bot
Verifies security setup and checks for vulnerabilities
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
import subprocess

class SecurityAudit:
    def __init__(self):
        self.project_root = Path.cwd()
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0,
            "checks": {},
            "recommendations": [],
            "critical_issues": [],
            "warnings": []
        }
        
    def run_full_audit(self):
        """Run complete security audit"""
        print("🔒 Security Audit - Options Scalping Bot")
        print("=" * 50)
        
        # Run all security checks
        self._check_file_permissions()
        self._check_sensitive_files()
        self._check_git_security()
        self._check_encryption_setup()
        self._check_api_key_security()
        self._check_environment_security()
        self._check_dependencies()
        self._check_code_security()
        
        # Calculate overall score
        self._calculate_score()
        
        # Generate report
        self._generate_report()
        
        return self.audit_results
    
    def _check_file_permissions(self):
        """Check file permissions for security"""
        print("\n📁 Checking file permissions...")
        
        critical_files = [
            ".env",
            "config/secure_config.json",
            "config/.secret_key",
            "logs/",
            "*.log"
        ]
        
        permission_issues = []
        
        for pattern in critical_files:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        mode = stat.st_mode & 0o777
                        
                        if mode != 0o600:
                            permission_issues.append({
                                "file": str(file_path),
                                "current_mode": oct(mode),
                                "expected_mode": "0o600"
                            })
                    except Exception as e:
                        permission_issues.append({
                            "file": str(file_path),
                            "error": str(e)
                        })
        
        self.audit_results["checks"]["file_permissions"] = {
            "status": len(permission_issues) == 0,
            "issues": permission_issues,
            "score": max(0, 100 - len(permission_issues) * 20)
        }
        
        if permission_issues:
            self.audit_results["warnings"].extend([
                f"File permission issue: {issue['file']}" for issue in permission_issues
            ])
    
    def _check_sensitive_files(self):
        """Check for sensitive files in repository"""
        print("🔍 Checking for sensitive files...")
        
        sensitive_patterns = [
            "*.key",
            "*.pem",
            "*.p12",
            "*.pfx",
            "secrets.json",
            "credentials.json",
            "api_keys.txt",
            "*.token",
            "schwab_tokens.json",
            "oauth_tokens.json"
        ]
        
        # Exclude virtual environment and package files
        exclude_patterns = [
            "lib/python",
            "venv/",
            "env/",
            ".venv/",
            "node_modules/",
            "__pycache__/",
            "bin/",
            "include/",
            "share/"
        ]
        
        found_sensitive = []
        
        for pattern in sensitive_patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    # Skip excluded patterns
                    file_str = str(file_path)
                    if any(exclude in file_str for exclude in exclude_patterns):
                        continue
                    found_sensitive.append(file_str)
        
        # Check if files are in .gitignore
        gitignore_file = self.project_root / ".gitignore"
        ignored_files = []
        
        if gitignore_file.exists():
            with open(gitignore_file, 'r') as f:
                gitignore_content = f.read()
                
            for file_path in found_sensitive:
                relative_path = Path(file_path).relative_to(self.project_root)
                if str(relative_path) in gitignore_content:
                    ignored_files.append(file_path)
        
        exposed_files = [f for f in found_sensitive if f not in ignored_files]
        
        self.audit_results["checks"]["sensitive_files"] = {
            "status": len(exposed_files) == 0,
            "found_sensitive": found_sensitive,
            "ignored_files": ignored_files,
            "exposed_files": exposed_files,
            "score": max(0, 100 - len(exposed_files) * 25)
        }
        
        if exposed_files:
            self.audit_results["critical_issues"].extend([
                f"Exposed sensitive file: {file}" for file in exposed_files
            ])
    
    def _check_git_security(self):
        """Check Git repository security"""
        print("🔐 Checking Git security...")
        
        git_dir = self.project_root / ".git"
        git_issues = []
        
        if not git_dir.exists():
            git_issues.append("No Git repository found")
        else:
            # Check for sensitive files in Git history
            try:
                result = subprocess.run(
                    ["git", "log", "--name-only", "--pretty=format:"],
                    capture_output=True, text=True, cwd=self.project_root
                )
                
                if result.returncode == 0:
                    committed_files = result.stdout.strip().split('\n')
                    sensitive_committed = []
                    
                    for file_path in committed_files:
                        if any(pattern in file_path for pattern in ['.env', '.key', 'secret', 'credential']):
                            sensitive_committed.append(file_path)
                    
                    if sensitive_committed:
                        git_issues.append(f"Found {len(sensitive_committed)} sensitive files in Git history")
                        
            except Exception as e:
                git_issues.append(f"Error checking Git history: {e}")
        
        self.audit_results["checks"]["git_security"] = {
            "status": len(git_issues) == 0,
            "issues": git_issues,
            "score": max(0, 100 - len(git_issues) * 30)
        }
        
        if git_issues:
            self.audit_results["critical_issues"].extend(git_issues)
    
    def _check_encryption_setup(self):
        """Check encryption setup"""
        print("🔐 Checking encryption setup...")
        
        encryption_issues = []
        
        # Check for encryption key
        secret_key_file = self.project_root / "config" / ".secret_key"
        if not secret_key_file.exists():
            encryption_issues.append("Encryption key not found")
        else:
            try:
                stat = secret_key_file.stat()
                mode = stat.st_mode & 0o777
                if mode != 0o600:
                    encryption_issues.append("Encryption key has insecure permissions")
            except Exception as e:
                encryption_issues.append(f"Error checking encryption key: {e}")
        
        # Check for secure config
        secure_config_file = self.project_root / "config" / "secure_config.json"
        if not secure_config_file.exists():
            encryption_issues.append("Secure config file not found")
        else:
            try:
                with open(secure_config_file, 'r') as f:
                    config = json.load(f)
                
                if not config.get("metadata", {}).get("encrypted", False):
                    encryption_issues.append("Config file not properly encrypted")
                    
            except Exception as e:
                encryption_issues.append(f"Error reading secure config: {e}")
        
        self.audit_results["checks"]["encryption_setup"] = {
            "status": len(encryption_issues) == 0,
            "issues": encryption_issues,
            "score": max(0, 100 - len(encryption_issues) * 25)
        }
        
        if encryption_issues:
            self.audit_results["critical_issues"].extend(encryption_issues)
    
    def _check_api_key_security(self):
        """Check API key security"""
        print("🔑 Checking API key security...")
        
        api_issues = []
        
        # Load environment variables from .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                # Fallback: manually parse .env file
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
        
        # Check environment variables
        env_vars = [
            "SCHWAB_CLIENT_ID",
            "SCHWAB_CLIENT_SECRET",
            "SCHWAB_MARKET_DATA_KEY",
            "SCHWAB_MARKET_DATA_SECRET"
        ]
        
        found_env_vars = []
        for var in env_vars:
            if os.getenv(var):
                found_env_vars.append(var)
        
        if not found_env_vars:
            api_issues.append("No API keys found in environment variables")
        
        # Check for hardcoded keys in code (exclude virtual environment)
        exclude_patterns = [
            "lib/python",
            "venv/",
            "env/",
            ".venv/",
            "node_modules/",
            "__pycache__/",
            "bin/",
            "include/",
            "share/"
        ]
        
        python_files = []
        for file_path in self.project_root.rglob("*.py"):
            file_str = str(file_path)
            if not any(exclude in file_str for exclude in exclude_patterns):
                python_files.append(file_path)
        
        hardcoded_keys = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Look for potential API keys (more specific patterns)
                patterns = [
                    r'api_key\s*=\s*["\'][A-Za-z0-9]{20,}["\']',  # API key assignments
                    r'secret\s*=\s*["\'][A-Za-z0-9]{20,}["\']',   # Secret assignments
                    r'password\s*=\s*["\'][A-Za-z0-9]{20,}["\']', # Password assignments
                    r'["\']([A-Za-z0-9]{32,})["\']'  # Very long strings (likely keys)
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if len(match) > 20:  # Likely an API key
                            hardcoded_keys.append(f"{file_path}: {match[:10]}...")
                            
            except Exception:
                continue
        
        if hardcoded_keys:
            api_issues.append(f"Found {len(hardcoded_keys)} potential hardcoded keys")
        
        self.audit_results["checks"]["api_key_security"] = {
            "status": len(api_issues) == 0,
            "issues": api_issues,
            "found_env_vars": found_env_vars,
            "hardcoded_keys": hardcoded_keys,
            "score": max(0, 100 - len(api_issues) * 20)
        }
        
        if hardcoded_keys:
            self.audit_results["critical_issues"].extend([
                f"Hardcoded key found: {key}" for key in hardcoded_keys[:5]  # Limit to first 5
            ])
    
    def _check_environment_security(self):
        """Check environment security"""
        print("🌍 Checking environment security...")
        
        env_issues = []
        
        # Check for .env file
        env_file = self.project_root / ".env"
        if env_file.exists():
            try:
                stat = env_file.stat()
                mode = stat.st_mode & 0o777
                if mode != 0o600:
                    env_issues.append(".env file has insecure permissions")
            except Exception as e:
                env_issues.append(f"Error checking .env file: {e}")
        else:
            env_issues.append(".env file not found")
        
        # Check for debug mode
        if os.getenv("DEBUG", "False").lower() == "true":
            env_issues.append("Debug mode is enabled")
        
        # Check for log level
        log_level = os.getenv("LOG_LEVEL", "INFO")
        if log_level.upper() == "DEBUG":
            env_issues.append("Debug logging is enabled")
        
        self.audit_results["checks"]["environment_security"] = {
            "status": len(env_issues) == 0,
            "issues": env_issues,
            "score": max(0, 100 - len(env_issues) * 25)
        }
        
        if env_issues:
            self.audit_results["warnings"].extend(env_issues)
    
    def _check_dependencies(self):
        """Check dependencies for security vulnerabilities"""
        print("📦 Checking dependencies...")
        
        dep_issues = []
        
        # Check requirements.txt
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            dep_issues.append("requirements.txt not found")
        else:
            try:
                with open(requirements_file, 'r') as f:
                    requirements = f.read()
                
                # Check for known vulnerable packages
                vulnerable_packages = [
                    "cryptography<3.4",
                    "requests<2.25.0",
                    "urllib3<1.26.0"
                ]
                
                for vuln_pkg in vulnerable_packages:
                    if vuln_pkg in requirements:
                        dep_issues.append(f"Potentially vulnerable package: {vuln_pkg}")
                        
            except Exception as e:
                dep_issues.append(f"Error reading requirements.txt: {e}")
        
        self.audit_results["checks"]["dependencies"] = {
            "status": len(dep_issues) == 0,
            "issues": dep_issues,
            "score": max(0, 100 - len(dep_issues) * 30)
        }
        
        if dep_issues:
            self.audit_results["warnings"].extend(dep_issues)
    
    def _check_code_security(self):
        """Check code for security issues"""
        print("💻 Checking code security...")
        
        code_issues = []
        
        # Check for common security issues in Python files
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for dangerous patterns
                dangerous_patterns = [
                    (r'eval\s*\(', "Use of eval() function"),
                    (r'exec\s*\(', "Use of exec() function"),
                    (r'os\.system\s*\(', "Use of os.system()"),
                    (r'subprocess\.call\s*\(', "Use of subprocess.call()"),
                    (r'input\s*\(', "Use of input() without validation"),
                    (r'pickle\.loads\s*\(', "Use of pickle.loads()"),
                    (r'\.format\s*\(.*\{.*\}', "Potential format string vulnerability")
                ]
                
                for pattern, description in dangerous_patterns:
                    if re.search(pattern, content):
                        code_issues.append(f"{file_path}: {description}")
                        
            except Exception:
                continue
        
        self.audit_results["checks"]["code_security"] = {
            "status": len(code_issues) == 0,
            "issues": code_issues,
            "score": max(0, 100 - len(code_issues) * 15)
        }
        
        if code_issues:
            self.audit_results["warnings"].extend(code_issues[:10])  # Limit to first 10
    
    def _calculate_score(self):
        """Calculate overall security score"""
        total_score = 0
        total_checks = 0
        
        for check_name, check_data in self.audit_results["checks"].items():
            if "score" in check_data:
                total_score += check_data["score"]
                total_checks += 1
        
        if total_checks > 0:
            self.audit_results["overall_score"] = total_score / total_checks
        
        # Add recommendations based on score
        if self.audit_results["overall_score"] < 50:
            self.audit_results["recommendations"].append("Critical security issues found - immediate action required")
        elif self.audit_results["overall_score"] < 75:
            self.audit_results["recommendations"].append("Security improvements needed")
        else:
            self.audit_results["recommendations"].append("Good security posture - maintain current practices")
    
    def _generate_report(self):
        """Generate security audit report"""
        print("\n📊 Security Audit Report")
        print("=" * 50)
        
        # Overall score
        score = self.audit_results["overall_score"]
        print(f"Overall Security Score: {score:.1f}%")
        
        if score >= 90:
            print("🎉 Excellent security posture!")
        elif score >= 75:
            print("✅ Good security posture")
        elif score >= 50:
            print("⚠️  Security improvements needed")
        else:
            print("❌ Critical security issues found")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for check_name, check_data in self.audit_results["checks"].items():
            status_icon = "✅" if check_data["status"] else "❌"
            score = check_data.get("score", 0)
            print(f"{status_icon} {check_name.replace('_', ' ').title()}: {score:.1f}%")
        
        # Critical issues
        if self.audit_results["critical_issues"]:
            print(f"\n🚨 Critical Issues ({len(self.audit_results['critical_issues'])}):")
            for issue in self.audit_results["critical_issues"][:5]:  # Show first 5
                print(f"  • {issue}")
        
        # Warnings
        if self.audit_results["warnings"]:
            print(f"\n⚠️  Warnings ({len(self.audit_results['warnings'])}):")
            for warning in self.audit_results["warnings"][:5]:  # Show first 5
                print(f"  • {warning}")
        
        # Recommendations
        if self.audit_results["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in self.audit_results["recommendations"]:
                print(f"  • {rec}")
        
        # Save report
        report_file = self.project_root / "logs" / "security_audit_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_file}")

def main():
    """Main function"""
    try:
        audit = SecurityAudit()
        results = audit.run_full_audit()
        
        # Exit with error code if critical issues found
        if results["critical_issues"]:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Audit failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 