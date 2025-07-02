# Adakings Backend API - Unified Setup

A simplified Django REST API for the Adakings Restaurant Management System with unified configuration.

## What Changed

✅ **Consolidated all environments into one unified Django setup**
✅ **Single `.env` file for all configuration**
✅ **Simplified settings structure**
✅ **Standard Django commands**
✅ **Removed complex environment switching**

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
The `.env` file is already configured for development with:
- SQLite database
- Debug mode enabled
- Console email backend
- Test Paystack keys

### 3. Setup Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run the Server
```bash
python manage.py runserver
```

## Access Points

- **API Documentation**: http://127.0.0.1:8000/api/schema/swagger-ui/
- **Admin Panel**: http://127.0.0.1:8000/admin/ (superusers only)
- **API Base**: http://127.0.0.1:8000/api/

## Key Features

- **Unified Settings**: Single `settings.py` file that adapts based on `DJANGO_DEBUG`
- **Environment Variables**: All configuration through `.env` file
- **Role-Based Access**: Superadmin, Admin, Frontdesk, Kitchen, Delivery roles
- **JWT Authentication**: Token-based API authentication
- **Paystack Integration**: Payment processing for Ghana (GHS)
- **Auto-Documentation**: Swagger UI and ReDoc

## Configuration

### Development (Default)
```bash
DJANGO_DEBUG=True
DATABASE_ENGINE=sqlite3
DATABASE_NAME=db.sqlite3
```

### Production
```bash
DJANGO_DEBUG=False
DATABASE_ENGINE=postgresql
DB_NAME=your_production_db
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
```

## API Endpoints

- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `GET /api/users/` - List users
- `GET /api/menu/` - Menu items
- `POST /api/orders/` - Create order
- `POST /api/payments/` - Process payment

## Files Removed

The following complex environment files have been removed:
- `environments/` directory
- `deploy_environment.py`
- `setup_environments.ps1`
- `smart_deploy.py`
- Environment-specific documentation

## Benefits

✅ **Simplified setup** - Just copy `.env` and run
✅ **Standard Django** - No custom environment switching
✅ **Less complexity** - Single settings file
✅ **Easy deployment** - Environment variables drive configuration
✅ **Better maintainability** - Standard Django patterns

The application now follows standard Django conventions while maintaining all functionality!
