# Adakings Backend API - Production Environment

## Overview
This is the **production environment** for the Adakings Backend API. This environment is optimized for production deployment with maximum security, performance, and reliability.

## Features
- Full production security settings
- PostgreSQL database with SSL
- Redis caching
- SMTP email configuration
- Live Paystack integration
- Comprehensive logging and monitoring
- Optimized performance settings

## ⚠️ IMPORTANT SECURITY NOTICE
This is the PRODUCTION environment. Never use this configuration for development or testing.

## Running the Production Environment

```bash
# Start the production server (for testing only)
python manage.py runserver prod

# For actual production, use:
gunicorn adakings_backend.wsgi:application --bind 0.0.0.0:8000
```

## Environment Variables
Production requires a complete `.env` file with live values. Use `.env.production.template` as a reference:

```bash
cp .env.production.template .env
# Edit .env with your LIVE production values
```

### Required Production Environment Variables
- `DJANGO_SECRET_KEY`: Strong secret key for production
- `DJANGO_ALLOWED_HOSTS`: Your domain(s)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Production database credentials
- `PAYSTACK_PUBLIC_KEY_LIVE`, `PAYSTACK_SECRET_KEY_LIVE`: Live Paystack keys
- `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`: SMTP settings
- `REDIS_URL`: Redis cache URL
- `CORS_ALLOWED_ORIGINS`: Your frontend domain(s)

## Database Setup
```bash
# Run migrations (production database)
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create production superuser
python manage.py createsuperuser
```

## Security Features
- SSL/TLS enforced
- HSTS headers enabled
- Secure cookies
- XSS protection
- Content type sniffing protection
- CSRF protection with trusted origins
- Frame denial protection

## Performance Features
- Redis caching
- Session caching
- Optimized database connections
- Static file optimization
- Compressed responses

## API Documentation
- Swagger UI: **DISABLED** in production
- ReDoc: **DISABLED** in production
- API Schema: Available for authorized users only

## Logging
Production logs are written to:
- File: `logs/production.log` (INFO level and above)
- Console: ERROR level only
- Structured logging for monitoring integration

## Monitoring
- Health check endpoints available
- Error tracking integration ready
- Performance monitoring ready

## Deployment Checklist
- [ ] All environment variables configured
- [ ] Database properly configured and migrated
- [ ] Static files collected
- [ ] Redis cache available
- [ ] SSL certificates configured
- [ ] Domain configured in ALLOWED_HOSTS
- [ ] CORS origins configured
- [ ] Email service configured and tested
- [ ] Paystack live keys configured and tested
- [ ] Backup strategy in place
- [ ] Monitoring configured

---
**Environment**: Production  
**Purpose**: Live production deployment  
**Database**: PostgreSQL with SSL  
**Debug Mode**: FALSE (always)
