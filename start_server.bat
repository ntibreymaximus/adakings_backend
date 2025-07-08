@echo off
echo.
echo =====================================
echo   Adakings Backend Development Server
echo =====================================
echo.
echo Starting server with environment validation...
echo.
python manage.py runserver %1
echo.
echo Server stopped.
pause
