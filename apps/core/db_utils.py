import time
import threading
from functools import wraps
from django.db import transaction, OperationalError
import logging

logger = logging.getLogger(__name__)

# Global lock for database operations during startup
_startup_lock = threading.Lock()


def retry_on_db_lock(max_retries=5, delay=0.5, backoff=2):
    """
    Decorator to retry database operations when encountering database lock errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries:
                        last_exception = e
                        logger.warning(
                            f"Database locked during {func.__name__}, "
                            f"attempt {attempt + 1}/{max_retries + 1}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
            
            # If we've exhausted all retries, raise the last exception
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def synchronized_startup(func):
    """
    Decorator to ensure startup operations don't run concurrently.
    This prevents database lock issues during app initialization.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with _startup_lock:
            return func(*args, **kwargs)
    return wrapper


class DatabaseTransactionContext:
    """
    Context manager for handling database transactions with retry logic.
    """
    def __init__(self, using=None, max_retries=5, delay=0.5):
        self.using = using
        self.max_retries = max_retries
        self.delay = delay
        self.transaction = None
        
    def __enter__(self):
        # Start transaction
        self.transaction = transaction.atomic(using=self.using)
        self.transaction.__enter__()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Handle transaction exit with retry logic
        if exc_type is OperationalError and "database is locked" in str(exc_val):
            # Rollback and let retry_on_db_lock handle it
            self.transaction.__exit__(exc_type, exc_val, exc_tb)
            return False
        else:
            # Normal transaction handling
            return self.transaction.__exit__(exc_type, exc_val, exc_tb)
