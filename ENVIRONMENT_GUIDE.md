# Adakings Backend API - Environment Guide

## Overview
The Adakings Backend API supports three distinct environments, each optimized for different use cases:

1. **Feature/Local** - Local development with maximum convenience
2. **Dev** - Production-like testing environment  
3. **Production** - Live deployment environment

## Quick Start

### Running Different Environments

```bash
# Local development (SQLite, debug mode, all dev tools)
python manage.py runserver local

# Dev environment (PostgreSQL, production-like settings, test values)
python manage.py runserver dev

# Production environment (full production configuration)
python manage.py runserver prod
```

### With Custom Ports

```bash
python manage.py runserver local 8001
python manage.py runserver dev 8002
python manage.py runserver prod 8003
```

## Environment Comparison

| Feature | Local/Feature | Dev | Production |
|---------|---------------|-----|------------|
| **Database** | SQLite (default) | PostgreSQL | PostgreSQL + SSL |
| **Debug Mode** | ✅ Always ON | ⚠️ Configurable (default OFF) | ❌ Always OFF |
| **Security** | Relaxed | Production-like | Maximum |
| **Email** | Console | Test SMTP | Live SMTP |
| **Paystack** | Test keys | Test keys | Live keys |
| **Caching** | Dummy (optional Redis) | Redis (fallback to dummy) | Redis (required) |
| **API Docs** | ✅ Full access | ✅ Full access | ❌ Disabled |
| **CORS** | Allow all | Specific origins | Strict origins |
| **SSL/HTTPS** | Not required | Optional | Required |
| **Logging** | Console + file (DEBUG) | Console + file (INFO) | File only (INFO) |

## Environment-Specific Files

### Directory Structure
```
environments/
├── feature/
│   ├── VERSION             # Feature environment version (1.0.0)
│   ├── CHANGELOG.md        # Feature environment changelog
│   ├── README.md           # Feature environment documentation
│   ├── requirements.txt    # All dev dependencies
│   ├── .env.template       # Local development template
│   └── setup.sh           # Setup script for local development
├── dev/
│   ├── VERSION             # Dev environment version (1.0.0)
│   ├── CHANGELOG.md        # Dev environment changelog
│   ├── README.md           # Dev environment documentation  
│   ├── requirements.txt    # Production-like dependencies
│   ├── .env.template       # Dev environment template
│   └── deploy.sh          # Deployment script for dev
└── production/
    ├── VERSION             # Production environment version (1.0.0)
    ├── CHANGELOG.md        # Production environment changelog
    ├── README.md           # Production environment documentation
    ├── requirements.txt    # Production dependencies
    ├── .env.template       # Production environment template
    └── deploy.sh          # Deployment script for production

# Legacy templates (for backward compatibility)
.env.feature.template       # Symlink to environments/feature/.env.template
.env.dev.template           # Symlink to environments/dev/.env.template
.env.production.template    # Symlink to environments/production/.env.template
```

### Settings Files
```
adakings_backend/settings/
├── __init__.py            # Environment detection and loading
├── base.py               # Shared base settings
├── development.py        # Local development settings (feature)
├── dev.py               # Dev environment settings (production-like)
└── production.py        # Production settings
```

## Environment Setup

### 1. Feature/Local Environment
**Purpose**: Local development, feature work, experimentation

```bash
# Setup using environment-specific files
cd environments/feature
./setup.sh

# Or manual setup
cp environments/feature/.env.template .env.example
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver local
```

**Features**:
- SQLite database (no setup required)
- Debug toolbar available
- Console email backend
- All CORS origins allowed
- Comprehensive logging
- All development tools included

### 2. Dev Environment  
**Purpose**: Production-like testing, integration testing, staging

```bash
# Setup using environment-specific files
cd environments/dev
./deploy.sh

# Or manual setup
cp environments/dev/.env.template .env
# Edit .env with your dev-specific values
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver dev
```

**Features**:
- PostgreSQL database
- Production-like security (but relaxed)
- Test SMTP configuration
- Test Paystack keys
- Redis caching (with fallback)
- Production-like performance settings

### 3. Production Environment
**Purpose**: Live deployment

```bash
# Setup using environment-specific files
cd environments/production
./deploy.sh

# Or manual setup
cp environments/production/.env.template .env
# Edit .env with LIVE production values
python manage.py migrate
python manage.py collectstatic --noinput

# Run (for testing only - use gunicorn for actual production)
python manage.py runserver prod
```

