#!/usr/bin/env python3
"""
Smart Deployment Script for Adakings Backend API - Branch-Specific Versioning
Manages deployments with independent version tracking for feature, dev, and production branches

Features:
- Branch-Specific Versioning: Independent version sequences for each branch type
- Multi-Version Tracking: VERSION file maintains separate versions for feature/dev/production
- Smart Git Workflow: Feature→main merge, dev→dev only, production→dev+prod with tags
- Production Tagging: Tags production versions on dev branch for tracking
- Remote Version Detection: Scans branch-specific remote versions for highest version
- Intelligent Version Bumping: Automatic major.minor.patch increments per branch type
- Atomic Commit Handling: Includes uncommitted changes in deployment commit (no premature commits)
- Comprehensive Logging: Detailed deployment history and changelogs
- Clean Git Workflow: Creates new branches and commits all changes together
- Branch Management: Creates, merges, and manages git branches with user confirmation

Usage:
    python smart_deploy.py production [major|minor|patch] ["commit message"]
    python smart_deploy.py dev [major|minor|patch] ["commit message"]
    python smart_deploy.py feature/name [major|minor|patch] ["commit message"]
    
Examples:
    # Feature deployment - continuous versioning across all features
    python smart_deploy.py feature/auth patch "Add authentication"
    # Result: feature/auth-1.0.0 (first feature)
    
    python smart_deploy.py feature/payments patch "Add payment system"
    # Result: feature/payments-1.0.1 (continues from previous feature version)
    
    # Dev deployment - independent dev versioning
    python smart_deploy.py dev minor "New user features"
    # Result: dev/1.1.0 (independent from feature versions)
    
    # Production deployment - independent production versioning
    python smart_deploy.py production major "Breaking changes"
    # Result: pushes to dev with prod-x.x.x tag, then pushes to prod branch

Version Management:
- Branch-Specific Versioning: Each branch type maintains its own version sequence
- Feature branches: Continuous versioning across all features (feature/name-x.x.x)
- Dev branches: Independent dev versioning (dev/x.x.x)
- Production branches: Independent production versioning (pushes to prod branch only)
- VERSION file format: feature=x.x.x\ndev=x.x.x\nproduction=x.x.x
- First deployment per branch type: Automatically uses 1.0.0
- Subsequent deployments: Bumps from highest version within that branch type

VERSION File Example:
    feature=1.0.5     # Latest feature version
    dev=1.2.1         # Latest dev version  
    production=1.1.0  # Latest production version

Git Workflow:
- Feature deployments: Push to feature/name-x.x.x, then merge with main
- Dev deployments: Push to dev/x.x.x and create/update devtest branch (no merge with main)
- Production deployments: Push to prod/x.x.x and create/update live branch (no merge with main)

Branch Versioning Strategy:
Each environment maintains its own versioned branches:
- Feature: feature/name-x.x.x (merged with main)
- Dev: dev/x.x.x (updates devtest branch)
- Production: prod/x.x.x (updates live branch)

Note: Each branch type deployment only updates its specific version in the VERSION file,
leaving other branch type versions unchanged.
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
        # Use the directory where the smart_deploy.py script is located
        self.base_dir = Path(__file__).parent.absolute()
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
                "merge_with": None,  # Production pushes to prod branch and updates live
                "description": "Production release with live branch update"
            },
            "dev": {
                "target_branch": "dev",
                "merge_with": None,  # Dev pushes to dev branch and updates devtest
                "description": "Development release with devtest branch update"
            },
            "feature": {
                "target_branch": None,  # Will be set dynamically
                "merge_with": "main",  # Feature branches merge with main after push
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
        """Get current version from VERSION file (legacy single version)."""
        if self.version_file.exists():
            content = self.version_file.read_text().strip()
            # Check if it's the new format
            if '\n' in content or 'feature=' in content:
                return self.get_version_from_file('feature')  # Default to feature for legacy
            return content
        return "1.0.0"
    
    def get_version_from_file(self, branch_type):
        """Get version for specific branch type from VERSION file."""
        if not self.version_file.exists():
            return "1.0.0"
        
        try:
            content = self.version_file.read_text().strip()
            
            # Handle legacy single version format
            if '\n' not in content and 'feature=' not in content and 'dev=' not in content and 'production=' not in content:
                # Legacy format - return the single version for any branch type
                return content
            
            # Parse new multi-branch format
            versions = {
                'feature': '1.0.0',
                'dev': '1.0.0', 
                'production': '1.0.0'
            }
            
            for line in content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key in versions:
                        versions[key] = value
            
            return versions.get(branch_type, '1.0.0')
            
        except Exception as e:
            self.log_warning(f"Error reading version file: {e}")
            return "1.0.0"
    
    def update_version_in_file(self, branch_type, new_version):
        """Update version for specific branch type in VERSION file."""
        # Get current versions for all branch types
        current_versions = {
            'feature': self.get_version_from_file('feature'),
            'dev': self.get_version_from_file('dev'),
            'production': self.get_version_from_file('production')
        }
        
        # Update the specific branch type
        current_versions[branch_type] = new_version
        
        # Write the updated VERSION file
        version_content = f"""feature={current_versions['feature']}
