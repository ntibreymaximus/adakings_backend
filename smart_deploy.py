#!/usr/bin/env python3
"""
Smart Deployment Script for Adakings Backend API
Manages environment-specific files and deployments

Usage:
    python smart_deploy.py production    # Deploy to production branch
    python smart_deploy.py dev           # Deploy to dev branch  
    python smart_deploy.py feature/name  # Deploy to feature branch
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
    
    def deploy(self, target_env, commit_message=""):
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
            
            # Switch to target branch
            if not self.switch_branch(target_branch):
                raise Exception(f"Failed to switch to branch: {target_branch}")
            
            # Set up environment files
            if not self.setup_environment_files(env_type):
                raise Exception(f"Failed to setup {env_type} files")
            
            # Clean environment-specific files
            self.clean_environment_files(env_type)
            
            # Commit and push
            if not self.commit_and_push(env_type, commit_message):
                raise Exception("Failed to commit and push changes")
            
            self.log_success(f"🎉 Successfully deployed to {target_env} environment!")
            self.log_info(f"Branch: {target_branch}")
            self.log_info(f"Environment: {env_type}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Deployment failed: {str(e)}")
            self.log_info("Restoring backup...")
            self.restore_backup()
            return False


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        print("\nAvailable environments:")
        print("  production     - Deploy to production branch")
        print("  dev            - Deploy to dev branch")
        print("  feature/name   - Deploy to feature branch")
        sys.exit(1)
    
    target_env = sys.argv[1]
    deployer = SmartDeployer()
    
    # Confirm deployment
    print(f"🎯 Target Environment: {target_env}")
    if target_env == "production":
        print("⚠️  WARNING: This will deploy to PRODUCTION!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("Deployment cancelled.")
            sys.exit(0)
    
    # Run deployment
    success = deployer.deploy(target_env)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
