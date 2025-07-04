@echo off
echo Installing Django Channels for WebSocket support...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install WebSocket requirements
echo Installing channels dependencies...
pip install -r requirements-channels.txt

REM Run migrations if needed
echo Running migrations...
python manage.py makemigrations
python manage.py migrate

echo WebSocket support enabled!
echo To start the server with WebSocket support, use:
echo   python manage.py runserver
echo.
echo Or for production ASGI:
echo   daphne -p 8000 adakings_backend.asgi:application

pause