**Features**:
- PostgreSQL with SSL
- Maximum security settings
- Live SMTP configuration
- Live Paystack keys
- Redis caching (required)
- Optimized for performance and security

## Environment Variables

### Feature/Local (.env.example)
```bash
DJANGO_ENVIRONMENT=development
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=local-dev-key
# Most settings have sensible defaults
# See environments/feature/.env.template for full list
```

### Dev (.env)
```bash
DJANGO_ENVIRONMENT=dev
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=dev-secret-key
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,dev.adakings.local
DB_NAME=adakings_dev
DB_USER=dev_user
DB_PASSWORD=dev_password_123
# See environments/dev/.env.template for full list
```

### Production (.env)
```bash
DJANGO_ENVIRONMENT=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=super-secret-production-key
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=adakings_prod
DB_USER=prod_user
DB_PASSWORD=secure_production_password
# See environments/production/.env.template for full list
```

## Smart Deploy Integration

The smart deploy script automatically handles environment-specific files and version management:

```bash
# Deploy to dev environment with version bump
python smart_deploy.py dev minor        # Updates environments/dev/VERSION

# Deploy to production with version bump
python smart_deploy.py production patch # Updates environments/production/VERSION

# Deploy to feature branch with version bump
python smart_deploy.py feature/auth patch # Updates environments/feature/VERSION
```

### Version Management
- Each environment maintains its own version file
- Versions start from 1.0.0 for all environments
- Smart deploy only pushes environment-specific files + core application files

## API Documentation Access

### Feature/Local Environment
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Full interactive documentation

### Dev Environment  
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Full documentation with test data

### Production Environment
- API documentation **disabled** for security
- Schema available only for authenticated admin users

## Common Workflows

### Feature Development
```bash
# 1. Start local environment
python manage.py runserver local

# 2. Make changes, test locally
# 3. Run tests
python manage.py test

# 4. Deploy to feature branch when ready (updates environments/feature/VERSION)
python smart_deploy.py feature/my-feature patch
```

### Testing Integration
```bash
# 1. Switch to dev environment  
python manage.py runserver dev

# 2. Test production-like behavior
# 3. Deploy to dev when ready (updates environments/dev/VERSION)
python smart_deploy.py dev minor
```

### Production Deployment
```bash
# 1. Test in production mode locally (optional)
python manage.py runserver prod

# 2. Deploy to production (updates environments/production/VERSION)
python smart_deploy.py production patch
```

## Troubleshooting

### Environment Not Loading
```bash
# Check environment detection
python -c "import os; print(os.environ.get('DJANGO_ENVIRONMENT', 'not set'))"

# Check settings module
python manage.py diffsettings
```

### Database Issues
```bash
# Check database configuration
python manage.py check --database default

# Test database connection
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Connected!')"
```

### Environment-Specific Debugging
```bash
# Show current settings
python manage.py diffsettings

# Show environment info
python manage.py shell -c "
from django.conf import settings
print(f'Environment: {settings.ENVIRONMENT}')  
print(f'Debug: {settings.DEBUG}')
print(f'Database: {settings.DATABASES[\"default\"][\"ENGINE\"]}')
"
```

## Version Management

### Environment-Specific Versions
Each environment maintains its own version:
- `environments/production/VERSION` - Production version
- `environments/dev/VERSION` - Dev environment version  
- `environments/feature/VERSION` - Feature environment version

### Version Bumping
```bash
# All environments start from 1.0.0
# Smart deploy automatically bumps versions
python smart_deploy.py production major  # 1.0.0 → 2.0.0
python smart_deploy.py dev minor         # 1.0.0 → 1.1.0  
python smart_deploy.py feature/auth patch # 1.0.0 → 1.0.1
```

### Git Integration
Smart deploy only pushes:
- Environment-specific files for the target environment
- Core application files
- Utility scripts (`smart_deploy.py`, `ENVIRONMENT_GUIDE.md`)

## Best Practices

1. **Never mix environments** - Use environment-specific .env files
2. **Test in dev before production** - Always validate in dev environment first  
3. **Use appropriate tools** - Debug toolbar in local, monitoring in production
4. **Secure secrets** - Never commit real credentials to version control
5. **Validate configuration** - Use Django's check command before deployment
6. **Monitor logs** - Check appropriate log files for each environment
7. **Use environment-specific scripts** - Run setup scripts from environment directories
8. **Version consistency** - Let smart deploy handle version management

---

**Need Help?** Check the environment-specific README files in the `environments/` directory for detailed setup instructions.
