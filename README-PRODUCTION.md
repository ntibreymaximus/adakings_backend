# Adakings Backend API - Production

[![Version](https://img.shields.io/badge/version-v1.0.8-blue.svg)](https://github.com/ntibreymaximus/adakings_backend)
[![Status](https://img.shields.io/badge/status-production-green.svg)](https://github.com/ntibreymaximus/adakings_backend)
[![API](https://img.shields.io/badge/API-REST-orange.svg)](https://github.com/ntibreymaximus/adakings_backend)

A production-ready RESTful API backend for the Adakings restaurant management system, built with Django and Django REST Framework.

## 🚀 Production Information

- **Current Version**: v1.0.8
- **Release Date**: June 30, 2025
- **Environment**: Production
- **API Base URL**: `https://api.adakings.com/api/` (Replace with your actual domain)
- **Status**: ✅ Stable

## 📋 Version History

### v1.0.0 (2025-06-30) - **PRODUCTION RELEASE**
- **MAJOR RELEASE**: Complete API-only architecture
- **Breaking Changes**: Removed all web interface components
- **Features**:
  - Pure REST API backend using Django REST Framework
  - Comprehensive API documentation with Swagger/OpenAPI
  - Session-based authentication with API permissions
  - Complete serializers for all models (menu, orders, payments, users)
  - Optimized database models and migrations
  - Paystack payment integration for mobile money
  - Role-based access control (Admin, Kitchen, Front Desk, Delivery)
  - Order management with status tracking
  - Menu management with categories and extras
  - User management and authentication

## 🛡️ Production Features

### Core Modules
- **Authentication & Authorization**: JWT-ready session-based auth
- **Menu Management**: Categories, items, extras, pricing
- **Order Processing**: Real-time order tracking and management
- **Payment Integration**: Cash and Mobile Money (Paystack)
- **User Management**: Role-based access control
- **API Documentation**: Swagger UI and ReDoc

### Security Features
- CORS configuration for frontend integration
- Environment-based configuration
- Secure payment processing
- Role-based permissions
- Input validation and sanitization

## 📚 API Documentation

### Available Endpoints
- **OpenAPI Schema**: `/api/schema/`
- **Swagger UI**: `/api/docs/swagger/`
- **ReDoc**: `/api/docs/`

### Core API Endpoints
```
Authentication:
POST   /api/users/register/     - User registration
POST   /api/users/login/        - User login
POST   /api/users/logout/       - User logout
GET    /api/users/me/           - Current user profile

Menu Management:
GET    /api/menu/categories/    - List categories
GET    /api/menu/items/         - List menu items
GET    /api/menu/extras/        - List extras

Order Management:
GET    /api/orders/             - List orders
POST   /api/orders/             - Create new order
GET    /api/orders/{id}/        - Order details
PUT    /api/orders/{id}/        - Update order

Payment Processing:
POST   /api/payments/process/   - Process payment
GET    /api/payments/verify/    - Verify payment status
```

## 🔧 Production Setup

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended for production)
- Redis (for caching - optional)
- NGINX (for reverse proxy)

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/adakings_prod

# Django Settings
DJANGO_SECRET_KEY=your-production-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# Payment Integration
PAYSTACK_PUBLIC_KEY=pk_live_your_live_public_key
PAYSTACK_SECRET_KEY=sk_live_your_live_secret_key

# CORS (for frontend)
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Production Deployment
1. Clone the production branch
2. Set up virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment variables
5. Run migrations: `python manage.py migrate`
6. Collect static files: `python manage.py collectstatic`
7. Start with WSGI server (Gunicorn recommended)

### Health Check
```bash
curl -f http://localhost:8000/api/schema/ || exit 1
```

## 🔄 Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes, incompatible API changes
- **MINOR** (X.Y.0): New features, backward compatible
- **PATCH** (X.Y.Z): Bug fixes, backward compatible

### Version Bump Guidelines
- **MAJOR**: API breaking changes, architecture changes
- **MINOR**: New endpoints, new features, database schema additions
- **PATCH**: Bug fixes, security patches, documentation updates

## 🚀 Deployment

### Quick Start
```bash
# Clone production branch
git clone -b production https://github.com/ntibreymaximus/adakings_backend.git
cd adakings_backend

# Setup environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment  
# Edit .env file with your production values

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Start server
python manage.py runserver 0.0.0.0:8000
```

### Production Server (Gunicorn)
```bash
gunicorn --bind 0.0.0.0:8000 adakings_backend.wsgi:application
```

## 📊 Performance & Monitoring

### Recommended Monitoring
- API response times
- Database query performance
- Payment transaction success rates
- User authentication metrics
- Error rates and logging

### Scaling Considerations
- Database connection pooling
- Redis caching implementation
- Load balancer configuration
- CDN for static assets

## 🛠️ Maintenance

### Regular Tasks
- Monitor server logs
- Update dependencies
- Database backups
- Security patches
- Performance optimization

### Support Information
- **Documentation**: Available in `/api/docs/`
- **Health Check**: `GET /api/health/` (if implemented)
- **Version Info**: `GET /api/version/` (if implemented)

## 📞 Production Support

For production issues:
1. Check server logs
2. Verify environment variables
3. Test database connectivity
4. Validate payment service status

## 🔒 Security

- Keep Django and dependencies updated
- Use HTTPS in production
- Implement rate limiting
- Monitor for suspicious activity
- Regular security audits

---

**Production Branch**: `production`  
**Last Updated**: June 30, 2025  
**Maintainer**: Adakings Development Team
