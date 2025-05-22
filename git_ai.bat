@echo off
set VERSION_FILE=version.txt
set README_FILE=README.md
set CHANGELOG_FILE=CHANGELOG.md

echo Starting Git Automation...

REM Fetch the latest Git version from tags, if available
FOR /F "tokens=* delims=" %%A IN ('git describe --tags 2^>nul') DO set CURRENT_VERSION=%%A
IF "%CURRENT_VERSION%"=="" (
    FOR /F "tokens=* delims=" %%A IN ('git rev-parse HEAD') DO set CURRENT_VERSION=%%A
)

echo Current Git Repository Version: %CURRENT_VERSION%

REM Extract major, minor, and patch numbers if using tag versioning
FOR /F "tokens=1,2,3 delims=." %%A IN ("%CURRENT_VERSION:v=%") DO (
    set MAJOR=%%A
    set MINOR=%%B
    set PATCH=%%C
)

echo Detecting changes automatically...

FOR /F "tokens=*" %%A IN ('git status --porcelain') DO set CHANGES=%%A

REM Auto-generate a branch name based on detected changes
set BRANCH_NAME=feature-%CURRENT_VERSION%-auto-update
git checkout -b "%BRANCH_NAME%"
echo Created new branch: %BRANCH_NAME%

REM Generate commit message automatically
set FULL_COMMIT_MSG=[%CURRENT_VERSION%] Auto-detected changes: %CHANGES%

REM Update README.md
echo. >> "%README_FILE%"
echo ## Version: %CURRENT_VERSION% >> "%README_FILE%"
echo ### Changes in this version: >> "%README_FILE%"
echo %CHANGES% >> "%README_FILE%"
echo Timestamp: %DATE% %TIME% >> "%README_FILE%"
echo. >> "%README_FILE%"

REM Append commit details to CHANGELOG.md
echo. >> "%CHANGELOG_FILE%"
echo ## Version: %CURRENT_VERSION% >> "%CHANGELOG_FILE%"
echo - %FULL_COMMIT_MSG% >> "%CHANGELOG_FILE%"
echo Timestamp: %DATE% %TIME% >> "%CHANGELOG_FILE%"
echo. >> "%CHANGELOG_FILE%"

git add .
git commit -m "%FULL_COMMIT_MSG%"

REM Auto-tag version
git tag "%CURRENT_VERSION%"

REM Auto-generate GitHub pull request description
echo ## Pull Request: %CURRENT_VERSION% > PR_description.txt
echo ### Summary of Changes: >> PR_description.txt
echo %CHANGES% >> PR_description.txt
echo Timestamp: %DATE% %TIME% >> PR_description.txt

echo Pull request details saved in PR_description.txt
echo Commit saved under version %CURRENT_VERSION% with README and CHANGELOG updated.