@echo off
set VERSION_FILE=version.txt
set README_FILE=README.md
set CHANGELOG_FILE=CHANGELOG.md

echo Starting Git Automation...

REM Fetch the current Git branch name
FOR /F "tokens=*" %%A IN ('git rev-parse --abbrev-ref HEAD') DO set CURRENT_BRANCH=%%A

echo Current Git Branch: %CURRENT_BRANCH%

REM Fetch the latest version number
FOR /F "tokens=* delims=" %%A IN ('git describe --tags 2^>nul') DO set CURRENT_VERSION=%%A
IF "%CURRENT_VERSION%"=="" (
    FOR /F "tokens=* delims=" %%A IN ('git rev-parse --short HEAD') DO set CURRENT_VERSION=%%A
)

echo Current Version: %CURRENT_VERSION%

REM Extract major, minor, and patch numbers
FOR /F "tokens=1,2,3 delims=." %%A IN ("%CURRENT_VERSION:v=%") DO (
    set MAJOR=%%A
    set MINOR=%%B
    set PATCH=%%C
)

echo Select an option:
echo 1. Commit changes (Patch update)
echo 2. Commit changes (Minor update)
echo 3. Commit changes (Major update)
echo 4. Push to current branch
echo 5. Show Git log
echo 6. Exit
set /p choice="Enter your choice: "

IF "%choice%"=="1" (
    set /a PATCH=%PATCH% + 1
    set NEW_VERSION=v%MAJOR%.%MINOR%.%PATCH%
) ELSE IF "%choice%"=="2" (
    set /a MINOR=%MINOR% + 1
    set PATCH=0
    set NEW_VERSION=v%MAJOR%.%MINOR%.%PATCH%
) ELSE IF "%choice%"=="3" (
    set /a MAJOR=%MAJOR% + 1
    set MINOR=0
    set PATCH=0
    set NEW_VERSION=v%MAJOR%.%MINOR%.%PATCH%
) ELSE IF "%choice%"=="4" (
    git push origin %CURRENT_BRANCH%
    echo Changes pushed to branch: %CURRENT_BRANCH%.
    exit /b
) ELSE IF "%choice%"=="5" (
    git log --oneline --graph --decorate --all
    exit /b
) ELSE IF "%choice%"=="6" (
    echo Exiting Git Automation.
    exit /b
) ELSE (
    echo Invalid option.
    exit /b
)

echo %NEW_VERSION% > "%VERSION_FILE%"
echo Updated Version: %NEW_VERSION%

REM Detect changes and auto-generate a description
FOR /F "tokens=*" %%A IN ('git status --porcelain') DO set CHANGES=%%A
set BRANCH_DESCRIPTION=update
IF "%CHANGES%" NEQ "" (
    set BRANCH_DESCRIPTION=auto-%CHANGES%
)

REM Generate branch name in the format `feature/current-branch-vX.Y.Z-description`
set BRANCH_NAME=feature/%CURRENT_BRANCH%-%NEW_VERSION%-%BRANCH_DESCRIPTION%
git checkout -b "%BRANCH_NAME%"
echo Created new branch: %BRANCH_NAME%

REM Generate commit message automatically
set FULL_COMMIT_MSG=[%CURRENT_BRANCH% %NEW_VERSION%] Auto-detected changes: %CHANGES%

REM Update README.md
echo. >> "%README_FILE%"
echo ## Branch: %CURRENT_BRANCH% >> "%README_FILE%"
echo ## Version: %NEW_VERSION% >> "%README_FILE%"
echo ### Changes in this update: >> "%README_FILE%"
echo %CHANGES% >> "%README_FILE%"
echo Timestamp: %DATE% %TIME% >> "%README_FILE%"
echo. >> "%README_FILE%"

REM Append commit details to CHANGELOG.md
echo. >> "%CHANGELOG_FILE%"
echo ## Branch: %CURRENT_BRANCH% >> "%CHANGELOG_FILE%"
echo ## Version: %NEW_VERSION% >> "%CHANGELOG_FILE%"
echo - %FULL_COMMIT_MSG% >> "%CHANGELOG_FILE%"
echo Timestamp: %DATE% %TIME% >> "%CHANGELOG_FILE%"
echo. >> "%CHANGELOG_FILE%"

git add .
git commit -m "%FULL_COMMIT_MSG%"

REM Auto-tag version
git tag "%NEW_VERSION%"

echo Commit saved under branch %CURRENT_BRANCH% with version %NEW_VERSION%.
echo README and CHANGELOG updated dynamically.
