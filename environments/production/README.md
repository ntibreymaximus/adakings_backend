# Adakings Backend API - Production Environment

## Production Deployment

This is the production environment for the Adakings Backend API. This environment contains production-optimized configurations and should only be deployed to live servers.

### Features
- Production-optimized Django settings
- Gunicorn WSGI server configuration
- Nginx reverse proxy configuration
- Docker containerization
- PostgreSQL database configuration
- SSL/TLS security configurations
- Performance optimizations
- Production logging and monitoring

### Security
- Debug mode disabled
- Secure headers enabled
- HTTPS redirects
- CSRF protection
- CORS configured for production domains
- Environment variables for sensitive data

### Infrastructure
- **Web Server**: Nginx
- **Application Server**: Gunicorn
- **Database**: PostgreSQL
- **Containerization**: Docker + Docker Compose
- **Process Management**: Systemd service

### Deployment
Use the smart deploy script to deploy to production:
```bash
python smart_deploy.py production [major|minor|patch]
```

### Environment Variables
Copy `.env.template` to `.env` and configure with production values:
- Database credentials
- Secret keys
- API keys (Paystack live keys)
- Domain configurations
- SSL certificate paths

### Monitoring
- Application logs: `/var/log/adakings/`
- Nginx logs: `/var/log/nginx/`
- Database logs: PostgreSQL logs
- System service: `systemctl status adakings-backend`

### Support
For production support, contact the development team.
