#!/usr/bin/env python3

import subprocess
import re

def run_command(command):
    try:
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        print(f"Return code: {result.returncode}")
        print(f"Stderr: {repr(result.stderr)}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_latest_version_for_branch_type(branch_type):
    """Debug version of the function"""
    print(f"Checking branch type: {branch_type}")
    
    if branch_type == "dev-test":
        # For dev-test, check dev-test/* branches on remote
        result = run_command("git branch -r --list 'origin/dev-test/*'")
        print(f"Git command result: {result.stdout if result else 'None'}")
        
        if result and result.stdout.strip():
            branches = result.stdout.strip().split('\n')
            print(f"Found branches: {branches}")
            
            versions = []
            for branch in branches:
                branch_name = branch.strip().replace('origin/', '')
                print(f"Processing branch: {branch_name}")
                
                version_part = branch_name.split('/')[-1]
                print(f"Version part: {version_part}")
                
                if re.match(r'^\d+\.\d+\.\d+$', version_part):
                    versions.append(version_part)
                    print(f"Valid version found: {version_part}")
                else:
                    print(f"Invalid version format: {version_part}")
            
            print(f"All versions: {versions}")
            
            if versions:
                # Sort versions properly (semantic versioning)
                versions.sort(key=lambda x: [int(i) for i in x.split('.')], reverse=True)
                print(f"Sorted versions: {versions}")
                return versions[0]  # Return highest version
            
        print("No valid versions found, returning default")
        return "1.0.0"  # Default for dev-test

# Test the function
result = get_latest_version_for_branch_type("dev-test")
print(f"\nFinal result: {result}")
