# Adakings Backend API - Environment Setup and Verification Script
# This script verifies and sets up all required environment files and dependencies

param(
    [ValidateSet("feature", "dev", "production", "all")]
    [string]$Environment = "all",
    [switch]$Force = $false,
    [switch]$VerifyOnly = $false
)

# Configuration
$PROJECT_DIR = Get-Location
$ENVIRONMENTS = @("feature", "dev", "production")

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

function Test-EnvironmentFiles {
    param($EnvName)
    
    $envDir = Join-Path $PROJECT_DIR "environments\$EnvName"
    $requiredFiles = @(
        ".env.template",
        "requirements.txt",
        "VERSION",
        "README.md",
        "CHANGELOG.md"
    )
    
    # Add environment-specific required files
    if ($EnvName -eq "dev" -or $EnvName -eq "production") {
        $requiredFiles += @(
            "gunicorn.conf.py",
            "nginx.conf",
            "Dockerfile",
            "docker-compose.yml"
        )
        
        if ($EnvName -eq "dev") {
            $requiredFiles += @("adakings-backend-dev.service")
        } else {
            $requiredFiles += @("adakings-backend.service")
        }
    }
    
    $missingFiles = @()
    $existingFiles = @()
    
    foreach ($file in $requiredFiles) {
        $filePath = Join-Path $envDir $file
        if (Test-Path $filePath) {
            $existingFiles += $file
        } else {
            $missingFiles += $file
        }
    }
    
    # Check for deployment scripts
    $bashScript = Join-Path $envDir "deploy.sh"
    $powershellScript = Join-Path $envDir "deploy.ps1"
    $setupScript = Join-Path $envDir "setup.sh"
    $setupPsScript = Join-Path $envDir "setup.ps1"
    
    if ($EnvName -eq "feature") {
        if (Test-Path $setupScript) { $existingFiles += "setup.sh" } else { $missingFiles += "setup.sh" }
        if (Test-Path $setupPsScript) { $existingFiles += "setup.ps1" } else { $missingFiles += "setup.ps1" }
    } else {
        if (Test-Path $bashScript) { $existingFiles += "deploy.sh" } else { $missingFiles += "deploy.sh" }
        if (Test-Path $powershellScript) { $existingFiles += "deploy.ps1" } else { $missingFiles += "deploy.ps1" }
    }
    
    return @{
        Environment = $EnvName
        ExistingFiles = $existingFiles
        MissingFiles = $missingFiles
        IsComplete = ($missingFiles.Count -eq 0)
    }
}

function Show-EnvironmentStatus {
    param($Results)
    
    Write-Host ""
    Write-Host "=== Environment Setup Status ===" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($result in $Results) {
        $envName = $result.Environment.ToUpper()
        if ($result.IsComplete) {
            Write-Success "✅ $envName environment is properly configured"
        } else {
            Write-Warning "⚠️  $envName environment has missing files"
        }
        
        if ($result.ExistingFiles.Count -gt 0) {
            Write-Info "   Existing files: $($result.ExistingFiles -join ', ')"
        }
        
        if ($result.MissingFiles.Count -gt 0) {
            Write-Warning "   Missing files: $($result.MissingFiles -join ', ')"
        }
        Write-Host ""
    }
}

function Test-PythonDependencies {
    Write-Info "Checking Python installation..."
    
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python is installed: $pythonVersion"
        } else {
            Write-Error "Python is not installed or not in PATH"
            return $false
        }
    } catch {
        Write-Error "Python is not installed or not in PATH"
        return $false
    }
    
    return $true
}

function Test-RequiredDirectories {
    Write-Info "Checking directory structure..."
    
    $requiredDirs = @(
        "environments",
        "environments\feature",
        "environments\dev", 
        "environments\production",
        "adakings_backend",
        "apps"
    )
    
    $allExist = $true
    foreach ($dir in $requiredDirs) {
        $dirPath = Join-Path $PROJECT_DIR $dir
        if (Test-Path $dirPath) {
            Write-Success "✅ Directory exists: $dir"
        } else {
            Write-Error "❌ Missing directory: $dir"
            $allExist = $false
        }
    }
    
    return $allExist
}

