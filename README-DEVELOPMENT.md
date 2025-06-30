# Adakings Backend API - Development

[![Version](https://img.shields.io/badge/version-v1.0.3-blue.svg)](https://github.com/ntibreymaximus/adakings_backend)
[![Status](https://img.shields.io/badge/status-development-orange.svg)](https://github.com/ntibreymaximus/adakings_backend)
[![API](https://img.shields.io/badge/API-REST-orange.svg)](https://github.com/ntibreymaximus/adakings_backend)

A RESTful API backend for the Adakings restaurant management system, built with Django and Django REST Framework. This is the development version with all development tools and utilities.

## 🔧 Development Information

- **Current Version**: v1.0.3
- **Environment**: Development
- **API Base URL**: `http://127.0.0.1:8000/api/`
- **Status**: 🔧 In Development

## 🛠️ Development Features

### Core Modules
- **Authentication & Authorization**: JWT-ready session-based auth
- **Menu Management**: Categories, items, extras, pricing
- **Order Processing**: Real-time order tracking and management
- **Payment Integration**: Cash and Mobile Money (Paystack - Test Mode)
- **User Management**: Role-based access control
- **API Documentation**: Swagger UI and ReDoc

### Development Tools
- **Django Debug Toolbar**: Performance analysis
- **API Documentation**: Interactive Swagger UI at `/api/docs/`
- **Test Framework**: Comprehensive test suite
- **Form Validation**: Django forms for testing
- **Template Tags**: Development utilities
- **Debug Scripts**: Database debugging tools

## 📚 API Documentation

### Available Endpoints
- **OpenAPI Schema**: `/api/schema/`
- **Swagger UI**: `/api/docs/swagger/`
- **ReDoc**: `/api/docs/`

## 🚀 Development Setup

### Prerequisites
- Python 3.8+
- SQLite (default) or PostgreSQL
- Git

### Quick Start
```bash
# Clone development branch
git clone -b dev https://github.com/ntibreymaximus/adakings_backend.git
cd adakings_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your development values

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Environment Configuration
```bash
# Development settings in .env
DJANGO_ENVIRONMENT=development
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0

# Test Paystack keys
PAYSTACK_PUBLIC_KEY=pk_test_your_test_key
PAYSTACK_SECRET_KEY=sk_test_your_test_key
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.users
python manage.py test apps.orders

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### API Testing
```bash
# Test API endpoints
python manage.py shell
>>> from django.test import Client
>>> client = Client()
>>> response = client.get('/api/schema/')
>>> response.status_code
```

## 🔧 Development Tools

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database
python manage.py flush

# Load sample data
python manage.py loaddata fixtures/sample_data.json
```

### Debug Tools
```bash
# Django shell
python manage.py shell

# Debug transactions
python debug_transactions.py

# Check deployment readiness
python manage.py check
```

## 📝 Development Workflow

### Branch Strategy
- **dev**: Main development branch
- **feature/***: Feature development branches
- **hotfix/***: Emergency fixes

### Code Quality
```bash
# Code formatting
black .
isort .

# Linting
flake8
pylint apps/

# Type checking
mypy apps/
```

## 🔄 Version Management

### Semantic Versioning
- **MAJOR**: Breaking changes
- **MINOR**: New features
- **PATCH**: Bug fixes

### Version Bumping
```bash
# Development versions
python bump_version.py patch   # Bug fixes
python bump_version.py minor   # New features
python bump_version.py major   # Breaking changes
```

## 🚀 Deployment to Other Environments

### Deploy to Production
```bash
# Use smart deployment script
python smart_deploy.py production
```

### Deploy to Staging
```bash
python smart_deploy.py feature/staging
```

## 🐛 Debugging

### Common Issues
- **Database locked**: Stop server and delete `db.sqlite3`
- **Migration conflicts**: Reset migrations
- **CORS errors**: Check `CORS_ALLOW_ALL_ORIGINS` setting

### Debug Mode Features
- Detailed error pages
- SQL query logging
- Template debugging
- Static file serving

## 📊 Development Metrics

### Performance Monitoring
- Django Debug Toolbar
- SQL query analysis
- Response time monitoring
- Memory usage tracking

## 🔒 Security (Development)

### Development Security
- Debug mode enabled for detailed errors
- Relaxed CORS settings for frontend development
- Test payment keys only
- Console email backend

## 📞 Development Support

### Getting Help
1. Check development documentation
2. Review API documentation at `/api/docs/`
3. Run tests to verify functionality
4. Check Django debug toolbar for performance issues

---

**Development Branch**: `dev`  
**Last Updated**: June 30, 2025  
**Development Team**: Adakings Developers
