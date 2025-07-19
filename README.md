# Adakings Backend API - Branch-Specific Versioning System

## Overview
This is the Adakings Backend API with a comprehensive **branch-specific versioning system** that maintains independent version sequences for feature, development, and production branches.

## 🚀 Current Version Status

```
feature=4.0.0
dev=2.3.1
production=2.4.0
```

## 📁 Project Structure

```
adakings_backend/
├── .deploy_backup
├── .dockerignore
├── .env
├── .env.google_sheets
├── .env.google_sheets.example
├── .gitignore
├── adakings_backend
├── adakings_local.db
├── adakings_menu.txt
├── apps
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
feature=4.0.0      # Latest feature version
dev=2.3.1          # Latest dev version
production=2.4.0   # Latest production version
```
