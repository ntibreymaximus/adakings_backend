#!/usr/bin/env python3
"""
Smart Deployment Script for Adakings Backend API
Manages environment-specific files, deployments, and version management

Usage:
    python smart_deploy.py production [major|minor|patch]    # Deploy to production branch with version bump
    python smart_deploy.py dev [minor|patch]                 # Deploy to dev branch with version bump
    python smart_deploy.py feature/name [patch]              # Deploy to feature branch with version bump
    
Examples:
    python smart_deploy.py production major                  # v1.0.0 -> v2.0.0
    python smart_deploy.py dev minor                         # v1.0.0 -> v1.1.0
    python smart_deploy.py feature/auth patch               # v1.0.0 -> v1.0.1
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime

class SmartDeployer:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.backup_dir = self.base_dir / ".deploy_backup"
        self.config_file = self.base_dir / "deploy_config.json"
        
        # Environment-specific file configurations
        self.env_configs = {
            "production": {
                "files": {
                    ".env": {
                        "source": ".env.production.template",
                        "description": "Production environment variables"
                    },
                    "README.md": {
                        "source": "README-PRODUCTION.md", 
                        "description": "Production documentation"
                    },
                    "CHANGELOG.md": {
                        "source": "CHANGELOG-PRODUCTION.md",
                        "description": "Production changelog"
                    },
                    "requirements.txt": {
                        "source": "requirements-production.txt",
                        "description": "Production dependencies"
                    },
                    "adakings_backend/settings/__init__.py": {
                        "content": '''"""
Production Settings for Adakings Backend API

This production branch only contains production configuration.
For development, use the dev or feature branches.
"""

# Production settings only
from .production import *

print("🚀 Production environment loaded (production branch)")''',
                        "description": "Production-only settings loader"
                    }
                },
                "exclude_patterns": [
                    "*.dev.*",
                    "*development*",
                    "debug_*",
                    "test_*",
                    "apps/*/forms.py",
                    "apps/*/templatetags/",
                    ".env.example"
                ],
                "branch": "production"
            },
            
            "dev-test": {
                "files": {
                    ".env": {
                        "source": ".env.dev-test.template",
                        "description": "Dev-test environment variables (production-like with test values)"
                    },
                    "README.md": {
                        "source": "README-PRODUCTION.md", 
                        "description": "Production-like documentation"
                    },
                    "CHANGELOG.md": {
                        "source": "CHANGELOG-PRODUCTION.md",
                        "description": "Production-like changelog"
                    },
                    "requirements.txt": {
                        "source": "requirements-production.txt",
                        "description": "Production dependencies"
                    },
                    "adakings_backend/settings/__init__.py": {
                        "content": '''"""\nDev-Test Settings for Adakings Backend API\n\nThis dev-test branch uses production-like configuration with test/placeholder values.\nSafe for testing production scenarios without real data/keys.\n"""\n\nimport os\n\n# Default to dev-test for this branch\nENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'dev-test')\n\nif ENVIRONMENT == 'production':\n    from .production import *\n    print("🚀 Production environment loaded")\nelif ENVIRONMENT == 'dev-test':\n    from .dev_test import *\n    print("🧪 Dev-Test environment loaded (dev-test branch)")\nelif ENVIRONMENT == 'development':\n    from .development import *  \n    print("🔧 Development environment loaded")\nelse:\n    # Fallback to dev-test for this branch\n    from .dev_test import *\n    print("⚠️  Unknown environment '{}', falling back to dev-test".format(ENVIRONMENT))''',
                        "description": "Dev-test settings loader"
                    }
                },
                "exclude_patterns": [
                    "*.dev.*",
                    "*development*",
                    "debug_*",
                    "test_*",
                    "apps/*/forms.py",
                    "apps/*/templatetags/",
                    ".env.example"
                ],
                "branch": "dev-test"
            },
            
            "development": {
                "files": {
                    ".env.example": {
                        "source": ".env.development.template",
                        "description": "Development environment template"
                    },
                    "README.md": {
                        "source": "README.md",  # Use existing README
                        "description": "Development documentation"
                    },
                    "CHANGELOG.md": {
                        "source": "CHANGELOG.md",  # Use existing CHANGELOG
                        "description": "Development changelog"
                    },
                    "requirements.txt": {
                        "source": "requirements.txt",  # Use existing requirements
                        "description": "Development dependencies"
                    },
                    "adakings_backend/settings/__init__.py": {
                        "content": '''"""
Settings package for Adakings Backend API

