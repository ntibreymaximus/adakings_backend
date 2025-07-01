# Smart Deployment Script for Adakings Backend API (PowerShell)
# Windows PowerShell equivalent of smart_deploy.py

param(
    [Parameter(Mandatory=$true)]
    [string]$Environment,
    
    [ValidateSet("major", "minor", "patch")]
    [string]$BumpType = $null
)

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

# Show usage information
function Show-Usage {
    Write-Host "Smart Deployment Script for Adakings Backend API" -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\smart_deploy.ps1 production [major|minor|patch]"
    Write-Host "  .\smart_deploy.ps1 dev [minor|patch]"
    Write-Host "  .\smart_deploy.ps1 feature/name [patch]"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\smart_deploy.ps1 production major   # v1.0.0 -> v2.0.0"
    Write-Host "  .\smart_deploy.ps1 dev minor          # v1.0.0 -> v1.1.0"
    Write-Host "  .\smart_deploy.ps1 feature/auth patch # v1.0.0 -> v1.0.1"
    Write-Host ""
    Write-Host "Available environments:"
    Write-Host "  production  - Deploy to production branch"
    Write-Host "  dev         - Deploy to dev branch (production-like with dev values)"
    Write-Host "  feature/name - Deploy to feature branch"
    Write-Host ""
    Write-Host "Version bump types:"
    Write-Host "  major  - Breaking changes (1.0.0 -> 2.0.0)"
    Write-Host "  minor  - New features (1.0.0 -> 1.1.0)"
    Write-Host "  patch  - Bug fixes (1.0.0 -> 1.0.1)"
}

# Validate environment
$validEnvironments = @("production", "dev")
$isFeatureBranch = $Environment.StartsWith("feature/")

if (-not ($validEnvironments -contains $Environment) -and -not $isFeatureBranch) {
    Write-Error "Invalid environment: $Environment"
    Show-Usage
    exit 1
}

# Set default bump type if not provided
if (-not $BumpType) {
    if ($Environment -eq "production") {
        $BumpType = "patch"  # Conservative default for production
    } elseif ($Environment -eq "dev") {
        $BumpType = "minor"  # New features in development
    } else {
        $BumpType = "patch"  # Feature branches typically have patches
    }
}

# Validate version bump type for environment
if ($Environment -eq "production" -and $BumpType -eq "major") {
    Write-Warning "Major version bump in production - this indicates breaking changes!"
}

Write-Host "🎯 Target Environment: $Environment" -ForegroundColor Cyan
Write-Host "🔢 Version Bump: $BumpType" -ForegroundColor Cyan

# Check if Python is available and use the Python script
$pythonAvailable = $false
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $pythonAvailable = $true
        Write-Info "Python is available: $pythonVersion"
    }
} catch {
    Write-Warning "Python not found in PATH"
}

if ($pythonAvailable) {
    Write-Info "Using Python smart_deploy.py script..."
    
    # Confirm deployment for production
    if ($Environment -eq "production") {
        Write-Warning "WARNING: This will deploy to PRODUCTION!"
        Write-Warning "This will create a new version with a $($BumpType.ToUpper()) bump."
        $response = Read-Host "Are you sure you want to continue? (yes/no)"
        if ($response.ToLower() -notin @("yes", "y")) {
            Write-Info "Deployment cancelled."
            exit 0
        }
    }
    
    # Execute Python smart deploy script
    python smart_deploy.py $Environment $BumpType
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Deployment completed successfully!"
    } else {
        Write-Error "Deployment failed!"
        exit 1
    }
} else {
    Write-Warning "Python not available. Using PowerShell deployment scripts..."
    
    # Determine which PowerShell script to run
    if ($Environment -eq "production") {
        $deployScript = ".\environments\production\deploy.ps1"
        if (Test-Path $deployScript) {
            Write-Info "Running production deployment script..."
            & $deployScript
        } else {
            Write-Error "Production deployment script not found: $deployScript"
            exit 1
        }
    } elseif ($Environment -eq "dev") {
        $deployScript = ".\environments\dev\deploy.ps1"
        if (Test-Path $deployScript) {
            Write-Info "Running dev deployment script..."
            & $deployScript -CreateSuperuser:$false -LoadSampleData:$false
        } else {
            Write-Error "Dev deployment script not found: $deployScript"
            exit 1
        }
    } elseif ($isFeatureBranch) {
        $setupScript = ".\environments\feature\setup.ps1"
        if (Test-Path $setupScript) {
            Write-Info "Running feature environment setup script..."
            & $setupScript -CreateSuperuser:$false -LoadSampleData:$false -RunTests:$false
        } else {
            Write-Error "Feature setup script not found: $setupScript"
            exit 1
        }
    }
    
    Write-Info ""
    Write-Info "Note: For full smart deployment features (version management, git operations),"
    Write-Info "please install Python and use the Python smart_deploy.py script."
    Write-Info ""
    Write-Info "Manual steps for version management:"
    Write-Info "1. Update version in environments\$Environment\VERSION"
    Write-Info "2. Update CHANGELOG.md in environments\$Environment\"
    Write-Info "3. Commit and push changes to appropriate branch"
}

Write-Host ""
Write-Info "Deployment process completed."
