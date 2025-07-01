#!/bin/bash
# Dev deployment script for Adakings Backend API
# This script sets up the development environment for testing

set -e  # Exit on any error

echo "🔧 Starting Adakings Backend API dev environment setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="adakings_backend"
PROJECT_DIR="$(pwd)"
VENV_DIR="$PROJECT_DIR/venv"
ENV_DIR="$PROJECT_DIR/environments/dev"
LOG_DIR="$PROJECT_DIR/logs"

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

# Create necessary directories
log_info "Creating directory structure..."
mkdir -p $LOG_DIR
log_success "Directory structure created"

# Check if dev .env file exists
if [ ! -f "$ENV_DIR/.env" ]; then
    log_warning "Dev .env file not found. Creating from template..."
    if [ -f "$ENV_DIR/.env.template" ]; then
        cp "$ENV_DIR/.env.template" "$ENV_DIR/.env"
        log_info "Please edit $ENV_DIR/.env with your dev-specific values"
    else
        log_error "Dev .env template not found at $ENV_DIR/.env.template!"
        exit 1
    fi
fi

# Copy dev environment file to project root
log_info "Setting up dev environment..."
cp "$ENV_DIR/.env" ".env"
log_success "Dev environment configured"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment..."
    python -m venv $VENV_DIR
    log_success "Virtual environment created"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source $VENV_DIR/bin/activate
log_success "Virtual environment activated"

# Install/update dev dependencies
log_info "Installing dev dependencies..."
pip install --upgrade pip
pip install -r $ENV_DIR/requirements.txt
log_success "Dev dependencies installed"

# Set Django settings for dev
export DJANGO_SETTINGS_MODULE=adakings_backend.settings.dev
export DJANGO_ENVIRONMENT=dev

# Run Django commands
log_info "Running Django management commands..."

# Run database migrations
log_info "Running database migrations..."
python manage.py migrate --noinput
log_success "Database migrations completed"

# Create cache table (if using database cache)
log_info "Creating cache table..."
python manage.py createcachetable || log_warning "Cache table creation failed or already exists"

# Create superuser if requested
read -p "Create superuser? (y/N): " create_superuser
if [[ $create_superuser =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

# Load sample data if available
if [ -f "fixtures/dev_sample_data.json" ]; then
    read -p "Load sample data? (y/N): " load_data
    if [[ $load_data =~ ^[Yy]$ ]]; then
        log_info "Loading sample data..."
        python manage.py loaddata fixtures/dev_sample_data.json
        log_success "Sample data loaded"
    fi
fi

# Check deployment
log_info "Running deployment checks..."
python manage.py check
log_success "Deployment checks passed"

# Test database connection
log_info "Testing database connection..."
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
log_success "Database connection verified"

# Final status
log_success "🎉 Dev environment setup completed successfully!"
log_info "You can now run: python manage.py runserver dev"
log_info "API Documentation: http://localhost:8000/api/docs/"
log_info "Admin interface: http://localhost:8000/admin/"

echo
log_info "Dev Environment Ready!"
log_info "Setup completed at: $(date)"
log_info "Environment: Dev (Production-like with test values)"
log_info "Database: PostgreSQL (Dev)"
log_info "Debug Mode: Configurable (check .env file)"
