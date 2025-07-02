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
    
    def get_highest_remote_version(self):
        """Get the highest version number from all remote branches."""
        try:
            # Get all remote branches
            remote_branches = self.run_command("git branch -r").stdout
            branches = [branch.strip() for branch in remote_branches.split('\n') if branch.strip() and not '->' in branch]
            
            versions = []
            
            # Extract version numbers from branch names
            for branch in branches:
                # Look for patterns like feature/name-x.x.x or dev/x.x.x
                if '-' in branch and ('feature/' in branch or 'dev/' in branch):
                    # Extract version from feature/name-x.x.x
                    version_part = branch.split('-')[-1]
                    if self.is_valid_version(version_part):
                        versions.append(version_part)
                elif branch.startswith('origin/dev/') and branch.count('/') == 2:
                    # Extract version from dev/x.x.x
                    version_part = branch.split('/')[-1]
                    if self.is_valid_version(version_part):
                        versions.append(version_part)
            
            if not versions:
                return "1.0.0"  # Default if no versions found
            
            # Sort versions and return the highest
            versions.sort(key=lambda v: tuple(map(int, v.split('.'))))
            return versions[-1]
            
        except Exception:
            return "1.0.0"  # Fallback to default
    
    def is_valid_version(self, version_str):
        """Check if a string is a valid semantic version (x.x.x)."""
        try:
            parts = version_str.split('.')
            if len(parts) != 3:
                return False
            for part in parts:
                int(part)  # Will raise ValueError if not a number
            return True
        except (ValueError, AttributeError):
            return False

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
        self.version_file.write_text(new_version, encoding='utf-8')
        self.log_success(f"Updated VERSION to {new_version}")
        
        # Update CHANGELOG.md
        changelog_file = self.base_dir / "CHANGELOG.md"
        if changelog_file.exists():
            try:
                current_content = changelog_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Fallback for files with different encoding
                current_content = changelog_file.read_text(encoding='latin-1')
            
            # Create new changelog entry
            timestamp = datetime.now().strftime("%Y-%m-%d")
            new_entry = f"""# Changelog

## [{new_version}] - {timestamp}

### {target_env.title()} Release
- {commit_message if commit_message else f"Deployed to {target_env} environment"}
- Version bump: {self.get_current_version()} -> {new_version}

{current_content.replace('# Changelog', '').strip()}
"""
            
            changelog_file.write_text(new_entry, encoding='utf-8')
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
        """Sync local repository with remote - fetch all branches."""
        self.log_info("Syncing with remote repository...")
        # Fetch all remote branches and tags
        self.run_command("git fetch --all")
        
        # Update current branch only if it exists remotely
        current_branch = self.get_current_branch()
        
        # Check if current branch exists remotely
        remote_branches = self.run_command("git branch -r").stdout
        if f"origin/{current_branch}" in remote_branches:
            try:
                self.run_command(f"git pull origin {current_branch}")
                self.log_info(f"Updated {current_branch} from remote")
            except subprocess.CalledProcessError:
                self.log_warning(f"Could not pull from origin/{current_branch}")
        else:
            self.log_info(f"Branch {current_branch} doesn't exist remotely - skipping pull")

    def create_or_checkout_branch(self, branch_name):
        """Create or checkout the target branch, preserving current changes."""
        
        # Get current branch to know where we're coming from
        current_branch = self.get_current_branch()
        self.log_info(f"Currently on branch: {current_branch}")
        
        # Check if local branch exists first
        local_branches = self.run_command("git branch").stdout
        # Clean branch names and check if our target branch exists
        clean_local_branches = [branch.strip().replace('*', '').strip() for branch in local_branches.split('\n') if branch.strip()]
        local_branch_exists = branch_name in clean_local_branches
        
        # Check remote branches (precise matching to avoid partial matches)
        remote_branches = self.run_command("git branch -r").stdout
        # Split by lines and clean each branch name for exact matching
        clean_remote_branches = [branch.strip() for branch in remote_branches.split('\n') if branch.strip() and not '->' in branch]
        remote_branch_exists = f"origin/{branch_name}" in clean_remote_branches
        
        self.log_info(f"Local branch exists: {local_branch_exists}")
        self.log_info(f"Remote branch exists: {remote_branch_exists}")
        
        if local_branch_exists:
            # Local branch exists, just checkout
            self.run_command(f"git checkout {branch_name}")
            if remote_branch_exists:
                # Pull latest changes if remote exists
                try:
                    self.run_command(f"git pull origin {branch_name}")
                except subprocess.CalledProcessError:
                    self.log_warning(f"Could not pull from origin/{branch_name}")
            self.log_info(f"Checked out existing local branch: {branch_name}")
        elif remote_branch_exists:
            # Remote branch exists but not locally - create local tracking branch
            self.run_command(f"git checkout -b {branch_name} origin/{branch_name}")
            self.log_info(f"Created local branch tracking origin/{branch_name}")
        else:
            # Neither local nor remote branch exists - create new branch
            self.run_command(f"git checkout -b {branch_name}")
            self.log_success(f"Created new branch: {branch_name} from {current_branch}")

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
        
        # Pre-deployment checks
        if not self.ensure_clean_working_directory():
            return False

        # Backup current state
        backup_path = self.backup_current_state()

        try:
            # Sync with remote first to get latest remote branches
            self.sync_with_remote()
            
            # Determine which version to use as base
            if target_env.startswith("feature/") or target_env == "dev":
                # For feature and dev branches, use highest remote version
                current_version = self.get_highest_remote_version()
                self.log_info(f"Using highest remote version as base: {current_version}")
            else:
                # For production, use local VERSION file
                current_version = self.get_current_version()
                self.log_info(f"Using local version as base: {current_version}")
            
            # Calculate new version
            new_version = self.bump_version(bump_type, current_version)
            
            # Parse target environment and create versioned branch names
            if target_env.startswith("feature/"):
                env_type = "feature"
                feature_name = target_env.replace("feature/", "")
                branch_name = f"feature/{feature_name}-{new_version}"
            elif target_env == "dev":
                env_type = "dev"
                branch_name = f"dev/{new_version}"
            elif target_env == "production":
                env_type = "production"
                branch_name = "prod"  # Single production branch
            else:
                self.log_error(f"Invalid target environment: {target_env}")
                return False
            
            self.log_info(f"Target branch: {branch_name}")
            self.log_info(f"Version: {current_version} -> {new_version}")

            # Create/checkout target branch
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
