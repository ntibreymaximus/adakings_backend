#!/usr/bin/env python3
"""
Environment-specific deployment helper for Adakings Backend API

This script helps ensure that only environment-specific files are deployed
and prevents accidental cross-environment contamination.

Usage:
    python deploy_environment.py feature [branch-name]
    python deploy_environment.py dev
    python deploy_environment.py production

Features:
- Environment-specific file validation
- Git branch management
- Environment isolation
- Deployment safety checks
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
from datetime import datetime

class EnvironmentDeployer:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.environments_dir = self.base_dir / 'environments'
        
        # Environment configurations
        self.env_configs = {
            'feature': {
                'branch_prefix': 'feature/',
                'description': 'Feature development environment',
                'env_file': 'environments/feature/.env',
                'requirements': 'environments/feature/requirements.txt',
                'allowed_branches': ['feature/*', 'develop', 'main'],
                'target': 'development'
            },
            'dev': {
                'branch_prefix': 'dev',
                'description': 'Development environment (production-like)',
                'env_file': 'environments/dev/.env',
                'requirements': 'environments/dev/requirements.txt',
                'allowed_branches': ['develop', 'dev', 'main'],
                'target': 'staging'
            },
            'production': {
                'branch_prefix': 'main',
                'description': 'Production environment',
                'env_file': 'environments/production/.env',
                'requirements': 'environments/production/requirements.txt',
                'allowed_branches': ['main', 'release/*'],
                'target': 'production'
            }
        }

    def get_current_branch(self):
        """Get the current git branch"""
        try:
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def get_git_status(self):
        """Check if there are uncommitted changes"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def validate_environment(self, env_name):
        """Validate that environment exists and is properly configured"""
        if env_name not in self.env_configs:
            print(f"❌ Error: Unknown environment '{env_name}'")
            print(f"Available environments: {', '.join(self.env_configs.keys())}")
            return False

        env_config = self.env_configs[env_name]
        env_dir = self.environments_dir / env_name
        
        # Check if environment directory exists
        if not env_dir.exists():
            print(f"❌ Error: Environment directory '{env_dir}' does not exist")
            return False

        # Check if .env.template exists
        env_template = env_dir / '.env.template'
        if not env_template.exists():
            print(f"❌ Error: Environment template '{env_template}' does not exist")
            return False

        # Check if .env file exists
        env_file = env_dir / '.env'
        if not env_file.exists():
            print(f"⚠️  Warning: Environment file '{env_file}' does not exist")
            print(f"   Creating from template...")
            shutil.copy(env_template, env_file)
            print(f"✅ Created {env_file} from template")
            print(f"   Please edit {env_file} with your {env_name}-specific values")

        return True

    def check_branch_compatibility(self, env_name, current_branch):
        """Check if current branch is compatible with environment"""
        env_config = self.env_configs[env_name]
        allowed_patterns = env_config['allowed_branches']
        
        for pattern in allowed_patterns:
            if pattern.endswith('/*'):
                # Handle wildcard patterns like "feature/*"
                prefix = pattern[:-2]
                if current_branch.startswith(prefix):
                    return True
            elif pattern == current_branch:
                return True
        
        return False

    def create_deployment_manifest(self, env_name):
        """Create a deployment manifest for tracking"""
        manifest = {
            'environment': env_name,
            'timestamp': datetime.now().isoformat(),
            'branch': self.get_current_branch(),
            'description': self.env_configs[env_name]['description'],
            'files': {
                'env_template': f'environments/{env_name}/.env.template',
                'requirements': f'environments/{env_name}/requirements.txt',
                'version': f'environments/{env_name}/VERSION',
                'changelog': f'environments/{env_name}/CHANGELOG.md'
            }
        }
        
        manifest_path = self.environments_dir / env_name / 'deployment_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_path

    def validate_env_file_safety(self, env_name):
        """Ensure .env files are not accidentally committed"""
        env_file = self.environments_dir / env_name / '.env'
        
        # Check if .env file is tracked by git
        try:
            result = subprocess.run(['git', 'ls-files', '--error-unmatch', str(env_file)], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"❌ Error: {env_file} is tracked by git!")
                print("   This file contains sensitive information and should not be committed.")
                print("   Run: git rm --cached " + str(env_file))
                return False
        except subprocess.CalledProcessError:
            pass  # File is not tracked, which is good
        
        return True

    def deploy(self, env_name, branch_name=None):
        """Deploy to specified environment"""
        print(f"🚀 Starting deployment to {env_name} environment")
        print(f"📝 Description: {self.env_configs[env_name]['description']}")
        print()

        # Step 1: Validate environment
        if not self.validate_environment(env_name):
            return False

        # Step 2: Check git status
        current_branch = self.get_current_branch()
        if not current_branch:
            print("❌ Error: Could not determine current git branch")
            return False

        print(f"📍 Current branch: {current_branch}")

        # Step 3: Check for uncommitted changes
        git_status = self.get_git_status()
        if git_status:
            print("⚠️  Warning: You have uncommitted changes:")
            print(git_status)
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("❌ Deployment cancelled")
                return False

        # Step 4: Validate branch compatibility
        if not self.check_branch_compatibility(env_name, current_branch):
            print(f"⚠️  Warning: Branch '{current_branch}' is not typically used for {env_name} deployments")
            print(f"   Recommended branches: {', '.join(self.env_configs[env_name]['allowed_branches'])}")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("❌ Deployment cancelled")
                return False

        # Step 5: Validate .env file safety
        if not self.validate_env_file_safety(env_name):
            return False

        # Step 6: Create deployment manifest
        manifest_path = self.create_deployment_manifest(env_name)
        print(f"📋 Created deployment manifest: {manifest_path}")

        # Step 7: Show what will be deployed
        print("\n📦 Environment-specific files that will be active:")
        env_config = self.env_configs[env_name]
        for file_type, file_path in {
            'Environment template': f'environments/{env_name}/.env.template',
            'Requirements': f'environments/{env_name}/requirements.txt',
            'Setup script': f'environments/{env_name}/setup.sh' if env_name == 'feature' else f'environments/{env_name}/deploy.sh',
            'Documentation': f'environments/{env_name}/README.md'
        }.items():
            full_path = self.base_dir / file_path
            if full_path.exists():
                print(f"   ✅ {file_type}: {file_path}")
            else:
                print(f"   ⚠️  {file_type}: {file_path} (missing)")

        print(f"\n✅ Deployment to {env_name} environment completed successfully!")
        print(f"🔧 To run this environment: python manage.py runserver {env_name}")
        
        if env_name == 'feature':
            print(f"💡 Tip: Your feature environment uses: environments/feature/.env")
        elif env_name == 'dev':
            print(f"💡 Tip: Your dev environment uses: environments/dev/.env")
        elif env_name == 'production':
            print(f"💡 Tip: Your production environment uses: environments/production/.env")
            print(f"⚠️  Warning: Make sure production .env has real values, not templates!")

        return True

    def list_environments(self):
        """List all available environments"""
        print("📋 Available environments:")
        print()
        for env_name, config in self.env_configs.items():
            env_dir = self.environments_dir / env_name
            status = "✅" if env_dir.exists() else "❌"
            print(f"  {status} {env_name}")
            print(f"     Description: {config['description']}")
            print(f"     Target: {config['target']}")
            print(f"     Recommended branches: {', '.join(config['allowed_branches'])}")
            print()

def main():
    deployer = EnvironmentDeployer()

    if len(sys.argv) < 2:
        print("Usage: python deploy_environment.py <environment> [branch-name]")
        print()
        deployer.list_environments()
        return

    command = sys.argv[1].lower()

    if command in ['list', 'ls']:
        deployer.list_environments()
        return

    if command in deployer.env_configs:
        branch_name = sys.argv[2] if len(sys.argv) > 2 else None
        success = deployer.deploy(command, branch_name)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Error: Unknown environment '{command}'")
        deployer.list_environments()
        sys.exit(1)

if __name__ == '__main__':
    main()
