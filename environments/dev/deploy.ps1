# Dev environment setup script for Adakings Backend API (Windows)
# This script sets up the development environment on Windows

param(
    [switch]$CreateSuperuser = $false,
    [switch]$LoadSampleData = $false
)

# Configuration
$PROJECT_NAME = "adakings_backend"
$PROJECT_DIR = Get-Location
$VENV_DIR = Join-Path $PROJECT_DIR "venv"
$ENV_DIR = Join-Path $PROJECT_DIR "environments\dev"

# Functions
function Write-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Host "🔧 Starting Adakings Backend API dev environment setup..." -ForegroundColor Cyan

# Check if dev .env file exists
$envDev = Join-Path $ENV_DIR ".env"
$envTemplate = Join-Path $ENV_DIR ".env.template"

if (!(Test-Path $envDev)) {
    Write-Warning "Dev .env file not found. Creating from template..."
    if (Test-Path $envTemplate) {
        Copy-Item $envTemplate $envDev
        Write-Info "Please edit $envDev with your dev-specific values"
    } else {
        Write-Error "Dev .env template not found at $envTemplate!"
        exit 1
    }
}

# Create virtual environment if it doesn't exist
if (!(Test-Path $VENV_DIR)) {
    Write-Info "Creating virtual environment..."
    python -m venv $VENV_DIR
    Write-Success "Virtual environment created"
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
$activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Success "Virtual environment activated"
}

# Install/update dev dependencies
# Copy dev-specific production configurations
Write-Info "Setting up dev-specific configurations..."
$devGunicornConf = Join-Path $ENV_DIR "gunicorn.conf.py"
if (Test-Path $devGunicornConf) {
    Copy-Item $devGunicornConf "gunicorn_dev.conf.py"
    Write-Success "Dev gunicorn configuration copied"
}

Write-Info "Installing dev dependencies..."
$requirementsFile = Join-Path $ENV_DIR "requirements.txt"
if (Test-Path $requirementsFile) {
    python -m pip install --upgrade pip
    python -m pip install -r $requirementsFile
    Write-Success "Dev dependencies installed"
}

# Run Django commands
Write-Info "Running Django management commands..."

# Run database migrations
Write-Info "Running database migrations..."
python manage.py migrate --noinput
Write-Success "Database migrations completed"

Write-Info "Creating cache table..."
python manage.py createcachetable

# Create superuser if requested
if ($CreateSuperuser) {
    Write-Host "Creating superuser..."
    python manage.py createsuperuser
}

# Load sample data if available
$sampleDataFile = Join-Path $PROJECT_DIR "fixtures\dev_sample_data.json"
if ((Test-Path $sampleDataFile) -and $LoadSampleData) {
    Write-Info "Loading sample data..."
    python manage.py loaddata $sampleDataFile
    Write-Success "Sample data loaded"
}

# Check deployment
Write-Info "Running deployment checks..."
python manage.py check
Write-Success "Deployment checks passed"

# Test database connection
Write-Info "Testing database connection..."
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
Write-Success "Database connection verified"

# Final status
Write-Success "🎉 Dev environment setup completed successfully!"
Write-Info "You can now run: python manage.py runserver dev"
Write-Info "API Documentation: http://localhost:8000/api/docs/"
Write-Info "Admin interface: http://localhost:8000/admin/"

Write-Host ""
Write-Info "Dev Environment Ready!"
Write-Info "Setup completed at: $(Get-Date)"
Write-Info "Environment: Dev (Production-like with test values)"
Write-Info "Database: PostgreSQL (Dev)"
Write-Info "Debug Mode: Configurable (check .env file)"

Write-Host ""
Write-Info "To use this script with options:"
Write-Info ".\deploy.ps1 -CreateSuperuser -LoadSampleData"
