#!/bin/bash
# Production deployment script for Adakings Backend API
# This script deploys the application to production environment

set -e  # Exit on any error

echo "🚀 Starting Adakings Backend API production deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="adakings_backend"
PROJECT_DIR="/var/www/$PROJECT_NAME"
VENV_DIR="$PROJECT_DIR/venv"
STATIC_DIR="$PROJECT_DIR/staticfiles"
MEDIA_DIR="$PROJECT_DIR/mediafiles"
LOG_DIR="/var/log/adakings"
RUN_DIR="/var/run/adakings"
ENV_DIR="$PROJECT_DIR/environments/production"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root for security reasons"
   exit 1
fi

# Create necessary directories
log_info "Creating directory structure..."
sudo mkdir -p $LOG_DIR $RUN_DIR $STATIC_DIR $MEDIA_DIR
sudo chown -R $USER:$USER $LOG_DIR $RUN_DIR $STATIC_DIR $MEDIA_DIR
log_success "Directory structure created"

# Navigate to project directory
cd $PROJECT_DIR

# Check if production .env file exists
if [ ! -f "$ENV_DIR/.env" ]; then
    log_error "Production .env file not found at $ENV_DIR/.env!"
    log_info "Please copy $ENV_DIR/.env.template to $ENV_DIR/.env and configure with production values"
    exit 1
fi

# Copy production environment file to project root
log_info "Setting up production environment..."
cp "$ENV_DIR/.env" ".env"
log_success "Production environment configured"

# Activate virtual environment
log_info "Activating virtual environment..."
source $VENV_DIR/bin/activate
log_success "Virtual environment activated"

# Install/update production dependencies
log_info "Installing production dependencies..."
pip install --upgrade pip
pip install -r $ENV_DIR/requirements.txt
log_success "Production dependencies installed"

# Set Django settings for production
export DJANGO_SETTINGS_MODULE=adakings_backend.settings.production
export DJANGO_ENVIRONMENT=production

# Run Django commands
log_info "Running Django management commands..."

# Collect static files
log_info "Collecting static files..."
python manage.py collectstatic --noinput --clear
log_success "Static files collected"

# Run database migrations
log_info "Running database migrations..."
python manage.py migrate --noinput
log_success "Database migrations completed"

# Create cache table (if using database cache)
log_info "Creating cache table..."
python manage.py createcachetable || log_warning "Cache table creation failed or already exists"

# Check deployment
log_info "Running deployment checks..."
python manage.py check --deploy
log_success "Deployment checks passed"

# Test database connection
log_info "Testing database connection..."
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
log_success "Database connection verified"

# Restart services
log_info "Restarting services..."

# Restart Gunicorn (assuming systemd service)
if systemctl is-active --quiet gunicorn-adakings; then
    sudo systemctl restart gunicorn-adakings
    log_success "Gunicorn restarted"
else
    log_warning "Gunicorn service not found or not running"
fi

# Restart Nginx (if applicable)
if systemctl is-active --quiet nginx; then
    sudo systemctl reload nginx
    log_success "Nginx reloaded"
else
    log_warning "Nginx service not found or not running"
fi

# Clear Django cache (if using cache)
log_info "Clearing application cache..."
python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared')" || log_warning "Cache clear failed"

# Set proper permissions
log_info "Setting file permissions..."
sudo chown -R $USER:www-data $PROJECT_DIR
sudo chmod -R 755 $PROJECT_DIR
sudo chmod -R 775 $STATIC_DIR $MEDIA_DIR $LOG_DIR
log_success "File permissions set"

# Health check
log_info "Performing health check..."
sleep 5  # Wait for services to start

# Check if API is responding
if curl -f http://localhost:8000/api/schema/ > /dev/null 2>&1; then
    log_success "API health check passed"
else
    log_error "API health check failed"
    exit 1
fi

# Final status
log_success "🎉 Production deployment completed successfully!"
log_info "API is available at: https://your-domain.com/api/"
log_info "Admin interface: https://your-domain.com/admin/"
log_info "Health check: https://your-domain.com/health/"

# Show service status
echo
log_info "Service Status:"
systemctl is-active gunicorn-adakings || echo "Gunicorn: Not running"
systemctl is-active nginx || echo "Nginx: Not running"

echo
log_info "Deployment completed at: $(date)"
log_info "Check logs at: $LOG_DIR"
log_info "Environment: Production"
