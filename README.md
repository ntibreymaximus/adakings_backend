# Adakings Backend API - Feature Environment

## Overview
This is the **feature environment** for the Adakings Backend API. This environment is optimized for local development with debugging enabled, minimal setup requirements, and developer-friendly features.

## Features
- SQLite database (no PostgreSQL setup required)
- Django Debug Toolbar (optional)
- Console email backend
- Test Paystack integration
- Relaxed security settings for development
- Hot reloading and debugging
- Comprehensive API documentation

## Running the Feature Environment

```bash
# Start the local development server
python manage.py runserver local

# Or with custom port
python manage.py runserver local 8001
```

## Environment Variables
For feature development, you can use the example environment file:

```bash
cp .env.feature.template .env.example
# Edit .env.example with your local values (optional)
```

Many settings have sensible defaults for local development.

## Database Setup
```bash
# Create and migrate database (SQLite)
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (if available)
python manage.py loaddata feature_sample_data.json
```

## Development Features
- **Hot Reloading**: Code changes automatically reload the server
- **Debug Mode**: Detailed error pages and debugging information
- **Console Email**: Emails are printed to the console
- **API Documentation**: Full Swagger UI and ReDoc available
- **Debug Toolbar**: Optional Django Debug Toolbar for performance analysis
- **Relaxed CORS**: Allows all origins for easy frontend integration

## Database Options
### SQLite (Default - Recommended for features)
```python
# No setup required - works out of the box
DATABASE_URL=sqlite:///adakings_feature.db
```

### PostgreSQL (Optional - for production-like testing)
```bash
# If you want to test with PostgreSQL locally
DB_NAME=adakings_feature
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

## API Documentation
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- API Schema: http://localhost:8000/api/schema/

## Development Tools

### Django Debug Toolbar (Optional)
Enable debug toolbar by setting:
```bash
ENABLE_DEBUG_TOOLBAR=True
```

### Email Testing
Emails are printed to console by default. For testing email sending:
```bash
# Use Mailtrap or similar for email testing
EMAIL_HOST=smtp.mailtrap.io
EMAIL_PORT=2525
EMAIL_HOST_USER=your_mailtrap_user
EMAIL_HOST_PASSWORD=your_mailtrap_password
```

## Logging
Development logs are written to:
- Console: DEBUG level and above
- File: `logs/development.log` (DEBUG level and above)

## Cache Configuration
- Default: Dummy cache (no setup required)
- Optional: Redis (if REDIS_URL is configured)

## Testing Paystack Integration
Use test keys only:
```bash
PAYSTACK_PUBLIC_KEY_LIVE=pk_test_your_test_key
PAYSTACK_SECRET_KEY_LIVE=sk_test_your_test_key
```

## Common Development Commands
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Start interactive shell
python manage.py shell

# Check for issues
python manage.py check

# Collect static files (if needed)
python manage.py collectstatic
```

## Performance Considerations
- Generous file upload limits (10MB)
- No rate limiting
- Relaxed security settings
- Longer JWT token lifetimes for convenience

---
**Environment**: Feature/Local  
**Purpose**: Local development and feature work  
**Database**: SQLite (default) or PostgreSQL (optional)  
**Debug Mode**: TRUE (always)
