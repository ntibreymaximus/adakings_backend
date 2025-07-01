#!/bin/bash
# Feature environment setup script for Adakings Backend API
# This script sets up the local development environment

set -e  # Exit on any error

echo "🛠️ Starting Adakings Backend API feature environment setup..."

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
ENV_DIR="$PROJECT_DIR/environments/feature"
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

# Check if feature .env.example file exists, create if needed
if [ ! -f ".env.example" ]; then
    log_info "Creating .env.example from feature template..."
    if [ -f "$ENV_DIR/.env.template" ]; then
        cp "$ENV_DIR/.env.template" ".env.example"
        log_success ".env.example created"
    else
        log_error "Feature .env template not found at $ENV_DIR/.env.template!"
        exit 1
    fi
else
    log_info ".env.example already exists"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment..."
    python -m venv $VENV_DIR
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source $VENV_DIR/bin/activate
log_success "Virtual environment activated"

# Install/update feature dependencies
log_info "Installing feature development dependencies..."
pip install --upgrade pip
pip install -r $ENV_DIR/requirements.txt
log_success "Feature dependencies installed"

# Set Django settings for development
export DJANGO_SETTINGS_MODULE=adakings_backend.settings.development
export DJANGO_ENVIRONMENT=development

# Run Django commands
log_info "Running Django management commands..."

# Run database migrations (SQLite by default)
log_info "Running database migrations..."
python manage.py migrate --noinput
log_success "Database migrations completed"

# Create superuser if requested
read -p "Create superuser for local development? (y/N): " create_superuser
if [[ $create_superuser =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

# Load sample data if available
if [ -f "fixtures/feature_sample_data.json" ]; then
    read -p "Load sample data? (y/N): " load_data
    if [[ $load_data =~ ^[Yy]$ ]]; then
        log_info "Loading sample data..."
        python manage.py loaddata fixtures/feature_sample_data.json
        log_success "Sample data loaded"
    fi
fi

# Check for development tools
log_info "Checking development tools..."

# Check if debug toolbar is available
python -c "import debug_toolbar" 2>/dev/null && log_success "Debug toolbar available" || log_warning "Debug toolbar not available (optional)"

# Check if pytest is available
python -c "import pytest" 2>/dev/null && log_success "Pytest available" || log_warning "Pytest not available"

# Check deployment
log_info "Running development checks..."
python manage.py check
log_success "Development checks passed"

# Test database connection
log_info "Testing database connection..."
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
log_success "Database connection verified"

# Run tests if available
read -p "Run tests? (y/N): " run_tests
if [[ $run_tests =~ ^[Yy]$ ]]; then
    log_info "Running tests..."
    python manage.py test || log_warning "Some tests failed"
fi

# Final status
log_success "🎉 Feature environment setup completed successfully!"
log_info "You can now run: python manage.py runserver local"
log_info "API Documentation: http://localhost:8000/api/docs/"
log_info "Admin interface: http://localhost:8000/admin/"

echo
log_info "Feature Environment Ready!"
log_info "Setup completed at: $(date)"
log_info "Environment: Feature/Local Development"
log_info "Database: SQLite (local file)"
log_info "Debug Mode: Enabled"
log_info "Hot Reloading: Enabled"

echo
log_info "Next Steps:"
log_info "1. Start development server: python manage.py runserver local"
log_info "2. Open browser: http://localhost:8000/api/docs/"
log_info "3. Start coding your features!"
log_info "4. Run tests: python manage.py test"
