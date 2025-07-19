import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adakings_backend.settings')

# Create the Celery app
app = Celery('adakings_backend')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed Django apps
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'reset-daily-deliveries': {
        'task': 'apps.deliveries.tasks.reset_daily_deliveries',
        'schedule': crontab(hour=0, minute=0),  # Run at midnight every day
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not executed
        }
    },
}

# Set timezone for periodic tasks
app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
