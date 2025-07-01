# Adakings Backend API - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Adakings Backend API to production environments. Both the **dev** and **production** environments are now fully configured with production-ready infrastructure.

## Available Deployment Methods

### 1. Traditional Server Deployment (Linux)
### 2. Docker Containerized Deployment
### 3. Windows Server Deployment

---

## Method 1: Traditional Linux Server Deployment

### Prerequisites
- Ubuntu 20.04+ or CentOS 8+ server
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Nginx
- Git

### Dev Environment Deployment

```bash
# 1. Clone repository
git clone <your-repo-url> /var/www/adakings_backend
cd /var/www/adakings_backend

# 2. Run dev environment setup
cd environments/dev
./deploy.sh

# 3. Install systemd service
sudo cp adakings-backend-dev.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable adakings-backend-dev
sudo systemctl start adakings-backend-dev

# 4. Configure Nginx
sudo cp nginx.conf /etc/nginx/sites-available/adakings-dev
sudo ln -s /etc/nginx/sites-available/adakings-dev /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 5. Check status
sudo systemctl status adakings-backend-dev
curl http://localhost:8001/health/
```

### Production Environment Deployment

```bash
# 1. Clone repository
git clone <your-repo-url> /var/www/adakings_backend
cd /var/www/adakings_backend

# 2. Configure production environment
cd environments/production
cp .env.template .env
# Edit .env with your production values

# 3. Run production deployment
./deploy.sh

# 4. Install systemd service
sudo cp adakings-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable adakings-backend
sudo systemctl start adakings-backend

# 5. Configure Nginx with SSL
sudo cp nginx.conf /etc/nginx/sites-available/adakings-prod
# Edit nginx.conf with your domain and SSL certificate paths
sudo ln -s /etc/nginx/sites-available/adakings-prod /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 6. Check status
sudo systemctl status adakings-backend
curl https://yourdomain.com/health/
```

---

## Method 2: Docker Containerized Deployment

### Dev Environment with Docker

```bash
cd environments/dev

# 1. Build and start services
docker-compose up -d --build

# 2. Check services
docker-compose ps
docker-compose logs web

# 3. Access application
curl http://localhost:8080/health/
```

### Production Environment with Docker

```bash
cd environments/production

# 1. Configure environment
cp .env.template .env
# Edit .env with production values

# 2. Build and start services
docker-compose up -d --build

# 3. Check services
docker-compose ps
docker-compose logs web

# 4. Access application (configure domain and SSL)
curl https://yourdomain.com/health/
```

### Docker Commands Reference

```bash
# View logs
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f redis

# Execute commands in container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic

# Scale services
docker-compose up -d --scale web=3

# Stop services
docker-compose down

# Remove volumes (careful - this deletes data!)
docker-compose down -v
```

---

## Method 3: Windows Server Deployment

### Dev Environment on Windows

```powershell
# 1. Clone repository
git clone <your-repo-url> C:\adakings_backend
cd C:\adakings_backend

# 2. Run PowerShell deployment script
.\environments\dev\deploy.ps1 -CreateSuperuser

# 3. Start application with gunicorn
python -m gunicorn -c environments\dev\gunicorn.conf.py adakings_backend.wsgi:application

# 4. Configure IIS or Nginx for Windows (optional)
```

### Production Environment on Windows

```powershell
# 1. Clone repository
git clone <your-repo-url> C:\adakings_backend
cd C:\adakings_backend

# 2. Configure production environment
copy environments\production\.env.template environments\production\.env
# Edit .env with production values

# 3. Run PowerShell deployment script
.\environments\production\deploy.ps1

# 4. Start application with gunicorn
python -m gunicorn -c environments\production\gunicorn.conf.py adakings_backend.wsgi:application

# 5. Configure IIS with reverse proxy or use Nginx for Windows
```

---

## Environment Configurations

### Dev Environment Features
- **Port**: 8001 (to avoid conflicts)
- **Debug Mode**: Configurable
- **Database**: PostgreSQL (dev instance)
- **Cache**: Redis
- **API Docs**: Enabled
- **Auto-reload**: Enabled
- **SSL**: Optional

### Production Environment Features
- **Port**: 8000
- **Debug Mode**: Disabled
- **Database**: PostgreSQL with SSL
- **Cache**: Redis (required)
- **API Docs**: Disabled
- **Auto-reload**: Disabled
- **SSL**: Required
- **Rate Limiting**: Enabled
- **Security Headers**: Maximum

---

## SSL Certificate Setup

### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Using Custom Certificates

```bash
# Copy certificates
sudo cp your-certificate.crt /etc/ssl/certs/adakings.crt
sudo cp your-private-key.key /etc/ssl/private/adakings.key

# Set permissions
sudo chmod 644 /etc/ssl/certs/adakings.crt
sudo chmod 600 /etc/ssl/private/adakings.key
```

---

## Monitoring and Maintenance

### Health Checks

```bash
# Application health
curl http://localhost:8000/health/

# Service status
sudo systemctl status adakings-backend
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis

# Docker health (if using Docker)
docker-compose ps
docker stats
```

### Log Monitoring

```bash
# Application logs
tail -f /var/www/adakings_backend/logs/gunicorn_error.log
tail -f /var/www/adakings_backend/logs/gunicorn_access.log

# System logs
sudo journalctl -u adakings-backend -f
sudo journalctl -u nginx -f

# Docker logs
docker-compose logs -f web
```

### Database Backup

```bash
# Manual backup
pg_dump adakings_production > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup (crontab)
0 2 * * * pg_dump adakings_production > /backups/adakings_$(date +\%Y\%m\%d).sql
```

---

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

2. **Permission denied**
   ```bash
   sudo chown -R adakings:adakings /var/www/adakings_backend
   sudo chmod -R 755 /var/www/adakings_backend
   ```

3. **Database connection failed**
   ```bash
   sudo systemctl status postgresql
   sudo -u postgres psql -c "SELECT version();"
   ```

4. **Static files not loading**
   ```bash
   python manage.py collectstatic --clear
   sudo systemctl reload nginx
   ```

### Performance Tuning

1. **Gunicorn workers**: Adjust in `gunicorn.conf.py`
2. **PostgreSQL**: Tune `postgresql.conf`
3. **Redis**: Configure `redis.conf`
4. **Nginx**: Enable gzip, set cache headers

---

## Security Checklist

- [ ] Environment variables configured
- [ ] Database credentials secured
- [ ] SSL certificates installed
- [ ] Firewall configured
- [ ] Debug mode disabled in production
- [ ] Secret keys rotated
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Database backups automated
- [ ] Log monitoring enabled

---

## Next Steps After Deployment

1. **Monitor application performance**
2. **Set up automated backups**
3. **Configure monitoring alerts**
4. **Implement CI/CD pipeline**
5. **Set up log aggregation**
6. **Configure application monitoring (e.g., Sentry)**
7. **Set up uptime monitoring**

For detailed environment-specific information, see the README files in each environment directory.
