# Adakings Backend API - Branch-Specific Versioning Deployment System

## 🎯 Current Deployment Status

### Version Tracking
```
feature=4.0.0      # Continuous across all features
dev=2.1.0          # Independent dev versioning
production=2.2.0   # Independent production versioning
```

### 📁 Project Structure
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
- **Feature Version**: 4.0.0
- **Dev Version**: 2.1.0
- **Production Version**: 2.2.0
- **Last Updated**: 2025-07-17 17:08:34
