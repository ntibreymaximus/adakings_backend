#!/usr/bin/env python3
"""
Version Bump Script for Adakings Backend API
Follows Semantic Versioning (semver.org)

Usage:
    python bump_version.py major    # 1.0.0 -> 2.0.0
    python bump_version.py minor    # 1.0.0 -> 1.1.0  
    python bump_version.py patch    # 1.0.0 -> 1.0.1
"""

import sys
import re
from pathlib import Path

def read_version():
    """Read current version from VERSION file."""
    version_file = Path("VERSION")
    if not version_file.exists():
        print("ERROR: VERSION file not found!")
        sys.exit(1)
    
    version = version_file.read_text().strip()
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        print(f"ERROR: Invalid version format in VERSION file: {version}")
        sys.exit(1)
    
    return version

def write_version(new_version):
    """Write new version to VERSION file."""
    version_file = Path("VERSION")
    version_file.write_text(f"{new_version}\n")
    print(f"✅ Updated VERSION file: {new_version}")

def bump_version(bump_type):
    """Bump version based on type (major, minor, patch)."""
    current_version = read_version()
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == 'major':
        new_version = f"{major + 1}.0.0"
        print(f"🚀 MAJOR version bump: {current_version} -> {new_version}")
    elif bump_type == 'minor':
        new_version = f"{major}.{minor + 1}.0"
        print(f"✨ MINOR version bump: {current_version} -> {new_version}")
    elif bump_type == 'patch':
        new_version = f"{major}.{minor}.{patch + 1}"
        print(f"🐛 PATCH version bump: {current_version} -> {new_version}")
    else:
        print("ERROR: Invalid bump type. Use 'major', 'minor', or 'patch'")
        sys.exit(1)
    
    return new_version

def update_readme_production(new_version):
    """Update version in README.md (production)."""
    readme_file = Path("README.md")
    if not readme_file.exists():
        print("WARNING: README.md not found, skipping update")
        return
    
    content = readme_file.read_text(encoding='utf-8')
    
    # Update version badge
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
    
    readme_file.write_text(content, encoding='utf-8')
    print(f"✅ Updated README.md with version {new_version}")

def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    
    bump_type = sys.argv[1].lower()
    
    if bump_type not in ['major', 'minor', 'patch']:
        print("ERROR: Invalid bump type. Use 'major', 'minor', or 'patch'")
        sys.exit(1)
    
    # Check if we're on production branch
    try:
        import subprocess
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, check=True)
        current_branch = result.stdout.strip()
        
        if current_branch != 'production':
            print(f"WARNING: You're on branch '{current_branch}', not 'production'")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                sys.exit(1)
    except:
        print("WARNING: Could not determine current git branch")
    
    # Bump version
    new_version = bump_version(bump_type)
    write_version(new_version)
    update_readme_production(new_version)
    
    print("\n📋 Next steps:")
    print("1. Update CHANGELOG.md with changes")
    print("2. Commit changes: git add . && git commit -m 'bump: version to v{}'".format(new_version))
    print("3. Create git tag: git tag v{}".format(new_version))
    print("4. Push changes: git push origin production --tags")
    
    # Version bump guidelines reminder
    print(f"\n📖 Version Bump Guidelines:")
    print("• MAJOR: API breaking changes, architecture changes")
    print("• MINOR: New features, backward compatible")  
    print("• PATCH: Bug fixes, security patches")

if __name__ == "__main__":
    main()
