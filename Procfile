web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn adakings_backend.wsgi:application --bind 0.0.0.0:$PORT
