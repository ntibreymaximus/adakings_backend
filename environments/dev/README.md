# Adakings Backend API - Development Environment

## Development Environment

This is the development environment for the Adakings Backend API. This environment provides a production-like setup but with development-friendly configurations and test data.

### Features
- Production-like Django settings with development values
- PostgreSQL database (like production)
- Redis caching
- Docker containerization
- Development debugging tools
- Test data and fixtures
- Development-friendly logging

### Purpose
The dev environment serves as:
- **Staging Environment**: Test production-like configurations
- **Integration Testing**: Test with production-similar setup
- **Team Development**: Shared development environment
- **Pre-production Testing**: Final testing before production deployment

### Differences from Production
- Debug mode can be enabled
- Less strict security settings
- Development-friendly CORS settings
- Test database credentials
- Enhanced logging for debugging
- Development tools included

### Infrastructure
- **Web Server**: Nginx (development configuration)
- **Application Server**: Gunicorn (development settings)
- **Database**: PostgreSQL (test database)
- **Cache**: Redis
- **Containerization**: Docker + Docker Compose

### Deployment
Use the smart deploy script to deploy to dev:
```bash
python smart_deploy.py dev [minor|patch]
```

### Environment Variables
Copy `.env.template` to `.env` and configure with development values:
- Test database credentials
- Development secret keys
- Test API keys (Paystack test keys)
- Development domain configurations
- Relaxed security settings

### Development Tools
- Django Debug Toolbar (optional)
- Enhanced logging
- API documentation (Swagger/ReDoc)
- Development fixtures
- Test data management

### Database
- PostgreSQL database with test data
- Development fixtures
- Migration testing
- Database seeding scripts

### Testing
- Integration testing
- API endpoint testing
- Database migration testing
- Performance testing
- Security testing

### Monitoring
- Application logs: Development level
- Database logs: Detailed for debugging
- Request/response logging
- Performance metrics

### Support
For development environment support, contact the development team.
