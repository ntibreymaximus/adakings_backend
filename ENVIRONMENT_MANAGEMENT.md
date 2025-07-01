# Environment Management Guide

This document explains how to manage environment-specific configurations and deployments for the Adakings Backend API.

## 🏗️ Environment Structure

```
environments/
├── feature/                 # Local development environment
│   ├── .env.template       # ✅ Committed (template)
│   ├── .env                # ❌ Not committed (actual config)
│   ├── requirements.txt    # ✅ Committed
│   ├── setup.sh           # ✅ Committed
│   └── README.md           # ✅ Committed
├── dev/                    # Development/staging environment
│   ├── .env.template       # ✅ Committed (template)
│   ├── .env                # ❌ Not committed (actual config)
│   ├── requirements.txt    # ✅ Committed
│   ├── deploy.sh          # ✅ Committed
│   └── README.md           # ✅ Committed
└── production/             # Production environment
    ├── .env.template       # ✅ Committed (template)
    ├── .env                # ❌ Not committed (actual config)
    ├── requirements.txt    # ✅ Committed
    ├── deploy.sh          # ✅ Committed
    └── README.md           # ✅ Committed
```

## 🔒 Security Best Practices

### What Gets Committed to Git

✅ **Safe to commit:**
- `.env.template` files (contain placeholder values)
- `requirements.txt` files
- Setup/deployment scripts
- Documentation files
- Version files and changelogs

❌ **NEVER commit:**
- `.env` files (contain real secrets)
- Database files
- Log files with sensitive data
- Deployment manifests

### Environment-Specific Files

Each environment maintains its own isolated configuration:

| Environment | Config File | Purpose |
|-------------|-------------|---------|
| **Local/Feature** | `environments/feature/.env` | Local development with SQLite |
| **Dev** | `environments/dev/.env` | Production-like testing with PostgreSQL |
| **Production** | `environments/production/.env` | Live deployment with real credentials |

## 🚀 Using the Deployment Helper

### Basic Usage

```bash
# List available environments
python deploy_environment.py list

# Deploy to feature environment
python deploy_environment.py feature

# Deploy to dev environment
python deploy_environment.py dev

# Deploy to production environment
python deploy_environment.py production
```

### What the Deployment Helper Does

1. **Validates environment setup** - Ensures all required files exist
2. **Checks git branch compatibility** - Warns if you're on an unusual branch
3. **Prevents accidental commits** - Checks that .env files aren't tracked
4. **Creates deployment manifest** - Tracks what was deployed when
5. **Shows environment status** - Lists which files are active

### Branch Recommendations

| Environment | Recommended Branches |
|-------------|---------------------|
| **Feature** | `feature/*`, `develop`, `main` |
| **Dev** | `develop`, `dev`, `main` |
| **Production** | `main`, `release/*` |

## 🔧 Running Different Environments

```bash
# Run local development environment
python manage.py runserver local

# Run dev environment (requires PostgreSQL)
python manage.py runserver dev

# Run production environment (for testing only)
python manage.py runserver prod
```

## 📝 Setting Up a New Environment

### 1. Create Environment Directory
```bash
mkdir environments/my-new-env
```

### 2. Create Template Files
```bash
# Copy from existing environment
cp environments/feature/.env.template environments/my-new-env/.env.template

# Edit template with environment-specific defaults
# Remove sensitive values, use placeholders
```

### 3. Create Actual Environment File
```bash
# Copy template to actual .env file
cp environments/my-new-env/.env.template environments/my-new-env/.env

# Edit .env with real values for your environment
```

### 4. Update Deployment Helper
Add your new environment to `deploy_environment.py`:

```python
'my-new-env': {
    'description': 'My new environment',
    'env_file': 'environments/my-new-env/.env',
    'requirements': 'environments/my-new-env/requirements.txt',
    'allowed_branches': ['feature/*', 'main'],
    'target': 'development'
}
```

## 🔄 Workflow Examples

### Feature Development Workflow

```bash
# 1. Switch to feature branch
git checkout -b feature/user-authentication

# 2. Set up feature environment
python deploy_environment.py feature

# 3. Run local development
python manage.py runserver local

# 4. Make changes, test locally

# 5. Commit code (excluding .env files)
git add .
git commit -m "Add user authentication"

# 6. Push feature branch
git push origin feature/user-authentication
```

### Dev Environment Deployment

```bash
# 1. Switch to develop branch
git checkout develop

# 2. Pull latest changes
git pull origin develop

# 3. Set up dev environment
python deploy_environment.py dev

# 4. Update dev .env if needed
# Edit environments/dev/.env

# 5. Run migrations and tests
python manage.py runserver dev
```

### Production Deployment

```bash
# 1. Switch to main branch
git checkout main

# 2. Ensure clean state
git pull origin main

# 3. Validate production environment
python deploy_environment.py production

# 4. Update production .env with live values
# Edit environments/production/.env

# 5. Deploy using your production deployment process
```

## 🛡️ Security Checklist

Before committing any changes:

- [ ] No `.env` files are staged for commit
- [ ] Only `.env.template` files contain placeholder values
- [ ] Real API keys and passwords are only in `.env` files
- [ ] Database credentials are environment-specific
- [ ] CORS settings are appropriate for each environment

### Check for Accidentally Tracked .env Files

```bash
# Check if any .env files are tracked
git ls-files | grep -E '\.env$'

# If found, remove from tracking (keep local file)
git rm --cached path/to/.env

# Add to .gitignore if not already there
echo "path/to/.env" >> .gitignore
```

## 🚨 Emergency Procedures

### If .env File Was Accidentally Committed

1. **Remove from git history:**
   ```bash
   git rm --cached environments/*/env
   git commit -m "Remove accidentally committed .env files"
   ```

2. **Rotate all secrets** that were exposed
3. **Update .gitignore** to prevent future accidents
4. **Force push** to remove from remote (if safe to do so)

### If Wrong Environment Used

1. **Stop the server** immediately
2. **Check which .env file** is being used
3. **Switch to correct environment:**
   ```bash
   python deploy_environment.py correct-environment
   python manage.py runserver correct-environment
   ```

## 📊 Monitoring Environment Usage

The deployment helper creates manifest files to track:
- When each environment was last deployed
- Which git branch was active
- What files were included
- Deployment timestamp

These files are in `environments/*/deployment_manifest.json` and are excluded from git.

## 🤝 Team Guidelines

1. **Never share .env files** directly - always use templates
2. **Use the deployment helper** for environment setup
3. **Document environment-specific settings** in README files
4. **Test environment isolation** before major deployments
5. **Keep environment templates updated** when adding new variables