dev={current_versions['dev']}
production={current_versions['production']}"""
        
        self.version_file.write_text(version_content, encoding='utf-8')
        self.log_success(f"Updated VERSION file - {branch_type}: {new_version}")
        
        # Also log the complete state
        self.log_info(f"VERSION file now contains:")
        self.log_info(f"  feature={current_versions['feature']}")
        self.log_info(f"  dev={current_versions['dev']}")
        self.log_info(f"  production={current_versions['production']}")
    
    def get_highest_branch_version(self, target_env, feature_name=None):
        """Get the highest version number for a specific branch type."""
        try:
            # Get all remote branches
            remote_branches = self.run_command("git branch -r").stdout
            branches = [branch.strip() for branch in remote_branches.split('\n') if branch.strip() and not '->' in branch]
            
            versions = []
            
            if target_env.startswith("feature/"):
                # For feature branches, look for ALL feature branch versions (continuous across all features)
                pattern = "origin/feature/"
                self.log_info("Scanning for all feature branch versions...")
                
                for branch in branches:
                    if branch.startswith(pattern) and '-' in branch:
                        # Extract version from feature/name-x.x.x pattern
                        version_part = branch.split('-')[-1]
                        if self.is_valid_version(version_part):
                            versions.append(version_part)
                            self.log_info(f"  Found version {version_part} in {branch}")
                            
            elif target_env == "dev":
                # For dev branches, look for dev/x.x.x pattern
                pattern = "origin/dev/"
                self.log_info("Scanning for dev branch versions...")
                
                for branch in branches:
                    if branch.startswith(pattern) and branch.count('/') == 2:
                        version_part = branch.replace(pattern, "")
                        if self.is_valid_version(version_part):
                            versions.append(version_part)
                            self.log_info(f"  Found version {version_part} in {branch}")
                            
            elif target_env == "production":
                # For production branches, look for prod/x.x.x pattern
                pattern = "origin/prod/"
                self.log_info("Scanning for production branch versions...")
                
                for branch in branches:
                    if branch.startswith(pattern) and branch.count('/') == 2:
                        version_part = branch.replace(pattern, "")
                        if self.is_valid_version(version_part):
                            versions.append(version_part)
                            self.log_info(f"  Found version {version_part} in {branch}")
            
            if not versions:
                self.log_info(f"No versioned branches found for {target_env} - starting from 1.0.0")
                return "1.0.0"  # Start from 1.0.0 if no versions found
            
            # Sort versions and return the highest
            versions.sort(key=lambda v: tuple(map(int, v.split('.'))))
            highest_version = versions[-1]
            self.log_info(f"Highest version found for {target_env}: {highest_version}")
            return highest_version
            
        except Exception as e:
            self.log_warning(f"Error scanning versions for {target_env}: {e}")
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
        
        # Generate comprehensive changelog entry
        self.generate_comprehensive_changelog(new_version, target_env, commit_message)
        self.log_success("Updated CHANGELOG.md")
    
    def update_documentation(self):
        """Update documentation files with the latest environment and versioning details."""
        readme_file = self.base_dir / "README.md"
        deployment_summary_file = self.base_dir / "DEPLOYMENT_SUMMARY.md"

        # Get current versions
        feature_version = self.get_version_from_file('feature')
        dev_version = self.get_version_from_file('dev')
        production_version = self.get_version_from_file('production')
        
        # Get file structure (simplified for documentation)
        try:
            structure_result = self.run_command('dir /B', shell=True)
            main_files = structure_result.stdout.strip().split('\n')[:10]  # First 10 files
            structure_summary = '\n'.join([f"├── {file.strip()}" for file in main_files if file.strip()])
        except:
            structure_summary = "├── adakings_backend/\n├── apps/\n├── smart_deploy.py\n├── VERSION\n├── README.md"

        # Update README.md
        latest_readme_content = f"""# Adakings Backend API - Branch-Specific Versioning System

## Overview
This is the Adakings Backend API with a comprehensive **branch-specific versioning system** that maintains independent version sequences for feature, development, and production branches.

## 🚀 Current Version Status

```
feature={feature_version}
dev={dev_version}
production={production_version}
```

## 📁 Project Structure

```
adakings_backend/
{structure_summary}
```

## 🔧 Branch-Specific Versioning

### How It Works
- **Feature branches**: Continuous versioning across all features (feature/name-x.x.x)
- **Dev branches**: Independent dev versioning (dev/x.x.x)  
- **Production branches**: Independent production versioning (prod/x.x.x)

### Quick Deploy Commands

```bash
# Feature deployment
python smart_deploy.py feature/auth patch "Add authentication"

# Dev deployment
python smart_deploy.py dev minor "New features"

# Production deployment
python smart_deploy.py production major "Major release"
```

### VERSION File
The VERSION file tracks all three branch types independently:
```
feature={feature_version}      # Latest feature version
dev={dev_version}          # Latest dev version
production={production_version}   # Latest production version
```
"""
        readme_file.write_text(latest_readme_content, encoding='utf-8')

        # Update DEPLOYMENT_SUMMARY.md
        latest_deployment_summary_content = f"""# Adakings Backend API - Branch-Specific Versioning Deployment System

