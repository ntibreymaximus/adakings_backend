# Adakings Backend API - Dev Environment

## Overview
This is the **dev environment** for the Adakings Backend API. This environment uses production-like configuration but with development-safe values, making it ideal for testing production scenarios without real data or live services.

## Features
- Production-like database configuration (PostgreSQL)
- Production-like security settings (but relaxed)
- Test SMTP email configuration
- Test Paystack integration
- Production-like caching (Redis or fallback)
- Comprehensive logging
- API documentation enabled

## Running the Dev Environment

```bash
# Start the dev server
python manage.py runserver dev

# Or with custom port
python manage.py runserver dev 8001
```

## Environment Variables
Make sure you have a `.env` file with dev-specific values. Use `.env.dev.template` as a reference:

```bash
cp .env.dev.template .env
# Edit .env with your dev-specific values
```

## Database Setup
```bash
# Create and migrate database
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (if available)
python manage.py loaddata dev_sample_data.json
```

## Key Differences from Production
- Uses test Paystack keys
- Relaxed CORS and security settings
- Test email configuration
- Development-friendly database settings
- Optional debug toolbar support

## API Documentation
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- API Schema: http://localhost:8000/api/schema/

## Logging
Logs are written to:
- Console: INFO level and above
- File: `logs/dev.log` (INFO level and above)

## Cache Configuration
- Primary: Redis (if available)
- Fallback: Dummy cache (if Redis unavailable)

---
**Environment**: Dev  
**Purpose**: Production-like testing and development  
**Database**: PostgreSQL  
**Debug Mode**: Configurable (default: False)
