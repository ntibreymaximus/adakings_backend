# Adakings Backend API - Branch-Specific Versioning Deployment System

## 🎯 Current Deployment Status

### Version Tracking
```
feature=2.0.0      # Continuous across all features
dev=4.0.0          # Independent dev versioning
production=1.1.1   # Independent production versioning
```

### 📁 Project Structure
```
adakings_backend/
├── .deploy_backup
├── .env
├── .env.example
├── .gitignore
├── adakings_backend
├── apps
├── CHANGELOG.md
├── clear_throttle_cache.py
├── CUSTOM_LOCATION_IMPLEMENTATION.md
├── db.sqlite3
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

# Deploy to dev (independent versioning)
python smart_deploy.py dev minor "Dev release"

# Deploy to production (independent versioning)
python smart_deploy.py production major "Production release"
```

## 📊 Latest Deployment
- **Feature Version**: 2.0.0
- **Dev Version**: 4.0.0
- **Production Version**: 1.1.1
- **Last Updated**: 2025-07-05 19:32:01