## 🎯 Current Deployment Status

### Version Tracking
```
feature={feature_version}      # Continuous across all features
dev={dev_version}          # Independent dev versioning
production={production_version}   # Independent production versioning
```

### 📁 Project Structure
```
adakings_backend/
{structure_summary}
```

## ✅ System Features

- **Branch-Specific Versioning**: Each branch type maintains its own version sequence
- **Automatic Documentation Updates**: README and deployment docs auto-update on deploy
- **Comprehensive Logging**: Detailed changelog with deployment history
- **Smart Git Workflow**: Automated branch creation, merging, and cleanup
- **Backup System**: Automatic backups before each deployment

## 🚀 Usage

```bash
# Deploy feature (continues from highest feature version)
python smart_deploy.py feature/name patch "Description"

    # Deploy to dev (independent versioning + devtest branch)
    python smart_deploy.py dev minor "Dev release"

    # Deploy to production (independent versioning + live branch)
    python smart_deploy.py production major "Production release"
```

## 📊 Latest Deployment
- **Feature Version**: {feature_version}
- **Dev Version**: {dev_version}
- **Production Version**: {production_version}
- **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        deployment_summary_file.write_text(latest_deployment_summary_content, encoding='utf-8')

    def generate_comprehensive_changelog(self, new_version, target_env, commit_message=""):
        """Generate a comprehensive changelog entry with detailed deployment information."""
        self.update_documentation()

        changelog_file = self.base_dir / "CHANGELOG.md"
        
        # Read existing content
        if changelog_file.exists():
            try:
                current_content = changelog_file.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                current_content = changelog_file.read_text(encoding='latin-1')
        else:
            current_content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
        
        # Get deployment details
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_only = datetime.now().strftime("%Y-%m-%d")
        current_branch = self.get_current_branch()
        
        # Get file changes for this deployment
        try:
            # Get list of changed files
            result = self.run_command("git status --porcelain", check=False)
            changed_files = []
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        status = line[:2]
                        filename = line[3:].strip()
                        action = "Modified" if 'M' in status else "Added" if 'A' in status else "Deleted" if 'D' in status else "Changed"
                        changed_files.append(f"  - {action}: `{filename}`")
        except Exception:
            changed_files = ["  - Various files updated"]
        
        # Determine release type and description
        if target_env.startswith("feature/"):
            release_type = "🔧 Feature Development"
            feature_name = target_env.replace("feature/", "")
            release_description = f"Feature branch for '{feature_name}' development"
            branch_info = f"feature/{feature_name}-{new_version}"
        elif target_env == "dev":
            release_type = "🚀 Development Release"
            release_description = "Development environment deployment with latest features"
            branch_info = f"dev/{new_version}"
        elif target_env == "production":
            release_type = "🎯 Production Release"
            release_description = "Production deployment - stable release"
            branch_info = "prod"
        
        # Get previous version for comparison
        try:
            if target_env.startswith("feature/") or target_env == "dev":
                previous_version = self.get_highest_remote_version()
            else:
                previous_version = self.get_current_version()
        except Exception:
            previous_version = "Unknown"
        
        # Build comprehensive changelog entry
        new_entry = f"""# Changelog

All notable changes to this project will be documented in this file.

## [{new_version}] - {date_only}

### {release_type}

**📋 Release Information:**
- **Environment**: {target_env}
- **Branch**: `{branch_info}`
- **Version**: `{previous_version}` → `{new_version}`
- **Deployment Time**: {timestamp}
- **Description**: {release_description}

**📝 Changes Made:**
{commit_message if commit_message else f"- Automated deployment to {target_env} environment"}

**📁 Files Modified:**
{chr(10).join(changed_files) if changed_files else "- No file changes detected"}

**🔄 Deployment Details:**
- **Source Branch**: `{current_branch}`
- **Target Branch**: `{branch_info}`
- **Merge Strategy**: Automatic merge with main branch
- **Version Bump Type**: {self.determine_bump_type(previous_version, new_version)}

**🎯 Environment Specific Notes:**
{self.get_environment_notes(target_env)}

---

{current_content.replace('# Changelog', '').replace('All notable changes to this project will be documented in this file.', '').strip()}
"""
        
        # Write updated changelog
        changelog_file.write_text(new_entry, encoding='utf-8')
    
    def determine_bump_type(self, old_version, new_version):
        """Determine the type of version bump that occurred."""
        try:
            old_parts = list(map(int, old_version.split('.')))
            new_parts = list(map(int, new_version.split('.')))
            
            if new_parts[0] > old_parts[0]:
                return "Major (breaking changes)"
            elif new_parts[1] > old_parts[1]:
                return "Minor (new features)"
            elif new_parts[2] > old_parts[2]:
                return "Patch (bug fixes)"
            else:
                return "Unknown"
        except Exception:
            return "Version update"
    
    def get_environment_notes(self, target_env):
        """Get environment-specific notes for the changelog."""
        if target_env.startswith("feature/"):
            return "- This is a feature branch deployment for development and testing\n- Changes are isolated and will be merged after review\n- Not suitable for production use"
        elif target_env == "dev":
            return "- Development environment deployment\n- Contains latest features and changes\n- Used for integration testing before production\n- May contain experimental features"
        elif target_env == "production":
            return "- Production environment deployment\n- Stable and tested release\n- Ready for end users\n- All features have been thoroughly tested"
        else:
            return f"- Deployment to {target_env} environment\n- See deployment documentation for environment details"

    def generate_comprehensive_commit_message(self, target_env, version, commit_message=""):
        """Generate a comprehensive commit message for deployment."""
        try:
            # Get git diff statistics
            diff_stats = self.run_command("git diff --cached --stat").stdout.strip()
            diff_summary = self.run_command("git diff --cached --shortstat").stdout.strip()
            
            # Get changed files with their status
            result = self.run_command("git status --porcelain")
            changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Categorize changes by type and file extension
            file_categories = {
                'backend': [],
                'frontend': [],
                'config': [],
                'docs': [],
                'tests': [],
                'deployment': [],
                'other': []
            }
            
            action_counts = {'modified': 0, 'added': 0, 'deleted': 0, 'renamed': 0}
            
            for change in changes:
                if not change.strip():
                    continue
                status = change[:2]
                filename = change[3:].strip()
                
                # Count actions
                if 'M' in status:
                    action_counts['modified'] += 1
                elif 'A' in status:
                    action_counts['added'] += 1
                elif 'D' in status:
                    action_counts['deleted'] += 1
                elif 'R' in status:
                    action_counts['renamed'] += 1
                
                # Categorize by file type
                if filename.endswith(('.py', '.pyc', '.pyo')):
                    file_categories['backend'].append(filename)
                elif filename.endswith(('.js', '.jsx', '.ts', '.tsx', '.vue', '.html', '.css', '.scss')):
                    file_categories['frontend'].append(filename)
                elif filename.endswith(('.env', '.ini', '.conf', '.config', '.yml', '.yaml', '.json', '.toml')):
                    file_categories['config'].append(filename)
                elif filename.endswith(('.md', '.rst', '.txt', '.pdf')):
                    file_categories['docs'].append(filename)
                elif 'test' in filename.lower() or filename.endswith(('.test.py', '.spec.py')):
                    file_categories['tests'].append(filename)
                elif filename in ['Dockerfile', 'docker-compose.yml', 'requirements.txt', 'setup.py', 'smart_deploy.py']:
                    file_categories['deployment'].append(filename)
                else:
                    file_categories['other'].append(filename)
            
            # Build comprehensive commit message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Header with conventional commit format
            commit_type = "feat" if target_env.startswith("feature/") else "release" if target_env == "production" else "deploy"
            header = f"{commit_type}({target_env}): Deploy version {version}"
            
            if commit_message:
                header += f" - {commit_message}"
            
            # Build detailed body
            body_parts = []
            
            # Summary of changes
            total_files = sum(action_counts.values())
            if total_files > 0:
                change_summary = []
                if action_counts['modified'] > 0:
                    change_summary.append(f"{action_counts['modified']} modified")
                if action_counts['added'] > 0:
                    change_summary.append(f"{action_counts['added']} added")
                if action_counts['deleted'] > 0:
                    change_summary.append(f"{action_counts['deleted']} deleted")
                if action_counts['renamed'] > 0:
                    change_summary.append(f"{action_counts['renamed']} renamed")
                
                body_parts.append(f"📊 Summary: {', '.join(change_summary)} files ({total_files} total)")
            
            # File categories
            for category, files in file_categories.items():
                if files:
                    icon = {
                        'backend': '🐍',
                        'frontend': '🎨',
                        'config': '⚙️',
                        'docs': '📚',
                        'tests': '🧪',
                        'deployment': '🚀',
                        'other': '📁'
                    }[category]
                    
                    if len(files) <= 3:
                        body_parts.append(f"{icon} {category.title()}: {', '.join(files)}")
                    else:
                        body_parts.append(f"{icon} {category.title()}: {', '.join(files[:3])} and {len(files)-3} more")
            
            # Deployment details
            body_parts.append(f"🎯 Target: {target_env} environment")
            body_parts.append(f"📦 Version: {version}")
            body_parts.append(f"⏰ Deployed: {timestamp}")
            
            # Git statistics if available
            if diff_summary:
                body_parts.append(f"📈 Changes: {diff_summary}")
            
            # Combine header and body
            full_message = header
            if body_parts:
                full_message += "\n\n" + "\n".join(body_parts)
            
            return full_message
            
        except Exception as e:
            # Fallback to basic message
            return f"deploy({target_env}): Deploy version {version} - {commit_message or 'Automated deployment'}"
    
    def check_working_directory(self):
        """Check if git working directory has uncommitted changes without committing them."""
        result = self.run_command("git status --porcelain")
        if result.stdout.strip():
            self.log_info("Working directory has uncommitted changes that will be included in deployment:")
            print(result.stdout)
            return True  # Has changes
        return False  # No changes

    def cleanup_deleted_remote_branches(self):
        """Remove local branches that no longer exist on remote."""
        try:
            self.log_info("Cleaning up deleted remote branches...")
            
            # Get current branch to avoid deleting it
            current_branch = self.get_current_branch()
            
            # Get all local branches
            local_result = self.run_command("git branch")
            local_branches = []
            for line in local_result.stdout.split('\n'):
                if line.strip():
                    branch = line.strip().replace('*', '').strip()
                    if branch and branch not in ['main', 'master']:
                        local_branches.append(branch)
            
            # Get all remote branches
            remote_result = self.run_command("git branch -r")
            remote_branches = []
            for line in remote_result.stdout.split('\n'):
                if line.strip() and not '->' in line:
                    # Extract branch name from origin/branch-name
                    branch = line.strip().replace('origin/', '')
                    if branch:
                        remote_branches.append(branch)
            
            # Find local branches that don't exist remotely
            branches_to_delete = []
            for local_branch in local_branches:
                if local_branch not in remote_branches and local_branch != current_branch:
                    branches_to_delete.append(local_branch)
            
            # Delete branches that no longer exist remotely
            if branches_to_delete:
                self.log_info(f"Found {len(branches_to_delete)} local branches to clean up:")
                for branch in branches_to_delete:
                    self.log_info(f"  - {branch}")
                
                for branch in branches_to_delete:
                    try:
                        # Force delete the branch
                        self.run_command(f"git branch -D {branch}")
                        self.log_success(f"Deleted local branch: {branch}")
                    except subprocess.CalledProcessError:
                        self.log_warning(f"Could not delete branch: {branch}")
            else:
                self.log_info("No stale local branches found to clean up")
                
        except Exception as e:
            self.log_warning(f"Branch cleanup failed: {e}")
    
    def sync_with_remote(self):
        """Sync local repository with remote - fetch all branches and clean up deleted ones."""
        self.log_info("Syncing with remote repository...")
        
        # Fetch all remote branches and tags
        self.run_command("git fetch --all")
        
        # Prune remote tracking branches that no longer exist
        self.run_command("git remote prune origin")
        
        # Clean up local branches that no longer exist on remote
        self.cleanup_deleted_remote_branches()
        
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

    def confirm_action(self, message):
        """Ask user for confirmation before proceeding."""
        try:
            response = input(f"\n❓ {message} (y/N): ").strip().lower()
            return response in ['y', 'yes']
        except KeyboardInterrupt:
            print("\n\n❌ Operation cancelled by user")
            return False
    
    def create_or_checkout_branch(self, branch_name, target_env, new_version):
        """Create or checkout the target branch, with user confirmation for new branches."""
        
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
            # Neither local nor remote branch exists - ASK FOR CONFIRMATION
            print(f"\n📋 Deployment Summary:")
            print(f"   🎯 Target Environment: {target_env}")
            print(f"   🌿 New Branch: {branch_name}")
            print(f"   📦 Version: {new_version}")
            print(f"   📍 Source Branch: {current_branch}")
            
            if not self.confirm_action(f"Create new branch '{branch_name}' and deploy version {new_version}?"):
                self.log_warning("Deployment cancelled by user")
                return False
            
            # Create new branch
            self.run_command(f"git checkout -b {branch_name}")
            self.log_success(f"Created new branch: {branch_name} from {current_branch}")
        
        return True

    def push_to_branch(self, branch_name, commit_message):
        """Commit changes and push to branch."""
        # Check if there are any changes to commit (including working directory changes)
        current_branch = self.get_current_branch()
        self.log_info(f"Currently on branch: {current_branch}")
        
        # Check for any changes (staged, unstaged, or untracked)
        status_result = self.run_command("git status --porcelain")
        
        if status_result.stdout.strip():
            self.log_info("Uncommitted changes:")
            print(status_result.stdout)
            
            # Add all changes (including uncommitted working directory changes)
            self.run_command("git add .")
            
            # Commit all changes to the new branch
            self.run_command(f'git commit -m "{commit_message}"')
        else:
            self.log_info("No changes to commit")
            return
        
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

    def manage_branch(self, branch_name, source_branch, new_version, commit_message, branch_type):
        """Generic branch creation and updating function."""
        self.log_info(f"Managing {branch_type} branch '{branch_name}' with version {new_version}...")
        
        # Store the current branch to return to
        current_branch = self.get_current_branch()
        
        # Verify we're on the correct source branch
        if current_branch != source_branch:
            self.log_warning(f"Expected to be on {source_branch}, but currently on {current_branch}")
            # Checkout the correct source branch
            self.run_command(f"git checkout {source_branch}")
            current_branch = source_branch

        self.log_info(f"Working from source branch: {source_branch}")

        # Check if target branch exists locally
        local_branches = self.run_command("git branch").stdout
        clean_local_branches = [branch.strip().replace('*', '').strip() for branch in local_branches.split('\n') if branch.strip()]
        local_exists = branch_name in clean_local_branches

        # Check if target branch exists remotely
        remote_branches = self.run_command("git branch -r").stdout
        clean_remote_branches = [branch.strip() for branch in remote_branches.split('\n') if branch.strip() and not '→' in branch]
        remote_exists = f"origin/{branch_name}" in clean_remote_branches

        self.log_info(f"Local {branch_name} exists: {local_exists}")
        self.log_info(f"Remote {branch_name} exists: {remote_exists}")

        if local_exists:
            # Local target branch exists, checkout and update
            self.run_command(f"git checkout {branch_name}")
            if remote_exists:
                try:
                    self.run_command(f"git pull origin {branch_name}")
                    self.log_info(f"Updated local {branch_name} with remote changes")
                except subprocess.CalledProcessError:
                    self.log_warning(f"Could not pull from origin/{branch_name} - continuing...")
        elif remote_exists:
            # Remote target branch exists but not locally - create local tracking branch
            self.run_command(f"git checkout -b {branch_name} origin/{branch_name}")
            self.log_info(f"Created local {branch_name} branch tracking origin/{branch_name}")
        else:
            # No target branch exists - create new one from source branch
            self.run_command(f"git checkout -b {branch_name} {source_branch}")
            self.log_info(f"Created new {branch_name} branch from {source_branch}")

        # Merge source branch changes into target branch
        try:
            self.run_command(f"git merge {source_branch}")
            self.log_info(f"Merged {source_branch} into {branch_name}")
        except subprocess.CalledProcessError:
            # Handle conflicts by taking source branch changes
            self.log_warning("Merge conflicts detected. Resolving by taking source branch changes...")
            self.run_command(f"git merge -X theirs {source_branch}")
            self.log_info(f"Resolved conflicts by taking {source_branch} changes")

        # Check for changes to commit
        status_result = self.run_command("git status --porcelain")

        if status_result.stdout.strip():
            self.run_command("git add .")
            final_commit_msg = f"{branch_type}({branch_name}): Update {branch_name} with {source_branch}/{new_version} changes - {commit_message or f'{branch_type.capitalize()} deployment'}"
            self.run_command(f'git commit -m "{final_commit_msg}"')
            self.log_info(f"Committed additional changes to {branch_name}")

        # Push target branch
        self.run_command(f"git push origin {branch_name}")
        self.log_success(f"✅ {branch_name.capitalize()} branch updated and pushed with {source_branch}/{new_version} changes")

        # Return to the source branch
        self.run_command(f"git checkout {source_branch}")
        self.log_info(f"Returned to {source_branch}")

    def create_or_update_devtest_branch(self, new_version, commit_message):
        """Create or update the devtest branch with the latest dev changes."""
        current_dev_branch = f"dev/{new_version}"
        self.manage_branch(
            branch_name='devtest',
            source_branch=current_dev_branch,
            new_version=new_version,
            commit_message=commit_message,
            branch_type='devtest'
        )

    def create_or_update_live_branch(self, new_version, commit_message):
        """Create or update the live branch with the latest production changes."""
        current_prod_branch = f"prod/{new_version}"
        self.manage_branch(
            branch_name='live',
            source_branch=current_prod_branch,
            new_version=new_version,
            commit_message=commit_message,
            branch_type='live'
        )


    def validate_production_version(self, new_version):
        """Validate that production version is being incremented properly."""
        current_prod_version = self.get_highest_branch_version('production')
        
        # Special case: If no production branches exist, allow 1.0.0 as first version
        try:
            remote_branches = self.run_command("git branch -r").stdout
            prod_branches_exist = any("origin/prod/" in branch for branch in remote_branches.split('\n') if branch.strip())
            
            if not prod_branches_exist and new_version == "1.0.0":
                self.log_info("First production deployment - allowing version 1.0.0")
                return True
        except Exception:
            pass
        
        # Compare versions to ensure new version is actually higher
        try:
            current_parts = list(map(int, current_prod_version.split('.')))
            new_parts = list(map(int, new_version.split('.')))
            
            # Check if new version is greater than current
            for i in range(3):
                if new_parts[i] > current_parts[i]:
                    return True
                elif new_parts[i] < current_parts[i]:
                    return False
            
            # Versions are equal - not allowed for production (except first deployment)
            return False
            
        except Exception as e:
            self.log_warning(f"Error comparing versions: {e}")
            return False
    
    def enforce_production_version_increment(self, target_env, new_version):
        """Enforce that production versions are always incremented."""
        if target_env != "production":
            return True  # Only enforce for production
        
        current_prod_version = self.get_highest_branch_version('production')
        
        self.log_info(f"🔍 Production Version Check:")
        self.log_info(f"   Current: {current_prod_version}")
        self.log_info(f"   Proposed: {new_version}")
        
        if not self.validate_production_version(new_version):
            self.log_error(f"❌ PRODUCTION VERSION ERROR!")
            self.log_error(f"   Production version must be incremented for deployment.")
            self.log_error(f"   Current production version: {current_prod_version}")
            self.log_error(f"   Proposed version: {new_version}")
            self.log_error(f"   ")
            self.log_error(f"   📋 To fix this issue:")
            self.log_error(f"   1. Use 'major', 'minor', or 'patch' bump type")
            self.log_error(f"   2. Ensure the new version is higher than {current_prod_version}")
            self.log_error(f"   ")
            self.log_error(f"   Examples:")
            self.log_error(f"   python smart_deploy.py production patch \"Bug fixes\"")
            self.log_error(f"   python smart_deploy.py production minor \"New features\"")
            self.log_error(f"   python smart_deploy.py production major \"Breaking changes\"")
            return False
        
        self.log_success(f"✅ Production version validation passed: {current_prod_version} → {new_version}")
        return True
    
    def show_version_summary(self, target_env, current_version, new_version):
        """Show a comprehensive version summary before deployment."""
        self.log_info(f"")
        self.log_info(f"📊 Version Summary for {target_env.upper()} deployment:")
        self.log_info(f"   ╭─────────────────────────────────────╮")
        self.log_info(f"   │  Current: {current_version:<20} │")
        self.log_info(f"   │  New:     {new_version:<20} │")
        self.log_info(f"   ╰─────────────────────────────────────╯")
        
        # Show all current versions for context
        feature_version = self.get_version_from_file('feature')
        dev_version = self.get_version_from_file('dev')
        production_version = self.get_version_from_file('production')
        
        self.log_info(f"")
        self.log_info(f"📋 All Environment Versions:")
        self.log_info(f"   Feature:    {feature_version}")
        self.log_info(f"   Dev:        {dev_version}")
        self.log_info(f"   Production: {production_version} {'→ ' + new_version if target_env == 'production' else ''}")
        self.log_info(f"")

    def deploy(self, target_env, bump_type, commit_message=""):
        """Main deployment function."""
        self.log_info(f"🚀 Starting deployment to {target_env} environment")
        
        # Pre-deployment checks - just check for changes, don't commit them yet
        has_uncommitted_changes = self.check_working_directory()

        # Backup current state
        backup_path = self.backup_current_state()

        try:
            # Sync with remote first to get latest remote branches
            self.sync_with_remote()
            
            # ALWAYS get current version by scanning remote branches for ALL environment types
            # This ensures we have the true current state, not what's in VERSION file
            if target_env == "production":
                current_version = self.get_highest_branch_version("production")
                self.log_info(f"Production version from remote branches: {current_version}")
            elif target_env == "dev":
                current_version = self.get_highest_branch_version("dev")
                self.log_info(f"Dev version from remote branches: {current_version}")
            else:
                # For feature branches
                current_version = self.get_highest_branch_version(target_env)
                self.log_info(f"Feature version from remote branches: {current_version}")
            
            # For first deployment of any branch type, use 1.0.0 as starting point
            # For subsequent deployments, bump the version
            if current_version == "1.0.0":
                # Check if any branches actually exist for this environment type
                try:
                    remote_branches = self.run_command("git branch -r").stdout
                    branches_exist = False
                    
                    if target_env.startswith("feature/"):
                        branches_exist = any("origin/feature/" in branch for branch in remote_branches.split('\n') if branch.strip())
                    elif target_env == "dev":
                        branches_exist = any("origin/dev/" in branch for branch in remote_branches.split('\n') if branch.strip())
                    elif target_env == "production":
                        branches_exist = any("origin/prod/" in branch for branch in remote_branches.split('\n') if branch.strip())
                    
                    if not branches_exist:
                        # No branches exist for this environment type - start from 1.0.0
                        self.log_info(f"No {target_env} branches found remotely - starting from version 1.0.0")
                        new_version = "1.0.0"
                    else:
                        # Branches exist but highest version is 1.0.0 - bump it
                        new_version = self.bump_version(bump_type, current_version)
                        self.log_info(f"Found {target_env} branches, bumping from base version: {current_version} → {new_version}")
                except Exception:
                    # Error checking branches - start from 1.0.0
                    self.log_info(f"Could not check existing branches - starting from version 1.0.0")
                    new_version = "1.0.0"
            else:
                # Branch type has existing versions, bump from the highest
                new_version = self.bump_version(bump_type, current_version)
                self.log_info(f"Using highest remote version for {target_env} as base: {current_version} → {new_version}")
            
            # PRODUCTION VERSION VALIDATION - Critical safeguard
            if not self.enforce_production_version_increment(target_env, new_version):
                self.log_error("🚫 Production deployment blocked due to version validation failure!")
                return False
            
            # Show comprehensive version summary
            self.show_version_summary(target_env, current_version, new_version)
            
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
                branch_name = f"prod/{new_version}"  # Versioned prod branch
            else:
                self.log_error(f"Invalid target environment: {target_env}")
                return False
            
            self.log_info(f"Target branch: {branch_name}")
            self.log_info(f"Version: {current_version} → {new_version}")

            # Production deployment - simplified single-step process with versioned branches
            if target_env == "production":
                print(f"\n🎯 PRODUCTION DEPLOYMENT:")
                print(f"   📦 Production Version: {current_version} → {new_version}")
                print(f"   🌿 Branch: {branch_name}")
                print(f"   🔴 Live Branch: Will be updated with production changes")
                print(f"   📝 Message: {commit_message or 'Automated production deployment'}")
                print(f"")
                
                if not self.confirm_action(f"Create production branch {branch_name} and update live branch?"):
                    self.log_warning("Production deployment cancelled by user")
                    return False
            
            # Create/checkout target branch (with user confirmation for new branches)
            if not self.create_or_checkout_branch(branch_name, target_env, new_version):
                return False

            # Update version file for specific branch type and changelog
            final_commit_message = commit_message or f"Version: {new_version} feat: Deploy to {target_env} environment"
            self.update_version_in_file(env_type, new_version)
            self.generate_comprehensive_changelog(new_version, target_env, final_commit_message)

            # Generate comprehensive commit message
            comprehensive_commit_msg = self.generate_comprehensive_commit_message(target_env, new_version, commit_message)
            
            # Commit and push changes
            self.push_to_branch(branch_name, comprehensive_commit_msg)

            # Handle special dev workflow - create/update devtest branch
            if target_env == "dev":
                self.log_info(f"\n🧪 DEV DEPLOYMENT - DEVTEST BRANCH MANAGEMENT")
                self.log_info(f"   Creating/updating devtest branch with dev/{new_version} changes")
                self.create_or_update_devtest_branch(new_version, commit_message)

            # Handle special production workflow - create/update live branch
            if target_env == "production":
                self.log_info(f"\n🔴 PRODUCTION DEPLOYMENT - LIVE BRANCH MANAGEMENT")
                self.log_info(f"   Creating/updating live branch with prod/{new_version} changes")
                self.create_or_update_live_branch(new_version, commit_message)
            
            # Merge with main if configured (only for features now)
            merge_target = self.git_config[env_type]["merge_with"]
            if merge_target:
                self.merge_with_main(branch_name)

            self.log_success(f"🎉 Successfully deployed to {target_env}!")
            self.log_success(f"📦 Version: {new_version}")
            self.log_success(f"🌿 Branch: {branch_name}")
            
            if merge_target:
                self.log_success(f"🔀 Merged with {merge_target}")
            
            if target_env == "dev":
                self.log_success(f"")
                self.log_success(f"🧪 DEV DEPLOYMENT COMPLETED:")
                self.log_success(f"   ✅ Dev branch created: dev/{new_version}")
                self.log_success(f"   ✅ Devtest branch updated with latest changes")
                self.log_success(f"🚀 Both dev and devtest branches successfully deployed!")
            elif target_env == "production":
                self.log_success(f"")
                self.log_success(f"🎆 PRODUCTION DEPLOYMENT COMPLETED:")
                self.log_success(f"   ✅ Production branch created: prod/{new_version}")
                self.log_success(f"   ✅ Live branch updated with latest changes")
                self.log_success(f"🚀 Both prod and live branches successfully deployed!")

            return True

        except Exception as e:
            self.log_error(f"Deployment failed: {e}")
            self.log_warning("You may need to manually resolve issues and restore from backup")
            self.log_info(f"Backup location: {backup_path}")
            return False

    def show_version_status(self):
        """Show current version status for all environments."""
        # Always check remote branches for accurate version status
        self.log_info("Checking remote branches for current versions...")
        feature_version = self.get_highest_branch_version('feature/dummy')  # Use dummy feature name to scan all features
        dev_version = self.get_highest_branch_version('dev')
        production_version = self.get_highest_branch_version('production')
        
        print(f"")
        print(f"📊 CURRENT VERSION STATUS")
        print(f"╭─────────────────────────────────────╮")
        print(f"│                                     │")
        print(f"│  🔧 Feature:    {feature_version:<16}     │")
        print(f"│  🚀 Dev:        {dev_version:<16}     │")
        print(f"│  🎯 Production: {production_version:<16}     │")
        print(f"│                                     │")
        print(f"╰─────────────────────────────────────╯")
        print(f"")
        
        # Show what the next versions would be for each bump type
        print(f"🔮 NEXT PRODUCTION VERSIONS:")
        try:
            next_patch = self.bump_version("patch", production_version)
            next_minor = self.bump_version("minor", production_version)
            next_major = self.bump_version("major", production_version)
            
            print(f"   📌 Patch:  {production_version} → {next_patch}")
            print(f"   🆕 Minor:  {production_version} → {next_minor}")
            print(f"   💥 Major:  {production_version} → {next_major}")
        except Exception as e:
            print(f"   ❌ Error calculating next versions: {e}")
        
        print(f"")
        print(f"💡 PRODUCTION DEPLOYMENT EXAMPLES:")
        print(f"   python smart_deploy.py production patch \"Bug fixes\"")
        print(f"   python smart_deploy.py production minor \"New features\"")
        print(f"   python smart_deploy.py production major \"Breaking changes\"")
        print(f"")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # Check for special commands
    if sys.argv[1] in ['status', 'version', '--status', '--version']:
        deployer = SmartDeployer()
        deployer.show_version_status()
        sys.exit(0)

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
