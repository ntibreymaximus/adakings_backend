#!/usr/bin/env python3
"""
Smart Deployment Script for Adakings Backend API - Unified Environment
Manages deployments and version management for the unified Django setup

Usage:
    python smart_deploy.py production [major|minor|patch]    # Deploy to production branch with version bump
    python smart_deploy.py dev [minor|patch]                 # Deploy to dev branch with version bump
    python smart_deploy.py feature/name [patch]              # Deploy to feature branch with version bump
    
Examples:
    python smart_deploy.py production major                  # v1.0.0 -> v2.0.0
    python smart_deploy.py dev minor                         # v1.0.0 -> v1.1.0
    python smart_deploy.py feature/auth patch               # v1.0.0 -> v1.0.1

Note: Since environments are now unified, this script focuses on git workflow 
and version management without environment-specific file copying.
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
        self.version_file = self.base_dir / "VERSION"
        
        # Simple version tracking since environments are unified
        self.version_config = {
            "production": {"file": "VERSION", "initial": "1.0.0"},
            "dev": {"file": "VERSION", "initial": "0.9.0"},
            "feature": {"file": "VERSION", "initial": "0.8.0"}
        }
        
        # Git workflow configuration
        self.git_config = {
            "production": {
                "target_branch": "prod",
                "merge_with": "main",  # Production goes to prod branch then merges with main
                "description": "Production release"
            },
            "dev": {
                "target_branch": "dev",
                "merge_with": "main",  # Dev merges with main after deployment
                "description": "Development release"
            },
            "feature": {
                "target_branch": None,  # Will be set dynamically
                "merge_with": "main",  # Feature branches merge with main
                "description": "Feature branch"
            }
        }

    def log_info(self, message):
        """Log informational message."""
        print(f"📍 {message}")

    def log_success(self, message):
        """Log success message."""
        print(f"✅ {message}")

    def log_warning(self, message):
        """Log warning message."""
        print(f"⚠️  {message}")

    def log_error(self, message):
        """Log error message."""
        print(f"❌ {message}")

    def run_command(self, command, check=True, shell=None):
        """Execute shell command and return result."""
        try:
            if shell is None:
                shell = os.name == 'nt'  # Use shell on Windows
            
            self.log_info(f"Running: {command}")
            result = subprocess.run(
                command, 
                shell=shell, 
                capture_output=True, 
                text=True, 
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            self.log_error(f"Command failed: {e}")
            self.log_error(f"STDOUT: {e.stdout}")
            self.log_error(f"STDERR: {e.stderr}")
            raise

    def get_current_branch(self):
        """Get the current git branch."""
        result = self.run_command("git branch --show-current")
        return result.stdout.strip()

    def backup_current_state(self):
        """Create backup of current state."""
        self.log_info("Creating backup of current state...")
        
        # Create backup directory
        backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = self.backup_dir / f"backup_{backup_time}"
        current_backup.mkdir(parents=True, exist_ok=True)
        
        # Backup key files
        key_files = [".env", "VERSION", "CHANGELOG.md", "requirements.txt"]
        for file in key_files:
            if (self.base_dir / file).exists():
                shutil.copy2(self.base_dir / file, current_backup / file)
        
        self.log_success(f"Backup created at: {current_backup}")
        return current_backup

    def get_current_version(self):
        """Get current version from VERSION file."""
        if self.version_file.exists():
            return self.version_file.read_text().strip()
        return "1.0.0"

    def bump_version(self, bump_type, current_version):
        """Bump version based on type."""
        major, minor, patch = map(int, current_version.split('.'))
        
        if bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        elif bump_type == 'patch':
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")
        
        return f"{major}.{minor}.{patch}"

    def update_version_and_changelog(self, new_version, target_env, commit_message=""):
        """Update version file and changelog."""
        # Update VERSION file
        self.version_file.write_text(new_version)
        self.log_success(f"Updated VERSION to {new_version}")
        
        # Update CHANGELOG.md
        changelog_file = self.base_dir / "CHANGELOG.md"
        if changelog_file.exists():
            current_content = changelog_file.read_text()
            
            # Create new changelog entry
            timestamp = datetime.now().strftime("%Y-%m-%d")
            new_entry = f"""# Changelog