function Initialize-Environment {
    param($EnvName)
    
    if ($VerifyOnly) {
        Write-Info "Verification mode - skipping initialization of $EnvName"
        return
    }
    
    Write-Info "Initializing $EnvName environment..."
    
    $envDir = Join-Path $PROJECT_DIR "environments\$EnvName"
    
    # Check if we can run the setup script
    if ($EnvName -eq "feature") {
        $setupScript = Join-Path $envDir "setup.ps1"
        if (Test-Path $setupScript) {
            Write-Info "Running feature environment setup..."
            try {
                & $setupScript -CreateSuperuser:$false -LoadSampleData:$false -RunTests:$false
                Write-Success "Feature environment initialized successfully"
            } catch {
                Write-Warning "Feature environment setup encountered issues: $($_.Exception.Message)"
            }
        }
    } else {
        $deployScript = Join-Path $envDir "deploy.ps1"
        if (Test-Path $deployScript) {
            Write-Info "Running $EnvName environment deployment..."
            try {
                if ($EnvName -eq "production") {
                    & $deployScript -SkipHealthCheck
                } else {
                    & $deployScript -CreateSuperuser:$false -LoadSampleData:$false
                }
                Write-Success "$EnvName environment initialized successfully"
            } catch {
                Write-Warning "$EnvName environment setup encountered issues: $($_.Exception.Message)"
            }
        }
    }
}

# Main execution
Write-Host "🛠️  Adakings Backend API - Environment Setup Verification" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host ""

# Test basic requirements
Write-Info "Verifying basic requirements..."
$pythonOk = Test-PythonDependencies
$dirsOk = Test-RequiredDirectories

if (-not $pythonOk -or -not $dirsOk) {
    Write-Error "Basic requirements not met. Please install Python and ensure directory structure is correct."
    exit 1
}

# Determine which environments to check
$envsToCheck = if ($Environment -eq "all") { $ENVIRONMENTS } else { @($Environment) }

# Test each environment
$results = @()
foreach ($env in $envsToCheck) {
    Write-Info "Checking $env environment..."
    $result = Test-EnvironmentFiles -EnvName $env
    $results += $result
}

# Show status
Show-EnvironmentStatus -Results $results

# Check if .env.example exists in root
Write-Info "Checking root environment files..."
$rootEnvExample = Join-Path $PROJECT_DIR ".env.example"
if (Test-Path $rootEnvExample) {
    Write-Success "✅ Root .env.example exists"
} else {
    Write-Warning "⚠️  Root .env.example missing (created during setup)"
}

# Summary
$completeEnvs = ($results | Where-Object { $_.IsComplete }).Count
$totalEnvs = $results.Count

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Complete environments: $completeEnvs/$totalEnvs" -ForegroundColor $(if ($completeEnvs -eq $totalEnvs) { "Green" } else { "Yellow" })

if ($completeEnvs -eq $totalEnvs) {
    Write-Success "🎉 All environments are properly configured!"
    Write-Info ""
    Write-Info "Quick Start Commands:"
    Write-Info "  Feature/Local: python manage.py runserver local"
    Write-Info "  Development:   python manage.py runserver dev"
    Write-Info "  Production:    python manage.py runserver prod"
    Write-Info ""
    Write-Info "Setup Commands:"
    Write-Info "  Feature:    .\environments\feature\setup.ps1"
    Write-Info "  Dev:        .\environments\dev\deploy.ps1"
    Write-Info "  Production: .\environments\production\deploy.ps1"
} else {
    Write-Warning "Some environments need attention. Check the missing files above."
    
    # Ask if user wants to initialize missing environments
    if (-not $VerifyOnly) {
        $incompleteEnvs = $results | Where-Object { -not $_.IsComplete }
        foreach ($env in $incompleteEnvs) {
            if ($Force) {
                Initialize-Environment -EnvName $env.Environment
            } else {
                $response = Read-Host "Do you want to initialize $($env.Environment) environment? (y/N)"
                if ($response -match "^[Yy]") {
                    Initialize-Environment -EnvName $env.Environment
                }
            }
        }
    }
}

Write-Host ""
Write-Info "Environment setup verification completed at: $(Get-Date)"
Write-Host ""
Write-Info "For more information, see: ENVIRONMENT_GUIDE.md"
