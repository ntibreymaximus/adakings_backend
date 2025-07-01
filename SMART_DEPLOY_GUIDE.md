# Smart Deployment Script Guide

## Overview

The `smart_deploy.py` script automates environment-specific deployments for the Adakings Backend API. It handles file management, branch switching, and deployment to different environments automatically.

## Features

- **Environment-Specific File Management**: Uses only environment-specific files and core application files
- **Branch and Version Management**: Switches to the correct branch, bumps version, and manages environment-specific files
- **Backup 6 Restore**: Creates backups before deployment and can restore on failure
- **Safety Checks**: Requires confirmation for production deployments
- **Automated Git Handling**: Pushing only environment-specific and core files

## Usage

### Deploy to Production
```bash
# Deploy to production branch with production-optimized files
python smart_deploy.py production
```

**What happens:**
- Switches to `production` branch
- Uses production-specific files (`.env`, `README-PRODUCTION.md`, etc.)
- Removes development-specific files
- Commits and pushes to production branch

### Deploy to Development
```bash
# Deploy to dev branch with development tools
python smart_deploy.py dev
```

**What happens:**
- Switches to `dev` branch  
- Uses development-specific files (`.env.example`, `README-DEVELOPMENT.md`, etc.)
- Includes development tools and utilities
- Commits and pushes to dev branch

### Deploy to Feature Branch
```bash
# Deploy to feature branch (creates if doesn't exist)
python smart_deploy.py feature/new-payment-system
```

**What happens:**
- Creates or switches to `feature/new-payment-system` branch
- Uses development-specific files (feature branches use dev environment)
- Includes all development tools for feature development
- Commits and pushes to the feature branch

## Environment-Specific Configuration

### Production Environment
**Target Branch**: `production`
**Files Used**:
- `environments/production/.env.template`
- `environments/production/README.md`
- `environments/production/CHANGELOG.md`
- `environments/production/requirements.txt`
- `environments/production/VERSION`
- Deployment and settings scripts

**Excluded Files**:
- Development forms (`apps/*/forms.py`)
- Template tags (`apps/*/templatetags/`)
- Debug scripts (`debug_*`)
- Test files (`test_*`)
- Development utilities

### Dev Environment
**Target Branch**: `dev`
**Files Used**:
- `environments/dev/.env.template`
- `environments/dev/README.md`
- `environments/dev/CHANGELOG.md`
- `environments/dev/requirements.txt`
- `environments/dev/VERSION`
- Deployment and settings scripts

### Feature Environment
**Target Branch**: `feature/*`
**Files Used**:
- `environments/feature/.env.template`
- `environments/feature/README.md`
- `environments/feature/CHANGELOG.md`
- `environments/feature/requirements.txt`
- `environments/feature/VERSION`
- Setup and settings scripts

**Included Files**:
- Dev environment includes development tools and utilities
- Feature environment includes testing modules and debugging capabilities
- Each environment maintains its own version and changelog

## Safety Features

### Production Deployment Protection
```bash
python smart_deploy.py production
# Output:
# 🎯 Target Environment: production
# ⚠️  WARNING: This will deploy to PRODUCTION!
# Are you sure you want to continue? (yes/no):
```

### Automatic Backup
- Creates backup in `.deploy_backup/` before making changes
- Automatically restores on failure
- Backs up key configuration files

### Error Handling
- Validates environment types
- Checks git operations
- Rolls back on failure
- Provides detailed error messages

## File Templates

The script uses template files that you should customize:

### Environment Templates
- `.env.production.template` - Production environment variables
- `.env.development.template` - Development environment variables

### Documentation Templates  
- `README-PRODUCTION.md` - Production documentation
- `README-DEVELOPMENT.md` - Development documentation
- `CHANGELOG-PRODUCTION.md` - Production release notes
- `CHANGELOG-DEVELOPMENT.md` - Development changes

### Requirements Templates
- `requirements-production.txt` - Production dependencies
- `requirements-development.txt` - Development dependencies with testing tools

## Workflow Examples

### Feature Development
```bash
# Start new feature
git checkout dev
python smart_deploy.py feature/user-authentication

# Work on feature...
# When ready for dev integration
python smart_deploy.py dev

# When ready for production
python smart_deploy.py production
```

### Hotfix Deployment
```bash
# Create hotfix branch
python smart_deploy.py feature/hotfix-payment-bug

# Fix bug and test...
# Deploy to production
python smart_deploy.py production
```

### Environment Testing
```bash
# Test in development
python smart_deploy.py dev

# Test in staging (feature branch)
python smart_deploy.py feature/staging

# Deploy to production when ready
python smart_deploy.py production
```

## Troubleshooting

### Common Issues

**Script fails with git errors:**
- Ensure you have committed all changes before running
- Check that git is properly configured
- Verify you have push permissions to the repository

**Template files not found:**
- Ensure all template files exist in the repository
- Check file names match the configuration in `smart_deploy.py`
- Verify file permissions
* Deployment fails:
- Check the backup in `.deploy_backup/` folder
- Review error messages for specific issues
- Restore backup manually if needed

### Recovery
```bash
# If deployment fails, files are automatically restored
# Manual restoration if needed:
cp -r .deploy_backup/* .
```

## Advanced Configuration

### Customizing Environments
Edit the `env_configs` section in `smart_deploy.py` to:
- Add new environment types
- Modify file mappings
- Change exclude/include patterns
- Customize branch targeting

### Adding New File Types
Update the `files` configuration in `smart_deploy.py`:
```python
"new-file.txt": {
    "source": "new-file.template.txt",
    "description": "Custom configuration file"
}
```

## Best Practices

1. **Always test in development first**
2. **Use feature branches for new development**
3. **Review changes before production deployment**
4. **Keep template files updated**
5. **Use descriptive commit messages**
6. **Monitor deployment success**

## Integration with CI/CD

The script can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Deploy to Production
  run: |
    echo "yes" | python smart_deploy.py production
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Support

For issues with the smart deployment script:
1. Check this guide for common solutions
2. Review the script logs for error details
3. Ensure all template files are properly configured
4. Verify git configuration and permissions
