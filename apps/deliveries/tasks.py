from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task
def reset_daily_deliveries():
    """
    Task to reset daily deliveries at midnight every day.
    This should be scheduled to run at 00:00 daily.
    """
    try:
        call_command('reset_daily_deliveries')
        logger.info("Successfully reset daily deliveries")
        return "Daily deliveries reset successfully"
    except Exception as e:
        logger.error(f"Error resetting daily deliveries: {e}")
        raise
