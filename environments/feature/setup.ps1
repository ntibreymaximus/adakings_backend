# Feature environment setup script for Adakings Backend API (Windows)
# This script sets up the local development environment on Windows

param(
    [switch]$CreateSuperuser = $false,
    [switch]$LoadSampleData = $false,
    [switch]$RunTests = $false
)

# Configuration
$PROJECT_NAME = "adakings_backend"
$PROJECT_DIR = Get-Location
$VENV_DIR = Join-Path $PROJECT_DIR "venv"
$ENV_DIR = Join-Path $PROJECT_DIR "environments\feature"
$LOG_DIR = Join-Path $PROJECT_DIR "logs"

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

Write-Host "🛠️ Starting Adakings Backend API feature environment setup..." -ForegroundColor Cyan

# Create necessary directories
Write-Info "Creating directory structure..."
if (!(Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
}
Write-Success "Directory structure created"

# Check if feature .env.example file exists, create if needed
$envExample = Join-Path $PROJECT_DIR ".env.example"
$envTemplate = Join-Path $ENV_DIR ".env.template"

if (!(Test-Path $envExample)) {
    Write-Info "Creating .env.example from feature template..."
    if (Test-Path $envTemplate) {
        Copy-Item $envTemplate $envExample
        Write-Success ".env.example created"
    } else {
        Write-Error "Feature .env template not found at $envTemplate!"
        exit 1
    }
} else {
    Write-Info ".env.example already exists"
}

# Create virtual environment if it doesn't exist
if (!(Test-Path $VENV_DIR)) {
    Write-Info "Creating virtual environment..."
    python -m venv $VENV_DIR
    Write-Success "Virtual environment created"
} else {
    Write-Info "Virtual environment already exists"
}

# Activate virtual environment
Write-Info "Activating virtual environment..."
$activateScript = Join-Path $VENV_DIR "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Success "Virtual environment activated"
} else {
    Write-Error "Could not find activation script at $activateScript"
    exit 1
}

# Install/update feature dependencies
Write-Info "Installing feature development dependencies..."
$requirementsFile = Join-Path $ENV_DIR "requirements.txt"
if (Test-Path $requirementsFile) {
    python -m pip install --upgrade pip
    python -m pip install -r $requirementsFile
    Write-Success "Feature dependencies installed"
} else {
    Write-Error "Requirements file not found at $requirementsFile"
    exit 1
}

# Set Django settings for development
$env:DJANGO_SETTINGS_MODULE = "adakings_backend.settings.development"
$env:DJANGO_ENVIRONMENT = "development"

# Run Django commands
Write-Info "Running Django management commands..."

# Run database migrations (SQLite by default)
Write-Info "Running database migrations..."
python manage.py migrate --noinput
if ($LASTEXITCODE -eq 0) {
    Write-Success "Database migrations completed"
} else {
    Write-Error "Database migration failed"
    exit 1
}

# Create superuser if requested
if ($CreateSuperuser) {
    Write-Info "Creating superuser..."
    python manage.py createsuperuser
}

# Load sample data if available and requested
$sampleDataFile = Join-Path $PROJECT_DIR "fixtures\feature_sample_data.json"
if ((Test-Path $sampleDataFile) -and $LoadSampleData) {
    Write-Info "Loading sample data..."
    python manage.py loaddata $sampleDataFile
    Write-Success "Sample data loaded"
}

# Check for development tools
Write-Info "Checking development tools..."

# Check if debug toolbar is available
python -c "import debug_toolbar" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Debug toolbar available"
} else {
    Write-Warning "Debug toolbar not available (optional)"
}

# Check if pytest is available
python -c "import pytest" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Success "Pytest available"
} else {
    Write-Warning "Pytest not available"
}

# Check deployment
Write-Info "Running development checks..."
python manage.py check
if ($LASTEXITCODE -eq 0) {
    Write-Success "Development checks passed"
} else {
    Write-Error "Development checks failed"
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

# Run tests if requested
if ($RunTests) {
    Write-Info "Running tests..."
    python manage.py test
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Some tests failed"
    }
}

# Final status
Write-Success "🎉 Feature environment setup completed successfully!"
Write-Info "You can now run: python manage.py runserver local"
Write-Info "API Documentation: http://localhost:8000/api/docs/"
Write-Info "Admin interface: http://localhost:8000/admin/"

Write-Host ""
Write-Info "Feature Environment Ready!"
Write-Info "Setup completed at: $(Get-Date)"
Write-Info "Environment: Feature/Local Development"
Write-Info "Database: SQLite (local file)"
Write-Info "Debug Mode: Enabled"
Write-Info "Hot Reloading: Enabled"

Write-Host ""
Write-Info "Next Steps:"
Write-Info "1. Start development server: python manage.py runserver local"
Write-Info "2. Open browser: http://localhost:8000/api/docs/"
Write-Info "3. Start coding your features!"
Write-Info "4. Run tests: python manage.py test"

Write-Host ""
Write-Info "To use this script with options:"
Write-Info ".\setup.ps1 -CreateSuperuser -LoadSampleData -RunTests"
