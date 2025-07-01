# Production environment setup script for Adakings Backend API (Windows)
# This script deploys the application to production environment on Windows

param(
    [switch]$SkipHealthCheck = $false
)

# Configuration
$PROJECT_NAME = "adakings_backend"
$PROJECT_DIR = Get-Location
$VENV_DIR = Join-Path $PROJECT_DIR "venv"
$STATIC_DIR = Join-Path $PROJECT_DIR "staticfiles"
$MEDIA_DIR = Join-Path $PROJECT_DIR "mediafiles"
$LOG_DIR = Join-Path $PROJECT_DIR "logs"
$ENV_DIR = Join-Path $PROJECT_DIR "environments\production"

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

Write-Host "🚀 Starting Adakings Backend API production deployment..." -ForegroundColor Cyan

# Create necessary directories
Write-Info "Creating directory structure..."
$directories = @($LOG_DIR, $STATIC_DIR, $MEDIA_DIR)
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Success "Directory structure created"

# Check if production .env file exists
$envProd = Join-Path $ENV_DIR ".env"
$envTemplate = Join-Path $ENV_DIR ".env.template"

if (!(Test-Path $envProd)) {
    Write-Error "Production .env file not found at $envProd!"
    Write-Info "Please copy $envTemplate to $envProd and configure with production values"
    exit 1
}

# Copy production environment file to project root
Write-Info "Setting up production environment..."
Copy-Item $envProd ".env"
Write-Success "Production environment configured"

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

# Copy production-specific configurations
Write-Info "Setting up production-specific configurations..."
$prodGunicornConf = Join-Path $ENV_DIR "gunicorn.conf.py"
if (Test-Path $prodGunicornConf) {
    Copy-Item $prodGunicornConf "gunicorn.conf.py" -Force
    Write-Success "Production gunicorn configuration copied"
}

# Copy systemd service file
$systemdFile = Join-Path $ENV_DIR "adakings-backend.service"
if (Test-Path $systemdFile) {
    Write-Info "Systemd service file available at: $systemdFile"
    Write-Info "To install: sudo cp $systemdFile /etc/systemd/system/"
}

# Copy nginx configuration
$nginxFile = Join-Path $ENV_DIR "nginx.conf"
if (Test-Path $nginxFile) {
    Write-Info "Nginx configuration available at: $nginxFile"
    Write-Info "Copy to your nginx sites-available directory"
}

# Install/update production dependencies
Write-Info "Installing production dependencies..."
$requirementsFile = Join-Path $ENV_DIR "requirements.txt"
if (Test-Path $requirementsFile) {
    python -m pip install --upgrade pip
    python -m pip install -r $requirementsFile
    Write-Success "Production dependencies installed"
}

# Set Django settings for production
$env:DJANGO_SETTINGS_MODULE = "adakings_backend.settings.production"
$env:DJANGO_ENVIRONMENT = "production"

# Run Django commands
Write-Info "Running Django management commands..."

# Collect static files
Write-Info "Collecting static files..."
python manage.py collectstatic --noinput --clear
Write-Success "Static files collected"

# Run database migrations
Write-Info "Running database migrations..."
python manage.py migrate --noinput
Write-Success "Database migrations completed"

# Create cache table (if using database cache)
Write-Info "Creating cache table..."
python manage.py createcachetable

# Check deployment
Write-Info "Running deployment checks..."
python manage.py check --deploy
if ($LASTEXITCODE -eq 0) {
    Write-Success "Deployment checks passed"
} else {
    Write-Error "Deployment checks failed"
    exit 1
}

# Test database connection
Write-Info "Testing database connection..."
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Database connection successful')"
if ($LASTEXITCODE -eq 0) {
    Write-Success "Database connection verified"
} else {
    Write-Error "Database connection failed"
    exit 1
}

# Clear Django cache (if using cache)
Write-Info "Clearing application cache..."
python manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache cleared')"

# Health check
if (!$SkipHealthCheck) {
    Write-Info "Performing health check..."
    Start-Sleep -Seconds 5  # Wait for services to start
    
    # Check if API is responding (adjust URL as needed)
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/schema/" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Success "API health check passed"
        } else {
            Write-Warning "API health check returned status: $($response.StatusCode)"
        }
    } catch {
        Write-Warning "API health check failed: $($_.Exception.Message)"
    }
}

# Final status
Write-Success "🎉 Production deployment completed successfully!"
Write-Info "API is ready for production use"
Write-Info "Static files location: $STATIC_DIR"
Write-Info "Media files location: $MEDIA_DIR"
Write-Info "Logs location: $LOG_DIR"

Write-Host ""
Write-Info "Production Environment Ready!"
Write-Info "Deployment completed at: $(Get-Date)"
Write-Info "Environment: Production"
Write-Info "Database: PostgreSQL (Production)"
Write-Info "Debug Mode: Disabled"
Write-Info "Static Files: Collected"

Write-Host ""
Write-Info "Next Steps:"
Write-Info "1. Configure your web server (IIS/Nginx) to serve static files"
Write-Info "2. Configure your WSGI server (e.g., Gunicorn on Linux or mod_wsgi)"
Write-Info "3. Set up monitoring and logging"
Write-Info "4. Configure SSL certificates"
Write-Info "5. Set up backup procedures"

Write-Host ""
Write-Info "To skip health check:"
Write-Info ".\deploy.ps1 -SkipHealthCheck"
