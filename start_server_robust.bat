@echo off
echo Starting Adakings Backend Server with Robust Error Handling...
echo.

REM Check if virtual environment exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using system Python.
)

REM Set environment variables for better error handling
set PYTHONUNBUFFERED=1
set DJANGO_SETTINGS_MODULE=adakings_backend.settings

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Check if Django Channels dependencies are installed
echo Checking Django Channels installation...
python -c "import channels" 2>nul
if errorlevel 1 (
    echo Django Channels not found. Installing...
    pip install -r requirements-channels.txt
    if errorlevel 1 (
        echo Failed to install Django Channels. Please check your Python environment.
        pause
        exit /b 1
    )
)

REM Run migrations
echo Running database migrations...
python manage.py migrate
if errorlevel 1 (
    echo Migration failed. Please check the database configuration.
    pause
    exit /b 1
)

echo.
echo Choose server type:
echo 1. Django Development Server (recommended for development)
echo 2. Daphne ASGI Server (for WebSocket testing)
echo 3. Gunicorn Server (for production-like testing)
echo 4. Custom startup script with enhanced monitoring
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo Starting Django development server...
    python manage.py runserver 0.0.0.0:8000
) else if "%choice%"=="2" (
    echo Starting Daphne ASGI server...
    python start_server.py --server daphne --port 8000
) else if "%choice%"=="3" (
    echo Starting Gunicorn server...
    python start_server.py --server gunicorn --port 8001
) else if "%choice%"=="4" (
    echo Starting with enhanced monitoring...
    python start_server.py --server django --port 8000
) else (
    echo Invalid choice. Starting Django development server by default...
    python manage.py runserver 0.0.0.0:8000
)

echo.
echo Server stopped.
pause
