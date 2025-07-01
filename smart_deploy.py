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
                        "source": "environments/production/.env",
                        "description": "Production environment variables"
                    },
                    "README.md": {
                        "source": "environments/production/README.md", 
                        "description": "Production documentation"
                    },
                    "CHANGELOG.md": {
                        "source": "environments/production/CHANGELOG.md",
                        "description": "Production changelog"
                    },
                    "requirements.txt": {
                        "source": "environments/production/requirements.txt",
                        "description": "Production dependencies"
                    },
                    "gunicorn.conf.py": {
                        "source": "environments/production/gunicorn.conf.py",
                        "description": "Production Gunicorn configuration"
                    },
                    "nginx.conf": {
                        "source": "environments/production/nginx.conf",
                        "description": "Production Nginx configuration"
                    },
                    "docker-compose.yml": {
                        "source": "environments/production/docker-compose.yml",
                        "description": "Production Docker Compose configuration"
                    },
                    "Dockerfile": {
                        "source": "environments/production/Dockerfile",
                        "description": "Production Docker configuration"
                    },
                    "adakings-backend.service": {
                        "source": "environments/production/adakings-backend.service",
                        "description": "Production systemd service file"
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
            
            "dev": {
                "files": {
                    ".env": {
                        "source": "environments/dev/.env",
                        "description": "Dev environment variables (production-like with dev values)"
                    },
                    "README.md": {
                        "source": "environments/dev/README.md", 
                        "description": "Dev environment documentation"
                    },
                    "CHANGELOG.md": {
                        "source": "environments/dev/CHANGELOG.md",
                        "description": "Dev environment changelog"
                    },
                    "requirements.txt": {
                        "source": "environments/dev/requirements.txt",
                        "description": "Dev environment dependencies"
                    },
                    "gunicorn.conf.py": {
                        "source": "environments/dev/gunicorn.conf.py",
                        "description": "Dev Gunicorn configuration"
                    },
                    "nginx.conf": {
                        "source": "environments/dev/nginx.conf",
                        "description": "Dev Nginx configuration"
                    },
                    "docker-compose.yml": {
                        "source": "environments/dev/docker-compose.yml",
                        "description": "Dev Docker Compose configuration"
                    },
                    "Dockerfile": {
                        "source": "environments/dev/Dockerfile",
                        "description": "Dev Docker configuration"
                    },
                    "adakings-backend-dev.service": {
                        "source": "environments/dev/adakings-backend-dev.service",
                        "description": "Dev systemd service file"
                    },
                    "adakings_backend/settings/__init__.py": {
                        "content": '''"""\nDev Settings for Adakings Backend API\n\nThis dev branch uses production-like configuration but with development values.\nSimilar to production but safe for development work.\n"""\n\nimport os\n\n# Default to dev for this branch\nENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'dev')\n\nif ENVIRONMENT == 'production':\n    from .production import *\n    print("🚀 Production environment loaded")\nelif ENVIRONMENT == 'dev':\n    from .dev import *\n    print("🔧 Dev environment loaded (dev branch)")\nelif ENVIRONMENT == 'development':\n    from .development import *  \n    print("🔧 Development environment loaded")\nelse:\n    # Fallback to dev for this branch\n    from .dev import *\n    print("⚠️  Unknown environment '{}', falling back to dev".format(ENVIRONMENT))''',
                        "description": "Dev settings loader"
                    }
                },
                "exclude_patterns": [
                    "*.feature.*",
                    "*local*",
                    "debug_*",
                    "test_*",
                    "apps/*/forms.py",
                    "apps/*/templatetags/",
                    ".env.example"
                ],
                "branch": "dev"
            },
            
            "feature": {
                "files": {
                    ".env.example": {
                        "source": "environments/feature/.env.template",
                        "description": "Feature environment template for local development"
                    },
                    "README.md": {
                        "source": "environments/feature/README.md",
                        "description": "Feature development documentation"
                    },
                    "CHANGELOG.md": {
                        "source": "environments/feature/CHANGELOG.md",
                        "description": "Feature development changelog"
                    },
                    "requirements.txt": {
                        "source": "environments/feature/requirements.txt",
                        "description": "Feature development dependencies"
                    },
                    "adakings_backend/settings/__init__.py": {
                        "content": '''"""\nSettings package for Adakings Backend API\n\nEnvironment-specific settings loading:\n- production.py: Production environment\n- dev.py: Development environment similar to production\n- development.py: Local development environment\n- base.py: Shared base settings\n"""\n\nimport os\n\n# Default to development for feature branches\nENVIRONMENT = os.environ.get('DJANGO_ENVIRONMENT', 'development')\n\nif ENVIRONMENT == 'production':\n    from .production import *\n    print("🚀 Production environment loaded")\nelif ENVIRONMENT == 'dev':\n    from .dev import *\n    print("🔧 Dev environment loaded")\nelif ENVIRONMENT == 'development':\n    from .development import *  \n    print("🔧 Development environment loaded (feature branch)")\nelse:\n    # Fallback to development for feature branches\n    from .development import *\n    print("⚠️  Unknown environment '{}', falling back to development".format(ENVIRONMENT))''',
                        "description": "Feature branch settings loader"
                    }
                },
                "include_patterns": [
                    "apps/*/forms.py",
                    "apps/*/templatetags/",
                    "debug_*",
                    "test_*",
                    "*development*",
                    "*local*"
                ],
                "branch": "feature"
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
    
    def clean_deleted_local_branches(self):
        """Clean up local branches that have been deleted from the remote repository"""
        self.log_info("🧹 Cleaning up local branches deleted from remote...")
        
        try:
            # First, fetch and prune to get accurate remote state
            fetch_result = self.run_command("git fetch origin --prune", check=False)
            if not fetch_result:
                self.log_warning("Failed to fetch/prune remote branches")
                return False
            
            # Get current branch to avoid deleting it
            current_branch = self.get_current_branch()
            if not current_branch:
                self.log_warning("Could not determine current branch")
                return False
            
            # Get list of local branches
            result = self.run_command("git branch --format='%(refname:short)'", check=False)
            if not result:
                self.log_warning("Could not get local branches")
                return False
            
            local_branches = [b.strip() for b in result.stdout.strip().split('\n') if b.strip()]
            
            # Get list of remote tracking branches (what used to exist on remote)
            result = self.run_command("git for-each-ref --format='%(refname:short)' refs/remotes/origin/", check=False)
            if not result:
                self.log_warning("Could not get remote tracking branches")
                return False
            
            remote_tracking = [b.strip().replace('origin/', '') for b in result.stdout.strip().split('\n') if b.strip() and not b.strip().endswith('/HEAD')]
            
            # Get current remote branches (what actually exists on remote now)
            result = self.run_command("git ls-remote --heads origin", check=False)
            if not result:
                self.log_warning("Could not get current remote branches")
                return False
            
            current_remote = [line.split('\trefs/heads/')[-1] for line in result.stdout.strip().split('\n') if '\trefs/heads/' in line]
            
            # Protected branches that should never be deleted
            protected_branches = {'main', 'master', 'production', 'dev', 'development', current_branch}
            
            deleted_count = 0
            skipped_count = 0
            
            # Only process branches that exist locally and used to have remote tracking
            for local_branch in local_branches:
                # Skip if it's a protected branch
                if local_branch in protected_branches:
                    continue
                
                # Skip if it's the current branch
                if local_branch == current_branch:
                    continue
                
                # Only delete if:
                # 1. The branch had a remote tracking branch (was pushed before)
                # 2. But no longer exists on the remote (was deleted from remote)
                if local_branch in remote_tracking and local_branch not in current_remote:
                    # Check if branch has unpushed commits
                    # Compare with the last known remote state if possible
                    has_unpushed = False
                    
                    # Check if there's a remote tracking branch to compare against
                    remote_ref = f"origin/{local_branch}"
                    ref_exists = self.run_command(f"git show-ref --verify --quiet refs/remotes/{remote_ref}", check=False)
                    
                    if ref_exists:
                        # Check for unpushed commits
                        diff_result = self.run_command(f"git log {remote_ref}..{local_branch} --oneline", check=False)
                        if diff_result and diff_result.stdout.strip():
                            has_unpushed = True
                    
                    if has_unpushed:
                        self.log_warning(f"⚠️  Skipping {local_branch} - has unpushed commits")
                        skipped_count += 1
                        continue
                    
                    # Safe to delete - branch was deleted from remote and no unpushed commits
                    self.log_info(f"🗑️  Deleting local branch: {local_branch} (deleted from remote)")
                    delete_result = self.run_command(f"git branch -D {local_branch}", check=False)
                    if delete_result:
                        deleted_count += 1
                        self.log_info(f"✓ Deleted {local_branch}")
                    else:
                        self.log_warning(f"Failed to delete {local_branch}")
            
            if deleted_count > 0:
                self.log_success(f"✅ Cleaned up {deleted_count} branches deleted from remote")
            else:
                self.log_info("✓ No deleted remote branches to clean up")
            
            if skipped_count > 0:
                self.log_info(f"ℹ️  Skipped {skipped_count} branches with unpushed commits")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error during branch cleanup: {str(e)}")
            return False
    
    def get_highest_version_from_remote(self, branch_type, specific_feature_name=None):
        """Get the highest version from ALL remote branches of a specific type"""
        import re
        
        try:
            # Always fetch latest from remote first
            self.log_info("🔄 Fetching latest from remote to get accurate version info...")
            fetch_result = self.run_command("git fetch origin --prune", check=False)
            if fetch_result:
                self.log_info("✓ Remote branches updated and pruned")
            else:
                self.log_warning("⚠️  Failed to fetch from remote")
            
            # Get all remote branches
            result = self.run_command("git branch -r", check=False)
            if not result or not result.stdout:
                self.log_warning("Could not get remote branches")
                return "1.0.0"  # Start directly from 1.0.0
            
            remote_branches = [b.strip() for b in result.stdout.strip().split('\n') if b.strip()]
            all_versions = []
            
            self.log_info(f"🔍 Searching for {branch_type} versions in remote branches...")
            
            if branch_type == "production":
                # For production, check production branch VERSION file
                version_result = self.run_command("git show origin/production:environments/production/VERSION", check=False)
                if version_result and version_result.stdout.strip():
                    version = version_result.stdout.strip()
                    if re.match(r'^\d+\.\d+\.\d+$', version):
                        self.log_info(f"📋 Found production VERSION file: {version}")
                        return version
                
                # Fallback: check git tags
                tags_result = self.run_command("git tag --list --sort=-version:refname 'v*'", check=False)
                if tags_result and tags_result.stdout.strip():
                    tags = tags_result.stdout.strip().split('\n')
                    for tag in tags:
                        clean_tag = tag.lstrip('v')
                        if re.match(r'^\d+\.\d+\.\d+$', clean_tag):
                            self.log_info(f"📋 Found highest production tag: {clean_tag}")
                            return clean_tag
                
                return "1.0.0"  # Start directly from 1.0.0
            
            elif branch_type == "dev":
                # For dev, look for dev/x.x.x pattern
                for branch in remote_branches:
                    if branch.startswith("origin/dev/"):
                        version_part = branch.replace("origin/dev/", "")
                        if re.match(r'^\d+\.\d+\.\d+$', version_part):
                            major, minor, patch = map(int, version_part.split('.'))
                            all_versions.append((major, minor, patch, version_part))
                            self.log_info(f"🔍 Found dev version: {branch} -> {version_part}")
            
            elif branch_type.startswith("feature/"):
                # For feature branches, look for feature/name-x.x.x pattern
                if specific_feature_name:
                    # Look for this specific feature's versions
                    pattern_prefix = f"origin/feature/{specific_feature_name}-"
                    for branch in remote_branches:
                        if branch.startswith(pattern_prefix):
                            version_part = branch.replace(pattern_prefix, "")
                            if re.match(r'^\d+\.\d+\.\d+$', version_part):
                                major, minor, patch = map(int, version_part.split('.'))
                                all_versions.append((major, minor, patch, version_part))
                                self.log_info(f"🔍 Found {specific_feature_name} version: {branch} -> {version_part}")
                else:
                    # Look across ALL feature branches to get global highest
                    for branch in remote_branches:
                        if branch.startswith("origin/feature/") and "-" in branch:
                            # Extract version from any feature branch
                            parts = branch.split("-")
                            if len(parts) >= 2:
                                version_part = parts[-1]
                                if re.match(r'^\d+\.\d+\.\d+$', version_part):
                                    major, minor, patch = map(int, version_part.split('.'))
                                    all_versions.append((major, minor, patch, version_part))
                                    self.log_info(f"🔍 Found feature version: {branch} -> {version_part}")
            
            if not all_versions:
                self.log_info(f"🆕 No existing {branch_type} versions found, starting from 1.0.0")
                return "1.0.0"  # Start directly from 1.0.0
            
            # Sort and return highest version
            all_versions.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
            highest = all_versions[0][3]
            self.log_info(f"🏆 Highest {branch_type} version found: {highest}")
            return highest
            
        except Exception as e:
            self.log_warning(f"Error getting version from remote: {e}")
            return "1.0.0"  # Start directly from 1.0.0
    
    def read_version(self, version_type="production"):
        """Read current version from environment-specific version file"""
        # Environment-specific version file mapping
        version_file_mapping = {
            "production": "environments/production/VERSION", 
            "dev": "environments/dev/VERSION",
            "features": "environments/feature/VERSION"
        }
        
        # Use environment-specific version files only
        if version_type in version_file_mapping:
            version_file = self.base_dir / version_file_mapping[version_type]
            if version_file.exists():
                try:
                    version = version_file.read_text().strip()
                    if version and version.count('.') == 2:
                        return version
                except Exception as e:
                    self.log_warning(f"Failed to read {version_file}: {e}")
        
        # Default version for all environments - start from 1.0.0
        return "1.0.0"
    
    def bump_version(self, bump_type, current_version, version_type="production"):
        """Bump version based on type"""
        major, minor, patch = map(int, current_version.split('.'))
        
        if bump_type == 'major':
            new_version = f"{major + 1}.0.0"
            self.log_info(f"🚀 MAJOR version bump ({version_type}): {current_version} -> {new_version}")
        elif bump_type == 'minor':
            new_version = f"{major}.{minor + 1}.0"
            self.log_info(f"✨ MINOR version bump ({version_type}): {current_version} -> {new_version}")
        elif bump_type == 'patch':
            new_version = f"{major}.{minor}.{patch + 1}"
            self.log_info(f"🐛 PATCH version bump ({version_type}): {current_version} -> {new_version}")
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
    
    def update_version_files_and_changelog(self, new_version, version_type="production"):
        """Update version and changelog files using new environment-specific system only"""
        
        # Environment-specific version file mapping
        version_file_mapping = {
            "production": "environments/production/VERSION", 
            "dev": "environments/dev/VERSION",
            "features": "environments/feature/VERSION"
        }
        
        # Update the environment-specific version file
        if version_type in version_file_mapping:
            version_file = self.base_dir / version_file_mapping[version_type]
            version_file.parent.mkdir(parents=True, exist_ok=True)
            version_file.write_text(f"{new_version}\n")
            self.log_success(f"✅ Updated {version_type} environment version: {new_version}")
        else:
            self.log_error(f"Unknown version type: {version_type}")
            return
        
        # Update environment-specific changelog
        changelog_files = {
            "production": "environments/production/CHANGELOG.md",
            "dev": "environments/dev/CHANGELOG.md", 
            "features": "environments/feature/CHANGELOG.md"
        }
        
        if version_type in changelog_files:
            changelog_path = self.base_dir / changelog_files[version_type]
            if changelog_path.exists():
                changelog_content = changelog_path.read_text(encoding='utf-8')
                new_entry = f"## {new_version} - {datetime.now().strftime('%Y-%m-%d')}\n\n- Deployment to {version_type} environment\n\n"
                changelog_content = new_entry + changelog_content
                changelog_path.write_text(changelog_content, encoding='utf-8')
                self.log_success(f"✅ Updated {version_type} environment changelog")
            else:
                self.log_warning(f"Changelog not found: {changelog_path}")

    def validate_production_config(self):
        
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
        
        # Check .env.example file - create if missing for feature branches
        env_file = self.base_dir / ".env.example"
        if not env_file.exists():
            self.log_info("📝 Creating missing .env.example file for feature branch...")
            self.ensure_env_example_exists()
        
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
    
    def get_highest_remote_version_for_branch_type(self, branch_type):
        """Get the highest version number from ALL branches of a specific type on remote"""
        import re
        
        # Get all remote branches
        result = self.run_command("git branch -r", check=False)
        if not result or not result.stdout:
            return None
        
        remote_branches = result.stdout.strip().split('\n')
        all_versions = []
        
        if branch_type.startswith("feature/"):
            # Extract version numbers from ALL feature branches (pattern: feature/anything-x.x.x)
            for branch in remote_branches:
                branch = branch.strip()
                if branch.startswith("origin/feature/") and "-" in branch:
                    # Extract version from any feature branch like "origin/feature/anything-1.2.3"
                    # Split on last dash to get version part
                    parts = branch.split("-")
                    if len(parts) >= 2:
                        version_part = parts[-1]  # Get the last part after the last dash
                        try:
                            # Validate it's a proper semantic version (x.x.x)
                            version_components = version_part.split('.')
                            if len(version_components) == 3:
                                major, minor, patch = map(int, version_components)
                                all_versions.append((major, minor, patch, version_part))
                                self.log_info(f"🔍 Found feature version: {branch} -> {version_part}")
                        except (ValueError, IndexError):
                            continue
        
        elif branch_type == "dev":
            # Extract version numbers from ALL dev branches (pattern: dev/x.x.x)
            for branch in remote_branches:
                branch = branch.strip()
                if branch.startswith("origin/dev/"):
                    # Extract version from dev branch like "origin/dev/1.2.3"
                    version_part = branch.replace("origin/dev/", "")
                    try:
                        # Validate it's a proper semantic version (x.x.x)
                        version_components = version_part.split('.')
                        if len(version_components) == 3:
                            major, minor, patch = map(int, version_components)
                            all_versions.append((major, minor, patch, version_part))
                            self.log_info(f"🔍 Found dev version: {branch} -> {version_part}")
                    except (ValueError, IndexError):
                        continue
        
        if not all_versions:
            self.log_info(f"🔍 No {branch_type} branches with versions found on remote")
            return None
        
        # Sort versions and return the highest one
        all_versions.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
        highest_version = all_versions[0][3]
        self.log_info(f"🏆 Highest version found across ALL {branch_type} branches: {highest_version}")
        return highest_version
    
    def sync_local_branches_with_remote(self):
        """Sync local branches with remote - delete local branches that don't exist on remote"""
        self.log_info("🔄 Syncing local branches with remote...")
        
        # Get remote branches
        result = self.run_command("git branch -r", check=False)
        if not result or not result.stdout:
            self.log_warning("Could not fetch remote branches")
            return
        
        remote_branches = set()
        for branch in result.stdout.strip().split('\n'):
            branch = branch.strip()
            if branch.startswith('origin/') and branch != 'origin/HEAD':
                # Remove 'origin/' prefix to get branch name
                branch_name = branch.replace('origin/', '')
                remote_branches.add(branch_name)
        
        # Get local branches
        result = self.run_command("git branch", check=False)
        if not result or not result.stdout:
            return
        
        local_branches = []
        current_branch = None
        for branch in result.stdout.strip().split('\n'):
            branch = branch.strip()
            if branch.startswith('* '):
                current_branch = branch[2:]
                local_branches.append(current_branch)
            elif branch:
                local_branches.append(branch)
        
        # Delete local branches that don't exist on remote
        deleted_count = 0
        for local_branch in local_branches:
            if local_branch not in remote_branches and local_branch != current_branch:
                self.log_info(f"🗑️  Deleting local branch '{local_branch}' (not on remote)")
                result = self.run_command(f"git branch -D {local_branch}", check=False)
                if result and result.returncode == 0:
                    self.log_info(f"✓ Deleted '{local_branch}'")
                    deleted_count += 1
                else:
                    self.log_warning(f"Failed to delete '{local_branch}'")
        
        if deleted_count > 0:
            self.log_success(f"✅ Cleaned up {deleted_count} local branches not on remote")
        else:
            self.log_info("✓ All local branches are synced with remote")
    
    def ensure_env_example_exists(self):
        """Ensure .env.example file exists for feature branches"""
        env_example_path = self.base_dir / ".env.example"
        
        if env_example_path.exists():
            return
        
        # Create .env.example with development-friendly defaults
        env_example_content = '''# Development Environment Variables for Adakings Backend API
# Copy this file to .env and update with your local values

# Django Settings
DJANGO_ENVIRONMENT=development
DJANGO_SECRET_KEY=your-local-development-secret-key-change-this
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,*.localhost

# Database Configuration (SQLite for development, PostgreSQL for production-like testing)
# Option 1: SQLite (easier for development)
# DATABASE_URL=sqlite:///adakings_dev.db

# Option 2: PostgreSQL (more production-like)
DB_NAME=adakings_dev
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration (Console backend for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=dev@adakings.local

# Paystack Configuration (Test Keys Only - NEVER use live keys in development)
PAYSTACK_PUBLIC_KEY_LIVE=pk_test_your_test_public_key_here
PAYSTACK_SECRET_KEY_LIVE=sk_test_your_test_secret_key_here

# CORS Configuration (Development)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Redis Configuration (Optional - leave empty to disable)
REDIS_URL=redis://127.0.0.1:6379/0

# Security Headers (Disabled for development)
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False

# Monitoring & Logging (Development)
SENTRY_DSN=
LOG_LEVEL=DEBUG
DJANGO_LOG_LEVEL=DEBUG

# Performance Settings (Development)
MAX_UPLOAD_SIZE=10485760
CACHE_TIMEOUT=60

# API Rate Limiting (Disabled or relaxed for development)
RATE_LIMIT_ENABLE=False
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60

# Development Tools
ENABLE_SWAGGER_UI=True
ENABLE_REDOC=True
ENABLE_DEBUG_TOOLBAR=True

# Development Database (if using SQLite)
# DATABASE_ENGINE=sqlite3
# DATABASE_NAME=adakings_dev.db
'''
        
        env_example_path.write_text(env_example_content, encoding='utf-8')
        self.log_info("✓ Created .env.example file for feature branch")
    
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
    
    def apply_environment_gitignore(self, env_type):
        """Apply deployment-safe gitignore that preserves all environments"""
        self.log_info(f"📝 Applying deployment-safe gitignore for {env_type} environment...")
        
        # Instead of removing other environments, just ensure sensitive files are ignored
        # All environment folders should remain in git for proper version control
        
        self.log_info(f"✓ Using base gitignore - all environments preserved")
        
        # Do NOT remove other environment directories from git tracking
        # This was causing the deletion issue
        self.log_info("✓ All environment directories preserved in git tracking")
    
    def remove_other_environments_from_git(self, current_env):
        """DISABLED: This method previously removed other environment directories from git tracking
        
        This functionality has been disabled to prevent environment folders from being deleted.
        All environment directories should remain tracked in git for proper version control.
        """
        self.log_info(f"✓ Preserving all environment directories in git (removal disabled)")
        
        # This method is intentionally disabled to prevent the deletion issue
        # All environment folders (production, dev, feature) should remain in git
        # This ensures proper version control and prevents accidental deletion

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
        """Add only environment-specific files based on environment type"""
        self.log_info(f"Adding {env_type} environment-specific files...")
        
        # Define environment-specific files
        env_files = {
            "production": {
                "version_file": "environments/production/VERSION",
                "changelog": "environments/production/CHANGELOG.md",
                "env_template": "environments/production/.env.template",
                "requirements": "environments/production/requirements.txt",
                "deploy_script": "environments/production/deploy.sh",
                "deploy_ps_script": "environments/production/deploy.ps1",
                "readme": "environments/production/README.md",
                "settings_file": "adakings_backend/settings/production.py",
                "gunicorn_conf": "environments/production/gunicorn.conf.py",
                "nginx_conf": "environments/production/nginx.conf",
                "dockerfile": "environments/production/Dockerfile",
                "docker_compose": "environments/production/docker-compose.yml",
                "systemd_service": "environments/production/adakings-backend.service",
            },
            "dev": {
                "version_file": "environments/dev/VERSION",
                "changelog": "environments/dev/CHANGELOG.md",
                "env_template": "environments/dev/.env.template",
                "requirements": "environments/dev/requirements.txt",
                "deploy_script": "environments/dev/deploy.sh",
                "deploy_ps_script": "environments/dev/deploy.ps1",
                "readme": "environments/dev/README.md",
                "settings_file": "adakings_backend/settings/dev.py",
                "gunicorn_conf": "environments/dev/gunicorn.conf.py",
                "nginx_conf": "environments/dev/nginx.conf",
                "dockerfile": "environments/dev/Dockerfile",
                "docker_compose": "environments/dev/docker-compose.yml",
                "systemd_service": "environments/dev/adakings-backend-dev.service",
            },
            "feature": {
                "version_file": "environments/feature/VERSION",
                "changelog": "environments/feature/CHANGELOG.md",
                "env_template": "environments/feature/.env.template",
                "requirements": "environments/feature/requirements.txt",
                "setup_script": "environments/feature/setup.sh",
                "setup_ps_script": "environments/feature/setup.ps1",
                "readme": "environments/feature/README.md",
                "settings_file": "adakings_backend/settings/development.py",
            }
        }
        
        # Core application files (always needed)
        core_files = [
            "manage.py",
            "adakings_backend/__init__.py",
            "adakings_backend/urls.py",
            "adakings_backend/wsgi.py",
            "adakings_backend/asgi.py",
            "adakings_backend/settings/__init__.py",
            "adakings_backend/settings/base.py",
        ]
        
        # Core app patterns (always needed)
        core_patterns = [
            "apps/*/models.py",
            "apps/*/views.py",
            "apps/*/serializers.py",
            "apps/*/urls.py",
            "apps/*/__init__.py",
            "apps/*/apps.py",
            "apps/*/admin.py",
        ]
        
        # Add environment-specific files
        if env_type in env_files:
            env_file_list = env_files[env_type]
            
            for file_desc, file_path in env_file_list.items():
                if (self.base_dir / file_path).exists():
                    result = self.run_command(f"git add {file_path}", check=False)
                    if result and result.returncode == 0:
                        self.log_info(f"✓ Added {env_type} {file_desc}: {file_path}")
                else:
                    self.log_warning(f"⚠️  {env_type} {file_desc} not found: {file_path}")
        
        # Add core application files
        self.log_info("Adding core application files...")
        for file_path in core_files:
            if (self.base_dir / file_path).exists():
                result = self.run_command(f"git add {file_path}", check=False)
                if result and result.returncode == 0:
                    self.log_info(f"✓ Added core file: {file_path}")
        
        # Add core application patterns
        for pattern in core_patterns:
            result = self.run_command(f"git add {pattern}", check=False)
            if result and result.returncode == 0:
                self.log_info(f"✓ Added core pattern: {pattern}")
        
        # Add smart deploy script and environment guide (always useful)
        additional_files = [
            "smart_deploy.py",
            "ENVIRONMENT_GUIDE.md"
        ]
        
        for file_path in additional_files:
            if (self.base_dir / file_path).exists():
                result = self.run_command(f"git add {file_path}", check=False)
                if result and result.returncode == 0:
                    self.log_info(f"✓ Added utility: {file_path}")
        
        self.log_success(f"Added {env_type} environment-specific files and core application files")
    
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
        # Determine version type based on environment
        if target_env == "production" or target_env == "dev-test":
            version_type = "production"
        else:
            version_type = "features"
        
        current_version = self.read_version(version_type)
        if not current_version:
            raise Exception("Failed to read current version")
        
        new_version = self.bump_version(bump_type, current_version, version_type)
        if not new_version:
            raise Exception("Failed to bump version")
        
        self.update_version_files_and_changelog(new_version, version_type)
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
        valid_environments = ["production", "dev", "development"]
        if target_env not in valid_environments and not target_env.startswith("feature/"):
            self.log_error(f"Invalid environment: {target_env}. Please check and try again.")
            return False
        
        # Normalize environment type
        if target_env == "production":
            env_type = "production"
        elif target_env == "dev":
            env_type = "dev"
        else:
            env_type = "feature"
        
        # Determine version type and get current version FROM REMOTE
        if target_env == "production":
            version_type = "production"
            # Always get highest from remote for production
            current_version = self.get_highest_version_from_remote("production")
            self.log_info(f"📡 Using highest remote version for production: {current_version}")
        elif target_env == "dev":
            version_type = "production"
            # For dev branches, use highest remote version from ALL dev branches
            current_version = self.get_highest_version_from_remote("dev")
            self.log_info(f"📡 Using highest remote version for dev: {current_version}")
        else:
            version_type = "features"
            if target_env.startswith("feature/"):
                # For feature branches, use highest remote version from ALL feature branches
                feature_name = target_env.split('/', 1)[1] if '/' in target_env else None
                current_version = self.get_highest_version_from_remote("feature/", feature_name)
                self.log_info(f"📡 Using highest remote version for feature branches: {current_version}")
            else:
                current_version = self.get_highest_version_from_remote("dev")
        
        new_version = self.calculate_new_version(bump_type, current_version)
        
        # Determine target branch
        if target_env == "production":
            target_branch = "production"
        elif target_env == "dev":
            # For dev branches, format: dev/x.x.x
            target_branch = f"dev/{new_version}"
        elif target_env == "development":
            target_branch = "dev"
        elif target_env.startswith("feature/"):
            # For feature branches, append version: feature/customname-x.x.x
            feature_name = target_env  # This is already feature/customname
            target_branch = f"{feature_name}-{new_version}"
        else:
            target_branch = target_env
        
        try:
            # Sync local branches with remote before starting deployment
            self.sync_local_branches_with_remote()
            
            # Clean up deleted local branches before starting deployment
            self.clean_deleted_local_branches()
            
            # Backup current state
            self.backup_current_state()
            
            # Switch to target branch FIRST (before any file changes)
            if not self.switch_branch(target_branch):
                raise Exception(f"Failed to switch to branch: {target_branch}")
            
            # Now update version files and changelog on the target branch
            version_type = "production" if target_env in ["production", "dev"] else "features"
            self.update_version_files_and_changelog(new_version, version_type)
            
            # Ensure .env.example exists for feature branches before validation
            if target_env.startswith("feature/") or target_env == "development":
                self.ensure_env_example_exists()
            
            # Pre-deployment checks
            if not self.deployment_checks(target_env):
                raise Exception("Pre-deployment checks failed")
            
            # Set up environment files
            if not self.setup_environment_files(env_type):
                raise Exception(f"Failed to setup {env_type} files")
            
            # Apply environment-specific gitignore to exclude other environments
            self.apply_environment_gitignore(env_type)
            
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
            
            # Automatically merge to main after successful deployment
            self.log_info(f"\n🔄 Auto-merging {target_branch} to main branch...")
            merge_success = self.merge_to_main(target_branch)
            
            if merge_success:
                self.log_success(f"✅ Successfully merged {target_branch} into main!")
            else:
                self.log_warning(f"⚠️  Deployment succeeded but merge to main failed")
                self.log_warning(f"You can manually merge later with: python smart_deploy.py main")
            
            return True
            
        except Exception as e:
            self.log_error(f"Deployment failed: {str(e)}")
            self.log_info("Restoring backup...")
            self.restore_backup()
            return False
    
    def merge_to_main(self, source_branch=None):
        """Merge current branch into main branch"""
        self.log_info("🚀 Starting merge to main branch...")
        
        # Get current branch if no source specified
        if not source_branch:
            source_branch = self.get_current_branch()
            if not source_branch:
                self.log_error("Could not determine current branch")
                return False
        
        self.log_info(f"📍 Source branch: {source_branch}")
        
        # Check for uncommitted changes first
        status_result = self.run_command("git status --porcelain", check=False)
        has_changes = bool(status_result and status_result.stdout.strip())
        
        if has_changes:
            self.log_warning("⚠️  Uncommitted changes detected. These need to be handled for main branch merge.")
            
            # Show what changes exist
            status_show = self.run_command("git status --short", check=False)
            if status_show and status_show.stdout.strip():
                self.log_info("📋 Current changes:")
                for line in status_show.stdout.strip().split('\n'):
                    self.log_info(f"   {line}")
            
            # Special handling for backup directory files - these should be ignored
            self.log_info("🧹 Cleaning up backup directory files that might interfere...")
            
            # Remove any changes in the backup directory
            backup_clean_result = self.run_command("git checkout -- .deploy_backup/", check=False)
            if backup_clean_result:
                self.log_info("✓ Cleaned up backup directory changes")
            
            # Check if we still have changes after cleanup
            status_result = self.run_command("git status --porcelain", check=False)
            has_changes = bool(status_result and status_result.stdout.strip())
            
            if has_changes:
                # For main branch operations, we need to commit remaining changes
                self.log_info("💡 Committing remaining changes before switching to main...")
                
                # Add all changes
                add_result = self.run_command("git add .", check=False)
                if not add_result:
                    self.log_error("Failed to add changes")
                    return False
                
                # Create a commit message
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_msg = f"feat: Auto-commit before merge to main\n\nBranch: {source_branch}\nTimestamp: {timestamp}\n\nChanges committed automatically by smart_deploy.py before merging to main."
                
                # Commit changes
                commit_result = self.run_command(['git', 'commit', '-m', commit_msg], shell=False, check=False)
                if not commit_result:
                    self.log_error("Failed to commit changes")
                    return False
                
                self.log_success("✅ Successfully committed changes on current branch")
            else:
                self.log_success("✅ All backup directory changes cleaned up, no commit needed")
        
        try:
            # Backup current state
            self.backup_current_state()
            
            # Ensure we have the latest changes from remote
            self.log_info("📡 Fetching latest changes from remote...")
            fetch_result = self.run_command("git fetch origin --prune")
            if not fetch_result:
                self.log_warning("Failed to fetch from remote")
            
            # Check if main branch exists locally
            main_exists_locally = self.run_command("git branch --list main", check=False)
            main_exists_locally = bool(main_exists_locally and main_exists_locally.stdout.strip())
            
            # Check if main branch exists on remote
            remote_branches_result = self.run_command("git ls-remote --heads origin", check=False)
            main_exists_remotely = False
            if remote_branches_result and remote_branches_result.stdout:
                main_exists_remotely = 'refs/heads/main' in remote_branches_result.stdout
            
            # Switch to or create main branch (now safe since we committed changes)
            if main_exists_locally:
                self.log_info("🔄 Switching to existing main branch...")
                switch_result = self.run_command("git checkout main")
                if not switch_result:
                    # Try git switch as fallback
                    switch_result = self.run_command("git switch main", check=False)
                    if not switch_result:
                        raise Exception("Failed to switch to main branch")
                
                # Pull latest changes if main exists remotely
                if main_exists_remotely:
                    self.log_info("⬇️ Pulling latest changes from remote main...")
                    pull_result = self.run_command("git pull origin main", check=False)
                    if not pull_result:
                        self.log_warning("Failed to pull from remote main, continuing...")
            else:
                if main_exists_remotely:
                    self.log_info("📥 Creating local main branch from remote...")
                    checkout_result = self.run_command("git checkout -b main origin/main")
                else:
                    self.log_info("🆕 Creating new main branch...")
                    checkout_result = self.run_command("git checkout -b main")
                
                if not checkout_result:
                    raise Exception("Failed to create/checkout main branch")
            
            # If we're already on main, we're done with switching
            if source_branch == "main":
                self.log_info("✅ Already on main branch")
                # Just push current state to remote
                push_result = self.run_command("git push origin main")
                if push_result:
                    self.log_success("🎉 Successfully pushed main branch to remote!")
                    return True
                else:
                    raise Exception("Failed to push main branch to remote")
            
            # Merge changes from source branch
            self.log_info(f"🔄 Merging changes from {source_branch} into main...")
            merge_result = self.run_command(['git', 'merge', source_branch, '--no-ff', '-m', f'Merge {source_branch} into main'], shell=False, check=False)
            
            if not merge_result or merge_result.returncode != 0:
                # Check if it's just a "already up to date" situation
                if merge_result and "Already up to date" in merge_result.stdout:
                    self.log_info("✅ Main is already up to date with source branch")
                else:
                    self.log_error(f"Merge failed: {merge_result.stderr if merge_result else 'Unknown error'}")
                    # Try to resolve merge conflicts or provide guidance
                    status_result = self.run_command("git status --porcelain", check=False)
                    if status_result and status_result.stdout.strip():
                        self.log_error("📋 Merge conflicts detected:")
                        self.log_error(status_result.stdout.strip())
                        self.log_error("\n🔧 Please resolve merge conflicts manually and then run:")
                        self.log_error("   git add .")
                        self.log_error("   git commit")
                        self.log_error(f"   git push origin main")
                        return False
                    else:
                        raise Exception(f"Merge failed: {merge_result.stderr if merge_result else 'Unknown error'}")
            
            # Push merged changes to remote main
            self.log_info("⬆️ Pushing merged changes to remote main...")
            push_result = self.run_command("git push origin main")
            if not push_result:
                raise Exception("Failed to push to remote main")
            
            self.log_success(f"🎉 Successfully merged {source_branch} into main and pushed to remote!")
            self.log_info("📍 Main branch is now up to date with all changes")
            
            # Switch back to source branch
            if source_branch != "main":
                self.log_info(f"🔙 Switching back to {source_branch}...")
                switch_back = self.run_command(f"git checkout {source_branch}", check=False)
                if not switch_back:
                    switch_back = self.run_command(f"git switch {source_branch}", check=False)
                    if not switch_back:
                        self.log_warning(f"Failed to switch back to {source_branch}")
                        self.log_info(f"You are currently on main branch. To switch back manually: git checkout {source_branch}")
                    else:
                        self.log_success(f"✅ Switched back to {source_branch}")
                else:
                    self.log_success(f"✅ Switched back to {source_branch}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Merge to main failed: {str(e)}")
            self.log_info("Restoring backup...")
            self.restore_backup()
            return False


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(__doc__)
        print("\nAvailable environments:")
        print("  production [major|minor|patch]     - Deploy to production branch with version bump")
        print("  dev [minor|patch]                  - Deploy to dev branch (production-like with dev values)")
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
    
    # Special handling for 'main' branch merge
    if target_env == "main":
        print(f"🎯 Target: Merge current branch into main")
        print("📝 This will merge your current branch into the main branch")
        
        # Confirm main merge
        print("⚠️  WARNING: This will merge into MAIN branch!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Merge cancelled.")
            sys.exit(0)
        
        # Run merge to main
        success = deployer.merge_to_main()
        if success:
            print("✅ Successfully merged into main branch!")
        else:
            print("❌ Failed to merge changes into main branch")
        sys.exit(0 if success else 1)
    
    # Show deployment information using same logic as deploy function
    if target_env == "production" or target_env == "dev-test":
        version_type = "production"
    else:
        version_type = "features"
    
    current_version = deployer.read_version(version_type)
    new_version = deployer.calculate_new_version(bump_type, current_version) if current_version else "unknown"
    
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
