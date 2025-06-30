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
            
            "development": {
                "files": {
                    ".env.example": {
                        "source": ".env.development.template",
                        "description": "Development environment template"
                    },
                    "README.md": {
                        "source": "README-DEVELOPMENT.md",
                        "description": "Development documentation"
                    },
                    "CHANGELOG.md": {
                        "source": "CHANGELOG-DEVELOPMENT.md", 
                        "description": "Development changelog"
                    },
                    "requirements.txt": {
                        "source": "requirements-development.txt",
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
    
    def run_command(self, command, check=True):
        """Run shell command and return result"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
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
    
    def read_version(self):
        """Read current version from VERSION file"""
        version_file = self.base_dir / "VERSION"
        if not version_file.exists():
            self.log_warning("VERSION file not found, creating v1.0.0")
            version_file.write_text("1.0.0\n")
            return "1.0.0"
        
        version = version_file.read_text().strip()
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', version):
            self.log_error(f"Invalid version format: {version}")
            return None
        
        return version
    
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
            env_content = env_file.read_text()
            
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
            req_content = req_file.read_text()
            
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
            settings_content = settings_init.read_text()
            if 'development' in settings_content and 'production' not in settings_content.split('\n')[10:]:
                warnings.append("Settings file may load development configuration in production")
        
        # Report validation results
        if validation_errors:
            self.log_error("❌ Production configuration validation failed:")
            for error in validation_errors:
                self.log_error(f"  • {error}")
            return False
        
        if warnings:
            self.log_warning("⚠️  Production configuration warnings:")
            for warning in warnings:
                self.log_warning(f"  • {warning}")
        
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
            env_content = env_file.read_text()
            
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
            req_content = req_file.read_text()
            
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
    
    def setup_environment_files(self, env_type):
        """Set up environment-specific files"""
        config = self.env_configs.get(env_type)
        if not config:
            self.log_error(f"Unknown environment type: {env_type}")
            return False
        
        self.log_info(f"Setting up {env_type} environment files...")
        
        # Process file configurations
        for dest_path, file_config in config["files"].items():
            dest = self.base_dir / dest_path
            
            if "source" in file_config:
                # Copy from source file
                source = self.base_dir / file_config["source"]
                if source.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                    self.log_info(f"✓ {file_config['description']}: {dest_path}")
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
                        self.run_command(f"git rm {file_path}")
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
    
    def commit_and_push(self, env_type, message_prefix=""):
        """Commit changes and push to appropriate branch"""
        config = self.env_configs.get(env_type, {})
        target_branch = config.get("branch", env_type)
        
        # Add all changes
        self.run_command("git add .")
        
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
        
        # Commit changes
        result = self.run_command(f'git commit -m "{commit_message}"')
        if not result:
            return False
        
        # Push to remote
        self.log_info(f"Pushing to {target_branch} branch...")
        result = self.run_command(f"git push origin {target_branch}")
        
        return result is not None
    
    def version_management(self, target_env, bump_type):
        """Manage version bump for the deployment"""
        current_version = self.read_version()
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
        else:
            return self.validate_development_config()

    def deploy(self, target_env, bump_type, commit_message=""):
        """Main deployment function"""
        self.log_info(f"🚀 Starting deployment to {target_env} environment")
        
        # Validate environment
        if target_env not in ["production", "dev", "development"] and not target_env.startswith("feature/"):
            self.log_error(f"Invalid environment: {target_env}")
            return False
        
        # Normalize environment type
        env_type = "production" if target_env == "production" else "development"
        
        # Determine target branch
        if target_env == "production":
            target_branch = "production"
        elif target_env in ["dev", "development"]:
            target_branch = "dev"
        else:
            target_branch = target_env  # feature branches
        
        try:
            # Backup current state
            self.backup_current_state()
            
            # Pre-deployment checks
            if not self.deployment_checks(target_env):
                raise Exception("Pre-deployment checks failed")
            
            # Version management
            new_version = self.version_management(target_env, bump_type)
            
            # Switch to target branch
            if not self.switch_branch(target_branch):
                raise Exception(f"Failed to switch to branch: {target_branch}")
            
            # Set up environment files
            if not self.setup_environment_files(env_type):
                raise Exception(f"Failed to setup {env_type} files")
            
            # Clean environment-specific files
            self.clean_environment_files(env_type)
            
            # Commit and push
            commit_message = f"{commit_message}\n\nVersion: {new_version}\n"
            if not self.commit_and_push(env_type, commit_message):
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
    
    # Show deployment information
    current_version = deployer.read_version()
    new_version = deployer.bump_version(bump_type, current_version) if current_version else "unknown"
    
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