## [{new_version}] - {timestamp}

### {target_env.title()} Release
- {commit_message if commit_message else f"Deployed to {target_env} environment"}
- Version bump: {self.get_current_version()} -> {new_version}

{current_content.replace('# Changelog', '').strip()}
"""
            
            changelog_file.write_text(new_entry)
            self.log_success("Updated CHANGELOG.md")

    def generate_commit_message_from_changes(self):
        """Generate a descriptive commit message based on file changes."""
        try:
            # Get status of changed files
            result = self.run_command("git status --porcelain")
            changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if not changes:
                return "Auto-commit: Prepare for deployment"
            
            # Categorize changes
            modified_files = []
            added_files = []
            deleted_files = []
            
            for change in changes:
                if not change.strip():
                    continue
                status = change[:2]
                filename = change[3:].strip()
                
                if 'M' in status:
                    modified_files.append(filename)
                elif 'A' in status:
                    added_files.append(filename)
                elif 'D' in status:
                    deleted_files.append(filename)
                else:
                    modified_files.append(filename)  # Default to modified
            
            # Generate descriptive message
            message_parts = []
            
            if modified_files:
                if len(modified_files) == 1:
                    message_parts.append(f"Update {modified_files[0]}")
                else:
                    message_parts.append(f"Update {len(modified_files)} files: {', '.join(modified_files[:3])}{'...' if len(modified_files) > 3 else ''}")
            
            if added_files:
                if len(added_files) == 1:
                    message_parts.append(f"Add {added_files[0]}")
                else:
                    message_parts.append(f"Add {len(added_files)} files")
            
            if deleted_files:
                if len(deleted_files) == 1:
                    message_parts.append(f"Remove {deleted_files[0]}")
                else:
                    message_parts.append(f"Remove {len(deleted_files)} files")
            
            return " | ".join(message_parts) if message_parts else "Auto-commit: Prepare for deployment"
            
        except Exception:
            return "Auto-commit: Prepare for deployment"
    
    def ensure_clean_working_directory(self):
        """Ensure git working directory is clean by auto-committing pending changes."""
        result = self.run_command("git status --porcelain")
        if result.stdout.strip():
            self.log_warning("Working directory has uncommitted changes.")
            self.log_info("Uncommitted changes:")
            print(result.stdout)
            
            self.log_info("Auto-committing pending changes before deployment...")
            
            # Generate descriptive commit message based on changes
            commit_msg = self.generate_commit_message_from_changes()
            
            # Add all changes
            self.run_command("git add .")
            
            # Commit changes to current branch (but don't push)
            self.run_command(f'git commit -m "{commit_msg}"')
            
            self.log_success("Committed pending changes")
        return True

    def sync_with_remote(self):
        """Sync local repository with remote."""
        self.log_info("Syncing with remote repository...")
        self.run_command("git fetch origin")
        self.run_command("git pull origin")

    def create_or_checkout_branch(self, branch_name):
        """Create or checkout the target branch."""
        try:
            # Try to checkout existing branch
            self.run_command(f"git checkout {branch_name}")
            self.log_info(f"Checked out existing branch: {branch_name}")
        except subprocess.CalledProcessError:
            # Create new branch
            self.run_command(f"git checkout -b {branch_name}")
            self.log_success(f"Created new branch: {branch_name}")

    def push_to_branch(self, branch_name, commit_message):
        """Commit changes and push to branch."""
        # Add all changes
        self.run_command("git add .")
        
        # Commit changes
        self.run_command(f'git commit -m "{commit_message}"')
        
        # Push to remote
        self.run_command(f"git push origin {branch_name}")
        self.log_success(f"Pushed changes to {branch_name}")

    def merge_with_main(self, source_branch):
        """Merge the source branch with main, taking all changes from source branch."""
        self.log_info(f"Merging {source_branch} with main...")
        
        # Checkout main
        self.run_command("git checkout main")
        
        # Pull latest main
        self.run_command("git pull origin main")
        
        # Merge source branch with strategy to favor incoming changes (theirs)
        # This ensures that everything from the new branch overwrites main
        try:
            self.run_command(f"git merge {source_branch}")
        except subprocess.CalledProcessError:
            # If there are conflicts, resolve them by taking the source branch version
            self.log_warning("Merge conflicts detected. Resolving by taking source branch changes...")
            self.run_command(f"git merge -X theirs {source_branch}")
        
        # Push updated main
        self.run_command("git push origin main")
        
        self.log_success(f"Successfully merged {source_branch} with main")

    def deploy(self, target_env, bump_type, commit_message=""):
        """Main deployment function."""
        self.log_info(f"🚀 Starting deployment to {target_env} environment")
        
        # Parse target environment
        if target_env.startswith("feature/"):
            env_type = "feature"
            branch_name = target_env
        else:
            env_type = target_env
            branch_name = self.git_config[env_type]["target_branch"]
            if env_type == "feature":
                self.log_error("Feature branches must be specified as 'feature/name'")
                return False

        # Pre-deployment checks
        if not self.ensure_clean_working_directory():
            return False

        # Backup current state
        backup_path = self.backup_current_state()

        try:
            # Sync with remote
            self.sync_with_remote()

            # Get current version and calculate new version
            current_version = self.get_current_version()
            new_version = self.bump_version(bump_type, current_version)
            
            self.log_info(f"Version: {current_version} -> {new_version}")

            # Create/checkout target branch
            if env_type == "feature":
                self.create_or_checkout_branch(branch_name)
            else:
                self.create_or_checkout_branch(branch_name)

            # Update version and changelog
            final_commit_message = commit_message or f"Version: {new_version} feat: Deploy to {target_env} environment"
            self.update_version_and_changelog(new_version, target_env, final_commit_message)

            # Commit and push changes
            self.push_to_branch(branch_name, final_commit_message)

            # Merge with main if configured
            merge_target = self.git_config[env_type]["merge_with"]
            if merge_target:
                self.merge_with_main(branch_name)

            self.log_success(f"🎉 Successfully deployed to {target_env}!")
            self.log_success(f"📦 Version: {new_version}")
            self.log_success(f"🌿 Branch: {branch_name}")
            
            if merge_target:
                self.log_success(f"🔀 Merged with {merge_target}")

            return True

        except Exception as e:
            self.log_error(f"Deployment failed: {e}")
            self.log_warning("You may need to manually resolve issues and restore from backup")
            self.log_info(f"Backup location: {backup_path}")
            return False

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target_env = sys.argv[1]
    bump_type = sys.argv[2] if len(sys.argv) > 2 else "patch"
    commit_message = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""

    # Validate bump type
    valid_bump_types = ["major", "minor", "patch"]
    if bump_type not in valid_bump_types:
        print(f"❌ Invalid bump type: {bump_type}")
        print(f"Valid types: {', '.join(valid_bump_types)}")
        sys.exit(1)

    # Validate target environment
    valid_envs = ["production", "dev"]
    if not (target_env in valid_envs or target_env.startswith("feature/")):
        print(f"❌ Invalid target environment: {target_env}")
        print(f"Valid environments: {', '.join(valid_envs)}, feature/name")
        sys.exit(1)

    # All environments now support major, minor, and patch version bumps
    # No restrictions on version bump types per environment

    # Initialize deployer and run deployment
    deployer = SmartDeployer()
    success = deployer.deploy(target_env, bump_type, commit_message)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
