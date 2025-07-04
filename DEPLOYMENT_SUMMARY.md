# Adakings Backend API - Branch-Specific Versioning Deployment System

## 🎯 Current Deployment Status

### Version Tracking
```
feature=1.2.0      # Continuous across all features
dev=3.1.0          # Independent dev versioning
production=1.1.0   # Independent production versioning
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
├── BROKEN_PIPE_FIXES.md
├── CHANGELOG.md
├── db.sqlite3
├── DEPLOYMENT_SUMMARY.md
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
- **Feature Version**: 1.2.0
- **Dev Version**: 3.1.0
- **Production Version**: 1.1.0
- **Last Updated**: 2025-07-04 18:40:51