Environment-specific settings loading:
- production.py: Production environment
- development.py: Development environment  
- base.py: Shared base settings
"""

import os

# Default to development if no environment is specified
ENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')

if ENVIRONMENT == 'production':
    from .production import *
    print("🚀 Production environment loaded")
elif ENVIRONMENT == 'development':
    from .development import *  
    print("🔧 Development environment loaded")
else:
    # Fallback to development for any other value
    from .development import *
    print("⚠️  Unknown environment '{}', falling back to development".format(ENVIRONMENT))''',
                        "description": "Multi-environment settings loader"
                    }
                },
                "include_patterns": [
                    "apps/*/forms.py",
                    "apps/*/templatetags/",
                    "debug_*",
                    "test_*",
                    "*development*"
                ],
                "branch": "dev"
            }
        }
    
    def log_info(self, message):
        """Log info message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🔵 [{timestamp}] {message}")
    
    def log_success(self, message):
        """Log success message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"✅ [{timestamp}] {message}")
    
    def log_warning(self, message):
        """Log warning message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"⚠️  [{timestamp}] {message}")
    
    def log_error(self, message):
        """Log error message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"❌ [{timestamp}] {message}")
    
    def run_command(self, command, check=True, shell=None):
        """Run shell command and return result"""
        try:
            # Determine shell usage
            if shell is None:
                shell = isinstance(command, str)
            
            result = subprocess.run(
                command, 
                shell=shell, 
                capture_output=True, 
                text=True, 
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log_error(f"Command failed: {command}")
            self.log_error(f"Error: {e.stderr}")
            return None
    
    def get_current_branch(self):
        """Get current git branch"""
        result = self.run_command("git branch --show-current")
        return result.stdout.strip() if result else None
    
    def backup_current_state(self):
        """Backup current state before making changes"""
        self.log_info("Creating backup of current state...")
        
        # Create backup directory
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir()
        
        # Backup key files
        backup_files = [
            ".env", ".env.example", "README.md", "CHANGELOG.md", 
            "requirements.txt", "adakings_backend/settings/__init__.py"
        ]
        
        for file_path in backup_files:
            src = self.base_dir / file_path
            if src.exists():
                dest = self.backup_dir / file_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
        
        self.log_success("Backup created")
    
    def restore_backup(self):
        """Restore from backup"""
        if not self.backup_dir.exists():
            self.log_warning("No backup found to restore")
            return
        
        self.log_info("Restoring from backup...")
        
        for backup_file in self.backup_dir.rglob("*"):
            if backup_file.is_file():
                relative_path = backup_file.relative_to(self.backup_dir)
                dest = self.base_dir / relative_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_file, dest)
        
        self.log_success("Backup restored")
    
    def get_latest_version_for_branch_type(self, branch_type):
        """Get latest version for specific branch type from git remote branches"""
        import re

        try:
            # Fetch latest from remote to ensure we have up-to-date branch info
            self.run_command("git fetch origin", check=False)
            
            if branch_type == "production":
                # For production, check VERSION file from production branch on remote
                result = self.run_command("git show origin/production:VERSION", check=False)
                if result and result.stdout.strip():
                    version = result.stdout.strip()
                    if re.match(r'^\d+\.\d+\.\d+$', version):
                        return version
                
                # If no production branch, check git tags as fallback
                result = self.run_command("git tag --list --sort=-version:refname", check=False)
                if result and result.stdout.strip():
                    tags = result.stdout.strip().split('\n')
                    for tag in tags:
                        if re.match(r'^v?\d+\.\d+\.\d+$', tag):
                            return tag.lstrip('v')
                return "1.0.0"  # Default for production
            
            elif branch_type == "dev-test":
                # For dev-test, check dev-test/* branches on remote (Windows compatible)
                result = self.run_command("git branch -r", check=False)
                if result and result.stdout.strip():
                    all_branches = result.stdout.strip().split('\n')
                    versions = []
                    for branch in all_branches:
                        branch_name = branch.strip().replace('origin/', '')
                        if branch_name.startswith('dev-test/'):
                            version_part = branch_name.split('/')[-1]
                            if re.match(r'^\d+\.\d+\.\d+$', version_part):
                                versions.append(version_part)
                    
                    if versions:
                        # Sort versions properly (semantic versioning)
                        versions.sort(key=lambda x: [int(i) for i in x.split('.')], reverse=True)
                        return versions[0]  # Return highest version
                return "1.0.0"  # Default for dev-test
            
            elif branch_type.startswith("feature/"):
                # For feature branches, check feature/name-version branches on remote
                feature_name = branch_type.split('/', 1)[1]
                pattern = f"origin/feature/{feature_name}-*"
                result = self.run_command(f"git branch -r --list '{pattern}' --sort=-version:refname", check=False)
                if result and result.stdout.strip():
                    branches = result.stdout.strip().split('\n')
                    for branch in branches:
                        branch_name = branch.strip().replace('origin/', '')
                        # Extract version from feature/name-version format
                        if f"feature/{feature_name}-" in branch_name:
                            version_part = branch_name.split(f"feature/{feature_name}-")[-1]
                            if re.match(r'^\d+\.\d+\.\d+$', version_part):
                                return version_part
                return "0.1.0"  # Default for feature branches
            
            else:
                # For dev/development, check dev/* branches on remote
                result = self.run_command("git branch -r --list 'origin/dev/*' --sort=-version:refname", check=False)
                if result and result.stdout.strip():
                    branches = result.stdout.strip().split('\n')
                    for branch in branches:
                        branch_name = branch.strip().replace('origin/', '')
                        version_part = branch_name.split('/')[-1]
                        if re.match(r'^\d+\.\d+\.\d+$', version_part):
                            return version_part
                
                return "0.1.0"  # Default for dev
                
        except Exception as e:
            self.log_warning(f"Could not determine version from git: {e}")
            return "1.0.0"
    
    def read_version(self, branch_type="production"):
        """Read current version based on branch type"""
        return self.get_latest_version_for_branch_type(branch_type)
    
    def bump_version(self, bump_type, current_version):
        """Bump version based on type"""
        major, minor, patch = map(int, current_version.split('.'))
        
        if bump_type == 'major':
            new_version = f"{major + 1}.0.0"
            self.log_info(f"🚀 MAJOR version bump: {current_version} -> {new_version}")
        elif bump_type == 'minor':
            new_version = f"{major}.{minor + 1}.0"
            self.log_info(f"✨ MINOR version bump: {current_version} -> {new_version}")
        elif bump_type == 'patch':
            new_version = f"{major}.{minor}.{patch + 1}"
            self.log_info(f"🐛 PATCH version bump: {current_version} -> {new_version}")
        else:
            self.log_error(f"Invalid bump type: {bump_type}")
            return None
        
        return new_version
    
    def calculate_new_version(self, bump_type, current_version):
        """Calculate new version without logging or updating files"""
        major, minor, patch = map(int, current_version.split('.'))
        
        if bump_type == 'major':
            return f"{major + 1}.0.0"
        elif bump_type == 'minor':
            return f"{major}.{minor + 1}.0"
        elif bump_type == 'patch':
            return f"{major}.{minor}.{patch + 1}"
        else:
            return None
    
    def ensure_unique_version(self, target_env, proposed_version, bump_type):
        """Ensure the proposed version doesn't conflict with existing branches"""
        import re
        
        # Build the target branch name to check
        if target_env == "production":
            # Production doesn't use versioned branches
            return proposed_version
        elif target_env == "dev-test":
            branch_pattern = f"dev-test/{proposed_version}"
        elif target_env in ["dev", "development"]:
            branch_pattern = f"dev/{proposed_version}"
        elif target_env.startswith("feature/"):
            feature_name = target_env.split('/', 1)[1]
            branch_pattern = f"feature/{feature_name}-{proposed_version}"
        else:
            return proposed_version
        
        # Check if branch already exists
        result = self.run_command(f"git branch -r --list 'origin/{branch_pattern}'", check=False)
        if result and result.stdout.strip():
            # Branch exists, increment version
            self.log_warning(f"Branch {branch_pattern} already exists, incrementing version...")
            
            # Parse version and increment patch
            major, minor, patch = map(int, proposed_version.split('.'))
            
            # Keep incrementing patch until we find a unique version
            while True:
                patch += 1
                new_version = f"{major}.{minor}.{patch}"
                
                if target_env == "dev-test":
                    test_branch = f"dev-test/{new_version}"
                elif target_env in ["dev", "development"]:
                    test_branch = f"dev/{new_version}"
                elif target_env.startswith("feature/"):
                    feature_name = target_env.split('/', 1)[1]
                    test_branch = f"feature/{feature_name}-{new_version}"
                
                result = self.run_command(f"git branch -r --list 'origin/{test_branch}'", check=False)
                if not result or not result.stdout.strip():
                    self.log_info(f"✨ Using unique version: {new_version}")
                    return new_version
        
        return proposed_version
    
    def update_version_files(self, new_version):
        """Update version in all relevant files"""
        # Update VERSION file
        version_file = self.base_dir / "VERSION"
        version_file.write_text(f"{new_version}\n")
        self.log_info(f"✓ Updated VERSION file: {new_version}")
        
        # Update README files with version badges
        readme_files = ["README.md", "README-PRODUCTION.md", "README-DEVELOPMENT.md"]
        
        for readme_file in readme_files:
            readme_path = self.base_dir / readme_file
            if readme_path.exists():
                content = readme_path.read_text(encoding='utf-8')
                
                # Update version badge
                import re
                content = re.sub(
                    r'(https://img\.shields\.io/badge/version-v)[^-]+(-.+\.svg)',
                    rf'\g<1>{new_version}\g<2>',
                    content
                )
                
                # Update current version
                content = re.sub(
                    r'(\*\*Current Version\*\*: v)[^\s]+',
                    rf'\g<1>{new_version}',
                    content
                )
                
                readme_path.write_text(content, encoding='utf-8')
                self.log_info(f"✓ Updated {readme_file} with version {new_version}")
    
    def validate_production_config(self):
        """Validate production configuration files"""
        self.log_info("🔍 Validating production configuration...")
        
        validation_errors = []
        warnings = []
        
        # Check .env file
        env_file = self.base_dir / ".env"
        if env_file.exists():
            try:
                env_content = env_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    env_content = env_file.read_text(encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        env_content = env_file.read_text(encoding='latin-1')
                    except UnicodeDecodeError:
                        env_content = env_file.read_text(encoding='cp1252')
            
            # Critical production settings
            required_settings = {
                'DJANGO_SECRET_KEY': 'Production secret key',
                'DJANGO_DEBUG': 'Debug mode (should be False)',
                'DJANGO_ALLOWED_HOSTS': 'Allowed hosts (your domain)',
                'DB_NAME': 'Database name',
                'DB_USER': 'Database user',
                'DB_PASSWORD': 'Database password',
                'PAYSTACK_PUBLIC_KEY_LIVE': 'Live Paystack public key',
                'PAYSTACK_SECRET_KEY_LIVE': 'Live Paystack secret key'
            }
            
            for setting, description in required_settings.items():
                if setting not in env_content:
                    validation_errors.append(f"Missing {setting} ({description})")
                elif f"{setting}=your-" in env_content or f"{setting}=pk_test_" in env_content or f"{setting}=sk_test_" in env_content:
                    validation_errors.append(f"{setting} contains placeholder/test value ({description})")
            
            # Check for debug mode
            if 'DJANGO_DEBUG=True' in env_content:
                validation_errors.append("DJANGO_DEBUG is set to True (should be False in production)")
            
            # Check for localhost/development domains
            if 'localhost' in env_content or '127.0.0.1' in env_content:
                warnings.append("Configuration contains localhost/127.0.0.1 - ensure this is correct for production")
            
            # Check for test Paystack keys
            if 'pk_test_' in env_content or 'sk_test_' in env_content:
                validation_errors.append("Production environment contains test Paystack keys")
        else:
            validation_errors.append(".env file not found")
        
        # Check requirements.txt
        req_file = self.base_dir / "requirements.txt"
        if req_file.exists():
            try:
                req_content = req_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    req_content = req_file.read_text(encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        req_content = req_file.read_text(encoding='latin-1')
                    except UnicodeDecodeError:
                        req_content = req_file.read_text(encoding='cp1252')
            
            # Check for production essentials
            prod_packages = ['gunicorn', 'psycopg2-binary', 'whitenoise']
            for package in prod_packages:
                if package not in req_content:
                    warnings.append(f"Missing recommended production package: {package}")
            
            # Check for development packages
            dev_packages = ['django-debug-toolbar', 'pytest', 'black', 'ipython']
            for package in dev_packages:
                if package in req_content:
                    warnings.append(f"Development package found in production requirements: {package}")
        
        # Check settings configuration
        settings_init = self.base_dir / "adakings_backend" / "settings" / "__init__.py"
        if settings_init.exists():
            try:
                settings_content = settings_init.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    settings_content = settings_init.read_text(encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        settings_content = settings_init.read_text(encoding='latin-1')
                    except UnicodeDecodeError:
                        settings_content = settings_init.read_text(encoding='cp1252')
            if 'development' in settings_content and 'production' not in settings_content.split('\n')[10:]:
                warnings.append("Settings file may load development configuration in production")
        
        # Report validation results
        if validation_errors:
            self.log_error("❌ Production configuration validation failed:")
            for error in validation_errors:
                self.log_error(f"  • {error}")
            return False
        
        if warnings:
            self.log_error("❌ Production deployment blocked due to warnings:")
            for warning in warnings:
                self.log_error(f"  • {warning}")
            self.log_error("\n🚫 Production deployments are blocked on ALL warnings.")
            self.log_error("Please resolve all warnings before deploying to production.")
            return False
        
        self.log_success("✅ Production configuration validation passed")
        return True
    
    def validate_development_config(self):
        """Validate development configuration files"""
        self.log_info("🔍 Validating development configuration...")
        
        validation_errors = []
        warnings = []
        
        # Check .env.example file
        env_file = self.base_dir / ".env.example"
        if env_file.exists():
            try:
                env_content = env_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    env_content = env_file.read_text(encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        env_content = env_file.read_text(encoding='latin-1')
                    except UnicodeDecodeError:
                        env_content = env_file.read_text(encoding='cp1252')
            
            # Check for development settings
            if 'DJANGO_DEBUG=False' in env_content:
                warnings.append("Development environment has DEBUG=False")
            
            # Check for production keys in development
            if 'pk_live_' in env_content or 'sk_live_' in env_content:
                validation_errors.append("Development environment contains live Paystack keys")
            
            # Check for localhost settings
            if 'localhost' not in env_content and '127.0.0.1' not in env_content:
                warnings.append("Development environment missing localhost configuration")
        else:
            validation_errors.append(".env.example file not found")
        
        # Check for development tools in requirements
        req_file = self.base_dir / "requirements.txt"
        if req_file.exists():
            try:
                req_content = req_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    req_content = req_file.read_text(encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        req_content = req_file.read_text(encoding='latin-1')
                    except UnicodeDecodeError:
                        req_content = req_file.read_text(encoding='cp1252')
            
            # Check for development essentials
            dev_packages = ['django-debug-toolbar', 'pytest']
            for package in dev_packages:
                if package not in req_content:
                    warnings.append(f"Missing recommended development package: {package}")
        
        # Report validation results
        if validation_errors:
            self.log_error("❌ Development configuration validation failed:")
            for error in validation_errors:
                self.log_error(f"  • {error}")
            return False
        
        if warnings:
            self.log_warning("⚠️  Development configuration warnings:")
            for warning in warnings:
                self.log_warning(f"  • {warning}")
        
        self.log_success("✅ Development configuration validation passed")
        return True
    
    def validate_dev_test_config(self):
        """Validate dev-test configuration files - production-like with test values"""
        self.log_info("🔍 Validating dev-test configuration...")
        
        validation_errors = []
        warnings = []
        
        # Check .env file
        env_file = self.base_dir / ".env"
        if env_file.exists():
            try:
                env_content = env_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    env_content = env_file.read_text(encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        env_content = env_file.read_text(encoding='latin-1')
                    except UnicodeDecodeError:
                        env_content = env_file.read_text(encoding='cp1252')
            
            # Critical production-like settings with placeholder warnings
            required_settings = {
                'DJANGO_SECRET_KEY': 'Secret key (currently using test value)',
                'DJANGO_DEBUG': 'Debug mode (should be False)',
                'DJANGO_ALLOWED_HOSTS': 'Allowed hosts (update for actual testing)',
                'DB_NAME': 'Database name (using test database)',
                'DB_USER': 'Database user (using test user)',
                'DB_PASSWORD': 'Database password (using test password)',
                'PAYSTACK_PUBLIC_KEY_LIVE': 'Paystack public key (using test placeholder)',
                'PAYSTACK_SECRET_KEY_LIVE': 'Paystack secret key (using test placeholder)'
            }
            
            for setting, description in required_settings.items():
                if setting not in env_content:
                    validation_errors.append(f"Missing {setting} ({description})")
                else:
                    # Check for placeholder/test values and warn (but don't fail)
                    if (setting == 'DJANGO_SECRET_KEY' and 'django-dev-test-secret-key' in env_content) or \
                       (setting == 'DB_PASSWORD' and 'test_password' in env_content) or \
                       (setting == 'DB_USER' and 'test_user' in env_content) or \
                       (setting == 'PAYSTACK_PUBLIC_KEY_LIVE' and 'placeholder' in env_content) or \
                       (setting == 'PAYSTACK_SECRET_KEY_LIVE' and 'placeholder' in env_content):
                        warnings.append(f"⚠️  {setting} is using placeholder/test value - {description}")
            
            # Check environment is set correctly
            if 'DJANGO_ENVIRONMENT=dev-test' not in env_content:
                warnings.append("DJANGO_ENVIRONMENT should be set to 'dev-test'")
            
            # Check for debug mode (should be False for prod-like testing)
            if 'DJANGO_DEBUG=True' in env_content:
                warnings.append("DJANGO_DEBUG is set to True (consider False for production-like testing)")
            
            # Check for test domains vs production domains
            if 'test.adakings.local' in env_content or 'localhost' in env_content:
                warnings.append("Using test/localhost domains - update if testing with real domains")
            
            # Check email configuration
            if 'mailtrap.io' in env_content or 'test_user' in env_content:
                warnings.append("Email configuration using test/placeholder values")
                
        else:
            validation_errors.append(".env file not found")
        
        # Check requirements.txt (should be production-like)
        req_file = self.base_dir / "requirements.txt"
        if req_file.exists():
            try:
                req_content = req_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    req_content = req_file.read_text(encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        req_content = req_file.read_text(encoding='latin-1')
                    except UnicodeDecodeError:
                        req_content = req_file.read_text(encoding='cp1252')
            
            # Check for production essentials (warn if missing)
            prod_packages = ['gunicorn', 'psycopg2-binary', 'whitenoise']
            for package in prod_packages:
                if package not in req_content:
                    warnings.append(f"Missing production package for testing: {package}")
        
        # Check settings configuration
        settings_init = self.base_dir / "adakings_backend" / "settings" / "__init__.py"
        if settings_init.exists():
            try:
                settings_content = settings_init.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                settings_content = settings_init.read_text(encoding='utf-8-sig')
            if 'dev-test' not in settings_content:
                warnings.append("Settings file should support dev-test environment")
        
        # Report validation results
        if validation_errors:
            self.log_error("❌ Dev-test configuration validation failed:")
            for error in validation_errors:
                self.log_error(f"  • {error}")
            return False
        
        if warnings:
            self.log_warning("⚠️  Dev-test configuration warnings (deployment will continue):")
            for warning in warnings:
                self.log_warning(f"  • {warning}")
            self.log_warning("")
            self.log_warning("🧪 These are test/placeholder values - safe for dev-test environment")
            self.log_warning("📝 Update these values when moving to actual production")
        
        self.log_success("✅ Dev-test configuration validation passed with warnings")
        return True
    
    def setup_environment_files(self, env_type):
        """Set up environment-specific files"""
        config = self.env_configs.get(env_type)
        if not config:
            self.log_error(f"Unknown environment type: {env_type}")
            return False
        
        self.log_info(f"Setting up {env_type} environment files...")
        
        # Process file configurations
        # Ensure all file operations are handled properly to avoid WinError 32
        for dest_path, file_config in config["files"].items():
            dest = self.base_dir / dest_path
            
            if "source" in file_config:
                # Copy from source file
                source = self.base_dir / file_config["source"]
                if source.exists():
                    # Check if source and destination are the same file
                    if source.resolve() == dest.resolve():
                        self.log_info(f"✓ {file_config['description']}: {dest_path} (already in place)")
                        continue
                    
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(source, dest)
                        self.log_info(f"✓ {file_config['description']}: {dest_path}")
                    except PermissionError as e:
                        self.log_warning(f"Permission error copying {source} to {dest}: {e}")
                        # Try alternative method
                        try:
                            with source.open('rb') as src_file:
                                with dest.open('wb') as dest_file:
                                    shutil.copyfileobj(src_file, dest_file)
                            self.log_info(f"✓ {file_config['description']}: {dest_path} (alternative method)")
                        except Exception as alt_e:
                            self.log_error(f"Failed to copy {source} to {dest}: {alt_e}")
                else:
                    self.log_warning(f"Source file not found: {source}")
                
            elif "content" in file_config:
                # Write content directly
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(file_config["content"], encoding='utf-8')
                self.log_info(f"✓ {file_config['description']}: {dest_path}")
        
        return True
    
    def clean_environment_files(self, env_type):
        """Remove files not needed for specific environment"""
        config = self.env_configs.get(env_type)
        if not config or "exclude_patterns" not in config:
            return
        
        self.log_info(f"Cleaning files not needed for {env_type}...")
        
        # Remove excluded files/patterns
        for pattern in config["exclude_patterns"]:
            files_to_remove = list(self.base_dir.glob(pattern))
            for file_path in files_to_remove:
                if file_path.is_file():
                    # Check if it's tracked by git
                    result = self.run_command(f"git ls-files {file_path}", check=False)
                    if result and result.stdout.strip():
                        # Use --force to handle local modifications
                        result = self.run_command(f"git rm --force {file_path}", check=False)
                        if result:
                            self.log_info(f"✓ Removed: {file_path}")
                        else:
                            # If git rm fails, just remove the file locally
                            file_path.unlink()
                            self.log_info(f"✓ Removed: {file_path}")
    
    def switch_branch(self, target_branch):
        """Switch to target branch, create if doesn't exist"""
        current_branch = self.get_current_branch()
        
        if current_branch == target_branch:
            self.log_info(f"Already on branch: {target_branch}")
            return True
        
        # Check if branch exists
        result = self.run_command(f"git branch --list {target_branch}", check=False)
        branch_exists = bool(result and result.stdout.strip())
        
        if branch_exists:
            self.log_info(f"Switching to existing branch: {target_branch}")
            result = self.run_command(f"git checkout {target_branch}")
        else:
            self.log_info(f"Creating new branch: {target_branch}")
            result = self.run_command(f"git checkout -b {target_branch}")
        
        return result is not None
    
    def add_environment_specific_files(self, env_type, target_branch):
        """Add files selectively based on environment type and branch"""
        self.log_info(f"Adding files for {env_type} environment...")
        
        if env_type == "production" or env_type == "dev-test":
            # Production and dev-test branches: only push production-specific files
            production_files = [
                ".env",
                "README.md", 
                "CHANGELOG.md",
                "requirements.txt",
                "adakings_backend/settings/__init__.py",
                "VERSION",
                "smart_deploy.py",
                "SMART_DEPLOY_GUIDE.md"
            ]
            
            # Add core application files (but not development-specific ones)
            core_patterns = [
                "adakings_backend/*.py",
                "adakings_backend/settings/base.py",
                "adakings_backend/settings/production.py",
                "adakings_backend/urls.py",
                "adakings_backend/wsgi.py",
                "adakings_backend/asgi.py",
                "apps/*/models.py",
                "apps/*/views.py",
                "apps/*/serializers.py",
                "apps/*/urls.py",
                "apps/*/__init__.py",
                "apps/*/apps.py",
                "apps/*/admin.py",
                "manage.py"
            ]
            
            # Add specific production files
            for file_path in production_files:
                if (self.base_dir / file_path).exists():
                    result = self.run_command(f"git add {file_path}", check=False)
                    if result and result.returncode == 0:
                        self.log_info(f"✓ Added: {file_path}")
            
            # Add core application files using patterns
            for pattern in core_patterns:
                result = self.run_command(f"git add {pattern}", check=False)
                if result and result.returncode == 0:
                    self.log_info(f"✓ Added pattern: {pattern}")
            
            self.log_success(f"Added production-specific files for {env_type} branch")
            
        else:
            # Development and feature branches: push development-specific files
            development_files = [
                ".env.example",
                "README.md",
                "CHANGELOG.md", 
                "requirements.txt",
                "adakings_backend/settings/__init__.py",
                "VERSION",
                "smart_deploy.py",
                "SMART_DEPLOY_GUIDE.md"
            ]
            
            # Add all application files including development tools
            dev_patterns = [
                "adakings_backend/*.py",
                "adakings_backend/settings/*.py",
                "apps/*/*.py",  # All Python files including forms.py, templatetags, etc.
                "apps/*/templatetags/*.py",
                "debug_*",
                "test_*",
                "tests/",
                "manage.py",
                "*.md",
                "*.txt",
                "*.json"
            ]
            
            # Add specific development files
            for file_path in development_files:
                if (self.base_dir / file_path).exists():
                    result = self.run_command(f"git add {file_path}", check=False)
                    if result and result.returncode == 0:
                        self.log_info(f"✓ Added: {file_path}")
            
            # Add development files using patterns
            for pattern in dev_patterns:
                result = self.run_command(f"git add {pattern}", check=False)
                if result and result.returncode == 0:
                    self.log_info(f"✓ Added pattern: {pattern}")
            
            self.log_success(f"Added development-specific files for feature/development branch")
    
    def commit_and_push(self, env_type, target_branch, message_prefix=""):
        """Commit changes and push to appropriate branch"""
        # Use the provided target_branch instead of config
        
        # Add files selectively based on branch type
        self.add_environment_specific_files(env_type, target_branch)
        
        # Check if there are changes to commit
        result = self.run_command("git diff --cached --quiet", check=False)
        if result and result.returncode == 0:
            self.log_info("No changes to commit")
            return True
        
        # Create commit message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"{message_prefix}feat: Deploy to {env_type} environment\n\n"
        commit_message += f"Environment: {env_type.upper()}\n"
        commit_message += f"Target Branch: {target_branch}\n"
        commit_message += f"Deployed: {timestamp}\n\n"
        commit_message += f"Changes:\n"
        
        if env_type == "production":
            commit_message += "- Production-optimized file structure\n"
            commit_message += "- Removed development dependencies\n"
            commit_message += "- Production environment configuration\n"
        else:
            commit_message += "- Development-friendly file structure\n"
            commit_message += "- Included development tools and utilities\n"
            commit_message += "- Development environment configuration\n"
        
        # Commit changes (escape quotes and handle multiline messages)
        safe_message = commit_message.replace('"', '\"').replace('\n', '\n')
        result = self.run_command(['git', 'commit', '-m', commit_message], shell=False)
        if not result:
            return False
        
        # Push to remote
        self.log_info(f"Pushing to {target_branch} branch...")
        result = self.run_command(f"git push origin {target_branch}")
        
        return result is not None
    
    def version_management(self, target_env, bump_type):
        """Manage version bump for the deployment"""
        # Get branch type for version tracking
        if target_env == "production":
            branch_type = "production"
        elif target_env == "dev-test":
            branch_type = "dev-test"
        elif target_env.startswith("feature/"):
            branch_type = target_env  # feature/name
        else:
            branch_type = "development"
        
        current_version = self.read_version(branch_type)
        if not current_version:
            raise Exception("Failed to read current version")
        
        new_version = self.bump_version(bump_type, current_version)
        if not new_version:
            raise Exception("Failed to bump version")
        
        self.update_version_files(new_version)
        return new_version

    def deployment_checks(self, target_env):
        """Run necessary checks before deployment"""
        if target_env == "production":
            return self.validate_production_config()
        elif target_env == "dev-test":
            return self.validate_dev_test_config()
        else:
            return self.validate_development_config()

    def deploy(self, target_env, bump_type, commit_message=""):
        """Main deployment function"""
        self.log_info(f"🚀 Starting deployment to {target_env} environment")
        
        # Validate environment
        if target_env not in ["production", "dev-test", "dev", "development"] and not target_env.startswith("feature/"):
            self.log_error(f"Invalid environment: {target_env}")
            return False
        
        # Normalize environment type
        if target_env == "production":
            env_type = "production"
        elif target_env == "dev-test":
            env_type = "dev-test"
        else:
            env_type = "development"
        
        # Get the LATEST version for target branch determination (without updating files yet)
        # This should get the highest version number from existing branches of this type
        if target_env == "production":
            branch_type = "production"
        elif target_env == "dev-test":
            branch_type = "dev-test"
        elif target_env.startswith("feature/"):
            branch_type = target_env  # feature/name
        else:
            branch_type = "development"
        
        current_version = self.get_latest_version_for_branch_type(branch_type)
        new_version = self.calculate_new_version(bump_type, current_version)
        
        # Ensure the new version doesn't conflict with existing branches
        new_version = self.ensure_unique_version(target_env, new_version, bump_type)
        
        # Determine target branch (with version for dev-test and feature branches)
        if target_env == "production":
            target_branch = "production"
        elif target_env == "dev-test":
            target_branch = f"dev-test/{new_version}"
        elif target_env in ["dev", "development"]:
            target_branch = f"dev/{new_version}"  # Versioned dev branches
        elif target_env.startswith("feature/"):
            # Use feature-name-version format to avoid git naming conflicts
            feature_name = target_env.split('/', 1)[1]
            target_branch = f"feature/{feature_name}-{new_version}"  # Use dash instead of slash
        else:
            target_branch = target_env
        
        try:
            # Backup current state
            self.backup_current_state()
            
            # Switch to target branch FIRST (before any file changes)
            if not self.switch_branch(target_branch):
                raise Exception(f"Failed to switch to branch: {target_branch}")
            
            # Now update version files on the target branch
            self.update_version_files(new_version)
            
            # Pre-deployment checks
            if not self.deployment_checks(target_env):
                raise Exception("Pre-deployment checks failed")
            
            # Set up environment files
            if not self.setup_environment_files(env_type):
                raise Exception(f"Failed to setup {env_type} files")
            
            # Clean environment-specific files
            self.clean_environment_files(env_type)
            
            # Commit and push
            commit_prefix = f"\n\nVersion: {new_version}\n"
            if not self.commit_and_push(env_type, target_branch, commit_prefix):
                raise Exception("Failed to commit and push changes")
            
            self.log_success(f"🎉 Successfully deployed to {target_env} environment!")
            self.log_info(f"Branch: {target_branch}")
            self.log_info(f"Environment: {env_type}")
            self.log_info(f"Version: {new_version}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Deployment failed: {str(e)}")
            self.log_info("Restoring backup...")
            self.restore_backup()
            return False


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(__doc__)
        print("\nAvailable environments:")
        print("  production [major|minor|patch]     - Deploy to production branch with version bump")
        print("  dev-test [minor|patch]             - Deploy to dev-test branch (production-like with test values)")
        print("  dev [minor|patch]                  - Deploy to dev branch with version bump")
        print("  feature/name [patch]               - Deploy to feature branch with version bump")
        print("\nVersion bump types:")
        print("  major  - Breaking changes (1.0.0 -> 2.0.0)")
        print("  minor  - New features (1.0.0 -> 1.1.0)")
        print("  patch  - Bug fixes (1.0.0 -> 1.0.1)")
        sys.exit(1)
    
    target_env = sys.argv[1]
    bump_type = sys.argv[2] if len(sys.argv) == 3 else None
    
    # Default version bump types based on environment
    if not bump_type:
        if target_env == "production":
            bump_type = "patch"  # Conservative default for production
        elif target_env in ["dev", "development"]:
            bump_type = "minor"  # New features in development
        else:
            bump_type = "patch"  # Feature branches typically have patches
    
    # Validate version bump type
    valid_bumps = ["major", "minor", "patch"]
    if bump_type not in valid_bumps:
        print(f"❌ Invalid version bump type: {bump_type}")
        print(f"Valid types: {', '.join(valid_bumps)}")
        sys.exit(1)
    
    # Validate version bump type for environment
    if target_env == "production" and bump_type == "major":
        print("⚠️  WARNING: Major version bump in production - this indicates breaking changes!")
    
    deployer = SmartDeployer()
    
    # Show deployment information using same logic as deploy function
    if target_env == "production":
        branch_type = "production"
    elif target_env == "dev-test":
        branch_type = "dev-test"
    elif target_env.startswith("feature/"):
        branch_type = target_env  # feature/name
    else:
        branch_type = "development"
    
    current_version = deployer.get_latest_version_for_branch_type(branch_type)
    new_version = deployer.calculate_new_version(bump_type, current_version) if current_version else "unknown"
    new_version = deployer.ensure_unique_version(target_env, new_version, bump_type)
    
    print(f"🎯 Target Environment: {target_env}")
    print(f"🔢 Version Bump: {bump_type} ({current_version} -> {new_version})")
    
    # Confirm deployment
    if target_env == "production":
        print("⚠️  WARNING: This will deploy to PRODUCTION!")
        print(f"This will create version {new_version} with a {bump_type.upper()} bump.")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Deployment cancelled.")
            sys.exit(0)
    
    # Run deployment
    success = deployer.deploy(target_env, bump_type)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
