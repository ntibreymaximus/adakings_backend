@echo off
echo ============================================================
echo 🚀 ADAKINGS BACKEND - LOCAL DEVELOPMENT SERVER
echo ============================================================
echo.
echo 🔧 Starting Django development server...
echo 🌐 Server will be available at: http://127.0.0.1:8000/
echo 📖 API Documentation: http://127.0.0.1:8000/api/docs/
echo 🔐 Admin Panel: http://127.0.0.1:8000/admin/
echo.
echo 📝 Superuser Credentials:
echo    Username: superadmin
echo    Email: admin@adakings.com
echo    Password: (see console output from create_superuser.py)
echo.
echo ⏹️  Press CTRL+C to stop the server
echo ============================================================
echo.

python manage.py runserver
