# Adakings Backend API - Branch-Specific Versioning System

## Overview
This is the Adakings Backend API with a comprehensive **branch-specific versioning system** that maintains independent version sequences for feature, development, and production branches.

## 🚀 Current Version Status

```
feature=1.0.0
dev=1.0.0
production=1.2.0
```

## 📁 Project Structure

```
adakings_backend/
├── .deploy_backup
├── asgi.py
├── CHANGELOG.md
├── DEPLOYMENT_SUMMARY.md
├── README.md
├── settings
├── urls.py
├── VERSION
├── wsgi.py
├── __init__.py
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
feature=1.0.0      # Latest feature version
dev=1.0.0          # Latest dev version
production=1.2.0   # Latest production version
```
