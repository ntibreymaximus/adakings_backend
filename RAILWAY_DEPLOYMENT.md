# Railway Deployment Guide for Adakings Backend

This guide will help you deploy your Django application to Railway with PostgreSQL.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Railway CLI** (optional): Install from [docs.railway.app/develop/cli](https://docs.railway.app/develop/cli)

## Step-by-Step Deployment

### 1. Create a New Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository containing the adakings_backend code

### 2. Add PostgreSQL Database

1. In your Railway project dashboard, click "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create a PostgreSQL instance and provide connection details

### 3. Configure Environment Variables

In your Railway project dashboard, go to the "Variables" section and add these environment variables:

#### Required Variables:
```bash
# Django Settings
DJANGO_SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
DJANGO_DEBUG=False
DJANGO_ENVIRONMENT=production

# Database (these are automatically set by Railway PostgreSQL service)
DATABASE_ENGINE=postgresql
# PGDATABASE, PGUSER, PGPASSWORD, PGHOST, PGPORT are auto-set by Railway

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# CORS - Update with your frontend domain
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
FRONTEND_URL=https://your-frontend-domain.com

# API Rate Limiting
RATE_LIMIT_ENABLE=True
RATE_LIMIT_REQUESTS=600
RATE_LIMIT_WINDOW=3600
```

#### Optional Variables (Configure as needed):
```bash
# Email Configuration (replace with your email provider)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@adakings.com

# Paystack Payment Gateway (NOT CONFIGURED YET - COMMENTED OUT)
# PAYSTACK_PUBLIC_KEY_LIVE=pk_live_your_public_key
# PAYSTACK_SECRET_KEY_LIVE=sk_live_your_secret_key

# Monitoring (Optional - sign up at sentry.io)
SENTRY_DSN=your-sentry-dsn-here

# Performance
MAX_UPLOAD_SIZE=10485760
CACHE_TIMEOUT=300
```

### 4. Deploy

1. Railway will automatically detect your Django app and start the deployment
2. The deployment will:
   - Install dependencies from `requirements-prod.txt`
   - Run database migrations
   - Collect static files
   - Start the gunicorn server

### 5. Custom Domain (Optional)

1. In Railway dashboard, go to "Settings" → "Domains"
2. Add your custom domain
3. Update your `DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` environment variables

### 6. Database Management

#### Run Django Management Commands:
1. Go to your Railway project dashboard
2. Click on your web service
3. Go to "Deploy" tab
4. Use the web console or deploy logs to run commands

#### Common Commands:
```bash
# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Clear cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

## Environment Variables Reference

### Automatically Set by Railway:
- `PORT` - The port your app should listen on
- `RAILWAY_ENVIRONMENT` - Current environment (production)
- `RAILWAY_PROJECT_ID` - Your project ID
- `RAILWAY_SERVICE_ID` - Your service ID
- `PGDATABASE`, `PGUSER`, `PGPASSWORD`, `PGHOST`, `PGPORT` - PostgreSQL connection details

### Must Be Set Manually:
- `DJANGO_SECRET_KEY` - Django secret key (generate a new one)
- `CORS_ALLOWED_ORIGINS` - Your frontend domain(s)
- Email service credentials (optional)
- Payment gateway credentials (when Paystack integration is completed)

## Monitoring and Debugging

1. **Logs**: Check Railway dashboard → "Deploy" tab for deployment and runtime logs
2. **Health Check**: Your app includes a health check at `/health/`
3. **Metrics**: Railway provides CPU, memory, and network metrics
4. **Database**: Monitor PostgreSQL metrics in the database service

## Security Considerations

1. **Secret Key**: Generate a new, random Django secret key for production
2. **HTTPS**: Railway provides HTTPS by default
3. **CORS**: Properly configure CORS for your frontend domain
4. **Environment Variables**: Never commit secrets to your repository
5. **Database**: Railway PostgreSQL is isolated and secure by default

## Troubleshooting

### Common Issues:

1. **Build Failures**: Check if all dependencies are in `requirements-prod.txt`
2. **Database Connection**: Verify PostgreSQL service is running and connected
3. **Static Files**: Ensure `collectstatic` runs during deployment
4. **Environment Variables**: Double-check all required variables are set

### Health Check:
Visit `https://your-app.railway.app/health/` to verify your deployment status.

## Cost Optimization

1. **Resource Usage**: Monitor your app's resource usage in Railway dashboard
2. **Database**: PostgreSQL usage is billed based on compute time
3. **Scaling**: Railway auto-scales based on demand

## Support

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Django Documentation**: [docs.djangoproject.com](https://docs.djangoproject.com)

---

**Next Steps**: After deployment, update your frontend application to use the new Railway backend URL.
